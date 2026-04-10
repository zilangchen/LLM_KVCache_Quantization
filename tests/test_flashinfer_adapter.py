"""Tests for the FlashInfer FP16 decode attention adapter.

Test 1 (CPU): dequant pipeline — unpack + dequant + layout conversion.
Test 2 (GPU + FlashInfer): end-to-end correctness vs PyTorch reference.
Test 3 (CPU): import guard — adapter module imports without FlashInfer.
"""

import os
import sys
import unittest

import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.quant.asymmetric_quant import (
    dequantize_asymmetric_per_channel,
    dequantize_asymmetric_per_token,
)
from src.quant.int4_basic import pack_int4, unpack_int4


class TestDequantPipeline(unittest.TestCase):
    """CPU-only: verify unpack → dequant → layout conversion."""

    def test_unpack_roundtrip(self):
        """pack then unpack should recover original values."""
        torch.manual_seed(42)
        # INT4 range: [-8, 7]
        original = torch.randint(-8, 8, (1, 2, 4, 8), dtype=torch.int8)
        packed = pack_int4(original)  # [1, 2, 4, 4]
        unpacked = unpack_int4(packed)  # [1, 2, 4, 8]
        self.assertTrue(torch.equal(original, unpacked))

    def test_dequant_per_channel_known_values(self):
        """Per-channel dequant: x_hat = q * scale + zp."""
        # Single batch, single head, 2 tokens, 4 channels
        q_int = torch.tensor([[[[1, -2, 3, 0], [4, -1, 2, -3]]]], dtype=torch.int8)
        scale = torch.tensor([[[0.5, 1.0, 0.25, 2.0]]], dtype=torch.float32)
        zp = torch.tensor([[[0.1, -0.2, 0.0, 0.5]]], dtype=torch.float32)
        result = dequantize_asymmetric_per_channel(q_int, scale, zp)
        expected = torch.tensor(
            [[[[0.6, -2.2, 0.75, 0.5], [2.1, -1.2, 0.5, -5.5]]]],
            dtype=torch.float32,
        )
        self.assertTrue(torch.allclose(result, expected, atol=1e-5))

    def test_dequant_per_token_known_values(self):
        """Per-token dequant: x_hat = q * scale + zp."""
        q_int = torch.tensor([[[[2, -1, 3, 0], [1, 4, -2, 5]]]], dtype=torch.int8)
        scale = torch.tensor([[[0.5, 1.0]]], dtype=torch.float32)
        zp = torch.tensor([[[0.1, -0.3]]], dtype=torch.float32)
        result = dequantize_asymmetric_per_token(q_int, scale, zp)
        expected = torch.tensor(
            [[[[1.1, -0.4, 1.6, 0.1], [0.7, 3.7, -2.3, 4.7]]]],
            dtype=torch.float32,
        )
        self.assertTrue(torch.allclose(result, expected, atol=1e-5))

    def test_layout_conversion_nhd(self):
        """[B, Hkv, S, D] → per-batch [S, Hkv, D] (NHD layout)."""
        B, Hkv, S, D = 2, 4, 8, 16
        tensor = torch.randn(B, Hkv, S, D)
        for b in range(B):
            nhd = tensor[b].permute(1, 0, 2).contiguous()  # [S, Hkv, D]
            self.assertEqual(nhd.shape, (S, Hkv, D))
            # Verify values match
            for s in range(S):
                for h in range(Hkv):
                    self.assertTrue(torch.equal(nhd[s, h, :], tensor[b, h, s, :]))


class TestFlashInferEndToEnd(unittest.TestCase):
    """GPU + FlashInfer: compare adapter output vs PyTorch reference SDPA."""

    def setUp(self):
        if not torch.cuda.is_available():
            self.skipTest("CUDA not available")
        try:
            import flashinfer  # noqa: F401
        except ImportError:
            self.skipTest("flashinfer not installed")

    def test_correctness_vs_torch_ref(self):
        """FlashInfer adapter output should match PyTorch SDPA reference."""
        from src.kernels.adapters.flashinfer_adapter import decode_attn_flashinfer
        from src.quant.asymmetric_quant import (
            quantize_asymmetric_per_channel,
            quantize_asymmetric_per_token,
        )

        torch.manual_seed(42)
        B, Hq, Hkv, S, D = 1, 8, 2, 32, 64
        device = "cuda"

        # Build FP16 Q, K, V
        q = torch.randn(B, Hq, D, dtype=torch.float16, device=device)
        k_fp = torch.randn(B, Hkv, S, D, dtype=torch.float16, device=device)
        v_fp = torch.randn(B, Hkv, S, D, dtype=torch.float16, device=device)

        sm_scale = 1.0 / (D ** 0.5)

        # --- Quantize KV to INT4 asymmetric, then call adapter ---
        k_q, k_scale, k_zp = quantize_asymmetric_per_channel(k_fp.float())
        v_q, v_scale, v_zp = quantize_asymmetric_per_token(v_fp.float())
        k_packed = pack_int4(k_q)
        v_packed = pack_int4(v_q)
        context_lens = torch.tensor([S], dtype=torch.int32, device=device)

        adapter_output = decode_attn_flashinfer(
            q, k_packed, v_packed, k_scale, k_zp, v_scale, v_zp,
            context_lens, sm_scale=sm_scale,
        )

        # Build quantised reference (dequant → PyTorch SDPA)
        k_deq = dequantize_asymmetric_per_channel(k_q, k_scale, k_zp).to(torch.float16)
        v_deq = dequantize_asymmetric_per_token(v_q, v_scale, v_zp).to(torch.float16)
        n_rep = Hq // Hkv
        k_deq_exp = k_deq.repeat_interleave(n_rep, dim=1)
        v_deq_exp = v_deq.repeat_interleave(n_rep, dim=1)
        q_ref = q.unsqueeze(2)  # [B, Hq, 1, D]
        attn_w = torch.matmul(q_ref, k_deq_exp.transpose(-1, -2)) * sm_scale
        attn_w = torch.softmax(attn_w, dim=-1)
        quant_ref = torch.matmul(attn_w, v_deq_exp).squeeze(2)

        self.assertEqual(adapter_output.shape, quant_ref.shape)
        self.assertTrue(
            torch.allclose(adapter_output, quant_ref, atol=1e-2, rtol=1e-2),
            f"Max diff: {(adapter_output - quant_ref).abs().max().item():.6f}",
        )


class TestImportGuard(unittest.TestCase):
    """Adapter module should import without FlashInfer; only the function call needs it."""

    def test_module_imports_without_flashinfer(self):
        """Importing the adapter module should not raise even if flashinfer is absent."""
        import importlib
        mod = importlib.import_module("src.kernels.adapters.flashinfer_adapter")
        self.assertTrue(hasattr(mod, "decode_attn_flashinfer"))


if __name__ == "__main__":
    unittest.main()
