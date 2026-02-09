
"""
Fused INT8 Decode Attention Kernel using Triton.

This kernel implements the Flash-Decoding style attention for the decoding phase (Query Length = 1).
It handles:
1. Loading INT8 Key/Value cache from global memory.
2. On-the-fly dequantization using group-wise scales.
3. Online Softmax (FlashAttention) to avoid materializing full score matrix.
4. Outputting FP16 attention result.

Pseudo-Code Logic:
------------------
Kernel `decode_attn_int8_kernel`:
    Inputs:
        Q: [Batch, N_Heads, Head_Dim] (FP16)
        K_int8: [Batch, N_Heads, Max_Seq_Len, Head_Dim] (INT8)
        V_int8: [Batch, N_Heads, Max_Seq_Len, Head_Dim] (INT8)
        K_scale: [Batch, N_Heads, Max_Seq_Len, Num_Groups] (FP16)
        V_scale: [Batch, N_Heads, Max_Seq_Len, Num_Groups] (FP16)
        Context_Lens: [Batch] (Actual sequence length for each request)
        Sm_Scale: float (1.0 / sqrt(head_dim))
        
    Grid: (Batch * N_Heads)
    
    Program ID (pid):
        batch_id = pid // N_Heads
        head_id = pid % N_Heads
        
    Determine Sequence Length:
        cur_seq_len = Context_Lens[batch_id]
        
    Pointers:
        Q_ptr = Q + (batch_id * N_Heads + head_id) * Head_Dim
        K_ptr_base = K_int8 + (batch_id * N_Heads + head_id) * Max_Seq_Len * Head_Dim
        V_ptr_base = V_int8 ...
        Scale_K_ptr_base = ...
        
    Load Q:
        q = load(Q_ptr + arange(Head_Dim))
        
    Initialize Accumulators:
        acc = zeros([Head_Dim])  # The weighted sum output
        l = 0.0                  # Denominator for softmax (sum of exp)
        m = -inf                 # Max score for numerical stability
        
    Loop over KV blocks (BLOCK_SIZE):
        for start_idx in range(0, cur_seq_len, BLOCK_SIZE):
            # Check boundaries
            full_block = start_idx + BLOCK_SIZE <= cur_seq_len
            
            # 1. Load INT8 K block
            # Shape: [BLOCK_SIZE, Head_Dim]
            k_int8 = load(K_ptr_base + ...)
            
            # 2. Load K Scales
            # Shape: [BLOCK_SIZE, Num_Groups]
            k_scale = load(Scale_K_ptr_base + ...)
            
            # 3. Dequantize K
            # Broadcast scales: [BLOCK_SIZE, Num_Groups] -> [BLOCK_SIZE, Num_Groups, Group_Size]
            # k_fp16 = k_int8 * k_scale (broadcasted)
            
            # 4. Compute QK^T
            # q: [Head_Dim], k_fp16: [BLOCK_SIZE, Head_Dim]
            # score = sum(q * k_fp16, axis=1) -> [BLOCK_SIZE]
            score = dot(q, k_fp16.T)
            score *= Sm_Scale
            
            # 5. Online Softmax Update
            # Get max in this block
            block_max = max(score)
            
            # Update global max 'm'
            m_new = max(m, block_max)
            
            # Calculate correction factors
            # alpha = exp(m - m_new)
            # beta = exp(score - m_new)
            
            # Update 'l' (sum of exps)
            # l_new = l * alpha + sum(beta)
            
            # 6. Load INT8 V block & Scale
            v_int8 = load(V_ptr_base + ...)
            v_scale = load(...)
            v_fp16 = v_int8 * v_scale
            
            # 7. Accumulate Output
            # acc = acc * alpha + dot(beta, v_fp16)
            
            # Update state
            m = m_new
            l = l_new
            
    Finalize:
        acc = acc / l
        store(Output_ptr, acc)

"""

import torch
import triton
import triton.language as tl


