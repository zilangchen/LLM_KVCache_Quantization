"""FlashInfer FP16 decode attention adapter for INT4 asymmetric KV cache.

Strategy: dequant packed INT4 KV to FP16, then call FlashInfer's optimised
FP16 single-decode SDPA.  This is an *end-to-end backend comparison* —
dequant overhead + FlashInfer FP16 Tensor-Core SDPA  vs  Triton in-kernel
INT4 dequant SDPA.

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


def decode_attn_flashinfer(
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
    """Decode attention via FlashInfer FP16 backend.

    Args:
        q:            [B, Hq, D]     fp16  — query (single decode step)
        k_packed:     [B, Hkv, S, D//2] int8  — bit-packed INT4 K cache
        v_packed:     [B, Hkv, S, D//2] int8  — bit-packed INT4 V cache
        k_scale:      [B, Hkv, D]     float32 — per-channel K scale
        k_zp:         [B, Hkv, D]     float32 — per-channel K zero-point
        v_scale:      [B, Hkv, S]     float32 — per-token  V scale
        v_zp:         [B, Hkv, S]     float32 — per-token  V zero-point
        context_lens: [B]             int32   — valid sequence length per batch
        sm_scale:     softmax scale (1/sqrt(D)); auto-computed when None

    Returns:
        [B, Hq, D] fp16 — attention output
    """
    import flashinfer  # lazy: only available on GPU hosts

    B, Hq, D = q.shape

    if sm_scale is None:
        sm_scale = 1.0 / math.sqrt(D)

    # --- 1. Unpack INT4 → int8 values in [-8, 7] ---
    k_unpacked = unpack_int4(k_packed)  # [B, Hkv, S, D]
    v_unpacked = unpack_int4(v_packed)  # [B, Hkv, S, D]

    # --- 2. Dequantize to FP16 ---
    k_fp = dequantize_asymmetric_per_channel(k_unpacked, k_scale, k_zp).to(
        torch.float16
    )  # [B, Hkv, S, D]
    v_fp = dequantize_asymmetric_per_token(v_unpacked, v_scale, v_zp).to(
        torch.float16
    )  # [B, Hkv, S, D]

    # --- 3. Per-batch FlashInfer decode ---
    outputs = []
    for b in range(B):
        s = context_lens[b].item()
        if s <= 0:
            # Empty sequence — return zeros (matches Triton kernel behaviour)
            outputs.append(torch.zeros(Hq, D, dtype=torch.float16, device=q.device))
            continue

        # Layout: [Hkv, S, D] → slice valid tokens → permute to NHD [s, Hkv, D]
        k_b = k_fp[b, :, :s, :].permute(1, 0, 2).contiguous()  # [s, Hkv, D]
        v_b = v_fp[b, :, :s, :].permute(1, 0, 2).contiguous()  # [s, Hkv, D]
        q_b = q[b]  # [Hq, D]

        out_b = flashinfer.decode.single_decode_with_kv_cache(
            q_b,
            k_b,
            v_b,
            kv_layout="NHD",
            sm_scale=sm_scale,
        )  # [Hq, D]
        outputs.append(out_b)

    return torch.stack(outputs, dim=0)  # [B, Hq, D]
