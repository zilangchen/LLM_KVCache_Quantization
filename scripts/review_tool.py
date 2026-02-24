#!/usr/bin/env python3
"""review_tool.py — Lightweight query tool for review_tracker.md.

Usage:
    python scripts/review_tool.py stats                  # Summary statistics
    python scripts/review_tool.py phase-gate             # Phase gate check (exit 0/1)
    python scripts/review_tool.py open                   # List open issues
    python scripts/review_tool.py open --sev HIGH        # Filter by severity
    python scripts/review_tool.py open --section AG      # Filter by section
    python scripts/review_tool.py progress               # Per-section progress
    python scripts/review_tool.py add --id AH-1 --sev HIGH --section "AH. New Section" --title "..."
"""
from __future__ import annotations

import argparse
import fcntl
import os
import re
import sys
import tempfile
import warnings
from collections import defaultdict
from pathlib import Path

TRACKER = Path(__file__).resolve().parent.parent / "review_tracker.md"

ISSUE_RE = re.compile(
    r'^- \[([ x])\] \*\*([A-Z]+-\d+)\*\* `\[(\w+)\]` (.+)$'
)
SECTION_RE = re.compile(r'^### ([A-Z]{1,3})\. (.+?)(?:\s*—\s*`.+`)?$')

SEV_ORDER = {"CRIT": 0, "HIGH": 1, "MED": 2, "LOW": 3}
SEV_FULL = {"CRIT": "CRITICAL", "HIGH": "HIGH", "MED": "MEDIUM", "LOW": "LOW"}


def parse_tracker(path: Path) -> list[dict]:
    """Parse review_tracker.md and return list of issue dicts."""
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        sys.exit(2)

    issues = []
    current_section = ""
    current_section_title = ""

    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.rstrip("\n")

            # Section header
            sec_m = SECTION_RE.match(line)
            if sec_m:
                current_section = sec_m.group(1)
                current_section_title = sec_m.group(2).strip()
                continue

            # Issue line
            m = ISSUE_RE.match(line)
            if m:
                checkbox, iid, sev, rest = m.groups()
                status = "open" if checkbox == " " else "resolved"

                # Parse resolution suffix
                resolution = ""
                if " — fixed commit " in rest:
                    idx = rest.index(" — fixed commit ")
                    resolution = rest[idx + len(" — fixed commit "):]
                    rest = rest[:idx]
                    status = "fixed"
                elif rest.endswith(" — fixed"):
                    rest = rest[: -len(" — fixed")]
                    status = "fixed"
                elif rest.endswith(" — false_positive"):
                    rest = rest[: -len(" — false_positive")]
                    status = "false_positive"
                elif rest.endswith(" — wont_fix"):
                    rest = rest[: -len(" — wont_fix")]
                    status = "wont_fix"
                elif checkbox == "x":
                    status = "fixed"

                issues.append({
                    "id": iid,
                    "severity": sev,
                    "title": rest.strip(),
                    "status": status,
                    "section": current_section,
                    "section_title": current_section_title,
                    "commit": resolution.strip() if resolution else "",
                })
                continue

            # RVW-003: Warn about lines that look like issues but don't match
            if line.startswith("- [") and current_section:
                warnings.warn(
                    f"{path}:{lineno}: issue-like line did not match "
                    f"ISSUE_RE: {line!r}",
                    stacklevel=1,
                )

    return issues


def cmd_stats(issues: list[dict]) -> int:
    total = len(issues)
    open_issues = [i for i in issues if i["status"] == "open"]
    fixed = sum(1 for i in issues if i["status"] == "fixed")
    fp = sum(1 for i in issues if i["status"] == "false_positive")
    wf = sum(1 for i in issues if i["status"] == "wont_fix")

    open_by_sev = defaultdict(int)
    for i in open_issues:
        open_by_sev[i["severity"]] += 1

    print(f"=== Review Tracker Stats ({total} total) ===")
    print(f"  open:           {len(open_issues)}")
    print(f"  fixed:          {fixed}")
    print(f"  false_positive: {fp}")
    if wf:
        print(f"  wont_fix:       {wf}")
    print()
    print("Open by severity:")
    for sev in ["CRIT", "HIGH", "MED", "LOW"]:
        c = open_by_sev.get(sev, 0)
        if c > 0:
            full = SEV_FULL.get(sev, sev)
            print(f"  {full:12s}: {c}")
    return 0


def cmd_phase_gate(issues: list[dict]) -> int:
    blockers = [i for i in issues if i["status"] == "open" and i["severity"] == "CRIT"]
    high_open = [i for i in issues if i["status"] == "open" and i["severity"] == "HIGH"]

    if blockers:
        print(f"PHASE GATE: BLOCKED ({len(blockers)} CRITICAL open)")
        for i in blockers:
            print(f"  {i['id']}: {i['title'][:80]}")

    if high_open:
        print(f"WARNING: {len(high_open)} HIGH severity issues still open:")
        for i in high_open:
            print(f"  {i['id']}: {i['title'][:80]}")

    if blockers:
        return 1

    if not high_open:
        print("PHASE GATE: CLEAR")
        print("No blocking CRITICAL issues.")
    else:
        print("PHASE GATE: CLEAR (with warnings)")
        print("No blocking CRITICAL issues, but HIGH issues remain.")
    return 0


