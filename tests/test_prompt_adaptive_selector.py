import json
from pathlib import Path

import pytest

from scripts.adaptive.build_prompt_policy_pool import build_policy_pool
from scripts.adaptive.export_prompt_selector import build_selector, resolve_policy_entry


def _touch_json(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"policy_name": path.stem}), encoding="utf-8")


def test_build_policy_pool_and_resolve_selector(tmp_path: Path):
    fixed = tmp_path / "fixed.json"
    heuristic = tmp_path / "heuristic.json"
    auto = tmp_path / "auto.json"
    role = tmp_path / "role.json"
    for item in (fixed, heuristic, auto, role):
        _touch_json(item)

    pool = build_policy_pool(
        model_key="7b",
        project_root=tmp_path,
        fixed_k_policy=str(fixed),
        heuristic_policy=str(heuristic),
        auto_k_policy=str(auto),
        role_aware_policy=str(role),
    )
    assert [item["policy_id"] for item in pool["policies"]] == [
        "fixed_k",
        "heuristic",
        "auto_k",
        "role_aware",
    ]

    selector = build_selector(
        pool=pool,
        task_routes={"narrativeqa": "fixed_k", "gov_report": "auto_k"},
        profile_routes={"default": "auto_k"},
        default_policy_id="auto_k",
    )
    assert resolve_policy_entry(selector, "narrativeqa")["policy_id"] == "fixed_k"
    assert resolve_policy_entry(selector, "gov_report")["policy_id"] == "auto_k"
    with pytest.raises(KeyError, match="unknown task_id"):
        resolve_policy_entry(selector, "unknown_task")
    with pytest.raises(KeyError, match="unknown profile_bucket"):
        resolve_policy_entry(selector, "narrativeqa", profile_bucket="unknown")


def test_selector_rejects_unknown_policy_id(tmp_path: Path):
    fixed = tmp_path / "fixed.json"
    auto = tmp_path / "auto.json"
    heuristic = tmp_path / "heuristic.json"
    for item in (fixed, auto, heuristic):
        _touch_json(item)

    pool = build_policy_pool(
        model_key="7b",
        project_root=tmp_path,
        fixed_k_policy=str(fixed),
        heuristic_policy=str(heuristic),
        auto_k_policy=str(auto),
        role_aware_policy=None,
    )
    with pytest.raises(ValueError, match="unknown policy_id"):
        build_selector(
            pool=pool,
            task_routes={"narrativeqa": "does_not_exist"},
            profile_routes={"default": "auto_k"},
            default_policy_id="auto_k",
        )
