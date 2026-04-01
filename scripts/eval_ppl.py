#!/usr/bin/env python3
"""
D3: Perplexity Evaluation Script (eval_ppl.py)
Uses wikitext-2-raw-v1 to measure PPL.
"""

import argparse
import csv
import json
import math
import os
import sys
import traceback
import torch
from tqdm import tqdm
from datetime import datetime
from pathlib import Path

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

# QUA-006: Design: Uses HF's built-in sliding-window PPL (stride=512) rather than custom engine,
# because PPL evaluation doesn't need quantized KV cache — it uses the model's own forward pass.

from transformers import AutoModelForCausalLM, AutoTokenizer
try:
    from transformers import DynamicCache
    HAS_DYNAMIC_CACHE = True
except ImportError:
    try:
        from transformers.cache_utils import DynamicCache
        HAS_DYNAMIC_CACHE = True
    except ImportError:
        HAS_DYNAMIC_CACHE = False
from datasets import load_dataset
from src.cache import FP16KVCache, INT8KVCache, INT4KVCache, KIVIStyleKVCache
from src.engine.patch_model import apply_int8_fused_patch
from src.engine.generate_loop import _register_prefill_temperature_hooks, _register_all_temperature_hooks
from src.utils.hf import resolve_pretrained_path
from src.utils.repro import (
    build_config_snapshot,
    get_git_commit,  # QUA-001: centralized
    get_hardware_info,
    resolve_quant_bits,
    set_seed,
    write_config_snapshot,
)
from scripts.config_utils import load_config, normalize_kv_params, resolve_run_config

# EVL-029: Standard exit codes aligned with eval_longbench/eval_ruler.
EXIT_OOM = 73
EXIT_EXCEPTION = 2

_LAST_ARGS: argparse.Namespace | None = None


def _write_task_failure(
    *,
    args: argparse.Namespace,
    failure_type: str,
    message: str,
    exception: Exception | None = None,
) -> None:
    """Write a structured failure JSON for run_experiments.py to consume."""
    out_dir = Path(args.out_dir) if getattr(args, "out_dir", None) else Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "script": Path(__file__).name,
        "timestamp": datetime.now().isoformat(),
        "failure_type": str(failure_type),
        "message": str(message),
        "kv_mode": str(getattr(args, "kv_mode", "")),
        "run_name": str(getattr(args, "run_name", "")),
        "seed": int(getattr(args, "seed", 0)),
        "replica_id": int(getattr(args, "replica_id", 0)),
        "seq_len": int(getattr(args, "seq_len", 0) or 0),
    }
    if exception is not None:
        payload["exception_type"] = type(exception).__name__
        payload["exception_repr"] = repr(exception)
        payload["traceback"] = traceback.format_exc()
    path = out_dir / f"task_failure_{Path(__file__).stem}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _handle_non_finite_ppl(
    *,
    args: argparse.Namespace,
    ppl_val: float,
    total_nll: float,
    total_tokens: int,
) -> None:
    """Fail fast when PPL is NaN/Inf so run_experiments can detect the failure."""
    if math.isfinite(ppl_val):
        return
    msg = (
        f"PPL is {ppl_val} (NaN or Inf). "
        f"total_nll={total_nll}, total_tokens={total_tokens}. "
        "This usually indicates corrupted logits (all-zero, NaN, or Inf) "
        "during evaluation. The result will NOT be written to CSV."
    )
    print(f"FATAL: {msg}")
    _write_task_failure(
        args=args,
        failure_type="nan_inf_ppl",
        message=msg,
    )
    raise SystemExit(EXIT_EXCEPTION)




def maybe_to_dynamic_cache(past_key_values):
    """
    Transformers versions differ on whether model forward accepts legacy tuples.
    If DynamicCache is available, convert legacy cache tuples to DynamicCache.
    """
    if not HAS_DYNAMIC_CACHE:
        return past_key_values
    if isinstance(past_key_values, tuple):
        try:
            return DynamicCache.from_legacy_cache(past_key_values)
        except Exception:
            # EVL-034: Conversion may fail for non-standard cache shapes
            # (e.g. KIVI tuples with quantized tensors). Fall back to the
            # raw tuple, which older Transformers versions accept directly.
            return past_key_values
    return past_key_values


