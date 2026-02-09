#!/usr/bin/env python3
"""
INT4 KV Cache implementation.

This module provides an INT4 quantized KV cache for more aggressive compression.
Storage uses INT8 (no bit packing for simplicity).
"""

from typing import List, Optional, Tuple

import torch
from torch import Tensor

from src.quant.int4_basic import (
    dequantize_symmetric_int4,
    quantize_symmetric_int4,
)


class INT4KVCache:
    """
    INT4 KV Cache for LLM inference.

    Stores key-value tensors in INT4 format (stored as INT8),
    performing quantization on append and dequantization on retrieval.

    Attributes:
        num_layers: Number of transformer layers
        device: Device to store tensors on
        clip_percentile: Clipping percentile for quantization
        group_size: Group size for quantization (smaller = more precision, more overhead)
        dtype: Output data type (default: torch.float16)
    """

    def __init__(
        self,
        num_layers: int,
        device: str = "cuda",
        clip_percentile: float = 99.9,
        group_size: int = 32,  # Smaller default for INT4
        dtype: torch.dtype = torch.float16,
    ):
        if num_layers <= 0:
            raise ValueError(f"num_layers must be > 0, got {num_layers}")

        self.num_layers = num_layers
        self.device = device
        self.clip_percentile = clip_percentile
        self.group_size = group_size
        self.dtype = dtype

        # Storage: list of (q_k, q_v, k_scale, v_scale) per layer
        self._k_cache: List[Optional[Tensor]] = [None] * num_layers
        self._v_cache: List[Optional[Tensor]] = [None] * num_layers
        self._k_scale: List[Optional[Tensor]] = [None] * num_layers
        self._v_scale: List[Optional[Tensor]] = [None] * num_layers
        self._seq_len: int = 0

    def append(self, layer_id: int, k: Tensor, v: Tensor) -> None:
        """
        Quantize and append KV tensors to the cache.

        Args:
            layer_id: Layer index
            k: Key tensor (float)
            v: Value tensor (float)
        """
        if layer_id < 0 or layer_id >= self.num_layers:
            raise ValueError(f"layer_id {layer_id} out of range")

        # Quantize incoming K and V to INT4
        q_k, scale_k = quantize_symmetric_int4(
            k, self.clip_percentile, self.group_size
        )
        q_v, scale_v = quantize_symmetric_int4(
            v, self.clip_percentile, self.group_size
        )

        # Move to storage device
        q_k = q_k.to(self.device)
        scale_k = scale_k.to(self.device)
        q_v = q_v.to(self.device)
        scale_v = scale_v.to(self.device)

        new_seq_len = k.shape[2]

        # Append
        if self._k_cache[layer_id] is None:
            self._k_cache[layer_id] = q_k
            self._v_cache[layer_id] = q_v
            self._k_scale[layer_id] = scale_k
            self._v_scale[layer_id] = scale_v
        else:
            self._k_cache[layer_id] = torch.cat(
                [self._k_cache[layer_id], q_k], dim=2
            )
            self._v_cache[layer_id] = torch.cat(
                [self._v_cache[layer_id], q_v], dim=2
            )
            self._k_scale[layer_id] = torch.cat(
                [self._k_scale[layer_id], scale_k], dim=2
            )
            self._v_scale[layer_id] = torch.cat(
                [self._v_scale[layer_id], scale_v], dim=2
            )

        if layer_id == 0:
            self._seq_len += new_seq_len

    def get_kv(self, layer_id: int) -> Tuple[Tensor, Tensor]:
        """
        Dequantize and return KV tensors.

        Args:
            layer_id: Layer index

        Returns:
            Tuple of (k, v) tensors in float16
        """
        if self._k_cache[layer_id] is None:
            raise ValueError(f"Cache for layer {layer_id} is empty")

        q_k = self._k_cache[layer_id]
        scale_k = self._k_scale[layer_id]
        q_v = self._v_cache[layer_id]
        scale_v = self._v_scale[layer_id]

        # Dequantize
        k = dequantize_symmetric_int4(q_k, scale_k)
        v = dequantize_symmetric_int4(q_v, scale_v)

        return k, v

    def get_int4_tensors(self, layer_id: int) -> Tuple[Tensor, Tensor, Tensor, Tensor]:
        """
        Return raw INT4 KV tensors and scales.
        
        Returns:
            (k_int4, v_int4, k_scale, v_scale)
        """
        if self._k_cache[layer_id] is None:
            raise ValueError(f"Cache for layer {layer_id} is empty")
            
        return (
            self._k_cache[layer_id],
            self._v_cache[layer_id],
            self._k_scale[layer_id],
            self._v_scale[layer_id]
        )

    def get_seq_len(self) -> int:
        return self._seq_len

    def clear(self) -> None:
        self._k_cache = [None] * self.num_layers
        self._v_cache = [None] * self.num_layers
        self._k_scale = [None] * self.num_layers
        self._v_scale = [None] * self.num_layers
        self._seq_len = 0

    def get_memory_mb(self) -> float:
        """Get current memory usage in MB including scales."""
        total_bytes = 0
        for i in range(self.num_layers):
            if self._k_cache[i] is not None:
                # INT4 stored as INT8 (1 byte per value)
                # With bit packing, this could be 0.5 bytes
                total_bytes += self._k_cache[i].numel() * 1
                total_bytes += self._v_cache[i].numel() * 1
                # Scale tensors (FP16)
                total_bytes += (
                    self._k_scale[i].numel() * self._k_scale[i].element_size()
                )
                total_bytes += (
                    self._v_scale[i].numel() * self._v_scale[i].element_size()
                )
        return total_bytes / (1024 * 1024)

    def to_tuple(self):
        """
        Convert cache to HuggingFace past_key_values format.
        Returns dequantized (k, v) tuples for each layer.
        """
        result = []
        for i in range(self.num_layers):
            if self._k_cache[i] is None:
                raise ValueError(f"Layer {i} cache is empty")
            k, v = self.get_kv(i)  # Dequantize
            result.append((k, v))
        return tuple(result)
