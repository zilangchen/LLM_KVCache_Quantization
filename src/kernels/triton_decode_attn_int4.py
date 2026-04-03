"""
INT4 fused decode-attention wrapper.

This wrapper reuses the INT8 Triton kernel by first materializing INT4 cache
values to signed INT8 in [-8, 7]. K/V scales remain group-wise FP16 and are
applied in-kernel exactly as INT8 path.

Notes:
- Supports both packed and unpacked INT4 cache tensors.
- Packed format stores 2x INT4 values per byte in last dimension.
"""

from __future__ import annotations

from typing import Optional

import torch

from src.kernels.triton_decode_attn_int8 import decode_attn_int8
from src.quant.int4_basic import unpack_int4


def _materialize_int4_as_int8(
    cache: torch.Tensor,
    *,
    head_dim: int,
    bit_packed: bool,
) -> torch.Tensor:
    if not bit_packed:
        if cache.shape[-1] != head_dim:
            raise ValueError(
                f"Unpacked INT4 cache last dim mismatch: got {cache.shape[-1]}, expected {head_dim}"
            )
        # KRN-024/029: unpacked path must be contiguous for correct kernel reshape
        if cache.stride(-1) != 1:
            raise ValueError(
                f"Unpacked INT4 cache inner dim must be contiguous (stride=1), "
                f"got stride={cache.stride(-1)}. Use .contiguous()."
            )
        # KRN-011: Validate dtype for unpacked path. Unpacked INT4 values
        # are stored as int8 (range [-8, 7]); other dtypes indicate a caller bug.
        if cache.dtype != torch.int8:
            raise ValueError(
                f"Unpacked INT4 cache must be int8, got {cache.dtype}. "
                "Unpacked INT4 values should be stored as torch.int8."
            )
        return cache

    if cache.shape[-1] * 2 != head_dim:
        raise ValueError(
            f"Packed INT4 cache last dim mismatch: got {cache.shape[-1]}, expected {head_dim // 2}"
        )
    return unpack_int4(cache)


def decode_attn_int4(
    q: torch.Tensor,
    k_cache_int4: torch.Tensor,
    v_cache_int4: torch.Tensor,
    k_scale: torch.Tensor,
    v_scale: torch.Tensor,
    context_lens: torch.Tensor,
    sm_scale: Optional[float] = None,
    *,
    bit_packed: bool = True,
    head_dim: Optional[int] = None,
    debug_stats: Optional[dict] = None,
    layer_idx: Optional[int] = None,
    block_size: Optional[int] = None,
) -> torch.Tensor:
    """
    Decode attention for INT4 KV cache (q_len == 1), backed by INT8 Triton kernel.

    Args:
        q: [B, Hq, D]
        k_cache_int4/v_cache_int4: [B, Hkv, S, D] if unpacked, [B, Hkv, S, D/2] if packed
        k_scale/v_scale: [B, Hkv, S, G]
        context_lens: [B]
        bit_packed: whether cache tensors are packed as 2x INT4 per byte
        head_dim: expected full head_dim D; defaults to q.shape[-1]
    """
    if q.ndim != 3:
        raise ValueError(f"q must have shape [B, Hq, D], got {tuple(q.shape)}")

    d = int(head_dim or q.shape[-1])
    k_cache_int8 = _materialize_int4_as_int8(
        k_cache_int4,
        head_dim=d,
        bit_packed=bit_packed,
    )
    v_cache_int8 = _materialize_int4_as_int8(
        v_cache_int4,
        head_dim=d,
        bit_packed=bit_packed,
    )

    return decode_attn_int8(
        q=q,
        k_cache=k_cache_int8,
        v_cache=v_cache_int8,
        k_scale=k_scale,
        v_scale=v_scale,
        context_lens=context_lens,
        sm_scale=sm_scale,
        debug_stats=debug_stats,
        layer_idx=layer_idx,
        block_size=block_size,
    )

