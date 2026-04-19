#!/usr/bin/env python3
"""Export a task/profile bucket prompt-adaptive selector."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_TASK_ROUTES = {
    "narrativeqa": "fixed_k",
    "hotpotqa": "auto_k",
    "gov_report": "auto_k",
    "dureader": "auto_k",
    "lcc": "heuristic",
}


def _parse_mapping(items: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for raw in items:
        if "=" not in raw:
            raise ValueError(f"invalid route {raw!r}; expected key=policy_id")
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise ValueError(f"invalid route {raw!r}; empty key or value")
        mapping[key] = value
    return mapping


def _pool_ids(pool: dict) -> set[str]:
    return {item["policy_id"] for item in pool.get("policies", [])}


def build_selector(
    *,
    pool: dict,
    task_routes: dict[str, str],
    profile_routes: dict[str, str],
    default_policy_id: str,
) -> dict:
    valid_ids = _pool_ids(pool)
    if default_policy_id not in valid_ids:
        raise ValueError(f"default_policy_id={default_policy_id!r} not found in policy pool")
    for source_name, mapping in (("task", task_routes), ("profile", profile_routes)):
        for _, policy_id in mapping.items():
            if policy_id not in valid_ids:
                raise ValueError(f"{source_name} route points to unknown policy_id={policy_id!r}")
    return {
        "selector_type": "task_profile_bucket_v1",
        "features": ["task_id", "profile_bucket"],
        "policy_pool": pool["policies"],
        "routing_rules": {
            "by_task": task_routes,
            "by_profile_bucket": profile_routes,
            "default_policy_id": default_policy_id,
        },
    }


def resolve_policy_entry(selector: dict, task_id: str, profile_bucket: str = "default") -> dict:
    rules = selector["routing_rules"]
    pool = {item["policy_id"]: item for item in selector["policy_pool"]}
    if task_id not in rules["by_task"]:
        raise KeyError(f"unknown task_id={task_id!r}")
    if profile_bucket not in rules["by_profile_bucket"]:
        raise KeyError(f"unknown profile_bucket={profile_bucket!r}")
    policy_id = rules["by_task"].get(task_id) or rules["by_profile_bucket"][profile_bucket]
    if policy_id not in pool:
        raise KeyError(f"selector resolved to unknown policy_id={policy_id!r}")
    return pool[policy_id]


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a prompt-adaptive selector.", allow_abbrev=False)
    parser.add_argument("--policy_pool", required=True)
    parser.add_argument("--task_route", action="append", default=[], help="Repeatable task=policy_id rule.")
    parser.add_argument(
        "--profile_route",
        action="append",
        default=[],
        help="Repeatable profile_bucket=policy_id rule.",
    )
    parser.add_argument("--default_policy", default="auto_k")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    pool = json.loads(Path(args.policy_pool).read_text(encoding="utf-8"))
    task_routes = _parse_mapping(args.task_route) if args.task_route else dict(DEFAULT_TASK_ROUTES)
    profile_routes = _parse_mapping(args.profile_route) if args.profile_route else {"default": args.default_policy}
    selector = build_selector(
        pool=pool,
        task_routes=task_routes,
        profile_routes=profile_routes,
        default_policy_id=args.default_policy,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(selector, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"Saved selector: {out_path}")


if __name__ == "__main__":
    main()
