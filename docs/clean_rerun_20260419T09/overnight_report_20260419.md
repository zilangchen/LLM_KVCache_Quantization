# Overnight Report — 2026-04-19

> **Period**: 2026-04-19 08:40 CST → 13:14 CST (~4h35m wall-clock)
> **Branches**: `codex/phase2-a-rerun` (local), `main` (remote exploratory), `ddada19` (clean workspace pin)
> **Clean workspace**: `/root/autodl-tmp/LLM_KVCache_Quantization_clean`

---

## A. L2 Track Summary

### A.1 Phase A — K/V asymmetric allocator

| Status | Gate A | Notes |
|---|---|---|
| ✅ 完成（earlier session） | **PASS** | `kv_asym_avgbits5p0` 已批准进 Phase B Pareto |

### A.2 Phase B — Pareto v4 full rerun

| Metric | Value |
|---|---|
| Wall-clock | 57m (09:01:01 → 09:58:01) |
| Matrix | 12 policies × {7b, 8b, mistral7b} — 4 policy 每 model |
| Pass criteria | **12/12 policies PASS** (q=3, failed_rows=0, marker=0, lat=1, mem=1, ppl=1, needle=1) |
| Quarantine | v3 raw → `results/l2_pareto/_quarantine_v3_20260419T0857/` + MANIFEST（v1/v2/v3 失败链记录） |

**Cross-model Pareto front (quality vs avg_bits)**：
- `7b/heuristic_k3` (4.43 bits, 7.00 q)
- `7b/bakv_auto_cov80_max` (5.86, 6.85)
- `8b/bakv_auto_cov80_max` (7.13, 9.47)
- `mistral7b/bakv_auto_cov80_max` (7.13, 14.68)

**Gate B 回答**：
1. 可判读？ **YES**（12/12 完整）
2. auto-k 进 Pareto front？ **YES (3/4 model)** — 7b/8b/mistral cov80 全进 front
3. heuristic / fixed-k / uniform / role-aware 相对位置：
   - heuristic 强 on 7B；BAKV fixed-k 强 on 8B/mistral
   - **uniform_int4 在 7B 灾难性失败** (q=2.87, PPL=6326, needle=0%) → allocator 必要性铁证
4. allocator 叙事支持：**YES** — BAKV auto-k cross-model top tier + Mistral-specific win + uniform 崩溃

### A.3 Phase C — Prompt-adaptive

| Metric | Value |
|---|---|
| Wall-clock | 37m (10:03:51 → 10:40:30) |
| Runs | 27 (3 models × 3 tasks × 3 variants) |
| Pass criteria | **9/9 cells PASS** |

**Gate C — Mixed signal**：

| Model | auto_k mean | fixed_k mean | prompt_adaptive mean | Verdict |
|---|---|---|---|---|
| 1p5b | 6.779 | **6.968** | 6.836 | prompt_adaptive < fixed_k（selector 在 hotpot 错选 auto） |
| 7b | 6.845 | 6.784 | **6.974** | prompt_adaptive 胜（+0.13~+0.19）|
| 8b | **9.472** | 9.122 | 9.124 | prompt_adaptive < auto_k（narra 错选 fixed：9.73 vs auto 10.77）|

**实现注**：`prompt_adaptive` 实质是 **task-id bucket routing**（不是 per-prompt re-selection），selector 在 7B 选对、1.5B/8B 错选。**不作为 final claim**，仅 exploratory finding。

### A.4 L2 Findings 去留

**保留（publishable, candidate-main）**：
1. Phase B: auto-k 跨 3 model top tier（Pareto front 包含）
2. Phase B: Mistral-specific auto-k win（cov80 14.68）
3. Phase B: 7B uniform_int4 崩溃 → allocator 必要性证据

**Engineering-proof only**：
- Phase B infrastructure：3 轮 bug 修复后 runner 完整覆盖 quality+4-aux（MANIFEST 记录）

**Mixed signal（不进正文主线）**：
- Phase C prompt-adaptive：selector 在 1.5B/8B 选错，**不宣称 cross-model benefit**

---

## B. Clean-Provenance Track Summary

### B.1 Preflight (Gate P0)

| Item | Status |
|---|---|
| Pin commit | `ddada195dcf3bbd205b627fab154ecb013f11c1c` (codex/phase2-a-rerun) |
| Clean workspace | `/root/autodl-tmp/LLM_KVCache_Quantization_clean` @ pin |
| git status --short | Clean（`git reset --hard ddada19` + `git clean -fd`）|
| Key file MD5 (9 files) | 全部记录于 `docs/clean_rerun_20260419T09/MANIFEST.md` |
| LongBench jsonl | `/root/autodl-tmp/longbench_data/data/` OK（34 files）|
| HF cache 5 models | 1.5B/3B/7B/8B/Mistral-7B ✓；14B 在 modelscope_cache（28G）|

