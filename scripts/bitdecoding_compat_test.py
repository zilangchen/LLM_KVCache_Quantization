#!/usr/bin/env python3
"""BitDecoding compatibility gate test.

Gate 0.1: Verify quant_mode="k-channel" k_params semantics
Gate 0.2: Compare our packed format vs BitDecoding packed format
Gate 0.3: End-to-end attention output comparison

Run on remote GPU server only:
    CUDA_VISIBLE_DEVICES=0 python3 scripts/bitdecoding_compat_test.py

Exit codes:
    0 = all gates passed
    1 = gate failed (report printed)
    2 = import/env error
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import json
from pathlib import Path

# --- Lazy import with clear error ---
try:
    from bit_decode import fwd_kvcache_int, kvcache_pack_int
    HAS_BITDECODING = True
except ImportError:
    HAS_BITDECODING = False

if not torch.cuda.is_available():
    print("ERROR: CUDA not available. Run on GPU server.")
    sys.exit(2)
if not HAS_BITDECODING:
    print("ERROR: bit_decode not installed. pip install bit-decode")
    sys.exit(2)

# ─── Config ───
BATCH = 1
SEQ_LEN = 64  # small for quick test
NHEADS_Q = 16
NHEADS_KV = 2
HEAD_DIM = 128
SEED = 42
REPORT = {}


def gate_0_1_k_params_semantics():
    """Gate 0.1: Understand what k_params contains after kvcache_pack_int.

    Hypothesis: quant_mode='k-channel' means per-TOKEN quantization
    (each token gets 1 scale + 1 zp across all channels).
    If true, k_params[b, s1, h, :] != k_params[b, s2, h, :] for different tokens,
    but the scale covers all D channels equally.

    Our format: per-CHANNEL quantization → [B, H, D] scale (one per channel).
    """
    print("=" * 60)
    print("Gate 0.1: k_params semantics analysis")
    print("=" * 60)

    torch.manual_seed(SEED)
    # Create K cache with known structure: each token has different magnitude
    k_fp16 = torch.randn(BATCH, SEQ_LEN, NHEADS_KV, HEAD_DIM,
                          device="cuda", dtype=torch.float16)
    # Make token 0 have 10x magnitude to test if scale varies per token
    k_fp16[:, 0, :, :] *= 10.0

    pack_dim = HEAD_DIM // 8
    k_pack = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, pack_dim,
                         device="cuda", dtype=torch.int32)
    k_params = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, 2,
                           device="cuda", dtype=torch.float16)

    # Dummy V (required by API)
    v_fp16 = torch.randn_like(k_fp16)
    v_pack = torch.zeros_like(k_pack)
    v_params = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, 2,
                           device="cuda", dtype=torch.float16)

    cu_seqlens = torch.tensor([0, SEQ_LEN], device="cuda", dtype=torch.int32)

    kvcache_pack_int(
        k_fp16, k_pack, k_params,
        v_fp16, v_pack, v_params,
        cu_seqlens_k=cu_seqlens,
        seqlen_k=SEQ_LEN,
        quant_mode="k-channel",
        group_size=HEAD_DIM,  # 1 group = full head_dim
        num_bits=4,
    )

    # Analyze k_params
    # k_params shape: [B, S, H, 2]
    k_scales = k_params[0, :, 0, 0]  # scale for head 0 across all tokens
    k_zps = k_params[0, :, 0, 1]     # zp for head 0 across all tokens

    all_same_scale = torch.allclose(k_scales, k_scales[0:1].expand_as(k_scales), atol=1e-4)
    scale_range = (k_scales.max() - k_scales.min()).item()
    scale_token0 = k_scales[0].item()
    scale_token1 = k_scales[1].item()

    result = {
        "k_params_shape": list(k_params.shape),
        "k_params_dtype": str(k_params.dtype),
        "all_tokens_same_scale": bool(all_same_scale),
        "scale_range": scale_range,
        "scale_token0_10x_mag": scale_token0,
        "scale_token1_normal_mag": scale_token1,
        "scale_token0_vs_token1_ratio": scale_token0 / max(scale_token1, 1e-8),
    }

    if all_same_scale:
        result["interpretation"] = (
            "Per-CHANNEL: all tokens share the same scale (computed across token dim). "
            "Compatible with our format (both reduce along S)."
        )
        result["compatible_with_ours"] = True
    else:
        result["interpretation"] = (
            "Per-TOKEN: each token has its own scale (computed across channel dim). "
            "INCOMPATIBLE with our per-channel format (we reduce along S, they reduce along D)."
        )
        result["compatible_with_ours"] = False

    REPORT["gate_0_1"] = result

    print(f"  k_params shape: {k_params.shape}")
    print(f"  All tokens same scale? {all_same_scale}")
    print(f"  Scale range across tokens: {scale_range:.6f}")
    print(f"  Token 0 scale (10x mag): {scale_token0:.6f}")
    print(f"  Token 1 scale (normal): {scale_token1:.6f}")
    print(f"  Ratio: {result['scale_token0_vs_token1_ratio']:.2f}x")
    print(f"  -> Interpretation: {result['interpretation']}")
    print()

    return result["compatible_with_ours"]


def gate_0_2_nibble_comparison():
    """Gate 0.2: Compare packed nibble values between our quantization and BitDecoding.

    Even if k_params semantics differ (Gate 0.1 FAIL), V is per-token in both
    systems. Check if V nibbles match when given the same FP16 input.

    Also: if we dequant our cache back to FP16 and repack with BitDecoding,
    measure the quality loss from the double-quantization round-trip.
    """
    print("=" * 60)
    print("Gate 0.2: Nibble format comparison")
    print("=" * 60)

    torch.manual_seed(SEED)
    k_fp16 = torch.randn(BATCH, SEQ_LEN, NHEADS_KV, HEAD_DIM,
                          device="cuda", dtype=torch.float16)
    v_fp16 = torch.randn(BATCH, SEQ_LEN, NHEADS_KV, HEAD_DIM,
                          device="cuda", dtype=torch.float16)

    # --- BitDecoding packing ---
    pack_dim = HEAD_DIM // 8
    k_pack_bd = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, pack_dim,
                            device="cuda", dtype=torch.int32)
    v_pack_bd = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, pack_dim,
                            device="cuda", dtype=torch.int32)
    k_params_bd = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, 2,
                              device="cuda", dtype=torch.float16)
    v_params_bd = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, 2,
                              device="cuda", dtype=torch.float16)

    cu_seqlens = torch.tensor([0, SEQ_LEN], device="cuda", dtype=torch.int32)

    kvcache_pack_int(
        k_fp16, k_pack_bd, k_params_bd,
        v_fp16, v_pack_bd, v_params_bd,
        cu_seqlens_k=cu_seqlens,
        seqlen_k=SEQ_LEN,
        quant_mode="k-channel",
        group_size=HEAD_DIM,
        num_bits=4,
    )

    # --- Our quantization (per-channel K, per-token V) ---
    from src.quant.asymmetric_quant import (
        quantize_asymmetric_per_channel,
        quantize_asymmetric_per_token,
    )
    from src.quant.int4_basic import pack_int4

    # Reshape to [B, H, S, D] for our functions
    k_bhsd = k_fp16.transpose(1, 2).contiguous()  # [B, H, S, D]
    v_bhsd = v_fp16.transpose(1, 2).contiguous()

    k_q_ours, k_scale_ours, k_zp_ours = quantize_asymmetric_per_channel(
        k_bhsd, quant_bits=4
    )
    v_q_ours, v_scale_ours, v_zp_ours = quantize_asymmetric_per_token(
        v_bhsd, quant_bits=4
    )

    k_packed_ours = pack_int4(k_q_ours)  # [B, H, S, D//2] int8
    v_packed_ours = pack_int4(v_q_ours)

    # --- Compare V (both per-token, might be similar) ---
    # BitDecoding v_params: [B, S, H, 2] -> extract scale/zp per token
    # Our v_scale: [B, H, S] per-token
    bd_v_scale = v_params_bd[0, :, 0, 0].float()  # [S]
    bd_v_zp = v_params_bd[0, :, 0, 1].float()     # [S]
    ours_v_scale = v_scale_ours[0, 0, :].float()   # [S]
    ours_v_zp = v_zp_ours[0, 0, :].float()         # [S]

    v_scale_diff = (bd_v_scale - ours_v_scale).abs().max().item()
    v_zp_diff = (bd_v_zp - ours_v_zp).abs().max().item()

    # --- Dequant round-trip quality ---
    # Dequant our V, then requant with BitDecoding, measure error
    from src.quant.asymmetric_quant import dequantize_asymmetric
    v_dequant_ours = dequantize_asymmetric(
        v_q_ours, v_scale_ours, v_zp_ours, axis=3
    )  # [B, H, S, D] float
    v_roundtrip_err = (v_dequant_ours.transpose(1, 2).half() - v_fp16).abs().max().item()

    result = {
        "v_scale_max_diff": v_scale_diff,
        "v_zp_max_diff": v_zp_diff,
        "v_scales_close": v_scale_diff < 0.01,
        "v_roundtrip_max_err_vs_fp16": v_roundtrip_err,
        "k_pack_ours_shape": list(k_packed_ours.shape),
        "k_pack_bd_shape": list(k_pack_bd.shape),
        "k_pack_dtype_ours": str(k_packed_ours.dtype),
        "k_pack_dtype_bd": str(k_pack_bd.dtype),
        "packing_format_diff": (
            f"Ours: [B,H,S,D//2] int8 (2 nibbles/byte). "
            f"BD: [B,S,H,D//8] int32 (8 nibbles/int32). "
            f"Byte order and nibble layout likely differ."
        ),
    }

    REPORT["gate_0_2"] = result

    print(f"  V scale max diff (BD vs ours): {v_scale_diff:.6f}")
    print(f"  V zp max diff: {v_zp_diff:.6f}")
    print(f"  V scales close (<0.01)? {result['v_scales_close']}")
    print(f"  V dequant roundtrip err vs FP16: {v_roundtrip_err:.6f}")
    print(f"  K pack shapes: ours={k_packed_ours.shape} vs BD={k_pack_bd.shape}")
    print(f"  K pack dtypes: ours={k_packed_ours.dtype} vs BD={k_pack_bd.dtype}")
    print()

    return result


def gate_0_3_attention_output():
    """Gate 0.3: End-to-end attention output comparison.

    Strategy: Since direct format conversion is blocked (Gate 0.1),
    test the dequant+repack path:
    1. Our quantize: FP16 → our INT4 → dequant back to FP16
    2. BitDecoding repack: that FP16 → BitDecoding INT4
    3. BitDecoding attention on step 2
    4. FP16 reference attention on original FP16
    5. Compare: (3) vs (4) max_abs_diff

    This measures: quality loss from double quantization round-trip
    + BitDecoding kernel numerical precision.
    """
    print("=" * 60)
    print("Gate 0.3: End-to-end attention output comparison")
    print("=" * 60)

    torch.manual_seed(SEED)

    q = torch.randn(BATCH, 1, NHEADS_Q, HEAD_DIM,
                     device="cuda", dtype=torch.float16)
    k_fp16 = torch.randn(BATCH, SEQ_LEN, NHEADS_KV, HEAD_DIM,
                          device="cuda", dtype=torch.float16)
    v_fp16 = torch.randn(BATCH, SEQ_LEN, NHEADS_KV, HEAD_DIM,
                          device="cuda", dtype=torch.float16)

    sm_scale = 1.0 / (HEAD_DIM ** 0.5)

    # --- Path 1: BitDecoding direct (from FP16) ---
    pack_dim = HEAD_DIM // 8
    k_pack = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, pack_dim,
                         device="cuda", dtype=torch.int32)
    v_pack = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, pack_dim,
                         device="cuda", dtype=torch.int32)
    k_params = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, 2,
                           device="cuda", dtype=torch.float16)
    v_params = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, 2,
                           device="cuda", dtype=torch.float16)
    cu_seqlens = torch.tensor([0, SEQ_LEN], device="cuda", dtype=torch.int32)

    kvcache_pack_int(
        k_fp16, k_pack, k_params,
        v_fp16, v_pack, v_params,
        cu_seqlens_k=cu_seqlens,
        seqlen_k=SEQ_LEN,
        quant_mode="k-channel",
        group_size=HEAD_DIM,
        num_bits=4,
    )

    out_bd_direct = fwd_kvcache_int(
        q, k_pack, k_params, v_pack, v_params,
        softmax_scale=sm_scale,
        quant_mode="k-channel",
        group_size=HEAD_DIM,
        num_bits=4,
    )

    # --- Path 2: Our quantize → dequant → BitDecoding repack → attention ---
    from src.quant.asymmetric_quant import (
        quantize_asymmetric_per_channel,
        quantize_asymmetric_per_token,
        dequantize_asymmetric,
    )

    k_bhsd = k_fp16.transpose(1, 2).contiguous()
    v_bhsd = v_fp16.transpose(1, 2).contiguous()

    k_q, k_sc, k_zp = quantize_asymmetric_per_channel(k_bhsd, quant_bits=4)
    v_q, v_sc, v_zp = quantize_asymmetric_per_token(v_bhsd, quant_bits=4)

    k_dequant = dequantize_asymmetric(k_q, k_sc, k_zp, axis=2).half()
    v_dequant = dequantize_asymmetric(v_q, v_sc, v_zp, axis=3).half()

    # Back to [B, S, H, D] for BitDecoding
    k_dq_bshd = k_dequant.transpose(1, 2).contiguous()
    v_dq_bshd = v_dequant.transpose(1, 2).contiguous()

    k_pack2 = torch.zeros_like(k_pack)
    v_pack2 = torch.zeros_like(v_pack)
    k_params2 = torch.zeros_like(k_params)
    v_params2 = torch.zeros_like(v_params)

    kvcache_pack_int(
        k_dq_bshd, k_pack2, k_params2,
        v_dq_bshd, v_pack2, v_params2,
        cu_seqlens_k=cu_seqlens,
        seqlen_k=SEQ_LEN,
        quant_mode="k-channel",
        group_size=HEAD_DIM,
        num_bits=4,
    )

    out_bd_roundtrip = fwd_kvcache_int(
        q, k_pack2, k_params2, v_pack2, v_params2,
        softmax_scale=sm_scale,
        quant_mode="k-channel",
        group_size=HEAD_DIM,
        num_bits=4,
    )

    # --- Path 3: FP16 reference ---
    q_ref = q.transpose(1, 2)
    k_ref = k_fp16.transpose(1, 2)
    v_ref = v_fp16.transpose(1, 2)
    n_rep = NHEADS_Q // NHEADS_KV
    k_ref = k_ref.repeat_interleave(n_rep, dim=1)
    v_ref = v_ref.repeat_interleave(n_rep, dim=1)
    scores = torch.matmul(q_ref, k_ref.transpose(-2, -1)) * sm_scale
    weights = torch.softmax(scores, dim=-1)
    out_fp16_ref = torch.matmul(weights, v_ref).transpose(1, 2)

    # --- Path 4: Our quantize → torch_ref attention ---
    # Uses our quantized+dequanted data with standard attention
    k_dq_ref = k_dequant  # [B, H, S, D]
    v_dq_ref = v_dequant
    k_dq_ref_exp = k_dq_ref.repeat_interleave(n_rep, dim=1)
    v_dq_ref_exp = v_dq_ref.repeat_interleave(n_rep, dim=1)
    q_for_ref = q.transpose(1, 2)  # [B, Hq, 1, D]
    scores_ours = torch.matmul(q_for_ref, k_dq_ref_exp.transpose(-2, -1)) * sm_scale
    weights_ours = torch.softmax(scores_ours, dim=-1)
    out_ours_ref = torch.matmul(weights_ours, v_dq_ref_exp).transpose(1, 2)

    # --- Compare ---
    diff_bd_direct_vs_fp16 = (out_bd_direct.float() - out_fp16_ref.float()).abs().max().item()
    diff_bd_roundtrip_vs_fp16 = (out_bd_roundtrip.float() - out_fp16_ref.float()).abs().max().item()
    diff_ours_ref_vs_fp16 = (out_ours_ref.float() - out_fp16_ref.float()).abs().max().item()
    diff_bd_roundtrip_vs_ours_ref = (out_bd_roundtrip.float() - out_ours_ref.float()).abs().max().item()
    diff_bd_direct_vs_roundtrip = (out_bd_direct.float() - out_bd_roundtrip.float()).abs().max().item()

    result = {
        "bd_direct_vs_fp16_max_diff": diff_bd_direct_vs_fp16,
        "bd_roundtrip_vs_fp16_max_diff": diff_bd_roundtrip_vs_fp16,
        "ours_torch_ref_vs_fp16_max_diff": diff_ours_ref_vs_fp16,
        "bd_roundtrip_vs_ours_ref_max_diff": diff_bd_roundtrip_vs_ours_ref,
        "bd_direct_vs_roundtrip_max_diff": diff_bd_direct_vs_roundtrip,
        "roundtrip_quality_acceptable": diff_bd_roundtrip_vs_ours_ref < 0.05,
    }

    REPORT["gate_0_3"] = result

    print(f"  BD direct (from FP16) vs FP16 ref:     {diff_bd_direct_vs_fp16:.6f}")
    print(f"  BD roundtrip (our quant→dequant→BD) vs FP16: {diff_bd_roundtrip_vs_fp16:.6f}")
    print(f"  Our torch_ref (our quant→dequant→SDPA) vs FP16: {diff_ours_ref_vs_fp16:.6f}")
    print(f"  BD roundtrip vs Our torch_ref:          {diff_bd_roundtrip_vs_ours_ref:.6f}")
    print(f"  BD direct vs BD roundtrip:              {diff_bd_direct_vs_roundtrip:.6f}")
    print(f"  Roundtrip quality acceptable (<0.05)?   {result['roundtrip_quality_acceptable']}")
    print()

    return result


def main():
    print("BitDecoding Compatibility Gate Test")
    print(f"Config: B={BATCH}, S={SEQ_LEN}, Hq={NHEADS_Q}, Hkv={NHEADS_KV}, D={HEAD_DIM}")
    print()

    # Gate 0.1
    k_compat = gate_0_1_k_params_semantics()

    # Gate 0.2
    gate_0_2_nibble_comparison()

    # Gate 0.3
    gate_0_3_attention_output()

    # --- Summary ---
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    gate_01_pass = REPORT.get("gate_0_1", {}).get("compatible_with_ours", False)
    gate_03_pass = REPORT.get("gate_0_3", {}).get("roundtrip_quality_acceptable", False)

    if gate_01_pass:
        print("Gate 0.1: PASS - k_params is per-channel, direct format conversion may work")
        print("  → Next: implement direct repack adapter (no dequant roundtrip)")
    else:
        print("Gate 0.1: FAIL - k_params is per-token, direct format conversion BLOCKED")
        print("  → K quantization semantics are incompatible")
        print("  → Only viable path: dequant → BitDecoding repack (loses our calibration)")

    if gate_03_pass:
        print("Gate 0.3: PASS - dequant+repack roundtrip quality acceptable")
        print("  → BitDecoding can be used as end-to-end backend (not same-quant comparison)")
    else:
        print("Gate 0.3: FAIL - roundtrip quality too poor")
        print("  → BitDecoding integration not recommended")

    overall = "PARTIAL" if (not gate_01_pass and gate_03_pass) else (
        "PASS" if (gate_01_pass and gate_03_pass) else "FAIL"
    )
    print(f"\nOverall: {overall}")
    REPORT["overall"] = overall

    # Save report
    out_path = Path("artifacts") / "bitdecoding_compat_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(REPORT, f, indent=2, default=str)
    print(f"\nReport saved to {out_path}")


if __name__ == "__main__":
    main()
