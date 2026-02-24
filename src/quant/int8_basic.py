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


def _normalize_static_scale(
    scale: Tensor,
    batch: int,
    heads: int,
    seq_len: int,
    num_groups: int,
) -> Tensor:
    """
    Normalize static scale to shape [B, H, S, num_groups, 1].

    Accepts scale in one of the following shapes:
    - [H, num_groups]                   (2D, broadcast over batch & seq)
    - [B, H, G] / [1, H, G]            (3D, broadcast over seq)
    - [H, 1, G] / [H, G, 1]            (3D legacy, broadcast over batch & seq)
    - [1, H, 1, num_groups]             (4D, broadcast over batch & seq)
    - [B, H, S, num_groups]             (4D, no broadcast needed)
    - [B, H, S, num_groups, 1]          (5D, already target shape)
    """
    if scale.ndim == 2:
        # [H, G] -> [1, H, 1, G, 1]
        scale_view = scale[None, :, None, :, None]
    elif scale.ndim == 4:
        # [B, H, S, G] -> [B, H, S, G, 1]
        scale_view = scale[..., None]
    elif scale.ndim == 5:
        scale_view = scale
    elif scale.ndim == 3:
        # Several 3D layouts are supported.
        # Dispatch is by matching shape dims against (batch, heads, num_groups).
        d0, d1, d2 = scale.shape
        if d2 == num_groups and d0 == batch and d1 == heads:
            # [B, H, G] -> [B, H, 1, G, 1]
            scale_view = scale[:, :, None, :, None]
        elif d2 == num_groups and d0 == 1 and d1 == heads:
            # [1, H, G] -> [1, H, 1, G, 1]; final expand handles batch.
            scale_view = scale[:, :, None, :, None]
        elif d2 == num_groups and d0 == heads and d1 == 1:
            # [H, 1, G] (legacy) -> [1, H, 1, G, 1]
            scale_view = scale[:, 0, :][None, :, None, :, None]
        elif d1 == num_groups and d0 == heads and d2 == 1:
            # [H, G, 1] (legacy) -> [1, H, 1, G, 1]
            scale_view = scale[..., 0][None, :, None, :, None]
        else:
            raise ValueError(
                f"Unsupported 3D scale shape: {scale.shape} for "
                f"batch={batch}, heads={heads}, num_groups={num_groups}"
            )
    else:
        raise ValueError(f"Unsupported scale ndim={scale.ndim}, shape={tuple(scale.shape)}")

    scale_view = scale_view.expand(batch, heads, seq_len, num_groups, 1)
    return scale_view


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

    abs_max = abs_max.to(tensor.dtype)

    # Avoid division by zero
    abs_max = abs_max.clamp(min=1e-5)
    scale = abs_max / 127.0  # [B, H, S, num_groups, 1]

    # Quantize: [..., num_groups, group_size]
    # Scale broadcasts over group_size dim
    quantized_reshaped = torch.round(reshaped / scale).clamp(-127, 127).to(torch.int8)
    
    # Restore shape: [B, H, S, D]
    quantized = quantized_reshaped.view(*input_shape)
    
    # Scale shape issues:
    # Scale is currently [B, H, S, num_groups, 1].
    # For storage, we might want to keep it as is, or flattened.
    # To maintain compatibility with dequantize which expects simple mul,
    # we should check dequantize logic.
    # If we return scale as [B, H, S, num_groups, 1], caller (Cache) needs to know.
    # For baseline (num_groups=1), this is [B, H, S, 1, 1] which views to [B, H, S, 1].
    
    # Let's flatten scale to [B, H, S, num_groups] if num_groups > 1?
    # Or keep it as [B, H, S, num_groups, 1] for easy dequantize?
    # Our dequantize function below needs update.
    
    # Store scales without the trailing singleton dim for kernel compatibility:
    # [B, H, S, num_groups, 1] -> [B, H, S, num_groups]
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
        scale_expanded: Scale tensor expanded to [batch, heads, seq, num_groups]
    """
    if not tensor.is_floating_point():
        raise ValueError(f"Input tensor must be float, got {tensor.dtype}")

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
    scale_expanded = _normalize_static_scale(scale, batch, heads, seq_len, num_groups)
    scale_expanded = scale_expanded.to(tensor.dtype)
    scale_expanded = scale_expanded.clamp(min=1e-5)

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
        group_size = D // num_groups

        q_reshaped = quantized.view(B, H, S, num_groups, group_size)
        decoded_reshaped = q_reshaped.to(scale.dtype) * scale
        return decoded_reshaped.view(B, H, S, D)

    # --- Path B / B': 4-D scale ---
    if scale.ndim == quantized.ndim:
        B, H, S, D = quantized.shape
        num_groups = scale.shape[-1]
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
