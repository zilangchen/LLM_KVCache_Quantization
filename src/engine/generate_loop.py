#!/usr/bin/env python3
"""
Custom generation loop with explicit prefill + decode separation.

This module implements a generation loop WITHOUT using model.generate(),
enabling precise control over KV cache, timing, and future quantization.

Usage:
    from src.engine.generate_loop import generate, GenerationOutput

    output = generate(model, tokenizer, "Hello, I am", max_new_tokens=128)
    print(f"Text: {output.text}")
    print(f"TTFT: {output.ttft_ms:.2f} ms")
    print(f"TPOT: {output.tpot_ms:.2f} ms")
"""

from dataclasses import dataclass
from typing import List, Optional
import gc
import json
import os
import torch
from transformers import PreTrainedModel, PreTrainedTokenizer
try:
    from transformers import DynamicCache
    HAS_DYNAMIC_CACHE = True
except ImportError:
    # Try older location? Or fall back
    try:
        from transformers.cache_utils import DynamicCache
        HAS_DYNAMIC_CACHE = True
    except ImportError:
        HAS_DYNAMIC_CACHE = False

from src.utils.timing import (
    CUDATimer,
    TimingStats,
    get_gpu_memory_mb,
    reset_gpu_memory_stats,
)
from src.utils.repro import set_seed


@dataclass
class GenerationOutput:
    """Structured output from the generation loop."""

    text: str
    tokens: List[int]
    ttft_ms: float          # Time To First Token (prefill time)
    tpot_ms: float          # Time Per Output Token (decode average)
    tok_per_s: float        # Throughput (tokens per second)
    gpu_mem_peak_mb: float  # Peak GPU memory usage
    prompt_len: int         # Number of prompt tokens
    gen_len: int            # Number of generated tokens


