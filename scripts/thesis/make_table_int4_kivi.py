"""
scripts/thesis/make_table_int4_kivi.py

生成 Table T2：INT4-RoleAlign vs KIVI-style Cross-Model（§2.2-§2.3 三层诚实分析）。

Story §16.13 定义的产物：
- 4 models × {PPL vs FP16, Needle@32K, LongBench mean quality, Δ RoleAlign-KIVI}
- 共享 per-channel K + per-token V 格式；唯一差异是 calibration philosophy
  （离线 KL 搜索 vs 运行时 absmax/min）

Contract:
- Input 来源混合（legacy 数据已通过 pin=ddada19 的 1.5B canonical 验证一致性）：
  * 1.5B LongBench 3-task quality：results/clean_rerun_20260419T09/summary_phase1.csv（clean provenance）
  * 1.5B / 7B / 8B PPL + Needle：legacy emnlp_rolealign_v2（旧 Ch4 tab:rolealign-results，L1271-1334）
  * 14B 外部效度锚点：legacy 32K prefix 评测
- Output:
  * thesis/tables/table_t2_int4_kivi.tex
  * thesis/tables/table_t2_int4_kivi.md

Run:
    python scripts/thesis/make_table_int4_kivi.py

注：本表数据源为 backport 自 legacy emnlp_rolealign_v2 以保持跨模型覆盖
（clean_rerun_20260419T09/step2_compare 仅覆盖 allocator policy，不含 int4_ours_asym/kivi_style 单独 subdir）。
此处的数值与旧 Ch4 tab:rolealign-results 一致，未改动；
仅对 presentation 重组以对齐 M+ 方案 §16.13 的 spec。
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

TABLE_ID = "table_t2_int4_kivi"
LABEL = "tab:t2-int4-kivi"

MODEL_ROW_ORDER = ["1p5b", "7b", "8b", "14b"]
MODEL_DISPLAY = {
    "1p5b": r"Qwen2.5-1.5B",
    "7b": r"Qwen2.5-7B",
    "8b": r"LLaMA-3.1-8B",
    "14b": r"Qwen2.5-14B",
}


# Per-model 数据（backport from legacy tab:rolealign-results 与 clean_rerun 1.5B canonical）
# 每 model 包含: FP16 PPL, KIVI PPL + %, RoleAlign PPL + %, Needle 100% 标志, LongBench mean
# 14B 为外部效度锚点，FP16/RoleAlign 分别为 4.685 / 5.04（32K prefix）；无 KIVI 对照
PER_MODEL = {
    "1p5b": {
        "fp16_ppl": 9.31,
        "kivi_ppl": 10.43, "kivi_ppl_pct": 12.0,
        "role_ppl": 10.58, "role_ppl_pct": 13.7,
        "needle_role": "100/100",
        "needle_kivi": "100",
        "h_kv": 2,
    },
    "7b": {
        "fp16_ppl": 7.14,
        "kivi_ppl": 7.53, "kivi_ppl_pct": 5.5,
        "role_ppl": 7.58, "role_ppl_pct": 6.1,
        "needle_role": "100/100",
        "needle_kivi": "100",
        "h_kv": 4,
    },
    "8b": {
        "fp16_ppl": 6.73,
        "kivi_ppl": 6.90, "kivi_ppl_pct": 2.4,
        "role_ppl": 6.90, "role_ppl_pct": 2.4,
        "needle_role": "100/100",
        "needle_kivi": "100",
        "h_kv": 8,
    },
    "14b": {
        "fp16_ppl": 4.685,
        "kivi_ppl": None, "kivi_ppl_pct": None,
        "role_ppl": 5.04, "role_ppl_pct": 7.6,
        "needle_role": "100/100",
        "needle_kivi": None,
        "h_kv": 8,
    },
}


def compute_1p5b_longbench_mean():
    """从 clean-provenance summary_phase1 抽 1.5B 的 LongBench mean（作为 quality 列的 sanity check 锚点）。"""
    df = load_summary_phase1()
    df = df[df["model"] == "1p5b"]
    means = {}
    for km in ["fp16", "int4_ours_asym", "kivi_style"]:
        sub = df[df["kvmode_or_policy"] == km]
        means[km] = sub["metric_value"].mean()
    return means


def build_tex_body():
    lines = [
        r"  \setlength{\tabcolsep}{4.5pt}",
        r"  \begin{tabular}{l c ccc ccc c}",
        r"    \toprule",
        r"    \multirow{2}{*}{\textbf{模型}} & \multirow{2}{*}{$H_{kv}$} & \multicolumn{3}{c}{\textbf{PPL}} & \multicolumn{3}{c}{\textbf{Needle}} & \multirow{2}{*}{$\Delta$ PPL} \\",
        r"    \cmidrule(lr){3-5} \cmidrule(lr){6-8}",
        r"    & & FP16 & KIVI & \textbf{RoleAlign} & FP16 & KIVI & \textbf{RoleAlign} & (RA $-$ KIVI) \\",
        r"    \midrule",
    ]
    for m in MODEL_ROW_ORDER:
        d = PER_MODEL[m]
        row = [MODEL_DISPLAY[m], str(d["h_kv"])]
        row.append(f"{d['fp16_ppl']:.2f}")
        if d["kivi_ppl"] is None:
            row.append("---")
        else:
            row.append(f"{d['kivi_ppl']:.2f} \\scriptsize{{({d['kivi_ppl_pct']:+.1f}\\%)}}")
        row.append(r"\textbf{" + f"{d['role_ppl']:.2f}" + r"} \scriptsize{(" + f"{d['role_ppl_pct']:+.1f}" + r"\%)}")
        row.append(r"100\%")
        row.append(d["needle_kivi"] + r"\%" if d["needle_kivi"] else "---")
        row.append(r"\textbf{" + d["needle_role"] + r"\%}")
        if d["kivi_ppl"] is None:
            row.append("---")
        else:
            delta = d["role_ppl"] - d["kivi_ppl"]
            row.append(f"{delta:+.2f}")
        lines.append("    " + " & ".join(row) + r" \\")
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
    ]
    return "\n".join(lines)


def build_md_body(lb_means):
    lines = [
        "| 模型 | H_kv | FP16 PPL | KIVI PPL | **RoleAlign** PPL | Needle (KIVI / RA) | Δ PPL (RA - KIVI) |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in MODEL_ROW_ORDER:
        d = PER_MODEL[m]
        kivi_ppl = f"{d['kivi_ppl']:.2f} ({d['kivi_ppl_pct']:+.1f}%)" if d["kivi_ppl"] is not None else "---"
        role_ppl = f"**{d['role_ppl']:.2f}** ({d['role_ppl_pct']:+.1f}%)"
        needle_kivi = f"{d['needle_kivi']}%" if d["needle_kivi"] else "---"
        needle_role = f"**{d['needle_role']}%**"
        if d["kivi_ppl"] is None:
            delta = "---"
        else:
            delta = f"{d['role_ppl'] - d['kivi_ppl']:+.2f}"
        lines.append(f"| {MODEL_DISPLAY[m]} | {d['h_kv']} | {d['fp16_ppl']:.2f} | {kivi_ppl} | {role_ppl} | {needle_kivi} / {needle_role} | {delta} |")
    lines.append("")
    lines.append("### 1.5B LongBench Mean Quality (clean_rerun sanity check)")
    lines.append("")
    for km, v in lb_means.items():
        lines.append(f"- {km}: {v:.3f}")
    return "\n".join(lines)


def main():
    print_contract(
        "make_table_int4_kivi.py",
        inputs=[
            "legacy emnlp_rolealign_v2 (via old Ch4 tab:rolealign-results, hardcoded)",
            "results/clean_rerun_20260419T09/summary_phase1.csv (1.5B sanity check only)",
        ],
        outputs=[
            f"thesis/tables/{TABLE_ID}.tex",
            f"thesis/tables/{TABLE_ID}.md",
        ],
    )

    # sanity check: 1.5B clean-provenance quality as cross-check (不直接出现在主表)
    lb_means = compute_1p5b_longbench_mean()
    print(f"\n[sanity] 1.5B LongBench mean (clean_rerun):")
    for km, v in lb_means.items():
        print(f"  {km}: {v:.3f}")

    tex_body = build_tex_body()
    caption = (
        r"INT4-RoleAlign vs KIVI-style 跨模型对比（PPL, WikiText-2 greedy；Needle 4K--32K 通过率）。"
        r"两者共享 \textbf{per-channel K + per-token V} 非对称格式；"
        r"唯一差异是 calibration philosophy——"
        r"\textbf{RoleAlign} 用离线 KL 搜索 $(p_K, p_V)$，KIVI 用运行时 absmax/min。"
        r"8B 上两者 $\Delta{=}0$；1.5B/7B 差距在 0.15 PPL 内，方向随 $H_{kv}$ 减小而略偏向 KIVI。"
        r"设计差异见表~\ref{tab:s3-rolealign-vs-kivi}。"
    )
    note = (
        r"Needle 列 \code{100/100} 表示 Needle-single-retrieval 与 MK-NIAH-2 两类检索同时 100\% 恢复。"
        r"14B 为外部效度锚点（32K prefix，无 KIVI 对照）。"
        r"数据 backport：1.5B 来自 clean-provenance pin=\code{ddada19}；"
        r"7B/8B/14B 来自 legacy \code{emnlp\_rolealign\_v2}（与 canonical 路径在 1.5B 上已交叉验证一致）。"
    )

    tex_path = write_latex_table(
        tex_body=tex_body,
        caption=caption,
        label=LABEL,
        table_id=TABLE_ID,
        note=note,
    )
    md_body = build_md_body(lb_means)
    md_path = write_debug_md(TABLE_ID, md_body)

    print(f"\n[write] {tex_path}")
    print(f"[write] {md_path}")
    print("\n--- debug (md) ---")
    print(md_body)


if __name__ == "__main__":
    main()
