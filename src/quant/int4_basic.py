#!/usr/bin/env python3
"""
INT4 Symmetric Quantization for KV Cache.

This module provides INT4 quantization functions for more aggressive compression.
INT4 uses 4-bit signed integers with range [-7, 7] (we leave -8 for special cases).

Note:
- Quantized values are represented as torch.int8 in [-7, 7].
- Bit packing (2x INT4 per byte) is supported by pack_int4/unpack_int4.
"""

from typing import Tuple
import torch
from torch import Tensor


def quantize_symmetric_int4(
    tensor: Tensor,
    percentile: float = 99.9,
    group_size: int = 32,
) -> Tuple[Tensor, Tensor]:
    """
    Quantize tensor to INT4 using symmetric quantization.

    Formula:
        scale = max(|tensor|) / 7.0  (per group)
        quantized = round(tensor / scale).clamp(-7, 7)

    Args:
        tensor: Input tensor (float16/float32), shape [B, H, S, D]
        percentile: Clipping percentile (default 99.9 for outlier robustness)
        group_size: Number of elements per quantization group

    Returns:
        (quantized, scale) tuple
        - quantized: INT8 tensor (storing INT4 values in [-7, 7])
        - scale: FP16 tensor for dequantization, shape [B, H, S, num_groups]
    """
    if not tensor.is_floating_point():
        raise ValueError(f"Input tensor must be float, got {tensor.dtype}")
    
    # Get dimensions
    head_dim = tensor.shape[-1]
    
    if group_size == -1:
        group_size = head_dim

    if head_dim % group_size != 0:
        raise ValueError(f"head_dim {head_dim} must be divisible by group_size {group_size}")

    num_groups = head_dim // group_size
    
    # Reshape to [..., num_groups, group_size]
    input_shape = tensor.shape
    reshaped = tensor.view(*input_shape[:-1], num_groups, group_size)
    
    # Calculate absolute maximum per group
    abs_reshaped = reshaped.abs()
    
    if percentile < 100.0:
        quantile = max(min(percentile / 100.0, 1.0), 0.0)
        abs_max = torch.quantile(
            abs_reshaped.float(),
            quantile,
            dim=-1,
            keepdim=True,
        )
    else:
        abs_max = torch.amax(abs_reshaped, dim=-1, keepdim=True)

    # Avoid division by zero
    abs_max = abs_max.to(tensor.dtype)
    abs_max = abs_max.clamp(min=1e-5)
    
    # INT4 range is [-7, 7] (we reserve -8 for potential special values)
    scale = abs_max / 7.0
    
    # Quantize
    quantized_reshaped = torch.round(reshaped / scale).clamp(-7, 7).to(torch.int8)
    
    # Restore shape
    quantized = quantized_reshaped.view(*input_shape)
    
    # Store scales without trailing singleton dim for cache/storage compatibility:
    # [B, H, S, num_groups, 1] -> [B, H, S, num_groups]
    scale = scale.to(torch.float16).squeeze(-1)
    
    return quantized, scale


def dequantize_symmetric_int4(
    quantized: Tensor,
    scale: Tensor,
) -> Tensor:
    """
    Dequantize INT4 tensor.

    Formula:
        tensor = quantized * scale

    Args:
        quantized: INT8 tensor (storing INT4 values)
        scale: Scale tensor

    Returns:
        Dequantized tensor in float16 (or scale.dtype)
    """
    # Check dimensions to detect group-wise scaling
    # quantized: [B, H, S, D]
    # scale: [B, H, S, num_groups] or [B, H, S, num_groups, 1] or [B, H, S, 1]
    
    if scale.ndim == quantized.ndim + 1:
        # Group-wise scale [..., num_groups, 1]
        B, H, S, D = quantized.shape
        num_groups = scale.shape[-2]
        group_size = D // num_groups
        
        q_reshaped = quantized.view(B, H, S, num_groups, group_size)
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
        
    return quantized.to(scale.dtype) * scale


def pack_int4(tensor: Tensor) -> Tensor:
    """
    Pack two INT4 values into one INT8.
    
    Args:
        tensor: INT8 tensor with values in [-7, 7], shape [..., N] where N is even
        
    Returns:
        Packed INT8 tensor with shape [..., N//2]
    """
    assert tensor.shape[-1] % 2 == 0, "Last dimension must be even for packing"
    
    # Shift values to unsigned range [0, 15] for packing
    # Original: -7 to 7 -> Shifted: 0 to 14 (we add 7)
    shifted = (tensor + 7).to(torch.uint8)
    
    # Reshape to [..., N//2, 2]
    shape = tensor.shape[:-1] + (tensor.shape[-1] // 2, 2)
    reshaped = shifted.view(*shape)
    
    # Pack: high 4 bits from first value, low 4 bits from second
    packed = (reshaped[..., 0] << 4) | reshaped[..., 1]
    
    return packed.to(torch.int8)


def unpack_int4(packed: Tensor) -> Tensor:
    """
    Unpack INT8 tensor back to two INT4 values.
    
    Args:
        packed: Packed INT8 tensor, shape [..., N]
        
    Returns:
        Unpacked INT8 tensor with values in [-7, 7], shape [..., N*2]
    """
    # Convert to unsigned for bit operations
    unsigned = packed.to(torch.uint8)
    
    # Extract high and low nibbles
    high = (unsigned >> 4) & 0x0F
    low = unsigned & 0x0F
    
    # Stack and reshape
    unpacked = torch.stack([high, low], dim=-1)
    unpacked = unpacked.view(*packed.shape[:-1], packed.shape[-1] * 2)
    
    # Shift back to signed range [-7, 7]
    unpacked = (unpacked.to(torch.int8) - 7)
    
    return unpacked
