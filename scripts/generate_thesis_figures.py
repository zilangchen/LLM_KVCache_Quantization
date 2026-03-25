#!/usr/bin/env python3
"""Generate publication-quality thesis figures from aggregated CSV data.

Reads from results/emnlp_final_raw/tables/ and outputs to thesis/figures/.
All figures use 300 DPI, consistent color palette, and professional styling.

Usage:
    python scripts/generate_thesis_figures.py
    python scripts/generate_thesis_figures.py --tables_dir results/emnlp_final_raw/tables --out_dir thesis/figures
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch

# ═══════════════════════════════════════════════════════════════
# STYLE CONFIGURATION
# ═══════════════════════════════════════════════════════════════

DPI = 300

# Semantic color palette — visually distinct, colorblind-friendly
COLORS = {
    "fp16":              "#2C3E50",  # dark slate (baseline anchor)
    "int8_baseline":     "#E67E22",  # orange
    "int8_ours":         "#27AE60",  # green (protagonist — emphasized)
    "int4_baseline":     "#E74C3C",  # red
    "int4_fused":        "#8E44AD",  # purple
    "int4_ours":         "#3498DB",  # blue
    "kivi_style":        "#E91E63",  # pink
    "int4_kivi_aligned": "#00BCD4",  # cyan (KIVI + inv_tau)
    "int4_mixed_kv":     "#795548",  # brown (K-INT8/V-INT4 hybrid)
}

LABELS = {
    "fp16":              "FP16",
    "int8_baseline":     "INT8-Baseline",
    "int8_ours":         "INT8-Ours",
    "int4_baseline":     "INT4-Baseline",
    "int4_fused":        "INT4-Fused",
    "int4_ours":         "INT4-Ours",
    "kivi_style":        "KIVI-style",
    "int4_kivi_aligned": "KV-RoleAlign (K)",
    "int4_mixed_kv":     "K-INT8/V-INT4",
}

MARKERS = {
    "fp16":              "o",
    "int8_baseline":     "s",
    "int8_ours":         "D",
    "int4_baseline":     "^",
    "int4_fused":        "v",
    "int4_ours":         "P",
    "kivi_style":        "X",
    "int4_kivi_aligned": "h",   # hexagon
    "int4_mixed_kv":     "*",   # star
}

# Line styles: solid for "ours", dashed for baselines
LINESTYLES = {
    "fp16":              "-",
    "int8_baseline":     "--",
    "int8_ours":         "-",
    "int4_baseline":     "--",
    "int4_fused":        "-.",
    "int4_ours":         "-",
    "kivi_style":        ":",
    "int4_kivi_aligned": "-.",
    "int4_mixed_kv":     ":",
}

# Mainline config per kv_mode: (group_size, clip_percentile)
MAINLINE_CFG = {
    "fp16":              (128, 99.9),
    "int8_baseline":     (16, 99.9),
    "int8_ours":         (16, 99.5),
    "int4_baseline":     (32, 99.9),
    "int4_fused":        (16, 99.5),
    "int4_ours":         (16, 99.5),
    "kivi_style":        (128, 99.9),
    "int4_kivi_aligned": (128, 99.9),
    "int4_mixed_kv":     (128, 99.9),
}

# Canonical plot order
PLOT_ORDER = [
    "fp16", "int8_baseline", "int8_ours",
    "int4_baseline", "int4_fused", "int4_ours", "kivi_style",
]

# INT8-focus and INT4-focus subsets for dual-panel figures
INT8_MODES = ["fp16", "int8_baseline", "int8_ours", "kivi_style"]
INT4_MODES = ["fp16", "int4_baseline", "int4_fused", "int4_ours", "kivi_style"]
QUALITY_DASHBOARD_MODES = ["fp16", "int8_baseline", "int8_ours", "kivi_style", "int4_ours"]
EFFICIENCY_DASHBOARD_MODES = ["fp16", "int8_baseline", "int8_ours", "kivi_style", "int4_fused"]

KV_ABLATION_COLORS = {
    "K-only": "#27AE60",
    "V-only": "#3498DB",
    "K4V8": "#E74C3C",
    "MixedKV": "#8E5A2B",
}

PRIMARY_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
PRIMARY_MODEL_DIR = "Qwen__Qwen2.5-1.5B-Instruct"


def setup_style():
    """Configure matplotlib for publication-quality output with CJK support."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Songti SC", "PingFang HK", "Heiti TC",
                            "STHeiti", "DejaVu Sans", "sans-serif"],
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 8,
        "legend.framealpha": 0.9,
        "legend.edgecolor": "#CCCCCC",
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linewidth": 0.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.8,
        "lines.markersize": 5,
        "legend.fancybox": False,
        "axes.unicode_minus": False,  # Fix minus sign rendering with CJK fonts
    })


# ═══════════════════════════════════════════════════════════════
# DATA UTILITIES
# ═══════════════════════════════════════════════════════════════

def filter_mainline(df):
    """Filter DataFrame to mainline configs only.

    For datasets with group_size/clip_percentile columns, keep only
    the mainline configuration for each kv_mode.
    """
    if "group_size" not in df.columns or "clip_percentile" not in df.columns:
        return df

    parts = []
    for mode, (gs, cp) in MAINLINE_CFG.items():
        mask = (df["kv_mode"] == mode)
        sub = df[mask]
        if sub.empty:
            continue
        # Try exact mainline match
        exact = sub[(sub["group_size"] == gs) & (np.isclose(sub["clip_percentile"], cp))]
        if not exact.empty:
            parts.append(exact)
        else:
            # Fallback: take first available config for this mode
            first_gs = sub["group_size"].iloc[0]
            first_cp = sub["clip_percentile"].iloc[0]
            parts.append(sub[(sub["group_size"] == first_gs) &
                            (np.isclose(sub["clip_percentile"], first_cp))])
    if not parts:
        return df
    return pd.concat(parts, ignore_index=True)


def sort_modes(modes):
    """Sort kv_modes in canonical plot order."""
    order = {m: i for i, m in enumerate(PLOT_ORDER)}
    return sorted(modes, key=lambda m: order.get(m, 99))


def format_seq_len(s):
    """Format sequence length for display: 4096 -> '4K', 32704 -> '32K'."""
    if s >= 1000:
        k = s / 1024
        if abs(k - round(k)) < 0.5:
            return f"{round(k)}K"
    return str(s)


def save_fig(fig, out_path):
    """Save figure and close."""
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print(f"  -> {out_path.name} ({out_path.stat().st_size // 1024} KB)")


def place_panel_tag(ax, tag, title):
    """Add a panel tag in a consistent style."""
    text = f"{tag} {title}".strip()
    ax.set_title(text, fontsize=10, loc="left", pad=8, fontweight="bold")


def annotate_last_point(ax, x, y, text, color, dx=0.04, dy=0.0):
    """Directly annotate the last point of a line."""
    if len(x) == 0 or len(y) == 0:
        return
    ax.annotate(
        text,
        xy=(x[-1], y[-1]),
        xytext=(x[-1] + dx * (x[-1] if x[-1] else 1), y[-1] + dy),
        textcoords="data",
        fontsize=7.5,
        color=color,
        ha="left",
        va="center",
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=color, lw=0.6, alpha=0.9),
        arrowprops=dict(arrowstyle="-", color=color, lw=0.8),
        zorder=6,
    )


def style_axis(ax, ylabel=None, xlabel=None):
    """Apply common axis styling."""
    if ylabel:
        ax.set_ylabel(ylabel)
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.grid(axis="y", alpha=0.25)
    ax.grid(axis="x", alpha=0.08)


def add_shared_legend(fig, handles, labels, ncol=5, y=0.01):
    """Add a shared legend below the figure."""
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, y),
        ncol=ncol,
        frameon=True,
        fontsize=8,
        columnspacing=1.2,
        handlelength=2.0,
    )


