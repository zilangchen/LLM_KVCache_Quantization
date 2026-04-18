#!/usr/bin/env python3
"""iteration_tool.py — Manage iteration.md: trim timeline, archive legacy plan state, stats.

Usage:
    python scripts/iteration_tool.py stats
    python scripts/iteration_tool.py trim-timeline [--keep 30] [--dry-run]
    python scripts/iteration_tool.py clean-plans [--dry-run]
"""
from __future__ import annotations

import argparse
import fcntl
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITERATION = ROOT / "iteration.md"
ARCHIVE_DIR = ROOT / "development_history"

H2_RE = re.compile(r"^## (.+)$")
H3_RE = re.compile(r"^### (.+)$")
COMPLETED_PLAN_RE = re.compile(r"^### Plan: (.+?) ✅ 已完成$")

# ---------------------------------------------------------------------------
# File I/O helpers (aligned with review_tool.py patterns)
# ---------------------------------------------------------------------------


def _read_locked(path: Path) -> str:
    """Read file with shared lock."""
    with open(path, "r", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        content = f.read()
        fcntl.flock(f, fcntl.LOCK_UN)
    return content


def _atomic_write(path: Path, content: str) -> None:
    """Write file atomically via tempfile + rename, with exclusive lock."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
            fcntl.flock(f, fcntl.LOCK_UN)
        os.rename(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _split_h3_entries(lines: list[str]) -> list[list[str]]:
    """Split a list of lines into H3 entry groups.

    Each group starts with a ``### ...`` line and includes all subsequent
    lines up to the next ``### `` or end-of-list.  Lines before the first
    ``### `` are discarded (they belong to the parent section header).
    """
    entries: list[list[str]] = []
    current: list[str] | None = None

    for line in lines:
        if H3_RE.match(line):
            if current is not None:
                entries.append(current)
            current = [line]
        elif current is not None:
            current.append(line)

    if current is not None:
        entries.append(current)
    return entries


def _find_section_range(
    lines: list[str], heading: str
) -> tuple[int, int] | None:
    """Return (start, end) line indices for the ``## <heading>`` section.

    *start* is the index of the ``## `` line itself.  *end* is the index of
    the next ``## `` line (or the ``---`` separator immediately before it),
    or ``len(lines)`` if this is the last section.
    """
    start: int | None = None
    for i, line in enumerate(lines):
        m = H2_RE.match(line)
        if m:
            if start is not None:
                # Check if previous line is a separator
                end = i
                if end > 0 and lines[end - 1].strip() == "---":
                    end -= 1
                # Also skip blank lines before separator
                while end > start and lines[end - 1].strip() == "":
                    end -= 1
                return (start, end)
            if m.group(1).strip() == heading:
                start = i
    if start is not None:
        return (start, len(lines))
    return None


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_stats(args: argparse.Namespace) -> int:
    """Print iteration.md statistics."""
    if not ITERATION.exists():
        print(f"ERROR: {ITERATION} not found", file=sys.stderr)
        return 2

    text = _read_locked(ITERATION)
    lines = text.split("\n")
    total_lines = len(lines)

    # Count H3 entries in each H2 section
    plans_range = _find_section_range(lines, "Approved Plans")
    timeline_range = _find_section_range(lines, "Timeline (Latest First)")

    plans_entries: list[list[str]] = []
    timeline_entries: list[list[str]] = []

    if plans_range:
        plans_entries = _split_h3_entries(lines[plans_range[0] : plans_range[1]])
    if timeline_range:
        timeline_entries = _split_h3_entries(
            lines[timeline_range[0] : timeline_range[1]]
        )

    # Classify plans
    completed_plans = 0
    active_plans = 0
    for entry in plans_entries:
        heading = entry[0].strip()
        if "✅" in heading:
            completed_plans += 1
        else:
            active_plans += 1

    print(f"=== iteration.md Statistics ===")
    print(f"Total lines:        {total_lines}")
    if plans_range:
        print(
            f"Legacy Plans:       {len(plans_entries)} "
            f"({completed_plans} completed, {active_plans} active)"
        )
        print(
            f"  Section range:    L{plans_range[0]+1}-L{plans_range[1]}"
            f" ({plans_range[1] - plans_range[0]} lines)"
        )
    else:
        print("Legacy Plans:       0 (deprecated; iteration.md is timeline-only)")
    print(f"Timeline entries:   {len(timeline_entries)}")
    if timeline_range:
        print(f"  Section range:    L{timeline_range[0]+1}-L{timeline_range[1]}"
              f" ({timeline_range[1] - timeline_range[0]} lines)")

    # Check archive
    archive_month = datetime.now().strftime("%Y%m")
    archive_path = ARCHIVE_DIR / f"iteration_archive_{archive_month}.md"
    if archive_path.exists():
        archive_lines = len(archive_path.read_text(encoding="utf-8").split("\n"))
        print(f"Archive ({archive_path.name}): {archive_lines} lines")
    else:
        print(f"Archive ({archive_path.name}): not found")

    return 0


def cmd_trim_timeline(args: argparse.Namespace) -> int:
    """Archive old Timeline entries, keeping only the most recent N."""
    keep: int = args.keep
    dry_run: bool = args.dry_run

    if not ITERATION.exists():
        print(f"ERROR: {ITERATION} not found", file=sys.stderr)
        return 2

    text = _read_locked(ITERATION)
    lines = text.split("\n")

    timeline_range = _find_section_range(lines, "Timeline (Latest First)")
    if timeline_range is None:
        print("ERROR: '## Timeline (Latest First)' section not found",
              file=sys.stderr)
        return 1

    # Extract timeline header lines (between ## heading and first ###)
    t_start, t_end = timeline_range
    timeline_section = lines[t_start:t_end]
    entries = _split_h3_entries(timeline_section)

    # Lines before first ### in timeline section (the ## heading + any blank lines)
    first_h3_offset = None
    for i, line in enumerate(timeline_section):
        if H3_RE.match(line):
            first_h3_offset = i
            break
    header_lines = timeline_section[:first_h3_offset] if first_h3_offset else timeline_section

    total = len(entries)
    if total <= keep:
        print(f"Timeline has {total} entries (≤ {keep}). Nothing to trim.")
        return 0

    to_keep = entries[:keep]
    to_archive = entries[keep:]

    archive_month = datetime.now().strftime("%Y%m")
    archive_path = ARCHIVE_DIR / f"iteration_archive_{archive_month}.md"

    # Build archive content
    archive_text_parts = []
    for entry in reversed(to_archive):  # Reverse so oldest is first in archive
        archive_text_parts.append("\n".join(entry))

    archive_addition = "\n".join(archive_text_parts)
    if not archive_addition.endswith("\n"):
        archive_addition += "\n"

    if dry_run:
        print(f"[DRY RUN] Would trim: {total} → {keep} entries "
              f"(archive {len(to_archive)} to {archive_path.name})")
        print(f"[DRY RUN] Entries to archive:")
        for entry in to_archive:
            heading = entry[0].strip()
            print(f"  - {heading}")
        return 0

    # Ensure archive directory exists
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    # Append to archive
    existing_archive = ""
    if archive_path.exists():
        existing_archive = _read_locked(archive_path)
        if not existing_archive.endswith("\n"):
            existing_archive += "\n"

    if not existing_archive:
        # Create with header
        archive_header = (
            f"# Iteration Log — Archive ({datetime.now().strftime('%Y-%m')})\n\n"
            f"> Archived Timeline entries from iteration.md.\n"
            f"> Current active progress: see `iteration.md`.\n\n---\n\n"
        )
        _atomic_write(archive_path, archive_header + archive_addition)
    else:
        _atomic_write(archive_path, existing_archive + "\n" + archive_addition)

    # Rebuild iteration.md with trimmed timeline
    new_timeline_lines = header_lines[:]
    for entry in to_keep:
        new_timeline_lines.extend(entry)

    new_lines = lines[:t_start] + new_timeline_lines + lines[t_end:]
    new_text = "\n".join(new_lines)
    _atomic_write(ITERATION, new_text)

    before_lines = len(lines)
    after_lines = len(new_text.split("\n"))
    print(f"Trimmed: {total} → {keep} entries, "
          f"archived {len(to_archive)} to {archive_path.name}")
    print(f"iteration.md: {before_lines} → {after_lines} lines")
    return 0


def cmd_clean_plans(args: argparse.Namespace) -> int:
    """Backwards-compatible no-op for legacy Approved Plans cleanup."""
    dry_run: bool = args.dry_run

    if not ITERATION.exists():
        print(f"ERROR: {ITERATION} not found", file=sys.stderr)
        return 2

    text = _read_locked(ITERATION)
    lines = text.split("\n")

    plans_range = _find_section_range(lines, "Approved Plans")
    if plans_range is None:
        print("Approved Plans already removed from iteration.md. Nothing to clean.")
        return 0

    p_start, p_end = plans_range
    plans_section = lines[p_start:p_end]
    entries = _split_h3_entries(plans_section)

    # Find completed plans
    completed: list[tuple[int, list[str]]] = []  # (index, entry)
    for i, entry in enumerate(entries):
        heading = entry[0].strip()
        if COMPLETED_PLAN_RE.match(heading):
            completed.append((i, entry))

    if not completed:
        print("No completed plans found. Nothing to clean.")
        return 0

    if dry_run:
        print(f"[DRY RUN] Would compress {len(completed)} completed plan(s):")
        for idx, entry in completed:
            heading = entry[0].strip()
            # Extract completion date if present
            date_str = "unknown"
            for line in entry:
                if "完成日期" in line:
                    m = re.search(r"(\d{4}-\d{2}-\d{2})", line)
                    if m:
                        date_str = m.group(1)
                    break
            print(f"  - {heading} (completed {date_str})")
        return 0

    # Replace completed entries with 1-line summaries
    for idx, entry in completed:
        heading = entry[0].strip()
        m = COMPLETED_PLAN_RE.match(heading)
        plan_name = m.group(1) if m else heading

        # Extract completion date
        date_str = "unknown"
        for line in entry:
            if "完成日期" in line:
                dm = re.search(r"(\d{4}-\d{2}-\d{2})", line)
                if dm:
                    date_str = dm.group(1)
                break

        summary = (
            f"### ~~Plan: {plan_name}~~ ✅ 完成 {date_str}"
            f"（详见 Timeline 归档）\n"
        )
        entries[idx] = [summary]

    # Rebuild plans section: header lines + entries
    first_h3_offset = None
    for i, line in enumerate(plans_section):
        if H3_RE.match(line):
            first_h3_offset = i
            break
    header_lines = plans_section[:first_h3_offset] if first_h3_offset else plans_section

    new_plans_lines = header_lines[:]
    for entry in entries:
        new_plans_lines.extend(entry)

    new_lines = lines[:p_start] + new_plans_lines + lines[p_end:]
    new_text = "\n".join(new_lines)
    _atomic_write(ITERATION, new_text)

    before_lines = len(lines)
    after_lines = len(new_text.split("\n"))
    print(f"Compressed {len(completed)} completed plan(s) to 1-line summaries.")
    print(f"iteration.md: {before_lines} → {after_lines} lines")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Manage iteration.md — timeline trim, legacy cleanup, stats."
    )
    sub = parser.add_subparsers(dest="command")

    # stats
    sub.add_parser("stats", help="Print iteration.md statistics")

    # trim-timeline
    p_trim = sub.add_parser(
        "trim-timeline",
        help="Archive old Timeline entries, keep most recent N",
    )
    p_trim.add_argument(
        "--keep", type=int, default=30, help="Number of entries to keep (default: 30)"
    )
    p_trim.add_argument(
        "--dry-run", action="store_true", help="Preview without modifying files"
    )

    # clean-plans
    p_clean = sub.add_parser(
        "clean-plans",
        help="Legacy compatibility: clean old Approved Plans if still present",
    )
    p_clean.add_argument(
        "--dry-run", action="store_true", help="Preview without modifying files"
    )

    args = parser.parse_args()

    if args.command == "stats":
        return cmd_stats(args)
    elif args.command == "trim-timeline":
        return cmd_trim_timeline(args)
    elif args.command == "clean-plans":
        return cmd_clean_plans(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
