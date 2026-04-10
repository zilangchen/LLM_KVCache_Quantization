#!/usr/bin/env python3
"""
Custom generation loop with explicit prefill + decode separation.

This module implements a generation loop WITHOUT using model.generate(),
enabling precise control over KV cache, timing, and future quantization.

Usage:
    from src.engine.generate_loop import generate, GenerationOutput

    output = generate(model, tokenizer, "Hello, I am", max_new_tokens=128)
    print(f"Text: {output.text}")
    print(f"TTFT: {output.ttft_ms:.2f} ms")
    print(f"TPOT: {output.tpot_ms:.2f} ms")
"""

from dataclasses import dataclass
from typing import List, Optional
import gc
import json
import os
import torch
from transformers import PreTrainedModel, PreTrainedTokenizer
try:
    from transformers import DynamicCache
    HAS_DYNAMIC_CACHE = True
except ImportError:
    # Try older location? Or fall back
    try:
        from transformers.cache_utils import DynamicCache
        HAS_DYNAMIC_CACHE = True
    except ImportError:
        HAS_DYNAMIC_CACHE = False

from src.utils.timing import (
    CUDATimer,
    TimingStats,
    get_gpu_memory_mb,
    reset_gpu_memory_stats,
)
from src.utils.repro import set_seed

# ENG-031: Module-level constant for fused KV modes to avoid repeated hardcoding.
_FUSED_KV_MODES = frozenset({"int8_fused", "int8_ours", "int4_fused", "int4_ours", "int4_ours_mixed"})
# INT4 asymmetric modes that CAN use fused patch (only when decode_attn_impl is triton_*)
_INT4_ASYM_FUSABLE = frozenset({"int4_ours_asym", "int4_ours_asym_ba", "kivi_style"})


def _normalize_eos_token_id(eos_token_id) -> Optional[int]:
    """Normalize tokenizer eos_token_id to a single int, handling list/tuple forms."""
    if eos_token_id is None:
        return None
    if isinstance(eos_token_id, (list, tuple)):
        if len(eos_token_id) == 0:
            return None
        return int(eos_token_id[0])
    return int(eos_token_id)


def _cache_stats_from_past_key_values(past_key_values) -> tuple[float, int]:
    """
    Best-effort memory/seq-len extraction from HF cache objects or legacy tuples.
    Returns (memory_mb, seq_len). Never raises.
    """
    if past_key_values is None:
        return 0.0, 0

    total_bytes = 0
    seq_len = 0

    # New cache API (transformers>=4.57): cache.layers[i].keys / values
    layers = getattr(past_key_values, "layers", None)
    if layers is not None:
        try:
            for layer in layers:
                k = getattr(layer, "keys", None)
                v = getattr(layer, "values", None)
                if isinstance(k, torch.Tensor):
                    total_bytes += k.numel() * k.element_size()
                    if seq_len == 0 and k.ndim >= 3:
                        seq_len = int(k.shape[-2])
                if isinstance(v, torch.Tensor):
                    total_bytes += v.numel() * v.element_size()
            if total_bytes > 0:
                return total_bytes / (1024 * 1024), seq_len
        except Exception:
            pass

    # Legacy tuple path (or iterable cache wrappers).
    legacy = None
    if isinstance(past_key_values, tuple):
        legacy = past_key_values
    elif hasattr(past_key_values, "to_legacy_cache"):
        try:
            legacy = past_key_values.to_legacy_cache()
        except Exception:
            legacy = None

    if isinstance(legacy, tuple):
        try:
            for item in legacy:
                if not isinstance(item, tuple) or len(item) < 2:
                    continue
                k, v = item[0], item[1]
                if isinstance(k, torch.Tensor):
                    total_bytes += k.numel() * k.element_size()
                    if seq_len == 0 and k.ndim >= 3:
                        seq_len = int(k.shape[-2])
                if isinstance(v, torch.Tensor):
                    total_bytes += v.numel() * v.element_size()
            return total_bytes / (1024 * 1024), seq_len
        except Exception:
            return 0.0, 0

    return 0.0, 0


def _to_dynamic_cache_safely(legacy_cache):
    """
    Convert legacy tuple cache to DynamicCache with robust fallback.
    Raises RuntimeError with details if conversion fails.
    """
    if not HAS_DYNAMIC_CACHE or not isinstance(legacy_cache, tuple):
        return legacy_cache

    errors: list[str] = []
    try:
        return DynamicCache.from_legacy_cache(legacy_cache)
    except Exception as exc:
        errors.append(f"from_legacy_cache failed: {exc}")

    # ENG-058: Manual DynamicCache construction — iterate (k, v) layers and
    # call cache.update() which is the stable public API.  The previous
    # fallback used the non-existent kwarg ``ddp_cache_data`` which always
    # raised TypeError, was silently caught, and fell through to RuntimeError.
    try:
        cache = DynamicCache()
        for layer_idx, (k, v) in enumerate(legacy_cache):
            cache.update(k, v, layer_idx)
        return cache
    except Exception as exc:
        errors.append(f"manual DynamicCache.update() construction failed: {exc}")

    raise RuntimeError(
        "Failed to convert legacy past_key_values tuple to DynamicCache. "
        + " | ".join(errors)
    )


@dataclass
class GenerationOutput:
    """Structured output from the generation loop."""

    text: str
    tokens: List[int]
    ttft_ms: float          # Time To First Token (prefill time)
    tpot_ms: float          # Time Per Output Token (decode average)
    tok_per_s: float        # Throughput (tokens per second)
    gpu_mem_peak_mb: float  # Peak GPU memory usage
    prompt_len: int         # Number of prompt tokens
    gen_len: int            # Number of generated tokens
    tok_per_s_per_seq: float = 0.0  # Per-sequence throughput for batch runs
    kv_cache_mem_mb: float = 0.0  # KV cache resident memory (implementation-specific)
    kv_cache_seq_len: int = 0  # KV cache sequence length after generation


@dataclass
class GenerationBatchOutput:
    """Batch output from generation_from_ids()."""

    generated_ids: torch.Tensor  # [B, gen_len]
    ttft_ms: float
    tpot_ms: float
    tok_per_s: float
    tok_per_s_per_seq: float
    gpu_mem_peak_mb: float
    prompt_len: int
    gen_len: int
    batch: int
    kv_cache_mem_mb: float = 0.0
    kv_cache_seq_len: int = 0


