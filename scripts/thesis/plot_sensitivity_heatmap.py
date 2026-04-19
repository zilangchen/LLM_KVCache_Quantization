"""
scripts/thesis/plot_sensitivity_heatmap.py

生成图 ④：Behavior Sensitivity Profile Heatmap（story §16.4 ⭐ 签名视觉）。

调整后的数据契约（从 story §16.4 理想化的 calibration JSON KL 偏移度
→ allocator auto-policy 的 per-layer decision 作为 behavior sensitivity 的 downstream proxy）：
- 对每个模型，读取 `artifacts/clean_rerun_20260419T09/allocator/sweep_<m>/bakv_auto_cov80_max.json`
  （14B 例外用 cov90，对齐 T3 的 auto policy 选择）
- per_layer_bits[l] = (K_bits, V_bits)，K_bits ∈ {4, 8}，代表 allocator 对该层的保护决策
- K_bits=8 = "behavior 原则标记该层为高敏感，保留 INT8 精度"
- K_bits=4 = "默认 INT4 即可"

图结构：
- 4 model 横排 subplot，每个 subplot 竖向一列 heatmap（y 轴为 layer index，按 num_layers 对齐）
- 色彩：K_bits 的二值（4 = light, 8 = dark）
- 顶部 annotation: top-k protected layer index
- X 轴共享 "Model"，Y 轴标为 "Layer depth (normalized to [0,1])"
- 对应 story §16.4 signature visual

Contract:
- Input: 4 JSON files in artifacts/clean_rerun_20260419T09/allocator/sweep_<m>/
- Output: thesis/figures/fig4_sensitivity_heatmap.pdf

Run:
    python scripts/thesis/plot_sensitivity_heatmap.py
"""

from __future__ import annotations

import sys
import json
import pathlib
import numpy as np

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _common import (  # noqa: E402
    CLEAN_RERUN_DIR,
    THESIS_FIGURES_DIR,
    ARTIFACTS_DIR,
    set_mpl_style,
    save_figure_pdf,
    print_contract,
)

FIG_ID = "fig4_sensitivity_heatmap"

MODEL_TO_SWEEP = {
    "3b":        ("sweep_3b",        "bakv_auto_cov80_max", "Qwen2.5-3B\n(cov80)"),
    "8b":        ("sweep_8b",        "bakv_auto_cov80_max", "Llama-3.1-8B\n(cov80)"),
    "14b":       ("sweep_14b",       "bakv_auto_cov90_max", "Qwen2.5-14B\n(cov90)"),
    "mistral7b": ("sweep_mistral7b", "bakv_auto_cov80_max", "Mistral-7B\n(cov80)"),
}
MODEL_ORDER = ["3b", "8b", "14b", "mistral7b"]


def load_per_layer_bits(model_key: str):
    sweep_dir, policy, _ = MODEL_TO_SWEEP[model_key]
    path = ARTIFACTS_DIR / "clean_rerun_20260419T09" / "allocator" / sweep_dir / f"{policy}.json"
    with open(path) as f:
        d = json.load(f)
    per_layer = d["per_layer_bits"]  # list of [K_bits, V_bits]
    num_layers = d["num_layers"]
    avg_bits = d.get("avg_bits")
    return per_layer, num_layers, avg_bits


def main():
    print_contract(
        "plot_sensitivity_heatmap.py",
        inputs=[
            "artifacts/clean_rerun_20260419T09/allocator/sweep_{3b,8b,14b,mistral7b}/bakv_auto_cov*_max.json"
        ],
        outputs=[f"thesis/figures/{FIG_ID}.pdf"],
    )

    set_mpl_style()
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm

    # 4 subplot 横排
    fig, axes = plt.subplots(1, 4, figsize=(12, 5), sharey=False)
    cmap = ListedColormap(["#E5F5F9", "#2CA25F"])  # light-gray (4bit) vs dark-green (8bit)
    norm = BoundaryNorm([3, 6, 9], ncolors=2)  # 4→index 0, 8→index 1

    top3_info = {}
    for ax, mkey in zip(axes, MODEL_ORDER):
        per_layer, num_layers, avg_bits = load_per_layer_bits(mkey)
        _, _, title = MODEL_TO_SWEEP[mkey]

        k_bits_arr = np.array([bits[0] for bits in per_layer], dtype=int)
        v_bits_arr = np.array([bits[1] for bits in per_layer], dtype=int)

        # 两列矩阵：K 列 | V 列，高 = num_layers
        mat = np.stack([k_bits_arr, v_bits_arr], axis=1)  # shape (num_layers, 2)

        im = ax.imshow(
            mat,
            aspect="auto",
            cmap=cmap,
            norm=norm,
            origin="lower",
            extent=(-0.5, 1.5, 0, num_layers),
            interpolation="nearest",
        )
        ax.set_title(title, fontsize=10)
        ax.set_xticks([0, 1])
        ax.set_xticklabels([r"$K$", r"$V$"], fontsize=10)
        ax.set_xlim(-0.5, 1.5)
        ax.set_ylabel("Layer index" if mkey == MODEL_ORDER[0] else "")
        ax.set_ylim(0, num_layers)
        ax.grid(False)

        # 标注 avg_bits
        ax.text(
            0.5, num_layers + 0.5,
            f"avg={avg_bits:.2f}bit" if avg_bits else "",
            ha="center", va="bottom", fontsize=8, color="#555",
        )

        # top-3 protected layer (K_bits=8) indices
        protected = np.where(k_bits_arr == 8)[0]
        top3_info[mkey] = (protected[:3].tolist(), protected.tolist(), num_layers)

    # Legend (shared)
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#E5F5F9", edgecolor="#666", label="INT4 (default)"),
        Patch(facecolor="#2CA25F", edgecolor="#666", label="INT8 (protected)"),
    ]
    fig.legend(
        handles=legend_elements,
        loc="lower center",
        ncol=2,
        bbox_to_anchor=(0.5, -0.02),
        frameon=False,
    )

    fig.suptitle(
        r"Behavior-guided AutoK per-layer bit allocation (K/V columns)",
        fontsize=11, y=1.02,
    )
    plt.tight_layout()

    pdf_path = save_figure_pdf(fig, FIG_ID)
    print(f"\n[write] {pdf_path}")

    # 打印摘要便于写 caption
    print("\n--- per-model protected layer summary ---")
    for mkey in MODEL_ORDER:
        top3, all_prot, num_layers = top3_info[mkey]
        print(f"  {mkey} (L={num_layers}): top-3 protected layers = {top3}, total protected = {len(all_prot)}")


if __name__ == "__main__":
    main()
