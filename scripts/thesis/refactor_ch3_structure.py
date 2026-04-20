#!/usr/bin/env python3
"""
Ch3 结构重组：10 section → 7 section。

新骨架：
  §3.1 注意力近似误差分析              （原 §3.1 重命名）
  §3.2 方法框架总览                    （原 §3.2 精简 + 纳入原 §3.9.1-3 系统实现）
  §3.3 行为引导校准方法                （原 §3.3 保留）
  §3.4 行为引导校准的 INT8 和 INT4 实现 （原 §3.4+§3.5+§3.8 合并；Triton 成 §3.4 末尾）
  §3.5 Behavior-Guided 层间预算分配器  （原 §3.6+§3.7 AutoK 合并）
  §3.6 复杂度与资源分析                （原 §3.9.4-8 B 类 独立）
  §3.7 本章小结                        （原 §3.10）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CH3 = ROOT / "thesis" / "chapters" / "ch3_method.tex"

SECTION_RE = re.compile(r"^\\section\{(.+?)\}\s*$")
SUBSEC_RE = re.compile(r"^\\subsection\{")


def find_section_boundaries(lines: list[str]) -> list[tuple[int, str]]:
    """返回 [(start_line, title), ...]"""
    out = []
    for i, L in enumerate(lines):
        m = SECTION_RE.match(L)
        if m:
            out.append((i, m.group(1)))
    return out


def slice_sections(lines: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    """切成 preamble + {title: block_lines}"""
    boundaries = find_section_boundaries(lines)
    preamble = lines[: boundaries[0][0]]
    sections: dict[str, list[str]] = {}
    for idx, (start, title) in enumerate(boundaries):
        end = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(lines)
        sections[title] = lines[start:end]
    return preamble, sections


def find_subsec_boundaries(block: list[str]) -> list[int]:
    """返回 block 里所有 \\subsection{} 起始行号"""
    return [i for i, L in enumerate(block) if SUBSEC_RE.match(L)]


def drop_subsec_title_lines(block: list[str], titles_to_drop: list[str]) -> list[str]:
    """删除指定 subsection 的 \\subsection{} 标题行（保留内容）。
    titles_to_drop 做 substring match。"""
    out = []
    for L in block:
        m = SUBSEC_RE.match(L)
        if m:
            for t in titles_to_drop:
                if t in L:
                    break
            else:
                out.append(L)
                continue
            # matched one of titles_to_drop, skip the line
            continue
        out.append(L)
    return out


def rename_section(block: list[str], new_title: str) -> list[str]:
    """把第一个 \\section{} 行改为 \\section{new_title}."""
    out = block.copy()
    out[0] = f"\\section{{{new_title}}}"
    return out


def strip_section_title(block: list[str]) -> list[str]:
    """删除首行 \\section{}，保留紧跟的 \\label{} 和其余内容。"""
    assert SECTION_RE.match(block[0]), f"First line not a \\section: {block[0]!r}"
    return block[1:]


def extract_subsec_range(block: list[str], indices: list[int]) -> list[str]:
    """提取指定索引的 subsection 块（含自身 \\subsection{} 标题 + 其 body）。"""
    subsec_starts = find_subsec_boundaries(block)
    out = []
    for idx in indices:
        start = subsec_starts[idx]
        end = subsec_starts[idx + 1] if idx + 1 < len(subsec_starts) else len(block)
        out.extend(block[start:end])
    return out


def main() -> int:
    text = CH3.read_text()
    lines = text.split("\n")

    preamble, sections = slice_sections(lines)

    TITLES = {
        "3.1": "问题形式化",
        "3.2": "框架总体设计",
        "3.3": "行为引导校准方法",
        "3.4": "自适应保护与 INT8 对称量化配置",
        "3.5": "KIVI-style 格式上的行为引导实例化 RoleAlign",
        "3.6": "Behavior-Guided Allocator",
        "3.7": "AutoK：Profile-Guided 预算建议机制",
        "3.8": "Triton 融合量化解码核：INT8 Canonical Path 的系统落地",
        "3.9": "系统实现与复杂度分析",
        "3.10": "本章小结",
    }
    for k, t in TITLES.items():
        if t not in sections:
            print(f"ERROR: {k} title {t!r} not found. Available: {list(sections.keys())}", file=sys.stderr)
            return 1

    parts: list[list[str]] = [preamble]

    # ===== §3.1 (new) = 原 §3.1 重命名 =====
    s31 = sections[TITLES["3.1"]]
    s31_new = rename_section(s31, "注意力近似误差分析")
    parts.append(s31_new)

    # ===== §3.2 (new) = 原 §3.2（精简）+ 原 §3.9.1-3 (A 类) =====
    s32_old = sections[TITLES["3.2"]]
    # 不删 3 个 subsection 标题 — 保留 "系统架构概述 / 离线校准阶段 / 在线推理阶段" 作为 anchor
    # 用户说"不需要分得那么细"，但每段 intro+body 还是 distinct，保留 subsection 做为 navigational anchor
    # 实际精简：删除 "系统架构概述" subsection 的标题（最 fluffy 的一段），保留其他两个
    s32_new = drop_subsec_title_lines(s32_old, ["系统架构概述"])

    # 从 §3.9 提取 A 类（§3.9.1-3）
    s39_old = sections[TITLES["3.9"]]
    s39_subsec_count = len(find_subsec_boundaries(s39_old))
    assert s39_subsec_count == 8, f"Expected §3.9 has 8 subsec, got {s39_subsec_count}"
    a_class = extract_subsec_range(s39_old, [0, 1, 2])  # KV Cache 管理 / 生成循环 / 量化模式总览

    # A 类加到 §3.2 末尾，同时 保留 sec:ch3-system label
    if s32_new and s32_new[-1].strip() == "":
        # 已有空行结尾，ok
        pass
    else:
        s32_new.append("")
    s32_new.append("% ==== 原 §3.9.1-3 系统架构/生成循环/量化模式总览合入此节 ====")
    s32_new.append("\\label{sec:ch3-system}  % 保持旧 ref 兼容")
    s32_new.extend(a_class)
    parts.append(s32_new)

    # ===== §3.3 (new) = 原 §3.3 保留 =====
    parts.append(sections[TITLES["3.3"]])

    # ===== §3.4 (new) = 原 §3.4 重命名 + 原 §3.5 无标题合入 + 原 §3.8 无标题合入 =====
    s34_old = sections[TITLES["3.4"]]
    s34_new = rename_section(s34_old, "行为引导校准的 INT8 和 INT4 实现")

    # 原 §3.5 → 去掉 section 标题，保留 label 和所有 content；加一个 paragraph 作为 sub-bridge
    s35_old = sections[TITLES["3.5"]]
    s34_new.append("")
    s34_new.append("% ==== 原 §3.5 KIVI-style 实例化 RoleAlign，无 section 标题合入 ====")
    s34_new.extend(strip_section_title(s35_old))

    # 原 §3.8 → 作为 §3.4 的 Triton 末尾（用户明确的 "3.4.4" 定位）
    s38_old = sections[TITLES["3.8"]]
    s34_new.append("")
    s34_new.append("% ==== 原 §3.8 Triton 融合核，作为 §3.4 末尾系统落地 ====")
    s34_new.extend(strip_section_title(s38_old))

    parts.append(s34_new)

    # ===== §3.5 (new) = 原 §3.6 重命名 + 原 §3.7 AutoK 合入 =====
    s36_old = sections[TITLES["3.6"]]
    s35_new = rename_section(s36_old, "Behavior-Guided 层间预算分配器")

    s37_old = sections[TITLES["3.7"]]
    s35_new.append("")
    s35_new.append("% ==== 原 §3.7 AutoK 作为预算建议机制合入此节 ====")
    s35_new.extend(strip_section_title(s37_old))

    parts.append(s35_new)

    # ===== §3.6 (new) = 原 §3.9 B 类 独立为复杂度与资源分析 =====
    b_class = extract_subsec_range(s39_old, [3, 4, 5, 6, 7])  # 复杂度/离线/KV显存/Triton访存/校准产物
    # B 类第 1 个 subsection 是 "复杂度与资源分析"（intro），升级为 section 标题
    # §3.9.4 标题为 `\subsection{复杂度与资源分析}` + `\label{sec:ch3-complexity}`
    # 处理：去掉 subsection 标题行，保留 label（转位），其余内容作为 section body
    new_s36: list[str] = ["\\section{复杂度与资源分析}"]
    # 找到 b_class 的首个 subsection 标题行
    first_subsec_idx = next(i for i, L in enumerate(b_class) if SUBSEC_RE.match(L))
    # 确认这是 "复杂度与资源分析"
    assert "复杂度与资源分析" in b_class[first_subsec_idx], f"Unexpected first subsec: {b_class[first_subsec_idx]!r}"
    # 去掉该 subsection 标题行，保留后续 (含 label)
    new_s36.extend(b_class[first_subsec_idx + 1 :])
    parts.append(new_s36)

    # ===== §3.7 (new) = 原 §3.10 本章小结 =====
    parts.append(sections[TITLES["3.10"]])

    # Flatten
    flat = []
    for p in parts:
        flat.extend(p)
    new_text = "\n".join(flat)
    # 保留末尾 newline
    if not new_text.endswith("\n"):
        new_text += "\n"
    CH3.write_text(new_text)

    # 统计
    new_lines = new_text.split("\n")
    new_boundaries = find_section_boundaries(new_lines)
    print(f"Ch3 重组完成。新 section 结构:")
    for start, title in new_boundaries:
        print(f"  L{start+1:4d}: \\section{{{title}}}")
    print(f"总行数 {len(lines)} → {len(new_lines)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
