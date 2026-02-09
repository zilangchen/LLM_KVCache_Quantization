
import unittest
import torch
import math
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.kernels import decode_attn_int8
    HAS_TRITON = True
except ImportError:
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
        
    def test_correctness(self):
        # 1. Prepare Inputs
        q = torch.randn((self.B, self.H, self.D), dtype=torch.float16, device=self.device)
        
        # Random integers for K/V in [-127, 127]
        k_int8 = torch.randint(-127, 127, (self.B, self.H, self.S, self.D), dtype=torch.int8, device=self.device)
        v_int8 = torch.randint(-127, 127, (self.B, self.H, self.S, self.D), dtype=torch.int8, device=self.device)
        
        # Positive scales
        k_scale = torch.rand((self.B, self.H, self.S, self.num_groups), dtype=torch.float16, device=self.device) * 0.1
        v_scale = torch.rand((self.B, self.H, self.S, self.num_groups), dtype=torch.float16, device=self.device) * 0.1
        
        # Context lengths (some variation)
        context_lens = torch.randint(low=self.S//2, high=self.S, size=(self.B,), dtype=torch.int32, device=self.device)
        
        # 2. Reference Implementation
        # We process each request in batch independently for simplicity in ref check
        ref_outputs = []
        tri_outputs = []
        
        # Run Triton Kernel
        # Note: Triton kernel expects context_lens to handle variable lengths
        triton_out = decode_attn_int8(q, k_int8, v_int8, k_scale, v_scale, context_lens)
        
        # Run Torch Reference
        for b in range(self.B):
            ctx_len = context_lens[b].item()
            
            # Slicing active sequence
            curr_q = q[b] # [H, D]
            curr_k_int8 = k_int8[b, :, :ctx_len, :] # [H, S_active, D]
            curr_v_int8 = v_int8[b, :, :ctx_len, :]
            curr_k_scale = k_scale[b, :, :ctx_len, :] # [H, S_active, NGS]
            curr_v_scale = v_scale[b, :, :ctx_len, :]
            
            # Dequantize K
            # [H, S, D] -> [H, S, NGS, GS]
            k_reshaped = curr_k_int8.view(self.H, ctx_len, self.num_groups, self.group_size)
            k_scale_expanded = curr_k_scale.unsqueeze(-1) # [H, S, NGS, 1]
            k_dequant = (k_reshaped.to(torch.float16) * k_scale_expanded).view(self.H, ctx_len, self.D)
            
            # Dequantize V
            v_reshaped = curr_v_int8.view(self.H, ctx_len, self.num_groups, self.group_size)
            v_scale_expanded = curr_v_scale.unsqueeze(-1)
            v_dequant = (v_reshaped.to(torch.float16) * v_scale_expanded).view(self.H, ctx_len, self.D)
            
            # Attention [H, 1, D] attention on [H, S, D]
            # scaled_dot_product_attention expects [Batch, Heads, Seq, Dim]
            # Here we have [H, S, D]. Let's unsqueeze batch dim 0
            # Q: [1, H, 1, D]
            # K: [1, H, S, D]
            # V: [1, H, S, D]
            q_in = curr_q.unsqueeze(0).unsqueeze(2)
            k_in = k_dequant.unsqueeze(0)
            v_in = v_dequant.unsqueeze(0)
            
            ref_out = torch.nn.functional.scaled_dot_product_attention(q_in, k_in, v_in)
            # Result: [1, H, 1, D] -> [H, D]
            ref_outputs.append(ref_out.squeeze(0).squeeze(1))
            
        ref_tensor = torch.stack(ref_outputs) # [B, H, D]
        
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
        k_int8 = torch.randint(-127, 127, (self.B, kv_heads, self.S, self.D), dtype=torch.int8, device=self.device)
        v_int8 = torch.randint(-127, 127, (self.B, kv_heads, self.S, self.D), dtype=torch.int8, device=self.device)
        k_scale = torch.rand((self.B, kv_heads, self.S, self.num_groups), dtype=torch.float16, device=self.device) * 0.1
        v_scale = torch.rand((self.B, kv_heads, self.S, self.num_groups), dtype=torch.float16, device=self.device) * 0.1
        context_lens = torch.randint(low=self.S//2, high=self.S, size=(self.B,), dtype=torch.int32, device=self.device)

        triton_out = decode_attn_int8(q, k_int8, v_int8, k_scale, v_scale, context_lens)

        ref_outputs = []
        for b in range(self.B):
            ctx_len = context_lens[b].item()
            curr_q = q[b]  # [q_heads, D]

            curr_k_int8 = k_int8[b, :, :ctx_len, :]  # [kv_heads, S, D]
            curr_v_int8 = v_int8[b, :, :ctx_len, :]
            curr_k_scale = k_scale[b, :, :ctx_len, :]  # [kv_heads, S, num_groups]
            curr_v_scale = v_scale[b, :, :ctx_len, :]

            # Dequantize KV heads then repeat to match q heads.
            k_reshaped = curr_k_int8.view(kv_heads, ctx_len, self.num_groups, self.group_size)
            k_dequant_kv = (k_reshaped.to(torch.float16) * curr_k_scale.unsqueeze(-1)).view(kv_heads, ctx_len, self.D)
            v_reshaped = curr_v_int8.view(kv_heads, ctx_len, self.num_groups, self.group_size)
            v_dequant_kv = (v_reshaped.to(torch.float16) * curr_v_scale.unsqueeze(-1)).view(kv_heads, ctx_len, self.D)

            k_dequant = k_dequant_kv.repeat_interleave(n_rep, dim=0)  # [q_heads, S, D]
            v_dequant = v_dequant_kv.repeat_interleave(n_rep, dim=0)

            q_in = curr_q.unsqueeze(0).unsqueeze(2)  # [1, q_heads, 1, D]
            k_in = k_dequant.unsqueeze(0)            # [1, q_heads, S, D]
            v_in = v_dequant.unsqueeze(0)
            ref_out = torch.nn.functional.scaled_dot_product_attention(q_in, k_in, v_in)
            ref_outputs.append(ref_out.squeeze(0).squeeze(1))  # [q_heads, D]

        ref_tensor = torch.stack(ref_outputs)  # [B, q_heads, D]
        print(f"[GQA] Max Diff: {(ref_tensor - triton_out).abs().max()}")
        print(f"[GQA] Mean Diff: {(ref_tensor - triton_out).abs().mean()}")
        self.assertTrue(torch.allclose(ref_tensor, triton_out, atol=1e-2, rtol=1e-2))

if __name__ == "__main__":
    unittest.main()
