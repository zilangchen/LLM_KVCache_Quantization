"""
Generate Chapter 4 Figure 4-5 as a merged two-panel regime figure.

Panel A is the cross-model policy suitability heatmap. Cell color is row-wise
normalized task-core quality, with darker colors indicating stronger suitability.
Panel B presents a simplified model-suitability roadmap for the Section 4.4
model-specific discussions.

Contract:
- Input:  results/clean_rerun_20260419T09/summary_final.csv (step=2_compare)
- Output: thesis/figures/ch4/fig_ch4_05_regime_heatmap.pdf

Run:
    python scripts/thesis/plot_ch4_regime_combined.py
"""

from __future__ import annotations

import csv
import pathlib
import sys

import numpy as np
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.font_manager import FontProperties

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _common import (  # noqa: E402
    CLEAN_RERUN_DIR,
    THESIS_FIGURES_DIR,
    print_contract,
    set_mpl_style,
)

FIG_ID = "fig_ch4_05_regime_heatmap"
SUMMARY_CSV = CLEAN_RERUN_DIR / "summary_final.csv"
OUTPUT_PDF = THESIS_FIGURES_DIR / "ch4" / f"{FIG_ID}.pdf"

MODEL_ORDER = ["3b", "8b", "14b", "mistral7b"]
MODEL_LABEL = {
    "3b": "Qwen2.5-3B",
    "8b": "LLaMA-3.1-8B",
    "14b": "Qwen2.5-14B",
    "mistral7b": "Mistral-7B",
}

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
    "14b": "bakv_auto_cov90_max",
    "mistral7b": "bakv_auto_cov80_max",
}

POLICY_COLS = ["uniform", "ba_fixed", "heuristic", "ba_auto"]
POLICY_HEADER = {
    "uniform": "Uniform\nINT4",
    "ba_fixed": "BA-$k_*$",
    "heuristic": "Heur.-$k_*$",
    "ba_auto": "BA-AutoK",
}
TASK_ORDER = ["narrativeqa", "hotpotqa", "gov_report"]
HIGH_CLUSTER_RATIO = 0.97

REGIME_CARDS = [
    {
        "model": "Mistral-7B",
        "policy": "BA-AutoK / Heur. 近簇",
        "title": "AutoK 最清楚的正向例子",
        "note": "自动预算直接落在高分区",
        "color": "#3A68AD",
        "fill": "#E0EBF9",
    },
    {
        "model": "Qwen2.5-3B",
        "policy": "BA-k1 / AutoK",
        "title": "早层保护能救回质量",
        "note": "关键层集中在最前面",
        "color": "#2F80A0",
        "fill": "#E1F0F6",
    },
    {
        "model": "LLaMA-3.1-8B",
        "policy": "BA-k11 / AutoK",
        "title": "固定 k 与 AutoK 都在高分区",
        "note": "高分策略形成接近簇",
        "color": "#428B85",
        "fill": "#E0F2EF",
    },
    {
        "model": "Qwen2.5-14B",
        "policy": "多策略近簇",
        "title": "多种策略接近，难分稳定赢家",
        "note": "敏感层铺得更开",
        "color": "#5B718E",
        "fill": "#E8EEF4",
    },
]


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
    raise RuntimeError("No CJK-capable font found for fig_ch4_05_regime_heatmap.")


