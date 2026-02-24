#!/usr/bin/env python3
"""
Config utilities for experiment matrix loading.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import warnings

import yaml


# QUA-005: Canonical KV mode ordering, shared across aggregate_results.py
# and export_tables_latex.py. Defined here as the single source of truth.
KV_MODE_ORDER: List[str] = [
    "fp16",
    "int8_baseline",
    "int8_ours",
    "int8_fused",
    "int4_baseline",
    "int4_ours",
    "int4_ours_mixed",
    "int4_fused",
    "kivi_style",
]


def load_config(config_path: str) -> Dict[str, Any]:
    """Load YAML config file."""
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    # RUN-020: yaml.safe_load returns None for empty files; raise early with clear message.
    if data is None:
        raise ValueError(
            f"Config file is empty or contains only comments: {config_path!r}. "
            "Expected a non-empty YAML mapping."
        )
    if not isinstance(data, dict):
        raise ValueError(
            f"Config file does not contain a YAML mapping at the top level: {config_path!r}. "
            f"Got {type(data).__name__}."
        )
    return data


def find_run_entry(config: Dict[str, Any], run_name: str) -> Dict[str, Any]:
    """Find a run entry by name."""
    for entry in config.get("matrix", []):
        if entry.get("run_name") == run_name:
            return entry
    raise ValueError(f"run_name '{run_name}' not found in config")


def resolve_run_config(config: Dict[str, Any], run_name: str) -> Dict[str, Any]:
    """
    Resolve a run entry with runtime defaults into flat args.
    """
    runtime = config.get("runtime", {})
    quant_defaults = runtime.get("quant_defaults", {})
    kernel_defaults = runtime.get("kernel_defaults", {})
    project = config.get("project", {})

    run_entry = find_run_entry(config, run_name)

    clip_percentile_k = run_entry.get(
        "clip_percentile_k",
        run_entry.get("clip_percentile", quant_defaults.get("clip_percentile_k", 99.9)),
    )
    clip_percentile_v = run_entry.get(
        "clip_percentile_v",
        run_entry.get("clip_percentile", quant_defaults.get("clip_percentile_v", 99.9)),
    )
    group_size_k = run_entry.get(
        "group_size_k",
        run_entry.get("group_size", quant_defaults.get("group_size_k", 128)),
    )
    group_size_v = run_entry.get(
        "group_size_v",
        run_entry.get("group_size", quant_defaults.get("group_size_v", 128)),
    )

    resolved = {
        "model_id": project.get("model_id"),
        "kv_mode": run_entry.get("kv_mode"),
        "seq_len": run_entry.get("seq_len"),
        "gen_len": run_entry.get("gen_len"),
        "batch": run_entry.get("batch"),
        "clip_percentile": clip_percentile_k,
        "group_size": group_size_k,
        "clip_percentile_k": clip_percentile_k,
        "clip_percentile_v": clip_percentile_v,
        "group_size_k": group_size_k,
        "group_size_v": group_size_v,
        "calib_strategy": run_entry.get(
            "calib_strategy", quant_defaults.get("calib_strategy")
        ),
        "decode_attn_impl": run_entry.get(
            "decode_attn_impl", kernel_defaults.get("decode_attn_impl")
        ),
        "quant_bits": run_entry.get("quant_bits", quant_defaults.get("quant_bits")),
        "dtype": runtime.get("dtype"),
        "seed": run_entry.get("seed", runtime.get("seed")),
        "calib_file": run_entry.get("calib_file", quant_defaults.get("calib_file")),
        "use_attn_temperature": run_entry.get(
            "use_attn_temperature", quant_defaults.get("use_attn_temperature")
        ),
    }
    return resolved


def normalize_kv_params(args) -> None:
    """
    Normalize k/v group_size and clip_percentile into shared args.
    We keep group_size/clip_percentile for backward compatibility and
    record k/v-specific values for config snapshots.
    """
    group_size_k = getattr(args, "group_size_k", None) or getattr(args, "group_size", None)
    group_size_v = getattr(args, "group_size_v", None) or getattr(args, "group_size", None)
    clip_k = getattr(args, "clip_percentile_k", None) or getattr(args, "clip_percentile", None)
    clip_v = getattr(args, "clip_percentile_v", None) or getattr(args, "clip_percentile", None)

    if group_size_k is not None and group_size_v is not None and group_size_k != group_size_v:
        warnings.warn(
            f"group_size_k ({group_size_k}) != group_size_v ({group_size_v}); "
            "using group_size_k for runtime.",
            UserWarning,
        )
    if clip_k is not None and clip_v is not None and clip_k != clip_v:
        warnings.warn(
            f"clip_percentile_k ({clip_k}) != clip_percentile_v ({clip_v}); "
            "using clip_percentile_k for runtime.",
            UserWarning,
        )

    setattr(args, "group_size_k", group_size_k)
    setattr(args, "group_size_v", group_size_v)
    setattr(args, "clip_percentile_k", clip_k)
    setattr(args, "clip_percentile_v", clip_v)

    if group_size_k is not None:
        setattr(args, "group_size", group_size_k)
    if clip_k is not None:
        setattr(args, "clip_percentile", clip_k)
