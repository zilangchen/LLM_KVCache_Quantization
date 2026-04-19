"""
scripts/thesis/plot_scale_trend.py

生成图 ⑨：Quality vs Model Scale（story §5 scale 维度独立可视化）。

图结构:
- 1 subplot (已简化自 story §16.8 的 2 subplot 设计，因 PPL 数据源非 canonical
  而 quality task-mean 直接来自 clean_rerun step2)
- x: model scale (log)，4 模型: 3B (2.5B param) / 7B (7.5B) / 8B (8B) / 14B (14B) + Mistral-7B (7.2B)
- y: task-core mean quality
- 多条线: 不同 policy family
  * Uniform INT4
  * BA-k (fixed, per-model best-k)
  * Heuristic-k (fixed)
  * BA-AutoK (cov80/cov90)

Contract:
- Input:  summary_final.csv (step=2_compare)
- Output: thesis/figures/fig9_scale_trend.pdf
"""

from __future__ import annotations

import sys
import pathlib
import numpy as np

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _common import (  # noqa: E402
    load_summary_final,
    set_mpl_style,
    save_figure_pdf,
    print_contract,
    POLICY_COLORS,
    POLICY_MARKERS,
)

FIG_ID = "fig9_scale_trend"

MODEL_X = {
    "3b": 2.5,
    "mistral7b": 7.2,
    "8b": 8.0,
    "14b": 14.0,
}
MODEL_ORDER = ["3b", "mistral7b", "8b", "14b"]
MODEL_LABEL = {
    "3b": "Qwen2.5-3B",
    "mistral7b": "Mistral-7B",
    "8b": "Llama-3.1-8B",
    "14b": "Qwen2.5-14B",
}

PER_MODEL_BEST_K = {
    "3b": "bakv_k1",
    "mistral7b": "bakv_k3",
    "8b": "bakv_k11",
    "14b": "bakv_k7",
}
PER_MODEL_HEUR = {
    "3b": "heuristic_k1",
    "mistral7b": "heuristic_k3",
    "8b": "heuristic_k11",
    "14b": "heuristic_k7",
}
PER_MODEL_AUTO = {
    "3b": "bakv_auto_cov80_max",
    "mistral7b": "bakv_auto_cov80_max",
    "8b": "bakv_auto_cov80_max",
    "14b": "bakv_auto_cov90_max",
}

LINE_DEFS = [
    ("uniform_int4", "Uniform INT4", {m: "uniform_int4_k4v4" for m in MODEL_ORDER}),
    ("bakv_fixed",   "BA-$k_*$ (best per model)", PER_MODEL_BEST_K),
    ("heuristic",    "Heuristic-$k_*$", PER_MODEL_HEUR),
    ("bakv_auto_cov80", "BA-AutoK", PER_MODEL_AUTO),
]

CORE_TASKS = ["narrativeqa", "hotpotqa", "gov_report"]


def main():
    print_contract(
        "plot_scale_trend.py",
        inputs=["summary_final.csv (step=2_compare core 3 tasks)"],
        outputs=[f"thesis/figures/{FIG_ID}.pdf"],
    )
    set_mpl_style()
    import matplotlib.pyplot as plt

    df = load_summary_final()
    df = df[(df["step"] == "2_compare") & (df["task"].isin(CORE_TASKS))]

    fig, ax = plt.subplots(figsize=(7.5, 5))

    for fam_key, label, model2policy in LINE_DEFS:
        xs, ys = [], []
        for m in MODEL_ORDER:
            policy = model2policy[m]
            sub = df[(df["model"] == m) & (df["kvmode_or_policy"] == policy)]
            if sub.empty:
                continue
            xs.append(MODEL_X[m])
            ys.append(sub["metric_value"].mean())
        ax.plot(
            xs, ys,
            marker=POLICY_MARKERS.get(fam_key, "o"),
            color=POLICY_COLORS.get(fam_key, "#888"),
            label=label,
            markersize=9,
            linewidth=1.7,
            markeredgecolor="#333",
            markeredgewidth=0.7,
        )

    ax.set_xscale("log")
    ax.set_xticks([MODEL_X[m] for m in MODEL_ORDER])
    ax.set_xticklabels([f"{MODEL_LABEL[m]}\n{MODEL_X[m]:.1f}B" for m in MODEL_ORDER], fontsize=8)
    ax.set_xlabel(r"Model scale (B params, log-scale)")
    ax.set_ylabel(r"Task-core mean quality")
    ax.set_title(r"Quality across model scale under 4 allocator policies")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=9, frameon=True, framealpha=0.9)

    # annotation for regime shift
    ax.annotate(
        "AutoK 在 Mistral 上远超其他\npolicy（strongest positive）",
        xy=(7.2, 13.5), xytext=(3.2, 13.0),
        arrowprops=dict(arrowstyle="->", color="#D55E00", lw=1.0),
        fontsize=8, color="#555",
    )

    plt.tight_layout()
    pdf_path = save_figure_pdf(fig, FIG_ID)
    print(f"\n[write] {pdf_path}")


if __name__ == "__main__":
    main()
