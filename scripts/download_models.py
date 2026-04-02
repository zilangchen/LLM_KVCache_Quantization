#!/usr/bin/env python3
"""Download models to HF cache. Run with network enabled."""
import os, sys, gc
# Do NOT set HF_HUB_OFFLINE here — we need network

from transformers import AutoModelForCausalLM, AutoTokenizer

models = [
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
]

for mid in models:
    print(f"\n=== Downloading {mid} ===", flush=True)
    try:
        tok = AutoTokenizer.from_pretrained(mid)
        print(f"  tokenizer: OK", flush=True)
    except Exception as e:
        print(f"  tokenizer: FAIL — {e}", flush=True)
        sys.exit(1)
    try:
        m = AutoModelForCausalLM.from_pretrained(mid, dtype="auto", device_map="cpu")
        n = sum(p.numel() for p in m.parameters())
        print(f"  model: OK ({n/1e9:.1f}B params)", flush=True)
        del m, tok
        gc.collect()
    except Exception as e:
        print(f"  model: FAIL — {e}", flush=True)
        sys.exit(1)

print("\n=== All models downloaded ===", flush=True)
