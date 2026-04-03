#!/usr/bin/env python3
"""
Reproducibility utilities (seed control and metadata helpers).
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import os
import random

import numpy as np
import torch
import yaml


def set_seed(seed: int = 1234, deterministic: bool = True) -> None:
    """
    Set random seeds across Python, NumPy, and PyTorch.

    Args:
        seed: Seed value.
        deterministic: Enable deterministic algorithms when possible.
    """
    # UTL-001: np.random.seed() requires a non-negative integer.  Validate
    # before calling any library so all three RNGs stay in sync on failure.
    if not isinstance(seed, int) or seed < 0:
        raise ValueError(
            f"seed must be a non-negative integer, got {seed!r}. "
            "numpy.random.seed() rejects negative values, and allowing "
            "partial seeding (Python ok, numpy fails) breaks reproducibility."
        )
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    if deterministic:
        # UTIL-006: CUBLAS_WORKSPACE_CONFIG is set here, after torch has already
        # been imported at module level. cuBLAS reads this env var lazily (on first
        # kernel launch), so setting it here is effective in practice. However, if
        # a cuBLAS kernel has already been launched before this call, the setting
        # may have no effect for that specific workspace configuration.
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        try:
            torch.use_deterministic_algorithms(True)
        except Exception as exc:
            # UTIL-005: Log a warning instead of silently swallowing the failure,
            # so users know deterministic mode could not be enabled.
            import warnings
            warnings.warn(
                f"torch.use_deterministic_algorithms(True) failed: {exc}. "
                "Falling back to best-effort determinism.",
                RuntimeWarning,
            )
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def get_git_commit() -> str:
    """Get current git commit hash (short, 8 chars).

    Attempts to resolve the project root by walking up from this file's
    location; falls back to the current working directory if the heuristic
    fails.  Returns ``"unknown"`` when git is unavailable or the directory
    is not a repository.
    """
    # Best-effort project root: src/utils/repro.py -> ../../
    try:
        _project_root = str(Path(__file__).resolve().parent.parent.parent)
    except Exception:
        _project_root = None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=_project_root,
            timeout=5,  # UTL-003: prevent infinite hang on NFS/index corruption
        )
        return result.stdout.strip()[:8]
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"


def get_hardware_info() -> Dict[str, str]:
    """
    Collect basic GPU hardware info for run metadata.
    """
    info = {"gpu": "N/A", "gpu_memory": "N/A"}
    if torch.cuda.is_available():
        info["gpu"] = torch.cuda.get_device_name(0)
        props = torch.cuda.get_device_properties(0)
        info["gpu_memory"] = f"{props.total_memory / 1e9:.1f} GB"
    return info


def build_config_snapshot(
    script_name: str,
    args: Any,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a minimal, serializable config snapshot for a run.

    Note (UTIL-010): The ``decoding`` dict is intentionally hardcoded to
    greedy-decode parameters (temperature=0, top_p=1, top_k=0). This is a
    fixed project decision (see CLAUDE.md §9 "Fixed Decisions") to ensure
    all experiments use identical decoding settings for reproducibility.
    """
    # UTIL-007: Guard against objects without __dict__ (e.g. plain dicts).
    # UTL-005: Copy args to avoid holding a live reference to __dict__.
    if isinstance(args, dict):
        args_dict = dict(args)
    elif hasattr(args, "__dict__"):
        args_dict = dict(vars(args))
    else:
        args_dict = {"_raw": str(args)}
    # UTL-008: Use UTC timestamp for cross-timezone comparability.
    snapshot: Dict[str, Any] = {
        "script": script_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "args": args_dict,
        "decoding": {
            "temperature": 0.0,
            "top_p": 1.0,
            "top_k": 0,
        },
    }
    if extra:
        # UTL-004: Warn if extra would overwrite core snapshot keys.
        _core_keys = {"script", "timestamp", "args", "decoding"}
        _conflicts = _core_keys & set(extra)
        if _conflicts:
            import warnings
            warnings.warn(
                f"build_config_snapshot: extra keys {_conflicts} overwrite core snapshot fields",
                RuntimeWarning,
            )
        snapshot.update(extra)
    return snapshot


def resolve_quant_bits(kv_mode: str, quant_bits_arg: int | None = None) -> int:
    """
    Determine effective quantization bit-width from kv_mode string.

    This is the **canonical** implementation. Scripts that previously defined
    a local ``_resolve_quant_bits`` should import this function instead:

        from src.utils.repro import resolve_quant_bits

    Args:
        kv_mode: KV cache mode string (e.g. "int8_baseline", "int4_ours", "kivi_style").
        quant_bits_arg: Explicit override from CLI ``--quant_bits``; takes precedence.

    Returns:
        Effective bit-width (4, 8, or 16).
    """
    if quant_bits_arg is not None:
        return int(quant_bits_arg)
    mode = str(kv_mode)
    if mode == "kivi_style":
        # UTIL-009: KIVI supports both INT4 and INT8. Default to 8 only when
        # the caller did not pass an explicit quant_bits_arg. For KIVI-INT4,
        # callers MUST supply quant_bits_arg=4 (handled by the early return above).
        return 8
    if "int4" in mode:
        return 4
    if "int8" in mode:
        return 8
    return 16


def ensure_dir(path: str) -> None:
    """Ensure a directory exists."""
    os.makedirs(path, exist_ok=True)


def write_config_snapshot(run_dir: str, snapshot: Dict[str, Any]) -> Optional[str]:
    """
    Write config snapshot to a run directory.

    Returns:
        Path to the written snapshot file, or None if writing failed.
    """
    # UTIL-008: Wrap I/O in try/except so callers are not killed by
    # permission errors or disk-full conditions during snapshot writes.
    try:
        ensure_dir(run_dir)
        path = os.path.join(run_dir, "config_snapshot.yaml")
        with open(path, "w") as f:
            yaml.safe_dump(snapshot, f, sort_keys=False)
        return path
    except Exception as exc:
        import warnings
        warnings.warn(
            f"Failed to write config snapshot to {run_dir}: {exc}",
            RuntimeWarning,
        )
        return None
