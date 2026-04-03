#!/usr/bin/env python3
"""
FP16 KV Cache implementation.

This module provides a simple FP16 KV cache that stores key-value tensors
for each layer, supporting dynamic sequence length growth.

Usage:
    from src.cache import FP16KVCache

    cache = FP16KVCache(num_layers=28, device="cuda")
    cache.append(layer_id=0, k=k_tensor, v=v_tensor)
    k, v = cache.get_kv(layer_id=0)
"""

from typing import List, Optional, Tuple

import torch
from torch import Tensor


class FP16KVCache:
    """
    FP16 KV Cache for LLM inference.

    Stores key-value tensors for each layer, supporting:
    - Batch append during prefill (multiple tokens)
    - Single token append during decode
    - Efficient retrieval for attention computation

    Attributes:
        num_layers: Number of transformer layers
        device: Device to store tensors on
        dtype: Data type (always torch.float16)
    """

    def __init__(
        self,
        num_layers: int,
        device: str = "cuda",
        dtype: torch.dtype = torch.float16,
        max_seq_len: Optional[int] = None,
    ):
        """
        Initialize FP16 KV Cache.

        Args:
            num_layers: Number of transformer layers
            device: Device to store tensors on ("cuda" or "cpu")
            dtype: Data type for storage (default: torch.float16)

        Raises:
            ValueError: If num_layers <= 0
        """
        if num_layers <= 0:
            raise ValueError(f"num_layers must be > 0, got {num_layers}")

        self.num_layers = num_layers
        self.device = device
        self.dtype = dtype
        self.max_seq_len = int(max_seq_len) if max_seq_len is not None else None
        if self.max_seq_len is not None and self.max_seq_len <= 0:
            raise ValueError(f"max_seq_len must be > 0, got {self.max_seq_len}")
        self._min_capacity = 256

        # Storage tensors are preallocated by capacity and written by slices.
        # Actual valid length is tracked per layer in _layer_seq_lens.
        self._k_cache: List[Optional[Tensor]] = [None] * num_layers
        self._v_cache: List[Optional[Tensor]] = [None] * num_layers
        self._layer_seq_lens: List[int] = [0] * num_layers
        self._layer_capacity: List[int] = [0] * num_layers
        self._seq_len: int = 0

    def _ensure_capacity(
        self,
        layer_id: int,
        batch: int,
        heads: int,
        head_dim: int,
        target_len: int,
    ) -> None:
        if self.max_seq_len is not None and target_len > self.max_seq_len:
            raise ValueError(
                f"target_len {target_len} exceeds max_seq_len {self.max_seq_len} for layer {layer_id}"
            )
        capacity = self._layer_capacity[layer_id]
        k_buf = self._k_cache[layer_id]
        v_buf = self._v_cache[layer_id]

        if k_buf is not None and v_buf is not None:
            if k_buf.shape[0] != batch or k_buf.shape[1] != heads or k_buf.shape[3] != head_dim:
                raise ValueError(
                    "Inconsistent KV shape for layer "
                    f"{layer_id}: existing={k_buf.shape}, incoming=({batch}, {heads}, *, {head_dim})"
                )

        if k_buf is None or v_buf is None:
            new_capacity = max(target_len, self._min_capacity)
            if self.max_seq_len is not None:
                new_capacity = min(new_capacity, self.max_seq_len)
                if new_capacity < target_len:
                    raise ValueError(
                        f"target_len {target_len} exceeds capped capacity {new_capacity} for layer {layer_id}"
                    )
            self._k_cache[layer_id] = torch.empty(
                (batch, heads, new_capacity, head_dim),
                device=self.device,
                dtype=self.dtype,
            )
            self._v_cache[layer_id] = torch.empty(
                (batch, heads, new_capacity, head_dim),
                device=self.device,
                dtype=self.dtype,
            )
            self._layer_capacity[layer_id] = new_capacity
            return

        if target_len <= capacity:
            return

        new_capacity = max(target_len, capacity * 2)
        if self.max_seq_len is not None:
            new_capacity = min(new_capacity, self.max_seq_len)
            if new_capacity < target_len:
                raise ValueError(
                    f"target_len {target_len} exceeds capped capacity {new_capacity} for layer {layer_id}"
                )
        old_len = self._layer_seq_lens[layer_id]

        new_k = torch.empty(
            (batch, heads, new_capacity, head_dim),
            device=self.device,
            dtype=self.dtype,
        )
        new_v = torch.empty(
            (batch, heads, new_capacity, head_dim),
            device=self.device,
            dtype=self.dtype,
        )
        if old_len > 0:
            new_k[:, :, :old_len, :] = k_buf[:, :, :old_len, :]
            new_v[:, :, :old_len, :] = v_buf[:, :, :old_len, :]

        self._k_cache[layer_id] = new_k
        self._v_cache[layer_id] = new_v
        self._layer_capacity[layer_id] = new_capacity

    def append(self, layer_id: int, k: Tensor, v: Tensor) -> None:
        """
        Append key-value tensors to the cache for a specific layer.

        Args:
            layer_id: Layer index (0-indexed)
            k: Key tensor, shape [batch, num_kv_heads, new_seq_len, head_dim]
            v: Value tensor, shape [batch, num_kv_heads, new_seq_len, head_dim]

        Raises:
            ValueError: If layer_id is out of range or shapes are mismatched
        """
        # Validate layer_id
        if layer_id < 0 or layer_id >= self.num_layers:
            raise ValueError(
                f"layer_id {layer_id} out of range [0, {self.num_layers})"
            )

        # Validate shapes
        if k.shape != v.shape:
            raise ValueError(
                f"K and V shapes must match. Got K: {k.shape}, V: {v.shape}"
            )

        if k.dim() != 4:
            raise ValueError(
                f"K/V must be 4D [batch, heads, seq, dim]. Got {k.dim()}D"
            )

        # Convert to target dtype and device if needed
        k = k.to(device=self.device, dtype=self.dtype)
        v = v.to(device=self.device, dtype=self.dtype)

        new_seq_len = k.shape[2]
        batch, heads, _, head_dim = k.shape
        old_len = self._layer_seq_lens[layer_id]
        target_len = old_len + new_seq_len
        self._ensure_capacity(layer_id, batch, heads, head_dim, target_len)

        self._k_cache[layer_id][:, :, old_len:target_len, :] = k
        self._v_cache[layer_id][:, :, old_len:target_len, :] = v
        self._layer_seq_lens[layer_id] = target_len

        # Update sequence length (use layer 0 as reference)
        if layer_id == 0:
            self._seq_len = target_len

    def get_kv(self, layer_id: int) -> Tuple[Tensor, Tensor]:
        """
        Get key-value tensors for a specific layer.

        Args:
            layer_id: Layer index (0-indexed)

        Returns:
            Tuple of (k, v) tensors with shapes
            [batch, num_kv_heads, seq_len, head_dim]

        Raises:
            ValueError: If layer_id is out of range or cache is empty
        """
        if layer_id < 0 or layer_id >= self.num_layers:
            raise ValueError(
                f"layer_id {layer_id} out of range [0, {self.num_layers})"
            )

        if self._k_cache[layer_id] is None:
            raise ValueError(
                f"Cache for layer {layer_id} is empty. Call append() first."
            )

        seq_len = self._layer_seq_lens[layer_id]
        return (
            self._k_cache[layer_id][:, :, :seq_len, :],
            self._v_cache[layer_id][:, :, :seq_len, :],
        )

    def get_seq_len(self) -> int:
        """
        Get current sequence length in the cache.

        Returns:
            Number of tokens currently cached
        """
        return self._seq_len

    def clear(self) -> None:
        """Reset sequence lengths while keeping allocated buffers for reuse."""
        self._layer_seq_lens = [0] * self.num_layers
        self._seq_len = 0

    def release(self) -> None:
        """Release all allocated buffers."""
        self._k_cache = [None] * self.num_layers
        self._v_cache = [None] * self.num_layers
        self._layer_seq_lens = [0] * self.num_layers
        self._layer_capacity = [0] * self.num_layers
        self._seq_len = 0

    def get_memory_mb(self) -> float:
        """
        Get current memory usage in MB.

        Returns:
            Memory usage in megabytes
        """
        total_bytes = 0
        for k, v in zip(self._k_cache, self._v_cache):
            if k is not None:
                total_bytes += k.numel() * k.element_size()
            if v is not None:
                total_bytes += v.numel() * v.element_size()
        return total_bytes / (1024 * 1024)

    def to_tuple(self) -> Tuple[Tuple[Tensor, Tensor], ...]:
        """
        Convert cache to HuggingFace past_key_values format.

        Returns:
            Tuple of (k, v) tuples for each layer

        Raises:
            ValueError: If any layer cache is empty
        """
        result = []
        for i in range(self.num_layers):
            if self._k_cache[i] is None:
                raise ValueError(f"Layer {i} cache is empty")
            result.append(self.get_kv(i))
        return tuple(result)

    @classmethod
    def from_tuple(
        cls,
        past_key_values: Tuple[Tuple[Tensor, Tensor], ...],
        device: str = "cuda",
    ) -> "FP16KVCache":
        """
        Create cache from HuggingFace past_key_values format.

        Args:
            past_key_values: Tuple of (k, v) tuples from model output
            device: Device to store tensors on

        Returns:
            FP16KVCache instance with loaded data
        """
        num_layers = len(past_key_values)
        cache = cls(num_layers=num_layers, device=device)

        for layer_id, (k, v) in enumerate(past_key_values):
            k = k.to(device=device, dtype=cache.dtype)
            v = v.to(device=device, dtype=cache.dtype)
            batch, heads, seq_len, head_dim = k.shape
            capacity = max(seq_len, cache._min_capacity)
            cache._k_cache[layer_id] = torch.empty(
                (batch, heads, capacity, head_dim),
                device=device,
                dtype=cache.dtype,
            )
            cache._v_cache[layer_id] = torch.empty(
                (batch, heads, capacity, head_dim),
                device=device,
                dtype=cache.dtype,
            )
            cache._k_cache[layer_id][:, :, :seq_len, :] = k
            cache._v_cache[layer_id][:, :, :seq_len, :] = v
            cache._layer_seq_lens[layer_id] = seq_len
            cache._layer_capacity[layer_id] = capacity

        # KVC-071: use max across all layers, not just layer 0
        max_seq = max(cache._layer_seq_lens) if cache._layer_seq_lens else 0
        if max_seq > 0:
            cache._seq_len = max_seq

        return cache

    def __repr__(self) -> str:
        return (
            f"FP16KVCache(num_layers={self.num_layers}, "
            f"seq_len={self._seq_len}, "
            f"memory={self.get_memory_mb():.2f}MB)"
        )
