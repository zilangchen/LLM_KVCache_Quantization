#!/usr/bin/env python3
"""
P4 Figure: Quality-Efficiency Pareto Front
Shows the trade-off between KV compression ratio and retrieval quality (Needle %)
for all quantization methods.

Output: thesis/figures/pareto_quality_efficiency.pdf
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ──────────────────────────────────────────────────
# Data: 1.5B model (most challenging, best for showing trade-off)
# Source: tab:main-results + tab:rolealign-results
# ──────────────────────────────────────────────────
methods = {
    "FP16":              {"kv_mb": 896, "needle": 100.0, "ppl_delta": 0.0,    "marker": "s", "color": "#2c3e50", "size": 100},
    "INT8-baseline":     {"kv_mb": 504, "needle": 100.0, "ppl_delta": 0.0,    "marker": "D", "color": "#95a5a6", "size": 80},
    "INT8-ours":         {"kv_mb": 504, "needle": 100.0, "ppl_delta": 0.2,    "marker": "^", "color": "#2ecc71", "size": 100},
    "INT4-baseline\n(symmetric)": {"kv_mb": 252, "needle": 0.0,   "ppl_delta": 118.7, "marker": "v", "color": "#e74c3c", "size": 80},
    "KIVI-style":        {"kv_mb": 462, "needle": 99.0,  "ppl_delta": 6.2,    "marker": "p", "color": "#e67e22", "size": 90},
    "INT4-RoleAlign":    {"kv_mb": 252, "needle": 100.0, "ppl_delta": 13.7,   "marker": "*", "color": "#3498db", "size": 160},
}

fig, ax = plt.subplots(1, 1, figsize=(6, 4.2))

# Compression ratio = 1 - kv_mb / fp16_kv_mb
fp16_kv = 896

for name, d in methods.items():
    compression = (1 - d["kv_mb"] / fp16_kv) * 100
    ax.scatter(compression, d["needle"],
               marker=d["marker"], c=d["color"], s=d["size"],
               edgecolors="white", linewidths=0.8, zorder=5,
               label=name)

    # Labels with leader lines to avoid overlap at Needle=100%
    label_configs = {
        "FP16":              {"xt": 4,   "yt": 85, "ha": "left"},
        "INT8-baseline":     {"xt": 35,  "yt": 85, "ha": "center"},
        "INT8-ours":         {"xt": 25,  "yt": 78, "ha": "center"},
        "INT4-baseline\n(symmetric)": {"xt": 60, "yt": 10, "ha": "left"},
        "KIVI-style":        {"xt": 55,  "yt": 85, "ha": "center"},
        "INT4-RoleAlign":    {"xt": 60,  "yt": 78, "ha": "left"},
    }
    cfg = label_configs[name]
    ax.annotate(name.replace("\n", " "),
                xy=(compression, d["needle"]),
                xytext=(cfg["xt"], cfg["yt"]),
                fontsize=7.5, color=d["color"], fontweight="bold",
                ha=cfg["ha"], va="center",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor=d["color"],
                          linewidth=0.5, alpha=0.85),
                arrowprops=dict(arrowstyle="-", color=d["color"], lw=0.8, alpha=0.5))

# Highlight the "ideal corner" (high compression + high quality)
ax.axhspan(95, 101, alpha=0.06, color="#27ae60", zorder=0)
ax.axvspan(65, 80, alpha=0.06, color="#27ae60", zorder=0)
ax.text(74, 93, "Ideal\nregion", fontsize=8, color="#27ae60",
        ha="center", va="center", alpha=0.4, style="italic")

# Catastrophic failure zone
ax.axhspan(-2, 10, alpha=0.04, color="#e74c3c", zorder=0)
ax.text(40, 4, "Catastrophic failure", fontsize=7, color="#e74c3c",
        ha="center", alpha=0.5, style="italic")

# Styling
ax.set_xlabel("KV Cache Compression (%)", fontsize=10)
ax.set_ylabel("Needle Retrieval Pass Rate (%)", fontsize=10)
ax.set_xlim(-3, 78)
ax.set_ylim(-5, 105)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(alpha=0.2, linestyle="--", zorder=0)

# Arrow: INT4-baseline → INT4-RoleAlign (design improvement)
comp_baseline = (1 - 252/896) * 100
ax.annotate("",
            xy=(comp_baseline - 0.5, 98), xytext=(comp_baseline + 0.5, 3),
            arrowprops=dict(arrowstyle="->, head_width=0.25",
                           color="#3498db", lw=1.5, ls="--",
                           connectionstyle="arc3,rad=0.2"))
ax.text(comp_baseline + 5, 50, "RoleAlign\nrescues\nretrieval",
        fontsize=7, color="#3498db", ha="left", va="center", style="italic")

fig.tight_layout()

out_path = "thesis/figures/pareto_quality_efficiency.pdf"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
print(f"Saved: {out_path}")
plt.close(fig)