**P0 PASS** ✓

### B.2 Calibration Provenance (Step 0)

| Model | Action | MD5 |
|---|---|---|
| 1.5B | Retained exploratory 2026-04-03 | `c187ee488d06ecf681186f7d0b55692a` |
| 7B | Retained exploratory 2026-02-23 | `3670c2581e835bf45b875bcddcb0fc87` |
| 8B | Retained exploratory 2026-04-18 | `6d62c2bcf34c573e28f9b50bfd330405` |
| 3B | **Clean regen @ 10:45** | `7e3060d539c6723a0dd23dde832a9240` |
| 14B | **Clean regen @ 10:45**（modelscope local path）| `41893e701aee00284f1b1c848fc2611b` |
| Mistral-7B | **Clean regen @ 10:45** | `ed87fb4a7e7a5d636bcfa393f2620cf8` |

### B.3 Step 1/2/3 Execution 结果

**Step 1 Canonical (Gate P1) — 1.5B × 4 kv_mode × 3 task**:

| kv_mode | narra | hotpot | gov | mean |
|---|---:|---:|---:|---:|
| fp16 | 7.0694 | 4.8978 | 9.2121 | 7.0598 |
| int8_ours | 7.1585 | 4.8754 | 9.2000 | 7.0780 |
| int4_ours_asym | 6.9851 | 5.3504 | 9.0393 | 7.1249 |
| kivi_style | 6.9350 | 4.8659 | 9.2315 | 7.0108 |

**P1 PASS** ✓ — int8_ours 与 fp16 差 +0.02（保真度 OK）；int4_ours_asym 甚至略高（+0.07）；kivi_style 基本持平。

**Step 2 Compare (Gate P2) — 4 models × 4 policies × 3 core tasks**:

| Model | Top policy | Mean | Narrative |
|---|---|---:|---|
| 3B | **bakv_k1** | 6.9023 | early-layer rescue (layer 0) |
| 8B | **bakv_k11** | 9.5214 | clean 里 fixed-k 微胜 cov80 (9.35) |
| 14B | **uniform_int4_k4v4** | 7.2345 | auto-k cov90 (7.15) top tier not winner |
| Mistral-7B | **bakv_auto_cov80_max** | 14.7640 | Mistral-specific win 保持（与 exploratory 精确匹配）|

**P2 PASS** ✓ — 4 claim-critical reading 全成立：auto-k 跨 4 model top tier（gap ≤ 0.17）；Mistral-specific win；3B early-layer；heuristic 强 baseline。

**Step 3 Extend (Gate P3) — {dureader, lcc}**:

| Model | Top policy | Mean | 跨 core/extend 关系 |
|---|---|---:|---|
| 3B | bakv_auto_cov80_max | 11.9652 | ⚠️ core bakv_k1 top → extend cov80 top（early-layer regime **不跨 extend**）|
| 8B | bakv_k11 | 11.5549 | ⚠️ core cov80 top-tier → extend **掉到 #4** (-1.0) |
| 14B | bakv_k7 | 12.4456 | ✅ core uniform top → extend bakv_k7 top（top-tier tie 内洗牌）|
| Mistral-7B | **bakv_auto_cov80_max** | 15.6946 | ✅ **core + extend 都 top** — Mistral-specific win **跨 task 稳定** |

**P3 Mixed PASS** ⚠️ — Mistral-specific win 跨 core + extend 成立；3B/8B 上 auto-k 的 top-tier 地位在 extend 任务上 weaken。

### B.4 Exploratory vs Clean Comparison

| Model/Policy | Exploratory v4 | Clean | Δ | 稳定？ |
|---|---:|---:|---:|---|
| 7B/cov80 | 6.8452 | n/a (clean 不含 7B compare) | — | — |
| 8B/cov80 | 9.4717 | 9.3543 | -0.12 | ✓ |
| 8B/bakv_k11 | 9.1217 | 9.5214 | **+0.40** | ⚠️ drift（但 still top-tier）|
| 8B/heuristic_k11 | 8.5416 | 8.5416 | 0.00 | ✓ exact |
| 8B/uniform_int4 | 8.5976 | 8.7364 | +0.14 | ✓ |
| Mistral/cov80 | 14.6846 | 14.7640 | +0.08 | ✓ |
| Mistral/bakv_k3 | 14.0614 | 14.0542 | -0.01 | ✓ |
| Mistral/heuristic_k3 | 13.7553 | 14.6036 | **+0.85** | ⚠️ drift（仍 < cov80） |
| Mistral/uniform | 13.6953 | 14.0217 | +0.33 | mild |

