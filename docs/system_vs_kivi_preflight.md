# System vs KIVI Preflight

## Scope

This document freezes the current preflight state for the formal
`Allocator-enabled RoleAlign vs KIVI-style` claim package.

It remains a Phase 0 document:

- it defines the intended compare systems
- it freezes the fairness rules
- it records the machine-checked `G0` status
- it does **not** claim that official smoke, main, or ablation runs have started

## Provenance

- Date: 2026-04-20
- Git HEAD: `ed879ca`
- Source plans:
  - `objective.md`
  - `docs/freeze_20260419.md`
  - `docs/thesis_upgrade_live_plan.md`
  - `docs/mainline_execution_queue.md`
  - `.agents/execplans/2026-04-20_allocator-vs-kivi-claim-package.md`
  - `.agents/execplans/2026-04-20_same-format-allocator-backend-enable.md`

## Formal Compare Systems

The frozen formal systems remain:

1. `kivi_style`
2. `rolealign_static`
3. `rolealign_allocator_fixed_eqmem`
4. `rolealign_allocator_auto_eqmem`

Main matrix target:

1. `kivi_style`
2. `rolealign_static`
3. `rolealign_allocator_auto_eqmem`

Mechanism ablation target:

1. `kivi_style`
2. `rolealign_static`
3. `rolealign_allocator_fixed_eqmem`
4. `rolealign_allocator_auto_eqmem`

## Fairness Rules

The formal package keeps the following rules frozen:

1. Same INT4-oriented comparison family (`kivi_asym_family` runtime backbone).
2. **Pareto-disclosure budget rule** (updated 2026-04-20 from legacy ±3% matched-budget):
   - `kv_cache_mem_mb` difference is **reported, not gated**.
   - The aggregation step must record, for every (model, compared system) pair,
     the absolute KV-cache memory of baseline and system, the relative drift
     percent, and the budget ratio `system_mem / baseline_mem`.
   - The aggregated report then places baseline and system on a single
     (budget, quality) Pareto plot so readers can judge the trade-off.
   - Rationale: a `{4, 8, 16}` bit allocator with non-trivial ratio of
     higher-bit layers **cannot**, by construction, stay within ±3% of a pure
     INT4 KIVI baseline without collapsing to full 4-bit (which erases the
     allocator). The C3 claim framing is therefore "Pareto extension into
     KIVI's unreachable (higher-budget, higher-quality) region", not
     "matched-budget winner". See §13 of `docs/thesis_story_20260420.md`.
   - Tooling: `scripts/check_system_vs_kivi_completeness.py` defaults to
     `--gate_mode pareto`; budget drift emits `info_budget_drift` rows that do
     not fail the gate. Passing `--gate_mode strict` restores the legacy
     ±3% behavior for sanity checks / ablations that specifically want a
     matched-budget subset.
3. Same decoding policy:
   - greedy decoding
   - `temperature=0`
   - `top_p=1`
   - `top_k=0`
4. Same decode backend policy:
   - `decode_attn_impl=torch_ref`
5. KIVI strongest-fair default:
   - `kv_mode=kivi_style`
   - `quant_bits=4`
   - `residual_length=0`

`residual_length=0` remains the frozen default because the earlier validated
INT4 RoleAlign path reported no measurable benefit from a residual buffer in the
canonical 1.5B comparison path.

## Current Runtime Mapping

The current executable mappings in the repository are:

| Formal system | Current runtime mapping | Cache path | Runtime family |
|---|---|---|---|
| `kivi_style` | `kv_mode=kivi_style` | `KIVIStyleKVCache` | `kivi_asym_family` |
| `rolealign_static` | `kv_mode=int4_ours_asym` + rolealign calib | `RoleAwareAsymKVCache` | `kivi_asym_family` |
| `rolealign_allocator_fixed_eqmem` | `kv_mode=int4_ours_asym_alloc` + rolealign calib + policy JSON | `RoleAwareAllocatorKVCache` | `kivi_asym_family` |
| `rolealign_allocator_auto_eqmem` | `kv_mode=int4_ours_asym_alloc` + rolealign calib + policy JSON | `RoleAwareAllocatorKVCache` | `kivi_asym_family` |

Additional backend constraints frozen by the current implementation:

- `int4_ours_asym_alloc` currently requires `decode_attn_impl=torch_ref`
- `int4_ours_asym_alloc` currently requires `residual_length=0`
- allocator policies are interpreted as per-layer `(k_bits, v_bits)` pairs
- supported per-layer bit values are `4`, `8`, and `16`

## Required Asset Status

