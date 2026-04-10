"""BitDecoding INT4 decode attention adapter for INT4 asymmetric KV cache.

Strategy: dequant our packed INT4 KV → FP16 → BitDecoding re-packs to its
own INT4 format → fused Tensor-Core attention via CUTLASS.

BitDecoding (HPCA 2026) uses CUTLASS templates with in-kernel INT4 dequant
and Tensor Core accumulation, achieving 3-9x speedup over Flash-Decoding.

Note: the dequant→repack step adds overhead. A deeper integration would
store KV directly in BitDecoding's pack format, eliminating this roundtrip.

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
_BD_PACK_NUMS = 16 // _BD_NUM_BITS  # 4 nibbles per uint16
_BD_GROUP_SIZE = 128


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
        k_packed:     [B, Hkv, S, D//2] int8  — bit-packed INT4 K cache
        v_packed:     [B, Hkv, S, D//2] int8  — bit-packed INT4 V cache
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
    S = k_packed.shape[2] * 2  # packed D//2 → D, but S is dim 2 of packed

    # Actually S is the sequence dimension (dim=2 of k_packed)
    S = k_packed.shape[2]
    # D_packed = k_packed.shape[3] = D // 2
    D_full = k_packed.shape[3] * 2

    if sm_scale is None:
        sm_scale = 1.0 / math.sqrt(D_full)

    import os
    if os.environ.get("BD_DEBUG", ""):
        print(f"[BD] q={q.shape} k_packed={k_packed.shape} v_packed={v_packed.shape} "
              f"k_scale={k_scale.shape} v_scale={v_scale.shape} "
              f"ctx_lens={context_lens} S={S} D={D_full}")

    # --- 1. Unpack + dequant our INT4 → FP16 ---
    k_unpacked = unpack_int4(k_packed)  # [B, Hkv, S, D]
    v_unpacked = unpack_int4(v_packed)  # [B, Hkv, S, D]

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

    # --- 3. Align sequence length for BitDecoding ---
    # BitDecoding requires S to be a multiple of _BD_PACK_NUMS (4) and
    # >= _BD_GROUP_SIZE (128).  Pad with zeros if needed.
    max_s = int(context_lens.max().item())
    if max_s <= 0:
        return torch.zeros(B, Hq, D_full, dtype=torch.float16, device=q.device)

    # Round up to nearest multiple of lcm(_BD_PACK_NUMS, _BD_GROUP_SIZE)
    align = _BD_GROUP_SIZE  # 128 is already a multiple of 4
    padded_s = ((max_s + align - 1) // align) * align

    # Pad FP16 tensors if padded_s > S
    if padded_s > S:
        pad_len = padded_s - S
        k_pad = torch.zeros(B, pad_len, Hkv, D_full, dtype=torch.float16, device=q.device)
        v_pad = torch.zeros(B, pad_len, Hkv, D_full, dtype=torch.float16, device=q.device)
        k_slice = torch.cat([k_bshd, k_pad], dim=1)  # [B, padded_s, Hkv, D]
        v_slice = torch.cat([v_bshd, v_pad], dim=1)
    else:
        k_slice = k_bshd[:, :padded_s, :, :]
        v_slice = v_bshd[:, :padded_s, :, :]

    # --- 4. Allocate BitDecoding buffers + repack ---
    k_bd_pack = torch.zeros(
        B, padded_s // _BD_PACK_NUMS, Hkv, D_full,
        dtype=torch.uint16, device=q.device,
    )
    k_bd_params = torch.zeros(
        B, padded_s // _BD_GROUP_SIZE, Hkv, D_full,
        dtype=torch.float32, device=q.device,
    )
    v_bd_pack = torch.zeros(
        B, padded_s, Hkv, D_full // _BD_PACK_NUMS,
        dtype=torch.uint16, device=q.device,
    )
    v_bd_params = torch.zeros(
        B, D_full // _BD_GROUP_SIZE, Hkv, padded_s,
        dtype=torch.float32, device=q.device,
    )
    cu_seqlens_k = torch.arange(
        0, (B + 1) * padded_s, padded_s, dtype=torch.int32, device=q.device,
    )

    kvcache_pack_int(
        k_slice, k_bd_pack, k_bd_params,
        v_slice, v_bd_pack, v_bd_params,
        None, cu_seqlens_k, padded_s,
        "k-channel", _BD_GROUP_SIZE, _BD_NUM_BITS,
    )

    # --- 5. Call BitDecoding fused attention ---
    # q needs shape [B, 1, Hq, D] for BitDecoding
    q_bd = q.unsqueeze(1)  # [B, 1, Hq, D]

    out = fwd_kvcache_int(
        q_bd, k_bd_pack, k_bd_params, v_bd_pack, v_bd_params,
        None, sm_scale, "k-channel", _BD_GROUP_SIZE, _BD_NUM_BITS,
    )  # [B, 1, Hq, D]

    return out.squeeze(1)  # [B, Hq, D]
