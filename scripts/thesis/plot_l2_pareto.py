"""
scripts/thesis/plot_l2_pareto.py

生成图 ⑦：Quality-cost Pareto Front（story §16.6 ⭐⭐）。

数据源: results/l2_pareto/pareto_plot_v4.csv
    Schema: model_key, policy_id, avg_bits, quality_core, peak_mem_mb, ...

图结构 (3 subplot：7b / 8b / mistral7b):
- x: peak_mem_mb (作为 kv_cache_mem_mb proxy, log-scale)
- y: quality_core (task-core mean quality)
- marker 形状区分 policy family:
    o = uniform_int4 / △ = bakv_k* (fixed) / ▽ = heuristic_k* / ★ = bakv_auto_cov*
- 每 subplot 画 Pareto front 连线
- Callout:
    * 7b uniform_int4 "quality cliff"
    * mistral bakv_auto "Pareto-dominant"

Contract:
- Input: results/l2_pareto/pareto_plot_v4.csv
- Output: thesis/figures/fig7_pareto.pdf

Run:
    python scripts/thesis/plot_l2_pareto.py
"""

from __future__ import annotations

import sys
import pathlib
import numpy as np

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _common import (  # noqa: E402
    RESULTS_DIR,
    load_csv,
    set_mpl_style,
    save_figure_pdf,
    print_contract,
    POLICY_COLORS,
    POLICY_MARKERS,
)

FIG_ID = "fig7_pareto"
PARETO_CSV = RESULTS_DIR / "l2_pareto" / "pareto_plot_v4.csv"

SUBPLOT_MODELS = ["7b", "8b", "mistral7b"]
MODEL_TITLES = {
    "7b":         r"Qwen2.5-7B ($H_{kv}{=}4$)",
    "8b":         r"Llama-3.1-8B ($H_{kv}{=}8$)",
    "mistral7b":  r"Mistral-7B-v0.3 ($H_{kv}{=}8$)",
}


def classify_policy(pid: str) -> str:
    """Map policy_id string → family key aligned with POLICY_COLORS/MARKERS."""
    if pid.startswith("uniform_int4") or pid == "uniform_int4_k4v4":
        return "uniform_int4"
    if pid.startswith("bakv_auto_cov"):
        return "bakv_auto_cov80"  # 同族
    if pid.startswith("bakv_k") or pid.startswith("bakv_mean"):
        return "bakv_fixed"
    if pid.startswith("heuristic_"):
        return "heuristic"
    if pid == "kivi_style":
        return "kivi_style"
    return "uniform_int4"  # fallback


def pareto_front(xs, ys):
    """Compute Pareto front: minimize x (mem), maximize y (quality)."""
    pts = sorted(zip(xs, ys), key=lambda p: (p[0], -p[1]))
    front = []
    best_y = -np.inf
    for x, y in pts:
        if y > best_y:
            front.append((x, y))
            best_y = y
    return list(zip(*front)) if front else ([], [])


def main():
    print_contract(
        "plot_l2_pareto.py",
        inputs=[str(PARETO_CSV.relative_to(RESULTS_DIR.parent))],
        outputs=[f"thesis/figures/{FIG_ID}.pdf"],
    )

    set_mpl_style()
    import matplotlib.pyplot as plt

    df = load_csv(PARETO_CSV)
    print(f"\n[data] loaded {len(df)} rows from {PARETO_CSV.name}")
    print(f"[data] models: {df['model_key'].unique().tolist()}")

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=False)

    for ax, mkey in zip(axes, SUBPLOT_MODELS):
        sub = df[df["model_key"] == mkey].dropna(subset=["quality_core", "peak_mem_mb"])
        print(f"  [{mkey}] {len(sub)} valid points")

        # group by policy family and plot
        sub = sub.copy()
        sub["family"] = sub["policy_id"].apply(classify_policy)

        for fam in ["uniform_int4", "bakv_fixed", "heuristic", "bakv_auto_cov80"]:
            sub_fam = sub[sub["family"] == fam]
            if sub_fam.empty:
                continue
            ax.scatter(
                sub_fam["peak_mem_mb"],
                sub_fam["quality_core"],
                c=POLICY_COLORS.get(fam, "#888"),
                marker=POLICY_MARKERS.get(fam, "o"),
                s=70,
                edgecolor="#333",
                linewidth=0.6,
                label=fam.replace("_", "-"),
                alpha=0.85,
                zorder=3,
            )

        # Pareto front line (across all points)
        xs = sub["peak_mem_mb"].values
        ys = sub["quality_core"].values
        if len(xs) >= 2:
            fx, fy = pareto_front(xs, ys)
            ax.plot(fx, fy, linestyle="--", color="#555", linewidth=1.2, alpha=0.7, zorder=2, label="Pareto front")

        # Callouts
        if mkey == "7b":
            uniform_pts = sub[sub["family"] == "uniform_int4"]
            if not uniform_pts.empty:
                worst = uniform_pts.loc[uniform_pts["quality_core"].idxmin()]
                ax.annotate(
                    "quality cliff",
                    xy=(worst["peak_mem_mb"], worst["quality_core"]),
                    xytext=(worst["peak_mem_mb"] * 1.15, worst["quality_core"] + 0.5),
                    arrowprops=dict(arrowstyle="->", color="#D55E00", lw=1.2),
                    fontsize=9, color="#D55E00",
                )
        elif mkey == "mistral7b":
            auto_pts = sub[sub["family"] == "bakv_auto_cov80"]
            if not auto_pts.empty:
                best = auto_pts.loc[auto_pts["quality_core"].idxmax()]
                ax.annotate(
                    "Pareto-dominant",
                    xy=(best["peak_mem_mb"], best["quality_core"]),
                    xytext=(best["peak_mem_mb"] * 0.75, best["quality_core"] + 0.3),
                    arrowprops=dict(arrowstyle="->", color="#009E73", lw=1.2),
                    fontsize=9, color="#009E73",
                )

        ax.set_xscale("log")
        ax.set_xlabel(r"KV cache peak memory (MB, log)")
        if mkey == SUBPLOT_MODELS[0]:
            ax.set_ylabel(r"Quality (task-core mean)")
        ax.set_title(MODEL_TITLES[mkey], fontsize=10)
        ax.grid(True, alpha=0.3)

        if mkey == SUBPLOT_MODELS[-1]:
            ax.legend(loc="lower right", fontsize=8, frameon=True, framealpha=0.9)

    fig.suptitle(
        r"Quality--memory Pareto front across 3 models (L2 sweep)",
        fontsize=11, y=1.02,
    )
    plt.tight_layout()
    pdf_path = save_figure_pdf(fig, FIG_ID)
    print(f"\n[write] {pdf_path}")


if __name__ == "__main__":
    main()
