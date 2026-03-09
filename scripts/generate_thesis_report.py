#!/usr/bin/env python3
"""
Generate publication-ready evidence reports from aggregated result tables.

Inputs (from scripts/aggregate_results.py):
  - significance_summary.csv
  - relative_gain_summary.csv
  - thesis_main_claims_32k.csv

Outputs:
  - claim_validation.csv
  - statistical_decision_summary.csv
  - reproducibility_gate.csv
  - paper_ready_summary.md
  - report_manifest.json
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClaimSpec:
    claim_id: str
    title: str
    metric: str
    baseline_mode: str
    challenger_mode: str
    min_gain_pct: float
    require_q_significance: bool
    target_seq_len: Optional[int] = None
    target_gen_len: Optional[int] = None
    target_batch: Optional[int] = None
    target_ppl_mode: Optional[str] = None
    target_chunk_size: Optional[int] = None
    target_model_ids: Optional[List[str]] = None
    note: str = ""


DEFAULT_PRACTICAL_THRESHOLDS: Dict[str, float] = {
    # Positive gain_pct means challenger is better by construction.
    "tpot_ms": 5.0,
    "tok_per_s": 5.0,
    "kv_cache_mem_mb": 20.0,
    "perplexity": -0.5,  # allow <=0.5% relative degradation as practical non-inferiority bound.
    "needle_pass_rate": -1.0,  # allow <=1% relative degradation for non-inferiority.
    "longbench_score": -1.0,  # allow <=1% relative degradation for non-inferiority.
    "ruler_pass_rate": -1.0,  # allow <=1% relative degradation for non-inferiority.
}


def _default_claims(target_seq_len: int) -> List[ClaimSpec]:
    return [
        ClaimSpec(
            claim_id="C1",
            title="INT8-ours significantly improves TPOT over INT8-baseline at long context.",
            metric="tpot_ms",
            baseline_mode="int8_baseline",
            challenger_mode="int8_ours",
            min_gain_pct=5.0,
            require_q_significance=True,
            target_seq_len=target_seq_len,
            target_gen_len=64,
            target_batch=1,
        ),
        ClaimSpec(
            claim_id="C2",
            title="INT8-ours keeps KV memory advantage over FP16 at long context.",
            metric="kv_cache_mem_mb",
            baseline_mode="fp16",
            challenger_mode="int8_ours",
            min_gain_pct=20.0,
            require_q_significance=False,
            target_seq_len=target_seq_len,
            target_gen_len=64,
            target_batch=1,
        ),
        ClaimSpec(
            claim_id="C3",
            title="INT8-ours is non-inferior to INT8-baseline on Needle pass rate.",
            metric="needle_pass_rate",
            baseline_mode="int8_baseline",
            challenger_mode="int8_ours",
            min_gain_pct=-1.0,
            require_q_significance=False,
            target_seq_len=target_seq_len,
        ),
        ClaimSpec(
            claim_id="C4",
            title="INT8-ours is non-inferior to INT8-baseline on PPL.",
            metric="perplexity",
            baseline_mode="int8_baseline",
            challenger_mode="int8_ours",
            min_gain_pct=-0.5,
            require_q_significance=False,
            # PPL generally uses a fixed eval setup; if seq_len is absent/mismatched use nearest available.
            target_seq_len=None,
            target_ppl_mode="kv_cache",
            target_chunk_size=128,
        ),
        ClaimSpec(
            claim_id="C5",
            title="INT8-ours is non-inferior to INT8-baseline on LongBench score.",
            metric="longbench_score",
            baseline_mode="int8_baseline",
            challenger_mode="int8_ours",
            min_gain_pct=-1.0,
            require_q_significance=False,
            target_seq_len=target_seq_len,
            note="Week5 external-validity benchmark.",
        ),
        ClaimSpec(
            claim_id="C6",
            title="INT8-ours is non-inferior to INT8-baseline on RULER pass rate.",
            metric="ruler_pass_rate",
            baseline_mode="int8_baseline",
            challenger_mode="int8_ours",
            min_gain_pct=-1.0,
            require_q_significance=False,
            target_seq_len=target_seq_len,
            note="Week5 external-validity benchmark.",
        ),
        # --- INT4 claims (RQ1: cross-bit-width generalization) ---
        ClaimSpec(
            claim_id="C7",
            title="INT4-ours is non-inferior to INT4-baseline on Needle pass rate.",
            metric="needle_pass_rate",
            baseline_mode="int4_baseline",
            challenger_mode="int4_ours",
            min_gain_pct=-1.0,
            require_q_significance=False,
            target_seq_len=target_seq_len,
            note="INT4 bit-width generalization.",
        ),
        ClaimSpec(
            claim_id="C8",
            title="INT4-ours is non-inferior to INT4-baseline on PPL.",
            metric="perplexity",
            baseline_mode="int4_baseline",
            challenger_mode="int4_ours",
            min_gain_pct=-0.5,
            require_q_significance=False,
            target_seq_len=None,
            target_ppl_mode="kv_cache",
            target_chunk_size=128,
            note="INT4 bit-width generalization.",
        ),
        # --- KIVI comparison claims (Milestone N validation) ---
        ClaimSpec(
            claim_id="C9",
            title="INT8-ours is non-inferior to KIVI-style on LongBench score.",
            metric="longbench_score",
            baseline_mode="kivi_style",
            challenger_mode="int8_ours",
            min_gain_pct=-1.0,
            require_q_significance=False,
            target_seq_len=target_seq_len,
            note="KIVI-style SOTA baseline comparison.",
        ),
        ClaimSpec(
            claim_id="C10",
            title="INT8-ours is non-inferior to KIVI-style on Needle pass rate.",
            metric="needle_pass_rate",
            baseline_mode="kivi_style",
            challenger_mode="int8_ours",
            min_gain_pct=-1.0,
            require_q_significance=False,
            target_seq_len=target_seq_len,
            note="KIVI-style SOTA baseline comparison.",
        ),
        # --- Cross-model robustness claim (RQ4) ---
        ClaimSpec(
            claim_id="C11",
            title="INT8-ours is non-inferior to INT8-baseline on LongBench across extended models.",
            metric="longbench_score",
            baseline_mode="int8_baseline",
            challenger_mode="int8_ours",
            min_gain_pct=-1.0,
            require_q_significance=False,
            target_seq_len=target_seq_len,
            target_model_ids=[
                "Qwen/Qwen2.5-7B-Instruct",
                "meta-llama/Llama-3.1-8B-Instruct",
            ],
            note="Cross-model robustness (7B/8B only); filtered by model_id.",
        ),
    ]


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception as exc:
        logger.warning("Failed to read CSV %s: %s", path, exc)
        return pd.DataFrame()


def _to_numeric(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def _to_bool(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value) != 0
    s = str(value).strip().lower()
    return s in {"1", "true", "yes", "y", "t"}


def _nearest_seq_value(df: pd.DataFrame, target_seq_len: Optional[int]) -> Optional[int]:
    if "seq_len" not in df.columns:
        return None
    seq = pd.to_numeric(df["seq_len"], errors="coerce").dropna()
    if seq.empty:
        return None
    seq_vals = sorted(int(x) for x in seq.unique())
    if target_seq_len is None:
        return int(seq_vals[-1])
    if target_seq_len in seq_vals:
        return int(target_seq_len)
    return int(min(seq_vals, key=lambda x: abs(x - int(target_seq_len))))


def _apply_optional_filters(df: pd.DataFrame, claim: ClaimSpec) -> pd.DataFrame:
    out = df.copy()
    for col, target in [
        ("metric", claim.metric),
        ("baseline_mode", claim.baseline_mode),
        ("challenger_mode", claim.challenger_mode),
    ]:
        if col in out.columns:
            out = out[out[col].astype(str) == str(target)]

    numeric_targets = [
        ("gen_len", claim.target_gen_len),
        ("batch", claim.target_batch),
        ("chunk_size", claim.target_chunk_size),
    ]
    for col, target in numeric_targets:
        if target is None or col not in out.columns:
            continue
        series = pd.to_numeric(out[col], errors="coerce")
        out = out[series == float(target)]

    if claim.target_ppl_mode is not None and "ppl_mode" in out.columns:
        out = out[out["ppl_mode"].astype(str) == str(claim.target_ppl_mode)]
    if claim.target_model_ids and "model_id" in out.columns:
        target_models = {str(m) for m in claim.target_model_ids}
        out = out[out["model_id"].astype(str).isin(target_models)]

    if "seq_len" in out.columns:
        seq_target = _nearest_seq_value(out, claim.target_seq_len)
        if seq_target is not None:
            seq_series = pd.to_numeric(out["seq_len"], errors="coerce")
            out = out[seq_series == float(seq_target)]
    return out


def _pick_best_relative_row(relative_gain: pd.DataFrame, claim: ClaimSpec) -> Optional[pd.Series]:
    if relative_gain.empty:
        return None
    sub = _apply_optional_filters(relative_gain, claim)
    if sub.empty:
        return None
    if "gain_pct" in sub.columns:
        # RPT-002: avoid "max gain" selection bias when multiple candidate rows
        # survive filters. Use the row closest to median gain as representative.
        gains = pd.to_numeric(sub["gain_pct"], errors="coerce")
        valid = gains.notna()
        if valid.any():
            idx = (gains[valid] - float(gains[valid].median())).abs().sort_values(kind="stable").index[0]
            return sub.loc[idx]
    return sub.iloc[0]


def _pick_best_significance_row(
    significance: pd.DataFrame,
    claim: ClaimSpec,
    observed_row: Optional[pd.Series],
) -> Optional[pd.Series]:
    if significance.empty:
        return None
    sub = _apply_optional_filters(significance, claim)
    if observed_row is not None:
        for col in ["seq_len", "gen_len", "batch", "ppl_mode", "chunk_size"]:
            if col in sub.columns and col in observed_row.index:
                val = observed_row[col]
                if pd.notna(val):
                    if col in {"seq_len", "gen_len", "batch", "chunk_size"}:
                        series = pd.to_numeric(sub[col], errors="coerce")
                        sub = sub[series == float(val)]
                    else:
                        sub = sub[sub[col].astype(str) == str(val)]
    if sub.empty:
        return None
    if "q_value" in sub.columns:
        sub = _to_numeric(sub, ["q_value"])
        sub = sub.sort_values("q_value", na_position="last")
    elif "p_value" in sub.columns:
        sub = _to_numeric(sub, ["p_value"])
        sub = sub.sort_values("p_value", na_position="last")
    return sub.iloc[0]


def _inconclusive_claim_row(claim: ClaimSpec, reason: str, model_id: str = "") -> Dict[str, object]:
    return {
        "claim_id": claim.claim_id,
        "title": claim.title,
        "metric": claim.metric,
        "baseline_mode": claim.baseline_mode,
        "challenger_mode": claim.challenger_mode,
        "status": "INCONCLUSIVE",
        "reason": reason,
        "min_gain_pct": float(claim.min_gain_pct),
        "observed_gain_pct": np.nan,
        "practical_pass": False,
        "require_q_significance": bool(claim.require_q_significance),
        "statistical_pass": False,
        "q_value": np.nan,
        "p_value": np.nan,
        "n_pairs": np.nan,
        "meets_min_pairs": False,
        "significant_q_alpha": False,
        "favors_challenger": False,
        "evidence_strength": "weak",
        "observed_seq_len": np.nan,
        "observed_gen_len": np.nan,
        "observed_batch": np.nan,
        "observed_ppl_mode": "",
        "observed_chunk_size": np.nan,
        "target_model_id": str(model_id),
        "min_gain_model": "",
        "max_degradation_model": "",
        "target_model_coverage": "",
        "target_model_statuses": "",
        "note": claim.note,
    }


def _evaluate_claim_row(
    *,
    claim: ClaimSpec,
    rel_row: Optional[pd.Series],
    sig_row: Optional[pd.Series],
    alpha: float,
) -> Dict[str, object]:
    if rel_row is None:
        return _inconclusive_claim_row(claim, "missing relative_gain evidence row")

    # AGG-029: gain_pct here is a single-point relative gain computed from
    # aggregated (cross-seed) mean metric values in relative_gain_summary.csv.
    # This differs from gain_pct_mean in significance_summary.csv, which is the
    # mean of per-seed paired relative gains.  Due to Jensen's inequality these
    # two quantities are NOT generally equal — gain_pct_mean (paired diff mean)
    # is the more statistically rigorous measure.  We use gain_pct here for the
    # practical threshold check because it reflects the best-estimate point
    # improvement, while significance_summary uses gain_pct_mean for hypothesis
    # testing with proper variance accounting.
    observed_gain_pct = float(pd.to_numeric(pd.Series([rel_row.get("gain_pct")]), errors="coerce").iloc[0])

    # NaN gain_pct (e.g. baseline=0) cannot be judged; treat as INCONCLUSIVE.
    if np.isnan(observed_gain_pct):
        row = _inconclusive_claim_row(claim, "gain_pct is NaN (possible zero baseline)")
        row["observed_gain_pct"] = observed_gain_pct
        row["observed_seq_len"] = rel_row.get("seq_len", np.nan)
        row["observed_gen_len"] = rel_row.get("gen_len", np.nan)
        row["observed_batch"] = rel_row.get("batch", np.nan)
        row["observed_ppl_mode"] = rel_row.get("ppl_mode", "")
        row["observed_chunk_size"] = rel_row.get("chunk_size", np.nan)
        row["target_model_id"] = str(rel_row.get("model_id", "")) if "model_id" in rel_row.index else ""
        return row

    practical_pass = bool(observed_gain_pct >= float(claim.min_gain_pct))

    q_value = np.nan
    p_value = np.nan
    n_pairs = np.nan
    meets_min_pairs = False
    significant_q = False
    favors_challenger = False
    statistical_pass = not claim.require_q_significance
    stat_reason = "q-significance not required"

    if sig_row is not None:
        q_value = float(pd.to_numeric(pd.Series([sig_row.get("q_value")]), errors="coerce").iloc[0])
        p_value = float(pd.to_numeric(pd.Series([sig_row.get("p_value")]), errors="coerce").iloc[0])
        n_pairs = float(pd.to_numeric(pd.Series([sig_row.get("n_pairs")]), errors="coerce").iloc[0])
        meets_min_pairs = _to_bool(sig_row.get("meets_min_pairs", False))
        significant_q = _to_bool(sig_row.get("significant_q_alpha", False))
        if not significant_q and np.isfinite(q_value):
            significant_q = bool(q_value <= float(alpha))
        favors_challenger = _to_bool(sig_row.get("favors_challenger", False))

        if claim.require_q_significance:
            statistical_pass = bool(significant_q and favors_challenger and meets_min_pairs)
            stat_reason = (
                "q-significant and direction-consistent"
                if statistical_pass
                else "required q-significance not met"
            )
        else:
            # For non-inferiority type claims, fail only if challenger is significantly worse.
            if significant_q and not favors_challenger:
                statistical_pass = False
                stat_reason = "statistically significant contradiction"
            else:
                statistical_pass = True
                stat_reason = "no significant contradiction"
    elif claim.require_q_significance:
        statistical_pass = False
        stat_reason = "missing significance row for required q-test"

    if practical_pass and statistical_pass:
        status = "PASS"
        evidence_strength = "strong" if significant_q else "moderate"
        reason = "practical and statistical criteria satisfied"
    elif not practical_pass:
        status = "FAIL"
        evidence_strength = "none"
        reason = (
            f"practical threshold not met: gain={observed_gain_pct:.4f}% < "
            f"required {claim.min_gain_pct:.4f}%"
        )
    else:
        status = "INCONCLUSIVE"
        evidence_strength = "weak"
        reason = stat_reason

    return {
        "claim_id": claim.claim_id,
        "title": claim.title,
        "metric": claim.metric,
        "baseline_mode": claim.baseline_mode,
        "challenger_mode": claim.challenger_mode,
        "status": status,
        "reason": reason,
        "min_gain_pct": float(claim.min_gain_pct),
        "observed_gain_pct": observed_gain_pct,
        "practical_pass": practical_pass,
        "require_q_significance": bool(claim.require_q_significance),
        "statistical_pass": statistical_pass,
        "q_value": q_value,
        "p_value": p_value,
        "n_pairs": n_pairs,
        "meets_min_pairs": bool(meets_min_pairs),
        "significant_q_alpha": bool(significant_q),
        "favors_challenger": bool(favors_challenger),
        "evidence_strength": evidence_strength,
        "observed_seq_len": rel_row.get("seq_len", np.nan),
        "observed_gen_len": rel_row.get("gen_len", np.nan),
        "observed_batch": rel_row.get("batch", np.nan),
        "observed_ppl_mode": rel_row.get("ppl_mode", ""),
        "observed_chunk_size": rel_row.get("chunk_size", np.nan),
        "target_model_id": str(rel_row.get("model_id", "")) if "model_id" in rel_row.index else "",
        "min_gain_model": "",
        "max_degradation_model": "",
        "target_model_coverage": "",
        "target_model_statuses": "",
        "note": claim.note,
    }


def build_claim_validation(
    *,
    relative_gain: pd.DataFrame,
    significance: pd.DataFrame,
    claims: List[ClaimSpec],
    alpha: float,
) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    sig = significance.copy()
    sig = _to_numeric(sig, ["p_value", "q_value", "n_pairs", "gain_pct_mean"])

    for claim in claims:
        target_models = [str(m).strip() for m in (claim.target_model_ids or []) if str(m).strip()]
        if len(target_models) > 1:
            per_model_rows: List[Dict[str, object]] = []
            for model_id in target_models:
                scoped_claim = replace(claim, target_model_ids=[model_id])
                rel_row = _pick_best_relative_row(relative_gain, scoped_claim)
                if rel_row is None:
                    logger.warning(
                        "Claim %s: no relative_gain data for model_id=%r; "
                        "marking INCONCLUSIVE for this model.",
                        claim.claim_id,
                        model_id,
                    )
                sig_row = _pick_best_significance_row(sig, scoped_claim, rel_row)
                row = _evaluate_claim_row(
                    claim=scoped_claim,
                    rel_row=rel_row,
                    sig_row=sig_row,
                    alpha=alpha,
                )
                row["target_model_id"] = model_id
                per_model_rows.append(row)

            status_tokens = {str(r.get("status", "")) for r in per_model_rows}
            if "FAIL" in status_tokens:
                agg_status = "FAIL"
                agg_reason = "at least one target model failed non-inferiority threshold"
            elif "INCONCLUSIVE" in status_tokens:
                agg_status = "INCONCLUSIVE"
                agg_reason = "at least one target model lacks sufficient evidence"
            else:
                agg_status = "PASS"
                agg_reason = "all target models satisfy practical and statistical criteria"

            gains = pd.to_numeric(
                pd.Series([r.get("observed_gain_pct") for r in per_model_rows]),
                errors="coerce",
            ).dropna()
            q_vals = pd.to_numeric(
                pd.Series([r.get("q_value") for r in per_model_rows]),
                errors="coerce",
            ).dropna()
            p_vals = pd.to_numeric(
                pd.Series([r.get("p_value") for r in per_model_rows]),
                errors="coerce",
            ).dropna()
            n_pairs = pd.to_numeric(
                pd.Series([r.get("n_pairs") for r in per_model_rows]),
                errors="coerce",
            ).dropna()

            # Derive practical_pass from the aggregate min-gain to stay consistent
            # with observed_gain_pct = gains.min().  When gains is empty (all NaN),
            # practical_pass must be False.
            if not gains.empty:
                practical_pass = bool(float(gains.min()) >= float(claim.min_gain_pct))
            else:
                practical_pass = False
            statistical_pass = all(bool(r.get("statistical_pass", False)) for r in per_model_rows)
            evidence_tokens = {str(r.get("evidence_strength", "weak")) for r in per_model_rows}
            if agg_status == "FAIL":
                evidence_strength = "none"
            elif evidence_tokens == {"strong"}:
                evidence_strength = "strong"
            elif evidence_tokens.issubset({"strong", "moderate"}):
                evidence_strength = "moderate"
            else:
                evidence_strength = "weak"

            exemplar = per_model_rows[0] if per_model_rows else _inconclusive_claim_row(claim, "no model rows")

            # Identify per-model extremes for schema completeness.
            _gain_pairs = [
                (r.get("target_model_id", ""), r.get("observed_gain_pct"))
                for r in per_model_rows
            ]
            _finite_gain_pairs = [
                (mid, g) for mid, g in _gain_pairs if isinstance(g, (int, float)) and np.isfinite(g)
            ]
            if _finite_gain_pairs:
                min_gain_model = str(min(_finite_gain_pairs, key=lambda x: x[1])[0])
                # RPT-004: degradation is meaningful only for negative gains.
                _degraded_pairs = [(mid, g) for mid, g in _finite_gain_pairs if float(g) < 0.0]
                max_degradation_model = (
                    str(min(_degraded_pairs, key=lambda x: x[1])[0])
                    if _degraded_pairs
                    else ""
                )
            else:
                min_gain_model = ""
                max_degradation_model = ""

            rows.append(
                {
                    "claim_id": claim.claim_id,
                    "title": claim.title,
                    "metric": claim.metric,
                    "baseline_mode": claim.baseline_mode,
                    "challenger_mode": claim.challenger_mode,
                    "status": agg_status,
                    "reason": agg_reason,
                    "min_gain_pct": float(claim.min_gain_pct),
                    "observed_gain_pct": float(gains.min()) if not gains.empty else np.nan,
                    "practical_pass": bool(practical_pass),
                    "require_q_significance": bool(claim.require_q_significance),
                    "statistical_pass": bool(statistical_pass),
                    "q_value": float(q_vals.max()) if not q_vals.empty else np.nan,
                    "p_value": float(p_vals.max()) if not p_vals.empty else np.nan,
                    "n_pairs": float(n_pairs.min()) if not n_pairs.empty else np.nan,
                    "meets_min_pairs": all(bool(r.get("meets_min_pairs", False)) for r in per_model_rows),
                    "significant_q_alpha": all(bool(r.get("significant_q_alpha", False)) for r in per_model_rows),
                    "favors_challenger": all(bool(r.get("favors_challenger", False)) for r in per_model_rows),
                    "evidence_strength": evidence_strength,
                    "observed_seq_len": exemplar.get("observed_seq_len", np.nan),
                    "observed_gen_len": exemplar.get("observed_gen_len", np.nan),
                    "observed_batch": exemplar.get("observed_batch", np.nan),
                    "observed_ppl_mode": exemplar.get("observed_ppl_mode", ""),
                    "observed_chunk_size": exemplar.get("observed_chunk_size", np.nan),
                    "target_model_id": ",".join(target_models),
                    "min_gain_model": min_gain_model,
                    "max_degradation_model": max_degradation_model,
                    "target_model_coverage": f"{len(per_model_rows)}/{len(target_models)}",
                    "target_model_statuses": ";".join(
                        f"{r.get('target_model_id', '')}:{r.get('status', '')}" for r in per_model_rows
                    ),
                    "note": claim.note,
                }
            )
            continue

        rel_row = _pick_best_relative_row(relative_gain, claim)
        sig_row = _pick_best_significance_row(sig, claim, rel_row)
        row = _evaluate_claim_row(
            claim=claim,
            rel_row=rel_row,
            sig_row=sig_row,
            alpha=alpha,
        )
        # When exactly one target model is specified, ensure target_model_id is set.
        if len(target_models) == 1 and not row.get("target_model_id"):
            row["target_model_id"] = target_models[0]
        rows.append(row)

    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    out = _to_numeric(
        out,
        [
            "min_gain_pct",
            "observed_gain_pct",
            "q_value",
            "p_value",
            "n_pairs",
            "observed_seq_len",
            "observed_gen_len",
            "observed_batch",
            "observed_chunk_size",
        ],
    )
    return out


def build_statistical_decisions(
    *,
    significance: pd.DataFrame,
    practical_thresholds: Dict[str, float],
) -> pd.DataFrame:
    if significance.empty:
        return pd.DataFrame()
    out = significance.copy()
    out = _to_numeric(out, ["gain_pct_mean", "n_pairs", "q_value", "p_value"])
    out["meets_min_pairs"] = out.get("meets_min_pairs", False).map(_to_bool)
    out["significant_q_alpha"] = out.get("significant_q_alpha", False).map(_to_bool)
    out["favors_challenger"] = out.get("favors_challenger", False).map(_to_bool)
    out["practical_threshold_pct"] = out["metric"].map(practical_thresholds).fillna(0.0)
    out["practical_pass"] = (
        pd.to_numeric(out["gain_pct_mean"], errors="coerce")
        >= pd.to_numeric(out["practical_threshold_pct"], errors="coerce")
    )

    decisions: List[str] = []
    for _, row in out.iterrows():
        if not _to_bool(row.get("meets_min_pairs")):
            decisions.append("insufficient_pairs")
            continue
        if _to_bool(row.get("significant_q_alpha")) and _to_bool(row.get("favors_challenger")) and _to_bool(row.get("practical_pass")):
            decisions.append("robust_support")
        elif _to_bool(row.get("significant_q_alpha")) and (not _to_bool(row.get("favors_challenger"))):
            decisions.append("significant_contradiction")
        elif _to_bool(row.get("favors_challenger")) and _to_bool(row.get("practical_pass")):
            decisions.append("practical_support_only")
        elif _to_bool(row.get("favors_challenger")) and (not _to_bool(row.get("practical_pass"))):
            decisions.append("small_effect_only")
        else:
            decisions.append("no_support")
    out["decision"] = decisions
    return out


def build_reproducibility_gate(
    *,
    claim_validation: pd.DataFrame,
    execution_coverage: pd.DataFrame,
    failure_registry: pd.DataFrame,
) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []

    total_tasks = int(len(execution_coverage))
    success_tasks = int(
        (execution_coverage.get("execution_state", pd.Series(dtype=object)) == "success").sum()
    )
    coverage_ratio = float(success_tasks / total_tasks) if total_tasks > 0 else 0.0
    rows.append(
        {
            "gate_id": "G1",
            "gate_name": "execution_coverage_present",
            "status": "PASS" if total_tasks > 0 else "FAIL",
            "value": float(total_tasks),
            "threshold": 1.0,
            "detail": "execution_coverage.csv contains task-level rows",
        }
    )
    rows.append(
        {
            "gate_id": "G2",
            "gate_name": "task_success_ratio",
            "status": "PASS" if coverage_ratio >= 0.90 else "FAIL",
            "value": coverage_ratio,
            "threshold": 0.90,
            "detail": "share of successful task rows in execution_coverage",
        }
    )

    if failure_registry.empty:
        unexpected_failures = 0
        expected_oom = 0
    else:
        fr = failure_registry.copy()
        is_oom = fr.get("failure_category", pd.Series(dtype=object)).astype(str) == "oom"
        is_throughput = fr.get("is_throughput_run", pd.Series(dtype=bool)).fillna(False).astype(bool)
        expected_oom_mask = is_oom & is_throughput
        expected_oom = int(expected_oom_mask.sum())
        unexpected_failures = int((~expected_oom_mask).sum())

    rows.append(
        {
            "gate_id": "G3",
            "gate_name": "no_unexpected_failures",
            "status": "PASS" if unexpected_failures == 0 else "FAIL",
            "value": float(unexpected_failures),
            "threshold": 0.0,
            "detail": f"expected_oom_rows={expected_oom}",
        }
    )

    claim_pass = int(
        (claim_validation.get("status", pd.Series(dtype=object)).astype(str) == "PASS").sum()
    )
    claim_total = int(len(claim_validation))
    rows.append(
        {
            "gate_id": "G4",
            "gate_name": "claim_rows_materialized",
            "status": "PASS" if claim_total >= 1 else "FAIL",
            "value": float(claim_total),
            "threshold": 1.0,
            "detail": f"pass_rows={claim_pass}",
        }
    )
    return pd.DataFrame(rows)


def _markdown_table(df: pd.DataFrame, columns: List[str]) -> str:
    if df.empty:
        return "_No rows._"
    work = df.copy()
    cols = [c for c in columns if c in work.columns]
    if not cols:
        return "_No display columns._"
    work = work[cols]
    header = "| " + " | ".join(cols) + " |"
    sep = "|" + "|".join(["---"] * len(cols)) + "|"
    lines = [header, sep]
    for _, row in work.iterrows():
        vals = []
        for col in cols:
            val = row[col]
            if isinstance(val, float):
                if np.isnan(val):
                    vals.append("")
                else:
                    vals.append(f"{val:.4f}")
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def build_markdown_report(
    *,
    claim_validation: pd.DataFrame,
    stat_decisions: pd.DataFrame,
    reproducibility_gate: pd.DataFrame,
    failure_registry: pd.DataFrame,
    tables_dir: Path,
) -> str:
    now = pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
    n_pass = int((claim_validation.get("status", pd.Series(dtype=object)) == "PASS").sum())
    n_fail = int((claim_validation.get("status", pd.Series(dtype=object)) == "FAIL").sum())
    n_inc = int((claim_validation.get("status", pd.Series(dtype=object)) == "INCONCLUSIVE").sum())

    if "decision" in stat_decisions.columns:
        decision_series = stat_decisions["decision"].astype(str)
    else:
        decision_series = pd.Series("", index=stat_decisions.index, dtype=object)
    critical = stat_decisions[decision_series == "significant_contradiction"]
    weak = stat_decisions[decision_series == "insufficient_pairs"]

    lines = []
    lines.append("# Paper-Ready Evidence Summary")
    lines.append("")
    lines.append(f"- Generated at (UTC): {now}")
    lines.append(f"- Source tables dir: `{tables_dir}`")
    lines.append("")
    lines.append("## Claim Gate")
    lines.append("")
    lines.append(f"- PASS: {n_pass}")
    lines.append(f"- FAIL: {n_fail}")
    lines.append(f"- INCONCLUSIVE: {n_inc}")
    lines.append("")
    lines.append(_markdown_table(
        claim_validation,
        [
            "claim_id",
            "status",
            "metric",
            "baseline_mode",
            "challenger_mode",
            "observed_gain_pct",
            "min_gain_pct",
            "q_value",
            "evidence_strength",
            "reason",
        ],
    ))
    lines.append("")
    lines.append("## Statistical Decision Snapshot")
    lines.append("")
    lines.append(_markdown_table(
        stat_decisions,
        [
            "metric",
            "baseline_mode",
            "challenger_mode",
            "seq_len",
            "gain_pct_mean",
            "q_value",
            "n_pairs",
            "decision",
        ],
    ))
    lines.append("")
    lines.append("## Risks")
    lines.append("")
    if not critical.empty:
        lines.append("- Significant contradiction detected; re-check claim statements before submission.")
    if not weak.empty:
        lines.append("- Some hypotheses have insufficient seed pairs; avoid strong causal claims on those rows.")
    if critical.empty and weak.empty:
        lines.append("- No critical statistical contradiction detected in current tables.")
    lines.append("")
    lines.append("## Reproducibility Gate")
    lines.append("")
    lines.append(
        _markdown_table(
            reproducibility_gate,
            ["gate_id", "gate_name", "status", "value", "threshold", "detail"],
        )
    )
    lines.append("")
    lines.append("## Failure Transparency")
    lines.append("")
    if failure_registry.empty:
        lines.append("- No failed task rows were recorded in failure_registry.csv.")
    else:
        lines.append(
            _markdown_table(
                failure_registry,
                [
                    "run_name",
                    "task",
                    "execution_state",
                    "failure_category",
                    "failure_type",
                    "returncode",
                ],
            )
        )
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append("- `claim_validation.csv`")
    lines.append("- `statistical_decision_summary.csv`")
    lines.append("- `reproducibility_gate.csv`")
    lines.append("- `paper_ready_summary.md`")
    return "\n".join(lines) + "\n"


def _save_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate paper-ready evidence report")
    parser.add_argument("--tables_dir", type=str, default="results/tables")
    parser.add_argument("--out_dir", type=str, default="results/reports")
    parser.add_argument("--target_seq_len", type=int, default=32704)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Fail when required source tables are missing.",
    )
    args = parser.parse_args()

    tables_dir = Path(args.tables_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    required = [
        tables_dir / "relative_gain_summary.csv",
        tables_dir / "significance_summary.csv",
    ]
    if args.strict:
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            print("Missing required tables:")
            for path in missing:
                print(f"  - {path}")
            return 2

    relative_gain = _read_csv(tables_dir / "relative_gain_summary.csv")
    significance = _read_csv(tables_dir / "significance_summary.csv")
    main_claims = _read_csv(tables_dir / "thesis_main_claims_32k.csv")
    execution_coverage = _read_csv(tables_dir / "execution_coverage.csv")
    failure_registry = _read_csv(tables_dir / "failure_registry.csv")
    _ = main_claims  # kept for future extension and explicit dependency tracking.

    claims = _default_claims(target_seq_len=int(args.target_seq_len))
    claim_validation = build_claim_validation(
        relative_gain=relative_gain,
        significance=significance,
        claims=claims,
        alpha=float(args.alpha),
    )
    stat_decisions = build_statistical_decisions(
        significance=significance,
        practical_thresholds=DEFAULT_PRACTICAL_THRESHOLDS,
    )
    reproducibility_gate = build_reproducibility_gate(
        claim_validation=claim_validation,
        execution_coverage=execution_coverage,
        failure_registry=failure_registry,
    )

    claim_csv = out_dir / "claim_validation.csv"
    stat_csv = out_dir / "statistical_decision_summary.csv"
    repro_csv = out_dir / "reproducibility_gate.csv"
    report_md = out_dir / "paper_ready_summary.md"
    manifest_json = out_dir / "report_manifest.json"

    _save_csv(claim_validation, claim_csv)
    _save_csv(stat_decisions, stat_csv)
    _save_csv(reproducibility_gate, repro_csv)
    report_md.write_text(
        build_markdown_report(
            claim_validation=claim_validation,
            stat_decisions=stat_decisions,
            reproducibility_gate=reproducibility_gate,
            failure_registry=failure_registry,
            tables_dir=tables_dir,
        ),
        encoding="utf-8",
    )

    manifest = {
        "tables_dir": str(tables_dir),
        "out_dir": str(out_dir),
        "target_seq_len": int(args.target_seq_len),
        "alpha": float(args.alpha),
        "claim_rows": int(len(claim_validation)),
        "stat_rows": int(len(stat_decisions)),
        "generated_files": [
            str(claim_csv),
            str(stat_csv),
            str(repro_csv),
            str(report_md),
        ],
    }
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8")

    print(f"Wrote report artifacts to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
