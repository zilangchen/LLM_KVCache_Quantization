#!/usr/bin/env python3
"""migrate_review_to_md.py — One-time migration from review.yaml to review_tracker.md.

Usage:
    python scripts/migrate_review_to_md.py
    python scripts/migrate_review_to_md.py --dry-run
"""
from __future__ import annotations

import argparse
import datetime
import sys
from collections import defaultdict
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
REVIEW_YAML = REPO_ROOT / "review.yaml"
OUTPUT_MD = REPO_ROOT / "review_tracker.md"

SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
SEV_SHORT = {"CRITICAL": "CRIT", "HIGH": "HIGH", "MEDIUM": "MED", "LOW": "LOW"}

# Natural sort key for section letters: A, B, ..., Z, AA, AB, ...
def section_sort_key(sec: str) -> tuple[int, str]:
    return (len(sec), sec)


def issue_to_line(iid: str, issue: dict) -> str:
    """Convert a single issue to a markdown checkbox line."""
    sev = issue.get("severity", "MEDIUM")
    sev_tag = SEV_SHORT.get(sev, sev)
    status = issue.get("status", "open")
    checkbox = "x" if status != "open" else " "

    # Use title; fall back to description if title == description
    title = issue.get("title", "(no title)")
    desc = issue.get("description", "")
    if title == desc or not title:
        title = desc

    # Truncate if too long
    if len(title) > 150:
        title = title[:147] + "..."

    line = f"- [{checkbox}] **{iid}** `[{sev_tag}]` {title}"

    # Append resolution info for non-open
    if status == "fixed":
        res = issue.get("resolution") or {}
        commit = res.get("commit", "")
        if commit:
            line += f" — fixed commit {commit}"
        else:
            line += " — fixed"
    elif status == "false_positive":
        line += " — false_positive"
    elif status == "wont_fix":
        line += " — wont_fix"

    return line


