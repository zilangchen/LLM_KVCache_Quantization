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

import warnings
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
        inv_tau: Optional[torch.Tensor] = None,
        use_attn_temperature: bool = False,
        residual_length: int = 0,
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
        # INT4 mode uses bit-packing (2 values per byte), which requires even
        # head_dim.  head_dim is unknown at __init__ time (it comes from the
        # first append() call), so the actual check is enforced in append().
        self.bit_packed = bool(quant_bits == 4)
        # ENG-009: V scale/zp (and K scale/zp) buffers are always allocated and
        # stored in float32 (_scale_dtype = torch.float32). This is intentional:
        # - Per-token V scales can be very small (e.g. < 1e-4 for near-zero tokens),
        #   which would underflow or lose precision in fp16 (min normal ~6e-8, but
        #   fp16 has only 10-bit mantissa giving ~0.1% relative error).
        # - Per-channel K scales are computed once at prefill and reused for all
        #   decode tokens; fp32 avoids cumulative rounding across long sequences.
        # Any code path that reads _v_scale / _v_zp / _k_scale / _k_zp must
        # preserve float32 precision (do NOT cast to fp16 before the dequant
        # multiply). The dequantized output is then cast to self.dtype (fp16 by
        # default) at the end of get_kv(), which is the intended precision point.
        self._scale_dtype = torch.float32

        # Used by patch_model.py routing — KIVI uses torch_ref by default.
        # For int4_kivi_aligned mode, inv_tau enables Q pre-scaling in decode path.
        self.decode_attn_impl = "torch_ref"
        self.inv_tau = inv_tau
        self.use_attn_temperature = use_attn_temperature

        self._min_capacity = 256

        # --- Residual buffer (KIVI paper §3.3) ---
        # Keep the most recent `residual_length` tokens in FP16 (unquantized).
        # When the buffer is full, the oldest tokens are quantized and moved to
        # the main INT4/INT8 cache. This preserves precision for recent tokens
        # that contribute most to current attention.
        self.residual_length = max(0, int(residual_length))
        # Lazily allocated on first append (need to know batch/heads/head_dim).
        self._fp16_k_recent: List[Optional[Tensor]] = [None] * num_layers
        self._fp16_v_recent: List[Optional[Tensor]] = [None] * num_layers
        self._residual_lens: List[int] = [0] * num_layers

        # K cache: quantized tokens + per-channel scale/zp (computed at prefill).
        # For quant_bits=4, K/V values are bit-packed as uint8 payloads in int8 tensors.
        # KVC-057: Dimension relationship when bit_packed=True:
        #   _k_cache[i] has shape [B, H, S, D//2] — two INT4 values packed per byte
        #   _k_scale[i] has shape [B, H, D]        — one scale per logical channel
        #   _k_zp[i]    has shape [B, H, D]        — one zero-point per logical channel
        # This is intentional: scale/zp operate on the *logical* head_dim (D), while
        # the cache stores the *packed* representation (D//2).  unpack_int4() restores
        # the logical dimension before dequantization in get_kv().  The same applies
        # to V cache vs V scale/zp (V scale is per-token so shape is [B, H, S]).
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

        # KVC-OOR: Out-of-range diagnostic interval. Default 0 = disabled in hot
        # path to avoid GPU→CPU sync (.item()) that costs ~0.5ms per layer per step.
        # Set KV_OOR_CHECK_INTERVAL=100 to enable periodic checking.
        import os
        self._oor_check_interval = int(os.environ.get("KV_OOR_CHECK_INTERVAL", "0"))
        self._oor_step_counter = 0

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
        if batch <= 0:
            raise ValueError(f"batch must be > 0, got {batch}")
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
                # KVC-017: overflow guard (first allocation path).
                if new_capacity < target_len:
                    raise ValueError(
                        f"target_len {target_len} exceeds capped capacity {new_capacity} for layer {layer_id}"
                    )
            # ENG-009: Assert scale dtype contract before allocation to catch any
            # accidental reassignment of self._scale_dtype elsewhere in the class.
            assert self._scale_dtype == torch.float32, (
                f"KIVIStyleKVCache._scale_dtype must be torch.float32, got {self._scale_dtype}. "
                "Changing this may cause precision loss in V scale/zp buffers."
            )
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

        # KVC-075: Grow V buffers only.  K scale/zp are per-channel (shape
        # [B, H, D]) and are computed once at prefill time, so they do NOT
        # need reallocation when the sequence grows.  Only K/V quantized
        # payload buffers and V scale/zp (which are per-token, shape
        # [B, H, capacity]) need to grow.  Do NOT add K scale/zp realloc
        # here — doing so would overwrite the prefill-computed per-channel
        # scales and silently corrupt K dequantization.
        #
        # KVC-073: Defensive assertion — K scale should already be initialized
        # by the time we reach realloc (which only happens on decode tokens
        # after prefill has set per-channel scales).
        assert self._k_scale_initialized[layer_id], (
            f"BUG: realloc triggered for layer {layer_id} but K scale is not "
            f"initialized. Per-channel K scale must be set during prefill "
            f"before any decode-time buffer growth."
        )
        new_capacity = max(target_len, capacity * 2)
        if self.max_seq_len is not None:
            new_capacity = min(new_capacity, self.max_seq_len)
            # KVC-017: overflow guard — if max_seq_len caps new_capacity below
            # target_len, raise a clear error instead of proceeding to an
            # out-of-bounds slice assignment (which causes a CUDA-level crash).
            if new_capacity < target_len:
                raise ValueError(
                    f"target_len {target_len} exceeds capped capacity {new_capacity} for layer {layer_id}"
                )
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

        # --- Residual buffer logic (KIVI paper §3.3) ---
        # During decode (new_seq_len == 1), if residual_length > 0, the new token
        # goes into the FP16 buffer first. When the buffer is full, the oldest
        # token is quantized and flushed to the main cache.
        # During prefill (new_seq_len > 1), all tokens are quantized normally
        # (K scale is computed from all prefill tokens), and the last
        # min(residual_length, new_seq_len) tokens are copied to the FP16 buffer.
        # KVC-092: Only route to residual buffer after prefill (K scale initialized).
        # A single-token "prefill" (new_seq_len==1, scale not yet computed) must go
        # through the normal quantization path to establish per-channel K scale.
        if (self.residual_length > 0 and new_seq_len == 1
                and self._k_scale_initialized[layer_id]):
            # Decode path: route to residual buffer
            if self._fp16_k_recent[layer_id] is None:
                # Lazy allocation
                self._fp16_k_recent[layer_id] = torch.zeros(
                    batch, heads, self.residual_length, head_dim,
                    device=target_device, dtype=self.dtype,
                )
                self._fp16_v_recent[layer_id] = torch.zeros(
                    batch, heads, self.residual_length, head_dim,
                    device=target_device, dtype=self.dtype,
                )

            rlen = self._residual_lens[layer_id]
            if rlen < self.residual_length:
                # Buffer not full: just add the token
                self._fp16_k_recent[layer_id][:, :, rlen:rlen+1, :] = k.to(self.dtype)
                self._fp16_v_recent[layer_id][:, :, rlen:rlen+1, :] = v.to(self.dtype)
                self._residual_lens[layer_id] = rlen + 1
                # Update seq_len tracking (total = quantized + residual)
                if layer_id == 0:
                    self._seq_len = self._layer_seq_lens[0] + self._residual_lens[0]
                return
            else:
                # Buffer full: evict oldest token to quantized cache, then shift
                # KVC-090 fix: must clone before shift, otherwise evict_k/v are
                # views into slot 0 which gets overwritten by the in-place shift.
                evict_k = self._fp16_k_recent[layer_id][:, :, 0:1, :].clone()  # [B,H,1,D]
                evict_v = self._fp16_v_recent[layer_id][:, :, 0:1, :].clone()
                # Shift buffer left
                self._fp16_k_recent[layer_id][:, :, :-1, :] = \
                    self._fp16_k_recent[layer_id][:, :, 1:, :].clone()
                self._fp16_v_recent[layer_id][:, :, :-1, :] = \
                    self._fp16_v_recent[layer_id][:, :, 1:, :].clone()
                # New token goes to end of buffer
                self._fp16_k_recent[layer_id][:, :, -1:, :] = k.to(self.dtype)
                self._fp16_v_recent[layer_id][:, :, -1:, :] = v.to(self.dtype)
                # Evicted token needs to be quantized — fall through to normal path
                k = evict_k
                v = evict_v
                new_seq_len = 1
                # target_len stays the same (evicted token goes to quantized cache)

        # --- K: per-channel quantization ---
        if not self._k_scale_initialized[layer_id]:
            # Prefill: compute per-channel scale from all incoming K tokens.
            q_k_full, k_scale, k_zp = quantize_asymmetric_per_channel(
                k, quant_bits=self.quant_bits, percentile=self.k_percentile
            )
            self._k_scale[layer_id] = k_scale.to(device=target_device, dtype=self._scale_dtype)
            self._k_zp[layer_id] = k_zp.to(device=target_device, dtype=self._scale_dtype)
            self._k_scale_initialized[layer_id] = True
            # Prefill: always use PyTorch pack (Triton fused only for decode)
            if self.bit_packed:
                _shifted = (q_k_full.to(torch.int16) + 8).to(torch.uint8)
                _reshaped = _shifted.view(*q_k_full.shape[:-1], head_dim // 2, 2)
                q_k_store = ((_reshaped[..., 0] << 4) | _reshaped[..., 1]).to(torch.int8)
            else:
                q_k_store = q_k_full
        else:
            # Decode: reuse prefill scale and zero-point.
            # KVC-060: The decode path performs manual quantization (round+clamp)
            # rather than calling quantize_asymmetric_per_channel(), because the
            # scale/zp are frozen from prefill.  The math is equivalent:
            #   q = round((x - zp) / scale).clamp(qmin, qmax)
            # The prefill path delegates this to quantize_asymmetric_per_channel
            # which also computes scale/zp from data, whereas decode reuses them.
            # No percentile clipping is applied in decode because the scale is
            # already calibrated — applying it again would be a no-op since the
            # percentile only affects scale *computation*, not the quantize step.
            # ENG-007: KIVI decode path dequant->requant accumulates precision loss; this is inherent to the KIVI design.
            # KVC-074: Assert that the per-channel K scale was actually computed
            # during prefill before we rely on it.  The outer `if/else` already
            # branches on `_k_scale_initialized`, but an explicit assert guards
            # against future refactors that might decouple the flag from the data.
            assert self._k_scale_initialized[layer_id], (
                f"BUG: entered decode branch for layer {layer_id} but "
                f"_k_scale_initialized is False"
            )
            k_scale = self._k_scale[layer_id]  # [B, H, D]
            k_zp = self._k_zp[layer_id]  # [B, H, D]
            if k_scale is None or k_zp is None:
                raise RuntimeError(
                    f"K scale/zp not initialized for layer {layer_id} during decode append."
                )
            expected_shape = (batch, heads, head_dim)
            if tuple(k_scale.shape) != expected_shape or tuple(k_zp.shape) != expected_shape:
                raise ValueError(
                    f"Inconsistent decode K scale/zp shape for layer {layer_id}: "
                    f"expected {expected_shape}, got scale={tuple(k_scale.shape)}, "
                    f"zp={tuple(k_zp.shape)}"
                )
            # KVC-FUSE-TRITON-INPLACE: For INT4 decode on CUDA, use inplace Triton
            # kernels that write directly to cache buffers (zero temp alloc, zero copy).
            _use_triton_inplace = (
                self.bit_packed and new_seq_len == 1 and k.is_cuda
                and self.v_percentile >= 100.0
            )
            if _use_triton_inplace:
                try:
                    from src.kernels.triton_quantize_pack_int4 import (
                        fused_quantize_pack_k_int4_inplace,
                        fused_quantize_pack_v_int4_inplace,
                    )
                    # Must ensure capacity BEFORE inplace write
                    storage_hd = head_dim // 2
                    self._ensure_capacity(layer_id, batch, heads, storage_hd, target_len)
                    # K: quantize+pack directly into cache
                    fused_quantize_pack_k_int4_inplace(
                        k, k_scale, k_zp, self._k_cache[layer_id], old_len
                    )
                    # V: quantize+pack+scale+zp directly into cache
                    fused_quantize_pack_v_int4_inplace(
                        v, self._v_cache[layer_id],
                        self._v_scale[layer_id], self._v_zp[layer_id], old_len
                    )
                    # Update bookkeeping and return early (skip the store block below)
                    self._layer_seq_lens[layer_id] = target_len
                    if layer_id == 0:
                        self._seq_len = max(self._seq_len, target_len)
                    else:
                        self._seq_len = max(self._seq_len, target_len)
                    return
                except Exception:
                    pass  # fall through to non-inplace path

            # Non-inplace Triton or PyTorch fallback
            if self.bit_packed and new_seq_len == 1 and k.is_cuda:
                try:
                    from src.kernels.triton_quantize_pack_int4 import fused_quantize_pack_k_int4
                    q_k_store = fused_quantize_pack_k_int4(k, k_scale, k_zp)
                except Exception:
                    q_k_store = None
                if q_k_store is None:
                    if self.quant_bits == 8:
                        qmin, qmax_val = -128, 127
                    else:
                        qmin, qmax_val = -8, 7
                    s = k_scale.unsqueeze(2)
                    zp = k_zp.unsqueeze(2)
                    _unscaled = (k.float() - zp) / s
                    q_k_full = torch.round(_unscaled).clamp(qmin, qmax_val).to(torch.int8)
                    _shifted = (q_k_full.to(torch.int16) + 8).to(torch.uint8)
                    _reshaped = _shifted.view(*q_k_full.shape[:-1], head_dim // 2, 2)
                    q_k_store = ((_reshaped[..., 0] << 4) | _reshaped[..., 1]).to(torch.int8)
            else:
                if self.quant_bits == 8:
                    qmin, qmax_val = -128, 127
                else:
                    qmin, qmax_val = -8, 7
                s = k_scale.unsqueeze(2)
                zp = k_zp.unsqueeze(2)
                _unscaled = (k.float() - zp) / s
                if self._oor_check_interval > 0 and layer_id == 0:
                    self._oor_step_counter += 1
                if (self._oor_check_interval > 0
                        and self._oor_step_counter % self._oor_check_interval == 0):
                    _out_of_range = ((_unscaled < qmin) | (_unscaled > qmax_val))
                    _oor_ratio = float(_out_of_range.sum().item()) / max(_out_of_range.numel(), 1)
                    if _oor_ratio > 0.05:
                        warnings.warn(
                            f"ENG-041: KIVI decode K clipping at layer {layer_id}: "
                            f"{_oor_ratio:.1%} of values exceed prefill-computed scale range "
                            f"[{qmin}, {qmax_val}]. Decode token magnitudes may have drifted "
                            f"beyond prefill calibration. Attention accuracy may degrade.",
                            RuntimeWarning,
                        )
                q_k_full = torch.round(_unscaled).clamp(qmin, qmax_val).to(torch.int8)
                if self.bit_packed:
                    _shifted = (q_k_full.to(torch.int16) + 8).to(torch.uint8)
                    _reshaped = _shifted.view(*q_k_full.shape[:-1], head_dim // 2, 2)
                    q_k_store = ((_reshaped[..., 0] << 4) | _reshaped[..., 1]).to(torch.int8)
                else:
                    q_k_store = q_k_full

        # --- V: per-token quantization (non-inplace path) ---
        if self.bit_packed and new_seq_len == 1 and v.is_cuda and self.v_percentile >= 100.0:
            try:
                from src.kernels.triton_quantize_pack_int4 import fused_quantize_pack_v_int4_simple
                q_v_store, v_scale, v_zp = fused_quantize_pack_v_int4_simple(v)
            except Exception:
                q_v_store = None
            if q_v_store is None:
                q_v_full, v_scale, v_zp = quantize_asymmetric_per_token(
                    v, quant_bits=self.quant_bits, percentile=self.v_percentile
                )
                _v_shifted = (q_v_full.to(torch.int16) + 8).to(torch.uint8)
                _v_reshaped = _v_shifted.view(*q_v_full.shape[:-1], head_dim // 2, 2)
                q_v_store = ((_v_reshaped[..., 0] << 4) | _v_reshaped[..., 1]).to(torch.int8)
        else:
            q_v_full, v_scale, v_zp = quantize_asymmetric_per_token(
                v, quant_bits=self.quant_bits, percentile=self.v_percentile
            )
            if self.bit_packed:
                _v_shifted = (q_v_full.to(torch.int16) + 8).to(torch.uint8)
                _v_reshaped = _v_shifted.view(*q_v_full.shape[:-1], head_dim // 2, 2)
                q_v_store = ((_v_reshaped[..., 0] << 4) | _v_reshaped[..., 1]).to(torch.int8)
            else:
                q_v_store = q_v_full

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
        # Update global seq_len as max across all layers.  Unlike INT8KVCache
        # (which updates only on layer_id==0 for speed), KIVI takes the max to
        # stay correct even when layers are appended out of order or
        # incrementally.  In normal sequential execution all layers have the
        # same length, so max() == any single layer's length.
        # Include residual buffer tokens in the total sequence length.
        quantized_len = max(self._layer_seq_lens)
        residual_len = max(self._residual_lens) if self.residual_length > 0 else 0
        self._seq_len = quantized_len + residual_len

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
        # KVC-059: Check for None *before* slicing — slicing a None tensor raises
        # TypeError, so a post-slice None check would be dead code.
        if self._v_scale[layer_id] is None or self._v_zp[layer_id] is None:
            raise RuntimeError(f"V scale/zp missing for layer {layer_id}")
        v_scale = self._v_scale[layer_id][:, :, :seq_len]
        v_zp = self._v_zp[layer_id][:, :, :seq_len]
        v = dequantize_asymmetric_per_token(q_v, v_scale, v_zp).to(self.dtype)

        # Append FP16 residual buffer tokens (if any) after quantized tokens.
        rlen = self._residual_lens[layer_id]
        if self.residual_length > 0 and rlen > 0 and self._fp16_k_recent[layer_id] is not None:
            k = torch.cat([k, self._fp16_k_recent[layer_id][:, :, :rlen, :]], dim=2)
            v = torch.cat([v, self._fp16_v_recent[layer_id][:, :, :rlen, :]], dim=2)

        return k, v

    def get_int4_asym_tensors(
        self, layer_id: int
    ) -> Tuple[Tensor, Tensor, Tensor, Tensor, Tensor, Tensor]:
        """
        Return raw packed cache + scale/zp for Triton INT4 asymmetric kernel.

        Returns:
            (k_packed, v_packed, k_scale, k_zp, v_scale, v_zp)
            k_packed: [B, H, S, D//2] int8 (bit-packed)
            v_packed: [B, H, S, D//2] int8
            k_scale:  [B, H, D] float32 per-channel
            k_zp:     [B, H, D] float32 per-channel
            v_scale:  [B, H, S] float32 per-token
            v_zp:     [B, H, S] float32 per-token
        """
        if layer_id < 0 or layer_id >= self.num_layers:
            raise ValueError(f"layer_id {layer_id} out of range [0, {self.num_layers})")
        if self._k_cache[layer_id] is None:
            raise ValueError(f"Cache for layer {layer_id} is empty")
        if not self.bit_packed:
            raise RuntimeError(
                "get_int4_asym_tensors requires bit_packed=True (quant_bits=4)"
            )

        seq_len = self._layer_seq_lens[layer_id]
        k_packed = self._k_cache[layer_id][:, :, :seq_len, :]
        v_packed = self._v_cache[layer_id][:, :, :seq_len, :]
        k_scale = self._k_scale[layer_id]
        k_zp = self._k_zp[layer_id]
        v_scale = self._v_scale[layer_id][:, :, :seq_len]
        v_zp = self._v_zp[layer_id][:, :, :seq_len]

        return k_packed, v_packed, k_scale, k_zp, v_scale, v_zp

    def get_seq_len(self) -> int:
        """Return current total sequence length (quantized + residual).

        KVC-025/KVC-061: Use cached _seq_len (O(1)) instead of O(N) max() over
        _layer_seq_lens.  _seq_len is maintained by append() at layer_id==0
        (same pattern as INT8/INT4 caches).

        KVC-091: When residual_length > 0, the returned value includes both
        quantized tokens and FP16 residual buffer tokens, matching the seq dim
        of tensors returned by get_kv().
        """
        return self._seq_len

    def clear(self) -> None:
        """Clear cache contents but keep buffers allocated.

        Resets seq_lens, K scale/zp (so next prefill recomputes), and
        re-allocates V scale/zp buffers to match the existing V cache capacity.
        This maintains the invariant that _ensure_capacity expects: if _k_cache
        is not None, then _v_cache, _v_scale, and _v_zp must also be not None.
        """
        self._layer_seq_lens = [0] * self.num_layers
        self._k_scale_initialized = [False] * self.num_layers
        # Reset K scale/zp so stale values from a previous batch don't persist.
        self._k_scale = [None] * self.num_layers
        self._k_zp = [None] * self.num_layers
        # KVC-058: Zero-fill V scale/zp buffers instead of leaving them
        # uninitialized.  With torch.empty the buffer contains random values;
        # if a new sequence is shorter than the old one, _ensure_capacity's
        # grow-and-copy path could propagate stale random scale/zp into the
        # new buffer beyond the valid region.  Using torch.zeros eliminates
        # this class of bug at negligible cost (clear() is called once per
        # new sequence, not per token).
        for i in range(self.num_layers):
            if self._v_cache[i] is not None:
                B, H, cap, _ = self._v_cache[i].shape
                self._v_scale[i] = torch.zeros(
                    (B, H, cap), device=self.device, dtype=self._scale_dtype
                )
                self._v_zp[i] = torch.zeros(
                    (B, H, cap), device=self.device, dtype=self._scale_dtype
                )
            else:
                self._v_scale[i] = None
                self._v_zp[i] = None
        # Reset residual buffers
        self._residual_lens = [0] * self.num_layers
        for i in range(self.num_layers):
            if self._fp16_k_recent[i] is not None:
                self._fp16_k_recent[i].zero_()
                self._fp16_v_recent[i].zero_()
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
        self._fp16_k_recent = [None] * self.num_layers
        self._fp16_v_recent = [None] * self.num_layers
        self._residual_lens = [0] * self.num_layers
        self._seq_len = 0

    def get_memory_mb(self) -> float:
        """Get total *allocated* memory in MB (includes unused capacity headroom).

        This counts the full pre-allocated buffer sizes, not just the valid
        (seq_len) portion, because the OS/CUDA allocator reserves the full
        capacity.  Includes K/V quantized payloads and their scale/zp metadata.
        """
        total_bytes = 0
        for i in range(self.num_layers):
            if self._k_cache[i] is not None:
                # Quantized payload (int8 storage; INT4 uses bit-packed int8 payload).
                total_bytes += self._k_cache[i].numel() * self._k_cache[i].element_size()
                total_bytes += self._v_cache[i].numel() * self._v_cache[i].element_size()
                # K scale/zp (per-channel, shape [B, H, D], stored as float32).
                if self._k_scale[i] is not None:
                    total_bytes += self._k_scale[i].numel() * self._k_scale[i].element_size()
                    total_bytes += self._k_zp[i].numel() * self._k_zp[i].element_size()
                # V scale/zp (per-token, shape [B, H, capacity], stored as float32).
                if self._v_scale[i] is not None:
                    total_bytes += self._v_scale[i].numel() * self._v_scale[i].element_size()
                    total_bytes += self._v_zp[i].numel() * self._v_zp[i].element_size()
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
        quant_bits: int = 8,
        k_percentile: float = 100.0,
        v_percentile: float = 100.0,
    ) -> "KIVIStyleKVCache":
        """
        Create KIVIStyleKVCache from HuggingFace past_key_values format.

        Each (k, v) pair is treated as a prefill batch: per-channel K scale
        is computed from the full K sequence, and V is quantized per-token.

        Args:
            past_key_values: Tuple of (k, v) tuples from model output.
            device: Device to store tensors on.
            quant_bits: 4 or 8.
            k_percentile: Clipping percentile for K quantization.
            v_percentile: Clipping percentile for V quantization.

        Returns:
            KIVIStyleKVCache instance with loaded data.
        """
        num_layers = len(past_key_values)
        cache = cls(
            num_layers=num_layers,
            device=device,
            quant_bits=quant_bits,
            k_percentile=k_percentile,
            v_percentile=v_percentile,
        )
        for layer_id, (k, v) in enumerate(past_key_values):
            cache.append(layer_id, k.to(device), v.to(device))
        return cache

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