def _register_all_temperature_hooks(model, inv_tau: torch.Tensor):
    """
    Apply per-head temperature to ALL forward passes (both prefill and decode).

    Used by int4_kivi_aligned mode where the decode path is torch_ref (not fused),
    so inv_tau must be applied via hooks at decode time too.

    Same mechanism as _register_prefill_temperature_hooks but without the
    seq_len <= 1 early return guard.
    """
    handles = []
    layers = getattr(getattr(model, "model", None), "layers", None)
    if layers is None:
        import warnings
        warnings.warn(
            "Cannot register temperature hooks: model.model.layers not found.",
            UserWarning,
        )
        return handles

    if not isinstance(inv_tau, torch.Tensor) or inv_tau.ndim != 2:
        raise ValueError(f"inv_tau must be a 2D tensor [layers, heads], got {type(inv_tau)} {getattr(inv_tau, 'shape', None)}")

    cfg = getattr(model, "config", None)
    cfg_heads = getattr(cfg, "num_attention_heads", None)

    for layer_idx, layer in enumerate(layers):
        attn = getattr(layer, "self_attn", None)
        if attn is None:
            continue

        # ENG-092: Use `is not None` instead of `or` to avoid skipping
        # num_heads=0 (which would be falsy but semantically different from None).
        _nh = getattr(attn, "num_heads", None)
        if _nh is None:
            _nh = getattr(attn, "_kv_num_attention_heads", None)
        if _nh is None:
            _nh = cfg_heads
        num_heads = _nh
        head_dim = getattr(attn, "head_dim", None)
        if num_heads is None or head_dim is None:
            continue

        if layer_idx >= inv_tau.shape[0]:
            raise ValueError(
                f"inv_tau has {inv_tau.shape[0]} layers but model has layer_idx={layer_idx}."
            )
        if inv_tau.shape[1] != int(num_heads):
            raise ValueError(
                f"inv_tau head count mismatch at layer {layer_idx}: "
                f"inv_tau.shape[1]={inv_tau.shape[1]} vs model.num_heads={num_heads}."
            )

        inv_tau_layer = inv_tau[layer_idx]  # [H]

        if getattr(attn, "q_norm", None) is not None:
            q_norm = attn.q_norm

            def _q_norm_hook(module, inputs, output, _inv=inv_tau_layer, _h=int(num_heads)):
                if not isinstance(output, torch.Tensor) or output.ndim != 4:
                    return output
                # Same layout detection as prefill hooks, but without seq_len guard.
                if output.shape[1] == _h:
                    scale = _inv.to(device=output.device, dtype=output.dtype)
                    return output * scale.view(1, -1, 1, 1)
                if output.shape[2] == _h:
                    scale = _inv.to(device=output.device, dtype=output.dtype)
                    return output * scale.view(1, 1, -1, 1)
                return output

            handles.append(q_norm.register_forward_hook(_q_norm_hook))
        else:
            q_proj = getattr(attn, "q_proj", None)
            if q_proj is None:
                continue

            def _q_proj_hook(module, inputs, output, _inv=inv_tau_layer, _h=int(num_heads), _d=int(head_dim)):
                if not isinstance(output, torch.Tensor) or output.ndim != 3:
                    return output
                # output: [B, S, H*D] — apply temperature regardless of seq_len.
                if output.shape[2] != _h * _d:
                    return output
                scale = _inv.to(device=output.device, dtype=output.dtype)
                bsz, seq_len, _ = output.shape
                out = output.view(bsz, seq_len, _h, _d) * scale.view(1, 1, -1, 1)
                return out.view(bsz, seq_len, _h * _d)

            handles.append(q_proj.register_forward_hook(_q_proj_hook))

    return handles


def _register_prefill_temperature_hooks(model, inv_tau: torch.Tensor):
    """
    Apply per-head temperature to prefill by scaling query states.

    Implementation detail:
    - If the attention module has q_norm, scale its output (post-normalization).
    - Otherwise, scale q_proj output (pre-reshape).

    Hooks only activate when the sequence length > 1, so decode (q_len==1) is not double-scaled.
    """
    handles = []

    layers = getattr(getattr(model, "model", None), "layers", None)
    if layers is None:
        # ENG-022: Warn when model structure does not match expected layout
        # instead of silently returning empty hooks.
        import warnings
        warnings.warn(
            "Cannot register prefill temperature hooks: model.model.layers not found. "
            "Per-head temperature scaling will NOT be applied during prefill.",
            UserWarning,
        )
        return handles

    if not isinstance(inv_tau, torch.Tensor) or inv_tau.ndim != 2:
        raise ValueError(f"inv_tau must be a 2D tensor [layers, heads], got {type(inv_tau)} {getattr(inv_tau, 'shape', None)}")

    cfg = getattr(model, "config", None)
    cfg_heads = getattr(cfg, "num_attention_heads", None)

    for layer_idx, layer in enumerate(layers):
        attn = getattr(layer, "self_attn", None)
        if attn is None:
            continue

        # ENG-092: Use `is not None` instead of `or` to avoid skipping
        # num_heads=0 (which would be falsy but semantically different from None).
        _nh = getattr(attn, "num_heads", None)
        if _nh is None:
            _nh = getattr(attn, "_kv_num_attention_heads", None)
        if _nh is None:
            _nh = cfg_heads
        num_heads = _nh
        head_dim = getattr(attn, "head_dim", None)
        if num_heads is None or head_dim is None:
            continue

        if layer_idx >= inv_tau.shape[0]:
            raise ValueError(
                f"inv_tau has {inv_tau.shape[0]} layers but model has layer_idx={layer_idx}."
            )
        if inv_tau.shape[1] != int(num_heads):
            raise ValueError(
                f"inv_tau head count mismatch at layer {layer_idx}: "
                f"inv_tau.shape[1]={inv_tau.shape[1]} vs model.num_heads={num_heads}."
            )

        inv_tau_layer = inv_tau[layer_idx]  # [H]

        if getattr(attn, "q_norm", None) is not None:
            q_norm = attn.q_norm

            def _q_norm_hook(module, inputs, output, _inv=inv_tau_layer, _h=int(num_heads)):
                if not isinstance(output, torch.Tensor) or output.ndim != 4:
                    return output

                # ENG-025: Layout detection between [B, H, S, D] and [B, S, H, D].
                # We check shape[1] first. When H == S (e.g. prefill with exactly
                # num_heads tokens), both branches would match, creating ambiguity.
                # Tiebreaker heuristic: prefer [B, H, S, D] (dim-1 == H) because
                # Qwen2 and most HF decoder models produce [B, H, S, D] from q_norm.
                # This is safe in practice because num_heads (e.g. 8–32) is rarely
                # equal to the prompt sequence length, and even if they match we apply
                # the scale in the correct position for the dominant layout.
                # If you see incorrect temperature scaling at exactly H-token prompts,
                # override by ensuring q_norm outputs [B, H, S, D] consistently.
                if output.shape[1] == _h:
                    seq_len = output.shape[2]
                    if seq_len <= 1:
                        return output
                    scale = _inv.to(device=output.device, dtype=output.dtype)
                    return output * scale.view(1, -1, 1, 1)

                if output.shape[2] == _h:
                    seq_len = output.shape[1]
                    if seq_len <= 1:
                        return output
                    scale = _inv.to(device=output.device, dtype=output.dtype)
                    return output * scale.view(1, 1, -1, 1)

                return output

            handles.append(q_norm.register_forward_hook(_q_norm_hook))
        else:
            q_proj = getattr(attn, "q_proj", None)
            if q_proj is None:
                continue

            def _q_proj_hook(module, inputs, output, _inv=inv_tau_layer, _h=int(num_heads), _d=int(head_dim)):
                if not isinstance(output, torch.Tensor) or output.ndim != 3:
                    return output
                # output: [B, S, H*D]
                if output.shape[1] <= 1:
                    return output
                if output.shape[2] != _h * _d:
                    return output

                scale = _inv.to(device=output.device, dtype=output.dtype)
                bsz, seq_len, _ = output.shape
                out = output.view(bsz, seq_len, _h, _d) * scale.view(1, 1, -1, 1)
                return out.view(bsz, seq_len, _h * _d)

            handles.append(q_proj.register_forward_hook(_q_proj_hook))

    return handles


