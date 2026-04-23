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
    "3b":        ("sweep_3b",        "bakv_auto_cov80_max", "Qwen2.5-3B", "AutoK cov80"),
    "8b":        ("sweep_8b",        "bakv_auto_cov80_max", "LLaMA-3.1-8B", "AutoK cov80"),
    "14b":       ("sweep_14b",       "bakv_auto_cov90_max", "Qwen2.5-14B", "AutoK cov90"),
    "mistral7b": ("sweep_mistral7b", "bakv_auto_cov80_max", "Mistral-7B", "AutoK cov80"),
}
MODEL_ORDER = ["3b", "8b", "14b", "mistral7b"]


def load_per_layer_bits(model_key: str):
    sweep_dir, policy, _, _ = MODEL_TO_SWEEP[model_key]
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
    from matplotlib import font_manager
    from matplotlib.font_manager import FontProperties

    cjk_font = None
    for family in ["Arial Unicode MS", "Hiragino Sans GB", "STHeiti", "Heiti TC", "PingFang HK"]:
        try:
            font_path = font_manager.findfont(
                FontProperties(family=family),
                fallback_to_default=False,
            )
            cjk_font = FontProperties(fname=font_path)
            break
        except Exception:
            continue
    if cjk_font is None:
        raise RuntimeError("No CJK-capable font found for fig4_sensitivity_heatmap.")

    # 4 subplot 横排：把 protection map 收成结构解释图，而不是调试可视化
    fig, axes = plt.subplots(1, 4, figsize=(11.6, 4.8), sharey=False)
    cmap = ListedColormap(["#F2F3EE", "#2F6B4F"])  # default INT4 vs protected INT8
    norm = BoundaryNorm([3, 6, 9], ncolors=2)  # 4→index 0, 8→index 1

    top3_info = {}
    for ax, mkey in zip(axes, MODEL_ORDER):
        per_layer, num_layers, avg_bits = load_per_layer_bits(mkey)
        _, _, title, subtitle = MODEL_TO_SWEEP[mkey]

        k_bits_arr = np.array([bits[0] for bits in per_layer], dtype=int)
        v_bits_arr = np.array([bits[1] for bits in per_layer], dtype=int)

        # 两列矩阵：K 列 | V 列，高 = num_layers
        mat = np.stack([k_bits_arr, v_bits_arr], axis=1)  # shape (num_layers, 2)

        im = ax.imshow(
            mat,
            aspect="auto",
            cmap=cmap,
            norm=norm,
            origin="upper",
            interpolation="nearest",
        )
        ax.set_title(title, fontsize=10, pad=18, fontweight="semibold")
        ax.set_xticks([0, 1])
        ax.set_xticklabels([r"$K$", r"$V$"], fontsize=10)
        ax.set_xlim(-0.5, 1.5)
        yticks = [0, max(0, num_layers // 2 - 1), num_layers - 1]
        ylabels = ["1", str(max(1, num_layers // 2)), str(num_layers)]
        ax.set_yticks(yticks)
        ax.set_yticklabels(ylabels)
        if mkey == MODEL_ORDER[0]:
            ax.set_ylabel("层", fontproperties=cjk_font)
        else:
            ax.set_ylabel("")
        ax.tick_params(axis="y", length=2.5)
        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_linewidth(0.8)
            spine.set_color("#666666")

        cov_label = subtitle.replace("AutoK ", "")
        protected = np.where(k_bits_arr == 8)[0]
        top3 = protected[:3].tolist()

        # subtitle：保留 budget 信息，但压成更克制的结构提示
        ax.text(
            0.5, 1.01,
            (
                f"{cov_label} · avg {avg_bits:.2f}b"
                + (f" · top {', '.join(str(i + 1) for i in top3)}" if top3 else "")
            ) if avg_bits else cov_label,
            transform=ax.transAxes,
            ha="center", va="bottom", fontsize=8, color="#555",
        )
        top3_info[mkey] = (top3, protected.tolist(), num_layers)

    # Legend (shared)
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#F2F3EE", edgecolor="#666", label="INT4 默认"),
        Patch(facecolor="#2F6B4F", edgecolor="#666", label="INT8 保护"),
    ]
    fig.legend(
        handles=legend_elements,
        loc="upper center",
        ncol=2,
        bbox_to_anchor=(0.5, 0.98),
        frameon=False,
        prop=cjk_font,
    )

    fig.suptitle(
        r"Behavior-guided AutoK 逐层保护图",
        fontsize=11, y=1.06, fontweight="semibold",
        fontproperties=cjk_font,
    )
    fig.text(
        0.02, 0.5, "浅层", rotation=90,
        va="center", ha="center", fontsize=8.5, color="#666666",
        fontproperties=cjk_font,
    )
    fig.text(
        0.98, 0.5, "深层", rotation=270,
        va="center", ha="center", fontsize=8.5, color="#666666",
        fontproperties=cjk_font,
    )
    plt.tight_layout(rect=(0.03, 0.02, 0.97, 0.90))

    pdf_path = save_figure_pdf(fig, FIG_ID)
    print(f"\n[write] {pdf_path}")

    # 打印摘要便于写 caption
    print("\n--- per-model protected layer summary ---")
    for mkey in MODEL_ORDER:
        top3, all_prot, num_layers = top3_info[mkey]
        print(f"  {mkey} (L={num_layers}): top-3 protected layers = {top3}, total protected = {len(all_prot)}")


if __name__ == "__main__":
    main()
