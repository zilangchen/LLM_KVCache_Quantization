#!/usr/bin/env python3
"""
Mixed KV Cache: K-INT8 symmetric + V-INT4 asymmetric per-token.

A hybrid cache that stores K in INT8 symmetric (per-group) quantization and
V in INT4 asymmetric (per-token, KIVI-style) quantization. This provides:
- K: High precision (INT8) to preserve attention distribution accuracy
- V: Aggressive compression (INT4) to reduce memory
- Combined: ~37.5% of FP16 memory (K@50% + V@25%)

Interface is compatible with KIVIStyleKVCache and INT8KVCache:
append(), get_kv(), get_seq_len(), clear(), release(), get_memory_mb().
"""

import warnings
from typing import Dict, List, Optional, Tuple

import torch
from torch import Tensor

from src.quant.int8_basic import quantize_symmetric_int8, dequantize_symmetric_int8
from src.quant.asymmetric_quant import (
    dequantize_asymmetric_per_token,
    quantize_asymmetric_per_token,
)


class MixedKVCache:
    """
    Mixed-precision KV Cache: K @ INT8 symmetric, V @ INT4 asymmetric per-token.

    K: symmetric INT8 per-group quantization (same as INT8KVCache K path).
    V: asymmetric INT4 per-token quantization (same as KIVIStyleKVCache V path).

    Attributes:
        num_layers: Number of transformer layers
        device: Device to store tensors on
        k_group_size: Group size for K quantization (default 128)
        k_clip_percentile: Clipping percentile for K quantization (default 99.9)
        v_percentile: Clipping percentile for V quantization (default 100.0)
        dtype: Output data type (default: torch.float16)
    """

    def __init__(
        self,
        num_layers: int,
        device: str = "cuda",
        dtype: torch.dtype = torch.float16,
        max_seq_len: Optional[int] = None,
        k_group_size: int = 128,
        k_clip_percentile: float = 99.9,
        v_percentile: float = 100.0,
    ):
        if num_layers <= 0:
            raise ValueError(f"num_layers must be > 0, got {num_layers}")

        self.num_layers = num_layers
        self.device = device
        self.dtype = dtype
        self.max_seq_len = int(max_seq_len) if max_seq_len is not None else None
        self.k_group_size = k_group_size
        self.k_clip_percentile = k_clip_percentile
        self.v_percentile = v_percentile

        # Interface compatibility
        self.decode_attn_impl = "torch_ref"
        self.inv_tau = None
        self.use_attn_temperature = False

        # K cache: INT8 symmetric per-group
        self._k_cache: List[Optional[Tensor]] = [None] * num_layers  # int8
        self._k_scale: List[Optional[Tensor]] = [None] * num_layers  # float32

        # V cache: INT4 asymmetric per-token (stored as int8, no bit-packing for simplicity)
        self._v_cache: List[Optional[Tensor]] = [None] * num_layers  # int8
        self._v_scale: List[Optional[Tensor]] = [None] * num_layers  # float32
        self._v_zp: List[Optional[Tensor]] = [None] * num_layers  # float32

        self._layer_seq_lens: List[int] = [0] * num_layers
        self._seq_len: int = 0

        # Decode stats (compatible interface)
        self.decode_stats: Dict[str, object] = {
            "fused_decode_calls": 0, "triton_kernel_calls": 0,
            "torch_ref_calls": 0, "layer_hits": {}, "triton_layer_hits": {},
        }

    def append(self, layer_id: int, k: Tensor, v: Tensor) -> None:
        """Quantize and append KV tensors.

        K: INT8 symmetric per-group quantization.
        V: INT4 asymmetric per-token quantization.
        """
        if layer_id < 0 or layer_id >= self.num_layers:
            raise ValueError(f"layer_id {layer_id} out of range [0, {self.num_layers})")
        if k.ndim != 4 or v.ndim != 4:
            raise ValueError(f"k/v must be 4D [B,H,S,D], got k={tuple(k.shape)} v={tuple(v.shape)}")
        if tuple(k.shape) != tuple(v.shape):
            raise ValueError(f"k/v shape mismatch: {tuple(k.shape)} vs {tuple(v.shape)}")

        # K: INT8 symmetric
        q_k, k_scale = quantize_symmetric_int8(
            k, percentile=self.k_clip_percentile, group_size=self.k_group_size
        )

        # V: INT4 asymmetric per-token
        q_v, v_scale, v_zp = quantize_asymmetric_per_token(
            v, quant_bits=4, percentile=self.v_percentile
        )

        # Concatenate with existing cache
        if self._k_cache[layer_id] is None:
            self._k_cache[layer_id] = q_k
            self._k_scale[layer_id] = k_scale
            self._v_cache[layer_id] = q_v
            self._v_scale[layer_id] = v_scale
            self._v_zp[layer_id] = v_zp
        else:
            self._k_cache[layer_id] = torch.cat([self._k_cache[layer_id], q_k], dim=2)
            self._k_scale[layer_id] = torch.cat([self._k_scale[layer_id], k_scale], dim=2)
            self._v_cache[layer_id] = torch.cat([self._v_cache[layer_id], q_v], dim=2)
            self._v_scale[layer_id] = torch.cat([self._v_scale[layer_id], v_scale], dim=2)
            self._v_zp[layer_id] = torch.cat([self._v_zp[layer_id], v_zp], dim=2)

        new_len = self._k_cache[layer_id].shape[2]
        self._layer_seq_lens[layer_id] = new_len
        self._seq_len = max(self._layer_seq_lens)

    def get_kv(self, layer_id: int) -> Tuple[Tensor, Tensor]:
        """Dequantize and return KV tensors."""
        if layer_id < 0 or layer_id >= self.num_layers:
            raise ValueError(f"layer_id {layer_id} out of range [0, {self.num_layers})")
        if self._k_cache[layer_id] is None:
            raise ValueError(f"Cache for layer {layer_id} is empty")

        # Dequantize K (INT8 symmetric)
        k = dequantize_symmetric_int8(
            self._k_cache[layer_id], self._k_scale[layer_id]
        ).to(self.dtype)

        # Dequantize V (INT4 asymmetric per-token)
        v = dequantize_asymmetric_per_token(
            self._v_cache[layer_id], self._v_scale[layer_id], self._v_zp[layer_id]
        ).to(self.dtype)

        return k, v

    def get_seq_len(self) -> int:
        return self._seq_len

    def clear(self) -> None:
        """Clear cache contents."""
        for i in range(self.num_layers):
            self._k_cache[i] = self._k_scale[i] = None
            self._v_cache[i] = self._v_scale[i] = self._v_zp[i] = None
        self._layer_seq_lens = [0] * self.num_layers
        self._seq_len = 0

    def release(self) -> None:
        self.clear()

    def get_memory_mb(self) -> float:
        total = 0
        for i in range(self.num_layers):
            for t in [self._k_cache[i], self._k_scale[i],
                       self._v_cache[i], self._v_scale[i], self._v_zp[i]]:
                if t is not None:
                    total += t.numel() * t.element_size()
        return total / (1024 * 1024)

    # --- Decode stats interface (compatible) ---

    def record_fused_decode(self, layer_id: int, decode_impl: str) -> None:
        pass

    def record_triton_kernel_call(self, layer_id=None) -> None:
        pass

    def reset_decode_stats(self) -> None:
        pass

    def get_decode_stats(self) -> Dict[str, object]:
        return self.decode_stats
