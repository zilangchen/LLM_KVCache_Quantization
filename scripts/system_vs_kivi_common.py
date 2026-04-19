#!/usr/bin/env python3
"""Shared definitions for the formal system-vs-KIVI compare package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SYSTEM_KIVI = "kivi_style"
SYSTEM_STATIC = "rolealign_static"
SYSTEM_FIXED = "rolealign_allocator_fixed_eqmem"
SYSTEM_AUTO = "rolealign_allocator_auto_eqmem"


@dataclass(frozen=True)
class ModelSpec:
    key: str
    model_id: str
    rolealign_calib: str
    allocator_fixed_policy: str
    allocator_auto_policy: str


@dataclass(frozen=True)
class PhasePlan:
    phase: str
    models: list[str]
    tasks: list[str]
    systems: list[str]


_MODEL_SPECS: dict[str, dict[str, str]] = {
    "1p5b": {
        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "rolealign_calib": "artifacts/kv_calib_rolealign_1p5b.json",
        "allocator_fixed_policy": "artifacts/allocator/l2_kv_asymmetric/1p5b/bakv_k3.json",
        "allocator_auto_policy": "artifacts/allocator/l2_kv_asymmetric/1p5b/bakv_auto_cov80_max.json",
    },
    "3b": {
        "model_id": "Qwen/Qwen2.5-3B-Instruct",
        "rolealign_calib": "artifacts/kv_calib_rolealign_3b_v3.json",
        "allocator_fixed_policy": "artifacts/allocator/sweep_3b/bakv_k1.json",
        "allocator_auto_policy": "artifacts/allocator/sweep_3b/bakv_auto_cov80_max.json",
    },
    "8b": {
        "model_id": "meta-llama/Llama-3.1-8B-Instruct",
        "rolealign_calib": "artifacts/kv_calib_rolealign_8b_v3.json",
        "allocator_fixed_policy": "artifacts/allocator/sweep_8b/bakv_k11.json",
        "allocator_auto_policy": "artifacts/allocator/sweep_8b/bakv_auto_cov80_max.json",
    },
    "14b": {
        "model_id": "Qwen/Qwen2.5-14B-Instruct",
        "rolealign_calib": "artifacts/kv_calib_rolealign_14b_v3.json",
        "allocator_fixed_policy": "artifacts/allocator/sweep_14b/bakv_k7.json",
        "allocator_auto_policy": "artifacts/allocator/sweep_14b/bakv_auto_cov90_max.json",
    },
    "mistral7b": {
        "model_id": "mistralai/Mistral-7B-Instruct-v0.3",
        "rolealign_calib": "artifacts/kv_calib_rolealign_mistral7b_v3.json",
        "allocator_fixed_policy": "artifacts/allocator/sweep_mistral7b/bakv_k3.json",
        "allocator_auto_policy": "artifacts/allocator/sweep_mistral7b/bakv_auto_cov80_max.json",
    },
}


def get_model_specs(*, repo_root: Path | None = None) -> dict[str, ModelSpec]:
    _ = PROJECT_ROOT if repo_root is None else repo_root
    return {
        key: ModelSpec(key=key, **payload)
        for key, payload in _MODEL_SPECS.items()
    }


def build_phase_plan(phase: str) -> PhasePlan:
    phase = str(phase).strip().lower()
    if phase == "smoke":
        return PhasePlan(
            phase=phase,
            models=["1p5b", "8b"],
            tasks=["narrativeqa", "dureader"],
            systems=[SYSTEM_KIVI, SYSTEM_STATIC, SYSTEM_AUTO],
        )
    if phase == "main":
        return PhasePlan(
            phase=phase,
            models=["1p5b", "3b", "8b", "14b", "mistral7b"],
            tasks=["narrativeqa", "hotpotqa", "gov_report", "dureader", "lcc"],
            systems=[SYSTEM_KIVI, SYSTEM_STATIC, SYSTEM_AUTO],
        )
    if phase == "ablation":
        return PhasePlan(
            phase=phase,
            models=["3b", "8b", "mistral7b"],
            tasks=["narrativeqa", "hotpotqa", "gov_report", "dureader", "lcc"],
            systems=[SYSTEM_KIVI, SYSTEM_STATIC, SYSTEM_FIXED, SYSTEM_AUTO],
        )
    raise ValueError(f"Unsupported phase: {phase!r}")


def _resolve_asset_paths(spec: ModelSpec, system_id: str) -> list[str]:
    if system_id == SYSTEM_KIVI:
        return []
    if system_id == SYSTEM_STATIC:
        return [spec.rolealign_calib]
    if system_id == SYSTEM_FIXED:
        return [spec.rolealign_calib, spec.allocator_fixed_policy]
    if system_id == SYSTEM_AUTO:
        return [spec.rolealign_calib, spec.allocator_auto_policy]
    raise ValueError(f"Unsupported system_id: {system_id!r}")


def find_missing_assets(
    model_keys: Iterable[str],
    system_ids: Iterable[str],
    *,
    repo_root: Path | None = None,
    specs: dict[str, ModelSpec] | None = None,
) -> list[str]:
    root = PROJECT_ROOT if repo_root is None else Path(repo_root)
    model_specs = get_model_specs(repo_root=root) if specs is None else specs
    missing: list[str] = []
    for model_key in model_keys:
        spec = model_specs[model_key]
        for system_id in system_ids:
            for rel_path in _resolve_asset_paths(spec, system_id):
                full_path = root / rel_path
                if not full_path.exists():
                    missing.append(str(full_path))
    return missing


def validate_matched_budget_rows(
    rows: Iterable[dict[str, object]],
    *,
    baseline_system: str = SYSTEM_KIVI,
    compared_systems: Iterable[str] = (SYSTEM_AUTO, SYSTEM_FIXED),
    tolerance_pct: float = 3.0,
) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, float]] = {}
    for row in rows:
        model_key = str(row.get("model_key", "")).strip()
        system_id = str(row.get("system_id", "")).strip()
        if not model_key or not system_id:
            continue
        try:
            kv_cache_mem_mb = float(row["kv_cache_mem_mb"])
        except (KeyError, TypeError, ValueError):
            continue
        grouped.setdefault(model_key, {})[system_id] = kv_cache_mem_mb

    issues: list[dict[str, object]] = []
    for model_key, by_system in sorted(grouped.items()):
        baseline = by_system.get(baseline_system)
        if baseline is None:
            issues.append(
                {
                    "model_key": model_key,
                    "system_id": baseline_system,
                    "issue": "missing_baseline",
                }
            )
            continue
        for system_id in compared_systems:
            value = by_system.get(system_id)
            if value is None:
                issues.append(
                    {
                        "model_key": model_key,
                        "system_id": system_id,
                        "issue": "missing_system",
                    }
                )
                continue
            if baseline == 0:
                rel_pct = 0.0 if value == 0 else float("inf")
            else:
                rel_pct = abs(value - baseline) / baseline * 100.0
            if rel_pct > tolerance_pct:
                issues.append(
                    {
                        "model_key": model_key,
                        "system_id": system_id,
                        "issue": "out_of_band",
                        "baseline_kv_cache_mem_mb": baseline,
                        "system_kv_cache_mem_mb": value,
                        "relative_pct": rel_pct,
                    }
                )
    return issues
