#!/usr/bin/env python3
"""
Asymmetric quantization utilities for KIVI-style KV Cache.

KIVI uses asymmetric quantization with per-channel K scales and per-token V scales.
Key difference from symmetric: uses zero_point to shift the quantization range.

Formula:
    q = clamp(round((x - zero_point) / scale), qmin, qmax)
    x_hat = q * scale + zero_point

For INT8: [qmin, qmax] = [-128, 127]
For INT4: [qmin, qmax] = [-8, 7]
"""

from typing import Tuple

import torch
from torch import Tensor

from src.quant._common import _check_quantize_input


def quantize_asymmetric(
    tensor: Tensor,
    axis: int,
    quant_bits: int = 8,
    percentile: float = 100.0,
) -> Tuple[Tensor, Tensor, Tensor]:
    """
    Asymmetric quantization along a specified axis.

    Args:
        tensor: Input float tensor
        axis: Axis along which to compute min/max for scale/zero_point.
              For per-channel K: axis=-1 (head_dim), scale shared across tokens.
              For per-token V: axis=-1 (head_dim), scale per token.
        quant_bits: 8 or 4
        percentile: Clipping percentile for outlier suppression (100.0 = no clipping)

    Returns:
        quantized: INT8 tensor (always stored as int8, even for 4-bit)
        scale: FP32 scale tensor (computed in float32 for numerical stability;
               callers such as kivi_style_cache may cast to a different dtype
               for storage via .to(scale_dtype))
        zero_point: FP32 zero_point tensor (same dtype convention as scale)
    """
    _check_quantize_input(tensor, "quantize_asymmetric")
    if not tensor.is_floating_point():
        raise ValueError(f"Input tensor must be float, got {tensor.dtype}")
    if quant_bits not in (4, 8):
        raise ValueError(f"quant_bits must be 4 or 8, got {quant_bits}")
    if not (50.0 < percentile <= 100.0):
        raise ValueError(
            f"percentile must be in (50.0, 100.0], got {percentile}. "
            "Values <= 50 invert min/max and produce silent errors."
        )

    if quant_bits == 8:
        qmin, qmax = -128, 127
    else:
        # INT4 asymmetric uses the full signed 4-bit range [-8, 7].
        # Edge cases to be aware of:
        #   - Constant tensors: t_max == t_min -> scale clamped to 1e-5/(qmax-qmin),
        #     all values quantize to the same code. Dequant error is negligible.
        #   - Single-element axis (e.g., seq_len=1 for per-channel K): scale is
        #     well-defined but has no variance across the reduction dim — acceptable.
        #   - Very small magnitude tensors (|max| < 1e-5): scale is clamped, so
        #     the quantized range is tiny. Precision is limited but NaN-free.
        #   - Negative qmin=-8 means pack_int4/unpack_int4 must use offset +8
        #     (not +7) to avoid uint8 overflow; see int4_basic.py.
        qmin, qmax = -8, 7

    axis = int(axis)
    if axis < 0:
        axis += tensor.ndim
    if axis < 0 or axis >= tensor.ndim:
        raise ValueError(f"axis out of range for tensor.ndim={tensor.ndim}: {axis}")

    if tensor.shape[axis] == 0:
        raise ValueError(
            f"Quantization axis {axis} has size 0 in tensor shape {tuple(tensor.shape)}"
        )

    # Compute min/max in float32 for stable scale/zero-point estimation.
    tensor_f = tensor.float()
    if percentile < 100.0:
        quantile_lo = max(0.0, min((100.0 - percentile) / 100.0, 1.0))
        quantile_hi = max(0.0, min(percentile / 100.0, 1.0))
        t_min = torch.quantile(tensor_f, quantile_lo, dim=axis, keepdim=True)
        t_max = torch.quantile(tensor_f, quantile_hi, dim=axis, keepdim=True)
    else:
        t_min = tensor_f.amin(dim=axis, keepdim=True)
        t_max = tensor_f.amax(dim=axis, keepdim=True)

    # Compute scale and zero_point.
    # QNT-034: The range clamp must guarantee that scale itself (after dividing
    # by qmax-qmin) stays above fp16 minimum normal (~6e-8).  If the caller
    # (e.g. kivi_style_cache) later casts scale to fp16 via .to(scale_dtype),
    # values below fp16 tiny underflow to 0 and corrupt dequantization.
    # For INT8 (qmax-qmin=255): 1e-5/255 ~ 3.9e-8 < fp16_tiny -> underflow.
    # We clamp the range to max(1e-5, fp16_tiny * (qmax-qmin)) so that the
    # resulting per-element scale is always >= fp16_tiny.
    _fp16_tiny = torch.finfo(torch.float16).tiny  # ~6.1e-5
    _range_floor = max(1e-5, _fp16_tiny * (qmax - qmin))
    scale = (t_max - t_min).clamp(min=_range_floor) / (qmax - qmin)
    # ENG-047: zero_point is stored as a *float offset* (in the original value
    # domain), NOT as an integer code.  Convention:
    #   zero_point = t_min - qmin * scale
    # so that dequantization is simply: x_hat = q * scale + zero_point.
    #
    # This differs from:
    #   (a) the KIVI paper, which defines zp as an integer zero-point code, and
    #   (b) PyTorch's quantization API (torch.quantize_per_tensor), which also
    #       uses an integer zero-point.
    #
    # We deliberately use a float offset because:
    #   1. It avoids an extra round(zp) step and keeps the forward path simpler.
    #   2. scale and zero_point share the same dtype (FP16), simplifying storage
    #      in KVCacheQuantizedINT8/INT4 (one Tensor each, no mixed int/float).
    #   3. Dequantization reduces to a single FMA: q * scale + zp.
    # The numerical difference vs. integer zp is at most 0.5 * scale per element,
    # which is well within the quantization noise floor.
    zero_point = t_min - qmin * scale

    # Quantize
    quantized = torch.round((tensor_f - zero_point) / scale).clamp(qmin, qmax).to(torch.int8)

    return quantized, scale.squeeze(axis), zero_point.squeeze(axis)


