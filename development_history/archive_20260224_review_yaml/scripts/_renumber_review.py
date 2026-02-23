#!/usr/bin/env python3
"""One-shot script: renumber review issues from section-based (A-1..AG-3)
to module-based (CAL-001..TST-018). Reads from archived review.yaml."""
from __future__ import annotations

import datetime
import sys
from collections import defaultdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
YAML_PATH = REPO / "development_history/archive_20260224_review_yaml/review.yaml"
OUTPUT = REPO / "review_tracker.md"

# --- Module definitions ---
# (code, display_name, primary_file)
MODULES = {
    "CAL": ("校准模块", "scripts/calibrate_behavior.py"),
    "KVC": ("KV Cache", "src/cache/"),
    "QNT": ("量化模块", "src/quant/"),
    "ENG": ("引擎模块", "src/engine/"),
    "EVL": ("评测脚本", "scripts/eval_*.py"),
    "CFG": ("配置", "configs/"),
    "RUN": ("实验运行", "scripts/run_experiments.py"),
    "AGG": ("聚合", "scripts/aggregate_results.py"),
    "EXP": ("导出/报告", "scripts/export_*.py"),
    "PRF": ("性能分析", "scripts/profile_*.py"),
    "CHK": ("完整性检查", "scripts/check_run_completeness.py"),
    "TST": ("测试覆盖", "tests/"),
}

# Section → module mapping (default, covers most issues)
SECTION_TO_MODULE = {
    "A": "CAL", "AA": "CAL",
    "B": "KVC", "V": "KVC", "X": "KVC",
    "C": "QNT", "Y": "QNT",
    "D": "ENG", "K": "ENG", "U": "ENG",
    "E": "EVL", "O": "EVL", "Q": "EVL", "AG": "EVL",
    "F": "CFG", "G": "CFG", "I": "CFG", "W": "CFG",
    "L": "RUN", "S": "RUN",
    "M": "AGG", "AB": "AGG",
    "H": "EXP", "AC": "EXP",
    "R": "PRF", "AD": "PRF",
    "T": "CHK",
    "P": "TST", "AE": "TST",
}

# Per-issue overrides for cross-cutting sections (AF, J, Z)
ISSUE_TO_MODULE = {
    "AF-1": "EVL",   # eval_longbench.py
    "AF-2": "ENG",   # patch_model.py
    "AF-3": "CAL",   # calibrate_behavior.py MSE clamping
    "AF-4": "QNT",   # _resolve_quant_bits() DRY
    "AF-5": "PRF",   # profile_memory.py
    "AF-6": "EVL",   # eval_ruler.py
    "AF-7": "ENG",   # generate_loop.py
    "AF-8": "KVC",   # kivi_style_cache.py
    "AF-9": "CFG",   # final_emnlp2026_v1.yaml
    "AF-10": "KVC",  # kivi_style_cache.py
    "J-1": "CAL",    # calibrate_behavior.py
    "J-2": "CAL",    # calibrate_behavior.py MSE clamping
    "J-3": "EVL",    # eval_longbench.py logger
    "Z-1": "RUN",    # 消融实验覆盖
    "Z-2": "CHK",    # 验证未确认
    "Z-3": "RUN",    # 消融 output dir 命名
}

SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
SEV_SHORT = {"CRITICAL": "CRIT", "HIGH": "HIGH", "MEDIUM": "MED", "LOW": "LOW"}


def get_module(old_id: str, issue: dict) -> str:
    if old_id in ISSUE_TO_MODULE:
        return ISSUE_TO_MODULE[old_id]
    sec = issue.get("audit", {}).get("section", "?")
    return SECTION_TO_MODULE.get(sec, "TST")