def generate(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    prompt: str,
    max_new_tokens: int = 128,
    kv_mode: str = "fp16",
    group_size: int = 128,
    clip_percentile: float = 99.9,
    seed: int = 1234,
    calib_file: Optional[str] = None,
    use_attn_temperature: bool = True,
) -> GenerationOutput:
    """
    Custom generation loop with prefill + token-by-token decode.

    This function does NOT use model.generate(). Instead, it manually:
    1. Prefill: Process the entire prompt in one forward pass
    2. Decode: Generate tokens one at a time using past_key_values

    Args:
        model: HuggingFace model (AutoModelForCausalLM)
        tokenizer: HuggingFace tokenizer
        prompt: Input text prompt
        max_new_tokens: Maximum number of tokens to generate
        kv_mode: KV cache mode (fp16 or int8_baseline)
        group_size: Group size for INT8 quantization
        clip_percentile: Percentile for INT8 clipping
        seed: Random seed for reproducibility
        calib_file: Path to calibration JSON (int8_ours only)
        use_attn_temperature: Apply per-head temperature if available (int8_ours)

    Returns:
        GenerationOutput with generated text and timing statistics

    Raises:
        ValueError: If input is too long or kv_mode is unsupported
        RuntimeError: If CUDA is not available
    """
    # Validate inputs
    if kv_mode not in ["fp16", "int8_baseline", "int8_fused", "int8_ours", "int4_baseline"]:
        raise ValueError(
            f"kv_mode='{kv_mode}' not supported. "
            f"Choose from ['fp16', 'int8_baseline', 'int8_fused', 'int8_ours', 'int4_baseline']."
        )
        
    # Apply Patch if needed
    if kv_mode in ["int8_fused", "int8_ours"]:
        if kv_mode == "int8_ours":
            import warnings
            warnings.warn(
                "kv_mode=int8_ours uses the fused int8 path; calibration will be loaded "
                "if calib_file is provided (or artifacts/kv_calib_kl.json exists).",
                UserWarning,
            )
        from src.engine.patch_model import apply_int8_fused_patch, INT8CacheWrapper
        apply_int8_fused_patch(model)

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is required for generation. Please run on a GPU-enabled server."
        )

    # ... (seeds, reset_stats, tokenizer...)
    # Set seeds for reproducibility
    set_seed(seed=seed, deterministic=True)
    
    # Reset memory stats for accurate peak measurement
    reset_gpu_memory_stats()
    
    # Get available GPU memory for OOM checks
    try:
        gpu_free_mb = (
            torch.cuda.get_device_properties(0).total_memory
            - torch.cuda.memory_allocated()
        ) / (1024 * 1024)
    except Exception:
        gpu_free_mb = None

    # Tokenize input
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_ids = inputs["input_ids"]
    attention_mask = inputs.get("attention_mask")
    prompt_len = input_ids.shape[1]

    # Check for excessively long input
    max_model_len = getattr(model.config, "max_position_embeddings", 32768)
    if prompt_len + max_new_tokens > max_model_len:
        raise ValueError(
            f"Total length ({prompt_len} + {max_new_tokens} = "
            f"{prompt_len + max_new_tokens}) exceeds model's max "
            f"position embeddings ({max_model_len}). "
            f"Reduce prompt length or max_new_tokens."
        )

    # Initialize KV Cache based on mode
    num_layers = getattr(model.config, "num_hidden_layers", 28)
    static_k_scale = None
    static_v_scale = None
    inv_tau = None

    if kv_mode == "int8_ours":
        import warnings
        calib_path = calib_file or os.path.join("artifacts", "kv_calib_kl.json")
        if calib_path and os.path.exists(calib_path):
            try:
                with open(calib_path, "r") as f:
                    calib = json.load(f)
                calib_group_k = calib.get("group_size_k", calib.get("group_size", group_size))
                calib_group_v = calib.get("group_size_v", calib.get("group_size", group_size))
                calib_clip_k = calib.get("clip_percentile_k", calib.get("clip_percentile", clip_percentile))
                calib_clip_v = calib.get("clip_percentile_v", calib.get("clip_percentile", clip_percentile))

                if calib_group_k and calib_group_v and calib_group_k != calib_group_v:
                    warnings.warn(
                        f"Calibration group_size_k ({calib_group_k}) != group_size_v ({calib_group_v}); "
                        "using group_size_k for both.",
                        UserWarning,
                    )
                if calib_clip_k and calib_clip_v and calib_clip_k != calib_clip_v:
                    warnings.warn(
                        f"Calibration clip_percentile_k ({calib_clip_k}) != clip_percentile_v ({calib_clip_v}); "
                        "using clip_percentile_k for both.",
                        UserWarning,
                    )

                group_size = calib_group_k or group_size
                clip_percentile = calib_clip_k or clip_percentile

                if "k_scale" in calib:
                    static_k_scale = torch.tensor(calib["k_scale"], dtype=torch.float16)
                if "v_scale" in calib:
                    static_v_scale = torch.tensor(calib["v_scale"], dtype=torch.float16)
                if use_attn_temperature and "inv_tau" in calib:
                    inv_tau = torch.tensor(calib["inv_tau"], dtype=torch.float32)

                if static_k_scale is not None:
                    static_k_scale = static_k_scale.to(model.device)
                if static_v_scale is not None:
                    static_v_scale = static_v_scale.to(model.device)
                if inv_tau is not None:
                    inv_tau = inv_tau.to(model.device)
            except Exception as exc:
                warnings.warn(
                    f"Failed to load calibration file {calib_path}: {exc}. "
                    "Falling back to baseline int8 behavior.",
                    UserWarning,
                )
        else:
            warnings.warn(
                f"Calibration file not found: {calib_path}. "
                "Falling back to baseline int8 behavior.",
                UserWarning,
            )
    if kv_mode == "fp16":
        from src.cache import FP16KVCache
        kv_cache = FP16KVCache(num_layers=num_layers, device=model.device.type)
    elif kv_mode in ["int8_baseline", "int8_fused", "int8_ours"]:
        from src.cache import INT8KVCache
        kv_cache = INT8KVCache(
            num_layers=num_layers,
            device=model.device.type,
            clip_percentile=clip_percentile,
            group_size=group_size,
            static_k_scale=static_k_scale,
            static_v_scale=static_v_scale,
            inv_tau=inv_tau,
            use_attn_temperature=use_attn_temperature,
        )
    elif kv_mode == "int4_baseline":
        from src.cache import INT4KVCache
        kv_cache = INT4KVCache(
            num_layers=num_layers,
            device=model.device.type,
            clip_percentile=clip_percentile,
            group_size=group_size,
        )
    
    # ... (memory check, prefill...)
    # Simple explicit memory check (rough estimate)
    if gpu_free_mb is not None and gpu_free_mb < 2000:
        import warnings
        warnings.warn(
            f"Low GPU memory ({gpu_free_mb:.0f} MB). Generation may OOM.",
            ResourceWarning
        )

    generated_tokens: List[int] = []
    decode_times = TimingStats()
    
    # ========== PREFILL PHASE ==========
    prefill_timer = CUDATimer()
    prefill_timer.start()

    with torch.no_grad():
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            use_cache=True,
        )
        
        # Extract and store KV cache
        if outputs.past_key_values is not None:
            for i, (k, v) in enumerate(outputs.past_key_values):
                kv_cache.append(i, k, v)
        
        next_token_logits = outputs.logits[:, -1, :]
        next_token = torch.argmax(next_token_logits, dim=-1)

    prefill_timer.stop()
    ttft_ms = prefill_timer.elapsed_ms

    generated_tokens.append(next_token.item())
    current_token = next_token.unsqueeze(0)  # [1, 1]

    # Update attention mask for decode phase
    if attention_mask is not None:
        attention_mask = torch.cat(
            [attention_mask,
             torch.ones((1, 1), device=model.device, dtype=attention_mask.dtype)],
            dim=1
        )

    # ========== DECODE PHASE ==========
    eos_token_id = tokenizer.eos_token_id

    for step in range(max_new_tokens - 1):
        if generated_tokens[-1] == eos_token_id:
            break

        decode_timer = CUDATimer()
        decode_timer.start()

        with torch.no_grad():
            # Prepare past_key_values
            if kv_mode in ["int8_fused", "int8_ours"]:
                # Use Container class that satisfies HF Cache interface
                from src.engine.patch_model import INT8CacheWrapperContainer
                current_past_key_values = INT8CacheWrapperContainer(kv_cache, num_layers)
            elif kv_mode in ["int8_baseline", "int4_baseline"]:
                # For baseline modes, we dequantize BEFORE attention
                current_past_key_values = []
                for i in range(num_layers):
                    k, v = kv_cache.get_kv(i)
                    current_past_key_values.append((k, v))
                current_past_key_values = tuple(current_past_key_values)
            else:
                # FP16 cache
                current_past_key_values = kv_cache.to_tuple()

            # Dynamic Cache Check (Skipped for fused wrapper as it mocks Cache)
            if kv_mode not in ["int8_fused", "int8_ours"] and HAS_DYNAMIC_CACHE and isinstance(current_past_key_values, tuple):
                 try:
                    current_past_key_values = DynamicCache.from_legacy_cache(current_past_key_values)
                 except: 
                    pass

            outputs = model(
                input_ids=current_token,
                attention_mask=attention_mask,
                past_key_values=current_past_key_values,
                use_cache=True,
            )
            
            # Update cache with NEW token's KV
            # For fused mode, the Patch's wrapper.update() ALREADY appended to engine?
            # Let's check patch_model.py: 
            #   cache_wrapper.engine.append(...) called inside _fused_forward_impl
            # So if we are in fused mode, `kv_cache` is ALREADY updated.
            # BUT `outputs.past_key_values` might be returning what?
            # Model returns `outputs.past_key_values` which are usually the inputs updated.
            # If fused patch returns `cache_wrapper`, then `outputs.past_key_values` is tuple of wrappers.
            
            # We ONLY need to update if we are NOT in fused mode (or verify).
            if kv_mode not in ["int8_fused", "int8_ours"]:
                if outputs.past_key_values is not None:
                    for i, (k, v) in enumerate(outputs.past_key_values):
                        if k.shape[2] > 1:
                            k_new = k[:, :, -1:, :]
                            v_new = v[:, :, -1:, :]
                            kv_cache.append(i, k_new, v_new)
                        else:
                            kv_cache.append(i, k, v)
            
            next_token_logits = outputs.logits[:, -1, :]
            next_token = torch.argmax(next_token_logits, dim=-1)


        decode_timer.stop()
        decode_times.add(decode_timer.elapsed_ms)

        generated_tokens.append(next_token.item())
        current_token = next_token.unsqueeze(0)

        # Update attention mask
        if attention_mask is not None:
            attention_mask = torch.cat(
                [attention_mask,
                 torch.ones((1, 1), device=model.device,
                            dtype=attention_mask.dtype)],
                dim=1
            )

    # ========== COLLECT RESULTS ==========
    gen_len = len(generated_tokens)
    gpu_mem_peak_mb = get_gpu_memory_mb()

    # TPOT: average decode time (exclude prefill)
    tpot_ms = decode_times.mean_ms if decode_times.count > 0 else 0.0

    # Throughput
    total_decode_ms = decode_times.total_ms
    if total_decode_ms > 0:
        decode_tokens = gen_len - 1
        tok_per_s = (decode_tokens / total_decode_ms) * 1000.0
    else:
        tok_per_s = 0.0

    generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True)

    output = GenerationOutput(
        text=generated_text,
        tokens=generated_tokens,
        ttft_ms=ttft_ms,
        tpot_ms=tpot_ms,
        tok_per_s=tok_per_s,
        gpu_mem_peak_mb=gpu_mem_peak_mb,
        prompt_len=prompt_len,
        gen_len=gen_len,
    )

    # Cleanup memory to prevent OOM across runs
    if 'kv_cache' in locals():
        kv_cache.clear()
        del kv_cache
    if 'outputs' in locals():
        del outputs
    if 'current_past_key_values' in locals():
        del current_past_key_values

    gc.collect()
    torch.cuda.empty_cache()

    return output
