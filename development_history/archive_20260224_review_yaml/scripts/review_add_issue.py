#!/usr/bin/env python3
"""review_add_issue.py — Add or update issues in review.yaml.

Usage:
    # Add new issue
    python scripts/review_add_issue.py add \\
        --id AG-4 --title "..." --severity HIGH --confidence MEDIUM \\
        --verification confirmed --module "path/file.py" --lines 100,200 \\
        --section AG --round 1 --description "..." --category boundary_case

    # Update status
    python scripts/review_add_issue.py update --id A-1 --status fixed --commit abc1234

    # Mark false positive
    python scripts/review_add_issue.py update --id J-5 --status false_positive
"""

from __future__ import annotations

import argparse
import datetime
import fcntl
import sys
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


class FileLock:
    """Simple file-based lock for concurrent write protection."""

    def __init__(self, path: Path):
        self.lock_path = path.with_suffix(path.suffix + ".lock")
        self._fd = None

    def __enter__(self):
        self._fd = open(self.lock_path, "w")
        fcntl.flock(self._fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, *args):
        if self._fd:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            self._fd.close()
            try:
                self.lock_path.unlink()
            except OSError:
                pass


def load_review(path: Path) -> dict:
    """Load review.yaml."""
    if not path.exists():
        return {
            "schema_version": "1.0.0",
            "meta": {
                "last_updated": datetime.datetime.now(
                    datetime.timezone.utc
                ).isoformat(),
                "last_updated_by": "system",
                "total_issues": 0,
                "open_issues": 0,
            },
            "phase_gate": {
                "blocking_criticals": 0,
                "blocking_highs": 0,
                "phase5_ready": True,
                "blockers": [],
            },
            "issues": {},
        }
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_review(data: dict, path: Path) -> None:
    """Save review.yaml with updated meta."""
    issues = data.get("issues", {})

    # Update meta
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
        if i.get("status") == "open"
        and i.get("severity") == "HIGH"
    )
    blocker_ids = [
        iid
        for iid, i in issues.items()
        if i.get("status") == "open"
        and i.get("severity") == "CRITICAL"
        and i.get("confidence", "MEDIUM") in ("HIGH", "MEDIUM")
    ]

    data["meta"] = {
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "last_updated_by": "reviewer",
        "total_issues": len(issues),
        "open_issues": open_issues,
    }
    data["phase_gate"] = {
        "blocking_criticals": blocking_criticals,
        "blocking_highs": blocking_highs,
        "phase5_ready": blocking_criticals == 0,
        "blockers": blocker_ids,
    }

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )


def validate_issue(issue: dict, issue_id: str) -> list[str]:
    """Validate a single issue. Returns list of errors."""
    errors = []

    if not issue.get("title"):
        errors.append(f"{issue_id}: missing title")
    if issue.get("severity") not in VALID_SEVERITIES:
        errors.append(f"{issue_id}: invalid severity '{issue.get('severity')}'")
    if issue.get("status") not in VALID_STATUSES:
        errors.append(f"{issue_id}: invalid status '{issue.get('status')}'")
    if issue.get("confidence") and issue["confidence"] not in VALID_CONFIDENCES:
        errors.append(f"{issue_id}: invalid confidence '{issue['confidence']}'")
    if (
        issue.get("verification")
        and issue["verification"] not in VALID_VERIFICATIONS
    ):
        errors.append(
            f"{issue_id}: invalid verification '{issue['verification']}'"
        )
    if issue.get("category") and issue["category"] not in VALID_CATEGORIES:
        errors.append(f"{issue_id}: invalid category '{issue['category']}'")

    sf = issue.get("suggested_fix")
    if isinstance(sf, dict):
        effort = sf.get("estimated_effort")
        if effort and effort not in VALID_EFFORTS:
            errors.append(f"{issue_id}: invalid estimated_effort '{effort}'")

    return errors


def cmd_add(args: argparse.Namespace, path: Path) -> int:
    """Add a new issue."""
    with FileLock(path):
        data = load_review(path)
        issues = data.setdefault("issues", {})

        if args.id in issues:
            print(f"ERROR: Issue '{args.id}' already exists", file=sys.stderr)
            return 1

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        issue = {
            "title": args.title,
            "description": args.description or args.title,
            "severity": args.severity,
            "confidence": args.confidence or "MEDIUM",
            "verification": args.verification or "unverified",
            "status": "open",
            "category": args.category or "code_quality",
            "module": args.module or "",
        }

        # Location
        if args.module or args.lines:
            loc = {}
            if args.module:
                loc["file"] = args.module
            if args.lines:
                loc["lines"] = [int(x) for x in args.lines.split(",")]
            issue["location"] = loc

        # Data flow
        if args.data_flow:
            issue["data_flow"] = [x.strip() for x in args.data_flow.split(";")]

        # Suggested fix
        if args.fix_approach:
            sf = {"approach": args.fix_approach}
            if args.fix_files:
                sf["files_to_change"] = [
                    x.strip() for x in args.fix_files.split(",")
                ]
            sf["estimated_effort"] = args.fix_effort or "small"
            issue["suggested_fix"] = sf

        # Related
        if args.related:
            issue["related_issues"] = [
                x.strip() for x in args.related.split(",")
            ]

        # Resolution (null for open)
        issue["resolution"] = None

        # Audit
        issue["audit"] = {
            "section": args.section or "",
            "section_title": args.section_title or "",
            "round": args.round or 1,
            "discovered_at": now,
            "discovered_by": args.discovered_by or "reviewer",
        }

        # Tags
        if args.tags:
            issue["tags"] = [x.strip() for x in args.tags.split(",")]

        # Validate
        errs = validate_issue(issue, args.id)
        if errs:
            print("Validation errors:", file=sys.stderr)
            for e in errs:
                print(f"  - {e}", file=sys.stderr)
            return 1

        issues[args.id] = issue
        save_review(data, path)
        print(f"Added issue {args.id}: {args.title}")
        return 0


