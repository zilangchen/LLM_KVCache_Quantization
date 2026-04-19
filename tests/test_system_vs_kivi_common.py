from pathlib import Path

import pytest

from scripts.system_vs_kivi_common import (
    build_phase_plan,
    find_missing_assets,
    get_model_specs,
    validate_matched_budget_rows,
)


def test_get_model_specs_applies_env_override(monkeypatch):
    """SVK_MODEL_PATH_<KEY> env var replaces the default HF model_id for the
    keyed model while leaving other models untouched."""
    monkeypatch.setenv("SVK_MODEL_PATH_14B", "/tmp/fake_local_14b")
    monkeypatch.delenv("SVK_MODEL_PATH_1P5B", raising=False)

    specs = get_model_specs()

    assert specs["14b"].model_id == "/tmp/fake_local_14b"
    # Other entries keep their default HF id
    assert specs["1p5b"].model_id == "Qwen/Qwen2.5-1.5B-Instruct"
    assert specs["8b"].model_id == "meta-llama/Llama-3.1-8B-Instruct"


def test_get_model_specs_returns_hf_default_without_override(monkeypatch):
    monkeypatch.delenv("SVK_MODEL_PATH_14B", raising=False)
    specs = get_model_specs()
    assert specs["14b"].model_id == "Qwen/Qwen2.5-14B-Instruct"


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


def test_validate_matched_budget_rows_strict_accepts_within_tolerance():
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
        gate_mode="strict",
    )
    assert issues == []


def test_validate_matched_budget_rows_strict_flags_missing_and_out_of_band():
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
        gate_mode="strict",
    )
    assert len(issues) == 2
    assert any(issue["issue"] == "out_of_band" for issue in issues)
    assert any(issue["issue"] == "missing_system" for issue in issues)


def test_validate_matched_budget_rows_pareto_reports_drift_as_info():
    """Under pareto gate_mode, budget drift is info (not failure)."""
    issues = validate_matched_budget_rows(
        [
            {"model_key": "1p5b", "system_id": "kivi_style", "kv_cache_mem_mb": 8.42},
            {"model_key": "1p5b", "system_id": "rolealign_allocator_auto_eqmem", "kv_cache_mem_mb": 12.64},
        ],
        compared_systems=["rolealign_allocator_auto_eqmem"],
        tolerance_pct=3.0,
        gate_mode="pareto",
    )
    assert len(issues) == 1
    info = issues[0]
    assert info["issue"] == "info_budget_drift"
    assert info["budget_ratio"] == 12.64 / 8.42
    # Drift percent is still reported for transparency
    assert abs(info["relative_pct"] - 50.118) < 0.01


def test_validate_matched_budget_rows_pareto_still_flags_missing_baseline():
    """Even under pareto mode, a missing baseline row is a hard problem."""
    issues = validate_matched_budget_rows(
        [
            {"model_key": "3b", "system_id": "rolealign_allocator_auto_eqmem", "kv_cache_mem_mb": 50.0},
        ],
        compared_systems=["rolealign_allocator_auto_eqmem"],
        gate_mode="pareto",
    )
    assert any(issue["issue"] == "missing_baseline" for issue in issues)


def test_validate_matched_budget_rows_rejects_unknown_gate_mode():
    import pytest
    with pytest.raises(ValueError, match="gate_mode"):
        validate_matched_budget_rows([], gate_mode="bogus")


def test_build_phase_plan_rejects_unknown_phase():
    with pytest.raises(ValueError, match="Unsupported phase"):
        build_phase_plan("unknown")
