#!/usr/bin/env python3
"""
Aggregate structured CSV outputs under results/runs/ into summary tables and plots.

Outputs:
  - results/tables/*.csv
  - results/plots/*.png

This script is intentionally "dumb but robust": it infers which CSVs to load by
filename prefixes produced by the repo's scripts (profile_latency, profile_memory,
profile_ppl, profile_needle, profile_longbench, profile_ruler, needle_details).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config_utils import KV_MODE_ORDER

try:
    from scipy.stats import t as _t_dist
    _HAS_SCIPY = True

    def _t_critical(df: int, alpha: float = 0.05) -> float:
        """Return two-tailed t critical value for given df and alpha."""
        # AGG-039: guard against df <= 0, which causes scipy to return NaN
        if df <= 0:
            return float("nan")
        return float(_t_dist.ppf(1.0 - alpha / 2.0, df))

except ImportError:
    _HAS_SCIPY = False
    # AGG-045: Two-tailed t-distribution critical values at alpha=0.05,
    # sourced from standard statistical tables (scipy.stats.t.ppf).
    # Confirmed against Abramowitz & Stegun (1964), Table 26.7.
    # Fallback lookup table for t_{0.975, df} (two-tailed 95% CI).
    _T_TABLE = {
        1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
        6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        15: 2.131, 20: 2.086, 25: 2.060, 30: 2.042, 40: 2.021,
        60: 2.000, 120: 1.980,
    }

    def _t_critical(df: int, alpha: float = 0.05) -> float:
        # AGG-039: guard against df <= 0; return NaN consistently with scipy path
        if df <= 0:
            return float("nan")
        if alpha != 0.05:
            # AGG-038: warn instead of silently returning z=1.96 for non-standard alpha
            logger.warning(
                "_t_critical fallback table only covers alpha=0.05; "
                "requested alpha=%.4f — returning z=1.96 approximation.",
                alpha,
            )
            return 1.96
        if df in _T_TABLE:
            return _T_TABLE[df]
        # Interpolate between nearest known df values
        keys = sorted(_T_TABLE.keys())
        if df < keys[0]:
            return _T_TABLE[keys[0]]
        if df > keys[-1]:
            # AGG-043: use the df=120 table entry as upper-bound fallback to
            # avoid a discontinuous jump from 1.980 at df=120 to 1.96 at df=121.
            return _T_TABLE.get(120, 1.980)
        for i in range(len(keys) - 1):
            if keys[i] <= df <= keys[i + 1]:
                lo, hi = keys[i], keys[i + 1]
                frac = (df - lo) / (hi - lo)
                return _T_TABLE[lo] * (1 - frac) + _T_TABLE[hi] * frac
        return 1.96

logger = logging.getLogger(__name__)

# AGG-042: log once at import time if scipy is unavailable so degradation is visible
if not _HAS_SCIPY:
    logger.warning(
        "scipy not found; _t_critical will use a fallback lookup table "
        "(two-tailed alpha=0.05 only). Install scipy for full t-distribution support."
    )

# AGG-015: Maximum sample size for exact sign-flip enumeration (2^n perms).
# At n=16, 2^16=65536 permutations — comfortably fast on any CPU.
# Beyond 16, the exponential cost becomes impractical and we switch to
# Monte Carlo approximation.
_EXACT_ENUM_THRESHOLD = 16

_KV_MODE_RANK = {mode: idx for idx, mode in enumerate(KV_MODE_ORDER)}


def _kv_mode_rank(value: object) -> int:
    return _KV_MODE_RANK.get(str(value), len(KV_MODE_ORDER))


def _sort_by_kv_mode(
    df: pd.DataFrame,
    *,
    col: str = "kv_mode",
    extra_cols: List[str] | None = None,
) -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return df
    out = df.copy()
    out["_kv_mode_rank"] = out[col].map(_kv_mode_rank)
    sort_cols = ["_kv_mode_rank", col]
    if extra_cols:
        sort_cols.extend([c for c in extra_cols if c in out.columns])
    out = out.sort_values(sort_cols, kind="stable").reset_index(drop=True)
    return out.drop(columns=["_kv_mode_rank"])


def _iter_grouped(df: pd.DataFrame, hue: str) -> List[tuple[object, pd.DataFrame]]:
    groups = list(df.groupby(hue))
    if hue == "kv_mode":
        groups.sort(key=lambda item: (_kv_mode_rank(item[0]), str(item[0])))
    else:
        groups.sort(key=lambda item: str(item[0]))
    return groups


def _count_duplicate_groups(
    df: pd.DataFrame,
    group_cols: List[str],
) -> tuple[int, int]:
    if df.empty or not group_cols:
        return 0, 0
    counts = df.groupby(group_cols, dropna=False).size()
    dup = counts[counts > 1]
    if dup.empty:
        return 0, 0
    duplicate_groups = int(dup.shape[0])
    duplicate_extra_rows = int((dup - 1).sum())
    return duplicate_groups, duplicate_extra_rows


def _read_csvs(runs_dir: Path, patterns: Iterable[str]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for pattern in patterns:
        # Results are written under per-run subdirectories (e.g., results/runs/<run_id>/profile_*.csv).
        # Use recursive glob so aggregation works regardless of directory layout.
        for path in sorted(runs_dir.rglob(pattern)):
            try:
                df = pd.read_csv(path)
            except Exception as exc:
                logger.warning("Skipped unreadable CSV %s: %s", path, exc)
                continue
            try:
                df["source_file"] = str(path.relative_to(runs_dir))
            except Exception as rel_exc:
                # AGG-044: log when relative_to fails so path resolution issues are visible
                logger.warning(
                    "_read_csvs: could not make path relative to runs_dir (%s); "
                    "using absolute path instead. Error: %s",
                    runs_dir,
                    rel_exc,
                )
                df["source_file"] = str(path)
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _to_numeric(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            before_na = int(df[col].isna().sum())
            df[col] = pd.to_numeric(df[col], errors="coerce")
            after_na = int(df[col].isna().sum())
            coerced = after_na - before_na
            if coerced > 0:
                logger.warning(
                    "_to_numeric: %d value(s) in column '%s' coerced to NaN.",
                    coerced, col,
                )
    return df


def _agg_mean_std(df: pd.DataFrame, keys: List[str], values: List[str]) -> pd.DataFrame:
    keep_values = [c for c in values if c in df.columns]
    if df.empty or not keep_values:
        return pd.DataFrame()
    out = (
        df.groupby(keys, dropna=False)[keep_values]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    # Flatten multi-index columns: tpot_ms_mean, tpot_ms_std, ...
    out.columns = [
        "_".join([c for c in col if c]) if isinstance(col, tuple) else col for col in out.columns
    ]
    return out


def _safe_t_crit(n: float) -> float:
    """QUA-003: module-level helper (moved out of _add_ci95_columns loop).
    Return t critical value for sample size *n*.

    # AGG-048: Non-finite n (inf, NaN) returns NaN — not 0.0 — because
    # a zero CI half-width creates a false "zero error" appearance in
    # downstream tables, whereas NaN correctly propagates as missing data.
    # n <= 1 also returns 0.0 as a first guard; _add_ci95_columns then
    # applies .where(cnt>1, NaN) as a second guard (QUA-008 defense-in-depth).
    """
    # AGG-048: non-finite n (inf, NaN) must yield NaN, not 0.0.
    if not np.isfinite(n):
        return float("nan")
    # AGG-036 / QUA-008: n <= 1 returns 0.0 (masked to NaN by caller).
    if n <= 1:
        return 0.0
    return _t_critical(max(1, int(n) - 1))


def _add_ci95_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add CI95 columns for every *_mean/*_std/*_count triplet in aggregated tables.
    """
    if df.empty:
        return df
    out = df.copy()
    for col in list(out.columns):
        if not col.endswith("_mean"):
            continue
        prefix = col[: -len("_mean")]
        std_col = f"{prefix}_std"
        cnt_col = f"{prefix}_count"
        if std_col not in out.columns or cnt_col not in out.columns:
            continue
        std = pd.to_numeric(out[std_col], errors="coerce")
        cnt = pd.to_numeric(out[cnt_col], errors="coerce")
        mean = pd.to_numeric(out[col], errors="coerce")
        sem = std / np.sqrt(cnt.clip(lower=1))
        # Use t-distribution critical value instead of fixed z=1.96.
        # For small n (e.g. n=5, df=4), t_{0.975}=2.776 vs z=1.96.
        t_crit = cnt.apply(_safe_t_crit)
        ci_half = t_crit * sem
        ci_half = ci_half.where(cnt > 1, np.nan)
        out[f"{prefix}_ci95_half"] = ci_half
        out[f"{prefix}_ci95_low"] = mean - ci_half
        out[f"{prefix}_ci95_high"] = mean + ci_half
    return out


def _extract_seed_from_run_id(run_id: str) -> float | None:
    if not isinstance(run_id, str):
        return None
    m = re.search(r"_s(\d+)_", run_id)
    if not m:
        return None
    try:
        return float(int(m.group(1)))
    except Exception:
        return None


def _save_table(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)


def _slugify_model_id(model_id: object) -> str:
    raw = str(model_id).strip()
    if not raw:
        return "unknown_model"
    slug = raw.replace("/", "__")
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", slug).strip("._")
    return slug or "unknown_model"


def _export_per_model_layered_tables(tables_dir: Path) -> pd.DataFrame:
    """
    Export per-model layered tables for all top-level CSVs that carry `model_id`.

    Output layout:
      tables/per_model/<model_slug>/<table_name>.csv

    Returns:
      Manifest rows with model/table/row_count metadata.
    """
    rows: List[Dict[str, object]] = []
    per_model_root = tables_dir / "per_model"

    for csv_path in sorted(tables_dir.glob("*.csv")):
        # Avoid recursively layering the layered-table manifest itself.
        if csv_path.name == "per_model_table_manifest.csv":
            continue
        try:
            df = pd.read_csv(csv_path)
        except Exception as exc:
            logger.warning("Failed to read CSV %s: %s", csv_path.name, exc)
            continue
        if df.empty or "model_id" not in df.columns:
            continue

        model_series = df["model_id"].astype(str).str.strip()
        model_values = sorted(
            {
                v
                for v in model_series.tolist()
                if v and v.lower() != "nan"
            }
        )
        if not model_values:
            continue

        for model_id in model_values:
            sub = df[model_series == model_id].copy()
            if sub.empty:
                continue
            model_slug = _slugify_model_id(model_id)
            out_path = per_model_root / model_slug / csv_path.name
            _save_table(sub, out_path)
            rows.append(
                {
                    "table_name": csv_path.name,
                    "model_id": model_id,
                    "model_slug": model_slug,
                    "row_count": int(len(sub)),
                    "output_file": str(out_path.relative_to(tables_dir)),
                }
            )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _parse_seq_tag_to_len(seq_tag: str) -> int | None:
    seq_tag = str(seq_tag).strip().lower()
    m = re.fullmatch(r"(\d+)(k?)", seq_tag)
    if not m:
        return None
    value = int(m.group(1))
    if m.group(2) == "k":
        return value * 1024
    return value


def _parse_batch_list(text: str) -> List[int]:
    if not isinstance(text, str) or not text.strip():
        return []
    out: List[int] = []
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            out.append(int(item))
        except Exception:
            continue
    return sorted(set(out))


def _format_batch_list(values: Iterable[int]) -> str:
    uniq = sorted({int(v) for v in values})
    return ",".join(str(v) for v in uniq)


