
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

import os
from typing import Optional

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
    # Program ID — grid is 2D: (Batch, N_Heads)
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
    
    # KRN-014: Pre-compute loop-invariant index vectors outside the loop.
    offs_g = tl.arange(0, NUM_GROUPS)
    group_indices = offs_d // GROUP_SIZE  # noqa: F841 — kept for documentation

    # Runtime loop avoids pathological compile-time unrolling at very long context lengths.
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
        
        ks_ptrs = ks_base + (offs_n[:, None] * stride_ks_s) + (offs_g[None, :] * stride_ks_g)
        k_scale = tl.load(ks_ptrs, mask=mask[:, None], other=1.0) # [BLOCK, NUM_GROUPS]
        
        # Broadcast Scale to Head Dim
        # Reshape k_scale to [BLOCK_SIZE, NUM_GROUPS, 1] ? 
        # Effectively we want k_scale[:, d // GROUP_SIZE]
        # TRITON trick: view and expand
        # k_scale_expanded = tl.view(k_scale, [BLOCK_SIZE, NUM_GROUPS, 1])
        # k_scale_expanded = tl.broadcast_to(...) 
        # This works if HEAD_DIM = NUM_GROUPS * GROUP_SIZE is strictly blocked.
        
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
        # KRN-005: Using elementwise mul + reduce instead of tl.dot because beta is
        # a 1-D vector (not a matrix), so tl.dot's tensor-core path doesn't apply.
        # A future optimisation could reshape beta to [1, BLOCK] and use tl.dot
        # for [1, BLOCK] x [BLOCK, HEAD_DIM] if profiling shows it's beneficial.
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


