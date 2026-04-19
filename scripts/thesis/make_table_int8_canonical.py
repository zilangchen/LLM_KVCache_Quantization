"""
scripts/thesis/make_table_int8_canonical.py

生成 Table T1：INT8 Canonical Path Fidelity（Qwen2.5-1.5B, clean-provenance pin=ddada19）。

Story §2.1 / §16.12 定义的产物：
- 3 tasks (NarrativeQA F1 / HotpotQA F1 / GovReport Rouge-L) × 4 kv_mode (FP16 / INT8-ours / INT4-RoleAlign / KIVI-style)
- 每 task 下列出每 kv_mode 的分数与 Δ vs FP16
- 末尾 mean across tasks 行，加粗 int8_ours mean Δ（应约等于 +0.02，对应 story §2.1 核心 claim）

Contract:
- Input:  results/clean_rerun_20260419T09/summary_phase1.csv（12 行，long-format）
- Output: thesis/tables/table_t1_int8_canonical.tex + thesis/tables/table_t1_int8_canonical.md

Run:
    python scripts/thesis/make_table_int8_canonical.py
"""

from __future__ import annotations

import sys
import pathlib

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _common import (  # noqa: E402
    load_summary_phase1,
    write_latex_table,
    write_debug_md,
    print_contract,
)

TABLE_ID = "table_t1_int8_canonical"
LABEL = "tab:t1-int8-canonical"

KV_MODE_ORDER = ["fp16", "int8_ours", "int4_ours_asym", "kivi_style"]
KV_MODE_HEADER = {
    "fp16": "FP16",
    "int8_ours": r"\textbf{INT8-ours}",
    "int4_ours_asym": r"INT4-RoleAlign",
    "kivi_style": r"KIVI-style",
}

TASK_ORDER = ["narrativeqa", "hotpotqa", "gov_report"]
TASK_DISPLAY = {
    "narrativeqa": r"NarrativeQA (F1)",
    "hotpotqa": r"HotpotQA (F1)",
    "gov_report": r"GovReport (Rouge-L)",
}


def build_pivot(df):
    """df (long-format) → dict[(task, kv_mode)] = metric_value。1.5B only。"""
    df = df[df["model"] == "1p5b"]
    pivot = {}
    for _, row in df.iterrows():
        pivot[(row["task"], row["kvmode_or_policy"])] = float(row["metric_value"])
    return pivot


def build_tex_rows(pivot):
    """构造 body rows：3 task 行 + mean 行。"""
    rows = []

    for task in TASK_ORDER:
        fp16_val = pivot[(task, "fp16")]
        cells = [TASK_DISPLAY[task]]
        for km in KV_MODE_ORDER:
            val = pivot[(task, km)]
            if km == "fp16":
                cells.append(f"{val:.2f}")
            else:
                delta = val - fp16_val
                sign = "+" if delta >= 0 else ""
                cells.append(f"{val:.2f} \\scriptsize{{({sign}{delta:.2f})}}")
        rows.append(" & ".join(cells) + r" \\")

    # mean row
    mean_cells = [r"\midrule" + "\n    " + r"\textbf{Mean}"]
    fp16_mean = sum(pivot[(t, "fp16")] for t in TASK_ORDER) / len(TASK_ORDER)
    for km in KV_MODE_ORDER:
        km_mean = sum(pivot[(t, km)] for t in TASK_ORDER) / len(TASK_ORDER)
        if km == "fp16":
            mean_cells.append(r"\textbf{" + f"{km_mean:.2f}" + r"}")
        else:
            delta = km_mean - fp16_mean
            sign = "+" if delta >= 0 else ""
            cell = f"{km_mean:.2f} \\scriptsize{{({sign}{delta:.2f})}}"
            if km == "int8_ours":
                cell = r"\textbf{" + cell + r"}"
            mean_cells.append(cell)
    rows.append(" & ".join(mean_cells) + r" \\")
    return rows


def build_tex_body(pivot):
    header = " & ".join(["Task"] + [KV_MODE_HEADER[km] for km in KV_MODE_ORDER]) + r" \\"
    body_rows = build_tex_rows(pivot)
    lines = [
        r"  \begin{tabular}{l" + "c" * len(KV_MODE_ORDER) + r"}",
        r"    \toprule",
        "    " + header,
        r"    \midrule",
        *(f"    {r}" for r in body_rows),
        r"    \bottomrule",
        r"  \end{tabular}",
    ]
    return "\n".join(lines)


def build_md_body(pivot):
    """Markdown 调试版，用于 review diff。"""
    lines = ["| Task | FP16 | INT8-ours | INT4-RoleAlign | KIVI-style |",
             "|---|---|---|---|---|"]
    for task in TASK_ORDER:
        fp16 = pivot[(task, "fp16")]
        row = [TASK_DISPLAY[task], f"{fp16:.2f}"]
        for km in ["int8_ours", "int4_ours_asym", "kivi_style"]:
            val = pivot[(task, km)]
            delta = val - fp16
            row.append(f"{val:.2f} ({delta:+.2f})")
        lines.append("| " + " | ".join(row) + " |")
    # mean row
    fp16_mean = sum(pivot[(t, "fp16")] for t in TASK_ORDER) / len(TASK_ORDER)
    mean_row = ["**Mean**", f"**{fp16_mean:.2f}**"]
    for km in ["int8_ours", "int4_ours_asym", "kivi_style"]:
        km_mean = sum(pivot[(t, km)] for t in TASK_ORDER) / len(TASK_ORDER)
        delta = km_mean - fp16_mean
        marker = "**" if km == "int8_ours" else ""
        mean_row.append(f"{marker}{km_mean:.2f} ({delta:+.2f}){marker}")
    lines.append("| " + " | ".join(mean_row) + " |")
    return "\n".join(lines)


def main():
    print_contract(
        "make_table_int8_canonical.py",
        inputs=["results/clean_rerun_20260419T09/summary_phase1.csv (1.5B × 4 kv_mode × 3 task)"],
        outputs=[
            f"thesis/tables/{TABLE_ID}.tex",
            f"thesis/tables/{TABLE_ID}.md",
        ],
    )

    df = load_summary_phase1()
    print(f"\n[data] loaded {len(df)} rows from summary_phase1.csv")
    pivot = build_pivot(df)
    assert len(pivot) == 12, f"expected 12 cells, got {len(pivot)}"

    tex_body = build_tex_body(pivot)
    caption = (
        r"INT8 Canonical Path 保真度（Qwen2.5-1.5B-Instruct, clean-provenance pin=\code{ddada19}）。"
        r"每单元格为分数，括号内为相对 FP16 的 $\Delta$。"
        r"\textbf{INT8-ours} 的 mean $\Delta$ 加粗展示——这是本章 §2.1 \textit{INT8 canonical path fidelity} 的核心硬证据。"
    )
    note = (
        r"数据来源：\code{results/clean\_rerun\_20260419T09/summary\_phase1.csv}。"
        r"INT4-RoleAlign 与 KIVI-style 在此表仅为 format 参考值，"
        r"完整跨模型对比见表~\ref{tab:t2-int4-kivi}。"
    )

    tex_path = write_latex_table(
        tex_body=tex_body,
        caption=caption,
        label=LABEL,
        table_id=TABLE_ID,
        note=note,
    )
    md_body = build_md_body(pivot)
    md_path = write_debug_md(TABLE_ID, md_body)

    print(f"\n[write] {tex_path}")
    print(f"[write] {md_path}")
    print("\n--- debug (md) ---")
    print(md_body)


if __name__ == "__main__":
    main()
