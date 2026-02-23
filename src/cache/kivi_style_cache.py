#!/usr/bin/env python3
"""
KIVI-style KV Cache implementation.

Implements per-channel K quantization + per-token V quantization with asymmetric
scaling, following the KIVI paper (Liu et al., 2024).

Key differences from our INT8KVCache:
- K: per-channel quantization (scale shared across tokens, computed at prefill time)
- V: per-token quantization (each token gets its own scale, computed at append time)
- Asymmetric quantization (has zero-point, our method is symmetric)
- No inv_tau temperature correction
- Uses torch_ref decode (no Triton fused kernel)

Interface is compatible with INT8KVCache: append(), get_kv(), get_seq_len(),
clear(), release(), get_memory_mb().
"""

from typing import Dict, List, Optional, Tuple

import torch
from torch import Tensor

from src.quant.asymmetric_quant import (
    dequantize_asymmetric_per_channel,
    dequantize_asymmetric_per_token,
    quantize_asymmetric_per_channel,
    quantize_asymmetric_per_token,
)
from src.quant.int4_basic import pack_int4, unpack_int4


class KIVIStyleKVCache:
    """
    KIVI-style asymmetric quantization KV Cache.

    K cache: per-channel quantization. During prefill, we compute per-channel
    min/max across all tokens to build a static scale. Decode tokens reuse that
    scale (values that exceed the range are clipped).

    V cache: per-token quantization. Each token independently computes its own
    per-token scale when appended.

    Attributes:
        num_layers: Number of transformer layers
        device: Device to store tensors on
        quant_bits: 8 or 4
        k_percentile: Clipping percentile for K quantization
        v_percentile: Clipping percentile for V quantization
        dtype: Output data type (default: torch.float16)
    """

    def __init__(
        self,
        num_layers: int,
        device: str = "cuda",
        dtype: torch.dtype = torch.float16,
        max_seq_len: Optional[int] = None,
        quant_bits: int = 8,
        k_percentile: float = 100.0,
        v_percentile: float = 100.0,
    ):
        if num_layers <= 0:
            raise ValueError(f"num_layers must be > 0, got {num_layers}")
        if quant_bits not in (4, 8):
            raise ValueError(f"quant_bits must be 4 or 8, got {quant_bits}")

        self.num_layers = num_layers
        self.device = device
        self.dtype = dtype
        self.max_seq_len = int(max_seq_len) if max_seq_len is not None else None
        self.quant_bits = quant_bits
        self.k_percentile = k_percentile
        self.v_percentile = v_percentile
        self.bit_packed = bool(quant_bits == 4)
        # Keep scale/zp in float32 to avoid silent precision truncation.
        self._scale_dtype = torch.float32

        # Used by patch_model.py routing — KIVI always uses torch_ref.
        self.decode_attn_impl = "torch_ref"
        # KIVI does not use temperature correction.
        self.inv_tau = None
        self.use_attn_temperature = False

        self._min_capacity = 256

        # K cache: quantized tokens + per-channel scale/zp (computed at prefill).
        # For quant_bits=4, K/V values are bit-packed as uint8 payloads in int8 tensors.
        self._k_cache: List[Optional[Tensor]] = [None] * num_layers  # int8
        self._k_scale: List[Optional[Tensor]] = [None] * num_layers  # [B, H, D]
        self._k_zp: List[Optional[Tensor]] = [None] * num_layers  # [B, H, D]
        self._k_scale_initialized: List[bool] = [False] * num_layers

        # V cache: quantized tokens + per-token scale/zp
        self._v_cache: List[Optional[Tensor]] = [None] * num_layers  # int8
        self._v_scale: List[Optional[Tensor]] = [None] * num_layers  # [B, H, S]
        self._v_zp: List[Optional[Tensor]] = [None] * num_layers  # [B, H, S]

        self._layer_seq_lens: List[int] = [0] * num_layers
        self._layer_capacity: List[int] = [0] * num_layers
        self._seq_len: int = 0

        # Decode statistics (compatible with INT8KVCache interface)
        self.decode_stats: Dict[str, object] = {
            "fused_decode_calls": 0,
            "triton_kernel_calls": 0,
            "torch_ref_calls": 0,
            "layer_hits": {},
            "triton_layer_hits": {},
        }

    def _ensure_capacity(
        self,
        layer_id: int,
        batch: int,
        heads: int,
        head_dim: int,
        target_len: int,
    ) -> None:
        """Ensure K/V buffers have enough capacity for target_len tokens."""
        if self.max_seq_len is not None and target_len > self.max_seq_len:
            raise ValueError(
                f"target_len {target_len} exceeds max_seq_len {self.max_seq_len} "
                f"for layer {layer_id}"
            )

        capacity = self._layer_capacity[layer_id]
        k_buf = self._k_cache[layer_id]
        v_buf = self._v_cache[layer_id]
        vs_buf = self._v_scale[layer_id]
        vzp_buf = self._v_zp[layer_id]

        # Check shape consistency if buffers exist
        if k_buf is not None:
            if (
                k_buf.shape[0] != batch
                or k_buf.shape[1] != heads
                or k_buf.shape[3] != head_dim
            ):
                raise ValueError(
                    f"Inconsistent shape for layer {layer_id}: "
                    f"existing K={k_buf.shape}, incoming=({batch}, {heads}, *, {head_dim})"
                )
            if (
                v_buf is None
                or vs_buf is None
                or vzp_buf is None
                or v_buf.shape[0] != batch
                or v_buf.shape[1] != heads
                or v_buf.shape[3] != head_dim
                or vs_buf.shape[0] != batch
                or vs_buf.shape[1] != heads
                or vzp_buf.shape[0] != batch
                or vzp_buf.shape[1] != heads
            ):
                raise ValueError(
                    f"Inconsistent V buffers for layer {layer_id}: "
                    f"V={None if v_buf is None else tuple(v_buf.shape)}, "
                    f"V_scale={None if vs_buf is None else tuple(vs_buf.shape)}, "
                    f"V_zp={None if vzp_buf is None else tuple(vzp_buf.shape)}, "
                    f"incoming=({batch}, {heads}, *, {head_dim})"
                )

        # First allocation
        if k_buf is None:
            new_capacity = max(target_len, self._min_capacity)
            if self.max_seq_len is not None:
                new_capacity = min(new_capacity, self.max_seq_len)
            self._k_cache[layer_id] = torch.empty(
                (batch, heads, new_capacity, head_dim), device=self.device, dtype=torch.int8
            )
            self._v_cache[layer_id] = torch.empty(
                (batch, heads, new_capacity, head_dim), device=self.device, dtype=torch.int8
            )
            self._v_scale[layer_id] = torch.empty(
                (batch, heads, new_capacity), device=self.device, dtype=self._scale_dtype
            )
            self._v_zp[layer_id] = torch.empty(
                (batch, heads, new_capacity), device=self.device, dtype=self._scale_dtype
            )
            self._layer_capacity[layer_id] = new_capacity
            return

        if target_len <= capacity:
            return

        # Grow buffers
        new_capacity = max(target_len, capacity * 2)
        if self.max_seq_len is not None:
            new_capacity = min(new_capacity, self.max_seq_len)
        old_len = self._layer_seq_lens[layer_id]

        new_k = torch.empty(
            (batch, heads, new_capacity, head_dim), device=self.device, dtype=torch.int8
        )
        new_v = torch.empty(
            (batch, heads, new_capacity, head_dim), device=self.device, dtype=torch.int8
        )
        new_vs = torch.empty(
            (batch, heads, new_capacity), device=self.device, dtype=self._scale_dtype
        )
        new_vzp = torch.empty(
            (batch, heads, new_capacity), device=self.device, dtype=self._scale_dtype
        )

        if old_len > 0:
            new_k[:, :, :old_len, :] = self._k_cache[layer_id][:, :, :old_len, :]
            new_v[:, :, :old_len, :] = self._v_cache[layer_id][:, :, :old_len, :]
            new_vs[:, :, :old_len] = self._v_scale[layer_id][:, :, :old_len]
            new_vzp[:, :, :old_len] = self._v_zp[layer_id][:, :, :old_len]

        self._k_cache[layer_id] = new_k
        self._v_cache[layer_id] = new_v
        self._v_scale[layer_id] = new_vs
        self._v_zp[layer_id] = new_vzp
        self._layer_capacity[layer_id] = new_capacity

    def append(self, layer_id: int, k: Tensor, v: Tensor) -> None:
        """
        Quantize and append KV tensors to the cache.

        For K: On first append (prefill), compute per-channel scale from all
        incoming tokens. On subsequent appends (decode), reuse the prefill scale.

        For V: Each token is independently quantized per-token.

        Args:
            layer_id: Layer index
            k: Key tensor [batch, kv_heads, new_seq_len, head_dim] float
            v: Value tensor [batch, kv_heads, new_seq_len, head_dim] float
        """
        if layer_id < 0 or layer_id >= self.num_layers:
            raise ValueError(f"layer_id {layer_id} out of range [0, {self.num_layers})")
        if not isinstance(k, torch.Tensor) or not isinstance(v, torch.Tensor):
            raise TypeError(f"k and v must be tensors, got {type(k)} / {type(v)}")
        if k.ndim != 4 or v.ndim != 4:
            raise ValueError(
                f"k/v must be 4D tensors [B,H,S,D], got k={tuple(k.shape)} v={tuple(v.shape)}"
            )
        if tuple(k.shape) != tuple(v.shape):
            raise ValueError(
                f"k/v shape mismatch: k={tuple(k.shape)} vs v={tuple(v.shape)}"
            )
        if not k.is_floating_point() or not v.is_floating_point():
            raise ValueError(f"k/v must be floating point, got {k.dtype} / {v.dtype}")

        batch, heads, new_seq_len, head_dim = k.shape
        if batch <= 0:
            raise ValueError("batch size must be > 0")
        if heads <= 0 or new_seq_len <= 0 or head_dim <= 0:
            raise ValueError(
                f"Invalid k/v shape values: heads={heads}, new_seq_len={new_seq_len}, head_dim={head_dim}"
            )
        if self.bit_packed and head_dim % 2 != 0:
            raise ValueError(
                f"KIVI INT4 bit packing requires even head_dim, got {head_dim}"
            )

        target_device = torch.device(self.device)
        if k.device.type != target_device.type or v.device.type != target_device.type:
            raise ValueError(
                f"Device mismatch: cache_device={target_device}, k.device={k.device}, v.device={v.device}"
            )
        if (
            target_device.index is not None
            and (k.device.index != target_device.index or v.device.index != target_device.index)
        ):
            raise ValueError(
                f"Device index mismatch: cache_device={target_device}, k.device={k.device}, v.device={v.device}"
            )

        old_len = self._layer_seq_lens[layer_id]
        target_len = old_len + new_seq_len

        # --- K: per-channel quantization ---
        if not self._k_scale_initialized[layer_id]:
            # Prefill: compute per-channel scale from all incoming K tokens.
            q_k_full, k_scale, k_zp = quantize_asymmetric_per_channel(
                k, quant_bits=self.quant_bits, percentile=self.k_percentile
            )
            self._k_scale[layer_id] = k_scale.to(device=target_device, dtype=self._scale_dtype)
            self._k_zp[layer_id] = k_zp.to(device=target_device, dtype=self._scale_dtype)
            self._k_scale_initialized[layer_id] = True
        else:
            # Decode: reuse prefill scale and zero-point.
            k_scale = self._k_scale[layer_id]  # [B, H, D]
            k_zp = self._k_zp[layer_id]  # [B, H, D]
            if k_scale is None or k_zp is None:
                raise RuntimeError(
                    f"K scale/zp not initialized for layer {layer_id} during decode append."
                )
            if self.quant_bits == 8:
                qmin, qmax_val = -128, 127
            else:
                qmin, qmax_val = -8, 7
            s = k_scale.unsqueeze(2)  # [B, H, 1, D]
            zp = k_zp.unsqueeze(2)  # [B, H, 1, D]
            q_k_full = torch.round((k.float() - zp) / s).clamp(qmin, qmax_val).to(torch.int8)

        q_k_store = pack_int4(q_k_full) if self.bit_packed else q_k_full

        # --- V: per-token quantization ---
        q_v_full, v_scale, v_zp = quantize_asymmetric_per_token(
            v, quant_bits=self.quant_bits, percentile=self.v_percentile
        )
        q_v_store = pack_int4(q_v_full) if self.bit_packed else q_v_full

        storage_head_dim = int(q_k_store.shape[-1])
        self._ensure_capacity(layer_id, batch, heads, storage_head_dim, target_len)

        self._k_cache[layer_id][:, :, old_len:target_len, :] = q_k_store.to(target_device)
        self._v_cache[layer_id][:, :, old_len:target_len, :] = q_v_store.to(target_device)
        self._v_scale[layer_id][:, :, old_len:target_len] = v_scale.to(
            device=target_device, dtype=self._scale_dtype
        )
        self._v_zp[layer_id][:, :, old_len:target_len] = v_zp.to(
            device=target_device, dtype=self._scale_dtype
        )

        self._layer_seq_lens[layer_id] = target_len
        self._seq_len = max(self._layer_seq_lens)

    def get_kv(self, layer_id: int) -> Tuple[Tensor, Tensor]:
        """
        Dequantize and return KV tensors.

        Args:
            layer_id: Layer index

        Returns:
            Tuple of (k, v) tensors in self.dtype
        """
        if layer_id < 0 or layer_id >= self.num_layers:
            raise ValueError(f"layer_id {layer_id} out of range [0, {self.num_layers})")
        if self._k_cache[layer_id] is None:
            raise ValueError(f"Cache for layer {layer_id} is empty")

        seq_len = self._layer_seq_lens[layer_id]
        if seq_len <= 0:
            raise ValueError(f"Cache for layer {layer_id} has no tokens")

        # Dequantize K (per-channel).
        q_k = self._k_cache[layer_id][:, :, :seq_len, :]
        if self.bit_packed:
            q_k = unpack_int4(q_k)
        k_scale = self._k_scale[layer_id]
        k_zp = self._k_zp[layer_id]
        if k_scale is None or k_zp is None:
            raise RuntimeError(f"K scale/zp missing for layer {layer_id}")
        k = dequantize_asymmetric_per_channel(q_k, k_scale, k_zp).to(self.dtype)

        # Dequantize V (per-token).
        q_v = self._v_cache[layer_id][:, :, :seq_len, :]
        if self.bit_packed:
            q_v = unpack_int4(q_v)
        v_scale = self._v_scale[layer_id][:, :, :seq_len]
        v_zp = self._v_zp[layer_id][:, :, :seq_len]
        if v_scale is None or v_zp is None:
            raise RuntimeError(f"V scale/zp missing for layer {layer_id}")
        v = dequantize_asymmetric_per_token(q_v, v_scale, v_zp).to(self.dtype)

        return k, v

    def get_seq_len(self) -> int:
        """Return current sequence length."""
        return int(max(self._layer_seq_lens)) if self._layer_seq_lens else 0

    def clear(self) -> None:
        """Clear cache contents but keep buffers allocated."""
        self._layer_seq_lens = [0] * self.num_layers
        self._k_scale_initialized = [False] * self.num_layers
        # Reset K scale/zp so stale values from a previous batch don't persist.
        self._k_scale = [None] * self.num_layers
        self._k_zp = [None] * self.num_layers
        self._seq_len = 0

    def release(self) -> None:
        """Release all buffers and reset state."""
        self._k_cache = [None] * self.num_layers
        self._v_cache = [None] * self.num_layers
        self._k_scale = [None] * self.num_layers
        self._k_zp = [None] * self.num_layers
        self._v_scale = [None] * self.num_layers
        self._v_zp = [None] * self.num_layers
        self._k_scale_initialized = [False] * self.num_layers
        self._layer_seq_lens = [0] * self.num_layers
        self._layer_capacity = [0] * self.num_layers
        self._seq_len = 0

    def get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        total_bytes = 0
        for i in range(self.num_layers):
            if self._k_cache[i] is not None:
                # Quantized payload (int8 storage; INT4 uses bit-packed int8 payload).
                total_bytes += self._k_cache[i].numel() * self._k_cache[i].element_size()
                total_bytes += self._v_cache[i].numel() * self._v_cache[i].element_size()
                # K scale/zp (per-channel, shape [B, H, D]).
                if self._k_scale[i] is not None:
                    total_bytes += self._k_scale[i].numel() * self._k_scale[i].element_size()
                    total_bytes += self._k_zp[i].numel() * self._k_zp[i].element_size()
                # V scale/zp (per-token, shape [B, H, S]).
                if self._v_scale[i] is not None:
                    total_bytes += self._v_scale[i].numel() * self._v_scale[i].element_size()
                    total_bytes += self._v_zp[i].numel() * self._v_zp[i].element_size()
        return total_bytes / (1024 * 1024)

    # --- Decode stats interface (compatible with INT8KVCache) ---

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
        return {
            "fused_decode_calls": int(self.decode_stats.get("fused_decode_calls", 0)),
            "triton_kernel_calls": int(self.decode_stats.get("triton_kernel_calls", 0)),
            "torch_ref_calls": int(self.decode_stats.get("torch_ref_calls", 0)),
            "triton_decode_calls": int(self.decode_stats.get("triton_decode_calls", 0)),
            "layer_hits": dict(self.decode_stats.get("layer_hits", {})),
            "triton_layer_hits": dict(self.decode_stats.get("triton_layer_hits", {})),
        }
