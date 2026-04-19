"""
scripts/thesis/make_table_3b_early_layer.py

生成 Table T5：Qwen2.5-3B Early-Layer Rescue（story §5.2）。

结构:
- 行: 3 core tasks
- 列: 4 policies — bakv_k1 (protect layer 0-2 region) / heuristic_k1 / bakv_k3 / uniform
- 加粗 bakv_k1 vs heuristic_k1 的 Δ (该 Δ 是 catastrophic)
- Footnote: 强调 heuristic_k1 在 NarrativeQA/HotpotQA 上 catastrophic

Contract:
- Input:  results/clean_rerun_20260419T09/summary_final.csv (3b step=2_compare)
- Output: thesis/tables/table_t5_3b_early_layer.{tex,md}
"""

from __future__ import annotations

import sys
import pathlib

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _common import (  # noqa: E402
    load_summary_final,
    write_latex_table,
    write_debug_md,
    print_contract,
)

TABLE_ID = "table_t5_3b_early_layer"
LABEL = "tab:t5-3b-early-layer"
MODEL = "3b"

TASK_ORDER = ["narrativeqa", "hotpotqa", "gov_report"]
TASK_DISPLAY = {
    "narrativeqa": "NarrativeQA (F1)",
    "hotpotqa": "HotpotQA (F1)",
    "gov_report": "GovReport (Rouge-L)",
}

POLICY_ORDER = ["bakv_k1", "heuristic_k1", "bakv_auto_cov80_max", "uniform_int4_k4v4"]
POLICY_HDR = {
    "bakv_k1":              r"\textbf{BA-$k_1$}",
    "heuristic_k1":         r"Heur-$k_1$",
    "bakv_auto_cov80_max":  r"BA-AutoK",
    "uniform_int4_k4v4":    r"Uniform",
}


def main():
    print_contract(
        "make_table_3b_early_layer.py",
        inputs=["summary_final.csv (3b step=2_compare)"],
        outputs=[f"thesis/tables/{TABLE_ID}.tex", f"thesis/tables/{TABLE_ID}.md"],
    )
    df = load_summary_final()
    df = df[(df["model"] == MODEL) & (df["step"] == "2_compare") & (df["task"].isin(TASK_ORDER))]
    pivot = {(r["task"], r["kvmode_or_policy"]): float(r["metric_value"]) for _, r in df.iterrows()}

    lines = [
        r"  \setlength{\tabcolsep}{6pt}",
        r"  \begin{tabular}{l cccc c}",
        r"    \toprule",
        r"    \textbf{Task} & " + " & ".join(POLICY_HDR[p] for p in POLICY_ORDER) + r" & $\Delta$ (BA$-$Heur) \\",
        r"    \midrule",
    ]
    deltas = []
    for task in TASK_ORDER:
        vals = [pivot.get((task, p)) for p in POLICY_ORDER]
        valid = [v for v in vals if v is not None]
        best = max(valid) if valid else None
        row = [TASK_DISPLAY[task]]
        for p, v in zip(POLICY_ORDER, vals):
            if v is None:
                row.append("---")
                continue
            s = f"{v:.2f}"
            if best is not None and abs(v - best) < 1e-6:
                s = r"\textbf{" + s + r"}"
            row.append(s)
        ba = pivot.get((task, "bakv_k1"))
        heur = pivot.get((task, "heuristic_k1"))
        if ba is not None and heur is not None:
            d = ba - heur
            deltas.append(d)
            if d > 2.0:
                row.append(r"\textcolor{red}{+" + f"{d:.2f}" + r"}")
            else:
                row.append(f"{d:+.2f}")
        else:
            row.append("---")
        lines.append("    " + " & ".join(row) + r" \\")
    lines.append(r"    \midrule")
    # 均值行
    mean_row = [r"\textit{Mean}"]
    for p in POLICY_ORDER:
        vs = [pivot.get((t, p)) for t in TASK_ORDER if pivot.get((t, p)) is not None]
        if vs:
            mean_row.append(r"\textit{" + f"{sum(vs)/len(vs):.2f}" + r"}")
        else:
            mean_row.append("---")
    if deltas:
        mean_row.append(r"\textit{" + f"{sum(deltas)/len(deltas):+.2f}" + r"}")
    else:
        mean_row.append("---")
    lines.append("    " + " & ".join(mean_row) + r" \\")
    lines.append(r"    \bottomrule")
    lines.append(r"  \end{tabular}")
    tex_body = "\n".join(lines)

    caption = (
        r"Qwen2.5-3B 的 early-layer rescue regime（story §5.2）。"
        r"\textbf{BA-$k_1$}（保护 layer 0，对应图~\ref{fig:sensitivity-heatmap} 的 3B top-1 protected layer）"
        r"相对 \textbf{Heur-$k_1$}（等距保护中层）呈现 catastrophic Δ——"
        r"heuristic 在 NarrativeQA / HotpotQA 上量化几乎完全失效，"
        r"而 behavior-guided 的单层保护把大部分 quality 捡回来。"
        r"这是跨模型里 behavior vs heuristic 差距最大的模型。"
    )
    note = (
        r"$\Delta$ 列为 BA-$k_1$ 减 Heur-$k_1$ 的分差，红色表示差距 $>2$ 分。"
        r"heuristic\_$k_1$ 在 3B 上保护中层（layer$\approx L/2$）；"
        r"而 3B behavior sensitivity profile 早层集中，"
        r"因此中层保护对量化回救几乎没有作用。"
    )
    tex_path = write_latex_table(
        tex_body=tex_body, caption=caption, label=LABEL, table_id=TABLE_ID, note=note,
    )
    md_lines = [f"# T5 3B Early-Layer Rescue (debug)", ""]
    md_lines.append("| Task | BA-k1 | Heur-k1 | AutoK | Uniform | Δ (BA-Heur) |")
    md_lines.append("|---|---|---|---|---|---|")
    for task in TASK_ORDER:
        vals = [pivot.get((task, p)) for p in POLICY_ORDER]
        ba = pivot.get((task, "bakv_k1"))
        heur = pivot.get((task, "heuristic_k1"))
        d = f"{ba - heur:+.2f}" if ba is not None and heur is not None else "---"
        md_lines.append(f"| {TASK_DISPLAY[task]} | {' | '.join(f'{v:.2f}' if v else '---' for v in vals)} | {d} |")
    md_path = write_debug_md(TABLE_ID, "\n".join(md_lines))
    print(f"\n[write] {tex_path}\n[write] {md_path}")


if __name__ == "__main__":
    main()