def iter_token_ids(dataset, tokenizer, max_tokens, *, allow_repeats: bool = False):
    sep_ids = tokenizer("\n\n", add_special_tokens=False).input_ids
    first_doc = True
    total_tokens = 0
    while True:
        produced_in_pass = False
        for row in dataset:
            if max_tokens is not None and total_tokens >= max_tokens:
                return

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
                    return
                if len(ids) > remaining:
                    ids = ids[:remaining]

            if not ids:
                continue
            produced_in_pass = True
            total_tokens += len(ids)
            yield ids

        if max_tokens is None:
            return
        if not allow_repeats or not produced_in_pass:
            return


def load_calibration(
    kv_mode: str,
    calib_file: str | None,
    group_size: int,
    clip_percentile: float,
    device: torch.device,
    use_attn_temperature: bool,
    use_static_scales: bool,
):
    static_k_scale = None
    static_v_scale = None
    inv_tau = None
    outlier_rescue_ratio = 0.0
    mixed_rescue = False

    if kv_mode not in ["int8_ours", "int4_ours", "int4_ours_mixed", "int4_fused", "int4_kivi_aligned"]:
        # PRF-009: calib_file is intentionally a no-op for kivi_style mode --
        # KIVI uses its own internal calibration. int4_kivi_aligned passes through
        # to load inv_tau from calibration file.
        return (
            static_k_scale,
            static_v_scale,
            inv_tau,
            group_size,
            clip_percentile,
            outlier_rescue_ratio,
            mixed_rescue,
        )

    import warnings
    if kv_mode == "int8_ours":
        default_calib = os.path.join("artifacts", "kv_calib_kl.json")
    else:
        default_calib = os.path.join("artifacts", "kv_calib_kl_int4_selected.json")
    calib_path = calib_file or default_calib
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

            if use_static_scales and "k_scale" in calib:
                static_k_scale = torch.tensor(calib["k_scale"], dtype=torch.float16, device=device)
            if use_static_scales and "v_scale" in calib:
                static_v_scale = torch.tensor(calib["v_scale"], dtype=torch.float16, device=device)
            if use_attn_temperature and "inv_tau" in calib:
                inv_tau = torch.tensor(calib["inv_tau"], dtype=torch.float32, device=device)
            outlier_rescue_ratio = float(calib.get("int4_outlier_ratio", 0.0) or 0.0)
            mixed_rescue = bool(calib.get("int4_mixed_rescue", False))
            if kv_mode == "int4_ours_mixed":
                mixed_rescue = True
        except Exception as exc:
            warnings.warn(
                f"Failed to load calibration file {calib_path}: {exc}. "
                "Falling back to baseline behavior.",
                UserWarning,
            )
    else:
        warnings.warn(
            f"Calibration file not found: {calib_path}. "
            "Falling back to baseline behavior.",
            UserWarning,
        )

    return (
        static_k_scale,
        static_v_scale,
        inv_tau,
        group_size,
        clip_percentile,
        outlier_rescue_ratio,
        mixed_rescue,
    )


