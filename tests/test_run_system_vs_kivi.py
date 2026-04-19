import subprocess
import sys
from pathlib import Path

from scripts.run_system_vs_kivi import (
    build_jobs,
    resolve_system_run_config,
    validate_longbench_dataset_config,
    validate_same_format_runtime,
)
from scripts.system_vs_kivi_common import build_phase_plan


def test_resolve_system_run_config_maps_systems_to_expected_runtime(tmp_path: Path):
    static_cfg = resolve_system_run_config("1p5b", "rolealign_static", repo_root=tmp_path)
    assert static_cfg.kv_mode == "int4_ours_asym"
    assert static_cfg.calib_file.endswith("artifacts/kv_calib_rolealign_1p5b.json")
    assert static_cfg.policy_json is None

    auto_cfg = resolve_system_run_config(
        "8b", "rolealign_allocator_auto_eqmem", repo_root=tmp_path
    )
    assert auto_cfg.kv_mode == "int4_ours_asym_alloc"
    assert auto_cfg.policy_json.endswith("artifacts/allocator/sweep_8b/bakv_auto_cov80_max.json")
    assert auto_cfg.calib_file.endswith("artifacts/kv_calib_rolealign_8b_v3.json")

    kivi_cfg = resolve_system_run_config("14b", "kivi_style", repo_root=tmp_path)
    assert kivi_cfg.kv_mode == "kivi_style"
    assert kivi_cfg.quant_bits == 4
    assert kivi_cfg.calib_file is None
    assert kivi_cfg.policy_json is None


def test_build_jobs_smoke_includes_quality_and_all_aux_tasks(tmp_path: Path):
    jobs = build_jobs(
        build_phase_plan("smoke"),
        repo_root=tmp_path,
        out_root=tmp_path / "results" / "system_vs_kivi",
    )
    quality_jobs = [job for job in jobs if job.job_type == "quality"]
    aux_jobs = [job for job in jobs if job.job_type != "quality"]

    assert len(quality_jobs) == 12
    assert len(aux_jobs) == 30
    assert {job.job_type for job in aux_jobs} == {
        "latency",
        "memory",
        "ppl",
        "needle",
        "ruler",
    }


def test_build_jobs_ablation_includes_fixed_eqmem_system(tmp_path: Path):
    jobs = build_jobs(
        build_phase_plan("ablation"),
        repo_root=tmp_path,
        out_root=tmp_path / "results" / "system_vs_kivi",
    )
    systems = {job.system_id for job in jobs}
    assert "rolealign_allocator_fixed_eqmem" in systems


def test_validate_same_format_runtime_accepts_allocator_backend(tmp_path: Path):
    configs = [
        resolve_system_run_config("1p5b", "kivi_style", repo_root=tmp_path),
        resolve_system_run_config("1p5b", "rolealign_static", repo_root=tmp_path),
        resolve_system_run_config("1p5b", "rolealign_allocator_auto_eqmem", repo_root=tmp_path),
    ]
    issues = validate_same_format_runtime(configs)
    assert issues == []


def test_validate_longbench_dataset_config_rejects_missing_jsonl_path():
    issues = validate_longbench_dataset_config(
        longbench_source="jsonl",
        longbench_dataset_path="",
    )
    assert issues == ["--longbench_dataset_path is required for longbench_source=jsonl"]


def test_validate_longbench_dataset_config_accepts_existing_jsonl_dir(tmp_path: Path):
    dataset_dir = tmp_path / "longbench_jsonl"
    dataset_dir.mkdir()
    issues = validate_longbench_dataset_config(
        longbench_source="jsonl",
        longbench_dataset_path=str(dataset_dir),
    )
    assert issues == []


def test_cli_script_runs_without_import_error():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "run_system_vs_kivi.py"
    completed = subprocess.run(
        [sys.executable, str(script_path), "--phase", "smoke", "--dry_run"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    assert "Preflight failed" in completed.stderr
