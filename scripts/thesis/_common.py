"""
scripts/thesis/_common.py

共享工具模板：11 个 `make_table_*.py` / `plot_*.py` 的公共 contract。

提供：
1. CSV / JSON 读取 helpers
2. LaTeX booktabs 表格输出 helpers（含加粗 best / Δ 色标）
3. Matplotlib style preset（color-blind safe palette / PDF 向量输出 / 字体嵌入）
4. Thesis 常量（路径 / 章节 / 模型列表）

每个生产脚本在顶部 `from _common import ...` 使用，确保一致性。

使用示例:
    from _common import (
        THESIS_TABLES_DIR, THESIS_FIGURES_DIR,
        MODEL_ORDER, MODEL_DISPLAY,
        load_csv, write_latex_table, save_figure_pdf,
        bold_best_cell, delta_color_marker,
        set_mpl_style,
    )
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

# ─────────────────────────────────────────────────
# 路径 / 章节常量
# ─────────────────────────────────────────────────

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
THESIS_TABLES_DIR = REPO_ROOT / "thesis" / "tables"
THESIS_FIGURES_DIR = REPO_ROOT / "thesis" / "figures"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
RESULTS_DIR = REPO_ROOT / "results"
CLEAN_RERUN_DIR = RESULTS_DIR / "clean_rerun_20260419T09"

# 确保输出目录存在
THESIS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
THESIS_FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────
# 模型 / 任务常量（对齐 M+ 方案）
# ─────────────────────────────────────────────────

MODEL_ORDER = ["1p5b", "3b", "7b", "8b", "14b", "mistral7b"]

MODEL_DISPLAY = {
    "1p5b": "Qwen2.5-1.5B",
    "3b": "Qwen2.5-3B",
    "7b": "Qwen2.5-7B",
    "8b": "Llama-3.1-8B",
    "14b": "Qwen2.5-14B",
    "mistral7b": "Mistral-7B-v0.3",
}

MODEL_GQA = {
    "1p5b":     {"num_layers": 28, "num_heads": 12, "num_kv_heads": 2, "head_dim": 128},
    "3b":       {"num_layers": 36, "num_heads": 16, "num_kv_heads": 2, "head_dim": 128},
    "7b":       {"num_layers": 28, "num_heads": 28, "num_kv_heads": 4, "head_dim": 128},
    "8b":       {"num_layers": 32, "num_heads": 32, "num_kv_heads": 8, "head_dim": 128},
    "14b":      {"num_layers": 48, "num_heads": 40, "num_kv_heads": 8, "head_dim": 128},
    "mistral7b":{"num_layers": 32, "num_heads": 32, "num_kv_heads": 8, "head_dim": 128},
}

CORE_TASKS = ["narrativeqa", "hotpotqa", "gov_report"]
EXTEND_TASKS = ["dureader", "lcc"]
ALL_TASKS = CORE_TASKS + EXTEND_TASKS

TASK_DISPLAY = {
    "narrativeqa": "NarrativeQA",
    "hotpotqa": "HotpotQA",
    "gov_report": "GovReport",
    "dureader": "DuReader",
    "lcc": "LCC",
}

MAIN_POLICIES = ["uniform_int4_k4v4", "bakv_fixed_best", "heuristic_best", "bakv_auto_cov80_max"]

KV_MODE_DISPLAY = {
    "fp16": "FP16",
    "int8_ours": "INT8-ours",
    "int4_ours_asym": "INT4-RoleAlign",
    "kivi_style": "KIVI-style",
}


# ─────────────────────────────────────────────────
# Data loaders
# ─────────────────────────────────────────────────

def load_csv(path: str | pathlib.Path):
    """Lazy import pandas 避免启动成本。"""
    import pandas as pd
    return pd.read_csv(path)


def load_json(path: str | pathlib.Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_summary_final():
    """Clean-rerun step2 compare 主 summary。"""
    return load_csv(CLEAN_RERUN_DIR / "summary_final.csv")


def load_summary_phase1():
    """Clean-rerun step1 canonical (1.5B × 4 kv_mode × 3 task)。"""
    return load_csv(CLEAN_RERUN_DIR / "summary_phase1.csv")


# ─────────────────────────────────────────────────
# LaTeX table helpers (booktabs)
# ─────────────────────────────────────────────────

def bold_best_cell(value: float, is_best: bool) -> str:
    """如果是 best 用 \\textbf{}，否则原值。"""
    s = f"{value:.2f}" if isinstance(value, float) else str(value)
    return f"\\textbf{{{s}}}" if is_best else s


def delta_color_marker(delta: float, threshold: float = 0.5) -> str:
    """Δ > 0 绿色 ↑；Δ < 0 红色 ↓；|Δ| < threshold 中性（不加符号）。"""
    if abs(delta) < threshold:
        return f"{delta:+.2f}"
    if delta > 0:
        return f"\\textcolor{{OliveGreen}}{{{delta:+.2f}$\\uparrow$}}"
    return f"\\textcolor{{red}}{{{delta:+.2f}$\\downarrow$}}"


def write_latex_table(
    tex_body: str,
    caption: str,
    label: str,
    table_id: str,
    note: str | None = None,
) -> pathlib.Path:
    """
    将 table tex body 包装为完整 \\begin{table} 环境并写入 thesis/tables/<table_id>.tex。
    同时写一份 .md 调试版 (thesis/tables/<table_id>.md) 方便 diff review。
    """
    wrapper = []
    wrapper.append("\\begin{table}[!htbp]")
    wrapper.append("  \\centering")
    wrapper.append("  \\small")
    wrapper.append(tex_body)
    wrapper.append(f"  \\caption{{{caption}}}")
    wrapper.append(f"  \\label{{{label}}}")
    if note:
        wrapper.append(f"  \\\\[2pt]\\footnotesize {note}")
    wrapper.append("\\end{table}")
    wrapper_str = "\n".join(wrapper)

    tex_path = THESIS_TABLES_DIR / f"{table_id}.tex"
    tex_path.write_text(wrapper_str, encoding="utf-8")

    return tex_path


def write_debug_md(table_id: str, md_body: str) -> pathlib.Path:
    """同时写一份 Markdown 调试版，便于 review。"""
    md_path = THESIS_TABLES_DIR / f"{table_id}.md"
    md_path.write_text(md_body, encoding="utf-8")
    return md_path


# ─────────────────────────────────────────────────
# Matplotlib style preset
# ─────────────────────────────────────────────────

def set_mpl_style():
    """
    统一 matplotlib 样式：
    - color-blind safe palette (viridis + okabe-ito)
    - 字体嵌入 PDF (pdf.fonttype=42, ps.fonttype=42)
    - 向量输出 (PDF)
    - 合理 default size
    """
    import matplotlib as mpl
    import matplotlib.pyplot as plt  # noqa: F401

    mpl.rcParams.update({
        # fonts
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "legend.fontsize": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        # PDF embedding
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        # style
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        # size
        "figure.figsize": (6, 4),
        "figure.dpi": 100,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


# Okabe-Ito color-blind safe palette (recommended for scientific figures)
OKABE_ITO = {
    "orange":   "#E69F00",
    "sky_blue": "#56B4E9",
    "green":    "#009E73",
    "yellow":   "#F0E442",
    "blue":     "#0072B2",
    "red":      "#D55E00",
    "purple":   "#CC79A7",
    "gray":     "#999999",
}

POLICY_COLORS = {
    "uniform_int4":        OKABE_ITO["gray"],
    "bakv_fixed":          OKABE_ITO["blue"],
    "heuristic":           OKABE_ITO["orange"],
    "bakv_auto_cov80":     OKABE_ITO["red"],
    "kivi_style":          OKABE_ITO["green"],
    "rolealign_static":    OKABE_ITO["sky_blue"],
}

POLICY_MARKERS = {
    "uniform_int4":    "o",
    "bakv_fixed":      "^",
    "heuristic":       "v",
    "bakv_auto_cov80": "*",
    "kivi_style":      "s",
    "rolealign_static": "D",
}


def save_figure_pdf(fig, fig_id: str, dpi: int = 300) -> pathlib.Path:
    """保存 figure 为 PDF（向量 + 字体嵌入）到 thesis/figures/<fig_id>.pdf。"""
    pdf_path = THESIS_FIGURES_DIR / f"{fig_id}.pdf"
    fig.savefig(pdf_path, dpi=dpi, bbox_inches="tight")
    return pdf_path


# ─────────────────────────────────────────────────
# CLI contract helper
# ─────────────────────────────────────────────────

def print_contract(script_name: str, inputs: list[str], outputs: list[str]):
    """每个 make_table / plot 脚本运行时 print 它的 contract，便于 audit。"""
    print(f"[{script_name}]")
    print(f"  inputs:")
    for inp in inputs:
        print(f"    - {inp}")
    print(f"  outputs:")
    for out in outputs:
        print(f"    - {out}")


# ─────────────────────────────────────────────────
# Smoke test (run this file directly)
# ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== thesis/_common.py smoke test ===")
    print(f"REPO_ROOT:          {REPO_ROOT}")
    print(f"THESIS_TABLES_DIR:  {THESIS_TABLES_DIR} (exists={THESIS_TABLES_DIR.exists()})")
    print(f"THESIS_FIGURES_DIR: {THESIS_FIGURES_DIR} (exists={THESIS_FIGURES_DIR.exists()})")
    print(f"CLEAN_RERUN_DIR:    {CLEAN_RERUN_DIR} (exists={CLEAN_RERUN_DIR.exists()})")
    print(f"MODEL_ORDER:        {MODEL_ORDER}")
    print(f"MODEL_DISPLAY[8b]:  {MODEL_DISPLAY['8b']}")
    print(f"ALL_TASKS:          {ALL_TASKS}")
    print(f"POLICY_COLORS:      {len(POLICY_COLORS)} colors defined")
    print()
    print("Testing LaTeX helpers:")
    print(f"  bold_best_cell(10.77, True) = {bold_best_cell(10.77, True)}")
    print(f"  bold_best_cell(9.85, False) = {bold_best_cell(9.85, False)}")
    print(f"  delta_color_marker(+1.23) = {delta_color_marker(1.23)}")
    print(f"  delta_color_marker(-2.45) = {delta_color_marker(-2.45)}")
    print(f"  delta_color_marker(+0.02) = {delta_color_marker(0.02)}")
    print()
    print("Testing matplotlib style preset:")
    try:
        set_mpl_style()
        print("  set_mpl_style() OK")
    except Exception as e:
        print(f"  set_mpl_style() FAILED: {e}")
    print()
    print("=== smoke test done ===")
