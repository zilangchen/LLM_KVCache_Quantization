#!/usr/bin/env python3
"""Run the formal allocator-vs-KIVI compare package."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.system_vs_kivi_common import (
    PhasePlan,
    SYSTEM_AUTO,
    SYSTEM_FIXED,
    SYSTEM_KIVI,
    SYSTEM_STATIC,
    build_phase_plan,
    find_missing_assets,
    get_model_specs,
)


@dataclass(frozen=True)
class SystemRunConfig:
    model_key: str
    model_id: str
    system_id: str
    kv_mode: str
    quant_bits: int
    decode_attn_impl: str
    calib_file: str | None = None
    policy_json: str | None = None


@dataclass(frozen=True)
class PlannedJob:
    job_type: str
    model_key: str
    system_id: str
    run_name: str
    out_dir: Path
    command: tuple[str, ...]
    task_name: str | None = None


DEFAULT_LONGBENCH_SOURCE = os.environ.get("SYSTEM_VS_KIVI_LONGBENCH_SOURCE", "jsonl")
DEFAULT_LONGBENCH_DATASET_PATH = os.environ.get(
    "SYSTEM_VS_KIVI_LONGBENCH_DATASET_PATH",
    "",
)


def _split_csv(values: str | None) -> list[str]:
    if not values:
        return []
    return [item.strip() for item in str(values).split(",") if item.strip()]


def resolve_system_run_config(
    model_key: str,
    system_id: str,
    *,
    repo_root: Path | None = None,
) -> SystemRunConfig:
    root = PROJECT_ROOT if repo_root is None else Path(repo_root)
    specs = get_model_specs(repo_root=root)
    spec = specs[model_key]
    if system_id == SYSTEM_KIVI:
        return SystemRunConfig(
            model_key=model_key,
            model_id=spec.model_id,
            system_id=system_id,
            kv_mode="kivi_style",
            quant_bits=4,
            decode_attn_impl="torch_ref",
        )
    if system_id == SYSTEM_STATIC:
        return SystemRunConfig(
            model_key=model_key,
            model_id=spec.model_id,
            system_id=system_id,
            kv_mode="int4_ours_asym",
            quant_bits=4,
            decode_attn_impl="torch_ref",
            calib_file=str(root / spec.rolealign_calib),
        )
    if system_id == SYSTEM_FIXED:
        return SystemRunConfig(
            model_key=model_key,
            model_id=spec.model_id,
            system_id=system_id,
            kv_mode="int4_ours_asym_alloc",
            quant_bits=4,
            decode_attn_impl="torch_ref",
            calib_file=str(root / spec.rolealign_calib),
            policy_json=str(root / spec.allocator_fixed_policy),
        )
    if system_id == SYSTEM_AUTO:
        return SystemRunConfig(
            model_key=model_key,
            model_id=spec.model_id,
            system_id=system_id,
            kv_mode="int4_ours_asym_alloc",
            quant_bits=4,
            decode_attn_impl="torch_ref",
            calib_file=str(root / spec.rolealign_calib),
            policy_json=str(root / spec.allocator_auto_policy),
        )
    raise ValueError(f"Unsupported system_id: {system_id!r}")


def _common_runtime_args(cfg: SystemRunConfig) -> list[str]:
    args = [
        "--model_id",
        cfg.model_id,
        "--kv_mode",
        cfg.kv_mode,
        "--quant_bits",
        str(cfg.quant_bits),
        "--decode_attn_impl",
        cfg.decode_attn_impl,
    ]
    if cfg.calib_file is not None:
        args.extend(["--calib_file", cfg.calib_file])
    if cfg.policy_json is not None:
        args.extend(["--policy_json", cfg.policy_json])
    return args


def _runtime_family(cfg: SystemRunConfig) -> str:
    if cfg.kv_mode in {"kivi_style", "int4_kivi_aligned", "int4_ours_asym", "int4_ours_asym_ba", "int4_ours_asym_alloc"}:
        return "kivi_asym_family"
    if cfg.kv_mode == "int4_mixed_kv":
        return "mixed_kv_family"
    return cfg.kv_mode


def validate_same_format_runtime(configs: list[SystemRunConfig]) -> list[dict[str, object]]:
    if not configs:
        return []
    baseline_family = _runtime_family(configs[0])
    issues: list[dict[str, object]] = []
    for cfg in configs[1:]:
        family = _runtime_family(cfg)
        if family != baseline_family:
            issues.append(
                {
                    "model_key": cfg.model_key,
                    "system_id": cfg.system_id,
                    "issue": "format_mismatch",
                    "expected_family": baseline_family,
                    "actual_family": family,
                    "kv_mode": cfg.kv_mode,
                }
            )
    return issues


def build_jobs(
    plan: PhasePlan,
    *,
    repo_root: Path | None = None,
    out_root: Path | None = None,
    longbench_source: str = DEFAULT_LONGBENCH_SOURCE,
    longbench_dataset_path: str = DEFAULT_LONGBENCH_DATASET_PATH,
    longbench_max_samples: int = 50,
    latency_seq_len: int = 1024,
    latency_gen_len: int = 128,
    ppl_max_length: int = 1024,
    ppl_target_tokens: int = 4096,
    needle_context_len: int = 4096,
    needle_depths: int = 5,
    needle_max_new_tokens: int = 32,
    ruler_seq_len: int = 4096,
    ruler_gen_len: int = 64,
    ruler_num_cases: int = 64,
    seed: int = 1234,
) -> list[PlannedJob]:
    root = PROJECT_ROOT if repo_root is None else Path(repo_root)
    results_root = root / "results" / "system_vs_kivi" if out_root is None else Path(out_root)
    jobs: list[PlannedJob] = []

    for model_key in plan.models:
        for system_id in plan.systems:
            cfg = resolve_system_run_config(model_key, system_id, repo_root=root)
            system_out_dir = results_root / "raw" / plan.phase / model_key / system_id

            for task_name in plan.tasks:
                run_name = f"systemvkivi_{plan.phase}_{model_key}_{system_id}_{task_name}_quality"
                command = [
                    sys.executable,
                    str(root / "scripts" / "eval_longbench.py"),
                    *_common_runtime_args(cfg),
                    "--longbench_source",
                    longbench_source,
                    "--longbench_tasks",
                    task_name,
                    "--longbench_max_samples",
                    str(longbench_max_samples),
                    "--seed",
                    str(seed),
                    "--out_dir",
                    str(system_out_dir),
                    "--run_name",
                    run_name,
                ]
                if longbench_dataset_path:
                    command.extend(["--longbench_dataset_path", longbench_dataset_path])
                jobs.append(
                    PlannedJob(
                        job_type="quality",
                        model_key=model_key,
                        system_id=system_id,
                        task_name=task_name,
                        run_name=run_name,
                        out_dir=system_out_dir,
                        command=tuple(command),
                    )
                )

            aux_specs = [
                (
                    "latency",
                    "profile_latency.py",
                    [
                        "--seq_len",
                        str(latency_seq_len),
                        "--gen_len",
                        str(latency_gen_len),
                        "--runs",
                        "1",
                        "--warmup",
                        "1",
                    ],
                ),
                (
                    "memory",
                    "profile_memory.py",
                    [
                        "--seq_len",
                        str(latency_seq_len),
                        "--gen_len",
                        str(latency_gen_len),
                        "--runs",
                        "1",
                        "--warmup",
                        "1",
                    ],
                ),
                (
                    "ppl",
                    "eval_ppl.py",
                    [
                        "--dataset",
                        "wikitext2",
                        "--max_length",
                        str(ppl_max_length),
                        "--target_tokens",
                        str(ppl_target_tokens),
                        "--seed",
                        str(seed),
                    ],
                ),
                (
                    "needle",
                    "eval_needle.py",
                    [
                        "--context_len",
                        str(needle_context_len),
                        "--num_depths",
                        str(needle_depths),
                        "--needle_max_new_tokens",
                        str(needle_max_new_tokens),
                        "--seed",
                        str(seed),
                    ],
                ),
                (
                    "ruler",
                    "eval_ruler.py",
                    [
                        "--seq_len",
                        str(ruler_seq_len),
                        "--gen_len",
                        str(ruler_gen_len),
                        "--ruler_context_len",
                        str(ruler_seq_len),
                        "--ruler_num_cases",
                        str(ruler_num_cases),
                        "--seed",
                        str(seed),
                    ],
                ),
            ]
            for job_type, script_name, extra_args in aux_specs:
                run_name = f"systemvkivi_{plan.phase}_{model_key}_{system_id}_{job_type}"
                command = [
                    sys.executable,
                    str(root / "scripts" / script_name),
                    *_common_runtime_args(cfg),
                    *extra_args,
                    "--out_dir",
                    str(system_out_dir),
                    "--run_name",
                    run_name,
                ]
                jobs.append(
                    PlannedJob(
                        job_type=job_type,
                        model_key=model_key,
                        system_id=system_id,
                        run_name=run_name,
                        out_dir=system_out_dir,
                        command=tuple(command),
                    )
                )
    return jobs


def _write_manifest(job: PlannedJob, cfg: SystemRunConfig, phase: str) -> None:
    job.out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = job.out_dir / "manifest.json"
    payload = {
        "phase": phase,
        "model_key": cfg.model_key,
        "model_id": cfg.model_id,
        "system_id": cfg.system_id,
        "kv_mode": cfg.kv_mode,
        "quant_bits": cfg.quant_bits,
        "decode_attn_impl": cfg.decode_attn_impl,
        "calib_file": cfg.calib_file,
        "policy_json": cfg.policy_json,
    }
    manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _override_plan(plan: PhasePlan, *, models: list[str], tasks: list[str]) -> PhasePlan:
    return PhasePlan(
        phase=plan.phase,
        models=models or plan.models,
        tasks=tasks or plan.tasks,
        systems=plan.systems,
    )


def _print_plan_summary(plan: PhasePlan, jobs: list[PlannedJob]) -> None:
    print(f"Phase: {plan.phase}")
    print(f"Models: {','.join(plan.models)}")
    print(f"Tasks: {','.join(plan.tasks)}")
    print(f"Systems: {','.join(plan.systems)}")
    print(f"Jobs: {len(jobs)}")
    counts: dict[str, int] = {}
    for job in jobs:
        counts[job.job_type] = counts.get(job.job_type, 0) + 1
    for job_type in sorted(counts):
        print(f"  {job_type}: {counts[job_type]}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Formal system-vs-KIVI runner", allow_abbrev=False)
    parser.add_argument("--phase", required=True, choices=["smoke", "main", "ablation"])
    parser.add_argument("--models", default="")
    parser.add_argument("--tasks", default="")
    parser.add_argument("--out_root", default=str(PROJECT_ROOT / "results" / "system_vs_kivi"))
    parser.add_argument("--dry_run", action="store_true", default=False)
    parser.add_argument("--longbench_source", default=DEFAULT_LONGBENCH_SOURCE)
    parser.add_argument("--longbench_dataset_path", default=DEFAULT_LONGBENCH_DATASET_PATH)
    parser.add_argument("--longbench_max_samples", type=int, default=50)
    parser.add_argument("--latency_seq_len", type=int, default=1024)
    parser.add_argument("--latency_gen_len", type=int, default=128)
    parser.add_argument("--ppl_max_length", type=int, default=1024)
    parser.add_argument("--ppl_target_tokens", type=int, default=4096)
    parser.add_argument("--needle_context_len", type=int, default=4096)
    parser.add_argument("--needle_depths", type=int, default=5)
    parser.add_argument("--needle_max_new_tokens", type=int, default=32)
    parser.add_argument("--ruler_seq_len", type=int, default=4096)
    parser.add_argument("--ruler_gen_len", type=int, default=64)
    parser.add_argument("--ruler_num_cases", type=int, default=64)
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args()

    plan = _override_plan(
        build_phase_plan(args.phase),
        models=_split_csv(args.models),
        tasks=_split_csv(args.tasks),
    )
    missing = find_missing_assets(plan.models, plan.systems, repo_root=PROJECT_ROOT)
    format_issues: list[dict[str, object]] = []
    for model_key in plan.models:
        configs = [
            resolve_system_run_config(model_key, system_id, repo_root=PROJECT_ROOT)
            for system_id in plan.systems
        ]
        format_issues.extend(validate_same_format_runtime(configs))
    if missing:
        print("Preflight failed: missing required assets", file=sys.stderr)
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        return 2
    if format_issues:
        print("Preflight failed: same-format runtime gate not satisfied", file=sys.stderr)
        for issue in format_issues:
            print(
                f"  model={issue['model_key']} system={issue['system_id']} "
                f"expected={issue['expected_family']} actual={issue['actual_family']} "
                f"kv_mode={issue['kv_mode']}",
                file=sys.stderr,
            )
        return 2

    jobs = build_jobs(
        plan,
        repo_root=PROJECT_ROOT,
        out_root=Path(args.out_root),
        longbench_source=args.longbench_source,
        longbench_dataset_path=args.longbench_dataset_path,
        longbench_max_samples=args.longbench_max_samples,
        latency_seq_len=args.latency_seq_len,
        latency_gen_len=args.latency_gen_len,
        ppl_max_length=args.ppl_max_length,
        ppl_target_tokens=args.ppl_target_tokens,
        needle_context_len=args.needle_context_len,
        needle_depths=args.needle_depths,
        needle_max_new_tokens=args.needle_max_new_tokens,
        ruler_seq_len=args.ruler_seq_len,
        ruler_gen_len=args.ruler_gen_len,
        ruler_num_cases=args.ruler_num_cases,
        seed=args.seed,
    )
    _print_plan_summary(plan, jobs)

    if args.dry_run:
        for job in jobs:
            print(" ".join(job.command))
        return 0

    written_manifests: set[tuple[str, str]] = set()
    for job in jobs:
        key = (job.model_key, job.system_id)
        if key not in written_manifests:
            cfg = resolve_system_run_config(job.model_key, job.system_id, repo_root=PROJECT_ROOT)
            _write_manifest(job, cfg, plan.phase)
            written_manifests.add(key)
        subprocess.run(job.command, cwd=PROJECT_ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
