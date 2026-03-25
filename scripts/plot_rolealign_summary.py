#!/usr/bin/env python3
"""Generate RoleAlign summary figure: PPL degradation + LongBench across 3 models.

Reads from results/emnlp_rolealign_v1/tables/ and outputs to thesis/figures/.
Uses the same color palette and styling as generate_thesis_figures.py.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

DPI = 300

# Match thesis color palette
C_KIVI = "#E91E63"       # pink — KIVI-style
C_ROLE = "#009688"       # teal — INT4-RoleAlign
C_FP16 = "#2C3E50"       # dark slate — FP16 baseline (reference line)

# ──────────────────────────────────────────────────────────
# DATA  (from emnlp_rolealign_v1 aggregation, chunk_size=128)
# ──────────────────────────────────────────────────────────

models = ["Qwen2.5-1.5B", "Qwen2.5-7B", "LLaMA-3.1-8B"]

# PPL absolute values (chunk_size=128, standard eval)
ppl_fp16  = [9.3088,  7.1407, 6.7330]
ppl_kivi  = [10.4294, 7.5311, 6.8954]
ppl_role  = [9.4197,  7.2141, 6.7511]

# PPL degradation (%) relative to FP16
ppl_deg_kivi = [(k - f) / f * 100 for k, f in zip(ppl_kivi, ppl_fp16)]
ppl_deg_role = [(r - f) / f * 100 for r, f in zip(ppl_role, ppl_fp16)]

# LongBench F1 Macro (more interpretable than longbench_score)
lb_kivi = [5.6649, 4.3037, 7.8518]
lb_role = [5.7354, 4.4795, 7.8518]

# Needle pass rate at 32K (all 100% — annotate only)
needle_kivi = [100.0, 100.0, 100.0]
needle_role = [100.0, 100.0, 100.0]

# ──────────────────────────────────────────────────────────
# FIGURE
# ──────────────────────────────────────────────────────────

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
})

x = np.arange(len(models))
w = 0.32

# ── Panel (a): PPL Degradation (%) ──
bars_kivi = ax1.bar(x - w/2, ppl_deg_kivi, w, color=C_KIVI, label="KIVI-style INT4", edgecolor="white", linewidth=0.5)
bars_role = ax1.bar(x + w/2, ppl_deg_role, w, color=C_ROLE, label="INT4-RoleAlign", edgecolor="white", linewidth=0.5)

# Value labels
for bar in bars_kivi:
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., h + 0.2, f"{h:.1f}%",
             ha="center", va="bottom", fontsize=8.5, color=C_KIVI, fontweight="bold")
for bar in bars_role:
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., h + 0.2, f"{h:.1f}%",
             ha="center", va="bottom", fontsize=8.5, color=C_ROLE, fontweight="bold")

ax1.set_ylabel("PPL Degradation vs FP16 (%)")
ax1.set_title("(a) Perplexity Degradation")
ax1.set_xticks(x)
ax1.set_xticklabels(models, fontsize=9)
ax1.set_ylim(0, max(ppl_deg_kivi) * 1.35)
ax1.legend(fontsize=8.5, loc="upper right")
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))

# Reduction annotations
for i in range(len(models)):
    reduction = ppl_deg_kivi[i] - ppl_deg_role[i]
    mid_y = (ppl_deg_kivi[i] + ppl_deg_role[i]) / 2
    ax1.annotate(f"−{reduction:.1f}pp",
                 xy=(x[i] + w/2, ppl_deg_role[i]),
                 xytext=(x[i] + w*1.5, mid_y + 1.0),
                 fontsize=7.5, color="#555555",
                 arrowprops=dict(arrowstyle="->", color="#999999", lw=0.8),
                 ha="left")

# ── Panel (b): LongBench F1 Macro ──
bars_kivi2 = ax2.bar(x - w/2, lb_kivi, w, color=C_KIVI, label="KIVI-style INT4", edgecolor="white", linewidth=0.5)
bars_role2 = ax2.bar(x + w/2, lb_role, w, color=C_ROLE, label="INT4-RoleAlign", edgecolor="white", linewidth=0.5)

for bar in bars_kivi2:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., h + 0.08, f"{h:.2f}",
             ha="center", va="bottom", fontsize=8.5, color=C_KIVI, fontweight="bold")
for bar in bars_role2:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., h + 0.08, f"{h:.2f}",
             ha="center", va="bottom", fontsize=8.5, color=C_ROLE, fontweight="bold")

ax2.set_ylabel("LongBench F1 Macro")
ax2.set_title("(b) LongBench Quality")
ax2.set_xticks(x)
ax2.set_xticklabels(models, fontsize=9)
ax2.set_ylim(0, max(max(lb_kivi), max(lb_role)) * 1.3)
ax2.legend(fontsize=8.5, loc="upper right")
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

# Needle annotation (all 100%)
ax2.text(0.98, 0.02,
         "Needle Pass Rate: 100% for both\nmethods across all 3 models",
         transform=ax2.transAxes, fontsize=7.5, color="#666666",
         ha="right", va="bottom",
         bbox=dict(boxstyle="round,pad=0.3", facecolor="#F5F5F5", edgecolor="#CCCCCC", alpha=0.9))

plt.tight_layout(pad=1.5)
plt.savefig("thesis/figures/rolealign_summary.pdf", dpi=DPI, bbox_inches="tight")
print("Saved: thesis/figures/rolealign_summary.pdf")