def decode_attn_int8(
    q,
    k_cache,
    v_cache,
    k_scale,
    v_scale,
    context_lens,
    sm_scale=None,
    debug_stats: Optional[dict] = None,
    layer_idx: Optional[int] = None,
    block_size: Optional[int] = None,
):
    """
    Wrapper for Triton kernel.
    """
    if sm_scale is None:
        sm_scale = 1.0 / (q.shape[-1] ** 0.5)

    if q.ndim != 3:
        raise ValueError(f"q must have shape [B, Hq, D], got {tuple(q.shape)}")
    if k_cache.ndim != 4 or v_cache.ndim != 4:
        raise ValueError(
            f"k_cache/v_cache must have shape [B, Hkv, S, D], got {tuple(k_cache.shape)} / {tuple(v_cache.shape)}"
        )
    if k_scale.ndim != 4 or v_scale.ndim != 4:
        raise ValueError(
            f"k_scale/v_scale must have shape [B, Hkv, S, G], got {tuple(k_scale.shape)} / {tuple(v_scale.shape)}"
        )
    if context_lens.ndim != 1:
        raise ValueError(f"context_lens must be 1D, got {tuple(context_lens.shape)}")
    if not q.is_cuda:
        raise ValueError("decode_attn_int8 requires CUDA tensors.")

    batch, q_heads, head_dim = q.shape
    # KRN-007: Triton reshape/broadcast operations require HEAD_DIM to be a
    # power of 2 (tl.reshape, tl.arange constraints).
    if head_dim == 0 or (head_dim & (head_dim - 1)) != 0:
        raise ValueError(
            f"HEAD_DIM must be a power of 2, got {head_dim}. "
            "Triton kernel uses tl.reshape which requires power-of-2 tile dimensions."
        )
    # q: [batch, q_heads, head_dim]
    # k_cache/v_cache: [batch, kv_heads, max_seq, head_dim]
    # k_scale/v_scale: [batch, kv_heads, max_seq, num_groups]

    # Validation
    if k_cache.shape[0] != batch or v_cache.shape[0] != batch:
        raise ValueError(
            f"Batch mismatch: q={batch}, k={k_cache.shape[0]}, v={v_cache.shape[0]}"
        )
    if k_cache.shape[-1] != head_dim or v_cache.shape[-1] != head_dim:
        raise ValueError(
            f"Head dim mismatch: q={head_dim}, k={k_cache.shape[-1]}, v={v_cache.shape[-1]}"
        )
    if k_cache.shape[:3] != v_cache.shape[:3]:
        raise ValueError(
            f"k/v cache shape mismatch: {tuple(k_cache.shape)} vs {tuple(v_cache.shape)}"
        )
    if k_scale.shape[:3] != k_cache.shape[:3] or v_scale.shape[:3] != v_cache.shape[:3]:
        raise ValueError(
            "Scale and cache shapes mismatch: "
            f"k_scale={tuple(k_scale.shape)}, v_scale={tuple(v_scale.shape)}, "
            f"k={tuple(k_cache.shape)}, v={tuple(v_cache.shape)}"
        )
    if context_lens.shape[0] != batch:
        raise ValueError(
            f"context_lens batch mismatch: expected {batch}, got {context_lens.shape[0]}"
        )

    kv_heads = k_cache.shape[1]
    if q_heads % kv_heads != 0:
        raise ValueError(
            f"GQA head mismatch: q_heads={q_heads} must be a multiple of kv_heads={kv_heads}"
        )
    n_rep = q_heads // kv_heads

    num_groups = k_scale.shape[-1]
    if num_groups <= 0:
        raise ValueError(f"num_groups must be > 0, got {num_groups}")
    if head_dim % num_groups != 0:
        raise ValueError(
            f"head_dim {head_dim} must be divisible by num_groups {num_groups}"
        )
    group_size = head_dim // num_groups
    max_seq = int(k_cache.shape[2])
    max_ctx_in_batch = int(context_lens.max().item())
    min_ctx_in_batch = int(context_lens.min().item())
    if min_ctx_in_batch < 0:
        raise ValueError(f"context_lens must be >= 0, got min={min_ctx_in_batch}")
    if max_ctx_in_batch > max_seq:
        raise ValueError(
            f"context_lens max ({max_ctx_in_batch}) exceeds cache seq dim ({max_seq})"
        )

    # ENG-016: If all context lengths are 0, return zeros immediately to avoid
    # NaN from softmax divide-by-zero inside the kernel.
    if max_ctx_in_batch == 0:
        return torch.zeros_like(q)

    # ENG-015: Kernel always outputs fp16. If q is not fp16, convert q to fp16
    # for kernel computation, then convert output back to original dtype.
    original_dtype = q.dtype
    if original_dtype != torch.float16:
        q = q.to(torch.float16)

    output = torch.empty_like(q)

    if block_size is None:
        env_block_size = os.environ.get("KV_TRITON_BLOCK_SIZE")
        if env_block_size:
            try:
                block_size = int(env_block_size)
            except ValueError as exc:
                raise ValueError(
                    f"KV_TRITON_BLOCK_SIZE must be an integer, got {env_block_size!r}"
                ) from exc
        else:
            # KRN-010: Using heuristic block selection instead of @triton.autotune.
            # Autotune adds warmup latency on first call per config, which is
            # problematic for benchmarking with varying seq_len.  The two-tier
            # heuristic (64 for short ctx, 128 for long) covers our target models
            # well.  Override via KV_TRITON_BLOCK_SIZE env var if needed.
            block_size = 128 if max_ctx_in_batch >= 8192 else 64

    if block_size not in (32, 64, 128, 256):
        raise ValueError(
            f"Unsupported block_size={block_size}. Choose from [32, 64, 128, 256]."
        )

    # Grid: (Batch, Heads)
    grid = (batch, q_heads)

    if isinstance(debug_stats, dict):
        debug_stats["triton_kernel_calls"] = int(debug_stats.get("triton_kernel_calls", 0)) + 1
        debug_stats["triton_block_size"] = int(block_size)
        if layer_idx is not None:
            triton_layer_hits = debug_stats.setdefault("triton_layer_hits", {})
            layer_key = str(layer_idx)
            triton_layer_hits[layer_key] = int(triton_layer_hits.get(layer_key, 0)) + 1

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
        BLOCK_SIZE=block_size,
        GROUP_SIZE=group_size,
        NUM_GROUPS=num_groups,
        N_REP=n_rep,
    )

    # ENG-016: Zero out output rows for batch entries with context_lens=0
    # to prevent NaN from kernel's softmax divide-by-zero.
    if min_ctx_in_batch == 0:
        zero_mask = (context_lens == 0)  # [B]
        output[zero_mask] = 0.0

    # ENG-015: Convert output back to original dtype if needed.
    if original_dtype != torch.float16:
        output = output.to(original_dtype)

    return output