def build_markdown(data: dict) -> str:
    """Build the complete review_tracker.md content."""
    issues = data.get("issues", {})
    now = datetime.datetime.now().strftime("%Y-%m-%d")

    # Categorize
    total = len(issues)
    open_issues = {k: v for k, v in issues.items() if v.get("status") == "open"}
    resolved_issues = {k: v for k, v in issues.items() if v.get("status") != "open"}
    fixed_count = sum(1 for v in issues.values() if v.get("status") == "fixed")
    fp_count = sum(1 for v in issues.values() if v.get("status") == "false_positive")
    wf_count = sum(1 for v in issues.values() if v.get("status") == "wont_fix")

    open_by_sev = defaultdict(int)
    for v in open_issues.values():
        open_by_sev[v.get("severity", "MEDIUM")] += 1

    # Identify blocker IDs (CRITICAL + open + confidence HIGH/MEDIUM)
    blocker_ids = [
        iid for iid, i in issues.items()
        if i.get("status") == "open"
        and i.get("severity") == "CRITICAL"
        and i.get("confidence", "MEDIUM") in ("HIGH", "MEDIUM")
    ]

    # Group by section
    sections_open = defaultdict(list)  # section -> [(iid, issue)]
    sections_resolved = defaultdict(list)
    section_titles = {}

    for iid, issue in issues.items():
        sec = issue.get("audit", {}).get("section", "?")
        sec_title = issue.get("audit", {}).get("section_title", "")
        if sec not in section_titles and sec_title:
            section_titles[sec] = sec_title

        if issue.get("status") == "open":
            sections_open[sec].append((iid, issue))
        else:
            sections_resolved[sec].append((iid, issue))

    # Sort issues within each section by severity
    def sort_by_sev(items):
        return sorted(items, key=lambda x: SEV_ORDER.get(x[1].get("severity", "LOW"), 9))

    # Identify Phase Blocker sections (sections containing CRITICAL open issues)
    blocker_sections = set()
    for iid, issue in open_issues.items():
        if issue.get("severity") == "CRITICAL":
            sec = issue.get("audit", {}).get("section", "?")
            blocker_sections.add(sec)

    # Build summary line
    open_count = len(open_issues)
    resolved_count = len(resolved_issues)
    sev_parts = []
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        c = open_by_sev.get(sev, 0)
        if c > 0:
            sev_parts.append(f"{c} {SEV_SHORT[sev]}")
    sev_str = ", ".join(sev_parts)

    res_parts = []
    if fixed_count:
        res_parts.append(f"{fixed_count} fixed")
    if fp_count:
        res_parts.append(f"{fp_count} false_positive")
    if wf_count:
        res_parts.append(f"{wf_count} wont_fix")
    res_str = " + ".join(res_parts)

    phase_status = "BLOCKED" if blocker_ids else "CLEAR"
    blocker_str = ", ".join(blocker_ids) if blocker_ids else "none"

    lines = []
    lines.append("# Code Review Tracker")
    lines.append("")
    lines.append(f"> {total} issues | {res_str} | {open_count} open ({sev_str})")
    lines.append(f"> Phase Gate: **{phase_status}** — {blocker_str}")
    lines.append(f"> Last updated: {now}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Phase Blockers section
    lines.append("## Phase Blockers (CRITICAL open)")
    lines.append("")
    if not blocker_sections:
        lines.append("*No CRITICAL open issues. Phase gate is CLEAR.*")
        lines.append("")
    else:
        for sec in sorted(blocker_sections, key=section_sort_key):
            sec_title = section_titles.get(sec, "")
            # Get the primary module from the first issue
            items = sections_open.get(sec, [])
            module = ""
            if items:
                module = items[0][1].get("module", "")

            header = f"### {sec}. {sec_title}"
            if module:
                header += f" — `{module}`"
            lines.append(header)
            lines.append("")
            for iid, issue in sort_by_sev(items):
                lines.append(issue_to_line(iid, issue))
            lines.append("")

    lines.append("---")
    lines.append("")

    # Open Issues section (non-CRITICAL sections)
    lines.append("## Open Issues")
    lines.append("")
    non_blocker_open_sections = sorted(
        [s for s in sections_open if s not in blocker_sections],
        key=section_sort_key
    )
    if not non_blocker_open_sections:
        lines.append("*No non-critical open issues.*")
        lines.append("")
    else:
        for sec in non_blocker_open_sections:
            sec_title = section_titles.get(sec, "")
            items = sections_open[sec]
            module = items[0][1].get("module", "") if items else ""

            header = f"### {sec}. {sec_title}"
            if module:
                header += f" — `{module}`"
            lines.append(header)
            for iid, issue in sort_by_sev(items):
                lines.append(issue_to_line(iid, issue))
            lines.append("")

    lines.append("---")
    lines.append("")

    # Resolved section (folded)
    lines.append("## Resolved")
    lines.append("")
    lines.append(f"<details>")
    lines.append(f"<summary>{res_str} (click to expand)</summary>")
    lines.append("")

    all_resolved_sections = sorted(sections_resolved.keys(), key=section_sort_key)
    for sec in all_resolved_sections:
        sec_title = section_titles.get(sec, "")
        items = sections_resolved[sec]
        lines.append(f"### {sec}. {sec_title}")
        for iid, issue in sort_by_sev(items):
            lines.append(issue_to_line(iid, issue))
        lines.append("")

    lines.append("</details>")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate review.yaml to review_tracker.md")
    parser.add_argument("--dry-run", action="store_true", help="Print stats only")
    parser.add_argument("--input", type=Path, default=REVIEW_YAML)
    parser.add_argument("--output", type=Path, default=OUTPUT_MD)
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: {args.input} not found", file=sys.stderr)
        return 1

    with open(args.input, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    issues = data.get("issues", {})
    from collections import Counter
    by_status = Counter(i["status"] for i in issues.values())
    open_by_sev = Counter(i["severity"] for i in issues.values() if i["status"] == "open")

    print(f"Loaded {len(issues)} issues from {args.input}")
    print(f"  Status: {dict(by_status)}")
    print(f"  Open by severity: {dict(open_by_sev)}")

    md_content = build_markdown(data)
    line_count = md_content.count("\n")

    if args.dry_run:
        print(f"\n[DRY RUN] Would write {line_count} lines to {args.output}")
        return 0

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\nWrote {line_count} lines to {args.output}")
    print("Verify: python scripts/review_tool.py stats")
    return 0


if __name__ == "__main__":
    sys.exit(main())