def build_kv_cache(
    kv_mode: str,
    model,
    group_size: int,
    clip_percentile: float,
    calib_file: str | None,
    use_attn_temperature: bool,
    use_static_scales: bool,
    adaptive_static_scales: bool,
    adaptive_static_margin: float,
    adaptive_static_k: bool,
    adaptive_static_v: bool,
    decode_attn_impl: str | None,
    quant_bits: int | None = None,
    k_bits: int | None = None,
    v_bits: int | None = None,
):
    num_layers = getattr(model.config, "num_hidden_layers", 28)
    (
        static_k_scale,
        static_v_scale,
        inv_tau,
        group_size,
        clip_percentile,
        outlier_rescue_ratio,
        mixed_rescue,
    ) = load_calibration(
        kv_mode,
        calib_file,
        group_size,
        clip_percentile,
        model.device,
        use_attn_temperature,
        use_static_scales,
    )

    if kv_mode == "fp16":
        return FP16KVCache(num_layers=num_layers, device=model.device.type), group_size, clip_percentile

    if kv_mode == "int4_baseline":
        return INT4KVCache(
            num_layers=num_layers,
            device=model.device.type,
            clip_percentile=clip_percentile,
            group_size=group_size,
        ), group_size, clip_percentile

    if kv_mode in ["int4_fused", "int4_ours", "int4_ours_mixed"]:
        apply_int8_fused_patch(model)
        return INT4KVCache(
            num_layers=num_layers,
            device=model.device.type,
            clip_percentile=clip_percentile,
            group_size=group_size,
            decode_attn_impl=decode_attn_impl or "triton_fused",
            static_k_scale=static_k_scale,
            static_v_scale=static_v_scale,
            inv_tau=inv_tau,
            use_attn_temperature=use_attn_temperature,
            adaptive_static_scales=adaptive_static_scales,
            adaptive_static_margin=adaptive_static_margin,
            adaptive_static_k=adaptive_static_k,
            adaptive_static_v=adaptive_static_v,
            outlier_rescue_ratio=outlier_rescue_ratio,
            mixed_rescue=mixed_rescue or kv_mode == "int4_ours_mixed",
        ), group_size, clip_percentile

    if kv_mode == "kivi_style":
        kivi_quant_bits = quant_bits if quant_bits is not None else 8
        return KIVIStyleKVCache(
            num_layers=num_layers,
            device=model.device.type,
            quant_bits=kivi_quant_bits,
        ), group_size, clip_percentile

    if kv_mode == "int4_kivi_aligned":
        return KIVIStyleKVCache(
            num_layers=num_layers,
            device=model.device.type,
            quant_bits=4,
            inv_tau=inv_tau,
            use_attn_temperature=use_attn_temperature,
        ), group_size, clip_percentile

    if kv_mode == "int4_mixed_kv":
        from src.cache.mixed_kv_cache import MixedKVCache
        return MixedKVCache(
            num_layers=num_layers,
            device=model.device.type,
            k_bits=k_bits if k_bits is not None else 8,
            v_bits=v_bits if v_bits is not None else 4,
        ), group_size, clip_percentile

    if kv_mode in ("int4_ours_asym", "int4_ours_asym_ba"):
        # Mirrors generate_loop.py L869-919 exactly.
        from src.cache.role_aware_asym_cache import RoleAwareAsymKVCache
        ra_k_percentile = 100.0
        ra_v_percentile = 100.0
        ra_inv_tau = None
        if calib_file is not None:
            calib_path = calib_file if os.path.isabs(calib_file) else os.path.join(os.getcwd(), calib_file)
            if os.path.exists(calib_path):
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
                    raw_tau = None
                    if "role_aware" in calib_data and "inv_tau" in calib_data["role_aware"]:
                        raw_tau = calib_data["role_aware"]["inv_tau"]
                    elif "k_calibration" in calib_data and "inv_tau" in calib_data["k_calibration"]:
                        raw_tau = calib_data["k_calibration"]["inv_tau"]
                    elif "inv_tau" in calib_data:
                        raw_tau = calib_data["inv_tau"]
                    if raw_tau is not None:
                        ra_inv_tau = torch.tensor(raw_tau, dtype=torch.float32, device=model.device)
        use_temp = use_attn_temperature and (kv_mode == "int4_ours_asym_ba")
        framework_tag = "ours_asym_ba" if kv_mode == "int4_ours_asym_ba" else "ours_asym"
        return RoleAwareAsymKVCache(
            num_layers=num_layers,
            device=model.device.type,
            quant_bits=4,
            k_percentile=ra_k_percentile,
            v_percentile=ra_v_percentile,
            inv_tau=ra_inv_tau,
            use_attn_temperature=use_temp,
            framework=framework_tag,
        ), group_size, clip_percentile

    if kv_mode in ["int8_fused", "int8_ours"]:
        apply_int8_fused_patch(model)

    # EVL-033: int8_baseline doesn't use fused attention, so default to
    # torch_ref rather than triton_fused to keep config semantics precise.
    effective_attn_impl = decode_attn_impl or (
        "torch_ref" if kv_mode == "int8_baseline" else "triton_fused"
    )

    return INT8KVCache(
        num_layers=num_layers,
        device=model.device.type,
        clip_percentile=clip_percentile,
        group_size=group_size,
        decode_attn_impl=effective_attn_impl,
        static_k_scale=static_k_scale,
        static_v_scale=static_v_scale,
        inv_tau=inv_tau,
        use_attn_temperature=use_attn_temperature,
        adaptive_static_scales=adaptive_static_scales,
        adaptive_static_margin=adaptive_static_margin,
        adaptive_static_k=adaptive_static_k,
        adaptive_static_v=adaptive_static_v,
    ), group_size, clip_percentile