def load_summary_rows(path: pathlib.Path) -> list[dict[str, object]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing source data: {path}")

    rows: list[dict[str, object]] = []
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


def policy_for(model: str, policy_col: str) -> str:
    if policy_col == "uniform":
        return "uniform_int4_k4v4"
    if policy_col == "ba_fixed":
        return PER_MODEL_BEST_K[model]
    if policy_col == "heuristic":
        return PER_MODEL_HEUR_K[model]
    if policy_col == "ba_auto":
        return PER_MODEL_AUTOK[model]
    raise ValueError(f"Unknown policy column: {policy_col}")


def build_mean_matrix(rows: list[dict[str, object]]) -> np.ndarray:
    mat = np.full((len(MODEL_ORDER), len(POLICY_COLS)), np.nan, dtype=float)
    for i, model in enumerate(MODEL_ORDER):
        for j, policy_col in enumerate(POLICY_COLS):
            target_policy = policy_for(model, policy_col)
            values = []
            for task in TASK_ORDER:
                matches = [
                    row
                    for row in rows
                    if row["step"] == "2_compare"
                    and row["model"] == model
                    and row["kvmode_or_policy"] == target_policy
                    and row["task"] == task
                ]
                if len(matches) != 1:
                    raise RuntimeError(
                        "Expected exactly one row for "
                        f"model={model}, policy={target_policy}, task={task}; "
                        f"got {len(matches)}"
                    )
                value = matches[0]["metric_value"]
                if np.isnan(value):
                    raise RuntimeError(
                        "Expected a finite metric_value for "
                        f"model={model}, policy={target_policy}, task={task}"
                    )
                values.append(float(value))
            mat[i, j] = float(np.mean(values))
    return mat


def row_normalize(mat: np.ndarray) -> np.ndarray:
    mat_norm = np.full_like(mat, np.nan, dtype=float)
    for i in range(mat.shape[0]):
        row = mat[i]
        lo, hi = np.nanmin(row), np.nanmax(row)
        if hi - lo <= 1e-9:
            mat_norm[i] = 0.5
        else:
            mat_norm[i] = (row - lo) / (hi - lo)
    return mat_norm


def draw_heatmap(ax, fig, mat: np.ndarray, mat_norm: np.ndarray, cjk_font: FontProperties):
    from matplotlib.patches import Rectangle

    cmap = LinearSegmentedColormap.from_list(
        "suitability_deep_high",
        ["#F4F6F5", "#D8E7E3", "#94C2BA", "#3F8F8B", "#0B4F5A"],
    )
    image = ax.imshow(mat_norm, cmap=cmap, vmin=0, vmax=1, aspect="auto")

    ax.set_xticks(np.arange(len(POLICY_COLS)))
    ax.set_xticklabels(
        [POLICY_HEADER[p] for p in POLICY_COLS],
        fontsize=8.8,
        fontproperties=cjk_font,
    )
    ax.set_yticks(np.arange(len(MODEL_ORDER)))
    ax.set_yticklabels([MODEL_LABEL[m] for m in MODEL_ORDER], fontsize=8.8)
    ax.set_title("(a) 策略适用区间热力图", fontsize=10.4, loc="left", fontproperties=cjk_font)

    ax.set_xticks(np.arange(-0.5, len(POLICY_COLS), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(MODEL_ORDER), 1), minor=True)
    ax.grid(which="minor", color="#FFFFFF", linestyle="-", linewidth=1.15)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.tick_params(axis="both", length=0)

    for i in range(len(MODEL_ORDER)):
        row_best = float(np.nanmax(mat[i]))
        best_j = int(np.nanargmax(mat[i]))
        for j in range(len(POLICY_COLS)):
            text_color = "white" if mat_norm[i, j] >= 0.65 else "#111827"
            ax.text(
                j,
                i,
                f"{mat[i, j]:.2f}",
                ha="center",
                va="center",
                fontsize=9.2,
                color=text_color,
            )
            if j != best_j and mat[i, j] >= row_best * HIGH_CLUSTER_RATIO:
                ax.add_patch(
                    Rectangle(
                        (j - 0.47, i - 0.47),
                        0.94,
                        0.94,
                        fill=False,
                        edgecolor="#4B5563",
                        linewidth=1.0,
                        linestyle=(0, (3, 2)),
                        zorder=5,
                    )
                )
        ax.add_patch(
            Rectangle(
                (best_j - 0.48, i - 0.48),
                0.96,
                0.96,
                fill=False,
                edgecolor="#111827",
                linewidth=1.4,
                zorder=6,
            )
        )

    cbar = fig.colorbar(image, ax=ax, fraction=0.047, pad=0.025)
    cbar.set_label("行内归一化适用性", fontsize=8.2, fontproperties=cjk_font)
    cbar.ax.tick_params(labelsize=7.8, length=2)

    ax.text(
        0.5,
        -0.135,
        "同一行内，某一列越深，表示该策略越接近该模型的最佳参数效果；实线=最高，虚线≥97%最高均值。\n"
        "BA-AutoK 不一定每行最深，但整体保持相对深色，说明自动预算选择效果较好。",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=8.1,
        color="#4B5563",
        fontproperties=cjk_font,
        linespacing=1.35,
    )


def draw_regime_cards(ax, cjk_font: FontProperties):
    from matplotlib.patches import Rectangle

    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(
        0.0,
        0.985,
        "(b) 模型适用区间速览",
        fontsize=10.8,
        va="top",
        fontproperties=cjk_font,
    )

    card_h = 0.195
    gap = 0.018
    top = 0.91
    for idx, card in enumerate(REGIME_CARDS):
        y = top - idx * (card_h + gap) - card_h
        ax.add_patch(
            Rectangle(
                (0.0, y),
                1.0,
                card_h,
                facecolor=card["fill"],
                edgecolor=card["color"],
                linewidth=0.85,
            )
        )
        ax.add_patch(
            Rectangle(
                (0.0, y),
                0.024,
                card_h,
                facecolor=card["color"],
                edgecolor=card["color"],
                linewidth=0,
            )
        )
        ax.text(
            0.052,
            y + card_h - 0.036,
            f"{card['model']}  ·  {card['policy']}",
            fontsize=9.2,
            fontproperties=cjk_font,
            color="#111827",
            va="top",
            weight="bold",
        )
        ax.text(
            0.052,
            y + card_h - 0.078,
            card["title"],
            fontsize=9.6,
            fontproperties=cjk_font,
            color=card["color"],
            va="top",
            weight="bold",
        )
        ax.text(
            0.052,
            y + card_h - 0.126,
            card["note"],
            fontsize=8.4,
            fontproperties=cjk_font,
            color="#4B5563",
            va="top",
        )

    ax.text(
        0.0,
        0.025,
        "按第 4.4.2--4.4.5 节顺序阅读；具体证据在各小节展开。",
        fontsize=7.8,
        fontproperties=cjk_font,
        color="#4B5563",
        va="bottom",
    )


def main():
    print_contract(
        "plot_ch4_regime_combined.py",
        inputs=[str(SUMMARY_CSV.relative_to(CLEAN_RERUN_DIR.parent.parent))],
        outputs=[str(OUTPUT_PDF.relative_to(THESIS_FIGURES_DIR.parent.parent))],
    )
    set_mpl_style()

    import matplotlib.pyplot as plt

    cjk_font = find_cjk_font()
    rows = load_summary_rows(SUMMARY_CSV)
    mat = build_mean_matrix(rows)
    mat_norm = row_normalize(mat)

    fig = plt.figure(figsize=(10.8, 5.05))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.12, 1.0], wspace=0.26)
    ax_heatmap = fig.add_subplot(grid[0, 0])
    ax_summary = fig.add_subplot(grid[0, 1])

    draw_heatmap(ax_heatmap, fig, mat, mat_norm, cjk_font)
    draw_regime_cards(ax_summary, cjk_font)

    fig.subplots_adjust(left=0.075, right=0.985, top=0.92, bottom=0.23)

    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PDF, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"\n[write] {OUTPUT_PDF}")
    print("\n--- per-model high-suitability policy summary ---")
    for i, model in enumerate(MODEL_ORDER):
        best_j = int(np.nanargmax(mat[i]))
        close = [
            POLICY_COLS[j]
            for j in range(len(POLICY_COLS))
            if mat[i, j] >= float(np.nanmax(mat[i])) * HIGH_CLUSTER_RATIO
        ]
        print(
            f"  {model}: best={POLICY_COLS[best_j]} "
            f"(score={mat[i, best_j]:.3f}); high_cluster={close}"
        )


if __name__ == "__main__":
    main()
