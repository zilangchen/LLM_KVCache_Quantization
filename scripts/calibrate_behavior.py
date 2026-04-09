#!/usr/bin/env python3
"""
F1: Behavior-Aligned Calibration Script (scripts/calibrate_behavior.py)

Supports KL divergence (default) and MSE loss functions for calibration
via --loss_function {kl, mse}.

Loss semantics:
  - KL divergence: D_KL(p_ref || p_quant) summed over the attention distribution.
    Uses probability-safe clamping (eps=1e-6) before log to avoid numerical issues.
    Units: nats (natural log). Typical range: 1e-5 to 1e-1 for well-quantized models.
  - MSE: sum of squared differences between FP16 and quantized attention probabilities,
    i.e. sum((p_ref - p_quant)^2). No clamping is applied because softmax outputs are
    already in [0,1] and subtraction cannot produce inf/NaN.
    Units: squared probability. Typical range: 1e-8 to 1e-3.
  - IMPORTANT: KL and MSE absolute values are on fundamentally different scales.
    Trial rankings (--search) are only comparable within the same loss_function.
    Do NOT compare mean_kl values with mean_mse values across runs.

Outputs:
  - artifacts/kv_calib_{loss_function}.json (static k/v scales + per-head inv_tau)
  - results/calibration/calibration_stats.csv (optional stats)
  - results/calibration/search_trials.csv (if --search)
  - results/calibration/outlier_profile.png (optional plot)

Default output path:
  - artifacts/kv_calib_kl.json   (when --loss_function kl)
  - artifacts/kv_calib_mse.json  (when --loss_function mse)
  Note: generate_loop.py expects 'artifacts/kv_calib_kl.json' for int8_ours and
  'artifacts/kv_calib_kl_int4_selected.json' for int4_ours. If your default output
  path differs, pass --calib_file explicitly to generate_loop or rename the output.

Version history:
  - v1 (current): MSE path does NOT clamp attention probabilities before computing
    squared error. Earlier prototypes clamped p_ref/p_quant to [eps, 1] before MSE,
    which introduced a positive bias when both distributions had near-zero entries.
    Clamping was removed to preserve true squared error semantics. Calibration
    artifacts produced by older clamped code are not numerically reproducible with
    the current code; re-run calibration to regenerate.
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
import matplotlib.pyplot as plt
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.utils.repro import (
    build_config_snapshot,
    get_hardware_info,
    set_seed,
    write_config_snapshot,
)
from src.utils.hf import resolve_pretrained_path
from scripts.config_utils import load_config, resolve_run_config


def _rotate_half(x: torch.Tensor) -> torch.Tensor:
    """Rotate half the hidden dims of the input (RoPE helper).

    CAL-035: This function duplicates patch_model.py's _rotate_half (L203).
    Both must stay in sync if either changes. A shared src/utils/rope.py
    extraction is deferred because the calibration script runs offline and
    the two call-sites have subtly different input shapes.
    """
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def _apply_rope_to_q(
    q: torch.Tensor,
    cos: torch.Tensor,
    sin: torch.Tensor,
) -> torch.Tensor:
    """Apply rotary position embedding to query states only.

    CAL-035: Near-duplicate of patch_model.py _apply_rope (L210). Both must
    stay in sync; see _rotate_half note above.

    Args:
        q: [B, H, S, D] query states.
        cos, sin: from rotary_emb(), typically [B, S, rotary_dim] or broadcastable.
    Returns:
        Rotated query states, same shape as q.
    """
    cos = cos.to(device=q.device, dtype=q.dtype)
    sin = sin.to(device=q.device, dtype=q.dtype)
    # Normalize to [B, 1, S, rotary_dim] for broadcast across heads.
    if cos.ndim == 3:
        cos = cos.unsqueeze(1)
        sin = sin.unsqueeze(1)
    rotary_dim = cos.shape[-1]
    q_rot = q[..., :rotary_dim]
    q_pass = q[..., rotary_dim:]
    q_embed = (q_rot * cos) + (_rotate_half(q_rot) * sin)
    if q_pass.numel() == 0:
        return q_embed
    return torch.cat([q_embed, q_pass], dim=-1)


def _get_rope_for_position(attn_module, dummy_states, position_ids, model_backbone=None):
    """Get RoPE cos/sin for given position_ids, compatible with Qwen2/LLaMA APIs.

    Returns (cos, sin) or (None, None) if rotary embedding is unavailable.

    CAL-034: transformers 4.48+ moved rotary_emb from self_attn to
    model.model (backbone level). We try attn-level first, then fall
    back to the backbone-level rotary_emb passed via *model_backbone*.
    """
    rotary = getattr(attn_module, "rotary_emb", None)
    if rotary is None and model_backbone is not None:
        rotary = getattr(model_backbone, "rotary_emb", None)
    if rotary is None:
        return None, None
    # CAL-016/023/034: Catch RuntimeError and ValueError in addition to the
    # original three, because some rotary_emb implementations (e.g. LLaMA
    # using shape[1] as seq_len when receiving q-shaped hidden states) raise
    # RuntimeError on shape mismatch rather than TypeError/AttributeError.
    _EXPECTED = (AttributeError, KeyError, TypeError, RuntimeError, ValueError)
    for call in (
        lambda: rotary(dummy_states, position_ids),
        lambda: rotary(dummy_states, position_ids=position_ids),
        # CAL-034: keyword-only position_ids variant used by some transformers versions
        lambda: rotary(dummy_states, seq_len=position_ids.shape[-1]),
        lambda: rotary(position_ids),
    ):
        try:
            out = call()
        except _EXPECTED:
            continue
        if isinstance(out, (tuple, list)) and len(out) == 2:
            return out[0], out[1]
    # CAL-034: All API variants exhausted without success; warn instead of
    # silently returning None so callers know RoPE was unavailable.
    import warnings
    warnings.warn(
        "All rotary_emb API variants failed; returning (None, None). "
        "Q vectors will not have RoPE applied during calibration.",
        RuntimeWarning,
        stacklevel=2,
    )
    return None, None


def resolve_kv_params(run_entry: dict, quant_defaults: dict) -> Tuple[float, float, int, int]:
    # RUN-096: Hardcode fallbacks (16 / 99.5) now match the project-standard
    # quant_defaults in exp_matrix.yaml rather than the previous 128 / 99.9
    # which diverged from config_utils.resolve_run_config (CFG-034). Same
    # pattern as config_utils.py L164-192 and run_experiments.py:552.
    _FALLBACK_GROUP_SIZE = 16
    _FALLBACK_CLIP_PERCENTILE = 99.5
    clip_k = run_entry.get(
        "clip_percentile_k",
        run_entry.get("clip_percentile", quant_defaults.get("clip_percentile_k", _FALLBACK_CLIP_PERCENTILE)),
    )
    clip_v = run_entry.get(
        "clip_percentile_v",
        run_entry.get("clip_percentile", quant_defaults.get("clip_percentile_v", _FALLBACK_CLIP_PERCENTILE)),
    )
    group_k = run_entry.get(
        "group_size_k",
        run_entry.get("group_size", quant_defaults.get("group_size_k", _FALLBACK_GROUP_SIZE)),
    )
    group_v = run_entry.get(
        "group_size_v",
        run_entry.get("group_size", quant_defaults.get("group_size_v", _FALLBACK_GROUP_SIZE)),
    )
    # RUN-096: warn if fallback was actually used (quant_defaults had no value).
    if not quant_defaults.get("group_size_k") and "group_size" not in run_entry and "group_size_k" not in run_entry:
        import logging
        logging.getLogger(__name__).warning(
            "resolve_kv_params: group_size_k for run %r fell through to "
            "hardcoded fallback %d; consider setting quant_defaults.group_size_k in YAML.",
            run_entry.get("run_name"), _FALLBACK_GROUP_SIZE,
        )
    return clip_k, clip_v, group_k, group_v


def get_calibration_dataset(tokenizer, n_samples=128, seq_len=512):
    print("Loading WikiText-2 for calibration...")
    try:
        data = load_dataset("wikitext", "wikitext-2-raw-v1", split="test")
    except Exception as exc:
        raise RuntimeError(
            "Failed to load WikiText-2 calibration dataset. "
            "Calibration requires real tokenized data; a dummy string fallback "
            "would crash on .to(device) because strings are not tensors. "
            f"Original error: {exc}"
        ) from exc

    min_text_len = 10  # skip very short texts that tokenize to near-empty sequences
    encodings = []
    for text in data["text"]:
        if len(text.strip()) >= min_text_len:
            enc = tokenizer(text, return_tensors="pt")["input_ids"]
            if enc.size(1) > seq_len:
                enc = enc[:, :seq_len]
            encodings.append(enc)
            if len(encodings) >= n_samples:
                break

    if len(encodings) < n_samples:
        import warnings
        warnings.warn(
            f"Calibration dataset returned only {len(encodings)}/{n_samples} samples "
            f"(min_text_len={min_text_len}, seq_len={seq_len}). "
            "Calibration quality may be degraded with fewer samples.",
            RuntimeWarning,
        )
    return encodings


def compute_absmax_per_group(tensor: torch.Tensor, group_size: int) -> torch.Tensor:
    """Compute per-group absmax over the full sequence dimension.

    .. note:: CAL-012 — systematic scale overestimation (confidence 80%)
       This function takes the absmax over the entire sequence (amax(dim=1)),
       producing the global maximum per (head, group). When used to compute
       static calibration scales (via collect_absmax_samples -> percentile),
       the resulting scale = percentile(absmax_over_seq, across_samples).
       During inference, KV tokens are quantized incrementally per token,
       where each token's actual absmax is typically much smaller than the
       sequence-wide maximum. This makes the static scale conservatively
       large, leading to a coarser quantization grid than necessary.

       This is a known design trade-off of static symmetric calibration:
       the scale must accommodate the worst-case token to avoid clipping.
       The adaptive_static_scales mechanism (adaptive_static_margin) partially
       mitigates this by allowing per-token scale adjustment at inference time.
       A tighter calibration would require per-token or sliding-window scale
       computation, which conflicts with the static-scale design goal.
       No code fix applied; documented for awareness.
    """
    # tensor: [heads, seq, head_dim]
    heads, seq_len, head_dim = tensor.shape
    # CAL-021: Validate divisibility before view() to give a descriptive error
    # instead of an opaque RuntimeError when called independently of upstream checks.
    if group_size <= 0 or head_dim % group_size != 0:
        raise ValueError(
            f"head_dim ({head_dim}) must be divisible by group_size ({group_size})"
        )
    num_groups = head_dim // group_size
    view = tensor.view(heads, seq_len, num_groups, group_size)
    return view.abs().amax(dim=3).amax(dim=1)  # [heads, num_groups]


def dequantize_with_scale(
    k: torch.Tensor,
    scale: torch.Tensor,
    group_size: int,
    qmax: int = 127,
) -> torch.Tensor:
    """Quantize-then-dequantize k using a static scale (calibration simulation).

    Args:
        k: [seq, head_dim] — key tensor for one head.
        scale: [num_groups] — per-group scale (where num_groups = head_dim // group_size).
               CAL-019: num_groups corresponds to *kv_heads'* head_dim groups, not num_heads.
        group_size: elements per quantization group.
        qmax: clipping bound (127 for INT8, 7 for INT4).

    Returns:
        Dequantized tensor, same shape as k.
    """
    head_dim = k.shape[-1]
    num_groups = head_dim // group_size
    k_view = k.view(-1, num_groups, group_size)
    # CAL-010 + CAL-013: Clamp scale identically to the production path
    # (_normalize_static_scale uses clamp(min=1e-5)) to ensure calibration
    # loss faithfully reflects true inference quantization error.
    scale = scale.clamp(min=1e-5)
    scale_view = scale.view(1, num_groups, 1)
    q = torch.round(k_view / scale_view).clamp(-int(qmax), int(qmax))
    k_deq = q * scale_view
    return k_deq.view(-1, head_dim)


def quantize_dequantize_with_clip_stats(
    tensor: torch.Tensor,
    scale: torch.Tensor,
    group_size: int,
    qmax: int = 127,
    outlier_rescue_ratio: float = 0.0,
) -> Tuple[torch.Tensor, int, int]:
    """
    Quantize/dequantize with int8 range and return clipping stats.

    CAL-042: outlier_rescue_ratio is shared between K and V paths. In
    mixed_rescue=False mode, V rescue_ratio is forced to 0 in the caller
    (evaluate_quant_candidate). K and V have different outlier distributions
    (K is per-head-dim, V is per-token), so a single ratio is suboptimal.
    Independent K/V rescue optimization would require a 2D grid search.

    tensor: [seq, head_dim], scale: [num_groups]
    returns: dequantized tensor [seq, head_dim], clipped_count, total_count
    """
    head_dim = tensor.shape[-1]
    num_groups = head_dim // group_size
    tensor_view = tensor.view(-1, num_groups, group_size)
    scale_view = scale.view(1, num_groups, 1).expand(tensor_view.shape[0], -1, -1)

    if outlier_rescue_ratio > 0.0:
        # Promote top-ratio largest group magnitudes to dynamic scale (absmax/qmax).
        dynamic_absmax = tensor_view.abs().amax(dim=-1)  # [N, G]
        dynamic_scale = (dynamic_absmax.clamp(min=1e-5) / float(qmax)).unsqueeze(-1)
        if outlier_rescue_ratio >= 1.0:
            scale_view = torch.maximum(scale_view, dynamic_scale)
        else:
            threshold = torch.quantile(
                dynamic_absmax.float().reshape(-1),
                max(0.0, min(1.0, 1.0 - outlier_rescue_ratio)),
            ).to(dynamic_absmax.dtype)
            rescue_mask = (dynamic_absmax >= threshold).unsqueeze(-1)
            scale_view = torch.where(
                rescue_mask,
                torch.maximum(scale_view, dynamic_scale),
                scale_view,
            )

    normalized = tensor_view / scale_view
    clip_mask = normalized.abs() > float(qmax)
    q = torch.round(normalized).clamp(-float(qmax), float(qmax))
    deq = q * scale_view

    clipped_count = int(clip_mask.sum().item())
    total_count = int(clip_mask.numel())
    return deq.view(-1, head_dim), clipped_count, total_count


def compute_inv_tau(
    q_samples: List[List[torch.Tensor]],
    k_samples: List[List[torch.Tensor]],
    k_scales: List[torch.Tensor],
    num_heads: int,
    num_kv_heads: int,
    head_dim: int,
    group_size: int,
    inv_tau_candidates: List[float],
    qmax: int,
    loss_function: str = "kl",
) -> torch.Tensor:
    """Search for optimal inv_tau per (layer, head) via grid search over candidates.

    .. note:: CAL-011 — short-sequence degeneracy (confidence 75%)
       When a calibration sample has very short sequence length (1-2 tokens),
       the softmax attention distribution degenerates to near-uniform for all
       inv_tau candidates, making the KL/MSE losses approximately equal. In
       this case argmin selects the first candidate (typically 0.5), which may
       not be meaningful. In practice this is benign because:
       (a) calibration samples are filtered by min_text_len (default 256),
       (b) the per-sample loss is averaged over all samples, so short outliers
           are diluted by longer samples,
       (c) inv_tau is NOT used in the final INT4-RoleAlign configuration.
       No code fix needed; this is a known theoretical limitation of the grid
       search approach documented here for completeness.
    """
    if not inv_tau_candidates:
        raise ValueError(
            "inv_tau_candidates is empty. At least one candidate value is required "
            "for inv_tau search (e.g. --inv_tau_candidates '0.5,1.0,1.5')."
        )

    sm_scale = 1.0 / (head_dim ** 0.5)
    inv_tau_tensor = torch.ones((len(k_scales), num_heads), dtype=torch.float32)
    inv_tau_candidates_t = torch.tensor(inv_tau_candidates, dtype=torch.float32)
    eps = 1e-6

    kv_ratio = num_heads // num_kv_heads

    for layer_idx in range(len(k_scales)):
        scale_layer = k_scales[layer_idx]  # [kv_heads, num_groups]
        for head_idx in range(num_heads):
            kv_head = head_idx // kv_ratio
            loss_accum = torch.zeros(len(inv_tau_candidates), dtype=torch.float32)

            for sample_idx in range(len(q_samples)):
                q = q_samples[sample_idx][layer_idx][head_idx].float()  # [D]
                k = k_samples[sample_idx][layer_idx][kv_head].float()   # [S, D]

                logits_fp16 = (q @ k.T) * sm_scale
                p_ref = torch.softmax(logits_fp16, dim=-1)

                k_deq = dequantize_with_scale(
                    k,
                    scale_layer[kv_head].float(),
                    group_size,
                    qmax=qmax,
                )
                logits_quant = (q @ k_deq.T) * sm_scale

                logits_scaled = logits_quant.unsqueeze(0) * inv_tau_candidates_t[:, None]
                p_quant = torch.softmax(logits_scaled, dim=-1)

                if loss_function == "mse":
                    # MSE between FP16 and quantized attention distributions.
                    # CAL-009/CAL-016: We intentionally avoid clamping here to
                    # preserve true squared error. Clamping was removed because
                    # it introduced a positive bias (see module docstring).
                    mse = ((p_ref.unsqueeze(0) - p_quant) ** 2).sum(dim=-1)
                    loss_accum += mse
                else:
                    # KL divergence (default)
                    # CAL-026: Clamping to [eps, 1] prevents log(0) but breaks
                    # the normalization invariant (sum(p) == 1). This makes the
                    # computed KL a known approximation, not a true KL divergence.
                    # The bias is negligible when most probability mass is >> eps,
                    # which holds for typical softmax attention distributions.
                    p_ref_safe = torch.clamp(p_ref, min=eps)
                    p_quant_safe = torch.clamp(p_quant, min=eps)
                    kl = (p_ref_safe * (torch.log(p_ref_safe) - torch.log(p_quant_safe))).sum(dim=-1)
                    loss_accum += kl

            # Normalise by sample count so result is independent of --samples.
            num_samples = len(q_samples)
            if num_samples > 0:
                loss_accum /= num_samples

            # CAL-037: Clamp accumulated loss to non-negative before argmin.
            # KL divergence can become slightly negative due to clamping that
            # breaks the normalization invariant (see CAL-026). Negative loss
            # would bias argmin toward those candidates. Clamping to zero makes
            # the selection robust against this numerical artifact.
            loss_accum.clamp_(min=0.0)

            # CAL-017: Detect NaN in loss_accum which could silently corrupt
            # inv_tau selection (argmin of NaN is undefined).
            if torch.isnan(loss_accum).any():
                import warnings
                nan_count = int(torch.isnan(loss_accum).sum().item())
                warnings.warn(
                    f"NaN detected in loss_accum at layer={layer_idx}, head={head_idx}: "
                    f"{nan_count}/{len(inv_tau_candidates)} candidates are NaN. "
                    "Falling back to inv_tau=1.0 for this head. "
                    "This may indicate numerical issues in the calibration data.",
                    RuntimeWarning,
                )
                inv_tau_tensor[layer_idx, head_idx] = 1.0
                continue

            # CAL-027: Detect all-inf loss_accum which would cause argmin
            # to silently return index 0 (undefined/misleading behaviour).
            if torch.isinf(loss_accum).all():
                import warnings
                warnings.warn(
                    f"All inv_tau candidates produced inf loss at layer={layer_idx}, "
                    f"head={head_idx}. Falling back to inv_tau=1.0 for this head.",
                    RuntimeWarning,
                )
                inv_tau_tensor[layer_idx, head_idx] = 1.0
                continue

            best_idx = torch.argmin(loss_accum).item()
            inv_tau_tensor[layer_idx, head_idx] = inv_tau_candidates[best_idx]

    return inv_tau_tensor


def evaluate_quant_candidate(
    q_samples: List[List[torch.Tensor]],
    k_samples: List[List[torch.Tensor]],
    v_samples: List[List[torch.Tensor]],
    k_scales: List[torch.Tensor],
    v_scales: List[torch.Tensor],
    num_heads: int,
    num_kv_heads: int,
    head_dim: int,
    group_size_k: int,
    group_size_v: int,
    qmax: int,
    outlier_rescue_ratio: float = 0.0,
    mixed_rescue: bool = False,
    loss_function: str = "kl",
) -> Dict[str, float]:
    """
    Evaluate one candidate quantization setting.

    NOTE (CAL-015): This function intentionally does NOT apply inv_tau (per-head
    attention temperature scaling). inv_tau is computed *after* the best
    (clip_percentile, group_size) is selected by the search, because inv_tau
    depends on the chosen k_scales. Including inv_tau during candidate evaluation
    would create a circular dependency: inv_tau needs scales, but scales are what
    we are selecting here. Therefore, this function measures raw quantization
    distortion without temperature correction, which is the correct signal for
    hyperparameter search.

    Returns:
      When loss_function=="kl":
        - mean_kl, p95_kl, max_kl over attention distributions
      When loss_function=="mse":
        - mean_mse, p95_mse, max_mse over attention distributions
        - NOTE: MSE values are not numerically comparable to KL values
      Always:
        - k_clip_rate, v_clip_rate (fraction of elements clipped to int8 range)
        - v_rel_l2_mean (value dequant relative L2 error, mean over heads/samples/layers)
    """
    sm_scale = 1.0 / (head_dim ** 0.5)
    kv_ratio = num_heads // num_kv_heads
    eps = 1e-6

    loss_values: List[float] = []
    v_rel_l2_values: List[float] = []
    k_clip_count = 0
    k_total_count = 0
    v_clip_count = 0
    v_total_count = 0

    for layer_idx in range(len(k_scales)):
        k_scale_layer = k_scales[layer_idx]  # [kv_heads, num_groups]
        v_scale_layer = v_scales[layer_idx]  # [kv_heads, num_groups]

        for sample_idx in range(len(q_samples)):
            k_deq_for_sample: List[torch.Tensor] = []
            for kv_head in range(num_kv_heads):
                # K clipping/dequant stats
                k = k_samples[sample_idx][layer_idx][kv_head].float()  # [S, D]
                k_deq, k_clip_local, k_total_local = quantize_dequantize_with_clip_stats(
                    k,
                    k_scale_layer[kv_head].float(),
                    group_size_k,
                    qmax=qmax,
                    outlier_rescue_ratio=outlier_rescue_ratio,
                )
                k_deq_for_sample.append(k_deq)
                k_clip_count += k_clip_local
                k_total_count += k_total_local

                # V clipping/dequant stats + relative L2
                v = v_samples[sample_idx][layer_idx][kv_head].float()  # [S, D]
                v_deq, v_clip_local, v_total_local = quantize_dequantize_with_clip_stats(
                    v,
                    v_scale_layer[kv_head].float(),
                    group_size_v,
                    qmax=qmax,
                    outlier_rescue_ratio=outlier_rescue_ratio if mixed_rescue else 0.0,
                )
                v_clip_count += v_clip_local
                v_total_count += v_total_local

                v_rel_l2 = torch.norm(v - v_deq) / (torch.norm(v) + eps)
                v_rel_l2_values.append(float(v_rel_l2.item()))

            for head_idx in range(num_heads):
                kv_head = head_idx // kv_ratio
                q = q_samples[sample_idx][layer_idx][head_idx].float()  # [D]
                k = k_samples[sample_idx][layer_idx][kv_head].float()   # [S, D]
                k_deq = k_deq_for_sample[kv_head]

                logits_fp16 = (q @ k.T) * sm_scale
                p_ref = torch.softmax(logits_fp16, dim=-1)

                logits_quant = (q @ k_deq.T) * sm_scale
                p_quant = torch.softmax(logits_quant, dim=-1)

                if loss_function == "mse":
                    # CAL-016: MSE uses raw softmax probabilities (no clamping).
                    # Softmax outputs are in [0,1], so squared differences are
                    # bounded and cannot produce inf. Unlike KL, MSE treats
                    # over-estimation and under-estimation symmetrically and does
                    # not penalise near-zero probabilities disproportionately.
                    # Earlier versions clamped to [eps,1] before MSE, which added
                    # a positive bias; that clamping was removed in version 1.
                    mse = ((p_ref - p_quant) ** 2).sum().item()
                    loss_values.append(float(mse))
                else:
                    # KL divergence (default)
                    # CAL-026: Clamping to [eps, 1] prevents log(0) but breaks
                    # the normalization invariant (sum(p) == 1). This makes the
                    # computed KL a known approximation — see comment in
                    # compute_inv_tau for full rationale.
                    p_ref_safe = torch.clamp(p_ref, min=eps)
                    p_quant_safe = torch.clamp(p_quant, min=eps)
                    kl = (p_ref_safe * (torch.log(p_ref_safe) - torch.log(p_quant_safe))).sum().item()
                    loss_values.append(float(kl))

    if loss_values:
        mean_loss = float(np.mean(loss_values))
        p95_loss = float(np.quantile(np.array(loss_values, dtype=np.float64), 0.95))
        max_loss = float(np.max(loss_values))
    else:
        # CAL-025: Return inf (not 0.0) when no samples were evaluated.
        # Returning 0.0 would fool the search into selecting this candidate
        # as the "best" since it appears to have zero loss.
        mean_loss = float('inf')
        p95_loss = float('inf')
        max_loss = float('inf')

    # Build result dict with appropriate key names based on loss function
    if loss_function == "mse":
        loss_key_prefix = "mse"
    else:
        loss_key_prefix = "kl"

    return {
        f"mean_{loss_key_prefix}": mean_loss,
        f"p95_{loss_key_prefix}": p95_loss,
        f"max_{loss_key_prefix}": max_loss,
        "k_clip_rate": float(k_clip_count / max(k_total_count, 1)),
        "v_clip_rate": float(v_clip_count / max(v_total_count, 1)),
        "v_rel_l2_mean": float(np.mean(v_rel_l2_values)) if v_rel_l2_values else 0.0,
    }


def select_best_trial(
    trials: List[Dict[str, float]],
    objective: str,
    max_k_clip_rate: float,
    max_v_clip_rate: float,
    loss_function: str = "kl",
) -> Tuple[Dict[str, float], Dict[str, object]]:
    """Select the best trial from a list of candidate quantization settings.

    LIMITATION (CAL-006): All trials are ranked within a single loss_function.
    KL divergence (nats) and MSE (squared probability) have fundamentally
    different numeric scales, so rankings produced under --loss_function kl
    are NOT comparable with rankings produced under --loss_function mse.
    If you need cross-loss comparison, normalize scores to z-scores or
    percentile ranks externally.

    Args:
        trials: List of trial dicts from evaluate_quant_candidate, each
            containing loss metrics, clip rates, and hyperparameters.
        objective: Selection objective ('robust', 'mean_kl', 'mean_mse').
        max_k_clip_rate: Maximum allowed K clip rate for feasibility (robust).
        max_v_clip_rate: Maximum allowed V clip rate for feasibility (robust).
        loss_function: The loss function used to generate trials ('kl' or 'mse').
            Must match the loss_function used during evaluate_quant_candidate.

    Returns:
        Tuple of (best_trial_dict, selection_metadata_dict).

    Raises:
        ValueError: If trials is empty.
        KeyError: If expected loss keys are missing from trial data.
    """
    if not trials:
        raise ValueError("No candidate trials found for calibration selection.")

    # CAL-044: Validate that objective and loss_function are consistent.
    # Explicit mean_kl / mean_mse objectives imply a specific loss_function;
    # a mismatch means the trial dicts won't contain the expected keys.
    if objective == "mean_kl" and loss_function != "kl":
        raise ValueError(
            f"objective='mean_kl' requires loss_function='kl', got '{loss_function}'. "
            "Trial data does not contain 'mean_kl' keys when generated with MSE loss."
        )
    if objective == "mean_mse" and loss_function != "mse":
        raise ValueError(
            f"objective='mean_mse' requires loss_function='mse', got '{loss_function}'. "
            "Trial data does not contain 'mean_mse' keys when generated with KL loss."
        )

    # Determine loss metric key prefix based on objective and loss_function.
    # For explicit mean_kl/mean_mse objectives, the key is in the objective name.
    # For "robust", derive from loss_function.
    # WARNING: KL and MSE produce different numeric scales. Rankings are ONLY
    # meaningful when all trials use the same loss_function. Mixing trials from
    # different loss functions in one select_best_trial call will produce
    # misleading rankings.
    if objective == "mean_mse" or (objective == "robust" and loss_function == "mse"):
        mean_key, p95_key = "mean_mse", "p95_mse"
    else:
        mean_key, p95_key = "mean_kl", "p95_kl"

    # Validate that loss keys exist in trial data.
    if trials and mean_key not in trials[0]:
        available = [k for k in trials[0] if k.startswith("mean_") or k.startswith("p95_")]
        raise KeyError(
            f"Loss key '{mean_key}' not found in trial data. "
            f"Available loss keys: {available}. "
            f"Check that --loss_function matches the objective."
        )

    # CAL-020: Use log2(group_size) as tiebreaker instead of raw group_size
    # to avoid scale-dependent bias. Raw values (16, 32, 64, 128) have
    # non-uniform spacing that unfairly penalises larger group sizes in
    # ascending sort. log2 normalises to (4, 5, 6, 7).
    import math

    def _gs_norm(x):
        return math.log2(max(x["group_size"], 1))

    if objective in ("mean_kl", "mean_mse"):
        ranked = sorted(
            trials,
            key=lambda x: (
                x[mean_key],
                x[p95_key],
                x["k_clip_rate"] + x["v_clip_rate"],
                _gs_norm(x),
                x["clip_percentile"],
            ),
        )
        return ranked[0], {
            "mode": objective,
            "constraints": None,
            "num_feasible": len(trials),
            "num_trials": len(trials),
        }

    feasible = [
        t
        for t in trials
        if t["k_clip_rate"] <= max_k_clip_rate and t["v_clip_rate"] <= max_v_clip_rate
    ]

    if feasible:
        ranked = sorted(
            feasible,
            key=lambda x: (
                x[p95_key],
                x[mean_key],
                x["v_rel_l2_mean"],
                _gs_norm(x),
                x["clip_percentile"],
            ),
        )
        return ranked[0], {
            "mode": "robust_feasible",
            "constraints": {
                "max_k_clip_rate": max_k_clip_rate,
                "max_v_clip_rate": max_v_clip_rate,
            },
            "num_feasible": len(feasible),
            "num_trials": len(trials),
        }

    ranked = sorted(
        trials,
        key=lambda x: (
            x["k_clip_rate"] + x["v_clip_rate"],
            x[p95_key],
            x[mean_key],
            x["v_rel_l2_mean"],
            _gs_norm(x),
            x["clip_percentile"],
        ),
    )
    return ranked[0], {
        "mode": "robust_fallback_clip_first",
        "constraints": {
            "max_k_clip_rate": max_k_clip_rate,
            "max_v_clip_rate": max_v_clip_rate,
        },
        "num_feasible": 0,
        "num_trials": len(trials),
    }


def collect_absmax_samples(
    kv_samples: List[List[torch.Tensor]],
    group_size: int,
) -> List[List[torch.Tensor]]:
    """
    Collect per-layer absmax-per-group statistics from cached KV tensors.

    kv_samples: list over samples -> list over layers -> tensor [kv_heads, seq, head_dim]
    Returns: list over layers -> list over samples -> tensor [kv_heads, num_groups]
    """
    if not kv_samples:
        return []
    num_layers = len(kv_samples[0])
    out: List[List[torch.Tensor]] = [[] for _ in range(num_layers)]
    for sample_idx in range(len(kv_samples)):
        for layer_idx in range(num_layers):
            out[layer_idx].append(compute_absmax_per_group(kv_samples[sample_idx][layer_idx], group_size))
    return out


def scales_from_absmax_samples(
    absmax_samples: List[List[torch.Tensor]],
    clip_percentile: float,
    qmax: int,
) -> List[torch.Tensor]:
    """Compute per-layer static scales from sample-level absmax statistics.

    CAL-024: The percentile operates over *sample-level* absmax values (i.e.
    the max within each calibration sample's sequence). This differs from the
    inference path which applies percentile clipping at the *token level*.
    The two "populations" are inherently different and cannot be directly
    aligned; this is a known design trade-off of static calibration.
    """
    scales: List[torch.Tensor] = []
    for layer_idx in range(len(absmax_samples)):
        # CAL-041: Guard against empty sample list for a layer, which would
        # cause torch.stack([]) to raise RuntimeError.
        if not absmax_samples[layer_idx]:
            raise ValueError(
                f"absmax_samples[{layer_idx}] is empty — no calibration "
                f"samples collected for layer {layer_idx}. Check that "
                f"num_layers matches the model."
            )
        # torch.quantile requires float32/float64
        stack = torch.stack(absmax_samples[layer_idx], dim=0).float()
        absmax = torch.quantile(stack, clip_percentile / 100.0, dim=0)
        scales.append(absmax.clamp(min=1e-5) / float(qmax))
    return scales


def calibrate_v_path_percentile(
    v_samples: list,
    q_samples: list,
    k_samples: list,
    num_heads: int,
    num_kv_heads: int,
    head_dim: int,
    percentile_candidates: list,
    quant_bits: int = 4,
) -> tuple:
    """
    Search optimal v_percentile for KIVI-style per-token V quantization.

    Uses attention-weighted V reconstruction error as proxy for token-level CE.
    For each candidate v_percentile:
    1. Quantize/dequantize V with per-token asymmetric at that percentile
    2. Compute attention weights A = softmax(Q K^T / sqrt(d))
    3. Compute ||A * (V - V_q)||^2 as output perturbation proxy
    4. Average over samples and layers

    Args:
        v_samples: [n_samples][n_layers] -> [kv_heads, seq, head_dim]
        q_samples: [n_samples][n_layers] -> [num_heads, head_dim]
        k_samples: [n_samples][n_layers] -> [kv_heads, seq, head_dim]
        num_heads: Number of query heads
        num_kv_heads: Number of KV heads
        head_dim: Head dimension
        percentile_candidates: List of v_percentile values to search
        quant_bits: 4 or 8

    Returns:
        (best_percentile, results_dict) where results_dict has per-candidate metrics
    """
    from src.quant.asymmetric_quant import (
        quantize_asymmetric_per_token,
        dequantize_asymmetric_per_token,
    )

    n_rep = num_heads // num_kv_heads
    n_samples = len(v_samples)
    n_layers = len(v_samples[0]) if v_samples else 0
    sm_scale = 1.0 / (head_dim ** 0.5)

    results = {}
    for pct in percentile_candidates:
        total_weighted_mse = 0.0
        total_v_sqnr = 0.0
        count = 0

        for s_idx in range(n_samples):
            for l_idx in range(n_layers):
                v = v_samples[s_idx][l_idx]  # [kv_heads, seq, head_dim]
                if v.ndim != 3:
                    continue

                # Quantize V with per-token asymmetric at this percentile
                v_4d = v.unsqueeze(0).float()  # [1, kv_heads, seq, head_dim]
                q_v, v_scale, v_zp = quantize_asymmetric_per_token(
                    v_4d, quant_bits=quant_bits, percentile=pct
                )
                v_deq = dequantize_asymmetric_per_token(q_v, v_scale, v_zp)
                v_deq = v_deq.squeeze(0)  # [kv_heads, seq, head_dim]

                # V reconstruction error (simple SQNR)
                v_f = v.float()
                v_d = v_deq.float()
                noise = (v_f - v_d).pow(2).mean().item()
                signal = v_f.pow(2).mean().item()
                if noise > 1e-20:
                    sqnr = 10.0 * torch.log10(torch.tensor(signal / noise)).item()
                else:
                    sqnr = 100.0
                total_v_sqnr += sqnr

                # Attention-weighted output perturbation (if Q/K available)
                if q_samples and k_samples and s_idx < len(q_samples) and l_idx < len(q_samples[s_idx]):
                    q = q_samples[s_idx][l_idx].float()  # [num_heads, head_dim]
                    k = k_samples[s_idx][l_idx].float()  # [kv_heads, seq, head_dim]

                    # GQA: repeat K/V to match Q heads
                    if n_rep > 1:
                        k_exp = k.repeat_interleave(n_rep, dim=0)  # [num_heads, seq, head_dim]
                        v_f_exp = v_f.repeat_interleave(n_rep, dim=0)
                        v_d_exp = v_d.repeat_interleave(n_rep, dim=0)
                    else:
                        k_exp = k
                        v_f_exp = v_f
                        v_d_exp = v_d

                    # Compute attention weights: A = softmax(q @ k^T * sm_scale)
                    # q: [num_heads, head_dim], k_exp: [num_heads, seq, head_dim]
                    logits = torch.einsum("hd,hsd->hs", q, k_exp) * sm_scale
                    attn_weights = torch.softmax(logits, dim=-1)  # [num_heads, seq]

                    # Output perturbation: ||A * delta_V||
                    delta_v = v_f_exp - v_d_exp  # [num_heads, seq, head_dim]
                    # Weighted delta: attn_weights[:, :, None] * delta_v
                    weighted_delta = attn_weights.unsqueeze(-1) * delta_v  # [num_heads, seq, head_dim]
                    # Output perturbation = sum over seq
                    output_perturb = weighted_delta.sum(dim=1).pow(2).mean().item()  # scalar
                    total_weighted_mse += output_perturb

                count += 1

        # CAL-054: count=0 means all samples were skipped — return inf, not 0.0
        if count == 0:
            avg_sqnr = float("inf")
            avg_weighted_mse = float("inf")
        else:
            avg_sqnr = total_v_sqnr / count
            avg_weighted_mse = total_weighted_mse / count

        results[pct] = {
            "v_percentile": pct,
            "avg_v_sqnr_db": round(avg_sqnr, 2),
            "avg_weighted_output_mse": avg_weighted_mse,
            "n_evaluations": count,
        }

    # Select best percentile by minimum weighted output MSE (or maximum SQNR as fallback)
    best_pct = min(
        percentile_candidates,
        key=lambda p: results[p]["avg_weighted_output_mse"]
        if results[p]["avg_weighted_output_mse"] > 0
        else -results[p]["avg_v_sqnr_db"],
    )

    return best_pct, results


def validate_group_size(head_dim: int, group_size: int, name: str) -> None:
    if group_size <= 0:
        raise ValueError(f"{name} must be > 0, got {group_size}.")
    if head_dim % group_size != 0:
        raise ValueError(
            f"{name} must divide head_dim exactly. head_dim={head_dim}, {name}={group_size}."
        )


def calibrate_k_path_percentile_asymmetric(
    q_samples: list,
    k_samples: list,
    num_heads: int,
    num_kv_heads: int,
    head_dim: int,
    percentile_candidates: list,
    quant_bits: int = 4,
) -> tuple:
    """
    Search optimal k_percentile for per-channel asymmetric K quantization.

    Uses attention KL divergence as objective:
    For each candidate k_percentile:
    1. Quantize/dequantize K with per-channel asymmetric at that percentile
    2. Compute attention weights with quantized K
    3. Compute KL(p_ref || p_quant)
    4. Average over samples, layers, and heads

    Args:
        q_samples: [n_samples][n_layers] -> [num_heads, head_dim]
        k_samples: [n_samples][n_layers] -> [kv_heads, seq, head_dim]
        num_heads: Number of query heads
        num_kv_heads: Number of KV heads
        head_dim: Head dimension
        percentile_candidates: List of k_percentile values to search
        quant_bits: 4 or 8

    Returns:
        (best_percentile, results_dict)
    """
    from src.quant.asymmetric_quant import (
        quantize_asymmetric_per_channel,
        dequantize_asymmetric_per_channel,
    )

    n_rep = num_heads // num_kv_heads
    n_samples = len(q_samples)
    n_layers = len(q_samples[0]) if q_samples else 0
    sm_scale = 1.0 / (head_dim ** 0.5)
    eps = 1e-6

    results = {}
    for pct in percentile_candidates:
        total_kl = 0.0
        count = 0

        for s_idx in range(n_samples):
            for l_idx in range(n_layers):
                q = q_samples[s_idx][l_idx].float()  # [num_heads, head_dim]
                k = k_samples[s_idx][l_idx].float()  # [kv_heads, seq, head_dim]
                if q.ndim != 2 or k.ndim != 3:
                    continue

                # Quantize K with per-channel asymmetric
                k_4d = k.unsqueeze(0)  # [1, kv_heads, seq, head_dim]
                q_k, k_scale, k_zp = quantize_asymmetric_per_channel(
                    k_4d, quant_bits=quant_bits, percentile=pct
                )
                k_deq = dequantize_asymmetric_per_channel(q_k, k_scale, k_zp)
                k_deq = k_deq.squeeze(0)  # [kv_heads, seq, head_dim]

                # GQA expansion
                if n_rep > 1:
                    k_ref = k.repeat_interleave(n_rep, dim=0)
                    k_q = k_deq.repeat_interleave(n_rep, dim=0)
                else:
                    k_ref = k
                    k_q = k_deq

                # Compute attention distributions
                logits_ref = torch.einsum("hd,hsd->hs", q, k_ref) * sm_scale
                logits_quant = torch.einsum("hd,hsd->hs", q, k_q) * sm_scale
                p_ref = torch.softmax(logits_ref, dim=-1).clamp(min=eps)
                p_quant = torch.softmax(logits_quant, dim=-1).clamp(min=eps)

                # KL divergence
                kl = (p_ref * (p_ref.log() - p_quant.log())).sum(dim=-1).mean().item()
                total_kl += kl
                count += 1

        # CAL-054: count=0 → all samples skipped, return inf to poison selection
        avg_kl = total_kl / count if count > 0 else float("inf")
        results[pct] = {
            "k_percentile": pct,
            "avg_kl": avg_kl,
            "n_evaluations": count,
        }

    # Select best percentile by minimum KL
    best_pct = min(percentile_candidates, key=lambda p: results[p]["avg_kl"])
    return best_pct, results


def main():
    parser = argparse.ArgumentParser(description="Behavior-aligned calibration for KV cache quantization")
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument(
        "--loss_function",
        type=str,
        default="kl",
        choices=["kl", "mse"],
        help=(
            "Loss function for calibration: "
            "kl=KL divergence between attention distributions (default); "
            "mse=mean squared error between attention distributions."
        ),
    )
    parser.add_argument(
        "--model_revision",
        type=str,
        default=None,
        help="Optional model revision (commit hash/tag) for strict reproducibility.",
    )
    # CAL-038: Default must match get_calibration_dataset(n_samples=128)
    # to avoid silent sample-count mismatch between CLI and function.
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--seq_len", type=int, default=512)
    parser.add_argument("--out_dir", type=str, default="results/calibration")
    parser.add_argument(
        "--calib_out",
        type=str,
        default=None,
        help=(
            "Output path for calibration JSON. "
            "Defaults to artifacts/kv_calib_{loss_function}.json."
        ),
    )
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--run_name", type=str, default=None)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument(
        "--quant_bits",
        type=int,
        default=8,
        choices=[4, 8],
        help="Quantization bits for calibration scale generation.",
    )
    parser.add_argument(
        "--int4_search",
        action="store_true",
        default=False,
        help="Shortcut: enable INT4 calibration/search (equivalent to --quant_bits 4).",
    )
    parser.add_argument(
        "--int4_outlier_ratio",
        type=float,
        default=0.0,
        help=(
            "Outlier-rescue ratio in [0,1]. Top-ratio largest group magnitudes use dynamic scale "
            "during trial evaluation."
        ),
    )
    parser.add_argument(
        "--int4_mixed_rescue",
        action="store_true",
        default=False,
        help="When enabled, also apply outlier rescue to V during candidate evaluation.",
    )
    parser.add_argument("--clip_percentile_k", type=float, default=99.9)
    parser.add_argument("--clip_percentile_v", type=float, default=99.9)
    parser.add_argument("--group_size_k", type=int, default=32)
    parser.add_argument("--group_size_v", type=int, default=32)
    parser.add_argument(
        "--search",
        action="store_true",
        help=(
            "Search over (clip_percentile, group_size). "
            "By default uses a robust objective (KL + clipping constraints)."
        ),
    )
    parser.add_argument(
        "--search_group_sizes",
        type=str,
        default="16,32,64,128",
        help="Comma-separated group_size candidates (applied to both K and V).",
    )
    parser.add_argument(
        "--search_clip_percentiles",
        type=str,
        default="99.0,99.5,99.9,100.0",
        help="Comma-separated clip_percentile candidates (applied to both K and V).",
    )
    parser.add_argument(
        "--search_outlier_ratios",
        type=str,
        default="0,0.0025,0.005,0.01",
        help=(
            "Comma-separated outlier rescue ratios for INT4 search. "
            "Ignored for INT8 search."
        ),
    )
    parser.add_argument(
        "--search_objective",
        type=str,
        default="robust",
        choices=["robust", "mean_kl", "mean_mse"],
        help=(
            "Selection objective: robust=prefer low p95 loss under clip-rate constraints; "
            "mean_kl=backward-compatible pure mean KL ranking; "
            "mean_mse=pure mean MSE ranking."
        ),
    )
    parser.add_argument(
        "--search_max_k_clip_rate",
        type=float,
        default=0.01,
        help="For robust objective: max allowed K clip rate (fraction) for feasible candidates.",
    )
    parser.add_argument(
        "--search_max_v_clip_rate",
        type=float,
        default=0.01,
        help="For robust objective: max allowed V clip rate (fraction) for feasible candidates.",
    )
    parser.add_argument(
        "--inv_tau_candidates",
        type=str,
        default="0.5,0.7,0.85,1.0,1.2,1.5,2.0",
    )
    parser.add_argument(
        "--v_calibration_mode",
        type=str,
        default="shared",
        choices=["shared", "token_ce", "token_kl"],
        help=(
            "V-path calibration mode. 'shared' uses the same attention-KL objective "
            "for K and V (default, current behavior). 'token_ce' independently "
            "calibrates V using attention-weighted output perturbation as proxy for "
            "next-token CE. 'token_kl' is reserved for future token-logits KL."
        ),
    )
    parser.add_argument(
        "--v_percentile_candidates",
        type=str,
        default="95.0,97.0,99.0,99.5,99.9,100.0",
        help="V-path percentile candidates for token_ce/token_kl calibration.",
    )
    parser.add_argument(
        "--role_aware_axes",
        action="store_true",
        default=False,
        help=(
            "Role-aware asymmetric calibration mode. "
            "Searches k_percentile and v_percentile on per-channel K / per-token V "
            "asymmetric axes (KIVI-style format), then searches inv_tau on the "
            "asymmetric-quantized K. Implies --quant_bits 4. "
            "Output JSON has 'role_aware' section with k_percentile, v_percentile, inv_tau."
        ),
    )
    parser.add_argument(
        "--role_aware_k_percentile_candidates",
        type=str,
        default="95.0,97.0,99.0,99.5,99.9,100.0",
        help="K-path percentile candidates for role_aware_axes mode.",
    )
    args = parser.parse_args()
    if args.int4_search:
        args.quant_bits = 4
    if args.role_aware_axes:
        args.quant_bits = 4
        # Force v_calibration_mode to token_ce for role-aware V percentile search
        if args.v_calibration_mode == "shared":
            args.v_calibration_mode = "token_ce"

    if args.config and args.run_name:
        cfg = load_config(args.config)
        resolved = resolve_run_config(cfg, args.run_name)
        # CAL-023: Track quant_bits before config override to detect silent changes.
        quant_bits_before = args.quant_bits
        for key, value in resolved.items():
            if value is not None:
                setattr(args, key, value)
        if args.quant_bits != quant_bits_before:
            import warnings
            warnings.warn(
                f"Config override changed quant_bits from {quant_bits_before} to "
                f"{args.quant_bits} (run_name={args.run_name!r}). "
                "This overrides --int4_search / --quant_bits CLI flags.",
                UserWarning,
            )

        quant_defaults = cfg.get("runtime", {}).get("quant_defaults", {})
        run_entry = None
        for entry in cfg.get("matrix", []):
            if entry.get("run_name") == args.run_name:
                run_entry = entry
                break
        if run_entry:
            clip_k, clip_v, group_k, group_v = resolve_kv_params(run_entry, quant_defaults)
            args.clip_percentile_k = clip_k
            args.clip_percentile_v = clip_v
            args.group_size_k = group_k
            args.group_size_v = group_v

    qmax = 127 if int(args.quant_bits) == 8 else 7
    if args.int4_outlier_ratio < 0.0 or args.int4_outlier_ratio > 1.0:
        raise ValueError(
            f"--int4_outlier_ratio must be in [0,1], got {args.int4_outlier_ratio}"
        )
    # CAL-045: Validate clip_percentile range to avoid opaque torch.quantile errors.
    for _cp_name in ("clip_percentile_k", "clip_percentile_v"):
        _cp_val = getattr(args, _cp_name, 99.9)
        if _cp_val is not None and (_cp_val < 0.0 or _cp_val > 100.0):
            raise ValueError(f"--{_cp_name} must be in [0, 100], got {_cp_val}")
    # CAL-046: Validate inv_tau_candidates are positive (negative inverts softmax).
    _inv_tau_str = getattr(args, "inv_tau_candidates", "1.0")
    _inv_tau_vals = [float(x) for x in str(_inv_tau_str).split(",") if x.strip()]
    if any(v <= 0 for v in _inv_tau_vals):
        raise ValueError(
            f"All inv_tau_candidates must be positive, got {_inv_tau_vals}"
        )

    set_seed(seed=args.seed, deterministic=True)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Default output path reflects loss function to avoid overwriting.
    if args.calib_out is None:
        args.calib_out = f"artifacts/kv_calib_{args.loss_function}.json"
    calib_out_path = Path(args.calib_out)
    calib_out_path.parent.mkdir(parents=True, exist_ok=True)

    # CAL-007: Warn if default output path doesn't match generate_loop.py defaults.
    # generate_loop.py expects:
    #   int8_ours  -> artifacts/kv_calib_kl.json
    #   int4_ours  -> artifacts/kv_calib_kl_int4_selected.json
    # If the user didn't set --calib_out explicitly, check for mismatches.
    _gl_int8_default = "artifacts/kv_calib_kl.json"
    _gl_int4_default = "artifacts/kv_calib_kl_int4_selected.json"
    _calib_out_str = str(calib_out_path)
    if _calib_out_str not in (_gl_int8_default, _gl_int4_default):
        import warnings
        warnings.warn(
            f"Calibration output path '{_calib_out_str}' does not match "
            f"generate_loop.py defaults (int8_ours: '{_gl_int8_default}', "
            f"int4_ours: '{_gl_int4_default}'). "
            "You will need to pass --calib_file explicitly when running "
            "generate_loop, or rename/symlink the output file.",
            UserWarning,
        )

    print(f"Loading {args.model_id}...")
    model_path = resolve_pretrained_path(args.model_id, revision=args.model_revision)
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, revision=args.model_revision, trust_remote_code=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto",
        revision=args.model_revision,
        trust_remote_code=True,
    )
    model.eval()

    dataset = get_calibration_dataset(tokenizer, args.samples, args.seq_len)
    # CAL-032: The getattr defaults (28, 12, 2, 1536) match
    # Qwen2.5-1.5B-Instruct specifically.  They are only hit if the model
    # config object is missing the attribute (extremely unlikely for any
    # Transformers-supported model).  For the other target models the
    # attributes are always present, so the defaults are never used.
    # If you add a model whose config genuinely lacks these fields, update
    # the defaults or add explicit per-model dispatch.
    num_layers = getattr(model.config, "num_hidden_layers", 28)
    num_heads = getattr(model.config, "num_attention_heads", 12)
    num_kv_heads = getattr(model.config, "num_key_value_heads", 2)
    head_dim = getattr(model.config, "hidden_size", 1536) // num_heads

    # Collect samples
    q_samples: List[List[torch.Tensor]] = []
    k_samples: List[List[torch.Tensor]] = []
    v_samples: List[List[torch.Tensor]] = []

    print("Collecting calibration samples...")
    with torch.no_grad():
        for input_ids in tqdm(dataset, desc="Calibration samples"):
            input_ids = input_ids.to(model.device)
            outputs = model(input_ids, use_cache=True, output_hidden_states=True)
            hidden_states = outputs.hidden_states
            past_key_values = outputs.past_key_values
            if not isinstance(past_key_values, tuple) and hasattr(
                past_key_values, "to_legacy_cache"
            ):
                past_key_values = past_key_values.to_legacy_cache()

            q_per_layer = []
            k_per_layer = []
            v_per_layer = []

            for layer_idx in range(num_layers):
                # CAL-031: model.model.layers[i] is intentionally hardcoded.
                # All three target models (Qwen2.5-1.5B-Instruct,
                # Qwen2.5-7B-Instruct, LLaMA-3.1-8B-Instruct) use the same
                # HuggingFace architecture attribute path:
                #   model.model.layers[i].self_attn
                # If a future model uses a different path, this line must be
                # updated (or a model-family dispatch added).
                layer = model.model.layers[layer_idx]
                attn = layer.self_attn
                # CAL-014 audit (2026-03-17): hidden_states[layer_idx] is correct.
                # HF outputs.hidden_states is a tuple:
                #   [0] = embedding output (input to layer 0)
                #   [i] = output of layer i-1 = input to layer i
                # So hidden_states[layer_idx] gives the true input to layer_idx.
                # No off-by-one: layer 0 gets embedding, layer N gets layer N-1 output.
                hs_last = hidden_states[layer_idx][:, -1:, :]

                # CAL-019: Apply input_layernorm before q_proj to match the
                # real forward pass.  DecoderLayer does:
                #   normed = input_layernorm(hidden_states)
                #   q, k, v = self_attn(normed, ...)
                # Without layernorm, Q is computed from un-normalized hidden
                # states, producing a distorted attention distribution.
                normed_hs = layer.input_layernorm(hs_last)
                q = attn.q_proj(normed_hs)
                bsz = q.shape[0]
                q = q.view(bsz, 1, num_heads, head_dim).transpose(1, 2)

                # Optional q_norm (model-dependent, e.g. Gemma).
                q_norm_fn = getattr(attn, "q_norm", None)
                if q_norm_fn is not None:
                    q = q_norm_fn(q)

                # CAL-020: Apply RoPE to Q.  K in past_key_values already has
                # RoPE applied by the model's forward pass.  Without RoPE on Q,
                # the Q·K^T dot product lacks proper positional encoding and the
                # calibrated inv_tau optimises for a wrong attention distribution.
                seq_len_val = hidden_states[layer_idx].shape[1]
                pos_ids = torch.tensor(
                    [[seq_len_val - 1]], device=q.device, dtype=torch.long
                )
                rope_cos, rope_sin = _get_rope_for_position(attn, q, pos_ids, model_backbone=model.model)
                if rope_cos is not None and rope_sin is not None:
                    q = _apply_rope_to_q(q, rope_cos, rope_sin)
                elif layer_idx == 0:
                    import warnings
                    warnings.warn(
                        "Could not obtain RoPE cos/sin for calibration Q vectors. "
                        "Calibration quality may be degraded because Q lacks "
                        "positional encoding while K already has it.",
                        RuntimeWarning,
                    )

                # CAL-040: Assert bsz==1 instead of squeeze, which silently
                # becomes a no-op when bsz>1, leaving an extra batch dimension
                # that corrupts downstream attention computation.
                assert bsz == 1, (
                    f"Calibration expects bsz=1, got bsz={bsz}. "
                    "Multi-sample batching is not supported in calibration."
                )
                # CAL-015: After the bsz==1 assertion, squeeze(0) is safe because
                # dimension 0 is guaranteed to be size 1. We use explicit indexing
                # for the q sequence dimension ([:, :, 0, :]) and squeeze only the
                # batch dim. Shape transformations:
                #   q: [1, num_heads, seq, head_dim] -> [:,:,0,:] -> [1, num_heads, head_dim] -> squeeze(0) -> [num_heads, head_dim]
                #   k: [1, kv_heads, seq, head_dim] -> squeeze(0) -> [kv_heads, seq, head_dim]
                #   v: [1, kv_heads, seq, head_dim] -> squeeze(0) -> [kv_heads, seq, head_dim]
                q_last = q[:, :, 0, :].squeeze(0).cpu()  # [num_heads, head_dim]

                k = past_key_values[layer_idx][0].squeeze(0).cpu()  # [kv_heads, seq, head_dim]
                v = past_key_values[layer_idx][1].squeeze(0).cpu()

                q_per_layer.append(q_last)
                k_per_layer.append(k)
                v_per_layer.append(v)

            q_samples.append(q_per_layer)
            k_samples.append(k_per_layer)
            v_samples.append(v_per_layer)

    selection = None
    if args.search:
        group_candidates_raw = [int(x) for x in args.search_group_sizes.split(",") if x.strip()]
        clip_candidates = [float(x) for x in args.search_clip_percentiles.split(",") if x.strip()]
        outlier_ratio_candidates = [float(x) for x in args.search_outlier_ratios.split(",") if x.strip()]
        if not group_candidates_raw or not clip_candidates:
            raise ValueError("Search candidates cannot be empty.")
        if int(args.quant_bits) != 4:
            outlier_ratio_candidates = [0.0]
        if not outlier_ratio_candidates:
            outlier_ratio_candidates = [float(args.int4_outlier_ratio)]

        # Filter invalid group sizes early for clearer diagnostics.
        group_candidates = []
        skipped_groups = []
        for group_size in group_candidates_raw:
            if group_size > 0 and head_dim % group_size == 0:
                group_candidates.append(group_size)
            else:
                skipped_groups.append(group_size)
        if not group_candidates:
            raise ValueError(
                f"No valid search group sizes for head_dim={head_dim}. "
                f"Provided={group_candidates_raw}"
            )
        if skipped_groups:
            print(
                f"Skipping invalid group_size candidates (must divide head_dim={head_dim}): {skipped_groups}"
            )

        print(
            "Selecting (clip_percentile, group_size) with "
            f"objective={args.search_objective}..."
        )
        trials = []

        # Cache absmax stats per group_size to avoid recomputation.
        k_absmax_cache = {}
        v_absmax_cache = {}
        for group_size in group_candidates:
            k_absmax_cache[group_size] = collect_absmax_samples(k_samples, group_size)
            v_absmax_cache[group_size] = collect_absmax_samples(v_samples, group_size)

        for group_size in group_candidates:
            absmax_samples_k = k_absmax_cache[group_size]
            absmax_samples_v = v_absmax_cache[group_size]
            for clip_p in clip_candidates:
                v_scales_candidate = scales_from_absmax_samples(absmax_samples_v, clip_p, qmax=qmax)
                k_scales_candidate = scales_from_absmax_samples(absmax_samples_k, clip_p, qmax=qmax)
                for outlier_ratio in outlier_ratio_candidates:
                    stats = evaluate_quant_candidate(
                        q_samples=q_samples,
                        k_samples=k_samples,
                        v_samples=v_samples,
                        k_scales=k_scales_candidate,
                        v_scales=v_scales_candidate,
                        num_heads=num_heads,
                        num_kv_heads=num_kv_heads,
                        head_dim=head_dim,
                        group_size_k=group_size,
                        group_size_v=group_size,
                        qmax=qmax,
                        outlier_rescue_ratio=float(outlier_ratio),
                        mixed_rescue=bool(args.int4_mixed_rescue),
                        loss_function=args.loss_function,
                    )
                    trial = {
                        "group_size": group_size,
                        "clip_percentile": clip_p,
                        "outlier_rescue_ratio": float(outlier_ratio),
                        "mixed_rescue": int(bool(args.int4_mixed_rescue)),
                        **stats,
                    }
                    trial["feasible"] = (
                        trial["k_clip_rate"] <= args.search_max_k_clip_rate
                        and trial["v_clip_rate"] <= args.search_max_v_clip_rate
                    )
                    trials.append(trial)
                    loss_pfx = "mse" if args.loss_function == "mse" else "kl"
                    print(
                        "  "
                        f"group_size={group_size:>4} clip={clip_p:>5} "
                        f"outlier_ratio={outlier_ratio:.4f}: "
                        f"mean_{loss_pfx}={trial[f'mean_{loss_pfx}']:.6f} "
                        f"p95_{loss_pfx}={trial[f'p95_{loss_pfx}']:.6f} "
                        f"k_clip={trial['k_clip_rate']:.4f} v_clip={trial['v_clip_rate']:.4f} "
                        f"v_rel_l2={trial['v_rel_l2_mean']:.6f}"
                    )

        best, selection_meta = select_best_trial(
            trials=trials,
            objective=args.search_objective,
            max_k_clip_rate=args.search_max_k_clip_rate,
            max_v_clip_rate=args.search_max_v_clip_rate,
            loss_function=args.loss_function,
        )
        args.group_size_k = int(best["group_size"])
        args.group_size_v = int(best["group_size"])
        args.clip_percentile_k = float(best["clip_percentile"])
        args.clip_percentile_v = float(best["clip_percentile"])
        args.int4_outlier_ratio = float(best.get("outlier_rescue_ratio", args.int4_outlier_ratio))
        args.int4_mixed_rescue = bool(best.get("mixed_rescue", args.int4_mixed_rescue))

        # CAL-014: The sort key uses absolute loss values. Since MSE and KL
        # operate on different numeric scales (MSE ~ 1e-8..1e-3, KL ~ 1e-5..1e-1),
        # the search grid exploration and ranking behaviour differ between the two.
        # For example, a group_size that produces tiny MSE differences may show
        # large KL differences, leading to different "best" candidates.
        # This is expected; users should pick one loss function consistently.
        #
        # CAL-036: CSV ranking now uses the SAME sort key as the selection mode
        # from select_best_trial(), ensuring JSON "best" == CSV rank=1.
        # An "is_selected" column explicitly marks the chosen trial.
        loss_pfx_sort = "mse" if args.loss_function == "mse" else "kl"
        _sel_mode = selection_meta["mode"]

        def _csv_sort_key(x):
            """Unified sort key matching select_best_trial logic."""
            import math
            # CAL-020: Use log2(group_size) to normalize tiebreaker scale,
            # avoiding bias toward small group_size from raw integer ordering.
            _gs_norm = math.log2(max(x["group_size"], 1))
            if _sel_mode == "robust_fallback_clip_first":
                return (
                    x["k_clip_rate"] + x["v_clip_rate"],
                    x[f"p95_{loss_pfx_sort}"],
                    x[f"mean_{loss_pfx_sort}"],
                    x["v_rel_l2_mean"],
                    _gs_norm,
                    x["clip_percentile"],
                )
            elif _sel_mode in ("mean_kl", "mean_mse"):
                return (
                    x[f"mean_{loss_pfx_sort}"],
                    x[f"p95_{loss_pfx_sort}"],
                    x["k_clip_rate"] + x["v_clip_rate"],
                    _gs_norm,
                    x["clip_percentile"],
                )
            else:  # robust_feasible (default)
                return (
                    x[f"p95_{loss_pfx_sort}"],
                    x[f"mean_{loss_pfx_sort}"],
                    x["v_rel_l2_mean"],
                    _gs_norm,
                    x["clip_percentile"],
                )

        trials_sorted = sorted(trials, key=_csv_sort_key)
        # Identify the selected best trial for the is_selected column.
        _best_id = id(best)
        for rank_idx, trial in enumerate(trials_sorted, start=1):
            trial["rank"] = rank_idx

        trials_csv_path = out_dir / "search_trials.csv"
        with open(trials_csv_path, "w") as f:
            f.write(
                "rank,group_size,clip_percentile,outlier_rescue_ratio,mixed_rescue,"
                f"mean_{loss_pfx_sort},p95_{loss_pfx_sort},max_{loss_pfx_sort},"
                "k_clip_rate,v_clip_rate,v_rel_l2_mean,feasible,is_selected\n"
            )
            for t in trials_sorted:
                f.write(
                    f"{t['rank']},{t['group_size']},{t['clip_percentile']},"
                    f"{t.get('outlier_rescue_ratio', 0.0)},{t.get('mixed_rescue', 0)},"
                    f"{t[f'mean_{loss_pfx_sort}']},{t[f'p95_{loss_pfx_sort}']},"
                    f"{t[f'max_{loss_pfx_sort}']},"
                    f"{t['k_clip_rate']},{t['v_clip_rate']},{t['v_rel_l2_mean']},"
                    f"{int(bool(t['feasible']))},{int(id(t) == _best_id)}\n"
                )
        print(f"Saved search trial metrics to {trials_csv_path}")

        selection = {
            "objective": args.search_objective,
            "constraints": selection_meta["constraints"],
            "selection_mode": selection_meta["mode"],
            "num_feasible": selection_meta["num_feasible"],
            "num_trials": selection_meta["num_trials"],
            "candidates": {
                "group_sizes": group_candidates,
                "clip_percentiles": clip_candidates,
                "outlier_rescue_ratios": outlier_ratio_candidates,
            },
            "best": {
                "group_size": int(best["group_size"]),
                "clip_percentile": float(best["clip_percentile"]),
                "outlier_rescue_ratio": float(best.get("outlier_rescue_ratio", 0.0)),
                "mixed_rescue": bool(best.get("mixed_rescue", 0)),
                f"mean_{loss_pfx_sort}": float(best[f"mean_{loss_pfx_sort}"]),
                f"p95_{loss_pfx_sort}": float(best[f"p95_{loss_pfx_sort}"]),
                f"max_{loss_pfx_sort}": float(best[f"max_{loss_pfx_sort}"]),
                "k_clip_rate": float(best["k_clip_rate"]),
                "v_clip_rate": float(best["v_clip_rate"]),
                "v_rel_l2_mean": float(best["v_rel_l2_mean"]),
            },
            "trials": trials_sorted,
            "trials_csv": str(trials_csv_path),
        }

    # Compute static scales (percentile over sample-wise absmax)
    validate_group_size(head_dim, int(args.group_size_k), "group_size_k")
    validate_group_size(head_dim, int(args.group_size_v), "group_size_v")
    print("Computing static scales...")
    k_absmax_samples = collect_absmax_samples(k_samples, args.group_size_k)
    v_absmax_samples = collect_absmax_samples(v_samples, args.group_size_v)
    k_scales = scales_from_absmax_samples(k_absmax_samples, args.clip_percentile_k, qmax=qmax)
    v_scales = scales_from_absmax_samples(v_absmax_samples, args.clip_percentile_v, qmax=qmax)

    # Compute inv_tau (loss minimization)
    print(f"Computing per-head inv_tau (loss_function={args.loss_function})...")
    inv_tau_candidates = [float(x) for x in args.inv_tau_candidates.split(",") if x.strip()]
    if not inv_tau_candidates:
        raise ValueError(
            "--inv_tau_candidates parsed to empty list. "
            "Provide at least one candidate (e.g. '0.5,1.0,1.5')."
        )
    inv_tau = compute_inv_tau(
        q_samples=q_samples,
        k_samples=k_samples,
        k_scales=k_scales,
        num_heads=num_heads,
        num_kv_heads=num_kv_heads,
        head_dim=head_dim,
        group_size=args.group_size_k,
        inv_tau_candidates=inv_tau_candidates,
        qmax=qmax,
        loss_function=args.loss_function,
    )

    # Role-aware K-path calibration: search k_percentile on per-channel asymmetric axes.
    ra_k_calib_result = None
    ra_k_best_pct = args.clip_percentile_k
    if getattr(args, "role_aware_axes", False):
        ra_k_pct_candidates = [float(x) for x in args.role_aware_k_percentile_candidates.split(",")]
        print(f"\n--- Role-Aware K-path calibration (per-channel asymmetric) ---")
        print(f"Searching k_percentile in {ra_k_pct_candidates}...")
        ra_k_best_pct, ra_k_calib_result = calibrate_k_path_percentile_asymmetric(
            q_samples=q_samples,
            k_samples=k_samples,
            num_heads=num_heads,
            num_kv_heads=num_kv_heads,
            head_dim=head_dim,
            percentile_candidates=ra_k_pct_candidates,
            quant_bits=int(args.quant_bits),
        )
        print(f"Best k_percentile (asymmetric): {ra_k_best_pct}")
        for pct, metrics in ra_k_calib_result.items():
            print(f"  k_pct={pct}: KL={metrics['avg_kl']:.6f}")

    # V-path independent calibration (Phase 1B: KV-RoleAlign).
    # When v_calibration_mode != "shared", search optimal v_percentile for KIVI-style
    # per-token V quantization using attention-weighted output perturbation proxy.
    v_calib_result = None
    v_calib_best_pct = args.clip_percentile_v  # default: use current setting
    if getattr(args, "v_calibration_mode", "shared") in ("token_ce", "token_kl"):
        v_pct_candidates = [float(x) for x in args.v_percentile_candidates.split(",")]
        print(f"\n--- V-path calibration (mode={args.v_calibration_mode}) ---")
        print(f"Searching v_percentile in {v_pct_candidates}...")
        v_calib_best_pct, v_calib_result = calibrate_v_path_percentile(
            v_samples=v_samples,
            q_samples=q_samples,
            k_samples=k_samples,
            num_heads=num_heads,
            num_kv_heads=num_kv_heads,
            head_dim=head_dim,
            percentile_candidates=v_pct_candidates,
            quant_bits=int(args.quant_bits),
        )
        print(f"Best v_percentile: {v_calib_best_pct}")
        for pct, metrics in v_calib_result.items():
            print(f"  v_pct={pct}: SQNR={metrics['avg_v_sqnr_db']:.2f}dB, "
                  f"weighted_MSE={metrics['avg_weighted_output_mse']:.6f}")

    # Save calibration file.
    # CAL-008: loss_function is always included so downstream loaders
    # (e.g. generate_loop.py) can validate compatibility.
    # CAL-033: version=2 indicates postfix-era format with provenance fields.
    #   version=1: original format (no MSE clamping, no provenance).
    #   version=2: adds model_revision, seed, dataset_source, n_samples,
    #              seq_len for audit trail and deterministic reproduction.
    #   version=3: adds k_calibration / v_calibration split for KV-RoleAlign.
    # CAL-013: inv_tau shape is [num_layers, num_heads] and is explicitly
    # recorded so loaders can validate dimensions before use.
    # CAL-043: Provenance fields (dataset_source, seed, n_samples, seq_len)
    # enable downstream audit of calibration determinism.
    use_v3 = getattr(args, "v_calibration_mode", "shared") != "shared"
    calib_payload = {
        "version": 3 if use_v3 else 2,
        "model_id": args.model_id,
        "model_revision": args.model_revision,
        "generated_at": datetime.now().isoformat(),
        "seed": args.seed,
        "loss_function": args.loss_function,
        "quant_bits": int(args.quant_bits),
        "qmax": int(qmax),
        "dataset_source": "wikitext-2-raw-v1",
        "n_samples": args.samples,
        "seq_len": args.seq_len,
        "num_layers": num_layers,
        "num_heads": num_heads,
        "num_kv_heads": num_kv_heads,
        "head_dim": head_dim,
        "clip_percentile_k": args.clip_percentile_k,
        "clip_percentile_v": args.clip_percentile_v,
        "group_size_k": args.group_size_k,
        "group_size_v": args.group_size_v,
        "k_scale": [k.tolist() for k in k_scales],
        "v_scale": [v.tolist() for v in v_scales],
        "inv_tau": inv_tau.tolist(),
        "inv_tau_shape": list(inv_tau.shape),  # [num_layers, num_heads]
        "inv_tau_candidates": inv_tau_candidates,
        "int4_outlier_ratio": float(args.int4_outlier_ratio),
        "int4_mixed_rescue": bool(args.int4_mixed_rescue),
    }
    # v3 schema: split K-path and V-path calibration metadata
    if use_v3:
        calib_payload["k_calibration"] = {
            "method": f"attention_{args.loss_function}",
            "k_percentile": args.clip_percentile_k,
            "inv_tau": inv_tau.tolist(),
        }
        calib_payload["v_calibration"] = {
            "method": args.v_calibration_mode,
            "v_percentile": v_calib_best_pct,
            "search_results": v_calib_result,
        }
    if selection is not None:
        calib_payload["selection"] = selection

    # Role-aware section: consolidated k_percentile + v_percentile + inv_tau
    # for ours_asym / ours_asym_ba modes. This is the primary section read by
    # generate_loop.py when kv_mode in {int4_ours_asym, int4_ours_asym_ba}.
    if getattr(args, "role_aware_axes", False):
        calib_payload["version"] = 4  # v4: role_aware schema
        calib_payload["role_aware"] = {
            "quantization_axes": "per_channel_k_per_token_v",
            "k_percentile": ra_k_best_pct,
            "v_percentile": v_calib_best_pct,
            "inv_tau": inv_tau.tolist(),
            "inv_tau_shape": list(inv_tau.shape),
            "k_search_results": ra_k_calib_result,
            "v_search_results": v_calib_result,
        }

    # CAL-039: Atomic write — use tempfile + os.replace so a crash mid-write
    # cannot leave a truncated/corrupt calibration JSON on disk.
    calib_out_dir = os.path.dirname(str(calib_out_path)) or "."
    fd, tmp_path = tempfile.mkstemp(suffix=".json", dir=calib_out_dir)
    try:
        with os.fdopen(fd, "w") as f:
            # CAL-018: allow_nan=False rejects float('inf')/NaN values that
            # produce non-standard JSON tokens (Infinity/NaN). If a trial
            # returned inf loss (empty loss_values), this catches it here
            # with a clear error rather than writing unparseable JSON.
            json.dump(calib_payload, f, indent=2, allow_nan=False)
        os.replace(tmp_path, str(calib_out_path))
    except BaseException:
        os.unlink(tmp_path)
        raise
    print(f"Saved calibration JSON to {calib_out_path}")

    # Optional: write stats CSV + plot
    csv_path = out_dir / "calibration_stats.csv"
    with open(csv_path, "w") as f:
        f.write("layer,type,global_max,mean_max,std_max\n")
        for idx in range(num_layers):
            k_vals = torch.stack(k_absmax_samples[idx]).numpy()
            v_vals = torch.stack(v_absmax_samples[idx]).numpy()
            f.write(f"{idx},K,{k_vals.max()},{k_vals.mean()},{k_vals.std()}\n")
            f.write(f"{idx},V,{v_vals.max()},{v_vals.mean()},{v_vals.std()}\n")

    # Plot outlier profile
    all_k_absmax = [torch.stack(k_absmax_samples[i]).max().item() for i in range(num_layers)]
    all_v_absmax = [torch.stack(v_absmax_samples[i]).max().item() for i in range(num_layers)]
    plt.figure(figsize=(10, 6))
    plt.plot(list(range(num_layers)), all_k_absmax, label="K AbsMax", marker="o")
    plt.plot(list(range(num_layers)), all_v_absmax, label="V AbsMax", marker="x")
    plt.xlabel("Layer Index")
    plt.ylabel("Absolute Max Value")
    plt.title("KV Cache Outlier Magnitude per Layer (WikiText-2)")
    plt.legend()
    plt.grid(True)
    plot_path = out_dir / "outlier_profile.png"
    plt.savefig(plot_path)
    # CAL-022: Close figure to release memory and avoid matplotlib
    # "too many open figures" warning in loop/test environments.
    plt.close()

    hardware = get_hardware_info()
    snapshot = build_config_snapshot(
        script_name=os.path.basename(__file__),
        args=args,
        extra={
            "hardware": f"{hardware['gpu']} ({hardware['gpu_memory']})",
            "outputs": {
                "calibration_stats": str(csv_path),
                "outlier_profile": str(plot_path),
                "calibration_json": str(calib_out_path),
                "search_trials": str(out_dir / "search_trials.csv") if args.search else None,
            },
        },
    )
    write_config_snapshot(str(out_dir), snapshot)


if __name__ == "__main__":
    main()
