#!/usr/bin/env python3
"""Aggregate Phase 1 TPOT CSVs into a single comparison table.

For each (model_tag, backend) directory under
results/emnlp_p012_batch/runs/tpot_<backend>_<model_tag>/,
compute mean ± std of tpot_ms across runs.
"""
import argparse
import glob
import os
import sys

import pandas as pd

BACKENDS = ["fp16", "triton_ra", "bd", "fi", "torchref", "kivi"]
MODELS = ["1p5b", "7b", "8b", "14b"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--runs_dir",
        default="results/emnlp_p012_batch/runs",
        help="Directory containing tpot_<backend>_<model> subdirs",
    )
    args = ap.parse_args()

    rows = []
    for be in BACKENDS:
        row = {"backend": be}
        for m in MODELS:
            d = os.path.join(args.runs_dir, f"tpot_{be}_{m}")
            csvs = sorted(glob.glob(os.path.join(d, "*.csv")))
            if not csvs:
                row[m] = "N/A"
                continue
            df = pd.read_csv(csvs[0])
            tpot = df["tpot_ms"].astype(float)
            row[m] = f"{tpot.mean():.2f} ± {tpot.std():.2f}"
        rows.append(row)

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