# ═══════════════════════════════════════════════════════════════
# LINE CHART HELPER
# ═══════════════════════════════════════════════════════════════

def plot_line_with_band(ax, x, y_mean, y_ci_half, mode, label=None):
    """Plot a line with shaded CI band."""
    color = COLORS.get(mode, "#999999")
    marker = MARKERS.get(mode, "o")
    ls = LINESTYLES.get(mode, "-")
    lbl = label or LABELS.get(mode, mode)
    y_lo = y_mean - y_ci_half
    y_hi = y_mean + y_ci_half

    ax.fill_between(x, y_lo, y_hi, alpha=0.15, color=color, linewidth=0)
    ax.plot(x, y_mean, color=color, marker=marker, linestyle=ls,
            label=lbl, markersize=5, markeredgecolor="white", markeredgewidth=0.5)


def _subset_modes(df, modes):
    """Keep only requested modes that exist in the dataframe."""
    present = [m for m in modes if m in set(df["kv_mode"].unique())]
    return df[df["kv_mode"].isin(present)], present


def _load_primary_table(tables_dir, csv_name):
    return pd.read_csv(tables_dir / "per_model" / PRIMARY_MODEL_DIR / csv_name)


def _project_root():
    """Repository root inferred from this script location."""
    return Path(__file__).resolve().parent.parent


def _shared_mode_handles(modes):
    handles = []
    labels = []
    for mode in modes:
        handles.append(plt.Line2D(
            [0], [0],
            color=COLORS.get(mode, "#999999"),
            marker=MARKERS.get(mode, "o"),
            linestyle=LINESTYLES.get(mode, "-"),
            linewidth=1.8,
            markersize=5,
        ))
        labels.append(LABELS.get(mode, mode))
    return handles, labels


def fig_main_quality_dashboard(tables_dir, out_dir):
    """Create a 2x2 dashboard for core quality metrics."""
    print("Fig: main_quality_dashboard")

    needle = _load_primary_table(tables_dir, "needle_summary.csv")
    longbench = filter_mainline(_load_primary_table(tables_dir, "longbench_summary.csv"))
    ruler = filter_mainline(_load_primary_table(tables_dir, "ruler_summary.csv"))
    ppl = filter_mainline(_load_primary_table(tables_dir, "ppl_summary.csv"))

    needle, modes = _subset_modes(needle, QUALITY_DASHBOARD_MODES)
    longbench, _ = _subset_modes(longbench, modes)
    ruler, _ = _subset_modes(ruler, modes)

    seq_lens = sorted(set(needle["seq_len"].unique()))
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    ax_ppl, ax_needle, ax_longbench, ax_ruler = axes.flat

    # (a) PPL point / lollipop chart at 32K
    ppl32 = ppl[ppl["seq_len"] >= 30000].copy()
    ppl32, ppl_modes = _subset_modes(ppl32, modes)
    ppl32["mode_rank"] = ppl32["kv_mode"].map({m: i for i, m in enumerate(ppl_modes)})
    ppl32 = ppl32.sort_values("mode_rank", ascending=False)
    y_pos = np.arange(len(ppl32))
    ax_ppl.hlines(y_pos, ppl32["perplexity_mean"].min() - 0.2, ppl32["perplexity_mean"], color="#D7DEE5", linewidth=1.0)
    ax_ppl.errorbar(
        ppl32["perplexity_mean"], y_pos,
        xerr=ppl32["perplexity_ci95_half"],
        fmt="none", ecolor="#333333", elinewidth=1, capsize=3, zorder=3
    )
    for i, row in enumerate(ppl32.itertuples()):
        mode = row.kv_mode
        ax_ppl.scatter(
            row.perplexity_mean, y_pos[i],
            s=70 if mode == "int8_ours" else 45,
            color=COLORS.get(mode, "#999999"),
            edgecolors="white",
            linewidths=0.8,
            zorder=4,
        )
        ax_ppl.text(
            row.perplexity_mean + 0.06, y_pos[i],
            f"{row.perplexity_mean:.2f}",
            va="center", ha="left", fontsize=7.5, color="#333333"
        )
    ax_ppl.set_yticks(y_pos)
    ax_ppl.set_yticklabels([LABELS.get(m, m) for m in ppl32["kv_mode"]])
    style_axis(ax_ppl, xlabel="Perplexity at 32K")
    place_panel_tag(ax_ppl, "(a)", "PPL 主结果对比")

    # (b) Needle vs context
    for mode in modes:
        sub = needle[needle["kv_mode"] == mode].sort_values("seq_len")
        if sub.empty:
            continue
        plot_line_with_band(
            ax_needle,
            sub["seq_len"].values,
            sub["needle_pass_rate_mean"].values,
            sub["needle_pass_rate_ci95_half"].values,
            mode,
        )
        if mode in ("fp16", "int8_ours", "int4_ours"):
            annotate_last_point(
                ax_needle,
                sub["seq_len"].values,
                sub["needle_pass_rate_mean"].values,
                LABELS.get(mode, mode),
                COLORS.get(mode, "#333333"),
                dx=0.015,
                dy=0.0 if mode != "fp16" else -2.5,
            )
    ax_needle.set_xticks(seq_lens)
    ax_needle.set_xticklabels([format_seq_len(s) for s in seq_lens])
    ax_needle.set_ylim(-5, 108)
    style_axis(ax_needle, ylabel="Needle Pass Rate (%)", xlabel="Context Length")
    place_panel_tag(ax_needle, "(b)", "Needle 通过率随上下文长度变化")

    # (c) LongBench vs context
    for mode in modes:
        sub = longbench[longbench["kv_mode"] == mode].sort_values("seq_len")
        if sub.empty:
            continue
        y_col = "longbench_score_mean" if "longbench_score_mean" in sub.columns else "longbench_official_macro_mean"
        ci_col = "longbench_score_ci95_half" if "longbench_score_ci95_half" in sub.columns else "longbench_official_macro_ci95_half"
        y = sub[y_col].values * 100
        ci = sub[ci_col].values * 100 if ci_col in sub.columns else np.zeros_like(y)
        plot_line_with_band(ax_longbench, sub["seq_len"].values, y, ci, mode)
        if mode in ("fp16", "int8_ours"):
            annotate_last_point(
                ax_longbench, sub["seq_len"].values, y,
                LABELS.get(mode, mode), COLORS.get(mode, "#333333"),
                dx=0.015, dy=0.0 if mode == "int8_ours" else -0.18,
            )
    ax_longbench.set_xticks(seq_lens)
    ax_longbench.set_xticklabels([format_seq_len(s) for s in seq_lens])
    style_axis(ax_longbench, ylabel="LongBench Score (×100)", xlabel="Context Length")
    place_panel_tag(ax_longbench, "(c)", "LongBench 综合评分随上下文长度变化")

    # (d) RULER vs context
    for mode in modes:
        sub = ruler[ruler["kv_mode"] == mode].sort_values("seq_len")
        if sub.empty:
            continue
        plot_line_with_band(
            ax_ruler,
            sub["seq_len"].values,
            sub["ruler_pass_rate_mean"].values,
            sub["ruler_pass_rate_ci95_half"].values,
            mode,
        )
        if mode in ("fp16", "int8_ours", "int4_ours"):
            annotate_last_point(
                ax_ruler,
                sub["seq_len"].values,
                sub["ruler_pass_rate_mean"].values,
                LABELS.get(mode, mode),
                COLORS.get(mode, "#333333"),
                dx=0.015,
                dy=0.0 if mode != "fp16" else -1.4,
            )
    ax_ruler.set_xticks(seq_lens)
    ax_ruler.set_xticklabels([format_seq_len(s) for s in seq_lens])
    style_axis(ax_ruler, ylabel="RULER Pass Rate (%)", xlabel="Context Length")
    place_panel_tag(ax_ruler, "(d)", "RULER 通过率随上下文长度变化")

    handles, labels = _shared_mode_handles(modes)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    add_shared_legend(fig, handles, labels, ncol=min(5, len(labels)), y=0.005)
    save_fig(fig, out_dir / "main_quality_dashboard.pdf")


