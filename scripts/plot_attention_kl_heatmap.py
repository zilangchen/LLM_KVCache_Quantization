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
from pathlib import Path

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


DPI = 300
CMAP = "magma"


def setup_style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [
            "Songti SC", "PingFang HK", "Heiti TC", "STHeiti",
            "DejaVu Sans", "sans-serif",
        ],
        "font.size": 10,
        "axes.titlesize": 10.5,
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "legend.framealpha": 0.92,
        "legend.edgecolor": "#CCCCCC",
        "axes.grid": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.unicode_minus": False,
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.04,
    })


def load_json(path: Path):
    with open(path) as f:
        return json.load(f)


def matrices_from_data(data):
    layers = data["layers"]
    k_matrix = np.array([layer["k_mse_per_head"] for layer in layers], dtype=float)
    v_matrix = np.array([layer["v_mse_per_head"] for layer in layers], dtype=float)
    k_layer_mean = np.array([layer["k_mse_mean"] for layer in layers], dtype=float)
    v_layer_mean = np.array([layer["v_mse_mean"] for layer in layers], dtype=float)
    return k_matrix, v_matrix, k_layer_mean, v_layer_mean


def model_tag(data):
    return data["model_id"].split("/")[-1]


def short_model_name(data):
    tag = model_tag(data)
    replacements = {
        "Qwen2.5-1.5B-Instruct": "Qwen2.5-1.5B",
        "Qwen2.5-7B-Instruct": "Qwen2.5-7B",
        "Llama-3.1-8B-Instruct": "LLaMA-3.1-8B",
        "Mistral-7B-Instruct-v0.3": "Mistral-7B-v0.3",
    }
    return replacements.get(tag, tag)


def focus_layer(k_layer_mean, v_layer_mean):
    return int(np.argmax((k_layer_mean + v_layer_mean) / 2.0))


def save_fig(fig, out_path: Path):
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    print(f"Saved figure: {out_path}")


def plot_single_heatmap(data, out_dir: Path):
    """Generate polished single-model K/V heatmap and layer summary."""
    out_dir.mkdir(parents=True, exist_ok=True)

    k_matrix, v_matrix, k_layer_mean, v_layer_mean = matrices_from_data(data)
    kv_mode = data["kv_mode"]
    tag = model_tag(data)
    short_name = short_model_name(data)
    layer_idx = np.arange(k_matrix.shape[0])
    focus = focus_layer(k_layer_mean, v_layer_mean)

    vmax = float(max(np.nanmax(k_matrix), np.nanmax(v_matrix)))
    if vmax <= 0:
        vmax = 1.0

    fig = plt.figure(figsize=(13.2, max(5.8, k_matrix.shape[0] * 0.22)))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1.15, 0.85], wspace=0.22)
    ax_k = fig.add_subplot(gs[0, 0])
    ax_v = fig.add_subplot(gs[0, 1])
    ax_summary = fig.add_subplot(gs[0, 2])

    im_k = ax_k.imshow(k_matrix, aspect="auto", cmap=CMAP, interpolation="nearest", vmin=0.0, vmax=vmax)
    im_v = ax_v.imshow(v_matrix, aspect="auto", cmap=CMAP, interpolation="nearest", vmin=0.0, vmax=vmax)

    for ax, title in ((ax_k, "Key error per head"), (ax_v, "Value error per head")):
        ax.set_xlabel("Head Index")
        ax.set_ylabel("Layer Index")
        ax.set_title(title, loc="left", fontweight="bold")
        ax.axhspan(focus - 0.5, focus + 0.5, facecolor="none", edgecolor="white", lw=1.2, linestyle="--")

    ax_summary.plot(k_layer_mean, layer_idx, color="#E74C3C", label="Key mean", linewidth=2.0)
    ax_summary.plot(v_layer_mean, layer_idx, color="#3498DB", label="Value mean", linewidth=2.0)
    ax_summary.scatter(
        [k_layer_mean[focus], v_layer_mean[focus]],
        [focus, focus],
        color=["#E74C3C", "#3498DB"],
        s=28,
        zorder=4,
        edgecolors="white",
        linewidths=0.7,
    )
    ax_summary.axhline(focus, color="#666666", linestyle="--", linewidth=0.8, alpha=0.8)
    ax_summary.text(
        0.02,
        0.03,
        f"Peak-error layer: {focus}",
        transform=ax_summary.transAxes,
        fontsize=7.6,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#CCCCCC", lw=0.7),
    )
    ax_summary.set_xlabel("Layer-wise mean MSE")
    ax_summary.set_ylabel("Layer Index")
    ax_summary.set_title("Layer-wise summary", loc="left", fontweight="bold")
    ax_summary.grid(axis="x", alpha=0.25)
    ax_summary.legend(loc="upper right", frameon=True)

    cbar = fig.colorbar(im_v, ax=[ax_k, ax_v], fraction=0.03, pad=0.02)
    cbar.set_label("Reconstruction MSE", fontsize=9)
    fig.suptitle(
        f"KV reconstruction error under {kv_mode} — {short_name} (seq_len={data['seq_len']}, samples={data['num_samples']})",
        fontsize=12.5,
        y=0.98,
    )

    heatmap_out = out_dir / f"kv_error_heatmap_{kv_mode}_{tag}.pdf"
    save_fig(fig, heatmap_out)

    # Keep the historical filename for the auxiliary per-layer comparison figure.
    fig2, ax = plt.subplots(figsize=(10.5, 4.2))
    ax.plot(layer_idx, k_layer_mean, color="#E74C3C", linewidth=2.0, marker="o", markersize=3.5, label="Key mean")
    ax.plot(layer_idx, v_layer_mean, color="#3498DB", linewidth=2.0, marker="s", markersize=3.5, label="Value mean")
    ax.axvline(focus, color="#666666", linestyle="--", linewidth=0.8, alpha=0.8)
    ax.annotate(
        f"peak layer {focus}",
        xy=(focus, max(k_layer_mean[focus], v_layer_mean[focus])),
        xytext=(focus + 0.5, max(k_layer_mean.max(), v_layer_mean.max()) * 0.92),
        arrowprops=dict(arrowstyle="->", lw=0.8, color="#666666"),
        fontsize=7.8,
        color="#444444",
    )
    ax.set_xlabel("Layer Index")
    ax.set_ylabel("Mean MSE")
    ax.set_title(f"Layer-wise K/V error summary — {short_name}", loc="left", fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="upper right", frameon=True)
    bars_out = out_dir / f"kv_error_bars_{kv_mode}_{tag}.pdf"
    save_fig(fig2, bars_out)