def cmd_update(args: argparse.Namespace, path: Path) -> int:
    """Update an existing issue."""
    with FileLock(path):
        data = load_review(path)
        issues = data.get("issues", {})

        if args.id not in issues:
            print(f"ERROR: Issue '{args.id}' not found", file=sys.stderr)
            return 1

        issue = issues[args.id]
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if args.status:
            if args.status not in VALID_STATUSES:
                print(
                    f"ERROR: Invalid status '{args.status}'", file=sys.stderr
                )
                return 1
            issue["status"] = args.status

            # If marking as fixed, update resolution
            if args.status == "fixed":
                if issue.get("resolution") is None:
                    issue["resolution"] = {}
                issue["resolution"]["fixed_at"] = now
                if args.commit:
                    issue["resolution"]["commit"] = args.commit
                if args.pr:
                    issue["resolution"]["pr"] = args.pr
                issue["resolution"]["verified_by"] = (
                    args.verified_by or "developer"
                )
                if args.notes:
                    issue["resolution"]["notes"] = args.notes

            # If marking as false_positive
            elif args.status == "false_positive":
                if issue.get("resolution") is None:
                    issue["resolution"] = {}
                issue["resolution"]["fixed_at"] = now
                issue["resolution"]["verified_by"] = (
                    args.verified_by or "reviewer"
                )
                if args.notes:
                    issue["resolution"]["notes"] = args.notes

        if args.severity:
            if args.severity not in VALID_SEVERITIES:
                print(
                    f"ERROR: Invalid severity '{args.severity}'",
                    file=sys.stderr,
                )
                return 1
            issue["severity"] = args.severity

        if args.confidence:
            if args.confidence not in VALID_CONFIDENCES:
                print(
                    f"ERROR: Invalid confidence '{args.confidence}'",
                    file=sys.stderr,
                )
                return 1
            issue["confidence"] = args.confidence

        if args.verification:
            if args.verification not in VALID_VERIFICATIONS:
                print(
                    f"ERROR: Invalid verification '{args.verification}'",
                    file=sys.stderr,
                )
                return 1
            issue["verification"] = args.verification

        if args.title:
            issue["title"] = args.title

        if args.notes and not args.status:
            # Just add notes without status change
            if issue.get("resolution") is None:
                issue["resolution"] = {}
            issue["resolution"]["notes"] = args.notes

        save_review(data, path)
        print(f"Updated issue {args.id}: status={issue.get('status')}")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add or update issues in review.yaml"
    )
    parser.add_argument(
        "--file", type=Path, default=None, help="Path to review.yaml"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add subcommand
    add_parser = subparsers.add_parser("add", help="Add a new issue")
    add_parser.add_argument("--id", required=True, help="Issue ID (e.g. AG-4)")
    add_parser.add_argument("--title", required=True, help="Issue title")
    add_parser.add_argument(
        "--severity",
        required=True,
        choices=sorted(VALID_SEVERITIES),
        help="Severity level",
    )
    add_parser.add_argument("--description", help="Detailed description")
    add_parser.add_argument(
        "--confidence", choices=sorted(VALID_CONFIDENCES), help="Confidence"
    )
    add_parser.add_argument(
        "--verification",
        choices=sorted(VALID_VERIFICATIONS),
        help="Verification status",
    )
    add_parser.add_argument("--module", help="Primary file path")
    add_parser.add_argument("--lines", help="Line numbers (comma-separated)")
    add_parser.add_argument(
        "--category", choices=sorted(VALID_CATEGORIES), help="Issue category"
    )
    add_parser.add_argument("--section", help="Audit section (e.g. AG)")
    add_parser.add_argument("--section-title", help="Audit section title")
    add_parser.add_argument("--round", type=int, help="Review round number")
    add_parser.add_argument("--discovered-by", help="Who discovered this")
    add_parser.add_argument(
        "--data-flow", help="Data flow path (semicolon-separated)"
    )
    add_parser.add_argument("--fix-approach", help="Suggested fix approach")
    add_parser.add_argument(
        "--fix-files", help="Files to change (comma-separated)"
    )
    add_parser.add_argument(
        "--fix-effort", choices=sorted(VALID_EFFORTS), help="Fix effort"
    )
    add_parser.add_argument(
        "--related", help="Related issue IDs (comma-separated)"
    )
    add_parser.add_argument("--tags", help="Tags (comma-separated)")

    # Update subcommand
    upd_parser = subparsers.add_parser("update", help="Update an issue")
    upd_parser.add_argument(
        "--id", required=True, help="Issue ID to update"
    )
    upd_parser.add_argument("--status", help="New status")
    upd_parser.add_argument("--severity", help="New severity")
    upd_parser.add_argument("--confidence", help="New confidence")
    upd_parser.add_argument("--verification", help="New verification")
    upd_parser.add_argument("--title", help="New title")
    upd_parser.add_argument("--commit", help="Fix commit hash")
    upd_parser.add_argument("--pr", help="PR number/URL")
    upd_parser.add_argument("--verified-by", help="Who verified the fix")
    upd_parser.add_argument("--notes", help="Resolution notes")

    args = parser.parse_args()
    review_path = args.file or REVIEW_YAML

    if args.command == "add":
        return cmd_add(args, review_path)
    elif args.command == "update":
        return cmd_update(args, review_path)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
