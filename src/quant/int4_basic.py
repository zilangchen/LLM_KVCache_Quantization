#!/usr/bin/env python3
"""
INT4 Symmetric Quantization for KV Cache.

This module provides INT4 quantization functions for more aggressive compression.
INT4 uses 4-bit signed integers. Symmetric quantization uses range [-7, 7];
asymmetric quantization (KIVI-style) uses the full [-8, 7] range.

Note:
- Quantized values are represented as torch.int8 in [-8, 7].
- Bit packing (2x INT4 per byte) is supported by pack_int4/unpack_int4.
  pack/unpack use an offset of +8 to map [-8, 7] to [0, 15] for nibble storage.
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

    # Precision note: for float16 inputs the non-quantile (amax) path stays
    # in float16.  The INT4 quantization step size (~1/7 ~= 0.14) is far
    # larger than float16 rounding error (~5e-4), so promoting to float32
    # is unnecessary and would increase peak memory.
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

    # INT4 symmetric range is [-7, 7]; asymmetric uses [-8, 7] (see asymmetric_quant.py).
    scale = abs_max / 7.0
    
    # Quantize
    quantized_reshaped = torch.round(reshaped / scale).clamp(-7, 7).to(torch.int8)
    
    # Restore shape
    quantized = quantized_reshaped.view(*input_shape)
    
    # Store scales without trailing singleton dim for cache/storage compatibility:
    # [B, H, S, num_groups, 1] -> [B, H, S, num_groups]
    # ENG-028: Preserve input dtype instead of forcing fp16, consistent with INT8 path.
    scale = scale.to(tensor.dtype).squeeze(-1)
    
    return quantized, scale


def quantize_symmetric_int4_with_scale(
    tensor: Tensor,
    scale: Tensor,
    group_size: int,
) -> Tuple[Tensor, Tensor]:
    """
    Symmetric INT4 quantization using a provided static scale.

    Args:
        tensor: Input tensor [B, H, S, D]
        scale: Static scale tensor (see _normalize_static_scale)
        group_size: Group size for scaling

    Returns:
        quantized: INT8 tensor storing INT4 values in [-7, 7]
        scale_expanded: Scale tensor expanded to [B, H, S, num_groups]
    """
    if not tensor.is_floating_point():
        raise ValueError(f"Input tensor must be float, got {tensor.dtype}")

    head_dim = tensor.shape[-1]
    if group_size == -1:
        group_size = head_dim
    if head_dim % group_size != 0:
        raise ValueError(f"head_dim {head_dim} must be divisible by group_size {group_size}")

    batch, heads, seq_len, _ = tensor.shape
    num_groups = head_dim // group_size
    reshaped = tensor.view(batch, heads, seq_len, num_groups, group_size)

    scale_expanded = _normalize_static_scale(scale, batch, heads, seq_len, num_groups)
    scale_expanded = scale_expanded.to(tensor.dtype).clamp(min=1e-5)

    quantized = torch.round(reshaped / scale_expanded).clamp(-7, 7).to(torch.int8)
    quantized = quantized.view(batch, heads, seq_len, head_dim)

    return quantized, scale_expanded.squeeze(-1)


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
    # QNT-008: Input type validation for defense-in-depth.
    if quantized.dtype != torch.int8:
        raise ValueError(f"quantized must be torch.int8, got {quantized.dtype}")
    if not scale.is_floating_point():
        raise ValueError(f"scale must be floating point, got {scale.dtype}")

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

    if scale.ndim == quantized.ndim:
        # Group-wise scale stored as [B, H, S, num_groups] (including num_groups==1).
        B, H, S, D = quantized.shape
        num_groups = scale.shape[-1]
        if num_groups <= 0 or D % num_groups != 0:
            raise ValueError(
                f"Invalid scale shape for group-wise dequantization: "
                f"quantized={tuple(quantized.shape)}, scale={tuple(scale.shape)}"
            )
        if num_groups == 1:
            return quantized.to(scale.dtype) * scale
        group_size = D // num_groups

        q_reshaped = quantized.view(B, H, S, num_groups, group_size)
        decoded_reshaped = q_reshaped.to(scale.dtype) * scale.unsqueeze(-1)
        return decoded_reshaped.view(B, H, S, D)

    raise ValueError(
        f"Unsupported scale rank for dequantize_symmetric_int4: "
        f"quantized.ndim={quantized.ndim}, scale.ndim={scale.ndim}"
    )


def pack_int4(tensor: Tensor) -> Tensor:
    """
    Pack two INT4 values into one INT8.

    Args:
        tensor: INT8 tensor with values in [-8, 7], shape [..., N] where N is even.
                Both symmetric ([-7, 7]) and asymmetric ([-8, 7]) ranges are supported.

    Returns:
        Packed INT8 tensor with shape [..., N//2]
    """
    assert tensor.shape[-1] % 2 == 0, "Last dimension must be even for packing"

    # Shift values to unsigned range [0, 15] for packing.
    # Offset +8 maps the full INT4 signed range [-8, 7] -> [0, 15].
    # This correctly handles both symmetric ([-7, 7]) and asymmetric ([-8, 7]) quantization.
    # (Previous offset of +7 failed for -8: -8+7=-1 overflowed to 255 in uint8.)
    shifted = (tensor + 8).to(torch.uint8)
    
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
        Unpacked INT8 tensor with values in [-8, 7], shape [..., N*2]
    """
    # Convert to unsigned for bit operations
    unsigned = packed.to(torch.uint8)

    # Extract high and low nibbles
    high = (unsigned >> 4) & 0x0F
    low = unsigned & 0x0F

    # Stack and reshape
    unpacked = torch.stack([high, low], dim=-1)
    unpacked = unpacked.view(*packed.shape[:-1], packed.shape[-1] * 2)

    # Shift back to signed range [-8, 7] (inverse of +8 offset in pack_int4).
    unpacked = (unpacked.to(torch.int8) - 8)

    return unpacked