def fig_main_efficiency_dashboard(tables_dir, out_dir):
    """Create a 1x3 dashboard for efficiency and memory metrics."""
    print("Fig: main_efficiency_dashboard")

    latency = filter_mainline(_load_primary_table(tables_dir, "latency_summary.csv"))
    memory = filter_mainline(_load_primary_table(tables_dir, "memory_summary.csv"))

    latency = latency[(latency["batch"] == 1) & (latency["gen_len"] == 64)]
    memory = memory[memory["batch"] == 1]
    latency, modes = _subset_modes(latency, EFFICIENCY_DASHBOARD_MODES)
    memory, _ = _subset_modes(memory, modes)
    seq_lens = sorted(latency["seq_len"].unique())

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.1))
    ax_tpot, ax_kv, ax_peak = axes

    for mode in modes:
        sub = latency[latency["kv_mode"] == mode].sort_values("seq_len")
        if sub.empty:
            continue
        plot_line_with_band(ax_tpot, sub["seq_len"].values, sub["tpot_ms_mean"].values, sub["tpot_ms_ci95_half"].values, mode)
        if mode in ("fp16", "int8_ours"):
            annotate_last_point(
                ax_tpot, sub["seq_len"].values, sub["tpot_ms_mean"].values,
                LABELS.get(mode, mode), COLORS.get(mode, "#333333"),
                dx=0.015, dy=-1.2 if mode == "fp16" else 0.0,
            )
    ax_tpot.set_xticks(seq_lens)
    ax_tpot.set_xticklabels([format_seq_len(s) for s in seq_lens])
    style_axis(ax_tpot, ylabel="TPOT (ms)", xlabel="Context Length")
    place_panel_tag(ax_tpot, "(a)", "解码延迟")

    base32 = latency[(latency["kv_mode"] == "int8_baseline") & (latency["seq_len"] == max(seq_lens))]
    ours32 = latency[(latency["kv_mode"] == "int8_ours") & (latency["seq_len"] == max(seq_lens))]
    if not base32.empty and not ours32.empty:
        gain = (base32["tpot_ms_mean"].iloc[0] - ours32["tpot_ms_mean"].iloc[0]) / base32["tpot_ms_mean"].iloc[0] * 100
        ax_tpot.text(
            0.02, 0.06,
            f"32K: INT8-Ours vs INT8-Baseline = +{gain:.1f}% faster",
            transform=ax_tpot.transAxes, fontsize=7.5, color=COLORS["int8_ours"],
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=COLORS["int8_ours"], lw=0.7),
        )

    for mode in modes:
        sub = memory[memory["kv_mode"] == mode].sort_values("seq_len")
        if sub.empty:
            continue
        plot_line_with_band(ax_kv, sub["seq_len"].values, sub["kv_cache_mem_mb_mean"].values, sub["kv_cache_mem_mb_ci95_half"].values, mode)
        if mode in ("fp16", "int8_ours"):
            annotate_last_point(
                ax_kv, sub["seq_len"].values, sub["kv_cache_mem_mb_mean"].values,
                LABELS.get(mode, mode), COLORS.get(mode, "#333333"),
                dx=0.015, dy=-18 if mode == "fp16" else 14,
            )
    ax_kv.set_xticks(seq_lens)
    ax_kv.set_xticklabels([format_seq_len(s) for s in seq_lens])
    style_axis(ax_kv, ylabel="KV Cache Memory (MB)", xlabel="Context Length")
    place_panel_tag(ax_kv, "(b)", "KV Cache 显存")

    fp16_mem = memory[(memory["kv_mode"] == "fp16") & (memory["seq_len"] == max(seq_lens))]
    int8_mem = memory[(memory["kv_mode"] == "int8_ours") & (memory["seq_len"] == max(seq_lens))]
    if not fp16_mem.empty and not int8_mem.empty:
        gain = (fp16_mem["kv_cache_mem_mb_mean"].iloc[0] - int8_mem["kv_cache_mem_mb_mean"].iloc[0]) / fp16_mem["kv_cache_mem_mb_mean"].iloc[0] * 100
        ax_kv.text(
            0.02, 0.92,
            f"32K memory reduction: {gain:.1f}%",
            transform=ax_kv.transAxes, fontsize=7.5, color=COLORS["int8_ours"],
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=COLORS["int8_ours"], lw=0.7),
        )

    for mode in modes:
        sub = memory[memory["kv_mode"] == mode].sort_values("seq_len")
        if sub.empty:
            continue
        plot_line_with_band(ax_peak, sub["seq_len"].values, sub["gpu_mem_peak_mb_mean"].values, sub["gpu_mem_peak_mb_ci95_half"].values, mode)
        if mode in ("fp16", "int8_ours"):
            annotate_last_point(
                ax_peak, sub["seq_len"].values, sub["gpu_mem_peak_mb_mean"].values,
                LABELS.get(mode, mode), COLORS.get(mode, "#333333"),
                dx=0.015, dy=-60 if mode == "fp16" else 45,
            )
    ax_peak.set_xticks(seq_lens)
    ax_peak.set_xticklabels([format_seq_len(s) for s in seq_lens])
    style_axis(ax_peak, ylabel="Peak GPU Memory (MB)", xlabel="Context Length")
    place_panel_tag(ax_peak, "(c)", "总峰值显存")

    handles, labels = _shared_mode_handles(modes)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    add_shared_legend(fig, handles, labels, ncol=min(5, len(labels)), y=0.01)
    save_fig(fig, out_dir / "main_efficiency_dashboard.pdf")


def fig_needle_depth_grid(tables_dir, out_dir):
    """2x2 dashboard for Needle depth heatmaps."""
    print("Fig: needle_depth_grid")
    csv_path = tables_dir / "needle_curve_by_depth.csv"
    if not csv_path.exists():
        print(f"  SKIP: {csv_path} not found")
        return

    df = pd.read_csv(csv_path)
    context_lens = sorted(df["context_len"].unique())
    modes = sort_modes(df["kv_mode"].unique())
    depths = sorted(df["depth"].unique())
    fig, axes = plt.subplots(2, 2, figsize=(12, 6.8), sharex=True, sharey=True)
    ims = []

    for ax, ctx, tag in zip(axes.flat, context_lens, ["(a)", "(b)", "(c)", "(d)"]):
        sub = df[df["context_len"] == ctx]
        matrix = np.full((len(modes), len(depths)), np.nan)
        for i, mode in enumerate(modes):
            for j, depth in enumerate(depths):
                cell = sub[(sub["kv_mode"] == mode) & (np.isclose(sub["depth"], depth))]
                if not cell.empty:
                    matrix[i, j] = cell["pass_rate"].iloc[0] * 100
        im = ax.imshow(matrix, aspect="auto", cmap="RdYlGn", vmin=0, vmax=100, interpolation="nearest")
        ims.append(im)
        ax.set_yticks(range(len(modes)))
        ax.set_yticklabels([LABELS.get(m, m) for m in modes], fontsize=7.5)
        step = max(1, len(depths) // 8)
        ax.set_xticks(range(0, len(depths), step))
        ax.set_xticklabels([f"{depths[i]:.0f}%" for i in range(0, len(depths), step)], fontsize=7)
        place_panel_tag(ax, tag, f"Context = {format_seq_len(int(ctx))}")
        if ax in axes[1]:
            ax.set_xlabel("Needle Depth (%)")
        if ax in (axes[0, 0], axes[1, 0]):
            ax.set_ylabel("Quantization Mode")
        for i in range(len(modes)):
            for j in range(len(depths)):
                val = matrix[i, j]
                if not np.isnan(val) and val < 99.5:
                    ax.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=5.5,
                            color="white" if val < 45 else "black", fontweight="bold")

    cbar = fig.colorbar(ims[-1], ax=axes.ravel().tolist(), shrink=0.96, pad=0.02)
    cbar.set_label("Pass Rate (%)", fontsize=9)
    fig.subplots_adjust(left=0.08, right=0.92, bottom=0.10, top=0.94, wspace=0.18, hspace=0.20)
    save_fig(fig, out_dir / "needle_depth_grid.pdf")


