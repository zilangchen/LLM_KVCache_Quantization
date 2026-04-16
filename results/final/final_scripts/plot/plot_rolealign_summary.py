#!/usr/bin/env python3
"""Generate the INT4-RoleAlign hero figure for the thesis.

This figure must reflect the post-v2fix narrative:
INT4-RoleAlign strongly preserves retrieval behavior and KV memory,
but still pays clear PPL and TPOT costs.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path
from matplotlib import font_manager
from matplotlib.lines import Line2D


DPI = 300

C_ROLE = "#8DA59B"
C_FP16 = "#5A6472"
C_WARN = "#B79466"
C_RISK = "#C6948C"
C_TEXT = "#4D5866"
C_NUM = "#1F2937"
C_GRID = "#E7EBF0"
C_BOX = "#FDFDFD"
C_BOX_EDGE = "#E2E7ED"
C_RETR = "#96A8C1"

models = ["Qwen2.5-1.5B", "Qwen2.5-7B", "LLaMA-3.1-8B"]
x = np.arange(len(models))

# Retrieval-oriented results at 32K (v2fix RULER + Needle summary).
# We use the latest validated per-model means for the hero figure.
needle_fp16 = [100.0, 100.0, 100.0]
needle_role = [100.0, 99.48, 99.43]  # S-NIAH contains proxy for retrieval parity
needle_drop = [max(f - r, 0.0) for f, r in zip(needle_fp16, needle_role)]

mkniah_fp16 = [100.0, 100.0, 100.0]
mkniah_role = [92.67, 99.48, 99.46]
mkniah_drop = [max(f - r, 0.0) for f, r in zip(mkniah_fp16, mkniah_role)]

# PPL absolute values (chunk_size=128, full WikiText-2; latest v2fix data).
ppl_fp16 = [9.31, 7.14, 6.73]
ppl_role = [10.58, 7.58, 6.90]
ppl_deg_role = [13.7, 6.1, 2.4]

# Serial exclusive-GPU profiling at seq_len=4096.
tpot_fp16 = [24.98, 24.81, 28.74]
tpot_role = [64.11, 61.32, 61.51]
tpot_ratio = [r / f for r, f in zip(tpot_role, tpot_fp16)]

kv_mem_fp16 = [115.47, 230.95, 527.88]
kv_mem_role = [30.73, 61.47, 140.50]
kv_mem_saving = [100.0 * (1.0 - r / f) for r, f in zip(kv_mem_role, kv_mem_fp16)]


def _setup_thesis_fonts():
    """Configure fonts: 宋体 (Chinese) + Times New Roman (English)."""
    songti_paths = [
        Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
        Path("/System/Library/Fonts/STSong.ttf"),
    ]
    for p in songti_paths:
        if p.exists():
            font_manager.fontManager.addfont(str(p))
            break


def setup_style():
    _setup_thesis_fonts()
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Songti SC", "STSong", "SimSun", "Times New Roman"],
        "mathtext.fontset": "stix",
        "font.size": 10.5,
        "axes.titlesize": 11,
        "axes.labelsize": 10.5,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 8.3,
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
    ax.text(x0 + width / 2, 0.67, title, transform=ax.transAxes,
            fontsize=7.9, color=C_TEXT, ha="center", va="center")
    ax.text(x0 + width / 2, 0.37, value, transform=ax.transAxes,
            fontsize=10.4, color=C_NUM, ha="center", va="center",
            fontweight="bold", linespacing=1.15)


def retrieval_drop_panel(ax, title, drops, ymax):
    ax.set_title(title, loc="left", fontweight="bold", pad=8)
    bars = ax.bar(x, drops, width=0.54, color=C_RETR, edgecolor="white", linewidth=0.7, zorder=3, alpha=0.96)
    for i, bar in enumerate(bars):
        h = bar.get_height()
        label = "0.00" if h == 0 else f"{h:.2f}"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + ymax * 0.03,
            label,
            ha="center",
            va="bottom",
            fontsize=8.0,
            color=C_NUM,
            fontweight="bold",
        )
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            max(h * 0.52, ymax * 0.08),
            f"{(100.0 - h):.1f}%",
            ha="center",
            va="center",
            fontsize=8.2,
            color=C_NUM,
            fontweight="bold",
        )
    ax.axhline(0.0, color=C_FP16, linestyle="--", linewidth=1.0, alpha=0.55)
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylabel("相对 FP16 的下降 (pp)")
    ax.set_ylim(0, ymax)
    ax.text(
        0.98, 0.96, "越低越好",
        transform=ax.transAxes, ha="right", va="top",
        fontsize=7.8, color="#64748B"
    )
    ax.grid(axis="y", alpha=0.24, color=C_GRID)
    ax.grid(axis="x", alpha=0.08, color="#E2E8F0")


def grouped_bar_panel(
    ax,
    title,
    baseline,
    rolealign,
    ylabel,
    baseline_color,
    role_color,
    annotate=True,
):
    w = 0.34
    ax.set_title(title, loc="left", fontweight="bold", pad=8)
    b1 = ax.bar(x - w / 2, baseline, w, color=baseline_color, edgecolor="white", linewidth=0.6, zorder=3, alpha=0.96)
    b2 = ax.bar(x + w / 2, rolealign, w, color=role_color, edgecolor="white", linewidth=0.6, zorder=3, alpha=0.96)
    if annotate:
        for bar in b1:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + max(baseline) * 0.015, f"{h:.1f}",
                    ha="center", va="bottom", fontsize=7.8, color=baseline_color, fontweight="bold")
        for bar in b2:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + max(rolealign) * 0.015, f"{h:.1f}",
                    ha="center", va="bottom", fontsize=7.8, color=role_color, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.24, color=C_GRID)
    ax.grid(axis="x", alpha=0.08, color="#E2E8F0")
    return b1, b2


def main():
    setup_style()

    fig = plt.figure(figsize=(11.4, 9.2))
    gs = fig.add_gridspec(3, 2, height_ratios=[0.92, 2.65, 3.25], hspace=0.40, wspace=0.30)

    ax_top = fig.add_subplot(gs[0, :])
    ax_needle = fig.add_subplot(gs[1, 0])
    ax_mkniah = fig.add_subplot(gs[1, 1])
    ax_ppl = fig.add_subplot(gs[2, 0])
    gs_sys = gs[2, 1].subgridspec(2, 1, hspace=0.42)
    ax_tpot = fig.add_subplot(gs_sys[0, 0])
    ax_mem = fig.add_subplot(gs_sys[1, 0])

    # Top summary ribbon
    ax_top.axis("off")
    summary_box(ax_top, 0.00, 0.31, "检索表现（32K）", "Needle 99.4–100%\nMK-NIAH 92.7–99.5%", C_ROLE)
    summary_box(ax_top, 0.345, 0.31, "语言建模代价", "PPL +2.4%–13.7%", C_WARN)
    summary_box(ax_top, 0.69, 0.31, "系统代价", "KV -73%\nTPOT ≈2.1–2.6×", C_RISK)

    # Panel (a): Needle retrieval degradation
    retrieval_drop_panel(
        ax_needle,
        "(a) Needle 检索退化（32K）",
        needle_drop,
        0.82,
    )

    # Panel (b): MK-NIAH retrieval degradation
    retrieval_drop_panel(
        ax_mkniah,
        "(b) MK-NIAH 检索退化（32K）",
        mkniah_drop,
        8.5,
    )

    # Panel (c): PPL degradation
    w = 0.52
    bars_role = ax_ppl.bar(x, ppl_deg_role, w, color=C_WARN, edgecolor="white", linewidth=0.7, zorder=3, alpha=0.96)
    for i, bar in enumerate(bars_role):
        h = bar.get_height()
        ax_ppl.text(
            bar.get_x() + bar.get_width() / 2,
            h + 0.25,
            f"{h:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8.2,
            color=C_NUM,
            fontweight="bold",
        )
        ax_ppl.text(
            bar.get_x() + bar.get_width() / 2,
            h * 0.45,
            f"PPL {ppl_role[i]:.2f}",
            ha="center",
            va="center",
            fontsize=7.8,
            color=C_NUM,
            fontweight="bold",
        )
    h_kv_vals = [2, 4, 8]
    for i, h in enumerate(h_kv_vals):
        ax_ppl.text(x[i], -2.35, f"$H_{{kv}}$={h}", ha="center",
                    fontsize=7.4, color="#64748B", style="italic")
    ax_ppl.set_title("(c) 语言建模代价", loc="left", fontweight="bold", pad=8)
    ax_ppl.set_ylabel("相对 FP16 的 PPL 退化 (%)")
    ax_ppl.set_xticks(x)
    ax_ppl.set_xticklabels(models)
    ax_ppl.set_ylim(0, max(ppl_deg_role) * 1.34)
    ax_ppl.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax_ppl.grid(axis="y", alpha=0.24, color=C_GRID)
    ax_ppl.grid(axis="x", alpha=0.08, color="#E2E8F0")

    # Panel (d1): TPOT
    grouped_bar_panel(
        ax_tpot,
        "(d) 系统收益与代价（4K，串行独占 GPU）",
        tpot_fp16,
        tpot_role,
        "TPOT (ms)",
        C_FP16,
        C_RISK,
    )
    ax_tpot.set_ylim(0, max(tpot_role) * 1.30)
    ax_tpot.set_xticklabels([])
    ax_tpot.tick_params(axis="x", length=0)
    for i, mult in enumerate(tpot_ratio):
        ax_tpot.text(
            x[i],
            max(tpot_fp16[i], tpot_role[i]) + 7.0,
            f"{mult:.1f}×",
            ha="center",
            va="bottom",
            fontsize=7.7,
            color=C_NUM,
            fontweight="bold",
        )

    # Panel (d2): KV cache memory
    grouped_bar_panel(
        ax_mem,
        "KV Cache 显存占用",
        kv_mem_fp16,
        kv_mem_role,
        "显存 (MB)",
        C_FP16,
        C_ROLE,
        annotate=False,
    )
    ax_mem.set_ylim(0, max(kv_mem_fp16) * 1.26)
    ax_mem.title.set_fontsize(9.4)
    for i in range(len(models)):
        ax_mem.text(
            x[i] - 0.17,
            kv_mem_fp16[i] + 10.0,
            f"{kv_mem_fp16[i]:.1f}",
            ha="center",
            va="bottom",
            fontsize=7.5,
            color=C_NUM,
            fontweight="bold",
        )
        ax_mem.text(
            x[i] + 0.17,
            kv_mem_role[i] + 8.0,
            f"{kv_mem_role[i]:.1f}",
            ha="center",
            va="bottom",
            fontsize=7.5,
            color=C_NUM,
            fontweight="bold",
        )

    legend_handles = [
        Line2D([0], [0], marker="s", markersize=8.0, linestyle="None",
               markerfacecolor=C_FP16, markeredgecolor="white", markeredgewidth=0.6,
               label="FP16 基线"),
        Line2D([0], [0], marker="s", markersize=8.0, linestyle="None",
               markerfacecolor=C_ROLE, markeredgecolor="white", markeredgewidth=0.6,
               label="INT4-RoleAlign"),
    ]
    fig.legend(
        legend_handles,
        [h.get_label() for h in legend_handles],
        loc="lower center",
        bbox_to_anchor=(0.5, 0.012),
        ncol=2,
        frameon=True,
        fontsize=8.3,
        columnspacing=1.8,
        handlelength=1.6,
    )
    fig.subplots_adjust(left=0.06, right=0.988, top=0.955, bottom=0.095)
    plt.savefig("thesis/figures/rolealign_summary.pdf")
    print("Saved: thesis/figures/rolealign_summary.pdf")


if __name__ == "__main__":
    main()
