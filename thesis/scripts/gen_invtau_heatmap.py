#!/usr/bin/env python3
"""Generate inv_tau heatmap figure for thesis ch3 (unified P1-B1 style)."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path

# --- Thesis font: Times New Roman + 宋体 ---
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

# Load calibration JSON
calib_path = Path(__file__).resolve().parents[1] / ".." / "artifacts" / "kv_calib_kl_selected_v3_quick.json"
with open(calib_path) as f:
    calib = json.load(f)

num_layers = calib["num_layers"]
num_heads = calib["num_heads"]

# Extract inv_tau matrix — top-level list of 28 per-head arrays
inv_tau_raw = calib["inv_tau"]
inv_tau = np.ones((num_layers, num_heads))
for l in range(num_layers):
    inv_tau[l] = inv_tau_raw[l]

# Create figure（单图，去掉复杂的 zoom inset；数字用黑字 + 透明背景）
fig, ax = plt.subplots(figsize=(6.5, 7.5))

# Diverging colormap centered at 1.0
# 大部分头的 τ⁻¹=1.0（居中色），少数非 1.0 偏向两端
vmin, vmax = 0.4, 1.1
norm = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)

im = ax.imshow(inv_tau, aspect='auto', cmap='RdYlBu_r', norm=norm,
               origin='lower', interpolation='nearest')

# Annotate non-1.0 cells（黑字、无背景框）
for i in range(num_layers):
    for j in range(num_heads):
        val = inv_tau[i, j]
        if val != 1.0:
            ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                    fontsize=8, fontweight='bold', color='black')

# Labels（全英文避免 mathtext stix 与 CJK 渲染冲突；中文说明放 LaTeX caption）
ax.set_xlabel('Attention Head Index', fontsize=10, fontweight='bold')
ax.set_ylabel('Transformer Layer Index', fontsize=10, fontweight='bold')
ax.set_xticks(range(num_heads))
ax.set_xticklabels(range(num_heads))
ax.set_yticks(range(0, num_layers, 2))
ax.set_yticklabels(range(0, num_layers, 2))

# Colorbar（τ⁻¹ 符号，无中文）
cbar = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.03)
cbar.set_label(r'$\tau^{-1}$', fontsize=11, fontweight='bold')
cbar.ax.tick_params(labelsize=8)
cbar.set_ticks([0.4, 0.6, 0.8, 1.0, 1.1])
cbar.set_ticklabels(['0.4', '0.6', '0.8', '1.0', '1.1'])

plt.tight_layout()
# Output PDF (thesis references .pdf not .png) — P1-B1
out_path = Path(__file__).resolve().parents[0] / ".." / "figures" / "ch3_invtau_heatmap.pdf"
out_path.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"Saved to {out_path}")
