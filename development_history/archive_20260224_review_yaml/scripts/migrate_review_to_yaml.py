#!/usr/bin/env python3
"""migrate_review_to_yaml.py — One-time migration from iteration.md TODO Backlog to review.yaml.

Parses the TODO Backlog section of iteration.md (lines 7-455) and converts
all ~200 issues into structured YAML format.

Usage:
    python scripts/migrate_review_to_yaml.py
    python scripts/migrate_review_to_yaml.py --dry-run   # Parse only, don't write
    python scripts/migrate_review_to_yaml.py --verbose    # Show parsing details
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ITERATION_MD = REPO_ROOT / "iteration.md"
REVIEW_YAML = REPO_ROOT / "review.yaml"


# --- Section metadata ---

SECTION_METADATA = {
    "A": {
        "title": "MSE 校准实现缺陷",
        "module": "scripts/calibrate_behavior.py",
        "round": 1,
    },
    "B": {
        "title": "KIVI Cache 实现",
        "module": "src/cache/kivi_style_cache.py",
        "round": 1,
    },
    "C": {
        "title": "非对称量化模块",
        "module": "src/quant/asymmetric_quant.py",
        "round": 1,
    },
    "D": {
        "title": "Engine 集成",
        "module": "src/engine/generate_loop.py",
        "round": 1,
    },
    "E": {
        "title": "评测脚本集成",
        "module": "scripts/",
        "round": 1,
    },
    "F": {
        "title": "实验配置矩阵一致性",
        "module": "configs/",
        "round": 1,
    },
    "G": {
        "title": "消融配置审查",
        "module": "configs/snapshots/exp_matrix_ablation_1p5b_v1.yaml",
        "round": 2,
    },
    "H": {
        "title": "export/generate/configs 审查",
        "module": "scripts/",
        "round": 2,
    },
    "I": {
        "title": "final_emnlp2026_v1.yaml 审查",
        "module": "configs/snapshots/final_emnlp2026_v1.yaml",
        "round": 3,
    },
    "J": {
        "title": "修复审查与新发现",
        "module": "scripts/",
        "round": 4,
    },
    "K": {
        "title": "generate_loop.py KIVI 路径",
        "module": "src/engine/generate_loop.py",
        "round": 5,
    },
    "L": {
        "title": "run_experiments.py 审查",
        "module": "scripts/run_experiments.py",
        "round": 5,
    },
    "M": {
        "title": "aggregate_results.py 审查",
        "module": "scripts/aggregate_results.py",
        "round": 5,
    },
    "N": {
        "title": "eval_ppl/aggregate 修复验证",
        "module": "scripts/",
        "round": 6,
    },
    "O": {
        "title": "eval_ruler.py 评分逻辑",
        "module": "scripts/eval_ruler.py",
        "round": 7,
    },
    "P": {
        "title": "测试覆盖质量",
        "module": "tests/",
        "round": 7,
    },
    "Q": {
        "title": "eval_longbench.py 评分指标",
        "module": "scripts/eval_longbench.py",
        "round": 8,
    },
    "R": {
        "title": "profile_memory.py 内存测量",
        "module": "scripts/profile_memory.py",
        "round": 8,
    },
    "S": {
        "title": "run_experiments.py 实验运行器",
        "module": "scripts/run_experiments.py",
        "round": 9,
    },
    "T": {
        "title": "check_run_completeness.py",
        "module": "scripts/check_run_completeness.py",
        "round": 9,
    },
    "U": {
        "title": "generate_loop + patch_model KIVI",
        "module": "src/engine/",
        "round": 10,
    },
    "V": {
        "title": "KIVI INT4 路径",
        "module": "src/cache/kivi_style_cache.py",
        "round": 11,
    },
    "W": {
        "title": "final_emnlp2026_v1.yaml 最终配置",
        "module": "configs/snapshots/final_emnlp2026_v1.yaml",
        "round": 11,
    },
    "X": {
        "title": "INT8KVCache vs KIVIStyleKVCache 对比",
        "module": "src/cache/",
        "round": 12,
    },
    "Y": {
        "title": "对称量化核心模块",
        "module": "src/quant/",
        "round": 13,
    },
    "Z": {
        "title": "Phase 4 完成验证",
        "module": "scripts/",
        "round": 14,
    },
    "AA": {
        "title": "calibrate_behavior MSE 审查",
        "module": "scripts/calibrate_behavior.py",
        "round": 15,
    },
    "AB": {
        "title": "aggregate_results KIVI/多模型",
        "module": "scripts/aggregate_results.py",
        "round": 15,
    },
    "AC": {
        "title": "export_tables + generate_thesis_report",
        "module": "scripts/",
        "round": 15,
    },
    "AD": {
        "title": "eval_ppl + profile_latency KIVI",
        "module": "scripts/",
        "round": 15,
    },
    "AE": {
        "title": "测试套件覆盖缺口",
        "module": "tests/",
        "round": 15,
    },
    "AF": {
        "title": "Codex PR #5 增量审查",
        "module": "scripts/",
        "round": 16,
    },
    "AG": {
        "title": "RULER 长上下文溢出",
        "module": "scripts/eval_ruler.py",
        "round": 17,
    },
}


def infer_category(description: str, section: str) -> str:
    """Infer issue category from description and section context."""
    desc_lower = description.lower()

    if any(
        kw in desc_lower
        for kw in [
            "mse",
            "loss",
            "scale",
            "量化",
            "精度",
            "dtype",
            "float16",
            "clamp",
            "nan",
            "inf",
            "数值",
            "quantile",
            "bit-pack",
        ]
    ):
        return "numerical_correctness"
    if any(
        kw in desc_lower
        for kw in ["接口", "interface", "api", "参数", "签名", "兼容", "破坏"]
    ):
        return "interface_compatibility"
    if any(
        kw in desc_lower
        for kw in [
            "边界",
            "boundary",
            "空",
            "零",
            "极端",
            "batch_size=0",
            "empty",
            "edge",
        ]
    ):
        return "boundary_case"
    if any(
        kw in desc_lower
        for kw in ["配置", "config", "yaml", "矩阵", "缺失", "不一致"]
    ):
        return "configuration_error"
    if any(
        kw in desc_lower for kw in ["测试", "test", "覆盖", "coverage", "单元"]
    ):
        return "test_coverage"
    if any(
        kw in desc_lower
        for kw in [
            "文档",
            "docstring",
            "注释",
            "comment",
            "说明",
            "pep",
            "doc",
        ]
    ):
        return "documentation"
    if any(
        kw in desc_lower
        for kw in ["论文", "paper", "claim", "声明", "公平", "fair", "实验"]
    ):
        return "research_semantics"
    if any(
        kw in desc_lower for kw in ["性能", "延迟", "内存", "memory", "latency"]
    ):
        return "performance"

    return "code_quality"


def infer_confidence(description: str, has_line_ref: bool) -> str:
    """Infer confidence from description characteristics."""
    desc_lower = description.lower()

    if has_line_ref and any(
        kw in desc_lower
        for kw in ["确认", "verified", "代码", "l1", "l2", "l3"]
    ):
        return "HIGH"
    if has_line_ref:
        return "MEDIUM"
    if any(
        kw in desc_lower
        for kw in ["可能", "建议", "理论", "若", "如果", "假设"]
    ):
        return "LOW"
    return "MEDIUM"


def infer_verification(description: str, is_fixed: bool) -> str:
    """Infer verification status."""
    if is_fixed:
        return "confirmed"
    desc_lower = description.lower()
    if any(kw in desc_lower for kw in ["确认", "验证", "confirmed"]):
        return "confirmed"
    if any(kw in desc_lower for kw in ["可能", "建议", "理论"]):
        return "suspected"
    return "unverified"


def parse_file_ref(text: str) -> tuple[str, list[int]]:
    """Extract file path and line numbers from text."""
    # Pattern: (file.py:L123-456) or (file.py L123) etc.
    file_match = re.search(r"\((\S+\.py)\s*[:\s]*(L?\d+(?:[-,L\d]*)*)\)", text)
    if file_match:
        filepath = file_match.group(1)
        line_str = file_match.group(2)
        lines = []
        for part in re.findall(r"\d+", line_str):
            lines.append(int(part))
        return filepath, lines

    # Pattern: file.py:L123 without parens
    file_match2 = re.search(r"(`?)(\S+\.py)\1\s*[:\s]*(L?\d+(?:[-,L\d]*)*)", text)
    if file_match2:
        filepath = file_match2.group(2)
        line_str = file_match2.group(3)
        lines = [int(x) for x in re.findall(r"\d+", line_str)]
        return filepath, lines

    # Pattern: just a .py file reference
    file_match3 = re.search(r"`?(\S+\.py)`?", text)
    if file_match3:
        return file_match3.group(1), []

    return "", []


def parse_commit_ref(text: str) -> str:
    """Extract commit hash from text."""
    m = re.search(r"commit\s+([0-9a-f]{7,40})", text, re.IGNORECASE)
    if m:
        return m.group(1)
    return ""


def parse_pr_ref(text: str) -> str:
    """Extract PR reference from text."""
    m = re.search(r"PR[-\s#]*(\d+)", text)
    if m:
        return f"#{m.group(1)}"
    return ""


def generate_suggested_fix(
    severity: str, description: str, module: str
) -> dict | None:
    """Generate suggested fix for CRITICAL/HIGH issues."""
    if severity not in ("CRITICAL", "HIGH"):
        return None

    desc_lower = description.lower()

    # Try to extract actionable suggestions from description
    approach = ""
    if "建议" in description:
        idx = description.find("建议")
        approach = description[idx:].split("。")[0]
    elif "应" in desc_lower and ("修复" in desc_lower or "改" in desc_lower):
        for sentence in description.split("。"):
            if "应" in sentence:
                approach = sentence.strip()
                break

    if not approach:
        approach = f"Review and fix the issue in {module}"

    return {
        "approach": approach[:200],
        "files_to_change": [module] if module else [],
        "estimated_effort": "small" if severity == "HIGH" else "medium",
    }


def parse_issues_from_markdown(lines: list[str], verbose: bool = False) -> dict:
    """Parse all issues from the TODO Backlog section of iteration.md."""
    issues = {}
    current_section = ""
    current_section_title = ""
    issue_counter = {}  # per-section counter
    in_backlog = False
    skip_until_section = False

    # Lines that are just verification summaries or narrative, not issues
    skip_patterns = [
        "修复质量评价",
        "代码质量评估",
        "整体质量",
        "数值正确性",
        "向后兼容性",
        "新增测试",
        "经验证的误报",
        "已修复项确认",
        "CRITICAL 修复验证",
        "已修复的前期问题映射",
        "未修复的 M 节残留问题",
        "验证发现 — D1 已修复",
    ]

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect start of TODO Backlog
        if "## TODO Backlog" in line:
            in_backlog = True
            i += 1
            continue

        # End of TODO Backlog
        if in_backlog and line.startswith("## ") and "TODO Backlog" not in line:
            break

        if not in_backlog:
            i += 1
            continue

        # Skip narrative headers
        if stripped.startswith(">") or stripped.startswith("---"):
            i += 1
            continue

        # Detect section headers: #### A. Title — file
        section_match = re.match(
            r"^####\s+([A-Z]{1,2})\.\s+(.+?)(?:\s*—\s*(.+?))?(?:\s*\((.+?)\))?$",
            stripped,
        )
        if section_match:
            current_section = section_match.group(1)
            current_section_title = section_match.group(2).strip()
            if current_section not in issue_counter:
                issue_counter[current_section] = 0
            skip_until_section = False
            if verbose:
                print(f"  Section {current_section}: {current_section_title}")
            i += 1
            continue

        # Skip the Phase 5 blocking summary at the top (L9-30)
        if stripped.startswith("### Phase 5") or stripped.startswith(
            "**4 个 CRITICAL"
        ):
            # Skip lines until next section header
            i += 1
            while i < len(lines):
                if lines[i].strip().startswith("####"):
                    break
                if lines[i].strip().startswith("**关键 HIGH"):
                    # Skip this subsection too
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith(
                        "---"
                    ):
                        i += 1
                    break
                i += 1
            continue

        # Skip narrative sub-headers
        if stripped.startswith("**") and not stripped.startswith("- ["):
            # Check if it's a narrative header we should skip
            is_narrative = any(pat in stripped for pat in skip_patterns)
            if is_narrative:
                i += 1
                continue
            # Check if it's a sub-section grouping like "新发现问题"
            i += 1
            continue

        # Parse issue lines: - [x] or - [ ]
        issue_match = re.match(
            r"^-\s+\[([ x~])\]\s*(?:`\[)?(CRITICAL|HIGH|MEDIUM|LOW)(?:\]`)?\s+(.+)",
            stripped,
        )
        if issue_match and current_section:
            checkbox = issue_match.group(1)
            severity = issue_match.group(2)
            rest = issue_match.group(3).strip()

            is_fixed = checkbox in ("x", "~")
            is_false_positive = False

            # Collect continuation lines (sub-bullets that belong to this issue)
            full_text = rest
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith("  ") and not next_line.startswith("- ["):
                    full_text += " " + next_line.strip()
                    i += 1
                elif next_line.startswith("- ") and not re.match(
                    r"^-\s+\[([ x~])\]", next_line
                ):
                    # Sub-bullet without checkbox
                    full_text += " " + next_line[2:].strip()
                    i += 1
                else:
                    break

            # Check for false positive markers — must be about the issue
            # itself, not describing bug behavior (e.g. "被误报为完成")
            fp_patterns = [
                "✅ 误报",
                "误报核销",
                "误报，",
                "误报）",
                "误报)",
                "agent 误报",
                "审查 agent 误报",
            ]
            if any(pat in full_text for pat in fp_patterns):
                is_false_positive = True
            elif "false positive" in full_text.lower():
                is_false_positive = True

            # Check for fix markers
            if "✅" in full_text or "已修复" in full_text:
                is_fixed = True

            # Determine status
            if is_false_positive:
                status = "false_positive"
            elif is_fixed:
                status = "fixed"
            else:
                status = "open"

            # Extract file/line references
            file_ref, line_refs = parse_file_ref(full_text)
            # If no file ref found in text, use section default
            if not file_ref:
                meta = SECTION_METADATA.get(current_section, {})
                file_ref = meta.get("module", "")

            # Extract commit and PR refs
            commit_ref = parse_commit_ref(full_text)
            pr_ref = parse_pr_ref(full_text)

            # Generate issue ID
            issue_counter[current_section] = (
                issue_counter.get(current_section, 0) + 1
            )
            idx = issue_counter[current_section]
            issue_id = f"{current_section}-{idx}"

            # Check if there's an explicit ID in the text (like AG1, AF-N2)
            explicit_id_match = re.search(
                r"\b(AG\d+|AF-[A-Z]\d+|O\d+|T\d+|E\d+)\b", full_text
            )
            # Don't override the systematic ID; we'll add explicit ones as tags

            # Extract title (first sentence or up to colon)
            title = rest
            # Clean up title — take first meaningful part
            if ":" in title and len(title.split(":")[0]) < 100:
                title = title.split(":")[0].strip()
            if " — " in title:
                title = title.split(" — ")[0].strip()
            if "✅" in title:
                title = title.split("✅")[0].strip()
            # Remove trailing parens with file refs
            title = re.sub(r"\s*\([^)]*\.py[^)]*\)\s*$", "", title)
            # Remove backticks
            title = title.replace("`", "")
            # Truncate
            if len(title) > 120:
                title = title[:117] + "..."

            # Description is the full text
            description = full_text.replace("`", "").strip()
            # Clean up fix markers from description
            description = re.sub(r"\s*—\s*✅.*$", "", description)

            # Infer fields
            has_line_ref = bool(line_refs)
            confidence = infer_confidence(full_text, has_line_ref)
            verification = infer_verification(full_text, is_fixed)
            category = infer_category(full_text, current_section)

            meta = SECTION_METADATA.get(current_section, {})
            review_round = meta.get("round", 1)

            # Build issue dict
            issue = {
                "title": title,
                "description": description[:500],
                "severity": severity,
                "confidence": confidence,
                "verification": verification,
                "status": status,
                "category": category,
                "module": file_ref,
            }

            # Location
            if file_ref or line_refs:
                loc = {}
                if file_ref:
                    loc["file"] = file_ref
                if line_refs:
                    loc["lines"] = line_refs
                issue["location"] = loc

            # Suggested fix
            sf = generate_suggested_fix(severity, full_text, file_ref)
            if sf:
                issue["suggested_fix"] = sf

            # Resolution
            if status in ("fixed", "false_positive"):
                resolution = {"fixed_at": "2026-02-23T00:00:00+00:00"}
                if commit_ref:
                    resolution["commit"] = commit_ref
                if pr_ref:
                    resolution["pr"] = pr_ref
                resolution["verified_by"] = "reviewer"
                issue["resolution"] = resolution
            else:
                issue["resolution"] = None

            # Audit
            issue["audit"] = {
                "section": current_section,
                "section_title": meta.get("title", current_section_title),
                "round": review_round,
                "discovered_at": "2026-02-23T00:00:00+00:00",
                "discovered_by": "reviewer",
            }

            # Tags
            tags = []
            if explicit_id_match:
                tags.append(f"legacy_id:{explicit_id_match.group(1)}")
            if "KIVI" in full_text or "kivi" in full_text:
                tags.append("kivi")
            if "论文" in full_text or "paper" in full_text.lower():
                tags.append("paper")
            if tags:
                issue["tags"] = tags

            issues[issue_id] = issue

            if verbose:
                print(
                    f"    {issue_id} [{severity}] [{status}] {title[:60]}"
                )

            continue

        # Also parse strikethrough items from the blocking summary
        # These are already covered by section-level parsing
        i += 1

    return issues


def build_review_yaml(issues: dict) -> dict:
    """Build the complete review.yaml structure."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    open_issues = sum(1 for i in issues.values() if i.get("status") == "open")
    blocking_criticals = sum(
        1
        for i in issues.values()
        if i.get("status") == "open"
        and i.get("severity") == "CRITICAL"
        and i.get("confidence", "MEDIUM") in ("HIGH", "MEDIUM")
    )
    blocking_highs = sum(
        1
        for i in issues.values()
        if i.get("status") == "open" and i.get("severity") == "HIGH"
    )
    blocker_ids = [
        iid
        for iid, i in issues.items()
        if i.get("status") == "open"
        and i.get("severity") == "CRITICAL"
        and i.get("confidence", "MEDIUM") in ("HIGH", "MEDIUM")
    ]

    return {
        "schema_version": "1.0.0",
        "meta": {
            "last_updated": now,
            "last_updated_by": "migration_script",
            "total_issues": len(issues),
            "open_issues": open_issues,
        },
        "phase_gate": {
            "blocking_criticals": blocking_criticals,
            "blocking_highs": blocking_highs,
            "phase5_ready": blocking_criticals == 0,
            "blockers": blocker_ids,
        },
        "issues": issues,
    }


