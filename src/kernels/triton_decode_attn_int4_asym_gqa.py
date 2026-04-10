"""
INT4 Asymmetric Fused Decode Attention Kernel with GQA-Aware Tiling.

Key optimization: grid=(batch, kv_heads) instead of (batch, q_heads).
Each thread block loads K/V cache ONCE and processes all N_REP query heads
that share the same KV head, reducing HBM reads by N_REP×.

Qwen2.5-1.5B:  N_REP=6 → 6× fewer HBM reads
Qwen2.5-7B:    N_REP=7 → 7× fewer HBM reads
LLaMA-3.1-8B:  N_REP=4 → 4× fewer HBM reads

Also includes v2 optimizations:
  - K zero-point precomputation (q_scaled + zp_bias)
  - @triton.autotune over BLOCK_SIZE × num_warps × num_stages

Same quantization format:
  K: per-channel scale/zp [B, H, D]
  V: per-token  scale/zp [B, H, S]
  Cache: bit-packed INT4 [B, H, S, D//2] with +8 offset

Supported modes: int4_ours_asym, int4_ours_asym_ba.
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
def decode_attn_int4_asym_gqa_kernel(
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
    # Autotune key
    ctx_len_rounded,
    # Constexprs
    HEAD_DIM: tl.constexpr,
    PACKED_DIM: tl.constexpr,
    BLOCK_SIZE: tl.constexpr,
    N_REP: tl.constexpr,        # q_heads // kv_heads
):
    batch_id = tl.program_id(0)
    # GQA change: grid over kv_heads, not q_heads
    kv_head_id = tl.program_id(1)
    q_head_start = kv_head_id * N_REP

    offs_pd = tl.arange(0, PACKED_DIM)
    offs_even = offs_pd * 2
    offs_odd = offs_pd * 2 + 1

    # --- Load K per-channel scale/zp (shared by all N_REP Q heads) ---
    ks_base = K_Scale_ptr + batch_id * stride_ks_b + kv_head_id * stride_ks_h
    kz_base = K_ZP_ptr + batch_id * stride_kz_b + kv_head_id * stride_kz_h
    ks_even = tl.load(ks_base + offs_even * stride_ks_d).to(tl.float32)  # [PD]
    ks_odd = tl.load(ks_base + offs_odd * stride_ks_d).to(tl.float32)
    kz_even = tl.load(kz_base + offs_even * stride_kz_d).to(tl.float32)
    kz_odd = tl.load(kz_base + offs_odd * stride_kz_d).to(tl.float32)

    # --- Load all N_REP Q vectors as 2D [N_REP, PD] ---
    q_head_offs = tl.arange(0, N_REP)  # [N_REP]
    q_ptrs_even = (Q_ptr + batch_id * stride_q_b
                   + (q_head_start + q_head_offs[:, None]) * stride_q_h
                   + offs_even[None, :] * stride_q_d)
    q_ptrs_odd = (Q_ptr + batch_id * stride_q_b
                  + (q_head_start + q_head_offs[:, None]) * stride_q_h
                  + offs_odd[None, :] * stride_q_d)
    q_even_all = tl.load(q_ptrs_even).to(tl.float32)  # [N_REP, PD]
    q_odd_all = tl.load(q_ptrs_odd).to(tl.float32)    # [N_REP, PD]

    # --- Precompute q_scaled and zp_bias for all Q heads ---
    q_scaled_even_all = q_even_all * ks_even[None, :]  # [N_REP, PD]
    q_scaled_odd_all = q_odd_all * ks_odd[None, :]     # [N_REP, PD]
    zp_bias_all = (tl.sum(q_even_all * kz_even[None, :], axis=1)
                   + tl.sum(q_odd_all * kz_odd[None, :], axis=1))  # [N_REP]

    ctx_len = tl.load(Context_Lens_ptr + batch_id)

    # KV base pointers (same for all N_REP Q heads)
    k_base = K_ptr + batch_id * stride_k_b + kv_head_id * stride_k_h
    v_base = V_ptr + batch_id * stride_v_b + kv_head_id * stride_v_h
    vs_base = V_Scale_ptr + batch_id * stride_vs_b + kv_head_id * stride_vs_h
    vz_base = V_ZP_ptr + batch_id * stride_vz_b + kv_head_id * stride_vz_h

    # --- 2D accumulators for all N_REP heads ---
    acc_even_all = tl.zeros([N_REP, PACKED_DIM], dtype=tl.float32)
    acc_odd_all = tl.zeros([N_REP, PACKED_DIM], dtype=tl.float32)
    m_all = tl.full([N_REP], -float("inf"), dtype=tl.float32)
    l_all = tl.zeros([N_REP], dtype=tl.float32)

    for start_n in range(0, ctx_len, BLOCK_SIZE):
        offs_n = start_n + tl.arange(0, BLOCK_SIZE)
        mask = offs_n < ctx_len

        # === K: Load packed, unpack — ONCE per block ===
        k_ptrs = k_base + offs_n[:, None] * stride_k_s + offs_pd[None, :] * stride_k_pd
        k_packed = tl.load(k_ptrs, mask=mask[:, None], other=0).to(tl.uint8)
        k_hi = ((k_packed >> 4) & 0x0F).to(tl.float32) - 8.0  # [BLOCK, PD]
        k_lo = (k_packed & 0x0F).to(tl.float32) - 8.0          # [BLOCK, PD]

        # === QK for ALL N_REP heads (3D broadcast → 2D reduce) ===
        # [N_REP, 1, PD] × [1, BLOCK, PD] → sum(axis=2) → [N_REP, BLOCK]
        qk_even = tl.sum(q_scaled_even_all[:, None, :] * k_hi[None, :, :], axis=2)
        qk_odd = tl.sum(q_scaled_odd_all[:, None, :] * k_lo[None, :, :], axis=2)
        qk_all = (qk_even + qk_odd + zp_bias_all[:, None]) * sm_scale  # [N_REP, BLOCK]
        qk_all = tl.where(mask[None, :], qk_all, float("-inf"))

        # === Online softmax (all 2D) ===
        m_new = tl.max(qk_all, axis=1)              # [N_REP]
        m_ij = tl.maximum(m_all, m_new)              # [N_REP]
        alpha_all = tl.exp(m_all - m_ij)             # [N_REP]
        beta_all = tl.exp(qk_all - m_ij[:, None])   # [N_REP, BLOCK]
        l_ij = l_all * alpha_all + tl.sum(beta_all, axis=1)  # [N_REP]

        # === V: Load packed, unpack, dequant — ONCE per block ===
        v_ptrs = v_base + offs_n[:, None] * stride_v_s + offs_pd[None, :] * stride_v_pd
        v_packed = tl.load(v_ptrs, mask=mask[:, None], other=0).to(tl.uint8)
        v_hi = ((v_packed >> 4) & 0x0F).to(tl.float32) - 8.0
        v_lo = (v_packed & 0x0F).to(tl.float32) - 8.0

        v_scale_tok = tl.load(vs_base + offs_n * stride_vs_s,
                              mask=mask, other=1.0).to(tl.float32)
        v_zp_tok = tl.load(vz_base + offs_n * stride_vz_s,
                           mask=mask, other=0.0).to(tl.float32)

        v_hi_dq = v_hi * v_scale_tok[:, None] + v_zp_tok[:, None]  # [BLOCK, PD]
        v_lo_dq = v_lo * v_scale_tok[:, None] + v_zp_tok[:, None]

        # === V accumulation for ALL heads (3D broadcast → 2D reduce) ===
        # [N_REP, BLOCK, 1] × [1, BLOCK, PD] → sum(axis=1) → [N_REP, PD]
        wv_even = tl.sum(beta_all[:, :, None] * v_hi_dq[None, :, :], axis=1)
        wv_odd = tl.sum(beta_all[:, :, None] * v_lo_dq[None, :, :], axis=1)

        acc_even_all = acc_even_all * alpha_all[:, None] + wv_even
        acc_odd_all = acc_odd_all * alpha_all[:, None] + wv_odd

        l_all = l_ij
        m_all = m_ij

    # --- Finalize ---
    acc_even_all = acc_even_all / l_all[:, None]
    acc_odd_all = acc_odd_all / l_all[:, None]

    # --- Store: write N_REP Q heads ---
    for qr in tl.static_range(N_REP):
        o_ptr = (Output_ptr + batch_id * stride_o_b
                 + (q_head_start + qr) * stride_o_h)
        tl.store(o_ptr + offs_even * stride_o_d,
                 acc_even_all[qr, :].to(tl.float16))
        tl.store(o_ptr + offs_odd * stride_o_d,
                 acc_odd_all[qr, :].to(tl.float16))


def decode_attn_int4_asym_gqa(
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
    INT4 asymmetric decode attention with GQA-aware tiling.

    Grid is (batch, kv_heads) instead of (batch, q_heads). Each block
    processes N_REP query heads sharing one KV head, loading KV data
    only once. This reduces HBM reads by N_REP× (4-7× for target models).

    Args/Returns: identical to v1/v2 decode_attn_int4_asym.
    """
    if sm_scale is None:
        sm_scale = 1.0 / (q.shape[-1] ** 0.5)

    if q.ndim != 3:
        raise ValueError(f"q must be [B, Hq, D], got {tuple(q.shape)}")
    if k_cache_packed.ndim != 4 or v_cache_packed.ndim != 4:
        raise ValueError(
            f"cache must be [B, Hkv, S, D//2], got K={tuple(k_cache_packed.shape)} "
            f"V={tuple(v_cache_packed.shape)}"
        )
    if k_scale.ndim != 3 or k_zp.ndim != 3:
        raise ValueError(
            f"k_scale/k_zp must be [B, Hkv, D], got "
            f"{tuple(k_scale.shape)}/{tuple(k_zp.shape)}"
        )
    if v_scale.ndim != 3 or v_zp.ndim != 3:
        raise ValueError(
            f"v_scale/v_zp must be [B, Hkv, S], got "
            f"{tuple(v_scale.shape)}/{tuple(v_zp.shape)}"
        )
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

    ctx_len_rounded = ((max_ctx + 63) // 64) * 64

    # GQA: grid over kv_heads, not q_heads
    grid = (batch, kv_heads)

    decode_attn_int4_asym_gqa_kernel[grid](
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
