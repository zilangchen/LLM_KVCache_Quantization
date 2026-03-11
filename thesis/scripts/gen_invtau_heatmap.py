#!/usr/bin/env python3
"""Generate inv_tau heatmap figure for thesis ch3."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path

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

# Create figure
fig, ax = plt.subplots(figsize=(6, 8))

# Diverging colormap centered at 1.0
vmin, vmax = 0.4, 1.1
norm = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)

im = ax.imshow(inv_tau, aspect='auto', cmap='RdBu_r', norm=norm,
               origin='lower', interpolation='nearest')

# Annotate non-1.0 cells
for i in range(num_layers):
    for j in range(num_heads):
        val = inv_tau[i, j]
        if val != 1.0:
            ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                    fontsize=9, fontweight='bold', color='white',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.6))

# Labels
ax.set_xlabel('Attention Head Index', fontsize=12)
ax.set_ylabel('Transformer Layer Index', fontsize=12)
ax.set_xticks(range(num_heads))
ax.set_xticklabels(range(num_heads))
ax.set_yticks(range(0, num_layers, 2))
ax.set_yticklabels(range(0, num_layers, 2))

# Colorbar
cbar = fig.colorbar(im, ax=ax, shrink=0.6, pad=0.02)
cbar.set_label(r'$\tau^{-1}$', fontsize=13)

# Zoom inset for layers 0-1 (where non-1.0 values exist)
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
axins = inset_axes(ax, width="45%", height="12%", loc='upper right',
                   borderpad=1.5)
inv_tau_zoom = inv_tau[:3, :]  # layers 0-2
norm_zoom = TwoSlopeNorm(vmin=0.4, vcenter=1.0, vmax=1.1)
axins.imshow(inv_tau_zoom, aspect='auto', cmap='RdBu_r', norm=norm_zoom,
             origin='lower', interpolation='nearest')
for i in range(3):
    for j in range(num_heads):
        val = inv_tau_zoom[i, j]
        if val != 1.0:
            axins.text(j, i, f'{val:.2f}', ha='center', va='center',
                       fontsize=7, fontweight='bold', color='white',
                       bbox=dict(boxstyle='round,pad=0.1', facecolor='black', alpha=0.6))
axins.set_xticks(range(num_heads))
axins.set_xticklabels(range(num_heads), fontsize=6)
axins.set_yticks(range(3))
axins.set_yticklabels(range(3), fontsize=6)
axins.set_title('Layers 0-2 (zoom)', fontsize=8)
mark_inset(ax, axins, loc1=1, loc2=3, fc="none", ec="red", lw=1.2)

plt.tight_layout()
out_path = Path(__file__).resolve().parents[0] / ".." / "figures" / "ch3_invtau_heatmap.png"
out_path.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"Saved to {out_path}")
