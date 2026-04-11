"""Debug BitDecoding adapter — find where NaN originates."""
import sys
import torch
sys.path.insert(0, ".")

from src.kernels.adapters import bitdecoding_adapter as bda

_orig = bda.decode_attn_bitdecoding
_call_count = [0]


def wrapped(q, k_packed, v_packed, k_scale, k_zp, v_scale, v_zp, context_lens, sm_scale=None):
    _call_count[0] += 1
    n = _call_count[0]

    # Check inputs
    in_issues = []
    for name, t in [("q", q), ("k_packed", k_packed), ("v_packed", v_packed),
                     ("k_scale", k_scale), ("k_zp", k_zp), ("v_scale", v_scale), ("v_zp", v_zp)]:
        if t.dtype.is_floating_point and torch.isnan(t).any():
            in_issues.append(f"{name}_NaN")
        if t.dtype.is_floating_point and torch.isinf(t).any():
            in_issues.append(f"{name}_Inf")

    if n <= 3:
        print(f"[call {n}] q={tuple(q.shape)} k_packed={tuple(k_packed.shape)} "
              f"ctx_lens={context_lens.tolist()} inputs_ok={not in_issues}", flush=True)

    if in_issues:
        print(f"[call {n}] INPUT ISSUES: {in_issues}", flush=True)

    out = _orig(q, k_packed, v_packed, k_scale, k_zp, v_scale, v_zp, context_lens, sm_scale)

    nan_count = torch.isnan(out).sum().item()
    inf_count = torch.isinf(out).sum().item()
    total = out.numel()
    if nan_count > 0 or inf_count > 0 or n <= 3:
        print(f"[call {n}] OUT shape={tuple(out.shape)} nan={nan_count}/{total} "
              f"inf={inf_count} max={out.abs().max().item():.4f}", flush=True)

    if nan_count > 0 and n > 1:
        # First NaN call detected after clean call — stop
        import traceback
        traceback.print_stack()
        raise RuntimeError(f"BD adapter produced NaN on call {n}")
    return out


bda.decode_attn_bitdecoding = wrapped

from transformers import AutoModelForCausalLM, AutoTokenizer
from src.engine.generate_loop import generate_from_ids

m = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct",
                                          torch_dtype=torch.float16, device_map="auto")
m.eval()
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct", trust_remote_code=True)
ids = tok("Hello " * 256, return_tensors="pt").input_ids[:, :512].to("cuda")
mask = torch.ones_like(ids)

try:
    generate_from_ids(
        model=m, tokenizer=tok, input_ids=ids, attention_mask=mask,
        max_new_tokens=2, kv_mode="int4_ours_asym",
        calib_file="artifacts/kv_calib_rolealign_1p5b_v3.json",
        decode_attn_impl="bitdecoding", use_attn_temperature=False,
        quant_bits=4, seed=1234,
    )
    print("OK")
except Exception as e:
    print(f"FAIL: {type(e).__name__}: {e}")
