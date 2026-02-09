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
    - [H, num_groups]
    - [1, H, 1, num_groups]
    - [B, H, S, num_groups]
    - [B, H, S, num_groups, 1]
    """
    if scale.ndim == 2:
        scale_view = scale[None, :, None, :, None]
    elif scale.ndim == 4:
        scale_view = scale[..., None]
    elif scale.ndim == 5:
        scale_view = scale
    elif scale.ndim == 3 and scale.shape[-1] == num_groups:
        # Assume [H, num_groups, 1] or [1, H, num_groups]
        if scale.shape[0] == heads:
            scale_view = scale[:, None, :][None, :, None, :, None]
        else:
            raise ValueError(f"Unsupported scale shape: {scale.shape}")
    else:
        raise ValueError(f"Unsupported scale shape: {scale.shape}")

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

    Args:
        quantized: INT8 tensor
        scale: Scale tensor

    Returns:
        Dequantized tensor in float16 (or scale.dtype)
    """
    # Check dimensions to detect group-wise scaling
    # quantized: [B, H, S, D]
    # scale: [B, H, S, num_groups] or [B, H, S, num_groups, 1] or [B, H, S, 1]
    
    if scale.ndim == quantized.ndim + 1:
        # Likely group-wise scale [..., num_groups, 1]
        # We need to reshape quantized to match
        B, H, S, D = quantized.shape
        num_groups = scale.shape[-2]
        group_size = D // num_groups
        
        q_reshaped = quantized.view(B, H, S, num_groups, group_size)  # [B, H, S, G, GS]
        # Scale broadcasts: [..., num_groups, 1] * [..., num_groups, group_size]
        decoded_reshaped = q_reshaped.to(scale.dtype) * scale
        
        return decoded_reshaped.view(B, H, S, D)

    if scale.ndim == quantized.ndim and scale.shape[-1] != 1:
        # Group-wise scale stored as [B, H, S, num_groups]
        B, H, S, D = quantized.shape
        num_groups = scale.shape[-1]
        group_size = D // num_groups
        q_reshaped = quantized.view(B, H, S, num_groups, group_size)
        decoded_reshaped = q_reshaped.to(scale.dtype) * scale.unsqueeze(-1)
        return decoded_reshaped.view(B, H, S, D)

    # Per-token/per-head scale: [B, H, S, 1] (broadcasts over D)
    return quantized.to(scale.dtype) * scale
