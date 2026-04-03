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
        # KVC-037: self.dtype is the *output* dtype for get_kv() dequantization
        # (cast applied after dequant). It does NOT control internal storage
        # (always int8 for cache, float32 for scales).
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
        # ENG-009 / KVC-066: Scale buffers are always stored in float32 to avoid
        # precision loss.  fp16 has only 10-bit mantissa (~0.1% relative error)
        # and its subnormal range can lose very small scales entirely.  This
        # matches KIVIStyleKVCache._scale_dtype and the project-wide convention
        # "Scale/zero_point always stored as float32".
        self._scale_dtype = torch.float32
        self._seq_len: int = 0
        self.decode_stats: Dict[str, object] = {
            "fused_decode_calls": 0,
            "triton_kernel_calls": 0,
            "triton_decode_calls": 0,  # KVC-044: Initialize to avoid KeyError
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
        scale_dtype: torch.dtype = None,  # ignored; kept for back-compat
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

        # KVC-067: Check all four buffers for consistency; detect partial None
        # state (e.g. after a partial OOM that corrupted only some slots).
        _bufs = [k_buf, v_buf, ks_buf, vs_buf]
        _non_none = sum(b is not None for b in _bufs)
        if _non_none not in (0, 4):
            raise RuntimeError(
                f"Inconsistent buffer state for layer {layer_id}: "
                f"{_non_none}/4 buffers are not None (expected 0 or 4). "
                f"This may indicate a partial OOM during a prior allocation. "
                f"Call release() and retry."
            )

        if _non_none == 4:
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

        if _non_none == 0:
            new_capacity = max(target_len, self._min_capacity)
            if self.max_seq_len is not None:
                new_capacity = min(new_capacity, self.max_seq_len)
                if new_capacity < target_len:
                    raise ValueError(
                        f"target_len {target_len} exceeds capped capacity {new_capacity} for layer {layer_id}"
                    )
            # KVC-036: Wrap initial allocation in try/except so that a partial
            # OOM (e.g. 2 of 4 buffers allocated) does not leave the layer in
            # an inconsistent state with some buffers set and others None.
            try:
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
                    dtype=self._scale_dtype,
                )
                new_vs = torch.empty(
                    (batch, heads, new_capacity, num_groups),
                    device=self.device,
                    dtype=self._scale_dtype,
                )
            except torch.cuda.OutOfMemoryError:
                # Roll back: ensure all four slots stay None so the layer
                # remains in a clean uninitialized state for retry.
                self._k_cache[layer_id] = None
                self._v_cache[layer_id] = None
                self._k_scale[layer_id] = None
                self._v_scale[layer_id] = None
                self._layer_capacity[layer_id] = 0
                raise
            self._k_cache[layer_id] = new_k
            self._v_cache[layer_id] = new_v
            self._k_scale[layer_id] = new_ks
            self._v_scale[layer_id] = new_vs
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
            dtype=self._scale_dtype,
        )
        new_vs = torch.empty(
            (batch, heads, new_capacity, num_groups),
            device=self.device,
            dtype=self._scale_dtype,
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
            "triton_decode_calls": 0,  # KVC-044: Must match __init__
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

        KVC-069: Returns scale in self._scale_dtype (float32) so that all
        scale arithmetic (adaptive max, dynamic comparison) stays in float32
        and both static/dynamic paths have symmetric dtype before storage.
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
        return scale_view.to(self._scale_dtype).clamp(min=1e-5)

    def _compute_dynamic_group_scale(self, tensor: Tensor) -> Tensor:
        """
        Compute per-token group scale from incoming tensor as absmax/127.
        Returns shape [B, H, S, num_groups].

        KVC-020: The division result (~7.87e-8 for small groups) falls into
        the fp16 subnormal range (< 6.1e-5), losing mantissa bits silently.
        We therefore compute in float32 and only cast back at the end.
        """
        batch, heads, seq_len, head_dim = tensor.shape
        if head_dim % self.group_size != 0:
            raise ValueError(
                f"head_dim {head_dim} must be divisible by group_size {self.group_size}"
            )
        num_groups = head_dim // self.group_size
        reshaped = tensor.view(batch, heads, seq_len, num_groups, self.group_size)
        absmax = reshaped.abs().amax(dim=-1)
        # KVC-020: compute in float32 to avoid fp16 subnormal precision loss.
        # KVC-069: return in self._scale_dtype (float32) so that both
        # static and dynamic paths produce symmetric dtype before storage.
        return (absmax.float().clamp(min=1e-5) / 127.0).to(self._scale_dtype)

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

        # KVC-022: Validate k/v shape and ndim (matching KIVI/FP16 behavior).
        if k.ndim != 4:
            raise ValueError(f"k must be 4D [B,H,S,D], got ndim={k.ndim}")
        if v.ndim != 4:
            raise ValueError(f"v must be 4D [B,H,S,D], got ndim={v.ndim}")
        if tuple(k.shape) != tuple(v.shape):
            raise ValueError(f"k/v shape mismatch: k={tuple(k.shape)} vs v={tuple(v.shape)}")

        # KVC-079: Validate device consistency (matching KIVI behavior).
        target_device = torch.device(self.device)
        if k.device.type != target_device.type or v.device.type != target_device.type:
            raise ValueError(
                f"Device mismatch: cache_device={target_device}, k.device={k.device}, v.device={v.device}"
            )

        # KVC-034: Validate static scale layer bounds before indexing.
        if self.static_k_scale is not None and layer_id >= len(self.static_k_scale):
            raise IndexError(
                f"layer_id {layer_id} exceeds calibration layers "
                f"{len(self.static_k_scale)} for static_k_scale"
            )
        if self.static_v_scale is not None and layer_id >= len(self.static_v_scale):
            raise IndexError(
                f"layer_id {layer_id} exceeds calibration layers "
                f"{len(self.static_v_scale)} for static_v_scale"
            )

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

        # Move to storage device; cast scales to float32 (KVC-066).
        q_k = q_k.to(self.device)
        scale_k = scale_k.to(device=self.device, dtype=self._scale_dtype)
        q_v = q_v.to(self.device)
        scale_v = scale_v.to(device=self.device, dtype=self._scale_dtype)

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
        # KVC-023: Validate layer_id bounds with descriptive error.
        if layer_id < 0 or layer_id >= self.num_layers:
            raise ValueError(
                f"layer_id {layer_id} out of range [0, {self.num_layers})"
            )
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
        # KVC-035: These are mutable views into the pre-allocated buffer.
        # All callers (generate_loop non-fused decode path, patch_model
        # CacheWrapperContainer) use them read-only for attention computation.
        # Cloning here would waste memory and VRAM bandwidth on every decode
        # step.  If a future caller needs to mutate the output, it must clone
        # explicitly at the call site.
        q_k = self._k_cache[layer_id][:, :, :seq_len, :]
        scale_k = self._k_scale[layer_id][:, :, :seq_len, :]
        q_v = self._v_cache[layer_id][:, :, :seq_len, :]
        scale_v = self._v_scale[layer_id][:, :, :seq_len, :]

        # Dequantize (scale is fp32, dequant returns fp32)
        k = dequantize_symmetric_int8(q_k, scale_k)
        v = dequantize_symmetric_int8(q_v, scale_v)

        # Cast back to model dtype (fp16) for API compatibility
        return k.to(self.dtype), v.to(self.dtype)

    def get_int8_tensors(self, layer_id: int) -> Tuple[Tensor, Tensor, Tensor, Tensor]:
        """
        Return raw INT8 KV tensors and scales.

        Returns:
            (k_int8, v_int8, k_scale, v_scale)
        """
        # KVC-023: Validate layer_id bounds with descriptive error.
        if layer_id < 0 or layer_id >= self.num_layers:
            raise ValueError(
                f"layer_id {layer_id} out of range [0, {self.num_layers})"
            )
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

    def __repr__(self) -> str:
        """KVC-043: Useful debug summary including seq_len and memory."""
        mem = self.get_memory_mb()
        return (
            f"INT8KVCache(num_layers={self.num_layers}, seq_len={self._seq_len}, "
            f"group_size={self.group_size}, decode_attn_impl={self.decode_attn_impl!r}, "
            f"memory_mb={mem:.2f}, device={self.device!r})"
        )

    def clear(self) -> None:
        """Reset sequence lengths while keeping allocated buffers for reuse.

        KVC-076: Buffers retain their batch/head/head_dim shape from the
        first append(). If the next sequence has a different batch size,
        _ensure_capacity will raise ValueError. Call release() instead
        of clear() when the batch size changes between sequences.
        """
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
        # KVC-040: Release static scale / inv_tau GPU tensors so GC can reclaim.
        self.static_k_scale = None
        self.static_v_scale = None
        self.inv_tau = None

    def get_memory_mb(self) -> float:
        """Get current memory usage in MB including scales."""
        total_bytes = 0
        for i in range(self.num_layers):
            if self._k_cache[i] is not None:
                # KVC-033: Use .element_size() instead of hardcoded 1 byte.
                total_bytes += self._k_cache[i].numel() * self._k_cache[i].element_size()
                total_bytes += self._v_cache[i].numel() * self._v_cache[i].element_size()
                # Scale tensors (usually FP16 or FP32)
                total_bytes += (
                    self._k_scale[i].numel() * self._k_scale[i].element_size()
                )
                total_bytes += (
                    self._v_scale[i].numel() * self._v_scale[i].element_size()
                )
        return total_bytes / (1024 * 1024)

    # ---- KVC-019: HuggingFace past_key_values interop ----

    def to_tuple(self) -> Tuple[Tuple[Tensor, Tensor], ...]:
        """
        Convert cache to HuggingFace past_key_values format.

        Each layer's quantized K/V is dequantized before returning, so the
        output is a tuple of (k_float, v_float) tuples identical to what
        ``get_kv()`` returns per layer.

        Returns:
            Tuple of (k, v) tuples for each layer.

        Raises:
            ValueError: If any layer cache is empty.
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
        clip_percentile: float = 99.9,
        group_size: int = 128,
    ) -> "INT8KVCache":
        """
        Create INT8KVCache from HuggingFace past_key_values format.

        Each (k, v) pair is quantized with the default dynamic-scale path
        (no static scales) and stored.

        Args:
            past_key_values: Tuple of (k, v) tuples from model output.
            device: Device to store tensors on.
            clip_percentile: Clipping percentile for quantization.
            group_size: Group size for quantization.

        Returns:
            INT8KVCache instance with loaded data.
        """
        num_layers = len(past_key_values)
        cache = cls(
            num_layers=num_layers,
            device=device,
            clip_percentile=clip_percentile,
            group_size=group_size,
        )
        for layer_id, (k, v) in enumerate(past_key_values):
            cache.append(layer_id, k.to(device), v.to(device))
        return cache

    def __repr__(self) -> str:
        # KVC-043: Provide a useful summary for debugging.
        return (
            f"INT8KVCache(num_layers={self.num_layers}, "
            f"seq_len={self._seq_len}, "
            f"memory={self.get_memory_mb():.2f}MB)"
        )
