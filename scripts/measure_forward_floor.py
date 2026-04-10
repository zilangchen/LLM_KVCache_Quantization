"""Measure pure model forward time as absolute floor for decode step."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "Qwen/Qwen2.5-1.5B-Instruct"
tok = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.float16, device_map="cuda")
model.eval()

input_ids = torch.tensor([[42]], device="cuda")

# Warmup
for _ in range(10):
    with torch.no_grad():
        model(input_ids=input_ids, use_cache=False)
torch.cuda.synchronize()

# Pure forward (no KV cache)
N = 100
torch.cuda.synchronize()
t0 = time.perf_counter()
for _ in range(N):
    with torch.no_grad():
        model(input_ids=input_ids, use_cache=False)
torch.cuda.synchronize()
t_no_cache = (time.perf_counter() - t0) / N * 1000

# Forward WITH FP16 KV cache (HF native)
from transformers import DynamicCache
dummy_cache = DynamicCache()
# Prefill to populate cache
prefill_ids = torch.tensor([[42] * 4096], device="cuda")
with torch.no_grad():
    out = model(input_ids=prefill_ids, use_cache=True)
    dummy_cache = out.past_key_values

# Warmup decode with cache
for _ in range(5):
    with torch.no_grad():
        model(input_ids=input_ids, past_key_values=dummy_cache, use_cache=True)
torch.cuda.synchronize()

# Timed decode with FP16 cache
torch.cuda.synchronize()
t0 = time.perf_counter()
for _ in range(N):
    with torch.no_grad():
        model(input_ids=input_ids, past_key_values=dummy_cache, use_cache=True)
torch.cuda.synchronize()
t_fp16_cache = (time.perf_counter() - t0) / N * 1000

print(f"Pure forward (no cache):        {t_no_cache:.2f} ms")
print(f"Decode with FP16 cache (4K):    {t_fp16_cache:.2f} ms")
print(f"FP16 attention overhead:        {t_fp16_cache - t_no_cache:+.2f} ms")
print(f"Per-layer (28L): no_cache={t_no_cache/28:.3f}ms, fp16_cache={t_fp16_cache/28:.3f}ms")
