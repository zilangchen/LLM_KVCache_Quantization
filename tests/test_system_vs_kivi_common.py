from pathlib import Path

import pytest

from scripts.system_vs_kivi_common import (
    build_phase_plan,
    find_missing_assets,
    get_model_specs,
    validate_matched_budget_rows,
)


def test_build_phase_plan_smoke_defaults():
    plan = build_phase_plan("smoke")
    assert plan.models == ["1p5b", "8b"]
    assert plan.tasks == ["narrativeqa", "dureader"]
    assert plan.systems == [
        "kivi_style",
        "rolealign_static",
        "rolealign_allocator_auto_eqmem",
    ]


def test_build_phase_plan_main_uses_official_matrix():
    plan = build_phase_plan("main")
    assert plan.models == ["1p5b", "3b", "8b", "14b", "mistral7b"]
    assert plan.tasks == ["narrativeqa", "hotpotqa", "gov_report", "dureader", "lcc"]
    assert plan.systems == [
        "kivi_style",
        "rolealign_static",
        "rolealign_allocator_auto_eqmem",
    ]


def test_build_phase_plan_ablation_includes_fixed_eqmem():
    plan = build_phase_plan("ablation")
    assert plan.models == ["3b", "8b", "mistral7b"]
    assert plan.tasks == ["narrativeqa", "hotpotqa", "gov_report", "dureader", "lcc"]
    assert plan.systems == [
        "kivi_style",
        "rolealign_static",
        "rolealign_allocator_fixed_eqmem",
        "rolealign_allocator_auto_eqmem",
    ]


def test_find_missing_assets_reports_missing_files(tmp_path: Path):
    specs = get_model_specs(repo_root=tmp_path)
    (tmp_path / "artifacts" / "allocator" / "l2_kv_asymmetric" / "1p5b").mkdir(parents=True)
    (tmp_path / "artifacts" / "kv_calib_rolealign_1p5b.json").write_text("{}", encoding="utf-8")
    (
        tmp_path
        / "artifacts"
        / "allocator"
        / "l2_kv_asymmetric"
        / "1p5b"
        / "bakv_auto_cov80_max.json"
    ).write_text("{}", encoding="utf-8")

    missing = find_missing_assets(
        ["1p5b"],
        ["rolealign_static", "rolealign_allocator_auto_eqmem", "rolealign_allocator_fixed_eqmem"],
        repo_root=tmp_path,
        specs=specs,
    )

    assert len(missing) == 1
    assert missing[0].endswith("artifacts/allocator/l2_kv_asymmetric/1p5b/bakv_k3.json")


def test_validate_matched_budget_rows_accepts_within_tolerance():
    issues = validate_matched_budget_rows(
        [
            {"model_key": "8b", "system_id": "kivi_style", "kv_cache_mem_mb": 100.0},
            {"model_key": "8b", "system_id": "rolealign_allocator_auto_eqmem", "kv_cache_mem_mb": 102.5},
            {"model_key": "8b", "system_id": "rolealign_allocator_fixed_eqmem", "kv_cache_mem_mb": 97.1},
        ],
        compared_systems=[
            "rolealign_allocator_auto_eqmem",
            "rolealign_allocator_fixed_eqmem",
        ],
        tolerance_pct=3.0,
    )
    assert issues == []


def test_validate_matched_budget_rows_flags_missing_and_out_of_band():
    issues = validate_matched_budget_rows(
        [
            {"model_key": "3b", "system_id": "kivi_style", "kv_cache_mem_mb": 100.0},
            {"model_key": "3b", "system_id": "rolealign_allocator_auto_eqmem", "kv_cache_mem_mb": 104.0},
        ],
        compared_systems=[
            "rolealign_allocator_auto_eqmem",
            "rolealign_allocator_fixed_eqmem",
        ],
        tolerance_pct=3.0,
    )
    assert len(issues) == 2
    assert any(issue["issue"] == "out_of_band" for issue in issues)
    assert any(issue["issue"] == "missing_system" for issue in issues)


def test_build_phase_plan_rejects_unknown_phase():
    with pytest.raises(ValueError, match="Unsupported phase"):
        build_phase_plan("unknown")
