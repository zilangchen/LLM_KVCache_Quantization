#!/usr/bin/env python3
"""Diagnose BD Needle 100% fail + RULER pass_rate > 1 issue."""

import glob
import pandas as pd

print("=" * 60)
print("BD Needle 4K s1234 generated_text (first 3 rows)")
print("=" * 60)
df_bd = pd.read_csv(glob.glob(
    "results/emnlp_p012_batch/runs/needle_bd_1p5b_c4096_s1234/needle_details_*.csv")[0])
for i, row in df_bd.head(3).iterrows():
    print(f"  [{i}] depth={row['depth']:.1f} passed={row['passed']}")
    print(f"      needle: {str(row['needle'])[:100]}")
    print(f"      gen:    {str(row['generated_text'])[:100]}")
    print()

print("=" * 60)
print("FI Needle 4K s1234 generated_text (first 3 rows)")
print("=" * 60)
df_fi = pd.read_csv(glob.glob(
    "results/emnlp_p012_batch/runs/needle_fi_1p5b_c4096_s1234/needle_details_*.csv")[0])
for i, row in df_fi.head(3).iterrows():
    print(f"  [{i}] depth={row['depth']:.1f} passed={row['passed']}")
    print(f"      needle: {str(row['needle'])[:100]}")
    print(f"      gen:    {str(row['generated_text'])[:100]}")
    print()

print("=" * 60)
print("BD RULER 1.5B sl4096 s1234 — task breakdown")
print("=" * 60)
task_files = glob.glob("results/emnlp_p012_batch/runs/ruler_bd_1p5b_sl4096_s1234/ruler_task_summary_*.csv")
if task_files:
    df_task = pd.read_csv(task_files[0])
    print(df_task.to_string())
else:
    print("  no task_summary file")

print()
print("=" * 60)
print("BD RULER summary stats (seed 1234, 1235, 1236)")
print("=" * 60)
for seed in [1234, 1235, 1236]:
    files = glob.glob(f"results/emnlp_p012_batch/runs/ruler_bd_1p5b_sl4096_s{seed}/profile_ruler_*.csv")
    if files:
        d = pd.read_csv(files[0])
        cols_show = [c for c in ["ruler_pass_rate", "ruler_exact_rate",
                                  "ruler_contains_rate", "ruler_f1_mean",
                                  "ruler_score", "ruler_num_cases"]
                     if c in d.columns]
        print(f"  seed {seed}: {d[cols_show].iloc[0].to_dict()}")

print()
print("=" * 60)
print("Longbench BD 1.5B s1234 — task + metric distribution")
print("=" * 60)
lb_files = glob.glob("results/emnlp_p012_batch/runs/longbench_bd_1p5b_s1234/longbench_details_*.csv")
if lb_files:
    df_lb = pd.read_csv(lb_files[0])
    print(f"  total rows: {len(df_lb)}")
    print(f"  tasks: {df_lb['task_name'].value_counts().to_dict()}")
    print(f"  f1 stats: mean={df_lb['f1'].mean():.4f}, non-zero count={(df_lb['f1'] > 0).sum()}")
    print(f"  official_metric stats: mean={df_lb['official_metric_value'].mean():.4f}, non-zero={(df_lb['official_metric_value'] > 0).sum()}")
    # 看一个非零样本
    nonzero = df_lb[df_lb['official_metric_value'] > 0]
    if len(nonzero) > 0:
        row = nonzero.iloc[0]
        print(f"  non-zero sample: task={row['task_name']}, f1={row['f1']:.3f}")
        print(f"    pred: {str(row['prediction'])[:100]}")
        print(f"    answer: {str(row['answers'])[:100]}")
