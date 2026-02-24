#!/usr/bin/env python3
"""
Run experiment matrix defined in configs/exp_matrix.yaml.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# QUA-002: module-level logger so that logger.warning calls work properly.
logger = logging.getLogger(__name__)

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from scripts.config_utils import ALLOWED_MODEL_IDS, load_config, read_json, read_text


TASK_TO_SCRIPT = {
    "profile_latency": "scripts/profile_latency.py",
    "profile_memory": "scripts/profile_memory.py",
    "eval_ppl": "scripts/eval_ppl.py",
    "eval_needle": "scripts/eval_needle.py",
    "eval_longbench": "scripts/eval_longbench.py",
    "eval_ruler": "scripts/eval_ruler.py",
}

TASK_TO_CSV_PATTERNS = {
    "profile_latency": "profile_latency_*.csv",
    "profile_memory": "profile_memory_*.csv",
    "eval_ppl": "profile_ppl_*.csv",
    "eval_needle": "profile_needle_*.csv",
    "eval_longbench": "profile_longbench_*.csv",
    "eval_ruler": "profile_ruler_*.csv",
}

SUPPORTED_KV_MODES = {
    "fp16",
    "int8_baseline",
    "int8_fused",
    "int8_ours",
    "int4_baseline",
    "int4_fused",
    "int4_ours",
    "int4_ours_mixed",
    "kivi_style",
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
    except Exception as _exc:
        # RUN-019: log a warning instead of silently swallowing import errors.
        print(f"Warning: failed to import torch for env info collection: {_exc}")
        info["torch_version"] = "unavailable"
        info["cuda_version"] = None
        info["cuda_available"] = False

    try:
        import transformers  # type: ignore

        info["transformers_version"] = getattr(transformers, "__version__", "unknown")
    except Exception as _exc:
        # RUN-019: log a warning instead of silently swallowing import errors.
        print(f"Warning: failed to import transformers for env info collection: {_exc}")
        info["transformers_version"] = "unavailable"

    payload = json.dumps(info, sort_keys=True, ensure_ascii=True)
    info["env_hash"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return info


# CHK-018: _read_json delegates to the shared implementation in config_utils.py.
def _read_json(path: Path) -> Dict[str, Any] | None:
    return read_json(path)


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=True)
        tmp_path.replace(path)
    except Exception:
        # RUN-028: clean up orphan .tmp file if replace() or write fails.
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        raise


def _existing_result_git_commits(run_dir: Path) -> List[str]:
    commits = set()
    patterns = [
        "profile_latency_*.csv",
        "profile_memory_*.csv",
        "profile_ppl_*.csv",
        "profile_needle_*.csv",
        "profile_longbench_*.csv",
        "profile_ruler_*.csv",
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
            except json.JSONDecodeError as exc:
                # RUN-033: log JSON/CSV parse errors explicitly.
                logger.warning("Failed to parse CSV %s: %s", path, exc)
                continue
            except OSError as exc:
                # RUN-033: log IO/permission errors explicitly.
                logger.warning("OS error reading CSV %s: %s", path, exc)
                continue
            except Exception as exc:
                # RUN-033: log unexpected errors with classification.
                logger.warning("Unexpected error reading CSV %s: %s", path, exc)
                continue
    return sorted(commits)


def _same_commit_prefix(a: str, b: str) -> bool:
    # RUN-018: warn when either commit is empty/unknown; do NOT treat as compatible.
    a = str(a).strip()
    b = str(b).strip()
    if not a or a == "unknown" or not b or b == "unknown":
        print(
            f"Warning: git commit comparison involves empty/unknown value "
            f"(a={a!r}, b={b!r}). Treating as incompatible to prevent silent cross-commit append."
        )
        return False
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


def _resolve_ruler_tasks_for_gate(ruler_tasks_arg: str | None) -> List[str]:
    if not ruler_tasks_arg:
        return ["s_niah", "mk_niah", "vt", "cwe"]
    out = [t.strip().lower() for t in str(ruler_tasks_arg).split(",") if t.strip()]
    return out or ["s_niah", "mk_niah", "vt", "cwe"]


def _ruler_peak_gen_tokens_for_gate(
    *,
    ruler_tasks_arg: str | None,
    ruler_max_new_tokens: int,
) -> int:
    peak = int(ruler_max_new_tokens)
    tasks = _resolve_ruler_tasks_for_gate(ruler_tasks_arg)
    if "cwe" in tasks:
        peak = max(peak, 128)
    return int(peak)


def _compute_ruler_truncation_warning(
    *,
    run_name: str,
    seq_len: int,
    gen_len: int,
    max_position_embeddings: int,
    ruler_context_len: int,
    ruler_max_new_tokens: int,
    ruler_tasks_arg: str | None,
) -> str | None:
    peak_gen = _ruler_peak_gen_tokens_for_gate(
        ruler_tasks_arg=ruler_tasks_arg,
        ruler_max_new_tokens=ruler_max_new_tokens,
    )
    base_total_budget = min(
        int(seq_len) + int(gen_len),
        int(max_position_embeddings),
    )
    # RUN-031: guard against negative safe_prompt_budget when peak_gen >= base_total_budget.
    safe_prompt_budget = min(int(ruler_context_len), max(0, int(base_total_budget) - int(peak_gen)))
    if safe_prompt_budget >= int(ruler_context_len):
        return None
    tasks = ",".join(_resolve_ruler_tasks_for_gate(ruler_tasks_arg))
    return (
        "Warning: RULER prompt budget will be truncated at runtime. "
        f"run_name={run_name} requested_context_len={ruler_context_len} "
        f"peak_gen_tokens={peak_gen} base_total_budget={base_total_budget} "
        f"safe_prompt_budget={safe_prompt_budget} tasks={tasks}. "
        "eval_ruler.py will enforce safe truncation to avoid length overflow."
    )


# CHK-018: _read_text_best_effort delegates to the shared read_text in config_utils.py.
# The shared version uses errors='replace' (CHK-008) instead of errors='ignore'.
def _read_text_best_effort(path: Path) -> str:
    return read_text(path)


def _classify_failure(*, log_path: Path, returncode: int | None) -> str:
    if returncode is not None and int(returncode) == 73:
        return "oom"
    if returncode is not None and int(returncode) == 130:
        return "interrupt"
    content = _read_text_best_effort(log_path).lower()
    # RUN-025: use word-boundary regex to avoid false positives like "room", "bloom".
    if (
        re.search(r"\boom\b", content)
        or "out of memory" in content
        or "cuda out of memory" in content
        or "outofmemoryerror" in content
    ):
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
    run_quant_bits: int | None,
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
    elif append_mode:
        # In append mode, keep run identity immutable and fail fast on mismatches.
        identity_pairs = [
            ("run_id", run_id),
            ("run_name", run_name),
            ("run_tag", run_tag),
            ("kv_mode", kv_mode),
            ("seed", int(seed)),
            ("replica_id", int(replica_id)),
            ("model_id", model_id),
        ]
        for key, expected in identity_pairs:
            existing = manifest.get(key, expected)
            if existing != expected:
                raise ValueError(
                    f"append blocked: manifest {key} mismatch "
                    f"(existing={existing!r}, incoming={expected!r})"
                )

    manifest["updated_at"] = now
    manifest["run_id"] = manifest.get("run_id", run_id)
    manifest["run_name"] = manifest.get("run_name", run_name)
    manifest["run_tag"] = manifest.get("run_tag", run_tag)
    manifest["kv_mode"] = manifest.get("kv_mode", kv_mode)
    manifest["seed"] = int(manifest.get("seed", int(seed)))
    manifest["replica_id"] = int(manifest.get("replica_id", int(replica_id)))
    manifest["model_id"] = manifest.get("model_id", model_id)
    manifest["model_revision"] = manifest.get("model_revision", model_revision)
    if run_quant_bits is not None:
        manifest["quant_bits"] = int(manifest.get("quant_bits", int(run_quant_bits)))
    manifest["git_commit"] = git_commit_full[:8] if git_commit_full else "unknown"
    manifest["git_commit_full"] = git_commit_full
    manifest["env_hash"] = env_info.get("env_hash", "unknown")
    # RUN-011: append mode overwrites manifest metadata (env_info, args) with current session values. Historical metadata is preserved in append_history.
    manifest["env_info"] = env_info
    manifest["append_mode"] = bool(append_mode)
    manifest["argv"] = list(sys.argv)
    if not isinstance(manifest.get("tasks"), dict):
        manifest["tasks"] = {}
    if not isinstance(manifest.get("append_history"), list):
        manifest["append_history"] = []
    if append_mode:
        # RUN-012: append_history records timestamps and status but not kv_mode/quant_bits changes. Full config is captured at run level.
        manifest["append_history"].append(
            {
                "timestamp": now,
                "run_id": run_id,
                "run_name": run_name,
                "run_tag": run_tag,
                "seed": int(seed),
                "replica_id": int(replica_id),
                "kv_mode": kv_mode,
                "quant_bits": int(run_quant_bits) if run_quant_bits is not None else None,
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
    record_history: bool = True,
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
    if status in {"success", "failed", "skipped"} and record_history:
        hist_row: Dict[str, Any] = {
            "timestamp": now,
            "status": status,
            "attempt": int(attempt_idx) if attempt_idx is not None else int(entry.get("attempts", 0)),
            "returncode": int(returncode) if returncode is not None else None,
            "failure_type": str(failure_type) if failure_type else "",
            "error": str(error) if error else "",
        }
        history.append(hist_row)
        # RUN-013: history is capped at 20 entries to prevent manifest bloat in long retry sequences.
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
    # RUN-032: validate numeric types and ranges for quant parameters.
    for _field, _val in (("clip_percentile_k", clip_percentile_k), ("clip_percentile_v", clip_percentile_v)):
        if not isinstance(_val, (int, float)) or isinstance(_val, bool):
            raise ValueError(
                f"resolve_quant_params: {_field}={_val!r} must be a numeric value, "
                f"got {type(_val).__name__}."
            )
        if not (0.0 < float(_val) <= 100.0):
            raise ValueError(
                f"resolve_quant_params: {_field}={_val!r} must be in the range (0, 100]."
            )
    for _field, _val in (("group_size_k", group_size_k), ("group_size_v", group_size_v)):
        if not isinstance(_val, int) or isinstance(_val, bool):
            raise ValueError(
                f"resolve_quant_params: {_field}={_val!r} must be an integer, "
                f"got {type(_val).__name__}."
            )
        if _val <= 0:
            raise ValueError(
                f"resolve_quant_params: {_field}={_val!r} must be a positive integer."
            )
    return {
        "clip_percentile": clip_percentile_k,
        "group_size": group_size_k,
        "clip_percentile_k": clip_percentile_k,
        "clip_percentile_v": clip_percentile_v,
        "group_size_k": group_size_k,
        "group_size_v": group_size_v,
    }


def resolve_calib_params(run_entry: Dict, quant_defaults: Dict, kv_mode: str) -> Dict[str, object]:
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
    default_calib_strategy = (
        "kivi_asymmetric" if kv_mode == "kivi_style" else quant_defaults.get("calib_strategy")
    )
    calib_strategy = run_entry.get("calib_strategy", default_calib_strategy)
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
    parser.add_argument(
        "--ppl_target_tokens",
        type=int,
        default=None,
        help=(
            "Pass through to eval_ppl.py --target_tokens. "
            "When set, each run must evaluate at least this many tokens."
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
        "--longbench_source",
        type=str,
        default="synthetic",
        choices=["synthetic", "hf", "jsonl"],
        help="Pass through to eval_longbench.py --longbench_source.",
    )
    parser.add_argument(
        "--longbench_tasks",
        type=str,
        default=None,
        help="Pass through to eval_longbench.py --longbench_tasks (comma-separated).",
    )
    parser.add_argument(
        "--longbench_dataset_repo",
        type=str,
        default="THUDM/LongBench",
        help="Pass through to eval_longbench.py --longbench_dataset_repo.",
    )
    parser.add_argument(
        "--longbench_dataset_split",
        type=str,
        default="test",
        help="Pass through to eval_longbench.py --longbench_dataset_split.",
    )
    parser.add_argument(
        "--longbench_dataset_path",
        type=str,
        default=None,
        help="Pass through to eval_longbench.py --longbench_dataset_path for jsonl source.",
    )
    parser.add_argument(
        "--longbench_max_samples",
        type=int,
        default=32,
        help="Pass through to eval_longbench.py --longbench_max_samples (per task).",
    )
    parser.add_argument(
        "--longbench_max_new_tokens",
        type=int,
        default=64,
        help="Pass through to eval_longbench.py --longbench_max_new_tokens.",
    )
    parser.add_argument(
        "--longbench_context_len",
        type=int,
        default=None,
        help="Pass through to eval_longbench.py --longbench_context_len.",
    )
    parser.add_argument(
        "--longbench_allow_synthetic_fallback",
        action="store_true",
        default=False,
        help="Pass through to eval_longbench.py --longbench_allow_synthetic_fallback.",
    )
    parser.add_argument(
        "--ruler_num_cases",
        type=int,
        default=64,
        help="Pass through to eval_ruler.py --ruler_num_cases.",
    )
    parser.add_argument(
        "--ruler_num_kv_pairs",
        type=int,
        default=256,
        help="Pass through to eval_ruler.py --ruler_num_kv_pairs.",
    )
    parser.add_argument(
        "--ruler_depth_ratios",
        type=str,
        default="0.1,0.5,0.9",
        help="Pass through to eval_ruler.py --ruler_depth_ratios.",
    )
    parser.add_argument(
        "--ruler_max_new_tokens",
        type=int,
        default=32,
        help="Pass through to eval_ruler.py --ruler_max_new_tokens.",
    )
    parser.add_argument(
        "--ruler_context_len",
        type=int,
        default=None,
        help="Pass through to eval_ruler.py --ruler_context_len.",
    )
    parser.add_argument(
        "--ruler_tasks",
        type=str,
        default=None,
        help="Pass through to eval_ruler.py --ruler_tasks (comma-separated).",
    )
    parser.add_argument(
        "--ruler_mk_num_keys",
        type=int,
        default=4,
        help="Pass through to eval_ruler.py --ruler_mk_num_keys.",
    )
    parser.add_argument(
        "--ruler_vt_num_chains",
        type=int,
        default=1,
        help="Pass through to eval_ruler.py --ruler_vt_num_chains.",
    )
    parser.add_argument(
        "--ruler_vt_num_hops",
        type=int,
        default=4,
        help="Pass through to eval_ruler.py --ruler_vt_num_hops.",
    )
    parser.add_argument(
        "--ruler_cwe_freq",
        type=int,
        default=30,
        help="Pass through to eval_ruler.py --ruler_cwe_freq.",
    )
    parser.add_argument(
        "--ruler_cwe_num_words",
        type=int,
        default=10,
        help="Pass through to eval_ruler.py --ruler_cwe_num_words.",
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
    # RUN-034: BREAKING CHANGE — Prior to RUN-022, subprocess tasks waited
    # indefinitely (no timeout).  The default is now 3600s (1 hour).  Callers
    # that relied on infinite wait must pass --subprocess_timeout 0 to restore
    # the old behaviour.
    parser.add_argument(
        "--subprocess_timeout",
        type=int,
        default=3600,
        help=(
            # RUN-022: configurable per-task subprocess timeout to avoid infinite blocks.
            "Timeout in seconds for each subprocess task call (default: 3600 = 1 hour). "
            "Set to 0 to disable the timeout and restore the pre-RUN-022 infinite-wait behaviour."
        ),
    )
    args = parser.parse_args()
    # QUA-002: configure logging infrastructure so logger.warning calls emit output.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
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
    # SEC-002: Reject unknown model IDs to prevent trust_remote_code RCE.
    if model_id not in ALLOWED_MODEL_IDS:
        print(
            f"Error: model_id={model_id!r} is not in the allowed model whitelist "
            f"(ALLOWED_MODEL_IDS). Add the model to scripts/config_utils.py if it "
            f"has been verified as safe."
        )
        return 2
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

    # RUN-010: matrix is not validated for non-empty here; an empty matrix results in zero iterations (harmless but confusing).
    matrix = config.get("matrix", [])
    if not isinstance(matrix, list) or len(matrix) == 0:
        print(
            "Error: config matrix is empty or invalid. "
            "Expected a non-empty list under key 'matrix'."
        )
        return 2

    invalid_kv_modes: List[str] = []
    for idx, entry in enumerate(matrix):
        if not isinstance(entry, dict):
            print(f"Error: matrix[{idx}] must be a mapping, got {type(entry).__name__}.")
            return 2
        run_name = entry.get("run_name")
        kv_mode = entry.get("kv_mode", "fp16")
        if kv_mode not in SUPPORTED_KV_MODES:
            label = run_name or f"index={idx}"
            if run_name_filter and run_name not in run_name_filter:
                print(
                    f"Warning: skipped entry {label} has unsupported kv_mode={kv_mode!r} "
                    f"(not in SUPPORTED_KV_MODES). Ignored because it does not match --run_names filter."
                )
                continue
            invalid_kv_modes.append(f"{label}:{kv_mode}")
            continue
        if run_name_filter and run_name not in run_name_filter:
            continue
    if invalid_kv_modes:
        print("Error: found unsupported kv_mode entries:")
        for item in invalid_kv_modes:
            print(f"  - {item}")
        return 2
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
            # RUN-029: warn when run_name is empty or missing instead of silently skipping.
            print(
                f"Warning: matrix entry missing or empty 'run_name' field: {run_entry!r}. Skipping."
            )
            continue
        if run_name_filter and run_name not in run_name_filter:
            continue

        kv_mode = run_entry.get("kv_mode", "fp16")
        if kv_mode not in SUPPORTED_KV_MODES:
            print(f"Error: unsupported kv_mode={kv_mode} for {run_name}")
            return 2

        seq_len = run_entry.get("seq_len", 1024)
        gen_len = run_entry.get("gen_len", 128)
        # RUN-021: validate seq_len and gen_len are positive integers.
        for _field, _val in (("seq_len", seq_len), ("gen_len", gen_len)):
            if not isinstance(_val, int) or isinstance(_val, bool):
                print(
                    f"Error: run_name={run_name} {_field}={_val!r} must be an integer, "
                    f"got {type(_val).__name__}."
                )
                return 2
            if _val <= 0:
                print(
                    f"Error: run_name={run_name} {_field}={_val!r} must be a positive integer."
                )
                return 2
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
        if max_position_embeddings is not None and "eval_ruler" in task_list:
            requested_ruler_context = (
                int(args.ruler_context_len)
                if args.ruler_context_len is not None
                else int(seq_len)
            )
            warning = _compute_ruler_truncation_warning(
                run_name=str(run_name),
                seq_len=int(seq_len),
                gen_len=int(gen_len),
                max_position_embeddings=int(max_position_embeddings),
                ruler_context_len=int(requested_ruler_context),
                ruler_max_new_tokens=int(args.ruler_max_new_tokens),
                ruler_tasks_arg=args.ruler_tasks,
            )
            if warning:
                # RUN-017: truncation warning goes to stdout only, not manifest.
                # Acceptable for now since manifest already records seq_len.
                print(warning)

        quant_params = resolve_quant_params(run_entry, quant_defaults)
        run_quant_bits = run_entry.get("quant_bits", quant_defaults.get("quant_bits"))
        calib_params = resolve_calib_params(run_entry, quant_defaults, kv_mode=kv_mode)
        decode_attn_impl = run_entry.get("decode_attn_impl")
        if decode_attn_impl is None:
            decode_attn_impl = "torch_ref" if kv_mode == "kivi_style" else kernel_defaults.get(
                "decode_attn_impl"
            )

        if kv_mode == "kivi_style":
            if run_quant_bits is None:
                run_quant_bits = 8
            if int(run_quant_bits) not in (4, 8):
                print(
                    f"Error: run_name={run_name} kv_mode=kivi_style requires quant_bits in {{4,8}}, "
                    f"got {run_quant_bits!r}."
                )
                return 2
            calib_strategy = str(calib_params.get("calib_strategy") or "").strip()
            if not calib_strategy:
                # Enforce kivi_asymmetric as the only valid strategy for kivi_style
                calib_params["calib_strategy"] = "kivi_asymmetric"
                calib_strategy = "kivi_asymmetric"
            if calib_strategy not in {"kivi_asymmetric"}:
                print(
                    f"Error: run_name={run_name} kv_mode=kivi_style requires calib_strategy=kivi_asymmetric, "
                    f"got {calib_strategy!r}."
                )
                return 2
            if decode_attn_impl and str(decode_attn_impl) != "torch_ref":
                source = "run_entry" if "decode_attn_impl" in run_entry else "kernel_defaults"
                print(
                    f"Error: run_name={run_name} kv_mode=kivi_style requires decode_attn_impl=torch_ref, "
                    f"got {decode_attn_impl!r} (from {source})."
                )
                return 2
            decode_attn_impl = "torch_ref"

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
                try:
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
                        run_quant_bits=int(run_quant_bits) if run_quant_bits is not None else None,
                        args=args,
                        append_mode=bool(args.append),
                        git_commit_full=git_commit_full,
                        env_info=env_info,
                    )
                except ValueError as exc:
                    print(f"Error: {exc}")
                    return 2
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
                    # RUN-027: warn explicitly when an unknown task name is encountered.
                    print(
                        f"Warning: unknown task name {task!r} for run_name={run_name}; "
                        f"supported tasks are: {sorted(TASK_TO_SCRIPT.keys())}. Skipping."
                    )
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
                    "--seed",
                    str(seed),
                    "--replica_id",
                    str(replica_id),
                    "--out_dir",
                    str(run_dir),
                ]
                if kv_mode in {
                    "int8_baseline",
                    "int8_fused",
                    "int8_ours",
                    "int4_baseline",
                    "int4_fused",
                    "int4_ours",
                    "int4_ours_mixed",
                }:
                    cmd.extend(
                        [
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
                        ]
                    )
                if run_name:
                    cmd.extend(["--run_name", str(run_name)])
                if model_revision:
                    cmd.extend(["--model_revision", str(model_revision)])
                # Only pass quant/calib params for quantized modes (not fp16)
                if kv_mode != "fp16":
                    if run_quant_bits is not None:
                        cmd.extend(["--quant_bits", str(run_quant_bits)])
                    if kv_mode in ["int8_ours", "int4_ours", "int4_ours_mixed"] and calib_file_path:
                        cmd.extend(["--calib_file", str(calib_file_path)])
                    if calib_params.get("calib_strategy"):
                        cmd.extend(["--calib_strategy", str(calib_params["calib_strategy"])])
                    # RUN-023: always send boolean flags explicitly to avoid implicit coupling.
                    if calib_params.get("use_attn_temperature"):
                        cmd.append("--use_attn_temperature")
                    else:
                        cmd.append("--no_use_attn_temperature")
                    if calib_params.get("use_static_scales"):
                        cmd.append("--use_static_scales")
                    else:
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
                    if args.ppl_target_tokens is not None:
                        cmd.extend(["--target_tokens", str(args.ppl_target_tokens)])

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

                if task == "eval_longbench":
                    cmd.extend(["--longbench_source", str(args.longbench_source)])
                    cmd.extend(
                        ["--longbench_dataset_repo", str(args.longbench_dataset_repo)]
                    )
                    cmd.extend(
                        ["--longbench_dataset_split", str(args.longbench_dataset_split)]
                    )
                    cmd.extend(
                        ["--longbench_max_samples", str(args.longbench_max_samples)]
                    )
                    cmd.extend(
                        ["--longbench_max_new_tokens", str(args.longbench_max_new_tokens)]
                    )
                    if args.longbench_tasks:
                        cmd.extend(["--longbench_tasks", str(args.longbench_tasks)])
                    if args.longbench_dataset_path:
                        cmd.extend(
                            ["--longbench_dataset_path", str(args.longbench_dataset_path)]
                        )
                    if args.longbench_context_len is not None:
                        cmd.extend(
                            ["--longbench_context_len", str(args.longbench_context_len)]
                        )
                    if args.longbench_allow_synthetic_fallback:
                        cmd.append("--longbench_allow_synthetic_fallback")

                if task == "eval_ruler":
                    cmd.extend(["--ruler_num_cases", str(args.ruler_num_cases)])
                    cmd.extend(["--ruler_num_kv_pairs", str(args.ruler_num_kv_pairs)])
                    cmd.extend(["--ruler_depth_ratios", str(args.ruler_depth_ratios)])
                    cmd.extend(
                        ["--ruler_max_new_tokens", str(args.ruler_max_new_tokens)]
                    )
                    if args.ruler_context_len is not None:
                        cmd.extend(["--ruler_context_len", str(args.ruler_context_len)])
                    if args.ruler_tasks is not None:
                        cmd.extend(["--ruler_tasks", str(args.ruler_tasks)])
                    cmd.extend(["--ruler_mk_num_keys", str(args.ruler_mk_num_keys)])
                    cmd.extend(["--ruler_vt_num_chains", str(args.ruler_vt_num_chains)])
                    cmd.extend(["--ruler_vt_num_hops", str(args.ruler_vt_num_hops)])
                    cmd.extend(["--ruler_cwe_freq", str(args.ruler_cwe_freq)])
                    cmd.extend(["--ruler_cwe_num_words", str(args.ruler_cwe_num_words)])

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
                    # RUN-008: Do not re-write manifest for already-completed tasks;
                    # the task is already recorded as success in the manifest.
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
                    # RUN-030: Note — append mode ("a") means previous attempt OOM traces
                    # remain in the same log file and may influence _classify_failure on
                    # subsequent retries. For clean per-attempt classification, separate log
                    # files per attempt would be needed. This is a known limitation; the
                    # current approach prioritises log continuity over isolation.
                    log_mode = "a" if (args.append or attempt_idx > 1) else "w"
                    # RUN-022: use a configurable timeout to avoid infinite subprocess hangs.
                    # QUA-007: renamed from _timeout to timeout_sec for clarity.
                    timeout_sec = int(args.subprocess_timeout) if int(args.subprocess_timeout) > 0 else None
                    with open(log_path, log_mode, encoding="utf-8") as f:
                        if attempt_idx > 1:
                            f.write(
                                f"\n[RETRY] attempt={attempt_idx}/{total_attempts} at {_now_iso()}\n"
                            )
                        try:
                            result = subprocess.run(
                                cmd,
                                stdout=f,
                                stderr=subprocess.STDOUT,
                                text=True,
                                timeout=timeout_sec,
                            )
                            returncode = int(result.returncode)
                        except subprocess.TimeoutExpired as exc:
                            f.write(
                                f"\n[ERROR] Subprocess timed out after {timeout_sec}s: {exc}\n"
                            )
                            returncode = 124
                            failure_type = "timeout"
                            err_msg = f"Task timed out after {timeout_sec}s: {' '.join(cmd)}"
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
                            execution_rows.append(
                                {
                                    "timestamp": _now_iso(),
                                    "run_id": run_id,
                                    "run_name": run_name,
                                    "seed": int(seed),
                                    "replica_id": int(replica_id),
                                    "task": task,
                                    "status": "failed",
                                    "failure_type": failure_type,
                                    "returncode": int(returncode),
                                    "attempt": int(attempt_idx),
                                    "log_path": str(log_path),
                                }
                            )
                            _flush_summary(1)
                            return 1
                        except (OSError, subprocess.SubprocessError, ValueError) as exc:
                            f.write(f"\n[ERROR] Failed to launch subprocess: {exc}\n")
                            returncode = 127
                            failure_type = "spawn_error"
                            err_msg = f"Task failed to launch: {' '.join(cmd)} ({exc})"
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
                            execution_rows.append(
                                {
                                    "timestamp": _now_iso(),
                                    "run_id": run_id,
                                    "run_name": run_name,
                                    "seed": int(seed),
                                    "replica_id": int(replica_id),
                                    "task": task,
                                    "status": "failed",
                                    "failure_type": failure_type,
                                    "returncode": int(returncode),
                                    "attempt": int(attempt_idx),
                                    "log_path": str(log_path),
                                }
                            )
                            _flush_summary(1)
                            return 1
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
