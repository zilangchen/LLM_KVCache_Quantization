# Clean Rerun Manifest — 2026-04-19 09:00+

## 0. Pin

- branch: `codex/phase2-a-rerun`
- commit: `ddada195dcf3bbd205b627fab154ecb013f11c1c`
- local source HEAD at rsync time: `9d1692f` (pre-pin, source of rsync)
- tag candidate: `phase2-clean-rerun-v1` (to be applied after Step 3 PASS)

## 1. Remote Workspace

- path: `/root/autodl-tmp/LLM_KVCache_Quantization_clean`
- created: 2026-04-19 09:06 CST (rsync from local `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/`, exclude `results/ artifacts/ .venv/ __pycache__/ *.pyc thesis/ experiments/ .agents/`)
- initialized by:
  1. `git config --global --add safe.directory /root/autodl-tmp/LLM_KVCache_Quantization_clean`
  2. `git reset --hard ddada19`
  3. `git clean -fd` (remove untracked L2 poll scripts + paper draft docs from 9d1692f)
- disk: `/dev/vdb` 200G, 84G free at creation

## 2. Runtime File MD5 (at ddada19)

| File | MD5 |
|---|---|
| `scripts/eval_longbench.py` | `979f6f7ae56ec3a68a7182ba4d4c5d7a` |
| `scripts/eval_ppl.py` | `67da87d876bdd23c0418e019a91158c1` |
| `scripts/eval_needle.py` | `d657d87aa2bab44577dbd2a0fb10ae2a` |
| `scripts/profile_latency.py` | `41aa1304377d5013363fa98d2b67fc43` |
| `scripts/profile_memory.py` | `288c50fce0130bdc270eed39bcd8a1d6` |
| `scripts/calibrate_behavior.py` | `37b693ee59cb559a024b16e51771d98b` |
| `scripts/adaptive/behavior_aligned_allocator.py` | `3e8993f91a6ed08eb410920a16adc86e` |
| `src/engine/generate_loop.py` | `c56ef61ed1d35b3ba9e72e2147d694c2` |
| `src/cache/mixed_kv_cache.py` | `8fa69fa9240a5be62a80ac60db74bee2` |

## 3. Calibration Decisions

### 3.1 Retained (cp from exploratory, plan §4.2)

| Model | File | MD5 | Source |
|---|---|---|---|
| Qwen2.5-1.5B | `kv_calib_kl_1p5b_int8_v5_fixed.json` | `c187ee488d06ecf681186f7d0b55692a` | exploratory 2026-04-03 |
| Qwen2.5-7B | `kv_calib_kl_qwen25_7b_int8.json` | `3670c2581e835bf45b875bcddcb0fc87` | exploratory 2026-02-23 |
| Llama-3.1-8B | `kv_calib_kl_llama31_8b_int8.json` | `6d62c2bcf34c573e28f9b50bfd330405` | exploratory 2026-04-18 |

Rationale: plan §4.2 permits retention if provenance is clean. Sources above are referenced in exploratory `iteration.md` and remain unmodified since their respective commits. cp is non-destructive; ledger above binds MD5.

### 3.2 To Regenerate (under ddada19 pin, plan §4.1)

- Qwen2.5-3B-Instruct
- Qwen2.5-14B-Instruct
- Mistral-7B-Instruct-v0.3

These three will be re-calibrated with `scripts/calibrate_behavior.py` at ddada19. Per-artifact ledger (md5 + timestamp + config) will be appended below after regeneration.

## 4. Preflight Results

- `py_compile` 9 critical files: **OK**
- `--policy_json` CLI support: `eval_longbench` ✓, `eval_ppl` ✓, `eval_needle` ✓
- `--warmup` CLI on `profile_memory`: **missing under ddada19** (fix landed after pin). Not on clean rerun critical path (L1 compare set does not call Pareto runner → `profile_memory` is not invoked). Not blocking.
- LongBench jsonl: `/root/autodl-tmp/longbench_data/data/` accessible, 34 files incl. `narrativeqa.jsonl`, `hotpotqa.jsonl`, `gov_report.jsonl`, `dureader.jsonl`, `lcc.jsonl`.
- HF cache: `/root/autodl-tmp/hf_cache/` accessible; 4 target models cached (3B/8B/14B/Mistral; 1.5B/7B already in cache for retained calibration).
- `git status --short`: clean.

## 5. Execution Scope (overnight plan §3)

### 5.1 Step 1: INT8 canonical path (Gate P1)

- Primary model: `Qwen/Qwen2.5-1.5B-Instruct`
- Optional echo: `Qwen/Qwen2.5-7B-Instruct`
- kv_modes: `fp16`, `int8_ours`, `int4_ours_asym`, `kivi_style`
- Tasks: `narrativeqa`, `hotpotqa`, `gov_report`
- Samples: 50 (same as Phase B smoke)

### 5.2 Step 2: Cross-model compare set (Gate P2)

Per plan §2.1 — 4 models × ≤ 5 policies each (best overall + best auto-k + strongest heuristic + strongest fixed-k + strongest uniform). Exploratory-identified leaders:

| Model | best overall | best auto-k | strongest heuristic | strongest BAKV fixed-k | strongest uniform |
|---|---|---|---|---|---|
| Qwen2.5-3B | `bakv_k1` (early-layer regime) | `bakv_auto_cov80_max` | TBD (pull from mainline_execution_queue.md) | `bakv_k1` (overlap) | `uniform_int4_k4v4` |
| Llama-3.1-8B | `bakv_auto_cov80_max` | (same) | `heuristic_k11` | `bakv_k11` | `uniform_int4_k4v4` |
| Qwen2.5-14B | `uniform_int4_k4v4` | `bakv_auto_cov90_max` | TBD | TBD | `uniform_int4_k4v4` (overlap with best overall) |
| Mistral-7B | `bakv_auto_cov80_max` | (same) | `heuristic_k3` | `bakv_k3` | `uniform_int4_k4v4` |

"strongest heuristic/BAKV fixed-k" TBD entries will be pinned after reading exploratory per-model aggregate CSV (done during clean rerun prep, pre-launch).

### 5.3 Step 3: Extend-task supporting evidence (Gate P3)

- Tasks: `dureader`, `lcc` (only — `trec` / `vcsum` out of scope per plan §2.3)
- Same 4 models × same compare set

### 5.4 Not in scope

- `trec`, `vcsum` (low information, 1.5B+INT4 floor effect already observed)
- L2 exploratory data (Phase A/B/C, separate track)
- 7B follow-up (plan §1C: only if extremely strong signal, recorded as suggestion not auto-launch)

## 6. Provenance Record Format (for re-generated calibrations)

Each regenerated calibration will append an entry here with:

- model id
- config snapshot (full command-line used)
- commit pin (always ddada19 for this rerun)
- md5 of output JSON
- timestamp (UTC)
- output path (relative to clean workspace)

## 7. Exploratory → Clean Comparison (to be filled at Gate P2/P3)

To be generated after Step 2 completes. Will compare:

1. mean ranking stability
2. task-best stability
3. key gap stability
4. mainline judgment stability

Upgrade to `final-ready support` condition (plan §6.2): direction preserved + top-tier relative positions basically stable + task-best vs strong baseline relationship not fundamentally changed.
