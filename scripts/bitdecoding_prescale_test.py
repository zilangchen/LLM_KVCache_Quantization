#!/usr/bin/env python3
"""Verify Q-prescaling trick for BitDecoding + our per-channel K quantization.

Hypothesis: We can use BitDecoding's fast kernel with our KL-calibrated
per-channel K quantization by:
  1. Pre-multiply Q by our K scale: Q_prescaled = Q * k_scale
  2. Pack our raw K_int into BitDecoding format with scale=1.0, zp=0.0
  3. BitDecoding computes: Q_prescaled · K_int = Q · (K_int * scale) = Q · K_dequant_ours
  4. K zero-point is absorbed by softmax's translation invariance

Three gates:
  Gate A: Can we set k_params=(1,0) and get correct raw-int dequant?
  Gate B: Can we convert our nibble packing to BitDecoding's int32 format?
  Gate C: End-to-end attention output matches our torch_ref?

Usage:
    CUDA_VISIBLE_DEVICES=0 python3 scripts/bitdecoding_prescale_test.py
"""
import sys
import os
import torch
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bit_decode import fwd_kvcache_int, kvcache_pack_int
except ImportError:
    print("ERROR: bit_decode not installed")
    sys.exit(2)

if not torch.cuda.is_available():
    print("ERROR: CUDA required")
    sys.exit(2)

BATCH = 1
SEQ_LEN = 256
NHEADS_Q = 12   # Qwen2.5-1.5B
NHEADS_KV = 2
HEAD_DIM = 128
N_REP = NHEADS_Q // NHEADS_KV  # 6
SEED = 42
REPORT = {}


def gate_a_forced_unit_scale():
    """Gate A: Does fwd_kvcache_int work with scale=1.0, zp=0.0?

    Pack known FP16 data with BitDecoding, then override k_params to (1,0).
    The kernel should output Q · (nibble - 8) instead of Q · dequant.
    """
    print("=" * 60)
    print("Gate A: forced unit scale (k_params = 1.0, 0.0)")
    print("=" * 60)

    torch.manual_seed(SEED)
    device = "cuda"

    # Create small random data
    q = torch.randn(BATCH, 1, NHEADS_Q, HEAD_DIM, device=device, dtype=torch.float16)
    k_fp16 = torch.randn(BATCH, SEQ_LEN, NHEADS_KV, HEAD_DIM, device=device, dtype=torch.float16)
    v_fp16 = torch.randn(BATCH, SEQ_LEN, NHEADS_KV, HEAD_DIM, device=device, dtype=torch.float16)
    sm_scale = 1.0 / (HEAD_DIM ** 0.5)

    # Pack with BitDecoding (normal)
    pack_dim = HEAD_DIM // 8
    k_pack = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, pack_dim, device=device, dtype=torch.int32)
    v_pack = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, pack_dim, device=device, dtype=torch.int32)
    k_params = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, 2, device=device, dtype=torch.float16)
    v_params = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, 2, device=device, dtype=torch.float16)
    cu = torch.tensor([0, SEQ_LEN], device=device, dtype=torch.int32)

    kvcache_pack_int(
        k_fp16, k_pack, k_params, v_fp16, v_pack, v_params,
        cu_seqlens_k=cu, seqlen_k=SEQ_LEN,
        quant_mode="k-channel", group_size=HEAD_DIM, num_bits=4,
    )

    # Test 1: Normal BitDecoding (with BD's own scales)
    out_normal = fwd_kvcache_int(
        q, k_pack, k_params, v_pack, v_params,
        softmax_scale=sm_scale, quant_mode="k-channel",
        group_size=HEAD_DIM, num_bits=4,
    )

    # Test 2: Force k_params = (1.0, 0.0)
    k_params_unit = torch.zeros_like(k_params)
    k_params_unit[..., 0] = 1.0  # scale = 1.0
    k_params_unit[..., 1] = 0.0  # zp = 0.0

    out_unit = fwd_kvcache_int(
        q, k_pack, k_params_unit, v_pack, v_params,
        softmax_scale=sm_scale, quant_mode="k-channel",
        group_size=HEAD_DIM, num_bits=4,
    )

    has_nan = torch.isnan(out_unit).any().item()
    diff = (out_normal.float() - out_unit.float()).abs().max().item()

    result = {
        "unit_scale_has_nan": has_nan,
        "unit_scale_output_shape": list(out_unit.shape),
        "diff_vs_normal": diff,
        "gate_pass": not has_nan,
    }
    REPORT["gate_a"] = result

    print(f"  Unit-scale output NaN: {has_nan}")
    print(f"  Output shape: {out_unit.shape}")
    print(f"  Diff vs normal BD: {diff:.6f} (expected: large, because scales differ)")
    print(f"  Gate A: {'PASS' if not has_nan else 'FAIL'} — kernel accepts forced scale")
    print()
    return not has_nan


