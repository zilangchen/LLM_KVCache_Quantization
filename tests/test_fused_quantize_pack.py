"""Tests for fused Triton quantize+pack INT4 kernels."""
import pytest
import torch

pytestmark = pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA required")


def _ref_quantize_pack_k(k, k_scale, k_zp):
    """Reference: PyTorch eager quantize + pack for K."""
    s = k_scale.unsqueeze(2)
    zp = k_zp.unsqueeze(2)
    unscaled = (k.float() - zp) / s
    q = torch.round(unscaled).clamp(-8, 7).to(torch.int8)
    shifted = (q.to(torch.int16) + 8).to(torch.uint8)
    reshaped = shifted.view(*q.shape[:-1], q.shape[-1] // 2, 2)
    packed = (reshaped[..., 0] << 4) | reshaped[..., 1]
    return packed.to(torch.int8)


def _ref_quantize_pack_v(v):
    """Reference: PyTorch eager quantize + pack for V (per-token)."""
    v_f = v.float()
    t_min = v_f.amin(dim=-1, keepdim=True)
    t_max = v_f.amax(dim=-1, keepdim=True)
    _fp16_tiny = torch.finfo(torch.float16).tiny
    range_floor = max(1e-5, _fp16_tiny * 15)
    scale = (t_max - t_min).clamp(min=range_floor) / 15.0
    zp = t_min + 8.0 * scale
    q = torch.round((v_f - zp) / scale).clamp(-8, 7).to(torch.int8)
    shifted = (q.to(torch.int16) + 8).to(torch.uint8)
    reshaped = shifted.view(*q.shape[:-1], q.shape[-1] // 2, 2)
    packed = (reshaped[..., 0] << 4) | reshaped[..., 1]
    return packed.to(torch.int8), scale.squeeze(-1), zp.squeeze(-1)


class TestFusedQuantizePackK:
    def test_basic(self):
        from src.kernels.triton_quantize_pack_int4 import fused_quantize_pack_k_int4
        torch.manual_seed(42)
        B, H, D = 1, 2, 128
        k = torch.randn(B, H, 1, D, device="cuda", dtype=torch.float16)
        k_scale = torch.randn(B, H, D, device="cuda", dtype=torch.float32).abs() * 0.1 + 0.01
        k_zp = torch.randn(B, H, D, device="cuda", dtype=torch.float32) * 0.05

        triton_out = fused_quantize_pack_k_int4(k, k_scale, k_zp)
        ref_out = _ref_quantize_pack_k(k, k_scale, k_zp)

        assert triton_out.shape == ref_out.shape
        assert (triton_out == ref_out).all(), f"K pack mismatch: {(triton_out != ref_out).sum()} diffs"

    def test_multiple_heads(self):
        from src.kernels.triton_quantize_pack_int4 import fused_quantize_pack_k_int4
        torch.manual_seed(123)
        B, H, D = 2, 4, 128
        k = torch.randn(B, H, 1, D, device="cuda", dtype=torch.float16)
        k_scale = torch.randn(B, H, D, device="cuda", dtype=torch.float32).abs() * 0.1 + 0.01
        k_zp = torch.randn(B, H, D, device="cuda", dtype=torch.float32) * 0.05

        triton_out = fused_quantize_pack_k_int4(k, k_scale, k_zp)
        ref_out = _ref_quantize_pack_k(k, k_scale, k_zp)
        assert (triton_out == ref_out).all()


class TestFusedQuantizePackV:
    def test_basic(self):
        from src.kernels.triton_quantize_pack_int4 import fused_quantize_pack_v_int4
        torch.manual_seed(42)
        B, H, D = 1, 2, 128

        v = torch.randn(B, H, 1, D, device="cuda", dtype=torch.float16)
        # Pre-allocate scale/zp buffers (simulating cache)
        v_scale_buf = torch.zeros(B, H, 64, device="cuda", dtype=torch.float32)
        v_zp_buf = torch.zeros(B, H, 64, device="cuda", dtype=torch.float32)

        triton_packed = fused_quantize_pack_v_int4(v, v_scale_buf, v_zp_buf, write_idx=0)
        ref_packed, ref_scale, ref_zp = _ref_quantize_pack_v(v)

        assert triton_packed.shape == ref_packed.shape
        # Allow ±1 nibble diff due to rounding mode differences
        diff = (triton_packed.to(torch.uint8) ^ ref_packed.to(torch.uint8))
        hi_diff = (diff >> 4) & 0x0F
        lo_diff = diff & 0x0F
        assert hi_diff.max() <= 1 and lo_diff.max() <= 1, \
            f"V pack diff too large: hi_max={hi_diff.max()}, lo_max={lo_diff.max()}"

        # Scale/zp should be close (flatten to avoid broadcast shape mismatch)
        triton_scale = v_scale_buf[:, :, 0].flatten()
        triton_zp = v_zp_buf[:, :, 0].flatten()
        assert (triton_scale - ref_scale.flatten()).abs().max() < 1e-4, "V scale mismatch"
        assert (triton_zp - ref_zp.flatten()).abs().max() < 1e-4, "V zp mismatch"
