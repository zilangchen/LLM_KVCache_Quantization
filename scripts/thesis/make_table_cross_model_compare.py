"""
scripts/thesis/make_table_cross_model_compare.py

生成 Table T3：Cross-Model Compare Main Table（C3 regime map 主证据，story §16.14 ⭐⭐）。

结构:
- 4 blocks (每个 model 一个) × 3 core tasks × 4 policy
- Policies: uniform_int4_k4v4 / bakv_k<best> / heuristic_k<best> / bakv_auto_cov80_max
- Per-model best-k (from clean_rerun step2_compare):
  3B → k1 / 8B → k11 / 14B → k7 / Mistral-7B → k3
- 每行加粗 per-(model, task) best policy
- 每 block 末: model mean 行
- Caption 强调 "no single winner across models" → regime map

Contract:
- Input:  results/clean_rerun_20260419T09/summary_final.csv (step=2_compare, 48 rows)
- Output: thesis/tables/table_t3_cross_model_main.{tex,md}

Run:
    python scripts/thesis/make_table_cross_model_compare.py
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

TABLE_ID = "table_t3_cross_model_main"
LABEL = "tab:t3-cross-model-main"

MODEL_ROW_ORDER = ["3b", "8b", "14b", "mistral7b"]
MODEL_DISPLAY = {
    "3b": r"Qwen2.5-3B ($H_{kv}{=}2$)",
    "8b": r"Llama-3.1-8B ($H_{kv}{=}8$)",
    "14b": r"Qwen2.5-14B ($H_{kv}{=}8$)",
    "mistral7b": r"Mistral-7B-v0.3 ($H_{kv}{=}8$)",
}

# Per-model best-k from clean_rerun step2_compare
PER_MODEL_BEST_K = {
    "3b": "bakv_k1",
    "8b": "bakv_k11",
    "14b": "bakv_k7",
    "mistral7b": "bakv_k3",
}
PER_MODEL_HEUR_K = {
    "3b": "heuristic_k1",
    "8b": "heuristic_k11",
    "14b": "heuristic_k7",
    "mistral7b": "heuristic_k3",
}
PER_MODEL_AUTOK = {
    "3b": "bakv_auto_cov80_max",
    "8b": "bakv_auto_cov80_max",
    "14b": "bakv_auto_cov90_max",  # 注：14b 实际用 cov90 不是 cov80
    "mistral7b": "bakv_auto_cov80_max",
}

TASK_ORDER = ["narrativeqa", "hotpotqa", "gov_report"]
TASK_DISPLAY = {
    "narrativeqa": "NarrativeQA",
    "hotpotqa": "HotpotQA",
    "gov_report": "GovReport",
}
TASK_METRIC_DISPLAY = {
    "narrativeqa": "F1",
    "hotpotqa": "F1",
    "gov_report": "Rouge-L",
}

POLICY_HEADER = {
    "uniform_int4_k4v4": r"Uniform",
    "bakv_fixed": r"\textbf{BA-$k$}",
    "heuristic_fixed": r"Heuristic-$k$",
    "bakv_auto": r"\textbf{BA-AutoK}",
}

POLICY_ORDER = ["uniform_int4_k4v4", "bakv_fixed", "heuristic_fixed", "bakv_auto"]


def build_pivot(df):
    """df (long-format, step2_compare only) → dict[(model, task, policy_canonical)] = metric_value."""
    df = df[df["step"] == "2_compare"]
    pivot = {}
    for _, row in df.iterrows():
        model = row["model"]
        policy_raw = row["kvmode_or_policy"]
        task = row["task"]
        val = float(row["metric_value"])

        # 把每模型的 bakv_k<best> / heuristic_k<best> / bakv_auto_cov* 映射为 canonical 列名
        if policy_raw == "uniform_int4_k4v4":
            canonical = "uniform_int4_k4v4"
        elif policy_raw == PER_MODEL_BEST_K.get(model):
            canonical = "bakv_fixed"
        elif policy_raw == PER_MODEL_HEUR_K.get(model):
            canonical = "heuristic_fixed"
        elif policy_raw == PER_MODEL_AUTOK.get(model):
            canonical = "bakv_auto"
        else:
            continue  # 忽略其它 policy variants（不进主表）
        pivot[(model, task, canonical)] = val
    return pivot


def find_best(pivot, model, task):
    """返回 (model, task) 下分数最高的 policy canonical。"""
    vals = {p: pivot.get((model, task, p)) for p in POLICY_ORDER}
    vals = {p: v for p, v in vals.items() if v is not None}
    return max(vals, key=vals.get)


def build_tex_body(pivot):
    lines = [
        r"  \setlength{\tabcolsep}{5pt}",
        r"  \begin{tabular}{l l cccc}",
        r"    \toprule",
        r"    \textbf{模型} & \textbf{Task (metric)} & " + " & ".join(POLICY_HEADER[p] for p in POLICY_ORDER) + r" \\",
        r"    \midrule",
    ]
    for m in MODEL_ROW_ORDER:
        # best-k subscript 动态显示
        best_k = PER_MODEL_BEST_K[m].split("_")[-1]
        heur_k = PER_MODEL_HEUR_K[m].split("_")[-1]
        best_hdr_fixed = f"\\textbf{{BA-{best_k}}}"
        best_hdr_heur = f"Heuristic-{best_k}"
        autok_name = PER_MODEL_AUTOK[m].replace("bakv_auto_", "").replace("_max", "")
        best_hdr_auto = f"\\textbf{{BA-auto-{autok_name}}}"

        # model row with custom best-k in first row of block
        first = True
        block_means = {p: [] for p in POLICY_ORDER}
        for task in TASK_ORDER:
            best_p = find_best(pivot, m, task)
            cells = []
            if first:
                cells.append(r"\multirow{4}{*}{" + MODEL_DISPLAY[m] + r"}")
                first = False
            else:
                cells.append("")
            cells.append(f"{TASK_DISPLAY[task]} ({TASK_METRIC_DISPLAY[task]})")
            for p in POLICY_ORDER:
                val = pivot.get((m, task, p))
                if val is None:
                    cells.append("---")
                    continue
                block_means[p].append(val)
                s = f"{val:.2f}"
                if p == best_p:
                    s = r"\textbf{" + s + r"}"
                cells.append(s)
            lines.append("    " + " & ".join(cells) + r" \\")

        # mean row
        best_mean_p = max(
            {p: sum(vs) / len(vs) for p, vs in block_means.items() if vs},
            key=lambda x: sum(block_means[x]) / len(block_means[x]),
        )
        mean_cells = ["", r"\textit{Mean}"]
        for p in POLICY_ORDER:
            if block_means[p]:
                m_val = sum(block_means[p]) / len(block_means[p])
                s = f"{m_val:.2f}"
                if p == best_mean_p:
                    s = r"\textbf{" + s + r"}"
                mean_cells.append(r"\textit{" + s + r"}")
            else:
                mean_cells.append("---")
        lines.append("    " + " & ".join(mean_cells) + r" \\")

        # 展开 header legend 到 caption-adjacent note (手动记录 best-k)
        header_ref_lines = []
        header_ref_lines.append(f"% {m}: BA-k* = {best_hdr_fixed}, heuristic-k* = {best_hdr_heur}, auto = {best_hdr_auto}")
        lines.extend(["    " + l for l in header_ref_lines])
        if m != MODEL_ROW_ORDER[-1]:
            lines.append(r"    \midrule")
    lines.append(r"    \bottomrule")
    lines.append(r"  \end{tabular}")
    return "\n".join(lines)


def build_md_body(pivot):
    lines = ["# T3 Cross-Model Main (debug)"]
    for m in MODEL_ROW_ORDER:
        lines.append("")
        lines.append(f"## {MODEL_DISPLAY[m]}  (best-k: {PER_MODEL_BEST_K[m]}, heur-k: {PER_MODEL_HEUR_K[m]}, autok: {PER_MODEL_AUTOK[m]})")
        lines.append("")
        lines.append("| Task | Uniform | **BA-k** | Heuristic-k | **BA-AutoK** | Winner |")
        lines.append("|---|---|---|---|---|---|")
        for task in TASK_ORDER:
            best_p = find_best(pivot, m, task)
            row = [f"{TASK_DISPLAY[task]} ({TASK_METRIC_DISPLAY[task]})"]
            for p in POLICY_ORDER:
                val = pivot.get((m, task, p))
                cell = "---" if val is None else f"{val:.2f}"
                if p == best_p:
                    cell = f"**{cell}**"
                row.append(cell)
            winner_map = {"uniform_int4_k4v4": "Uniform", "bakv_fixed": "BA-k", "heuristic_fixed": "Heur-k", "bakv_auto": "AutoK"}
            row.append(winner_map.get(best_p, "?"))
            lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def main():
    print_contract(
        "make_table_cross_model_compare.py",
        inputs=["results/clean_rerun_20260419T09/summary_final.csv (step=2_compare, 48 rows)"],
        outputs=[f"thesis/tables/{TABLE_ID}.tex", f"thesis/tables/{TABLE_ID}.md"],
    )
    df = load_summary_final()
    print(f"\n[data] loaded {len(df)} rows")
    pivot = build_pivot(df)
    print(f"[data] pivot filled {len(pivot)} cells (expected 4 model × 3 task × 4 policy = 48)")
    assert len(pivot) == 48, f"expected 48, got {len(pivot)}"

    tex_body = build_tex_body(pivot)
    caption = (
        r"Cross-model policy comparison under matched INT4 budget (clean-provenance pin=\code{ddada19})。"
        r"\textbf{加粗}标注 per-(model, task) 最优 policy；\textit{Mean} 为 block 内 3 task 均值。"
        r"Per-model best-$k$ 动态选择：3B 用 $k{=}1$、Llama-3.1-8B 用 $k{=}11$、14B 用 $k{=}7$、Mistral-7B 用 $k{=}3$；"
        r"AutoK 的 \code{cov} 阈值：14B 用 \code{cov90}，其余用 \code{cov80}。"
        r"四模型的 winner policy 不一致——这是本章 \textbf{(family, scale, task)-dependent regime map} 的直接证据。"
    )
    note = (
        r"matched INT4 budget：所有 policy 在本表内 KV memory 近似相等（$\pm 3\%$），详见配套图~\ref{fig:t7-pareto}。"
        r"Uniform 指 \code{uniform\_int4\_k4v4}（所有层 K/V 统一 INT4）；"
        r"BA-$k$ 指 behavior-guided allocator 保护 top-$k$ 高敏感层；"
        r"Heuristic-$k$ 指等距位置启发式保护 $k$ 层；"
        r"BA-AutoK 指 profile-guided cov$x$\% coverage 自动决定 budget。"
    )

    tex_path = write_latex_table(
        tex_body=tex_body, caption=caption, label=LABEL,
        table_id=TABLE_ID, note=note,
    )
    md_body = build_md_body(pivot)
    md_path = write_debug_md(TABLE_ID, md_body)
    print(f"\n[write] {tex_path}")
    print(f"[write] {md_path}")
    print("\n--- debug (md) first 30 lines ---")
    print("\n".join(md_body.split("\n")[:30]))


if __name__ == "__main__":
    main()
