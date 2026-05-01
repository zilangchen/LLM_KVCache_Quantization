"""
Generate Chapter 4 Figure 4-1 as a multi-probe K/V role-sensitivity figure.

The figure uses a bit-layout view to bridge Chapter 3's motivation figure and
Chapter 4's full K/V diagnosis. Values are assembled from existing paper tables
and archived K4V8 Needle profiles; no value is inferred.

Contract:
- Inputs:
  results/archive/round4_misc/paper_tables/table1_main_quality_*.csv
  results/archive/round4_misc/paper_tables/table3_mixedkv_*.csv
  results/final/final_data/kv_ablation/tables/kv_ablation_{ruler,longbench}.csv
  results/archive/round2_postfix/emnlp_postfix_v2/runs/k_int4_v_int8_long_*/profile_needle_*.csv
- Outputs:
  thesis/figures/ch4/fig_ch4_01_kv_ruler32.pdf
  thesis/figures/ch4/fig_ch4_01_kv_role_sensitivity_data.csv

Run:
    python scripts/thesis/plot_ch4_kv_role_sensitivity.py
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _common import (  # noqa: E402
    RESULTS_DIR,
    THESIS_FIGURES_DIR,
    print_contract,
    set_mpl_style,
)

FIG_ID = "fig_ch4_01_kv_ruler32"
DATA_ID = "fig_ch4_01_kv_role_sensitivity_data.csv"
OUTPUT_DIR = THESIS_FIGURES_DIR / "ch4"
OUTPUT_PDF = OUTPUT_DIR / f"{FIG_ID}.pdf"
OUTPUT_DATA = OUTPUT_DIR / DATA_ID

PAPER_TABLES_DIR = RESULTS_DIR / "archive" / "round4_misc" / "paper_tables"
KV_ABLATION_TABLES_DIR = RESULTS_DIR / "final" / "final_data" / "kv_ablation" / "tables"
K4V8_NEEDLE_RUNS_DIR = RESULTS_DIR / "archive" / "round2_postfix" / "emnlp_postfix_v2" / "runs"

MODEL_ROWS = [
    {
        "key": "1p5b",
        "label": "Qwen2.5\n1.5B",
        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "table1": "table1_main_quality_qwen25_1p5b.csv",
        "table3": "table3_mixedkv_qwen25_1p5b.csv",
    },
    {
        "key": "7b",
        "label": "Qwen2.5\n7B",
        "model_id": "Qwen/Qwen2.5-7B-Instruct",
        "table1": "table1_main_quality_qwen25_7b.csv",
        "table3": "table3_mixedkv_qwen25_7b.csv",
    },
    {
        "key": "8b",
        "label": "LLaMA-3.1\n8B",
        "model_id": "meta-llama/Llama-3.1-8B-Instruct",
        "table1": "table1_main_quality_llama31_8b.csv",
        "table3": "table3_mixedkv_llama31_8b.csv",
    },
]

CONFIG_ROWS = [
    {"key": "FP16", "label": "FP16", "source": "main_quality", "kv_mode": "fp16"},
    {"key": "K8V8", "label": "K8V8", "source": "main_quality", "kv_mode": "int8_ours"},
    {"key": "K8V4", "label": "K8V4", "source": "mixedkv", "kv_mode": "int4_mixed_kv"},
    {"key": "K4V8", "label": "K4V8", "source": "kv_ablation", "method": "K4V8"},
    {"key": "K4V4", "label": "K4V4", "source": "main_quality", "kv_mode": "int4_ours"},
]

CONFIG_STYLE = {
    "FP16": {"color": "#111827", "fill": "#111827"},
    "K8V8": {"color": "#787878", "fill": "#EFEFEF"},
    "K8V4": {"color": "#426CB0", "fill": "#DEE7F7"},
    "K4V8": {"color": "#BA564F", "fill": "#F6DFDB"},
    "K4V4": {"color": "#B0871E", "fill": "#F8EEC7"},
}

OMITTED_POINTS: set[tuple[str, str, str]] = set()

METRIC_ROWS = [
    {"key": "needle", "title": "(a) Needle", "unit": "%", "ylim": (0, 105)},
    {"key": "ruler", "title": "(b) RULER", "unit": "%", "ylim": (0, 40)},
    {"key": "longbench", "title": "(c) LongBench", "unit": "x100", "ylim": (0, 21)},
]

METRIC_COLOR = {
    "needle": "#426CB0",
    "ruler": "#3F8F68",
    "longbench": "#B0871E",
}


def find_cjk_font() -> FontProperties:
    candidates = [
        "Arial Unicode MS",
        "Hiragino Sans GB",
        "STHeiti",
        "Heiti TC",
        "PingFang HK",
        "Songti SC",
    ]
    for name in candidates:
        try:
            path = font_manager.findfont(name, fallback_to_default=False)
        except ValueError:
            continue
        if path and pathlib.Path(path).exists():
            return FontProperties(fname=path)
    raise RuntimeError("No CJK-capable font found for fig_ch4_01_kv_ruler32.")


def require_csv(path: pathlib.Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing source data: {path}")
    return pd.read_csv(path)


def single_row(df: pd.DataFrame, mask: pd.Series, context: str) -> pd.Series:
    sub = df[mask]
    if len(sub) != 1:
        raise RuntimeError(f"Expected exactly one row for {context}; got {len(sub)}")
    return sub.iloc[0]


def metric_from_paper_row(row: pd.Series, metric: str) -> tuple[float, float | None]:
    if metric == "needle":
        return float(row["needle_pct"]), None
    if metric == "ruler":
        return float(row["ruler_mean"]), float(row["ruler_std"]) if not pd.isna(row["ruler_std"]) else None
    if metric == "longbench":
        mean = float(row["longbench_mean"]) * 100.0
        std = float(row["longbench_std"]) * 100.0 if not pd.isna(row["longbench_std"]) else None
        return mean, std
    raise ValueError(f"Unknown metric: {metric}")


def load_k4v8_needle() -> pd.DataFrame:
    paths = sorted(K4V8_NEEDLE_RUNS_DIR.glob("k_int4_v_int8_long_*/profile_needle_*.csv"))
    if not paths:
        raise FileNotFoundError(f"No K4V8 Needle profiles found under {K4V8_NEEDLE_RUNS_DIR}")

    rows = []
    for path in paths:
        df = require_csv(path)
        required = {"model_id", "seq_len", "needle_pass_rate"}
        if not required.issubset(df.columns):
            raise RuntimeError(f"Unexpected K4V8 Needle profile schema: {path}")
        first = df.iloc[0]
        rows.append(
            {
                "model_id": first["model_id"],
                "seq_len": int(first["seq_len"]),
                "value": float(first["needle_pass_rate"]),
                "source_file": str(path),
            }
        )
    raw = pd.DataFrame(rows)
    raw = raw[raw["seq_len"] == 32704].copy()
    if raw.empty:
        raise RuntimeError("K4V8 Needle profiles contain no 32704-context rows.")

    grouped = (
        raw.groupby("model_id")
        .agg(value=("value", "mean"), std=("value", "std"), count=("value", "count"))
        .reset_index()
    )
    return grouped


def build_source_matrix() -> pd.DataFrame:
    ruler_ablation = require_csv(KV_ABLATION_TABLES_DIR / "kv_ablation_ruler.csv")
    longbench_ablation = require_csv(KV_ABLATION_TABLES_DIR / "kv_ablation_longbench.csv")
    k4v8_needle = load_k4v8_needle()

    rows: list[dict[str, object]] = []
    for model in MODEL_ROWS:
        table1_path = PAPER_TABLES_DIR / model["table1"]
        table3_path = PAPER_TABLES_DIR / model["table3"]
        table1 = require_csv(table1_path)
        table3 = require_csv(table3_path)

        for config in CONFIG_ROWS:
            for metric in METRIC_ROWS:
                metric_key = metric["key"]
                if (metric_key, model["key"], config["key"]) in OMITTED_POINTS:
                    continue

                std: float | None
                source_file: pathlib.Path | str
                source_note: str

                if config["source"] == "main_quality":
                    row = single_row(
                        table1,
                        table1["kv_mode"] == config["kv_mode"],
                        f"{model['key']} {config['key']} {metric_key}",
                    )
                    value, std = metric_from_paper_row(row, metric_key)
                    source_file = table1_path
                    source_note = f"{config['key']} maps to kv_mode={config['kv_mode']}"
                elif config["source"] == "mixedkv":
                    row = single_row(
                        table3,
                        table3["kv_mode"] == config["kv_mode"],
                        f"{model['key']} {config['key']} {metric_key}",
                    )
                    value, std = metric_from_paper_row(row, metric_key)
                    source_file = table3_path
                    source_note = "K8V4 maps to MixedKV (K@INT8 + V@INT4)"
                elif config["source"] == "kv_ablation":
                    if metric_key == "needle":
                        row = single_row(
                            k4v8_needle,
                            k4v8_needle["model_id"] == model["model_id"],
                            f"{model['key']} K4V8 needle",
                        )
                        value = float(row["value"])
                        std = float(row["std"]) if not pd.isna(row["std"]) else None
                        source_file = K4V8_NEEDLE_RUNS_DIR
                        source_note = (
                            f"K4V8 Needle archived 32704-context mean across "
                            f"{int(row['count'])} profiles"
                        )
                    elif metric_key == "ruler":
                        row = single_row(
                            ruler_ablation,
                            (ruler_ablation["model_key"] == model["key"])
                            & (ruler_ablation["method"] == config["method"]),
                            f"{model['key']} K4V8 ruler",
                        )
                        value = float(row["mean"])
                        std = float(row["std"]) if not pd.isna(row["std"]) else None
                        source_file = KV_ABLATION_TABLES_DIR / "kv_ablation_ruler.csv"
                        source_note = "K4V8 maps to K@INT4 + V@INT8 ablation"
                    elif metric_key == "longbench":
                        row = single_row(
                            longbench_ablation,
                            (longbench_ablation["model_key"] == model["key"])
                            & (longbench_ablation["method"] == config["method"]),
                            f"{model['key']} K4V8 longbench",
                        )
                        value = float(row["mean"]) * 100.0
                        std = float(row["std"]) * 100.0 if not pd.isna(row["std"]) else None
                        source_file = KV_ABLATION_TABLES_DIR / "kv_ablation_longbench.csv"
                        source_note = "K4V8 maps to K@INT4 + V@INT8 ablation"
                    else:
                        raise ValueError(f"Unknown metric: {metric_key}")
                else:
                    raise ValueError(f"Unknown source: {config['source']}")

                rows.append(
                    {
                        "metric": metric_key,
                        "model_key": model["key"],
                        "model": model["label"].replace("\n", " "),
                        "config": config["key"],
                        "value": value,
                        "std": std,
                        "source_file": str(source_file),
                        "source_note": source_note,
                    }
                )

    out = pd.DataFrame(rows)
    expected = len(MODEL_ROWS) * len(CONFIG_ROWS) * len(METRIC_ROWS) - len(OMITTED_POINTS)
    if len(out) != expected:
        raise RuntimeError(f"Expected {expected} matrix rows, got {len(out)}")
    if out["value"].isna().any():
        raise RuntimeError("Figure matrix contains NaN values.")
    return out


def format_value(metric: str, value: float) -> str:
    if metric == "needle":
        return f"{value:.0f}" if abs(value - round(value)) < 0.05 else f"{value:.1f}"
    return f"{value:.1f}"


def marker_positions(metric_key: str, values: np.ndarray, ylim: tuple[float, float]) -> np.ndarray:
    threshold = {"needle": 1.1, "ruler": 0.35, "longbench": 0.20}[metric_key]
    step = {"needle": 1.0, "ruler": 0.28, "longbench": 0.14}[metric_key]
    y_min, y_max = ylim
    display = values.copy()

    for row_idx in range(values.shape[0]):
        finite_indices = [idx for idx in range(values.shape[1]) if np.isfinite(values[row_idx, idx])]
        if not finite_indices:
            continue
        order = sorted(finite_indices, key=lambda idx: (values[row_idx, idx], idx))
        clusters: list[list[int]] = []
        cluster = [order[0]]
        for idx in order[1:]:
            prev = cluster[-1]
            if abs(values[row_idx, idx] - values[row_idx, prev]) <= threshold:
                cluster.append(idx)
            else:
                clusters.append(cluster)
                cluster = [idx]
        clusters.append(cluster)

        for cluster in clusters:
            if len(cluster) <= 1:
                continue
            cluster = sorted(cluster)
            shifts = np.array([(k - (len(cluster) - 1) / 2.0) * step for k in range(len(cluster))])
            shifted = values[row_idx, cluster] + shifts
            lower = y_min + step * 0.25
            upper = y_max - step * 0.25
            if shifted.min() < lower:
                shifts += lower - shifted.min()
                shifted = values[row_idx, cluster] + shifts
            if shifted.max() > upper:
                shifts -= shifted.max() - upper
            for config_idx, shift in zip(cluster, shifts):
                display[row_idx, config_idx] = values[row_idx, config_idx] + shift
    return display


def draw_metric_panel(ax, matrix_df: pd.DataFrame, metric: dict[str, object], cjk_font: FontProperties):
    metric_key = str(metric["key"])
    values = np.full((len(MODEL_ROWS), len(CONFIG_ROWS)), np.nan, dtype=float)
    for i, model in enumerate(MODEL_ROWS):
        for j, config in enumerate(CONFIG_ROWS):
            mask = (
                (matrix_df["metric"] == metric_key)
                & (matrix_df["model_key"] == model["key"])
                & (matrix_df["config"] == config["key"])
            )
            sub = matrix_df[mask]
            if sub.empty and (metric_key, model["key"], config["key"]) in OMITTED_POINTS:
                continue
            if len(sub) != 1:
                raise RuntimeError(
                    f"Expected exactly one row for matrix {metric_key} "
                    f"{model['key']} {config['key']}; got {len(sub)}"
                )
            values[i, j] = float(sub.iloc[0]["value"])

    x = np.arange(len(MODEL_ROWS), dtype=float)
    marker_y = marker_positions(metric_key, values, metric["ylim"])
    ax.set_title(
        str(metric["title"]),
        loc="left",
        fontsize=10.2,
        fontweight="bold",
        fontproperties=cjk_font,
    )
    for j, config in enumerate(CONFIG_ROWS):
        style = CONFIG_STYLE[str(config["key"])]
        series = values[:, j]
        ax.plot(
            x,
            series,
            color=style["color"],
            linewidth=1.8,
            label=str(config["label"]),
            zorder=2,
        )
        finite = np.isfinite(series)
        ax.scatter(
            x[finite],
            marker_y[finite, j],
            s=34,
            color=style["fill"],
            edgecolor=style["color"],
            linewidth=0.95,
            zorder=4,
        )

    ax.set_xticks(x)
    ax.set_xticklabels([m["label"] for m in MODEL_ROWS], fontsize=8.0, fontweight="bold")
    ax.set_xlim(-0.45, len(MODEL_ROWS) - 0.55)
    ax.set_ylim(*metric["ylim"])
    ylabel = "通过率（%）" if metric_key in {"needle", "ruler"} else "综合分（×100）"
    ax.set_ylabel(ylabel, fontsize=8.8, fontproperties=cjk_font)
    ax.tick_params(axis="both", labelsize=8.0)
    ax.grid(axis="y", alpha=0.25, linewidth=0.7, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.text(
        0.0,
        -0.22,
        "重叠标记轻微避让，折线为原始读数",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.2,
        color="#64748B",
        fontproperties=cjk_font,
    )
    if metric_key == "longbench":
        ax.text(
            0.0,
            -0.34,
            "注：LLaMA-3.1-8B 的 K4V4 点为 synthetic task-core 格式敏感读数，仅作审计",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=7.2,
            color="#64748B",
            fontproperties=cjk_font,
        )


def draw_drop_panel(ax, matrix_df: pd.DataFrame, cjk_font: FontProperties):
    x = np.arange(len(MODEL_ROWS), dtype=float)
    width = 0.22
    metric_order = ["needle", "ruler", "longbench"]
    metric_label = {
        "needle": "Needle",
        "ruler": "RULER",
        "longbench": "LongBench",
    }

    for idx, metric_key in enumerate(metric_order):
        drops = []
        for model in MODEL_ROWS:
            k8v4 = float(
                single_row(
                    matrix_df,
                    (matrix_df["metric"] == metric_key)
                    & (matrix_df["model_key"] == model["key"])
                    & (matrix_df["config"] == "K8V4"),
                    f"drop {metric_key} {model['key']} K8V4",
                )["value"]
            )
            k4v8 = float(
                single_row(
                    matrix_df,
                    (matrix_df["metric"] == metric_key)
                    & (matrix_df["model_key"] == model["key"])
                    & (matrix_df["config"] == "K4V8"),
                    f"drop {metric_key} {model['key']} K4V8",
                )["value"]
            )
            drops.append(k8v4 - k4v8)
        offsets = x + (idx - 1) * width
        ax.bar(
            offsets,
            drops,
            width=width,
            color=METRIC_COLOR[metric_key],
            edgecolor="white",
            linewidth=0.8,
            label=metric_label[metric_key],
            zorder=3,
        )
        for xp, val in zip(offsets, drops):
            va = "bottom" if val >= 0 else "top"
            dy = 1.2 if val >= 0 else -1.2
            ax.text(
                xp,
                val + dy,
                f"{val:.1f}",
                ha="center",
                va=va,
                fontsize=7.0,
                color="#111827",
            )

    ax.axhline(0, color="#475569", linewidth=0.8)
    ax.set_title(
        "(d) K 侧降幅摘要",
        loc="left",
        fontsize=10.2,
        fontweight="bold",
        fontproperties=cjk_font,
    )
    ax.set_xticks(x)
    ax.set_xticklabels([m["label"] for m in MODEL_ROWS], fontsize=8.0)
    ax.set_ylabel("K8V4 - K4V8", fontsize=8.8)
    ax.set_ylim(-8, 108)
    ax.grid(axis="y", alpha=0.22, linewidth=0.7, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(
        loc="upper right",
        frameon=True,
        fontsize=7.3,
        ncol=1,
        borderpad=0.35,
        labelspacing=0.25,
        handlelength=1.2,
        facecolor="white",
        edgecolor="#CBD5E1",
        framealpha=0.96,
    )
    ax.text(
        0.0,
        -0.24,
        "正值表示 K4V8 低于 K8V4；负值表示没有下降",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.2,
        color="#64748B",
        fontproperties=cjk_font,
    )


def draw_figure(matrix_df: pd.DataFrame, cjk_font: FontProperties):
    set_mpl_style()
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(2, 2, figsize=(10.8, 6.7))
    axes = axes.ravel()
    for ax, metric in zip(axes[:3], METRIC_ROWS):
        draw_metric_panel(ax, matrix_df, metric, cjk_font)
    draw_drop_panel(axes[3], matrix_df, cjk_font)

    config_handles = [
        Line2D(
            [0],
            [0],
            color=CONFIG_STYLE[str(config["key"])]["color"],
            marker="o",
            markersize=5.5,
            linewidth=1.8,
            markerfacecolor=CONFIG_STYLE[str(config["key"])]["fill"],
            markeredgecolor=CONFIG_STYLE[str(config["key"])]["color"],
            markeredgewidth=0.95,
            label=str(config["label"]),
        )
        for config in CONFIG_ROWS
    ]
    fig.legend(
        handles=config_handles,
        loc="upper center",
        ncol=len(config_handles),
        frameon=False,
        fontsize=8.6,
        bbox_to_anchor=(0.5, 1.015),
    )
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PDF, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    print_contract(
        "plot_ch4_kv_role_sensitivity.py",
        inputs=[
            str(PAPER_TABLES_DIR / "table1_main_quality_*.csv"),
            str(PAPER_TABLES_DIR / "table3_mixedkv_*.csv"),
            str(KV_ABLATION_TABLES_DIR / "kv_ablation_ruler.csv"),
            str(KV_ABLATION_TABLES_DIR / "kv_ablation_longbench.csv"),
            str(K4V8_NEEDLE_RUNS_DIR / "k_int4_v_int8_long_*/profile_needle_*.csv"),
        ],
        outputs=[str(OUTPUT_PDF), str(OUTPUT_DATA)],
    )
    cjk_font = find_cjk_font()
    matrix_df = build_source_matrix()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    matrix_df.to_csv(OUTPUT_DATA, index=False)
    draw_figure(matrix_df, cjk_font)
    print(f"  wrote: {OUTPUT_DATA}")
    print(f"  wrote: {OUTPUT_PDF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
