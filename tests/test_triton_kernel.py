
import unittest
import torch
import math
import sys
import os

# Add project root to path (insert at front to avoid shadowing by same-named modules)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.kernels import decode_attn_int4, decode_attn_int8
    from src.quant.int4_basic import pack_int4, unpack_int4
    HAS_TRITON = True
except Exception:  # Catch all failures (ImportError, RuntimeError from Triton JIT, etc.)
    HAS_TRITON = False
    print("Triton not available or kernel import failed.")

class TestTritonDecodeAttn(unittest.TestCase):
    
    def setUp(self):
        if not torch.cuda.is_available():
            self.skipTest("CUDA not available")
        if not HAS_TRITON:
            self.skipTest("Triton not importable")
            
        torch.manual_seed(42)
        self.B = 2
        self.H = 4
        self.D = 128
        self.S = 256
        self.group_size = 64
        self.num_groups = self.D // self.group_size
        self.device = "cuda"

    def _torch_ref_decode(
        self,
        q: torch.Tensor,
        k_int8: torch.Tensor,
        v_int8: torch.Tensor,
        k_scale: torch.Tensor,
        v_scale: torch.Tensor,
        context_lens: torch.Tensor,
    ) -> torch.Tensor:
        batch, q_heads, head_dim = q.shape
        kv_heads = k_int8.shape[1]
        n_rep = q_heads // kv_heads
        sm_scale = 1.0 / (head_dim ** 0.5)

        outs = []
        for b in range(batch):
            ctx_len = int(context_lens[b].item())
            curr_q = q[b]  # [Hq, D]

            curr_k_int8 = k_int8[b, :, :ctx_len, :]
            curr_v_int8 = v_int8[b, :, :ctx_len, :]
            curr_k_scale = k_scale[b, :, :ctx_len, :]
            curr_v_scale = v_scale[b, :, :ctx_len, :]

            k_reshaped = curr_k_int8.view(kv_heads, ctx_len, self.num_groups, self.group_size)
            k_dequant_kv = (
                k_reshaped.to(torch.float32) * curr_k_scale.to(torch.float32).unsqueeze(-1)
            ).view(kv_heads, ctx_len, head_dim)
            v_reshaped = curr_v_int8.view(kv_heads, ctx_len, self.num_groups, self.group_size)
            v_dequant_kv = (
                v_reshaped.to(torch.float32) * curr_v_scale.to(torch.float32).unsqueeze(-1)
            ).view(kv_heads, ctx_len, head_dim)

            if n_rep > 1:
                k_dequant = k_dequant_kv.repeat_interleave(n_rep, dim=0)
                v_dequant = v_dequant_kv.repeat_interleave(n_rep, dim=0)
            else:
                k_dequant = k_dequant_kv
                v_dequant = v_dequant_kv

            scores = torch.einsum("hd,hsd->hs", curr_q.to(torch.float32), k_dequant) * sm_scale
            probs = torch.softmax(scores, dim=-1)
            out = torch.einsum("hs,hsd->hd", probs, v_dequant).to(dtype=curr_q.dtype)
            outs.append(out)

        return torch.stack(outs, dim=0)
        
    def test_correctness(self):
        # 1. Prepare Inputs
        q = torch.randn((self.B, self.H, self.D), dtype=torch.float16, device=self.device)
        
        # Random integers for K/V in [-128, 127] (full int8 range).
        # TST-045: upper bound must be 128 (exclusive) so that 127 can be generated.
        k_int8 = torch.randint(-128, 128, (self.B, self.H, self.S, self.D), dtype=torch.int8, device=self.device)
        v_int8 = torch.randint(-128, 128, (self.B, self.H, self.S, self.D), dtype=torch.int8, device=self.device)
        
        # Positive scales
        k_scale = torch.rand((self.B, self.H, self.S, self.num_groups), dtype=torch.float16, device=self.device) * 0.1
        v_scale = torch.rand((self.B, self.H, self.S, self.num_groups), dtype=torch.float16, device=self.device) * 0.1
        
        # Fixed context lengths to keep the test deterministic.
        context_lens = torch.tensor([self.S - 7, self.S - 43], dtype=torch.int32, device=self.device)

        # Run Triton Kernel
        # Note: Triton kernel expects context_lens to handle variable lengths
        triton_out = decode_attn_int8(q, k_int8, v_int8, k_scale, v_scale, context_lens)
        ref_tensor = self._torch_ref_decode(q, k_int8, v_int8, k_scale, v_scale, context_lens)
        
        # 3. Compare
        # Tolerances: INT8 quantized attention can have some noise, but here we compare 
        # equivalent math (dequant -> dot vs fused). 
        # Fused kernel does online softmax which is slightly more precise than standard softmax for large S?
        # But for small S, it should be close.
        # However, accumulation order might differ.
        
        print(f"Max Diff: {(ref_tensor - triton_out).abs().max()}")
        print(f"Mean Diff: {(ref_tensor - triton_out).abs().mean()}")
        
        self.assertTrue(torch.allclose(ref_tensor, triton_out, atol=1e-2, rtol=1e-2))

    def test_gqa_head_mapping(self):
        # Validate GQA mapping behavior: q_heads > kv_heads, with kv heads shared.
        q_heads = 8
        kv_heads = 2
        n_rep = q_heads // kv_heads
        assert n_rep > 1

        q = torch.randn((self.B, q_heads, self.D), dtype=torch.float16, device=self.device)
        # TST-045: upper bound 128 (exclusive) so value 127 can be generated.
        k_int8 = torch.randint(-128, 128, (self.B, kv_heads, self.S, self.D), dtype=torch.int8, device=self.device)
        v_int8 = torch.randint(-128, 128, (self.B, kv_heads, self.S, self.D), dtype=torch.int8, device=self.device)
        k_scale = torch.rand((self.B, kv_heads, self.S, self.num_groups), dtype=torch.float16, device=self.device) * 0.1
        v_scale = torch.rand((self.B, kv_heads, self.S, self.num_groups), dtype=torch.float16, device=self.device) * 0.1
        context_lens = torch.tensor([self.S - 5, self.S - 29], dtype=torch.int32, device=self.device)

        triton_out = decode_attn_int8(q, k_int8, v_int8, k_scale, v_scale, context_lens)
        ref_tensor = self._torch_ref_decode(q, k_int8, v_int8, k_scale, v_scale, context_lens)
        print(f"[GQA] Max Diff: {(ref_tensor - triton_out).abs().max()}")
        print(f"[GQA] Mean Diff: {(ref_tensor - triton_out).abs().mean()}")
        self.assertTrue(torch.allclose(ref_tensor, triton_out, atol=1e-2, rtol=1e-2))

    def test_int4_wrapper_matches_int8_kernel(self):
        q = torch.randn((self.B, self.H, self.D), dtype=torch.float16, device=self.device)
        # INT4 logical values in [-7, 7]
        k_int4 = torch.randint(-7, 8, (self.B, self.H, self.S, self.D), dtype=torch.int8, device=self.device)
        v_int4 = torch.randint(-7, 8, (self.B, self.H, self.S, self.D), dtype=torch.int8, device=self.device)
        k_packed = pack_int4(k_int4)
        v_packed = pack_int4(v_int4)

        k_scale = torch.rand((self.B, self.H, self.S, self.num_groups), dtype=torch.float16, device=self.device) * 0.2
        v_scale = torch.rand((self.B, self.H, self.S, self.num_groups), dtype=torch.float16, device=self.device) * 0.2
        context_lens = torch.tensor([self.S - 11, self.S - 37], dtype=torch.int32, device=self.device)

        out_int4 = decode_attn_int4(
            q=q,
            k_cache_int4=k_packed,
            v_cache_int4=v_packed,
            k_scale=k_scale,
            v_scale=v_scale,
            context_lens=context_lens,
            bit_packed=True,
            head_dim=self.D,
        )
        out_int8_ref = decode_attn_int8(
            q=q,
            k_cache=unpack_int4(k_packed),
            v_cache=unpack_int4(v_packed),
            k_scale=k_scale,
            v_scale=v_scale,
            context_lens=context_lens,
        )

        print(f"[INT4_WRAPPER] Max Diff: {(out_int4 - out_int8_ref).abs().max()}")
        print(f"[INT4_WRAPPER] Mean Diff: {(out_int4 - out_int8_ref).abs().mean()}")
        self.assertTrue(torch.allclose(out_int4, out_int8_ref, atol=1e-2, rtol=1e-2))

    def test_long_context_gqa_correctness(self):
        if os.environ.get("RUN_TRITON_LONG_TEST", "0") != "1":
            self.skipTest("Set RUN_TRITON_LONG_TEST=1 to run long-context Triton stress test.")

        # Long-context guardrail: ensure fused kernel stays numerically stable with
        # near-max sequence length and GQA head mapping.
        # Use a lighter head config so this stays runnable in test environments.
        batch = 1
        q_heads = 2
        kv_heads = 1
        head_dim = 64
        seq_len = int(os.environ.get("TRITON_LONG_SEQ_LEN", "32704"))
        group_size = 32
        num_groups = head_dim // group_size
        n_rep = q_heads // kv_heads

        q = torch.randn((batch, q_heads, head_dim), dtype=torch.float16, device=self.device)
        # TST-045: upper bound 128 (exclusive) so value 127 can be generated.
        k_int8 = torch.randint(
            -128,
            128,
            (batch, kv_heads, seq_len, head_dim),
            dtype=torch.int8,
            device=self.device,
        )
        v_int8 = torch.randint(
            -128,
            128,
            (batch, kv_heads, seq_len, head_dim),
            dtype=torch.int8,
            device=self.device,
        )
        k_scale = (
            torch.rand(
                (batch, kv_heads, seq_len, num_groups),
                dtype=torch.float16,
                device=self.device,
            )
            * 0.1
        )
        v_scale = (
            torch.rand(
                (batch, kv_heads, seq_len, num_groups),
                dtype=torch.float16,
                device=self.device,
            )
            * 0.1
        )
        context_lens = torch.tensor([seq_len], dtype=torch.int32, device=self.device)

        triton_out = decode_attn_int8(q, k_int8, v_int8, k_scale, v_scale, context_lens)

        curr_q = q[0]  # [q_heads, D]
        curr_k_int8 = k_int8[0]  # [kv_heads, S, D]
        curr_v_int8 = v_int8[0]
        curr_k_scale = k_scale[0]  # [kv_heads, S, num_groups]
        curr_v_scale = v_scale[0]

        k_reshaped = curr_k_int8.view(kv_heads, seq_len, num_groups, group_size)
        v_reshaped = curr_v_int8.view(kv_heads, seq_len, num_groups, group_size)
        k_dequant_kv = (k_reshaped.to(torch.float16) * curr_k_scale.unsqueeze(-1)).view(
            kv_heads, seq_len, head_dim
        )
        v_dequant_kv = (v_reshaped.to(torch.float16) * curr_v_scale.unsqueeze(-1)).view(
            kv_heads, seq_len, head_dim
        )

        k_dequant = k_dequant_kv.repeat_interleave(n_rep, dim=0)  # [q_heads, S, D]
        v_dequant = v_dequant_kv.repeat_interleave(n_rep, dim=0)
        # Use explicit q_len=1 attention math instead of SDPA here because SDPA can be
        # extremely slow for this long-sequence shape in some CUDA stack combinations.
        q_ref = curr_q.to(torch.float32)  # [q_heads, D]
        k_ref = k_dequant.to(torch.float32)  # [q_heads, S, D]
        v_ref = v_dequant.to(torch.float32)  # [q_heads, S, D]

        logits = torch.einsum("hd,hsd->hs", q_ref, k_ref) / math.sqrt(head_dim)
        attn = torch.softmax(logits, dim=-1)
        ref_out = torch.einsum("hs,hsd->hd", attn, v_ref).to(torch.float16)
        ref_tensor = ref_out.unsqueeze(0)  # [1, q_heads, D]

        max_diff = (ref_tensor - triton_out).abs().max().item()
        mean_diff = (ref_tensor - triton_out).abs().mean().item()
        print(f"[LONG_GQA] Max Diff: {max_diff}")
        print(f"[LONG_GQA] Mean Diff: {mean_diff}")

        self.assertTrue(torch.allclose(ref_tensor, triton_out, atol=3e-2, rtol=3e-2))

    def test_inv_tau_prescaled_query(self):
        """Verify that pre-scaling Q by inv_tau produces correct results.

        The int8_ours path applies inv_tau by scaling Q before attention:
            attn(inv_tau * Q, K, V) == softmax(inv_tau * Q @ K^T / sqrt(d)) @ V
        This test confirms the kernel handles pre-scaled queries correctly
        by comparing against a reference that applies the same pre-scaling.
        """
        inv_tau = torch.rand(self.H, dtype=torch.float16, device=self.device) * 0.5 + 0.75

        q_raw = torch.randn((self.B, self.H, self.D), dtype=torch.float16, device=self.device)
        q_scaled = q_raw * inv_tau.view(1, -1, 1)

        # TST-045: upper bound 128 (exclusive) so value 127 can be generated.
        k_int8 = torch.randint(-128, 128, (self.B, self.H, self.S, self.D), dtype=torch.int8, device=self.device)
        v_int8 = torch.randint(-128, 128, (self.B, self.H, self.S, self.D), dtype=torch.int8, device=self.device)
        k_scale = torch.rand((self.B, self.H, self.S, self.num_groups), dtype=torch.float16, device=self.device) * 0.1
        v_scale = torch.rand((self.B, self.H, self.S, self.num_groups), dtype=torch.float16, device=self.device) * 0.1
        context_lens = torch.tensor([self.S - 10, self.S - 20], dtype=torch.int32, device=self.device)

        out_scaled = decode_attn_int8(q_scaled, k_int8, v_int8, k_scale, v_scale, context_lens)
        ref_scaled = self._torch_ref_decode(q_scaled, k_int8, v_int8, k_scale, v_scale, context_lens)

        max_diff = (out_scaled - ref_scaled).abs().max().item()
        print(f"[INV_TAU] Max Diff: {max_diff}")
        self.assertTrue(
            torch.allclose(out_scaled, ref_scaled, atol=1e-2, rtol=1e-2),
            f"Pre-scaled query should match reference; max_diff={max_diff}",
        )

        out_raw = decode_attn_int8(q_raw, k_int8, v_int8, k_scale, v_scale, context_lens)
        self.assertFalse(
            torch.allclose(out_scaled, out_raw, atol=1e-3),
            "Scaled and unscaled queries should produce different outputs",
        )


if __name__ == "__main__":
    unittest.main()
