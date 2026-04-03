#!/usr/bin/env python3
"""
Visualize calibration artifacts for thesis figures.

Reads a KL calibration JSON file (e.g. artifacts/kv_calib_kl.json)
and produces:
  1. inv_tau heatmap  (layer x head)
  2. inv_tau histogram (distribution across all heads)
  3. k_scale / v_scale heatmaps

Usage:
    python scripts/plot_calib_analysis.py \
        --calib artifacts/kv_calib_kl_selected_v3_quick.json \
        --out_dir results/calib_plots
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib is required. Install: pip install matplotlib")
    sys.exit(1)


def load_calib(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def plot_inv_tau_heatmap(
    inv_tau: list, out_path: str, title: str = "Per-Head Temperature"
) -> None:
    """Plot inv_tau as a layer x head heatmap."""
    num_layers = len(inv_tau)
    if num_layers == 0:
        print(f"  SKIP heatmap: inv_tau is empty")
        return
    num_heads = len(inv_tau[0])
    # CAL-048: ragged inv_tau (different head counts per layer) → pad to max
    max_h = max(len(row) for row in inv_tau)
    if any(len(row) != max_h for row in inv_tau):
        inv_tau = [row + [float("nan")] * (max_h - len(row)) for row in inv_tau]
        num_heads = max_h
    arr = np.array(inv_tau, dtype=np.float64)  # [L, H]

    fig, ax = plt.subplots(figsize=(max(6, num_heads * 0.5), max(4, num_layers * 0.25)))
    im = ax.imshow(arr, aspect="auto", cmap="RdYlBu_r", interpolation="nearest")
    ax.set_xlabel("KV Head Index")
    ax.set_ylabel("Layer Index")
    ax.set_title(f"{title} ($\\tau^{{-1}}$)")
    # CAL-050: Guard xticks with a threshold matching yticks to prevent
    # unreadable overlapping labels on models with many KV heads (32+).
    if num_heads <= 32:
        ax.set_xticks(range(num_heads))
    if num_layers <= 30:
        ax.set_yticks(range(num_layers))
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("$\\tau^{-1}$")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path}")


def plot_inv_tau_histogram(
    inv_tau: list, out_path: str
) -> None:
    """Plot distribution of inv_tau values."""
    arr = np.array(inv_tau, dtype=object)
    arr = np.concatenate([np.asarray(row, dtype=np.float64) for row in arr]) if len(arr) > 0 else np.array([], dtype=np.float64)
    arr = arr[np.isfinite(arr)]  # CAL-048: drop NaN from ragged padding
    if len(arr) == 0:  # CAL-049: empty inv_tau guard
        print(f"  SKIP histogram: no valid inv_tau values")
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(arr, bins=20, edgecolor="black", alpha=0.75, color="#4C72B0")
    ax.axvline(1.0, color="red", linestyle="--", linewidth=1, label="$\\tau^{-1}=1$ (no scaling)")
    ax.set_xlabel("$\\tau^{-1}$ Value")
    ax.set_ylabel("Count (Layer x Head)")
    ax.set_title("Distribution of Per-Head Temperature ($\\tau^{-1}$)")
    ax.legend()
    stats_text = (
        f"mean={arr.mean():.3f}\n"
        f"std={arr.std():.3f}\n"
        f"min={arr.min():.3f}\n"
        f"max={arr.max():.3f}"
    )
    ax.text(
        0.97, 0.97, stats_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path}")


def plot_scale_heatmap(
    scale_data: list,
    out_path: str,
    title: str = "Scale",
    group_dim: bool = True,
) -> None:
    """Plot per-layer scale as heatmap.

    scale_data: list of layers, each layer is [H, G] or [H] scale values.
    """
    processed = []
    for layer_scale in scale_data:
        layer_arr = np.array(layer_scale)
        if layer_arr.ndim == 2:
            processed.append(layer_arr.mean(axis=-1))
        elif layer_arr.ndim == 1:
            processed.append(layer_arr)
        else:
            processed.append(np.array([layer_arr.mean()]))

    if not processed:
        print(f"  SKIP scale heatmap: no scale data")
        return
    # CAL-051: Ragged head counts across layers (e.g. MOE/Hybrid architectures)
    # produce an object-dtype array that imshow cannot render. Pad to max width.
    max_h = max(len(row) for row in processed)
    if any(len(row) != max_h for row in processed):
        processed = [
            np.pad(row, (0, max_h - len(row)), constant_values=np.nan)
            for row in processed
        ]
    arr = np.array(processed, dtype=np.float64)  # [L, H]
    fig, ax = plt.subplots(figsize=(max(6, arr.shape[1] * 0.5), max(4, arr.shape[0] * 0.25)))
    im = ax.imshow(arr, aspect="auto", cmap="viridis", interpolation="nearest")
    ax.set_xlabel("KV Head Index")
    ax.set_ylabel("Layer Index")
    ax.set_title(f"{title} (mean over groups)")
    if arr.shape[0] <= 30:
        ax.set_yticks(range(arr.shape[0]))
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Scale value")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Visualize KL calibration artifacts"
    )
    parser.add_argument(
        "--calib",
        type=str,
        default="artifacts/kv_calib_kl_selected_v3_quick.json",
        help="Path to calibration JSON file",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="results/calib_plots",
        help="Output directory for plots",
    )
    args = parser.parse_args()

    if not os.path.exists(args.calib):
        print(f"ERROR: Calibration file not found: {args.calib}")
        sys.exit(1)

    os.makedirs(args.out_dir, exist_ok=True)
    data = load_calib(args.calib)

    print(f"Model: {data.get('model_id', 'unknown')}")
    print(f"Layers: {data.get('num_layers')}, "
          f"KV Heads: {data.get('num_kv_heads')}, "
          f"Head Dim: {data.get('head_dim')}")
    print(f"Group Size: K={data.get('group_size_k')}, V={data.get('group_size_v')}")
    print(f"Clip Percentile: K={data.get('clip_percentile_k')}, "
          f"V={data.get('clip_percentile_v')}")

    if "inv_tau" in data and data["inv_tau"]:
        print("\nGenerating inv_tau plots...")
        plot_inv_tau_heatmap(
            data["inv_tau"],
            os.path.join(args.out_dir, "inv_tau_heatmap.png"),
        )
        plot_inv_tau_histogram(
            data["inv_tau"],
            os.path.join(args.out_dir, "inv_tau_histogram.png"),
        )
    else:
        print("No inv_tau data found in calibration file.")

    if "k_scale" in data and data["k_scale"]:
        print("\nGenerating K scale heatmap...")
        plot_scale_heatmap(
            data["k_scale"],
            os.path.join(args.out_dir, "k_scale_heatmap.png"),
            title="K Scale",
        )

    if "v_scale" in data and data["v_scale"]:
        print("\nGenerating V scale heatmap...")
        plot_scale_heatmap(
            data["v_scale"],
            os.path.join(args.out_dir, "v_scale_heatmap.png"),
            title="V Scale",
        )

    print(f"\nDone. All plots saved to: {args.out_dir}")


if __name__ == "__main__":
    main()
