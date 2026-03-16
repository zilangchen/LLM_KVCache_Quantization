#!/usr/bin/env python3
"""
D4: Needle In A Haystack (eval_needle.py)
Strategy A: Synthetic UUID Retrieval.
"""

import argparse
import csv
import json
import sys
import torch
import uuid
import numpy as np
import traceback
from datetime import datetime
from pathlib import Path

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.engine.generate_loop import generate_from_ids
from src.utils.hf import resolve_pretrained_path
from src.utils.repro import (
    build_config_snapshot,
    get_git_commit,  # QUA-001: centralized
    get_hardware_info,
    resolve_quant_bits,
    set_seed,
    write_config_snapshot,
)
from transformers import AutoModelForCausalLM, AutoTokenizer
from scripts.config_utils import load_config, normalize_kv_params, resolve_run_config

EXIT_OOM = 73
EXIT_EXCEPTION = 74
_LAST_ARGS: argparse.Namespace | None = None


def _resolve_out_dir(out_dir_arg: str) -> Path:
    out_dir = Path(out_dir_arg)
    if not out_dir.is_absolute():
        out_dir = project_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _write_task_failure(
    *,
    args: argparse.Namespace,
    failure_type: str,
    message: str,
    exception: Exception | None = None,
) -> None:
    # SEC-004: Traceback/paths in failure JSON are intentional (research CLI tool).
    out_dir = _resolve_out_dir(args.out_dir)
    payload = {
        "script": Path(__file__).name,
        "timestamp": datetime.now().isoformat(),
        "failure_type": str(failure_type),
        "message": str(message),
        "kv_mode": str(getattr(args, "kv_mode", "")),
        "run_name": str(getattr(args, "run_name", "")),
        "seed": int(getattr(args, "seed", 0)),
        "replica_id": int(getattr(args, "replica_id", 0)),
        "context_len": int(getattr(args, "context_len", 0)),
        "num_depths": int(getattr(args, "num_depths", 0)),
    }
    if exception is not None:
        payload["exception_type"] = type(exception).__name__
        payload["exception_repr"] = repr(exception)
        payload["traceback"] = traceback.format_exc()
    path = out_dir / f"task_failure_{Path(__file__).stem}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

def generate_haystack_ids(tokenizer, context_len, needle, depth_percent):
    """
    Generate a haystack token-id list with the needle inserted at depth_percent.
    Haystack is "The quick brown fox..." repeated.
    """
    filler = "The quick brown fox jumps over the lazy dog. " * 50
    filler_tokens = tokenizer.encode(filler, add_special_tokens=False)
    
    # Needle phrasing
    needle_text = f" The special secret passkey is {needle}. Remember it. "
    needle_tokens = tokenizer.encode(needle_text, add_special_tokens=False)
    
    # Target total tokens for the haystack only.
    # Keep a safety margin for system/user template + question + answer.
    target_len = context_len - 100
    if target_len <= 0:
        raise ValueError(f"context_len too small: {context_len}")

    # Ensure the needle is always included even at depth_percent=100.
    filler_len = target_len - len(needle_tokens)
    if filler_len <= 0:
        raise ValueError(
            f"context_len too small to fit needle: context_len={context_len}, "
            f"target_len={target_len}, needle_tokens={len(needle_tokens)}"
        )

    depth_idx = int(filler_len * (depth_percent / 100.0))
    depth_idx = max(0, min(depth_idx, filler_len))

    # Build: filler_before + needle + filler_after, total == target_len.
    current_tokens = []
    while len(current_tokens) < depth_idx:
        current_tokens.extend(filler_tokens)
    current_tokens = current_tokens[:depth_idx]

    current_tokens.extend(needle_tokens)

    remaining = target_len - len(current_tokens)
    while len(current_tokens) < target_len:
        current_tokens.extend(filler_tokens)
    current_tokens = current_tokens[:target_len]

    if remaining < 0:
        # Should not happen; keep as a guard to avoid silent needle truncation.
        raise RuntimeError(
            f"Internal error: haystack overflow. target_len={target_len}, "
            f"len(current_tokens)={len(current_tokens)}"
        )

    return current_tokens

