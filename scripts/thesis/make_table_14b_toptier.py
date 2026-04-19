"""
scripts/thesis/make_table_14b_toptier.py

生成 Table T6：Qwen2.5-14B Top-Tier Distribution（story §5.4 定量化"no stable winner"）。

结构:
- 行: 3 core tasks
- 列: 4 policies — uniform / bakv_k7 / heuristic_k7 / bakv_auto_cov90
- 加粗 per-task top-3 分数
- 表末: "top-3 within X% of top-1" 统计 + gap 摘要

Contract:
- Input:  summary_final.csv (14b step=2_compare)
- Output: thesis/tables/table_t6_14b_toptier.{tex,md}
"""

from __future__ import annotations

import sys
import pathlib
import numpy as np

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _common import (  # noqa: E402
    load_summary_final,
    write_latex_table,
    write_debug_md,
    print_contract,
)

TABLE_ID = "table_t6_14b_toptier"
LABEL = "tab:t6-14b-toptier"
MODEL = "14b"

TASK_ORDER = ["narrativeqa", "hotpotqa", "gov_report"]
TASK_DISPLAY = {
    "narrativeqa": "NarrativeQA (F1)",
    "hotpotqa": "HotpotQA (F1)",
    "gov_report": "GovReport (Rouge-L)",
}

POLICY_ORDER = ["uniform_int4_k4v4", "bakv_k7", "heuristic_k7", "bakv_auto_cov90_max"]
POLICY_HDR = {
    "uniform_int4_k4v4":    r"Uniform",
    "bakv_k7":              r"BA-$k_7$",
    "heuristic_k7":         r"Heur-$k_7$",
    "bakv_auto_cov90_max":  r"BA-AutoK (cov90)",
}


def main():
    print_contract(
        "make_table_14b_toptier.py",
        inputs=["summary_final.csv (14b step=2_compare)"],
        outputs=[f"thesis/tables/{TABLE_ID}.tex", f"thesis/tables/{TABLE_ID}.md"],
    )
    df = load_summary_final()
    df = df[(df["model"] == MODEL) & (df["step"] == "2_compare") & (df["task"].isin(TASK_ORDER))]
    pivot = {(r["task"], r["kvmode_or_policy"]): float(r["metric_value"]) for _, r in df.iterrows()}

    lines = [
        r"  \setlength{\tabcolsep}{5pt}",
        r"  \begin{tabular}{l cccc}",
        r"    \toprule",
        r"    \textbf{Task} & " + " & ".join(POLICY_HDR[p] for p in POLICY_ORDER) + r" \\",
        r"    \midrule",
    ]
    per_task_gaps = []  # relative gap top-1 vs top-3
    for task in TASK_ORDER:
        vals = {p: pivot.get((task, p)) for p in POLICY_ORDER}
        valid = {p: v for p, v in vals.items() if v is not None}
        sorted_vals = sorted(valid.values(), reverse=True)
        top1 = sorted_vals[0]
        top3_last = sorted_vals[2] if len(sorted_vals) >= 3 else sorted_vals[-1]
        gap_rel = (top1 - top3_last) / max(top1, 1e-6) * 100
        per_task_gaps.append(gap_rel)
        # mark top-3 bold
        sorted_policies = sorted(valid.items(), key=lambda x: -x[1])
        top3_policies = set(p for p, v in sorted_policies[:3])
        row = [TASK_DISPLAY[task]]
        for p in POLICY_ORDER:
            v = vals[p]
            if v is None:
                row.append("---")
                continue
            s = f"{v:.2f}"
            if p in top3_policies:
                s = r"\textbf{" + s + r"}"
            row.append(s)
        lines.append("    " + " & ".join(row) + r" \\")
    lines.append(r"    \midrule")
    # Mean row
    mean_cells = [r"\textit{Mean}"]
    for p in POLICY_ORDER:
        vs = [pivot.get((t, p)) for t in TASK_ORDER if pivot.get((t, p)) is not None]
        if vs:
            mean_cells.append(r"\textit{" + f"{sum(vs)/len(vs):.2f}" + r"}")
        else:
            mean_cells.append("---")
    lines.append("    " + " & ".join(mean_cells) + r" \\")
    lines.append(r"    \bottomrule")
    lines.append(r"  \end{tabular}")
    tex_body = "\n".join(lines)

    # top-3 within gap summary
    max_gap = max(per_task_gaps)
    avg_gap = sum(per_task_gaps) / len(per_task_gaps)

    caption = (
        r"Qwen2.5-14B top-tier 分布（story §5.4 "
        r"\textit{top-tier but no stable winner} 定量化）。"
        r"\textbf{加粗}：每 task 的 top-3 policy。"
        r"Top-3 policies 相对 top-1 的最大 relative gap 为 "
        + f"{max_gap:.1f}\\%，平均 {avg_gap:.1f}\\%——"
        r"即 14B 上多 policy 挤在高 quality 区间内，"
        r"不存在 clear across-task winner。"
    )
    note = (
        r"\textbf{relative gap}：$(top_1 - top_3) / top_1$。"
        r"由于 gap 量级在 bootstrap CI 半宽内，"
        r"14B top-tier 的 "
        r"policy 之间 statistical distinguishability 需 $n{=}5$ seed CI 叠加判定——"
        r"因样本量小 $p$-值接近 sign-flip 下界，读作 "
        r"\emph{inconclusive at this power}。"
    )
    tex_path = write_latex_table(
        tex_body=tex_body, caption=caption, label=LABEL, table_id=TABLE_ID, note=note,
    )
    md_lines = [f"# T6 14B Top-Tier (debug)", f"top-3 gaps: {[f'{g:.1f}%' for g in per_task_gaps]}, max={max_gap:.2f}%", ""]
    md_lines.append("| Task | " + " | ".join(POLICY_HDR[p] for p in POLICY_ORDER) + " |")
    md_lines.append("|" + "---|" * (len(POLICY_ORDER) + 1))
    for task in TASK_ORDER:
        row = [TASK_DISPLAY[task]]
        for p in POLICY_ORDER:
            v = pivot.get((task, p))
            row.append(f"{v:.2f}" if v else "---")
        md_lines.append("| " + " | ".join(row) + " |")
    md_path = write_debug_md(TABLE_ID, "\n".join(md_lines))
    print(f"\n[write] {tex_path}\n[write] {md_path}")
    print(f"[stat] 14B top-3 gaps: max={max_gap:.2f}%, avg={avg_gap:.2f}%")


if __name__ == "__main__":
    main()
