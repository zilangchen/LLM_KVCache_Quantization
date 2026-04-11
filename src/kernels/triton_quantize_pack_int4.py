"""
Fused Triton kernels for INT4 quantize + pack.

Replaces the chain of ~12 PyTorch eager ops (float → quantize → clamp →
cast → shift → pack) with a single Triton kernel, reducing CUDA launch
overhead from ~12 launches to 1 per (K or V) per layer.

For 28-layer decode: 28 × 2 × ~12 = 672 launches → 28 × 2 = 56 launches.
"""

from __future__ import annotations

import torch
import triton
import triton.language as tl


@triton.jit
def _fused_quantize_pack_k_int4_kernel(
    K_ptr,          # [B, H, 1, D] float16 input
    K_Scale_ptr,    # [B, H, D] float32 per-channel scale
    K_ZP_ptr,       # [B, H, D] float32 per-channel zero-point
    K_Packed_ptr,   # [B, H, 1, D//2] int8 output
    stride_k_b, stride_k_h, stride_k_s, stride_k_d,
    stride_ks_b, stride_ks_h, stride_ks_d,
    stride_kz_b, stride_kz_h, stride_kz_d,
    stride_kp_b, stride_kp_h, stride_kp_s, stride_kp_d,
    PACKED_DIM: tl.constexpr,
):
    """Fused K quantize + pack: one block per (batch, head)."""
    batch_id = tl.program_id(0)
    head_id = tl.program_id(1)

    offs_pd = tl.arange(0, PACKED_DIM)
    offs_even = offs_pd * 2        # [0, 2, 4, ...]
    offs_odd = offs_pd * 2 + 1     # [1, 3, 5, ...]

    # Load float K for even/odd channels
    k_base = K_ptr + batch_id * stride_k_b + head_id * stride_k_h
    k_even = tl.load(k_base + offs_even * stride_k_d).to(tl.float32)
    k_odd = tl.load(k_base + offs_odd * stride_k_d).to(tl.float32)

    # Load per-channel scale/zp
    ks_base = K_Scale_ptr + batch_id * stride_ks_b + head_id * stride_ks_h
    kz_base = K_ZP_ptr + batch_id * stride_kz_b + head_id * stride_kz_h
    s_even = tl.load(ks_base + offs_even * stride_ks_d)
    s_odd = tl.load(ks_base + offs_odd * stride_ks_d)
    z_even = tl.load(kz_base + offs_even * stride_kz_d)
    z_odd = tl.load(kz_base + offs_odd * stride_kz_d)

    # Quantize: round((k - zp) / scale).clamp(-8, 7) + 8 → [0, 15]
    q_even = tl.extra.cuda.libdevice.rint((k_even - z_even) / s_even)
    q_even = tl.minimum(tl.maximum(q_even, -8.0), 7.0) + 8.0
    q_odd = tl.extra.cuda.libdevice.rint((k_odd - z_odd) / s_odd)
    q_odd = tl.minimum(tl.maximum(q_odd, -8.0), 7.0) + 8.0

    # Pack: hi nibble = even, lo nibble = odd
    packed = (q_even.to(tl.uint8) << 4) | q_odd.to(tl.uint8)

    # Store packed [D//2]
    kp_base = K_Packed_ptr + batch_id * stride_kp_b + head_id * stride_kp_h
    tl.store(kp_base + offs_pd * stride_kp_d, packed.to(tl.int8))


