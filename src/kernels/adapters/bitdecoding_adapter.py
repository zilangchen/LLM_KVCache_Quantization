"""BitDecoding INT4 decode attention adapter for INT4 asymmetric KV cache.

Strategy: dequant our packed INT4 KV → FP16 → BitDecoding re-packs to its
own INT4 format → fused Tensor-Core attention via CUTLASS.

BitDecoding (HPCA 2026) uses CUTLASS templates with in-kernel INT4 dequant
and Tensor Core accumulation.

API shapes (bit_decode 1.0.0.post1, matching scripts/test_bitdecoding.py):
  q:         [B, 1, Hq, D]                 fp16
  k_pack:    [B, S, Hkv, D//8]              int32  (8 nibbles per int32)
  k_params:  [B, S, Hkv, 2]                 fp16   (scale, zero_point per token)
  v_pack:    [B, S, Hkv, D//8]              int32
  v_params:  [B, S, Hkv, 2]                 fp16

Note: BD uses per-token quantization. Our per-channel K scales are LOST
in the dequant→repack round-trip (BD re-quantizes with its own per-token math).
This is a system-level comparison, not "same quant different kernel".

Supported kv_modes: int4_ours_asym, int4_ours_asym_ba.
"""

from __future__ import annotations

import math
from typing import Optional

import torch

from src.quant.asymmetric_quant import (
    dequantize_asymmetric_per_channel,
    dequantize_asymmetric_per_token,
)
from src.quant.int4_basic import unpack_int4

# BitDecoding constants
_BD_NUM_BITS = 4
_BD_GROUP_SIZE = 128
# pack_dim = head_dim // 8 (8 nibbles per int32)


def decode_attn_bitdecoding(
    q: torch.Tensor,
    k_packed: torch.Tensor,
    v_packed: torch.Tensor,
    k_scale: torch.Tensor,
    k_zp: torch.Tensor,
    v_scale: torch.Tensor,
    v_zp: torch.Tensor,
    context_lens: torch.Tensor,
    sm_scale: Optional[float] = None,
) -> torch.Tensor:
    """Decode attention via BitDecoding INT4 CUTLASS backend.

    Args:
        q:            [B, Hq, D]        fp16  — query (single decode step)
        k_packed:     [B, Hkv, S, D//2] int8  — our bit-packed INT4 K cache
        v_packed:     [B, Hkv, S, D//2] int8  — our bit-packed INT4 V cache
        k_scale:      [B, Hkv, D]       float32 — per-channel K scale
        k_zp:         [B, Hkv, D]       float32 — per-channel K zero-point
        v_scale:      [B, Hkv, S]       float32 — per-token  V scale
        v_zp:         [B, Hkv, S]       float32 — per-token  V zero-point
        context_lens: [B]               int32   — valid sequence length per batch
        sm_scale:     softmax scale (1/sqrt(D)); auto-computed when None

    Returns:
        [B, Hq, D] fp16 — attention output
    """
    from bit_decode import fwd_kvcache_int, kvcache_pack_int  # lazy import

    B, Hq, D = q.shape
    Hkv = k_packed.shape[1]
    S = k_packed.shape[2]
    pack_dim = D // 8  # 8 nibbles per int32

    if sm_scale is None:
        sm_scale = 1.0 / math.sqrt(D)

    # --- 1. Unpack + dequant our INT4 → FP16 ---
    k_unpacked = unpack_int4(k_packed)  # [B, Hkv, S, D] int8
    v_unpacked = unpack_int4(v_packed)  # [B, Hkv, S, D] int8

    k_fp = dequantize_asymmetric_per_channel(k_unpacked, k_scale, k_zp).to(
        torch.float16
    )  # [B, Hkv, S, D]
    v_fp = dequantize_asymmetric_per_token(v_unpacked, v_scale, v_zp).to(
        torch.float16
    )  # [B, Hkv, S, D]

    # --- 2. Transpose to BitDecoding BSHD layout ---
    # Our format: [B, Hkv, S, D] → BitDecoding: [B, S, Hkv, D]
    k_bshd = k_fp.permute(0, 2, 1, 3).contiguous()  # [B, S, Hkv, D]
    v_bshd = v_fp.permute(0, 2, 1, 3).contiguous()  # [B, S, Hkv, D]

    # --- 3. Allocate BD buffers with test_bitdecoding.py layout ---
    # BitDecoding requires S to be a multiple of group_size (128).
    # Pad only when strictly necessary.
    max_s = int(context_lens.max().item())
    if max_s <= 0:
        return torch.zeros(B, Hq, D, dtype=torch.float16, device=q.device)

    align = _BD_GROUP_SIZE
    padded_s = ((max_s + align - 1) // align) * align

    # If padding needed, extend with last-token repeat (avoid per-token zero-scale NaN)
    if padded_s > S:
        pad_len = padded_s - S
        # Repeat last token to fill padding (avoids scale=0 → NaN)
        k_last = k_bshd[:, S - 1:S, :, :].expand(B, pad_len, Hkv, D)
        v_last = v_bshd[:, S - 1:S, :, :].expand(B, pad_len, Hkv, D)
        k_slice = torch.cat([k_bshd, k_last], dim=1).contiguous()
        v_slice = torch.cat([v_bshd, v_last], dim=1).contiguous()
    else:
        k_slice = k_bshd[:, :padded_s, :, :].contiguous()
        v_slice = v_bshd[:, :padded_s, :, :].contiguous()

    # --- 4. Allocate BD packed buffers (matching test_bitdecoding.py) ---
    k_bd_pack = torch.zeros(
        B, padded_s, Hkv, pack_dim,
        dtype=torch.int32, device=q.device,
    )
    v_bd_pack = torch.zeros(
        B, padded_s, Hkv, pack_dim,
        dtype=torch.int32, device=q.device,
    )
    k_bd_params = torch.zeros(
        B, padded_s, Hkv, 2,
        dtype=torch.float16, device=q.device,
    )
    v_bd_params = torch.zeros(
        B, padded_s, Hkv, 2,
        dtype=torch.float16, device=q.device,
    )

    cu_seqlens_k = torch.tensor(
        [0, padded_s], dtype=torch.int32, device=q.device,
    )

    # --- 5. Pack with BD's per-token quantization ---
    kvcache_pack_int(
        k_slice, k_bd_pack, k_bd_params,
        v_slice, v_bd_pack, v_bd_params,
        cu_seqlens_k=cu_seqlens_k,
        seqlen_k=padded_s,
        quant_mode="k-channel",
        group_size=_BD_GROUP_SIZE,
        num_bits=_BD_NUM_BITS,
    )

    # --- 6. Call BitDecoding fused attention ---
    # q needs shape [B, 1, Hq, D] for BitDecoding
    q_bd = q.unsqueeze(1).contiguous()  # [B, 1, Hq, D]

    out = fwd_kvcache_int(
        q_bd, k_bd_pack, k_bd_params, v_bd_pack, v_bd_params,
        softmax_scale=sm_scale,
        quant_mode="k-channel",
        group_size=_BD_GROUP_SIZE,
        num_bits=_BD_NUM_BITS,
    )  # [B, 1, Hq, D]

    return out.squeeze(1)  # [B, Hq, D]
