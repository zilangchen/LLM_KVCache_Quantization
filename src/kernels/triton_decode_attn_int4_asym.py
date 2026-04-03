"""
INT4 Asymmetric Fused Decode Attention Kernel using Triton.

Supports KIVI-style and RoleAlign asymmetric quantization:
  K: per-channel scale/zp [B, H, D] — shared across all tokens
  V: per-token  scale/zp [B, H, S] — shared across all channels
  Cache: bit-packed INT4 [B, H, S, D//2] with +8 offset

Dequant: x_hat = (nibble - 8) * scale + zero_point

Design: Split-channel approach — processes even (hi nibble) and odd (lo nibble)
channels separately throughout the kernel, avoiding any interleave/reshape.
For K: qk = dot(q_even, k_hi_dequant) + dot(q_odd, k_lo_dequant)
For V: accumulate even/odd halves separately, then interleave at output.
"""

from __future__ import annotations

import os
from typing import Optional

import torch
import triton
import triton.language as tl


@triton.jit
def decode_attn_int4_asym_kernel(
    Q_ptr,              # [B, Hq, D] fp16
    K_ptr,              # [B, Hkv, S, D//2] packed int8
    V_ptr,              # [B, Hkv, S, D//2] packed int8
    K_Scale_ptr,        # [B, Hkv, D] fp16 — per-channel
    K_ZP_ptr,           # [B, Hkv, D] fp16 — per-channel
    V_Scale_ptr,        # [B, Hkv, S] fp16 — per-token
    V_ZP_ptr,           # [B, Hkv, S] fp16 — per-token
    Context_Lens_ptr,   # [B]
    Output_ptr,         # [B, Hq, D] fp16
    sm_scale,
    # Q strides [B, Hq, D]
    stride_q_b, stride_q_h, stride_q_d,
    # K packed strides [B, Hkv, S, D//2]
    stride_k_b, stride_k_h, stride_k_s, stride_k_pd,
    # V packed strides [B, Hkv, S, D//2]
    stride_v_b, stride_v_h, stride_v_s, stride_v_pd,
    # K scale/zp strides [B, Hkv, D]
    stride_ks_b, stride_ks_h, stride_ks_d,
    stride_kz_b, stride_kz_h, stride_kz_d,
    # V scale/zp strides [B, Hkv, S]
    stride_vs_b, stride_vs_h, stride_vs_s,
    stride_vz_b, stride_vz_h, stride_vz_s,
    # Output strides [B, Hq, D]
    stride_o_b, stride_o_h, stride_o_d,
    # Constexprs
    HEAD_DIM: tl.constexpr,
    PACKED_DIM: tl.constexpr,   # = HEAD_DIM // 2
    BLOCK_SIZE: tl.constexpr,
    N_REP: tl.constexpr,
):
    batch_id = tl.program_id(0)
    head_id = tl.program_id(1)
    kv_head_id = head_id // N_REP

    # --- Load Q split into even/odd channels ---
    q_ptr = Q_ptr + batch_id * stride_q_b + head_id * stride_q_h
    offs_d = tl.arange(0, HEAD_DIM)
    offs_pd = tl.arange(0, PACKED_DIM)
    q_full = tl.load(q_ptr + offs_d * stride_q_d).to(tl.float32)
    # Split: q_even = q[0,2,4,...], q_odd = q[1,3,5,...]
    # Pack layout: byte[i] → hi=val[2i], lo=val[2i+1]
    # So even channels (0,2,4...) come from hi nibbles, odd (1,3,5...) from lo
    offs_even = offs_pd * 2        # [0, 2, 4, ...]
    offs_odd = offs_pd * 2 + 1     # [1, 3, 5, ...]
    q_even = tl.load(q_ptr + offs_even * stride_q_d).to(tl.float32)  # [PACKED_DIM]
    q_odd = tl.load(q_ptr + offs_odd * stride_q_d).to(tl.float32)    # [PACKED_DIM]

    # --- Load K per-channel scale/zp [HEAD_DIM] split into even/odd ---
    ks_base = K_Scale_ptr + batch_id * stride_ks_b + kv_head_id * stride_ks_h
    kz_base = K_ZP_ptr + batch_id * stride_kz_b + kv_head_id * stride_kz_h
    ks_even = tl.load(ks_base + offs_even * stride_ks_d).to(tl.float32)
    ks_odd = tl.load(ks_base + offs_odd * stride_ks_d).to(tl.float32)
    kz_even = tl.load(kz_base + offs_even * stride_kz_d).to(tl.float32)
    kz_odd = tl.load(kz_base + offs_odd * stride_kz_d).to(tl.float32)

    ctx_len = tl.load(Context_Lens_ptr + batch_id)

    # KV base pointers
    k_base = K_ptr + batch_id * stride_k_b + kv_head_id * stride_k_h
    v_base = V_ptr + batch_id * stride_v_b + kv_head_id * stride_v_h
    vs_base = V_Scale_ptr + batch_id * stride_vs_b + kv_head_id * stride_vs_h
    vz_base = V_ZP_ptr + batch_id * stride_vz_b + kv_head_id * stride_vz_h

    # --- Online softmax accumulators ---
    m_i = -float('inf')
    l_i = 0.0
    # Split accumulator: even channels and odd channels
    acc_even = tl.zeros([PACKED_DIM], dtype=tl.float32)
    acc_odd = tl.zeros([PACKED_DIM], dtype=tl.float32)

    for start_n in range(0, ctx_len, BLOCK_SIZE):
        offs_n = start_n + tl.arange(0, BLOCK_SIZE)
        mask = offs_n < ctx_len

        # === K: Load packed [BLOCK, PACKED_DIM], unpack, dequant, dot ===
        k_ptrs = k_base + offs_n[:, None] * stride_k_s + offs_pd[None, :] * stride_k_pd
        k_packed = tl.load(k_ptrs, mask=mask[:, None], other=0).to(tl.uint8)

        # Unpack nibbles → signed float
        k_hi = ((k_packed >> 4) & 0x0F).to(tl.float32) - 8.0  # even channels [BLOCK, PD]
        k_lo = (k_packed & 0x0F).to(tl.float32) - 8.0          # odd channels  [BLOCK, PD]

        # Dequant per-channel: k_fp = k_int * scale + zp
        k_hi_dq = k_hi * ks_even[None, :] + kz_even[None, :]  # [BLOCK, PD]
        k_lo_dq = k_lo * ks_odd[None, :] + kz_odd[None, :]    # [BLOCK, PD]

        # QK = sum(q_even * k_hi_dq) + sum(q_odd * k_lo_dq)  per row
        qk_even = tl.sum(q_even[None, :] * k_hi_dq, axis=1)   # [BLOCK]
        qk_odd = tl.sum(q_odd[None, :] * k_lo_dq, axis=1)     # [BLOCK]
        qk = (qk_even + qk_odd) * sm_scale
        qk = tl.where(mask, qk, float("-inf"))

        # === Online Softmax ===
        m_i_new = tl.max(qk, 0)
        m_ij = tl.maximum(m_i, m_i_new)
        alpha = tl.exp(m_i - m_ij)
        beta = tl.exp(qk - m_ij)
        l_ij = l_i * alpha + tl.sum(beta, 0)

        # === V: Load packed, unpack, dequant, accumulate ===
        v_ptrs = v_base + offs_n[:, None] * stride_v_s + offs_pd[None, :] * stride_v_pd
        v_packed = tl.load(v_ptrs, mask=mask[:, None], other=0).to(tl.uint8)

        v_hi = ((v_packed >> 4) & 0x0F).to(tl.float32) - 8.0  # even channels
        v_lo = (v_packed & 0x0F).to(tl.float32) - 8.0          # odd channels

        # V per-token dequant
        v_scale_tok = tl.load(vs_base + offs_n * stride_vs_s,
                              mask=mask, other=1.0).to(tl.float32)  # [BLOCK]
        v_zp_tok = tl.load(vz_base + offs_n * stride_vz_s,
                           mask=mask, other=0.0).to(tl.float32)    # [BLOCK]

        v_hi_dq = v_hi * v_scale_tok[:, None] + v_zp_tok[:, None]  # [BLOCK, PD]
        v_lo_dq = v_lo * v_scale_tok[:, None] + v_zp_tok[:, None]  # [BLOCK, PD]

        # Accumulate: weighted sum by softmax weights
        wv_even = tl.sum(beta[:, None] * v_hi_dq, axis=0)  # [PD]
        wv_odd = tl.sum(beta[:, None] * v_lo_dq, axis=0)   # [PD]
        acc_even = acc_even * alpha + wv_even
        acc_odd = acc_odd * alpha + wv_odd

        l_i = l_ij
        m_i = m_ij

    # --- Finalize ---
    acc_even = acc_even / l_i  # [PD]
    acc_odd = acc_odd / l_i    # [PD]

    # --- Store: interleave even/odd back to full HEAD_DIM ---
    o_ptr = Output_ptr + batch_id * stride_o_b + head_id * stride_o_h
    tl.store(o_ptr + offs_even * stride_o_d, acc_even.to(tl.float16))
    tl.store(o_ptr + offs_odd * stride_o_d, acc_odd.to(tl.float16))


