#!/usr/bin/env python3
"""Round 2 diagnostic: 14B RULER, FI LongBench, 14B Needle."""

import glob
import os
import pandas as pd


def print_header(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


print_header("14B RA RULER sl4096 all seeds")
for seed in [1234, 1235, 1236]:
    fs = glob.glob(f"results/emnlp_p012_batch/runs/ruler_ra_14b_sl4096_s{seed}/profile_ruler_*.csv")
    print(f"  seed {seed}: {len(fs)} file(s)")
    for f in fs:
        d = pd.read_csv(f)
        name = os.path.basename(f)
        print(f"    file: {name}")
        print(f"    rows: {len(d)}")
        print(f"    ruler_pass_rate: {d['ruler_pass_rate'].tolist()}")
        print(f"    ruler_f1_mean: {d['ruler_f1_mean'].tolist()}")


print_header("14B RA RULER task breakdown (sl4096 s1234)")
fs = glob.glob("results/emnlp_p012_batch/runs/ruler_ra_14b_sl4096_s1234/ruler_task_summary_*.csv")
for f in fs:
    d = pd.read_csv(f)
    cols = [c for c in ["ruler_task", "sample_count", "ruler_pass_rate",
                         "ruler_contains_rate", "ruler_f1_mean"] if c in d.columns]
    print(d[cols].to_string())


print_header("FI RULER task breakdown (sl4096 s1234)")
fs = glob.glob("results/emnlp_p012_batch/runs/ruler_fi_1p5b_sl4096_s1234/ruler_task_summary_*.csv")
for f in fs:
    d = pd.read_csv(f)
    cols = [c for c in ["ruler_task", "sample_count", "ruler_pass_rate",
                         "ruler_contains_rate", "ruler_f1_mean"] if c in d.columns]
    print(d[cols].to_string())


print_header("FI LongBench 1.5B s1234 stats")
lb = glob.glob("results/emnlp_p012_batch/runs/longbench_fi_1p5b_s1234/longbench_details_*.csv")
for f in lb:
    d = pd.read_csv(f)
    print(f"  total rows: {len(d)}")
    print(f"  tasks: {d['task_name'].value_counts().to_dict()}")
    print(f"  f1 mean: {d['f1'].mean():.4f}")
    print(f"  f1 non-zero: {(d['f1'] > 0).sum()}")
    print(f"  official_metric mean: {d['official_metric_value'].mean():.4f}")
    print(f"  official_metric non-zero: {(d['official_metric_value'] > 0).sum()}")
    # Sample a non-zero row
    nz = d[d["f1"] > 0]
    if len(nz) > 0:
        r = nz.iloc[0]
        print(f"  non-zero sample: task={r['task_name']}")
        print(f"    pred: {str(r['prediction'])[:120]}")
        print(f"    answer: {str(r['answers'])[:120]}")
    # 看 0 分样本
    zeros = d[d["f1"] == 0]
    if len(zeros) > 0:
        r = zeros.iloc[0]
        print(f"  zero sample: task={r['task_name']}")
        print(f"    pred: {str(r['prediction'])[:120]}")
        print(f"    answer: {str(r['answers'])[:120]}")


print_header("14B RA Needle 32K s1234 (first 3)")
n = glob.glob("results/emnlp_p012_batch/runs/needle_ra_14b_c32704_s1234/needle_details_*.csv")
if n:
    d = pd.read_csv(n[0])
    for i, row in d.head(3).iterrows():
        print(f"  [{i}] depth={row['depth']:.1f} passed={row['passed']}")
        print(f"      needle: {str(row['needle'])[:100]}")
        print(f"      gen:    {str(row['generated_text'])[:100]}")