def generate_from_ids(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    input_ids: torch.Tensor,
    attention_mask: Optional[torch.Tensor] = None,
    max_new_tokens: int = 128,
    kv_mode: str = "fp16",
    group_size: int = 128,
    clip_percentile: float = 99.9,
    seed: int = 1234,
    calib_file: Optional[str] = None,
    use_attn_temperature: bool = True,
    use_static_scales: bool = True,
    adaptive_static_scales: bool = False,
    adaptive_static_margin: float = 1.0,
    adaptive_static_k: bool = True,
    adaptive_static_v: bool = True,
    decode_attn_impl: str = "triton_fused",
    allow_missing_calib: bool = False,
    stop_on_eos: bool = True,
    quant_bits: int = 8,  # XMD-002: aligned with generate() default
    k_bits: Optional[int] = None,
    v_bits: Optional[int] = None,
    residual_length: int = 0,
) -> GenerationBatchOutput:
    """
    Batched generation loop using explicit prefill + token-by-token decode.

    This is an internal helper to enable batch throughput experiments and
    batched needle evaluation. It assumes *uniform* sequence length across the
    batch (input_ids is a dense [B, S] tensor).

    Important constraints:
    - For kv_mode in {"int8_fused","int8_ours","int4_fused","int4_ours","int4_ours_mixed"},
      fused decode does NOT support
      padding/variable context lengths. For safety, when batch>1 we require
      attention_mask to be all ones (no padding).
    - kv_mode="kivi_style" supports quant_bits {4, 8} only and always runs
      torch_ref decode attention (non-fused path).
    - kv_mode="int4_mixed_kv" supports k_bits/v_bits for K/V ablation.
    """
    # ENG-008: batch constraint validation is intentionally checked here even if partially
    # redundant with earlier checks, as a defense-in-depth measure.
    # Validate inputs
    if kv_mode not in [
        "fp16",
        "int8_baseline",
        "int8_fused",
        "int8_ours",
        "int4_baseline",
        "int4_fused",
        "int4_ours",
        "int4_ours_mixed",
        "kivi_style",
        "int4_kivi_aligned",
        "int4_mixed_kv",
        "int4_ours_asym",
        "int4_ours_asym_ba",
    ]:
        raise ValueError(
            f"kv_mode='{kv_mode}' not supported. "
            "Choose from ['fp16', 'int8_baseline', 'int8_fused', 'int8_ours', "
            "'int4_baseline', 'int4_fused', 'int4_ours', 'int4_ours_mixed', "
            "'kivi_style', 'int4_kivi_aligned', 'int4_mixed_kv', "
            "'int4_ours_asym', 'int4_ours_asym_ba']."
        )

    _valid_impls = {"triton_fused", "torch_ref", "triton_int4_asym", "flashinfer"}
    if decode_attn_impl not in _valid_impls:
        raise ValueError(
            f"decode_attn_impl='{decode_attn_impl}' not supported. "
            f"Choose from {sorted(_valid_impls)}."
        )
    # P2 fix: triton_int4_asym only valid for INT4 asymmetric modes
    if decode_attn_impl == "triton_int4_asym" and kv_mode not in (
        "int4_ours_asym", "int4_ours_asym_ba", "kivi_style",
    ):
        raise ValueError(
            f"decode_attn_impl='triton_int4_asym' only supports kv_mode in "
            f"{{int4_ours_asym, int4_ours_asym_ba, kivi_style}}, got '{kv_mode}'."
        )
    if decode_attn_impl == "flashinfer" and kv_mode not in (
        "int4_ours_asym", "int4_ours_asym_ba",
    ):
        raise ValueError(
            f"decode_attn_impl='flashinfer' only supports kv_mode in "
            f"{{int4_ours_asym, int4_ours_asym_ba}}, got '{kv_mode}'."
        )

    if kv_mode == "kivi_style":
        import warnings

        # ENG-006: Validate quant_bits for kivi_style mode.
        # KIVI quantization only supports 8-bit (asymmetric int8) and 4-bit
        # (asymmetric int4 with bit-packing). Other values are not implemented
        # in KIVIStyleKVCache and would produce a runtime error in append().
        kivi_quant_bits = 8 if quant_bits is None else int(quant_bits)
        if kivi_quant_bits not in (4, 8):
            raise ValueError(
                f"kv_mode='kivi_style' requires quant_bits in {{4, 8}}, got {kivi_quant_bits}"
            )
        quant_bits = kivi_quant_bits

        # ENG-014: Warn when calibration / static-scale parameters are passed with
        # kivi_style mode. KIVI uses its own per-channel K / per-token V quantization
        # scheme and does NOT consult calib_file, inv_tau, static scales, or adaptive
        # scale logic. Passing these parameters silently has no effect, which could
        # mislead users into believing their calibration data is being applied.
        ignored_fields = []
        if calib_file is not None:
            ignored_fields.append("calib_file")
        if use_attn_temperature:
            ignored_fields.append("use_attn_temperature")
        if use_static_scales:
            ignored_fields.append("use_static_scales")
        if adaptive_static_scales:
            ignored_fields.append("adaptive_static_scales")
        if adaptive_static_margin != 1.0:
            ignored_fields.append("adaptive_static_margin")
        if not adaptive_static_k:
            ignored_fields.append("adaptive_static_k")
        if not adaptive_static_v:
            ignored_fields.append("adaptive_static_v")
        if allow_missing_calib:
            ignored_fields.append("allow_missing_calib")
        if ignored_fields:
            warnings.warn(
                "kv_mode='kivi_style' ignores calibration/static-scale parameters: "
                + ", ".join(sorted(ignored_fields)),
                UserWarning,
            )

        if decode_attn_impl != "torch_ref":
            warnings.warn(
                f"kv_mode='kivi_style' forces decode_attn_impl='torch_ref' "
                f"(got {decode_attn_impl!r}).",
                UserWarning,
            )
            decode_attn_impl = "torch_ref"

    elif kv_mode == "int4_kivi_aligned":
        import warnings

        # INT4 KIVI + attention-aligned calibration (K-path inv_tau).
        # Uses KIVIStyleKVCache with INT4 + inv_tau Q pre-scaling.
        quant_bits = 4

        # int4_kivi_aligned REQUIRES calib_file for inv_tau; warn if missing.
        if calib_file is None and use_attn_temperature:
            warnings.warn(
                "kv_mode='int4_kivi_aligned' with use_attn_temperature=True but "
                "no calib_file — inv_tau will not be applied.",
                UserWarning,
            )

        # Static scale / adaptive parameters are still ignored (KIVI skeleton).
        if use_static_scales:
            warnings.warn(
                "kv_mode='int4_kivi_aligned' ignores use_static_scales (KIVI skeleton).",
                UserWarning,
            )

        if decode_attn_impl != "torch_ref":
            warnings.warn(
                f"kv_mode='int4_kivi_aligned' forces decode_attn_impl='torch_ref' "
                f"(got {decode_attn_impl!r}).",
                UserWarning,
            )
            decode_attn_impl = "torch_ref"

    elif kv_mode == "int4_mixed_kv":
        import warnings

        # K-INT8/V-INT4 hybrid mode — uses MixedKVCache.
        quant_bits = 4  # Nominal; K uses INT8, V uses INT4.

        if decode_attn_impl != "torch_ref":
            warnings.warn(
                f"kv_mode='int4_mixed_kv' forces decode_attn_impl='torch_ref' "
                f"(got {decode_attn_impl!r}).",
                UserWarning,
            )
            decode_attn_impl = "torch_ref"

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is required for generation. Please run on a GPU-enabled server."
        )

    if not isinstance(input_ids, torch.Tensor):
        raise TypeError(f"input_ids must be a torch.Tensor, got {type(input_ids)}")
    if input_ids.ndim != 2:
        raise ValueError(f"input_ids must have shape [B, S], got {tuple(input_ids.shape)}")

    # Ensure dtype/device
    input_ids = input_ids.to(device=model.device, dtype=torch.long)
    batch_size, prompt_len = int(input_ids.shape[0]), int(input_ids.shape[1])

    # ENG-020: Validate non-degenerate input shapes.
    if batch_size == 0:
        raise ValueError(f"input_ids batch_size must be > 0, got shape {tuple(input_ids.shape)}")
    if prompt_len == 0:
        raise ValueError(f"input_ids prompt_len must be > 0, got shape {tuple(input_ids.shape)}")

    if attention_mask is None:
        attention_mask = torch.ones_like(input_ids, dtype=torch.long, device=model.device)
    else:
        if not isinstance(attention_mask, torch.Tensor):
            raise TypeError(f"attention_mask must be a torch.Tensor, got {type(attention_mask)}")
        if attention_mask.shape != input_ids.shape:
            raise ValueError(
                f"attention_mask shape must match input_ids. "
                f"Got attention_mask={tuple(attention_mask.shape)} input_ids={tuple(input_ids.shape)}"
            )
        attention_mask = attention_mask.to(device=model.device, dtype=torch.long)

    if batch_size > 1:
        # ENG-005: Padding check for batch>1.
        # Our custom KV cache implementation does not track per-sample context lengths
        # and does not maintain a positional offset per sequence. Padding (i.e. any
        # attention_mask value that is 0) would mean some sequences are shorter than
        # others, which would silently corrupt decode-step attention because the cache
        # stores tokens at sequential positions without a per-sample valid-length mask.
        # This check is intentional and must NOT be removed without also adding
        # per-sequence length tracking to every cache backend and to the decode path.
        if not torch.all(attention_mask == 1).item():
            raise ValueError(
                "Batched generation requires attention_mask to be all ones (no padding). "
                f"Got batch={batch_size} kv_mode={kv_mode}."
            )

    # ENG-086: Define _restore_fused_patch() BEFORE the outer try so it is
    # always in scope for the finally block.  Strictly idempotent: checks
    # _fused_patch_applied flag, restores after first call, further calls
    # are no-ops.
    _fused_patch_applied = False

    def _restore_fused_patch():
        nonlocal _fused_patch_applied
        if not _fused_patch_applied:
            return
        _fused_patch_applied = False
        try:
            from src.engine.patch_model import remove_int8_fused_patch as _remove
            _remove(model)
        except Exception:
            # Last-resort manual restore if the high-level helper fails.
            try:
                first_attn = model.model.layers[0].self_attn
                AttnClass = first_attn.__class__
                if hasattr(AttnClass, "_original_forward"):
                    AttnClass.forward = AttnClass._original_forward
                    del AttnClass._original_forward
            except Exception:
                pass

    # ENG-086: Outer try/finally wraps the patch call itself AND the entire
    # post-patch region so _restore_fused_patch() is guaranteed to run on
    # ALL exit paths — including partial-patch failures, ValueError (length
    # check), RuntimeError/FileNotFoundError (calibration), cache
    # construction failures, and hook registration errors.
    try:
        # ENG-090: Set seeds BEFORE apply_patch so that any random state
        # consumed during patching is deterministic. Also reset memory stats
        # before patching so the peak measurement starts from a clean baseline.
        set_seed(seed=seed, deterministic=True)
        reset_gpu_memory_stats()

        # Apply patch if needed
        # INT4 asymmetric modes only get fused patch when using triton kernel
        _use_fused = kv_mode in _FUSED_KV_MODES or (
            kv_mode in _INT4_ASYM_FUSABLE
            and decode_attn_impl in ("triton_fused", "triton_int4_asym", "flashinfer")
        )
        if _use_fused:
            if kv_mode == "int8_ours":
                import warnings

                warnings.warn(
                    "kv_mode=int8_ours uses the fused int8 path; calibration will be loaded "
                    "if calib_file is provided (or artifacts/kv_calib_kl.json exists).",
                    UserWarning,
                )
            from src.engine.patch_model import apply_int8_fused_patch

            # Inner try/except handles partial-patch cleanup before re-raising.
            try:
                apply_int8_fused_patch(model)
                _fused_patch_applied = True
            except Exception:
                # Attempt to restore original forward if it was partially saved.
                try:
                    first_attn = model.model.layers[0].self_attn
                    AttnClass = first_attn.__class__
                    if hasattr(AttnClass, "_original_forward"):
                        AttnClass.forward = AttnClass._original_forward
                        del AttnClass._original_forward
                except Exception:
                    pass
                raise

        # ENG-060: Get available GPU memory for OOM checks using the model's
        # actual device instead of hardcoded GPU 0.
        try:
            _model_device = model.device
            _device_idx = _model_device.index if _model_device.index is not None else 0
            gpu_free_mb = (
                torch.cuda.get_device_properties(_device_idx).total_memory
                - torch.cuda.memory_allocated(_device_idx)
            ) / (1024 * 1024)
        except Exception:
            gpu_free_mb = None

        # Check for excessively long input
        max_model_len = getattr(model.config, "max_position_embeddings", 32768)
        if prompt_len + max_new_tokens > int(max_model_len):
            raise ValueError(
                f"Total length ({prompt_len} + {max_new_tokens} = "
                f"{prompt_len + max_new_tokens}) exceeds model's max "
                f"position embeddings ({max_model_len}). "
                f"Reduce prompt length or max_new_tokens."
            )

        max_cache_len = min(int(max_model_len), int(prompt_len + max_new_tokens))

        # Initialize KV Cache based on mode
        num_layers = getattr(model.config, "num_hidden_layers", 28)
        static_k_scale = None
        static_v_scale = None
        inv_tau = None
        outlier_rescue_ratio = 0.0
        mixed_rescue = False

        if kv_mode in ["int8_ours", "int4_ours", "int4_ours_mixed", "int4_fused"]:
            import warnings

            # ENG-089: Compute project root from __file__ so default calib paths
            # resolve correctly regardless of the caller's working directory.
            _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if kv_mode == "int8_ours":
                default_calib = os.path.join(_project_root, "artifacts", "kv_calib_kl.json")
            else:
                default_calib = os.path.join(_project_root, "artifacts", "kv_calib_kl_int4_selected.json")
            # ENG-061: Use `is not None` instead of `or` so that calib_file=""
            # (empty string, meaning "no calibration") is not replaced by default.
            calib_path = calib_file if calib_file is not None else default_calib
            if calib_path and os.path.exists(calib_path):
                try:
                    with open(calib_path, "r") as f:
                        calib = json.load(f)

                    # CAL-033: Version check — warn on legacy v1, fail-fast if
                    # postfix gate requires v2.
                    _calib_version = calib.get("version", 0)
                    if _calib_version < 2:
                        warnings.warn(
                            f"Calibration file '{calib_path}' has version={_calib_version} "
                            f"(expected >=2). Legacy v1 calibration lacks provenance fields "
                            f"(model_revision, seed, dataset_source). Results may not be "
                            f"reproducible. Re-run calibrate_behavior.py to generate v2.",
                            UserWarning,
                        )
                    calib_group_k = calib.get("group_size_k", calib.get("group_size", group_size))
                    calib_group_v = calib.get("group_size_v", calib.get("group_size", group_size))
                    calib_clip_k = calib.get("clip_percentile_k", calib.get("clip_percentile", clip_percentile))
                    calib_clip_v = calib.get("clip_percentile_v", calib.get("clip_percentile", clip_percentile))

                    if calib_group_k and calib_group_v and calib_group_k != calib_group_v:
                        # CAL-022: group_size_v is read from calib but the cache engine
                        # uses a single group_size for both K and V. Warn explicitly that
                        # group_size_v is discarded so users know V-side calibration differs.
                        warnings.warn(
                            f"CAL-022: Calibration group_size_k ({calib_group_k}) != group_size_v ({calib_group_v}); "
                            "the cache engine uses a single group_size for both K and V. "
                            "group_size_k will be used for both; group_size_v is discarded. "
                            "Re-calibrate with symmetric group sizes to avoid this mismatch.",
                            UserWarning,
                        )
                    if calib_clip_k and calib_clip_v and calib_clip_k != calib_clip_v:
                        # CAL-022: clip_percentile_v is read from calib but the cache engine
                        # uses a single clip_percentile for both K and V. Warn explicitly.
                        warnings.warn(
                            f"CAL-022: Calibration clip_percentile_k ({calib_clip_k}) != clip_percentile_v ({calib_clip_v}); "
                            "the cache engine uses a single clip_percentile for both K and V. "
                            "clip_percentile_k will be used for both; clip_percentile_v is discarded.",
                            UserWarning,
                        )

                    # ENG-026: Use `is not None` instead of `or` to avoid
                    # replacing legitimate falsy values (e.g. 0).
                    group_size = calib_group_k if calib_group_k is not None else group_size
                    clip_percentile = calib_clip_k if calib_clip_k is not None else clip_percentile

                    if use_static_scales and "k_scale" in calib:
                        # ENG-021/ENG-066: INT4 scales loaded as float32 to preserve
                        # precision through the quantization chain. INT4's coarse step
                        # size (1/7) amplifies fp16 rounding error ~18×. INT8 path
                        # remains fp16 (step size 1/127 tolerates fp16 precision).
                        _scale_dtype = torch.float32 if kv_mode.startswith("int4") else torch.float16
                        static_k_scale = torch.tensor(calib["k_scale"], dtype=_scale_dtype)
                    if use_static_scales and "v_scale" in calib:
                        _scale_dtype = torch.float32 if kv_mode.startswith("int4") else torch.float16
                        static_v_scale = torch.tensor(calib["v_scale"], dtype=_scale_dtype)

                    # ENG-048: Detect asymmetric k_scale / v_scale presence and warn.
                    # Having k_scale without v_scale (or vice versa) means one side uses
                    # static scales while the other uses dynamic quantization. This is
                    # almost always unintentional and indicates a corrupt or partial
                    # calibration file. Without this warning, the mismatch is silent.
                    if use_static_scales:
                        _has_k_scale = "k_scale" in calib
                        _has_v_scale = "v_scale" in calib
                        if _has_k_scale and not _has_v_scale:
                            warnings.warn(
                                "ENG-048: Calibration file has 'k_scale' but no 'v_scale'. "
                                "K uses static scales; V will use dynamic quantization. "
                                "This asymmetry is usually unintentional. Verify calibration file.",
                                UserWarning,
                            )
                        elif _has_v_scale and not _has_k_scale:
                            warnings.warn(
                                "ENG-048: Calibration file has 'v_scale' but no 'k_scale'. "
                                "V uses static scales; K will use dynamic quantization. "
                                "This asymmetry is usually unintentional. Verify calibration file.",
                                UserWarning,
                            )
                    if use_attn_temperature and "inv_tau" in calib:
                        inv_tau = torch.tensor(calib["inv_tau"], dtype=torch.float32)
                    outlier_rescue_ratio = float(calib.get("int4_outlier_ratio", 0.0) or 0.0)
                    mixed_rescue = bool(calib.get("int4_mixed_rescue", False))
                    if kv_mode == "int4_ours_mixed":
                        mixed_rescue = True

                    if static_k_scale is not None:
                        static_k_scale = static_k_scale.to(model.device)
                    if static_v_scale is not None:
                        static_v_scale = static_v_scale.to(model.device)
                    if inv_tau is not None:
                        inv_tau = inv_tau.to(model.device)
                except Exception as exc:
                    if allow_missing_calib:
                        # ENG-038: Warn clearly that the fallback means no static_scale
                        # and no inv_tau will be used, even though kv_mode remains
                        # unchanged. Without this warning, experiment results labelled
                        # as "int8_ours" (or int4_ours) actually run as baseline,
                        # silently invalidating comparisons.
                        warnings.warn(
                            f"Failed to load calibration file {calib_path}: {exc}. "
                            f"Falling back to dynamic-only quantization (no static scales, "
                            f"no inv_tau temperature). kv_mode is still '{kv_mode}' but "
                            f"effective behavior is equivalent to baseline. Results "
                            f"labelled '{kv_mode}' from this run should NOT be compared "
                            f"against properly-calibrated runs.",
                            UserWarning,
                        )
                    else:
                        raise RuntimeError(
                            f"Failed to load calibration file {calib_path}: {exc}."
                        ) from exc
            else:
                if allow_missing_calib:
                    warnings.warn(
                        f"Calibration file not found: {calib_path}. "
                        "Falling back to baseline behavior.",
                        UserWarning,
                    )
                else:
                    raise FileNotFoundError(
                        f"kv_mode={kv_mode} requires a calibration file, but it was not found: {calib_path}. "
                        "Run scripts/calibrate_behavior.py to generate calibration artifacts, "
                        "or switch kv_mode to baseline."
                    )

        if kv_mode == "fp16":
            from src.cache import FP16KVCache

            kv_cache = FP16KVCache(
                num_layers=num_layers,
                device=model.device.type,
                max_seq_len=max_cache_len,
            )
        elif kv_mode in ["int8_baseline", "int8_fused", "int8_ours"]:
            from src.cache import INT8KVCache

            kv_cache = INT8KVCache(
                num_layers=num_layers,
                device=model.device.type,
                clip_percentile=clip_percentile,
                group_size=group_size,
                max_seq_len=max_cache_len,
                decode_attn_impl=decode_attn_impl,
                static_k_scale=static_k_scale,
                static_v_scale=static_v_scale,
                inv_tau=inv_tau,
                use_attn_temperature=use_attn_temperature,
                adaptive_static_scales=adaptive_static_scales,
                adaptive_static_margin=adaptive_static_margin,
                adaptive_static_k=adaptive_static_k,
                adaptive_static_v=adaptive_static_v,
            )
        elif kv_mode in ["int4_baseline", "int4_fused", "int4_ours", "int4_ours_mixed"]:
            from src.cache import INT4KVCache

            kv_cache = INT4KVCache(
                num_layers=num_layers,
                device=model.device.type,
                clip_percentile=clip_percentile,
                group_size=group_size,
                max_seq_len=max_cache_len,
                decode_attn_impl=decode_attn_impl,
                static_k_scale=static_k_scale,
                static_v_scale=static_v_scale,
                inv_tau=inv_tau,
                use_attn_temperature=use_attn_temperature,
                adaptive_static_scales=adaptive_static_scales,
                adaptive_static_margin=adaptive_static_margin,
                adaptive_static_k=adaptive_static_k,
                adaptive_static_v=adaptive_static_v,
                outlier_rescue_ratio=outlier_rescue_ratio,
                mixed_rescue=mixed_rescue,
            )
        elif kv_mode == "kivi_style":
            # ENG-013: KIVI mode — uses asymmetric per-channel K / per-token V quantization
            # from the KIVI paper (Liu et al., 2024). Always runs torch_ref decode attention.
            from src.cache import KIVIStyleKVCache

            kv_cache = KIVIStyleKVCache(
                num_layers=num_layers,
                device=model.device.type,
                max_seq_len=max_cache_len,
                quant_bits=int(quant_bits),
                residual_length=residual_length,
            )
        elif kv_mode == "int4_kivi_aligned":
            # KIVI INT4 skeleton + attention-aligned calibration (K-path inv_tau).
            # Uses KIVIStyleKVCache with inv_tau for Q pre-scaling in decode.
            from src.cache import KIVIStyleKVCache

            # Load calibration file for inv_tau (v3 schema supported).
            kivi_inv_tau = None
            kivi_v_percentile = 100.0
            if calib_file is not None:
                # ENG-113/EVL-149: resolve relative paths from project root
                # (src/engine/generate_loop.py -> 3 dirname levels to repo root),
                # not CWD. Fail-fast when user-provided path does not exist.
                _proj = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                calib_path = calib_file if os.path.isabs(calib_file) else os.path.join(_proj, calib_file)
                if not os.path.exists(calib_path):
                    raise FileNotFoundError(
                        f"int4_kivi_aligned: calib_file={calib_file!r} not found "
                        f"(resolved to {calib_path!r}). Use an absolute path or "
                        f"run from the project root."
                    )
                with open(calib_path, "r") as f:
                    calib_data = json.load(f)
                # v3 schema: separate k_calibration / v_calibration
                if "k_calibration" in calib_data and "inv_tau" in calib_data["k_calibration"]:
                    raw_tau = calib_data["k_calibration"]["inv_tau"]
                    kivi_inv_tau = torch.tensor(raw_tau, dtype=torch.float32, device=model.device)
                elif "inv_tau" in calib_data:
                    # v2 schema fallback
                    raw_tau = calib_data["inv_tau"]
                    kivi_inv_tau = torch.tensor(raw_tau, dtype=torch.float32, device=model.device)
                # v3: v_calibration with optimized v_percentile
                if "v_calibration" in calib_data and "v_percentile" in calib_data["v_calibration"]:
                    kivi_v_percentile = float(calib_data["v_calibration"]["v_percentile"])

            kv_cache = KIVIStyleKVCache(
                num_layers=num_layers,
                device=model.device.type,
                max_seq_len=max_cache_len,
                quant_bits=4,
                v_percentile=kivi_v_percentile,
                inv_tau=kivi_inv_tau,
                use_attn_temperature=use_attn_temperature,
                residual_length=residual_length,  # P2 fix: pass residual_length
            )
        elif kv_mode in ("int4_ours_asym", "int4_ours_asym_ba"):
            # Role-Aware Asymmetric: per-channel K + per-token V with BA calibration.
            # ours_asym: BA-calibrated percentiles only (no inv_tau)
            # ours_asym_ba: BA-calibrated percentiles + inv_tau (full method)
            from src.cache.role_aware_asym_cache import RoleAwareAsymKVCache

            ra_k_percentile = 100.0
            ra_v_percentile = 100.0
            ra_inv_tau = None

            if calib_file is not None:
                # ENG-112/EVL-149: resolve relative paths from project root
                # (src/engine/generate_loop.py -> 3 dirname levels to repo root),
                # not CWD. Fail-fast when user-provided path does not exist.
                _proj = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                calib_path = calib_file if os.path.isabs(calib_file) else os.path.join(_proj, calib_file)
                if not os.path.exists(calib_path):
                    raise FileNotFoundError(
                        f"int4_ours_asym: calib_file={calib_file!r} not found "
                        f"(resolved to {calib_path!r}). Use an absolute path or "
                        f"run from the project root."
                    )
                with open(calib_path, "r") as f:
                    calib_data = json.load(f)
                # Role-aware schema: k_percentile, v_percentile at top level or under role_aware
                if "role_aware" in calib_data:
                    ra_section = calib_data["role_aware"]
                    ra_k_percentile = float(ra_section.get("k_percentile", 100.0))
                    ra_v_percentile = float(ra_section.get("v_percentile", 100.0))
                elif "k_calibration" in calib_data:
                    # Fallback: v3 schema from int4_kivi_aligned calibration.
                    # Look inside k_calibration first, then top-level.
                    import warnings
                    warnings.warn(
                        f"RoleAlign mode '{kv_mode}' using k_calibration fallback schema; "
                        "consider re-generating calibration with role_aware schema.",
                        UserWarning,
                    )
                    k_cal = calib_data["k_calibration"]
                    ra_k_percentile = float(k_cal.get("k_percentile", calib_data.get("k_percentile", 100.0)))
                    if "v_calibration" in calib_data:
                        ra_v_percentile = float(calib_data["v_calibration"].get("v_percentile", 100.0))
                # inv_tau: only for ours_asym_ba
                if kv_mode == "int4_ours_asym_ba":
                    if "role_aware" in calib_data and "inv_tau" in calib_data["role_aware"]:
                        raw_tau = calib_data["role_aware"]["inv_tau"]
                        ra_inv_tau = torch.tensor(raw_tau, dtype=torch.float32, device=model.device)
                    elif "k_calibration" in calib_data and "inv_tau" in calib_data["k_calibration"]:
                        raw_tau = calib_data["k_calibration"]["inv_tau"]
                        ra_inv_tau = torch.tensor(raw_tau, dtype=torch.float32, device=model.device)
                    elif "inv_tau" in calib_data:
                        raw_tau = calib_data["inv_tau"]
                        ra_inv_tau = torch.tensor(raw_tau, dtype=torch.float32, device=model.device)

            use_temp = use_attn_temperature and (kv_mode == "int4_ours_asym_ba")
            framework_tag = "ours_asym_ba" if kv_mode == "int4_ours_asym_ba" else "ours_asym"

            kv_cache = RoleAwareAsymKVCache(
                num_layers=num_layers,
                device=model.device.type,
                max_seq_len=max_cache_len,
                quant_bits=4,
                k_percentile=ra_k_percentile,
                v_percentile=ra_v_percentile,
                inv_tau=ra_inv_tau,
                use_attn_temperature=use_temp,
                framework=framework_tag,
            )
            # Set decode_attn_impl on cache so _fused_forward_impl can read it
            kv_cache.decode_attn_impl = decode_attn_impl
            if decode_attn_impl not in ("torch_ref", "triton_fused", "triton_int4_asym", "flashinfer"):
                import warnings
                warnings.warn(
                    f"kv_mode='{kv_mode}': unknown decode_attn_impl='{decode_attn_impl}', "
                    f"falling back to 'torch_ref'.",
                    UserWarning,
                )
                decode_attn_impl = "torch_ref"
            # INT4 asymmetric supports both torch_ref and triton_int4_asym.
            # triton_fused also accepted — routes to int4_asym kernel via patch_model.
        elif kv_mode == "int4_mixed_kv":
            # K-INT8 symmetric + V-INT4 asymmetric per-token (hybrid mode).
            # k_bits/v_bits allow K/V ablation (K-only, V-only, counterfactual).
            from src.cache.mixed_kv_cache import MixedKVCache

            kv_cache = MixedKVCache(
                num_layers=num_layers,
                device=model.device.type,
                max_seq_len=max_cache_len,
                k_bits=k_bits if k_bits is not None else 8,
                v_bits=v_bits if v_bits is not None else 4,
            )
        else:
            raise ValueError(f"Unsupported kv_mode: {kv_mode}")

        # Simple explicit memory check (rough estimate)
        if gpu_free_mb is not None and gpu_free_mb < 2000:
            import warnings

            warnings.warn(
                f"Low GPU memory ({gpu_free_mb:.0f} MB). Generation may OOM.",
                ResourceWarning,
            )

        generated_steps: List[torch.Tensor] = []
        decode_times = TimingStats()
        model_cache_for_decode = None
        fp16_use_model_cache = False

        hook_handles = []
        if kv_mode == "int4_kivi_aligned" and use_attn_temperature:
            # int4_kivi_aligned uses torch_ref decode (not fused), so inv_tau must
            # be applied via hooks for BOTH prefill and decode.
            _kivi_inv_tau = inv_tau
            if _kivi_inv_tau is None and hasattr(kv_cache, "inv_tau"):
                _kivi_inv_tau = kv_cache.inv_tau
            if _kivi_inv_tau is not None:
                hook_handles = _register_all_temperature_hooks(model, _kivi_inv_tau)
        elif kv_mode == "int4_ours_asym_ba" and use_attn_temperature and not _use_fused:
            # P1 fix: Only register hooks for torch_ref path. When _use_fused=True,
            # _fused_forward_impl applies inv_tau directly — hooks would double-apply.
            # ours_asym_ba torch_ref decode needs hooks for BOTH prefill and decode.
            _ra_inv_tau = inv_tau
            if _ra_inv_tau is None and hasattr(kv_cache, "inv_tau"):
                _ra_inv_tau = kv_cache.inv_tau
            if _ra_inv_tau is not None:
                hook_handles = _register_all_temperature_hooks(model, _ra_inv_tau)
        elif kv_mode in {"int8_ours", "int4_ours", "int4_ours_mixed", "int4_fused"} and use_attn_temperature and inv_tau is not None:
            # Fused modes: prefill hooks only; decode temperature handled by _fused_forward_impl.
            hook_handles = _register_prefill_temperature_hooks(model, inv_tau)

        # ENG-088: Helper to guarantee kv_cache cleanup on any exit path (OOM, etc.).
        def _cleanup_kv_cache():
            try:
                kv_cache.clear()
            except Exception:
                pass
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        # ========== PREFILL PHASE ==========
        prefill_timer = CUDATimer()
        prefill_timer.start()

        try:
            with torch.no_grad():
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    use_cache=True,
                )

                # Extract and store KV cache (prefill)
                if outputs.past_key_values is not None:
                    # ENG-046: We iterate outputs.past_key_values as an iterable of
                    # (k, v) tuples. For transformers < 4.36 this is a plain tuple.
                    # For transformers >= 4.36, model.forward may return a DynamicCache
                    # object. We rely on DynamicCache.__iter__ yielding per-layer
                    # (key_cache[i], value_cache[i]) tuples, which is the documented
                    # behavior as of transformers 4.40 but may change in future versions.
                    # If the iteration behavior changes (e.g. yields layer objects instead
                    # of tensor tuples), this loop will break with a TypeError at unpack.
                    # Pin transformers version in requirements.txt to avoid silent drift.
                    # ENG-065: Validate prefill layer count matches cache expectation.
                    _prefill_layers = sum(1 for _ in outputs.past_key_values)
                    if hasattr(kv_cache, "num_layers") and _prefill_layers != kv_cache.num_layers:
                        import warnings
                        warnings.warn(
                            f"ENG-065: Prefill returned {_prefill_layers} layers but "
                            f"kv_cache expects {kv_cache.num_layers}. Layer count mismatch "
                            f"may cause IndexError or truncated context.",
                            RuntimeWarning,
                        )
                    for i, (k, v) in enumerate(outputs.past_key_values):
                        kv_cache.append(i, k, v)
                    if (
                        kv_mode == "fp16"
                        and HAS_DYNAMIC_CACHE
                        and hasattr(outputs.past_key_values, "get_seq_length")
                    ):
                        # Reuse HF dynamic cache directly in decode to avoid
                        # per-step tuple->DynamicCache conversion spikes at high batch.
                        model_cache_for_decode = outputs.past_key_values
                        fp16_use_model_cache = True
                        # ENG-091: Release duplicate prefill KV from kv_cache since
                        # decode will use model_cache_for_decode exclusively. Without
                        # this, both kv_cache and model_cache_for_decode hold the same
                        # prefill KV data, doubling VRAM usage until function exit.
                        # Codex FAIL: clear() only resets lengths, not buffers.
                        # Use release() to actually free the tensor memory.
                        kv_cache.release()

                next_token_logits = outputs.logits[:, -1, :]
                next_token = torch.argmax(next_token_logits, dim=-1)  # [B]
        except Exception:
            # ENG-088: Guarantee kv_cache cleanup on prefill failure (e.g. OOM).
            _cleanup_kv_cache()
            raise
        finally:
            # UTIL-001: Ensure prefill_timer.stop() runs even if model() throws,
            # so ttft_ms is always defined and CUDA events are properly finalized.
            prefill_timer.stop()
            for h in hook_handles:
                try:
                    h.remove()
                except Exception:
                    pass

        ttft_ms = prefill_timer.elapsed_ms

        # ENG-018: If max_new_tokens=0, skip generation entirely.
        # ENG-093: When max_new_tokens=0, no tokens are generated and gen_len=0.
        # TTFT is still measured (prefill latency), but TPOT is 0.0 since no
        # decode steps occur. The prefill argmax is computed but not stored.
        if max_new_tokens > 0:
            generated_steps.append(next_token)
            current_token = next_token.view(batch_size, 1)  # [B, 1]

            # Update attention mask for decode phase
            if attention_mask is not None:
                attention_mask = torch.cat(
                    [
                        attention_mask,
                        torch.ones((batch_size, 1), device=model.device, dtype=attention_mask.dtype),
                    ],
                    dim=1,
                )

        # ========== DECODE PHASE ==========
        eos_token_id = _normalize_eos_token_id(tokenizer.eos_token_id)

        # ENG-110: Per-sequence EOS tracking. Once a sequence emits EOS, all its
        # subsequent tokens are forced to eos_token_id to avoid garbage generation
        # while waiting for slower sequences in the batch to finish.
        eos_reached = torch.zeros(batch_size, dtype=torch.bool, device=model.device)
        if stop_on_eos and eos_token_id is not None and max_new_tokens > 0 and generated_steps:
            eos_reached = generated_steps[-1] == eos_token_id

        for _ in range(max(max_new_tokens - 1, 0)):
            if stop_on_eos and eos_token_id is not None:
                if torch.all(eos_reached).item():
                    break

            decode_timer = CUDATimer()
            decode_timer.start()

            # ENG-087: Wrap decode step in try/finally so decode_timer.stop()
            # always executes, preventing CUDATimer event leaks on exceptions.
            # ENG-088: Also guarantee kv_cache cleanup on decode-step exceptions.
            try:
                with torch.no_grad():
                    # Prepare past_key_values
                    if kv_mode == "fp16" and fp16_use_model_cache and model_cache_for_decode is not None:
                        current_past_key_values = model_cache_for_decode
                    elif kv_mode in _FUSED_KV_MODES or _use_fused:
                        from src.engine.patch_model import INT8CacheWrapperContainer

                        # ENG-033: INT8CacheWrapperContainer is reconstructed each decode step. This is intentional — wrappers are lightweight (no buffer copy), and caching them would require tracking cache mutations.
                        current_past_key_values = INT8CacheWrapperContainer(kv_cache, num_layers)
                    elif kv_mode in ["int8_baseline", "int4_baseline", "kivi_style", "int4_kivi_aligned", "int4_mixed_kv", "int4_ours_asym", "int4_ours_asym_ba"]:
                        # For baseline / KIVI / mixed / role-aware-asym modes, we dequantize BEFORE attention.
                        # For int4_kivi_aligned and int4_ours_asym_ba, inv_tau Q pre-scaling is applied via
                        # hooks registered on model forward (both prefill and decode).
                        current_past_key_values = []
                        for i in range(num_layers):
                            k, v = kv_cache.get_kv(i)
                            current_past_key_values.append((k, v))
                        current_past_key_values = tuple(current_past_key_values)
                    else:
                        current_past_key_values = kv_cache.to_tuple()

                    # Dynamic Cache Check (Skipped for fused wrapper as it mocks Cache)
                    if (
                        kv_mode not in _FUSED_KV_MODES
                        and HAS_DYNAMIC_CACHE
                        and isinstance(current_past_key_values, tuple)
                    ):
                        current_past_key_values = _to_dynamic_cache_safely(current_past_key_values)

                    outputs = model(
                        input_ids=current_token,
                        attention_mask=attention_mask,
                        past_key_values=current_past_key_values,
                        use_cache=True,
                    )
                    if kv_mode == "fp16" and fp16_use_model_cache:
                        model_cache_for_decode = outputs.past_key_values

                    # Update cache with NEW token's KV for non-fused modes.
                    if (
                        kv_mode not in _FUSED_KV_MODES
                        and not _use_fused
                        and not (kv_mode == "fp16" and fp16_use_model_cache)
                    ):
                        if outputs.past_key_values is not None:
                            for i, (k, v) in enumerate(outputs.past_key_values):
                                # Only append the newly produced token when model returns full cache.
                                # This avoids re-quantizing historical tokens already stored in kv_cache.
                                if k.shape[2] > 1:
                                    # ENG-045: The model returned more than one new KV token
                                    # (k.shape[2] > 1). This occurs with speculative decoding
                                    # or models that return the full cumulative cache instead
                                    # of only the new token. We take only the last token to
                                    # avoid re-appending previously cached tokens, but any
                                    # accepted draft tokens beyond the last one are silently
                                    # dropped. Speculative decoding multi-token returns are
                                    # NOT correctly handled by this non-fused decode path.
                                    import warnings
                                    warnings.warn(
                                        f"ENG-045: Layer {i} decode step returned k.shape[2]={k.shape[2]} > 1. "
                                        "Only the last token will be appended to the KV cache. "
                                        "Speculative decoding with multiple accepted tokens is not "
                                        "supported in non-fused mode; extra tokens will be dropped, "
                                        "which may degrade output quality.",
                                        RuntimeWarning,
                                        stacklevel=2,
                                    )
                                    k_new = k[:, :, -1:, :]
                                    v_new = v[:, :, -1:, :]
                                    kv_cache.append(i, k_new, v_new)
                                else:
                                    kv_cache.append(i, k, v)
                        else:
                            # ENG-027: past_key_values is None in decode step for a non-fused
                            # mode. This should not happen under normal circumstances because
                            # use_cache=True is always passed to the model. When it does happen
                            # (e.g. model ignores use_cache, or HF version mismatch), the KV
                            # cache is NOT updated for this decode step, causing the cache to
                            # fall behind by one token. Subsequent decode steps will use a
                            # stale/shorter context, silently degrading output quality.
                            import warnings
                            warnings.warn(
                                f"Decode step returned past_key_values=None for kv_mode={kv_mode!r}. "
                                "The KV cache will NOT be updated for this step, which may degrade "
                                "output quality. Ensure use_cache=True is supported by the model.",
                                RuntimeWarning,
                                stacklevel=2,
                            )

                    next_token_logits = outputs.logits[:, -1, :]
                    next_token = torch.argmax(next_token_logits, dim=-1)  # [B]

                    # ENG-110: Force completed sequences to emit EOS instead of garbage.
                    # Without this, sequences that finished early continue decoding with
                    # stale context, producing meaningless tokens in the output.
                    if stop_on_eos and eos_token_id is not None:
                        next_token = torch.where(
                            eos_reached,
                            torch.full_like(next_token, eos_token_id),
                            next_token,
                        )
                        eos_reached = eos_reached | (next_token == eos_token_id)
            except Exception:
                # ENG-088: Guarantee kv_cache cleanup on decode-step failure.
                _cleanup_kv_cache()
                raise
            finally:
                decode_timer.stop()
            decode_times.add(decode_timer.elapsed_ms)

            generated_steps.append(next_token)
            current_token = next_token.view(batch_size, 1)

            # Update attention mask
            # ENG-034: attention_mask grows O(seq_len^2) each step. The fused path deletes it, but the non-fused path still allocates. Acceptable for current max_seq_len=32K.
            if attention_mask is not None:
                attention_mask = torch.cat(
                    [
                        attention_mask,
                        torch.ones((batch_size, 1), device=model.device, dtype=attention_mask.dtype),
                    ],
                    dim=1,
                )

        # ========== COLLECT RESULTS ==========
        gen_len = int(len(generated_steps))
        gpu_mem_peak_mb = get_gpu_memory_mb()
        kv_cache_mem_mb = 0.0
        kv_cache_seq_len = 0
        if kv_mode == "fp16" and fp16_use_model_cache and model_cache_for_decode is not None:
            kv_cache_mem_mb, kv_cache_seq_len = _cache_stats_from_past_key_values(model_cache_for_decode)
        else:
            try:
                kv_cache_mem_mb = float(kv_cache.get_memory_mb())
            except Exception:
                kv_cache_mem_mb = 0.0
            try:
                kv_cache_seq_len = int(kv_cache.get_seq_len())
            except Exception:
                kv_cache_seq_len = 0

        # TPOT: average decode time (exclude prefill)
        tpot_ms = decode_times.mean_ms if decode_times.count > 0 else 0.0

        # Throughput: report both total tok/s (across batch) and per-sequence tok/s.
        total_decode_ms = decode_times.total_ms
        if total_decode_ms > 0:
            decode_tokens_per_seq = max(gen_len - 1, 0)
            decode_tokens_total = batch_size * decode_tokens_per_seq
            tok_per_s_total = (decode_tokens_total / total_decode_ms) * 1000.0
            tok_per_s_per_seq = tok_per_s_total / max(batch_size, 1)
        else:
            tok_per_s_total = 0.0
            tok_per_s_per_seq = 0.0

        # ENG-018: Handle empty generated_steps when max_new_tokens=0.
        if generated_steps:
            generated_ids = torch.stack(generated_steps, dim=1).to(dtype=torch.long)  # [B, gen_len]
        else:
            generated_ids = torch.empty((batch_size, 0), dtype=torch.long, device=model.device)

        output = GenerationBatchOutput(
            generated_ids=generated_ids,
            ttft_ms=ttft_ms,
            tpot_ms=tpot_ms,
            tok_per_s=float(tok_per_s_total),
            tok_per_s_per_seq=float(tok_per_s_per_seq),
            gpu_mem_peak_mb=float(gpu_mem_peak_mb),
            kv_cache_mem_mb=float(kv_cache_mem_mb),
            kv_cache_seq_len=int(kv_cache_seq_len),
            prompt_len=int(prompt_len),
            gen_len=int(gen_len),
            batch=int(batch_size),
        )

        # ENG-056 + ENG-088: Cleanup kv_cache and intermediates.
        # _cleanup_kv_cache() is also called via the except blocks above if an
        # exception occurs before reaching this point.
        _cleanup_kv_cache()
        try:
            del kv_cache
        except NameError:
            pass
        try:
            del outputs
        except NameError:
            pass
        try:
            del current_past_key_values
        except NameError:
            pass

        gc.collect()
        torch.cuda.empty_cache()

        return output  # inside try so finally always runs before return

    finally:
        # ENG-086 + ENG-103: Guarantee patch removal on ALL exit paths — normal
        # return, exceptions, and early exits.  Without this, the monkey-patched
        # forward_proxy persists for the process lifetime, polluting subsequent
        # generate_from_ids calls with different kv_modes (e.g. fp16 or
        # int8_baseline would still route through the fused proxy's isinstance
        # checks, relying on implicit runtime detection instead of a clean model
        # state).  This is the symmetric counterpart to apply_int8_fused_patch.
        _restore_fused_patch()


