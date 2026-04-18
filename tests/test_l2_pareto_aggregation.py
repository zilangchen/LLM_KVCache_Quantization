import csv
import json
from pathlib import Path

from scripts.aggregate_l2_pareto import build_front, build_table


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_build_table_and_front(tmp_path: Path):
    raw_dir = tmp_path / "raw"

    fast_dir = raw_dir / "7b" / "fast_policy"
    fast_dir.mkdir(parents=True)
    (fast_dir / "manifest.json").write_text(
        json.dumps(
            {
                "model_key": "7b",
                "model_id": "Qwen/Qwen2.5-7B-Instruct",
                "policy_id": "fast_policy",
                "policy_json": "/tmp/fast.json",
                "avg_bits": 4.5,
            }
        ),
        encoding="utf-8",
    )
    _write_csv(
        fast_dir / "longbench_task_summary_fast.csv",
        ["run_name", "task_name", "official_metric_name", "official_metric_value"],
        [
            {"run_name": "x", "task_name": "narrativeqa", "official_metric_name": "f1", "official_metric_value": 8.0},
            {"run_name": "x", "task_name": "hotpotqa", "official_metric_name": "f1", "official_metric_value": 7.0},
            {"run_name": "x", "task_name": "gov_report", "official_metric_name": "rouge_l", "official_metric_value": 9.0},
        ],
    )
    _write_csv(
        fast_dir / "profile_latency_x.csv",
        ["run_name", "ttft_ms", "tpot_ms"],
        [{"run_name": "x", "ttft_ms": 10.0, "tpot_ms": 5.0}],
    )
    _write_csv(
        fast_dir / "profile_memory_x.csv",
        ["run_name", "gpu_mem_peak_mb"],
        [{"run_name": "x", "gpu_mem_peak_mb": 1000.0}],
    )
    _write_csv(
        fast_dir / "profile_ppl_x.csv",
        ["run_name", "perplexity"],
        [{"run_name": "x", "perplexity": 12.0}],
    )
    _write_csv(
        fast_dir / "profile_needle_x.csv",
        ["run_name", "needle_pass_rate"],
        [{"run_name": "x", "needle_pass_rate": 0.9}],
    )

    slow_dir = raw_dir / "7b" / "slow_policy"
    slow_dir.mkdir(parents=True)
    (slow_dir / "manifest.json").write_text(
        json.dumps(
            {
                "model_key": "7b",
                "model_id": "Qwen/Qwen2.5-7B-Instruct",
                "policy_id": "slow_policy",
                "policy_json": "/tmp/slow.json",
                "avg_bits": 4.5,
            }
        ),
        encoding="utf-8",
    )
    _write_csv(
        slow_dir / "longbench_task_summary_slow.csv",
        ["run_name", "task_name", "official_metric_name", "official_metric_value"],
        [
            {"run_name": "y", "task_name": "narrativeqa", "official_metric_name": "f1", "official_metric_value": 7.0},
            {"run_name": "y", "task_name": "hotpotqa", "official_metric_name": "f1", "official_metric_value": 6.0},
            {"run_name": "y", "task_name": "gov_report", "official_metric_name": "rouge_l", "official_metric_value": 8.0},
        ],
    )
    _write_csv(
        slow_dir / "profile_latency_y.csv",
        ["run_name", "ttft_ms", "tpot_ms"],
        [{"run_name": "y", "ttft_ms": 11.0, "tpot_ms": 6.0}],
    )

    table = build_table(raw_dir)
    assert len(table) == 2
    fast_row = next(row for row in table if row["policy_id"] == "fast_policy")
    assert fast_row["quality_core"] == "8.0000"
    assert fast_row["tpot_ms"] == "5.0000"

    front = build_front(table)
    assert [row["policy_id"] for row in front] == ["fast_policy"]
