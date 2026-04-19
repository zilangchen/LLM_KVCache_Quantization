#!/usr/bin/env python3
"""
Role-aware allocator-enabled asymmetric KV cache.

This cache keeps the same quantization family as KIVI/RoleAlign:
- K: per-channel asymmetric quantization with prefill-computed scale reused in decode
- V: per-token asymmetric quantization at append time

Unlike RoleAwareAsymKVCache, this backend supports per-layer mixed K/V bit pairs
driven by an allocator policy. It is intended for formal matched-format
allocator-vs-KIVI comparisons and is exposed through a dedicated kv_mode.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
from torch import Tensor

from src.quant.asymmetric_quant import (
    dequantize_asymmetric_per_channel,
    dequantize_asymmetric_per_token,
    quantize_asymmetric_per_channel,
    quantize_asymmetric_per_token,
)
from src.quant.int4_basic import unpack_int4


_SUPPORTED_BITS = frozenset({4, 8, 16})


def load_per_layer_bits_from_policy(
    policy_json: str | Path,
    *,
    project_root: str | Path,
) -> list[tuple[int, int]]:
    """Load and validate per-layer K/V bit pairs from a policy JSON."""
    root = Path(project_root)
    policy_path = Path(policy_json)
    if not policy_path.is_absolute():
        policy_path = root / policy_path
    if not policy_path.exists():
        raise FileNotFoundError(
            f"policy_json={str(policy_json)!r} not found "
            f"(resolved to {str(policy_path)!r})."
        )
    with policy_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    raw = payload.get("per_layer_bits")
    if raw is None:
        raise ValueError(
            f"policy_json {str(policy_path)!r} missing required key 'per_layer_bits'"
        )
    pairs: list[tuple[int, int]] = []
    for idx, entry in enumerate(raw):
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            raise ValueError(
                f"per_layer_bits[{idx}] must be a 2-tuple/list (k_bits, v_bits), got {entry!r}"
            )
        k_bits, v_bits = int(entry[0]), int(entry[1])
        if k_bits not in _SUPPORTED_BITS or v_bits not in _SUPPORTED_BITS:
            raise ValueError(
                f"per_layer_bits[{idx}]=({k_bits},{v_bits}) contains unsupported bits; "
                f"allowed values: {sorted(_SUPPORTED_BITS)}"
            )
        pairs.append((k_bits, v_bits))
    return pairs


class RoleAwareAllocatorKVCache:
    """Allocator-enabled RoleAlign/KIVI-family asymmetric KV cache."""

    def __init__(
        self,
        num_layers: int,
        *,
        per_layer_bits: List[Tuple[int, int]],
        device: str = "cuda",
        dtype: torch.dtype = torch.float16,
        max_seq_len: Optional[int] = None,
        k_percentile: float = 100.0,
        v_percentile: float = 100.0,
        inv_tau: Optional[Tensor] = None,
        use_attn_temperature: bool = False,
        framework: str = "ours_asym_allocator",
        residual_length: int = 0,
    ):
        if num_layers <= 0:
            raise ValueError(f"num_layers must be > 0, got {num_layers}")
        if len(per_layer_bits) != num_layers:
            raise ValueError(
                f"per_layer_bits length {len(per_layer_bits)} must equal num_layers {num_layers}"
            )
        normalized: list[tuple[int, int]] = []
        for idx, entry in enumerate(per_layer_bits):
            if not isinstance(entry, (tuple, list)) or len(entry) != 2:
                raise ValueError(
                    f"per_layer_bits[{idx}] must be a 2-tuple/list (k_bits, v_bits), got {entry!r}"
                )
            k_bits, v_bits = int(entry[0]), int(entry[1])
            if k_bits not in _SUPPORTED_BITS or v_bits not in _SUPPORTED_BITS:
                raise ValueError(
                    f"per_layer_bits[{idx}]=({k_bits},{v_bits}) contains unsupported bits; "
                    f"allowed values: {sorted(_SUPPORTED_BITS)}"
                )
            normalized.append((k_bits, v_bits))
        if int(residual_length) != 0:
            raise ValueError(
                "RoleAwareAllocatorKVCache currently requires residual_length=0"
            )

        self.num_layers = num_layers
        self.device = device
        self.dtype = dtype
        self.max_seq_len = int(max_seq_len) if max_seq_len is not None else None
        self.k_percentile = float(k_percentile)
        self.v_percentile = float(v_percentile)
        self.inv_tau = inv_tau
        self.use_attn_temperature = bool(use_attn_temperature)
        self.framework = framework
        self.ba_calibrated = (self.k_percentile != 100.0) or (self.v_percentile != 100.0)
        self.residual_length = 0
        self.decode_attn_impl = "torch_ref"
        self._scale_dtype = torch.float32
        self._min_capacity = 256
        self._per_layer_bits = normalized

        self._k_cache: List[Optional[Tensor]] = [None] * num_layers
        self._k_scale: List[Optional[Tensor]] = [None] * num_layers
        self._k_zp: List[Optional[Tensor]] = [None] * num_layers
        self._k_scale_initialized: List[bool] = [False] * num_layers
        self._v_cache: List[Optional[Tensor]] = [None] * num_layers
        self._v_scale: List[Optional[Tensor]] = [None] * num_layers
        self._v_zp: List[Optional[Tensor]] = [None] * num_layers
        self._layer_seq_lens: List[int] = [0] * num_layers
        self._layer_capacity: List[int] = [0] * num_layers
        self._head_dims: List[Optional[int]] = [None] * num_layers
        self._seq_len: int = 0
        self.decode_stats: Dict[str, object] = {
            "fused_decode_calls": 0,
            "triton_kernel_calls": 0,
            "torch_ref_calls": 0,
            "layer_hits": {},
            "triton_layer_hits": {},
        }

    def _resolve_bits(self, layer_id: int) -> tuple[int, int]:
        return self._per_layer_bits[layer_id]

    @staticmethod
    def _is_bit_packed(bits: int) -> bool:
        return bits == 4

    @staticmethod
    def _qrange(bits: int) -> tuple[int, int]:
        if bits == 8:
            return -128, 127
        if bits == 4:
            return -8, 7
        raise ValueError(f"qrange requested for unsupported bits={bits}")

    @staticmethod
    def _pack_int4(q_tensor: Tensor) -> Tensor:
        head_dim = int(q_tensor.shape[-1])
        shifted = (q_tensor.to(torch.int16) + 8).to(torch.uint8)
        reshaped = shifted.view(*q_tensor.shape[:-1], head_dim // 2, 2)
        return ((reshaped[..., 0] << 4) | reshaped[..., 1]).to(torch.int8)

    def _storage_dim(self, head_dim: int, bits: int) -> int:
        if bits == 4:
            if head_dim % 2 != 0:
                raise ValueError(
                    f"INT4 bit packing requires even head_dim, got {head_dim}"
                )
            return head_dim // 2
        return head_dim

    def _payload_dtype(self, bits: int) -> torch.dtype:
        return self.dtype if bits == 16 else torch.int8

    def _ensure_capacity(
        self,
        layer_id: int,
        batch: int,
        heads: int,
        head_dim: int,
        target_len: int,
    ) -> None:
        if batch <= 0 or heads <= 0 or head_dim <= 0:
            raise ValueError(
                f"invalid shape values batch={batch} heads={heads} head_dim={head_dim}"
            )
        if self.max_seq_len is not None and target_len > self.max_seq_len:
            raise ValueError(
                f"target_len {target_len} exceeds max_seq_len {self.max_seq_len} for layer {layer_id}"
            )

        k_bits, v_bits = self._resolve_bits(layer_id)
        k_storage_dim = self._storage_dim(head_dim, k_bits)
        v_storage_dim = self._storage_dim(head_dim, v_bits)
        old_capacity = self._layer_capacity[layer_id]
        old_len = self._layer_seq_lens[layer_id]
        old_k = self._k_cache[layer_id]
        old_v = self._v_cache[layer_id]

        if old_k is not None:
            expected_k_shape = (batch, heads, old_capacity, k_storage_dim)
            expected_v_shape = (batch, heads, old_capacity, v_storage_dim)
            if tuple(old_k.shape) != expected_k_shape:
                raise ValueError(
                    f"Inconsistent K cache shape for layer {layer_id}: "
                    f"expected {expected_k_shape}, got {tuple(old_k.shape)}"
                )
            if old_v is None or tuple(old_v.shape) != expected_v_shape:
                raise ValueError(
                    f"Inconsistent V cache shape for layer {layer_id}: "
                    f"expected {expected_v_shape}, got "
                    f"{None if old_v is None else tuple(old_v.shape)}"
                )
            if self._head_dims[layer_id] != head_dim:
                raise ValueError(
                    f"Inconsistent head_dim for layer {layer_id}: "
                    f"existing={self._head_dims[layer_id]} incoming={head_dim}"
                )

        if old_k is not None and target_len <= old_capacity:
            return

        new_capacity = max(target_len, self._min_capacity)
        if old_capacity > 0:
            new_capacity = max(new_capacity, old_capacity * 2)
        if self.max_seq_len is not None:
            new_capacity = min(new_capacity, self.max_seq_len)
            if new_capacity < target_len:
                raise ValueError(
                    f"target_len {target_len} exceeds capped capacity {new_capacity} for layer {layer_id}"
                )

        new_k = torch.empty(
            (batch, heads, new_capacity, k_storage_dim),
            device=self.device,
            dtype=self._payload_dtype(k_bits),
        )
        new_v = torch.empty(
            (batch, heads, new_capacity, v_storage_dim),
            device=self.device,
            dtype=self._payload_dtype(v_bits),
        )

        new_v_scale = None
        new_v_zp = None
        if v_bits != 16:
            new_v_scale = torch.empty(
                (batch, heads, new_capacity),
                device=self.device,
                dtype=self._scale_dtype,
            )
            new_v_zp = torch.empty(
                (batch, heads, new_capacity),
                device=self.device,
                dtype=self._scale_dtype,
            )

        if old_len > 0 and old_k is not None and old_v is not None:
            new_k[:, :, :old_len, :] = old_k[:, :, :old_len, :]
            new_v[:, :, :old_len, :] = old_v[:, :, :old_len, :]
            if new_v_scale is not None and self._v_scale[layer_id] is not None:
                new_v_scale[:, :, :old_len] = self._v_scale[layer_id][:, :, :old_len]
                new_v_zp[:, :, :old_len] = self._v_zp[layer_id][:, :, :old_len]

        self._k_cache[layer_id] = new_k
        self._v_cache[layer_id] = new_v
        self._v_scale[layer_id] = new_v_scale
        self._v_zp[layer_id] = new_v_zp
        self._layer_capacity[layer_id] = new_capacity
        self._head_dims[layer_id] = head_dim

    def _quantize_k_with_existing_scale(
        self,
        k: Tensor,
        *,
        bits: int,
        scale: Tensor,
        zero_point: Tensor,
    ) -> Tensor:
        qmin, qmax = self._qrange(bits)
        unscaled = (k.float() - zero_point.unsqueeze(2)) / scale.unsqueeze(2)
        q_k = torch.round(unscaled).clamp(qmin, qmax).to(torch.int8)
        if bits == 4:
            return self._pack_int4(q_k)
        return q_k

    def append(self, layer_id: int, k: Tensor, v: Tensor) -> None:
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
        if batch <= 0 or heads <= 0 or new_seq_len <= 0 or head_dim <= 0:
            raise ValueError(
                f"Invalid k/v shape values: batch={batch}, heads={heads}, "
                f"new_seq_len={new_seq_len}, head_dim={head_dim}"
            )
        target_device = torch.device(self.device)
        if k.device.type != target_device.type or v.device.type != target_device.type:
            raise ValueError(
                f"Device mismatch: cache_device={target_device}, "
                f"k.device={k.device}, v.device={v.device}"
            )
        if (
            target_device.index is not None
            and (k.device.index != target_device.index or v.device.index != target_device.index)
        ):
            raise ValueError(
                f"Device index mismatch: cache_device={target_device}, "
                f"k.device={k.device}, v.device={v.device}"
            )

        k_bits, v_bits = self._resolve_bits(layer_id)
        old_len = self._layer_seq_lens[layer_id]
        target_len = old_len + new_seq_len

        if k_bits == 16:
            q_k_store = k.to(self.dtype)
            k_scale = None
            k_zp = None
        elif not self._k_scale_initialized[layer_id]:
            q_k_full, k_scale, k_zp = quantize_asymmetric_per_channel(
                k, quant_bits=k_bits, percentile=self.k_percentile
            )
            if k_bits == 4:
                q_k_store = self._pack_int4(q_k_full)
            else:
                q_k_store = q_k_full
            self._k_scale[layer_id] = k_scale.to(device=target_device, dtype=self._scale_dtype)
            self._k_zp[layer_id] = k_zp.to(device=target_device, dtype=self._scale_dtype)
            self._k_scale_initialized[layer_id] = True
        else:
            k_scale = self._k_scale[layer_id]
            k_zp = self._k_zp[layer_id]
            if k_scale is None or k_zp is None:
                raise RuntimeError(
                    f"K scale/zp not initialized for layer {layer_id} during decode append."
                )
            q_k_store = self._quantize_k_with_existing_scale(
                k,
                bits=k_bits,
                scale=k_scale,
                zero_point=k_zp,
            )

        if v_bits == 16:
            q_v_store = v.to(self.dtype)
            v_scale = None
            v_zp = None
        else:
            q_v_full, v_scale, v_zp = quantize_asymmetric_per_token(
                v, quant_bits=v_bits, percentile=self.v_percentile
            )
            if v_bits == 4:
                q_v_store = self._pack_int4(q_v_full)
            else:
                q_v_store = q_v_full

        self._ensure_capacity(layer_id, batch, heads, head_dim, target_len)

        self._k_cache[layer_id][:, :, old_len:target_len, :] = q_k_store.to(self._k_cache[layer_id].dtype)
        self._v_cache[layer_id][:, :, old_len:target_len, :] = q_v_store.to(self._v_cache[layer_id].dtype)
        if v_scale is not None:
            self._v_scale[layer_id][:, :, old_len:target_len] = v_scale.to(
                device=target_device, dtype=self._scale_dtype
            )
            self._v_zp[layer_id][:, :, old_len:target_len] = v_zp.to(
                device=target_device, dtype=self._scale_dtype
            )

        self._layer_seq_lens[layer_id] = target_len
        self._seq_len = max(self._seq_len, target_len)

    def get_kv(self, layer_id: int) -> Tuple[Tensor, Tensor]:
        if layer_id < 0 or layer_id >= self.num_layers:
            raise ValueError(f"layer_id {layer_id} out of range [0, {self.num_layers})")
        seq_len = self._layer_seq_lens[layer_id]
        if seq_len <= 0:
            raise ValueError(f"Cache for layer {layer_id} has no tokens")

        k_bits, v_bits = self._resolve_bits(layer_id)

        q_k = self._k_cache[layer_id][:, :, :seq_len, :]
        if k_bits == 16:
            k = q_k.to(self.dtype)
        else:
            if k_bits == 4:
                q_k = unpack_int4(q_k)
            k_scale = self._k_scale[layer_id]
            k_zp = self._k_zp[layer_id]
            if k_scale is None or k_zp is None:
                raise RuntimeError(f"K scale/zp missing for layer {layer_id}")
            k = dequantize_asymmetric_per_channel(q_k, k_scale, k_zp).to(self.dtype)

        q_v = self._v_cache[layer_id][:, :, :seq_len, :]
        if v_bits == 16:
            v = q_v.to(self.dtype)
        else:
            if v_bits == 4:
                q_v = unpack_int4(q_v)
            v_scale = self._v_scale[layer_id]
            v_zp = self._v_zp[layer_id]
            if v_scale is None or v_zp is None:
                raise RuntimeError(f"V scale/zp missing for layer {layer_id}")
            v = dequantize_asymmetric_per_token(
                q_v,
                v_scale[:, :, :seq_len],
                v_zp[:, :, :seq_len],
            ).to(self.dtype)

        return k, v

    def get_seq_len(self) -> int:
        return self._seq_len

    def clear(self) -> None:
        self._layer_seq_lens = [0] * self.num_layers
        self._k_scale_initialized = [False] * self.num_layers
        self._k_scale = [None] * self.num_layers
        self._k_zp = [None] * self.num_layers
        for layer_id in range(self.num_layers):
            _, v_bits = self._resolve_bits(layer_id)
            if self._v_cache[layer_id] is not None and v_bits != 16:
                batch, heads, capacity, _ = self._v_cache[layer_id].shape
                self._v_scale[layer_id] = torch.zeros(
                    (batch, heads, capacity), device=self.device, dtype=self._scale_dtype
                )
                self._v_zp[layer_id] = torch.zeros(
                    (batch, heads, capacity), device=self.device, dtype=self._scale_dtype
                )
            else:
                self._v_scale[layer_id] = None
                self._v_zp[layer_id] = None
        self._seq_len = 0

    def release(self) -> None:
        self._k_cache = [None] * self.num_layers
        self._k_scale = [None] * self.num_layers
        self._k_zp = [None] * self.num_layers
        self._k_scale_initialized = [False] * self.num_layers
        self._v_cache = [None] * self.num_layers
        self._v_scale = [None] * self.num_layers
        self._v_zp = [None] * self.num_layers
        self._layer_seq_lens = [0] * self.num_layers
        self._layer_capacity = [0] * self.num_layers
        self._head_dims = [None] * self.num_layers
        self._seq_len = 0

    def get_memory_mb(self) -> float:
        total_bytes = 0
        for layer_id in range(self.num_layers):
            if self._k_cache[layer_id] is not None:
                total_bytes += self._k_cache[layer_id].numel() * self._k_cache[layer_id].element_size()
            if self._v_cache[layer_id] is not None:
                total_bytes += self._v_cache[layer_id].numel() * self._v_cache[layer_id].element_size()
            if self._k_scale[layer_id] is not None:
                total_bytes += self._k_scale[layer_id].numel() * self._k_scale[layer_id].element_size()
                total_bytes += self._k_zp[layer_id].numel() * self._k_zp[layer_id].element_size()
            if self._v_scale[layer_id] is not None:
                total_bytes += self._v_scale[layer_id].numel() * self._v_scale[layer_id].element_size()
                total_bytes += self._v_zp[layer_id].numel() * self._v_zp[layer_id].element_size()
        return total_bytes / (1024 * 1024)

    def to_tuple(self) -> Tuple[Tuple[Tensor, Tensor], ...]:
        result = []
        for layer_id in range(self.num_layers):
            if self._layer_seq_lens[layer_id] <= 0:
                raise ValueError(f"Layer {layer_id} cache is empty")
            result.append(self.get_kv(layer_id))
        return tuple(result)

    def _bump_counter(self, key: str, delta: int = 1) -> None:
        self.decode_stats[key] = int(self.decode_stats.get(key, 0)) + int(delta)

    def record_fused_decode(self, layer_id: int, decode_impl: str) -> None:
        self._bump_counter("fused_decode_calls", 1)
        if decode_impl == "torch_ref":
            self._bump_counter("torch_ref_calls", 1)
        else:
            self._bump_counter("triton_kernel_calls", 1)
        layer_hits = self.decode_stats.setdefault("layer_hits", {})
        layer_hits[layer_id] = int(layer_hits.get(layer_id, 0)) + 1
