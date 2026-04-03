"""Quick check of 8B INT8 calibration file."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "artifacts/kv_calib_kl_llama31_8b_int8.json"
c = json.load(open(path))
print(f"version={c.get('version')}")
print(f"keys={list(c.keys())}")
for k in ["k_scale", "static_k_scale", "v_scale", "static_v_scale"]:
    if k in c:
        v = c[k]
        if isinstance(v, list):
            print(f"{k}: layers={len(v)}, first_type={type(v[0]).__name__}, first_len={len(v[0]) if hasattr(v[0],'__len__') else 'scalar'}")
print(f"has_inv_tau={'inv_tau' in c}")
sk = c.get("static_k_scale", c.get("k_scale", []))
if sk and isinstance(sk[0], list):
    print(f"first_layer_scale_len={len(sk[0])}")
    # LLaMA-3.1-8B: 8 KV heads, head_dim=128, group_size=128 → 8 groups
    # Qwen2.5-1.5B: 2 KV heads, head_dim=128, group_size=128 → 2 groups
    n = len(sk[0])
    if n == 2:
        print("WARNING: scale has 2 elements — this is a 1.5B calibration file, NOT 8B!")
    elif n == 8:
        print("OK: scale has 8 elements — matches LLaMA-3.1-8B (8 KV heads)")
    elif n == 4:
        print("WARNING: scale has 4 elements — this is a 7B calibration file, NOT 8B!")
