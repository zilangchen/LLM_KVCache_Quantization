#!/usr/bin/env python3
"""
INT4 KV Cache implementation.

This module provides an INT4 quantized KV cache for more aggressive compression.
By default it uses 4-bit packing (2x INT4 values per byte) to achieve real
memory savings. Dequantization unpacks back to FP16 for attention.
"""

from typing import Dict, List, Optional, Tuple

import torch
from torch import Tensor

from src.quant.int4_basic import (
    dequantize_symmetric_int4,
    quantize_symmetric_int4,
    pack_int4,
    unpack_int4,
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
        max_seq_len: Optional[int] = None,
        bit_packed: bool = True,
        decode_attn_impl: str = "triton_fused",
    ):
        if num_layers <= 0:
            raise ValueError(f"num_layers must be > 0, got {num_layers}")

        self.num_layers = num_layers
        self.device = device
        self.clip_percentile = clip_percentile
        self.group_size = group_size
        self.dtype = dtype
        self.bit_packed = bool(bit_packed)
        self.decode_attn_impl = decode_attn_impl
        self.max_seq_len = int(max_seq_len) if max_seq_len is not None else None
        if self.max_seq_len is not None and self.max_seq_len <= 0:
            raise ValueError(f"max_seq_len must be > 0, got {self.max_seq_len}")
        self._min_capacity = 256

        # Storage tensors are preallocated by capacity and written by slices.
        # Actual valid length is tracked per layer in _layer_seq_lens.
        self._k_cache: List[Optional[Tensor]] = [None] * num_layers
        self._v_cache: List[Optional[Tensor]] = [None] * num_layers
        self._k_scale: List[Optional[Tensor]] = [None] * num_layers
        self._v_scale: List[Optional[Tensor]] = [None] * num_layers
        self._layer_seq_lens: List[int] = [0] * num_layers
        self._layer_capacity: List[int] = [0] * num_layers
        self._seq_len: int = 0
        self.decode_stats: Dict[str, object] = {
            "fused_decode_calls": 0,
            "triton_kernel_calls": 0,
            "torch_ref_calls": 0,
            "layer_hits": {},
            "triton_layer_hits": {},
        }

    def _bump_counter(self, key: str, delta: int = 1) -> None:
        self.decode_stats[key] = int(self.decode_stats.get(key, 0)) + int(delta)

    def record_fused_decode(self, layer_id: int, decode_impl: str) -> None:
        self._bump_counter("fused_decode_calls", 1)
        if decode_impl == "triton_fused":
            self._bump_counter("triton_decode_calls", 1)
        elif decode_impl == "torch_ref":
            self._bump_counter("torch_ref_calls", 1)

        layer_hits = self.decode_stats.setdefault("layer_hits", {})
        key = str(layer_id)
        layer_hits[key] = int(layer_hits.get(key, 0)) + 1

    def record_triton_kernel_call(self, layer_id: Optional[int] = None) -> None:
        self._bump_counter("triton_kernel_calls", 1)
        if layer_id is None:
            return
        layer_hits = self.decode_stats.setdefault("triton_layer_hits", {})
        key = str(layer_id)
        layer_hits[key] = int(layer_hits.get(key, 0)) + 1

    def reset_decode_stats(self) -> None:
        self.decode_stats = {
            "fused_decode_calls": 0,
            "triton_kernel_calls": 0,
            "torch_ref_calls": 0,
            "layer_hits": {},
            "triton_layer_hits": {},
        }

    def get_decode_stats(self) -> Dict[str, object]:
        # Return a detached copy for logging/assertion.
        return {
            "fused_decode_calls": int(self.decode_stats.get("fused_decode_calls", 0)),
            "triton_kernel_calls": int(self.decode_stats.get("triton_kernel_calls", 0)),
            "torch_ref_calls": int(self.decode_stats.get("torch_ref_calls", 0)),
            "triton_decode_calls": int(self.decode_stats.get("triton_decode_calls", 0)),
            "layer_hits": dict(self.decode_stats.get("layer_hits", {})),
            "triton_layer_hits": dict(self.decode_stats.get("triton_layer_hits", {})),
        }

    def _ensure_capacity(
        self,
        layer_id: int,
        batch: int,
        heads: int,
        head_dim: int,
        num_groups: int,
        target_len: int,
        scale_dtype: torch.dtype,
    ) -> None:
        if self.max_seq_len is not None and target_len > self.max_seq_len:
            raise ValueError(
                f"target_len {target_len} exceeds max_seq_len {self.max_seq_len} for layer {layer_id}"
            )
        capacity = self._layer_capacity[layer_id]
        k_buf = self._k_cache[layer_id]
        v_buf = self._v_cache[layer_id]
        ks_buf = self._k_scale[layer_id]
        vs_buf = self._v_scale[layer_id]

        if (
            k_buf is not None
            and v_buf is not None
            and ks_buf is not None
            and vs_buf is not None
        ):
            if (
                k_buf.shape[0] != batch
                or k_buf.shape[1] != heads
                or k_buf.shape[3] != head_dim
                or ks_buf.shape[3] != num_groups
            ):
                raise ValueError(
                    "Inconsistent KV shape for layer "
                    f"{layer_id}: existing K={k_buf.shape}, K_scale={ks_buf.shape}, "
                    f"incoming=({batch}, {heads}, *, {head_dim}) with groups={num_groups}"
                )

        if (
            k_buf is None
            or v_buf is None
            or ks_buf is None
            or vs_buf is None
        ):
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
                dtype=torch.int8,
            )
            self._v_cache[layer_id] = torch.empty(
                (batch, heads, new_capacity, head_dim),
                device=self.device,
                dtype=torch.int8,
            )
            self._k_scale[layer_id] = torch.empty(
                (batch, heads, new_capacity, num_groups),
                device=self.device,
                dtype=scale_dtype,
            )
            self._v_scale[layer_id] = torch.empty(
                (batch, heads, new_capacity, num_groups),
                device=self.device,
                dtype=scale_dtype,
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
            dtype=torch.int8,
        )
        new_v = torch.empty(
            (batch, heads, new_capacity, head_dim),
            device=self.device,
            dtype=torch.int8,
        )
        new_ks = torch.empty(
            (batch, heads, new_capacity, num_groups),
            device=self.device,
            dtype=ks_buf.dtype,
        )
        new_vs = torch.empty(
            (batch, heads, new_capacity, num_groups),
            device=self.device,
            dtype=vs_buf.dtype,
        )

        if old_len > 0:
            new_k[:, :, :old_len, :] = k_buf[:, :, :old_len, :]
            new_v[:, :, :old_len, :] = v_buf[:, :, :old_len, :]
            new_ks[:, :, :old_len, :] = ks_buf[:, :, :old_len, :]
            new_vs[:, :, :old_len, :] = vs_buf[:, :, :old_len, :]

        self._k_cache[layer_id] = new_k
        self._v_cache[layer_id] = new_v
        self._k_scale[layer_id] = new_ks
        self._v_scale[layer_id] = new_vs
        self._layer_capacity[layer_id] = new_capacity

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

        if self.bit_packed:
            if q_k.shape[-1] % 2 != 0:
                raise ValueError(
                    f"INT4 bit packing requires even head_dim, got {q_k.shape[-1]}"
                )
            q_k = pack_int4(q_k)
            q_v = pack_int4(q_v)

        # Move to storage device
        q_k = q_k.to(self.device)
        scale_k = scale_k.to(self.device)
        q_v = q_v.to(self.device)
        scale_v = scale_v.to(self.device)

        new_seq_len = q_k.shape[2]
        batch, heads, _, head_dim = q_k.shape
        num_groups = scale_k.shape[-1]
        old_len = self._layer_seq_lens[layer_id]
        target_len = old_len + new_seq_len

        self._ensure_capacity(
            layer_id,
            batch=batch,
            heads=heads,
            head_dim=head_dim,
            num_groups=num_groups,
            target_len=target_len,
            scale_dtype=scale_k.dtype,
        )

        self._k_cache[layer_id][:, :, old_len:target_len, :] = q_k
        self._v_cache[layer_id][:, :, old_len:target_len, :] = q_v
        self._k_scale[layer_id][:, :, old_len:target_len, :] = scale_k
        self._v_scale[layer_id][:, :, old_len:target_len, :] = scale_v
        self._layer_seq_lens[layer_id] = target_len

        if layer_id == 0:
            self._seq_len = target_len

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

        seq_len = self._layer_seq_lens[layer_id]
        q_k = self._k_cache[layer_id][:, :, :seq_len, :]
        scale_k = self._k_scale[layer_id][:, :, :seq_len, :]
        q_v = self._v_cache[layer_id][:, :, :seq_len, :]
        scale_v = self._v_scale[layer_id][:, :, :seq_len, :]

        if self.bit_packed:
            q_k = unpack_int4(q_k)
            q_v = unpack_int4(q_v)

        # Dequantize
        k = dequantize_symmetric_int4(q_k, scale_k)
        v = dequantize_symmetric_int4(q_v, scale_v)

        return k, v

    def get_int4_tensors(self, layer_id: int) -> Tuple[Tensor, Tensor, Tensor, Tensor]:
        """
        Return raw INT4 KV tensors and scales.

        Note: if bit_packed=True, k_int4/v_int4 are packed bytes (2x INT4 per byte).
        
        Returns:
            (k_int4, v_int4, k_scale, v_scale)
        """
        if self._k_cache[layer_id] is None:
            raise ValueError(f"Cache for layer {layer_id} is empty")
        seq_len = self._layer_seq_lens[layer_id]
        return (
            self._k_cache[layer_id][:, :, :seq_len, :],
            self._v_cache[layer_id][:, :, :seq_len, :],
            self._k_scale[layer_id][:, :, :seq_len, :],
            self._v_scale[layer_id][:, :, :seq_len, :],
        )

    def get_seq_len(self) -> int:
        return self._seq_len

    def clear(self) -> None:
        self._layer_seq_lens = [0] * self.num_layers
        self._seq_len = 0

    def release(self) -> None:
        self._k_cache = [None] * self.num_layers
        self._v_cache = [None] * self.num_layers
        self._k_scale = [None] * self.num_layers
        self._v_scale = [None] * self.num_layers
        self._layer_seq_lens = [0] * self.num_layers
        self._layer_capacity = [0] * self.num_layers
        self._seq_len = 0

    def get_memory_mb(self) -> float:
        """Get current memory usage in MB including scales."""
        total_bytes = 0
        for i in range(self.num_layers):
            if self._k_cache[i] is not None:
                total_bytes += self._k_cache[i].numel() * self._k_cache[i].element_size()
                total_bytes += self._v_cache[i].numel() * self._v_cache[i].element_size()
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
