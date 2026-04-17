#!/usr/bin/env python3
"""
Behavior-Aligned KV Precision Allocator (POC, 72h sprint).

核心思想：attention-KL 校准产物中的 per-layer k_scale 振幅反映了量化敏感度；
把 top-k 敏感层保为 INT8、其他层压为 INT4，在"几乎不增加存储"的前提下改善质量。

使用方式:
  python behavior_aligned_allocator.py \
      --calib artifacts/kv_calib_kl_selected_v2.json \
      --policy top_k --k 3 \
      --out artifacts/adaptive_policy_top3.json

生成的 policy JSON 结构:
  {
    "model_id": "...",
    "num_layers": 28,
    "policy_name": "top_3_protection",
    "avg_bits": 4.43,
    "per_layer_bits": [(k_bits, v_bits), ...]  # len = num_layers
  }

后续 MixedKVCache 加载该 policy 时按 per_layer_bits[layer_id] 分配精度。
"""

import argparse
import json
from pathlib import Path

import numpy as np


def compute_layer_sensitivity(calib: dict) -> np.ndarray:
    """用 per-layer max(k_scale) 作为敏感度代理。"""
    k_scale = np.array(calib["k_scale"])  # (L, H_kv, G)
    return k_scale.max(axis=tuple(range(1, k_scale.ndim)))


def policy_top_k(sens: np.ndarray, k: int,
                 high_bits: tuple = (8, 8), low_bits: tuple = (4, 4)) -> list:
    """Top-k 最敏感层保高比特，其他低比特。"""
    L = len(sens)
    top_k_layers = set(np.argsort(sens)[-k:].tolist())
    return [high_bits if i in top_k_layers else low_bits for i in range(L)]


def policy_threshold(sens: np.ndarray, thresh: float,
                     high_bits: tuple = (8, 8), low_bits: tuple = (4, 4)) -> list:
    """敏感度超过阈值的层保高比特。"""
    return [high_bits if s > thresh else low_bits for s in sens]


def policy_uniform(L: int, bits: tuple) -> list:
    """所有层同精度（baseline 对照）。"""
    return [bits for _ in range(L)]


def policy_random_k(L: int, k: int, seed: int,
                    high_bits: tuple = (8, 8), low_bits: tuple = (4, 4)) -> list:
    """随机选 k 层保高比特（负对照，证明 top-k 不是偶然）。"""
    rng = np.random.default_rng(seed)
    chosen = set(rng.choice(L, size=k, replace=False).tolist())
    return [high_bits if i in chosen else low_bits for i in range(L)]


def compute_avg_bits(per_layer: list) -> float:
    """计算平均 bit（K 和 V 各半）。"""
    total = sum((k + v) / 2.0 for (k, v) in per_layer)
    return total / len(per_layer)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calib", required=True, help="校准产物 JSON")
    ap.add_argument("--policy", choices=["top_k", "threshold", "uniform", "random_k"],
                    default="top_k")
    ap.add_argument("--k", type=int, default=3, help="top-k 或 random-k 的 k 值")
    ap.add_argument("--threshold", type=float, default=0.3)
    ap.add_argument("--high_bits", nargs=2, type=int, default=[8, 8],
                    help="高精度层的 (k_bits, v_bits)")
    ap.add_argument("--low_bits", nargs=2, type=int, default=[4, 4],
                    help="低精度层的 (k_bits, v_bits)")
    ap.add_argument("--uniform_bits", nargs=2, type=int, default=[4, 4])
    ap.add_argument("--seed", type=int, default=42, help="random_k 用")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    calib = json.load(open(args.calib))
    L = calib["num_layers"]
    high = tuple(args.high_bits)
    low = tuple(args.low_bits)

    if args.policy == "uniform":
        per_layer = policy_uniform(L, tuple(args.uniform_bits))
        name = f"uniform_k{args.uniform_bits[0]}v{args.uniform_bits[1]}"
    elif args.policy == "top_k":
        sens = compute_layer_sensitivity(calib)
        per_layer = policy_top_k(sens, args.k, high, low)
        name = f"top_{args.k}_protection"
    elif args.policy == "threshold":
        sens = compute_layer_sensitivity(calib)
        per_layer = policy_threshold(sens, args.threshold, high, low)
        name = f"threshold_{args.threshold}"
    elif args.policy == "random_k":
        per_layer = policy_random_k(L, args.k, args.seed, high, low)
        name = f"random_{args.k}_seed{args.seed}"
    else:
        raise ValueError(args.policy)

    avg_bits = compute_avg_bits(per_layer)
    policy = {
        "model_id": calib.get("model_id"),
        "num_layers": L,
        "policy_name": name,
        "avg_bits": round(avg_bits, 3),
        "high_bits": list(high),
        "low_bits": list(low),
        "per_layer_bits": per_layer,
    }

    if args.policy in ("top_k", "threshold"):
        sens = compute_layer_sensitivity(calib)
        policy["layer_sensitivity"] = [float(s) for s in sens]
        policy["protected_layers"] = sorted(
            [i for i, b in enumerate(per_layer) if b == high]
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(policy, open(out_path, "w"), indent=2)
    print(f"Policy saved: {out_path}")
    print(f"  name = {name}")
    print(f"  avg_bits = {avg_bits:.3f}")
    if "protected_layers" in policy:
        print(f"  protected layers = {policy['protected_layers']}")


if __name__ == "__main__":
    main()
