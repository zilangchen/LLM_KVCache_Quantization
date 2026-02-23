#!/usr/bin/env python3
"""
F1: Behavior-Aligned Calibration Script (scripts/calibrate_behavior.py)

Supports KL divergence (default) and MSE loss functions for calibration
via --loss_function {kl, mse}.

Loss semantics:
  - KL path uses probability-safe clamping before log to avoid numerical issues.
  - MSE path compares raw attention probabilities without clamping.
  - KL and MSE absolute values are different scales; ranking is only comparable
    within the same loss_function.

Outputs:
  - artifacts/kv_calib_kl.json (static k/v scales + per-head inv_tau)
  - results/calibration/calibration_stats.csv (optional stats)
  - results/calibration/search_trials.csv (if --search)
  - results/calibration/outlier_profile.png (optional plot)
"""

import argparse
import json
import os
import sys
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


def resolve_kv_params(run_entry: dict, quant_defaults: dict) -> Tuple[float, float, int, int]:
    clip_k = run_entry.get(
        "clip_percentile_k",
        run_entry.get("clip_percentile", quant_defaults.get("clip_percentile_k", 99.9)),
    )
    clip_v = run_entry.get(
        "clip_percentile_v",
        run_entry.get("clip_percentile", quant_defaults.get("clip_percentile_v", 99.9)),
    )
    group_k = run_entry.get(
        "group_size_k",
        run_entry.get("group_size", quant_defaults.get("group_size_k", 128)),
    )
    group_v = run_entry.get(
        "group_size_v",
        run_entry.get("group_size", quant_defaults.get("group_size_v", 128)),
    )
    return clip_k, clip_v, group_k, group_v


def get_calibration_dataset(tokenizer, n_samples=128, seq_len=512):
    print("Loading WikiText-2 for calibration...")
    try:
        data = load_dataset("wikitext", "wikitext-2-raw-v1", split="test")
    except Exception:
        print("Warning: Failed to load WikiText-2. Using dummy data.")
        return ["This is a test sentence for calibration. " * 20] * n_samples

    encodings = []
    for text in data["text"]:
        if len(text.strip()) > 0:
            enc = tokenizer(text, return_tensors="pt")["input_ids"]
            if enc.size(1) > seq_len:
                enc = enc[:, :seq_len]
            encodings.append(enc)
            if len(encodings) >= n_samples:
                break
    return encodings


def compute_absmax_per_group(tensor: torch.Tensor, group_size: int) -> torch.Tensor:
    # tensor: [heads, seq, head_dim]
    heads, seq_len, head_dim = tensor.shape
    num_groups = head_dim // group_size
    view = tensor.view(heads, seq_len, num_groups, group_size)
    return view.abs().amax(dim=3).amax(dim=1)  # [heads, num_groups]