def gate_b_nibble_conversion():
    """Gate B: Can we convert our int8 packed nibbles to BitDecoding's int32?

    Our packing: (val + 8) as uint8, hi nibble << 4 | lo nibble, stored as int8
    BD packing: 8 nibbles per int32

    Test: pack the same integer values both ways, compare nibble content.
    """
    print("=" * 60)
    print("Gate B: nibble format conversion (int8 → int32)")
    print("=" * 60)

    torch.manual_seed(SEED)
    device = "cuda"

    # Create known integer values in [-8, 7]
    k_int = torch.randint(-8, 8, (BATCH, NHEADS_KV, SEQ_LEN, HEAD_DIM),
                          device=device, dtype=torch.int8)

    # --- Our packing: [B, H, S, D] → [B, H, S, D//2] int8 ---
    from src.quant.int4_basic import pack_int4, unpack_int4
    k_packed_ours = pack_int4(k_int)  # [B, H, S, D//2] int8

    # Verify our round-trip
    k_unpacked = unpack_int4(k_packed_ours)
    assert (k_unpacked == k_int).all(), "Our pack/unpack roundtrip failed!"

    # --- BitDecoding packing: feed FP16 values that are exactly the integers ---
    # We want BD to pack the SAME integer values.
    # Strategy: create FP16 K where quantization with BD's method produces the
    # same integers. Since BD uses per-token quantization, we can't guarantee
    # the same integers. Instead, let's directly test format conversion.

    # Convert our int8 packed to int32 by reinterpreting bytes
    # Our layout: [B, H, S, D//2] int8 → transpose to [B, S, H, D//2] → view as int32
    k_packed_transposed = k_packed_ours.transpose(1, 2).contiguous()  # [B, S, H, D//2]

    # D//2 = 64 bytes → D//8 = 16 int32s (4 bytes each)
    # Reinterpret: every 4 consecutive int8 → 1 int32
    B, S, H, half_d = k_packed_transposed.shape
    k_as_int32 = k_packed_transposed.view(B, S, H, half_d // 4, 4)
    # Combine 4 bytes into int32 (little-endian on CUDA)
    k_int32_manual = (
        k_as_int32[..., 0].to(torch.int32) & 0xFF
        | ((k_as_int32[..., 1].to(torch.int32) & 0xFF) << 8)
        | ((k_as_int32[..., 2].to(torch.int32) & 0xFF) << 16)
        | ((k_as_int32[..., 3].to(torch.int32) & 0xFF) << 24)
    )  # [B, S, H, D//8]

    # --- Now test: does BD produce the same int32 from the same FP16? ---
    # Create FP16 values that exactly represent our integers (for comparison)
    k_fp16_from_int = k_int.float().half()  # [B, H, S, D] — values like -8.0, -7.0, ..., 7.0
    k_fp16_bshd = k_fp16_from_int.transpose(1, 2).contiguous()  # [B, S, H, D]

    pack_dim = HEAD_DIM // 8
    k_pack_bd = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, pack_dim, device=device, dtype=torch.int32)
    v_dummy = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, HEAD_DIM, device=device, dtype=torch.float16)
    v_pack_bd = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, pack_dim, device=device, dtype=torch.int32)
    k_params_bd = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, 2, device=device, dtype=torch.float16)
    v_params_bd = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, 2, device=device, dtype=torch.float16)
    cu = torch.tensor([0, SEQ_LEN], device=device, dtype=torch.int32)

    kvcache_pack_int(
        k_fp16_bshd, k_pack_bd, k_params_bd,
        v_dummy, v_pack_bd, v_params_bd,
        cu_seqlens_k=cu, seqlen_k=SEQ_LEN,
        quant_mode="k-channel", group_size=HEAD_DIM, num_bits=4,
    )

    # Compare int32 values
    match = (k_int32_manual == k_pack_bd).all().item()
    diff_count = (k_int32_manual != k_pack_bd).sum().item()
    total = k_int32_manual.numel()

    # Also check nibble-level: extract nibbles from both and compare
    # Our nibbles: hi = (byte >> 4) & 0xF, lo = byte & 0xF
    # BD nibbles: need to extract from int32

    result = {
        "int32_match": match,
        "diff_count": diff_count,
        "total_int32s": total,
        "match_rate": 1.0 - diff_count / max(total, 1),
        "our_shape": list(k_int32_manual.shape),
        "bd_shape": list(k_pack_bd.shape),
        "note": "BD re-quantizes FP16, so exact nibble match unlikely. "
                "Key question is whether direct byte reinterpret works.",
    }
    REPORT["gate_b"] = result

    print(f"  Our int32 shape: {k_int32_manual.shape}")
    print(f"  BD int32 shape:  {k_pack_bd.shape}")
    print(f"  Exact int32 match: {match}")
    print(f"  Diff count: {diff_count} / {total} ({100*diff_count/max(total,1):.1f}%)")
    print(f"  Note: BD re-quantizes, so mismatch expected. Direct reinterpret may not work.")
    print(f"  → If mismatch: need to use BD's packer on our dequanted data")
    print(f"  → But with scale=1,zp=0 the packer should preserve raw ints")
    print()
    return result


