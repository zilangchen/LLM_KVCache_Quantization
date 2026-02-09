#!/usr/bin/env python3
"""
D3: Perplexity Evaluation Script (eval_ppl.py)
Uses wikitext-2-raw-v1 to measure PPL.
"""

import argparse
import csv
import json
import os
import sys
import torch
from tqdm import tqdm
from datetime import datetime
from pathlib import Path
import subprocess

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

# Import engine logic if needed, but for PPL we mostly need model forward
# However, to support 'kv_mode' we might need to hook our cache?
# Actually PPL is usually done via model(input_ids, past_key_values=...)
# To truly evaluate OUR cache, we should use our engine or a adapted loop.
# But standard PPL is effectively "prefill" of long sequence.
# Let's implementation standard sliding window using HuggingFace loop FIRST,
# but if we want to test "int8_cache", we need our custom cache.
# LIMITATION: Standard HF `model()` doesn't easily use our `KVCache` class unless we patch it.
# DECISION: For Milestone D, "System Efficacy" means running PPL on the QUANTIZED model/cache.
# If we cannot plug our cache into HF `model()`, we must use our `generate` or `prefill` loop?
# Wait, PPL is next-token prediction loss. We can do this via our engine's prefill?
# Currently `generate_loop.py` separates prefill and decode.
# PPL = exp(mean(nll)). 
# We need logits for the targets.
# Let's use standard HF approach for now to establish baseline PPL (fp16).
# For INT8 support, if we modify the model to use our Cache, we can still use HF loop.
# But we haven't modified the model yet (Milestone E/F).
# So for D3, we implement standard HF sliding window.
# When we reach E/F and patch the model, this script will naturally pick it up if we load the patched model.
# Or we can manually feed batches.

from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset
from src.cache import FP16KVCache, INT8KVCache, INT4KVCache
from src.engine.patch_model import apply_int8_fused_patch
from src.utils.repro import (
    build_config_snapshot,
    get_hardware_info,
    set_seed,
    write_config_snapshot,
)
from scripts.config_utils import load_config, normalize_kv_params, resolve_run_config

def get_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=project_root,
        )
        return result.stdout.strip()[:8]
    except Exception:
        return "unknown"


def iter_token_ids(dataset, tokenizer, max_tokens):
    sep_ids = tokenizer("\n\n", add_special_tokens=False).input_ids
    first_doc = True
    total_tokens = 0

    for row in dataset:
        if max_tokens is not None and total_tokens >= max_tokens:
            break

        text = row.get("text", "")
        if not text or not text.strip():
            continue

        ids = tokenizer(text, add_special_tokens=False).input_ids
        if not ids:
            continue

        if not first_doc and sep_ids:
            ids = sep_ids + ids
        first_doc = False

        if max_tokens is not None:
            remaining = max_tokens - total_tokens
            if remaining <= 0:
                break
            if len(ids) > remaining:
                ids = ids[:remaining]

    total_tokens += len(ids)
    yield ids


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

    if kv_mode == "int4_baseline":
        return INT4KVCache(
            num_layers=num_layers,
            device=model.device.type,
            clip_percentile=clip_percentile,
            group_size=group_size,
        )

    if kv_mode in ["int8_fused", "int8_ours"]:
        apply_int8_fused_patch(model)

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


def build_past_key_values(kv_mode: str, kv_cache, num_layers: int):
    if kv_cache.get_seq_len() == 0:
        return None, True

    if kv_mode in ["int8_fused", "int8_ours"]:
        from src.engine.patch_model import INT8CacheWrapperContainer
        return INT8CacheWrapperContainer(kv_cache, num_layers), False

    if kv_mode == "fp16":
        return kv_cache.to_tuple(), True

    current_past_key_values = []
    for i in range(num_layers):
        k, v = kv_cache.get_kv(i)
        current_past_key_values.append((k, v))
    return tuple(current_past_key_values), True


def eval_window_kv_cache(
    model,
    input_ids: torch.Tensor,
    trg_len: int,
    kv_cache,
    kv_mode: str,
):
    num_layers = getattr(model.config, "num_hidden_layers", 28)
    seq_len = input_ids.size(1)
    start_loss_idx = max(seq_len - trg_len, 0)

    kv_cache.clear()
    attention_mask = torch.ones((1, 1), device=model.device, dtype=torch.long)
    current_token = input_ids[:, 0:1]

    total_nll = torch.tensor(0.0, device=model.device)
    total_tokens = 0

    with torch.no_grad():
        for t in range(seq_len - 1):
            past_key_values, should_update_cache = build_past_key_values(
                kv_mode, kv_cache, num_layers
            )

            outputs = model(
                input_ids=current_token,
                attention_mask=attention_mask,
                past_key_values=past_key_values,
                use_cache=True,
            )

            next_token = input_ids[:, t + 1 : t + 2]
            logits = outputs.logits[:, -1, :]
            log_probs = torch.log_softmax(logits, dim=-1)
            nll = -log_probs.gather(dim=-1, index=next_token).squeeze(-1)

            pred_idx = t + 1
            if pred_idx >= start_loss_idx:
                total_nll += nll
                total_tokens += 1

            if should_update_cache and outputs.past_key_values is not None:
                for i, (k, v) in enumerate(outputs.past_key_values):
                    if k.shape[2] > 1:
                        k_new = k[:, :, -1:, :]
                        v_new = v[:, :, -1:, :]
                        kv_cache.append(i, k_new, v_new)
                    else:
                        kv_cache.append(i, k, v)

            attention_mask = torch.cat(
                [attention_mask, torch.ones((1, 1), device=model.device, dtype=attention_mask.dtype)],
                dim=1,
            )
            current_token = next_token

    return total_nll, total_tokens


