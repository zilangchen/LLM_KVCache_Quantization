#!/usr/bin/env python3
"""
thesis terminology & language normalization.

Runs three stages on thesis/chapters/*.tex:
  Stage 1: 术语冲突统一（7 条决议）
  Stage 2: 泛用英文散装词 → 中文（Tier A + Tier C）
  Stage 3: 内部工作语言清理（final-ready / Phase N / Gate C / Level-5 / story 引用）

Protects these regions from modification:
  - 引用/交叉引用命令参数：\\label{}, \\ref{}, \\cite{}, \\eqref{}, ...
  - 代码/路径命令：\\texttt{}, \\code{}, \\verb||, \\path{}, \\url{}
  - 行内数学：$...$

Usage:
  python3 scripts/thesis/normalize_terminology.py --dry-run    # 只统计
  python3 scripts/thesis/normalize_terminology.py --apply      # 写入
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CHAPTERS = ROOT / "thesis" / "chapters"

PROTECTED_PATTERN = re.compile(
    r"("
    r"\\(?:label|ref|autoref|eqref|cite|citep|citet|Cref|cref|pageref|nameref)\{[^}]+\}"
    r"|\\texttt\{[^}]+\}"
    r"|\\code\{[^}]+\}"
    r"|\\verb\|[^|]+\|"
    r"|\\path\{[^}]+\}"
    r"|\\url\{[^}]+\}"
    r"|\$[^$\n]+\$"
    r")",
    flags=0,
)


def mask(text: str) -> tuple[str, list[str]]:
    placeholders: list[str] = []

    def sub(m: re.Match[str]) -> str:
        idx = len(placeholders)
        placeholders.append(m.group(0))
        return f"\u27e6MASK{idx}\u27e7"

    return PROTECTED_PATTERN.sub(sub, text), placeholders


def unmask(text: str, placeholders: list[str]) -> str:
    for i, orig in enumerate(placeholders):
        text = text.replace(f"\u27e6MASK{i}\u27e7", orig)
    return text


STAGE1_RULES: list[tuple[str, str, str]] = [
    (r"行为对齐", r"行为引导", "#1 行为对齐→行为引导"),
    (r"Behavior-Aligned", r"Behavior-Guided", "#1 英文大写"),
    (r"Behavior-aligned", r"Behavior-guided", "#1 英文小写"),
    (r"BA-guided", r"Behavior-Guided", "#7 BA-guided→Behavior-Guided"),
    (r"KIVI 格式", r"KIVI-style 格式", "#5 补 style"),
    (r"角色对齐", r"Role-Aware", "#2 清除角色对齐"),
    (r"角色感知", r"Role-Aware", "#2 清除角色感知"),
    (r"Auto-K", r"AutoK", "#4 Auto-K→AutoK"),
]

STAGE2_RULES: list[tuple[str, str, str]] = [
    (r"\bframework\b", r"框架", "Tier A: framework"),
    (r"\bbaseline\b", r"基线", "Tier A: baseline"),
    (r"\bbudget\b", r"预算", "Tier A: budget"),
    (r"\bablation\b", r"消融", "Tier A: ablation"),
    (r"clean-provenance", r"溯源完整", "Tier A: clean-provenance (Q1-A)"),
    (r"clean provenance", r"溯源完整", "Tier A: clean provenance (Q1-A)"),
    (r"\bcoverage\b", r"覆盖度", "Tier A: coverage"),
    (r"\boverview\b", r"总览", "Tier A: overview"),
    (r"\bpipeline\b", r"流程", "Tier A: pipeline"),
    (r"\bbenchmark\b", r"基准", "Tier A: benchmark"),
    (r"\bsetup\b", r"设置", "Tier A: setup"),
    (r"\bthroughput\b", r"吞吐量", "Tier A: throughput"),
    (r"\binsight\b", r"洞察", "Tier A: insight"),
    (r"\binstance\b", r"实例", "Tier A: instance"),
    (r"\bfindings\b", r"发现", "Tier A: findings"),
    (r"\bvalidation\b", r"验证", "Tier A: validation"),
    (r"\bthreshold\b", r"阈值", "Tier A: threshold"),
    (r"\bmapping\b", r"映射", "Tier A: mapping"),
    (r"\blatency\b", r"延迟", "Tier A: latency"),
    (r"\bdispatch\b", r"调度", "Tier A: dispatch"),
    (r"\bdownstream\b", r"下游", "Tier A: downstream"),
    (r"main matrix", r"主表", "Tier A: main matrix"),
    (r"\bregime\b", r"适用区间", "Tier C Q2-B: regime→适用区间"),
]

STAGE3_RULES: list[tuple[str, str, str]] = [
    (r"（clean-provenance pin=\\code\{([^}]+)\}）", r"（数据溯源完整，对应提交号 \\code{\1}）", "泄露: clean-provenance pin=..."),
    (r"clean-provenance pin=\\code\{([^}]+)\}", r"数据溯源完整（提交号 \\code{\1}）", "泄露: clean-provenance pin= (无括号)"),
    (r"五 final-ready claim", r"五条核心结论", "泄露: five final-ready claim"),
    (r"five final-ready claim", r"五条核心结论", "泄露: five final-ready claim"),
    (r"5 条 final-ready supported claims", r"5 条核心结论", "泄露: final-ready supported claims"),
    (r"5 条 final-ready 的", r"5 条", "泄露: final-ready"),
    (r"final-ready 数据", r"正文数据", "泄露: final-ready 数据"),
    (r"final-ready claims", r"核心主张", "泄露: final-ready claims"),
    (r"final-ready supported claims", r"核心结论", "泄露: final-ready supported claims"),
    (r"Phase 1 TPOT 对比", r"4K 序列 TPOT 对比", "泄露: Phase 1 TPOT"),
    (r"Phase 1 TPOT", r"4K 序列 TPOT", "泄露: Phase 1 TPOT"),
    (r"在 Phase 1（4K）下", r"在 4K 序列长度下", "泄露: Phase 1 (4K)"),
    (r"Gate C verdict \\textbf\{Weak / Mixed\}", r"prompt-adaptive 呈现弱改善或混合特征", "泄露: Gate C verdict"),
    (r"8B Gate C 数据", r"8B 补充数据", "泄露: Gate C"),
    (r"主矩阵的 Level-5 clean-provenance 数据", r"主表数据", "泄露: Level-5"),
    (r"（story §12\.4）", r"", "泄露: story §12.4"),
    (r"（story §15 术语冻结：降 appendix）", r"", "泄露: story §15"),
    (r"story 附 B", r"附录 B", "泄露: story 附 B"),
]

# cross-model 必须在 Stage 2（masked text 上），否则会破坏 \label{*-cross-model-*} / \ref{}
# 并且三条规则的顺序：组合 phrase 先于单词替换，防止 "cross-model" 被先吃掉
STAGE2_CROSS_MODEL_RULES: list[tuple[str, str, str]] = [
    (r"cross-model regime map 主矩阵", r"跨模型适用区间主表", "复合: cross-model regime map 主矩阵"),
    (r"cross-model", r"跨模型", "泛用: cross-model"),
    (r"Cross-Model", r"跨模型", "泛用: Cross-Model"),
]

COMMENT_CLEAN_RULES: list[tuple[str, str, str]] = [
    (r"（Phase \d+[a-z]?[- ]?[^）]*）", r"", "注释: （Phase N ...）"),
    (r"\(Phase \d+[a-z]?[- ]?[^)]*\)", r"", "注释: (Phase N ...)"),
    (r"【Phase \d+[a-z]?[^】]*】", r"", "注释: 【Phase N...】"),
    (r"% story §\d+\.\d+ [^\n]*", r"%", "注释: % story §X.Y ..."),
    (r"% orphan ref resolved \(Phase \d+ §[\d.]+\)", r"", "注释: orphan ref resolved"),
]


def apply_stage(
    text: str,
    rules: list[tuple[str, str, str]],
) -> tuple[str, list[tuple[str, int]]]:
    log: list[tuple[str, int]] = []
    for pat, repl, desc in rules:
        text, n = re.subn(pat, repl, text)
        if n:
            log.append((desc, n))
    return text, log


def process_file(tex: Path, apply: bool) -> dict:
    orig = tex.read_text()

    stage1_logs: list[tuple[str, int]] = []
    stage2_logs: list[tuple[str, int]] = []
    stage3_logs: list[tuple[str, int]] = []
    comment_logs: list[tuple[str, int]] = []

    body = orig

    # abstract_en.tex 是英文摘要，仅做注释清理，不触中英词替换
    if tex.name != "abstract_en.tex":
        # Stage 3 必须在 mask 之前跑：它含 LaTeX 命令组合规则（如 "clean-provenance pin=\\code{...}"），
        # mask 会吃掉 \\code{} 导致规则匹配不到。
        body, stage3_logs = apply_stage(body, STAGE3_RULES)

        # mask 保护 label/ref/cite/texttt/code/verb/path/url/inline-math 后再做单词级替换
        body, placeholders = mask(body)
        body, stage1_logs = apply_stage(body, STAGE1_RULES)
        # cross-model 组合规则先跑（phrase 优先于单词）
        body, cm_logs = apply_stage(body, STAGE2_CROSS_MODEL_RULES)
        body, stage2_logs = apply_stage(body, STAGE2_RULES)
        stage2_logs = cm_logs + stage2_logs
        body = unmask(body, placeholders)

    # Comment 清理在最后（不需要 mask 保护，comment 行就是全文本）
    for pat, repl, desc in COMMENT_CLEAN_RULES:
        body, n = re.subn(pat, repl, body)
        if n:
            comment_logs.append((desc, n))

    new = body

    changed = new != orig
    if changed and apply:
        tex.write_text(new)

    return {
        "file": tex.name,
        "changed": changed,
        "stage1": stage1_logs,
        "stage2": stage2_logs,
        "stage3": stage3_logs,
        "comments": comment_logs,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not (args.apply or args.dry_run):
        parser.error("must pass --dry-run or --apply")

    files = sorted(CHAPTERS.glob("*.tex"))
    total = {"stage1": 0, "stage2": 0, "stage3": 0, "comments": 0}
    report_lines: list[str] = []

    for tex in files:
        r = process_file(tex, apply=args.apply)
        if not r["changed"]:
            continue
        report_lines.append(f"\n=== {r['file']} ===")
        for key, label in [
            ("stage1", "[Stage1 术语统一]"),
            ("stage2", "[Stage2 散装英文]"),
            ("stage3", "[Stage3 内部语言]"),
            ("comments", "[Comment 清理]"),
        ]:
            if r[key]:
                report_lines.append(f"  {label}")
                for desc, n in r[key]:
                    report_lines.append(f"    {n:3d} × {desc}")
                    total[key] += n

    print("\n".join(report_lines))
    print("\n--- TOTAL ---")
    for k, v in total.items():
        print(f"  {k}: {v}")
    print(f"  mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
