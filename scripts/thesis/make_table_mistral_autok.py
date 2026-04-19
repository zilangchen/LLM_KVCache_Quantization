"""
scripts/thesis/make_table_mistral_autok.py

生成 Table T4：Mistral-7B AutoK 5-task Detail（story §5.1 strongest AutoK positive case）。

结构:
- Rows: 5 tasks (narrativeqa / hotpotqa / gov_report / dureader / lcc)
- Cols: 4 policies (uniform / bakv_k3 / heuristic_k3 / bakv_auto_cov80_max)
- 每行加粗 task winner；bakv_auto 列整体加粗（story strongest positive case）
- 末尾加 mean 行 + cov80=14.764 注解

Contract:
- Input:  results/clean_rerun_20260419T09/summary_final.csv
         (step=2_compare mistral7b + step=3_extend mistral7b)
- Output: thesis/tables/table_t4_mistral_autok.{tex,md}

Run:
    python scripts/thesis/make_table_mistral_autok.py
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

TABLE_ID = "table_t4_mistral_autok"
LABEL = "tab:t4-mistral-autok"

MODEL = "mistral7b"

TASK_ORDER = ["narrativeqa", "hotpotqa", "gov_report", "dureader", "lcc"]
TASK_DISPLAY = {
    "narrativeqa": "NarrativeQA (F1)",
    "hotpotqa": "HotpotQA (F1)",
    "gov_report": "GovReport (Rouge-L)",
    "dureader": "DuReader (Rouge-L)",
    "lcc": "LCC (EditSim)",
}

POLICY_ORDER = ["uniform_int4_k4v4", "bakv_k3", "heuristic_k3", "bakv_auto_cov80_max"]
POLICY_HDR = {
    "uniform_int4_k4v4":    r"Uniform",
    "bakv_k3":              r"BA-$k_3$",
    "heuristic_k3":         r"Heur-$k_3$",
    "bakv_auto_cov80_max":  r"\textbf{BA-AutoK}",
}


def build_pivot(df):
    df = df[(df["model"] == MODEL) & (df["task"].isin(TASK_ORDER))]
    pivot = {}
    for _, row in df.iterrows():
        pivot[(row["task"], row["kvmode_or_policy"])] = float(row["metric_value"])
    return pivot


def build_tex_body(pivot):
    lines = [
        r"  \setlength{\tabcolsep}{6pt}",
        r"  \begin{tabular}{l cccc}",
        r"    \toprule",
        r"    \textbf{Task} & " + " & ".join(POLICY_HDR[p] for p in POLICY_ORDER) + r" \\",
        r"    \midrule",
    ]
    per_policy_sum = {p: 0.0 for p in POLICY_ORDER}
    per_policy_n = {p: 0 for p in POLICY_ORDER}
    for task in TASK_ORDER:
        cells = [TASK_DISPLAY[task]]
        vals = [pivot.get((task, p)) for p in POLICY_ORDER]
        valid = [v for v in vals if v is not None]
        best = max(valid) if valid else None
        for p, v in zip(POLICY_ORDER, vals):
            if v is None:
                cells.append("---")
                continue
            per_policy_sum[p] += v
            per_policy_n[p] += 1
            s = f"{v:.2f}"
            if best is not None and abs(v - best) < 1e-6:
                s = r"\textbf{" + s + r"}"
            cells.append(s)
        lines.append("    " + " & ".join(cells) + r" \\")
    lines.append(r"    \midrule")
    mean_cells = [r"\textit{Mean}"]
    means = {p: (per_policy_sum[p] / per_policy_n[p] if per_policy_n[p] else None) for p in POLICY_ORDER}
    best_mean = max([m for m in means.values() if m is not None])
    for p in POLICY_ORDER:
        m = means[p]
        if m is None:
            mean_cells.append("---")
            continue
        s = f"{m:.2f}"
        if abs(m - best_mean) < 1e-6:
            s = r"\textbf{" + s + r"}"
        mean_cells.append(r"\textit{" + s + r"}")
    lines.append("    " + " & ".join(mean_cells) + r" \\")
    lines.append(r"    \bottomrule")
    lines.append(r"  \end{tabular}")
    return "\n".join(lines)


def build_md_body(pivot):
    lines = ["# T4 Mistral-7B AutoK 5-Task (debug)", "", "| Task | " + " | ".join(POLICY_HDR[p].replace(r"\textbf{", "**").replace(r"}", "**") for p in POLICY_ORDER) + " |",
             "|" + "---|" * (len(POLICY_ORDER) + 1)]
    for task in TASK_ORDER:
        row = [TASK_DISPLAY[task]]
        vals = [pivot.get((task, p)) for p in POLICY_ORDER]
        valid = [v for v in vals if v is not None]
        best = max(valid) if valid else None
        for v in vals:
            cell = "---" if v is None else f"{v:.2f}"
            if v is not None and best is not None and abs(v - best) < 1e-6:
                cell = f"**{cell}**"
            row.append(cell)
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def main():
    print_contract(
        "make_table_mistral_autok.py",
        inputs=["summary_final.csv (mistral7b step=2+3)"],
        outputs=[f"thesis/tables/{TABLE_ID}.tex", f"thesis/tables/{TABLE_ID}.md"],
    )
    df = load_summary_final()
    pivot = build_pivot(df)
    print(f"\n[data] pivot cells: {len(pivot)} (expected 5×4=20)")
    # 核 AutoK wins count
    wins = 0
    for t in TASK_ORDER:
        vals = {p: pivot.get((t, p)) for p in POLICY_ORDER}
        valid = {p: v for p, v in vals.items() if v is not None}
        if valid and max(valid, key=valid.get) == "bakv_auto_cov80_max":
            wins += 1
    print(f"[stat] AutoK task-wins: {wins}/{len(TASK_ORDER)}")

    tex_body = build_tex_body(pivot)
    caption = (
        r"Mistral-7B-v0.3 上 INT4 预算下的 5-task 细节（clean-provenance pin=\code{ddada19}）。"
        r"\textbf{BA-AutoK}（cov$80$\% coverage）在 5 个 task 中获得最多 task-wise 胜利，"
        r"形成\textbf{单模型最强的 AutoK 正面案例}——"
        r"这是本章 §\ref{subsec:exp-per-model-mistral} 的主证据。"
    )
    note = (
        r"\textbf{Mean} 为 5 task 均值。Uniform 指 \code{uniform\_int4\_k4v4}；"
        r"BA-$k_3$ 指 behavior-guided allocator 保护 top-3 层；"
        r"Heur-$k_3$ 指等距位置启发式保护 3 层；"
        r"BA-AutoK 指 profile-guided cov$80$\% 自动 budget。"
    )
    tex_path = write_latex_table(
        tex_body=tex_body, caption=caption, label=LABEL,
        table_id=TABLE_ID, note=note,
    )
    md_path = write_debug_md(TABLE_ID, build_md_body(pivot))
    print(f"\n[write] {tex_path}")
    print(f"[write] {md_path}")


if __name__ == "__main__":
    main()