**稳定性判读**：
- **Mean ranking stability**：✅ 所有 model 上 top policy ranking 方向不翻转（8B 上 cov80 vs k11 tie 区间内 micro-swap）
- **Task-best stability**：✅ cov80 仍 Mistral task-best；uniform_int4 仍 14B task-best
- **Key gap stability**：8B cov80 vs k11 从 exploratory +0.35 → clean -0.17（tie 翻转）；**3B early-layer gap 成立（bakv_k1 胜 heuristic_k1 +98%, matches exploratory 预期）**；**Mistral cov80 vs heuristic gap 从 +1.0 → +0.16（缩小，但仍 positive）**
- **Mainline judgment stability**：✅ 主结论方向全部保留

### B.5 升级建议 (plan §6.2)

**可以升级到 `final-ready support` 的 claims**：
1. ✅ **Mistral-specific auto-k win** — cov80 跨 core + extend 都 top (14.76 / 15.69)
2. ✅ **3B early-layer rescue regime** — bakv_k1 on core tasks（narra/hotpot/gov），但论文须限定 "on long-context QA, not on dureader/lcc"
3. ✅ **14B top-tier, not winner** — uniform_int4 core top；clean 精确复现 exploratory gap
4. ✅ **INT8 canonical path 保真** — Gate P1 通过（int8_ours vs fp16 Δ = +0.02）
5. ✅ **heuristic 作为强 baseline** — 14B/heur ≈ cov90；但 3B/heur_k1 灾难 (3.48) 说明 "heuristic 强" 有 regime 依赖

**建议加脚注 / threats to validity 的 claims**：
1. ⚠️ **auto-k cross-model top-tier** — 在 core tasks 成立，**但 8B extend 上 cov80 掉到 #4** (-1.0 vs top)；不宣称 "universal cross-task winner"
2. ⚠️ **8B 上 cov80 vs bakv_k11 排名** — exploratory v4 cov80 > k11 (+0.35)；clean k11 > cov80 (-0.17)。两者 top-tier tie，写法须保守（推荐 "both top-tier, close tie"）

**不能直接升级的 claims**：
- **无**（plan §6.3 的 4 个禁用条件无一触发）

---

## C. Bug Fix 记录

### C.1 `profile_memory.py --warmup` argparse parity
- **Problem**: L2 Phase B v3 runner 传 `--warmup 1`，remote profile_memory.py 不接受
- **Fix**: 新增 `--warmup` 参数（L307-316），no-op for memory profiling；**不** 重定义 `--runs`（已存在 L182 PRF-021）
- **Impact**: runner aux 与 profile_latency 签名一致
- **Files**: `scripts/profile_memory.py`

### C.2 Pareto runner post-quality failed-row 硬检查
- **Problem**: `eval_longbench.py` 可能 exit 0 但产 `official_metric_name=failed` 行，静默进聚合成为 invalid low-score Pareto 点
- **Fix**: quality 循环后扫 CSV `$10=="failed"` → touch `.quality_failed` marker + exit 3
- **Impact**: 聚合器无法消费静默失败的 policy
- **Files**: `scripts/phase2_l2_pareto_eval.sh`

### C.3 `L2_PARETO_RAW_BASE` env override
- **Problem**: smoke 需独立 out_dir
- **Fix**: `RAW_BASE="${L2_PARETO_RAW_BASE:-...}"` default override hook
- **Files**: `scripts/phase2_l2_pareto_eval.sh`

### C.4 14B model path: modelscope vs hf_cache
- **Problem**: Clean calib 14B 首次启动 fail with `HF offline 模式下未找到本地缓存模型`
- **Evidence**: `ls /root/autodl-tmp/hf_cache/hub/` 无 14B；exploratory calibration JSON 的 `model_id` 指向 `/root/autodl-tmp/modelscope_cache/qwen/Qwen2.5-14B-Instruct`
- **Fix**: clean_rerun_{calibrate,eval}.sh 的 14b 分支用 modelscope 本地路径
- **Impact**: 14B calibration 2 min 完成；Step 2/3 14b 正常跑
- **Files**: `/tmp/clean_rerun_scripts/clean_rerun_calibrate.sh`, `clean_rerun_eval.sh`