def cmd_open(issues: list[dict], sev: str | None = None, section: str | None = None) -> int:
    open_issues = [i for i in issues if i["status"] == "open"]
    if sev:
        sev_upper = sev.upper()
        # Accept both short and full names
        sev_map = {"CRITICAL": "CRIT", "HIGH": "HIGH", "MEDIUM": "MED", "LOW": "LOW"}
        target = sev_map.get(sev_upper, sev_upper)
        valid_sevs = set(SEV_ORDER.keys())
        if target not in valid_sevs:
            print(
                f"ERROR: invalid severity '{sev}'. "
                f"Valid values: {', '.join(sorted(valid_sevs, key=lambda s: SEV_ORDER[s]))} "
                f"(or CRITICAL/MEDIUM)",
                file=sys.stderr,
            )
            return 1
        open_issues = [i for i in open_issues if i["severity"] == target]
    if section:
        sec_upper = section.upper()
        open_issues = [i for i in open_issues if i["section"].upper() == sec_upper]

    open_issues.sort(key=lambda x: SEV_ORDER.get(x["severity"], 9))

    filters = []
    if sev:
        filters.append(f"sev={sev}")
    if section:
        filters.append(f"section={section}")
    filter_str = f" ({', '.join(filters)})" if filters else ""

    print(f"=== Open Issues: {len(open_issues)}{filter_str} ===")
    for i in open_issues:
        print(f"  [{i['severity']:4s}] {i['id']:8s} {i['title'][:90]}")
    return 0


def cmd_progress(issues: list[dict]) -> int:
    sections = defaultdict(lambda: {"total": 0, "resolved": 0, "title": ""})
    for i in issues:
        sec = i["section"]
        sections[sec]["total"] += 1
        sections[sec]["title"] = i["section_title"]
        if i["status"] != "open":
            sections[sec]["resolved"] += 1

    print("=== Progress by Section ===")
    total_all = 0
    resolved_all = 0

    # Sort sections naturally
    for sec in sorted(sections, key=lambda s: (len(s), s)):
        info = sections[sec]
        t, r = info["total"], info["resolved"]
        total_all += t
        resolved_all += r
        pct = r / t * 100 if t > 0 else 0
        bar_len = 8
        filled = round(r / t * bar_len) if t > 0 else 0
        bar = "\u2588" * filled + "\u2591" * (bar_len - filled)
        title = info["title"][:28]
        print(f"  {sec:3s} {title:30s} {bar} {r}/{t}  ({pct:.0f}%)")

    pct_all = resolved_all / total_all * 100 if total_all > 0 else 0
    filled_all = round(resolved_all / total_all * 8) if total_all > 0 else 0
    bar_all = "\u2588" * filled_all + "\u2591" * (8 - filled_all)
    print(f"  {'':3s} {'Total':30s} {bar_all} {resolved_all}/{total_all}  ({pct_all:.0f}%)")
    return 0