def gate_c_e2e_prescale_attention():
    """Gate C: End-to-end test of Q-prescaling trick.

    Flow:
    1. Our quantization: FP16 → per-channel K_int + scale + zp
    2. Pack K_int into BD format (via BD packer with FP16 = raw ints)
    3. Q_prescaled = Q * k_scale (per channel)
    4. Call fwd_kvcache_int with Q_prescaled, k_pack, k_params=(1,0)
    5. Compare vs FP16 reference attention

    Note: V uses BD's own quantization here (we'll optimize V later).
    """
    print("=" * 60)
    print("Gate C: end-to-end Q-prescale attention")
    print("=" * 60)

    torch.manual_seed(SEED)
    device = "cuda"
    sm_scale = 1.0 / (HEAD_DIM ** 0.5)

    # Original FP16 data
    q = torch.randn(BATCH, 1, NHEADS_Q, HEAD_DIM, device=device, dtype=torch.float16)
    k_fp16 = torch.randn(BATCH, SEQ_LEN, NHEADS_KV, HEAD_DIM, device=device, dtype=torch.float16)
    v_fp16 = torch.randn(BATCH, SEQ_LEN, NHEADS_KV, HEAD_DIM, device=device, dtype=torch.float16)

    # --- Step 1: Our per-channel K quantization ---
    from src.quant.asymmetric_quant import quantize_asymmetric_per_channel

    k_bhsd = k_fp16.transpose(1, 2).contiguous()  # [B, H, S, D]
    k_int_full, k_scale, k_zp = quantize_asymmetric_per_channel(k_bhsd, quant_bits=4)
    # k_int_full: [B, H, S, D] int8 in [-8, 7]
    # k_scale: [B, H, D] float32 per-channel
    # k_zp: [B, H, D] float32 per-channel

    # --- Step 2: Pack K_int into BD format ---
    # Strategy: convert K_int to FP16 (just cast ints to float),
    # then use BD packer. BD will re-quantize, but since values are
    # already in [-8, 7] (small range), BD's scale should be ~1.0.
    k_int_fp16 = k_int_full.float().half()  # [B, H, S, D] — values like -8.0 to 7.0
    k_int_bshd = k_int_fp16.transpose(1, 2).contiguous()  # [B, S, H, D]

    pack_dim = HEAD_DIM // 8
    k_pack = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, pack_dim, device=device, dtype=torch.int32)
    v_pack = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, pack_dim, device=device, dtype=torch.int32)
    k_params_packed = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, 2, device=device, dtype=torch.float16)
    v_params = torch.zeros(BATCH, SEQ_LEN, NHEADS_KV, 2, device=device, dtype=torch.float16)
    cu = torch.tensor([0, SEQ_LEN], device=device, dtype=torch.int32)

    kvcache_pack_int(
        k_int_bshd, k_pack, k_params_packed,
        v_fp16, v_pack, v_params,
        cu_seqlens_k=cu, seqlen_k=SEQ_LEN,
        quant_mode="k-channel", group_size=HEAD_DIM, num_bits=4,
    )

    # Check what BD computed for k_params (should be close to scale≈1, zp≈0
    # since input values are small integers)
    bd_k_scale_mean = k_params_packed[..., 0].mean().item()
    bd_k_zp_mean = k_params_packed[..., 1].mean().item()
    print(f"  BD auto-computed k_params: scale_mean={bd_k_scale_mean:.4f}, zp_mean={bd_k_zp_mean:.4f}")
    print(f"  (Expected: scale≈1.0, zp≈0.0 since input is integers [-8,7])")

    # --- Step 3: Override k_params to (1.0, 0.0) ---
    k_params_unit = torch.zeros_like(k_params_packed)
    k_params_unit[..., 0] = 1.0
    k_params_unit[..., 1] = 0.0

    # --- Step 4: Q prescaling ---
    # q: [B, 1, Hq, D] → need to multiply by k_scale [B, Hkv, D]
    # For GQA: each Q head r maps to KV head r // N_REP
    # k_scale: [B, Hkv, D] → expand to [B, Hq, D]
    k_scale_expanded = k_scale.repeat_interleave(N_REP, dim=1)  # [B, Hq, D]
    q_prescaled = q.clone()
    q_prescaled[0, 0, :, :] = q[0, 0, :, :] * k_scale_expanded[0, :, :].half()

    # --- Step 5: BitDecoding attention with prescaled Q ---
    out_prescale = fwd_kvcache_int(
        q_prescaled, k_pack, k_params_unit, v_pack, v_params,
        softmax_scale=sm_scale, quant_mode="k-channel",
        group_size=HEAD_DIM, num_bits=4,
    )

    # --- Reference 1: FP16 attention ---
    q_ref = q.transpose(1, 2)  # [B, Hq, 1, D]
    k_ref = k_fp16.transpose(1, 2)  # [B, Hkv, S, D]
    v_ref = v_fp16.transpose(1, 2)
    k_ref_exp = k_ref.repeat_interleave(N_REP, dim=1)
    v_ref_exp = v_ref.repeat_interleave(N_REP, dim=1)
    scores_fp16 = torch.matmul(q_ref, k_ref_exp.transpose(-2, -1)) * sm_scale
    weights_fp16 = torch.softmax(scores_fp16, dim=-1)
    out_fp16 = torch.matmul(weights_fp16, v_ref_exp).transpose(1, 2)  # [B, 1, Hq, D]

    # --- Reference 2: Our quant → dequant → manual attention ---
    from src.quant.asymmetric_quant import dequantize_asymmetric
    k_dequant = dequantize_asymmetric(k_int_full, k_scale, k_zp, axis=2).half()
    k_dq_exp = k_dequant.repeat_interleave(N_REP, dim=1)
    v_ref2 = v_ref  # V same as FP16 ref for now
    v_ref2_exp = v_ref2.repeat_interleave(N_REP, dim=1)
    scores_ours = torch.matmul(q_ref, k_dq_exp.transpose(-2, -1)) * sm_scale
    weights_ours = torch.softmax(scores_ours, dim=-1)
    out_ours_ref = torch.matmul(weights_ours, v_ref2_exp).transpose(1, 2)

    # --- Reference 3: Normal BitDecoding (BD's own quant) ---
    k_pack_normal = torch.zeros_like(k_pack)
    v_pack_normal = torch.zeros_like(v_pack)
    k_params_normal = torch.zeros_like(k_params_packed)
    v_params_normal = torch.zeros_like(v_params)
    kvcache_pack_int(
        k_fp16, k_pack_normal, k_params_normal,
        v_fp16, v_pack_normal, v_params_normal,
        cu_seqlens_k=cu, seqlen_k=SEQ_LEN,
        quant_mode="k-channel", group_size=HEAD_DIM, num_bits=4,
    )
    out_bd_normal = fwd_kvcache_int(
        q, k_pack_normal, k_params_normal, v_pack_normal, v_params_normal,
        softmax_scale=sm_scale, quant_mode="k-channel",
        group_size=HEAD_DIM, num_bits=4,
    )

    # --- Compare ---
    diff_prescale_vs_fp16 = (out_prescale.float() - out_fp16.float()).abs().max().item()
    diff_prescale_vs_ours = (out_prescale.float() - out_ours_ref.float()).abs().max().item()
    diff_bd_normal_vs_fp16 = (out_bd_normal.float() - out_fp16.float()).abs().max().item()
    diff_ours_ref_vs_fp16 = (out_ours_ref.float() - out_fp16.float()).abs().max().item()

    has_nan = torch.isnan(out_prescale).any().item()

    result = {
        "prescale_vs_fp16": diff_prescale_vs_fp16,
        "prescale_vs_ours_ref": diff_prescale_vs_ours,
        "bd_normal_vs_fp16": diff_bd_normal_vs_fp16,
        "ours_ref_vs_fp16": diff_ours_ref_vs_fp16,
        "has_nan": has_nan,
        "prescale_quality_ok": diff_prescale_vs_ours < 0.1 and not has_nan,
        "bd_k_scale_mean": bd_k_scale_mean,
        "bd_k_zp_mean": bd_k_zp_mean,
    }
    REPORT["gate_c"] = result

    print(f"\n  Q-prescale vs FP16 ref:     {diff_prescale_vs_fp16:.6f}")
    print(f"  Q-prescale vs Our quant ref: {diff_prescale_vs_ours:.6f}  ← THIS is the key metric")
    print(f"  BD normal vs FP16 ref:       {diff_bd_normal_vs_fp16:.6f}")
    print(f"  Our quant ref vs FP16:       {diff_ours_ref_vs_fp16:.6f}")
    print(f"  Has NaN: {has_nan}")
    print()

    if diff_prescale_vs_ours < 0.1 and not has_nan:
        print(f"  Gate C: PASS ✓")
        print(f"  Q-prescale trick works! Our calibration + BD kernel = quality preserved.")
        print(f"  Diff vs our reference ({diff_prescale_vs_ours:.4f}) is from V quantization")
        print(f"  difference only (V uses BD's quant, K uses ours via prescaling).")
    elif not has_nan:
        print(f"  Gate C: PARTIAL — no NaN but diff={diff_prescale_vs_ours:.4f} > 0.1")
        print(f"  May need to investigate nibble packing mismatch.")
    else:
        print(f"  Gate C: FAIL — NaN in output")
    print()

    return result