def generate(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    prompt: str,
    max_new_tokens: int = 128,
    kv_mode: str = "fp16",
    group_size: int = 128,
    clip_percentile: float = 99.9,
    seed: int = 1234,
    calib_file: Optional[str] = None,
    use_attn_temperature: bool = True,
    use_static_scales: bool = True,
    adaptive_static_scales: bool = False,
    adaptive_static_margin: float = 1.0,
    adaptive_static_k: bool = True,
    adaptive_static_v: bool = True,
    decode_attn_impl: str = "triton_fused",
    allow_missing_calib: bool = False,
    stop_on_eos: bool = True,
    quant_bits: int = 8,
    k_bits: Optional[int] = None,
    v_bits: Optional[int] = None,
) -> GenerationOutput:
    """
    Custom generation loop with prefill + token-by-token decode.

    This function does NOT use model.generate(). Instead, it manually:
    1. Prefill: Process the entire prompt in one forward pass
    2. Decode: Generate tokens one at a time using past_key_values

    Args:
        model: HuggingFace model (AutoModelForCausalLM)
        tokenizer: HuggingFace tokenizer
        prompt: Input text prompt
        max_new_tokens: Maximum number of tokens to generate
        kv_mode: KV cache mode (fp16/int8/int4 variants, plus kivi_style).
            kivi_style mode uses KIVI's asymmetric quantization approach.
        group_size: Group size for quantization
        clip_percentile: Percentile for quantization clipping
        seed: Random seed for reproducibility
        calib_file: Path to calibration JSON (int8_ours only)
        use_attn_temperature: Apply per-head temperature if available (int8_ours)
        use_static_scales: Use static K/V scales from calibration if available (int8_ours)
        adaptive_static_scales: If using static scales, adaptively raise per-token scales
            to avoid clipping at runtime.
        adaptive_static_margin: Multiplicative safety margin applied to static scales before
            adaptive max with observed per-token scales.
        adaptive_static_k: Apply adaptive static-scale safeguard on K.
        adaptive_static_v: Apply adaptive static-scale safeguard on V.
        decode_attn_impl: Decode attention implementation for fused kv modes.
            For kv_mode='kivi_style', torch_ref is enforced.
            - "triton_fused" (mainline, fast)
            - "torch_ref" (reference, correctness/ablation)
        allow_missing_calib: If True, int8_ours will warn+fallback when calib is missing.
        quant_bits: Quantization bits. Used by kv_mode='kivi_style' (must be 4 or 8).
        k_bits: K cache bit-width for int4_mixed_kv mode (4/8/16). Default None → 8.
        v_bits: V cache bit-width for int4_mixed_kv mode (4/8/16). Default None → 4.

    Returns:
        GenerationOutput with generated text and timing statistics

    Raises:
        ValueError: If input is too long or kv_mode is unsupported
        RuntimeError: If CUDA is not available
    """
    # Tokenize input
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    batch_out = generate_from_ids(
        model=model,
        tokenizer=tokenizer,
        input_ids=inputs["input_ids"],
        attention_mask=inputs.get("attention_mask"),
        max_new_tokens=max_new_tokens,
        kv_mode=kv_mode,
        group_size=group_size,
        clip_percentile=clip_percentile,
        seed=seed,
        calib_file=calib_file,
        use_attn_temperature=use_attn_temperature,
        use_static_scales=use_static_scales,
        adaptive_static_scales=adaptive_static_scales,
        adaptive_static_margin=adaptive_static_margin,
        adaptive_static_k=adaptive_static_k,
        adaptive_static_v=adaptive_static_v,
        decode_attn_impl=decode_attn_impl,
        allow_missing_calib=allow_missing_calib,
        stop_on_eos=stop_on_eos,
        quant_bits=quant_bits,
        k_bits=k_bits,
        v_bits=v_bits,
    )

    generated_tokens = batch_out.generated_ids[0].tolist()
    generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True)

    return GenerationOutput(
        text=generated_text,
        tokens=generated_tokens,
        ttft_ms=batch_out.ttft_ms,
        tpot_ms=batch_out.tpot_ms,
        tok_per_s=batch_out.tok_per_s,
        tok_per_s_per_seq=batch_out.tok_per_s_per_seq,
        gpu_mem_peak_mb=batch_out.gpu_mem_peak_mb,
        kv_cache_mem_mb=batch_out.kv_cache_mem_mb,
        kv_cache_seq_len=batch_out.kv_cache_seq_len,
        prompt_len=batch_out.prompt_len,
        gen_len=batch_out.gen_len,
    )
