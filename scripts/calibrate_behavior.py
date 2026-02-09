#!/usr/bin/env python3
"""
F1: KL Calibration Script (scripts/calibrate_behavior.py)

Outputs:
  - artifacts/kv_calib_kl.json (static k/v scales + per-head inv_tau)
  - results/calibration/calibration_stats.csv (optional stats)
  - results/calibration/outlier_profile.png (optional plot)
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

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
) -> torch.Tensor:
    # k: [seq, head_dim], scale: [num_groups]
    head_dim = k.shape[-1]
    num_groups = head_dim // group_size
    k_view = k.view(-1, num_groups, group_size)
    scale_view = scale.view(1, num_groups, 1)
    q = torch.round(k_view / scale_view).clamp(-127, 127)
    k_deq = q * scale_view
    return k_deq.view(-1, head_dim)


def compute_inv_tau(
    q_samples: List[List[torch.Tensor]],
    k_samples: List[List[torch.Tensor]],
    k_scales: List[torch.Tensor],
    num_heads: int,
    num_kv_heads: int,
    head_dim: int,
    group_size: int,
    inv_tau_candidates: List[float],
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
            kl_accum = torch.zeros(len(inv_tau_candidates), dtype=torch.float32)

            for sample_idx in range(len(q_samples)):
                q = q_samples[sample_idx][layer_idx][head_idx].float()  # [D]
                k = k_samples[sample_idx][layer_idx][kv_head].float()   # [S, D]

                logits_fp16 = (q @ k.T) * sm_scale
                p_ref = torch.softmax(logits_fp16, dim=-1)

                k_deq = dequantize_with_scale(k, scale_layer[kv_head].float(), group_size)
                logits_quant = (q @ k_deq.T) * sm_scale

                logits_scaled = logits_quant.unsqueeze(0) * inv_tau_candidates_t[:, None]
                p_quant = torch.softmax(logits_scaled, dim=-1)

                p_ref_safe = torch.clamp(p_ref, min=eps)
                p_quant_safe = torch.clamp(p_quant, min=eps)
                kl = (p_ref_safe * (torch.log(p_ref_safe) - torch.log(p_quant_safe))).sum(dim=-1)
                kl_accum += kl

            best_idx = torch.argmin(kl_accum).item()
            inv_tau_tensor[layer_idx, head_idx] = inv_tau_candidates[best_idx]

    return inv_tau_tensor


def main():
    parser = argparse.ArgumentParser(description="KL calibration for KV cache quantization")
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--seq_len", type=int, default=512)
    parser.add_argument("--out_dir", type=str, default="results/calibration")
    parser.add_argument("--calib_out", type=str, default="artifacts/kv_calib_kl.json")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--run_name", type=str, default=None)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--clip_percentile_k", type=float, default=99.9)
    parser.add_argument("--clip_percentile_v", type=float, default=99.9)
    parser.add_argument("--group_size_k", type=int, default=32)
    parser.add_argument("--group_size_v", type=int, default=32)
    parser.add_argument(
        "--inv_tau_candidates",
        type=str,
        default="0.5,0.7,0.85,1.0,1.2,1.5,2.0",
    )
    args = parser.parse_args()

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

    set_seed(seed=args.seed, deterministic=True)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    calib_out_path = Path(args.calib_out)
    calib_out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading {args.model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()

    dataset = get_calibration_dataset(tokenizer, args.samples, args.seq_len)
    num_layers = getattr(model.config, "num_hidden_layers", 28)
    num_heads = getattr(model.config, "num_attention_heads", 12)
    num_kv_heads = getattr(model.config, "num_key_value_heads", 2)
    head_dim = getattr(model.config, "hidden_size", 1536) // num_heads

    # Collect samples
    k_absmax_samples = [[] for _ in range(num_layers)]
    v_absmax_samples = [[] for _ in range(num_layers)]
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

            q_per_layer = []
            k_per_layer = []
            v_per_layer = []

            for layer_idx in range(num_layers):
                attn = model.model.layers[layer_idx].self_attn
                hs_last = hidden_states[layer_idx][:, -1:, :]
                q = attn.q_proj(hs_last)
                bsz = q.shape[0]
                q = q.view(bsz, 1, attn.num_heads, attn.head_dim).transpose(1, 2)
                q_last = q.squeeze(2).squeeze(0).cpu()  # [num_heads, head_dim]

                k = past_key_values[layer_idx][0].squeeze(0).cpu()  # [kv_heads, seq, head_dim]
                v = past_key_values[layer_idx][1].squeeze(0).cpu()

                q_per_layer.append(q_last)
                k_per_layer.append(k)
                v_per_layer.append(v)

                k_absmax = compute_absmax_per_group(k, args.group_size_k)
                v_absmax = compute_absmax_per_group(v, args.group_size_v)
                k_absmax_samples[layer_idx].append(k_absmax)
                v_absmax_samples[layer_idx].append(v_absmax)

            q_samples.append(q_per_layer)
            k_samples.append(k_per_layer)
            v_samples.append(v_per_layer)

    # Compute static scales (percentile over sample-wise absmax)
    print("Computing static scales...")
    k_scales = []
    v_scales = []
    for layer_idx in range(num_layers):
        k_stack = torch.stack(k_absmax_samples[layer_idx], dim=0)
        v_stack = torch.stack(v_absmax_samples[layer_idx], dim=0)
        k_absmax = torch.quantile(k_stack, args.clip_percentile_k / 100.0, dim=0)
        v_absmax = torch.quantile(v_stack, args.clip_percentile_v / 100.0, dim=0)
        k_scale = k_absmax.clamp(min=1e-5) / 127.0
        v_scale = v_absmax.clamp(min=1e-5) / 127.0
        k_scales.append(k_scale)
        v_scales.append(v_scale)

    # Compute inv_tau (KL minimization)
    print("Computing per-head inv_tau...")
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
    )

    # Save calibration file
    calib_payload = {
        "version": 1,
        "model_id": args.model_id,
        "generated_at": datetime.now().isoformat(),
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
    }

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
            },
        },
    )
    write_config_snapshot(str(out_dir), snapshot)


if __name__ == "__main__":
    main()