def dequantize_with_scale(
    k: torch.Tensor,
    scale: torch.Tensor,
    group_size: int,
    qmax: int = 127,
) -> torch.Tensor:
    # k: [seq, head_dim], scale: [num_groups]
    head_dim = k.shape[-1]
    num_groups = head_dim // group_size
    k_view = k.view(-1, num_groups, group_size)
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
                    # We intentionally avoid clamping here to preserve true squared error.
                    mse = ((p_ref.unsqueeze(0) - p_quant) ** 2).sum(dim=-1)
                    loss_accum += mse
                else:
                    # KL divergence (default)
                    p_ref_safe = torch.clamp(p_ref, min=eps)
                    p_quant_safe = torch.clamp(p_quant, min=eps)
                    kl = (p_ref_safe * (torch.log(p_ref_safe) - torch.log(p_quant_safe))).sum(dim=-1)
                    loss_accum += kl

            # Normalise by sample count so result is independent of --samples.
            num_samples = len(q_samples)
            if num_samples > 0:
                loss_accum /= num_samples
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
                    # MSE uses raw softmax probabilities (no clamping required).
                    mse = ((p_ref - p_quant) ** 2).sum().item()
                    loss_values.append(float(mse))
                else:
                    # KL divergence (default)
                    p_ref_safe = torch.clamp(p_ref, min=eps)
                    p_quant_safe = torch.clamp(p_quant, min=eps)
                    kl = (p_ref_safe * (torch.log(p_ref_safe) - torch.log(p_quant_safe))).sum().item()
                    loss_values.append(float(kl))

    if loss_values:
        mean_loss = float(np.mean(loss_values))
        p95_loss = float(np.quantile(np.array(loss_values, dtype=np.float64), 0.95))
        max_loss = float(np.max(loss_values))
    else:
        mean_loss = 0.0
        p95_loss = 0.0
        max_loss = 0.0

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
    if not trials:
        raise ValueError("No candidate trials found for calibration selection.")

    # Determine loss metric key prefix based on objective and loss_function.
    # For explicit mean_kl/mean_mse objectives, the key is in the objective name.
    # For "robust", derive from loss_function.
    # NOTE: KL and MSE are different numeric scales; ranking is only meaningful
    # within one selected loss_function.
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

    if objective in ("mean_kl", "mean_mse"):
        ranked = sorted(
            trials,
            key=lambda x: (
                x[mean_key],
                x[p95_key],
                x["k_clip_rate"] + x["v_clip_rate"],
                x["group_size"],
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
                x["group_size"],
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
            x["group_size"],
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
    scales: List[torch.Tensor] = []
    for layer_idx in range(len(absmax_samples)):
        # torch.quantile requires float32/float64
        stack = torch.stack(absmax_samples[layer_idx], dim=0).float()
        absmax = torch.quantile(stack, clip_percentile / 100.0, dim=0)
        scales.append(absmax.clamp(min=1e-5) / float(qmax))
    return scales


def validate_group_size(head_dim: int, group_size: int, name: str) -> None:
    if group_size <= 0:
        raise ValueError(f"{name} must be > 0, got {group_size}.")
    if head_dim % group_size != 0:
        raise ValueError(
            f"{name} must divide head_dim exactly. head_dim={head_dim}, {name}={group_size}."
        )


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
    parser.add_argument("--samples", type=int, default=16)
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
    args = parser.parse_args()
    if args.int4_search:
        args.quant_bits = 4

    if args.config and args.run_name:
        cfg = load_config(args.config)
        resolved = resolve_run_config(cfg, args.run_name)
        for key, value in resolved.items():
            if value is not None:
                setattr(args, key, value)

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

    set_seed(seed=args.seed, deterministic=True)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Default output path reflects loss function to avoid overwriting.
    if args.calib_out is None:
        args.calib_out = f"artifacts/kv_calib_{args.loss_function}.json"
    calib_out_path = Path(args.calib_out)
    calib_out_path.parent.mkdir(parents=True, exist_ok=True)

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
                attn = model.model.layers[layer_idx].self_attn
                hs_last = hidden_states[layer_idx][:, -1:, :]
                q = attn.q_proj(hs_last)
                bsz = q.shape[0]
                q = q.view(bsz, 1, num_heads, head_dim).transpose(1, 2)
                q_last = q.squeeze(2).squeeze(0).cpu()  # [num_heads, head_dim]

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

        loss_pfx_sort = "mse" if args.loss_function == "mse" else "kl"
        trials_sorted = sorted(
            trials,
            key=lambda x: (
                x[f"p95_{loss_pfx_sort}"],
                x[f"mean_{loss_pfx_sort}"],
                x["k_clip_rate"] + x["v_clip_rate"],
                x.get("outlier_rescue_ratio", 0.0),
                x["group_size"],
                x["clip_percentile"],
            ),
        )
        for rank_idx, trial in enumerate(trials_sorted, start=1):
            trial["rank"] = rank_idx

        trials_csv_path = out_dir / "search_trials.csv"
        with open(trials_csv_path, "w") as f:
            f.write(
                "rank,group_size,clip_percentile,outlier_rescue_ratio,mixed_rescue,"
                f"mean_{loss_pfx_sort},p95_{loss_pfx_sort},max_{loss_pfx_sort},"
                "k_clip_rate,v_clip_rate,v_rel_l2_mean,feasible\n"
            )
            for t in trials_sorted:
                f.write(
                    f"{t['rank']},{t['group_size']},{t['clip_percentile']},"
                    f"{t.get('outlier_rescue_ratio', 0.0)},{t.get('mixed_rescue', 0)},"
                    f"{t[f'mean_{loss_pfx_sort}']},{t[f'p95_{loss_pfx_sort}']},"
                    f"{t[f'max_{loss_pfx_sort}']},"
                    f"{t['k_clip_rate']},{t['v_clip_rate']},{t['v_rel_l2_mean']},"
                    f"{int(bool(t['feasible']))}\n"
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

    # Save calibration file
    calib_payload = {
        "version": 1,
        "model_id": args.model_id,
        "generated_at": datetime.now().isoformat(),
        "loss_function": args.loss_function,
        "quant_bits": int(args.quant_bits),
        "qmax": int(qmax),
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
        "inv_tau_candidates": inv_tau_candidates,
        "int4_outlier_ratio": float(args.int4_outlier_ratio),
        "int4_mixed_rescue": bool(args.int4_mixed_rescue),
    }
    if selection is not None:
        calib_payload["selection"] = selection

    with open(calib_out_path, "w") as f:
        json.dump(calib_payload, f, indent=2)
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
