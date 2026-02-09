
import logging
import torch
import math
from src.kernels import decode_attn_int8


import torch
import torch.nn as nn
from typing import Optional, Tuple
from src.kernels import decode_attn_int8

# Wrapper to pass INT8KVCache + LayerIdx + Sequence Length info to the model forward
class INT8CacheWrapper:
    def __init__(self, cache_engine, layer_idx):
        self.engine = cache_engine
        self.layer_idx = layer_idx
        
    def update(self, key_states, value_states, layer_idx, cache_kwargs=None):
        # This is called by original forward if we fallback. 
        # But we handle updates in generate_loop usually? 
        # HF Style: cache.update(k, v, layer_idx)
        # We delegate to engine
        self.engine.append(layer_idx, key_states, value_states)
        return self.engine.get_kv(layer_idx) # Return dequantized for fallback if needed

    def get_seq_length(self, layer_idx=0):
        return self.engine.get_seq_len()
    
    def __getitem__(self, idx):
        # Some legacy code accesses cache[layer_idx] -> (k, v)
        return self.engine.get_kv(idx)

    def __iter__(self):
        for i in range(self.engine.num_layers):
            yield self.engine.get_kv(i)
            
    def __len__(self):
        return self.engine.num_layers


class INT8CacheWrapperContainer:
    """
    Container class that satisfies HuggingFace Cache interface.
    HF model.forward() calls past_key_values.get_seq_length() at model level,
    then passes past_key_values[layer_idx] to each attention layer.
    """
    def __init__(self, cache_engine, num_layers):
        self.engine = cache_engine
        self.num_layers = num_layers
        # Create per-layer wrappers
        self._layer_wrappers = [INT8CacheWrapper(cache_engine, i) for i in range(num_layers)]
        
    def get_seq_length(self, layer_idx=0):
        return self.engine.get_seq_len()
    
    def get_max_cache_shape(self):
        # Required by some HF versions
        return None
    
    def __getitem__(self, layer_idx):
        # HF calls past_key_values[layer_idx] to get per-layer cache
        return self._layer_wrappers[layer_idx]
    
    def __iter__(self):
        return iter(self._layer_wrappers)
    
    def __len__(self):
        return self.num_layers
    
    def to_legacy_cache(self):
        # For compatibility - return tuple of (k, v) per layer
        return tuple(self.engine.get_kv(i) for i in range(self.num_layers))
    
    def get_mask_sizes(self, cache_position, layer_idx):
        """
        Required by HF transformers >= 4.47 for attention masking.
        Returns (kv_length, kv_offset).
        """
        kv_length = self.engine.get_seq_len()
        # kv_offset is typically 0 for our use case (no sliding window)
        kv_offset = 0
        return kv_length, kv_offset
    
    def update(self, key_states, value_states, layer_idx, cache_kwargs=None):
        """
        Called by HF Attention layers if they fallback to original forward.
        We delegate to the per-layer wrapper's update.
        """
        self.engine.append(layer_idx, key_states, value_states)
        return self.engine.get_kv(layer_idx)

