#!/usr/bin/env python3
"""Build a prompt-adaptive policy pool manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_POLICY_CANDIDATES = {
    "1p5b": {
        "fixed_k": [
            "artifacts/allocator/l2_kv_asymmetric/1p5b/bakv_k3.json",
            "artifacts/allocator/sweep/bakv_k3.json",
            "artifacts/allocator/bakv_top3.json",
        ],
        "heuristic": [
            "artifacts/allocator/sweep/heuristic_k3.json",
        ],
        "auto_k": [
            "artifacts/allocator/l2_kv_asymmetric/1p5b/bakv_auto_cov80_max.json",
            "artifacts/allocator/sweep/bakv_auto_cov80_max.json",
        ],
        "role_aware": [
            "artifacts/allocator/l2_kv_asymmetric/1p5b/kv_asym_avgbits5p0.json",
        ],
    },
    "7b": {
        "fixed_k": [
            "artifacts/allocator/l2_kv_asymmetric/7b/bakv_k3.json",
            "artifacts/allocator/sweep_7b/bakv_k3.json",
        ],
        "heuristic": [
            "artifacts/allocator/sweep_7b/heuristic_k3.json",
        ],
        "auto_k": [
            "artifacts/allocator/l2_kv_asymmetric/7b/bakv_auto_cov80_max.json",
            "artifacts/allocator/sweep_7b/bakv_auto_cov80_max.json",
        ],
        "role_aware": [
            "artifacts/allocator/l2_kv_asymmetric/7b/kv_asym_avgbits5p0.json",
        ],
    },
    "8b": {
        "fixed_k": [
            "artifacts/allocator/sweep_8b/bakv_k11.json",
            "artifacts/allocator/sweep_8b/bakv_k9.json",
        ],
        "heuristic": [
            "artifacts/allocator/sweep_8b/heuristic_k11.json",
            "artifacts/allocator/sweep_8b/heuristic_k9.json",
        ],
        "auto_k": [
            "artifacts/allocator/l2_kv_asymmetric/8b/bakv_auto_cov80_max.json",
            "artifacts/allocator/sweep_8b/bakv_auto_cov80_max.json",
        ],
        "role_aware": [
            "artifacts/allocator/l2_kv_asymmetric/8b/kv_asym_avgbits5p0.json",
        ],
    },
}


def _resolve_default_path(model_key: str, policy_id: str, project_root: Path) -> str | None:
    for candidate in DEFAULT_POLICY_CANDIDATES.get(model_key, {}).get(policy_id, []):
        path = project_root / candidate
        if path.exists():
            return str(path)
    return None


def build_policy_pool(
    *,
    model_key: str,
    project_root: Path,
    fixed_k_policy: str | None,
    heuristic_policy: str | None,
    auto_k_policy: str | None,
    role_aware_policy: str | None,
) -> dict:
    pool = {
        "pool_type": "prompt_policy_pool_v1",
        "model_key": model_key,
        "policies": [],
    }
    requested = {
        "fixed_k": fixed_k_policy,
        "heuristic": heuristic_policy,
        "auto_k": auto_k_policy,
        "role_aware": role_aware_policy,
    }
    for policy_id, explicit_path in requested.items():
        path = explicit_path or _resolve_default_path(model_key, policy_id, project_root)
        if path is None:
            if policy_id == "role_aware":
                continue
            raise FileNotFoundError(
                f"No policy path available for {policy_id!r} under model_key={model_key!r}"
            )
        resolved = Path(path)
        if not resolved.is_absolute():
            resolved = project_root / resolved
        if not resolved.exists():
            raise FileNotFoundError(f"policy file missing for {policy_id!r}: {resolved}")
        pool["policies"].append(
            {
                "policy_id": policy_id,
                "label": policy_id,
                "policy_json": str(resolved),
            }
        )
    return pool


def main() -> None:
    parser = argparse.ArgumentParser(description="Build prompt-adaptive policy pool.", allow_abbrev=False)
    parser.add_argument("--model_key", required=True, choices=sorted(DEFAULT_POLICY_CANDIDATES))
    parser.add_argument("--fixed_k_policy", default=None)
    parser.add_argument("--heuristic_policy", default=None)
    parser.add_argument("--auto_k_policy", default=None)
    parser.add_argument("--role_aware_policy", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    payload = build_policy_pool(
        model_key=args.model_key,
        project_root=project_root,
        fixed_k_policy=args.fixed_k_policy,
        heuristic_policy=args.heuristic_policy,
        auto_k_policy=args.auto_k_policy,
        role_aware_policy=args.role_aware_policy,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"Saved pool: {out_path}")


if __name__ == "__main__":
    main()
