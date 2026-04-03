#!/usr/bin/env python3
"""
Basic INT8 quantization implementations.

This module provides symmetric INT8 quantization/dequantization with:
- Percentile clipping for outlier suppression
- Group-wise scaling (group_size dimension)
"""

from typing import Tuple

import torch
from torch import Tensor

from src.quant._common import _check_quantize_input, _normalize_static_scale


def quantize_symmetric_int8(
    tensor: Tensor,
    percentile: float = 99.9,
    group_size: int = 128,
) -> Tuple[Tensor, Tensor]:
    """
    Symmetric INT8 quantization with percentile clipping.

    Formula:
        abs_max = percentile(abs(tensor), p)
        scale = abs_max / 127.0
        q = clamp(round(tensor / scale), -127, 127)

    Args:
        tensor: Input tensor [batch, heads, seq, dim]
        percentile: Clipping percentile (default: 99.9)
        group_size: Group size for scaling. Currently supports:
                    - 128 (when head_dim=128, equivalent to per-head quantization)

    Returns:
        quantized: INT8 tensor [batch, heads, seq, dim]
        scale: Scale tensor [batch, heads, seq, num_groups] where num_groups = head_dim / group_size.
               For per-head quantization (num_groups=1), this is [batch, heads, seq, 1].
    """
    if not tensor.is_floating_point():
        raise ValueError(f"Input tensor must be float, got {tensor.dtype}")
    _check_quantize_input(tensor, "quantize_symmetric_int8")
    if tensor.ndim != 4:  # QNT-029: dynamic path expects [B, H, S, D]
        raise ValueError(f"quantize_symmetric_int8 expects 4D tensor [B,H,S,D], got ndim={tensor.ndim}")

    # For naive implementation, we currently assume per-token or per-head quantization
    # depending on group_size and dimension alignment.

    # Handling group-wise quantization
    head_dim = tensor.shape[-1]
    
    if group_size == -1:
        # Per-token quantization (group_size = head_dim)
        group_size = head_dim

    if head_dim % group_size != 0:
        raise ValueError(f"head_dim {head_dim} must be divisible by group_size {group_size}")

    num_groups = head_dim // group_size
    
    # Reshape to [..., num_groups, group_size] to compute scale per group
    # Original: [B, H, S, D] -> [B, H, S, num_groups, group_size]
    input_shape = tensor.shape
    reshaped = tensor.view(*input_shape[:-1], num_groups, group_size)  # [B, H, S, G, GS]
    
    # Calculate absolute maximum over the last dimension (group_size)
    abs_reshaped = reshaped.abs()
    
    # Precision note: when tensor.dtype is float16, the quantile path already
    # promotes to float32 for stability.  The non-quantile (amax) path keeps
    # the input dtype.  Scale computation and the round/clamp below therefore
    # run in the input dtype.  For float16 inputs this is intentional: the
    # quantization error from float16 arithmetic (~5e-4 relative) is well
    # below the INT8 quantization step size (~1/127 ~= 7.8e-3), so promoting
    # to float32 here would increase memory without meaningful accuracy gain.
    if percentile < 100.0:
        quantile = max(min(percentile / 100.0, 1.0), 0.0)
        abs_max = torch.quantile(
            abs_reshaped.float(), quantile, dim=-1, keepdim=True
        )
    else:
        abs_max = torch.amax(abs_reshaped, dim=-1, keepdim=True)

    # ENG-037: Clamp abs_max BEFORE casting to tensor.dtype to prevent
    # fp16 precision loss from producing exact 0.0 (fp16 has limited
    # subnormal range). If abs_max is very small and cast to fp16 first,
    # it can become 0.0, then clamp(min=1e-5) is too late — the value is
    # already zero and scale=0 causes NaN from round(x/0).
    abs_max = abs_max.clamp(min=1e-5)
    abs_max = abs_max.to(tensor.dtype)

    scale = abs_max / 127.0  # [B, H, S, num_groups, 1]

    # Quantize: [..., num_groups, group_size]
    # Scale broadcasts over group_size dim
    quantized_reshaped = torch.round(reshaped / scale).clamp(-127, 127).to(torch.int8)
    
    # Restore shape: [B, H, S, D]
    quantized = quantized_reshaped.view(*input_shape)
    
    # QNT-048: Scale layout — the trailing singleton is squeezed for cache/kernel
    # compatibility.  [B, H, S, num_groups, 1] -> [B, H, S, num_groups].
    # QNT-031: For fp16 inputs the scale inherits fp16 dtype; the ~0.1% relative
    # error from fp16 arithmetic is well below INT8's step size (~0.78%) so this
    # is acceptable.  See precision note at the top of the quantize function.
    return quantized, scale.squeeze(-1)