def _fused_forward_impl(self, hidden_states, cache_wrapper, attention_mask):
    """
    Implementation of Fused Attention using Triton Kernel.
    self: The Attention Module (Qwen2Attention)
    hidden_states: [Batch, 1, Hidden_Dim] (Query)
    cache_wrapper: Our INT8CacheWrapper
    """
    layer_idx = self.layer_idx
    
    # 1. Get Query (hidden_states)
    # Shape: [B, 1, Hidden_Dim] -> [B, 1, Num_Heads * Head_Dim]
    # We need to project Q
    bsz, q_len, _ = hidden_states.shape
    query_states = self.q_proj(hidden_states)
    query_states = query_states.view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)
    # query_states: [B, Num_Heads, 1, Head_Dim]
    
    # Remove singleton sequence dim for kernel: [B, Num_Heads, Head_Dim]
    query_states = query_states.squeeze(2) 
    
    # Apply per-head temperature correction if available (inv_tau)
    inv_tau = getattr(cache_wrapper.engine, "inv_tau", None)
    if inv_tau is not None and getattr(cache_wrapper.engine, "use_attn_temperature", True):
        inv_tau_layer = inv_tau[layer_idx].to(query_states.device)
        query_states = query_states * inv_tau_layer.view(1, -1, 1)
    
    # 2. Get KV Cache (INT8 Tensors)
    k_int8, v_int8, k_scale, v_scale = cache_wrapper.engine.get_int8_tensors(layer_idx)
    
    # 3. Context Lengths
    # In generate_loop, we assume all batch items verify same length or padded?
    # Our generate_loop is usually single-request or left-padded.
    # The kernel needs `context_lens`.
    # Current/Total seq len = cache_wrapper.get_seq_length() (which is uniform scalar in our simple loop)
    # But for robustness, we construct tensor.
    curr_seq_len = cache_wrapper.get_seq_length() 
    # Note: engine.append() happens AFTER verify? Or BEFORE?
    # Usually in decode loop:
    # 1. model(x) -> attention(x) -> cache.update()
    # OR 2. cache.update() -> model(x)
    # HF standard: model(x) calls cache.update().
    # So `k_int8` inside cache ALREADY includes the current step? OR NOT?
    # In `generate_loop.py`, we see:
    # `outputs = model(..., past_key_values=...)`
    # Then `kv_cache.append(...)`
    # So the KV Cache passed to model DOES NOT contain current token yet.
    # THIS IS A PROBLEM for Fused Kernel if it expects to attend to "History + Current".
    
    # Wait, FlashAttention usually computes Attention(Q, K_all, V_all).
    # If the cache only has history, we must:
    # a) Compute Attn(Q, K_history, V_history) + Attn(Q, K_curr, V_curr)
    # b) Or Append current K/V to cache FIRST?
    
    # In standard HF `forward`:
    # 1. Project Q, K, V for current token.
    # 2. Update Cache with current K, V.
    # 3. Get full K, V (history + current).
    # 4. Compute Q @ K.T
    
    # So we must replicate Step 1 & 2.
    key_states = self.k_proj(hidden_states)
    value_states = self.v_proj(hidden_states)
    key_states = key_states.view(bsz, q_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)
    value_states = value_states.view(bsz, q_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)
    
    # Update Cache (Using our engine's quantization)
    # We must call engine.append() here!
    # BUT `generate_loop.py` assumes it handles append after model return.
    # If we do it here, we must prevent `generate_loop` from doing it again?
    # OR we let `generate_loop` know.
    
    # Modification: The `cache_wrapper.update()` is designated for this.
    # But `update` in simple cache returns new KV.
    
    # Let's perform quantization & append explicitly here.
    # But `engine.append()` takes (layer, k, v) and does quantization.
    # k/v here are [B, H_kv, 1, D].
    cache_wrapper.engine.append(layer_idx, key_states.transpose(1, 2), value_states.transpose(1, 2))
    # Note: `engine.append` expects [Batch, Heads, Seq, Dim] but checks input carefully.
    # Checking `int8_cache.py`: `q_k, scale_k = quantize(k, ...)`
    
    # Now get FULL tensors
    k_int8_full, v_int8_full, k_scale_full, v_scale_full = cache_wrapper.engine.get_int8_tensors(layer_idx)
    
    # Context Lens
    # Now total length is `curr_seq_len + 1` (since we just appended).
    # Wait, `get_seq_len` tracks what? `self._seq_len`. 
    # `append` updates `_seq_len` only if layer==0.
    # If we differ layers, we must be careful.
    
    # Simple fix: Recalculate context_lens from `k_int8_full` or use engine's tracker.
    real_seq_len = cache_wrapper.engine.get_seq_len()
    context_lens = torch.full((bsz,), real_seq_len, dtype=torch.int32, device=hidden_states.device)
    
    # 4. Call Triton Kernel
    # Q: [B, H_q, D]
    # K_cache: [B, H_kv, MaxSeq, D]
    # We need to handle GQA (Group Query Attention)?
    # Qwen2 usually has GQA. num_heads != num_key_value_heads.
    # Our Triton kernel as written assumes `n_heads` matches or explicit loop?
    # Currently my kernel assumes `Q` and `K` have same number of heads or handles broadcast?
    # Checking `triton_decode_attn_int8.py`: `Q_ptr` and `K_ptr` strides.
    # Grid is `Batch * N_Heads` (where N_Heads is Q heads).
    # If K heads < Q heads, K stride_h should be 0? OR we map indices.
    
    # GQA Handling in Kernel:
    # If stride_k_h is set correctly, we can map multiple Q heads to single K head.
    # Q_heads = 32, K_heads = 4. Ratio = 8.
    # q_head_id = pid % N_Heads
    # k_head_id = q_head_id // Ratio
    # My kernel uses `k_base = K_ptr + ... + head_id * stride_k_h`.
    # IF we pass raw `K` tensor stride, `head_id` is iterating 0..31.
    # K tensor only has 4 heads. Accessing index 5 will crash.
    
    # FIX: We need to handle GQA in kernel or pass expanded K?
    # Expanding K (virtual view) is easier.
    # k_int8_expanded = k_int8_full.repeat_interleave(self.num_heads // self.num_key_value_heads, dim=1)
    # This involves metadata manip, no copy if using `expand`.
    n_rep = self.num_heads // self.num_key_value_heads
    if n_rep > 1:
        k_int8_full = k_int8_full.detach().repeat_interleave(n_rep, dim=1)
        v_int8_full = v_int8_full.detach().repeat_interleave(n_rep, dim=1)
        k_scale_full = k_scale_full.detach().repeat_interleave(n_rep, dim=1)
        v_scale_full = v_scale_full.detach().repeat_interleave(n_rep, dim=1)
    
    attn_output_val = decode_attn_int8(
        query_states, 
        k_int8_full, v_int8_full, 
        k_scale_full, v_scale_full, 
        context_lens
    )
    # Output: [B, Num_Heads, Head_Dim]
    
    # 5. Connect Output
    bsz, n_heads, head_dim = attn_output_val.shape
    attn_output_val = attn_output_val.unsqueeze(2) # [B, H, 1, D]
    attn_output_val = attn_output_val.transpose(1, 2).reshape(bsz, q_len, n_heads * head_dim)
    
    # Output projection
    attn_output = self.o_proj(attn_output_val)
    
    return attn_output, None, cache_wrapper


