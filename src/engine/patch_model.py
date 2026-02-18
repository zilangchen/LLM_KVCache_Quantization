from __future__ import annotations

import inspect
import json
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

import torch

from src.kernels import decode_attn_int4, decode_attn_int8
from src.quant.int4_basic import unpack_int4

logger = logging.getLogger(__name__)
_FUSED_DUMP_WRITTEN = set()


def _parse_optional_int_env(name: str) -> Optional[int]:
    raw = os.environ.get(name)
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid %s=%r; expected integer.", name, raw)
        return None


def _topk_summary(tensor: torch.Tensor, k: int = 8) -> dict:
    flat = tensor.detach().float().reshape(-1)
    topk = min(k, int(flat.numel()))
    if topk <= 0:
        return {"indices": [], "values": []}
    values, indices = torch.topk(flat, k=topk)
    return {
        "indices": [int(x) for x in indices.cpu().tolist()],
        "values": [float(x) for x in values.cpu().tolist()],
    }


def _materialize_int4_cache_as_int8(
    k_int4: torch.Tensor,
    v_int4: torch.Tensor,
    *,
    head_dim: int,
    bit_packed: bool,
) -> Tuple[torch.Tensor, torch.Tensor]:
    if not bit_packed:
        if k_int4.shape[-1] != head_dim or v_int4.shape[-1] != head_dim:
            raise ValueError(
                "Unpacked INT4 cache shape mismatch: "
                f"k={tuple(k_int4.shape)} v={tuple(v_int4.shape)} head_dim={head_dim}"
            )
        return k_int4, v_int4

    if k_int4.shape[-1] * 2 != head_dim or v_int4.shape[-1] * 2 != head_dim:
        raise ValueError(
            "Packed INT4 cache shape mismatch: "
            f"k={tuple(k_int4.shape)} v={tuple(v_int4.shape)} expected_last_dim={head_dim // 2}"
        )
    return unpack_int4(k_int4), unpack_int4(v_int4)

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
        # HF uses this to size the causal/attention masks for the *effective* KV length
        # visible to the attention layer during this forward. That includes both:
        #   - already-cached tokens (engine.get_seq_len())
        #   - the current forward tokens (len(cache_position))
        #
        # If we return only the cached length, HF may build a too-short causal mask when
        # q_len > 1 (e.g., chunked prefill), causing shape mismatches.
        cached = int(self.engine.get_seq_len())
        current = 0
        if cache_position is not None:
            try:
                current = int(cache_position.shape[0])
            except Exception:
                current = int(getattr(cache_position, "numel", lambda: 0)())
        kv_length = cached + current
        kv_offset = 0  # no sliding window
        return kv_length, kv_offset
    
    def update(self, key_states, value_states, layer_idx, cache_kwargs=None):
        """
        Called by HF Attention layers if they fallback to original forward.
        We delegate to the per-layer wrapper's update.
        """
        self.engine.append(layer_idx, key_states, value_states)
        return self.engine.get_kv(layer_idx)