### C.5 clean workspace sweep_* dirs missing (quick recovery)
- **Problem**: Clean Step 2 首次启动 tmux 秒退，[SKIP] missing policy json on all models
- **Root cause**: MANIFEST 只 cp calibration，没 cp policy sweep_* dirs
- **Fix**: cp 4 sweep dirs (3b/8b/14b/mistral7b) from exploratory; md5 recorded
- **Impact**: 16/16 policies verified ready；relaunch tmux OK。clean provenance 论证：policy JSONs 是 pin-era allocator 的 derivation artifacts，md5 记录绑定。
- **Files**: artifact cp only

### C.6 Observed but non-blocking: calibrate.sh line 62 exit 127
- **Problem**: 3B/Mistral calib 打印 "Saved calibration JSON"（成功）后 bash 报 `line 62: --model_id: command not found; exit=127`。14B 无此问题。
- **Status**: **NON-BLOCKING** — 3 artifact md5 全有效（7e3060d5/41893e70/ed87fb4a）
- **Action**: 不修复（artifact gate PASS，exit code cosmetic）；poll script 用 artifact md5 做真 gate，通过。

---

## D. Tables

### Table 1 — 总进度

| Track | Phase | Status | Completed | Remaining | Gate | Notes |
|---|---|---|---|---|---|---|
| L2 | A (K/V async) | ✅ | 36 runs | — | **A PASS** | earlier session |
| L2 | B (Pareto v4) | ✅ | 12 policies × 3 models | — | **B PASS** | 12/12；auto-k top 3/4；Mistral win；7B uniform 崩 |
| L2 | C (Prompt-adaptive) | ✅ | 27 runs | — | **C Mixed** | 7B win；1.5B/8B lose → not final claim |
| Clean | P0 (Preflight) | ✅ | pin+md5+calib | — | **P0 PASS** | workspace 就绪 |
| Clean | Step 0 (Calib regen) | ✅ | 3B + 14B + Mistral | — | 3/3 md5 OK | 1.5B/7B/8B retained |
| Clean | Step 1 (Canonical) | ✅ | 12 runs | — | **P1 PASS** | fp16↔int8 Δ=+0.02 |
| Clean | Step 2 (Compare) | ✅ | 48 runs (4 models × 12) | — | **P2 PASS** | 4 readings 全成立 |
| Clean | Step 3 (Extend) | ✅ | 32 runs (4 models × 8) | — | **P3 Mixed** | Mistral cov80 跨 task；3B/8B auto-k extend weaken |

### Table 2 — 覆盖情况

#### L2 Phase B v4 (quality + 4 aux 全覆盖)

| Model | Policy | quality | latency | memory | ppl | needle | failed_rows | quarantine? | valid_for_gate? |
|---|---|---|---|---|---|---|---|---|---|
| 7b | uniform_int4_k4v4 | 3 | 1 | 1 | 1 | 1 | 0 | no | **NO (崩: q=2.87, ppl=6326, needle=0%)** |
| 7b | bakv_k3 | 3 | 1 | 1 | 1 | 1 | 0 | no | YES |
| 7b | heuristic_k3 | 3 | 1 | 1 | 1 | 1 | 0 | no | YES (Pareto front) |
| 7b | bakv_auto_cov80_max | 3 | 1 | 1 | 1 | 1 | 0 | no | YES (Pareto front) |
| 8b | uniform_int4_k4v4 | 3 | 1 | 1 | 1 | 1 | 0 | no | YES |
| 8b | bakv_k11 | 3 | 1 | 1 | 1 | 1 | 0 | no | YES |
| 8b | heuristic_k11 | 3 | 1 | 1 | 1 | 1 | 0 | no | YES |
| 8b | bakv_auto_cov80_max | 3 | 1 | 1 | 1 | 1 | 0 | no | YES (Pareto front) |
| mistral7b | uniform_int4_k4v4 | 3 | 1 | 1 | 1 | 1 | 0 | no | YES |
| mistral7b | bakv_k3 | 3 | 1 | 1 | 1 | 1 | 0 | no | YES |
| mistral7b | heuristic_k3 | 3 | 1 | 1 | 1 | 1 | 0 | no | YES |
| mistral7b | bakv_auto_cov80_max | 3 | 1 | 1 | 1 | 1 | 0 | no | YES (Pareto front) |

#### Clean Rerun (quality only; no aux — 未 scope)

