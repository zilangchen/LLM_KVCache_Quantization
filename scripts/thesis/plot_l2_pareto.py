"""
scripts/thesis/plot_l2_pareto.py

生成图 ⑦：Quality-budget Pareto View（story §16.6 ⭐⭐）。

数据源: results/l2_pareto/pareto_plot_v4.csv
    Schema: model_key, policy_id, avg_bits, quality_core, peak_mem_mb, ...

图结构 (3 subplot：7b / 8b / mistral7b):
- x: avg_bits（平均 KV bit budget，更贴近 chapter §4.3 的 budget-band 口径）
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

import csv
import sys
import pathlib
import numpy as np

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _common import (  # noqa: E402
    RESULTS_DIR,
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
    "8b":         r"LLaMA-3.1-8B ($H_{kv}{=}8$)",
    "mistral7b":  r"Mistral-7B ($H_{kv}{=}8$)",
}
FAMILY_LABELS = {
    "uniform_int4": "统一 INT4",
    "bakv_fixed": r"BA-$k_*$",
    "heuristic": r"Heuristic-$k_*$",
    "bakv_auto_cov80": "BA-AutoK",
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
    """Compute Pareto front: minimize x (budget), maximize y (quality)."""
    pts = sorted(zip(xs, ys), key=lambda p: (p[0], -p[1]))
    front = []
    best_y = -np.inf
    for x, y in pts:
        if y > best_y:
            front.append((x, y))
            best_y = y
    return list(zip(*front)) if front else ([], [])


def load_pareto_rows(path: pathlib.Path):
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            avg_bits = row.get("avg_bits", "")
            quality_core = row.get("quality_core", "")
            try:
                row["avg_bits"] = float(avg_bits) if avg_bits not in ("", None) else None
            except ValueError:
                row["avg_bits"] = None
            try:
                row["quality_core"] = float(quality_core) if quality_core not in ("", None) else None
            except ValueError:
                row["quality_core"] = None
            rows.append(row)
    return rows


def main():
    print_contract(
        "plot_l2_pareto.py",
        inputs=[str(PARETO_CSV.relative_to(RESULTS_DIR.parent))],
        outputs=[f"thesis/figures/{FIG_ID}.pdf"],
    )

    set_mpl_style()
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.font_manager import FontProperties

    cjk_font = None
    for family in ["Arial Unicode MS", "Hiragino Sans GB", "Heiti TC", "PingFang HK"]:
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
        raise RuntimeError("No CJK-capable font found for fig7_pareto.")

    rows = load_pareto_rows(PARETO_CSV)
    print(f"\n[data] loaded {len(rows)} rows from {PARETO_CSV.name}")
    print(f"[data] models: {sorted({row['model_key'] for row in rows})}")

    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.6), sharey=False)
    legend_handles = []
    legend_labels = []

    for ax, mkey in zip(axes, SUBPLOT_MODELS):
        sub = [
            row for row in rows
            if row["model_key"] == mkey
            and row["quality_core"] is not None
            and row["avg_bits"] is not None
        ]
        print(f"  [{mkey}] {len(sub)} valid points")

        # group by policy family and plot
        for row in sub:
            row["family"] = classify_policy(row["policy_id"])

        for fam in ["uniform_int4", "bakv_fixed", "heuristic", "bakv_auto_cov80"]:
            sub_fam = [row for row in sub if row["family"] == fam]
            if not sub_fam:
                continue
            sc = ax.scatter(
                [row["avg_bits"] for row in sub_fam],
                [row["quality_core"] for row in sub_fam],
                c=POLICY_COLORS.get(fam, "#888"),
                marker=POLICY_MARKERS.get(fam, "o"),
                s=70,
                edgecolor="#333",
                linewidth=0.6,
                label=fam.replace("_", "-"),
                alpha=0.85,
                zorder=3,
            )
            label = FAMILY_LABELS.get(fam, fam)
            if label not in legend_labels:
                legend_handles.append(sc)
                legend_labels.append(label)

        # Pareto front line (across all points)
        xs = np.array([row["avg_bits"] for row in sub], dtype=float)
        ys = np.array([row["quality_core"] for row in sub], dtype=float)
        if len(xs) >= 2:
            fx, fy = pareto_front(xs, ys)
            line, = ax.plot(
                fx, fy,
                linestyle="--", color="#555", linewidth=1.2, alpha=0.8, zorder=2,
            )
            if "Pareto 前沿" not in legend_labels:
                legend_handles.append(line)
                legend_labels.append("Pareto 前沿")

        if len(sub) > 0:
            xmin = min(row["avg_bits"] for row in sub) - 0.2
            xmax = max(row["avg_bits"] for row in sub) + 0.25
            ymin = min(row["quality_core"] for row in sub) - 0.25
            ymax = max(row["quality_core"] for row in sub) + 0.25
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)

        # Callouts（使用 axes coords 避免 log 刻度下 xytext 乘法失真）
        if mkey == "7b":
            uniform_pts = [row for row in sub if row["family"] == "uniform_int4"]
            if uniform_pts:
                worst = min(uniform_pts, key=lambda row: row["quality_core"])
                ax.annotate(
                    "明显质量断崖",
                    xy=(worst["avg_bits"], worst["quality_core"]),
                    xytext=(0.24, 0.2), textcoords="axes fraction",
                    arrowprops=dict(arrowstyle="->", color="#D55E00", lw=1.1),
                    fontsize=9, color="#D55E00", fontproperties=cjk_font,
                )
        elif mkey == "mistral7b":
            auto_pts = [row for row in sub if row["family"] == "bakv_auto_cov80"]
            if auto_pts:
                best = max(auto_pts, key=lambda row: row["quality_core"])
                ax.annotate(
                    "AutoK 最显著\n正向区间",
                    xy=(best["avg_bits"], best["quality_core"]),
                    xytext=(0.18, 0.8), textcoords="axes fraction",
                    arrowprops=dict(arrowstyle="->", color="#009E73", lw=1.1),
                    fontsize=9, color="#009E73", fontproperties=cjk_font,
                )

        ax.set_xlabel(r"平均 KV bit budget ($\bar{b}$)", fontproperties=cjk_font)
        if mkey == SUBPLOT_MODELS[0]:
            ax.set_ylabel("任务核心平均质量", fontproperties=cjk_font)
        ax.set_title(MODEL_TITLES[mkey], fontsize=10)
        ax.grid(True, alpha=0.3)

    fig.suptitle(
        r"质量-预算 Pareto 视图",
        fontsize=11, y=1.02, fontproperties=cjk_font,
    )
    fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        ncol=5,
        bbox_to_anchor=(0.5, -0.03),
        frameon=True,
        framealpha=0.92,
        fontsize=8,
        prop=cjk_font,
    )
    plt.tight_layout(rect=(0, 0.08, 1, 1))
    pdf_path = save_figure_pdf(fig, FIG_ID)
    print(f"\n[write] {pdf_path}")


if __name__ == "__main__":
    main()
