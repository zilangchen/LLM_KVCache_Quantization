#!/usr/bin/env python3
"""
Phase 2 编号 6 policy routing verifier.

独立 CLI sanity check：给一个 policy JSON，验证：
  1. JSON schema 合法（含 per_layer_bits + avg_bits + 等字段）
  2. MixedKVCache 能用此 policy 构造（per_layer_bits 通过校验）
  3. `_resolve_bits(layer_id)` 返回的 bits 与 JSON 逐层一致
  4. 不同 layer 确实分配到不同 bits（对 non-uniform policy 而言）
  5. 打印 protected_layers summary + avg_bits 供人工 cross-check

用法:
  python3 scripts/verify_policy_routing.py --policy artifacts/allocator/bakv_top3.json

输出：
  policy name / num_layers / avg_bits
  per-layer bit allocation
  cache._resolve_bits(i) vs JSON 对齐验证
  最终 PASS/FAIL
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Ensure project root is importable when this script is invoked via `python scripts/...`.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.cache.mixed_kv_cache import MixedKVCache


def load_policy(path: Path) -> dict:
    data = json.load(open(path))
    required_keys = ["num_layers", "policy_name", "avg_bits", "per_layer_bits"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ValueError(f"policy JSON missing required keys: {missing}")
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True, type=Path, help="policy JSON path")
    ap.add_argument("--device", default="cpu",
                    help="device for MixedKVCache construction (cpu OK for this sanity check, default cpu)")
    args = ap.parse_args()

    if not args.policy.exists():
        print(f"FATAL: policy file not found: {args.policy}")
        sys.exit(2)

    policy = load_policy(args.policy)
    L = policy["num_layers"]
    name = policy["policy_name"]
    avg_bits = policy.get("avg_bits")
    protected = policy.get("protected_layers", [])
    per_layer_raw = policy["per_layer_bits"]

    print("=" * 60)
    print(f"Policy: {name}")
    print(f"  file          : {args.policy}")
    print(f"  num_layers    : {L}")
    print(f"  avg_bits      : {avg_bits}")
    print(f"  protected     : {protected}")
    print(f"  per_layer_bits: (showing first 3 + last 3)")
    for i in list(range(min(3, L))) + ["..."] + list(range(max(0, L - 3), L)):
        if i == "...":
            print("        ...")
            continue
        print(f"    layer {i:3d}: {tuple(per_layer_raw[i])}")
    print("=" * 60)

    # Build MixedKVCache with this policy (dry construction, no actual quantize).
    try:
        cache = MixedKVCache(
            num_layers=L,
            device=args.device,
            per_layer_bits=[tuple(x) for x in per_layer_raw],
        )
    except Exception as e:
        print(f"FATAL: MixedKVCache construction failed with policy: {e}")
        sys.exit(1)

    # Verify _resolve_bits matches JSON per layer.
    mismatches = []
    for i in range(L):
        got = cache._resolve_bits(i)
        expected = tuple(per_layer_raw[i])
        if got != expected:
            mismatches.append((i, got, expected))

    print()
    print(f"_resolve_bits consistency: {'PASS' if not mismatches else 'FAIL'}")
    if mismatches:
        print(f"  {len(mismatches)} mismatches:")
        for i, got, expected in mismatches[:5]:
            print(f"    layer {i}: resolve={got} JSON={expected}")
        sys.exit(1)

    # Confirm the cache truly has differentiated bit-width per layer (sanity for non-uniform).
    unique_configs = set(tuple(x) for x in per_layer_raw)
    print(f"Unique (k_bits, v_bits) pairs in policy: {len(unique_configs)} {sorted(unique_configs)}")
    if len(unique_configs) == 1:
        print("  NOTE: policy is uniform (all layers same bits) — acceptable for Uniform-INT4/INT8 baselines")
    else:
        print(f"  Non-uniform policy dispatches {len(unique_configs)} distinct bit configurations ✓")

    # Final
    print()
    print("=" * 60)
    print("🟢 PASS: policy JSON valid, MixedKVCache consumes per-layer bits correctly")
    print("=" * 60)


if __name__ == "__main__":
    main()
