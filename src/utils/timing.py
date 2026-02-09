#!/usr/bin/env python3
"""
Timing utilities for GPU-synchronized performance measurement.

Provides accurate TTFT (Time To First Token) and TPOT (Time Per Output Token)
measurements with proper CUDA synchronization.

Usage:
    from src.utils.timing import CUDATimer, timer_context

    # Using context manager
    with timer_context() as timer:
        # your GPU code here
        pass
    print(f"Elapsed: {timer.elapsed_ms:.2f} ms")

    # Using CUDATimer class
    timer = CUDATimer()
    timer.start()
    # your GPU code here
    timer.stop()
    print(f"Elapsed: {timer.elapsed_ms:.2f} ms")
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import List, Optional

import torch


@dataclass
class TimingStats:
    """Statistics for a series of timing measurements."""
    measurements: List[float] = field(default_factory=list)

    def add(self, elapsed_ms: float) -> None:
        """Add a timing measurement."""
        self.measurements.append(elapsed_ms)

    @property
    def mean_ms(self) -> float:
        """Average time in milliseconds."""
        if not self.measurements:
            return 0.0
        return sum(self.measurements) / len(self.measurements)

    @property
    def total_ms(self) -> float:
        """Total time in milliseconds."""
        return sum(self.measurements)

    @property
    def count(self) -> int:
        """Number of measurements."""
        return len(self.measurements)


class CUDATimer:
    """
    GPU-synchronized timer using CUDA events for accurate measurement.

    This timer ensures proper synchronization before and after timed regions
    to get accurate GPU execution time (not just CPU dispatch time).
    """

    def __init__(self, sync_before: bool = True, sync_after: bool = True):
        """
        Initialize the timer.

        Args:
            sync_before: Whether to synchronize before starting the timer.
            sync_after: Whether to synchronize after stopping the timer.
        """
        self.sync_before = sync_before
        self.sync_after = sync_after
        self._start_time: Optional[float] = None
        self._elapsed_ms: Optional[float] = None
        self._cuda_available = torch.cuda.is_available()

    def start(self) -> "CUDATimer":
        """Start the timer. Returns self for chaining."""
        if self._cuda_available and self.sync_before:
            torch.cuda.synchronize()
        self._start_time = time.perf_counter()
        self._elapsed_ms = None
        return self

    def stop(self) -> float:
        """Stop the timer and return elapsed time in milliseconds."""
        if self._start_time is None:
            raise RuntimeError("Timer was not started. Call start() first.")

        if self._cuda_available and self.sync_after:
            torch.cuda.synchronize()

        end_time = time.perf_counter()
        self._elapsed_ms = (end_time - self._start_time) * 1000.0
        return self._elapsed_ms

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        if self._elapsed_ms is None:
            raise RuntimeError("Timer not stopped. Call stop() first.")
        return self._elapsed_ms

    def reset(self) -> None:
        """Reset the timer for reuse."""
        self._start_time = None
        self._elapsed_ms = None


@contextmanager
def timer_context(sync_before: bool = True, sync_after: bool = True):
    """
    Context manager for timing GPU operations.

    Usage:
        with timer_context() as timer:
            # GPU operations
            pass
        print(f"Elapsed: {timer.elapsed_ms:.2f} ms")

    Args:
        sync_before: Synchronize CUDA before entering the block.
        sync_after: Synchronize CUDA before exiting the block.

    Yields:
        CUDATimer: Timer object with elapsed_ms property after block exits.
    """
    timer = CUDATimer(sync_before=sync_before, sync_after=sync_after)
    timer.start()
    try:
        yield timer
    finally:
        timer.stop()


def get_gpu_memory_mb() -> float:
    """
    Get current GPU memory usage in MB.

    Returns:
        Peak allocated GPU memory in MB, or 0.0 if CUDA not available.
    """
    if not torch.cuda.is_available():
        return 0.0
    return torch.cuda.max_memory_allocated() / (1024 * 1024)


def reset_gpu_memory_stats() -> None:
    """Reset GPU memory statistics for fresh measurement."""
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.empty_cache()