@triton.jit
def decode_attn_int8_kernel(
    Q_ptr,              # [Batch, N_Heads, Head_Dim]
    K_ptr,              # [Batch, N_Heads, Max_Seq_Len, Head_Dim]
    V_ptr,              # [Batch, N_Heads, Max_Seq_Len, Head_Dim]
    K_Scale_ptr,        # [Batch, N_Heads, Max_Seq_Len, Num_Groups]
    V_Scale_ptr,        # [Batch, N_Heads, Max_Seq_Len, Num_Groups]
    Context_Lens_ptr,   # [Batch]
    Output_ptr,         # [Batch, N_Heads, Head_Dim]
    sm_scale,
    stride_q_b, stride_q_h, stride_q_d,
    stride_k_b, stride_k_h, stride_k_s, stride_k_d,
    stride_v_b, stride_v_h, stride_v_s, stride_v_d,
    stride_ks_b, stride_ks_h, stride_ks_s, stride_ks_g,
    stride_vs_b, stride_vs_h, stride_vs_s, stride_vs_g,
    stride_o_b, stride_o_h, stride_o_d,
    HEAD_DIM: tl.constexpr,
    BLOCK_SIZE: tl.constexpr,
    GROUP_SIZE: tl.constexpr,
    NUM_GROUPS: tl.constexpr,
    N_REP: tl.constexpr,
):
    # Program ID
    pid = tl.program_id(0)
    # We launch grid as (Batch * N_Heads)
    # Reconstruct batch and head indices
    # We need n_heads to decode pid
    # BUT, we can't pass n_heads as tensor if it's constant or we can calculate it from grid?
    # Usually we pass strides. 
    # Let's assume grid is 1D: batch * n_heads.
    # We can infer valid indices if we knew n_heads. 
    # Or simpler: The strides tell us everything if we handle pointers linearly?
    # Actually, to get Context_Len[batch_id], we need batch_id.
    # So we MUST pass n_heads or stride related info.
    # Correction: pass n_heads as argument or deduce from strides?
    # Standard practice: grid = (Batch, N_Heads). 2D grid is easier.
    
    batch_id = tl.program_id(0)
    head_id = tl.program_id(1)
    # GQA mapping: multiple query heads share one KV head.
    kv_head_id = head_id // N_REP
    
    # 1. Load Query
    # Q location: batch_id, head_id
    q_ptr = Q_ptr + batch_id * stride_q_b + head_id * stride_q_h
    # Q range: [0, HEAD_DIM]
    offs_d = tl.arange(0, HEAD_DIM)
    q = tl.load(q_ptr + offs_d * stride_q_d)
    
    # 2. Get Context Length
    ctx_len = tl.load(Context_Lens_ptr + batch_id)
    
    # 3. Pointers to KV
    # K Base: batch, head
    k_base = K_ptr + batch_id * stride_k_b + kv_head_id * stride_k_h
    v_base = V_ptr + batch_id * stride_v_b + kv_head_id * stride_v_h
    ks_base = K_Scale_ptr + batch_id * stride_ks_b + kv_head_id * stride_ks_h
    vs_base = V_Scale_ptr + batch_id * stride_vs_b + kv_head_id * stride_vs_h
    
    # Initialize Accumulators
    m_i = -float('inf') # Max score
    l_i = 0.0           # Sum exp
    acc = tl.zeros([HEAD_DIM], dtype=tl.float32) # Accumulator
    
    # Loop over Sequence Length
    # We step by BLOCK_SIZE
    for start_n in range(0, ctx_len, BLOCK_SIZE):
        # Current block indices: [start_n : start_n + BLOCK_SIZE]
        offs_n = start_n + tl.arange(0, BLOCK_SIZE)
        # Mask for valid tokens
        mask = offs_n < ctx_len
        
        # --- LOAD K, Scale_K ---
        # K Shape: [BLOCK_SIZE, HEAD_DIM]
        # Pointers: base + offs_n[:, None] * stride_s + offs_d[None, :] * stride_d
        k_ptrs = k_base + (offs_n[:, None] * stride_k_s) + (offs_d[None, :] * stride_k_d)
        k_int8 = tl.load(k_ptrs, mask=mask[:, None], other=0.0)
        
        # Scale locations:
        # Scale Shape: [BLOCK_SIZE, NUM_GROUPS]
        # We need to map HEAD_DIM to NUM_GROUPS
        # HEAD_DIM index 'd' maps to group index 'd // GROUP_SIZE'
        # To do this efficiently, we load all scales for the block: [BLOCK_SIZE, NUM_GROUPS]
        # Then broadcast.
        
        # But `tl.load` of non-contiguous scale mapping might be tricky if we construct it pixel-wise.
        # Better: Load scales [BLOCK_SIZE, NUM_GROUPS] 
        # Then expand/broadcast to [BLOCK_SIZE, HEAD_DIM]
        
        offs_g = tl.arange(0, NUM_GROUPS)
        ks_ptrs = ks_base + (offs_n[:, None] * stride_ks_s) + (offs_g[None, :] * stride_ks_g)
        k_scale = tl.load(ks_ptrs, mask=mask[:, None], other=1.0) # [BLOCK, NUM_GROUPS]
        
        # Broadcast Scale to Head Dim
        # Reshape k_scale to [BLOCK_SIZE, NUM_GROUPS, 1] ? 
        # Effectively we want k_scale[:, d // GROUP_SIZE]
        # TRITON trick: view and expand
        # k_scale_expanded = tl.view(k_scale, [BLOCK_SIZE, NUM_GROUPS, 1])
        # k_scale_expanded = tl.broadcast_to(...) 
        # This works if HEAD_DIM = NUM_GROUPS * GROUP_SIZE is strictly blocked.
        
        # Actually simplest way in Triton:
        # Construct index mapping
        group_indices = offs_d // GROUP_SIZE
        # k_scale is [BLOCK, NUM_GROUPS]
        # We want [BLOCK, HEAD_DIM]
        # Triton doesn't support advanced integer indexing nicely like numpy?
        # A clearer way: 
        # Reshape K_int8 to [BLOCK, NUM_GROUPS, GROUP_SIZE]
        # Load Scale as [BLOCK, NUM_GROUPS, 1]
        # Multiply
        # Reshape back to [BLOCK, HEAD_DIM]
        
        k_int8_reshaped = tl.reshape(k_int8, [BLOCK_SIZE, NUM_GROUPS, GROUP_SIZE])
        k_scale_reshaped = tl.reshape(k_scale, [BLOCK_SIZE, NUM_GROUPS, 1])
        
        # Dequantize to FP32 for better precision
        k_fp32 = k_int8_reshaped.to(tl.float32) * k_scale_reshaped.to(tl.float32)
        k_fp32 = tl.reshape(k_fp32, [BLOCK_SIZE, HEAD_DIM])
        
        # --- COMPUTE ATTENTION SCORES ---
        # q: [HEAD_DIM]
        # k_fp16: [BLOCK_SIZE, HEAD_DIM]
        # score[i] = sum(q * k[i])
        # logic: q[None, :] * k_fp32[:, :] -> sum over dim 1 (FP32 for precision)
        q_fp32 = q.to(tl.float32)
        qk = tl.sum(q_fp32[None, :] * k_fp32, axis=1) # [BLOCK_SIZE]
        qk *= sm_scale
        
        # Apply mask (set invalid scores to -inf)
        qk = tl.where(mask, qk, float("-inf"))
        
        # --- ONLINE SOFTMAX ---
        m_i_new = tl.max(qk, 0)
        m_ij = tl.maximum(m_i, m_i_new)
        
        # alpha = exp(m_i - m_ij)
        # beta = exp(qk - m_ij)
        alpha = tl.exp(m_i - m_ij)
        beta = tl.exp(qk - m_ij)
        
        l_i_new = tl.sum(beta, 0) # Sum for current block
        l_ij = l_i * alpha + l_i_new
        
        # --- LOAD V, Scale_V ---
        v_ptrs = v_base + (offs_n[:, None] * stride_v_s) + (offs_d[None, :] * stride_v_d)
        v_int8 = tl.load(v_ptrs, mask=mask[:, None], other=0.0)
        
        vs_ptrs = vs_base + (offs_n[:, None] * stride_vs_s) + (offs_g[None, :] * stride_vs_g)
        v_scale = tl.load(vs_ptrs, mask=mask[:, None], other=1.0)
        
        # Dequantize V to FP32 for better precision
        v_int8_reshaped = tl.reshape(v_int8, [BLOCK_SIZE, NUM_GROUPS, GROUP_SIZE])
        v_scale_reshaped = tl.reshape(v_scale, [BLOCK_SIZE, NUM_GROUPS, 1])
        v_fp32 = v_int8_reshaped.to(tl.float32) * v_scale_reshaped.to(tl.float32)
        v_fp32 = tl.reshape(v_fp32, [BLOCK_SIZE, HEAD_DIM])
        
        # --- ACCUMULATE ---
        # acc = acc * alpha + beta @ v
        # beta is [BLOCK_SIZE], v is [BLOCK_SIZE, HEAD_DIM]
        # weight v by beta
        # beta[:, None] * v_fp32 -> [BLOCK, HEAD_DIM] -> sum over BLOCK (all FP32)
        weighted_v = tl.sum(beta[:, None] * v_fp32, axis=0)
        
        acc = acc * alpha + weighted_v  # Both are FP32 now
        
        # Update running stats
        l_i = l_ij
        m_i = m_ij

    # Finalize
    # Out = acc / l
    acc = acc / l_i
    
    # Store Output
    o_ptr = Output_ptr + batch_id * stride_o_b + head_id * stride_o_h
    tl.store(o_ptr + offs_d * stride_o_d, acc.to(tl.float16))