def decode_attn_int4_asym(
    q: torch.Tensor,
    k_cache_packed: torch.Tensor,
    v_cache_packed: torch.Tensor,
    k_scale: torch.Tensor,
    k_zp: torch.Tensor,
    v_scale: torch.Tensor,
    v_zp: torch.Tensor,
    context_lens: torch.Tensor,
    sm_scale: float | None = None,
    block_size: int | None = None,
) -> torch.Tensor:
    """
    INT4 asymmetric decode attention with in-kernel unpacking.

    Args:
        q: [B, Hq, D] fp16
        k_cache_packed: [B, Hkv, S, D//2] int8 (bit-packed, +8 offset)
        v_cache_packed: [B, Hkv, S, D//2] int8
        k_scale: [B, Hkv, D] per-channel K scale (float32 or fp16)
        k_zp: [B, Hkv, D] per-channel K zero point
        v_scale: [B, Hkv, S] per-token V scale
        v_zp: [B, Hkv, S] per-token V zero point
        context_lens: [B] int32
        sm_scale: 1/sqrt(D), auto-computed if None
        block_size: Triton block size (32/64/128/256)

    Returns:
        [B, Hq, D] fp16
    """
    if sm_scale is None:
        sm_scale = 1.0 / (q.shape[-1] ** 0.5)

    if q.ndim != 3:
        raise ValueError(f"q must be [B, Hq, D], got {tuple(q.shape)}")
    if k_cache_packed.ndim != 4 or v_cache_packed.ndim != 4:
        raise ValueError(
            f"cache must be [B, Hkv, S, D//2], got K={tuple(k_cache_packed.shape)} V={tuple(v_cache_packed.shape)}"
        )
    if k_scale.ndim != 3 or k_zp.ndim != 3:
        raise ValueError(f"k_scale/k_zp must be [B, Hkv, D], got {tuple(k_scale.shape)}/{tuple(k_zp.shape)}")
    if v_scale.ndim != 3 or v_zp.ndim != 3:
        raise ValueError(f"v_scale/v_zp must be [B, Hkv, S], got {tuple(v_scale.shape)}/{tuple(v_zp.shape)}")
    if not q.is_cuda:
        raise ValueError("Requires CUDA tensors")

    batch, q_heads, head_dim = q.shape
    kv_heads = k_cache_packed.shape[1]
    packed_dim = k_cache_packed.shape[-1]

    if packed_dim * 2 != head_dim:
        raise ValueError(f"packed_dim={packed_dim} * 2 != head_dim={head_dim}")
    if head_dim == 0 or (head_dim & (head_dim - 1)) != 0:
        raise ValueError(f"HEAD_DIM must be power of 2, got {head_dim}")
    if q_heads % kv_heads != 0:
        raise ValueError(f"q_heads={q_heads} not multiple of kv_heads={kv_heads}")

    n_rep = q_heads // kv_heads
    max_ctx = int(context_lens.max().item())

    if max_ctx == 0:
        return torch.zeros_like(q)

    # P2 fix: Keep scale/zp in fp32 for precision (asymmetric per-token V scales
    # can be very small; fp16 would round them to zero). Kernel loads as tl.float32.
    if k_scale.dtype != torch.float32:
        k_scale = k_scale.to(torch.float32)
    if k_zp.dtype != torch.float32:
        k_zp = k_zp.to(torch.float32)
    if v_scale.dtype != torch.float32:
        v_scale = v_scale.to(torch.float32)
    if v_zp.dtype != torch.float32:
        v_zp = v_zp.to(torch.float32)

    original_dtype = q.dtype
    if original_dtype != torch.float16:
        q = q.to(torch.float16)

    output = torch.empty_like(q)

    if block_size is None:
        block_size = 128 if max_ctx >= 8192 else 64
    if block_size not in (32, 64, 128, 256):
        raise ValueError(f"Unsupported block_size={block_size}")

    grid = (batch, q_heads)

    decode_attn_int4_asym_kernel[grid](
        q, k_cache_packed, v_cache_packed,
        k_scale, k_zp, v_scale, v_zp,
        context_lens, output, sm_scale,
        q.stride(0), q.stride(1), q.stride(2),
        k_cache_packed.stride(0), k_cache_packed.stride(1),
        k_cache_packed.stride(2), k_cache_packed.stride(3),
        v_cache_packed.stride(0), v_cache_packed.stride(1),
        v_cache_packed.stride(2), v_cache_packed.stride(3),
        k_scale.stride(0), k_scale.stride(1), k_scale.stride(2),
        k_zp.stride(0), k_zp.stride(1), k_zp.stride(2),
        v_scale.stride(0), v_scale.stride(1), v_scale.stride(2),
        v_zp.stride(0), v_zp.stride(1), v_zp.stride(2),
        output.stride(0), output.stride(1), output.stride(2),
        HEAD_DIM=head_dim,
        PACKED_DIM=packed_dim,
        BLOCK_SIZE=block_size,
        N_REP=n_rep,
    )

    min_ctx = int(context_lens.min().item())
    if min_ctx == 0:
        output[context_lens == 0] = 0.0

    if original_dtype != torch.float16:
        output = output.to(original_dtype)

    return output