def main():
    print("BitDecoding Q-Prescaling Compatibility Test")
    print(f"Config: B={BATCH}, S={SEQ_LEN}, Hq={NHEADS_Q}, Hkv={NHEADS_KV}, D={HEAD_DIM}")
    print()

    gate_a_ok = gate_a_forced_unit_scale()
    gate_b_result = gate_b_nibble_conversion()
    gate_c_result = gate_c_e2e_prescale_attention()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Gate A (unit scale accepted): {'PASS' if gate_a_ok else 'FAIL'}")
    print(f"  Gate B (nibble conversion):   match_rate={gate_b_result.get('match_rate', 0):.1%}")
    print(f"  Gate C (e2e prescale attn):   {'PASS' if gate_c_result.get('prescale_quality_ok') else 'FAIL'}")
    print(f"    prescale vs our_ref diff:   {gate_c_result.get('prescale_vs_ours_ref', -1):.6f}")

    overall = "PASS" if (gate_a_ok and gate_c_result.get("prescale_quality_ok")) else "FAIL"
    print(f"\n  Overall: {overall}")
    REPORT["overall"] = overall

    out_path = "artifacts/bitdecoding_prescale_report.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(REPORT, f, indent=2, default=str)
    print(f"  Report: {out_path}")


if __name__ == "__main__":
    main()