def fig_appendix_throughput_dashboard(tables_dir, out_dir):
    """1x3 appendix dashboard for batch throughput scaling."""
    print("Fig: appendix_throughput_dashboard")
    df = pd.read_csv(tables_dir / "per_model" / PRIMARY_MODEL_DIR / "throughput_by_batch.csv")
    df = filter_mainline(df)
    seq_len_counts = df["seq_len"].value_counts()
    target_seq = seq_len_counts.index[0]
    df = df[df["seq_len"] == target_seq]
    df_plot = df[df["point_status"] == "measured"] if "point_status" in df.columns else df
    df_plot, modes = _subset_modes(df_plot, EFFICIENCY_DASHBOARD_MODES)

    panels = [
        ("tok_per_s_mean", "tok_per_s_ci95_half", "总吞吐量 (tokens/s)", "(a) 总吞吐量"),
        ("tok_per_s_per_seq_mean", "tok_per_s_per_seq_ci95_half", "单序列吞吐量 (tokens/s/seq)", "(b) 单序列吞吐量"),
        ("prefill_tok_per_s_mean", "prefill_tok_per_s_ci95_half", "Prefill 吞吐量 (tokens/s)", "(c) Prefill 吞吐量"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharex=True)
    batches = sorted(df_plot["batch"].unique())
    for ax, (y_col, ci_col, ylabel, title) in zip(axes, panels):
        for mode in modes:
            sub = df_plot[df_plot["kv_mode"] == mode].sort_values("batch")
            if sub.empty or y_col not in sub.columns:
                continue
            plot_line_with_band(ax, sub["batch"].values, sub[y_col].values, sub[ci_col].values, mode)
            if mode in ("fp16", "int8_ours"):
                annotate_last_point(ax, sub["batch"].values, sub[y_col].values, LABELS.get(mode, mode), COLORS.get(mode, "#333333"), dx=0.15, dy=0.0)
        ax.set_xticks(batches)
        ax.set_xticklabels([str(int(b)) for b in batches])
        style_axis(ax, ylabel=ylabel, xlabel="Batch Size")
        place_panel_tag(ax, title.split()[0], " ".join(title.split()[1:]))
    handles, labels = _shared_mode_handles(modes)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    add_shared_legend(fig, handles, labels, ncol=min(5, len(labels)), y=0.01)
    save_fig(fig, out_dir / "appendix_throughput_dashboard.pdf")


def fig_appendix_memory_dashboard(tables_dir, out_dir):
    """1x2 appendix dashboard for batch memory scaling."""
    print("Fig: appendix_memory_dashboard")
    df = pd.read_csv(tables_dir / "per_model" / PRIMARY_MODEL_DIR / "throughput_by_batch.csv")
    df = filter_mainline(df)
    seq_len_counts = df["seq_len"].value_counts()
    target_seq = seq_len_counts.index[0]
    df = df[df["seq_len"] == target_seq]
    df_plot = df[df["point_status"] == "measured"] if "point_status" in df.columns else df
    df_plot, modes = _subset_modes(df_plot, EFFICIENCY_DASHBOARD_MODES)

    panels = [
        ("kv_cache_mem_mb_mean", "kv_cache_mem_mb_ci95_half", "KV Cache 显存 (MB)", "(a) KV Cache 显存"),
        ("gpu_mem_peak_mb_mean", "gpu_mem_peak_mb_ci95_half", "总峰值显存 (MB)", "(b) 总峰值显存"),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.1), sharex=True)
    batches = sorted(df_plot["batch"].unique())
    for ax, (y_col, ci_col, ylabel, title) in zip(axes, panels):
        for mode in modes:
            sub = df_plot[df_plot["kv_mode"] == mode].sort_values("batch")
            if sub.empty or y_col not in sub.columns:
                continue
            plot_line_with_band(ax, sub["batch"].values, sub[y_col].values, sub[ci_col].values, mode)
            if mode in ("fp16", "int8_ours"):
                annotate_last_point(ax, sub["batch"].values, sub[y_col].values, LABELS.get(mode, mode), COLORS.get(mode, "#333333"), dx=0.15, dy=0.0)
        ax.set_xticks(batches)
        ax.set_xticklabels([str(int(b)) for b in batches])
        style_axis(ax, ylabel=ylabel, xlabel="Batch Size")
        place_panel_tag(ax, title.split()[0], " ".join(title.split()[1:]))
    handles, labels = _shared_mode_handles(modes)
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    add_shared_legend(fig, handles, labels, ncol=min(5, len(labels)), y=0.01)
    save_fig(fig, out_dir / "appendix_memory_dashboard.pdf")


def fig_kv_ablation_summary_ruler(project_root, out_dir):
    """Grouped bar chart summarizing K/V sensitivity with MixedKV."""
    print("Fig: kv_ablation_summary_ruler")
    ruler_path = project_root / "results" / "emnlp_expansion_v1" / "tables" / "kv_ablation_ruler.csv"
    if not ruler_path.exists():
        print(f"  SKIP: {ruler_path} not found")
        return

    ruler = pd.read_csv(ruler_path)
    model_rows = [
        ("Qwen2.5-1.5B", "1p5b", project_root / "results" / "paper_tables" / "table3_mixedkv_qwen25_1p5b.csv"),
        ("Qwen2.5-7B", "7b", project_root / "results" / "paper_tables" / "table3_mixedkv_qwen25_7b.csv"),
        ("LLaMA-3.1-8B", "8b", project_root / "results" / "paper_tables" / "table3_mixedkv_llama31_8b.csv"),
    ]
    methods = ["K-only", "V-only", "K4V8", "MixedKV"]
    values = {m: [] for m in methods}

    for model_label, model_key, mixedkv_csv in model_rows:
        sub = ruler[ruler["model_key"] == model_key]
        values["K-only"].append(float(sub[sub["method"] == "K-only"]["mean"].iloc[0]))
        values["V-only"].append(float(sub[sub["method"] == "V-only"]["mean"].iloc[0]))
        values["K4V8"].append(float(sub[sub["method"] == "K4V8"]["mean"].iloc[0]))
        mixed_df = pd.read_csv(mixedkv_csv)
        mixed_val = float(mixed_df[mixed_df["kv_mode"] == "int4_mixed_kv"]["ruler_mean"].iloc[0])
        values["MixedKV"].append(mixed_val)

    fig, ax = plt.subplots(figsize=(8.8, 4.6))
    x = np.arange(len(model_rows))
    width = 0.18
    for i, method in enumerate(methods):
        offset = (i - 1.5) * width
        bars = ax.bar(
            x + offset,
            values[method],
            width=width,
            color=KV_ABLATION_COLORS[method],
            edgecolor="white",
            linewidth=0.5,
            label=method,
            zorder=3,
        )
        for bar, val in zip(bars, values[method]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                val + 0.55,
                f"{val:.1f}",
                ha="center",
                va="bottom",
                fontsize=7.2,
                color="#333333",
            )
    ax.set_xticks(x)
    ax.set_xticklabels([row[0].replace("Qwen2.5-", "Qwen\n").replace("LLaMA-3.1-", "LLaMA\n") for row in model_rows])
    style_axis(ax, ylabel="RULER Pass Rate (%)")
    place_panel_tag(ax, "", "K/V 敏感性总结（RULER, 32K）")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.14), frameon=True, fontsize=8)
    ax.text(
        0.02, 0.03,
        "K4V8 在 Qwen 上完全崩溃，而 MixedKV 保留了可用质量。",
        transform=ax.transAxes, fontsize=7.6, color="#333333",
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#CCCCCC", lw=0.7),
    )
    fig.tight_layout()
    save_fig(fig, out_dir / "kv_ablation_summary_ruler.pdf")


