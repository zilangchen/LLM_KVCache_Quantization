#!/usr/bin/env python3
"""Generate the INT4-RoleAlign hero figure for the thesis."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


DPI = 300

C_KIVI = "#E11D48"
C_ROLE = "#0F766E"
C_TEXT = "#334155"
C_GRID = "#CBD5E1"
C_BOX = "#F8FAFC"
C_BOX_EDGE = "#CBD5E1"

models = ["Qwen2.5-1.5B", "Qwen2.5-7B", "LLaMA-3.1-8B"]

# PPL absolute values (chunk_size=128)
ppl_fp16 = [9.3088, 7.1407, 6.7330]
ppl_kivi = [10.4294, 7.5311, 6.8954]
ppl_role = [9.4197, 7.2141, 6.7511]

ppl_deg_kivi = [(k - f) / f * 100 for k, f in zip(ppl_kivi, ppl_fp16)]
ppl_deg_role = [(r - f) / f * 100 for r, f in zip(ppl_role, ppl_fp16)]

# LongBench-style synthetic macro scores (x100 in paper tables)
lb_kivi = [4.83, 3.87, 6.31]
lb_role = [4.92, 3.93, 6.31]


def setup_style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Nimbus Sans", "DejaVu Sans", "sans-serif"],
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

    fig = plt.figure(figsize=(10.4, 4.9))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 4.2], hspace=0.22, wspace=0.28)

    ax_top = fig.add_subplot(gs[0, :])
    ax_ppl = fig.add_subplot(gs[1, 0])
    ax_lb = fig.add_subplot(gs[1, 1])

    # Top summary ribbon
    ax_top.axis("off")
    summary_box(ax_top, 0.00, 0.31, "Needle retrieval", "100% across all 3 models", C_ROLE)
    summary_box(ax_top, 0.345, 0.31, "PPL degradation", "0.3%–1.2%", C_ROLE)
    summary_box(ax_top, 0.69, 0.31, "KV cache compression", "75%", C_ROLE)

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

    for i in range(len(models)):
        reduction = ppl_deg_kivi[i] - ppl_deg_role[i]
        ax_ppl.annotate(
            f"−{reduction:.1f} pp",
            xy=(x[i] + w / 2, ppl_deg_role[i]),
            xytext=(x[i] + 0.40, (ppl_deg_kivi[i] + ppl_deg_role[i]) / 2 + 0.7),
            fontsize=7.5,
            color="#475569",
            arrowprops=dict(arrowstyle="->", color="#94A3B8", lw=0.9),
            ha="left",
        )

    ax_ppl.set_title("(a) Perplexity Degradation", loc="left", fontweight="bold", pad=8)
    ax_ppl.set_ylabel("PPL degradation vs FP16 (%)")
    ax_ppl.set_xticks(x)
    ax_ppl.set_xticklabels(models)
    ax_ppl.set_ylim(0, max(ppl_deg_kivi) * 1.32)
    ax_ppl.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax_ppl.legend(loc="upper right")
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

    ax_lb.set_title("(b) LongBench-style Synthetic Quality", loc="left", fontweight="bold", pad=8)
    ax_lb.set_ylabel("Synthetic macro score (×100)")
    ax_lb.set_xticks(x)
    ax_lb.set_xticklabels(models)
    ax_lb.set_ylim(0, max(max(lb_kivi), max(lb_role)) * 1.36)
    ax_lb.legend(loc="upper right")
    ax_lb.grid(axis="y", alpha=0.25, color=C_GRID)
    ax_lb.grid(axis="x", alpha=0.08, color="#E2E8F0")
    ax_lb.text(
        0.98, 0.05,
        "LLaMA-3.1-8B is tied on this synthetic metric;\nRoleAlign still delivers the cleanest PPL improvement.",
        transform=ax_lb.transAxes,
        fontsize=7.4,
        color="#475569",
        ha="right",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=C_BOX_EDGE, lw=0.8, alpha=0.96),
    )

    plt.savefig("thesis/figures/rolealign_summary.pdf")
    print("Saved: thesis/figures/rolealign_summary.pdf")


if __name__ == "__main__":
    main()
