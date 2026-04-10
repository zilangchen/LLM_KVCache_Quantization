"""
INT4 Asymmetric Fused Decode Attention Kernel v2 using Triton.

Improvements over v1 (triton_decode_attn_int4_asym.py):
  1. Removed unused full-Q load (v1 L67 loaded q_full but never used it)
  2. K zero-point precomputation: fuse q*scale outside loop, lift sum(q*zp)
     to a scalar bias — eliminates per-block K dequant multiply+add
  3. @triton.autotune: sweep BLOCK_SIZE x num_warps x num_stages
  4. V accumulation unchanged (per-token scale prevents loop extraction)

Same quantization format as v1:
  K: per-channel scale/zp [B, H, D] — shared across all tokens
  V: per-token  scale/zp [B, H, S] — shared across all channels
  Cache: bit-packed INT4 [B, H, S, D//2] with +8 offset
  Dequant: x_hat = (nibble - 8) * scale + zero_point

Supported modes: int4_ours_asym, int4_ours_asym_ba (NOT kivi_style).
"""

from __future__ import annotations

import os
from typing import Optional

import torch
import triton
import triton.language as tl


@triton.autotune(
    configs=[
        triton.Config({"BLOCK_SIZE": 32}, num_warps=2, num_stages=2),
        triton.Config({"BLOCK_SIZE": 32}, num_warps=4, num_stages=2),
        triton.Config({"BLOCK_SIZE": 64}, num_warps=2, num_stages=2),
        triton.Config({"BLOCK_SIZE": 64}, num_warps=4, num_stages=2),
        triton.Config({"BLOCK_SIZE": 128}, num_warps=4, num_stages=2),
        triton.Config({"BLOCK_SIZE": 128}, num_warps=8, num_stages=2),
    ],
    key=["ctx_len_rounded"],
)
@triton.jit
def decode_attn_int4_asym_v2_kernel(
    Q_ptr,              # [B, Hq, D] fp16
    K_ptr,              # [B, Hkv, S, D//2] packed int8
    V_ptr,              # [B, Hkv, S, D//2] packed int8
    K_Scale_ptr,        # [B, Hkv, D] fp32 per-channel
    K_ZP_ptr,           # [B, Hkv, D] fp32 per-channel
    V_Scale_ptr,        # [B, Hkv, S] fp32 per-token
    V_ZP_ptr,           # [B, Hkv, S] fp32 per-token
    Context_Lens_ptr,   # [B] int32
    Output_ptr,         # [B, Hq, D] fp16
    sm_scale,           # float
    # Q strides
    stride_q_b, stride_q_h, stride_q_d,
    # K packed strides
    stride_k_b, stride_k_h, stride_k_s, stride_k_pd,
    # V packed strides
    stride_v_b, stride_v_h, stride_v_s, stride_v_pd,
    # K scale strides
    stride_ks_b, stride_ks_h, stride_ks_d,
    # K zp strides
    stride_kz_b, stride_kz_h, stride_kz_d,
    # V scale strides
    stride_vs_b, stride_vs_h, stride_vs_s,
    # V zp strides
    stride_vz_b, stride_vz_h, stride_vz_s,
    # Output strides
    stride_o_b, stride_o_h, stride_o_d,
    # Autotune key (regular arg, not used in computation)
    ctx_len_rounded,
    # Constexprs
    HEAD_DIM: tl.constexpr,
    PACKED_DIM: tl.constexpr,   # = HEAD_DIM // 2
    BLOCK_SIZE: tl.constexpr,   # from autotune config
    N_REP: tl.constexpr,
):
    batch_id = tl.program_id(0)
    head_id = tl.program_id(1)
    kv_head_id = head_id // N_REP

    # --- Load Q: even/odd channels only (v1 had an unused full-Q load) ---
    q_ptr = Q_ptr + batch_id * stride_q_b + head_id * stride_q_h
    offs_pd = tl.arange(0, PACKED_DIM)
    # Pack layout: byte[i] -> hi=val[2i] (even), lo=val[2i+1] (odd)
    offs_even = offs_pd * 2        # [0, 2, 4, ...]
    offs_odd = offs_pd * 2 + 1     # [1, 3, 5, ...]
    q_even = tl.load(q_ptr + offs_even * stride_q_d).to(tl.float32)  # [PD]
    q_odd = tl.load(q_ptr + offs_odd * stride_q_d).to(tl.float32)    # [PD]

    # --- Load K per-channel scale/zp, split into even/odd ---
    ks_base = K_Scale_ptr + batch_id * stride_ks_b + kv_head_id * stride_ks_h
    kz_base = K_ZP_ptr + batch_id * stride_kz_b + kv_head_id * stride_kz_h
    ks_even = tl.load(ks_base + offs_even * stride_ks_d).to(tl.float32)
    ks_odd = tl.load(ks_base + offs_odd * stride_ks_d).to(tl.float32)
    kz_even = tl.load(kz_base + offs_even * stride_kz_d).to(tl.float32)
    kz_odd = tl.load(kz_base + offs_odd * stride_kz_d).to(tl.float32)

    # --- Optimization 2: Precompute q_scaled and zp_bias ---
    # Math: qk = sum(q * (k_int * scale + zp))
    #          = sum((q * scale) * k_int) + sum(q * zp)
    #          = sum(q_scaled * k_int) + zp_bias
    # This eliminates per-block K scale multiply + zp add (saves
    # 2 * BLOCK * PACKED_DIM muls + 2 * BLOCK * PACKED_DIM adds per iter).
    q_scaled_even = q_even * ks_even   # [PD]
    q_scaled_odd = q_odd * ks_odd      # [PD]
    zp_bias = tl.sum(q_even * kz_even) + tl.sum(q_odd * kz_odd)  # scalar

    ctx_len = tl.load(Context_Lens_ptr + batch_id)

    # KV base pointers
    k_base = K_ptr + batch_id * stride_k_b + kv_head_id * stride_k_h
    v_base = V_ptr + batch_id * stride_v_b + kv_head_id * stride_v_h
    vs_base = V_Scale_ptr + batch_id * stride_vs_b + kv_head_id * stride_vs_h
    vz_base = V_ZP_ptr + batch_id * stride_vz_b + kv_head_id * stride_vz_h

    # --- Online softmax accumulators ---
    m_i = -float("inf")
    l_i = 0.0
    # Split accumulator: even channels and odd channels
    acc_even = tl.zeros([PACKED_DIM], dtype=tl.float32)
    acc_odd = tl.zeros([PACKED_DIM], dtype=tl.float32)

    for start_n in range(0, ctx_len, BLOCK_SIZE):
        offs_n = start_n + tl.arange(0, BLOCK_SIZE)
        mask = offs_n < ctx_len

        # === K: Load packed [BLOCK, PD], unpack nibbles, dot with q_scaled ===
        k_ptrs = k_base + offs_n[:, None] * stride_k_s + offs_pd[None, :] * stride_k_pd
        k_packed = tl.load(k_ptrs, mask=mask[:, None], other=0).to(tl.uint8)

        # Unpack nibbles -> signed float (NO scale/zp application — precomputed)
        k_hi = ((k_packed >> 4) & 0x0F).to(tl.float32) - 8.0  # even [BLOCK, PD]
        k_lo = (k_packed & 0x0F).to(tl.float32) - 8.0          # odd  [BLOCK, PD]

        # QK = dot(q_scaled_even, k_hi) + dot(q_scaled_odd, k_lo) + zp_bias
        # KRN-v2-001: Using tl.sum(a*b) instead of tl.dot because M=1 (single
        # query token in decode) — tensor cores require M>=16.  Triton compiler
        # still generates efficient vectorized FMA for tl.sum(a*b, axis=1).
        qk = (tl.sum(q_scaled_even[None, :] * k_hi, axis=1)
              + tl.sum(q_scaled_odd[None, :] * k_lo, axis=1)
              + zp_bias) * sm_scale                             # [BLOCK]
        qk = tl.where(mask, qk, float("-inf"))

        # === Online Softmax ===
        m_i_new = tl.max(qk, 0)
        m_ij = tl.maximum(m_i, m_i_new)
        alpha = tl.exp(m_i - m_ij)
        beta = tl.exp(qk - m_ij)
        l_ij = l_i * alpha + tl.sum(beta, 0)

        # === V: Load packed, unpack, dequant (per-token — can't precompute) ===
        v_ptrs = v_base + offs_n[:, None] * stride_v_s + offs_pd[None, :] * stride_v_pd
        v_packed = tl.load(v_ptrs, mask=mask[:, None], other=0).to(tl.uint8)

        v_hi = ((v_packed >> 4) & 0x0F).to(tl.float32) - 8.0  # even channels
        v_lo = (v_packed & 0x0F).to(tl.float32) - 8.0          # odd channels

        # V per-token dequant (cannot be precomputed — scales vary per token)
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


def decode_attn_int4_asym_v2(
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
    INT4 asymmetric decode attention v2 with in-kernel unpacking.

    Optimizations over v1:
      1. Removed dead Q load
      2. K zero-point precomputed outside main loop
      3. @triton.autotune over BLOCK_SIZE x num_warps x num_stages

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
        block_size: Accepted for API compat with v1; ignored by autotune.

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

    # Keep scale/zp in fp32 for precision (asymmetric per-token V scales
    # can be very small; fp16 would round them to zero).
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

    # Autotune key: round max_ctx to 64-multiple to avoid per-token recompile
    ctx_len_rounded = ((max_ctx + 63) // 64) * 64

    grid = (batch, q_heads)

    decode_attn_int4_asym_v2_kernel[grid](
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
        ctx_len_rounded,
        HEAD_DIM=head_dim,
        PACKED_DIM=packed_dim,
        N_REP=n_rep,
    )

    min_ctx = int(context_lens.min().item())
    if min_ctx == 0:
        output[context_lens == 0] = 0.0

    if original_dtype != torch.float16:
        output = output.to(original_dtype)

    return output
