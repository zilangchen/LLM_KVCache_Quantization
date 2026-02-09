#!/usr/bin/env python3
"""
Reproducibility utilities (seed control and metadata helpers).
"""

from __future__ import annotations

from datetime import datetime
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
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    if deterministic:
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        try:
            torch.use_deterministic_algorithms(True)
        except Exception:
            # Fall back to best-effort determinism if the backend disallows it.
            pass
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


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
    """
    snapshot: Dict[str, Any] = {
        "script": script_name,
        "timestamp": datetime.now().isoformat(),
        "args": vars(args),
        "decoding": {
            "temperature": 0.0,
            "top_p": 1.0,
            "top_k": 0,
        },
    }
    if extra:
        snapshot.update(extra)
    return snapshot


def ensure_dir(path: str) -> None:
    """Ensure a directory exists."""
    os.makedirs(path, exist_ok=True)


def write_config_snapshot(run_dir: str, snapshot: Dict[str, Any]) -> str:
    """
    Write config snapshot to a run directory.

    Returns:
        Path to the written snapshot file.
    """
    ensure_dir(run_dir)
    path = os.path.join(run_dir, "config_snapshot.yaml")
    with open(path, "w") as f:
        yaml.safe_dump(snapshot, f, sort_keys=False)
    return path
