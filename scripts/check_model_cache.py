#!/usr/bin/env python3
"""Check if all 3 models are fully cached and loadable offline."""
import os, gc, sys
os.environ["HF_HUB_OFFLINE"] = "1"

from transformers import AutoModelForCausalLM, AutoTokenizer

models = [
    "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
]

all_ok = True
for mid in models:
    try:
        tok = AutoTokenizer.from_pretrained(mid)
        print(f"{mid}: tokenizer OK", flush=True)
    except Exception as e:
        print(f"{mid}: tokenizer FAIL — {type(e).__name__}: {e}", flush=True)
        all_ok = False
        continue
    try:
        m = AutoModelForCausalLM.from_pretrained(mid, torch_dtype="auto", device_map="cpu")
        n = sum(p.numel() for p in m.parameters())
        print(f"{mid}: model OK ({n/1e9:.1f}B params)", flush=True)
        del m, tok
        gc.collect()
    except Exception as e:
        print(f"{mid}: model FAIL — {type(e).__name__}: {e}", flush=True)
        all_ok = False

sys.exit(0 if all_ok else 1)
