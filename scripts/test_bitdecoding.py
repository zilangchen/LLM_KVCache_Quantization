"""Quick test: BitDecoding INT4 fused decode attention."""
import torch
from bit_decode import fwd_kvcache_int, kvcache_pack_int

def test_basic():
    torch.manual_seed(42)
    batch, seqlen_k, nheads_q, nheads_kv, head_dim = 1, 512, 16, 2, 128

    # FP16 Q, K, V
    q = torch.randn(batch, 1, nheads_q, head_dim, device="cuda", dtype=torch.float16)
    k_cache = torch.randn(batch, seqlen_k, nheads_kv, head_dim, device="cuda", dtype=torch.float16)
    v_cache = torch.randn(batch, seqlen_k, nheads_kv, head_dim, device="cuda", dtype=torch.float16)

    # Pack K/V into INT4
    pack_dim = head_dim // 8  # 4-bit packing
    k_pack = torch.zeros(batch, seqlen_k, nheads_kv, pack_dim, device="cuda", dtype=torch.int32)
    v_pack = torch.zeros(batch, seqlen_k, nheads_kv, pack_dim, device="cuda", dtype=torch.int32)

    # k_params/v_params: [batch, seqlen_k, nheads_kv, 2] (scale + zero_point)
    k_params = torch.zeros(batch, seqlen_k, nheads_kv, 2, device="cuda", dtype=torch.float16)
    v_params = torch.zeros(batch, seqlen_k, nheads_kv, 2, device="cuda", dtype=torch.float16)

    cu_seqlens_k = torch.tensor([0, seqlen_k], device="cuda", dtype=torch.int32)

    # Pack
    print("Packing K/V cache...")
    kvcache_pack_int(
        k_cache, k_pack, k_params,
        v_cache, v_pack, v_params,
        cu_seqlens_k=cu_seqlens_k,
        seqlen_k=seqlen_k,
        quant_mode="k-channel",
        group_size=128,
        num_bits=4,
    )
    print(f"k_pack shape: {k_pack.shape}, k_params shape: {k_params.shape}")

    # Forward
    print("Running fwd_kvcache_int...")
    softmax_scale = 1.0 / (head_dim ** 0.5)
    out = fwd_kvcache_int(
        q, k_pack, k_params, v_pack, v_params,
        softmax_scale=softmax_scale,
        quant_mode="k-channel",
        group_size=128,
        num_bits=4,
    )
    print(f"Output shape: {out.shape}")
    print(f"Output sample: {out[0, 0, 0, :5]}")

    # Reference: FP16 attention
    q_ref = q.transpose(1, 2)  # [B, Hq, 1, D]
    k_ref = k_cache.transpose(1, 2)  # [B, Hkv, S, D]
    v_ref = v_cache.transpose(1, 2)

    # GQA expand
    n_rep = nheads_q // nheads_kv
    k_ref = k_ref.repeat_interleave(n_rep, dim=1)
    v_ref = v_ref.repeat_interleave(n_rep, dim=1)

    scores = torch.matmul(q_ref, k_ref.transpose(-2, -1)) * softmax_scale
    weights = torch.softmax(scores, dim=-1)
    ref_out = torch.matmul(weights, v_ref).transpose(1, 2)  # [B, 1, Hq, D]

    # Compare
    max_diff = (out.float() - ref_out.float()).abs().max().item()
    print(f"Max diff vs FP16 ref: {max_diff:.6f}")
    print(f"{'PASS' if max_diff < 0.1 else 'FAIL'} (threshold 0.1 for INT4)")

if __name__ == "__main__":
    test_basic()