@triton.jit
def _fused_quantize_pack_v_int4_kernel(
    V_ptr,          # [B, H, 1, D] float16 input
    V_Packed_ptr,   # [B, H, 1, D//2] int8 output
    V_Scale_ptr,    # [B, H, 1] float32 output (per-token scale)
    V_ZP_ptr,       # [B, H, 1] float32 output (per-token zero-point)
    stride_v_b, stride_v_h, stride_v_s, stride_v_d,
    stride_vp_b, stride_vp_h, stride_vp_s, stride_vp_d,
    stride_vs_b, stride_vs_h, stride_vs_s,
    stride_vz_b, stride_vz_h, stride_vz_s,
    PACKED_DIM: tl.constexpr,
    HEAD_DIM: tl.constexpr,
    RANGE_FLOOR: tl.constexpr,
):
    """Fused V quantize + pack: one block per (batch, head). Computes per-token scale/zp."""
    batch_id = tl.program_id(0)
    head_id = tl.program_id(1)

    offs_pd = tl.arange(0, PACKED_DIM)
    offs_even = offs_pd * 2
    offs_odd = offs_pd * 2 + 1

    # Load float V as even/odd channels (avoids gather indexing)
    v_base = V_ptr + batch_id * stride_v_b + head_id * stride_v_h
    v_even = tl.load(v_base + offs_even * stride_v_d).to(tl.float32)  # [PD]
    v_odd = tl.load(v_base + offs_odd * stride_v_d).to(tl.float32)    # [PD]

    # Compute per-token min/max from both halves
    v_min = tl.minimum(tl.min(v_even, axis=0), tl.min(v_odd, axis=0))
    v_max = tl.maximum(tl.max(v_even, axis=0), tl.max(v_odd, axis=0))
    range_val = tl.maximum(v_max - v_min, RANGE_FLOOR)
    scale = range_val / 15.0   # qmax - qmin = 7 - (-8) = 15
    zp = v_min + 8.0 * scale   # = v_min - qmin * scale, qmin = -8

    # Quantize even/odd separately
    q_even = tl.extra.cuda.libdevice.rint((v_even - zp) / scale)
    q_even = tl.minimum(tl.maximum(q_even, -8.0), 7.0) + 8.0
    q_odd = tl.extra.cuda.libdevice.rint((v_odd - zp) / scale)
    q_odd = tl.minimum(tl.maximum(q_odd, -8.0), 7.0) + 8.0

    # Pack: hi nibble = even, lo nibble = odd
    packed = (q_even.to(tl.uint8) << 4) | q_odd.to(tl.uint8)

    # Store packed [D//2]
    vp_base = V_Packed_ptr + batch_id * stride_vp_b + head_id * stride_vp_h
    tl.store(vp_base + offs_pd * stride_vp_d, packed.to(tl.int8))

    # Store scale/zp [1]
    vs_base = V_Scale_ptr + batch_id * stride_vs_b + head_id * stride_vs_h
    vz_base = V_ZP_ptr + batch_id * stride_vz_b + head_id * stride_vz_h
    tl.store(vs_base, scale)
    tl.store(vz_base, zp)


def fused_quantize_pack_k_int4(
    k: torch.Tensor,
    k_scale: torch.Tensor,
    k_zp: torch.Tensor,
) -> torch.Tensor:
    """
    Fused K quantize + pack in a single Triton kernel.

    Args:
        k: [B, H, 1, D] float16 (single decode token)
        k_scale: [B, H, D] float32 per-channel scale
        k_zp: [B, H, D] float32 per-channel zero-point

    Returns:
        k_packed: [B, H, 1, D//2] int8 (bit-packed INT4)
    """
    batch, heads, seq_len, head_dim = k.shape
    assert seq_len == 1, f"fused K quant+pack only for decode (seq_len=1), got {seq_len}"
    packed_dim = head_dim // 2

    k_packed = torch.empty(batch, heads, 1, packed_dim, device=k.device, dtype=torch.int8)

    grid = (batch, heads)
    _fused_quantize_pack_k_int4_kernel[grid](
        k, k_scale, k_zp, k_packed,
        k.stride(0), k.stride(1), k.stride(2), k.stride(3),
        k_scale.stride(0), k_scale.stride(1), k_scale.stride(2),
        k_zp.stride(0), k_zp.stride(1), k_zp.stride(2),
        k_packed.stride(0), k_packed.stride(1), k_packed.stride(2), k_packed.stride(3),
        PACKED_DIM=packed_dim,
    )
    return k_packed