# ═══════════════════════════════════════════════════════════════
# FIGURE 1: PPL Grouped Bar Chart
# ═══════════════════════════════════════════════════════════════

def fig_ppl_bar(tables_dir, out_dir):
    """PPL as grouped bar chart with inset zoom for INT8 range."""
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes

    print("Fig: ppl_vs_tokens (grouped bar chart + inset)")
    df = pd.read_csv(tables_dir / "per_model" / PRIMARY_MODEL_DIR / "ppl_summary.csv")
    df = filter_mainline(df)

    modes = sort_modes(df["kv_mode"].unique())
    means = []
    ci_halfs = []
    for m in modes:
        sub = df[df["kv_mode"] == m]
        if sub.empty:
            means.append(0)
            ci_halfs.append(0)
        else:
            means.append(sub["perplexity_mean"].iloc[0])
            ci_halfs.append(sub["perplexity_ci95_half"].iloc[0])

    fig, ax = plt.subplots(figsize=(7.5, 4))
    x = np.arange(len(modes))
    colors = [COLORS.get(m, "#999") for m in modes]
    bars = ax.bar(x, means, width=0.6, color=colors, edgecolor="white",
                  linewidth=0.5, zorder=3)
    ax.errorbar(x, means, yerr=ci_halfs, fmt="none", ecolor="#333333",
                elinewidth=1, capsize=3, zorder=4)

    # Value labels on bars
    for i, (bar, val) in enumerate(zip(bars, means)):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + ci_halfs[i] + 0.3,
                f"{val:.3f}", ha="center", va="bottom", fontsize=7.5, color="#333")

    ax.set_xticks(x)
    ax.set_xticklabels([LABELS.get(m, m) for m in modes], rotation=25, ha="right")
    ax.set_ylabel("Perplexity")
    ax.set_title("各量化模式的困惑度 (32K Context)", fontsize=10, pad=8)
    ax.set_ylim(0, max(means) * 1.12)
    ax.grid(axis="y", alpha=0.3)
    ax.grid(axis="x", visible=False)

    # --- Inset: zoom into INT8 range ---
    # Identify INT8-class modes (PPL close to FP16)
    int8_idx = [i for i, m in enumerate(modes)
                if m in ("fp16", "int8_baseline", "int8_ours", "kivi_style")]
    if int8_idx:
        int8_means = [means[i] for i in int8_idx]
        int8_ci = [ci_halfs[i] for i in int8_idx]
        int8_labels = [LABELS.get(modes[i], modes[i]) for i in int8_idx]
        int8_colors = [colors[i] for i in int8_idx]

        ax_inset = inset_axes(ax, width="42%", height="50%", loc="upper left",
                              bbox_to_anchor=(0.05, 0.0, 1, 1),
                              bbox_transform=ax.transAxes)
        xi = np.arange(len(int8_idx))
        bars_i = ax_inset.bar(xi, int8_means, width=0.55, color=int8_colors,
                              edgecolor="white", linewidth=0.5, zorder=3)
        ax_inset.errorbar(xi, int8_means, yerr=int8_ci, fmt="none",
                          ecolor="#333", elinewidth=0.8, capsize=2, zorder=4)

        for j, (bar, val, ci) in enumerate(zip(bars_i, int8_means, int8_ci)):
            ax_inset.text(bar.get_x() + bar.get_width() / 2, val + ci + 0.003,
                          f"{val:.4f}", ha="center", va="bottom", fontsize=6.5, color="#333")

        ymin_i = min(int8_means) - 0.05
        ymax_i = max(int8_means) + 0.08
        ax_inset.set_ylim(ymin_i, ymax_i)
        ax_inset.set_xticks(xi)
        ax_inset.set_xticklabels(int8_labels, fontsize=6.5, rotation=15, ha="right")
        ax_inset.set_ylabel("PPL (zoomed)", fontsize=7)
        ax_inset.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.3f"))
        ax_inset.tick_params(labelsize=6.5)
        ax_inset.set_title("INT8 Range (zoom)", fontsize=7.5, pad=3)
        ax_inset.grid(axis="y", alpha=0.3, linewidth=0.3)
        ax_inset.grid(axis="x", visible=False)
        # FP16 baseline line in inset
        fp16_val = means[modes.index("fp16")] if "fp16" in modes else None
        if fp16_val:
            ax_inset.axhline(y=fp16_val, color=COLORS["fp16"], linestyle="--",
                             linewidth=0.6, alpha=0.5)

    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.20, top=0.92)
    save_fig(fig, out_dir / "ppl_vs_tokens.pdf")


# ═══════════════════════════════════════════════════════════════
# FIGURE 2: Needle Dual-Panel
# ═══════════════════════════════════════════════════════════════

def fig_needle_dual_panel(tables_dir, out_dir):
    """Needle pass rate: INT8 panel (left) + INT4 panel (right)."""
    print("Fig: needle_pass_rate_vs_context (dual panel)")
    df = pd.read_csv(tables_dir / "per_model" / PRIMARY_MODEL_DIR / "needle_summary.csv")
    # needle_summary has no group_size/clip columns — data is pre-aggregated

    seq_lens = sorted(df["seq_len"].unique())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)

    for ax, mode_set, title in [
        (ax1, INT8_MODES, "(a) INT8 Quantization"),
        (ax2, INT4_MODES, "(b) INT4 Quantization"),
    ]:
        for mode in mode_set:
            sub = df[df["kv_mode"] == mode].sort_values("seq_len")
            if sub.empty:
                continue
            x = sub["seq_len"].values
            y = sub["needle_pass_rate_mean"].values
            ci = sub["needle_pass_rate_ci95_half"].values
            plot_line_with_band(ax, x, y, ci, mode)

        ax.set_xlabel("Context Length")
        ax.set_title(title, fontsize=10)
        ax.set_xticks(seq_lens)
        ax.set_xticklabels([format_seq_len(s) for s in seq_lens])
        ax.set_ylim(-5, 108)
        ax.legend(loc="lower left", fontsize=7.5)

    ax1.set_ylabel("Needle Pass Rate (%)")
    fig.tight_layout(w_pad=2)
    save_fig(fig, out_dir / "needle_pass_rate_vs_context.pdf")


# ═══════════════════════════════════════════════════════════════
# FIGURE 3-5: Latency/Memory vs Sequence Length (batch=1)
# ═══════════════════════════════════════════════════════════════

def _plot_metric_vs_seq(tables_dir, out_dir, filename, y_col, y_ci_col,
                        ylabel, title, gen_len=64):
    """Generic line chart: metric vs seq_len at batch=1."""
    print(f"Fig: {filename}")
    csv_name = "latency_summary.csv" if "tpot" in y_col else "memory_summary.csv"
    df = pd.read_csv(tables_dir / "per_model" / PRIMARY_MODEL_DIR / csv_name)
    df = filter_mainline(df)

    # Filter to batch=1, gen_len
    mask = (df["batch"] == 1)
    if "gen_len" in df.columns:
        mask &= (df["gen_len"] == gen_len)
    df = df[mask]

    seq_lens = sorted(df["seq_len"].unique())
    modes = sort_modes(df["kv_mode"].unique())

    fig, ax = plt.subplots(figsize=(6.5, 4))
    for mode in modes:
        sub = df[df["kv_mode"] == mode].sort_values("seq_len")
        if sub.empty or y_col not in sub.columns:
            continue
        x = sub["seq_len"].values
        y = sub[y_col].values
        ci = sub[y_ci_col].values if y_ci_col in sub.columns else np.zeros_like(y)
        plot_line_with_band(ax, x, y, ci, mode)

    ax.set_xlabel("Sequence Length")
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=10, pad=8)
    ax.set_xticks(seq_lens)
    ax.set_xticklabels([format_seq_len(s) for s in seq_lens])
    ax.legend(fontsize=7.5, ncol=2)
    fig.tight_layout()
    save_fig(fig, out_dir / filename)


