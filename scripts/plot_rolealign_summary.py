#!/usr/bin/env python3
"""Generate the INT4-RoleAlign hero figure for the thesis."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path
from matplotlib import font_manager


DPI = 300

C_KIVI = "#E11D48"
C_ROLE = "#0F766E"
C_TEXT = "#334155"
C_GRID = "#CBD5E1"
C_BOX = "#F8FAFC"
C_BOX_EDGE = "#CBD5E1"

models = ["Qwen2.5-1.5B", "Qwen2.5-7B", "LLaMA-3.1-8B"]

# PPL absolute values (chunk_size=128, from tab:rolealign-results)
# CRITICAL: ppl_role was previously [9.4197, 7.2141, 6.7511] — this was
# buggy INT8-fallback data, NOT INT4-RoleAlign. Fixed 2026-04-02.
ppl_fp16 = [9.31,  7.14,  6.73]
ppl_kivi = [10.43, 7.53,  6.90]
ppl_role = [10.58, 7.58,  6.90]

# Use thesis-stated percentages directly to avoid floating-point rounding
# discrepancies (e.g., 6.16% computed vs 6.1% stated).
ppl_deg_kivi = [12.0, 5.5, 2.4]
ppl_deg_role = [13.7, 6.1, 2.4]

# LongBench-style synthetic macro scores (x100 in paper tables)
lb_kivi = [4.83, 3.87, 6.31]
lb_role = [4.92, 3.93, 6.31]


def _pick_cjk_font_family():
    candidates = [
        Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
    ]
    for path in candidates:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            return font_manager.FontProperties(fname=str(path)).get_name()
    return "DejaVu Sans"


def setup_style():
    font_family = _pick_cjk_font_family()
    plt.rcParams.update({
        "font.family": font_family,
        "font.sans-serif": [font_family, "Arial Unicode MS", "DejaVu Sans", "sans-serif"],
        "font.size": 10.5,
        "axes.titlesize": 11,
        "axes.labelsize": 10.5,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 8.5,
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": C_TEXT,
        "axes.linewidth": 0.9,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.22,
        "grid.linewidth": 0.6,
        "grid.color": C_GRID,
        "legend.framealpha": 0.95,
        "legend.edgecolor": C_BOX_EDGE,
        "axes.unicode_minus": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def summary_box(ax, x0, width, title, value, accent):
    rect = plt.Rectangle(
        (x0, 0.1), width, 0.8,
        facecolor=C_BOX, edgecolor=C_BOX_EDGE, linewidth=1.0,
        transform=ax.transAxes, clip_on=False,
    )
    ax.add_patch(rect)
    ax.text(x0 + 0.04, 0.68, title, transform=ax.transAxes,
            fontsize=8.2, color=C_TEXT, ha="left", va="center")
    ax.text(x0 + 0.04, 0.36, value, transform=ax.transAxes,
            fontsize=12.5, color=accent, ha="left", va="center", fontweight="bold")


def main():
    setup_style()

    fig = plt.figure(figsize=(10.6, 6.1))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 4.8], hspace=0.24, wspace=0.30)

    ax_top = fig.add_subplot(gs[0, :])
    ax_ppl = fig.add_subplot(gs[1, 0])
    ax_lb = fig.add_subplot(gs[1, 1])

    # Top summary ribbon
    ax_top.axis("off")
    summary_box(ax_top, 0.00, 0.31, "Needle 检索", "三模型均为 100%", C_ROLE)
    summary_box(ax_top, 0.345, 0.31, "PPL 退化", "2.4% – 13.7%", "#B45309")
    summary_box(ax_top, 0.69, 0.31, "KV Cache 压缩", "73%", C_ROLE)

    x = np.arange(len(models))
    w = 0.34

    # Panel (a): PPL degradation
    bars_kivi = ax_ppl.bar(x - w / 2, ppl_deg_kivi, w, color=C_KIVI, label="KIVI-style INT4", edgecolor="white", linewidth=0.6, zorder=3)
    bars_role = ax_ppl.bar(x + w / 2, ppl_deg_role, w, color=C_ROLE, label="INT4-RoleAlign", edgecolor="white", linewidth=0.6, zorder=3)

    for bar in bars_kivi:
        h = bar.get_height()
        ax_ppl.text(bar.get_x() + bar.get_width() / 2, h + 0.18, f"{h:.1f}%", ha="center", va="bottom", fontsize=8.3, color=C_KIVI, fontweight="bold")
    for bar in bars_role:
        h = bar.get_height()
        ax_ppl.text(bar.get_x() + bar.get_width() / 2, h + 0.18, f"{h:.1f}%", ha="center", va="bottom", fontsize=8.3, color=C_ROLE, fontweight="bold")

    # H_kv trend annotation (replacing old "reduction" arrows — RA does NOT
    # reduce PPL vs KIVI; the advantage is in retrieval robustness, not PPL)
    h_kv_vals = [2, 4, 8]
    for i, h in enumerate(h_kv_vals):
        ax_ppl.text(x[i], -2.2, f"$H_{{kv}}$={h}", ha="center",
                    fontsize=7.5, color="#64748B", style="italic")

    ax_ppl.set_title("(a) PPL 退化", loc="left", fontweight="bold", pad=8)
    ax_ppl.set_ylabel("相对 FP16 的 PPL 退化 (%)")
    ax_ppl.set_xticks(x)
    ax_ppl.set_xticklabels(models)
    ax_ppl.set_ylim(0, max(ppl_deg_kivi) * 1.32)
    ax_ppl.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax_ppl.grid(axis="y", alpha=0.25, color=C_GRID)
    ax_ppl.grid(axis="x", alpha=0.08, color="#E2E8F0")

    # Panel (b): LongBench-style synthetic quality
    bars_kivi2 = ax_lb.bar(x - w / 2, lb_kivi, w, color=C_KIVI, label="KIVI-style INT4", edgecolor="white", linewidth=0.6, zorder=3)
    bars_role2 = ax_lb.bar(x + w / 2, lb_role, w, color=C_ROLE, label="INT4-RoleAlign", edgecolor="white", linewidth=0.6, zorder=3)

    for bar in bars_kivi2:
        h = bar.get_height()
        ax_lb.text(bar.get_x() + bar.get_width() / 2, h + 0.06, f"{h:.2f}", ha="center", va="bottom", fontsize=8.2, color=C_KIVI, fontweight="bold")
    for bar in bars_role2:
        h = bar.get_height()
        ax_lb.text(bar.get_x() + bar.get_width() / 2, h + 0.06, f"{h:.2f}", ha="center", va="bottom", fontsize=8.2, color=C_ROLE, fontweight="bold")

    ax_lb.set_title("(b) LongBench-style 合成质量", loc="left", fontweight="bold", pad=8)
    ax_lb.set_ylabel("合成宏平均分 (×100)")
    ax_lb.set_xticks(x)
    ax_lb.set_xticklabels(models)
    ax_lb.set_ylim(0, max(max(lb_kivi), max(lb_role)) * 1.36)
    ax_lb.grid(axis="y", alpha=0.25, color=C_GRID)
    ax_lb.grid(axis="x", alpha=0.08, color="#E2E8F0")
    handles, labels = ax_ppl.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.01),
        ncol=2,
        frameon=True,
        fontsize=8.5,
        columnspacing=1.6,
        handlelength=2.0,
    )
    fig.subplots_adjust(left=0.07, right=0.985, top=0.95, bottom=0.12)
    plt.savefig("thesis/figures/rolealign_summary.pdf")
    print("Saved: thesis/figures/rolealign_summary.pdf")


if __name__ == "__main__":
    main()