def fused_quantize_pack_v_int4(
    v: torch.Tensor,
    v_scale_buf: torch.Tensor,
    v_zp_buf: torch.Tensor,
    write_idx: int,
) -> torch.Tensor:
    """
    Fused V quantize + pack in a single Triton kernel.

    Args:
        v: [B, H, 1, D] float16 (single decode token)
        v_scale_buf: [B, H, S] float32 — pre-allocated scale buffer (writes to [:,:,write_idx])
        v_zp_buf: [B, H, S] float32 — pre-allocated zp buffer
        write_idx: token index to write scale/zp

    Returns:
        v_packed: [B, H, 1, D//2] int8 (bit-packed INT4)
        (scale/zp written directly to buffers)
    """
    batch, heads, seq_len, head_dim = v.shape
    assert seq_len == 1, f"fused V quant+pack only for decode (seq_len=1), got {seq_len}"
    packed_dim = head_dim // 2

    v_packed = torch.empty(batch, heads, 1, packed_dim, device=v.device, dtype=torch.int8)

    # Slice scale/zp buffers to the write position
    v_scale_out = v_scale_buf[:, :, write_idx:write_idx+1]  # [B, H, 1]
    v_zp_out = v_zp_buf[:, :, write_idx:write_idx+1]

    _fp16_tiny = torch.finfo(torch.float16).tiny
    range_floor = max(1e-5, _fp16_tiny * 15)  # 15 = qmax - qmin

    grid = (batch, heads)
    _fused_quantize_pack_v_int4_kernel[grid](
        v, v_packed, v_scale_out, v_zp_out,
        v.stride(0), v.stride(1), v.stride(2), v.stride(3),
        v_packed.stride(0), v_packed.stride(1), v_packed.stride(2), v_packed.stride(3),
        v_scale_out.stride(0), v_scale_out.stride(1), v_scale_out.stride(2),
        v_zp_out.stride(0), v_zp_out.stride(1), v_zp_out.stride(2),
        PACKED_DIM=packed_dim,
        HEAD_DIM=head_dim,
        RANGE_FLOOR=range_floor,
    )
    return v_packed


