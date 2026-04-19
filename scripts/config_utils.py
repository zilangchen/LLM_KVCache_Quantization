#!/usr/bin/env python3
"""
Config utilities for experiment matrix loading.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import warnings

import yaml

_logger = logging.getLogger(__name__)


# SEC-002: Allowed model IDs — whitelist for trust_remote_code=True usage.
# Only models listed here are permitted; unknown model_ids are rejected early
# in run_experiments.py rather than loading arbitrary remote code on a GPU server.
ALLOWED_MODEL_IDS: frozenset[str] = frozenset({
    "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-14B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
})

# QUA-005: Canonical KV mode ordering, shared across aggregate_results.py
# and export_tables_latex.py. Defined here as the single source of truth.
# CFG-050: int8_fused is a valid internal mode (Triton fused INT8 decode)
# but is not listed in CLAUDE.md §9 fixed quantization methods because it
# is an implementation variant of int8_ours, not a separate research method.
# It is kept here for correct table ordering when int8_fused runs appear.
KV_MODE_ORDER: List[str] = [
    "fp16",
    "int8_baseline",
    "int8_ours",
    "int8_fused",
    "int4_baseline",
    "int4_fused",
    "int4_ours",
    "int4_ours_mixed",
    "kivi_style",
    "int4_kivi_aligned",
    "int4_mixed_kv",
    "int4_ours_asym",
    "int4_ours_asym_ba",
]


# ---------------------------------------------------------------------------
# CHK-018: Shared IO helpers — used by check_run_completeness.py and
# run_experiments.py.  Moved here to eliminate duplication.
# ---------------------------------------------------------------------------


def split_csv(values: str | None) -> List[str]:
    """Split a comma-separated string into stripped, non-empty tokens."""
    if not values:
        return []
    return [x.strip() for x in str(values).split(",") if x.strip()]


def read_json(path: Path) -> Dict[str, Any] | None:
    """Read a JSON file, returning None if missing or not a dict.

    Logs a warning on JSON decode errors instead of silently returning None.
    """
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _logger.warning("Failed to parse JSON from %s: %s", path, exc)
        return None
    except OSError as exc:
        _logger.warning("OS error reading %s: %s", path, exc)
        return None
    except Exception as exc:
        _logger.warning("Unexpected error reading %s: %s", path, exc)
        return None
    if not isinstance(data, dict):
        return None
    return data


def read_text(path: Path) -> str:
    """Read a text file, using replacement characters for non-UTF-8 bytes.

    Uses errors='replace' so that corrupted bytes are visible as U+FFFD rather
    than silently dropped.
    """
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        # CFG-052: Log instead of silently returning empty string.
        _logger.warning("Error reading text file %s: %s", path, exc)
        return ""


def load_config(config_path: str) -> Dict[str, Any]:
    """Load YAML config file.

    Raises
    ------
    FileNotFoundError
        CFG-051: If *config_path* does not exist (with contextual message).
    ValueError
        If the file is empty, not a mapping, or contains invalid YAML (CFG-035).
    """
    p = Path(config_path)
    # CFG-051: Explicit existence check with context, matching read_json style.
    if not p.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path!r}. "
            "Check the --config path or configs/ directory."
        )
    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        # CFG-035: Wrap yaml.YAMLError with path context, matching read_json style.
        raise ValueError(
            f"Invalid YAML in config file {config_path!r}: {exc}"
        ) from exc
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

    # CFG-034: Hardcode fallbacks (16 / 99.5) now match the project-standard
    # quant_defaults in exp_matrix.yaml rather than the previous 128 / 99.9
    # which diverged from actual tuned values.  A warning is emitted when
    # fallback is actually triggered so mis-configurations are visible.
    _FALLBACK_GROUP_SIZE = 16
    _FALLBACK_CLIP_PERCENTILE = 99.5
    clip_percentile_k = run_entry.get(
        "clip_percentile_k",
        run_entry.get("clip_percentile", quant_defaults.get("clip_percentile_k", _FALLBACK_CLIP_PERCENTILE)),
    )
    clip_percentile_v = run_entry.get(
        "clip_percentile_v",
        run_entry.get("clip_percentile", quant_defaults.get("clip_percentile_v", _FALLBACK_CLIP_PERCENTILE)),
    )
    group_size_k = run_entry.get(
        "group_size_k",
        run_entry.get("group_size", quant_defaults.get("group_size_k", _FALLBACK_GROUP_SIZE)),
    )
    group_size_v = run_entry.get(
        "group_size_v",
        run_entry.get("group_size", quant_defaults.get("group_size_v", _FALLBACK_GROUP_SIZE)),
    )
    # Warn if fallback was actually used (quant_defaults had no value).
    if not quant_defaults.get("group_size_k") and "group_size" not in run_entry:
        _logger.warning(
            "resolve_run_config: group_size_k for run %r fell through to "
            "hardcoded fallback %d; consider setting quant_defaults.group_size_k in YAML.",
            run_name, _FALLBACK_GROUP_SIZE,
        )

    # CFG-049: kv_mode is required, None causes silent fp16 fallback
    kv_mode = run_entry.get("kv_mode")
    if kv_mode is None:
        raise ValueError("run entry missing required 'kv_mode' field")
    resolved = {
        "model_id": project.get("model_id"),
        "kv_mode": kv_mode,
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
        "model_revision": project.get("model_revision"),  # CFG-031: pass revision to child scripts
        "dtype": runtime.get("dtype"),
        "seed": run_entry.get("seed", runtime.get("seed")),
        "calib_file": run_entry.get("calib_file", quant_defaults.get("calib_file")),
        "use_attn_temperature": run_entry.get(
            "use_attn_temperature", quant_defaults.get("use_attn_temperature")
        ),
        # EVL-089: pass use_static_scales so matrix runner can override via config
        "use_static_scales": run_entry.get(
            "use_static_scales", quant_defaults.get("use_static_scales", True)
        ),
        # CFG-030: pass adaptive_static_* fields so that child scripts invoked
        # via --config+--run_name get the same values as the run_experiments.py
        # dispatch path (which reads these from its own resolve_quant_params).
        "adaptive_static_scales": run_entry.get(
            "adaptive_static_scales", quant_defaults.get("adaptive_static_scales", False)
        ),
        "adaptive_static_margin": run_entry.get(
            "adaptive_static_margin", quant_defaults.get("adaptive_static_margin", 1.0)
        ),
        "adaptive_static_k": run_entry.get(
            "adaptive_static_k", quant_defaults.get("adaptive_static_k", True)
        ),
        "adaptive_static_v": run_entry.get(
            "adaptive_static_v", quant_defaults.get("adaptive_static_v", True)
        ),
        "k_bits": run_entry.get("k_bits"),
        "v_bits": run_entry.get("v_bits"),
        # Allocator backends read per-layer (k_bits, v_bits) from this JSON;
        # required for kv_mode=int4_ours_asym_alloc. Optional for other modes.
        "policy_json": run_entry.get("policy_json"),
    }

    # CFG-053: Extract runtime.decoding section so child scripts can use
    # centrally-defined greedy decoding parameters instead of hardcoding.
    decoding = runtime.get("decoding", {})
    if decoding:
        resolved["temperature"] = decoding.get("temperature")
        resolved["top_p"] = decoding.get("top_p")
        resolved["top_k"] = decoding.get("top_k")

    return resolved


def normalize_kv_params(args: argparse.Namespace) -> None:
    """Normalize k/v group_size and clip_percentile into shared args.

    **Mutates *args* in-place** (CFG-037): sets ``group_size_k``,
    ``group_size_v``, ``clip_percentile_k``, ``clip_percentile_v``, and
    the legacy ``group_size`` / ``clip_percentile`` attributes.  The
    function is intentionally side-effect-based so that all 7+ call sites
    get consistent attribute resolution.
    """
    # CFG-033: Use `is not None` instead of `or` to avoid falsy-value
    # short-circuit (e.g. group_size_k=0 or clip_percentile_k=0.0 would
    # silently fall through to the backup value with bare `or`).
    _gk = getattr(args, "group_size_k", None)
    group_size_k = _gk if _gk is not None else getattr(args, "group_size", None)
    _gv = getattr(args, "group_size_v", None)
    group_size_v = _gv if _gv is not None else getattr(args, "group_size", None)
    _ck = getattr(args, "clip_percentile_k", None)
    clip_k = _ck if _ck is not None else getattr(args, "clip_percentile", None)
    _cv = getattr(args, "clip_percentile_v", None)
    clip_v = _cv if _cv is not None else getattr(args, "clip_percentile", None)

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


_ALLOCATOR_ONLY_KV_MODES = ("int4_ours_asym_alloc",)
_ALLOCATOR_REQUIRED_DECODE_ATTN_IMPL = "torch_ref"


def normalize_allocator_cli_args(args: argparse.Namespace) -> None:
    """Enforce allocator-kv_mode invariants at CLI normalization time.

    Called after ``parser.parse_args()`` *and* ``resolve_run_config()``, so
    yaml-driven runs whose ``runtime.kernel_defaults.decode_attn_impl`` is
    ``triton_fused`` are folded into ``args`` before this helper runs.

    Enforces two invariants when ``args.kv_mode`` is an allocator-only mode:

    1. ``decode_attn_impl`` must be ``torch_ref``. If it is ``None``, fill in
       ``torch_ref``. If it is any other value (e.g. ``triton_fused`` pulled
       from yaml ``kernel_defaults``), override it to ``torch_ref`` and emit
       a :class:`UserWarning` so the override is visible in logs — raising
       would break every config-driven allocator run.
    2. ``policy_json`` must be non-empty. Allocator backends need per-layer
       ``(k_bits, v_bits)`` and fail deep inside ``generate_from_ids`` if it
       is missing; failing here turns that into an early, cheap CLI error.

    Mutates *args* in-place. Safe to call unconditionally from any CLI
    entrypoint.
    """
    kv_mode = getattr(args, "kv_mode", None)
    if kv_mode not in _ALLOCATOR_ONLY_KV_MODES:
        return

    current = getattr(args, "decode_attn_impl", None)
    if current not in (None, _ALLOCATOR_REQUIRED_DECODE_ATTN_IMPL):
        warnings.warn(
            f"kv_mode={kv_mode!r} requires decode_attn_impl="
            f"{_ALLOCATOR_REQUIRED_DECODE_ATTN_IMPL!r}; overriding "
            f"{current!r} (from CLI or yaml kernel_defaults).",
            UserWarning,
            stacklevel=2,
        )
    setattr(args, "decode_attn_impl", _ALLOCATOR_REQUIRED_DECODE_ATTN_IMPL)

    policy_json = getattr(args, "policy_json", None)
    if not policy_json:
        raise ValueError(
            f"kv_mode={kv_mode!r} requires --policy_json <file>, but none was "
            "provided. Pass --policy_json on the command line or set "
            "`policy_json:` in the yaml run entry."
        )
