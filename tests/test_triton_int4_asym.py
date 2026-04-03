"""Tests for INT4 asymmetric Triton decode attention kernel."""
import pytest
import torch

# Skip entire module if CUDA unavailable
pytestmark = pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA required")


def _make_test_data(batch=1, q_heads=8, kv_heads=2, seq_len=64, head_dim=128, seed=42):
    """Create synthetic packed INT4 cache + scale/zp for testing."""
    torch.manual_seed(seed)
    device = "cuda"
    packed_dim = head_dim // 2

    # Random Q
    q = torch.randn(batch, q_heads, head_dim, device=device, dtype=torch.float16)

    # Random INT4 values in [-8, 7]
    k_int4 = torch.randint(-8, 8, (batch, kv_heads, seq_len, head_dim),
                           device=device, dtype=torch.int8)
    v_int4 = torch.randint(-8, 8, (batch, kv_heads, seq_len, head_dim),
                           device=device, dtype=torch.int8)

    # Pack: offset +8 → [0,15], hi<<4 | lo
    def pack(t):
        shifted = (t.to(torch.int16) + 8).to(torch.uint8)
        reshaped = shifted.view(*t.shape[:-1], t.shape[-1] // 2, 2)
        packed = (reshaped[..., 0] << 4) | reshaped[..., 1]
        return packed.to(torch.int8)

    k_packed = pack(k_int4)
    v_packed = pack(v_int4)

    # Random scale/zp (per-channel K, per-token V)
    k_scale = torch.randn(batch, kv_heads, head_dim, device=device, dtype=torch.float32).abs() * 0.1 + 0.01
    k_zp = torch.randn(batch, kv_heads, head_dim, device=device, dtype=torch.float32) * 0.05
    v_scale = torch.randn(batch, kv_heads, seq_len, device=device, dtype=torch.float32).abs() * 0.1 + 0.01
    v_zp = torch.randn(batch, kv_heads, seq_len, device=device, dtype=torch.float32) * 0.05

    context_lens = torch.full((batch,), seq_len, device=device, dtype=torch.int32)

    return q, k_packed, v_packed, k_int4, v_int4, k_scale, k_zp, v_scale, v_zp, context_lens


def _torch_ref_int4_asym(q, k_int4, v_int4, k_scale, k_zp, v_scale, v_zp, context_lens):
    """Reference implementation using PyTorch."""
    batch, q_heads, head_dim = q.shape
    kv_heads = k_int4.shape[1]
    n_rep = q_heads // kv_heads
    outputs = []

    for b in range(batch):
        ctx = context_lens[b].item()
        batch_outs = []
        for qh in range(q_heads):
            kvh = qh // n_rep
            q_vec = q[b, qh].float()  # [D]
            k_vals = k_int4[b, kvh, :ctx].float()  # [S, D]
            v_vals = v_int4[b, kvh, :ctx].float()  # [S, D]

            # Dequant K: per-channel → scale/zp broadcast over seq dim
            k_dq = k_vals * k_scale[b, kvh].unsqueeze(0) + k_zp[b, kvh].unsqueeze(0)  # [S, D]
            # Dequant V: per-token → scale/zp broadcast over head dim
            v_dq = v_vals * v_scale[b, kvh, :ctx].unsqueeze(1) + v_zp[b, kvh, :ctx].unsqueeze(1)  # [S, D]

            # Attention
            sm_scale = 1.0 / (head_dim ** 0.5)
            scores = (q_vec @ k_dq.T) * sm_scale  # [S]
            weights = torch.softmax(scores, dim=-1)  # [S]
            out = weights @ v_dq  # [D]
            batch_outs.append(out)
        outputs.append(torch.stack(batch_outs))

    return torch.stack(outputs).to(torch.float16)


class TestInt4AsymDecodeAttn:
    """Test INT4 asymmetric Triton kernel against torch reference."""

    def test_basic_correctness(self):
        from src.kernels.triton_decode_attn_int4_asym import decode_attn_int4_asym

        q, k_packed, v_packed, k_int4, v_int4, k_scale, k_zp, v_scale, v_zp, ctx = _make_test_data()

        triton_out = decode_attn_int4_asym(
            q, k_packed, v_packed, k_scale, k_zp, v_scale, v_zp, ctx
        )
        ref_out = _torch_ref_int4_asym(q, k_int4, v_int4, k_scale, k_zp, v_scale, v_zp, ctx)

        max_diff = (triton_out.float() - ref_out.float()).abs().max().item()
        assert max_diff < 1e-2, f"Max diff {max_diff} >= 1e-2"

    def test_gqa_heads(self):
        """Test with GQA (q_heads=8, kv_heads=2 → n_rep=4)."""
        from src.kernels.triton_decode_attn_int4_asym import decode_attn_int4_asym

        q, k_packed, v_packed, k_int4, v_int4, k_scale, k_zp, v_scale, v_zp, ctx = _make_test_data(
            q_heads=8, kv_heads=2
        )
        triton_out = decode_attn_int4_asym(
            q, k_packed, v_packed, k_scale, k_zp, v_scale, v_zp, ctx
        )
        ref_out = _torch_ref_int4_asym(q, k_int4, v_int4, k_scale, k_zp, v_scale, v_zp, ctx)

        max_diff = (triton_out.float() - ref_out.float()).abs().max().item()
        assert max_diff < 1e-2, f"GQA max diff {max_diff} >= 1e-2"

    def test_partial_context(self):
        """Test with context_lens < max_seq_len (padding)."""
        from src.kernels.triton_decode_attn_int4_asym import decode_attn_int4_asym

        q, k_packed, v_packed, k_int4, v_int4, k_scale, k_zp, v_scale, v_zp, _ = _make_test_data(
            batch=2, seq_len=128
        )
        ctx = torch.tensor([64, 100], device="cuda", dtype=torch.int32)

        triton_out = decode_attn_int4_asym(
            q, k_packed, v_packed, k_scale, k_zp, v_scale, v_zp, ctx
        )
        ref_out = _torch_ref_int4_asym(q, k_int4, v_int4, k_scale, k_zp, v_scale, v_zp, ctx)

        max_diff = (triton_out.float() - ref_out.float()).abs().max().item()
        assert max_diff < 1e-2, f"Partial ctx max diff {max_diff} >= 1e-2"

    def test_zero_context(self):
        """Test with context_lens=0 returns zeros."""
        from src.kernels.triton_decode_attn_int4_asym import decode_attn_int4_asym

        q, k_packed, v_packed, k_int4, v_int4, k_scale, k_zp, v_scale, v_zp, _ = _make_test_data()
        ctx = torch.zeros(1, device="cuda", dtype=torch.int32)

        out = decode_attn_int4_asym(
            q, k_packed, v_packed, k_scale, k_zp, v_scale, v_zp, ctx
        )
        assert out.abs().max().item() == 0.0

    def test_small_block_boundary(self):
        """Test seq_len not aligned to block_size."""
        from src.kernels.triton_decode_attn_int4_asym import decode_attn_int4_asym

        q, k_packed, v_packed, k_int4, v_int4, k_scale, k_zp, v_scale, v_zp, _ = _make_test_data(
            seq_len=37  # not aligned to any block size
        )
        ctx = torch.tensor([37], device="cuda", dtype=torch.int32)

        triton_out = decode_attn_int4_asym(
            q, k_packed, v_packed, k_scale, k_zp, v_scale, v_zp, ctx,
            block_size=32,
        )
        ref_out = _torch_ref_int4_asym(q, k_int4, v_int4, k_scale, k_zp, v_scale, v_zp, ctx)

        max_diff = (triton_out.float() - ref_out.float()).abs().max().item()
        assert max_diff < 1e-2, f"Unaligned max diff {max_diff} >= 1e-2"