def quantize_symmetric_int8_with_scale(
    tensor: Tensor,
    scale: Tensor,
    group_size: int,
) -> Tuple[Tensor, Tensor]:
    """
    Symmetric INT8 quantization using a provided static scale.

    Args:
        tensor: Input tensor [batch, heads, seq, dim]
        scale: Static scale tensor (see _normalize_static_scale)
        group_size: Group size for scaling

    Returns:
        quantized: INT8 tensor [batch, heads, seq, dim]
        scale_expanded: Scale tensor expanded to [batch, heads, seq, num_groups],
            cast to tensor.dtype. QNT-033: If tensor.dtype is bfloat16, the
            returned scale is bfloat16 — Triton kernels that require fp16 scale
            must cast explicitly before calling decode_attn_int8.
    """
    if not tensor.is_floating_point():
        raise ValueError(f"Input tensor must be float, got {tensor.dtype}")
    _check_quantize_input(tensor, "quantize_symmetric_int8_with_scale")

    head_dim = tensor.shape[-1]
    if group_size == -1:
        group_size = head_dim

    if head_dim % group_size != 0:
        raise ValueError(
            f"head_dim {head_dim} must be divisible by group_size {group_size}"
        )

    batch, heads, seq_len, _ = tensor.shape
    num_groups = head_dim // group_size

    reshaped = tensor.view(batch, heads, seq_len, num_groups, group_size)
    # QNT-042: Catch device mismatch early — scale on CPU + tensor on GPU
    # would fail at division time with an unclear error far from root cause.
    if scale.device != tensor.device:
        raise ValueError(
            f"scale device ({scale.device}) != tensor device ({tensor.device}). "
            "Move scale to the same device before quantization."
        )
    scale_expanded = _normalize_static_scale(scale, batch, heads, seq_len, num_groups)
    # QNT-024/QNT-033: Clamp BEFORE dtype cast to prevent fp16 near-zero underflow.
    # This follows the ENG-037 pattern (clamp-then-cast) consistently with the
    # dynamic quantize path above.
    scale_expanded = scale_expanded.clamp(min=1e-5).to(tensor.dtype)

    quantized = torch.round(reshaped / scale_expanded).clamp(-127, 127).to(torch.int8)
    quantized = quantized.view(batch, heads, seq_len, head_dim)

    return quantized, scale_expanded.squeeze(-1)


def dequantize_symmetric_int8(
    quantized: Tensor,
    scale: Tensor,
) -> Tensor:
    """
    Dequantize INT8 tensor.

    Formula:
        tensor = quantized * scale

    The function handles three scale layouts (produced by different quantize paths):

    Path A -- scale.ndim == quantized.ndim + 1:
        scale shape [B, H, S, num_groups, 1] (5-D with trailing singleton).
        Reshape quantized to [B, H, S, G, group_size], multiply, reshape back.

    Path B -- scale.ndim == quantized.ndim, num_groups > 1:
        scale shape [B, H, S, num_groups] (4-D, squeezed from Path A).
        Same reshape logic, but unsqueeze(-1) on scale to broadcast.

    Path B' -- scale.ndim == quantized.ndim, num_groups == 1:
        scale shape [B, H, S, 1] (per-token scalar scale).
        Direct broadcast multiply, no reshape needed.

    Args:
        quantized: INT8 tensor [B, H, S, D]
        scale: Scale tensor (see layout descriptions above)

    Returns:
        Dequantized tensor in scale.dtype
    """
    # QNT-008: Input type validation for defense-in-depth.
    if quantized.dtype != torch.int8:
        raise ValueError(f"quantized must be torch.int8, got {quantized.dtype}")
    if not scale.is_floating_point():
        raise ValueError(f"scale must be floating point, got {scale.dtype}")

    # --- Path A: 5-D scale with trailing singleton ---
    if scale.ndim == quantized.ndim + 1:
        B, H, S, D = quantized.shape
        num_groups = scale.shape[-2]
        # QNT-046: Validate divisibility (Path B has this check; Path A was missing).
        if num_groups <= 0 or D % num_groups != 0:
            raise ValueError(
                f"Invalid scale shape for group-wise dequantization (Path A): "
                f"quantized={tuple(quantized.shape)}, scale={tuple(scale.shape)}"
            )
        group_size = D // num_groups

        q_reshaped = quantized.view(B, H, S, num_groups, group_size)
        decoded_reshaped = q_reshaped.to(scale.dtype) * scale
        return decoded_reshaped.view(B, H, S, D)

    # --- Path B / B': 4-D scale ---
    if scale.ndim == quantized.ndim:
        B, H, S, D = quantized.shape
        num_groups = scale.shape[-1]
        # QNT-036: Validate num_groups and divisibility for ALL sub-paths,
        # including the num_groups==1 fast path (Path B').  Without this
        # check, a scale with shape [B, H, S, 1] but D not divisible by 1
        # (impossible in practice, but D==0 would slip through) or an
        # invalid num_groups would silently produce wrong results.
        if num_groups <= 0 or D % num_groups != 0:
            raise ValueError(
                f"Invalid scale shape for group-wise dequantization: "
                f"quantized={tuple(quantized.shape)}, scale={tuple(scale.shape)}"
            )
        # Path B': per-token scalar scale (num_groups == 1).
        if num_groups == 1:
            return quantized.to(scale.dtype) * scale
        # Path B: group-wise scale.
        group_size = D // num_groups
        q_reshaped = quantized.view(B, H, S, num_groups, group_size)
        decoded_reshaped = q_reshaped.to(scale.dtype) * scale.unsqueeze(-1)
        return decoded_reshaped.view(B, H, S, D)

    raise ValueError(
        f"Unsupported scale rank for dequantize_symmetric_int8: "
        f"quantized.ndim={quantized.ndim}, scale.ndim={scale.ndim}"
    )
