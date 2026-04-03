#!/usr/bin/env python3
"""
RULER-style long-context evaluation with 4 subtask categories.

Implements the four core RULER task types (Hsieh et al., 2024):
  - S-NIAH: Single Needle-in-a-Haystack (retrieval of one passkey)
  - MK-NIAH: Multi-Key NIAH (retrieval of multiple key-value pairs)
  - VT: Variable Tracking (multi-hop variable assignment chains)
  - CWE: Common Words Extraction (frequency-based aggregation)

Each task generates deterministic synthetic cases controlled by seed.
Context length is filled with distractor noise to hit the target token budget.

Outputs:
- profile_ruler_*.csv       (summary: ruler_score = macro accuracy across tasks)
- ruler_task_summary_*.csv  (per-task metrics)
- ruler_depth_summary_*.csv (per-depth-ratio metrics, backward compatible)
- ruler_details_*.csv       (per-case predictions)
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import string
import sys
import traceback
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from scripts.config_utils import load_config, normalize_kv_params, resolve_run_config
from src.engine.generate_loop import generate_from_ids
from src.utils.hf import resolve_pretrained_path
from src.utils.repro import (
    build_config_snapshot,
    get_git_commit,  # QUA-001: centralized
    get_hardware_info,
    resolve_quant_bits,
    set_seed,
    write_config_snapshot,
)

EXIT_OOM = 73
EXIT_EXCEPTION = 74
_LAST_ARGS: argparse.Namespace | None = None

RULER_TASKS = ["s_niah", "mk_niah", "vt", "cwe"]

# ---------------------------------------------------------------------------
# Truncation strategy constants for _truncate_prompt_ids()
# ---------------------------------------------------------------------------
# When a prompt exceeds the token budget, we preserve a small tail portion
# (the question/instruction) and fill the rest with the context prefix.
# TRUNCATION_TAIL_MAX: absolute upper bound on tail tokens to keep.
# TRUNCATION_TAIL_RATIO: fraction of total budget allocated to the tail.
# Effective tail size = min(TRUNCATION_TAIL_MAX, budget * TRUNCATION_TAIL_RATIO).
TRUNCATION_TAIL_MAX: int = 128
TRUNCATION_TAIL_RATIO: float = 1.0 / 8.0

# ---------------------------------------------------------------------------
# Noise generation
# ---------------------------------------------------------------------------

_NOISE_SENTENCES = [
    "The conference proceedings include detailed reports on unrelated topics.",
    "Historical archives document various administrative decisions from prior eras.",
    "Metadata streams contain references to entities outside the current scope.",
    "Background information discusses organizational policies and routine updates.",
    "Statistical summaries from previous quarters are included for reference.",
    "External audit findings pertain to compliance matters unrelated to this query.",
    "Supplementary records describe infrastructure changes from past fiscal years.",
    "Meeting minutes cover agenda items that are not relevant to the question.",
]


def _build_noise_block(
    rng: random.Random,
    tokenizer,
    target_tokens: int,
) -> str:
    """Build a block of noise text that is approximately *target_tokens* long."""
    if target_tokens <= 0:
        return ""
    lines: List[str] = []
    total_tok = 0
    while total_tok < target_tokens:
        line = rng.choice(_NOISE_SENTENCES)
        line_tok = len(tokenizer(line, add_special_tokens=False).input_ids)
        lines.append(line)
        total_tok += line_tok
    return "\n".join(lines)


def _count_tokens(tokenizer, text: str) -> int:
    return len(tokenizer(text, add_special_tokens=False).input_ids)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RulerCase:
    task_name: str
    case_id: str
    depth_ratio: float
    context: str
    question: str
    expected_answers: List[str]
    metadata: Dict[str, object] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    text = str(text).strip().lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text)
    return text


def _token_f1(pred: str, truth: str) -> float:
    pred_tokens = _normalize_text(pred).split()
    truth_tokens = _normalize_text(truth).split()
    if not pred_tokens and not truth_tokens:
        return 1.0
    if not pred_tokens or not truth_tokens:
        return 0.0
    pred_counts: Dict[str, int] = Counter(pred_tokens)
    truth_counts: Dict[str, int] = Counter(truth_tokens)
    common = 0
    for tok, c in pred_counts.items():
        common += min(c, truth_counts.get(tok, 0))
    if common <= 0:
        return 0.0
    precision = common / len(pred_tokens)
    recall = common / len(truth_tokens)
    if precision + recall <= 0:
        return 0.0
    return (2.0 * precision * recall) / (precision + recall)


def _score_single_answer(prediction: str, answer: str) -> Dict[str, float]:
    """Score for tasks with a single expected answer (S-NIAH, VT)."""
    pred_norm = _normalize_text(prediction)
    ans_norm = _normalize_text(answer)
    exact = 1.0 if pred_norm == ans_norm else 0.0
    contains = 1.0 if ans_norm and ans_norm in pred_norm else 0.0
    f1 = _token_f1(prediction, answer)
    return {"exact_match": exact, "contains_match": contains, "f1": f1}


def _score_multi_answer(prediction: str, answers: List[str]) -> Dict[str, float]:
    """Score for tasks with multiple expected answers (MK-NIAH).

    Each answer is checked independently; metrics are micro-averaged.
    """
    if not answers:
        return {"exact_match": 0.0, "contains_match": 0.0, "f1": 0.0}
    pred_norm = _normalize_text(prediction)
    hits_contains = 0
    f1_sum = 0.0
    for ans in answers:
        ans_norm = _normalize_text(ans)
        if ans_norm and ans_norm in pred_norm:
            hits_contains += 1
        f1_sum += _token_f1(prediction, ans)
    n = len(answers)
    # Check if ALL answers are present (strict multi-key exact match)
    all_present = all(
        _normalize_text(a) in pred_norm for a in answers if _normalize_text(a)
    )
    return {
        "exact_match": 1.0 if all_present else 0.0,
        "contains_match": hits_contains / n,
        "f1": f1_sum / n,
    }


def _score_set_answer(prediction: str, answers: List[str]) -> Dict[str, float]:
    """Score for set-matching tasks (CWE).

    Extracts words from prediction, computes set overlap with expected answers.
    EVL-075 FIX: Use set for recall (truth coverage) but count total predicted
    words for precision denominator (penalizes repetition and noise).
    """
    pred_tokens = [w for w in _normalize_text(prediction).split() if w]
    pred_unique = set(pred_tokens)
    truth_words = set(_normalize_text(a) for a in answers if _normalize_text(a))
    if not truth_words:
        return {"exact_match": 0.0, "contains_match": 0.0, "f1": 0.0}
    intersection = pred_unique & truth_words
    if not intersection:
        return {"exact_match": 0.0, "contains_match": 0.0, "f1": 0.0}
    # Precision: fraction of predicted tokens that are in truth (penalizes noise/repetition)
    precision = sum(1 for w in pred_tokens if w in truth_words) / max(1, len(pred_tokens))
    recall = len(intersection) / len(truth_words)
    f1 = (2.0 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    # EVL-032: CWE exact_match checks recall==1.0 (all truth words in pred),
    # which is intentionally more lenient than other tasks' full string match.
    # This is the standard CWE evaluation approach per the RULER benchmark.
    exact = 1.0 if intersection == truth_words else 0.0
    contains = recall  # fraction of truth words found
    return {"exact_match": exact, "contains_match": contains, "f1": f1}


def _score_case(case: RulerCase, prediction: str) -> Dict[str, float]:
    """Dispatch scoring based on task type."""
    if case.task_name == "cwe":
        return _score_set_answer(prediction, case.expected_answers)
    if case.task_name == "mk_niah":
        return _score_multi_answer(prediction, case.expected_answers)
    # EVL-121 FIX: VT always uses _score_multi_answer even for single-chain.
    # _score_single_answer uses strict exact_match which penalises VT unfairly
    # when the model wraps the correct value in extra text (e.g. "The value is
    # v_abc123").  _score_multi_answer checks contains_match per answer, which
    # is the appropriate primary metric for retrieval tasks.
    if case.task_name == "vt":
        return _score_multi_answer(prediction, case.expected_answers)
    # s_niah: single expected answer
    return _score_single_answer(prediction, case.expected_answers[0])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _random_token(rng: random.Random, prefix: str, n: int = 8) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    suffix = "".join(rng.choice(alphabet) for _ in range(max(4, int(n))))
    return f"{prefix}_{suffix}"


def _parse_depth_ratios(text: str) -> List[float]:
    out: List[float] = []
    for item in str(text).split(","):
        item = item.strip()
        if not item:
            continue
        ratio = float(item)
        ratio = max(0.0, min(1.0, ratio))
        out.append(ratio)
    if not out:
        out = [0.1, 0.5, 0.9]
    return out


def _parse_tasks(text: str) -> List[str]:
    if not text:
        return list(RULER_TASKS)
    tasks = [t.strip().lower() for t in str(text).split(",") if t.strip()]
    for t in tasks:
        if t not in RULER_TASKS:
            raise ValueError(
                f"Unknown RULER task '{t}'. Valid: {RULER_TASKS}"
            )
    return tasks


def _embed_payload_in_noise(
    *,
    tokenizer,
    rng: random.Random,
    payload_text: str,
    depth_ratio: float,
    context_len: int,
) -> str:
    """Embed payload_text at depth_ratio position within noise of context_len tokens."""
    payload_tokens = _count_tokens(tokenizer, payload_text)
    noise_budget = max(0, context_len - payload_tokens - 50)
    noise_before_budget = int(round(noise_budget * depth_ratio))
    noise_after_budget = noise_budget - noise_before_budget

    noise_before = _build_noise_block(rng, tokenizer, noise_before_budget)
    noise_after = _build_noise_block(rng, tokenizer, noise_after_budget)

    parts = [p for p in [noise_before, payload_text, noise_after] if p]
    return "\n\n".join(parts)


def _embed_multiple_payloads(
    *,
    tokenizer,
    rng: random.Random,
    payloads: List[Tuple[str, float]],
    context_len: int,
) -> str:
    """Embed multiple (payload_text, depth_ratio) pairs at scattered positions.

    EVL-048 FIX: Each payload is placed at its own depth position within a
    shared noise context, matching the RULER paper convention of scattering
    needles at different depths rather than packing them at a single location.

    Algorithm: sort payloads by depth_ratio, then partition the noise budget
    into segments separated by the payloads.  Each payload lands at its
    designated fractional position.
    """
    if not payloads:
        return _build_noise_block(rng, tokenizer, context_len)

    # Sort by depth so we can lay them out left-to-right
    sorted_payloads = sorted(payloads, key=lambda x: x[1])

    total_payload_tokens = sum(
        _count_tokens(tokenizer, p) for p, _ in sorted_payloads
    )
    noise_budget = max(0, context_len - total_payload_tokens - 50)

    # Partition noise into len(payloads)+1 segments based on depth_ratios.
    # depth_ratio=0.0 means start, 1.0 means end.
    # Segment boundaries: 0.0, d0, d1, ..., dN, 1.0
    # Noise before payload_i gets budget proportional to its gap from previous.
    boundaries = [0.0] + [d for _, d in sorted_payloads] + [1.0]
    gaps = [boundaries[i + 1] - boundaries[i] for i in range(len(boundaries) - 1)]
    gap_total = sum(gaps)
    if gap_total <= 0:
        # All at same depth; distribute noise evenly
        segment_budgets = [noise_budget // (len(gaps))] * len(gaps)
    else:
        segment_budgets = [int(round(noise_budget * g / gap_total)) for g in gaps]

    # Build the context: noise_0, payload_0, noise_1, payload_1, ..., noise_N
    parts: List[str] = []
    for i, (payload_text, _depth) in enumerate(sorted_payloads):
        noise_seg = _build_noise_block(rng, tokenizer, segment_budgets[i])
        if noise_seg:
            parts.append(noise_seg)
        parts.append(payload_text)
    # Final trailing noise segment
    trailing = _build_noise_block(rng, tokenizer, segment_budgets[-1])
    if trailing:
        parts.append(trailing)

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Task generators
# ---------------------------------------------------------------------------

def _build_s_niah_cases(
    *,
    num_cases: int,
    depth_ratios: List[float],
    context_len: int,
    tokenizer,
    rng: random.Random,
) -> List[RulerCase]:
    """S-NIAH: Single Needle-in-a-Haystack.

    A random passkey (magic number) is embedded in noise at a given depth.
    The model must retrieve the passkey.
    """
    cases: List[RulerCase] = []
    for idx in range(num_cases):
        ratio = depth_ratios[idx % len(depth_ratios)]
        passkey = str(rng.randint(100000, 999999))
        payload = (
            f"The special magic number is: {passkey}. "
            "Remember this number for later retrieval."
        )
        context = _embed_payload_in_noise(
            tokenizer=tokenizer,
            rng=rng,
            payload_text=payload,
            depth_ratio=ratio,
            context_len=context_len,
        )
        question = (
            "What is the special magic number mentioned in the provided text? "
            "Output only the number, nothing else."
        )
        cases.append(RulerCase(
            task_name="s_niah",
            case_id=f"s_niah_{idx:05d}",
            depth_ratio=ratio,
            context=context,
            question=question,
            expected_answers=[passkey],
            metadata={"passkey": passkey},
        ))
    return cases


def _build_mk_niah_cases(
    *,
    num_cases: int,
    depth_ratios: List[float],
    context_len: int,
    num_keys: int,
    tokenizer,
    rng: random.Random,
) -> List[RulerCase]:
    """MK-NIAH: Multi-Key Needle-in-a-Haystack.

    EVL-048 FIX: Each key-value pair is embedded at a different depth position,
    matching the RULER paper convention of scattering multiple needles across
    the context rather than packing them at a single location.
    """
    if num_keys <= 0:
        raise ValueError(f"num_keys must be >= 1, got {num_keys}")
    cases: List[RulerCase] = []
    for idx in range(num_cases):
        base_ratio = depth_ratios[idx % len(depth_ratios)]
        pairs: List[Tuple[str, str]] = []
        for k_idx in range(num_keys):
            key = f"KEY_{idx:04d}_{k_idx:02d}"
            value = _random_token(rng, prefix="val", n=6)
            pairs.append((key, value))

        # EVL-048: Scatter pairs around base_ratio, respecting --ruler_depth_ratios.
        # Spread is symmetric around base_ratio, clamped to [0.05, 0.95].
        base_ratio = max(0.05, min(0.95, base_ratio))  # clamp to safe range
        if num_keys == 1:
            pair_depths = [base_ratio]
        else:
            max_spread = max(0.0, min(base_ratio - 0.05, 0.95 - base_ratio, 0.40))
            pair_depths = [
                max(0.05, min(0.95,
                    base_ratio + max_spread * (2.0 * k_idx / (num_keys - 1) - 1.0)))
                for k_idx in range(num_keys)
            ]
        # Build (payload, depth) tuples for _embed_multiple_payloads
        payload_depth_pairs: List[Tuple[str, float]] = []
        for (k, v), depth in zip(pairs, pair_depths):
            payload_depth_pairs.append(
                (f"Important record: {k} = {v}.", depth)
            )

        context = _embed_multiple_payloads(
            tokenizer=tokenizer,
            rng=rng,
            payloads=payload_depth_pairs,
            context_len=context_len,
        )
        key_names = ", ".join(k for k, _ in pairs)
        question = (
            f"From the text above, retrieve the values for: {key_names}. "
            "List all values separated by semicolons, in order. "
            "Output only the values, nothing else."
        )
        expected = [v for _, v in pairs]
        # depth_ratio for the case record: use statistical median
        sorted_depths = sorted(pair_depths)
        n = len(sorted_depths)
        median_depth = float(
            (sorted_depths[n // 2 - 1] + sorted_depths[n // 2]) / 2.0
            if n % 2 == 0 else sorted_depths[n // 2]
        )
        cases.append(RulerCase(
            task_name="mk_niah",
            case_id=f"mk_niah_{idx:05d}",
            depth_ratio=median_depth,
            context=context,
            question=question,
            expected_answers=expected,
            metadata={"num_keys": num_keys, "pairs": pairs,
                       "pair_depths": pair_depths},
        ))
    return cases


def _build_vt_cases(
    *,
    num_cases: int,
    depth_ratios: List[float],
    context_len: int,
    num_chains: int,
    num_hops: int,
    tokenizer,
    rng: random.Random,
) -> List[RulerCase]:
    """VT: Variable Tracking (multi-hop variable assignment chains).

    Creates assignment chains: X0 = VALUE; X1 = X0; X2 = X1; ... XN = X_{N-1}.
    The model must determine the final value of XN.
    """
    cases: List[RulerCase] = []
    for idx in range(num_cases):
        ratio = depth_ratios[idx % len(depth_ratios)]
        chains_text: List[str] = []
        final_vars: List[str] = []
        final_values: List[str] = []

        for chain_idx in range(num_chains):
            # EVL-072 FIX: Randomise variable name prefix per chain so that
            # the model cannot exploit a fixed pattern (e.g. C0_VAR_0..C0_VAR_4)
            # to shortcut the variable-tracking task.
            rand_letter = rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            rand_num = rng.randint(0, 99)
            prefix = f"{rand_letter}{rand_num}"
            value = _random_token(rng, prefix="v", n=6)
            var_names = [f"{prefix}_VAR_{h}" for h in range(num_hops + 1)]
            assignments: List[str] = []
            assignments.append(f"{var_names[0]} = {value}")
            for h in range(1, num_hops + 1):
                assignments.append(f"{var_names[h]} = {var_names[h - 1]}")
            chains_text.append("; ".join(assignments) + ".")
            final_vars.append(var_names[-1])
            final_values.append(value)

        payload = "\n".join(chains_text)
        context = _embed_payload_in_noise(
            tokenizer=tokenizer,
            rng=rng,
            payload_text=payload,
            depth_ratio=ratio,
            context_len=context_len,
        )
        if num_chains == 1:
            question = (
                f"Given the variable assignments in the text above, "
                f"what is the value of {final_vars[0]}? "
                "Output only the value, nothing else."
            )
        else:
            var_list = ", ".join(final_vars)
            question = (
                f"Given the variable assignments in the text above, "
                f"what are the values of {var_list}? "
                "List the values separated by semicolons, in order. "
                "Output only the values, nothing else."
            )

        cases.append(RulerCase(
            task_name="vt",
            case_id=f"vt_{idx:05d}",
            depth_ratio=ratio,
            context=context,
            question=question,
            expected_answers=final_values,
            metadata={
                "num_chains": num_chains,
                "num_hops": num_hops,
                "final_vars": final_vars,
            },
        ))
    return cases


def _build_cwe_cases(
    *,
    num_cases: int,
    depth_ratios: List[float],
    context_len: int,
    freq_cw: int,
    num_cw: int,
    tokenizer,
    rng: random.Random,
) -> List[RulerCase]:
    """CWE: Common Words Extraction.

    Generates a long word list where certain target words appear with high
    frequency. The model must identify the top-N most frequent words.
    """
    # Word pool: common English words (avoid stop words)
    word_pool = [
        "apple", "bridge", "castle", "dragon", "eagle", "falcon", "garden",
        "harbor", "island", "jungle", "knight", "lantern", "marble", "nectar",
        "oracle", "palace", "quartz", "ribbon", "silver", "throne", "umbrella",
        "violet", "walrus", "zenith", "beacon", "cipher", "delta", "ember",
        "frost", "glacier", "herald", "ivory", "jasper", "karma", "lotus",
        "meadow", "nimbus", "opal", "prism", "quill", "raven", "summit",
        "timber", "ultra", "venom", "whisper", "yarn", "zephyr", "anchor",
    ]

    cases: List[RulerCase] = []
    for idx in range(num_cases):
        ratio = depth_ratios[idx % len(depth_ratios)]
        available = list(word_pool)
        rng.shuffle(available)
        target_words = available[:num_cw]
        distractor_words = available[num_cw: num_cw + 20]
        if not distractor_words:
            distractor_words = available[num_cw:]

        # Build word list: target words appear freq_cw times, distractors
        # appear much less frequently.
        # EVL-047 FIX: Padding uses target words (not distractors) to ensure
        # target words remain the most frequent throughout.
        all_words: List[str] = []
        for w in target_words:
            all_words.extend([w] * freq_cw)
        for w in distractor_words:
            all_words.extend([w] * rng.randint(1, 3))

        # Pad to fill context — use a MIX that maintains target dominance.
        # EVL-074 FIX: Use _count_tokens for accurate budget instead of // 2.
        words_text = " ".join(all_words)
        words_tokens = _count_tokens(tokenizer, words_text)
        extra_budget = max(0, context_len - words_tokens - 200)
        if extra_budget > 0:
            # Estimate tokens per word (~1.3 for BPE) with safety margin
            extra_words_count = int(extra_budget / 1.5)
            # Split padding: 70% target words (maintain dominance), 30% distractors
            n_target_pad = int(extra_words_count * 0.7)
            n_distractor_pad = extra_words_count - n_target_pad
            for _ in range(n_target_pad):
                all_words.append(rng.choice(target_words))
            for _ in range(n_distractor_pad):
                all_words.append(rng.choice(distractor_words))

        rng.shuffle(all_words)
        payload = "Word list:\n" + " ".join(all_words)

        context = _embed_payload_in_noise(
            tokenizer=tokenizer,
            rng=rng,
            payload_text=payload,
            depth_ratio=ratio,
            context_len=context_len,
        )
        question = (
            f"From the word list in the text above, identify the {num_cw} "
            "most frequently occurring words. "
            "List them separated by commas. Output only the words, nothing else."
        )
        cases.append(RulerCase(
            task_name="cwe",
            case_id=f"cwe_{idx:05d}",
            depth_ratio=ratio,
            context=context,
            question=question,
            expected_answers=target_words,
            metadata={"freq_cw": freq_cw, "num_cw": num_cw},
        ))
    return cases


# ---------------------------------------------------------------------------
# Prompt & inference helpers
# ---------------------------------------------------------------------------

def _build_prompt(case: RulerCase) -> str:
    return (
        "You are a precise information extraction assistant.\n"
        "Read the context carefully and answer exactly as instructed.\n\n"
        f"Context:\n{case.context}\n\n"
        f"Question:\n{case.question}\n\n"
        "Answer:"
    )


def _truncate_prompt_ids(
    tokenizer, prompt: str, max_tokens: int
) -> Tuple[torch.Tensor, bool]:
    ids = tokenizer(prompt, add_special_tokens=False).input_ids
    truncated = False
    if max_tokens > 0 and len(ids) > max_tokens:
        # Keep most of the context prefix while preserving a small question tail.
        # This avoids dropping the entire haystack (right-keep truncation) when
        # prompts slightly exceed the context budget.
        tail_keep = min(TRUNCATION_TAIL_MAX, int(max_tokens * TRUNCATION_TAIL_RATIO))
        head_keep = max_tokens - tail_keep
        if head_keep <= 0:
            ids = ids[:max_tokens]
        elif tail_keep == 0:  # EVL-076: ids[-0:] returns all, guard against it
            ids = ids[:head_keep]
        else:
            ids = ids[:head_keep] + ids[-tail_keep:]
        truncated = True
    return torch.tensor([ids], dtype=torch.long), truncated


def _effective_prompt_budget(
    *,
    requested_context_len: int,
    seq_len: int,
    gen_tokens_case: int,
    max_model_len: int,
) -> Tuple[int, int]:
    """Return (effective_prompt_budget, base_total_budget).

    EVL-079 FIX: Use gen_tokens_case (the actual per-case generation budget,
    e.g. cwe_max_tokens=128 for CWE) instead of the global gen_len for both
    base_total_budget and the prompt budget subtraction.  Previously CWE used
    gen_len=64 for the total budget but subtracted cwe_max_tokens=128, making
    the effective prompt budget 64 tokens too small.
    """
    base_total_budget = min(int(seq_len) + int(gen_tokens_case), int(max_model_len))
    effective_prompt_budget = min(
        int(requested_context_len),
        int(base_total_budget) - int(gen_tokens_case),
    )
    return int(effective_prompt_budget), int(base_total_budget)


# ---------------------------------------------------------------------------
# Utility: git / paths / failure handling
# ---------------------------------------------------------------------------

def _resolve_out_dir(out_dir_arg: str) -> Path:
    out_dir = Path(out_dir_arg)
    if not out_dir.is_absolute():
        out_dir = project_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _write_task_failure(
    *,
    args: argparse.Namespace,
    failure_type: str,
    message: str,
    exception: Exception | None = None,
) -> None:
    # SEC-004: Traceback/paths in failure JSON are intentional (research CLI tool).
    out_dir = _resolve_out_dir(args.out_dir)
    payload = {
        "script": Path(__file__).name,
        "timestamp": datetime.now().isoformat(),
        "failure_type": str(failure_type),
        "message": str(message),
        "kv_mode": str(getattr(args, "kv_mode", "")),
        "run_name": str(getattr(args, "run_name", "")),
        "seed": int(getattr(args, "seed", 0)),
        "replica_id": int(getattr(args, "replica_id", 0)),
        "seq_len": int(getattr(args, "seq_len", 0) or 0),
        "ruler_num_cases": int(getattr(args, "ruler_num_cases", 0) or 0),
    }
    if exception is not None:
        payload["exception_type"] = type(exception).__name__
        payload["exception_repr"] = repr(exception)
        payload["traceback"] = traceback.format_exc()
    path = out_dir / f"task_failure_{Path(__file__).stem}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    global _LAST_ARGS
    parser = argparse.ArgumentParser(
        description="RULER-style long-context evaluation (4 subtasks)"
    )
    parser.add_argument("--seq_len", type=int, default=4096)
    parser.add_argument("--gen_len", type=int, default=64)
    parser.add_argument(
        "--kv_mode",
        type=str,
        default="fp16",
        choices=[
            "fp16",
            "int8_baseline",
            "int8_fused",
            "int8_ours",
            "int4_baseline",
            "int4_fused",
            "int4_ours",
            "int4_ours_mixed",
            "kivi_style",
            "int4_kivi_aligned",
            "int4_mixed_kv",
            "int4_ours_asym",
            "int4_ours_asym_ba",
        ],
    )
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--model_revision", type=str, default=None)
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--run_name", type=str, default=None)

    # Quantization args
    parser.add_argument("--group_size", type=int, default=128)
    parser.add_argument("--clip_percentile", type=float, default=99.9)
    parser.add_argument("--group_size_k", type=int, default=None)
    parser.add_argument("--group_size_v", type=int, default=None)
    parser.add_argument("--clip_percentile_k", type=float, default=None)
    parser.add_argument("--clip_percentile_v", type=float, default=None)
    parser.add_argument("--calib_strategy", type=str, default=None)
    parser.add_argument("--decode_attn_impl", type=str, default=None)
    parser.add_argument("--calib_file", type=str, default=None)
    parser.add_argument(
        "--quant_bits",
        type=int,
        default=None,
        help="Override quant_bits for CSV output (needed for kivi_style which can be 4 or 8).",
    )
    parser.add_argument(
        "--k_bits",
        type=int,
        default=None,
        help="K cache bit-width for int4_mixed_kv mode (4/8/16). Default: 8.",
    )
    parser.add_argument(
        "--v_bits",
        type=int,
        default=None,
        help="V cache bit-width for int4_mixed_kv mode (4/8/16). Default: 4.",
    )
    parser.add_argument(
        "--use_attn_temperature",
        dest="use_attn_temperature",
        action="store_true",
        default=False,  # EVL-078 FIX: project mainline uses False
    )
    parser.add_argument(
        "--no_use_attn_temperature",
        dest="use_attn_temperature",
        action="store_false",
    )
    parser.add_argument(
        "--use_static_scales",
        dest="use_static_scales",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--no_use_static_scales",
        dest="use_static_scales",
        action="store_false",
    )
    parser.add_argument(
        "--adaptive_static_scales",
        dest="adaptive_static_scales",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--no_adaptive_static_scales",
        dest="adaptive_static_scales",
        action="store_false",
    )
    parser.add_argument("--adaptive_static_margin", type=float, default=1.0)
    parser.add_argument(
        "--adaptive_static_k",
        dest="adaptive_static_k",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--no_adaptive_static_k",
        dest="adaptive_static_k",
        action="store_false",
    )
    parser.add_argument(
        "--adaptive_static_v",
        dest="adaptive_static_v",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--no_adaptive_static_v",
        dest="adaptive_static_v",
        action="store_false",
    )

    # RULER task params (backward compatible + new)
    parser.add_argument("--ruler_num_cases", type=int, default=64,
                        help="Total cases PER TASK.")
    parser.add_argument("--ruler_num_kv_pairs", type=int, default=256,
                        help="(Legacy/S-NIAH compat) Not used by new impl; "
                             "kept for backward compat with run_experiments.py.")
    parser.add_argument("--ruler_depth_ratios", type=str, default="0.1,0.5,0.9")
    parser.add_argument("--ruler_max_new_tokens", type=int, default=32)
    parser.add_argument("--ruler_context_len", type=int, default=None)
    parser.add_argument("--ruler_tasks", type=str, default=None,
                        help="Comma-separated RULER subtasks to run. "
                             "Default: s_niah,mk_niah,vt,cwe")
    # MK-NIAH params
    parser.add_argument("--ruler_mk_num_keys", type=int, default=4,
                        help="Number of keys for MK-NIAH task.")
    # VT params
    parser.add_argument("--ruler_vt_num_chains", type=int, default=1,
                        help="Number of variable chains for VT task.")
    parser.add_argument("--ruler_vt_num_hops", type=int, default=4,
                        help="Number of hops per chain for VT task.")
    # CWE params
    parser.add_argument("--ruler_cwe_freq", type=int, default=30,
                        help="Frequency of target words in CWE task.")
    parser.add_argument("--ruler_cwe_num_words", type=int, default=10,
                        help="Number of target words to identify in CWE task.")

    parser.add_argument("--save_csv", action="store_true", default=True)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--replica_id", type=int, default=0)
    parser.add_argument("--out_dir", type=str, default="results/runs")

    args = parser.parse_args()
    _LAST_ARGS = args

    if args.config and args.run_name:
        cfg = load_config(args.config)
        resolved = resolve_run_config(cfg, args.run_name)
        for key, value in resolved.items():
            if value is not None:
                setattr(args, key, value)

    normalize_kv_params(args)
    set_seed(seed=args.seed, deterministic=True)
    runtime_quant_bits = (
        resolve_quant_bits(args.kv_mode, getattr(args, "quant_bits", None))
        if args.kv_mode == "kivi_style"
        else getattr(args, "quant_bits", None)
    )

    tasks = _parse_tasks(args.ruler_tasks)
    depth_ratios = _parse_depth_ratios(args.ruler_depth_ratios)
    context_len = int(args.ruler_context_len or args.seq_len)
    if context_len <= 0:
        raise ValueError("ruler_context_len/seq_len must be positive")
    num_cases = int(args.ruler_num_cases)
    if num_cases <= 0:
        raise ValueError("ruler_num_cases must be positive")

    print(f"Loading {args.model_id}...")
    model_path = resolve_pretrained_path(args.model_id, revision=args.model_revision)
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, revision=args.model_revision, trust_remote_code=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto",
        revision=args.model_revision,
        trust_remote_code=True,
    )
    model.eval()
    max_model_len = int(getattr(model.config, "max_position_embeddings", 32768) or 32768)
    print(f"Resolved max_position_embeddings={max_model_len}")

    # ---- Generate cases for each task ----
    all_cases: List[RulerCase] = []
    rng = random.Random(int(args.seed))
    failed_task_count = 0  # EVL-049: track task generation failures

    for task_name in tasks:
        try:
            if task_name == "s_niah":
                all_cases.extend(_build_s_niah_cases(
                    num_cases=num_cases,
                    depth_ratios=depth_ratios,
                    context_len=context_len,
                    tokenizer=tokenizer,
                    rng=rng,
                ))
            elif task_name == "mk_niah":
                all_cases.extend(_build_mk_niah_cases(
                    num_cases=num_cases,
                    depth_ratios=depth_ratios,
                    context_len=context_len,
                    num_keys=int(args.ruler_mk_num_keys),
                    tokenizer=tokenizer,
                    rng=rng,
                ))
            elif task_name == "vt":
                all_cases.extend(_build_vt_cases(
                    num_cases=num_cases,
                    depth_ratios=depth_ratios,
                    context_len=context_len,
                    num_chains=int(args.ruler_vt_num_chains),
                    num_hops=int(args.ruler_vt_num_hops),
                    tokenizer=tokenizer,
                    rng=rng,
                ))
            elif task_name == "cwe":
                all_cases.extend(_build_cwe_cases(
                    num_cases=num_cases,
                    depth_ratios=depth_ratios,
                    context_len=context_len,
                    freq_cw=int(args.ruler_cwe_freq),
                    num_cw=int(args.ruler_cwe_num_words),
                    tokenizer=tokenizer,
                    rng=rng,
                ))
        except Exception as exc:  # noqa: BLE001
            failed_task_count += 1
            print(
                f"  [WARN] Case generation failed for task '{task_name}': "
                f"{type(exc).__name__}: {exc}. Skipping this task."
            )

    if failed_task_count > 0:
        print(
            f"  [WARN] {failed_task_count}/{len(tasks)} task(s) failed "
            f"during case generation."
        )
    if not all_cases:
        raise RuntimeError(
            f"No RULER cases generated. "
            f"{failed_task_count}/{len(tasks)} task(s) failed during generation."
        )

    print(f"Generated {len(all_cases)} RULER cases across tasks: {tasks}")

    timestamp = datetime.now().isoformat()
    git_commit = get_git_commit()
    hardware = get_hardware_info()
    out_dir = _resolve_out_dir(args.out_dir)

    # ---- Run inference and score ----
    details_rows: List[Dict[str, object]] = []
    # Per-task scores
    task_scores: Dict[str, List[Dict[str, float]]] = defaultdict(list)
    # Per-depth scores (backward compatible)
    depth_scores: Dict[float, List[Dict[str, float]]] = defaultdict(list)
    ttft_vals: List[float] = []
    tpot_vals: List[float] = []
    tokps_vals: List[float] = []
    peak_mem_vals: List[float] = []

    max_new_tokens = int(args.ruler_max_new_tokens)
    # CWE needs more tokens to list words
    cwe_max_tokens = max(max_new_tokens, 128)
    case_total = int(len(all_cases))
    case_success_count = 0
    case_error_count = 0
    # Initialise base_total_budget; updated per-case inside the loop via
    # _effective_prompt_budget(). The initial value is used only for the
    # summary row if all cases error out (guarded by the success check below).
    base_total_budget = min(int(args.seq_len) + int(args.gen_len), max_model_len)

    for idx, case in enumerate(all_cases):
        prompt = _build_prompt(case)
        gen_tokens = cwe_max_tokens if case.task_name == "cwe" else max_new_tokens
        effective_prompt_budget, base_total_budget = _effective_prompt_budget(
            requested_context_len=int(context_len),
            seq_len=int(args.seq_len),
            gen_tokens_case=int(gen_tokens),
            max_model_len=int(max_model_len),
        )
        try:
            if effective_prompt_budget <= 0:
                raise ValueError(
                    "effective prompt budget is non-positive: "
                    f"requested_context_len={context_len}, seq_len={args.seq_len}, "
                    f"gen_len={args.gen_len}, gen_tokens_case={gen_tokens}, "
                    f"max_model_len={max_model_len}"
                )

            input_ids, input_truncated = _truncate_prompt_ids(
                tokenizer, prompt, effective_prompt_budget
            )
            input_ids = input_ids.to(model.device)
            attention_mask = torch.ones_like(
                input_ids, dtype=torch.long, device=model.device
            )

            out = generate_from_ids(
                model=model,
                tokenizer=tokenizer,
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=gen_tokens,
                kv_mode=args.kv_mode,
                group_size=args.group_size,
                clip_percentile=args.clip_percentile,
                seed=args.seed,
                calib_file=args.calib_file,
                use_attn_temperature=args.use_attn_temperature,
                use_static_scales=args.use_static_scales,
                adaptive_static_scales=args.adaptive_static_scales,
                adaptive_static_margin=args.adaptive_static_margin,
                adaptive_static_k=args.adaptive_static_k,
                adaptive_static_v=args.adaptive_static_v,
                decode_attn_impl=args.decode_attn_impl or "triton_fused",
                stop_on_eos=True,
                quant_bits=runtime_quant_bits,
                k_bits=getattr(args, 'k_bits', None),
                v_bits=getattr(args, 'v_bits', None),
            )

            pred_text = tokenizer.decode(
                out.generated_ids[0].tolist(), skip_special_tokens=True
            ).strip()
            score = _score_case(case, pred_text)
            task_scores[case.task_name].append(score)
            depth_scores[case.depth_ratio].append(score)
            case_success_count += 1

            details_rows.append(
                {
                    "run_id": f"ruler_{timestamp}",
                    "case_index": idx,
                    "case_id": case.case_id,
                    "ruler_task": case.task_name,
                    "kv_mode": args.kv_mode,
                    "seq_len": int(input_ids.shape[1]),
                    "gen_len": gen_tokens,
                    "depth_ratio": float(case.depth_ratio),
                    "expected": ";".join(case.expected_answers),
                    "prediction": pred_text,
                    "exact_match": float(score["exact_match"]),
                    "contains_match": float(score["contains_match"]),
                    "f1": float(score["f1"]),
                    "input_truncated": bool(input_truncated),
                    "requested_context_len": int(context_len),
                    "effective_prompt_budget": int(effective_prompt_budget),
                    "base_total_budget": int(base_total_budget),
                    "max_model_len": int(max_model_len),
                    "case_status": "success",
                    "case_error_type": "",
                    "case_error_msg": "",
                    "seed": int(args.seed),
                    "replica_id": int(args.replica_id),
                    "timestamp": timestamp,
                    "git_commit": git_commit,
                }
            )

            ttft_vals.append(float(out.ttft_ms))
            tpot_vals.append(float(out.tpot_ms))
            tokps_vals.append(float(out.tok_per_s))
            peak_mem_vals.append(float(out.gpu_mem_peak_mb))

            if (idx + 1) % 10 == 0 or idx == len(all_cases) - 1:
                print(
                    f"  [{idx + 1}/{len(all_cases)}] {case.task_name} "
                    f"em={score['exact_match']:.0f} f1={score['f1']:.2f} "
                    f"errors={case_error_count}"
                )
        except torch.cuda.OutOfMemoryError:
            # EVL-123: OOM must propagate, not be silently counted as case error
            raise
        except Exception as exc:  # noqa: BLE001
            case_error_count += 1
            print(
                f"  [WARN] case failed idx={idx + 1}/{len(all_cases)} "
                f"task={case.task_name} type={type(exc).__name__}: {exc}"
            )
            details_rows.append(
                {
                    "run_id": f"ruler_{timestamp}",
                    "case_index": idx,
                    "case_id": case.case_id,
                    "ruler_task": case.task_name,
                    "kv_mode": args.kv_mode,
                    "seq_len": np.nan,
                    "gen_len": gen_tokens,
                    "depth_ratio": float(case.depth_ratio),
                    "expected": ";".join(case.expected_answers),
                    "prediction": "",
                    "exact_match": np.nan,
                    "contains_match": np.nan,
                    "f1": np.nan,
                    "input_truncated": np.nan,
                    "requested_context_len": int(context_len),
                    "effective_prompt_budget": int(effective_prompt_budget),
                    "base_total_budget": int(base_total_budget),
                    "max_model_len": int(max_model_len),
                    "case_status": "error",
                    "case_error_type": type(exc).__name__,
                    "case_error_msg": str(exc),
                    "seed": int(args.seed),
                    "replica_id": int(args.replica_id),
                    "timestamp": timestamp,
                    "git_commit": git_commit,
                }
            )

    if case_success_count <= 0:
        raise RuntimeError(
            "All RULER cases failed; no valid samples to aggregate. "
            f"case_total={case_total} case_error_count={case_error_count}"
        )
    # EVL-124: warn + exit non-zero if error rate is high but not 100%
    error_rate = case_error_count / max(case_total, 1)
    if error_rate > 0.3:
        print(
            f"  [WARN] High case error rate: {error_rate:.1%} "
            f"({case_error_count}/{case_total}). Results may be unreliable."
        )

    # ---- Aggregate per-task ----
    task_rows: List[Dict[str, object]] = []
    task_contains_rates: List[float] = []  # EVL-070: primary metric = contains_match
    task_exact_rates: List[float] = []     # secondary metric = exact_match (strict)
    task_f1_scores: List[float] = []       # EVL-081: task-level F1 for consistent aggregation

    for task_name in tasks:
        vals = task_scores.get(task_name, [])
        if not vals:
            continue
        # Use nanmean defensively: if a scoring function ever returns NaN
        # (e.g. edge-case inputs), individual NaN values are ignored rather
        # than poisoning the entire task aggregate.
        exact_rate = float(np.nanmean([v["exact_match"] for v in vals]) * 100.0)
        contains_rate = float(np.nanmean([v["contains_match"] for v in vals]) * 100.0)
        f1_mean = float(np.nanmean([v["f1"] for v in vals]) * 100.0)
        task_contains_rates.append(contains_rate)
        task_exact_rates.append(exact_rate)
        task_f1_scores.append(f1_mean)
        task_rows.append(
            {
                "run_id": f"ruler_{timestamp}",
                "kv_mode": args.kv_mode,
                "seq_len": int(context_len),
                "ruler_task": task_name,
                "sample_count": int(len(vals)),
                "ruler_pass_rate": round(contains_rate, 4),  # EVL-070: primary=contains
                "ruler_exact_rate": round(exact_rate, 4),
                "ruler_contains_rate": round(contains_rate, 4),
                "ruler_f1_mean": round(f1_mean, 4),
                "seed": int(args.seed),
                "replica_id": int(args.replica_id),
                "timestamp": timestamp,
                "git_commit": git_commit,
            }
        )

    # ---- Aggregate per-depth (backward compatible) ----
    depth_rows: List[Dict[str, object]] = []
    depth_exact_rates: List[float] = []
    depth_contains_rates: List[float] = []
    depth_f1_scores: List[float] = []

    for depth_ratio in sorted(depth_scores.keys()):
        vals = depth_scores[depth_ratio]
        exact_rate = float(np.nanmean([v["exact_match"] for v in vals]) * 100.0)
        contains_rate = float(np.nanmean([v["contains_match"] for v in vals]) * 100.0)
        f1_mean = float(np.nanmean([v["f1"] for v in vals]) * 100.0)
        depth_exact_rates.append(exact_rate)
        depth_contains_rates.append(contains_rate)
        depth_f1_scores.append(f1_mean)
        depth_rows.append(
            {
                "run_id": f"ruler_{timestamp}",
                "kv_mode": args.kv_mode,
                "seq_len": int(context_len),
                "gen_len": int(max_new_tokens),
                "depth_ratio": float(depth_ratio),
                "sample_count": int(len(vals)),
                "ruler_pass_rate": round(contains_rate, 4),  # EVL-070: primary=contains
                "ruler_exact_rate": round(exact_rate, 4),
                "ruler_contains_rate": round(contains_rate, 4),
                "ruler_f1_mean": round(f1_mean, 4),
                "seed": int(args.seed),
                "replica_id": int(args.replica_id),
                "timestamp": timestamp,
                "git_commit": git_commit,
            }
        )

    # ---- Summary row (backward compatible schema) ----
    quant_bits = resolve_quant_bits(args.kv_mode, getattr(args, "quant_bits", None))

    # EVL-026: Aggregation dimension note — overall_pass_rate uses a task-level
    # MACRO average (mean of per-task pass rates), not a case-level MICRO
    # average (mean over all individual cases).
    #
    # Design rationale:
    #   - MACRO average gives each RULER subtask (s_niah, mk_niah, vt, cwe)
    #     equal weight in the summary score regardless of how many cases were
    #     generated per task.  This matches the RULER paper's reporting
    #     convention where task categories are balanced contributors.
    #   - MICRO average would give implicit extra weight to tasks that have more
    #     cases (e.g. if task sizes differ due to filtering or case errors).
    #
    # Consequence: when tasks have unequal sample counts (e.g. after case
    # errors that drop some tasks), overall_pass_rate reflects task-balance
    # rather than raw case-count balance.  Downstream consumers that require
    # micro-averaged accuracy should compute it from ruler_details_*.csv
    # (case_status=="success" rows) directly.
    #
    # EVL-081 FIX: All overall_* metrics now use task-level macro average
    # (mean of per-task scores) for semantic consistency.  Previously
    # overall_f1 and overall_contains used depth-level macro average while
    # overall_pass_rate used task-level, causing inconsistent aggregation.
    # EVL-070: primary metric switched from exact_match to contains_match.
    # exact_match is too strict for S-NIAH (model outputs "The magic number
    # is 123456" but exact requires just "123456"), causing systematic 0%.
    overall_pass_rate = round(
        float(np.mean(task_contains_rates)) if task_contains_rates else 0.0, 4
    )
    overall_exact_rate = round(
        float(np.mean(task_exact_rates)) if task_exact_rates else 0.0, 4
    )
    overall_f1 = round(
        float(np.mean(task_f1_scores)) if task_f1_scores else 0.0, 4
    )
    overall_contains = round(
        float(np.mean(task_contains_rates)) if task_contains_rates else 0.0, 4
    )

    summary_row = {
        "run_id": f"ruler_{timestamp}",
        "model_id": args.model_id,
        "run_name": args.run_name,
        "benchmark": "ruler",
        "kv_mode": args.kv_mode,
        "quant_bits": quant_bits,
        "clip_percentile": args.clip_percentile,
        "group_size": args.group_size,
        "dtype": str(model.dtype),
        "hardware": f"{hardware['gpu']} ({hardware['gpu_memory']})",
        "seq_len": int(context_len),
        "gen_len": int(max_new_tokens),
        "batch": 1,
        "ttft_ms": round(float(np.mean(ttft_vals)), 4) if ttft_vals else 0.0,
        "tpot_ms": round(float(np.mean(tpot_vals)), 4) if tpot_vals else 0.0,
        "tok_per_s": round(float(np.mean(tokps_vals)), 4) if tokps_vals else 0.0,
        "gpu_mem_peak_mb": round(float(np.max(peak_mem_vals)), 2) if peak_mem_vals else 0.0,
        "timestamp": timestamp,
        "git_commit": git_commit,
        "seed": int(args.seed),
        "replica_id": int(args.replica_id),
        "ruler_num_cases": int(args.ruler_num_cases),
        "ruler_num_kv_pairs": int(getattr(args, "ruler_num_kv_pairs", 0) or 0),
        "ruler_depth_count": int(len(depth_rows)),
        "requested_context_len": int(context_len),
        "base_total_budget": int(base_total_budget),
        "max_model_len": int(max_model_len),
        "case_total": int(case_total),
        "case_success_count": int(case_success_count),
        "case_error_count": int(case_error_count),
        "case_error_rate": round(float(case_error_count / max(case_total, 1)), 6),
        "ruler_tasks": ",".join(tasks),
        "ruler_pass_rate": overall_pass_rate,       # EVL-070: now uses contains_match
        "ruler_exact_rate": overall_exact_rate,      # strict exact_match (reference)
        "ruler_contains_rate": overall_contains,
        "ruler_f1_mean": overall_f1,
        "ruler_score": overall_pass_rate,            # same as ruler_pass_rate
    }

    # ---- Write CSVs ----
    if args.save_csv:
        stamp = timestamp.replace(":", "-")

        profile_path = out_dir / f"profile_ruler_{args.kv_mode}_{stamp}.csv"
        with open(profile_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_row.keys()))
            writer.writeheader()
            writer.writerow(summary_row)

        depth_path = out_dir / f"ruler_depth_summary_{args.kv_mode}_{stamp}.csv"
        if depth_rows:
            with open(depth_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(depth_rows[0].keys()))
                writer.writeheader()
                writer.writerows(depth_rows)

        task_path = out_dir / f"ruler_task_summary_{args.kv_mode}_{stamp}.csv"
        if task_rows:
            with open(task_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(task_rows[0].keys()))
                writer.writeheader()
                writer.writerows(task_rows)

        details_path = out_dir / f"ruler_details_{args.kv_mode}_{stamp}.csv"
        if details_rows:
            with open(details_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(details_rows[0].keys()))
                writer.writeheader()
                writer.writerows(details_rows)

        print(f"Saved summary: {profile_path}")
        if depth_rows:
            print(f"Saved depth:   {depth_path}")
        if task_rows:
            print(f"Saved tasks:   {task_path}")
        if details_rows:
            print(f"Saved details: {details_path}")

    # ---- Config snapshot ----
    run_snapshot_dir = out_dir / summary_row["run_id"]
    snapshot = build_config_snapshot(
        script_name=Path(__file__).name,
        args=args,
        extra={
            "ruler_tasks": tasks,
            "ruler_num_cases": int(args.ruler_num_cases),
            "ruler_depth_ratios": depth_ratios,
            "ruler_depth_count": int(len(depth_rows)),
            "ruler_mk_num_keys": int(args.ruler_mk_num_keys),
            "ruler_vt_num_chains": int(args.ruler_vt_num_chains),
            "ruler_vt_num_hops": int(args.ruler_vt_num_hops),
            "ruler_cwe_freq": int(args.ruler_cwe_freq),
            "ruler_cwe_num_words": int(args.ruler_cwe_num_words),
        },
    )
    write_config_snapshot(str(run_snapshot_dir), snapshot)

    # ---- Print summary ----
    print(f"\n{'='*60}")
    print(f"RULER Summary: {args.kv_mode} @ {context_len} tokens")
    print(f"  Tasks: {', '.join(tasks)}")
    for tr in task_rows:
        print(f"  {tr['ruler_task']:10s}: pass={tr['ruler_pass_rate']:6.2f}%  "
              f"f1={tr['ruler_f1_mean']:6.2f}%")
    print(f"  {'OVERALL':10s}: pass={overall_pass_rate:6.2f}%  "
          f"f1={overall_f1:6.2f}%")
    print(f"{'='*60}")


if __name__ == "__main__":
    try:
        main()
    except torch.cuda.OutOfMemoryError as exc:
        print("OOM")
        if _LAST_ARGS is not None:
            _write_task_failure(
                args=_LAST_ARGS,
                failure_type="oom",
                message="CUDA out of memory during eval_ruler execution.",
                exception=exc,
            )
        sys.exit(EXIT_OOM)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {type(exc).__name__}: {exc}")
        if _LAST_ARGS is not None:
            _write_task_failure(
                args=_LAST_ARGS,
                failure_type="exception",
                message="Unhandled exception during eval_ruler execution.",
                exception=exc,
            )
        sys.exit(EXIT_EXCEPTION)
