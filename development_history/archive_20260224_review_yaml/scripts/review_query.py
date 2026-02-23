#!/usr/bin/env python3
"""review_query.py — Query and validate review.yaml.

Usage:
    python scripts/review_query.py --summary          # Stats by severity/status
    python scripts/review_query.py --open              # List all open issues
    python scripts/review_query.py --phase-gate        # Phase gate check (exit 0/1)
    python scripts/review_query.py --module <path>     # Filter by module
    python scripts/review_query.py --severity CRITICAL # Filter by severity
    python scripts/review_query.py --section A         # Filter by audit section
    python scripts/review_query.py --validate          # Schema validation
    python scripts/review_query.py --stats             # Detailed statistics
    python scripts/review_query.py --sort severity     # Sort output (severity|status|section|id)
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import yaml

REVIEW_YAML = Path(__file__).resolve().parent.parent / "review.yaml"

VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
VALID_STATUSES = {"open", "fixed", "false_positive", "wont_fix", "deferred"}
VALID_CONFIDENCES = {"HIGH", "MEDIUM", "LOW"}
VALID_VERIFICATIONS = {"confirmed", "suspected", "unverified"}
VALID_CATEGORIES = {
    "numerical_correctness",
    "interface_compatibility",
    "boundary_case",
    "configuration_error",
    "test_coverage",
    "documentation",
    "code_quality",
    "performance",
    "research_semantics",
}
VALID_EFFORTS = {"trivial", "small", "medium", "large"}
SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def load_review(path: Path | None = None) -> dict:
    """Load and return the review.yaml data."""
    p = path or REVIEW_YAML
    if not p.exists():
        print(f"ERROR: {p} not found", file=sys.stderr)
        sys.exit(2)
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        print("ERROR: review.yaml root must be a mapping", file=sys.stderr)
        sys.exit(2)
    return data


def validate_schema(data: dict) -> list[str]:
    """Validate review.yaml schema. Returns list of error strings."""
    errors = []

    # Top-level keys
    if "schema_version" not in data:
        errors.append("Missing top-level key: schema_version")
    if "issues" not in data:
        errors.append("Missing top-level key: issues")
        return errors

    issues = data.get("issues", {})
    if not isinstance(issues, dict):
        errors.append("'issues' must be a mapping")
        return errors

    all_ids = set(issues.keys())

    for issue_id, issue in issues.items():
        prefix = f"Issue {issue_id}"
        if not isinstance(issue, dict):
            errors.append(f"{prefix}: must be a mapping")
            continue

        # Required fields
        for field in ("title", "severity", "status"):
            if field not in issue:
                errors.append(f"{prefix}: missing required field '{field}'")

        # Severity
        sev = issue.get("severity")
        if sev and sev not in VALID_SEVERITIES:
            errors.append(f"{prefix}: invalid severity '{sev}'")

        # Status
        status = issue.get("status")
        if status and status not in VALID_STATUSES:
            errors.append(f"{prefix}: invalid status '{status}'")

        # Confidence
        conf = issue.get("confidence")
        if conf and conf not in VALID_CONFIDENCES:
            errors.append(f"{prefix}: invalid confidence '{conf}'")

        # Verification
        verif = issue.get("verification")
        if verif and verif not in VALID_VERIFICATIONS:
            errors.append(f"{prefix}: invalid verification '{verif}'")

        # Category
        cat = issue.get("category")
        if cat and cat not in VALID_CATEGORIES:
            errors.append(f"{prefix}: invalid category '{cat}'")

        # Suggested fix effort
        sf = issue.get("suggested_fix")
        if isinstance(sf, dict):
            effort = sf.get("estimated_effort")
            if effort and effort not in VALID_EFFORTS:
                errors.append(f"{prefix}: invalid estimated_effort '{effort}'")

        # CRITICAL/HIGH must have suggested_fix
        if sev in ("CRITICAL", "HIGH") and status == "open":
            if not issue.get("suggested_fix"):
                errors.append(
                    f"{prefix}: CRITICAL/HIGH open issue must have suggested_fix"
                )

        # Related issues — check for dangling references
        related = issue.get("related_issues", [])
        if isinstance(related, list):
            for ref in related:
                if ref not in all_ids:
                    errors.append(
                        f"{prefix}: related_issues reference '{ref}' not found"
                    )

        # Title length
        title = issue.get("title", "")
        if len(title) > 150:
            errors.append(f"{prefix}: title exceeds 150 chars ({len(title)})")

    return errors


def get_issues(data: dict) -> dict:
    """Return the issues dict."""
    return data.get("issues", {})


def filter_issues(
    issues: dict,
    *,
    status: str | None = None,
    severity: str | None = None,
    module: str | None = None,
    section: str | None = None,
) -> dict:
    """Filter issues by criteria."""
    result = {}
    for iid, issue in issues.items():
        if status and issue.get("status") != status:
            continue
        if severity and issue.get("severity") != severity:
            continue
        if module:
            issue_module = issue.get("module", "")
            if module not in issue_module:
                continue
        if section:
            audit = issue.get("audit", {})
            if audit.get("section", "").upper() != section.upper():
                continue
        result[iid] = issue
    return result


def sort_issues(
    issues: dict, sort_key: str = "severity"
) -> list[tuple[str, dict]]:
    """Sort issues by given key."""
    items = list(issues.items())
    if sort_key == "severity":
        items.sort(key=lambda x: SEVERITY_ORDER.get(x[1].get("severity", "LOW"), 9))
    elif sort_key == "status":
        items.sort(key=lambda x: x[1].get("status", ""))
    elif sort_key == "section":
        items.sort(key=lambda x: x[1].get("audit", {}).get("section", "ZZ"))
    elif sort_key == "id":
        items.sort(key=lambda x: x[0])
    return items


def print_issue_line(iid: str, issue: dict) -> None:
    """Print a single-line summary of an issue."""
    sev = issue.get("severity", "?")
    status = issue.get("status", "?")
    conf = issue.get("confidence", "?")
    title = issue.get("title", "(no title)")
    module = issue.get("module", "")
    marker = "x" if status != "open" else " "
    print(f"  [{marker}] {iid:8s} [{sev:8s}] [{conf:6s}] {title}")
    if module:
        print(f"           └─ {module}")


def cmd_summary(data: dict) -> None:
    """Print summary statistics."""
    issues = get_issues(data)
    total = len(issues)

    by_status = Counter(i.get("status", "unknown") for i in issues.values())
    by_severity = Counter(i.get("severity", "unknown") for i in issues.values())
    open_by_severity = Counter(
        i.get("severity", "unknown")
        for i in issues.values()
        if i.get("status") == "open"
    )

    print(f"=== Review Summary ({total} total issues) ===\n")
    print("By status:")
    for s in ["open", "fixed", "false_positive", "wont_fix", "deferred"]:
        if by_status.get(s, 0) > 0:
            print(f"  {s:16s}: {by_status[s]}")

    print("\nBy severity (all):")
    for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if by_severity.get(s, 0) > 0:
            print(f"  {s:16s}: {by_severity[s]}")

    print("\nBy severity (open only):")
    for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if open_by_severity.get(s, 0) > 0:
            print(f"  {s:16s}: {open_by_severity[s]}")


def cmd_stats(data: dict) -> None:
    """Print detailed statistics."""
    issues = get_issues(data)
    total = len(issues)

    by_status = Counter(i.get("status", "unknown") for i in issues.values())
    by_severity = Counter(i.get("severity", "unknown") for i in issues.values())
    by_category = Counter(i.get("category", "unknown") for i in issues.values())
    by_section = Counter(
        i.get("audit", {}).get("section", "?") for i in issues.values()
    )
    by_confidence = Counter(
        i.get("confidence", "unknown") for i in issues.values()
    )

    open_issues = {k: v for k, v in issues.items() if v.get("status") == "open"}
    open_by_sev = Counter(i.get("severity") for i in open_issues.values())

    print(f"=== Detailed Review Statistics ({total} total issues) ===\n")

    print("--- Status ---")
    for s, c in sorted(by_status.items(), key=lambda x: -x[1]):
        print(f"  {s:20s}: {c:4d}  ({c/total*100:.1f}%)")

    print("\n--- Severity ---")
    for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        c = by_severity.get(s, 0)
        print(f"  {s:20s}: {c:4d}  ({c/total*100:.1f}%)")

    print("\n--- Open by severity ---")
    for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        c = open_by_sev.get(s, 0)
        if c > 0:
            print(f"  {s:20s}: {c:4d}")

    print("\n--- Category ---")
    for cat, c in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat:30s}: {c:4d}")

    print("\n--- Confidence ---")
    for conf in ["HIGH", "MEDIUM", "LOW"]:
        c = by_confidence.get(conf, 0)
        print(f"  {conf:20s}: {c:4d}")

    print("\n--- Audit section ---")
    for sec, c in sorted(by_section.items()):
        print(f"  {sec:10s}: {c:4d}")


def cmd_open(data: dict, sort_key: str = "severity") -> None:
    """List all open issues."""
    issues = get_issues(data)
    open_issues = filter_issues(issues, status="open")
    sorted_items = sort_issues(open_issues, sort_key)

    print(f"=== Open Issues ({len(open_issues)}) ===\n")
    for iid, issue in sorted_items:
        print_issue_line(iid, issue)


def cmd_phase_gate(data: dict) -> int:
    """Check phase gate. Returns 0 if clear, 1 if blocked."""
    issues = get_issues(data)
    blockers = []
    for iid, issue in issues.items():
        if (
            issue.get("status") == "open"
            and issue.get("severity") == "CRITICAL"
            and issue.get("confidence", "MEDIUM") in ("HIGH", "MEDIUM")
        ):
            blockers.append((iid, issue))

    if not blockers:
        print("PHASE GATE: CLEAR")
        print("No blocking CRITICAL issues found.")
        return 0

    print(f"PHASE GATE: BLOCKED ({len(blockers)} blocking issues)\n")
    for iid, issue in blockers:
        conf = issue.get("confidence", "?")
        title = issue.get("title", "(no title)")
        print(f"  {iid}: [{conf}] {title}")

    return 1


def cmd_validate(data: dict) -> int:
    """Validate schema. Returns 0 if valid, 1 if errors."""
    errors = validate_schema(data)
    if not errors:
        print("VALID: review.yaml passes schema validation")
        issues = get_issues(data)
        print(f"  Total issues: {len(issues)}")
        return 0

    print(f"INVALID: {len(errors)} schema errors found:\n")
    for err in errors:
        print(f"  - {err}")
    return 1


def cmd_filter(
    data: dict,
    *,
    severity: str | None = None,
    module: str | None = None,
    section: str | None = None,
    sort_key: str = "severity",
) -> None:
    """Filter and display issues."""
    issues = get_issues(data)
    filtered = filter_issues(
        issues, severity=severity, module=module, section=section
    )
    sorted_items = sort_issues(filtered, sort_key)

    filters = []
    if severity:
        filters.append(f"severity={severity}")
    if module:
        filters.append(f"module={module}")
    if section:
        filters.append(f"section={section}")
    filter_desc = ", ".join(filters) if filters else "none"

    print(f"=== Filtered Issues ({len(filtered)}, filters: {filter_desc}) ===\n")
    for iid, issue in sorted_items:
        print_issue_line(iid, issue)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Query and validate review.yaml"
    )
    parser.add_argument(
        "--file", type=Path, default=None, help="Path to review.yaml"
    )

    # Mode flags
    parser.add_argument("--summary", action="store_true", help="Summary stats")
    parser.add_argument("--stats", action="store_true", help="Detailed stats")
    parser.add_argument("--open", action="store_true", help="List open issues")
    parser.add_argument(
        "--phase-gate", action="store_true", help="Phase gate check"
    )
    parser.add_argument("--validate", action="store_true", help="Schema validation")

    # Filters
    parser.add_argument("--severity", type=str, help="Filter by severity")
    parser.add_argument("--module", type=str, help="Filter by module path")
    parser.add_argument("--section", type=str, help="Filter by audit section")

    # Sort
    parser.add_argument(
        "--sort",
        type=str,
        default="severity",
        choices=["severity", "status", "section", "id"],
        help="Sort order",
    )

    args = parser.parse_args()
    data = load_review(args.file)

    if args.validate:
        return cmd_validate(data)
    elif args.phase_gate:
        return cmd_phase_gate(data)
    elif args.summary:
        cmd_summary(data)
        return 0
    elif args.stats:
        cmd_stats(data)
        return 0
    elif args.open:
        cmd_open(data, args.sort)
        return 0
    elif args.severity or args.module or args.section:
        cmd_filter(
            data,
            severity=args.severity,
            module=args.module,
            section=args.section,
            sort_key=args.sort,
        )
        return 0
    else:
        # Default: summary
        cmd_summary(data)
        return 0


if __name__ == "__main__":
    sys.exit(main())
