"""Verify allocator kv_mode wiring is complete across every eval/profile entrypoint.

AST-only check: does not import the scripts, so it runs cleanly in environments
that lack heavy GPU deps (triton, fused kernels). This guards against *three*
execution-chain bugs that otherwise only surface at the first allocator job in a
smoke/main/ablation run:

1. Runner forwards ``--kv_mode int4_ours_asym_alloc`` but a downstream argparse
   rejects it with "invalid choice".
2. Runner forwards ``--policy_json <path>`` for every allocator job, but a
   downstream argparse never declared ``--policy_json`` and rejects with
   "unrecognized arguments".
3. Direct CLI users drop ``--decode_attn_impl torch_ref`` and a downstream
   script silently falls back to ``triton_fused`` → ``generate_from_ids`` raises
   ``ValueError`` at the first decode step. Every allocator-capable entrypoint
   must wire ``normalize_allocator_cli_args(args)`` after parse_args so
   the failure becomes an argparse-time mistake instead of a mid-run crash.

``eval_ppl.py`` is included here because ``run_system_vs_kivi.build_jobs()``
schedules it as a PPL aux entrypoint for allocator systems alongside
longbench/needle/ruler/latency/memory.
"""

from __future__ import annotations

import ast
from pathlib import Path


SCRIPT_NAMES = [
    "eval_longbench.py",
    "eval_needle.py",
    "eval_ppl.py",
    "eval_ruler.py",
    "profile_latency.py",
    "profile_memory.py",
]

REQUIRED_KV_MODE = "int4_ours_asym_alloc"
REQUIRED_FLAG = "--policy_json"
REQUIRED_NORMALIZER = "normalize_allocator_cli_args"


def _walk_add_argument_calls(tree: ast.AST):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "add_argument":
            yield node


