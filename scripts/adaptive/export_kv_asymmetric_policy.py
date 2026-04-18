#!/usr/bin/env python3
"""Export a role-aware K/V asymmetric layer-wise policy JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure repo root is in sys.path so `from scripts.adaptive.xxx import ...`
# resolves when invoked as a standalone script (e.g.,
# `python3 scripts/adaptive/export_kv_asymmetric_policy.py --calib_file ...`).
# Avoids requiring `python -m scripts.adaptive.xxx` or adding __init__.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.adaptive.behavior_aligned_allocator import export_kv_asymmetric_policy


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a K/V asymmetric layer-wise policy for int4_mixed_kv.",
        allow_abbrev=False,
    )
    parser.add_argument("--calib_file", required=True, help="Calibration JSON with k_scale / v_scale.")
    parser.add_argument(
        "--budget_mode",
        choices=["avg_bits", "role_slots"],
        default="avg_bits",
        help="Budget interpretation for K/V upgrades.",
    )
    parser.add_argument(
        "--budget_value",
        type=float,
        default=5.0,
        help="Budget value matching --budget_mode. avg_bits uses layer-average bits.",
    )
    parser.add_argument(
        "--sensitivity_agg",
        choices=["max", "mean"],
        default="max",
        help="Aggregation applied to k_scale / v_scale before role scoring.",
    )
    parser.add_argument("--k_bias", type=float, default=1.15, help="Multiplicative bias on K scores.")
    parser.add_argument("--v_bias", type=float, default=1.0, help="Multiplicative bias on V scores.")
    parser.add_argument("--high_bit", type=int, default=8, help="High bit-width (default: 8).")
    parser.add_argument("--low_bit", type=int, default=4, help="Low bit-width (default: 4).")
    parser.add_argument("--policy_name", default="kv_asymmetric_layerwise", help="Logical policy name.")
    parser.add_argument("--out", required=True, help="Output policy JSON path.")
    args = parser.parse_args()

    with open(args.calib_file, encoding="utf-8") as handle:
        calib = json.load(handle)

    policy = export_kv_asymmetric_policy(
        calib,
        out_path=Path(args.out),
        policy_name=args.policy_name,
        budget_mode=args.budget_mode,
        budget_value=args.budget_value,
        agg=args.sensitivity_agg,
        k_bias=args.k_bias,
        v_bias=args.v_bias,
        high_bit=args.high_bit,
        low_bit=args.low_bit,
    )

    print(f"Policy saved: {args.out}")
    print(f"  policy_type = {policy['policy_type']}")
    print(f"  avg_bits = {policy['avg_bits']:.3f}")
    print(f"  role_slots = {policy['role_slots']}")
    print(f"  k_only_layers = {policy['k_only_layers']}")
    print(f"  v_only_layers = {policy['v_only_layers']}")


if __name__ == "__main__":
    main()
