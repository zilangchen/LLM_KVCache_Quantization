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

        # Storage: list of (k, v) tuples per layer
        # Each k, v has shape [batch, num_kv_heads, seq_len, head_dim]
        self._k_cache: List[Optional[Tensor]] = [None] * num_layers
        self._v_cache: List[Optional[Tensor]] = [None] * num_layers
        self._seq_len: int = 0

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

        # Append to existing cache or initialize
        if self._k_cache[layer_id] is None:
            # First append for this layer
            self._k_cache[layer_id] = k
            self._v_cache[layer_id] = v
        else:
            # Concatenate along sequence dimension
            self._k_cache[layer_id] = torch.cat(
                [self._k_cache[layer_id], k], dim=2
            )
            self._v_cache[layer_id] = torch.cat(
                [self._v_cache[layer_id], v], dim=2
            )

        # Update sequence length (use layer 0 as reference)
        if layer_id == 0:
            self._seq_len += new_seq_len

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

        return self._k_cache[layer_id], self._v_cache[layer_id]

    def get_seq_len(self) -> int:
        """
        Get current sequence length in the cache.

        Returns:
            Number of tokens currently cached
        """
        return self._seq_len

    def clear(self) -> None:
        """Clear all cached key-value tensors."""
        self._k_cache = [None] * self.num_layers
        self._v_cache = [None] * self.num_layers
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
            result.append((self._k_cache[i], self._v_cache[i]))
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
            cache._k_cache[layer_id] = k.to(device=device)
            cache._v_cache[layer_id] = v.to(device=device)

        # Set sequence length from first layer
        if cache._k_cache[0] is not None:
            cache._seq_len = cache._k_cache[0].shape[2]

        return cache

    def __repr__(self) -> str:
        return (
            f"FP16KVCache(num_layers={self.num_layers}, "
            f"seq_len={self._seq_len}, "
            f"memory={self.get_memory_mb():.2f}MB)"
        )