def apply_int8_fused_patch(model):
    """
    Apply monkey patch to model.
    """
    first_layer = model.model.layers[0].self_attn
    AttnClass = first_layer.__class__
    
    logging.info(f"Patching {AttnClass.__name__} for INT8 Fused Kernel")
    
    if not hasattr(AttnClass, "_original_forward"):
        AttnClass._original_forward = AttnClass.forward
        
    def forward_proxy(self, hidden_states, attention_mask=None, position_ids=None, past_key_values=None, output_attentions=False, use_cache=False, **kwargs):
        # Trigger fused path if:
        # 1. Decoding (q_len == 1)
        # 2. past_key_values is our INT8CacheWrapper
        is_fused = False
        if hidden_states.shape[1] == 1 and isinstance(past_key_values, INT8CacheWrapper):
            is_fused = True
            
        if is_fused:
            return _fused_forward_impl(self, hidden_states, past_key_values, attention_mask)
        else:
            # Pass all args as kwargs to avoid signature mismatch
            return AttnClass._original_forward(
                self, 
                hidden_states, 
                attention_mask=attention_mask, 
                position_ids=position_ids, 
                past_key_values=past_key_values, 
                output_attentions=output_attentions, 
                use_cache=use_cache, 
                **kwargs
            )
            
    AttnClass.forward = forward_proxy
