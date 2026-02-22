#!/usr/bin/env python3
"""
Run experiment matrix defined in configs/exp_matrix.yaml.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from scripts.config_utils import load_config


TASK_TO_SCRIPT = {
    "profile_latency": "scripts/profile_latency.py",
    "profile_memory": "scripts/profile_memory.py",
    "eval_ppl": "scripts/eval_ppl.py",
    "eval_needle": "scripts/eval_needle.py",
}

TASK_TO_CSV_PATTERNS = {
    "profile_latency": "profile_latency_*.csv",
    "profile_memory": "profile_memory_*.csv",
    "eval_ppl": "profile_ppl_*.csv",
    "eval_needle": "profile_needle_*.csv",
}


def _now_iso() -> str:
    return datetime.now().isoformat()


def _get_git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=project_root,
        ).stdout.strip()
        return out or "unknown"
    except Exception:
        return "unknown"


def _collect_env_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "platform": platform.platform(),
    }
    try:
        import torch  # type: ignore

        info["torch_version"] = getattr(torch, "__version__", "unknown")
        info["cuda_version"] = getattr(getattr(torch, "version", None), "cuda", None)
        info["cuda_available"] = bool(torch.cuda.is_available())
    except Exception:
        info["torch_version"] = "unavailable"
        info["cuda_version"] = None
        info["cuda_available"] = False

    try:
        import transformers  # type: ignore

        info["transformers_version"] = getattr(transformers, "__version__", "unknown")
    except Exception:
        info["transformers_version"] = "unavailable"

    payload = json.dumps(info, sort_keys=True, ensure_ascii=True)
    info["env_hash"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return info


def _read_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=True)
    tmp_path.replace(path)


def _existing_result_git_commits(run_dir: Path) -> List[str]:
    commits = set()
    patterns = [
        "profile_latency_*.csv",
        "profile_memory_*.csv",
        "profile_ppl_*.csv",
        "profile_needle_*.csv",
    ]
    for pattern in patterns:
        for path in run_dir.glob(pattern):
            try:
                with open(path, "r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        commit = str(row.get("git_commit", "")).strip()
                        if commit:
                            commits.add(commit)
            except Exception:
                continue
    return sorted(commits)


def _same_commit_prefix(a: str, b: str) -> bool:
    a = str(a).strip()
    b = str(b).strip()
    if not a or not b:
        return True
    if a == "unknown" or b == "unknown":
        return True
    return a[:8] == b[:8]


def _validate_append_commit(
    run_dir: Path,
    manifest_path: Path,
    current_git_commit: str,
    current_env_hash: str,
) -> tuple[bool, str]:
    manifest = _read_json(manifest_path)
    if manifest:
        prev_commit = str(manifest.get("git_commit", "")).strip()
        if prev_commit and not _same_commit_prefix(prev_commit, current_git_commit):
            return (
                False,
                "append blocked: existing run_manifest git_commit "
                f"({prev_commit}) != current git_commit ({current_git_commit[:8]}).",
            )
        prev_env_hash = str(manifest.get("env_hash", "")).strip()
        if prev_env_hash and current_env_hash and prev_env_hash != current_env_hash:
            return (
                False,
                "append blocked: existing run_manifest env_hash "
                f"({prev_env_hash}) != current env_hash ({current_env_hash}).",
            )

    for prev_commit in _existing_result_git_commits(run_dir):
        if not _same_commit_prefix(prev_commit, current_git_commit):
            return (
                False,
                "append blocked: existing CSV git_commit "
                f"({prev_commit}) != current git_commit ({current_git_commit[:8]}).",
            )
    return True, ""


def _is_nonempty_dir(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    try:
        next(path.iterdir())
        return True
    except StopIteration:
        return False
    except Exception:
        return True


def _task_has_csv(run_dir: Path, task: str) -> bool:
    pattern = TASK_TO_CSV_PATTERNS.get(task)
    if not pattern:
        return False
    return any(run_dir.glob(pattern))


def _read_text_best_effort(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _classify_failure(*, log_path: Path, returncode: int | None) -> str:
    if returncode is not None and int(returncode) == 73:
        return "oom"
    if returncode is not None and int(returncode) == 130:
        return "interrupt"
    content = _read_text_best_effort(log_path).lower()
    if "oom" in content or "out of memory" in content or "cuda out of memory" in content:
        return "oom"
    if "traceback (most recent call last):" in content:
        return "traceback"
    if returncode is not None and int(returncode) != 0:
        return "runtime_error"
    return "unknown"


def _init_manifest(
    manifest_path: Path,
    *,
    run_id: str,
    run_name: str,
    run_tag: str,
    kv_mode: str,
    seed: int,
    replica_id: int,
    model_id: str,
    model_revision: str | None,
    args: argparse.Namespace,
    append_mode: bool,
    git_commit_full: str,
    env_info: Dict[str, Any],
) -> Dict[str, Any]:
    now = _now_iso()
    manifest = _read_json(manifest_path) or {}
    if not manifest:
        manifest = {
            "manifest_version": 1,
            "created_at": now,
            "tasks": {},
            "append_history": [],
        }

    manifest["updated_at"] = now
    manifest["run_id"] = run_id
    manifest["run_name"] = run_name
    manifest["run_tag"] = run_tag
    manifest["kv_mode"] = kv_mode
    manifest["seed"] = int(seed)
    manifest["replica_id"] = int(replica_id)
    manifest["model_id"] = model_id
    manifest["model_revision"] = model_revision
    manifest["git_commit"] = git_commit_full[:8] if git_commit_full else "unknown"
    manifest["git_commit_full"] = git_commit_full
    manifest["env_hash"] = env_info.get("env_hash", "unknown")
    manifest["env_info"] = env_info
    manifest["append_mode"] = bool(append_mode)
    manifest["argv"] = list(sys.argv)
    if not isinstance(manifest.get("tasks"), dict):
        manifest["tasks"] = {}
    if not isinstance(manifest.get("append_history"), list):
        manifest["append_history"] = []
    if append_mode:
        manifest["append_history"].append(
            {
                "timestamp": now,
                "tasks": args.tasks,
                "config": args.config,
            }
        )
    _write_json(manifest_path, manifest)
    return manifest


def _mark_task_status(
    manifest_path: Path,
    manifest: Dict[str, Any],
    *,
    task: str,
    status: str,
    cmd: List[str],
    log_path: Path,
    returncode: int | None = None,
    error: str | None = None,
    failure_type: str | None = None,
    attempt_idx: int | None = None,
) -> None:
    now = _now_iso()
    tasks = manifest.setdefault("tasks", {})
    entry = tasks.get(task, {})
    history = entry.get("history")
    if not isinstance(history, list):
        history = []
    if status == "running":
        entry["attempts"] = int(entry.get("attempts", 0)) + 1
        entry["started_at"] = now
        if attempt_idx is None:
            attempt_idx = int(entry["attempts"])
    entry["status"] = status
    entry["updated_at"] = now
    entry["log_path"] = str(log_path)
    entry["cmd"] = cmd
    if attempt_idx is not None:
        entry["last_attempt"] = int(attempt_idx)
    if returncode is not None:
        entry["returncode"] = int(returncode)
    if status in {"success", "skipped"}:
        # Keep terminal success state canonical when resuming/skip-completed paths.
        entry.pop("failure_type", None)
        entry.pop("error", None)
    elif failure_type:
        entry["failure_type"] = str(failure_type)
    if error and status not in {"success", "skipped"}:
        entry["error"] = str(error)
    if status in {"success", "failed", "skipped"}:
        hist_row: Dict[str, Any] = {
            "timestamp": now,
            "status": status,
            "attempt": int(attempt_idx) if attempt_idx is not None else int(entry.get("attempts", 0)),
            "returncode": int(returncode) if returncode is not None else None,
            "failure_type": str(failure_type) if failure_type else "",
            "error": str(error) if error else "",
        }
        history.append(hist_row)
        # Keep manifest compact; preserve the latest 20 terminal events.
        entry["history"] = history[-20:]
    tasks[task] = entry
    manifest["tasks"] = tasks
    manifest["updated_at"] = now
    _write_json(manifest_path, manifest)


def _task_is_completed_successfully(
    *,
    manifest: Dict[str, Any],
    run_dir: Path,
    task: str,
) -> bool:
    task_info = manifest.get("tasks", {}).get(task, {})
    if not isinstance(task_info, dict):
        return False
    status = str(task_info.get("status", "")).strip().lower()
    if status not in {"success", "skipped"}:
        history = task_info.get("history")
        has_success_history = False
        if isinstance(history, list):
            for item in history:
                if isinstance(item, dict) and str(item.get("status", "")).strip().lower() == "success":
                    has_success_history = True
                    break
        if not has_success_history:
            return False
    return _task_has_csv(run_dir, task)


def _write_execution_summary(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, payload)


def resolve_quant_params(run_entry: Dict, quant_defaults: Dict) -> Dict[str, float]:
    clip_percentile_k = run_entry.get(
        "clip_percentile_k",
        run_entry.get("clip_percentile", quant_defaults.get("clip_percentile_k", 99.9)),
    )
    clip_percentile_v = run_entry.get(
        "clip_percentile_v",
        run_entry.get("clip_percentile", quant_defaults.get("clip_percentile_v", 99.9)),
    )
    group_size_k = run_entry.get(
        "group_size_k",
        run_entry.get("group_size", quant_defaults.get("group_size_k", 128)),
    )
    group_size_v = run_entry.get(
        "group_size_v",
        run_entry.get("group_size", quant_defaults.get("group_size_v", 128)),
    )
    return {
        "clip_percentile": clip_percentile_k,
        "group_size": group_size_k,
        "clip_percentile_k": clip_percentile_k,
        "clip_percentile_v": clip_percentile_v,
        "group_size_k": group_size_k,
        "group_size_v": group_size_v,
    }


def resolve_calib_params(run_entry: Dict, quant_defaults: Dict) -> Dict[str, object]:
    calib_file = run_entry.get("calib_file", quant_defaults.get("calib_file"))
    use_attn_temperature = run_entry.get(
        "use_attn_temperature", quant_defaults.get("use_attn_temperature", False)
    )
    use_static_scales = run_entry.get(
        "use_static_scales", quant_defaults.get("use_static_scales", True)
    )
    adaptive_static_scales = run_entry.get(
        "adaptive_static_scales", quant_defaults.get("adaptive_static_scales", False)
    )
    adaptive_static_margin = run_entry.get(
        "adaptive_static_margin", quant_defaults.get("adaptive_static_margin", 1.0)
    )
    adaptive_static_k = run_entry.get(
        "adaptive_static_k", quant_defaults.get("adaptive_static_k", True)
    )
    adaptive_static_v = run_entry.get(
        "adaptive_static_v", quant_defaults.get("adaptive_static_v", True)
    )
    calib_strategy = run_entry.get("calib_strategy", quant_defaults.get("calib_strategy"))
    return {
        "calib_file": calib_file,
        "use_attn_temperature": use_attn_temperature,
        "use_static_scales": use_static_scales,
        "adaptive_static_scales": adaptive_static_scales,
        "adaptive_static_margin": adaptive_static_margin,
        "adaptive_static_k": adaptive_static_k,
        "adaptive_static_v": adaptive_static_v,
        "calib_strategy": calib_strategy,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run experiment matrix")
    parser.add_argument("--config", type=str, default="configs/exp_matrix.yaml")
    parser.add_argument(
        "--tasks",
        type=str,
        default="profile_latency,profile_memory,eval_ppl,eval_needle",
        help="Comma-separated task list",
    )
    parser.add_argument(
        "--run_names",
        type=str,
        default=None,
        help="Comma-separated run_name filter",
    )
    parser.add_argument(
        "--run_tag",
        type=str,
        default=None,
        help=(
            "Override the timestamp suffix used to build per-run directories: "
            "run_id = <run_name>_<run_tag>. Use the same --run_tag across multiple "
            "invocations to append different tasks into the same run_id directory."
        ),
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help=(
            "Append mode for an existing run_id directory: keep the existing "
            "config_snapshot.yaml (if present) and append to task logs instead of overwriting."
        ),
    )
    parser.add_argument(
        "--failure_policy",
        type=str,
        choices=["abort", "continue_on_oom", "continue_all"],
        default="abort",
        help=(
            "Failure handling policy. "
            "'abort': stop immediately on any failed task; "
            "'continue_on_oom': continue only when failure is OOM; "
            "'continue_all': continue on any failed task."
        ),
    )
    parser.add_argument(
        "--max_retries",
        type=int,
        default=0,
        help="Maximum retry count per failed task (total attempts = max_retries + 1).",
    )
    parser.add_argument(
        "--retry_backoff_sec",
        type=float,
        default=0.0,
        help="Sleep interval between retry attempts in seconds.",
    )
    parser.add_argument(
        "--skip_completed_success",
        action="store_true",
        default=False,
        help=(
            "When used with --append, skip tasks already marked success in run_manifest "
            "and with matching CSV artifacts."
        ),
    )
    parser.add_argument(
        "--summary_json",
        type=str,
        default="",
        help="Optional path to write execution summary JSON.",
    )
    parser.add_argument("--out_dir", type=str, default="results/runs")
    parser.add_argument("--logs_dir", type=str, default="logs/run_experiments")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument(
        "--seeds",
        type=str,
        default=None,
        help=(
            "Comma-separated seed list. When provided, each selected run_name is executed once per seed "
            "and the seed is appended to the run_id as '<run_name>_s<seed>_<run_tag>'. "
            "When omitted, uses runtime.seed from the config."
        ),
    )
    parser.add_argument("--ppl_max_length", type=int, default=1024)
    parser.add_argument("--ppl_stride", type=int, default=512)
    parser.add_argument(
        "--ppl_chunk_size",
        type=int,
        default=128,
        help=(
            "Pass through to eval_ppl.py --chunk_size for ppl_mode=kv_cache. Larger chunks reduce "
            "Python overhead and increase GPU utilization."
        ),
    )
    parser.add_argument(
        "--ppl_mode",
        type=str,
        default="kv_cache",
        choices=["hf", "kv_cache"],
        help="Pass through to eval_ppl.py --ppl_mode.",
    )
    parser.add_argument(
        "--ppl_max_samples",
        type=int,
        default=32,
        help=(
            "Pass through to eval_ppl.py --max_samples to limit total evaluated tokens. "
            "NOTE: kv_cache PPL can still be slow on large settings; reduce this if you hit time limits."
        ),
    )
    parser.add_argument("--needle_context_len", type=int, default=None)
    parser.add_argument(
        "--needle_num_depths",
        type=int,
        default=None,
        help="Pass through to eval_needle.py --num_depths to reduce evaluation cost.",
    )
    parser.add_argument(
        "--needle_max_new_tokens",
        type=int,
        default=64,
        help="Pass through to eval_needle.py --needle_max_new_tokens.",
    )
    parser.add_argument(
        "--needle_depth_batch",
        type=int,
        default=1,
        help="Pass through to eval_needle.py --depth_batch to batch multiple depths per forward.",
    )
    parser.add_argument(
        "--needle_report_exact_match",
        action="store_true",
        default=False,
        help="Pass through to eval_needle.py --report_exact_match (appendix metric only).",
    )
    parser.add_argument(
        "--latency_runs",
        type=int,
        default=None,
        help="Pass through to profile_latency.py --runs (useful for long-context runs).",
    )
    parser.add_argument(
        "--latency_warmup",
        type=int,
        default=None,
        help="Pass through to profile_latency.py --warmup (useful for long-context runs).",
    )
    args = parser.parse_args()
    if int(args.max_retries) < 0:
        print("Error: --max_retries must be >= 0.")
        return 2
    if float(args.retry_backoff_sec) < 0:
        print("Error: --retry_backoff_sec must be >= 0.")
        return 2

    config_path = Path(args.config).resolve()
    deprecated_config = (project_root / "exp_matrix.yaml").resolve()
    if config_path == deprecated_config:
        print(
            "Error: root exp_matrix.yaml is deprecated. "
            "Use configs/exp_matrix.yaml instead."
        )
        return 2

    config = load_config(args.config)
    if args.dry_run:
        build_config_snapshot = None
        write_config_snapshot = None
    else:
        # Keep --dry_run usable on machines without torch installed.
        try:
            from src.utils.repro import build_config_snapshot, write_config_snapshot
        except ModuleNotFoundError as exc:
            if getattr(exc, "name", None) == "torch":
                print("Error: torch is not installed in this environment.")
                print("Run this on the GPU server (see AGENTS.md and .agents/skills/remote-server/SKILL.md),")
                print("or rerun with --dry_run to preview commands.")
                return 2
            raise

    project = config.get("project", {})
    runtime = config.get("runtime", {})
    quant_defaults = runtime.get("quant_defaults", {})
    kernel_defaults = runtime.get("kernel_defaults", {})

    model_id = project.get("model_id", "Qwen/Qwen2.5-1.5B-Instruct")
    model_revision = project.get("model_revision")
    git_commit_full = _get_git_commit()
    env_info = _collect_env_info()
    default_seed = runtime.get("seed", 1234)
    seed_list = [int(default_seed)]
    if args.seeds:
        raw = [x.strip() for x in args.seeds.split(",") if x.strip()]
        if not raw:
            print("Error: --seeds must contain at least one integer.")
            return 2
        try:
            seed_list = [int(x) for x in raw]
        except ValueError:
            print(f"Error: invalid --seeds value: {args.seeds!r}. Expected comma-separated integers.")
            return 2

    max_position_embeddings = None
    if not args.dry_run:
        try:
            from transformers import AutoConfig

            model_cfg = AutoConfig.from_pretrained(
                model_id,
                revision=model_revision,
                trust_remote_code=True,
            )
            max_position_embeddings = getattr(model_cfg, "max_position_embeddings", None)
        except ModuleNotFoundError as exc:
            if getattr(exc, "name", None) in {"transformers", "torch"}:
                print(
                    "Error: transformers/torch is not installed in this environment. "
                    "Run on the GPU server or use --dry_run."
                )
                return 2
            raise
        except Exception as exc:
            print(f"Error: failed to load model config for length gate check: {exc}")
            return 2

    task_list = [t.strip() for t in args.tasks.split(",") if t.strip()]
    if args.run_names:
        run_name_filter = {
            name.strip() for name in args.run_names.split(",") if name.strip()
        }
    else:
        run_name_filter = None

    matrix = config.get("matrix", [])
    run_tag = args.run_tag.strip() if args.run_tag else datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.run_tag:
        if not run_tag:
            print("Error: --run_tag must be a non-empty string.")
            return 2
        if not re.fullmatch(r"[A-Za-z0-9._-]+", run_tag):
            print(
                "Error: --run_tag contains unsupported characters. "
                "Allowed: letters, digits, '.', '_', '-'."
            )
            return 2

    summary_path: Path | None = None
    if args.summary_json:
        summary_path = Path(args.summary_json)
        if not summary_path.is_absolute():
            summary_path = project_root / summary_path

    execution_rows: List[Dict[str, Any]] = []

    def _flush_summary(exit_code: int) -> None:
        if summary_path is None:
            return
        success_count = sum(1 for row in execution_rows if row.get("status") == "success")
        failed_count = sum(1 for row in execution_rows if row.get("status") == "failed")
        skipped_count = sum(1 for row in execution_rows if row.get("status") == "skipped")
        payload = {
            "generated_at": _now_iso(),
            "exit_code": int(exit_code),
            "failure_policy": str(args.failure_policy),
            "max_retries": int(args.max_retries),
            "retry_backoff_sec": float(args.retry_backoff_sec),
            "append": bool(args.append),
            "skip_completed_success": bool(args.skip_completed_success),
            "run_tag": run_tag,
            "config": args.config,
            "tasks": task_list,
            "totals": {
                "executed": int(len(execution_rows)),
                "success": int(success_count),
                "failed": int(failed_count),
                "skipped": int(skipped_count),
            },
            "rows": execution_rows,
        }
        _write_execution_summary(summary_path, payload)

    for run_entry in matrix:
        run_name = run_entry.get("run_name")
        if not run_name:
            continue
        if run_name_filter and run_name not in run_name_filter:
            continue

        kv_mode = run_entry.get("kv_mode", "fp16")
        if kv_mode not in [
            "fp16",
            "int8_baseline",
            "int8_fused",
            "int8_ours",
            "int4_baseline",
            "int4_fused",
            "int4_ours",
            "int4_ours_mixed",
        ]:
            print(f"Skip unsupported kv_mode={kv_mode} for {run_name}")
            continue

        seq_len = run_entry.get("seq_len", 1024)
        gen_len = run_entry.get("gen_len", 128)
        batch = int(run_entry.get("batch", 1) or 1)
        if max_position_embeddings is not None and seq_len + gen_len > int(max_position_embeddings):
            suggested_seq_len = max(int(max_position_embeddings) - int(gen_len), 1)
            print(
                "Error: run exceeds model max_position_embeddings. "
                f"run_name={run_name} seq_len={seq_len} gen_len={gen_len} "
                f"max_position_embeddings={max_position_embeddings}."
            )
            print(
                "Suggested fix: set "
                f"seq_len <= {suggested_seq_len} (or reduce gen_len)."
            )
            return 2

        quant_params = resolve_quant_params(run_entry, quant_defaults)
        calib_params = resolve_calib_params(run_entry, quant_defaults)
        decode_attn_impl = run_entry.get(
            "decode_attn_impl", kernel_defaults.get("decode_attn_impl")
        )

        calib_file_path = None
        calib_file = calib_params.get("calib_file")
        if calib_file:
            calib_file_path = Path(calib_file)
            if not calib_file_path.is_absolute():
                calib_file_path = project_root / calib_file_path

        if not args.dry_run and kv_mode in ["int8_ours", "int4_ours", "int4_ours_mixed"]:
            needs_calib = (
                calib_params.get("calib_strategy") == "kl_attn"
                or calib_params.get("use_attn_temperature") is True
            )
            if needs_calib and (calib_file_path is None or not calib_file_path.exists()):
                print(
                    f"Error: kv_mode={kv_mode} requires calibration file but it was not found: {calib_file_path}."
                )
                print(
                    "Run scripts/calibrate_behavior.py to generate it, or switch calib_strategy to 'percentile' and "
                    "disable use_attn_temperature."
                )
                return 2

        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = project_root / out_dir

        logs_dir = Path(args.logs_dir)
        if not logs_dir.is_absolute():
            logs_dir = project_root / logs_dir

        multi_seed = args.seeds is not None and len(seed_list) > 0
        for replica_id, seed in enumerate(seed_list):
            run_id = f"{run_name}_s{seed}_{run_tag}" if multi_seed else f"{run_name}_{run_tag}"
            run_dir = out_dir / run_id
            manifest_path = run_dir / "run_manifest.json"
            if not args.dry_run:
                if not args.append and _is_nonempty_dir(run_dir):
                    print(
                        "Error: target run_dir already exists and is non-empty. "
                        f"Refusing to overwrite: {run_dir}"
                    )
                    print("Use a new --run_tag for a clean run, or pass --append for controlled resume.")
                    return 2
                run_dir.mkdir(parents=True, exist_ok=True)
                if args.append:
                    ok, reason = _validate_append_commit(
                        run_dir=run_dir,
                        manifest_path=manifest_path,
                        current_git_commit=git_commit_full,
                        current_env_hash=str(env_info.get("env_hash", "")),
                    )
                    if not ok:
                        print(f"Error: {reason}")
                        return 2
                manifest = _init_manifest(
                    manifest_path,
                    run_id=run_id,
                    run_name=run_name,
                    run_tag=run_tag,
                    kv_mode=kv_mode,
                    seed=int(seed),
                    replica_id=int(replica_id),
                    model_id=model_id,
                    model_revision=model_revision,
                    args=args,
                    append_mode=bool(args.append),
                    git_commit_full=git_commit_full,
                    env_info=env_info,
                )
            else:
                manifest = {}

            if build_config_snapshot and write_config_snapshot:
                snapshot = build_config_snapshot(
                    script_name=Path(__file__).name,
                    args=args,
                    extra={"run_entry": run_entry, "model_id": model_id, "seed": int(seed)},
                )
                if args.append and (run_dir / "config_snapshot.yaml").exists():
                    pass
                else:
                    write_config_snapshot(str(run_dir), snapshot)

            for task in task_list:
                script = TASK_TO_SCRIPT.get(task)
                if not script:
                    print(f"Unknown task: {task}")
                    continue

                cmd = [
                    sys.executable,
                    "-u",
                    script,
                    "--kv_mode",
                    kv_mode,
                    "--model_id",
                    model_id,
                    "--seq_len",
                    str(seq_len),
                    "--gen_len",
                    str(gen_len),
                    "--group_size",
                    str(quant_params["group_size"]),
                    "--clip_percentile",
                    str(quant_params["clip_percentile"]),
                    "--group_size_k",
                    str(quant_params["group_size_k"]),
                    "--group_size_v",
                    str(quant_params["group_size_v"]),
                    "--clip_percentile_k",
                    str(quant_params["clip_percentile_k"]),
                    "--clip_percentile_v",
                    str(quant_params["clip_percentile_v"]),
                    "--seed",
                    str(seed),
                    "--replica_id",
                    str(replica_id),
                    "--out_dir",
                    str(run_dir),
                ]
                if run_name:
                    cmd.extend(["--run_name", str(run_name)])
                if model_revision:
                    cmd.extend(["--model_revision", str(model_revision)])
                if kv_mode in ["int8_ours", "int4_ours", "int4_ours_mixed"] and calib_file_path:
                    cmd.extend(["--calib_file", str(calib_file_path)])
                if calib_params.get("calib_strategy"):
                    cmd.extend(["--calib_strategy", str(calib_params["calib_strategy"])])
                if calib_params.get("use_attn_temperature") is False:
                    cmd.append("--no_use_attn_temperature")
                if calib_params.get("use_static_scales") is False:
                    cmd.append("--no_use_static_scales")
                if calib_params.get("adaptive_static_scales") is True:
                    cmd.append("--adaptive_static_scales")
                adaptive_static_margin = calib_params.get("adaptive_static_margin")
                if (
                    adaptive_static_margin is not None
                    and float(adaptive_static_margin) != 1.0
                ):
                    cmd.extend(["--adaptive_static_margin", str(adaptive_static_margin)])
                if calib_params.get("adaptive_static_k") is False:
                    cmd.append("--no_adaptive_static_k")
                if calib_params.get("adaptive_static_v") is False:
                    cmd.append("--no_adaptive_static_v")
                if decode_attn_impl:
                    cmd.extend(["--decode_attn_impl", str(decode_attn_impl)])

                if task == "eval_ppl":
                    max_length = min(seq_len, args.ppl_max_length)
                    cmd.extend(["--ppl_mode", str(args.ppl_mode)])
                    cmd.extend(["--max_length", str(max_length)])
                    cmd.extend(["--stride", str(args.ppl_stride)])
                    if args.ppl_max_samples is not None:
                        cmd.extend(["--max_samples", str(args.ppl_max_samples)])
                    if args.ppl_chunk_size is not None:
                        cmd.extend(["--chunk_size", str(args.ppl_chunk_size)])

                if task == "eval_needle":
                    cmd.extend(["--needle_max_new_tokens", str(args.needle_max_new_tokens)])
                    if args.needle_context_len:
                        cmd.extend(["--context_len", str(args.needle_context_len)])
                    if args.needle_num_depths is not None:
                        cmd.extend(["--num_depths", str(args.needle_num_depths)])
                    if args.needle_depth_batch is not None:
                        cmd.extend(["--depth_batch", str(args.needle_depth_batch)])
                    if args.needle_report_exact_match:
                        cmd.append("--report_exact_match")

                if task == "profile_latency":
                    cmd.extend(["--batch", str(batch)])
                    if args.latency_runs is not None:
                        cmd.extend(["--runs", str(args.latency_runs)])
                    if args.latency_warmup is not None:
                        cmd.extend(["--warmup", str(args.latency_warmup)])

                if task == "profile_memory":
                    cmd.extend(["--batch", str(batch)])

                log_path = logs_dir / run_id / f"{task}.log"

                if args.dry_run:
                    print("DRY RUN:", " ".join(cmd))
                    continue

                label = f"{run_name} (seed={seed})" if multi_seed else run_name
                if (
                    args.append
                    and args.skip_completed_success
                    and _task_is_completed_successfully(
                        manifest=manifest,
                        run_dir=run_dir,
                        task=task,
                    )
                ):
                    print(f"Skipping {task} for {label}: already marked success with CSV artifacts.")
                    _mark_task_status(
                        manifest_path,
                        manifest,
                        task=task,
                        status="success",
                        cmd=cmd,
                        log_path=log_path,
                        returncode=0,
                    )
                    execution_rows.append(
                        {
                            "timestamp": _now_iso(),
                            "run_id": run_id,
                            "run_name": run_name,
                            "seed": int(seed),
                            "replica_id": int(replica_id),
                            "task": task,
                            "status": "skipped",
                            "failure_type": "",
                            "returncode": 0,
                            "log_path": str(log_path),
                        }
                    )
                    continue

                print(f"Running {task} for {label}")
                total_attempts = max(int(args.max_retries), 0) + 1
                for attempt_idx in range(1, total_attempts + 1):
                    _mark_task_status(
                        manifest_path,
                        manifest,
                        task=task,
                        status="running",
                        cmd=cmd,
                        log_path=log_path,
                        attempt_idx=attempt_idx,
                    )
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                    log_mode = "a" if (args.append or attempt_idx > 1) else "w"
                    with open(log_path, log_mode, encoding="utf-8") as f:
                        if attempt_idx > 1:
                            f.write(
                                f"\n[RETRY] attempt={attempt_idx}/{total_attempts} at {_now_iso()}\n"
                            )
                        result = subprocess.run(
                            cmd,
                            stdout=f,
                            stderr=subprocess.STDOUT,
                            text=True,
                        )
                    returncode = int(result.returncode)
                    if returncode == 0:
                        _mark_task_status(
                            manifest_path,
                            manifest,
                            task=task,
                            status="success",
                            cmd=cmd,
                            log_path=log_path,
                            returncode=returncode,
                            attempt_idx=attempt_idx,
                        )
                        execution_rows.append(
                            {
                                "timestamp": _now_iso(),
                                "run_id": run_id,
                                "run_name": run_name,
                                "seed": int(seed),
                                "replica_id": int(replica_id),
                                "task": task,
                                "status": "success",
                                "failure_type": "",
                                "returncode": int(returncode),
                                "attempt": int(attempt_idx),
                                "log_path": str(log_path),
                            }
                        )
                        break

                    failure_type = _classify_failure(log_path=log_path, returncode=returncode)
                    err_msg = f"Task failed: {' '.join(cmd)}"
                    _mark_task_status(
                        manifest_path,
                        manifest,
                        task=task,
                        status="failed",
                        cmd=cmd,
                        log_path=log_path,
                        returncode=returncode,
                        error=err_msg,
                        failure_type=failure_type,
                        attempt_idx=attempt_idx,
                    )
                    if attempt_idx <= int(args.max_retries):
                        print(
                            "Task failed (will retry): "
                            f"run_id={run_id} task={task} attempt={attempt_idx}/{total_attempts} "
                            f"failure_type={failure_type} returncode={returncode}"
                        )
                        if float(args.retry_backoff_sec) > 0:
                            time.sleep(float(args.retry_backoff_sec))
                        continue

                    execution_rows.append(
                        {
                            "timestamp": _now_iso(),
                            "run_id": run_id,
                            "run_name": run_name,
                            "seed": int(seed),
                            "replica_id": int(replica_id),
                            "task": task,
                            "status": "failed",
                            "failure_type": str(failure_type),
                            "returncode": int(returncode),
                            "attempt": int(attempt_idx),
                            "log_path": str(log_path),
                        }
                    )
                    print(
                        "Task failed: "
                        f"run_id={run_id} task={task} failure_type={failure_type} returncode={returncode}"
                    )
                    should_continue = False
                    if args.failure_policy == "continue_all":
                        should_continue = True
                    elif args.failure_policy == "continue_on_oom" and failure_type == "oom":
                        should_continue = True

                    if should_continue:
                        print(
                            "Continuing after failure due to policy: "
                            f"policy={args.failure_policy} run_id={run_id} task={task}"
                        )
                        break

                    _flush_summary(1)
                    return 1

    _flush_summary(0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
