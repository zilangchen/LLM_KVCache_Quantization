#!/usr/bin/env python3
"""TST-036: Minimal end-to-end test for aggregate_results.py main() pipeline.

Creates synthetic CSV files mimicking run output, invokes aggregate_results.py,
and verifies that expected output tables are produced.
"""

import csv
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure project root is on sys.path for imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))


def _write_csv(path: Path, fieldnames: list, rows: list[dict]) -> None:
    """Write a CSV file with given fieldnames and rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _make_ppl_csv(runs_dir: Path, seed: int, kv_mode: str) -> None:
    """Create a minimal ppl_summary CSV for one seed/kv_mode."""
    run_id = f"ppl_{kv_mode}_s{seed}"
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        run_dir / f"ppl_summary_{run_id}.csv",
        [
            "run_id", "model_id", "kv_mode", "quant_bits", "seq_len",
            "gen_len", "batch", "seed", "replica_id", "perplexity",
            "ppl_ci95_low", "ppl_ci95_high", "ppl_mode", "tokens_evaluated",
            "chunk_size", "hardware", "git_commit", "timestamp",
        ],
        [
            {
                "run_id": run_id,
                "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
                "kv_mode": kv_mode,
                "quant_bits": 16 if kv_mode == "fp16" else 8,
                "seq_len": 4096,
                "gen_len": 128,
                "batch": 1,
                "seed": seed,
                "replica_id": 0,
                "perplexity": 8.5 + seed * 0.1 + (0 if kv_mode == "fp16" else 0.3),
                "ppl_ci95_low": 8.4,
                "ppl_ci95_high": 8.6,
                "ppl_mode": "sliding_window",
                "tokens_evaluated": 5000,
                "chunk_size": 512,
                "hardware": "test",
                "git_commit": "abc1234",
                "timestamp": "2026-01-01T00:00:00",
            }
        ],
    )


def _make_latency_csv(runs_dir: Path, seed: int, kv_mode: str) -> None:
    """Create a minimal latency_summary CSV."""
    run_id = f"lat_{kv_mode}_s{seed}"
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        run_dir / f"latency_summary_{run_id}.csv",
        [
            "run_id", "model_id", "kv_mode", "quant_bits", "seq_len",
            "gen_len", "batch", "seed", "replica_id", "tpot_ms", "ttft_ms",
            "tok_per_s", "hardware", "git_commit", "timestamp",
        ],
        [
            {
                "run_id": run_id,
                "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
                "kv_mode": kv_mode,
                "quant_bits": 16 if kv_mode == "fp16" else 8,
                "seq_len": 32704,
                "gen_len": 64,
                "batch": 1,
                "seed": seed,
                "replica_id": 0,
                "tpot_ms": 4.5 + seed * 0.01,
                "ttft_ms": 12.0,
                "tok_per_s": 220.0,
                "hardware": "test",
                "git_commit": "abc1234",
                "timestamp": "2026-01-01T00:00:00",
            }
        ],
    )


def _make_memory_csv(runs_dir: Path, seed: int, kv_mode: str) -> None:
    """Create a minimal memory_summary CSV."""
    run_id = f"mem_{kv_mode}_s{seed}"
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        run_dir / f"memory_summary_{run_id}.csv",
        [
            "run_id", "model_id", "kv_mode", "quant_bits", "seq_len",
            "gen_len", "batch", "seed", "replica_id",
            "gpu_mem_peak_mb", "kv_cache_mem_mb",
            "hardware", "git_commit", "timestamp",
        ],
        [
            {
                "run_id": run_id,
                "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
                "kv_mode": kv_mode,
                "quant_bits": 16 if kv_mode == "fp16" else 8,
                "seq_len": 32704,
                "gen_len": 64,
                "batch": 1,
                "seed": seed,
                "replica_id": 0,
                "gpu_mem_peak_mb": 8120.0,
                "kv_cache_mem_mb": 1530.0 if kv_mode == "fp16" else 780.0,
                "hardware": "test",
                "git_commit": "abc1234",
                "timestamp": "2026-01-01T00:00:00",
            }
        ],
    )


class TestAggregateMainE2E(unittest.TestCase):
    """TST-036: End-to-end test for aggregate_results.py main().

    Creates synthetic run CSVs in a temp directory, invokes the script
    via subprocess, and checks that expected output tables are produced.
    """

    def test_basic_aggregation_produces_output_tables(self):
        """Given minimal PPL/latency/memory CSVs, main() should produce summary CSVs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "runs"
            tables_dir = Path(tmpdir) / "tables"
            plots_dir = Path(tmpdir) / "plots"

            # Create synthetic data for 3 seeds × 2 kv_modes
            for seed in [1234, 1235, 1236]:
                for kv_mode in ["fp16", "int8_ours"]:
                    _make_ppl_csv(runs_dir, seed, kv_mode)
                    _make_latency_csv(runs_dir, seed, kv_mode)
                    _make_memory_csv(runs_dir, seed, kv_mode)

            # Run aggregate_results.py
            result = subprocess.run(
                [
                    sys.executable,
                    str(_PROJECT_ROOT / "scripts" / "aggregate_results.py"),
                    "--runs_dir", str(runs_dir),
                    "--tables_dir", str(tables_dir),
                    "--plots_dir", str(plots_dir),
                ],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(_PROJECT_ROOT),
            )

            self.assertEqual(
                result.returncode, 0,
                f"aggregate_results.py failed:\nstdout: {result.stdout[-500:]}\nstderr: {result.stderr[-500:]}",
            )

            # Check that key output tables were created
            self.assertTrue(tables_dir.exists(), "tables_dir was not created")

            # At minimum, ppl_summary.csv should be produced
            expected_tables = ["ppl_summary.csv"]
            for table_name in expected_tables:
                table_path = tables_dir / table_name
                self.assertTrue(
                    table_path.exists(),
                    f"Expected output table {table_name} not found. "
                    f"Available: {[f.name for f in tables_dir.iterdir()] if tables_dir.exists() else []}",
                )

            # Verify ppl_summary has expected structure
            import pandas as pd
            ppl = pd.read_csv(tables_dir / "ppl_summary.csv")
            self.assertGreater(len(ppl), 0, "ppl_summary.csv is empty")
            self.assertIn("kv_mode", ppl.columns)
            # Should have aggregated across seeds
            for mode in ["fp16", "int8_ours"]:
                mode_rows = ppl[ppl["kv_mode"] == mode]
                self.assertGreater(len(mode_rows), 0, f"Missing {mode} in ppl_summary")

    def test_basic_aggregation_content_correctness(self):
        """TST-034: Verify output CSV content, not just file existence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "runs"
            tables_dir = Path(tmpdir) / "tables"
            plots_dir = Path(tmpdir) / "plots"

            for seed in [1234, 1235, 1236]:
                for kv_mode in ["fp16", "int8_ours"]:
                    _make_ppl_csv(runs_dir, seed, kv_mode)
                    _make_latency_csv(runs_dir, seed, kv_mode)
                    _make_memory_csv(runs_dir, seed, kv_mode)

            result = subprocess.run(
                [
                    sys.executable,
                    str(_PROJECT_ROOT / "scripts" / "aggregate_results.py"),
                    "--runs_dir", str(runs_dir),
                    "--tables_dir", str(tables_dir),
                    "--plots_dir", str(plots_dir),
                ],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(_PROJECT_ROOT),
            )
            self.assertEqual(result.returncode, 0, f"stderr: {result.stderr[-500:]}")

            import pandas as pd

            # Verify ppl_summary content
            ppl_path = tables_dir / "ppl_summary.csv"
            self.assertTrue(ppl_path.exists())
            ppl = pd.read_csv(ppl_path)
            self.assertGreater(len(ppl), 0, "ppl_summary should not be empty")
            # Must have required columns
            for col in ["kv_mode", "perplexity"]:
                self.assertIn(col, ppl.columns, f"Missing column: {col}")
            # Perplexity values should be positive numbers
            for _, row in ppl.iterrows():
                if pd.notna(row.get("perplexity")):
                    self.assertGreater(
                        float(row["perplexity"]), 0,
                        "Perplexity must be positive"
                    )

    def test_nonexistent_runs_dir_returns_2(self):
        """When runs_dir does not exist, main() should return exit code 2."""
        result = subprocess.run(
            [
                sys.executable,
                str(_PROJECT_ROOT / "scripts" / "aggregate_results.py"),
                "--runs_dir", "/nonexistent/path/runs",
                "--tables_dir", "/tmp/tables",
                "--plots_dir", "/tmp/plots",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(_PROJECT_ROOT),
        )
        self.assertEqual(result.returncode, 2)

    def test_empty_runs_dir_produces_no_crash(self):
        """An empty runs_dir should not crash; the script should exit 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "runs"
            runs_dir.mkdir()
            tables_dir = Path(tmpdir) / "tables"
            plots_dir = Path(tmpdir) / "plots"

            result = subprocess.run(
                [
                    sys.executable,
                    str(_PROJECT_ROOT / "scripts" / "aggregate_results.py"),
                    "--runs_dir", str(runs_dir),
                    "--tables_dir", str(tables_dir),
                    "--plots_dir", str(plots_dir),
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(_PROJECT_ROOT),
            )
            self.assertEqual(
                result.returncode, 0,
                f"Empty runs_dir should not crash:\nstderr: {result.stderr[-500:]}",
            )


if __name__ == "__main__":
    unittest.main()
