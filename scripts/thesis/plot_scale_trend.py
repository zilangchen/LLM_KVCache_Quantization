"""
scripts/thesis/plot_scale_trend.py

生成图 ⑨：Policy ordering across family / scale regimes。

图结构:
- 1 subplot
- x: 按 family / scale 排序的离散模型类别（不是连续 scaling-law 坐标轴）
- y: task-core mean quality
- 多条线: 不同 policy family，连接离散类别以展示 ordering 的变化

Contract:
- Input:  summary_final.csv (step=2_compare)
- Output: thesis/figures/fig9_scale_trend.pdf
"""

from __future__ import annotations

import csv
import sys
import pathlib
import numpy as np
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _common import (  # noqa: E402
    CLEAN_RERUN_DIR,
    set_mpl_style,
    save_figure_pdf,
    print_contract,
    POLICY_COLORS,
    POLICY_MARKERS,
)

FIG_ID = "fig9_scale_trend"
SUMMARY_CSV = CLEAN_RERUN_DIR / "summary_final.csv"

MODEL_ORDER = ["3b", "mistral7b", "8b", "14b"]
MODEL_LABEL = {
    "3b": "Qwen2.5-3B",
    "mistral7b": "Mistral-7B",
    "8b": "LLaMA-3.1-8B",
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
    ("uniform_int4", "统一 INT4", {m: "uniform_int4_k4v4" for m in MODEL_ORDER}),
    ("bakv_fixed",   r"BA-$k_*$", PER_MODEL_BEST_K),
    ("heuristic",    "Heuristic-$k_*$", PER_MODEL_HEUR),
    ("bakv_auto_cov80", "BA-AutoK", PER_MODEL_AUTO),
]

CORE_TASKS = ["narrativeqa", "hotpotqa", "gov_report"]


def find_cjk_font() -> FontProperties:
    candidates = [
        "Arial Unicode MS",
        "Hiragino Sans GB",
        "STHeiti",
        "Heiti TC",
        "PingFang HK",
    ]
    for name in candidates:
        try:
            path = font_manager.findfont(name, fallback_to_default=False)
        except ValueError:
            continue
        if path and pathlib.Path(path).exists():
            return FontProperties(fname=path)
    raise RuntimeError("No CJK-capable font found for fig9_scale_trend.")


def load_summary_rows(path: pathlib.Path):
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metric_value = row.get("metric_value", "")
            try:
                row["metric_value"] = (
                    float(metric_value) if metric_value not in ("", None) else np.nan
                )
            except ValueError:
                row["metric_value"] = np.nan
            rows.append(row)
    return rows


def main():
    print_contract(
        "plot_scale_trend.py",
        inputs=["summary_final.csv (step=2_compare core 3 tasks)"],
        outputs=[f"thesis/figures/{FIG_ID}.pdf"],
    )
    set_mpl_style()
    import matplotlib.pyplot as plt

    cjk_font = find_cjk_font()
    legend_font = FontProperties(fname=cjk_font.get_file(), size=8.6)
    rows = load_summary_rows(SUMMARY_CSV)
    rows = [
        row for row in rows
        if row["step"] == "2_compare"
        and row["task"] in CORE_TASKS
        and not np.isnan(row["metric_value"])
    ]

    fig, ax = plt.subplots(figsize=(7.8, 5.1))
    x_pos = list(range(len(MODEL_ORDER)))

    for fam_key, label, model2policy in LINE_DEFS:
        xs, ys = [], []
        for idx, m in enumerate(MODEL_ORDER):
            policy = model2policy[m]
            sub = [
                row["metric_value"]
                for row in rows
                if row["model"] == m and row["kvmode_or_policy"] == policy
            ]
            if not sub:
                continue
            xs.append(idx)
            ys.append(float(np.mean(sub)))
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

    ax.set_xticks(x_pos)
    ax.set_xticklabels([MODEL_LABEL[m] for m in MODEL_ORDER], fontsize=8)
    ax.set_xlim(-0.15, len(MODEL_ORDER) - 0.85)
    ax.set_ylabel("任务核心平均质量", fontproperties=cjk_font)
    ax.set_title("Family/Scale 分类排序汇总图", fontproperties=cjk_font)
    ax.grid(True, alpha=0.3)
    ax.legend(
        loc="lower right",
        bbox_to_anchor=(0.985, 0.18),
        ncol=2,
        frameon=True,
        framealpha=0.93,
        borderpad=0.35,
        labelspacing=0.35,
        columnspacing=1.0,
        prop=legend_font,
    )

    for xpos in [0.5, 1.5, 2.5]:
        ax.axvline(xpos, color="#BBBBBB", linewidth=0.8, alpha=0.5, zorder=0)

    # highlight Mistral strongest positive case
    ax.annotate(
        "Mistral：\nAutoK 最显著正向案例",
        xy=(1, 14.7), xytext=(1.42, 14.25),
        arrowprops=dict(arrowstyle="->", color="#D55E00", lw=1.0),
        fontsize=8, color="#555", ha="left", fontproperties=cjk_font,
    )

    plt.tight_layout()
    pdf_path = save_figure_pdf(fig, FIG_ID)
    print(f"\n[write] {pdf_path}")


if __name__ == "__main__":
    main()