def main():
    global _LAST_ARGS
    parser = argparse.ArgumentParser(description="D4: Needle Evaluation")
    parser.add_argument("--context_len", type=int, default=4096)
    parser.add_argument("--num_depths", type=int, default=10) # How many checkpoints (e.g. 0, 10, ... 100)
    parser.add_argument(
        "--depth_batch",
        type=int,
        default=1,
        help=(
            "Batch multiple depths per forward pass. Requires equal-length prompts and no padding. "
            "Recommended: 2-8 on H20."
        ),
    )
    parser.add_argument(
        "--needle_max_new_tokens",
        type=int,
        default=64,
        help="Maximum tokens to generate for the answer span.",
    )
    parser.add_argument(
        "--report_exact_match",
        action="store_true",
        default=False,
        help=(
            "Also compute exact-match stats (generated_text.strip()==needle) for appendix; "
            "main pass criterion remains contains."
        ),
    )
    # NOTE: scripts/run_experiments.py passes --seq_len/--gen_len for all tasks. Needle eval uses
    # --context_len and a fixed generation length; accept these args for compatibility.
    parser.add_argument(
        "--seq_len",
        type=int,
        default=None,
        help="Alias for --context_len (run_experiments compatibility).",
    )
    parser.add_argument(
        "--gen_len",
        type=int,
        default=None,
        help="Ignored. Needle eval uses a fixed short generation length.",
    )
    parser.add_argument(
        "--kv_mode",
        type=str,
        default="fp16",
        choices=[
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
        ],
    )
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument(
        "--model_revision",
        type=str,
        default=None,
        help="Optional model revision (commit hash/tag) for strict reproducibility.",
    )
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--run_name", type=str, default=None)
    # Schema args
    parser.add_argument("--group_size", type=int, default=128)
    parser.add_argument("--clip_percentile", type=float, default=99.9)
    parser.add_argument("--group_size_k", type=int, default=None)
    parser.add_argument("--group_size_v", type=int, default=None)
    parser.add_argument("--clip_percentile_k", type=float, default=None)
    parser.add_argument("--clip_percentile_v", type=float, default=None)
    parser.add_argument("--calib_strategy", type=str, default=None)
    parser.add_argument("--decode_attn_impl", type=str, default=None)
    parser.add_argument("--calib_file", type=str, default=None)
    parser.add_argument(
        "--quant_bits",
        type=int,
        default=None,
        help="Override quant_bits for CSV output (needed for kivi_style which can be 4 or 8).",
    )
    parser.add_argument(
        "--use_attn_temperature",
        dest="use_attn_temperature",
        action="store_true",
        default=True,
        help="Apply per-head temperature if available (int8_ours).",
    )
    parser.add_argument(
        "--no_use_attn_temperature",
        dest="use_attn_temperature",
        action="store_false",
        help="Disable per-head temperature even if calib provides it.",
    )
    parser.add_argument(
        "--use_static_scales",
        dest="use_static_scales",
        action="store_true",
        default=True,
        help="Use static K/V scales from calibration if available (int8_ours).",
    )
    parser.add_argument(
        "--no_use_static_scales",
        dest="use_static_scales",
        action="store_false",
        help="Ignore static K/V scales from calibration (int8_ours).",
    )
    parser.add_argument(
        "--adaptive_static_scales",
        dest="adaptive_static_scales",
        action="store_true",
        default=False,
        help="Adaptively raise static scales with runtime observed scales (int8_ours).",
    )
    parser.add_argument(
        "--no_adaptive_static_scales",
        dest="adaptive_static_scales",
        action="store_false",
        help="Disable adaptive static-scale safeguard.",
    )
    parser.add_argument(
        "--adaptive_static_margin",
        type=float,
        default=1.0,
        help="Safety margin multiplier for static scales before adaptive max.",
    )
    parser.add_argument(
        "--adaptive_static_k",
        dest="adaptive_static_k",
        action="store_true",
        default=True,
        help="Apply adaptive static-scale safeguard on K.",
    )
    parser.add_argument(
        "--no_adaptive_static_k",
        dest="adaptive_static_k",
        action="store_false",
        help="Disable adaptive static-scale safeguard on K.",
    )
    parser.add_argument(
        "--adaptive_static_v",
        dest="adaptive_static_v",
        action="store_true",
        default=True,
        help="Apply adaptive static-scale safeguard on V.",
    )
    parser.add_argument(
        "--no_adaptive_static_v",
        dest="adaptive_static_v",
        action="store_false",
        help="Disable adaptive static-scale safeguard on V.",
    )
    parser.add_argument("--save_csv", action="store_true", default=True)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument(
        "--replica_id",
        type=int,
        default=0,
        help="Replica id for repeated runs (set by run_experiments multi-seed loop).",
    )
    parser.add_argument("--out_dir", type=str, default="results/runs")

    args = parser.parse_args()
    _LAST_ARGS = args

    if args.config and args.run_name:
        cfg = load_config(args.config)
        resolved = resolve_run_config(cfg, args.run_name)
        for key, value in resolved.items():
            if value is not None:
                setattr(args, key, value)

    # Apply aliasing for matrix-runner compatibility.
    if args.seq_len is not None:
        args.context_len = args.seq_len

    normalize_kv_params(args)
    set_seed(seed=args.seed, deterministic=True)

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
        trust_remote_code=True
    )

    depths = np.linspace(0, 100, args.num_depths)
    results = []
    timestamp = datetime.now().isoformat()
    git_commit = get_git_commit()
    hardware = get_hardware_info()

    print(f"Running Needle Test (Context: {args.context_len}, Depths: {args.num_depths})...")

    pass_count = 0
    exact_pass_count = 0
    rng = np.random.default_rng(args.seed)
    depth_batch = max(int(args.depth_batch), 1)

    prefix_text = (
        "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
        "<|im_start|>user\n"
    )
    suffix_text = (
        "\n\nWhat is the special passkey mentioned in the text?\n"
        "Reply with the passkey only (verbatim), no extra words.<|im_end|>\n"
        "<|im_start|>assistant\n"
    )
    prefix_ids = tokenizer.encode(prefix_text, add_special_tokens=False)
    suffix_ids = tokenizer.encode(suffix_text, add_special_tokens=False)

    prompt_ids_list = []
    needles = []
    depth_values = []
    
    for depth in depths:
        needle = str(uuid.UUID(bytes=rng.bytes(16)))
        haystack_ids = generate_haystack_ids(tokenizer, args.context_len, needle, depth)
        haystack_text = tokenizer.decode(haystack_ids, skip_special_tokens=True)
        if needle not in haystack_text:
            raise RuntimeError(
                "Needle not present in generated haystack. "
                f"context_len={args.context_len} depth={float(depth):.1f} needle={needle}"
            )

        prompt_ids = prefix_ids + haystack_ids + suffix_ids
        prompt_ids_list.append(prompt_ids)
        needles.append(needle)
        depth_values.append(float(depth))

    if not prompt_ids_list:
        raise RuntimeError("No prompts were generated for needle evaluation.")

    prompt_len = len(prompt_ids_list[0])
    for idx, ids in enumerate(prompt_ids_list):
        if len(ids) != prompt_len:
            raise RuntimeError(
                "Needle batch requires equal-length prompts, but found mismatch: "
                f"idx0_len={prompt_len} idx{idx}_len={len(ids)}"
            )

    for start in range(0, len(prompt_ids_list), depth_batch):
        batch_prompts = prompt_ids_list[start : start + depth_batch]
        batch_needles = needles[start : start + depth_batch]
        batch_depths = depth_values[start : start + depth_batch]

        input_ids = torch.tensor(batch_prompts, dtype=torch.long, device=model.device)
        attention_mask = torch.ones_like(input_ids, dtype=torch.long, device=model.device)

        out = generate_from_ids(
            model=model,
            tokenizer=tokenizer,
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=args.needle_max_new_tokens,
            kv_mode=args.kv_mode,
            group_size=args.group_size,
            clip_percentile=args.clip_percentile,
            calib_file=args.calib_file,
            use_attn_temperature=args.use_attn_temperature,
            use_static_scales=args.use_static_scales,
            adaptive_static_scales=args.adaptive_static_scales,
            adaptive_static_margin=args.adaptive_static_margin,
            adaptive_static_k=args.adaptive_static_k,
            adaptive_static_v=args.adaptive_static_v,
            decode_attn_impl=args.decode_attn_impl or "triton_fused",
            seed=args.seed,
            stop_on_eos=True,
            quant_bits=getattr(args, 'quant_bits', None),
        )

        gen_ids = out.generated_ids
        for j in range(gen_ids.shape[0]):
            generated_text = tokenizer.decode(
                gen_ids[j].tolist(), skip_special_tokens=True
            )
            needle = batch_needles[j]
            depth = batch_depths[j]
            passed = needle in generated_text
            exact_match = generated_text.strip() == needle
            if passed:
                pass_count += 1
            if exact_match:
                exact_pass_count += 1

            print(
                f"Depth {depth:.1f}%: {'PASS' if passed else 'FAIL'} "
                f"(Needle: {needle} vs Gen: {generated_text.strip()})"
            )

            results.append(
                {
                    "depth": depth,
                    "passed": int(passed),
                    "exact_match": int(exact_match),
                    "needle": needle,
                    "generated_text": generated_text.strip(),
                }
            )

    pass_rate = (pass_count / len(depths)) * 100
    exact_match_rate = (exact_pass_count / len(depths)) * 100 if len(depths) > 0 else 0.0
    print(f"\nFinal Pass Rate: {pass_rate:.2f}%")
    if args.report_exact_match:
        print(f"Exact Match Rate: {exact_match_rate:.2f}%")

    if args.save_csv:
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = project_root / out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"profile_needle_{args.kv_mode}_{timestamp.replace(':','-')}.csv"
        details_path = out_dir / f"needle_details_{args.kv_mode}_{timestamp.replace(':','-')}.csv"
        
        row = {
            "run_id": f"needle_{timestamp}",
            "model_id": args.model_id,
            "run_name": args.run_name,
            "kv_mode": args.kv_mode,
            "quant_bits": resolve_quant_bits(
                args.kv_mode,
                getattr(args, "quant_bits", None),
            ),
            "clip_percentile": args.clip_percentile,
            "group_size": args.group_size,
            "dtype": str(model.dtype),
            "hardware": f"{hardware['gpu']} ({hardware['gpu_memory']})",
            "seq_len": args.context_len,
            "gen_len": args.needle_max_new_tokens,
            "batch": int(depth_batch),
            "ttft_ms": 0,
            "tpot_ms": 0,
            "tok_per_s": 0,
            "gpu_mem_peak_mb": 0,
            "timestamp": timestamp,
            "git_commit": git_commit,
            "seed": int(args.seed),
            "replica_id": int(args.replica_id),
            "needle_pass_rate": pass_rate,
            "needle_exact_match_rate": exact_match_rate,
        }
        
        fields = [
            "run_id", "model_id", "run_name", "kv_mode", "quant_bits", "clip_percentile", "group_size",
            "dtype", "hardware", "seq_len", "gen_len", "batch", "ttft_ms", "tpot_ms",
            "tok_per_s",
            "gpu_mem_peak_mb",
            "timestamp",
            "git_commit",
            "seed",
            "replica_id",
            "needle_pass_rate",
            "needle_exact_match_rate",
        ]
        
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerow(row)
        print(f"Saved to {path}")

        detail_fields = [
            "run_id",
            "run_name",
            "seed",
            "replica_id",
            "kv_mode",
            "context_len",
            "depth",
            "passed",
            "exact_match",
            "needle",
            "generated_text",
        ]
        with open(details_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=detail_fields)
            writer.writeheader()
            for r in results:
                writer.writerow(
                    {
                        "run_id": row["run_id"],
                        "run_name": args.run_name,
                        "seed": int(args.seed),
                        "replica_id": int(args.replica_id),
                        "kv_mode": args.kv_mode,
                        "context_len": args.context_len,
                        "depth": r["depth"],
                        "passed": r["passed"],
                        "exact_match": r["exact_match"],
                        "needle": r["needle"],
                        "generated_text": r["generated_text"],
                    }
                )
        print(f"Saved needle details to {details_path}")

        run_snapshot_dir = out_dir / row["run_id"]
        snapshot = build_config_snapshot(
            script_name=Path(__file__).name,
            args=args,
        )
        write_config_snapshot(str(run_snapshot_dir), snapshot)

if __name__ == "__main__":
    try:
        main()
    except torch.cuda.OutOfMemoryError as exc:
        print("OOM")
        if _LAST_ARGS is not None:
            _write_task_failure(
                args=_LAST_ARGS,
                failure_type="oom",
                message="CUDA out of memory during eval_needle execution.",
                exception=exc,
            )
        sys.exit(EXIT_OOM)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {type(exc).__name__}: {exc}")
        if _LAST_ARGS is not None:
            _write_task_failure(
                args=_LAST_ARGS,
                failure_type="exception",
                message="Unhandled exception during eval_needle execution.",
                exception=exc,
            )
        sys.exit(EXIT_EXCEPTION)
