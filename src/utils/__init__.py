"""Utility modules for timing, logging, and common helpers."""

from src.utils.timing import (
    CUDATimer,
    TimingStats,
    timer_context,
    get_gpu_memory_mb,
    reset_gpu_memory_stats,
)
from src.utils.repro import (
    set_seed,
    get_git_commit,
    get_hardware_info,
    build_config_snapshot,
    ensure_dir,
    write_config_snapshot,
    resolve_quant_bits,
)
# UTL-010: Export hf utility for consistent module API.
from src.utils.hf import resolve_pretrained_path

__all__ = [
    "CUDATimer",
    "TimingStats",
    "timer_context",
    "get_gpu_memory_mb",
    "reset_gpu_memory_stats",
    "set_seed",
    "get_git_commit",
    "get_hardware_info",
    "build_config_snapshot",
    "ensure_dir",
    "write_config_snapshot",
    "resolve_quant_bits",
    "resolve_pretrained_path",
]
