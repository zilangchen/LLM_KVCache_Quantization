#!/usr/bin/env python3
"""
INT8 KV Cache implementation.

This module provides an INT8 quantized KV cache that reduces memory usage
by storing K/V tensors in int8 format with associated scales.
"""

import logging
import warnings
from typing import Dict, List, Optional, Tuple

import torch
from torch import Tensor

logger = logging.getLogger(__name__)

# ENG-040: Threshold for warning on excessive clipping in static-scale quantization.
# If more than this fraction of values are clipped to [-127, 127], emit a warning.
_CLIP_WARN_THRESHOLD = 0.05  # 5%

from src.quant.int8_basic import (
    dequantize_symmetric_int8,
    quantize_symmetric_int8,
    quantize_symmetric_int8_with_scale,
)


class INT8KVCache:
    """
    INT8 KV Cache for LLM inference.

    Stores key-value tensors in INT8 format, performing quantization
    on append and dequantization on retrieval.

    Attributes:
        num_layers: Number of transformer layers
        device: Device to store tensors on
        clip_percentile: Clipping percentile for quantization
        group_size: Group size for quantization
        dtype: Output data type (default: torch.float16)
    """

    def __init__(
        self,
        num_layers: int,
        device: str = "cuda",
        clip_percentile: float = 99.9,
        group_size: int = 128,
        dtype: torch.dtype = torch.float16,
        max_seq_len: Optional[int] = None,
        decode_attn_impl: str = "triton_fused",
        static_k_scale: Optional[Tensor] = None,
        static_v_scale: Optional[Tensor] = None,
        inv_tau: Optional[Tensor] = None,
        use_attn_temperature: bool = True,
        adaptive_static_scales: bool = False,
        adaptive_static_margin: float = 1.0,
        adaptive_static_k: bool = True,
        adaptive_static_v: bool = True,
    ):
        if num_layers <= 0:
            raise ValueError(f"num_layers must be > 0, got {num_layers}")
        if adaptive_static_margin <= 0:
            raise ValueError(
                f"adaptive_static_margin must be > 0, got {adaptive_static_margin}"
            )

        self.num_layers = num_layers
        self.device = device
        self.clip_percentile = clip_percentile
        self.group_size = group_size
        self.dtype = dtype
        self.max_seq_len = int(max_seq_len) if max_seq_len is not None else None
        if self.max_seq_len is not None and self.max_seq_len <= 0:
            raise ValueError(f"max_seq_len must be > 0, got {self.max_seq_len}")
        self._min_capacity = 256
        # Used by patch_model.py to route q_len==1 decode attention.
        # "triton_fused" is the fast mainline path; "torch_ref" is for correctness/ablation.
        self.decode_attn_impl = decode_attn_impl
        self.static_k_scale = static_k_scale
        self.static_v_scale = static_v_scale
        self.inv_tau = inv_tau
        self.use_attn_temperature = use_attn_temperature
        self.adaptive_static_scales = adaptive_static_scales
        self.adaptive_static_margin = adaptive_static_margin
        self.adaptive_static_k = adaptive_static_k
        self.adaptive_static_v = adaptive_static_v

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

    def _expand_static_scale_for_tensor(self, scale: Tensor, tensor: Tensor) -> Tensor:
        """
        Expand static scale to [B, H, S, num_groups] for the incoming tensor.
        """
        batch, heads, seq_len, head_dim = tensor.shape
        if head_dim % self.group_size != 0:
            raise ValueError(
                f"head_dim {head_dim} must be divisible by group_size {self.group_size}"
            )
        num_groups = head_dim // self.group_size

        if scale.ndim == 2:
            # [H, G]
            scale_view = scale[None, :, None, :]
        elif scale.ndim == 4:
            # [B, H, S, G]
            scale_view = scale
        elif scale.ndim == 5 and scale.shape[-1] == 1:
            # [B, H, S, G, 1]
            scale_view = scale.squeeze(-1)
        else:
            raise ValueError(f"Unsupported static scale shape: {tuple(scale.shape)}")

        scale_view = scale_view.expand(batch, heads, seq_len, num_groups)
        return scale_view.to(tensor.dtype).clamp(min=1e-5)

    def _compute_dynamic_group_scale(self, tensor: Tensor) -> Tensor:
        """
        Compute per-token group scale from incoming tensor as absmax/127.
        Returns shape [B, H, S, num_groups].
        """
        batch, heads, seq_len, head_dim = tensor.shape
        if head_dim % self.group_size != 0:
            raise ValueError(
                f"head_dim {head_dim} must be divisible by group_size {self.group_size}"
            )
        num_groups = head_dim // self.group_size
        reshaped = tensor.view(batch, heads, seq_len, num_groups, self.group_size)
        absmax = reshaped.abs().amax(dim=-1)
        return (absmax.clamp(min=1e-5) / 127.0).to(tensor.dtype)

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

        # Quantize incoming K and V
        # Note: We quantize the new token(s) before appending
        # This assumes independent quantization per token step for baseline
        if self.static_k_scale is not None:
            scale_k = self.static_k_scale[layer_id].to(k.device)
            if self.adaptive_static_scales and self.adaptive_static_k:
                scale_k = self._expand_static_scale_for_tensor(scale_k, k)
                dynamic_k_scale = self._compute_dynamic_group_scale(k)
                scale_k = torch.maximum(
                    scale_k * float(self.adaptive_static_margin), dynamic_k_scale
                )
            q_k, scale_k = quantize_symmetric_int8_with_scale(
                k, scale_k, self.group_size
            )
            # ENG-040: Detect excessive clipping in static-scale K quantization.
            # quantize_symmetric_int8_with_scale silently clips to [-127, 127].
            # If many values are clipped, the static scale is too small for the
            # incoming data, causing silent accuracy degradation.
            _total_k = q_k.numel()
            if _total_k > 0:
                _clipped_k = int(((q_k == 127) | (q_k == -127)).sum().item())
                _clip_ratio_k = _clipped_k / _total_k
                if _clip_ratio_k > _CLIP_WARN_THRESHOLD:
                    warnings.warn(
                        f"ENG-040: Static K scale overflow at layer {layer_id}: "
                        f"{_clip_ratio_k:.1%} of values clipped to [-127, 127] "
                        f"(threshold={_CLIP_WARN_THRESHOLD:.0%}). "
                        f"The static scale may be too small for this input. "
                        f"Consider re-calibrating or enabling adaptive_static_scales.",
                        RuntimeWarning,
                    )
        else:
            q_k, scale_k = quantize_symmetric_int8(
                k, self.clip_percentile, self.group_size
            )

        if self.static_v_scale is not None:
            scale_v = self.static_v_scale[layer_id].to(v.device)
            if self.adaptive_static_scales and self.adaptive_static_v:
                scale_v = self._expand_static_scale_for_tensor(scale_v, v)
                dynamic_v_scale = self._compute_dynamic_group_scale(v)
                scale_v = torch.maximum(
                    scale_v * float(self.adaptive_static_margin), dynamic_v_scale
                )
            q_v, scale_v = quantize_symmetric_int8_with_scale(
                v, scale_v, self.group_size
            )
            # ENG-040: Detect excessive clipping in static-scale V quantization.
            _total_v = q_v.numel()
            if _total_v > 0:
                _clipped_v = int(((q_v == 127) | (q_v == -127)).sum().item())
                _clip_ratio_v = _clipped_v / _total_v
                if _clip_ratio_v > _CLIP_WARN_THRESHOLD:
                    warnings.warn(
                        f"ENG-040: Static V scale overflow at layer {layer_id}: "
                        f"{_clip_ratio_v:.1%} of values clipped to [-127, 127] "
                        f"(threshold={_CLIP_WARN_THRESHOLD:.0%}). "
                        f"The static scale may be too small for this input. "
                        f"Consider re-calibrating or enabling adaptive_static_scales.",
                        RuntimeWarning,
                    )
        else:
            q_v, scale_v = quantize_symmetric_int8(
                v, self.clip_percentile, self.group_size
            )

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

        # ENG-032: _seq_len is only updated on layer_id==0 for performance.
        # generate_loop always appends layers in order 0..N-1, so layer 0 is
        # always the first to be updated each step.  _layer_seq_lens[layer_id]
        # tracks per-layer lengths for correctness; _seq_len is a fast-path
        # shortcut used by get_seq_len() for the common sequential case.
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
        # KVC-018 / ENG-055: warn on zero-length get_kv, distinguishing between
        # the clear() state (buffers allocated, seq_len reset to 0) and the
        # fully-released state (buffers are None, already handled above).
        # After clear(), seq_len==0 but _k_cache is still allocated. Telling
        # the user to "Call release()" is misleading when they may have called
        # clear() intentionally (e.g. to reuse buffers for a new sequence).
        # Instead, inform them that get_kv() returns an empty slice and that
        # release() is only needed if they want to free the buffer memory.
        if seq_len == 0 and self._k_cache[layer_id] is not None:
            logger.warning(
                "get_kv(layer_id=%d) returning zero-length tensors. "
                "The cache was cleared (clear() resets seq_len to 0 but keeps "
                "pre-allocated buffers for reuse). If you intended to append new "
                "tokens, call append() first. Call release() only if you want to "
                "free the underlying buffer memory.",
                layer_id,
            )
        q_k = self._k_cache[layer_id][:, :, :seq_len, :]
        scale_k = self._k_scale[layer_id][:, :, :seq_len, :]
        q_v = self._v_cache[layer_id][:, :, :seq_len, :]
        scale_v = self._v_scale[layer_id][:, :, :seq_len, :]

        # Dequantize
        k = dequantize_symmetric_int8(q_k, scale_k)
        v = dequantize_symmetric_int8(q_v, scale_v)

        return k, v

    def get_int8_tensors(self, layer_id: int) -> Tuple[Tensor, Tensor, Tensor, Tensor]:
        """
        Return raw INT8 KV tensors and scales.
        
        Returns:
            (k_int8, v_int8, k_scale, v_scale)
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
                # INT8 tensors
                total_bytes += self._k_cache[i].numel() * 1  # 1 byte
                total_bytes += self._v_cache[i].numel() * 1
                # Scale tensors (usually FP16 or FP32)
                total_bytes += (
                    self._k_scale[i].numel() * self._k_scale[i].element_size()
                )
                total_bytes += (
                    self._v_scale[i].numel() * self._v_scale[i].element_size()
                )
        return total_bytes / (1024 * 1024)