def fused_quantize_pack_v_int4_simple(
    v: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Fused V quantize + pack returning (packed, scale, zp).

    Simpler interface for cache append integration — allocates scale/zp
    tensors internally instead of writing to pre-allocated buffers.

    Args:
        v: [B, H, 1, D] float16

    Returns:
        (v_packed [B,H,1,D//2] int8, v_scale [B,H,1] fp32, v_zp [B,H,1] fp32)
    """
    batch, heads, seq_len, head_dim = v.shape
    assert seq_len == 1
    packed_dim = head_dim // 2

    v_packed = torch.empty(batch, heads, 1, packed_dim, device=v.device, dtype=torch.int8)
    v_scale = torch.empty(batch, heads, 1, device=v.device, dtype=torch.float32)
    v_zp = torch.empty(batch, heads, 1, device=v.device, dtype=torch.float32)

    _fp16_tiny = torch.finfo(torch.float16).tiny
    range_floor = max(1e-5, _fp16_tiny * 15)

    grid = (batch, heads)
    _fused_quantize_pack_v_int4_kernel[grid](
        v, v_packed, v_scale, v_zp,
        v.stride(0), v.stride(1), v.stride(2), v.stride(3),
        v_packed.stride(0), v_packed.stride(1), v_packed.stride(2), v_packed.stride(3),
        v_scale.stride(0), v_scale.stride(1), v_scale.stride(2),
        v_zp.stride(0), v_zp.stride(1), v_zp.stride(2),
        PACKED_DIM=packed_dim,
        HEAD_DIM=head_dim,
        RANGE_FLOOR=range_floor,
    )
    # Return scale/zp as [B, H, 1] — matching quantize_asymmetric_per_token output
    return v_packed, v_scale, v_zp


# ---------------------------------------------------------------------------
# Inplace variants: write directly to cache buffers (zero-copy, zero-alloc)
# ---------------------------------------------------------------------------

def fused_quantize_pack_k_int4_inplace(
    k: torch.Tensor,
    k_scale: torch.Tensor,
    k_zp: torch.Tensor,
    k_cache: torch.Tensor,
    write_offset: int,
) -> None:
    """Write quantized+packed K directly to cache buffer at write_offset."""
    batch, heads, _, head_dim = k.shape
    packed_dim = head_dim // 2
    # Slice the cache at the write position: [B, H, 1, D//2]
    k_out = k_cache[:, :, write_offset:write_offset + 1, :]
    grid = (batch, heads)
    _fused_quantize_pack_k_int4_kernel[grid](
        k, k_scale, k_zp, k_out,
        k.stride(0), k.stride(1), k.stride(2), k.stride(3),
        k_scale.stride(0), k_scale.stride(1), k_scale.stride(2),
        k_zp.stride(0), k_zp.stride(1), k_zp.stride(2),
        k_out.stride(0), k_out.stride(1), k_out.stride(2), k_out.stride(3),
        PACKED_DIM=packed_dim,
    )


@triton.jit
def _fused_quantize_pack_v_int4_with_bounds_kernel(
    V_ptr,          # [B, H, 1, D] float16
    V_min_ptr,      # [B, H, 1, 1] float32 (precomputed quantile lower bound)
    V_max_ptr,      # [B, H, 1, 1] float32 (precomputed quantile upper bound)
    V_Packed_ptr,   # [B, H, 1, D//2] int8 output
    V_Scale_ptr,    # [B, H, 1] float32 output
    V_ZP_ptr,       # [B, H, 1] float32 output
    stride_v_b, stride_v_h, stride_v_s, stride_v_d,
    stride_vmin_b, stride_vmin_h,
    stride_vmax_b, stride_vmax_h,
    stride_vp_b, stride_vp_h, stride_vp_s, stride_vp_d,
    stride_vs_b, stride_vs_h, stride_vs_s,
    stride_vz_b, stride_vz_h, stride_vz_s,
    PACKED_DIM: tl.constexpr,
    RANGE_FLOOR: tl.constexpr,
):
    """V quantize + pack with externally precomputed bounds (e.g. percentile)."""
    batch_id = tl.program_id(0)
    head_id = tl.program_id(1)

    offs_pd = tl.arange(0, PACKED_DIM)
    offs_even = offs_pd * 2
    offs_odd = offs_pd * 2 + 1

    # Load V even/odd channels
    v_base = V_ptr + batch_id * stride_v_b + head_id * stride_v_h
    v_even = tl.load(v_base + offs_even * stride_v_d).to(tl.float32)
    v_odd = tl.load(v_base + offs_odd * stride_v_d).to(tl.float32)

    # Load precomputed bounds (scalar per (batch, head))
    v_min = tl.load(V_min_ptr + batch_id * stride_vmin_b + head_id * stride_vmin_h)
    v_max = tl.load(V_max_ptr + batch_id * stride_vmax_b + head_id * stride_vmax_h)

    range_val = tl.maximum(v_max - v_min, RANGE_FLOOR)
    scale = range_val / 15.0
    zp = v_min + 8.0 * scale  # = v_min - qmin * scale, qmin = -8

    # Quantize
    q_even = tl.extra.cuda.libdevice.rint((v_even - zp) / scale)
    q_even = tl.minimum(tl.maximum(q_even, -8.0), 7.0) + 8.0
    q_odd = tl.extra.cuda.libdevice.rint((v_odd - zp) / scale)
    q_odd = tl.minimum(tl.maximum(q_odd, -8.0), 7.0) + 8.0

    packed = (q_even.to(tl.uint8) << 4) | q_odd.to(tl.uint8)

    vp_base = V_Packed_ptr + batch_id * stride_vp_b + head_id * stride_vp_h
    tl.store(vp_base + offs_pd * stride_vp_d, packed.to(tl.int8))

    vs_base = V_Scale_ptr + batch_id * stride_vs_b + head_id * stride_vs_h
    vz_base = V_ZP_ptr + batch_id * stride_vz_b + head_id * stride_vz_h
    tl.store(vs_base, scale)
    tl.store(vz_base, zp)


def fused_quantize_pack_v_int4_with_bounds(
    v: torch.Tensor,
    t_min: torch.Tensor,
    t_max: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Fused V quantize+pack using precomputed bounds (percentile-aware).

    Args:
        v: [B, H, 1, D] float16
        t_min: [B, H, 1, 1] float32 (e.g. from torch.quantile)
        t_max: [B, H, 1, 1] float32

    Returns:
        (v_packed [B,H,1,D//2] int8, v_scale [B,H,1] fp32, v_zp [B,H,1] fp32)
    """
    batch, heads, seq_len, head_dim = v.shape
    assert seq_len == 1
    packed_dim = head_dim // 2

    v_packed = torch.empty(batch, heads, 1, packed_dim, device=v.device, dtype=torch.int8)
    v_scale = torch.empty(batch, heads, 1, device=v.device, dtype=torch.float32)
    v_zp = torch.empty(batch, heads, 1, device=v.device, dtype=torch.float32)

    _fp16_tiny = torch.finfo(torch.float16).tiny
    range_floor = max(1e-5, _fp16_tiny * 15)

    grid = (batch, heads)
    _fused_quantize_pack_v_int4_with_bounds_kernel[grid](
        v, t_min, t_max, v_packed, v_scale, v_zp,
        v.stride(0), v.stride(1), v.stride(2), v.stride(3),
        t_min.stride(0), t_min.stride(1),
        t_max.stride(0), t_max.stride(1),
        v_packed.stride(0), v_packed.stride(1), v_packed.stride(2), v_packed.stride(3),
        v_scale.stride(0), v_scale.stride(1), v_scale.stride(2),
        v_zp.stride(0), v_zp.stride(1), v_zp.stride(2),
        PACKED_DIM=packed_dim,
        RANGE_FLOOR=range_floor,
    )
    return v_packed, v_scale, v_zp


def fused_quantize_pack_v_int4_inplace(
    v: torch.Tensor,
    v_cache: torch.Tensor,
    v_scale_buf: torch.Tensor,
    v_zp_buf: torch.Tensor,
    write_offset: int,
) -> None:
    """Write quantized+packed V + scale/zp directly to cache buffers."""
    batch, heads, _, head_dim = v.shape
    packed_dim = head_dim // 2
    v_out = v_cache[:, :, write_offset:write_offset + 1, :]
    vs_out = v_scale_buf[:, :, write_offset:write_offset + 1]
    vz_out = v_zp_buf[:, :, write_offset:write_offset + 1]

    _fp16_tiny = torch.finfo(torch.float16).tiny
    range_floor = max(1e-5, _fp16_tiny * 15)

    grid = (batch, heads)
    _fused_quantize_pack_v_int4_kernel[grid](
        v, v_out, vs_out, vz_out,
        v.stride(0), v.stride(1), v.stride(2), v.stride(3),
        v_out.stride(0), v_out.stride(1), v_out.stride(2), v_out.stride(3),
        vs_out.stride(0), vs_out.stride(1), vs_out.stride(2),
        vz_out.stride(0), vz_out.stride(1), vz_out.stride(2),
        PACKED_DIM=packed_dim,
        HEAD_DIM=head_dim,
        RANGE_FLOOR=range_floor,
    )