def build_past_key_values(kv_mode: str, kv_cache, num_layers: int):
    if kv_mode in ["int8_fused", "int8_ours", "int4_fused", "int4_ours", "int4_ours_mixed"]:
        from src.engine.patch_model import INT8CacheWrapperContainer
        # IMPORTANT: Always pass our wrapper container, even when the cache is empty.
        # Otherwise the first chunk (q_len > 1) would run with float K/V and only quantize
        # after the forward, which changes logits and breaks chunk_size equivalence.
        return INT8CacheWrapperContainer(kv_cache, num_layers), False

    if kv_cache.get_seq_len() == 0:
        return None, True

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
    chunk_size: int = 1,
):
    num_layers = getattr(model.config, "num_hidden_layers", 28)
    seq_len = input_ids.size(1)
    start_loss_idx = max(seq_len - trg_len, 0)

    kv_cache.clear()
    total_nll = torch.tensor(0.0, device=model.device)
    total_tokens = 0

    with torch.no_grad():
        chunk_size = int(chunk_size)
        if chunk_size <= 1:
            attention_mask = torch.ones((1, 1), device=model.device, dtype=torch.long)
            current_token = input_ids[:, 0:1]

            for t in range(seq_len - 1):
                past_key_values, should_update_cache = build_past_key_values(
                    kv_mode, kv_cache, num_layers
                )
                past_key_values = maybe_to_dynamic_cache(past_key_values)

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
                # Ensure scalar to avoid in-place broadcast issues on 0-dim tensors.
                nll = nll.sum()

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
                    [
                        attention_mask,
                        torch.ones(
                            (1, 1),
                            device=model.device,
                            dtype=attention_mask.dtype,
                        ),
                    ],
                    dim=1,
                )
                current_token = next_token
        else:
            # Chunked path: process multiple tokens per forward to reduce Python overhead.
            # Note: this changes intra-chunk KV quantization exposure (tokens within a chunk
            # attend to each other with float K/V); keep chunk_size=1 for strict decode-like evaluation.
            attention_mask = torch.zeros((1, 0), device=model.device, dtype=torch.long)
            pos = 0
            while pos < (seq_len - 1):
                chunk_len = min(chunk_size, (seq_len - 1) - pos)
                chunk_input = input_ids[:, pos : pos + chunk_len]

                # attention_mask must include past + current tokens
                attention_mask = torch.cat(
                    [
                        attention_mask,
                        torch.ones(
                            (1, chunk_len),
                            device=model.device,
                            dtype=attention_mask.dtype,
                        ),
                    ],
                    dim=1,
                )

                past_key_values, should_update_cache = build_past_key_values(
                    kv_mode, kv_cache, num_layers
                )
                past_key_values = maybe_to_dynamic_cache(past_key_values)

                outputs = model(
                    input_ids=chunk_input,
                    attention_mask=attention_mask,
                    past_key_values=past_key_values,
                    use_cache=True,
                )

                # Compute NLL for this chunk: predict token (pos+1 .. pos+chunk_len)
                targets = input_ids[:, pos + 1 : pos + chunk_len + 1]
                log_probs = torch.log_softmax(outputs.logits, dim=-1)
                nll = -log_probs.gather(dim=-1, index=targets.unsqueeze(-1)).squeeze(-1)  # [1, L]

                pred_indices = torch.arange(
                    pos + 1, pos + chunk_len + 1, device=model.device
                )
                mask = pred_indices >= int(start_loss_idx)
                if mask.any().item():
                    total_nll += nll[0, mask].sum()
                    total_tokens += int(mask.sum().item())

                if should_update_cache and outputs.past_key_values is not None:
                    for i, (k, v) in enumerate(outputs.past_key_values):
                        if k.shape[2] > chunk_len:
                            k_new = k[:, :, -chunk_len:, :]
                            v_new = v[:, :, -chunk_len:, :]
                            kv_cache.append(i, k_new, v_new)
                        else:
                            kv_cache.append(i, k, v)

                pos += chunk_len

    return total_nll, total_tokens