def _find_pair_candidates(datasets):
    qwen = None
    llama = None
    for data in datasets:
        tag = model_tag(data)
        if "Qwen2.5-1.5B" in tag and qwen is None:
            qwen = data
        if "Llama-3.1-8B" in tag and llama is None:
            llama = data
    return qwen, llama


def plot_paired_heatmap(data_a, data_b, out_dir: Path):
    """Generate a paired Qwen/LLaMA comparison with unified color scale."""
    out_dir.mkdir(parents=True, exist_ok=True)

    matrices = []
    for data in (data_a, data_b):
        matrices.append((data, *matrices_from_data(data)))

    vmax = max(
        float(np.nanmax(k_matrix))
        for _, k_matrix, _, _, _ in matrices
    )
    vmax = max(
        vmax,
        max(float(np.nanmax(v_matrix)) for _, _, v_matrix, _, _ in matrices),
    )
    if vmax <= 0:
        vmax = 1.0

    fig = plt.figure(figsize=(13.5, 8.0))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.08, 1.08, 0.82], hspace=0.24, wspace=0.22)
    image_axes = []

    for row, (data, k_matrix, v_matrix, k_layer_mean, v_layer_mean) in enumerate(matrices):
        row_axes = [
            fig.add_subplot(gs[row, 0]),
            fig.add_subplot(gs[row, 1]),
            fig.add_subplot(gs[row, 2]),
        ]
        ax_k, ax_v, ax_summary = row_axes
        image_axes.extend([ax_k, ax_v])
        focus = focus_layer(k_layer_mean, v_layer_mean)
        short_name = short_model_name(data)

        im_k = ax_k.imshow(k_matrix, aspect="auto", cmap=CMAP, interpolation="nearest", vmin=0.0, vmax=vmax)
        im_v = ax_v.imshow(v_matrix, aspect="auto", cmap=CMAP, interpolation="nearest", vmin=0.0, vmax=vmax)

        for ax, title in ((ax_k, f"{short_name} — Key"), (ax_v, f"{short_name} — Value")):
            ax.set_title(title, loc="left", fontweight="bold")
            ax.set_xlabel("Head Index")
            ax.set_ylabel("Layer Index")
            ax.axhspan(focus - 0.5, focus + 0.5, facecolor="none", edgecolor="white", lw=1.2, linestyle="--")

        layers = np.arange(k_matrix.shape[0])
        ax_summary.plot(k_layer_mean, layers, color="#E74C3C", linewidth=2.0, label="Key mean")
        ax_summary.plot(v_layer_mean, layers, color="#3498DB", linewidth=2.0, label="Value mean")
        ax_summary.axhline(focus, color="#666666", linestyle="--", linewidth=0.8, alpha=0.8)
        ax_summary.text(
            0.02,
            0.03,
            f"Peak layer: {focus}",
            transform=ax_summary.transAxes,
            fontsize=7.4,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#CCCCCC", lw=0.7),
        )
        ax_summary.set_title(f"{short_name} — Layer summary", loc="left", fontweight="bold")
        ax_summary.set_xlabel("Mean MSE")
        ax_summary.set_ylabel("Layer Index")
        ax_summary.grid(axis="x", alpha=0.25)
        if row == 0:
            ax_summary.legend(loc="upper right", frameon=True)

    cbar = fig.colorbar(im_v, ax=image_axes, fraction=0.025, pad=0.02)
    cbar.set_label("Reconstruction MSE", fontsize=9)
    fig.suptitle(
        f"Paired K/V reconstruction error comparison — {data_a['kv_mode']} (shared scale)",
        fontsize=12.5,
        y=0.99,
    )

    out_path = out_dir / f"kv_error_heatmap_pair_{data_a['kv_mode']}.pdf"
    save_fig(fig, out_path)


def main():
    parser = argparse.ArgumentParser(description="B9: Plot Attention KL Heatmaps")
    parser.add_argument("--input", type=str, nargs="+", required=True, help="Path(s) to attention_kl JSON files")
    parser.add_argument("--out_dir", type=str, default="results/plots/attention_kl")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    setup_style()

    datasets = []
    for input_path in args.input:
        path = Path(input_path)
        print(f"Processing {path}...")
        datasets.append(load_json(path))

    for data in datasets:
        plot_single_heatmap(data, out_dir)

    qwen, llama = _find_pair_candidates(datasets)
    if qwen is not None and llama is not None and qwen["kv_mode"] == llama["kv_mode"]:
        plot_paired_heatmap(qwen, llama, out_dir)
    else:
        print("Skipping paired heatmap: Qwen/LLaMA pair with matching kv_mode not found.")


if __name__ == "__main__":
    main()