def main():
    parser = argparse.ArgumentParser(description="D3: PPL Evaluation")
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    # PPL specific
    parser.add_argument("--stride", type=int, default=512)
    parser.add_argument(
        "--max_length",
        type=int,
        default=1024,
        help="Context window for PPL.",
    )
    parser.add_argument(
        "--max_samples",
        type=int,
        default=None,
        help="Limit total tokens to max_samples * max_length",
    )
    
    # Schema filler args
    parser.add_argument(
        "--kv_mode",
        type=str,
        default="fp16",
        choices=["fp16", "int8_baseline", "int8_fused", "int8_ours", "int4_baseline"],
    )
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
    parser.add_argument("--save_csv", action="store_true", default=True)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--out_dir", type=str, default="results/runs")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--run_name", type=str, default=None)
    parser.add_argument(
        "--ppl_mode",
        type=str,
        default="hf",
        choices=["hf", "kv_cache"],
        help="PPL evaluation mode: hf (standard) or kv_cache (uses custom KV cache).",
    )

    args = parser.parse_args()

    if args.config and args.run_name:
        cfg = load_config(args.config)
        resolved = resolve_run_config(cfg, args.run_name)
        for key, value in resolved.items():
            if value is not None:
                setattr(args, key, value)

    normalize_kv_params(args)
    set_seed(seed=args.seed, deterministic=True)

    kv_mode_used = args.kv_mode
    ppl_mode = args.ppl_mode
    if args.kv_mode != "fp16" and ppl_mode == "hf":
        print("kv_mode != fp16; switching ppl_mode=kv_cache to evaluate quantized KV path.")
        ppl_mode = "kv_cache"

    print(f"Loading {args.model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    
    # Note: Currently this script tests the MODEL weights PPL.
    # To test KV Cache quantization PPL, we must ensure the `model` object uses our KV Cache.
    # Since we haven't monkey-patched HF model yet (Milestone E/F), this serves as
    # FP16 Baseline PPL reference.
    # For INT8, we will eventually need to inject the Quantized Cache into the model.

    print("Loading wikitext-2-raw-v1...")
    try:
        test = load_dataset("wikitext", "wikitext-2-raw-v1", split="test")
    except Exception as e:
        print(f"Failed to load dataset: {e}. Check network/proxy.")
        # Fallback smoke test if network fails and we just want to verify script logic?
        # No, objective demands robustness. Fail.
        sys.exit(1)

    max_length = args.max_length
    stride = args.stride
    if stride <= 0 or max_length <= 0:
        print("Invalid stride/max_length. Both must be positive.")
        sys.exit(1)
    if stride > max_length:
        print("Invalid stride: stride must be <= max_length.")
        sys.exit(1)

    max_tokens = None
    if args.max_samples:
        max_tokens = args.max_samples * max_length

    total_nll = torch.tensor(0.0, device=model.device)
    total_tokens = 0
    prev_end_loc = 0
    global_idx = 0

    print(
        f"Evaluating PPL with {ppl_mode} mode "
        f"(Window: {max_length}, Stride: {stride})..."
    )
    pbar = tqdm(desc="Evaluating PPL", unit="win")
    buffer_tokens = []

    kv_cache = None
    if ppl_mode == "kv_cache":
        kv_cache = build_kv_cache(
            args.kv_mode,
            model,
            args.group_size,
            args.clip_percentile,
            args.calib_file,
            args.use_attn_temperature,
        )

    try:
        for ids in iter_token_ids(test, tokenizer, max_tokens):
            if not ids:
                continue
            buffer_tokens.extend(ids)

            while len(buffer_tokens) >= max_length:
                window = buffer_tokens[:max_length]
                end_loc = global_idx + max_length
                trg_len = end_loc - prev_end_loc
                if trg_len <= 0:
                    print("Invalid target length during evaluation.")
                    sys.exit(1)

                input_ids = torch.tensor([window], device=model.device)
                target_ids = input_ids.clone()
                if trg_len < input_ids.size(1):
                    target_ids[:, :-trg_len] = -100

                if ppl_mode == "hf":
                    with torch.no_grad():
                        outputs = model(input_ids, labels=target_ids)
                        neg_log_likelihood = outputs.loss * trg_len
                    total_nll += neg_log_likelihood
                    total_tokens += trg_len
                else:
                    nll, tokens = eval_window_kv_cache(
                        model=model,
                        input_ids=input_ids,
                        trg_len=trg_len,
                        kv_cache=kv_cache,
                        kv_mode=args.kv_mode,
                    )
                    total_nll += nll
                    total_tokens += tokens
                prev_end_loc = end_loc
                global_idx += stride
                buffer_tokens = buffer_tokens[stride:]
                pbar.update(1)

        # Flush remaining tokens (short window)
        if buffer_tokens:
            end_loc = global_idx + len(buffer_tokens)
            trg_len = end_loc - prev_end_loc
            if trg_len > 0:
                input_ids = torch.tensor([buffer_tokens], device=model.device)
                target_ids = input_ids.clone()
                if trg_len < input_ids.size(1):
                    target_ids[:, :-trg_len] = -100

                if ppl_mode == "hf":
                    with torch.no_grad():
                        outputs = model(input_ids, labels=target_ids)
                        neg_log_likelihood = outputs.loss * trg_len
                    total_nll += neg_log_likelihood
                    total_tokens += trg_len
                else:
                    nll, tokens = eval_window_kv_cache(
                        model=model,
                        input_ids=input_ids,
                        trg_len=trg_len,
                        kv_cache=kv_cache,
                        kv_mode=args.kv_mode,
                    )
                    total_nll += nll
                    total_tokens += tokens
                prev_end_loc = end_loc
                pbar.update(1)
    except RuntimeError as e:
        print(f"PPL evaluation failed: {e}")
        if "out of memory" in str(e).lower():
            print("Tip: reduce --max_length or --max_samples.")
        sys.exit(1)
    finally:
        pbar.close()

    if prev_end_loc <= 0 or total_tokens <= 0:
        print("No tokens were evaluated. Check dataset/tokenization.")
        sys.exit(1)

    seq_len = prev_end_loc
    ppl = torch.exp(total_nll / total_tokens)
    print(f"\nResult PPL: {ppl.item():.2f}")

    if args.save_csv:
        timestamp = datetime.now().isoformat()
        git_commit = get_git_commit()
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = project_root / out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"profile_ppl_{kv_mode_used}_{timestamp.replace(':','-')}.csv"
        hardware = get_hardware_info()
        
        # Mapping to Schema: PPL stores 'perplexity' in a flexible column or abuses a field?
        # Objective says "quality_metrics" can be added. 
        # But mandatory fields must exist.
        row = {
            "run_id": f"ppl_{timestamp}",
            "model_id": args.model_id,
            "kv_mode": kv_mode_used,
            "quant_bits": 4 if "int4" in kv_mode_used else (8 if "int8" in kv_mode_used else 16),
            "clip_percentile": args.clip_percentile,
            "group_size": args.group_size,
            "dtype": str(model.dtype),
            "hardware": f"{hardware['gpu']} ({hardware['gpu_memory']})",
            "seq_len": seq_len, # Total evaluated
            "gen_len": 0,
            "batch": 1,
            "ttft_ms": 0,
            "tpot_ms": 0,
            "tok_per_s": 0,
            "gpu_mem_peak_mb": 0,
            "timestamp": timestamp,
            "git_commit": git_commit,
            # Extra
            "perplexity": round(ppl.item(), 4),
            "ppl_mode": ppl_mode,
            "tokens_evaluated": total_tokens,
        }
        
        # Extended fields
        fields = [
            "run_id", "model_id", "kv_mode", "quant_bits", "clip_percentile", "group_size", 
            "dtype", "hardware", "seq_len", "gen_len", "batch", "ttft_ms", "tpot_ms",
            "tok_per_s", "gpu_mem_peak_mb", "timestamp", "git_commit", "perplexity",
            "ppl_mode", "tokens_evaluated"
        ]
        
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerow(row)
        print(f"Saved to {path}")

        run_snapshot_dir = out_dir / row["run_id"]
        snapshot = build_config_snapshot(
            script_name=Path(__file__).name,
            args=args,
            extra={
                "kv_mode_used": kv_mode_used,
                "ppl_mode": ppl_mode,
                "tokens_evaluated": total_tokens,
                "ppl_tokenization": {
                    "add_special_tokens": False,
                    "separator": "\\n\\n",
                    "max_tokens": max_tokens,
                    "window": max_length,
                    "stride": stride,
                },
            },
        )
        write_config_snapshot(str(run_snapshot_dir), snapshot)

if __name__ == "__main__":
    main()