def dequantize_asymmetric(
    quantized: Tensor,
    scale: Tensor,
    zero_point: Tensor,
    axis: int,
) -> Tensor:
    """
    Dequantize asymmetric quantized tensor.

    Args:
        quantized: INT8 tensor
        scale: Scale tensor (one fewer dim along axis vs quantized)
        zero_point: Zero-point tensor (same shape as scale)
        axis: Original quantization axis (for unsqueezing scale/zp)

    Returns:
        Dequantized tensor in scale.dtype

    Note (QNT-035):
        For uninitialized cache slots where quantized==0 (e.g. from torch.empty),
        the output is ``0 * scale + zero_point = zero_point``, which is generally
        nonzero.  Callers must mask or ignore positions beyond the actual sequence
        length; this function does NOT zero-fill unused slots.
    """
    if quantized.dtype != torch.int8:
        raise ValueError(f"quantized must be torch.int8, got {quantized.dtype}")
    if not scale.is_floating_point():
        raise ValueError(f"scale must be floating point, got {scale.dtype}")
    if not zero_point.is_floating_point():
        raise ValueError(f"zero_point must be floating point, got {zero_point.dtype}")
    if scale.shape != zero_point.shape:
        raise ValueError(
            f"scale and zero_point shape mismatch: {tuple(scale.shape)} vs {tuple(zero_point.shape)}"
        )

    axis = int(axis)
    if axis < 0:
        axis += quantized.ndim
    if axis < 0 or axis >= quantized.ndim:
        raise ValueError(f"axis out of range for quantized.ndim={quantized.ndim}: {axis}")

    expected = list(quantized.shape)
    expected.pop(axis)
    if tuple(expected) != tuple(scale.shape):
        raise ValueError(
            f"scale/zero_point shape {tuple(scale.shape)} incompatible with "
            f"quantized shape {tuple(quantized.shape)} and axis={axis}"
        )

    # Unsqueeze scale and zero_point to broadcast correctly.
    s = scale.unsqueeze(axis)
    zp = zero_point.unsqueeze(axis)
    return quantized.to(s.dtype) * s + zp


def quantize_asymmetric_per_channel(
    tensor: Tensor,
    quant_bits: int = 8,
    percentile: float = 100.0,
) -> Tuple[Tensor, Tensor, Tensor]:
    """
    Per-channel asymmetric quantization for K cache (KIVI-style).

    Input shape: [batch, kv_heads, seq_len, head_dim]
    Quantizes along seq_len (axis=2), so each (batch, head, dim_idx) gets one scale.
    This means scale/zp shape: [batch, kv_heads, head_dim].

    In KIVI, K is quantized per-channel: the same scale is shared across all tokens
    for each channel position within a head.

    Args:
        tensor: K tensor [batch, kv_heads, seq_len, head_dim]
        quant_bits: 8 or 4
        percentile: Clipping percentile

    Returns:
        quantized: [batch, kv_heads, seq_len, head_dim] int8
        scale: [batch, kv_heads, head_dim]
        zero_point: [batch, kv_heads, head_dim]
    """
    return quantize_asymmetric(tensor, axis=2, quant_bits=quant_bits, percentile=percentile)


def dequantize_asymmetric_per_channel(
    quantized: Tensor,
    scale: Tensor,
    zero_point: Tensor,
) -> Tensor:
    """
    Dequantize per-channel K cache.

    Args:
        quantized: [batch, kv_heads, seq_len, head_dim] int8
        scale: [batch, kv_heads, head_dim]
        zero_point: [batch, kv_heads, head_dim]

    Returns:
        Dequantized [batch, kv_heads, seq_len, head_dim]
    """
    return dequantize_asymmetric(quantized, scale, zero_point, axis=2)


def quantize_asymmetric_per_token(
    tensor: Tensor,
    quant_bits: int = 8,
    percentile: float = 100.0,
) -> Tuple[Tensor, Tensor, Tensor]:
    """
    Per-token asymmetric quantization for V cache (KIVI-style).

    Input shape: [batch, kv_heads, seq_len, head_dim]
    Quantizes along head_dim (axis=-1), so each (batch, head, token_idx) gets one scale.
    This means scale/zp shape: [batch, kv_heads, seq_len].

    In KIVI, V is quantized per-token: each token has its own scale across all channels.

    Args:
        tensor: V tensor [batch, kv_heads, seq_len, head_dim]
        quant_bits: 8 or 4
        percentile: Clipping percentile

    Returns:
        quantized: [batch, kv_heads, seq_len, head_dim] int8
        scale: [batch, kv_heads, seq_len]
        zero_point: [batch, kv_heads, seq_len]
    """
    return quantize_asymmetric(tensor, axis=-1, quant_bits=quant_bits, percentile=percentile)


def dequantize_asymmetric_per_token(
    quantized: Tensor,
    scale: Tensor,
    zero_point: Tensor,
) -> Tensor:
    """
    Dequantize per-token V cache.

    Args:
        quantized: [batch, kv_heads, seq_len, head_dim] int8
        scale: [batch, kv_heads, seq_len]
        zero_point: [batch, kv_heads, seq_len]

    Returns:
        Dequantized [batch, kv_heads, seq_len, head_dim]
    """
    return dequantize_asymmetric(quantized, scale, zero_point, axis=-1)