def _rotate_half(x: torch.Tensor) -> torch.Tensor:
    rotary_dim = x.shape[-1]
    x1 = x[..., : rotary_dim // 2]
    x2 = x[..., rotary_dim // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def _apply_rope(
    query_states: torch.Tensor,
    key_states: torch.Tensor,
    cos: torch.Tensor,
    sin: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Apply RoPE to query/key states.

    Supports full or partial rotary (cos/sin last dim can be <= head_dim).
    Expects query/key shapes [B, H, S, D] and cos/sin shapes [B, S, rotary_dim] or broadcastable.
    """
    bsz, _, q_len, head_dim = query_states.shape
    cos = cos.to(device=query_states.device, dtype=query_states.dtype)
    sin = sin.to(device=query_states.device, dtype=query_states.dtype)

    # Normalize cos/sin to [B, 1, S, rotary_dim] for broadcast across heads.
    if cos.ndim == 2:
        cos = cos[None, :, :]
        sin = sin[None, :, :]
    if cos.ndim == 3:
        if cos.shape[0] == 1 and bsz > 1:
            cos = cos.expand(bsz, -1, -1)
            sin = sin.expand(bsz, -1, -1)
        cos = cos.unsqueeze(1)
        sin = sin.unsqueeze(1)

    rotary_dim = cos.shape[-1]
    if rotary_dim > head_dim:
        raise ValueError(f"RoPE dim {rotary_dim} > head_dim {head_dim}")

    q_rot, q_pass = query_states[..., :rotary_dim], query_states[..., rotary_dim:]
    k_rot, k_pass = key_states[..., :rotary_dim], key_states[..., rotary_dim:]

    q_embed = (q_rot * cos) + (_rotate_half(q_rot) * sin)
    k_embed = (k_rot * cos) + (_rotate_half(k_rot) * sin)

    if q_pass.numel() == 0:
        return q_embed, k_embed
    return torch.cat([q_embed, q_pass], dim=-1), torch.cat([k_embed, k_pass], dim=-1)


def _decode_attn_int8_torch_ref(
    q: torch.Tensor,
    k_int8: torch.Tensor,
    v_int8: torch.Tensor,
    k_scale: torch.Tensor,
    v_scale: torch.Tensor,
    context_lens: torch.Tensor,
    sm_scale: float,
) -> torch.Tensor:
    """
    Reference decode attention for q_len==1 using INT8 KV + group-wise scales.

    Shapes:
      q:       [B, Hq, D] (fp16/bf16)
      k_int8:  [B, Hkv, S, D] (int8)
      v_int8:  [B, Hkv, S, D] (int8)
      k_scale: [B, Hkv, S, G] (fp16)
      v_scale: [B, Hkv, S, G] (fp16)
      context_lens: [B] (int32)
    Returns:
      out: [B, Hq, D]
    """
    if q.ndim != 3:
        raise ValueError(f"Expected q [B, H, D], got {q.shape}")
    if k_int8.ndim != 4 or v_int8.ndim != 4:
        raise ValueError(
            f"Expected k/v [B, H, S, D], got {k_int8.shape} / {v_int8.shape}"
        )
    if k_scale.ndim != 4 or v_scale.ndim != 4:
        raise ValueError(
            f"Expected k/v scale [B, H, S, G], got {k_scale.shape} / {v_scale.shape}"
        )

    bsz, q_heads, head_dim = q.shape
    _, kv_heads, _, head_dim_kv = k_int8.shape
    if head_dim_kv != head_dim:
        raise ValueError(f"Head dim mismatch: q D={head_dim}, kv D={head_dim_kv}")
    if q_heads % kv_heads != 0:
        raise ValueError(
            f"GQA unsupported: q_heads={q_heads} not divisible by kv_heads={kv_heads}"
        )

    num_groups = int(k_scale.shape[-1])
    if num_groups <= 0 or head_dim % num_groups != 0:
        raise ValueError(f"Invalid scale groups: D={head_dim} groups={num_groups}")
    group_size = head_dim // num_groups
    n_rep = q_heads // kv_heads

    outs = []
    for b in range(bsz):
        ctx_len = int(context_lens[b].item())
        if ctx_len <= 0:
            outs.append(
                torch.zeros((q_heads, head_dim), device=q.device, dtype=q.dtype)
            )
            continue

        curr_q = q[b]  # [Hq, D]
        curr_k_int8 = k_int8[b, :, :ctx_len, :]  # [Hkv, S, D]
        curr_v_int8 = v_int8[b, :, :ctx_len, :]
        curr_k_scale = k_scale[b, :, :ctx_len, :]  # [Hkv, S, G]
        curr_v_scale = v_scale[b, :, :ctx_len, :]

        k_dequant = (
            curr_k_int8.view(kv_heads, ctx_len, num_groups, group_size).to(torch.float16)
            * curr_k_scale.unsqueeze(-1)
        ).view(kv_heads, ctx_len, head_dim)
        v_dequant = (
            curr_v_int8.view(kv_heads, ctx_len, num_groups, group_size).to(torch.float16)
            * curr_v_scale.unsqueeze(-1)
        ).view(kv_heads, ctx_len, head_dim)

        if n_rep != 1:
            k_dequant = k_dequant.repeat_interleave(n_rep, dim=0)
            v_dequant = v_dequant.repeat_interleave(n_rep, dim=0)

        # Keep reference math in fp32 for long-context stability.
        q_fp32 = curr_q.float()
        k_fp32 = k_dequant.float()
        v_fp32 = v_dequant.float()
        scores = torch.einsum("hd,hsd->hs", q_fp32, k_fp32) * sm_scale  # [Hq, S]
        probs = torch.softmax(scores, dim=-1)
        out = torch.einsum("hs,hsd->hd", probs, v_fp32).to(dtype=curr_q.dtype)
        outs.append(out)

    return torch.stack(outs, dim=0)  # [B, Hq, D]


def _maybe_dump_fused_decode(
    layer_idx: int,
    step: int,
    decode_impl: str,
    q_kernel: torch.Tensor,
    k_int8: torch.Tensor,
    v_int8: torch.Tensor,
    k_scale: torch.Tensor,
    v_scale: torch.Tensor,
    context_lens: torch.Tensor,
    sm_scale: float,
    fused_out: torch.Tensor,
) -> None:
    """
    Optionally dump fused decode tensors for one selected (layer, step).

    Env switches:
      - KV_FUSED_DUMP_DIR: enabled when non-empty.
      - KV_FUSED_DUMP_LAYER: optional exact layer filter.
      - KV_FUSED_DUMP_STEP: optional exact decode step filter (uses seq_len after append).
    """
    dump_dir_raw = os.environ.get("KV_FUSED_DUMP_DIR", "").strip()
    if not dump_dir_raw:
        return

    dump_layer = _parse_optional_int_env("KV_FUSED_DUMP_LAYER")
    dump_step = _parse_optional_int_env("KV_FUSED_DUMP_STEP")
    if dump_layer is not None and layer_idx != dump_layer:
        return
    if dump_step is not None and step != dump_step:
        return

    dump_key = (dump_dir_raw, int(layer_idx), int(step))
    if dump_key in _FUSED_DUMP_WRITTEN:
        return

    dump_dir = Path(dump_dir_raw)
    dump_dir.mkdir(parents=True, exist_ok=True)

    ref_out = _decode_attn_int8_torch_ref(
        q=q_kernel,
        k_int8=k_int8,
        v_int8=v_int8,
        k_scale=k_scale,
        v_scale=v_scale,
        context_lens=context_lens,
        sm_scale=sm_scale,
    )
    max_abs_diff = float((fused_out - ref_out).abs().max().item())
    mean_abs_diff = float((fused_out - ref_out).abs().mean().item())

    stem = f"fused_layer{int(layer_idx):02d}_step{int(step):05d}_pid{os.getpid()}"
    tensor_path = dump_dir / f"{stem}.pt"
    summary_path = dump_dir / f"{stem}.json"

    payload = {
        "layer_idx": int(layer_idx),
        "step": int(step),
        "decode_impl": decode_impl,
        "sm_scale": float(sm_scale),
        "context_len": int(context_lens.max().item()),
        "q": q_kernel.detach().cpu(),
        "k_int8": k_int8.detach().cpu(),
        "v_int8": v_int8.detach().cpu(),
        "k_scale": k_scale.detach().cpu(),
        "v_scale": v_scale.detach().cpu(),
        "fused_out": fused_out.detach().cpu(),
        "ref_out": ref_out.detach().cpu(),
    }
    torch.save(payload, tensor_path)

    summary = {
        "layer_idx": int(layer_idx),
        "step": int(step),
        "decode_impl": decode_impl,
        "sm_scale": float(sm_scale),
        "context_len": int(context_lens.max().item()),
        "tensor_path": str(tensor_path),
        "max_abs_diff": max_abs_diff,
        "mean_abs_diff": mean_abs_diff,
        "logits_topk_fused": _topk_summary(fused_out),
        "logits_topk_ref": _topk_summary(ref_out),
    }
    summary_path.write_text(json.dumps(summary, indent=2))

    _FUSED_DUMP_WRITTEN.add(dump_key)
    logger.info(
        "Wrote fused decode dump: layer=%s step=%s tensor=%s summary=%s",
        layer_idx,
        step,
        tensor_path,
        summary_path,
    )


def _get_rope_cos_sin(
    attn_module,
    value_states: torch.Tensor,
    position_ids: Optional[torch.Tensor],
    position_embeddings: Optional[Tuple[torch.Tensor, torch.Tensor]],
) -> Tuple[Optional[torch.Tensor], Optional[torch.Tensor]]:
    if position_embeddings is not None:
        try:
            cos, sin = position_embeddings
            return cos, sin
        except Exception:
            pass

    rotary = getattr(attn_module, "rotary_emb", None)
    if rotary is None or position_ids is None:
        return None, None

    # Common HF API: rotary_emb(x, position_ids) -> (cos, sin)
    for call in (
        lambda: rotary(value_states, position_ids),
        lambda: rotary(value_states, position_ids=position_ids),
        lambda: rotary(position_ids),
        lambda: rotary(position_ids=position_ids),
    ):
        try:
            out = call()
        except TypeError:
            continue
        except Exception:
            continue
        if isinstance(out, (tuple, list)) and len(out) == 2:
            return out[0], out[1]

    # Fallback: rotary_emb(x, seq_len=...) returning base tables; gather by position_ids.
    try:
        seq_len = int(position_ids.max().item()) + 1
        out = rotary(value_states, seq_len=seq_len)
        if isinstance(out, (tuple, list)) and len(out) == 2:
            cos, sin = out
            if cos.ndim == 3 and cos.shape[0] == 1:
                cos = cos.squeeze(0)
                sin = sin.squeeze(0)
            if cos.ndim == 2:
                cos = cos[position_ids]
                sin = sin[position_ids]
                return cos, sin
    except Exception:
        pass

    return None, None


def _infer_heads_from_proj(attn_module, proj_name: str, head_dim: int) -> Optional[int]:
    proj = getattr(attn_module, proj_name, None)
    if proj is None:
        return None

    out_features = getattr(proj, "out_features", None)
    if out_features is None and hasattr(proj, "weight"):
        out_features = int(proj.weight.shape[0])
    if out_features is None:
        return None
    if int(out_features) % int(head_dim) != 0:
        raise ValueError(
            f"{proj_name}.out_features={out_features} is not divisible by head_dim={head_dim}"
        )
    return int(out_features) // int(head_dim)


def _resolve_attn_shape_meta(attn_module) -> Tuple[int, int, int]:
    head_dim = getattr(attn_module, "head_dim", None)
    if head_dim is None:
        raise ValueError("Attention module is missing head_dim.")
    head_dim = int(head_dim)

    q_heads = getattr(attn_module, "_kv_num_attention_heads", None)
    kv_heads = getattr(attn_module, "_kv_num_key_value_heads", None)

    if q_heads is None:
        q_heads = getattr(attn_module, "num_heads", None)
    if kv_heads is None:
        kv_heads = getattr(attn_module, "num_key_value_heads", None)

    if q_heads is None:
        q_heads = _infer_heads_from_proj(attn_module, "q_proj", head_dim)
    if kv_heads is None:
        kv_heads = _infer_heads_from_proj(attn_module, "k_proj", head_dim)
    if kv_heads is None:
        kv_heads = q_heads

    if q_heads is None or kv_heads is None:
        raise ValueError("Unable to resolve attention head metadata for fused decode.")

    q_heads = int(q_heads)
    kv_heads = int(kv_heads)

    if q_heads <= 0 or kv_heads <= 0:
        raise ValueError(f"Invalid heads: q_heads={q_heads}, kv_heads={kv_heads}")
    if q_heads % kv_heads != 0:
        raise ValueError(
            f"Invalid GQA mapping for fused decode: q_heads={q_heads}, kv_heads={kv_heads}"
        )

    return q_heads, kv_heads, head_dim


def _fused_forward_impl(
    self,
    hidden_states: torch.Tensor,
    cache_wrapper: INT8CacheWrapper,
    attention_mask: Optional[torch.Tensor] = None,
    position_ids: Optional[torch.Tensor] = None,
    position_embeddings: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
    cache_position: Optional[torch.Tensor] = None,
    return_cache: bool = False,
    **kwargs,
):
    """
    Decode-only fused attention path (q_len == 1).
    """
    del attention_mask, cache_position, kwargs

    layer_idx = getattr(cache_wrapper, "layer_idx", getattr(self, "layer_idx", 0))

    bsz, q_len, _ = hidden_states.shape
    if q_len != 1:
        raise ValueError(f"Fused decode expects q_len==1, got {q_len}")

    q_heads, kv_heads, head_dim = _resolve_attn_shape_meta(self)

    # Projections for current token.
    query_states = self.q_proj(hidden_states)
    key_states = self.k_proj(hidden_states)
    value_states = self.v_proj(hidden_states)

    # Reshape: [B, 1, H*D] -> [B, H, 1, D]
    query_states = query_states.view(bsz, q_len, q_heads, head_dim).transpose(1, 2)
    key_states = key_states.view(bsz, q_len, kv_heads, head_dim).transpose(1, 2)
    value_states = value_states.view(bsz, q_len, kv_heads, head_dim).transpose(1, 2)

    # Optional norms (model-dependent; apply if present).
    if getattr(self, "q_norm", None) is not None:
        query_states = self.q_norm(query_states)
    if getattr(self, "k_norm", None) is not None:
        key_states = self.k_norm(key_states)

    # RoPE for Q/K.
    cos, sin = _get_rope_cos_sin(self, value_states, position_ids, position_embeddings)
    if cos is not None and sin is not None:
        query_states, key_states = _apply_rope(query_states, key_states, cos, sin)
    else:
        # Most decoder-only models (incl. Qwen2) require RoPE.
        raise RuntimeError(
            "Failed to obtain RoPE cos/sin for fused decode. "
            "Check transformers version/model API (position_ids/position_embeddings)."
        )

    # Optional per-head temperature correction (inv_tau) for int8_ours.
    inv_tau = getattr(cache_wrapper.engine, "inv_tau", None)
    if inv_tau is not None and getattr(cache_wrapper.engine, "use_attn_temperature", True):
        inv_tau_layer = inv_tau[layer_idx].to(device=query_states.device, dtype=query_states.dtype)
        query_states = query_states * inv_tau_layer.view(1, -1, 1, 1)

    # Append current KV into the INT8 cache (quantizes internally).
    cache_wrapper.engine.append(layer_idx, key_states, value_states)

    # Fetch quantized cache for this layer (includes the appended token).
    cache_kind = "int8"
    if hasattr(cache_wrapper.engine, "get_int8_tensors"):
        k_quant, v_quant, k_scale, v_scale = cache_wrapper.engine.get_int8_tensors(
            layer_idx
        )
    elif hasattr(cache_wrapper.engine, "get_int4_tensors"):
        cache_kind = "int4"
        k_quant, v_quant, k_scale, v_scale = cache_wrapper.engine.get_int4_tensors(
            layer_idx
        )
    else:
        raise RuntimeError(
            "Fused path requires cache engine to provide get_int8_tensors or get_int4_tensors."
        )

    seq_len = int(k_quant.shape[2])
    context_lens = torch.full((bsz,), seq_len, dtype=torch.int32, device=hidden_states.device)

    # Decode attention (q_len == 1)
    q_kernel = query_states.squeeze(2)  # [B, Hq, D]
    sm_scale = float(getattr(self, "scaling", 1.0 / (head_dim ** 0.5)))
    decode_impl = getattr(cache_wrapper.engine, "decode_attn_impl", "triton_fused")
    if hasattr(cache_wrapper.engine, "record_fused_decode"):
        cache_wrapper.engine.record_fused_decode(layer_idx, decode_impl)

    dump_enabled = os.environ.get("KV_FUSED_DUMP_DIR", "").strip() != ""
    k_int8_for_ref = None
    v_int8_for_ref = None
    if cache_kind == "int8":
        k_int8_for_ref, v_int8_for_ref = k_quant, v_quant
    elif decode_impl == "torch_ref" or dump_enabled:
        # Int4 path: materialize int8 view only when needed by torch reference
        # or when fused debug dump is enabled.
        k_int8_for_ref, v_int8_for_ref = _materialize_int4_cache_as_int8(
            k_quant,
            v_quant,
            head_dim=head_dim,
            bit_packed=bool(getattr(cache_wrapper.engine, "bit_packed", True)),
        )

    if decode_impl == "triton_fused":
        stats = getattr(cache_wrapper.engine, "decode_stats", None)
        if cache_kind == "int8":
            try:
                attn_output_val = decode_attn_int8(
                    q_kernel,
                    k_quant,
                    v_quant,
                    k_scale,
                    v_scale,
                    context_lens,
                    sm_scale=sm_scale,
                    debug_stats=stats,
                    layer_idx=layer_idx,
                )
            except TypeError:
                # Compatibility path for monkey-patched decode_attn function in verify script.
                attn_output_val = decode_attn_int8(
                    q_kernel,
                    k_quant,
                    v_quant,
                    k_scale,
                    v_scale,
                    context_lens,
                    sm_scale=sm_scale,
                )
        else:
            try:
                attn_output_val = decode_attn_int4(
                    q_kernel,
                    k_quant,
                    v_quant,
                    k_scale,
                    v_scale,
                    context_lens,
                    sm_scale=sm_scale,
                    bit_packed=bool(getattr(cache_wrapper.engine, "bit_packed", True)),
                    head_dim=head_dim,
                    debug_stats=stats,
                    layer_idx=layer_idx,
                )
            except TypeError:
                # Compatibility path for monkey-patched decode_attn function in verify script.
                attn_output_val = decode_attn_int4(
                    q_kernel,
                    k_quant,
                    v_quant,
                    k_scale,
                    v_scale,
                    context_lens,
                    sm_scale=sm_scale,
                    bit_packed=bool(getattr(cache_wrapper.engine, "bit_packed", True)),
                    head_dim=head_dim,
                )
    elif decode_impl == "torch_ref":
        if k_int8_for_ref is None or v_int8_for_ref is None:
            raise RuntimeError("torch_ref decode for int4 requires materialized INT8 tensors.")
        attn_output_val = _decode_attn_int8_torch_ref(
            q_kernel,
            k_int8_for_ref,
            v_int8_for_ref,
            k_scale,
            v_scale,
            context_lens,
            sm_scale=sm_scale,
        )
    else:
        raise ValueError(
            f"Unknown decode_attn_impl={decode_impl!r}. Use 'triton_fused' or 'torch_ref'."
        )

    _maybe_dump_fused_decode(
        layer_idx=layer_idx,
        step=seq_len,
        decode_impl=decode_impl,
        q_kernel=q_kernel,
        k_int8=k_int8_for_ref,
        v_int8=v_int8_for_ref,
        k_scale=k_scale,
        v_scale=v_scale,
        context_lens=context_lens,
        sm_scale=sm_scale,
        fused_out=attn_output_val,
    )

    # Project back to hidden dim.
    attn_output_val = attn_output_val.unsqueeze(2).transpose(1, 2)
    attn_output_val = attn_output_val.reshape(bsz, q_len, q_heads * head_dim)
    attn_output = self.o_proj(attn_output_val)

    # Optional debug: prove fused path executed.
    if os.environ.get("KV_FUSED_DEBUG", "") not in ("", "0"):
        calls = getattr(cache_wrapper.engine, "_fused_decode_calls", 0) + 1
        cache_wrapper.engine._fused_decode_calls = calls
        if calls == 1:
            logger.info(
                "INT8 fused decode active (layer=%s q_heads=%s kv_heads=%s seq_len=%s).",
                layer_idx,
                q_heads,
                kv_heads,
                seq_len,
            )

    if return_cache:
        return attn_output, None, cache_wrapper
    return attn_output, None


def apply_int8_fused_patch(model):
    """
    Apply monkey patch to model.
    """
    # Attempt to set layer indices for safety.
    try:
        layers = model.model.layers
    except Exception:
        layers = None

    if layers is not None:
        cfg = getattr(model, "config", None)
        cfg_q_heads = getattr(cfg, "num_attention_heads", None)
        cfg_kv_heads = getattr(cfg, "num_key_value_heads", cfg_q_heads)

        for idx, layer in enumerate(layers):
            attn = getattr(layer, "self_attn", None)
            if attn is None:
                continue
            if not hasattr(attn, "layer_idx"):
                setattr(attn, "layer_idx", idx)

            head_dim = getattr(attn, "head_dim", None)
            if head_dim is None:
                continue

            q_heads = cfg_q_heads
            kv_heads = cfg_kv_heads
            if q_heads is None:
                q_heads = _infer_heads_from_proj(attn, "q_proj", int(head_dim))
            if kv_heads is None:
                kv_heads = _infer_heads_from_proj(attn, "k_proj", int(head_dim))
            if kv_heads is None:
                kv_heads = q_heads

            if q_heads is not None:
                setattr(attn, "_kv_num_attention_heads", int(q_heads))
            if kv_heads is not None:
                setattr(attn, "_kv_num_key_value_heads", int(kv_heads))

    first_attn = model.model.layers[0].self_attn
    AttnClass = first_attn.__class__

    logger.info("Patching %s.forward for INT8 fused decode.", AttnClass.__name__)

    if not hasattr(AttnClass, "_original_forward"):
        AttnClass._original_forward = AttnClass.forward

    original_sig = inspect.signature(AttnClass._original_forward)
    has_past_key_value = "past_key_value" in original_sig.parameters
    has_past_key_values = "past_key_values" in original_sig.parameters
    has_use_cache = "use_cache" in original_sig.parameters

    def _filter_kwargs(kwargs_in: dict) -> dict:
        return {k: v for k, v in kwargs_in.items() if k in original_sig.parameters}

    def forward_proxy(
        self,
        hidden_states,
        attention_mask=None,
        position_ids=None,
        past_key_value=None,
        past_key_values=None,
        output_attentions=False,
        use_cache=False,
        **kwargs,
    ):
        # Normalize past alias.
        if past_key_value is None:
            past_key_value = past_key_values

        cache_wrapper = None
        if isinstance(past_key_value, INT8CacheWrapper):
            cache_wrapper = past_key_value
        elif isinstance(past_key_value, INT8CacheWrapperContainer):
            layer_idx = getattr(self, "layer_idx", 0)
            cache_wrapper = past_key_value[layer_idx]
        elif hasattr(past_key_value, "__getitem__") and hasattr(past_key_value, "engine"):
            # Fallback for Cache-like wrappers that expose per-layer indexing.
            try:
                layer_idx = getattr(self, "layer_idx", 0)
                candidate = past_key_value[layer_idx]
                if isinstance(candidate, INT8CacheWrapper):
                    cache_wrapper = candidate
            except Exception:
                cache_wrapper = None

        is_fused = (
            hidden_states is not None
            and hidden_states.shape[1] == 1
            and cache_wrapper is not None
        )

        if is_fused:
            return _fused_forward_impl(
                self,
                hidden_states,
                cache_wrapper,
                attention_mask=attention_mask,
                position_ids=position_ids,
                position_embeddings=kwargs.get("position_embeddings"),
                cache_position=kwargs.get("cache_position"),
                return_cache=has_use_cache,
            )

        kwargs_fwd = dict(
            attention_mask=attention_mask,
            position_ids=position_ids,
            output_attentions=output_attentions,
            use_cache=use_cache,
            **kwargs,
        )
        kwargs_fwd = _filter_kwargs(kwargs_fwd)
        if past_key_value is not None:
            if has_past_key_value:
                kwargs_fwd["past_key_value"] = past_key_value
            elif has_past_key_values:
                kwargs_fwd["past_key_values"] = past_key_value
        return AttnClass._original_forward(self, hidden_states, **kwargs_fwd)

    AttnClass.forward = forward_proxy