def print_migration_report(issues: dict) -> None:
    """Print migration summary."""
    from collections import Counter

    total = len(issues)
    by_status = Counter(i["status"] for i in issues.values())
    by_severity = Counter(i["severity"] for i in issues.values())
    by_section = Counter(
        i.get("audit", {}).get("section", "?") for i in issues.values()
    )
    open_by_sev = Counter(
        i["severity"] for i in issues.values() if i["status"] == "open"
    )

    print(f"\n{'='*60}")
    print(f"Migration Report: {total} issues migrated")
    print(f"{'='*60}")

    print("\nBy status:")
    for s in ["open", "fixed", "false_positive", "wont_fix", "deferred"]:
        if by_status.get(s, 0) > 0:
            print(f"  {s:16s}: {by_status[s]:4d}")

    print("\nBy severity (all):")
    for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if by_severity.get(s, 0) > 0:
            print(f"  {s:16s}: {by_severity[s]:4d}")

    print("\nOpen by severity:")
    for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if open_by_sev.get(s, 0) > 0:
            print(f"  {s:16s}: {open_by_sev[s]:4d}")

    print("\nBy section:")
    for sec in sorted(by_section.keys()):
        print(f"  {sec:6s}: {by_section[sec]:4d}")

    # Highlight blockers
    blockers = [
        (iid, i)
        for iid, i in issues.items()
        if i["status"] == "open"
        and i["severity"] == "CRITICAL"
        and i.get("confidence", "MEDIUM") in ("HIGH", "MEDIUM")
    ]
    if blockers:
        print(f"\nPhase gate BLOCKERS ({len(blockers)}):")
        for iid, issue in blockers:
            print(f"  {iid}: {issue['title'][:80]}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate iteration.md TODO Backlog to review.yaml"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse only, don't write"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show parsing details"
    )
    parser.add_argument(
        "--iteration-md", type=Path, default=ITERATION_MD, help="iteration.md path"
    )
    parser.add_argument(
        "--output", type=Path, default=REVIEW_YAML, help="Output YAML path"
    )
    args = parser.parse_args()

    if not args.iteration_md.exists():
        print(f"ERROR: {args.iteration_md} not found", file=sys.stderr)
        return 1

    print("Reading iteration.md...")
    with open(args.iteration_md, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print("Parsing TODO Backlog...")
    issues = parse_issues_from_markdown(lines, verbose=args.verbose)

    if not issues:
        print("ERROR: No issues parsed!", file=sys.stderr)
        return 1

    print_migration_report(issues)

    if args.dry_run:
        print("\n[DRY RUN] Would write to:", args.output)
        return 0

    data = build_review_yaml(issues)

    print(f"\nWriting {args.output}...")
    with open(args.output, "w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )

    print("Done! Run validation:")
    print(f"  python scripts/review_query.py --validate --file {args.output}")
    print(f"  python scripts/review_query.py --stats --file {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