def fig_tpot_vs_seq(tables_dir, out_dir):
    _plot_metric_vs_seq(tables_dir, out_dir, "latency_tpot_vs_seq.pdf",
                        "tpot_ms_mean", "tpot_ms_ci95_half",
                        "TPOT (ms)", "解码延迟 (TPOT) 随序列长度的变化 (batch=1)")


def fig_memory_kv_vs_seq(tables_dir, out_dir):
    _plot_metric_vs_seq(tables_dir, out_dir, "memory_kv_cache_vs_seq.pdf",
                        "kv_cache_mem_mb_mean", "kv_cache_mem_mb_ci95_half",
                        "KV Cache Memory (MB)", "KV Cache 显存随序列长度的变化 (batch=1)")


def fig_memory_peak_vs_seq(tables_dir, out_dir):
    _plot_metric_vs_seq(tables_dir, out_dir, "memory_peak_vs_seq.pdf",
                        "gpu_mem_peak_mb_mean", "gpu_mem_peak_mb_ci95_half",
                        "Peak GPU Memory (MB)", "总峰值显存随序列长度的变化 (batch=1)")


# ═══════════════════════════════════════════════════════════════
# FIGURE 6: Inverse Temperature Heatmap (ch3)
# ═══════════════════════════════════════════════════════════════