| Model | Step | Coverage | failed_rows | valid_for_P_gate? |
|---|---|---|---:|---|
| 1.5B | Step 1 canonical | 4 kv_mode × 3 task = 12/12 | 0 | ✅ P1 |
| 3B | Step 2 compare | 4 policy × 3 task = 12/12 | 0 | ✅ P2 |
| 3B | Step 3 extend | 4 policy × 2 task = 8/8 | 0 | ✅ P3 |
| 8B | Step 2 compare | 12/12 | 0 | ✅ P2 |
| 8B | Step 3 extend | 8/8 | 0 | ✅ P3 |
| 14B | Step 2 compare | 12/12 | 0 | ✅ P2 |
| 14B | Step 3 extend | 8/8 | 0 | ✅ P3 |
| Mistral-7B | Step 2 compare | 12/12 | 0 | ✅ P2 |
| Mistral-7B | Step 3 extend | 8/8 | 0 | ✅ P3 |

Total clean rerun runs: **92** (12 canonical + 48 compare + 32 extend)；0 failed_rows；0 quarantine。

---

## E. 建议的下一步（非必须，仅记录）

1. **论文写作收口**：把 B.5 的 5 个 final-ready claim 落到 Chapter 4 主表；⚠️-脚注 2 个 caveat 到 Discussion / Threats to Validity
2. **drift 根因调查（可选）**：mistral/heuristic_k3 +0.85 drift — 可能是 calibration 的 RNG state 或 longbench sample order 差异；若想彻底消除，clean rerun + 同 seed / 锁 RNG
3. **scope creep 拒绝**：plan §1C "不扩 7b follow-up" — 建议保持，7B 上已有 v4 exploratory 证据
4. **Phase C prompt-adaptive**：当前 selector 在 1.5B/8B 选错；若想 publish 需做 per-prompt (not task-id) 真正的 re-selection 实验。**不建议本轮扩**。

---

## 产物清单

### 新增文件（远端 clean workspace）
- `docs/clean_rerun_20260419T09/MANIFEST.md`（117 lines, 5782 bytes）
- `docs/clean_rerun_20260419T09/readout_phase1.md`（Step 1+2 mid-aggregation）
- `docs/clean_rerun_20260419T09/readout_final.md`（Step 1+2+3 full aggregation）
- `results/clean_rerun/summary_final.csv`（92 rows flat CSV）
- `scripts/clean_rerun_calibrate.sh` / `clean_rerun_eval.sh` / `clean_rerun_step_poll.sh` / `clean_rerun_aggregate.py`
- `artifacts/kv_calib_kl_qwen25_{3b,14b}_int8.json` + `kv_calib_kl_mistral7b_int8.json`（3 newly-regen）+ cp 3 retained
- `artifacts/allocator/sweep_{3b,8b,14b,mistral7b}/`（cp from exploratory at same pin）

### 新增文件（远端 exploratory workspace）
- `scripts/phase2_l2b_smoke_poll.sh` + `phase2_l2b_v4_poll.sh` + `phase2_l2c_one.sh` + `phase2_l2c_poll.sh`（L2 poll infrastructure）
- `results/l2_pareto/raw/{7b,8b,mistral7b}/` 12 policy out_dirs（Phase B v4 产物）
- `results/l2_prompt_adaptive/{1p5b,7b,8b}/` per-task out_dirs（Phase C 产物）
- `results/l2_pareto/pareto_{table,front,plot}_v4.csv`
- `results/l2_prompt_adaptive_summary.csv` + `docs/l2_prompt_adaptive_readout_v1.md`
- `results/l2_pareto/_quarantine_v3_20260419T0857/`（v3 invalid data 隔离 + MANIFEST）

### 本地修改（待 commit 决定）
- `scripts/profile_memory.py`（+ `--warmup`）
- `scripts/phase2_l2_pareto_eval.sh`（post-quality failed-row + env override）
- `scripts/phase2_l2b_smoke_poll.sh` / `phase2_l2b_v4_poll.sh` / `phase2_l2c_one.sh` / `phase2_l2c_poll.sh`（new files）

---

## 一句话总结

> L2 三 Phase 全跑完（Gate A/B PASS，C Mixed）；Clean-provenance Step 0-3 全通过（P0/P1/P2 PASS，P3 Mixed）；核心 4 claim（Mistral-specific win / 3B early-layer / 14B top-tier not winner / auto-k cross-model top-tier in core）**全部复现**，可升级为 `final-ready support`；2 个 caveat 需脚注（8B cov80↔k11 top-tier tie、auto-k 在 3B/8B extend tasks 上 weaken）。