def main():
    parser = argparse.ArgumentParser(description="D3: PPL Evaluation")
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument(
        "--model_revision",
        type=str,
        default=None,
        help="Optional model revision (commit hash/tag) for strict reproducibility.",
    )
    # PPL specific
    parser.add_argument(
        "--dataset",
        type=str,
        default="wikitext2",
        choices=["wikitext2", "c4"],
        help="Dataset for PPL evaluation. wikitext2 (default) or c4 (allenai/c4 validation).",
    )
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
    parser.add_argument(
        "--target_tokens",
        type=int,
        default=None,
        help=(
            "Hard lower bound on evaluated token count. "
            "If max_samples is also set, the larger token budget is used."
        ),
    )
    parser.add_argument(
        "--allow_dataset_repeat",
        dest="allow_dataset_repeat",
        action="store_true",
        default=True,
        help="Allow repeating dataset stream when target_tokens exceeds one pass.",
    )
    parser.add_argument(
        "--no_allow_dataset_repeat",
        dest="allow_dataset_repeat",
        action="store_false",
        help="Disable dataset repeat even when target_tokens is set.",
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=128,
        help=(
            "Chunk size for ppl_mode=kv_cache. Use 1 for strict token-by-token evaluation; "
            "larger values reduce Python overhead and increase GPU utilization."
        ),
    )
    
    # Schema filler args
    # NOTE: scripts/run_experiments.py passes --seq_len/--gen_len for all tasks; accept them
    # as no-ops here to keep the matrix runner compatible.
    parser.add_argument("--seq_len", type=int, default=None)
    parser.add_argument("--gen_len", type=int, default=None)
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
            "int4_ours_asym",
            "int4_ours_asym_ba",
        ],
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
        "--quant_bits",
        type=int,
        default=None,
        help="Override quant_bits for CSV output (needed for kivi_style which can be 4 or 8).",
    )
    parser.add_argument(
        "--k_bits",
        type=int,
        default=None,
        help="K cache bit-width for int4_mixed_kv mode (4/8/16). Default: 8.",
    )
    parser.add_argument(
        "--v_bits",
        type=int,
        default=None,
        help="V cache bit-width for int4_mixed_kv mode (4/8/16). Default: 4.",
    )
    parser.add_argument(
        "--use_attn_temperature",
        dest="use_attn_temperature",
        action="store_true",
        default=False,
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
    global _LAST_ARGS  # noqa: PLW0603
    _LAST_ARGS = args

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
    
    # Note: Currently this script tests the MODEL weights PPL.
    # To test KV Cache quantization PPL, we must ensure the `model` object uses our KV Cache.
    # Since we haven't monkey-patched HF model yet (Milestone E/F), this serves as
    # FP16 Baseline PPL reference.
    # For INT8, we will eventually need to inject the Quantized Cache into the model.

    dataset_name = getattr(args, "dataset", "wikitext2")
    if dataset_name == "c4":
        print("Loading allenai/c4 (en, validation)...")
        try:
            test = load_dataset("allenai/c4", "en", split="validation", streaming=True)
            # Convert streaming dataset to iterable; iter_token_ids handles iteration.
        except Exception as e:
            print(f"Failed to load C4 dataset: {e}. Check network/proxy.")
            sys.exit(1)
    else:
        print("Loading wikitext-2-raw-v1...")
        try:
            test = load_dataset("wikitext", "wikitext-2-raw-v1", split="test")
        except Exception as e:
            print(f"Failed to load dataset: {e}. Check network/proxy.")
            sys.exit(1)

    max_length = args.max_length
    stride = args.stride
    if stride <= 0 or max_length <= 0:
        print("Invalid stride/max_length. Both must be positive.")
        sys.exit(1)
    if stride > max_length:
        print("Invalid stride: stride must be <= max_length.")
        sys.exit(1)
    if args.max_samples is not None and int(args.max_samples) <= 0:
        print("Invalid max_samples: must be positive when provided.")
        sys.exit(1)
    if args.target_tokens is not None and int(args.target_tokens) <= 0:
        print("Invalid target_tokens: must be positive when provided.")
        sys.exit(1)

    max_tokens = None
    if args.max_samples:
        max_tokens = args.max_samples * max_length
    if args.target_tokens is not None:
        # next-token PPL evaluation has one fewer target than input tokens.
        # Reserve +1 input token so evaluated targets can reach target_tokens exactly.
        min_input_tokens = int(args.target_tokens) + 1
        if max_tokens is None or int(max_tokens) < min_input_tokens:
            max_tokens = min_input_tokens

    total_nll = torch.tensor(0.0, device=model.device)
    total_tokens = 0
    prev_end_loc = 0
    global_idx = 0

    print(
        f"Evaluating PPL with {ppl_mode} mode "
        f"(Window: {max_length}, Stride: {stride}, Chunk: {args.chunk_size}, "
        f"TokenBudget: {max_tokens if max_tokens is not None else 'full-dataset'})..."
    )
    pbar = tqdm(desc="Evaluating PPL", unit="win")
    buffer_tokens = []

    kv_cache = None
    hook_handles = []
    effective_group_size = args.group_size
    effective_clip_percentile = args.clip_percentile
    if ppl_mode == "kv_cache":
        kv_cache, effective_group_size, effective_clip_percentile = build_kv_cache(
            args.kv_mode,
            model,
            args.group_size,
            args.clip_percentile,
            args.calib_file,
            args.use_attn_temperature,
            args.use_static_scales,
            args.adaptive_static_scales,
            args.adaptive_static_margin,
            args.adaptive_static_k,
            args.adaptive_static_v,
            args.decode_attn_impl,
            quant_bits=args.quant_bits,
            k_bits=getattr(args, "k_bits", None),
            v_bits=getattr(args, "v_bits", None),
        )
        if (
            args.use_attn_temperature
            and getattr(kv_cache, "inv_tau", None) is not None
        ):
            if args.kv_mode in ("int4_kivi_aligned", "int4_ours_asym_ba"):
                # torch_ref decode modes: inv_tau must be applied for ALL seq_len
                # (both prefill chunks and decode).
                hook_handles = _register_all_temperature_hooks(model, kv_cache.inv_tau)
            elif args.kv_mode in ["int8_ours", "int4_ours", "int4_ours_mixed", "int4_fused"]:
                # Fused modes: prefill-only hooks; decode temperature handled by kernel.
                hook_handles = _register_prefill_temperature_hooks(model, kv_cache.inv_tau)

    try:
        for ids in iter_token_ids(
            test,
            tokenizer,
            max_tokens,
            allow_repeats=bool(args.allow_dataset_repeat and args.target_tokens is not None),
        ):
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
                        chunk_size=args.chunk_size,
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
                        chunk_size=args.chunk_size,
                    )
                    total_nll += nll
                    total_tokens += tokens
                prev_end_loc = end_loc
                pbar.update(1)
    except RuntimeError as e:
        is_oom = "out of memory" in str(e).lower()
        print(f"PPL evaluation failed: {e}")
        if is_oom:
            print("Tip: reduce --max_length or --max_samples.")
        # EVL-029/036: Write structured failure JSON and use standard exit codes.
        _write_task_failure(
            args=args,
            failure_type="oom" if is_oom else "exception",
            message=f"RuntimeError during eval_ppl: {e}",
            exception=e,
        )
        sys.exit(EXIT_OOM if is_oom else EXIT_EXCEPTION)
    finally:
        for h in hook_handles:
            try:
                h.remove()
            except Exception:
                pass
        pbar.close()

    if prev_end_loc <= 0 or total_tokens <= 0:
        print("No tokens were evaluated. Check dataset/tokenization.")
        sys.exit(1)
    if args.target_tokens is not None and total_tokens < int(args.target_tokens):
        print(
            "Target token floor not met: "
            f"evaluated={total_tokens}, target_tokens={int(args.target_tokens)}."
        )
        print("Tip: keep --allow_dataset_repeat enabled or reduce --target_tokens.")
        sys.exit(2)

    seq_len = prev_end_loc
    ppl = torch.exp(total_nll / total_tokens)

    ppl_val = ppl.item()
    _handle_non_finite_ppl(
        args=args,
        ppl_val=ppl_val,
        total_nll=float(total_nll.item()),
        total_tokens=int(total_tokens),
    )

    print(f"\nResult PPL: {ppl_val:.2f}")

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
            "quant_bits": resolve_quant_bits(
                kv_mode_used,
                getattr(args, "quant_bits", None),
            ),
            "clip_percentile": effective_clip_percentile,
            "group_size": effective_group_size,
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
            "seed": int(args.seed),
            "replica_id": int(args.replica_id),
            # Extra
            "perplexity": round(ppl.item(), 4),
            # EVL-031: Per-run CSV uses point estimate for CI fields (no
            # bootstrap within a single run).  Actual CI is computed across
            # seeds by aggregate_results.py.
            "ppl_ci95_low": round(ppl.item(), 4),
            "ppl_ci95_high": round(ppl.item(), 4),
            "ppl_mode": ppl_mode,
            "tokens_evaluated": total_tokens,
            "chunk_size": int(args.chunk_size),
            "target_tokens": int(args.target_tokens) if args.target_tokens is not None else "",
        }
        
        # Extended fields
        fields = [
            "run_id", "model_id", "kv_mode", "quant_bits", "clip_percentile", "group_size", 
            "dtype", "hardware", "seq_len", "gen_len", "batch", "ttft_ms", "tpot_ms",
            "tok_per_s", "gpu_mem_peak_mb", "timestamp", "git_commit", "seed", "replica_id",
            "perplexity", "ppl_ci95_low", "ppl_ci95_high", "ppl_mode", "tokens_evaluated", "chunk_size",
            "target_tokens"
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
                    "target_tokens": args.target_tokens,
                    "window": max_length,
                    "stride": stride,
                    "allow_dataset_repeat": bool(args.allow_dataset_repeat),
                },
            },
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
                message="CUDA out of memory during eval_ppl execution.",
                exception=exc,
            )
        sys.exit(EXIT_OOM)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {type(exc).__name__}: {exc}")
        if _LAST_ARGS is not None:
            _write_task_failure(
                args=_LAST_ARGS,
                failure_type="exception",
                message="Unhandled exception during eval_ppl execution.",
                exception=exc,
            )
        sys.exit(EXIT_EXCEPTION)
