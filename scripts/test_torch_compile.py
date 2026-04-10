"""Test torch.compile effect on INT4 decode TPOT."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from src.engine.generate_loop import generate_from_ids

model_id = "Qwen/Qwen2.5-1.5B-Instruct"
tok = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.float16, device_map="cuda")
model.eval()

tok_id = tok.encode("Hello", add_special_tokens=False)[0]
input_ids = torch.tensor([[tok_id] * 4096], device="cuda")
attn_mask = torch.ones_like(input_ids)
GEN = 64

def run_tpot(m, label):
    generate_from_ids(model=m, tokenizer=tok, input_ids=input_ids, attention_mask=attn_mask,
        max_new_tokens=8, kv_mode="int4_ours_asym", decode_attn_impl="triton_int4_asym",
        seed=42, stop_on_eos=False)
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    generate_from_ids(model=m, tokenizer=tok, input_ids=input_ids, attention_mask=attn_mask,
        max_new_tokens=GEN, kv_mode="int4_ours_asym", decode_attn_impl="triton_int4_asym",
        seed=42, stop_on_eos=False)
    torch.cuda.synchronize()
    ms = (time.perf_counter() - t0) / GEN * 1000
    print(f"{label}: {ms:.2f} ms/step")
    return ms

# Normal
t_normal = run_tpot(model, "Normal")

# torch.compile (default mode)
print("\nCompiling model (mode=default)...")
try:
    compiled = torch.compile(model, mode="default")
    t_default = run_tpot(compiled, "compile(default)")
except Exception as e:
    print(f"compile(default) failed: {type(e).__name__}: {e}")
    t_default = None

# torch.compile (reduce-overhead = CUDA graphs)
print("\nCompiling model (mode=reduce-overhead)...")
try:
    compiled_ro = torch.compile(model, mode="reduce-overhead")
    t_ro = run_tpot(compiled_ro, "compile(reduce-overhead)")
except Exception as e:
    print(f"compile(reduce-overhead) failed: {type(e).__name__}: {e}")
    t_ro = None

print("\n=== Summary ===")
print(f"Normal:              {t_normal:.2f} ms/step")
if t_default: print(f"compile(default):    {t_default:.2f} ms/step ({(t_default-t_normal)/t_normal*100:+.1f}%)")
if t_ro: print(f"compile(reduce-oh):  {t_ro:.2f} ms/step ({(t_ro-t_normal)/t_normal*100:+.1f}%)")