def decode_attn_int8(q, k_cache, v_cache, k_scale, v_scale, context_lens, sm_scale=None):
    """
    Wrapper for Triton kernel.
    """
    if sm_scale is None:
        sm_scale = 1.0 / (q.shape[-1] ** 0.5)
        
    batch, q_heads, head_dim = q.shape
    # q: [batch, q_heads, head_dim]
    # k_cache/v_cache: [batch, kv_heads, max_seq, head_dim]
    # k_scale/v_scale: [batch, kv_heads, max_seq, num_groups]
    
    # Validation
    assert k_cache.shape[-1] == head_dim
    assert k_scale.ndim == 4
    assert v_cache.shape[:3] == k_cache.shape[:3]
    assert v_scale.shape[:3] == k_scale.shape[:3]

    kv_heads = k_cache.shape[1]
    if q_heads % kv_heads != 0:
        raise ValueError(
            f"GQA head mismatch: q_heads={q_heads} must be a multiple of kv_heads={kv_heads}"
        )
    n_rep = q_heads // kv_heads
    
    num_groups = k_scale.shape[-1]
    group_size = head_dim // num_groups
    
    output = torch.empty_like(q)
    
    # Grid: (Batch, Heads)
    grid = (batch, q_heads)
    
    # Block size 128 usually good
    BLOCK_SIZE = 128
    
    # Launch
    decode_attn_int8_kernel[grid](
        q, k_cache, v_cache, k_scale, v_scale,
        context_lens,
        output,
        sm_scale,
        
        # Strides (Q)
        q.stride(0), q.stride(1), q.stride(2),
        # Strides (K)
        k_cache.stride(0), k_cache.stride(1), k_cache.stride(2), k_cache.stride(3),
        # Strides (V)
        v_cache.stride(0), v_cache.stride(1), v_cache.stride(2), v_cache.stride(3),
        # Strides (K Scale)
        k_scale.stride(0), k_scale.stride(1), k_scale.stride(2), k_scale.stride(3),
        # Strides (V Scale)
        v_scale.stride(0), v_scale.stride(1), v_scale.stride(2), v_scale.stride(3),
        # Strides (Out)
        output.stride(0), output.stride(1), output.stride(2),
        
        HEAD_DIM=head_dim,
        BLOCK_SIZE=BLOCK_SIZE,
        GROUP_SIZE=group_size,
        NUM_GROUPS=num_groups,
        N_REP=n_rep,
    )
    
    return output