def main():
    with open(YAML_PATH) as f:
        data = yaml.safe_load(f)

    issues = data["issues"]

    # Group by new module
    module_issues: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for old_id, issue in issues.items():
        mod = get_module(old_id, issue)
        module_issues[mod].append((old_id, issue))

    # Sort within each module: severity first, then old ID
    for mod in module_issues:
        module_issues[mod].sort(key=lambda x: (
            SEV_ORDER.get(x[1].get("severity", "LOW"), 9),
            x[0]
        ))

    # Assign new IDs
    id_map = {}  # old_id -> new_id
    all_new = []  # (new_id, old_id, issue, module)
    for mod in sorted(MODULES.keys()):
        for idx, (old_id, issue) in enumerate(module_issues.get(mod, []), 1):
            new_id = f"{mod}-{idx:03d}"
            id_map[old_id] = new_id
            all_new.append((new_id, old_id, issue, mod))

    # Stats
    total = len(all_new)
    open_count = sum(1 for _, _, i, _ in all_new if i["status"] == "open")
    fixed_count = sum(1 for _, _, i, _ in all_new if i["status"] == "fixed")
    fp_count = sum(1 for _, _, i, _ in all_new if i["status"] == "false_positive")

    open_by_sev = defaultdict(int)
    for _, _, i, _ in all_new:
        if i["status"] == "open":
            open_by_sev[i["severity"]] += 1

    sev_parts = []
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        c = open_by_sev.get(sev, 0)
        if c > 0:
            sev_parts.append(f"{c} {SEV_SHORT[sev]}")

    res_parts = []
    if fixed_count: res_parts.append(f"{fixed_count} fixed")
    if fp_count: res_parts.append(f"{fp_count} false_positive")

    # Identify blockers
    blockers = [nid for nid, _, i, _ in all_new
                if i["status"] == "open" and i["severity"] == "CRITICAL"
                and i.get("confidence", "MEDIUM") in ("HIGH", "MEDIUM")]

    phase_status = "BLOCKED" if blockers else "CLEAR"
    now = datetime.datetime.now().strftime("%Y-%m-%d")

    # --- Build markdown ---
    lines = []
    lines.append("# Code Review Tracker")
    lines.append("")
    lines.append(f"> {total} issues | {' + '.join(res_parts)} | {open_count} open ({', '.join(sev_parts)})")
    lines.append(f"> Phase Gate: **{phase_status}** — {', '.join(blockers) if blockers else 'none'}")
    lines.append(f"> Last updated: {now}")
    lines.append("")
    lines.append("---")
    lines.append("")

    def issue_line(new_id, old_id, issue):
        sev = SEV_SHORT.get(issue["severity"], issue["severity"])
        status = issue["status"]
        cb = "x" if status != "open" else " "
        title = issue["title"]
        if len(title) > 150:
            title = title[:147] + "..."
        line = f"- [{cb}] **{new_id}** `[{sev}]` {title}"
        if status == "fixed":
            commit = (issue.get("resolution") or {}).get("commit", "")
            line += f" — fixed commit {commit}" if commit else " — fixed"
        elif status == "false_positive":
            line += " — false_positive"
        return line

    # Phase Blockers: modules that contain CRITICAL open issues
    blocker_mods = set()
    for nid, oid, issue, mod in all_new:
        if issue["status"] == "open" and issue["severity"] == "CRITICAL":
            blocker_mods.add(mod)

    lines.append("## Phase Blockers (CRITICAL open)")
    lines.append("")
    if not blocker_mods:
        lines.append("*No CRITICAL open issues. Phase gate is CLEAR.*")
        lines.append("")
    else:
        for mod in sorted(blocker_mods):
            name, file = MODULES[mod]
            lines.append(f"### {mod}. {name} — `{file}`")
            lines.append("")
            open_in_mod = [(nid, oid, i) for nid, oid, i, m in all_new
                           if m == mod and i["status"] == "open"]
            for nid, oid, issue in open_in_mod:
                lines.append(issue_line(nid, oid, issue))
            lines.append("")

    lines.append("---")
    lines.append("")

    # Open Issues: non-blocker modules with open issues
    lines.append("## Open Issues")
    lines.append("")
    for mod in sorted(MODULES.keys()):
        if mod in blocker_mods:
            continue
        open_in_mod = [(nid, oid, i) for nid, oid, i, m in all_new
                       if m == mod and i["status"] == "open"]
        if not open_in_mod:
            continue
        name, file = MODULES[mod]
        lines.append(f"### {mod}. {name} — `{file}`")
        for nid, oid, issue in open_in_mod:
            lines.append(issue_line(nid, oid, issue))
        lines.append("")

    lines.append("---")
    lines.append("")

    # Resolved (folded)
    lines.append("## Resolved")
    lines.append("")
    lines.append("<details>")
    lines.append(f"<summary>{' + '.join(res_parts)} (click to expand)</summary>")
    lines.append("")
    for mod in sorted(MODULES.keys()):
        resolved = [(nid, oid, i) for nid, oid, i, m in all_new
                     if m == mod and i["status"] != "open"]
        if not resolved:
            continue
        name, _ = MODULES[mod]
        lines.append(f"### {mod}. {name}")
        for nid, oid, issue in resolved:
            lines.append(issue_line(nid, oid, issue))
        lines.append("")
    lines.append("</details>")
    lines.append("")

    content = "\n".join(lines)
    with open(OUTPUT, "w") as f:
        f.write(content)

    print(f"Wrote {content.count(chr(10))} lines to {OUTPUT}")
    print(f"Total: {total}, Open: {open_count}, Fixed: {fixed_count}, FP: {fp_count}")
    print(f"Modules: {len(MODULES)}")
    print(f"Blockers: {blockers}")

    # Print ID mapping for reference
    print("\n--- ID Mapping (old → new) ---")
    for old_id in sorted(id_map, key=lambda x: id_map[x]):
        print(f"  {old_id:8s} → {id_map[old_id]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
