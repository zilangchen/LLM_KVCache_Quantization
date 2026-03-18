#!/usr/bin/env python3
"""
B9: Plot attention KL / reconstruction error heatmaps.

Reads JSON output from collect_attention_kl.py and generates publication-ready
heatmap figures showing per-layer per-head K/V reconstruction error.

Usage:
    python scripts/plot_attention_kl_heatmap.py \
        --input results/attention_kl/attention_kl_int4_mixed_kv_*.json \
        --out_dir results/plots/attention_kl/
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))


def plot_heatmap(data, out_dir: Path):
    """Generate K/V reconstruction error heatmaps."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    layers = data["layers"]
    num_layers = len(layers)
    num_heads = len(layers[0]["k_mse_per_head"])

    k_matrix = np.array([l["k_mse_per_head"] for l in layers])  # [L, H]
    v_matrix = np.array([l["v_mse_per_head"] for l in layers])  # [L, H]

    kv_mode = data["kv_mode"]
    model_tag = data["model_id"].split("/")[-1]

    out_dir.mkdir(parents=True, exist_ok=True)

    # K heatmap
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, max(6, num_layers * 0.25)))
    fig.suptitle(f"KV Cache Reconstruction Error — {model_tag} ({kv_mode})", fontsize=13)

    im1 = ax1.imshow(k_matrix, aspect="auto", cmap="YlOrRd", interpolation="nearest")
    ax1.set_title("K (Key) MSE per Head", fontsize=11)
    ax1.set_xlabel("Head Index")
    ax1.set_ylabel("Layer Index")
    plt.colorbar(im1, ax=ax1, shrink=0.8)

    im2 = ax2.imshow(v_matrix, aspect="auto", cmap="YlOrRd", interpolation="nearest")
    ax2.set_title("V (Value) MSE per Head", fontsize=11)
    ax2.set_xlabel("Head Index")
    ax2.set_ylabel("Layer Index")
    plt.colorbar(im2, ax=ax2, shrink=0.8)

    plt.tight_layout()
    out_path = out_dir / f"kv_error_heatmap_{kv_mode}_{model_tag}.pdf"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved heatmap: {out_path}")

    # K vs V summary bar chart (layer-averaged)
    fig2, ax = plt.subplots(figsize=(10, 5))
    k_means = [l["k_mse_mean"] for l in layers]
    v_means = [l["v_mse_mean"] for l in layers]
    x = np.arange(num_layers)
    width = 0.35
    ax.bar(x - width / 2, k_means, width, label="K MSE", color="#e74c3c", alpha=0.8)
    ax.bar(x + width / 2, v_means, width, label="V MSE", color="#3498db", alpha=0.8)
    ax.set_xlabel("Layer Index")
    ax.set_ylabel("Mean Squared Error")
    ax.set_title(f"K vs V Reconstruction Error by Layer — {model_tag} ({kv_mode})")
    ax.legend()
    ax.set_xticks(x[::max(1, num_layers // 10)])

    out_path2 = out_dir / f"kv_error_bars_{kv_mode}_{model_tag}.pdf"
    fig2.savefig(out_path2, dpi=150, bbox_inches="tight")
    plt.close(fig2)
    print(f"Saved bar chart: {out_path2}")


def main():
    parser = argparse.ArgumentParser(description="B9: Plot Attention KL Heatmaps")
    parser.add_argument("--input", type=str, nargs="+", required=True,
                        help="Path(s) to attention_kl JSON files")
    parser.add_argument("--out_dir", type=str, default="results/plots/attention_kl")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)

    for input_path in args.input:
        print(f"Processing {input_path}...")
        with open(input_path) as f:
            data = json.load(f)
        plot_heatmap(data, out_dir)


if __name__ == "__main__":
    main()
