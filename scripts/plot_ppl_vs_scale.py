#!/usr/bin/env python3
"""
P0 Figure: Model Scale vs PPL Degradation
Shows the structural relationship between GQA head count and INT4 PPL degradation.

Key message: PPL degradation decreases with H_kv, but Needle stays at 100%.
This is the "decoupling" insight — retrieval is robust while language modeling degrades.

Output: thesis/figures/ppl_degradation_vs_scale.pdf
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path
from matplotlib import font_manager

# --- Thesis font: 宋体 + Times New Roman ---
for p in [Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
          Path("/System/Library/Fonts/STSong.ttf")]:
    if p.exists():
        font_manager.fontManager.addfont(str(p))
        break
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Songti SC", "STSong", "SimSun"],
    "mathtext.fontset": "stix",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8,
    "axes.unicode_minus": False,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

# ──────────────────────────────────────────────────
# Data from tab:rolealign-results (verified)
# ──────────────────────────────────────────────────
models = ["Qwen2.5\n1.5B", "Qwen2.5\n7B", "LLaMA-3.1\n8B"]
h_kv =   [2, 4, 8]

# PPL degradation vs FP16 (%)
ppl_rolealign = [13.7, 6.1, 2.4]
ppl_kivi      = [12.0, 5.5, 2.4]

# Needle pass rate (%)
needle_rolealign = [100, 100, 100]

# ──────────────────────────────────────────────────
# Figure
# ──────────────────────────────────────────────────
fig, ax = plt.subplots(1, 1, figsize=(5.5, 3.8))

x = np.arange(len(models))
width = 0.32

# Bars — unified palette: INT4-RoleAlign = teal (int4_ours_asym), KIVI = soft purple
bars_ra = ax.bar(x - width/2, ppl_rolealign, width,
                 label="INT4-RoleAlign", color="#16a085", edgecolor="white", linewidth=0.8, zorder=3)
bars_kv = ax.bar(x + width/2, ppl_kivi, width,
                 label="KIVI-style INT4", color="#9b59b6", edgecolor="white", linewidth=0.8, alpha=0.85, zorder=3)

# Value labels on bars
for bar, val in zip(bars_ra, ppl_rolealign):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f"{val}%", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#2c3e50")
for bar, val in zip(bars_kv, ppl_kivi):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f"{val}%", ha="center", va="bottom", fontsize=8, color="#5b2c6f")

# H_kv annotation
for i, h in enumerate(h_kv):
    ax.text(i, -1.8, f"$H_{{kv}}$={h}", ha="center", va="top",
            fontsize=8, color="#7f8c8d", style="italic")

# Needle annotation: green checkmarks
for i in range(len(models)):
    ax.text(i, max(ppl_rolealign[i], ppl_kivi[i]) + 1.8,
            "Needle 100%", ha="center", va="bottom",
            fontsize=8, color="#27ae60", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="#eafaf1", edgecolor="#27ae60", linewidth=0.6))

# Styling
ax.set_xticks(x)
ax.set_xticklabels(models, fontsize=9)
ax.set_ylabel("PPL Degradation vs FP16 (%)", fontsize=10)
ax.set_ylim(0, 18)
ax.yaxis.set_major_locator(mticker.MultipleLocator(2))
ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", alpha=0.3, linestyle="--", zorder=0)

# Trend arrow annotation
ax.annotate("", xy=(2.4, 3.5), xytext=(0.0, 14.5),
            arrowprops=dict(arrowstyle="->, head_width=0.3", color="#95a5a6", lw=1.3, ls="--"))
ax.text(1.5, 10.5, "$H_{kv}$ ↑  degradation ↓", fontsize=8, color="#7f8c8d",
        rotation=-32, ha="center")

fig.tight_layout()

out_path = "thesis/figures/ppl_degradation_vs_scale.pdf"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
print(f"Saved: {out_path}")
plt.close(fig)
