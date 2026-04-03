#!/usr/bin/env python3
"""
INT4 KV Cache implementation.

This module provides an INT4 quantized KV cache for more aggressive compression.
By default it uses 4-bit packing (2x INT4 values per byte) to achieve real
memory savings. Dequantization unpacks back to FP16 for attention.
"""

import logging
import warnings
from typing import Dict, List, Optional, Tuple

import torch
from torch import Tensor

logger = logging.getLogger(__name__)

# KVC-021: Threshold for warning on excessive clipping in static-scale quantization.
# If more than this fraction of values are clipped to [-7, 7], emit a warning.
_CLIP_WARN_THRESHOLD = 0.05  # 5%

from src.quant.int4_basic import (
    dequantize_symmetric_int4,
    quantize_symmetric_int4,
    quantize_symmetric_int4_with_scale,
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
        static_k_scale: Optional[Tensor] = None,
        static_v_scale: Optional[Tensor] = None,
        inv_tau: Optional[Tensor] = None,
        use_attn_temperature: bool = True,
        adaptive_static_scales: bool = False,
        adaptive_static_margin: float = 1.0,
        adaptive_static_k: bool = True,
        adaptive_static_v: bool = True,
        outlier_rescue_ratio: float = 0.0,
        mixed_rescue: bool = False,
    ):
        if num_layers <= 0:
            raise ValueError(f"num_layers must be > 0, got {num_layers}")
        if adaptive_static_margin <= 0:
            raise ValueError(
                f"adaptive_static_margin must be > 0, got {adaptive_static_margin}"
            )
        if outlier_rescue_ratio < 0.0 or outlier_rescue_ratio > 1.0:
            raise ValueError(
                f"outlier_rescue_ratio must be in [0, 1], got {outlier_rescue_ratio}"
            )

        self.num_layers = num_layers
        self.device = device
        self.clip_percentile = clip_percentile
        self.group_size = group_size
        self.dtype = dtype
        self.bit_packed = bool(bit_packed)
        self.decode_attn_impl = decode_attn_impl
        self.static_k_scale = static_k_scale
        self.static_v_scale = static_v_scale
        self.inv_tau = inv_tau
        self.use_attn_temperature = use_attn_temperature
        self.adaptive_static_scales = adaptive_static_scales
        self.adaptive_static_margin = adaptive_static_margin
        self.adaptive_static_k = adaptive_static_k
        self.adaptive_static_v = adaptive_static_v
        self.outlier_rescue_ratio = float(outlier_rescue_ratio)
        self.mixed_rescue = bool(mixed_rescue)
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
            "triton_decode_calls": 0,  # KVC-072/KVC-054: Initialize to avoid KeyError
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
            "triton_decode_calls": 0,  # KVC-072/KVC-054: Must match __init__
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
        scale_dtype: torch.dtype = torch.float32,
    ) -> None:
        # KVC-066: Force scale buffers to float32 for INT4 precision chain.
        # fp16 scales lose precision at the INT4 quantization boundary.
        scale_dtype = torch.float32
        # KVC-050 / KVC-068 / KVC-070: Dimension semantics when bit_packed=True.
        #
        # When bit_packed=True, two INT4 values are packed into one byte, so:
        #   head_dim = D // 2   (packed, from q_k.shape[-1] after pack_int4)
        #   num_groups = D / group_size  (logical, from scale_k.shape[-1])
        #
        # These use *different dimension bases* by design:
        #   - K/V buffer dim-3 stores the packed representation (D//2)
        #   - Scale buffer dim-3 stores group counts based on the original D
        #
        # Each is internally self-consistent: every append() call passes the
        # same (head_dim, num_groups) pair derived from the *same* quantized
        # output, so shape checks in _ensure_capacity always compare like
        # with like.  The mixed bases are intentional, not a bug.
        if self.max_seq_len is not None and target_len > self.max_seq_len:
            raise ValueError(
                f"target_len {target_len} exceeds max_seq_len {self.max_seq_len} for layer {layer_id}"
            )
        capacity = self._layer_capacity[layer_id]
        k_buf = self._k_cache[layer_id]
        v_buf = self._v_cache[layer_id]
        ks_buf = self._k_scale[layer_id]
        vs_buf = self._v_scale[layer_id]

        # KVC-055: Check all four buffers for consistency; detect partial None
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
            # KVC-055: Wrap initial allocation in try/except so that a partial
            # OOM does not leave the layer in an inconsistent state.
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
                    dtype=scale_dtype,
                )
                new_vs = torch.empty(
                    (batch, heads, new_capacity, num_groups),
                    device=self.device,
                    dtype=scale_dtype,
                )
            except torch.cuda.OutOfMemoryError:
                # Roll back: ensure all four slots stay None.
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
        # KVC-065: use torch.float32 for scale buffers instead of inheriting
        # from old buffer dtype, which could be wrong after prior allocations.
        new_ks = torch.empty(
            (batch, heads, new_capacity, num_groups),
            device=self.device,
            dtype=torch.float32,
        )
        new_vs = torch.empty(
            (batch, heads, new_capacity, num_groups),
            device=self.device,
            dtype=torch.float32,
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
        # ENG-066: Keep scales in float32 for INT4 precision chain.
        return scale_view.to(torch.float32).clamp(min=1e-5)

    def _compute_dynamic_group_scale(self, tensor: Tensor) -> Tensor:
        """
        Compute per-token dynamic INT4 group scale as absmax/7.
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
        # KVC-020/ENG-066: compute in float32 to avoid fp16 subnormal risk.
        return absmax.float().clamp(min=1e-5) / 7.0

    def _apply_outlier_rescue(self, tensor: Tensor, scale: Tensor) -> Tensor:
        """
        Outlier-rescue scale adjustment for INT4:
        for the top-ratio largest group absmax values, switch to dynamic scale.

        KVC-051: Interaction with mixed_rescue.
        When both mixed_rescue=True and outlier_rescue_ratio>0, the call order
        in append() is: (1) mixed_rescue applies torch.maximum(static, dynamic)
        globally, then (2) outlier_rescue selectively replaces the top-ratio
        groups with max(current_scale, dynamic).  Since mixed_rescue already
        set scale >= dynamic everywhere, outlier_rescue becomes a no-op in
        practice (max(X, dynamic) == X when X >= dynamic).  This is harmless
        but the combined configuration is redundant — users should use one or
        the other.  mixed_rescue is the more conservative option (affects all
        groups); outlier_rescue is the selective option (affects top-ratio only).
        """
        ratio = float(self.outlier_rescue_ratio)
        if ratio <= 0.0:
            return scale

        dynamic_scale = self._compute_dynamic_group_scale(tensor)
        if ratio >= 1.0:
            return torch.maximum(scale, dynamic_scale)

        # Compute global threshold across [B, H, S, G].
        threshold = torch.quantile(
            dynamic_scale.float().reshape(-1),
            max(0.0, min(1.0, 1.0 - ratio)),
        ).to(dynamic_scale.dtype)
        rescue_mask = dynamic_scale >= threshold
        return torch.where(rescue_mask, torch.maximum(scale, dynamic_scale), scale)

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

        # KVC-031: Warn when outlier_rescue_ratio / mixed_rescue have no effect
        # because static scales are not provided.  Check each side independently:
        # if K has a static scale but V does not (or vice-versa), the rescue
        # parameters silently do nothing for the missing side.
        _missing_sides = []
        if self.static_k_scale is None:
            _missing_sides.append("K")
        if self.static_v_scale is None:
            _missing_sides.append("V")
        if _missing_sides:
            _side_str = " and ".join(_missing_sides)
            if self.outlier_rescue_ratio > 0:
                warnings.warn(
                    f"KVC-031: outlier_rescue_ratio={self.outlier_rescue_ratio} has no "
                    f"effect on {_side_str} at layer {layer_id} because no static "
                    f"{_side_str} scale is provided. Outlier rescue only adjusts "
                    f"static scales; dynamic quantization already adapts per-token.",
                    RuntimeWarning,
                )
            if self.mixed_rescue:
                warnings.warn(
                    f"KVC-031: mixed_rescue=True has no effect on {_side_str} at layer "
                    f"{layer_id} because no static {_side_str} scale is provided. "
                    f"Mixed rescue only adjusts static scales; dynamic quantization "
                    f"already adapts per-token.",
                    RuntimeWarning,
                )

        # Quantize incoming K and V to INT4
        if self.static_k_scale is not None:
            scale_k = self.static_k_scale[layer_id].to(k.device)
            scale_k = self._expand_static_scale_for_tensor(scale_k, k)
            if self.adaptive_static_scales and self.adaptive_static_k:
                dynamic_k_scale = self._compute_dynamic_group_scale(k)
                scale_k = torch.maximum(
                    scale_k * float(self.adaptive_static_margin), dynamic_k_scale
                )
            # mixed_rescue: make K more conservative to preserve attention logits.
            if self.mixed_rescue:
                scale_k = torch.maximum(scale_k, self._compute_dynamic_group_scale(k))
            scale_k = self._apply_outlier_rescue(k, scale_k)
            q_k, scale_k = quantize_symmetric_int4_with_scale(
                k, scale_k, self.group_size
            )
            # KVC-021: Detect excessive clipping in static-scale K quantization.
            # Check in the float domain *before* quantization: values whose
            # absolute magnitude exceeds 7*scale will be clipped to +/-7.
            # Using post-quantization `abs(q)==7` is unreliable because 7
            # is itself a valid non-clipped value.
            _total_k = k.numel()
            if _total_k > 0:
                _k_reshaped = k.view(
                    k.shape[0], k.shape[1], k.shape[2], -1, self.group_size
                )
                _k_bound = (scale_k.unsqueeze(-1) * 7.0).expand_as(_k_reshaped)
                _clip_ratio_k = (
                    (_k_reshaped.abs() > _k_bound).float().mean().item()
                )
                if _clip_ratio_k > _CLIP_WARN_THRESHOLD:
                    warnings.warn(
                        f"KVC-021: Static K scale overflow at layer {layer_id}: "
                        f"{_clip_ratio_k:.1%} of values exceed scale capacity "
                        f"(threshold={_CLIP_WARN_THRESHOLD:.0%}). "
                        f"The static scale may be too small for this input. "
                        f"Consider re-calibrating or enabling adaptive_static_scales.",
                        RuntimeWarning,
                    )
        else:
            q_k, scale_k = quantize_symmetric_int4(
                k, self.clip_percentile, self.group_size
            )

        if self.static_v_scale is not None:
            scale_v = self.static_v_scale[layer_id].to(v.device)
            scale_v = self._expand_static_scale_for_tensor(scale_v, v)
            if self.adaptive_static_scales and self.adaptive_static_v:
                dynamic_v_scale = self._compute_dynamic_group_scale(v)
                scale_v = torch.maximum(
                    scale_v * float(self.adaptive_static_margin), dynamic_v_scale
                )
            # KVC-032: Apply mixed_rescue to V as well (not just K).
            if self.mixed_rescue:
                scale_v = torch.maximum(scale_v, self._compute_dynamic_group_scale(v))
            scale_v = self._apply_outlier_rescue(v, scale_v)
            q_v, scale_v = quantize_symmetric_int4_with_scale(
                v, scale_v, self.group_size
            )
            # KVC-021: Detect excessive clipping in static-scale V quantization.
            # Float-domain check: values exceeding 7*scale will be clipped.
            _total_v = v.numel()
            if _total_v > 0:
                _v_reshaped = v.view(
                    v.shape[0], v.shape[1], v.shape[2], -1, self.group_size
                )
                _v_bound = (scale_v.unsqueeze(-1) * 7.0).expand_as(_v_reshaped)
                _clip_ratio_v = (
                    (_v_reshaped.abs() > _v_bound).float().mean().item()
                )
                if _clip_ratio_v > _CLIP_WARN_THRESHOLD:
                    warnings.warn(
                        f"KVC-021: Static V scale overflow at layer {layer_id}: "
                        f"{_clip_ratio_v:.1%} of values exceed scale capacity "
                        f"(threshold={_CLIP_WARN_THRESHOLD:.0%}). "
                        f"The static scale may be too small for this input. "
                        f"Consider re-calibrating or enabling adaptive_static_scales.",
                        RuntimeWarning,
                    )
        else:
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

        # Move to storage device.
        # KVC-066: Ensure scales are float32 regardless of quantizer output dtype.
        q_k = q_k.to(self.device)
        scale_k = scale_k.to(device=self.device, dtype=torch.float32)
        q_v = q_v.to(self.device)
        scale_v = scale_v.to(device=self.device, dtype=torch.float32)

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

        # KVC-070: Verify dimension invariant — when bit_packed, head_dim is
        # D//2 (packed) while num_groups is based on the original D.  Both are
        # derived from the quantizer output within this same append() call, so
        # they are always self-consistent.  The assertion catches any future
        # refactor that accidentally decouples them.
        if self.bit_packed:
            assert self._k_cache[layer_id].shape[3] == head_dim, (
                f"BUG: packed K buffer dim mismatch: "
                f"buffer={self._k_cache[layer_id].shape[3]}, head_dim={head_dim}"
            )
            assert self._k_scale[layer_id].shape[3] == num_groups, (
                f"BUG: K scale group dim mismatch: "
                f"buffer={self._k_scale[layer_id].shape[3]}, num_groups={num_groups}"
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
        # KVC-018: warn on zero-length get_kv after clear()
        if seq_len == 0 and self._k_cache[layer_id] is not None:
            logger.warning(
                "get_kv(layer_id=%d) returning zero-length tensors; "
                "buffers are still allocated (likely after clear()). "
                "Call release() to free memory.",
                layer_id,
            )
        q_k = self._k_cache[layer_id][:, :, :seq_len, :]
        scale_k = self._k_scale[layer_id][:, :, :seq_len, :]
        q_v = self._v_cache[layer_id][:, :, :seq_len, :]
        scale_v = self._v_scale[layer_id][:, :, :seq_len, :]

        if self.bit_packed:
            q_k = unpack_int4(q_k)
            q_v = unpack_int4(q_v)

        # KVC-053: Defensive check for corrupted INT4 data after unpacking.
        # Valid symmetric INT4 values are in [-7, 7]. The value -8 is
        # representable in 4-bit signed but outside the symmetric range,
        # indicating possible bit-packing corruption or data integrity issues.
        if (q_k < -7).any() or (q_k > 7).any():
            warnings.warn(
                f"KVC-053: Unpacked INT4 K values out of [-7, 7] range at layer "
                f"{layer_id}. This may indicate bit-packing corruption.",
                RuntimeWarning,
            )
        if (q_v < -7).any() or (q_v > 7).any():
            warnings.warn(
                f"KVC-053: Unpacked INT4 V values out of [-7, 7] range at layer "
                f"{layer_id}. This may indicate bit-packing corruption.",
                RuntimeWarning,
            )

        # Dequantize
        k = dequantize_symmetric_int4(q_k, scale_k)
        v = dequantize_symmetric_int4(q_v, scale_v)
        # ENG-066: Ensure output dtype matches cache dtype (fp16) regardless of internal
        # scale precision. Without this, float32 scales would propagate to attention math.
        return k.to(self.dtype), v.to(self.dtype)

    def get_int4_tensors(self, layer_id: int) -> Tuple[Tensor, Tensor, Tensor, Tensor]:
        """
        Return raw INT4 KV tensors and scales.

        Note: if bit_packed=True, k_int4/v_int4 are packed bytes (2x INT4 per byte).
        
        Returns:
            (k_int4, v_int4, k_scale, v_scale)
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

    def get_memory_mb(self) -> float:
        """Get current memory usage in MB including scales."""
        total_bytes = 0
        for i in range(self.num_layers):
            if self._k_cache[i] is not None:
                total_bytes += self._k_cache[i].numel() * self._k_cache[i].element_size()
                total_bytes += self._v_cache[i].numel() * self._v_cache[i].element_size()
                # Scale tensors (FP32, per KVC-066)
                total_bytes += (
                    self._k_scale[i].numel() * self._k_scale[i].element_size()
                )
                total_bytes += (
                    self._v_scale[i].numel() * self._v_scale[i].element_size()
                )
        return total_bytes / (1024 * 1024)

    # ---- KVC-019 / KVC-078: HuggingFace past_key_values interop ----

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
            k, v = self.get_kv(i)  # Dequantize
            result.append((k, v))
        return tuple(result)

    @classmethod
    def from_tuple(
        cls,
        past_key_values: Tuple[Tuple[Tensor, Tensor], ...],
        device: str = "cuda",
        clip_percentile: float = 99.9,
        group_size: int = 32,
        bit_packed: bool = True,
    ) -> "INT4KVCache":
        """
        Create INT4KVCache from HuggingFace past_key_values format.

        Each (k, v) pair is quantized with the default dynamic-scale path
        (no static scales) and stored.

        Args:
            past_key_values: Tuple of (k, v) tuples from model output.
            device: Device to store tensors on.
            clip_percentile: Clipping percentile for quantization.
            group_size: Group size for quantization.
            bit_packed: Whether to use INT4 bit packing.

        Returns:
            INT4KVCache instance with loaded data.
        """
        num_layers = len(past_key_values)
        cache = cls(
            num_layers=num_layers,
            device=device,
            clip_percentile=clip_percentile,
            group_size=group_size,
            bit_packed=bit_packed,
        )
        for layer_id, (k, v) in enumerate(past_key_values):
            cache.append(layer_id, k.to(device), v.to(device))
        return cache
