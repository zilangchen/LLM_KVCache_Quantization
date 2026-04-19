"""
scripts/thesis/plot_regime_map.py

生成图 ⑧：Cross-Model Regime Map Heatmap（story §16.7）。

图结构:
- 4 model (行) × 4 policy (列) 的 heatmap
- cell 色彩 = 该 policy 在该 model 上的 **task-mean quality**（3 core tasks 的归一化均值）
- 每 cell 里标注具体分数
- 加粗框 = per-model best policy (对应 Ch4 §4.3 'winner 多样性' 证据)
- 色阶: viridis（color-blind safe）

对齐 T3 表格的 policy canonical（uniform / BA-k / heuristic-k / BA-AutoK），
但以 heatmap 形式让读者 2 秒看出"no two rows share the same best policy"的
regime map 现象。

Contract:
- Input: results/clean_rerun_20260419T09/summary_final.csv (step=2_compare)
- Output: thesis/figures/fig8_regime_map.pdf

Run:
    python scripts/thesis/plot_regime_map.py
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
)

FIG_ID = "fig8_regime_map"

MODEL_ORDER = ["3b", "8b", "14b", "mistral7b"]
MODEL_LABEL = {
    "3b":        r"Qwen2.5-3B",
    "8b":        r"Llama-3.1-8B",
    "14b":       r"Qwen2.5-14B",
    "mistral7b": r"Mistral-7B",
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
    "uniform":    "Uniform\nINT4",
    "ba_fixed":   "BA-$k$\n(fixed)",
    "heuristic":  "Heuristic-$k$",
    "ba_auto":    "BA-AutoK",
}

TASK_ORDER = ["narrativeqa", "hotpotqa", "gov_report"]


def build_mean_matrix(df):
    """返回 (model, policy) → task-mean 的矩阵 + per-model best column index."""
    df = df[df["step"] == "2_compare"]
    mat = np.zeros((len(MODEL_ORDER), len(POLICY_COLS)))
    for i, m in enumerate(MODEL_ORDER):
        best_k_policy = PER_MODEL_BEST_K[m]
        heur_policy = PER_MODEL_HEUR_K[m]
        auto_policy = PER_MODEL_AUTOK[m]
        for j, col in enumerate(POLICY_COLS):
            if col == "uniform":
                target = "uniform_int4_k4v4"
            elif col == "ba_fixed":
                target = best_k_policy
            elif col == "heuristic":
                target = heur_policy
            elif col == "ba_auto":
                target = auto_policy
            sub = df[(df["model"] == m) & (df["kvmode_or_policy"] == target)
                     & (df["task"].isin(TASK_ORDER))]
            if sub.empty:
                mat[i, j] = np.nan
            else:
                mat[i, j] = sub["metric_value"].mean()
    return mat


def row_normalize(mat):
    """每行独立归一化到 [0, 1]（让跨模型色彩具有同等视觉权重）。"""
    mat_norm = np.zeros_like(mat)
    for i in range(mat.shape[0]):
        row = mat[i]
        lo, hi = np.nanmin(row), np.nanmax(row)
        if hi - lo > 1e-9:
            mat_norm[i] = (row - lo) / (hi - lo)
        else:
            mat_norm[i] = 0.5
    return mat_norm


def main():
    print_contract(
        "plot_regime_map.py",
        inputs=["results/clean_rerun_20260419T09/summary_final.csv"],
        outputs=[f"thesis/figures/{FIG_ID}.pdf"],
    )
    set_mpl_style()
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    df = load_summary_final()
    mat = build_mean_matrix(df)
    mat_norm = row_normalize(mat)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    im = ax.imshow(mat_norm, cmap="viridis", aspect="auto", vmin=0, vmax=1)

    # annotate absolute scores in each cell
    for i in range(len(MODEL_ORDER)):
        for j in range(len(POLICY_COLS)):
            val = mat[i, j]
            if np.isnan(val):
                txt = "---"
            else:
                txt = f"{val:.2f}"
            color = "white" if mat_norm[i, j] < 0.5 else "black"
            ax.text(j, i, txt, ha="center", va="center", color=color, fontsize=9)

    # bold outline for per-model best
    for i in range(len(MODEL_ORDER)):
        best_j = int(np.nanargmax(mat[i]))
        rect = Rectangle(
            (best_j - 0.48, i - 0.48), 0.96, 0.96,
            fill=False, edgecolor="red", linewidth=2.0, zorder=5,
        )
        ax.add_patch(rect)

    ax.set_xticks(np.arange(len(POLICY_COLS)))
    ax.set_xticklabels([POLICY_HEADER[p] for p in POLICY_COLS], fontsize=10)
    ax.set_yticks(np.arange(len(MODEL_ORDER)))
    ax.set_yticklabels([MODEL_LABEL[m] for m in MODEL_ORDER], fontsize=10)
    ax.set_title(
        r"Cross-model regime map (task-core mean quality, row-normalized)",
        fontsize=11,
    )

    # colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("row-normalized quality (0=row min, 1=row max)")

    # footnote text
    ax.text(
        0.5, -0.25,
        "Red outline = per-model best policy. "
        "No two rows share the same best policy → regime map.",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=8, color="#555",
    )
    plt.tight_layout()

    pdf_path = save_figure_pdf(fig, FIG_ID)
    print(f"\n[write] {pdf_path}")

    # print winner summary
    print("\n--- per-model winner policy ---")
    for i, m in enumerate(MODEL_ORDER):
        best_j = int(np.nanargmax(mat[i]))
        print(f"  {m}: {POLICY_COLS[best_j]} (score={mat[i, best_j]:.3f})")


if __name__ == "__main__":
    main()
