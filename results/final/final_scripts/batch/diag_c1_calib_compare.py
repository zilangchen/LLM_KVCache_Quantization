#!/usr/bin/env python3
"""Compare KL vs MSE calibration parameters for 7B."""
import json

for label, path in [
    ("MSE 7B", "artifacts/kv_calib_mse_7b_int4_rolealign_v1.json"),
    ("KL 7B (v3)", "artifacts/kv_calib_rolealign_7b_v3.json"),
]:
    print(f"=== {label}: {path} ===")
    try:
        d = json.load(open(path))
        if "role_aware" in d:
            ra = d["role_aware"]
            print(f"  k_percentile: {ra.get('k_percentile', '?')}")
            print(f"  v_percentile: {ra.get('v_percentile', '?')}")
            if "k_search_results" in ra:
                ksr = ra["k_search_results"]
                if isinstance(ksr, list) and len(ksr) > 0:
                    print(f"  k_search top-3: {ksr[:3]}")
        elif "k_calibration" in d:
            kc = d["k_calibration"]
            print(f"  k_percentile: {kc.get('k_percentile', '?')}")
            if "v_calibration" in d:
                vc = d["v_calibration"]
                print(f"  v_percentile: {vc.get('v_percentile', '?')}")
        else:
            print(f"  top keys: {list(d.keys())[:12]}")
            print(f"  loss_function: {d.get('loss_function', '?')}")
    except Exception as e:
        print(f"  error: {e}")
    print()