def _atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically via tmpfile + os.replace."""
    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), prefix=".review_tool_tmp_", suffix=".md"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_f:
            tmp_f.write(content)
            tmp_f.flush()
            os.fsync(tmp_f.fileno())
        os.replace(tmp_path, str(path))
    except BaseException:
        # Clean up temp file on any failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def cmd_add(path: Path, issue_id: str, sev: str, section_header: str, title: str) -> int:
    """Add a new issue to the Open Issues section."""
    sev_map = {"CRITICAL": "CRIT", "HIGH": "HIGH", "MEDIUM": "MED", "LOW": "LOW"}
    sev_tag = sev_map.get(sev.upper(), sev.upper())

    new_line = f"- [ ] **{issue_id}** `[{sev_tag}]` {title}"

    # RVW-021: Use file locking to prevent concurrent write corruption
    lock_path = path.with_suffix(".md.lock")
    lock_fd = open(lock_path, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # RVW-016: Check for duplicate issue ID
        if re.search(rf'\*\*{re.escape(issue_id)}\*\*', content):
            print(
                f"ERROR: issue ID '{issue_id}' already exists in {path}",
                file=sys.stderr,
            )
            return 1

        # RVW-014: Ensure "## Open Issues" section exists
        oi_match = re.search(r'^## Open Issues', content, re.MULTILINE)
        if not oi_match:
            print(
                f"ERROR: '## Open Issues' section not found in {path}",
                file=sys.stderr,
            )
            return 1

        # Find the section in Open Issues, or create it
        section_pattern = re.compile(
            rf'^### {re.escape(section_header)}',
            re.MULTILINE
        )

        m = section_pattern.search(content)
        if m:
            # Find the end of this section (next ### or ---)
            rest = content[m.end():]
            next_section = re.search(r'\n(?=###\s|---)', rest)
            if next_section:
                insert_pos = m.end() + next_section.start()
            else:
                insert_pos = len(content)
            content = content[:insert_pos] + "\n" + new_line + content[insert_pos:]
        else:
            # Insert new section before "---" that ends Open Issues
            rest = content[oi_match.end():]
            sep = re.search(r'\n---', rest)
            if sep:
                insert_pos = oi_match.end() + sep.start()
                new_section = f"\n\n### {section_header}\n{new_line}\n"
                content = content[:insert_pos] + new_section + content[insert_pos:]
            else:
                # RVW-014: Fail explicitly instead of silently dropping the issue
                print(
                    f"ERROR: no '---' separator found after '## Open Issues' "
                    f"in {path}. Cannot determine insertion point for new "
                    f"section '{section_header}'.",
                    file=sys.stderr,
                )
                return 1

        # RVW-002: Atomic write
        _atomic_write(path, content)

        # Update summary line
        _update_summary(path)
        print(f"Added: {issue_id} [{sev_tag}] {title}")
        return 0
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
        try:
            os.unlink(lock_path)
        except OSError:
            pass


def _update_summary(path: Path) -> None:
    """Re-parse and update the summary lines at the top."""
    import datetime

    issues = parse_tracker(path)
    total = len(issues)
    open_issues = [i for i in issues if i["status"] == "open"]
    fixed = sum(1 for i in issues if i["status"] == "fixed")
    fp = sum(1 for i in issues if i["status"] == "false_positive")
    wf = sum(1 for i in issues if i["status"] == "wont_fix")

    open_by_sev = defaultdict(int)
    for i in open_issues:
        open_by_sev[i["severity"]] += 1

    sev_parts = []
    for sev in ["CRIT", "HIGH", "MED", "LOW"]:
        c = open_by_sev.get(sev, 0)
        if c > 0:
            sev_parts.append(f"{c} {sev}")

    # RVW-022: Include wont_fix in resolution parts
    res_parts = []
    if fixed:
        res_parts.append(f"{fixed} fixed")
    if fp:
        res_parts.append(f"{fp} false_positive")
    if wf:
        res_parts.append(f"{wf} wont_fix")

    blockers = [i for i in issues if i["status"] == "open" and i["severity"] == "CRIT"]
    blocker_ids = [i["id"] for i in blockers]
    phase_status = "BLOCKED" if blocker_ids else "CLEAR"
    blocker_str = ", ".join(blocker_ids) if blocker_ids else "none"

    new_issues_line = f"> {total} issues | {' + '.join(res_parts)} | {len(open_issues)} open ({', '.join(sev_parts)})\n"
    new_phase_line = f"> Phase Gate: **{phase_status}** — {blocker_str}\n"
    new_date_line = f"> Last updated: {datetime.datetime.now().strftime('%Y-%m-%d')}\n"

    # RVW-023: Use regex per-line matching instead of relying on order
    # RVW-004: Robustify summary replacement with regex matching
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith("> "):
            if re.match(r'^> \d+ issues \|', line):
                new_lines.append(new_issues_line)
                continue
            if re.match(r'^> Phase Gate:', line):
                new_lines.append(new_phase_line)
                continue
            if re.match(r'^> Last updated:', line):
                new_lines.append(new_date_line)
                continue
        new_lines.append(line)

    # RVW-002: Atomic write for summary update
    _atomic_write(path, "".join(new_lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Query review_tracker.md")
    parser.add_argument("--file", type=Path, default=None)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("stats", help="Summary statistics")
    subparsers.add_parser("phase-gate", help="Phase gate check")

    open_parser = subparsers.add_parser("open", help="List open issues")
    open_parser.add_argument("--sev", help="Filter by severity")
    open_parser.add_argument("--section", help="Filter by section")

    subparsers.add_parser("progress", help="Per-section progress")

    add_parser = subparsers.add_parser("add", help="Add new issue")
    add_parser.add_argument("--id", required=True, help="Issue ID (e.g. AH-1)")
    add_parser.add_argument("--sev", required=True, help="Severity: CRITICAL/HIGH/MEDIUM/LOW")
    add_parser.add_argument("--section", required=True, help='Section header (e.g. "AH. New Section")')
    add_parser.add_argument("--title", required=True, help="Issue title")

    args = parser.parse_args()
    path = args.file or TRACKER

    if args.command == "add":
        return cmd_add(path, args.id, args.sev, args.section, args.title)

    issues = parse_tracker(path)

    if args.command == "stats":
        return cmd_stats(issues)
    elif args.command == "phase-gate":
        return cmd_phase_gate(issues)
    elif args.command == "open":
        return cmd_open(issues, getattr(args, "sev", None), getattr(args, "section", None))
    elif args.command == "progress":
        return cmd_progress(issues)
    else:
        return cmd_stats(issues)


if __name__ == "__main__":
    sys.exit(main())