def fig_invtau_heatmap(tables_dir, out_dir):
    """Heatmap of per-layer per-head inv_tau from calibration artifact."""
    print("Fig: ch3_invtau_heatmap")
    # Calibration artifact is at project root / artifacts/
    project_root = tables_dir
    while project_root != project_root.parent:
        if (project_root / "artifacts").is_dir():
            break
        project_root = project_root.parent
    calib_path = project_root / "artifacts" / "kv_calib_kl_selected_v3_quick.json"
    if not calib_path.exists():
        print(f"  SKIP: {calib_path} not found")
        return

    with open(calib_path) as f:
        calib = json.load(f)

    inv_tau = np.array(calib["inv_tau"])  # shape: (num_layers, num_heads)
    n_layers, n_heads = inv_tau.shape

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(inv_tau, aspect="auto", cmap="RdYlGn_r",
                   vmin=0.4, vmax=1.2, interpolation="nearest")

    ax.set_xlabel("Head Index")
    ax.set_ylabel("Layer Index")
    ax.set_title(f"Per-Layer Per-Head Inverse Temperature ($\\tau^{{-1}}$)\n"
                 f"{calib.get('model_id', 'Qwen2.5-1.5B-Instruct')}, INT8 KL Calibration",
                 fontsize=10, pad=10)

    # Tick labels
    ax.set_xticks(range(0, n_heads, max(1, n_heads // 12)))
    ax.set_yticks(range(0, n_layers, max(1, n_layers // 14)))

    cbar = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
    cbar.set_label("$\\tau^{-1}$", fontsize=10)

    # Annotate cells where tau != 1.0
    for i in range(n_layers):
        for j in range(n_heads):
            val = inv_tau[i, j]
            if abs(val - 1.0) > 0.01:
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=5.5, color="white" if val < 0.7 else "black")

    fig.tight_layout()
    save_fig(fig, out_dir / "ch3_invtau_heatmap.pdf")


# ═══════════════════════════════════════════════════════════════
# FIGURE 7: RULER Pass Rate vs Context
# ═══════════════════════════════════════════════════════════════

def fig_ruler_vs_context(tables_dir, out_dir):
    """RULER pass rate vs sequence length."""
    print("Fig: ruler_pass_rate_vs_context")
    df = pd.read_csv(tables_dir / "per_model" / PRIMARY_MODEL_DIR / "ruler_summary.csv")
    df = filter_mainline(df)

    seq_lens = sorted(df["seq_len"].unique())
    modes = sort_modes(df["kv_mode"].unique())

    fig, ax = plt.subplots(figsize=(6.5, 4))
    for mode in modes:
        sub = df[df["kv_mode"] == mode].sort_values("seq_len")
        if sub.empty:
            continue
        x = sub["seq_len"].values
        y = sub["ruler_pass_rate_mean"].values
        ci = sub["ruler_pass_rate_ci95_half"].values
        plot_line_with_band(ax, x, y, ci, mode)

    ax.set_xlabel("Context Length")
    ax.set_ylabel("RULER Pass Rate (%)")
    ax.set_title("RULER 通过率随上下文长度的变化", fontsize=10, pad=8)
    ax.set_xticks(seq_lens)
    ax.set_xticklabels([format_seq_len(s) for s in seq_lens])
    ax.legend(fontsize=7.5, ncol=2)
    fig.tight_layout()
    save_fig(fig, out_dir / "ruler_pass_rate_vs_context.pdf")


# ═══════════════════════════════════════════════════════════════
# FIGURE 8: LongBench Score vs Context
# ═══════════════════════════════════════════════════════════════

def fig_longbench_vs_context(tables_dir, out_dir):
    """LongBench composite score vs sequence length."""
    print("Fig: longbench_score_vs_context")
    df = pd.read_csv(tables_dir / "per_model" / PRIMARY_MODEL_DIR / "longbench_summary.csv")
    df = filter_mainline(df)

    seq_lens = sorted(df["seq_len"].unique())
    modes = sort_modes(df["kv_mode"].unique())

    fig, ax = plt.subplots(figsize=(6.5, 4))
    for mode in modes:
        sub = df[df["kv_mode"] == mode].sort_values("seq_len")
        if sub.empty:
            continue
        y_col = "longbench_score_mean"
        ci_col = "longbench_score_ci95_half"
        if y_col not in sub.columns:
            y_col = "longbench_official_macro_mean"
            ci_col = "longbench_official_macro_ci95_half"
        x = sub["seq_len"].values
        y = sub[y_col].values
        ci = sub[ci_col].values if ci_col in sub.columns else np.zeros_like(y)
        plot_line_with_band(ax, x, y, ci, mode)

    ax.set_xlabel("Context Length")
    ax.set_ylabel("LongBench Score")
    ax.set_title("LongBench 综合评分随上下文长度的变化", fontsize=10, pad=8)
    ax.set_xticks(seq_lens)
    ax.set_xticklabels([format_seq_len(s) for s in seq_lens])
    ax.legend(fontsize=7.5, ncol=2)
    fig.tight_layout()
    save_fig(fig, out_dir / "longbench_score_vs_context.pdf")


# ═══════════════════════════════════════════════════════════════
# FIGURE 9-12: Needle Depth Heatmaps
# ═══════════════════════════════════════════════════════════════

def fig_needle_depth_heatmaps(tables_dir, out_dir):
    """Needle pass rate by depth for each context length."""
    print("Fig: needle_curve_depth heatmaps")
    csv_path = tables_dir / "needle_curve_by_depth.csv"
    if not csv_path.exists():
        print(f"  SKIP: {csv_path} not found")
        return

    df = pd.read_csv(csv_path)
    context_lens = sorted(df["context_len"].unique())

    for ctx in context_lens:
        fname = f"needle_curve_depth_ctx{int(ctx)}.pdf"
        print(f"  Sub-fig: {fname}")
        sub = df[df["context_len"] == ctx]

        modes = sort_modes(sub["kv_mode"].unique())
        depths = sorted(sub["depth"].unique())

        # Build matrix: rows=modes, cols=depths
        matrix = np.full((len(modes), len(depths)), np.nan)
        for i, mode in enumerate(modes):
            for j, depth in enumerate(depths):
                cell = sub[(sub["kv_mode"] == mode) & (np.isclose(sub["depth"], depth))]
                if not cell.empty:
                    matrix[i, j] = cell["pass_rate"].iloc[0] * 100

        fig, ax = plt.subplots(figsize=(8, 3.2))
        im = ax.imshow(matrix, aspect="auto", cmap="RdYlGn",
                       vmin=0, vmax=100, interpolation="nearest")

        ax.set_yticks(range(len(modes)))
        ax.set_yticklabels([LABELS.get(m, m) for m in modes], fontsize=8)

        # Depth ticks: show every other
        step = max(1, len(depths) // 8)
        ax.set_xticks(range(0, len(depths), step))
        ax.set_xticklabels([f"{depths[i]:.0f}%" for i in range(0, len(depths), step)],
                           fontsize=7)
        ax.set_xlabel("Needle Depth (%)")
        ax.set_title(f"Needle Pass Rate by Depth — Context = {format_seq_len(int(ctx))}",
                     fontsize=10, pad=8)

        cbar = fig.colorbar(im, ax=ax, shrink=0.9, pad=0.02)
        cbar.set_label("Pass Rate (%)", fontsize=8)

        # Annotate cells with < 100% pass rate
        for i in range(len(modes)):
            for j in range(len(depths)):
                val = matrix[i, j]
                if not np.isnan(val) and val < 99.5:
                    txt_color = "white" if val < 50 else "black"
                    ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                            fontsize=6, color=txt_color, fontweight="bold")

        fig.tight_layout()
        save_fig(fig, out_dir / fname)


# ═══════════════════════════════════════════════════════════════
# FIGURE 13: Needle Exact Match vs Context
# ═══════════════════════════════════════════════════════════════

def fig_needle_exact_match(tables_dir, out_dir):
    """Needle exact match rate vs context length."""
    print("Fig: needle_exact_match_vs_context")
    df = pd.read_csv(tables_dir / "per_model" / PRIMARY_MODEL_DIR / "needle_summary.csv")

    seq_lens = sorted(df["seq_len"].unique())
    modes = sort_modes(df["kv_mode"].unique())

    fig, ax = plt.subplots(figsize=(6.5, 4))
    for mode in modes:
        sub = df[df["kv_mode"] == mode].sort_values("seq_len")
        if sub.empty:
            continue
        x = sub["seq_len"].values
        y = sub["needle_exact_match_rate_mean"].values
        ci = sub["needle_exact_match_rate_ci95_half"].values
        plot_line_with_band(ax, x, y, ci, mode)

    ax.set_xlabel("Context Length")
    ax.set_ylabel("Exact Match Rate (%)")
    ax.set_title("Needle 精确匹配率随上下文长度的变化", fontsize=10, pad=8)
    ax.set_xticks(seq_lens)
    ax.set_xticklabels([format_seq_len(s) for s in seq_lens])
    ax.set_ylim(-5, 108)
    ax.legend(fontsize=7.5, ncol=2)
    fig.tight_layout()
    save_fig(fig, out_dir / "needle_exact_match_vs_context.pdf")


# ═══════════════════════════════════════════════════════════════
# FIGURE 14: TPOT Gain vs FP16
# ═══════════════════════════════════════════════════════════════

def fig_tpot_gain(tables_dir, out_dir):
    """TPOT speedup relative to FP16 (positive = faster)."""
    print("Fig: latency_tpot_gain_vs_fp16")
    # Compute gain from latency data rather than pre-computed CSV
    df = pd.read_csv(tables_dir / "per_model" / PRIMARY_MODEL_DIR / "latency_summary.csv")
    df = filter_mainline(df)

    # Filter batch=1, gen_len=64
    mask = (df["batch"] == 1) & (df["gen_len"] == 64)
    df = df[mask]

    seq_lens = sorted(df["seq_len"].unique())
    modes = sort_modes([m for m in df["kv_mode"].unique() if m != "fp16"])

    # Get FP16 baseline TPOT
    fp16 = df[df["kv_mode"] == "fp16"].set_index("seq_len")["tpot_ms_mean"]

    fig, ax = plt.subplots(figsize=(7, 4))
    bar_width = 0.12
    x = np.arange(len(seq_lens))

    for i, mode in enumerate(modes):
        sub = df[df["kv_mode"] == mode].set_index("seq_len")
        gains = []
        for s in seq_lens:
            if s in sub.index and s in fp16.index:
                # Positive gain = faster (lower TPOT)
                gain = (fp16[s] - sub.loc[s, "tpot_ms_mean"]) / fp16[s] * 100
                gains.append(gain)
            else:
                gains.append(0)

        offset = (i - len(modes) / 2 + 0.5) * bar_width
        bars = ax.bar(x + offset, gains, bar_width, color=COLORS.get(mode, "#999"),
                      edgecolor="white", linewidth=0.3, label=LABELS.get(mode, mode),
                      zorder=3)

    ax.axhline(y=0, color="#333", linewidth=0.8, linestyle="-", zorder=2)
    ax.set_xlabel("Sequence Length")
    ax.set_ylabel("TPOT Change vs FP16 (%)")
    ax.set_title("各量化模式相对 FP16 的 TPOT 变化 (batch=1)", fontsize=10, pad=8)
    ax.set_xticks(x)
    ax.set_xticklabels([format_seq_len(s) for s in seq_lens])

    # Annotate: above zero = faster, below zero = slower
    ylim = ax.get_ylim()
    ax.text(0.98, 0.97, "↑ 加速 (TPOT 降低)", transform=ax.transAxes,
            ha="right", va="top", fontsize=7, color="#27AE60", style="italic")
    ax.text(0.98, 0.03, "↓ 减速 (TPOT 增加)", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=7, color="#E74C3C", style="italic")

    ax.legend(fontsize=7, ncol=2, loc="lower left")
    ax.grid(axis="y", alpha=0.3)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    save_fig(fig, out_dir / "latency_tpot_gain_vs_fp16.pdf")


# ═══════════════════════════════════════════════════════════════
# FIGURES 15-19: Throughput/Memory vs Batch Size
# ═══════════════════════════════════════════════════════════════

def _plot_metric_vs_batch(tables_dir, out_dir, filename, y_col, y_ci_col,
                          ylabel, title, use_throughput_csv=True, add_oom=True):
    """Generic line chart: metric vs batch size at fixed seq_len."""
    print(f"Fig: {filename}")

    if use_throughput_csv:
        df = pd.read_csv(tables_dir / "per_model" / PRIMARY_MODEL_DIR / "throughput_by_batch.csv")
    else:
        # Use memory or latency data
        csv_name = "memory_summary.csv" if "mem" in y_col else "latency_summary.csv"
        df = pd.read_csv(tables_dir / "per_model" / PRIMARY_MODEL_DIR / csv_name)

    df = filter_mainline(df)

    # Determine seq_len for batch-varying figures
    # Use the most common seq_len in the data
    if "seq_len" in df.columns:
        seq_len_counts = df["seq_len"].value_counts()
        target_seq = seq_len_counts.index[0]
        df = df[df["seq_len"] == target_seq]

    if y_col not in df.columns:
        print(f"  SKIP: column {y_col} not in data")
        return

    # Filter measured points (for throughput data)
    if "point_status" in df.columns:
        df_plot = df[df["point_status"] == "measured"]
        df_oom = df[df["point_status"] != "measured"]
    else:
        df_plot = df
        df_oom = pd.DataFrame()

    modes = sort_modes(df_plot["kv_mode"].unique())
    fig, ax = plt.subplots(figsize=(7, 4.2))

    for mode in modes:
        sub = df_plot[df_plot["kv_mode"] == mode].sort_values("batch")
        if sub.empty:
            continue
        x = sub["batch"].values
        y = sub[y_col].values
        ci = sub[y_ci_col].values if y_ci_col in sub.columns else np.zeros_like(y)
        plot_line_with_band(ax, x, y, ci, mode)

    # Add OOM markers
    if add_oom and not df_oom.empty:
        for mode in df_oom["kv_mode"].unique():
            oom_sub = df_oom[df_oom["kv_mode"] == mode]
            for _, row in oom_sub.iterrows():
                ax.scatter(row["batch"], ax.get_ylim()[1] * 0.95,
                           marker="x", s=60, color=COLORS.get(mode, "#999"),
                           linewidths=2, zorder=5)

    # Add capacity limit annotations (only for throughput figures with OOM)
    if use_throughput_csv and add_oom:
        cap_path = tables_dir / "throughput_capacity_limits.csv"
        if cap_path.exists():
            caps = pd.read_csv(cap_path)
            for _, row in caps.iterrows():
                mode = row["kv_mode"]
                max_b = row.get("max_success_batch", None)
                if pd.notna(max_b) and mode in modes:
                    # Find the y-value at max batch
                    mode_data = df_plot[(df_plot["kv_mode"] == mode) &
                                       (df_plot["batch"] == max_b)]
                    if not mode_data.empty and y_col in mode_data.columns:
                        y_val = mode_data[y_col].iloc[0]
                        ax.annotate("", xy=(max_b + 0.5, y_val),
                                    xytext=(max_b + 2, y_val),
                                    arrowprops=dict(arrowstyle="->",
                                                    color=COLORS.get(mode, "#999"),
                                                    lw=1.5))

    ax.set_xlabel("Batch Size")
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=10, pad=8)

    # Set x ticks to actual batch values
    batches = sorted(df_plot["batch"].unique())
    ax.set_xticks(batches)
    ax.set_xticklabels([str(int(b)) for b in batches])

    ax.legend(fontsize=7.5, ncol=2)
    fig.tight_layout()
    save_fig(fig, out_dir / filename)


def fig_throughput_vs_batch(tables_dir, out_dir):
    _plot_metric_vs_batch(
        tables_dir, out_dir, "throughput_tok_per_s_vs_batch.pdf",
        "tok_per_s_mean", "tok_per_s_ci95_half",
        "Throughput (tokens/s)", "吞吐量随 Batch Size 的扩展曲线",
        use_throughput_csv=True)


def fig_throughput_per_seq_vs_batch(tables_dir, out_dir):
    _plot_metric_vs_batch(
        tables_dir, out_dir, "throughput_tok_per_s_per_seq_vs_batch.pdf",
        "tok_per_s_per_seq_mean", "tok_per_s_per_seq_ci95_half",
        "Throughput per Sequence (tokens/s/seq)",
        "单序列吞吐量随 Batch Size 的变化",
        use_throughput_csv=True)


def fig_memory_kv_vs_batch(tables_dir, out_dir):
    _plot_metric_vs_batch(
        tables_dir, out_dir, "memory_kv_cache_vs_batch.pdf",
        "kv_cache_mem_mb_mean", "kv_cache_mem_mb_ci95_half",
        "KV Cache Memory (MB)", "KV Cache 显存随 Batch Size 的变化",
        use_throughput_csv=True, add_oom=False)


def fig_memory_peak_vs_batch(tables_dir, out_dir):
    _plot_metric_vs_batch(
        tables_dir, out_dir, "memory_peak_vs_batch.pdf",
        "gpu_mem_peak_mb_mean", "gpu_mem_peak_mb_ci95_half",
        "Peak GPU Memory (MB)", "总峰值显存随 Batch Size 的变化",
        use_throughput_csv=True, add_oom=False)


def fig_prefill_vs_batch(tables_dir, out_dir):
    _plot_metric_vs_batch(
        tables_dir, out_dir, "prefill_tok_per_s_vs_batch.pdf",
        "prefill_tok_per_s_mean", "prefill_tok_per_s_ci95_half",
        "Prefill Throughput (tokens/s)", "Prefill 阶段吞吐量随 Batch Size 的变化",
        use_throughput_csv=True, add_oom=False)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Generate publication-quality thesis figures")
    parser.add_argument("--tables_dir", type=Path,
                        default=Path("results/emnlp_final_raw/tables"))
    parser.add_argument("--out_dir", type=Path, default=Path("thesis/figures"))
    parser.add_argument("--calib_artifact", type=Path,
                        default=Path("artifacts/kv_calib_kl_selected_v3_quick.json"))
    parser.add_argument("--only", type=str, default=None,
                        help="Generate only specific figure(s), comma-separated")
    args = parser.parse_args()

    tables_dir = args.tables_dir
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not tables_dir.exists():
        print(f"ERROR: tables_dir not found: {tables_dir}")
        return 1

    setup_style()
    print(f"Tables: {tables_dir}")
    print(f"Output: {out_dir}")
    print(f"DPI: {DPI}")
    print()

    # All figure generators
    generators = {
        "main_quality":     lambda: fig_main_quality_dashboard(tables_dir, out_dir),
        "main_efficiency":  lambda: fig_main_efficiency_dashboard(tables_dir, out_dir),
        "ppl":              lambda: fig_ppl_bar(tables_dir, out_dir),
        "needle":           lambda: fig_needle_dual_panel(tables_dir, out_dir),
        "tpot_seq":         lambda: fig_tpot_vs_seq(tables_dir, out_dir),
        "mem_kv_seq":       lambda: fig_memory_kv_vs_seq(tables_dir, out_dir),
        "mem_peak_seq":     lambda: fig_memory_peak_vs_seq(tables_dir, out_dir),
        "invtau":           lambda: fig_invtau_heatmap(tables_dir, out_dir),
        "ruler":            lambda: fig_ruler_vs_context(tables_dir, out_dir),
        "longbench":        lambda: fig_longbench_vs_context(tables_dir, out_dir),
        "needle_depth":     lambda: fig_needle_depth_heatmaps(tables_dir, out_dir),
        "needle_depth_grid": lambda: fig_needle_depth_grid(tables_dir, out_dir),
        "needle_exact":     lambda: fig_needle_exact_match(tables_dir, out_dir),
        "tpot_gain":        lambda: fig_tpot_gain(tables_dir, out_dir),
        "throughput_batch":     lambda: fig_throughput_vs_batch(tables_dir, out_dir),
        "throughput_per_seq":   lambda: fig_throughput_per_seq_vs_batch(tables_dir, out_dir),
        "mem_kv_batch":     lambda: fig_memory_kv_vs_batch(tables_dir, out_dir),
        "mem_peak_batch":   lambda: fig_memory_peak_vs_batch(tables_dir, out_dir),
        "prefill":          lambda: fig_prefill_vs_batch(tables_dir, out_dir),
        "throughput_dashboard": lambda: fig_appendix_throughput_dashboard(tables_dir, out_dir),
        "memory_dashboard": lambda: fig_appendix_memory_dashboard(tables_dir, out_dir),
        "kv_ablation_summary": lambda: fig_kv_ablation_summary_ruler(_project_root(), out_dir),
    }

    if args.only:
        selected = [s.strip() for s in args.only.split(",")]
    else:
        selected = list(generators.keys())

    success = 0
    failed = 0
    for name in selected:
        if name not in generators:
            print(f"WARN: unknown figure '{name}', skipping")
            continue
        try:
            generators[name]()
            success += 1
        except Exception as e:
            print(f"  ERROR: {name} — {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\nDone: {success} generated, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
