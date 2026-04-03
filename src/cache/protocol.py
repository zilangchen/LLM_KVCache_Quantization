#!/usr/bin/env python3
"""
KVC-078: Lightweight KV cache protocol for static type checking.

Uses typing.Protocol (PEP 544) so that concrete cache classes satisfy
the contract structurally -- no base class inheritance or decorator
registration required.  Existing classes (FP16KVCache, INT8KVCache,
INT4KVCache, KIVIStyleKVCache, MixedKVCache, RoleAwareAsymKVCache)
all conform without modification.

This is NOT an ABC: it adds zero runtime overhead and does not change
any class hierarchy.  Its sole purpose is to let type checkers (mypy,
pyright) verify that new cache implementations expose the required
interface.

Usage for type annotations:
    from src.cache.protocol import KVCacheProtocol

    def run_inference(cache: KVCacheProtocol, ...) -> ...:
        cache.append(layer_id, k, v)
        k, v = cache.get_kv(layer_id)
"""

from typing import Protocol, Tuple, runtime_checkable

import torch
from torch import Tensor


@runtime_checkable
class KVCacheProtocol(Protocol):
    """Structural protocol that every KV cache class must satisfy."""

    num_layers: int
    device: str

    def append(self, layer_id: int, k: Tensor, v: Tensor) -> None:
        """Quantize (if applicable) and store K/V for a layer."""
        ...

    def get_kv(self, layer_id: int) -> Tuple[Tensor, Tensor]:
        """Retrieve (dequantized) K/V for a layer."""
        ...

    def get_seq_len(self) -> int:
        """Return current sequence length."""
        ...

    def clear(self) -> None:
        """Reset sequence lengths; keep pre-allocated buffers."""
        ...

    def release(self) -> None:
        """Release all buffers and reset state."""
        ...

    def get_memory_mb(self) -> float:
        """Return current memory usage in MB."""
        ...

    def to_tuple(self) -> Tuple[Tuple[Tensor, Tensor], ...]:
        """Convert to HuggingFace past_key_values format."""
        ...
