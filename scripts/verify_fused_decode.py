#!/usr/bin/env python3
"""
Verify fused INT8 decode path against a reference path.

This script compares logits from:
  - Fused INT8 decode (Triton kernel via patch_model)
  - Reference decode (dequantized INT8 cache or FP16 cache)

Usage:
  python scripts/verify_fused_decode.py --prompt "Hello world" --kv_mode int8_fused
"""

import argparse
import json
import os
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.cache import FP16KVCache, INT8KVCache
from src.engine.patch_model import apply_int8_fused_patch, INT8CacheWrapperContainer
from src.utils.repro import set_seed


def load_calibration(
    kv_mode: str,
    calib_file: str | None,
    group_size: int,
    clip_percentile: float,
    device: torch.device,
    use_attn_temperature: bool,
):
    static_k_scale = None
    static_v_scale = None
    inv_tau = None

    if kv_mode != "int8_ours":
        return static_k_scale, static_v_scale, inv_tau, group_size, clip_percentile

    import warnings
    calib_path = calib_file or os.path.join("artifacts", "kv_calib_kl.json")
    if calib_path and os.path.exists(calib_path):
        try:
            with open(calib_path, "r") as f:
                calib = json.load(f)
            calib_group_k = calib.get("group_size_k", calib.get("group_size", group_size))
            calib_group_v = calib.get("group_size_v", calib.get("group_size", group_size))
            calib_clip_k = calib.get("clip_percentile_k", calib.get("clip_percentile", clip_percentile))
            calib_clip_v = calib.get("clip_percentile_v", calib.get("clip_percentile", clip_percentile))

            if calib_group_k and calib_group_v and calib_group_k != calib_group_v:
                warnings.warn(
                    f"Calibration group_size_k ({calib_group_k}) != group_size_v ({calib_group_v}); "
                    "using group_size_k for both.",
                    UserWarning,
                )
            if calib_clip_k and calib_clip_v and calib_clip_k != calib_clip_v:
                warnings.warn(
                    f"Calibration clip_percentile_k ({calib_clip_k}) != clip_percentile_v ({calib_clip_v}); "
                    "using clip_percentile_k for both.",
                    UserWarning,
                )

            group_size = calib_group_k or group_size
            clip_percentile = calib_clip_k or clip_percentile

            if "k_scale" in calib:
                static_k_scale = torch.tensor(calib["k_scale"], dtype=torch.float16, device=device)
            if "v_scale" in calib:
                static_v_scale = torch.tensor(calib["v_scale"], dtype=torch.float16, device=device)
            if use_attn_temperature and "inv_tau" in calib:
                inv_tau = torch.tensor(calib["inv_tau"], dtype=torch.float32, device=device)
        except Exception as exc:
            warnings.warn(
                f"Failed to load calibration file {calib_path}: {exc}. "
                "Falling back to baseline int8 behavior.",
                UserWarning,
            )
    else:
        warnings.warn(
            f"Calibration file not found: {calib_path}. "
            "Falling back to baseline int8 behavior.",
            UserWarning,
        )

    return static_k_scale, static_v_scale, inv_tau, group_size, clip_percentile


def build_kv_cache(
    kv_mode: str,
    model,
    group_size: int,
    clip_percentile: float,
    calib_file: str | None,
    use_attn_temperature: bool,
):
    num_layers = getattr(model.config, "num_hidden_layers", 28)
    static_k_scale, static_v_scale, inv_tau, group_size, clip_percentile = load_calibration(
        kv_mode,
        calib_file,
        group_size,
        clip_percentile,
        model.device,
        use_attn_temperature,
    )

    if kv_mode == "fp16":
        return FP16KVCache(num_layers=num_layers, device=model.device.type)

    return INT8KVCache(
        num_layers=num_layers,
        device=model.device.type,
        clip_percentile=clip_percentile,
        group_size=group_size,
        static_k_scale=static_k_scale,
        static_v_scale=static_v_scale,
        inv_tau=inv_tau,
        use_attn_temperature=use_attn_temperature,
    )


def main():
    parser = argparse.ArgumentParser(description="Verify fused decode path")
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--prompt", type=str, default="Hello, I am a language model.")
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--kv_mode", type=str, default="int8_fused", choices=["int8_fused", "int8_ours"])
    parser.add_argument("--group_size", type=int, default=128)
    parser.add_argument("--clip_percentile", type=float, default=99.9)
    parser.add_argument("--calib_file", type=str, default=None)
    parser.add_argument("--use_attn_temperature", action="store_true", default=True)
    parser.add_argument(
        "--ref_mode",
        type=str,
        default="int8_dequant",
        choices=["int8_dequant", "fp16_cache"],
        help="Reference path for comparison.",
    )
    parser.add_argument("--max_abs_tol", type=float, default=0.5)
    parser.add_argument("--mean_abs_tol", type=float, default=0.05)
    args = parser.parse_args()

    set_seed(seed=args.seed, deterministic=True)

    if not torch.cuda.is_available():
        print("CUDA is required for fused verification.")
        sys.exit(1)

    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    model_ref = AutoModelForCausalLM.from_pretrained(
        args.model_id, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True
    )
    model_fused = AutoModelForCausalLM.from_pretrained(
        args.model_id, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True
    )

    apply_int8_fused_patch(model_fused)

    inputs = tokenizer(args.prompt, return_tensors="pt").to(model_ref.device)
    input_ids = inputs["input_ids"]
    attention_mask = inputs.get("attention_mask")

    with torch.no_grad():
        outputs_ref = model_ref(
            input_ids=input_ids,
            attention_mask=attention_mask,
            use_cache=True,
            output_hidden_states=False,
        )

    kv_cache = build_kv_cache(
        args.kv_mode,
        model_fused,
        args.group_size,
        args.clip_percentile,
        args.calib_file,
        args.use_attn_temperature,
    )
    for i, (k, v) in enumerate(outputs_ref.past_key_values):
        kv_cache.append(i, k, v)

    current_token = input_ids[:, -1:]
    if attention_mask is None:
        attention_mask = torch.ones_like(input_ids)

    # Fused logits
    fused_past = INT8CacheWrapperContainer(kv_cache, kv_cache.num_layers)
    with torch.no_grad():
        outputs_fused = model_fused(
            input_ids=current_token,
            attention_mask=attention_mask,
            past_key_values=fused_past,
            use_cache=True,
        )
    logits_fused = outputs_fused.logits[:, -1, :]

    # Reference logits
    if args.ref_mode == "fp16_cache":
        past_key_values_ref = outputs_ref.past_key_values
    else:
        past_key_values_ref = tuple(kv_cache.get_kv(i) for i in range(kv_cache.num_layers))

    with torch.no_grad():
        outputs_ref_step = model_ref(
            input_ids=current_token,
            attention_mask=attention_mask,
            past_key_values=past_key_values_ref,
            use_cache=True,
        )
    logits_ref = outputs_ref_step.logits[:, -1, :]

    diff = (logits_fused - logits_ref).abs()
    max_abs = diff.max().item()
    mean_abs = diff.mean().item()
    top1_match = torch.argmax(logits_fused, dim=-1).item() == torch.argmax(logits_ref, dim=-1).item()

    print(f"max_abs_diff={max_abs:.6f} mean_abs_diff={mean_abs:.6f} top1_match={top1_match}")
    if max_abs > args.max_abs_tol or mean_abs > args.mean_abs_tol:
        print("❌ Fused decode differs beyond tolerance.")
        sys.exit(2)
    print("✅ Fused decode within tolerance.")


if __name__ == "__main__":
    main()
