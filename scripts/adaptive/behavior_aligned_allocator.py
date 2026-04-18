#!/usr/bin/env python3
"""
Behavior-aligned precision allocator helpers.

This module still powers the existing layer-wise allocator policies
(`top_k`, `heuristic`, `random_k`, `auto_k_coverage`) and now also exposes
the role-aware K/V asymmetric helpers used by L2.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


SUPPORTED_BITS = {4, 8, 16}


def _as_array(calib: dict[str, Any], key: str) -> np.ndarray:
    if key not in calib:
        raise KeyError(f"calibration missing required key {key!r}")
    arr = np.asarray(calib[key], dtype=float)
    if arr.ndim < 1:
        raise ValueError(f"{key!r} must have at least one dimension, got shape={arr.shape}")
    return arr


def _aggregate_role_scale(calib: dict[str, Any], key: str, agg: str = "max") -> np.ndarray:
    """Aggregate a per-role calibration tensor to layer-level scores."""
    arr = _as_array(calib, key)
    axes = tuple(range(1, arr.ndim))
    if agg == "max":
        return arr.max(axis=axes)
    if agg == "mean":
        return arr.mean(axis=axes)
    raise ValueError(
        f"sensitivity_agg must be 'max' or 'mean' (got {agg!r}). "
        "'random' is NOT valid for sensitivity_agg — use --policy random_k directly "
        "(Codex 2026-04-18 06:55 修订，语义清洁)。"
    )


def _normalize_scores(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return values.astype(float)
    vmax = float(np.max(values))
    if vmax <= 0.0:
        return np.zeros_like(values, dtype=float)
    return values.astype(float) / vmax


def _importance_tiers(combined: np.ndarray, high_fraction: float, medium_fraction: float) -> list[str]:
    if not (0.0 < high_fraction <= medium_fraction <= 1.0):
        raise ValueError(
            "tier fractions must satisfy 0 < high_fraction <= medium_fraction <= 1"
        )
    num_layers = len(combined)
    if num_layers == 0:
        return []
    order = np.argsort(combined)[::-1]
    high_count = max(1, min(num_layers, int(math.ceil(num_layers * high_fraction))))
    medium_count = max(high_count, min(num_layers, int(math.ceil(num_layers * medium_fraction))))
    high_layers = set(order[:high_count].tolist())
    medium_layers = set(order[:medium_count].tolist())
    tiers = []
    for layer_idx in range(num_layers):
        if layer_idx in high_layers:
            tiers.append("high")
        elif layer_idx in medium_layers:
            tiers.append("medium")
        else:
            tiers.append("low")
    return tiers


def compute_layer_sensitivity(calib: dict[str, Any], agg: str = "max") -> np.ndarray:
    """Use per-layer `k_scale` aggregation as the original layer sensitivity proxy."""
    return _aggregate_role_scale(calib, "k_scale", agg=agg)


def compute_role_sensitivity(calib: dict[str, Any], agg: str = "max") -> tuple[np.ndarray, np.ndarray]:
    """Return layer-level K / V sensitivity proxies."""
    k_sens = _aggregate_role_scale(calib, "k_scale", agg=agg)
    v_sens = _aggregate_role_scale(calib, "v_scale", agg=agg)
    if k_sens.shape != v_sens.shape:
        raise ValueError(
            f"k_scale and v_scale layer shapes must match, got {k_sens.shape} vs {v_sens.shape}"
        )
    return k_sens, v_sens


def score_kv_roles(
    calib: dict[str, Any],
    *,
    agg: str = "max",
    k_bias: float = 1.15,
    v_bias: float = 1.0,
    high_fraction: float = 0.25,
    medium_fraction: float = 0.50,
) -> dict[str, Any]:
    """Build per-layer K/V role scores for the L2 asymmetric allocator.

    The scoring intentionally keeps the logic simple:
    - aggregate K/V scales independently to layer level
    - normalize per role to [0, 1]
    - apply a light K-side bias
    - rank importance by max(k_score, v_score)
    """

    if k_bias <= 0.0 or v_bias <= 0.0:
        raise ValueError("k_bias and v_bias must be > 0")

    k_raw, v_raw = compute_role_sensitivity(calib, agg=agg)
    k_norm = _normalize_scores(k_raw)
    v_norm = _normalize_scores(v_raw)
    k_score = k_norm * float(k_bias)
    v_score = v_norm * float(v_bias)
    combined = np.maximum(k_score, v_score)
    tiers = _importance_tiers(combined, high_fraction=high_fraction, medium_fraction=medium_fraction)
    order = np.argsort(combined)[::-1].tolist()
    return {
        "k_raw": k_raw,
        "v_raw": v_raw,
        "k_score": k_score,
        "v_score": v_score,
        "combined_score": combined,
        "importance_tier": tiers,
        "combined_order": order,
        "k_bias": float(k_bias),
        "v_bias": float(v_bias),
        "sensitivity_agg": agg,
    }


def policy_top_k(
    sens: np.ndarray,
    k: int,
    high_bits: tuple[int, int] = (8, 8),
    low_bits: tuple[int, int] = (4, 4),
) -> list[tuple[int, int]]:
    """Top-k most sensitive layers keep higher precision."""
    num_layers = len(sens)
    top_k_layers = set(np.argsort(sens)[-k:].tolist())
    return [high_bits if i in top_k_layers else low_bits for i in range(num_layers)]


def policy_threshold(
    sens: np.ndarray,
    thresh: float,
    high_bits: tuple[int, int] = (8, 8),
    low_bits: tuple[int, int] = (4, 4),
) -> list[tuple[int, int]]:
    """Layers above threshold keep higher precision."""
    return [high_bits if score > thresh else low_bits for score in sens]


def select_top_k_by_coverage(
    sens: np.ndarray,
    coverage: float,
    min_k: int = 1,
    max_k: int | None = None,
) -> tuple[int, list[int], float]:
    """Select the smallest k whose cumulative sensitivity reaches the coverage target."""
    if not (0.0 < coverage <= 1.0):
        raise ValueError(f"coverage must be in (0, 1], got {coverage!r}")
    num_layers = len(sens)
    if num_layers <= 0:
        raise ValueError("sensitivity must contain at least one layer")
    if min_k < 1:
        raise ValueError(f"min_k must be >= 1, got {min_k}")
    if max_k is None:
        max_k = num_layers
    if max_k < min_k:
        raise ValueError(f"max_k must be >= min_k (got min_k={min_k}, max_k={max_k})")

    max_k = min(max_k, num_layers)
    order = np.argsort(sens)[::-1]
    ordered = sens[order]
    total = float(np.sum(ordered))

    if total <= 0.0:
        selected_k = min_k
        achieved = 0.0
    else:
        cum = np.cumsum(ordered)
        target = coverage * total
        selected_k = int(np.searchsorted(cum, target, side="left")) + 1
        achieved = float(cum[min(selected_k, num_layers) - 1] / total)

    selected_k = max(min_k, min(selected_k, max_k))
    protected = sorted(order[:selected_k].tolist())
    if total > 0.0:
        achieved = float(np.sum(sens[protected]) / total)
    return selected_k, protected, achieved


def propose_auto_k_range(
    sens: np.ndarray,
    coverage_targets: list[float] | tuple[float, ...],
    min_k: int = 1,
    max_k: int | None = None,
) -> dict[str, Any]:
    """Build a small candidate band instead of a single oracle k."""
    if not coverage_targets:
        raise ValueError("coverage_targets must not be empty")
    normalized = [float(c) for c in coverage_targets]
    proposals = []
    for cov in normalized:
        k, protected, achieved = select_top_k_by_coverage(
            sens,
            coverage=cov,
            min_k=min_k,
            max_k=max_k,
        )
        proposals.append(
            {
                "coverage": cov,
                "selected_k": int(k),
                "protected_layers": protected,
                "achieved_coverage": float(achieved),
            }
        )

    candidate_ks = sorted({item["selected_k"] for item in proposals})
    recommended = min(
        proposals,
        key=lambda item: (abs(item["coverage"] - 0.8), item["selected_k"]),
    )
    return {
        "coverage_targets": normalized,
        "proposals": proposals,
        "candidate_ks": candidate_ks,
        "recommended_k": int(recommended["selected_k"]),
        "recommended_coverage": float(recommended["coverage"]),
    }


def policy_auto_k_coverage(
    sens: np.ndarray,
    coverage: float,
    high_bits: tuple[int, int] = (8, 8),
    low_bits: tuple[int, int] = (4, 4),
    min_k: int = 1,
    max_k: int | None = None,
) -> tuple[list[tuple[int, int]], int, list[int], float]:
    """Select protected layers from a coverage target."""
    selected_k, protected, achieved = select_top_k_by_coverage(
        sens,
        coverage=coverage,
        min_k=min_k,
        max_k=max_k,
    )
    protected_set = set(protected)
    per_layer = [high_bits if i in protected_set else low_bits for i in range(len(sens))]
    return per_layer, selected_k, protected, achieved


def policy_uniform(num_layers: int, bits: tuple[int, int]) -> list[tuple[int, int]]:
    return [bits for _ in range(num_layers)]


def policy_random_k(
    num_layers: int,
    k: int,
    seed: int,
    high_bits: tuple[int, int] = (8, 8),
    low_bits: tuple[int, int] = (4, 4),
) -> list[tuple[int, int]]:
    rng = np.random.default_rng(seed)
    chosen = set(rng.choice(num_layers, size=k, replace=False).tolist())
    return [high_bits if i in chosen else low_bits for i in range(num_layers)]


def policy_heuristic(
    num_layers: int,
    k: int,
    high_bits: tuple[int, int] = (8, 8),
    low_bits: tuple[int, int] = (4, 4),
) -> list[tuple[int, int]]:
    """Equally spaced layer-position heuristic."""
    if k <= 0:
        raise ValueError(f"heuristic policy requires k > 0, got {k}")
    if k > num_layers:
        k = num_layers
    if k == 1:
        chosen = {num_layers // 2}
    elif k == 2:
        chosen = {0, num_layers - 1}
    else:
        positions = np.linspace(0, num_layers - 1, k).round().astype(int).tolist()
        chosen = set(positions)
    return [high_bits if i in chosen else low_bits for i in range(num_layers)]


def compute_avg_bits(per_layer: list[tuple[int, int]]) -> float:
    total = sum((k_bits + v_bits) / 2.0 for (k_bits, v_bits) in per_layer)
    return total / len(per_layer)


def _coerce_bit(bit: int) -> int:
    bit = int(bit)
    if bit not in SUPPORTED_BITS:
        raise ValueError(f"unsupported bit-width {bit}; expected one of {sorted(SUPPORTED_BITS)}")
    return bit


def assign_kv_bit_pairs(
    role_scores: dict[str, Any],
    *,
    budget_mode: str = "avg_bits",
    budget_value: float = 5.0,
    high_bit: int = 8,
    low_bit: int = 4,
) -> dict[str, Any]:
    """Assign per-layer `(k_bits, v_bits)` from role scores under a simple budget.

    Supported budget modes:
    - `avg_bits`: target layer-average bit-width (e.g. 5.0)
    - `role_slots`: explicit number of role upgrades across all layer-role pairs
    """

    high_bit = _coerce_bit(high_bit)
    low_bit = _coerce_bit(low_bit)
    if high_bit <= low_bit:
        raise ValueError(f"high_bit must be > low_bit, got low={low_bit}, high={high_bit}")

    k_score = np.asarray(role_scores["k_score"], dtype=float)
    v_score = np.asarray(role_scores["v_score"], dtype=float)
    if k_score.shape != v_score.shape:
        raise ValueError(f"k_score and v_score must match, got {k_score.shape} vs {v_score.shape}")
    num_layers = len(k_score)
    if num_layers == 0:
        raise ValueError("role_scores must contain at least one layer")

    if budget_mode == "avg_bits":
        target_avg_bits = float(budget_value)
        if target_avg_bits < low_bit or target_avg_bits > high_bit:
            raise ValueError(
                f"avg_bits target must be within [{low_bit}, {high_bit}], got {target_avg_bits}"
            )
        slot_delta = (high_bit - low_bit) / 2.0
        raw_slots = (target_avg_bits - low_bit) * num_layers / slot_delta
        role_slots = int(math.floor(raw_slots + 1e-9))
    elif budget_mode == "role_slots":
        role_slots = int(budget_value)
        target_avg_bits = low_bit + ((high_bit - low_bit) / 2.0) * (role_slots / num_layers)
    else:
        raise ValueError(
            f"budget_mode must be 'avg_bits' or 'role_slots' (got {budget_mode!r})"
        )

    role_slots = max(0, min(role_slots, num_layers * 2))

    candidates: list[tuple[float, int, str, int]] = []
    for layer_idx in range(num_layers):
        candidates.append((float(k_score[layer_idx]), 1, "k", layer_idx))
        candidates.append((float(v_score[layer_idx]), 0, "v", layer_idx))
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)

    selected_k = set()
    selected_v = set()
    for _, _, role, layer_idx in candidates[:role_slots]:
        if role == "k":
            selected_k.add(layer_idx)
        else:
            selected_v.add(layer_idx)

    per_layer_bits: list[tuple[int, int]] = []
    protected_layers = []
    k_only_layers = []
    v_only_layers = []
    high_layers = []
    medium_layers = []
    assignment_tier = []

    for layer_idx in range(num_layers):
        k_bits = high_bit if layer_idx in selected_k else low_bit
        v_bits = high_bit if layer_idx in selected_v else low_bit
        pair = (k_bits, v_bits)
        per_layer_bits.append(pair)
        if pair != (low_bit, low_bit):
            protected_layers.append(layer_idx)
        if pair == (high_bit, low_bit):
            k_only_layers.append(layer_idx)
            medium_layers.append(layer_idx)
            assignment_tier.append("medium")
        elif pair == (low_bit, high_bit):
            v_only_layers.append(layer_idx)
            medium_layers.append(layer_idx)
            assignment_tier.append("medium")
        elif pair == (high_bit, high_bit):
            high_layers.append(layer_idx)
            assignment_tier.append("high")
        else:
            assignment_tier.append("low")

    avg_bits = compute_avg_bits(per_layer_bits)
    return {
        "budget_mode": budget_mode,
        "budget_value": float(budget_value),
        "target_avg_bits": float(target_avg_bits),
        "role_slots": int(role_slots),
        "per_layer_bits": per_layer_bits,
        "avg_bits": float(avg_bits),
        "protected_layers": protected_layers,
        "k_only_layers": k_only_layers,
        "v_only_layers": v_only_layers,
        "high_layers": high_layers,
        "medium_layers": medium_layers,
        "assignment_tier": assignment_tier,
        "high_bit": int(high_bit),
        "low_bit": int(low_bit),
    }


def export_kv_asymmetric_policy(
    calib: dict[str, Any],
    out_path: str | Path,
    *,
    policy_name: str = "kv_asymmetric_layerwise",
    budget_mode: str = "avg_bits",
    budget_value: float = 5.0,
    agg: str = "max",
    k_bias: float = 1.15,
    v_bias: float = 1.0,
    high_bit: int = 8,
    low_bit: int = 4,
) -> dict[str, Any]:
    """Export a role-aware layer-wise policy JSON for `int4_mixed_kv`."""
    role_scores = score_kv_roles(
        calib,
        agg=agg,
        k_bias=k_bias,
        v_bias=v_bias,
    )
    assignment = assign_kv_bit_pairs(
        role_scores,
        budget_mode=budget_mode,
        budget_value=budget_value,
        high_bit=high_bit,
        low_bit=low_bit,
    )
    policy = {
        "policy_type": "kv_asymmetric_layerwise",
        "policy_name": policy_name,
        "model_id": calib.get("model_id"),
        "num_layers": int(calib.get("num_layers", len(assignment["per_layer_bits"]))),
        "avg_bits": round(float(assignment["avg_bits"]), 3),
        "budget_mode": budget_mode,
        "budget_value": float(budget_value),
        "target_avg_bits": round(float(assignment["target_avg_bits"]), 3),
        "role_slots": int(assignment["role_slots"]),
        "high_bits": [int(high_bit), int(high_bit)],
        "low_bits": [int(low_bit), int(low_bit)],
        "per_layer_bits": assignment["per_layer_bits"],
        "protected_layers": assignment["protected_layers"],
        "k_only_layers": assignment["k_only_layers"],
        "v_only_layers": assignment["v_only_layers"],
        "high_layers": assignment["high_layers"],
        "medium_layers": assignment["medium_layers"],
        "assignment_tier": assignment["assignment_tier"],
        "sensitivity_agg": agg,
        "k_bias": float(k_bias),
        "v_bias": float(v_bias),
        "k_score": [round(float(value), 6) for value in role_scores["k_score"]],
        "v_score": [round(float(value), 6) for value in role_scores["v_score"]],
        "combined_score": [round(float(value), 6) for value in role_scores["combined_score"]],
        "importance_tier": role_scores["importance_tier"],
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(policy, handle, indent=2, ensure_ascii=True)
    return policy


def main() -> None:
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--calib", required=True, help="校准产物 JSON")
    ap.add_argument(
        "--policy",
        choices=["top_k", "threshold", "uniform", "random_k", "heuristic", "auto_k_coverage"],
        default="top_k",
    )
    ap.add_argument("--k", type=int, default=3, help="top-k 或 random-k 的 k 值")
    ap.add_argument("--threshold", type=float, default=0.3)
    ap.add_argument(
        "--sensitivity_agg",
        choices=["max", "mean"],
        default="max",
        help="k_scale 聚合方式（编号 7 消融 1）；默认 max 保持与编号 6 backward compat",
    )
    ap.add_argument("--coverage", type=float, default=0.8, help="auto_k_coverage 的单点 target")
    ap.add_argument(
        "--coverage_targets",
        nargs="+",
        type=float,
        default=[0.7, 0.8, 0.9],
        help="auto-k 候选区间 coverage targets；默认 0.7 0.8 0.9",
    )
    ap.add_argument("--min_k", type=int, default=1, help="auto-k 最小保护层数")
    ap.add_argument("--max_k", type=int, default=0, help="auto-k 最大保护层数；0 表示不限制")
    ap.add_argument("--high_bits", nargs=2, type=int, default=[8, 8], help="高精度层的 (k_bits, v_bits)")
    ap.add_argument("--low_bits", nargs=2, type=int, default=[4, 4], help="低精度层的 (k_bits, v_bits)")
    ap.add_argument("--uniform_bits", nargs=2, type=int, default=[4, 4])
    ap.add_argument("--seed", type=int, default=42, help="random_k 用")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.calib, encoding="utf-8") as handle:
        calib = json.load(handle)

    num_layers = int(calib["num_layers"])
    high = tuple(args.high_bits)
    low = tuple(args.low_bits)
    max_k = None if args.max_k == 0 else args.max_k
    sens = None
    auto_meta = None

    if args.policy == "uniform":
        per_layer = policy_uniform(num_layers, tuple(args.uniform_bits))
        name = f"uniform_k{args.uniform_bits[0]}v{args.uniform_bits[1]}"
    elif args.policy == "top_k":
        sens = compute_layer_sensitivity(calib, agg=args.sensitivity_agg)
        per_layer = policy_top_k(sens, args.k, high, low)
        name = (
            f"top_{args.k}_protection"
            if args.sensitivity_agg == "max"
            else f"top_{args.k}_{args.sensitivity_agg}_protection"
        )
    elif args.policy == "threshold":
        sens = compute_layer_sensitivity(calib, agg=args.sensitivity_agg)
        per_layer = policy_threshold(sens, args.threshold, high, low)
        name = (
            f"threshold_{args.threshold}"
            if args.sensitivity_agg == "max"
            else f"threshold_{args.sensitivity_agg}_{args.threshold}"
        )
    elif args.policy == "auto_k_coverage":
        sens = compute_layer_sensitivity(calib, agg=args.sensitivity_agg)
        auto_meta = propose_auto_k_range(
            sens,
            coverage_targets=args.coverage_targets,
            min_k=args.min_k,
            max_k=max_k,
        )
        per_layer, selected_k, protected, achieved = policy_auto_k_coverage(
            sens,
            coverage=args.coverage,
            high_bits=high,
            low_bits=low,
            min_k=args.min_k,
            max_k=max_k,
        )
        coverage_tag = int(round(args.coverage * 100))
        name = f"auto_cov{coverage_tag}_{args.sensitivity_agg}"
    elif args.policy == "random_k":
        per_layer = policy_random_k(num_layers, args.k, args.seed, high, low)
        name = f"random_{args.k}_seed{args.seed}"
    elif args.policy == "heuristic":
        per_layer = policy_heuristic(num_layers, args.k, high, low)
        name = f"heuristic_{args.k}"
    else:
        raise ValueError(args.policy)

    avg_bits = compute_avg_bits(per_layer)
    policy: dict[str, Any] = {
        "model_id": calib.get("model_id"),
        "num_layers": num_layers,
        "policy_name": name,
        "avg_bits": round(avg_bits, 3),
        "high_bits": list(high),
        "low_bits": list(low),
        "per_layer_bits": per_layer,
    }

    if args.policy in ("top_k", "threshold", "auto_k_coverage"):
        policy["layer_sensitivity"] = [float(s) for s in sens]
        policy["sensitivity_agg"] = args.sensitivity_agg
    if args.policy == "auto_k_coverage":
        policy["selection_mode"] = "coverage_range"
        policy["coverage_target"] = float(args.coverage)
        policy["coverage_targets"] = [float(c) for c in auto_meta["coverage_targets"]]
        policy["candidate_ks"] = [int(k) for k in auto_meta["candidate_ks"]]
        policy["recommended_k"] = int(auto_meta["recommended_k"])
        policy["recommended_coverage"] = float(auto_meta["recommended_coverage"])
        policy["selected_k"] = int(selected_k)
        policy["achieved_coverage"] = float(achieved)
        policy["range_proposals"] = auto_meta["proposals"]
    if args.policy in ("top_k", "threshold", "heuristic", "random_k", "auto_k_coverage"):
        policy["protected_layers"] = sorted(
            [i for i, bits in enumerate(per_layer) if tuple(bits) == tuple(high)]
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(policy, handle, indent=2, ensure_ascii=True)

    print(f"Policy saved: {out_path}")
    print(f"  name = {name}")
    print(f"  avg_bits = {avg_bits:.3f}")
    if "protected_layers" in policy:
        print(f"  protected layers = {policy['protected_layers']}")
    if args.policy == "auto_k_coverage":
        print(f"  selected_k = {policy['selected_k']}")
        print(f"  candidate_ks = {policy['candidate_ks']}")
        print(
            f"  recommended_k = {policy['recommended_k']} @ cov={policy['recommended_coverage']:.2f}"
        )


if __name__ == "__main__":
    main()
