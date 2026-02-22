#!/usr/bin/env python3
"""
Week5: LongBench-style long-context evaluation.

This script supports three data sources:
- synthetic (default): deterministic synthetic QA tasks for offline reproducibility
- hf: attempt to load tasks from HuggingFace datasets
- jsonl: local JSONL file with fields context/question/answers/task

Outputs:
- profile_longbench_*.csv
- longbench_task_summary_*.csv
- longbench_details_*.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import string
import subprocess
import sys
import traceback
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

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
    get_hardware_info,
    set_seed,
    write_config_snapshot,
)

EXIT_OOM = 73
EXIT_EXCEPTION = 74
_LAST_ARGS: argparse.Namespace | None = None


@dataclass
class LongBenchSample:
    task_name: str
    context: str
    question: str
    answers: List[str]
    sample_id: str


def get_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=project_root,
        )
        return result.stdout.strip()[:8]
    except Exception:
        return "unknown"


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
        "longbench_source": str(getattr(args, "longbench_source", "")),
    }
    if exception is not None:
        payload["exception_type"] = type(exception).__name__
        payload["exception_repr"] = repr(exception)
        payload["traceback"] = traceback.format_exc()
    path = out_dir / f"task_failure_{Path(__file__).stem}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _split_csv(text: str | None) -> List[str]:
    if not text:
        return []
    return [x.strip() for x in str(text).split(",") if x.strip()]


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
    pred_counts: Dict[str, int] = defaultdict(int)
    truth_counts: Dict[str, int] = defaultdict(int)
    for tok in pred_tokens:
        pred_counts[tok] += 1
    for tok in truth_tokens:
        truth_counts[tok] += 1
    common = 0
    for tok, c in pred_counts.items():
        common += min(c, truth_counts.get(tok, 0))
    if common <= 0:
        return 0.0
    precision = common / max(1, len(pred_tokens))
    recall = common / max(1, len(truth_tokens))
    if precision + recall <= 0:
        return 0.0
    return (2.0 * precision * recall) / (precision + recall)


# ---------------------------------------------------------------------------
# Official LongBench metrics per task type
# ---------------------------------------------------------------------------
# Mapping follows THUDM/LongBench official evaluation protocol:
#   QA tasks → token-F1,  Summarization → Rouge-L,
#   Classification → Accuracy,  Code completion → Edit Similarity
TASK_OFFICIAL_METRIC: Dict[str, str] = {
    # QA → F1
    "narrativeqa": "f1",
    "qasper": "f1",
    "multifieldqa_en": "f1",
    "multifieldqa_zh": "f1",
    "hotpotqa": "f1",
    "2wikimqa": "f1",
    "musique": "f1",
    "triviaqa": "f1",
    # Chinese QA → Rouge-L (LongBench official uses Rouge-L for dureader)
    "dureader": "rouge_l",
    # Summarization → Rouge-L
    "gov_report": "rouge_l",
    "qmsum": "rouge_l",
    "multi_news": "rouge_l",
    "vcsum": "rouge_l",
    "samsum": "rouge_l",
    # Classification → Accuracy
    "trec": "accuracy",
    "lsht": "accuracy",
    "passage_count": "accuracy",
    "passage_retrieval_en": "accuracy",
    "passage_retrieval_zh": "accuracy",
    # Code → Edit Similarity
    "lcc": "edit_sim",
    "repobench-p": "edit_sim",
}


def _lcs_length(x: List[str], y: List[str]) -> int:
    """Longest Common Subsequence length via space-optimised DP."""
    m, n = len(x), len(y)
    if m == 0 or n == 0:
        return 0
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, [0] * (n + 1)
    return prev[n]


def _rouge_l(pred: str, truth: str) -> float:
    """Rouge-L F1 score based on token-level LCS."""
    pred_tokens = _normalize_text(pred).split()
    truth_tokens = _normalize_text(truth).split()
    if not pred_tokens and not truth_tokens:
        return 1.0
    if not pred_tokens or not truth_tokens:
        return 0.0
    lcs = _lcs_length(pred_tokens, truth_tokens)
    precision = lcs / len(pred_tokens)
    recall = lcs / len(truth_tokens)
    if precision + recall <= 0:
        return 0.0
    return (2.0 * precision * recall) / (precision + recall)


def _edit_similarity(pred: str, truth: str) -> float:
    """Edit similarity = 1 - normalised edit distance (character-level)."""
    pred_norm = _normalize_text(pred)
    truth_norm = _normalize_text(truth)
    if not pred_norm and not truth_norm:
        return 1.0
    if not pred_norm or not truth_norm:
        return 0.0
    m, n = len(pred_norm), len(truth_norm)
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        curr = [i] + [0] * n
        for j in range(1, n + 1):
            if pred_norm[i - 1] == truth_norm[j - 1]:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr
    return 1.0 - prev[n] / max(m, n)


def _classification_accuracy(pred: str, answers: Sequence[str]) -> float:
    """Classification accuracy: 1.0 if normalised prediction matches any answer."""
    pred_norm = _normalize_text(pred)
    for ans in answers:
        ans_norm = _normalize_text(ans)
        if ans_norm and (pred_norm == ans_norm or ans_norm in pred_norm):
            return 1.0
    return 0.0


def _compute_official_metric(
    pred: str, answers: Sequence[str], task_name: str
) -> tuple[str, float]:
    """Return (metric_name, score) using the LongBench official metric for *task_name*."""
    metric_name = TASK_OFFICIAL_METRIC.get(task_name, "f1")
    if not answers:
        return metric_name, 0.0
    if metric_name == "rouge_l":
        score = max((_rouge_l(pred, ans) for ans in answers), default=0.0)
    elif metric_name == "accuracy":
        score = _classification_accuracy(pred, answers)
    elif metric_name == "edit_sim":
        score = max((_edit_similarity(pred, ans) for ans in answers), default=0.0)
    else:  # "f1" or unknown → token-F1
        score = max((_token_f1(pred, ans) for ans in answers), default=0.0)
        metric_name = "f1"
    return metric_name, score


def _score_prediction(prediction: str, answers: Sequence[str]) -> Dict[str, float]:
    if not answers:
        return {"exact_match": 0.0, "contains_match": 0.0, "f1": 0.0}
    pred_norm = _normalize_text(prediction)
    em = 0.0
    contains = 0.0
    f1_best = 0.0
    for ans in answers:
        ans_norm = _normalize_text(ans)
        if pred_norm == ans_norm:
            em = 1.0
        if ans_norm and ans_norm in pred_norm:
            contains = 1.0
        f1_best = max(f1_best, _token_f1(prediction, ans))
    return {"exact_match": em, "contains_match": contains, "f1": f1_best}


def _truncate_prompt_ids(tokenizer, prompt: str, max_tokens: int) -> torch.Tensor:
    ids = tokenizer(prompt, add_special_tokens=False).input_ids
    if max_tokens > 0 and len(ids) > max_tokens:
        # Keep tail so the question/instruction remains visible.
        ids = ids[-max_tokens:]
    return torch.tensor([ids], dtype=torch.long)


def _synthetic_context(task_name: str, answer: str, depth: float) -> tuple[str, str]:
    noise = (
        "Historical logs describe unrelated events. "
        "Irrelevant entities repeat across timelines for robustness checks. "
    )
    lead = noise * 120
    tail = noise * 120
    anchor = (
        f"Task {task_name} reference fact: the requested canonical answer is {answer}. "
        "Use this fact to answer the final question. "
    )
    split = int(len(lead) * max(0.0, min(1.0, depth)))
    context = lead[:split] + anchor + lead[split:] + tail
    question = (
        f"For task {task_name}, provide exactly the canonical answer token. "
        "Return only the answer string."
    )
    return context, question


def _load_synthetic_samples(
    *,
    tasks: List[str],
    max_samples: int,
    seed: int,
) -> List[LongBenchSample]:
    rng = random.Random(seed)
    samples: List[LongBenchSample] = []
    if not tasks:
        tasks = ["narrativeqa", "dureader", "hotpotqa", "gov_report", "vcsum", "trec", "lcc"]
    for task in tasks:
        for idx in range(max_samples):
            answer = f"ans_{task}_{idx}_{rng.randint(1000,9999)}"
            depth = (idx % 10) / 10.0
            context, question = _synthetic_context(task, answer, depth)
            samples.append(
                LongBenchSample(
                    task_name=task,
                    context=context,
                    question=question,
                    answers=[answer],
                    sample_id=f"synthetic_{task}_{idx}",
                )
            )
    return samples


def _coerce_answers(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        v = value.strip()
        return [v] if v else []
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            if item is None:
                continue
            v = str(item).strip()
            if v:
                out.append(v)
        return out
    v = str(value).strip()
    return [v] if v else []


def _extract_generic_sample(row: Dict[str, object], fallback_task: str, sample_id: str) -> LongBenchSample | None:
    # LongBench standard format: "context" = long document, "input" = question/instruction.
    # Handle this pattern first before falling back to generic extraction.
    context = ""
    question = ""
    answers: List[str] = []

    ctx_val = row.get("context")
    inp_val = row.get("input")

    if isinstance(ctx_val, str) and ctx_val.strip() and isinstance(inp_val, str) and inp_val.strip():
        # LongBench pattern: context = document, input = question
        context = ctx_val
        question = inp_val
    elif isinstance(inp_val, str) and inp_val.strip():
        # Some tasks have no separate context; input contains everything
        context = inp_val
        question = "Based on the text above, provide the answer."
    else:
        # Generic fallback
        context_keys = ["context", "article", "passage", "document", "text", "input"]
        for k in context_keys:
            v = row.get(k)
            if isinstance(v, str) and v.strip():
                context = v
                break
        question_keys = ["question", "query", "instruction", "input"]
        for k in question_keys:
            if k == "input" and context:
                continue  # already used as context
            v = row.get(k)
            if isinstance(v, str) and v.strip():
                question = v
                break

    answer_keys = ["answers", "answer", "ground_truth", "label", "target"]
    for k in answer_keys:
        if k in row:
            answers = _coerce_answers(row.get(k))
            if answers:
                break

    if not context or not answers:
        return None
    if not question:
        question = "Based on the text above, provide the answer."

    task_name = str(row.get("task", row.get("task_name", fallback_task))).strip() or fallback_task
    return LongBenchSample(
        task_name=task_name,
        context=context,
        question=question,
        answers=answers,
        sample_id=sample_id,
    )


def _load_jsonl_samples(
    *,
    path: Path,
    tasks: List[str],
    max_samples: int,
) -> List[LongBenchSample]:
    if not path.exists():
        raise FileNotFoundError(f"longbench jsonl path not found: {path}")
    tasks_set = set(tasks)
    counts: Dict[str, int] = defaultdict(int)
    samples: List[LongBenchSample] = []

    # Determine file list: directory of per-task JSONL files, or a single file
    if path.is_dir():
        files_to_load: List[tuple] = []  # (filepath, task_name_override)
        for task in tasks:
            candidate = path / f"{task}.jsonl"
            if candidate.exists():
                files_to_load.append((candidate, task))
            else:
                logger.warning("JSONL file not found for task '%s' in %s", task, path)
        if not files_to_load:
            raise FileNotFoundError(
                f"No matching JSONL files found in {path} for tasks {tasks}"
            )
    else:
        files_to_load = [(path, None)]  # single file, infer task from content

    for filepath, task_override in files_to_load:
        with open(filepath, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, start=1):
                text = line.strip()
                if not text:
                    continue
                row = json.loads(text)
                if not isinstance(row, dict):
                    continue
                if task_override is not None:
                    task_name = task_override
                else:
                    task_name = str(
                        row.get("dataset", row.get("task", row.get("task_name", "generic")))
                    ).strip() or "generic"
                if tasks_set and task_name not in tasks_set:
                    continue
                if counts[task_name] >= max_samples:
                    continue
                sample = _extract_generic_sample(row, task_name, sample_id=f"jsonl_{task_name}_{line_idx}")
                if sample is None:
                    continue
                counts[task_name] += 1
                samples.append(sample)
    return samples


def _load_hf_samples(
    *,
    repo: str,
    split: str,
    tasks: List[str],
    max_samples: int,
) -> List[LongBenchSample]:
    try:
        from datasets import load_dataset  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("datasets package is required for longbench_source=hf") from exc

    if not tasks:
        tasks = ["narrativeqa", "dureader", "hotpotqa", "gov_report", "vcsum", "trec", "lcc"]

    samples: List[LongBenchSample] = []
    for task in tasks:
        loaded = None
        candidates = [
            {"path": repo, "name": task, "split": split},
            {"path": f"{repo}/{task}", "name": None, "split": split},
        ]
        for cand in candidates:
            try:
                loaded = load_dataset(cand["path"], cand["name"], split=cand["split"])
                break
            except Exception:
                continue
        if loaded is None:
            raise RuntimeError(
                f"Failed to load LongBench task '{task}' from repo='{repo}'."
            )

        kept = 0
        for idx, row in enumerate(loaded):
            sample = _extract_generic_sample(
                row if isinstance(row, dict) else {},
                fallback_task=task,
                sample_id=f"hf_{task}_{idx}",
            )
            if sample is None:
                continue
            samples.append(sample)
            kept += 1
            if kept >= max_samples:
                break
    return samples


def _build_prompt(sample: LongBenchSample) -> str:
    return (
        "You are a long-context QA assistant. Read the context and answer exactly.\n\n"
        f"Context:\n{sample.context}\n\n"
        f"Question:\n{sample.question}\n\n"
        "Answer:"
    )


def _load_samples(args: argparse.Namespace) -> List[LongBenchSample]:
    tasks = _split_csv(args.longbench_tasks)
    if args.longbench_source == "synthetic":
        return _load_synthetic_samples(
            tasks=tasks,
            max_samples=int(args.longbench_max_samples),
            seed=int(args.seed),
        )

    if args.longbench_source == "jsonl":
        if not args.longbench_dataset_path:
            raise ValueError("--longbench_dataset_path is required for longbench_source=jsonl")
        return _load_jsonl_samples(
            path=Path(args.longbench_dataset_path),
            tasks=tasks,
            max_samples=int(args.longbench_max_samples),
        )

    # hf
    try:
        return _load_hf_samples(
            repo=str(args.longbench_dataset_repo),
            split=str(args.longbench_dataset_split),
            tasks=tasks,
            max_samples=int(args.longbench_max_samples),
        )
    except Exception:
        if args.longbench_allow_synthetic_fallback:
            print("Warning: HF LongBench loading failed; fallback to synthetic source.")
            return _load_synthetic_samples(
                tasks=tasks,
                max_samples=int(args.longbench_max_samples),
                seed=int(args.seed),
            )
        raise


def main() -> None:
    global _LAST_ARGS
    parser = argparse.ArgumentParser(description="Week5: LongBench-style evaluation")
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
        ],
    )
    parser.add_argument("--model_id", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--model_revision", type=str, default=None)
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--run_name", type=str, default=None)

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
        "--use_attn_temperature",
        dest="use_attn_temperature",
        action="store_true",
        default=True,
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

    parser.add_argument("--longbench_source", type=str, default="synthetic", choices=["synthetic", "hf", "jsonl"])
    parser.add_argument("--longbench_tasks", type=str, default="")
    parser.add_argument("--longbench_dataset_repo", type=str, default="THUDM/LongBench")
    parser.add_argument("--longbench_dataset_split", type=str, default="test")
    parser.add_argument("--longbench_dataset_path", type=str, default="")
    parser.add_argument("--longbench_max_samples", type=int, default=32)
    parser.add_argument("--longbench_max_new_tokens", type=int, default=64)
    parser.add_argument("--longbench_context_len", type=int, default=None)
    parser.add_argument("--longbench_allow_synthetic_fallback", action="store_true", default=False)

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

    samples = _load_samples(args)
    if not samples:
        raise RuntimeError("No LongBench samples loaded. Check source/task filters.")

    max_context_len = int(args.longbench_context_len or args.seq_len)
    if max_context_len <= 0:
        raise ValueError("longbench_context_len/seq_len must be positive")

    timestamp = datetime.now().isoformat()
    git_commit = get_git_commit()
    hardware = get_hardware_info()
    out_dir = _resolve_out_dir(args.out_dir)

    details_rows: List[Dict[str, object]] = []
    task_scores: Dict[str, List[Dict[str, float]]] = defaultdict(list)
    ttft_vals: List[float] = []
    tpot_vals: List[float] = []
    tokps_vals: List[float] = []
    peak_mem_vals: List[float] = []

    for idx, sample in enumerate(samples):
        prompt = _build_prompt(sample)
        input_ids = _truncate_prompt_ids(tokenizer, prompt, max_context_len).to(model.device)
        attention_mask = torch.ones_like(input_ids, dtype=torch.long, device=model.device)

        out = generate_from_ids(
            model=model,
            tokenizer=tokenizer,
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=int(args.longbench_max_new_tokens),
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
            quant_bits=getattr(args, 'quant_bits', None),
        )

        pred_text = tokenizer.decode(out.generated_ids[0].tolist(), skip_special_tokens=True).strip()
        score = _score_prediction(pred_text, sample.answers)
        official_metric_name, official_metric_value = _compute_official_metric(
            pred_text, sample.answers, sample.task_name
        )
        score["official_metric_name"] = official_metric_name  # type: ignore[assignment]
        score["official_metric_value"] = official_metric_value

        details_rows.append(
            {
                "run_id": f"longbench_{timestamp}",
                "sample_index": idx,
                "sample_id": sample.sample_id,
                "task_name": sample.task_name,
                "kv_mode": args.kv_mode,
                "seq_len": int(input_ids.shape[1]),
                "gen_len": int(args.longbench_max_new_tokens),
                "prediction": pred_text,
                "answers": " || ".join(sample.answers),
                "exact_match": float(score["exact_match"]),
                "contains_match": float(score["contains_match"]),
                "f1": float(score["f1"]),
                "official_metric_name": str(official_metric_name),
                "official_metric_value": float(official_metric_value),
                "seed": int(args.seed),
                "replica_id": int(args.replica_id),
                "timestamp": timestamp,
                "git_commit": git_commit,
            }
        )
        task_scores[sample.task_name].append(score)

        ttft_vals.append(float(out.ttft_ms))
        tpot_vals.append(float(out.tpot_ms))
        tokps_vals.append(float(out.tok_per_s))
        peak_mem_vals.append(float(out.gpu_mem_peak_mb))

    task_rows: List[Dict[str, object]] = []
    em_macro = []
    contains_macro = []
    f1_macro = []
    official_macro: List[float] = []
    sample_total = 0

    for task_name in sorted(task_scores.keys()):
        vals = task_scores[task_name]
        sample_total += len(vals)
        em = float(np.mean([v["exact_match"] for v in vals]) * 100.0)
        contains = float(np.mean([v["contains_match"] for v in vals]) * 100.0)
        f1 = float(np.mean([v["f1"] for v in vals]) * 100.0)
        task_off_name = str(vals[0].get("official_metric_name", "f1"))
        task_off_val = float(np.mean([v["official_metric_value"] for v in vals]) * 100.0)
        em_macro.append(em)
        contains_macro.append(contains)
        f1_macro.append(f1)
        official_macro.append(task_off_val)
        task_rows.append(
            {
                "run_id": f"longbench_{timestamp}",
                "task_name": task_name,
                "kv_mode": args.kv_mode,
                "seq_len": int(max_context_len),
                "gen_len": int(args.longbench_max_new_tokens),
                "sample_count": len(vals),
                "exact_match_rate": round(em, 4),
                "contains_match_rate": round(contains, 4),
                "f1_mean": round(f1, 4),
                "official_metric_name": task_off_name,
                "official_metric_value": round(task_off_val, 4),
                "seed": int(args.seed),
                "replica_id": int(args.replica_id),
                "timestamp": timestamp,
                "git_commit": git_commit,
            }
        )

    quant_bits = getattr(args, 'quant_bits', None) or (4 if "int4" in args.kv_mode else (8 if "int8" in args.kv_mode else 16))

    summary_row = {
        "run_id": f"longbench_{timestamp}",
        "model_id": args.model_id,
        "run_name": args.run_name,
        "benchmark": "longbench",
        "longbench_source": args.longbench_source,
        "kv_mode": args.kv_mode,
        "quant_bits": quant_bits,
        "clip_percentile": args.clip_percentile,
        "group_size": args.group_size,
        "dtype": str(model.dtype),
        "hardware": f"{hardware['gpu']} ({hardware['gpu_memory']})",
        "seq_len": int(max_context_len),
        "gen_len": int(args.longbench_max_new_tokens),
        "batch": 1,
        "ttft_ms": round(float(np.mean(ttft_vals)), 4) if ttft_vals else 0.0,
        "tpot_ms": round(float(np.mean(tpot_vals)), 4) if tpot_vals else 0.0,
        "tok_per_s": round(float(np.mean(tokps_vals)), 4) if tokps_vals else 0.0,
        "gpu_mem_peak_mb": round(float(np.max(peak_mem_vals)), 2) if peak_mem_vals else 0.0,
        "timestamp": timestamp,
        "git_commit": git_commit,
        "seed": int(args.seed),
        "replica_id": int(args.replica_id),
        "longbench_task_count": int(len(task_rows)),
        "longbench_sample_count": int(sample_total),
        "longbench_em_macro": round(float(np.mean(em_macro)) if em_macro else 0.0, 4),
        "longbench_contains_macro": round(float(np.mean(contains_macro)) if contains_macro else 0.0, 4),
        "longbench_f1_macro": round(float(np.mean(f1_macro)) if f1_macro else 0.0, 4),
        "longbench_official_macro": round(float(np.mean(official_macro)) if official_macro else 0.0, 4),
        "longbench_score": round(float(np.mean(official_macro)) if official_macro else 0.0, 4),
    }

    if args.save_csv:
        profile_path = out_dir / f"profile_longbench_{args.kv_mode}_{timestamp.replace(':','-')}.csv"
        profile_fields = list(summary_row.keys())
        with open(profile_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=profile_fields)
            writer.writeheader()
            writer.writerow(summary_row)

        task_path = out_dir / f"longbench_task_summary_{args.kv_mode}_{timestamp.replace(':','-')}.csv"
        if task_rows:
            with open(task_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(task_rows[0].keys()))
                writer.writeheader()
                writer.writerows(task_rows)

        detail_path = out_dir / f"longbench_details_{args.kv_mode}_{timestamp.replace(':','-')}.csv"
        if details_rows:
            with open(detail_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(details_rows[0].keys()))
                writer.writeheader()
                writer.writerows(details_rows)

        print(f"Saved to {profile_path}")
        if task_rows:
            print(f"Saved to {task_path}")
        if details_rows:
            print(f"Saved to {detail_path}")

    run_snapshot_dir = out_dir / summary_row["run_id"]
    snapshot = build_config_snapshot(
        script_name=Path(__file__).name,
        args=args,
        extra={
            "longbench_source": args.longbench_source,
            "longbench_tasks": _split_csv(args.longbench_tasks),
            "longbench_task_count": int(len(task_rows)),
            "longbench_sample_count": int(sample_total),
        },
    )
    write_config_snapshot(str(run_snapshot_dir), snapshot)


if __name__ == "__main__":
    try:
        main()
    except torch.cuda.OutOfMemoryError as exc:
        print("OOM")
        if _LAST_ARGS is not None:
            _write_task_failure(
                args=_LAST_ARGS,
                failure_type="oom",
                message="CUDA out of memory during eval_longbench execution.",
                exception=exc,
            )
        sys.exit(EXIT_OOM)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {type(exc).__name__}: {exc}")
        if _LAST_ARGS is not None:
            _write_task_failure(
                args=_LAST_ARGS,
                failure_type="exception",
                message="Unhandled exception during eval_longbench execution.",
                exception=exc,
            )
        sys.exit(EXIT_EXCEPTION)