Local rolealign calibration assets required by the formal package are present:

| Model key | Local path | Status | MD5 |
|---|---|---|---|
| `1p5b` | `artifacts/kv_calib_rolealign_1p5b.json` | present | `8d8fd9730ed6129613a16fdc267f9372` |
| `3b` | `artifacts/kv_calib_rolealign_3b_v3.json` | present | `3cfb416a8fe1054fc81a453dd1f00e1a` |
| `8b` | `artifacts/kv_calib_rolealign_8b_v3.json` | present | `0a8e2a298c4160ea35083309cc707faa` |
| `14b` | `artifacts/kv_calib_rolealign_14b_v3.json` | present | `a90f48f728bd078c7173416fe0e39f8d` |
| `mistral7b` | `artifacts/kv_calib_rolealign_mistral7b_v3.json` | present | `19a113081a70d9e26d9d002608f9dfaf` |

### Asset Provenance Notes

- `1p5b` and `14b` were already present locally before this backend enablement.
- `8b` was recovered from the existing remote repository artifact and copied
  back to local with MD5 parity check:
  - remote MD5: `0a8e2a298c4160ea35083309cc707faa`
  - local MD5: `0a8e2a298c4160ea35083309cc707faa`
- `3b` was newly calibrated on the remote clean workspace
  `/root/autodl-tmp/LLM_KVCache_Quantization_clean` and then copied back:
  - remote clean workspace HEAD: `ddada19`
  - output file: `artifacts/kv_calib_rolealign_3b_v3.json`
  - remote log: `logs/system_vs_kivi_g0_3b.log`
  - remote/local MD5: `3cfb416a8fe1054fc81a453dd1f00e1a`
- `mistral7b` was newly calibrated on the same remote clean workspace and then
  copied back:
  - remote clean workspace HEAD: `ddada19`
  - output file: `artifacts/kv_calib_rolealign_mistral7b_v3.json`
  - remote log: `logs/system_vs_kivi_g0_mistral7b.log`
  - remote/local MD5: `19a113081a70d9e26d9d002608f9dfaf`

These provenance notes are sufficient for `G0` because the current task is
backend enablement plus asset completion. Publishable claim tables will still
need the later clean-provenance official runs.

## G0 Machine-Checked Evidence

The following entry-point checks now pass locally:

```bash
python3 scripts/run_system_vs_kivi.py --phase smoke --dry_run
python3 scripts/run_system_vs_kivi.py --phase main --dry_run
python3 scripts/run_system_vs_kivi.py --phase ablation --dry_run
```

Observed dry-run coverage:

| Phase | Models | Systems | Tasks | Jobs | Result |
|---|---|---|---|---:|---|
| `smoke` | `1p5b,8b` | `3` | `2` | `42` | pass |
| `main` | `1p5b,3b,8b,14b,mistral7b` | `3` | `5` | `150` | pass |
| `ablation` | `3b,8b,mistral7b` | `4` | `5` | `120` | pass |

Machine-check meaning:

- no missing required asset failures
- no same-format runtime mismatch failures
- allocator systems now resolve to `int4_ours_asym_alloc`
- `int4_ours_asym_alloc` is accepted by the formal runner as
  `kivi_asym_family`

## Current G0 Verdict

`G0 Fairness Gate` is now **PASS** at the preflight / dry-run level.

That verdict is limited to:

1. runtime-family fairness enablement
2. required local calib asset completeness
3. phase entry-point validity for `smoke`, `main`, and `ablation`

It does **not** mean:

- official smoke has already been launched
- official main matrix has already been launched
- official mechanism ablation has already been launched
- any quality or systems claim has already been established

## Default Execution Parameters Frozen For Later Use

The current runner implementation freezes these provisional execution defaults:

- LongBench quality:
  - source: `jsonl` by default, overridable via environment
  - `longbench_max_samples=50`
- Latency / memory:
  - `seq_len=1024`
  - `gen_len=128`
- PPL:
  - dataset: `wikitext2`
  - `max_length=1024`
  - `target_tokens=4096`
- Needle:
  - `context_len=4096`
  - `num_depths=5`
  - `needle_max_new_tokens=32`
- RULER:
  - `seq_len=4096`
  - `gen_len=64`
  - `ruler_num_cases=64`

## Immediate Next Actions

With `G0` now passing, the next formal-package steps are:

1. launch the official smoke phase with clean-provenance logging
2. if smoke passes, enter the official main matrix
3. after `G1`, run the mechanism ablation
4. only then move to aggregation, statistics, and claim judgment

Until those runs exist, this document remains a preflight record, not a claim
document.
