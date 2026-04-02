#!/usr/bin/env python3
"""Validate RULER v2fix results as they come in."""
import csv, glob, sys, os

RD = "results/emnlp_rolealign_v2/runs"
issues = []

for tag in ["1p5b", "7b", "8b"]:
    for ctx in [8192, 16384, 32704]:
        for seed in [1234, 1235, 1236]:
            pat = f"{RD}/ruler_v2fix_{tag}_ctx{ctx}_s{seed}/ruler_details_*.csv"
            files = sorted(glob.glob(pat))
            if not files:
                continue  # not yet produced

            rows = list(csv.DictReader(open(files[-1])))
            if not rows:
                issues.append(f"{tag} ctx={ctx} s={seed}: EMPTY CSV")
                continue

            # 1. Check truncation
            trunc = sum(1 for r in rows if r.get("input_truncated") == "True")
            total = len(rows)
            if trunc > 0:
                issues.append(f"{tag} ctx={ctx} s={seed}: {trunc}/{total} TRUNCATED")

            # 2. Check effective_prompt_budget
            eff = int(rows[0].get("effective_prompt_budget", 0))
            if eff < ctx:
                issues.append(f"{tag} ctx={ctx} s={seed}: eff_budget={eff} < ctx={ctx}")

            # 3. Per-task analysis
            tasks = {}
            for r in rows:
                t = r["ruler_task"]
                if t not in tasks:
                    tasks[t] = {"pass": 0, "contains": 0, "n": 0, "depths_pass": [], "depths_fail": []}
                tasks[t]["n"] += 1
                if r["contains_match"] == "1.0":
                    tasks[t]["contains"] += 1
                    tasks[t]["depths_pass"].append(float(r["depth_ratio"]))
                else:
                    tasks[t]["depths_fail"].append(float(r["depth_ratio"]))
                if r["exact_match"] == "1.0":
                    tasks[t]["pass"] += 1

            print(f"\n{tag} ctx={ctx} s={seed} (eff={eff}, trunc={trunc}/{total}):")
            for tname, tdata in sorted(tasks.items()):
                n = tdata["n"]
                pr = tdata["pass"] / n * 100 if n else 0
                cr = tdata["contains"] / n * 100 if n else 0
                print(f"  {tname:<10} pass={pr:5.1f}%  contains={cr:5.1f}%  n={n}")

                # 4. Check for 34.4% ceiling (the bug pattern)
                if abs(cr - 34.375) < 0.1 and tname in ("s_niah", "mk_niah"):
                    issues.append(f"{tag} ctx={ctx} s={seed} {tname}: contains={cr:.1f}% = 34.4% CEILING BUG!")

                # 5. Check depth correlation
                if tdata["depths_pass"] and tdata["depths_fail"]:
                    max_pass_d = max(tdata["depths_pass"])
                    min_fail_d = min(tdata["depths_fail"])
                    if max_pass_d < min_fail_d and cr < 90:
                        issues.append(
                            f"{tag} ctx={ctx} s={seed} {tname}: depth cutoff at {max_pass_d:.2f} "
                            f"(all fails at d>={min_fail_d:.2f}) — possible truncation"
                        )

print("\n" + "=" * 60)
if issues:
    print(f"ISSUES FOUND ({len(issues)}):")
    for i in issues:
        print(f"  ⚠ {i}")
    sys.exit(1)
else:
    completed = len(glob.glob(f"{RD}/ruler_v2fix_*/ruler_details_*.csv"))
    expected = 27  # 3 models × 3 seeds × 3 contexts
    print(f"ALL OK — {completed}/{expected} results validated, 0 issues")
    sys.exit(0)