def _first_positional_literal(call: ast.Call):
    positional = [a for a in call.args if not isinstance(a, ast.Starred)]
    if not positional:
        return None
    first = positional[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


def _collect_kv_mode_choices(tree: ast.AST):
    for call in _walk_add_argument_calls(tree):
        if _first_positional_literal(call) != "--kv_mode":
            continue
        for kw in call.keywords:
            if kw.arg == "choices" and isinstance(kw.value, (ast.List, ast.Tuple)):
                return {
                    elt.value
                    for elt in kw.value.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                }
    return None


def _declared_argument_flags(tree: ast.AST):
    flags = set()
    for call in _walk_add_argument_calls(tree):
        name = _first_positional_literal(call)
        if name is not None:
            flags.add(name)
    return flags


def _calls_named(tree: ast.AST, name: str) -> bool:
    """True if the tree contains any direct call to ``name(...)``."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == name:
            return True
    return False


def _parse(script_path: Path) -> ast.AST:
    return ast.parse(script_path.read_text(encoding="utf-8"), filename=str(script_path))


def test_allocator_kv_mode_is_registered_in_cli_parsers():
    project_root = Path(__file__).resolve().parents[1]
    scripts_dir = project_root / "scripts"

    per_script_choices: dict[str, set[str]] = {}
    missing: list[str] = []
    no_parser: list[str] = []
    for script_name in SCRIPT_NAMES:
        tree = _parse(scripts_dir / script_name)
        choices = _collect_kv_mode_choices(tree)
        if choices is None:
            no_parser.append(script_name)
            continue
        per_script_choices[script_name] = choices
        if REQUIRED_KV_MODE not in choices:
            missing.append(script_name)

    assert not no_parser, (
        f"Scripts missing --kv_mode add_argument call (parser regression): {no_parser}"
    )
    assert not missing, (
        f"Allocator kv_mode {REQUIRED_KV_MODE!r} not registered in CLI choices for: "
        f"{missing}. Current choices per script: {per_script_choices}"
    )


def test_policy_json_flag_is_registered_in_cli_parsers():
    """Runner appends --policy_json for every allocator job; every downstream
    script that is a valid allocator job entrypoint must declare this flag,
    otherwise argparse rejects with 'unrecognized arguments' and the allocator
    system dies on its first job."""
    project_root = Path(__file__).resolve().parents[1]
    scripts_dir = project_root / "scripts"

    missing: list[str] = []
    for script_name in SCRIPT_NAMES:
        tree = _parse(scripts_dir / script_name)
        flags = _declared_argument_flags(tree)
        if REQUIRED_FLAG not in flags:
            missing.append(script_name)

    assert not missing, (
        f"{REQUIRED_FLAG!r} is not declared in: {missing}. Runner appends this "
        f"flag for every allocator job; missing declarations cause argparse "
        f"'unrecognized arguments' failure on the first allocator run."
    )


def test_allocator_decode_attn_impl_normalizer_is_wired():
    """Every allocator-capable entrypoint must call
    ``normalize_allocator_cli_args(args)`` after parse_args so a
    missing ``--decode_attn_impl`` no longer silently falls back to
    ``triton_fused`` (which ``generate_from_ids`` rejects for allocator mode)."""
    project_root = Path(__file__).resolve().parents[1]
    scripts_dir = project_root / "scripts"

    missing: list[str] = []
    for script_name in SCRIPT_NAMES:
        tree = _parse(scripts_dir / script_name)
        if not _calls_named(tree, REQUIRED_NORMALIZER):
            missing.append(script_name)

    assert not missing, (
        f"{REQUIRED_NORMALIZER!r} is not invoked in: {missing}. Without it, "
        "direct CLI users of --kv_mode int4_ours_asym_alloc hit a runtime "
        "ValueError inside generate_from_ids instead of an argparse-time error."
    )


# --- Behavioral tests for normalize_allocator_cli_args itself --------
# config_utils.py only depends on stdlib + pyyaml, so these imports are safe
# even in environments that lack torch/triton.
import argparse
import pytest
from scripts.config_utils import normalize_allocator_cli_args


import warnings


def _allocator_args(**overrides):
    """Build a Namespace with allocator defaults and optional overrides."""
    base = dict(
        kv_mode="int4_ours_asym_alloc",
        decode_attn_impl=None,
        policy_json="/tmp/fake_policy.json",
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def test_normalize_fills_missing_decode_attn_impl_for_allocator():
    args = _allocator_args(decode_attn_impl=None)
    normalize_allocator_cli_args(args)
    assert args.decode_attn_impl == "torch_ref"


def test_normalize_accepts_explicit_torch_ref():
    args = _allocator_args(decode_attn_impl="torch_ref")
    normalize_allocator_cli_args(args)
    assert args.decode_attn_impl == "torch_ref"


def test_normalize_overrides_incompatible_backend_with_warning():
    """yaml kernel_defaults=triton_fused should be overridden with a warning,
    not a hard error, so config-driven allocator runs don't break."""
    args = _allocator_args(decode_attn_impl="triton_fused")
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        normalize_allocator_cli_args(args)
    assert args.decode_attn_impl == "torch_ref"
    assert any(
        issubclass(w.category, UserWarning) and "torch_ref" in str(w.message)
        for w in captured
    ), [str(w.message) for w in captured]


def test_normalize_raises_when_policy_json_missing_for_allocator():
    args = _allocator_args(policy_json=None)
    with pytest.raises(ValueError, match="policy_json"):
        normalize_allocator_cli_args(args)


def test_normalize_raises_when_policy_json_empty_string_for_allocator():
    args = _allocator_args(policy_json="")
    with pytest.raises(ValueError, match="policy_json"):
        normalize_allocator_cli_args(args)


def test_normalize_leaves_other_kv_modes_alone():
    # Non-allocator modes are untouched, even with no policy_json.
    args = argparse.Namespace(kv_mode="kivi_style", decode_attn_impl=None)
    normalize_allocator_cli_args(args)
    assert args.decode_attn_impl is None

    args = argparse.Namespace(kv_mode="int4_ours_asym", decode_attn_impl="triton_fused")
    normalize_allocator_cli_args(args)
    assert args.decode_attn_impl == "triton_fused"


def test_normalize_is_safe_when_kv_mode_missing():
    """Bare namespaces (kv_mode attr missing) short-circuit before any checks."""
    normalize_allocator_cli_args(argparse.Namespace())
