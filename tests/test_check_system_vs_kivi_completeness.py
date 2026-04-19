import csv
import json
from pathlib import Path

from scripts.check_system_vs_kivi_completeness import evaluate_completeness


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _make_system_dir(
    root: Path,
    *,
    model_key: str,
    system_id: str,
    quality_tasks: list[str],
    kv_cache_mem_mb: float,
    failed_task: str | None = None,
    omit_aux: set[str] | None = None,
) -> None:
    omit_aux = omit_aux or set()
    system_dir = root / model_key / system_id
    system_dir.mkdir(parents=True, exist_ok=True)
    (system_dir / "manifest.json").write_text(
        json.dumps(
            {
                "model_key": model_key,
                "model_id": "dummy/model",
                "system_id": system_id,
            }
        ),
        encoding="utf-8",
    )
    quality_rows = []
    for task in quality_tasks:
        quality_rows.append(
            {
                "task_name": task,
                "official_metric_name": "failed" if task == failed_task else "f1",
                "official_metric_value": 0.0 if task == failed_task else 1.0,
            }
        )
    _write_csv(
        system_dir / f"longbench_task_summary_{system_id}.csv",
        ["task_name", "official_metric_name", "official_metric_value"],
        quality_rows,
    )
    _write_csv(
        system_dir / f"profile_memory_{system_id}.csv",
        ["kv_cache_mem_mb"],
        [{"kv_cache_mem_mb": kv_cache_mem_mb}],
    )
    if "latency" not in omit_aux:
        _write_csv(
            system_dir / f"profile_latency_{system_id}.csv",
            ["ttft_ms", "tpot_ms"],
            [{"ttft_ms": 10.0, "tpot_ms": 5.0}],
        )
    if "ppl" not in omit_aux:
        _write_csv(
            system_dir / f"profile_ppl_{system_id}.csv",
            ["perplexity"],
            [{"perplexity": 12.0}],
        )
    if "needle" not in omit_aux:
        _write_csv(
            system_dir / f"profile_needle_{system_id}.csv",
            ["needle_pass_rate"],
            [{"needle_pass_rate": 0.9}],
        )
    if "ruler" not in omit_aux:
        _write_csv(
            system_dir / f"profile_ruler_{system_id}.csv",
            ["ruler_pass_rate"],
            [{"ruler_pass_rate": 0.8}],
        )


def test_evaluate_completeness_passes_for_full_smoke_matrix(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    systems = ["kivi_style", "rolealign_static", "rolealign_allocator_auto_eqmem"]
    for system_id, kv_mem in zip(systems, [100.0, 101.0, 102.5], strict=True):
        _make_system_dir(
            raw_dir,
            model_key="8b",
            system_id=system_id,
            quality_tasks=["narrativeqa", "dureader"],
            kv_cache_mem_mb=kv_mem,
        )

    report = evaluate_completeness(
        raw_dir,
        expected_models=["8b"],
        expected_systems=systems,
        expected_tasks=["narrativeqa", "dureader"],
        compared_systems=["rolealign_allocator_auto_eqmem"],
        tolerance_pct=3.0,
    )
    assert report["ok"] is True
    # Pareto mode: the compared system always emits an info_budget_drift row
    # (even when drift is small). Hard issues must be empty.
    hard = [i for i in report["issues"] if i.get("issue") != "info_budget_drift"]
    assert hard == []


def test_evaluate_completeness_flags_missing_aux_and_failed_rows(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    _make_system_dir(
        raw_dir,
        model_key="8b",
        system_id="kivi_style",
        quality_tasks=["narrativeqa", "dureader"],
        kv_cache_mem_mb=100.0,
    )
    _make_system_dir(
        raw_dir,
        model_key="8b",
        system_id="rolealign_allocator_auto_eqmem",
        quality_tasks=["narrativeqa", "dureader"],
        kv_cache_mem_mb=101.0,
        failed_task="dureader",
        omit_aux={"ppl"},
    )

    report = evaluate_completeness(
        raw_dir,
        expected_models=["8b"],
        expected_systems=["kivi_style", "rolealign_allocator_auto_eqmem"],
        expected_tasks=["narrativeqa", "dureader"],
        compared_systems=["rolealign_allocator_auto_eqmem"],
        tolerance_pct=3.0,
    )
    assert report["ok"] is False
    issues = report["issues"]
    assert any(issue["issue"] == "failed_row_contamination" for issue in issues)
    assert any(issue["issue"] == "missing_aux_metric" for issue in issues)


def test_evaluate_completeness_strict_flags_budget_out_of_band(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    _make_system_dir(
        raw_dir,
        model_key="3b",
        system_id="kivi_style",
        quality_tasks=["narrativeqa", "dureader"],
        kv_cache_mem_mb=100.0,
    )
    _make_system_dir(
        raw_dir,
        model_key="3b",
        system_id="rolealign_allocator_auto_eqmem",
        quality_tasks=["narrativeqa", "dureader"],
        kv_cache_mem_mb=106.0,
    )

    report = evaluate_completeness(
        raw_dir,
        expected_models=["3b"],
        expected_systems=["kivi_style", "rolealign_allocator_auto_eqmem"],
        expected_tasks=["narrativeqa", "dureader"],
        compared_systems=["rolealign_allocator_auto_eqmem"],
        tolerance_pct=3.0,
        gate_mode="strict",
    )
    assert report["ok"] is False
    assert any(issue["issue"] == "out_of_band" for issue in report["issues"])
    assert report["gate_mode"] == "strict"


def test_evaluate_completeness_pareto_reports_drift_without_failing(tmp_path: Path):
    """Default pareto mode: big budget drift is info, gate still passes."""
    raw_dir = tmp_path / "raw"
    _make_system_dir(
        raw_dir,
        model_key="1p5b",
        system_id="kivi_style",
        quality_tasks=["narrativeqa", "dureader"],
        kv_cache_mem_mb=8.42,
    )
    _make_system_dir(
        raw_dir,
        model_key="1p5b",
        system_id="rolealign_allocator_auto_eqmem",
        quality_tasks=["narrativeqa", "dureader"],
        kv_cache_mem_mb=12.64,
    )

    report = evaluate_completeness(
        raw_dir,
        expected_models=["1p5b"],
        expected_systems=["kivi_style", "rolealign_allocator_auto_eqmem"],
        expected_tasks=["narrativeqa", "dureader"],
        compared_systems=["rolealign_allocator_auto_eqmem"],
        tolerance_pct=3.0,
    )
    # Default mode must be pareto now
    assert report["gate_mode"] == "pareto"
    # Gate passes despite ~+50% drift, because info-only
    assert report["ok"] is True
    drift = [i for i in report["issues"] if i["issue"] == "info_budget_drift"]
    assert len(drift) == 1
    assert drift[0]["budget_ratio"] == 12.64 / 8.42