def _log_contains_oom(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    try:
        content = log_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return bool(re.search(r"\bOOM\b|out of memory", content, flags=re.IGNORECASE))


def _log_contains_traceback(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    try:
        content = log_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return "Traceback (most recent call last):" in content


def _strict_log_failures(runs_dir: Path, logs_dir: Path | None) -> List[str]:
    issues: List[str] = []
    if logs_dir is None or not logs_dir.exists():
        issues.append(
            "strict mode requires logs_dir to validate Traceback/OOM conditions "
            f"(current logs_dir={logs_dir})."
        )
        return issues

    task_to_csv_pattern = {
        "profile_latency": "profile_latency_*.csv",
        "profile_memory": "profile_memory_*.csv",
        "eval_ppl": "profile_ppl_*.csv",
        "eval_needle": "profile_needle_*.csv",
        "eval_longbench": "profile_longbench_*.csv",
        "eval_ruler": "profile_ruler_*.csv",
    }
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        for task_name, csv_pattern in task_to_csv_pattern.items():
            log_path = logs_dir / run_dir.name / f"{task_name}.log"
            if not log_path.exists():
                continue
            has_traceback = _log_contains_traceback(log_path)
            has_oom = _log_contains_oom(log_path)
            if not (has_traceback or has_oom):
                continue
            has_csv = any(run_dir.glob(csv_pattern))
            if has_csv:
                reason = "traceback" if has_traceback else "oom"
                issues.append(
                    "mixed failure/success detected: "
                    f"run_dir={run_dir.name} task={task_name} reason={reason} "
                    f"log={log_path}"
                )
            elif has_traceback:
                issues.append(
                    "task traceback detected: "
                    f"run_dir={run_dir.name} task={task_name} log={log_path}"
                )
    return issues


def _strict_missing_seed(df: pd.DataFrame, *, table_name: str) -> List[str]:
    if df.empty:
        return []
    if "seed" not in df.columns:
        return [f"{table_name}: missing required column 'seed'."]
    seed_series = pd.to_numeric(df["seed"], errors="coerce")
    missing = seed_series.isna()
    n_missing = int(missing.sum())
    if n_missing <= 0:
        return []
    sample = []
    if "source_file" in df.columns:
        sample = (
            df.loc[missing, "source_file"]
            .dropna()
            .astype(str)
            .head(3)
            .tolist()
        )
    sample_txt = f" sample_files={sample}" if sample else ""
    return [
        f"{table_name}: found {n_missing} rows with missing/non-numeric seed.{sample_txt}"
    ]


def _print_strict_issues(issues: List[str]) -> None:
    if not issues:
        return
    print("Strict mode checks failed:")
    for idx, issue in enumerate(issues, start=1):
        print(f"  {idx}. {issue}")


def _read_json(path: Path) -> dict:
    """Read a JSON file, returning {} if missing or not a dict.

    AGG-046: uses classified exception handling with logging instead of
    bare ``except Exception: return {}``.
    """
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        logger.warning("_read_json: %s did not contain a dict (got %s), returning {}", path, type(data).__name__)
    except json.JSONDecodeError as exc:
        # AGG-046: log JSON corruption explicitly.
        logger.warning("_read_json: JSON decode error reading %s: %s", path, exc)
    except OSError as exc:
        # AGG-046: log IO/permission errors explicitly.
        logger.warning("_read_json: OS error reading %s: %s", path, exc)
    except Exception as exc:
        # AGG-046: log unexpected errors with classification.
        logger.warning("_read_json: unexpected error reading %s: %s", path, exc)
    return {}


def _same_commit_prefix(a: str, b: str) -> bool:
    # AGG-047: aligned with run_experiments.py semantics — empty/unknown commits
    # are treated as incompatible (returns False) with a warning, to prevent
    # silent cross-commit data aggregation.
    a = str(a).strip()
    b = str(b).strip()
    if not a or a == "unknown" or not b or b == "unknown":
        logger.warning(
            "AGG-047: git commit comparison involves empty/unknown value "
            "(a=%r, b=%r). Treating as incompatible.",
            a, b,
        )
        return False
    return a[:8] == b[:8]


def _csv_git_commits(path: Path) -> List[str]:
    commits = set()
    try:
        df = pd.read_csv(path, usecols=["git_commit"])
    except ValueError:
        return []
    except Exception:
        return []
    for val in df.get("git_commit", pd.Series(dtype=object)).dropna().astype(str):
        v = val.strip()
        if v:
            commits.add(v)
    return sorted(commits)


def _strict_manifest_and_artifact_checks(
    runs_dir: Path,
    logs_dir: Path | None,
) -> List[str]:
    issues: List[str] = []
    task_to_csv_pattern = {
        "profile_latency": "profile_latency_*.csv",
        "profile_memory": "profile_memory_*.csv",
        "eval_ppl": "profile_ppl_*.csv",
        "eval_needle": "profile_needle_*.csv",
        "eval_longbench": "profile_longbench_*.csv",
        "eval_ruler": "profile_ruler_*.csv",
    }
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        csv_files = []
        for pattern in task_to_csv_pattern.values():
            csv_files.extend(sorted(run_dir.glob(pattern)))
        if not csv_files:
            continue

        manifest_path = run_dir / "run_manifest.json"
        manifest = _read_json(manifest_path)
        if not manifest:
            issues.append(f"{run_dir.name}: missing or invalid run_manifest.json")
            tasks = {}
            manifest_commit = ""
        else:
            tasks = manifest.get("tasks", {})
            if not isinstance(tasks, dict):
                tasks = {}
            manifest_commit = str(manifest.get("git_commit", "")).strip()

        run_commits = set()
        for csv_path in csv_files:
            for c in _csv_git_commits(csv_path):
                run_commits.add(c)
        if len(run_commits) > 1:
            issues.append(
                f"{run_dir.name}: inconsistent git_commit across CSVs: {sorted(run_commits)}"
            )
        if manifest_commit and run_commits:
            mismatch = [
                c for c in sorted(run_commits) if not _same_commit_prefix(c, manifest_commit)
            ]
            if mismatch:
                issues.append(
                    f"{run_dir.name}: run_manifest git_commit ({manifest_commit}) "
                    f"mismatches CSV git_commit values {mismatch}"
                )

        for task_name, pattern in task_to_csv_pattern.items():
            task_csvs = sorted(run_dir.glob(pattern))
            if len(task_csvs) > 1:
                issues.append(
                    f"{run_dir.name}: task={task_name} has multiple CSV files: "
                    f"{[p.name for p in task_csvs]}"
                )
            if not task_csvs:
                continue

            if logs_dir is not None:
                log_path = logs_dir / run_dir.name / f"{task_name}.log"
                if not log_path.exists():
                    issues.append(
                        f"{run_dir.name}: task={task_name} has CSV but missing log file ({log_path})"
                    )

            task_info = tasks.get(task_name, {})
            status = ""
            if isinstance(task_info, dict):
                status = str(task_info.get("status", "")).strip().lower()
            if not status:
                issues.append(
                    f"{run_dir.name}: task={task_name} missing task status in run_manifest."
                )
            elif status != "success":
                issues.append(
                    f"{run_dir.name}: task={task_name} status={status} in run_manifest but CSV exists."
                )

    return issues


def _collect_execution_coverage(
    runs_dir: Path,
    logs_dir: Path | None,
) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    known_tasks = {
        "profile_latency": "profile_latency_*.csv",
        "profile_memory": "profile_memory_*.csv",
        "eval_ppl": "profile_ppl_*.csv",
        "eval_needle": "profile_needle_*.csv",
        "eval_longbench": "profile_longbench_*.csv",
        "eval_ruler": "profile_ruler_*.csv",
    }
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        manifest = _read_json(run_dir / "run_manifest.json") or {}
        task_map = manifest.get("tasks", {}) if isinstance(manifest.get("tasks"), dict) else {}

        observed_tasks = set()
        for task_name, pattern in known_tasks.items():
            if any(run_dir.glob(pattern)):
                observed_tasks.add(task_name)
            if logs_dir is not None and (logs_dir / run_dir.name / f"{task_name}.log").exists():
                observed_tasks.add(task_name)
            if task_name in task_map:
                observed_tasks.add(task_name)
        if not observed_tasks:
            continue

        for task_name in sorted(observed_tasks):
            csv_pattern = known_tasks.get(task_name, "")
            has_csv = bool(csv_pattern and any(run_dir.glob(csv_pattern)))
            log_path = logs_dir / run_dir.name / f"{task_name}.log" if logs_dir is not None else Path("")
            has_log = bool(log_path and log_path.exists())
            log_has_oom = _log_contains_oom(log_path) if has_log else False
            log_has_traceback = _log_contains_traceback(log_path) if has_log else False

            info = task_map.get(task_name, {}) if isinstance(task_map.get(task_name, {}), dict) else {}
            manifest_status = str(info.get("status", "")).strip().lower()
            attempts = pd.to_numeric(info.get("attempts"), errors="coerce")
            returncode = pd.to_numeric(info.get("returncode"), errors="coerce")
            failure_type = str(info.get("failure_type", "")).strip().lower()

            if has_csv and manifest_status == "success":
                execution_state = "success"
            elif failure_type == "oom" or (log_has_oom and not has_csv):
                execution_state = "oom_failure"
            elif log_has_traceback:
                execution_state = "traceback_failure"
            elif has_csv and manifest_status and manifest_status != "success":
                execution_state = "csv_without_success_status"
            elif manifest_status in {"failed", "running"}:
                execution_state = f"{manifest_status}_without_csv"
            elif has_csv:
                execution_state = "csv_without_manifest_status"
            else:
                execution_state = "missing_artifacts"

            rows.append(
                {
                    "run_dir": run_dir.name,
                    "run_name": manifest.get("run_name", ""),
                    "run_tag": manifest.get("run_tag", ""),
                    "kv_mode": manifest.get("kv_mode", ""),
                    "seed": pd.to_numeric(manifest.get("seed"), errors="coerce"),
                    "replica_id": pd.to_numeric(manifest.get("replica_id"), errors="coerce"),
                    "task": task_name,
                    "manifest_status": manifest_status,
                    "attempts": attempts,
                    "returncode": returncode,
                    "failure_type": failure_type,
                    "has_csv": bool(has_csv),
                    "has_log": bool(has_log),
                    "log_has_oom": bool(log_has_oom),
                    "log_has_traceback": bool(log_has_traceback),
                    "log_path": str(log_path) if has_log else "",
                    "execution_state": execution_state,
                }
            )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _build_failure_registry(execution_coverage: pd.DataFrame) -> pd.DataFrame:
    if execution_coverage.empty:
        return pd.DataFrame()
    fail_states = {
        "oom_failure",
        "traceback_failure",
        "csv_without_success_status",
        "running_without_csv",
        "failed_without_csv",
        "csv_without_manifest_status",
    }
    sub = execution_coverage[execution_coverage["execution_state"].isin(fail_states)].copy()
    if sub.empty:
        return pd.DataFrame()

    def _category(state: str) -> str:
        s = str(state)
        if "oom" in s:
            return "oom"
        if "traceback" in s:
            return "traceback"
        if "running" in s:
            return "incomplete"
        if "csv_without" in s:
            return "status_mismatch"
        if "failed" in s:
            return "runtime_failure"
        return "other"

    sub["failure_category"] = sub["execution_state"].map(_category)
    sub["is_throughput_run"] = sub["run_name"].astype(str).str.contains("_throughput_")
    return sub.sort_values(["run_dir", "task"]).reset_index(drop=True)


def _collect_throughput_attempts(runs_dir: Path, logs_dir: Path | None) -> pd.DataFrame:
    """
    Parse attempted throughput runs from runs/<run_dir_name>.
    Expected naming pattern includes: <kv_mode>_throughput_<seq_tag>_b<batch>
    """
    rows = []
    pattern = re.compile(
        r"(?P<kv_mode>[A-Za-z0-9_]+)_throughput_(?P<seq_tag>[0-9]+k?)_b(?P<batch>[0-9]+)"
    )
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        m = pattern.search(run_dir.name)
        if not m:
            continue
        seq_len = _parse_seq_tag_to_len(m.group("seq_tag"))
        if seq_len is None:
            continue
        kv_mode = m.group("kv_mode")
        batch = int(m.group("batch"))
        has_latency_csv = any(run_dir.glob("profile_latency_*.csv"))
        latency_log = (
            logs_dir / run_dir.name / "profile_latency.log"
            if logs_dir is not None
            else Path("")
        )
        has_oom = _log_contains_oom(latency_log) if logs_dir is not None else False
        status = "ok" if has_latency_csv else ("oom" if has_oom else "missing")
        rows.append(
            {
                "run_dir": run_dir.name,
                "kv_mode": kv_mode,
                "seq_len": seq_len,
                "batch": batch,
                "has_latency_csv": bool(has_latency_csv),
                "status": status,
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _build_throughput_capacity_summary(
    lat_batch: pd.DataFrame,
    attempts: pd.DataFrame,
    *,
    target_seq: int,
) -> pd.DataFrame:
    if attempts.empty:
        return pd.DataFrame()

    work_attempts = attempts.copy()
    work_attempts["seq_len"] = pd.to_numeric(work_attempts["seq_len"], errors="coerce")
    work_attempts["batch"] = pd.to_numeric(work_attempts["batch"], errors="coerce")
    work_attempts = work_attempts[work_attempts["seq_len"] == float(target_seq)]
    if work_attempts.empty:
        return pd.DataFrame()

    work_latency = lat_batch.copy()
    if not work_latency.empty and {"kv_mode", "batch"}.issubset(work_latency.columns):
        work_latency["batch"] = pd.to_numeric(work_latency["batch"], errors="coerce")
        work_latency = work_latency.dropna(subset=["batch"])
    else:
        work_latency = pd.DataFrame(columns=["kv_mode", "batch"])

    rows = []
    for kv_mode, sub in _iter_grouped(work_attempts, "kv_mode"):
        attempted_batches = sorted(int(x) for x in sub["batch"].dropna().unique())
        successful_batches = sorted(
            int(x)
            for x in work_latency.loc[work_latency["kv_mode"] == kv_mode, "batch"].dropna().unique()
        )
        missing_batches = sorted(set(attempted_batches) - set(successful_batches))
        oom_batches = sorted(
            int(x) for x in sub.loc[sub["status"] == "oom", "batch"].dropna().unique()
        )
        mode_status = "complete"
        if missing_batches:
            mode_status = "oom_or_missing"
            if set(missing_batches).issubset(set(oom_batches)):
                mode_status = "oom_capacity_limit"
            elif not oom_batches:
                mode_status = "missing_results"
        rows.append(
            {
                "seq_len": target_seq,
                "kv_mode": kv_mode,
                "attempted_batches": _format_batch_list(attempted_batches),
                "successful_batches": _format_batch_list(successful_batches),
                "missing_batches": _format_batch_list(missing_batches),
                "oom_batches": _format_batch_list(oom_batches),
                "max_success_batch": max(successful_batches) if successful_batches else np.nan,
                "first_missing_batch": min(missing_batches) if missing_batches else np.nan,
                "first_oom_batch": min(oom_batches) if oom_batches else np.nan,
                "mode_status": mode_status,
            }
        )
    if not rows:
        return pd.DataFrame()
    return _sort_by_kv_mode(pd.DataFrame(rows))


def _annotate_batch_curve_with_capacity(
    curve_df: pd.DataFrame,
    capacity_df: pd.DataFrame,
) -> pd.DataFrame:
    if curve_df.empty:
        return curve_df
    out = curve_df.copy()
    out["point_status"] = "measured"
    out["status_reason"] = "ok"
    out["capacity_limit_batch"] = np.nan
    out["is_capacity_limit"] = False

    if capacity_df.empty:
        return out

    missing_rows = []
    for _, info in capacity_df.iterrows():
        kv_mode = info.get("kv_mode")
        if not isinstance(kv_mode, str):
            continue
        mode_rows = out[out["kv_mode"] == kv_mode]
        max_success = pd.to_numeric(info.get("max_success_batch"), errors="coerce")
        missing_batches = _parse_batch_list(str(info.get("missing_batches", "")))

        if pd.notna(max_success) and missing_batches and not mode_rows.empty:
            cap_mask = (out["kv_mode"] == kv_mode) & (
                pd.to_numeric(out["batch"], errors="coerce") == float(max_success)
            )
            out.loc[cap_mask, "is_capacity_limit"] = True
            out.loc[cap_mask, "capacity_limit_batch"] = float(max_success)

        if not missing_batches:
            continue

        mode_status = str(info.get("mode_status", "missing"))
        template = mode_rows.iloc[0] if not mode_rows.empty else None
        for batch in missing_batches:
            row = {col: np.nan for col in out.columns}
            row["kv_mode"] = kv_mode
            row["batch"] = batch
            row["point_status"] = "missing"
            row["status_reason"] = mode_status
            row["capacity_limit_batch"] = float(max_success) if pd.notna(max_success) else np.nan
            row["is_capacity_limit"] = False
            if "seq_len" in row:
                row["seq_len"] = info.get("seq_len", np.nan)
            for copy_col in [
                "model_id",
                "hardware",
                "gen_len",
                "group_size",
                "clip_percentile",
            ]:
                if template is not None and copy_col in out.columns:
                    row[copy_col] = template.get(copy_col, np.nan)
            missing_rows.append(row)

    if missing_rows:
        out = pd.concat([out, pd.DataFrame(missing_rows)], ignore_index=True)
    if "batch" in out.columns:
        out = _sort_by_kv_mode(out, extra_cols=["batch"])
    return out


def _plot_batch_with_capacity(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    hue: str,
    title: str,
    xlabel: str,
    ylabel: str,
    out_path: Path,
    yerr: str | None = None,
) -> None:
    if df.empty or y not in df.columns:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plot_df = df.copy()
    plot_df[x] = pd.to_numeric(plot_df[x], errors="coerce")
    plot_df[y] = pd.to_numeric(plot_df[y], errors="coerce")
    plot_df = plot_df.dropna(subset=[x])
    if plot_df.empty:
        return

    measured = plot_df
    if "point_status" in plot_df.columns:
        measured = plot_df[plot_df["point_status"] != "missing"]
    if measured.empty:
        return

    plt.figure(figsize=(8, 5))
    color_map = {}
    for label, sub in _iter_grouped(measured, hue):
        sub = sub.sort_values(x)
        if yerr and yerr in sub.columns:
            # AGG-040: matplotlib plt.errorbar silently skips individual error bars
            # when the corresponding yerr values are NaN (no visual gap or marker is
            # shown for the missing bar). This is matplotlib's built-in behavior and
            # is acceptable here — NaN CI means insufficient replicates for that point.
            cont = plt.errorbar(
                sub[x],
                sub[y],
                yerr=sub[yerr],
                marker="o",
                label=str(label),
                capsize=3,
            )
            try:
                color_map[str(label)] = cont[0].get_color()
            except Exception:
                pass
        else:
            line = plt.plot(sub[x], sub[y], marker="o", label=str(label))
            if line:
                try:
                    color_map[str(label)] = line[0].get_color()
                except Exception:
                    pass

    # Capacity-limit annotation lines.
    if "is_capacity_limit" in measured.columns:
        limits = measured[measured["is_capacity_limit"] == True]
        y_max = pd.to_numeric(measured[y], errors="coerce").max()
        if pd.notna(y_max):
            used_labels = set()
            for idx, row in limits.iterrows():
                mode = str(row.get(hue))
                x_cap = pd.to_numeric(row.get(x), errors="coerce")
                if pd.isna(x_cap):
                    continue
                color = color_map.get(mode, "gray")
                plt.axvline(x_cap, linestyle="--", linewidth=1.0, alpha=0.25, color=color)
                if mode in used_labels:
                    continue
                y_text = y_max * (0.97 - 0.05 * (len(used_labels) % 6))
                plt.text(
                    x_cap,
                    y_text,
                    f"{mode} cap≤{int(x_cap)}",
                    rotation=90,
                    fontsize=8,
                    color=color,
                    ha="right",
                    va="top",
                    alpha=0.75,
                )
                used_labels.add(mode)

    # Missing / OOM markers.
    if {"point_status", "status_reason"}.issubset(plot_df.columns):
        missing = plot_df[plot_df["point_status"] == "missing"]
        for mode, sub_miss in _iter_grouped(missing, hue):
            mode_str = str(mode)
            mode_measured = measured[measured[hue] == mode]
            if mode_measured.empty:
                continue
            anchor = pd.to_numeric(mode_measured[y], errors="coerce").dropna()
            if anchor.empty:
                continue
            anchor_y = float(anchor.iloc[-1])
            color = color_map.get(mode_str, "red")
            for _, row in sub_miss.sort_values(x).iterrows():
                x_miss = pd.to_numeric(row.get(x), errors="coerce")
                if pd.isna(x_miss):
                    continue
                reason = str(row.get("status_reason", "missing")).lower()
                marker_text = "OOM" if "oom" in reason else "MISS"
                marker_color = "red" if marker_text == "OOM" else color
                plt.scatter([x_miss], [anchor_y], marker="x", color=marker_color, s=45, zorder=6)
                plt.text(
                    x_miss,
                    anchor_y,
                    marker_text,
                    fontsize=7,
                    color=marker_color,
                    ha="left",
                    va="bottom",
                )

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def _plot_lines(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: str,
    title: str,
    xlabel: str,
    ylabel: str,
    out_path: Path,
    yerr: str | None = None,
) -> None:
    if df.empty:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    for label, sub in _iter_grouped(df, hue):
        sub = sub.sort_values(x)
        if yerr and yerr in sub.columns:
            # AGG-040: matplotlib plt.errorbar silently skips individual error bars
            # when the corresponding yerr values are NaN (no visual gap or marker is
            # shown for the missing bar). This is matplotlib's built-in behavior and
            # is acceptable here — NaN CI means insufficient replicates for that point.
            plt.errorbar(
                sub[x],
                sub[y],
                yerr=sub[yerr],
                marker="o",
                label=str(label),
                capsize=3,
            )
        else:
            plt.plot(sub[x], sub[y], marker="o", label=str(label))
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def _maybe_filter_batch_gen_len(
    df: pd.DataFrame,
    *,
    batch: int | None = None,
    gen_len: int | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df
    out = df
    if batch is not None and "batch" in out.columns:
        out = out[pd.to_numeric(out["batch"], errors="coerce") == float(batch)]
    if gen_len is not None and "gen_len" in out.columns:
        out = out[pd.to_numeric(out["gen_len"], errors="coerce") == float(gen_len)]
    return out


def _pick_seq_len_for_batch_curves(df: pd.DataFrame, *, preferred: int = 8192) -> int | None:
    if df.empty or "seq_len" not in df.columns or "batch" not in df.columns:
        return None
    tmp = df.copy()
    tmp["seq_len"] = pd.to_numeric(tmp["seq_len"], errors="coerce")
    tmp["batch"] = pd.to_numeric(tmp["batch"], errors="coerce")
    tmp = tmp.dropna(subset=["seq_len", "batch"])
    if tmp.empty:
        return None

    if (tmp["seq_len"] == float(preferred)).any():
        return int(preferred)

    counts = tmp.groupby("seq_len")["batch"].nunique().sort_values(ascending=False)
    if counts.empty:
        return None
    return int(counts.index[0])


def _significance_summary(
    df: pd.DataFrame,
    metric_col: str,
    key_cols: List[str],
    pairings: List[tuple[str, str]],
    metric_name: str,
    *,
    higher_is_better: bool,
    min_pairs: int = 3,
    alpha: float = 0.05,
    ci_level: float = 0.95,
    n_bootstrap: int = 10000,
    n_permutations: int = 20000,
    random_seed: int = 1234,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build publication-grade paired significance summaries.

    Returns:
      (summary_df, paired_rows_df)
    """
    paired = _build_paired_metric_rows(
        df=df,
        metric_col=metric_col,
        key_cols=key_cols,
        pairings=pairings,
        metric_name=metric_name,
        higher_is_better=higher_is_better,
    )
    if paired.empty:
        return pd.DataFrame(), pd.DataFrame()

    keep_keys = [c for c in key_cols if c in paired.columns]
    group_cols = ["metric", "baseline_mode", "challenger_mode"] + keep_keys
    rows = []

    for group_key, sub in paired.groupby(group_cols, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        row = {col: val for col, val in zip(group_cols, group_key)}

        _diff_s = pd.to_numeric(sub["diff"], errors="coerce")
        _gain_s = pd.to_numeric(sub["gain_pct"], errors="coerce")
        # Use a joint mask so diff and gain_pct are based on exactly the same rows.
        _joint_valid = _diff_s.notna() & _gain_s.notna()
        diff = _diff_s[_joint_valid].to_numpy(dtype=np.float64)
        gain = _gain_s[_joint_valid].to_numpy(dtype=np.float64)
        if int(_diff_s.notna().sum()) != int(_joint_valid.sum()):
            logger.warning(
                "gain_pct had %d extra NaN rows vs diff; using joint mask (%d rows) "
                "for consistent sample size.",
                int(_diff_s.notna().sum()) - int(_joint_valid.sum()),
                int(_joint_valid.sum()),
            )
        favorable = pd.to_numeric(sub["favorable_diff"], errors="coerce").dropna().to_numpy(dtype=np.float64)
        base_val = pd.to_numeric(sub["baseline_value"], errors="coerce").dropna().to_numpy(dtype=np.float64)
        chall_val = pd.to_numeric(sub["challenger_value"], errors="coerce").dropna().to_numpy(dtype=np.float64)
        seed_series = pd.to_numeric(sub["seed"], errors="coerce").dropna()

        n_pairs = int(diff.size)
        n_unique_seeds = int(seed_series.nunique())
        dup_groups = int(
            pd.to_numeric(
                sub.get("duplicate_groups_collapsed", pd.Series([0])),
                errors="coerce",
            )
            .fillna(0)
            .max()
        )
        dup_rows = int(
            pd.to_numeric(
                sub.get("duplicate_extra_rows_collapsed", pd.Series([0])),
                errors="coerce",
            )
            .fillna(0)
            .max()
        )

        row["n_pairs"] = n_pairs
        row["n_unique_seeds"] = n_unique_seeds
        row["duplicate_groups_collapsed"] = dup_groups
        row["duplicate_extra_rows_collapsed"] = dup_rows
        row["seed_min"] = float(seed_series.min()) if not seed_series.empty else np.nan
        row["seed_max"] = float(seed_series.max()) if not seed_series.empty else np.nan
        row["higher_is_better"] = bool(higher_is_better)
        row["favorable_direction"] = (
            "challenger > baseline" if higher_is_better else "challenger < baseline"
        )
        row["meets_min_pairs"] = bool(n_pairs >= int(min_pairs))
        if n_pairs < 2:
            row["inference_status"] = "insufficient_pairs_for_test"
        elif n_pairs < int(min_pairs):
            row["inference_status"] = "below_recommended_pairs"
        else:
            row["inference_status"] = "ok"

        row["baseline_mean"] = float(np.mean(base_val)) if base_val.size else np.nan
        row["challenger_mean"] = float(np.mean(chall_val)) if chall_val.size else np.nan
        row["diff_mean"] = float(np.mean(diff)) if n_pairs else np.nan
        row["diff_median"] = float(np.median(diff)) if n_pairs else np.nan
        row["diff_std"] = float(np.std(diff, ddof=1)) if n_pairs > 1 else np.nan
        row["mean_favorable_diff"] = float(np.mean(favorable)) if favorable.size else np.nan
        row["probability_of_superiority"] = (
            float(np.mean(favorable > 0.0) + 0.5 * np.mean(favorable == 0.0))
            if favorable.size
            else np.nan
        )
        row["effect_size_dz"] = _cohens_dz(diff)
        row["favors_challenger"] = bool(row["mean_favorable_diff"] > 0.0) if favorable.size else False

        row["gain_pct_mean"] = float(np.mean(gain)) if gain.size else np.nan
        row["gain_pct_median"] = float(np.median(gain)) if gain.size else np.nan
        row["gain_pct_std"] = float(np.std(gain, ddof=1)) if gain.size > 1 else np.nan

        ci_seed = _stable_random_seed(random_seed, metric_name, *group_key)
        diff_ci_low, diff_ci_high = _bootstrap_ci_mean(
            diff, n_bootstrap=n_bootstrap, ci_level=ci_level, seed=ci_seed
        )
        gain_ci_low, gain_ci_high = _bootstrap_ci_mean(
            gain, n_bootstrap=n_bootstrap, ci_level=ci_level, seed=_stable_random_seed(ci_seed, "gain")
        )
        row["diff_ci95_low"] = diff_ci_low
        row["diff_ci95_high"] = diff_ci_high
        row["gain_pct_ci95_low"] = gain_ci_low
        row["gain_pct_ci95_high"] = gain_ci_high

        p_value, p_method, permutation_samples = _paired_signflip_pvalue(
            diff,
            n_permutations=n_permutations,
            seed=_stable_random_seed(ci_seed, "perm"),
        )
        row["p_value"] = p_value
        row["p_method"] = p_method
        row["permutation_samples"] = int(permutation_samples)
        row["bootstrap_samples"] = int(n_bootstrap) if n_pairs >= 2 else 0
        row["alpha"] = float(alpha)
        row["ci_level"] = float(ci_level)
        rows.append(row)

    if not rows:
        return pd.DataFrame(), pd.DataFrame()
    summary = pd.DataFrame(rows)
    return summary, paired


def _build_paired_metric_rows(
    *,
    df: pd.DataFrame,
    metric_col: str,
    key_cols: List[str],
    pairings: List[tuple[str, str]],
    metric_name: str,
    higher_is_better: bool,
) -> pd.DataFrame:
    if df.empty or metric_col not in df.columns:
        return pd.DataFrame()
    if "kv_mode" not in df.columns:
        return pd.DataFrame()

    work = df.copy()
    if "seed" not in work.columns and "run_id" in work.columns:
        work["seed"] = work["run_id"].map(_extract_seed_from_run_id)
    work["seed"] = pd.to_numeric(work.get("seed"), errors="coerce")
    work[metric_col] = pd.to_numeric(work[metric_col], errors="coerce")
    work = work.dropna(subset=["seed", metric_col])
    if work.empty:
        return pd.DataFrame()

    keys = [c for c in key_cols if c in work.columns]
    # AGG-037: explicitly warn when key_cols specifies columns absent from the
    # DataFrame (e.g. "model_id") — silent filtering can mask grouping errors.
    _dropped_key_cols = [c for c in key_cols if c not in work.columns]
    if _dropped_key_cols:
        logger.warning(
            "_build_paired_metric_rows: key_cols %r are specified but missing "
            "from DataFrame columns; they will be silently ignored for grouping. "
            "This may cause incorrect pairing if multiple values exist for the "
            "missing columns.  metric=%s",
            _dropped_key_cols,
            metric_name,
        )
    rows: List[pd.DataFrame] = []
    for base_mode, challenger_mode in pairings:
        sub = work[work["kv_mode"].isin([base_mode, challenger_mode])]
        if sub.empty:
            continue
        dup_groups, dup_rows = _count_duplicate_groups(sub, keys + ["seed", "kv_mode"])
        if dup_groups > 0:
            logger.warning(
                "Significance pairing collapsed duplicate rows by mean "
                "(metric=%s, base=%s, challenger=%s, "
                "duplicate_groups=%d, duplicate_extra_rows=%d).",
                metric_name, base_mode, challenger_mode, dup_groups, dup_rows,
            )
        pivot = sub.pivot_table(
            index=keys + ["seed"],
            columns="kv_mode",
            values=metric_col,
            aggfunc="mean",
        )
        if base_mode not in pivot.columns or challenger_mode not in pivot.columns:
            continue
        pivot = pivot.dropna(subset=[base_mode, challenger_mode], how="any").reset_index()
        if pivot.empty:
            continue

        baseline = pd.to_numeric(pivot[base_mode], errors="coerce")
        challenger = pd.to_numeric(pivot[challenger_mode], errors="coerce")
        diff = challenger - baseline
        favorable_diff = diff if higher_is_better else -diff
        denom = baseline.abs().replace(0.0, np.nan)
        if higher_is_better:
            gain_pct = ((challenger - baseline) / denom) * 100.0
        else:
            gain_pct = ((baseline - challenger) / denom) * 100.0

        paired = pivot[keys + ["seed"]].copy()
        paired["metric"] = metric_name
        paired["baseline_mode"] = base_mode
        paired["challenger_mode"] = challenger_mode
        paired["baseline_value"] = baseline
        paired["challenger_value"] = challenger
        paired["diff"] = diff
        paired["favorable_diff"] = favorable_diff
        paired["gain_pct"] = gain_pct
        paired["duplicate_groups_collapsed"] = int(dup_groups)
        paired["duplicate_extra_rows_collapsed"] = int(dup_rows)
        rows.append(paired)

    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    out = _to_numeric(
        out,
        ["seed", "baseline_value", "challenger_value", "diff", "favorable_diff", "gain_pct"],
    )
    out = out.dropna(
        subset=["seed", "baseline_value", "challenger_value", "diff", "favorable_diff"]
    )
    return out.reset_index(drop=True)


# AGG-012: seed is derived from SHA256 hash of string inputs, providing deterministic but well-distributed seeds across different (metric, kv_mode) combinations.
def _stable_random_seed(base_seed: int, *parts: object) -> int:
    txt = "||".join(str(p) for p in parts)
    digest = hashlib.sha256(txt.encode("utf-8")).hexdigest()
    offset = int(digest[:8], 16)
    return int((int(base_seed) + offset) % (2**32 - 1))


def _bootstrap_ci_mean(
    values: np.ndarray,
    *,
    n_bootstrap: int,
    ci_level: float,
    seed: int,
) -> Tuple[float, float]:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    n = int(arr.size)
    if n <= 0:
        return np.nan, np.nan
    if n == 1:
        # AGG-014: single-sample CI returns identical bounds -- caller
        # (_add_ci95_columns) already handles n<=1 by setting NaN.
        return float(arr[0]), float(arr[0])

    ci = float(ci_level)
    if not (0.0 < ci < 1.0):
        ci = 0.95
    n_bs = max(1000, int(n_bootstrap))
    rng = np.random.default_rng(int(seed))
    sample_idx = rng.integers(0, n, size=(n_bs, n))
    means = arr[sample_idx].mean(axis=1)
    alpha = 1.0 - ci
    low = float(np.quantile(means, alpha / 2.0))
    high = float(np.quantile(means, 1.0 - alpha / 2.0))
    return low, high


def _paired_signflip_pvalue(
    values: np.ndarray,
    *,
    n_permutations: int,
    seed: int,
) -> Tuple[float, str, int]:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    n = int(arr.size)
    if n < 2:
        return np.nan, "insufficient_pairs", 0

    # AGG-031: This is a two-tailed test (using |mean|).  When combined with the
    # downstream `favors_challenger` direction check, the effective significance
    # threshold is 2× conservative compared to a one-tailed test (p_one = p_two/2).
    # This is an intentional design choice: being conservative is preferred in a
    # research paper context.  If a true one-tailed test is needed later, halve
    # the returned p-value at the call site rather than changing this function.
    observed = abs(float(np.mean(arr)))
    if observed == 0.0:
        return 1.0, "zero_effect", 0

    # Exact paired sign-flip test for small n; MC approximation for larger n.
    if n <= _EXACT_ENUM_THRESHOLD:
        n_enum = 1 << n
        idx = np.arange(n_enum, dtype=np.uint32)[:, None]
        bits = ((idx >> np.arange(n, dtype=np.uint32)) & 1).astype(np.int8)
        signs = bits * 2 - 1
        perm_means = np.abs((signs * arr[None, :]).mean(axis=1))
        exceed = int(np.count_nonzero(perm_means >= (observed - 1e-12)))
        p_value = float((exceed + 1) / (n_enum + 1))
        return p_value, "exact_signflip", int(n_enum)

    n_perm = max(2000, int(n_permutations))
    rng = np.random.default_rng(int(seed))
    signs = rng.choice(np.array([-1.0, 1.0], dtype=np.float64), size=(n_perm, n), replace=True)
    perm_means = np.abs((signs * arr[None, :]).mean(axis=1))
    exceed = int(np.count_nonzero(perm_means >= (observed - 1e-12)))
    p_value = float((exceed + 1) / (n_perm + 1))
    return p_value, "mc_signflip", int(n_perm)


def _cohens_dz(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if arr.size < 2:
        return np.nan
    std = float(np.std(arr, ddof=1))
    if std <= 0.0:
        return np.nan
    return float(np.mean(arr) / std)


def _add_bh_fdr_qvalues(
    df: pd.DataFrame,
    *,
    p_col: str = "p_value",
    q_col: str = "q_value",
) -> pd.DataFrame:
    if df.empty or p_col not in df.columns:
        return df
    out = df.copy()
    p = pd.to_numeric(out[p_col], errors="coerce").to_numpy(dtype=np.float64)
    q = np.full_like(p, np.nan, dtype=np.float64)
    valid = np.isfinite(p) & (p >= 0.0) & (p <= 1.0)
    m = int(np.count_nonzero(valid))
    if m <= 0:
        out[q_col] = q
        return out
    valid_idx = np.where(valid)[0]
    p_valid = p[valid_idx]
    order = np.argsort(p_valid)
    ranked = p_valid[order]
    ranks = np.arange(1, m + 1, dtype=np.float64)
    adjusted = ranked * (float(m) / ranks)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    q[valid_idx[order]] = adjusted
    out[q_col] = q
    return out


def _relative_gain_table(
    df: pd.DataFrame,
    *,
    metric_col: str,
    metric_name: str,
    key_cols: List[str],
    pairings: List[tuple[str, str]],
    higher_is_better: bool,
) -> pd.DataFrame:
    """
    Build relative-gain table for selected mode pairings on aggregated summaries.
    gain_pct > 0 means challenger is better than baseline under the metric direction.
    """
    if df.empty or metric_col not in df.columns or "kv_mode" not in df.columns:
        return pd.DataFrame()
    keep = [c for c in key_cols if c in df.columns]
    sub = df[keep + ["kv_mode", metric_col]].copy()
    sub[metric_col] = pd.to_numeric(sub[metric_col], errors="coerce")
    sub = sub.dropna(subset=[metric_col])
    if sub.empty:
        return pd.DataFrame()
    dup_groups, dup_rows = _count_duplicate_groups(sub, keep + ["kv_mode"])
    if dup_groups > 0:
        logger.warning(
            "Relative gain aggregation collapsed duplicate rows by mean "
            "(metric=%s, duplicate_groups=%d, duplicate_extra_rows=%d).",
            metric_name, dup_groups, dup_rows,
        )

    pivot = sub.pivot_table(index=keep, columns="kv_mode", values=metric_col, aggfunc="mean")
    out_frames: List[pd.DataFrame] = []
    for baseline, challenger in pairings:
        if baseline not in pivot.columns or challenger not in pivot.columns:
            continue
        tmp = pivot[[baseline, challenger]].dropna().reset_index()
        if tmp.empty:
            continue
        base_val = pd.to_numeric(tmp[baseline], errors="coerce")
        chall_val = pd.to_numeric(tmp[challenger], errors="coerce")
        delta_abs = chall_val - base_val
        denom = base_val.abs().replace(0, np.nan)
        delta_pct = (delta_abs / denom) * 100.0
        if higher_is_better:
            gain_pct = delta_pct
        else:
            gain_pct = ((base_val - chall_val) / denom) * 100.0

        row = tmp[keep].copy()
        row["metric"] = metric_name
        row["baseline_mode"] = baseline
        row["challenger_mode"] = challenger
        row["baseline_value"] = base_val
        row["challenger_value"] = chall_val
        row["delta_abs"] = delta_abs
        row["delta_pct"] = delta_pct
        row["gain_pct"] = gain_pct
        row["duplicate_groups_collapsed"] = int(dup_groups)
        row["duplicate_extra_rows_collapsed"] = int(dup_rows)
        out_frames.append(row)

    if not out_frames:
        return pd.DataFrame()
    return pd.concat(out_frames, ignore_index=True)


def _main_claims_32k_table(
    latency_summary: pd.DataFrame,
    memory_summary: pd.DataFrame,
    needle_summary: pd.DataFrame,
    ppl_summary: pd.DataFrame,
    longbench_summary: pd.DataFrame,
    ruler_summary: pd.DataFrame,
    *,
    target_seq_len: int = 32704,
) -> pd.DataFrame:
    """
    Build a one-glance thesis claim table at 32K context (or nearest available point).
    """
    def _pick_seq(df: pd.DataFrame, preferred: int) -> int | None:
        if df.empty or "seq_len" not in df.columns:
            return None
        seq = pd.to_numeric(df["seq_len"], errors="coerce").dropna()
        if seq.empty:
            return None
        if (seq == float(preferred)).any():
            return int(preferred)
        return int(seq.max())

    lat = latency_summary.copy()
    mem = memory_summary.copy()
    ned = needle_summary.copy()
    ppl = ppl_summary.copy()
    lb = longbench_summary.copy()
    rul = ruler_summary.copy()

    lat_seq = _pick_seq(lat, target_seq_len)
    mem_seq = _pick_seq(mem, target_seq_len)
    ned_seq = _pick_seq(ned, target_seq_len)
    lb_seq = _pick_seq(lb, target_seq_len)
    rul_seq = _pick_seq(rul, target_seq_len)
    if lat_seq is None and mem_seq is None and ned_seq is None and lb_seq is None and rul_seq is None:
        return pd.DataFrame()

    if not lat.empty and "batch" in lat.columns:
        lat = lat[pd.to_numeric(lat["batch"], errors="coerce") == 1]
    if not lat.empty and "gen_len" in lat.columns:
        gen = pd.to_numeric(lat["gen_len"], errors="coerce")
        if (gen == 64).any():
            lat = lat[gen == 64]
    if lat_seq is not None and "seq_len" in lat.columns:
        lat = lat[pd.to_numeric(lat["seq_len"], errors="coerce") == float(lat_seq)]

    if not mem.empty and "batch" in mem.columns:
        mem = mem[pd.to_numeric(mem["batch"], errors="coerce") == 1]
    if not mem.empty and "gen_len" in mem.columns:
        gen = pd.to_numeric(mem["gen_len"], errors="coerce")
        if (gen == 64).any():
            mem = mem[gen == 64]
    if mem_seq is not None and "seq_len" in mem.columns:
        mem = mem[pd.to_numeric(mem["seq_len"], errors="coerce") == float(mem_seq)]

    if ned_seq is not None and "seq_len" in ned.columns:
        ned = ned[pd.to_numeric(ned["seq_len"], errors="coerce") == float(ned_seq)]
    if lb_seq is not None and "seq_len" in lb.columns:
        lb = lb[pd.to_numeric(lb["seq_len"], errors="coerce") == float(lb_seq)]
    if rul_seq is not None and "seq_len" in rul.columns:
        rul = rul[pd.to_numeric(rul["seq_len"], errors="coerce") == float(rul_seq)]

    # PPL: choose kv_cache row with maximal tokens_evaluated for each mode.
    if not ppl.empty and "ppl_mode" in ppl.columns:
        ppl = ppl[ppl["ppl_mode"] == "kv_cache"]
    # Determine merge keys: include model_id when available to avoid cartesian product.
    _has_mid = "model_id" in lat.columns or "model_id" in mem.columns
    merge_keys = ["model_id", "kv_mode"] if _has_mid else ["kv_mode"]
    if not ppl.empty and "tokens_evaluated_mean" in ppl.columns:
        dedup_cols = [c for c in merge_keys if c in ppl.columns]
        ppl = (
            ppl.sort_values("tokens_evaluated_mean", ascending=False)
            .drop_duplicates(subset=dedup_cols, keep="first")
        )

    _id_prefix = ["model_id"] if _has_mid else []
    lat_cols = [c for c in _id_prefix + ["kv_mode", "tpot_ms_mean", "ttft_ms_mean", "tok_per_s_mean"] if c in lat.columns]
    mem_cols = [c for c in _id_prefix + ["kv_mode", "gpu_mem_peak_mb_mean", "kv_cache_mem_mb_mean"] if c in mem.columns]
    ned_cols = [c for c in _id_prefix + ["kv_mode", "needle_pass_rate_mean", "needle_exact_match_rate_mean"] if c in ned.columns]
    ppl_cols = [c for c in _id_prefix + ["kv_mode", "perplexity_mean", "tokens_evaluated_mean"] if c in ppl.columns]
    lb_cols = [
        c
        for c in _id_prefix + [
            "kv_mode",
            "longbench_score_mean",
            "longbench_f1_macro_mean",
            "longbench_em_macro_mean",
            "longbench_contains_macro_mean",
        ]
        if c in lb.columns
    ]
    rul_cols = [
        c
        for c in _id_prefix + [
            "kv_mode",
            "ruler_pass_rate_mean",
            "ruler_f1_mean_mean",
            "ruler_contains_rate_mean",
        ]
        if c in rul.columns
    ]

    if not lat_cols or not mem_cols:
        missing = []
        if not lat_cols:
            missing.append("latency")
        if not mem_cols:
            missing.append("memory")
        logger.warning(
            "_main_claims_32k_table: returning empty DataFrame because %s "
            "columns are missing or empty.",
            " and ".join(missing),
        )
        return pd.DataFrame()

    # AGG-041: renamed merge key variables from cryptic _mk/_nk/_pk/_lk/_rk to
    # descriptive names so intent is clear at each merge site.
    memory_merge_keys = [c for c in merge_keys if c in lat.columns and c in mem.columns]
    if not memory_merge_keys:
        # AGG-035: warn when falling back to ["kv_mode"] to surface potential Cartesian products
        logger.warning(
            "_main_claims_32k_table: latency-memory merge key fallback to ['kv_mode'] "
            "(merge_keys=%s not found in both DataFrames); Cartesian product possible.",
            merge_keys,
        )
        memory_merge_keys = ["kv_mode"]
    out = lat[lat_cols].copy()
    _pre_merge_rows = len(out)
    if mem_cols:
        out = out.merge(mem[mem_cols], on=memory_merge_keys, how="outer")
    if ned_cols:
        needle_merge_keys = [c for c in merge_keys if c in out.columns and c in ned[ned_cols].columns]
        if not needle_merge_keys:
            logger.warning(
                "_main_claims_32k_table: needle merge key fallback to ['kv_mode'] "
                "(merge_keys=%s not found); Cartesian product possible.",
                merge_keys,
            )
            needle_merge_keys = ["kv_mode"]
        out = out.merge(ned[ned_cols], on=needle_merge_keys, how="outer")
    if ppl_cols:
        ppl_merge_keys = [c for c in merge_keys if c in out.columns and c in ppl[ppl_cols].columns]
        if not ppl_merge_keys:
            logger.warning(
                "_main_claims_32k_table: ppl merge key fallback to ['kv_mode'] "
                "(merge_keys=%s not found); Cartesian product possible.",
                merge_keys,
            )
            ppl_merge_keys = ["kv_mode"]
        out = out.merge(ppl[ppl_cols], on=ppl_merge_keys, how="left")
    if lb_cols:
        longbench_merge_keys = [c for c in merge_keys if c in out.columns and c in lb[lb_cols].columns]
        if not longbench_merge_keys:
            logger.warning(
                "_main_claims_32k_table: longbench merge key fallback to ['kv_mode'] "
                "(merge_keys=%s not found); Cartesian product possible.",
                merge_keys,
            )
            longbench_merge_keys = ["kv_mode"]
        out = out.merge(lb[lb_cols], on=longbench_merge_keys, how="left")
    if rul_cols:
        ruler_merge_keys = [c for c in merge_keys if c in out.columns and c in rul[rul_cols].columns]
        if not ruler_merge_keys:
            logger.warning(
                "_main_claims_32k_table: ruler merge key fallback to ['kv_mode'] "
                "(merge_keys=%s not found); Cartesian product possible.",
                merge_keys,
            )
            ruler_merge_keys = ["kv_mode"]
        out = out.merge(rul[rul_cols], on=ruler_merge_keys, how="left")

    _post_merge_rows = len(out)
    if _post_merge_rows > _pre_merge_rows * 2:
        logger.warning(
            "_main_claims_32k_table: merge expanded rows from %d to %d "
            "(>2x), possible ghost rows from mismatched keys.",
            _pre_merge_rows,
            _post_merge_rows,
        )
    elif _post_merge_rows != _pre_merge_rows:
        logger.info(
            "_main_claims_32k_table: row count changed from %d to %d after merges.",
            _pre_merge_rows,
            _post_merge_rows,
        )

    out["claim_seq_len"] = int(
        lat_seq or mem_seq or ned_seq or lb_seq or rul_seq or target_seq_len
    )
    out = _sort_by_kv_mode(out)
    return out


def _speedup_vs_reference(
    df: pd.DataFrame,
    *,
    metric_col: str,
    reference_mode: str,
    key_cols: List[str],
    higher_is_better: bool = False,
) -> pd.DataFrame:
    """
    Compute relative speedup/gain vs reference mode for each kv_mode and key.
    """
    if df.empty or metric_col not in df.columns or "kv_mode" not in df.columns:
        return pd.DataFrame()
    keep = [c for c in key_cols if c in df.columns]
    sub = df[keep + ["kv_mode", metric_col]].copy()
    sub[metric_col] = pd.to_numeric(sub[metric_col], errors="coerce")
    sub = sub.dropna(subset=[metric_col])
    if sub.empty:
        return pd.DataFrame()
    dup_groups, dup_rows = _count_duplicate_groups(sub, keep + ["kv_mode"])
    if dup_groups > 0:
        logger.warning(
            "Speedup aggregation collapsed duplicate rows by mean "
            "(metric=%s, duplicate_groups=%d, duplicate_extra_rows=%d).",
            metric_col, dup_groups, dup_rows,
        )
    pivot = sub.pivot_table(index=keep, columns="kv_mode", values=metric_col, aggfunc="mean")
    if reference_mode not in pivot.columns:
        return pd.DataFrame()
    ref = pd.to_numeric(pivot[reference_mode], errors="coerce")
    denom = ref.abs().replace(0, np.nan)

    rows: List[pd.DataFrame] = []
    for mode in pivot.columns:
        if mode == reference_mode:
            continue
        val = pd.to_numeric(pivot[mode], errors="coerce")
        if higher_is_better:
            gain = ((val - ref) / denom) * 100.0
        else:
            gain = ((ref - val) / denom) * 100.0
        tmp = gain.reset_index(name="gain_pct")
        tmp["reference_mode"] = reference_mode
        tmp["challenger_mode"] = mode
        tmp["metric"] = metric_col
        tmp["duplicate_groups_collapsed"] = int(dup_groups)
        tmp["duplicate_extra_rows_collapsed"] = int(dup_rows)
        rows.append(tmp)

    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate results into tables and plots")
    parser.add_argument("--runs_dir", type=str, default="results/runs")
    parser.add_argument("--tables_dir", type=str, default="results/tables")
    parser.add_argument("--plots_dir", type=str, default="results/plots")
    parser.add_argument(
        "--logs_dir",
        type=str,
        default="",
        help="Optional logs directory for OOM/missing annotation (default: sibling of runs_dir).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help=(
            "Enable strict data-quality gates. Fails on Traceback/OOM mixed runs "
            "and missing seed values."
        ),
    )
    parser.add_argument(
        "--significance_min_pairs",
        type=int,
        default=3,
        help=(
            "Minimum paired seeds required for significance claims. "
            "Rows below this threshold are marked as low-confidence."
        ),
    )
    parser.add_argument(
        "--significance_alpha",
        type=float,
        default=0.05,
        help="Alpha threshold for p/q significance flags.",
    )
    parser.add_argument(
        "--significance_ci_level",
        type=float,
        default=0.95,
        help="Confidence level used for bootstrap intervals.",
    )
    parser.add_argument(
        "--significance_bootstrap",
        type=int,
        default=10000,
        help="Number of bootstrap resamples per significance row.",
    )
    parser.add_argument(
        "--significance_permutations",
        type=int,
        default=20000,
        help=f"Number of sign-flip permutations for Monte Carlo tests when n>{_EXACT_ENUM_THRESHOLD}.",
    )
    parser.add_argument(
        "--significance_seed",
        type=int,
        default=1234,
        help="Base RNG seed for deterministic bootstrap/permutation statistics.",
    )
    args = parser.parse_args()

    # AGG-034: configure logging so all logger.warning/info calls produce output
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    runs_dir = Path(args.runs_dir)
    tables_dir = Path(args.tables_dir)
    plots_dir = Path(args.plots_dir)
    logs_dir: Path | None = None
    if args.logs_dir:
        logs_dir = Path(args.logs_dir)
    else:
        sibling_logs = runs_dir.parent / "logs"
        if sibling_logs.exists():
            logs_dir = sibling_logs

    if not runs_dir.exists():
        print(f"runs_dir not found: {runs_dir}")
        return 2

    if args.strict:
        strict_issues = []
        strict_issues.extend(_strict_manifest_and_artifact_checks(runs_dir, logs_dir))
        strict_issues.extend(_strict_log_failures(runs_dir, logs_dir))
        if strict_issues:
            _print_strict_issues(strict_issues)
            return 2

    execution_coverage = _collect_execution_coverage(runs_dir, logs_dir)
    if not execution_coverage.empty:
        _save_table(execution_coverage, tables_dir / "execution_coverage.csv")
        failure_registry = _build_failure_registry(execution_coverage)
        if not failure_registry.empty:
            _save_table(failure_registry, tables_dir / "failure_registry.csv")

    throughput_attempts = _collect_throughput_attempts(runs_dir, logs_dir)
    throughput_capacity_summary = pd.DataFrame()

    # Latency
    latency = _read_csvs(runs_dir, ["profile_latency_*.csv"])
    latency = _to_numeric(
        latency,
        [
            "seq_len",
            "gen_len",
            "batch",
            "ttft_ms",
            "tpot_ms",
            "tok_per_s",
            "tok_per_s_per_seq",
            "gpu_mem_peak_mb",
            "kv_cache_mem_mb",
            "kv_cache_seq_len",
            "prefill_tok_per_s",
        ],
    )
    if "seed" not in latency.columns and "run_id" in latency.columns:
        latency["seed"] = latency["run_id"].map(_extract_seed_from_run_id)
    latency = _to_numeric(latency, ["seed"])
    if args.strict:
        strict_issues = _strict_missing_seed(latency, table_name="latency")
        if strict_issues:
            _print_strict_issues(strict_issues)
            return 2
    latency_keys = [
        c
        for c in [
            "model_id",
            "hardware",
            "kv_mode",
            "seq_len",
            "gen_len",
            "batch",
            "group_size",
            "clip_percentile",
        ]
        if c in latency.columns
    ]
    latency_summary = _agg_mean_std(
        latency,
        latency_keys,
        [
            "ttft_ms",
            "tpot_ms",
            "tok_per_s",
            "tok_per_s_per_seq",
            "gpu_mem_peak_mb",
            "kv_cache_mem_mb",
            "kv_cache_seq_len",
            "prefill_tok_per_s",
        ],
    )
    if not latency_summary.empty:
        latency_summary = _add_ci95_columns(latency_summary)
        # AGG-009: ensure canonical kv_mode ordering in output table.
        latency_summary = _sort_by_kv_mode(latency_summary, extra_cols=["seq_len", "gen_len", "batch"])
        _save_table(latency_summary, tables_dir / "latency_summary.csv")
        lat_seq = _maybe_filter_batch_gen_len(latency_summary, batch=1, gen_len=64)
        if "seq_len" in lat_seq.columns and "tpot_ms_mean" in lat_seq.columns:
            _plot_lines(
                lat_seq,
                x="seq_len",
                y="tpot_ms_mean",
                hue="kv_mode",
                title="TPOT vs Seq Len",
                xlabel="Sequence length (tokens)",
                ylabel="TPOT (ms, mean)",
                out_path=plots_dir / "latency_tpot_vs_seq.png",
                yerr="tpot_ms_ci95_half",
            )

        # Batch throughput curve (throughput vs batch).
        target_seq = _pick_seq_len_for_batch_curves(latency_summary, preferred=8192)
        if target_seq is not None and {"batch", "tok_per_s_mean", "kv_mode"}.issubset(latency_summary.columns):
            lat_batch = latency_summary[latency_summary["seq_len"] == target_seq]
            if "gen_len" in lat_batch.columns and (lat_batch["gen_len"] == 128).any():
                lat_batch = lat_batch[lat_batch["gen_len"] == 128]
            if not lat_batch.empty:
                capacity_summary = _build_throughput_capacity_summary(
                    lat_batch,
                    throughput_attempts,
                    target_seq=target_seq,
                )
                throughput_capacity_summary = capacity_summary
                if not capacity_summary.empty:
                    _save_table(capacity_summary, tables_dir / "throughput_capacity_limits.csv")
                lat_batch_annotated = _annotate_batch_curve_with_capacity(
                    lat_batch,
                    capacity_summary,
                )
                _save_table(lat_batch_annotated, tables_dir / "throughput_by_batch.csv")
                _plot_batch_with_capacity(
                    lat_batch_annotated,
                    x="batch",
                    y="tok_per_s_mean",
                    hue="kv_mode",
                    title=f"Throughput vs Batch (seq_len={target_seq})",
                    xlabel="Batch size",
                    ylabel="Tokens per second (total, mean)",
                    out_path=plots_dir / "throughput_tok_per_s_vs_batch.png",
                    yerr="tok_per_s_ci95_half",
                )
                if "tok_per_s_per_seq_mean" in lat_batch.columns:
                    _plot_batch_with_capacity(
                        lat_batch_annotated,
                        x="batch",
                        y="tok_per_s_per_seq_mean",
                        hue="kv_mode",
                        title=f"Throughput per Sequence vs Batch (seq_len={target_seq})",
                        xlabel="Batch size",
                        ylabel="Tokens/s/seq (mean)",
                        out_path=plots_dir / "throughput_tok_per_s_per_seq_vs_batch.png",
                        yerr="tok_per_s_per_seq_ci95_half",
                    )

                if "prefill_tok_per_s_mean" in lat_batch.columns:
                    _plot_batch_with_capacity(
                        lat_batch_annotated,
                        x="batch",
                        y="prefill_tok_per_s_mean",
                        hue="kv_mode",
                        title=f"Prefill Throughput vs Batch (seq_len={target_seq})",
                        xlabel="Batch size",
                        ylabel="Prefill tokens/s (mean)",
                        out_path=plots_dir / "prefill_tok_per_s_vs_batch.png",
                        yerr="prefill_tok_per_s_ci95_half",
                    )
        # Relative TPOT gain vs FP16 (batch=1, curve points).
        tpot_gain = _speedup_vs_reference(
            _maybe_filter_batch_gen_len(latency_summary, batch=1, gen_len=64),
            metric_col="tpot_ms_mean",
            reference_mode="fp16",
            key_cols=["seq_len", "gen_len", "batch"],
            higher_is_better=False,
        )
        if not tpot_gain.empty and {"seq_len", "gain_pct", "challenger_mode"}.issubset(tpot_gain.columns):
            _save_table(tpot_gain, tables_dir / "latency_tpot_gain_vs_fp16.csv")
            _plot_lines(
                tpot_gain,
                x="seq_len",
                y="gain_pct",
                hue="challenger_mode",
                title="TPOT Gain vs FP16",
                xlabel="Sequence length (tokens)",
                ylabel="Gain vs FP16 (%)",
                out_path=plots_dir / "latency_tpot_gain_vs_fp16.png",
            )

    # Memory
    memory = _read_csvs(runs_dir, ["profile_memory_*.csv"])
    memory = _to_numeric(
        memory,
        [
            "seq_len",
            "gen_len",
            "batch",
            "gpu_mem_peak_mb",
            "kv_cache_mem_mb",
            "kv_cache_seq_len",
            "torch_peak_mb",
            "nvml_peak_mb",
            "tok_per_s",
            "tok_per_s_per_seq",
        ],
    )
    if "seed" not in memory.columns and "run_id" in memory.columns:
        memory["seed"] = memory["run_id"].map(_extract_seed_from_run_id)
    memory = _to_numeric(memory, ["seed"])
    if args.strict:
        strict_issues = _strict_missing_seed(memory, table_name="memory")
        if strict_issues:
            _print_strict_issues(strict_issues)
            return 2
    memory_keys = [
        c
        for c in [
            "model_id",
            "hardware",
            "kv_mode",
            "seq_len",
            "gen_len",
            "batch",
            "group_size",
            "clip_percentile",
        ]
        if c in memory.columns
    ]
    memory_summary = _agg_mean_std(
        memory,
        memory_keys,
        ["gpu_mem_peak_mb", "kv_cache_mem_mb", "kv_cache_seq_len", "torch_peak_mb", "nvml_peak_mb"],
    )
    if not memory_summary.empty:
        memory_summary = _add_ci95_columns(memory_summary)
        # AGG-009: ensure canonical kv_mode ordering in output table.
        memory_summary = _sort_by_kv_mode(memory_summary, extra_cols=["seq_len", "gen_len", "batch"])
        _save_table(memory_summary, tables_dir / "memory_summary.csv")
        mem_seq = _maybe_filter_batch_gen_len(memory_summary, batch=1, gen_len=64)
        if "seq_len" in mem_seq.columns and "gpu_mem_peak_mb_mean" in mem_seq.columns:
            _plot_lines(
                mem_seq,
                x="seq_len",
                y="gpu_mem_peak_mb_mean",
                hue="kv_mode",
                title="Peak GPU Memory vs Seq Len",
                xlabel="Sequence length (tokens)",
                ylabel="Peak GPU memory (MB, mean)",
                out_path=plots_dir / "memory_peak_vs_seq.png",
                yerr="gpu_mem_peak_mb_ci95_half",
            )
        if "seq_len" in mem_seq.columns and "kv_cache_mem_mb_mean" in mem_seq.columns:
            _plot_lines(
                mem_seq,
                x="seq_len",
                y="kv_cache_mem_mb_mean",
                hue="kv_mode",
                title="KV Cache Resident Memory vs Seq Len",
                xlabel="Sequence length (tokens)",
                ylabel="KV cache memory (MB, mean)",
                out_path=plots_dir / "memory_kv_cache_vs_seq.png",
                yerr="kv_cache_mem_mb_ci95_half",
            )

        target_seq = _pick_seq_len_for_batch_curves(memory_summary, preferred=8192)
        if target_seq is not None and {"batch", "gpu_mem_peak_mb_mean", "kv_mode"}.issubset(memory_summary.columns):
            mem_batch = memory_summary[memory_summary["seq_len"] == target_seq]
            if "gen_len" in mem_batch.columns and (mem_batch["gen_len"] == 128).any():
                mem_batch = mem_batch[mem_batch["gen_len"] == 128]
            if not mem_batch.empty:
                mem_batch_annotated = _annotate_batch_curve_with_capacity(
                    mem_batch,
                    throughput_capacity_summary,
                )
                _plot_batch_with_capacity(
                    mem_batch_annotated,
                    x="batch",
                    y="gpu_mem_peak_mb_mean",
                    hue="kv_mode",
                    title=f"Peak GPU Memory vs Batch (seq_len={target_seq})",
                    xlabel="Batch size",
                    ylabel="Peak GPU memory (MB, mean)",
                    out_path=plots_dir / "memory_peak_vs_batch.png",
                    yerr="gpu_mem_peak_mb_ci95_half",
                )
        if target_seq is not None and {"batch", "kv_cache_mem_mb_mean", "kv_mode"}.issubset(memory_summary.columns):
            mem_batch = memory_summary[memory_summary["seq_len"] == target_seq]
            if "gen_len" in mem_batch.columns and (mem_batch["gen_len"] == 128).any():
                mem_batch = mem_batch[mem_batch["gen_len"] == 128]
            if not mem_batch.empty:
                mem_batch_annotated = _annotate_batch_curve_with_capacity(
                    mem_batch,
                    throughput_capacity_summary,
                )
                _plot_batch_with_capacity(
                    mem_batch_annotated,
                    x="batch",
                    y="kv_cache_mem_mb_mean",
                    hue="kv_mode",
                    title=f"KV Cache Memory vs Batch (seq_len={target_seq})",
                    xlabel="Batch size",
                    ylabel="KV cache memory (MB, mean)",
                    out_path=plots_dir / "memory_kv_cache_vs_batch.png",
                    yerr="kv_cache_mem_mb_ci95_half",
                )

    # PPL
    ppl = _read_csvs(runs_dir, ["profile_ppl_*.csv"])
    ppl = _to_numeric(ppl, ["seq_len", "batch", "perplexity", "tokens_evaluated", "seed", "replica_id"])
    if "seed" not in ppl.columns and "run_id" in ppl.columns:
        ppl["seed"] = ppl["run_id"].map(_extract_seed_from_run_id)
    ppl = _to_numeric(ppl, ["seed"])
    if args.strict:
        strict_issues = _strict_missing_seed(ppl, table_name="ppl")
        if strict_issues:
            _print_strict_issues(strict_issues)
            return 2
    ppl_keys = [
        c
        for c in [
            "model_id",
            "hardware",
            "kv_mode",
            "ppl_mode",
            "seq_len",
            "batch",
            "group_size",
            "clip_percentile",
            "chunk_size",
        ]
        if c in ppl.columns
    ]
    ppl_summary = _agg_mean_std(ppl, ppl_keys, ["perplexity", "tokens_evaluated"])
    if not ppl_summary.empty:
        ppl_summary = _add_ci95_columns(ppl_summary)
        # AGG-009: ensure canonical kv_mode ordering in output table.
        ppl_summary = _sort_by_kv_mode(ppl_summary, extra_cols=["seq_len"])
        _save_table(ppl_summary, tables_dir / "ppl_summary.csv")
        if "seq_len" in ppl_summary.columns and "perplexity_mean" in ppl_summary.columns:
            _plot_lines(
                ppl_summary,
                x="seq_len",
                y="perplexity_mean",
                hue="kv_mode",
                title="Perplexity vs Evaluated Tokens",
                xlabel="Evaluated tokens (seq_len)",
                ylabel="Perplexity (mean)",
                out_path=plots_dir / "ppl_vs_tokens.png",
                yerr="perplexity_ci95_half",
            )

    # Needle (summary)
    needle = _read_csvs(runs_dir, ["profile_needle_*.csv"])
    needle = _to_numeric(
        needle,
        ["seq_len", "needle_pass_rate", "needle_exact_match_rate", "seed"],
    )
    if "seed" not in needle.columns and "run_id" in needle.columns:
        needle["seed"] = needle["run_id"].map(_extract_seed_from_run_id)
    needle = _to_numeric(needle, ["seed"])
    if args.strict:
        strict_issues = _strict_missing_seed(needle, table_name="needle")
        if strict_issues:
            _print_strict_issues(strict_issues)
            return 2
    needle_keys = [c for c in ["model_id", "hardware", "kv_mode", "seq_len"] if c in needle.columns]
    needle_summary = _agg_mean_std(
        needle,
        needle_keys,
        ["needle_pass_rate", "needle_exact_match_rate"],
    )
    if not needle_summary.empty:
        needle_summary = _add_ci95_columns(needle_summary)
        # AGG-009: ensure canonical kv_mode ordering in output table.
        needle_summary = _sort_by_kv_mode(needle_summary, extra_cols=["seq_len"])
        _save_table(needle_summary, tables_dir / "needle_summary.csv")
        if "seq_len" in needle_summary.columns and "needle_pass_rate_mean" in needle_summary.columns:
            _plot_lines(
                needle_summary,
                x="seq_len",
                y="needle_pass_rate_mean",
                hue="kv_mode",
                title="Needle Pass Rate vs Context Len",
                xlabel="Context length (tokens)",
                ylabel="Pass rate (%)",
                out_path=plots_dir / "needle_pass_rate_vs_context.png",
                yerr="needle_pass_rate_ci95_half",
            )
        if "needle_exact_match_rate_mean" in needle_summary.columns:
            exact = needle_summary.dropna(subset=["needle_exact_match_rate_mean"], how="all")
            if not exact.empty:
                _plot_lines(
                    exact,
                    x="seq_len",
                    y="needle_exact_match_rate_mean",
                    hue="kv_mode",
                    title="Needle Exact Match Rate vs Context Len",
                    xlabel="Context length (tokens)",
                    ylabel="Exact match rate (%)",
                    out_path=plots_dir / "needle_exact_match_vs_context.png",
                    yerr="needle_exact_match_rate_ci95_half",
                )

    # LongBench (summary)
    longbench = _read_csvs(runs_dir, ["profile_longbench_*.csv"])
    longbench = _to_numeric(
        longbench,
        [
            "seq_len",
            "batch",
            "seed",
            "replica_id",
            "ttft_ms",
            "tpot_ms",
            "tok_per_s",
            "longbench_score",
            "longbench_official_macro",
            "longbench_f1_macro",
            "longbench_em_macro",
            "longbench_contains_macro",
            "longbench_task_count",
            "longbench_sample_count",
        ],
    )
    if "seed" not in longbench.columns and "run_id" in longbench.columns:
        longbench["seed"] = longbench["run_id"].map(_extract_seed_from_run_id)
    longbench = _to_numeric(longbench, ["seed"])
    if args.strict:
        strict_issues = _strict_missing_seed(longbench, table_name="longbench")
        if strict_issues:
            _print_strict_issues(strict_issues)
            return 2
    longbench_keys = [
        c
        for c in [
            "model_id",
            "hardware",
            "kv_mode",
            "seq_len",
            "batch",
            "group_size",
            "clip_percentile",
            "longbench_source",
        ]
        if c in longbench.columns
    ]
    # AGG-007: LongBench reports 3 sub-metrics (f1_macro, em_macro, contains_macro)
    # alongside the official_macro composite.  These are NOT synonymous: different
    # LongBench tasks use different scoring (F1, exact-match, or contains-match).
    # Keeping all 3 enables per-metric-type diagnostics; official_macro is the
    # primary comparison metric used in claims and plots.
    longbench_summary = _agg_mean_std(
        longbench,
        longbench_keys,
        [
            "longbench_score",
            "longbench_official_macro",
            "longbench_f1_macro",
            "longbench_em_macro",
            "longbench_contains_macro",
            "longbench_task_count",
            "longbench_sample_count",
            "ttft_ms",
            "tpot_ms",
            "tok_per_s",
        ],
    )
    if not longbench_summary.empty:
        longbench_summary = _add_ci95_columns(longbench_summary)
        # AGG-009: ensure canonical kv_mode ordering in output table.
        longbench_summary = _sort_by_kv_mode(longbench_summary, extra_cols=["seq_len"])
        _save_table(longbench_summary, tables_dir / "longbench_summary.csv")
        if (
            "seq_len" in longbench_summary.columns
            and "longbench_score_mean" in longbench_summary.columns
        ):
            _plot_lines(
                longbench_summary,
                x="seq_len",
                y="longbench_score_mean",
                hue="kv_mode",
                title="LongBench Official-Metric Macro vs Context Len",
                xlabel="Context length (tokens)",
                ylabel="LongBench score (official-metric macro, 0-1)",
                out_path=plots_dir / "longbench_score_vs_context.png",
                yerr="longbench_score_ci95_half",
            )

    longbench_task = _read_csvs(runs_dir, ["longbench_task_summary_*.csv"])
    longbench_task = _to_numeric(
        longbench_task,
        [
            "seq_len",
            "gen_len",
            "sample_count",
            "exact_match_rate",
            "contains_match_rate",
            "f1_mean",
            "seed",
            "replica_id",
        ],
    )
    if not longbench_task.empty and "seed" not in longbench_task.columns and "run_id" in longbench_task.columns:
        longbench_task["seed"] = longbench_task["run_id"].map(_extract_seed_from_run_id)
    longbench_task = _to_numeric(longbench_task, ["seed"])
    if args.strict:
        strict_issues = _strict_missing_seed(longbench_task, table_name="longbench_task")
        if strict_issues:
            _print_strict_issues(strict_issues)
            return 2
    longbench_task_keys = [
        c
        for c in ["task_name", "kv_mode", "seq_len", "gen_len", "run_name"]
        if c in longbench_task.columns
    ]
    longbench_task_summary = _agg_mean_std(
        longbench_task,
        longbench_task_keys,
        ["exact_match_rate", "contains_match_rate", "f1_mean", "sample_count"],
    )
    if not longbench_task_summary.empty:
        longbench_task_summary = _add_ci95_columns(longbench_task_summary)
        # AGG-009: ensure canonical kv_mode ordering in output table.
        longbench_task_summary = _sort_by_kv_mode(longbench_task_summary, extra_cols=["task_name", "seq_len"])
        _save_table(longbench_task_summary, tables_dir / "longbench_task_summary.csv")

    # RULER (summary)
    ruler = _read_csvs(runs_dir, ["profile_ruler_*.csv"])
    ruler = _to_numeric(
        ruler,
        [
            "seq_len",
            "batch",
            "seed",
            "replica_id",
            "ttft_ms",
            "tpot_ms",
            "tok_per_s",
            "ruler_num_cases",
            "ruler_num_kv_pairs",
            "ruler_depth_count",
            "ruler_pass_rate",
            "ruler_contains_rate",
            "ruler_f1_mean",
            "ruler_score",
        ],
    )
    if "seed" not in ruler.columns and "run_id" in ruler.columns:
        ruler["seed"] = ruler["run_id"].map(_extract_seed_from_run_id)
    ruler = _to_numeric(ruler, ["seed"])
    if args.strict:
        strict_issues = _strict_missing_seed(ruler, table_name="ruler")
        if strict_issues:
            _print_strict_issues(strict_issues)
            return 2
    ruler_keys = [
        c
        for c in [
            "model_id",
            "hardware",
            "kv_mode",
            "seq_len",
            "batch",
            "group_size",
            "clip_percentile",
            "ruler_num_kv_pairs",
        ]
        if c in ruler.columns
    ]
    ruler_summary = _agg_mean_std(
        ruler,
        ruler_keys,
        [
            "ruler_pass_rate",
            "ruler_contains_rate",
            "ruler_f1_mean",
            "ruler_score",
            "ruler_num_cases",
            "ruler_depth_count",
            "ttft_ms",
            "tpot_ms",
            "tok_per_s",
        ],
    )
    if not ruler_summary.empty:
        ruler_summary = _add_ci95_columns(ruler_summary)
        # AGG-009: ensure canonical kv_mode ordering in output table.
        ruler_summary = _sort_by_kv_mode(ruler_summary, extra_cols=["seq_len"])
        _save_table(ruler_summary, tables_dir / "ruler_summary.csv")
        if "seq_len" in ruler_summary.columns and "ruler_pass_rate_mean" in ruler_summary.columns:
            _plot_lines(
                ruler_summary,
                x="seq_len",
                y="ruler_pass_rate_mean",
                hue="kv_mode",
                title="RULER Pass Rate vs Context Len",
                xlabel="Context length (tokens)",
                ylabel="RULER pass rate (%)",
                out_path=plots_dir / "ruler_pass_rate_vs_context.png",
                yerr="ruler_pass_rate_ci95_half",
            )

    ruler_depth = _read_csvs(runs_dir, ["ruler_depth_summary_*.csv"])
    ruler_depth = _to_numeric(
        ruler_depth,
        [
            "seq_len",
            "gen_len",
            "depth_ratio",
            "sample_count",
            "ruler_pass_rate",
            "ruler_contains_rate",
            "ruler_f1_mean",
            "seed",
            "replica_id",
        ],
    )
    if not ruler_depth.empty and "seed" not in ruler_depth.columns and "run_id" in ruler_depth.columns:
        ruler_depth["seed"] = ruler_depth["run_id"].map(_extract_seed_from_run_id)
    ruler_depth = _to_numeric(ruler_depth, ["seed"])
    if args.strict:
        strict_issues = _strict_missing_seed(ruler_depth, table_name="ruler_depth")
        if strict_issues:
            _print_strict_issues(strict_issues)
            return 2
    ruler_depth_keys = [
        c for c in ["model_id", "kv_mode", "seq_len", "depth_ratio"] if c in ruler_depth.columns
    ]
    ruler_depth_summary = _agg_mean_std(
        ruler_depth,
        ruler_depth_keys,
        ["ruler_pass_rate", "ruler_contains_rate", "ruler_f1_mean", "sample_count"],
    )
    if not ruler_depth_summary.empty:
        ruler_depth_summary = _add_ci95_columns(ruler_depth_summary)
        # AGG-009: ensure canonical kv_mode ordering in output table.
        ruler_depth_summary = _sort_by_kv_mode(ruler_depth_summary, extra_cols=["seq_len", "depth_ratio"])
        _save_table(ruler_depth_summary, tables_dir / "ruler_depth_summary.csv")

    # RULER task summary (per-subtask metrics)
    ruler_task = _read_csvs(runs_dir, ["ruler_task_summary_*.csv"])
    ruler_task = _to_numeric(
        ruler_task,
        [
            "seq_len",
            "batch",
            "sample_count",
            "ruler_pass_rate",
            "ruler_contains_rate",
            "ruler_f1_mean",
            "seed",
            "replica_id",
        ],
    )
    if not ruler_task.empty and "seed" not in ruler_task.columns and "run_id" in ruler_task.columns:
        ruler_task["seed"] = ruler_task["run_id"].map(_extract_seed_from_run_id)
    if "ruler_task" not in ruler_task.columns and "task_name" in ruler_task.columns:
        ruler_task["ruler_task"] = ruler_task["task_name"]
    ruler_task = _to_numeric(ruler_task, ["seed"])
    if args.strict:
        strict_issues = _strict_missing_seed(ruler_task, table_name="ruler_task")
        if strict_issues:
            _print_strict_issues(strict_issues)
            return 2
    ruler_task_keys = [
        c
        for c in ["model_id", "hardware", "ruler_task", "kv_mode", "seq_len", "batch"]
        if c in ruler_task.columns
    ]
    ruler_task_summary = _agg_mean_std(
        ruler_task,
        ruler_task_keys,
        ["ruler_pass_rate", "ruler_contains_rate", "ruler_f1_mean", "sample_count"],
    )
    if not ruler_task_summary.empty:
        ruler_task_summary = _add_ci95_columns(ruler_task_summary)
        # AGG-009: ensure canonical kv_mode ordering in output table.
        ruler_task_summary = _sort_by_kv_mode(ruler_task_summary, extra_cols=["ruler_task", "seq_len"])
        _save_table(ruler_task_summary, tables_dir / "ruler_task_summary.csv")
        _save_table(ruler_task_summary, tables_dir / "ruler_subtask_summary.csv")

    # Needle details (curve over depth)
    needle_details = _read_csvs(runs_dir, ["needle_details_*.csv"])
    needle_details = _to_numeric(needle_details, ["context_len", "depth", "passed"])
    if not needle_details.empty and {"kv_mode", "context_len", "depth", "passed"}.issubset(needle_details.columns):
        curve = (
            needle_details.groupby(["kv_mode", "context_len", "depth"], dropna=False)["passed"]
            .mean()
            .reset_index()
            .rename(columns={"passed": "pass_rate"})
        )
        # AGG-009: ensure canonical kv_mode ordering in output table.
        curve = _sort_by_kv_mode(curve, extra_cols=["context_len", "depth"])
        _save_table(curve, tables_dir / "needle_curve_by_depth.csv")
        for context_len, sub_ctx in sorted(curve.groupby("context_len")):
            out_path = plots_dir / f"needle_curve_depth_ctx{int(context_len)}.png"
            _plot_lines(
                sub_ctx,
                x="depth",
                y="pass_rate",
                hue="kv_mode",
                title=f"Needle Pass Rate vs Depth (context_len={int(context_len)})",
                xlabel="Needle depth (%)",
                ylabel="Pass rate (0-1, mean)",
                out_path=out_path,
            )

    # Significance / paired-difference summaries by seed.
    # AGG-008: KIVI quant_bits (4 or 8) is not distinguished in pairings. Currently only INT8 KIVI runs exist in the experiment matrix.
    pairings = [
        ("int8_baseline", "int8_ours"),
        ("int4_baseline", "int4_ours"),
        ("int4_fused", "int4_ours"),
        ("kivi_style", "int8_ours"),       # Claims C9/C10: INT8-ours vs KIVI
        ("kivi_style", "int8_baseline"),   # completeness: INT8-baseline vs KIVI
    ]
    sig_frames = []
    sig_pair_rows = []
    sig_specs = [
        {
            "df": latency,
            "metric_col": "tpot_ms",
            "metric_name": "tpot_ms",
            "key_cols": ["model_id", "seq_len", "gen_len", "batch"],
            "higher_is_better": False,
        },
        {
            "df": ppl,
            "metric_col": "perplexity",
            "metric_name": "perplexity",
            "key_cols": ["model_id", "seq_len", "ppl_mode", "chunk_size"],
            "higher_is_better": False,
        },
        {
            "df": needle,
            "metric_col": "needle_pass_rate",
            "metric_name": "needle_pass_rate",
            "key_cols": ["model_id", "seq_len"],
            "higher_is_better": True,
        },
        {
            "df": longbench,
            "metric_col": "longbench_score",
            "metric_name": "longbench_score",
            "key_cols": ["model_id", "seq_len", "longbench_source"],
            "higher_is_better": True,
        },
        {
            "df": ruler,
            "metric_col": "ruler_pass_rate",
            "metric_name": "ruler_pass_rate",
            "key_cols": ["model_id", "seq_len", "ruler_num_kv_pairs"],
            "higher_is_better": True,
        },
    ]
    for spec in sig_specs:
        sig_summary, paired_rows = _significance_summary(
            spec["df"],
            metric_col=spec["metric_col"],
            key_cols=spec["key_cols"],
            pairings=pairings,
            metric_name=spec["metric_name"],
            higher_is_better=bool(spec["higher_is_better"]),
            min_pairs=max(2, int(args.significance_min_pairs)),
            alpha=float(args.significance_alpha),
            ci_level=float(args.significance_ci_level),
            n_bootstrap=max(1000, int(args.significance_bootstrap)),
            n_permutations=max(2000, int(args.significance_permutations)),
            random_seed=int(args.significance_seed),
        )
        if not sig_summary.empty:
            sig_frames.append(sig_summary)
        if not paired_rows.empty:
            sig_pair_rows.append(paired_rows)

    if sig_frames:
        significance_summary = pd.concat(sig_frames, ignore_index=True)
        significance_summary = _add_bh_fdr_qvalues(
            significance_summary, p_col="p_value", q_col="q_value"
        )
        alpha = float(args.significance_alpha)
        significance_summary["significant_p_alpha"] = (
            pd.to_numeric(significance_summary["p_value"], errors="coerce") <= alpha
        ) & significance_summary["meets_min_pairs"].astype(bool)
        significance_summary["significant_q_alpha"] = (
            pd.to_numeric(significance_summary["q_value"], errors="coerce") <= alpha
        ) & significance_summary["meets_min_pairs"].astype(bool)
        _save_table(significance_summary, tables_dir / "significance_summary.csv")

        coverage_cols = [
            c
            for c in [
                "metric",
                "baseline_mode",
                "challenger_mode",
                "seq_len",
                "gen_len",
                "batch",
                "ppl_mode",
                "chunk_size",
                "longbench_source",
                "ruler_num_kv_pairs",
                "n_pairs",
                "n_unique_seeds",
                "seed_min",
                "seed_max",
                "meets_min_pairs",
                "inference_status",
                "significant_p_alpha",
                "significant_q_alpha",
            ]
            if c in significance_summary.columns
        ]
        if coverage_cols:
            _save_table(
                significance_summary[coverage_cols].copy(),
                tables_dir / "significance_coverage.csv",
            )
    if sig_pair_rows:
        significance_pairs = pd.concat(sig_pair_rows, ignore_index=True)
        _save_table(significance_pairs, tables_dir / "significance_pairs.csv")

    # Relative gain summary table for thesis discussion.
    pairings = [
        ("int8_baseline", "int8_ours"),
        ("int4_fused", "int4_ours"),
        ("int4_ours", "int4_ours_mixed"),
        ("fp16", "int8_ours"),
        ("fp16", "int4_ours"),
        ("kivi_style", "int8_ours"),
        ("kivi_style", "int8_baseline"),
    ]
    gain_frames = []
    gain_frames.append(
        _relative_gain_table(
            latency_summary,
            metric_col="tpot_ms_mean",
            metric_name="tpot_ms",
            key_cols=["model_id", "seq_len", "gen_len", "batch"],
            pairings=pairings,
            higher_is_better=False,
        )
    )
    gain_frames.append(
        _relative_gain_table(
            latency_summary,
            metric_col="tok_per_s_mean",
            metric_name="tok_per_s",
            key_cols=["model_id", "seq_len", "gen_len", "batch"],
            pairings=pairings,
            higher_is_better=True,
        )
    )
    gain_frames.append(
        _relative_gain_table(
            memory_summary,
            metric_col="kv_cache_mem_mb_mean",
            metric_name="kv_cache_mem_mb",
            key_cols=["model_id", "seq_len", "gen_len", "batch"],
            pairings=pairings,
            higher_is_better=False,
        )
    )
    gain_frames.append(
        _relative_gain_table(
            ppl_summary,
            metric_col="perplexity_mean",
            metric_name="perplexity",
            key_cols=["model_id", "seq_len", "ppl_mode", "chunk_size"],
            pairings=pairings,
            higher_is_better=False,
        )
    )
    gain_frames.append(
        _relative_gain_table(
            needle_summary,
            metric_col="needle_pass_rate_mean",
            metric_name="needle_pass_rate",
            key_cols=["model_id", "seq_len"],
            pairings=pairings,
            higher_is_better=True,
        )
    )
    gain_frames.append(
        _relative_gain_table(
            longbench_summary,
            metric_col="longbench_score_mean",
            metric_name="longbench_score",
            key_cols=["model_id", "seq_len", "longbench_source"],
            pairings=pairings,
            higher_is_better=True,
        )
    )
    gain_frames.append(
        _relative_gain_table(
            ruler_summary,
            metric_col="ruler_pass_rate_mean",
            metric_name="ruler_pass_rate",
            key_cols=["model_id", "seq_len", "ruler_num_kv_pairs"],
            pairings=pairings,
            higher_is_better=True,
        )
    )
    gain_frames = [g for g in gain_frames if not g.empty]
    if gain_frames:
        gain_summary = pd.concat(gain_frames, ignore_index=True)
        _save_table(gain_summary, tables_dir / "relative_gain_summary.csv")

    main_claims = _main_claims_32k_table(
        latency_summary=latency_summary,
        memory_summary=memory_summary,
        needle_summary=needle_summary,
        ppl_summary=ppl_summary,
        longbench_summary=longbench_summary,
        ruler_summary=ruler_summary,
        target_seq_len=32704,
    )
    if not main_claims.empty:
        _save_table(main_claims, tables_dir / "thesis_main_claims_32k.csv")

    per_model_manifest = _export_per_model_layered_tables(tables_dir)
    if not per_model_manifest.empty:
        _save_table(
            per_model_manifest.sort_values(["model_id", "table_name"]).reset_index(drop=True),
            tables_dir / "per_model_table_manifest.csv",
        )

    print(f"Wrote tables to {tables_dir} and plots to {plots_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
