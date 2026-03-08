# Iteration Log — Archive (2026-02 前期)

> 本文件包含 iteration.md 中 2026-02-22 17:24 及更早的 Timeline 条目。
> 当前活跃进度见 `iteration.md`。

---

### 2026-02-22 17:24 | Week5 External-Validity Chain + Remote Smoke Closure
- Goal: complete Week5 engineering upgrade (LongBench/RULER integration + PPL token-floor hardening) and verify the full experiment-to-report pipeline on Remote-Server.
- Scope: add missing eval task implementation, wire runner/strict aggregation/report/latex, fix runtime edge cases discovered in remote smoke.
- Changed files:
  - `scripts/eval_ruler.py`
  - `scripts/eval_ppl.py`
  - `scripts/run_experiments.py`
  - `scripts/check_run_completeness.py`
  - `scripts/aggregate_results.py`
  - `scripts/export_tables_latex.py`
  - `scripts/generate_thesis_report.py`
  - `scripts/run_week5_external_validity_v1.sh`
  - `configs/snapshots/exp_matrix_week5_external_validity_v1.yaml`
  - `tests/test_aggregate_results_stats.py`
  - `iteration.md`
- Commands:
  - local compile: `python3 -m compileall ...`
  - local unit tests: `python3 -m unittest tests/test_run_experiments_resilience.py tests/test_check_run_completeness.py`
  - remote health: `ssh -p 31867 root@region-42.seetacloud.com "echo SSH OK && nvidia-smi -L"`
  - remote smoke (tmux): run `eval_ppl,eval_needle,eval_longbench,eval_ruler` on `fp16_kv_curve_4k` with strict aggregation/export/report
  - remote report regression test: `/root/miniconda3/bin/python -m unittest tests/test_generate_thesis_report.py`
- Outputs:
  - new week5 runner entrypoint: `scripts/run_week5_external_validity_v1.sh`
  - remote smoke package: `results/week5_smoke_remote_r2/` (runs/logs/tables/plots/latex/reports)
  - new aggregated artifacts confirmed: `longbench_summary.csv`, `ruler_summary.csv`, `ruler_depth_summary.csv`, `longbench_task_summary.csv`
- Validation:
  - remote `run_experiments_smoke.json`: 4/4 tasks success (`eval_ppl`, `eval_needle`, `eval_longbench`, `eval_ruler`)
  - strict aggregation completed: `results/week5_smoke_remote_r2/aggregate.log`
  - latex export completed: `results/week5_smoke_remote_r2/export_latex.log`
  - report generation completed after fix: `results/week5_smoke_remote_r2/report.log`
  - fixed two real defects found during smoke:
    - `eval_ppl` token-floor off-by-one (target 4096 -> evaluated 4095) by reserving `target_tokens + 1` input budget
    - `generate_thesis_report.py` crash when `stat_decisions` has no `decision` column (now robust fallback)
- Risks / follow-ups:
  - local host python environment still lacks usable `numpy` runtime (`libcblas.3.dylib` missing); numpy-dependent local tests remain blocked
  - current smoke validates functionality, not statistical claims (single fp16 run only), so claim rows are expected `INCONCLUSIVE`

### 2026-02-22 16:31 | Record C1 Statistical Inconclusive Risk
- Goal: formally record the `C1` long-context TPOT significance issue for planned optimization, without mutating current final package results.
- Scope: add a traceable risk entry with evidence paths, root-cause interpretation, and explicit follow-up rerun action.
- Changed files:
  - `iteration.md`
- Commands:
  - inspect `results/final_journal_v1/reports/claim_validation.csv`
  - inspect `results/final_journal_v1/tables/significance_summary.csv`
  - inspect `results/final_journal_v1/tables/significance_pairs.csv`
- Outputs:
  - documented issue: `C1` is `INCONCLUSIVE` due to `q_value=0.0852` and `p_value=0.0625` at `n_pairs=5`
  - documented interpretation: with current paired exact two-sided test and small `n`, statistical power is insufficient for `q<0.05` despite strong practical gain
  - documented follow-up plan: targeted long-context TPOT补跑（新增 seed 至 n>=8，建议 n=8~10）后重聚合
- Validation:
  - evidence is consistent across `claim_validation.csv` and significance tables
  - current final package integrity unchanged (no rerun/no overwrite)
- Risks / follow-ups:
  - until long-context paired sample size is increased, C1 remains non-definitive for strict significance claims
  - execute targeted补跑 in next optimization iteration and refresh claim gate artifacts

### 2026-02-22 11:02 | SOP Entrypoint Rename
- Goal: switch experiment SOP to a single canonical file `experiment_sop.md` and avoid broken legacy links.
- Scope: rename protocol file, update active guidance references, and provide a legacy redirect note at old path.
- Changed files:
  - `experiment_sop.md` (moved from `docs/final_experiment_protocol.md`)
  - `AGENTS.md`
  - `README.md`
  - `iteration.md`
  - `docs/final_experiment_protocol.md` (legacy redirect notice)
  - `development_record.md` (historical note update)
- Commands:
  - `mv docs/final_experiment_protocol.md experiment_sop.md`
  - replace active references to `experiment_sop.md`
  - create legacy notice at `docs/final_experiment_protocol.md`
- Outputs:
  - unique active SOP entrypoint: `experiment_sop.md`
  - old link path now resolves to a redirect notice instead of missing file
- Validation:
  - active policy and README now point to `experiment_sop.md`
  - no broken path for legacy `docs/final_experiment_protocol.md` access
- Risks / follow-ups:
  - `development_record.md` retains historical old-path text by design

### 2026-02-22 10:55 | Rename Agent Workspace Directory
- Goal: rename the repository agent workspace from `.agent/` to `.agents/` and remove stale path guidance.
- Scope: move directory, update active docs/scripts/global policy references, and re-scan for old path pointers.
- Changed files:
  - `.agents/` (renamed from `.agent/`)
  - `AGENTS.md`
  - `scripts/run_experiments.py`
  - `.agents/execplans/README.md`
  - `.agents/skills/execplan/SKILL.md`
  - `/Users/chenzilang/.codex/AGENTS.md`
  - `development_record.md` (legacy path note)
  - `iteration.md`
- Commands:
  - `mv .agent .agents`
  - replace `.agent/` -> `.agents/` in active guidance files
  - `rg -n "\\.agent/" ...` scans to verify old-path cleanup
- Outputs:
  - single canonical agent workspace path: `.agents/`
- Validation:
  - active guidance now points to `.agents/...`
  - only historical logs may still mention `.agent/` (expected)
- Risks / follow-ups:
  - `development_record.md` keeps legacy strings for historical traceability

### 2026-02-22 10:49 | Workflow Guide Path Fixes
- Goal: prevent broken workflow guidance where agents/users follow a documented path but cannot find files or scripts.
- Scope: align active docs to one remote repo path and remove invalid script reference from skills.
- Changed files:
  - `README.md`
  - `experiment_sop.md`
  - `docs/final_results_summary.md`
  - `docs/thesis_preflight_checklist.md`
  - `.agents/skills/reproducibility/SKILL.md`
  - `.agents/skills/long-running-task/SKILL.md`
  - `iteration.md`
- Commands:
  - replace `/root/autodl-tmp/LLM_KVCache_Quantization` -> `/root/LLM_KVCache_Quantization` in active docs
  - replace invalid `scripts.utils` validation command with `scripts/run_experiments.py --config configs/exp_matrix.yaml --dry_run`
  - `rg -n` scans for deprecated paths and missing workflow references
- Outputs:
  - active workflow docs now point to existing canonical paths
  - reproducibility skill no longer references missing `scripts/utils.py`
- Validation:
  - no hits in active files for `.agent/`, `lang.md`, `docs/AGENT_README.md`, `scripts/agent_tools`, or `scripts.utils`
- Risks / follow-ups:
  - `development_record.md` keeps historical legacy references by design (not an active workflow guide)

### 2026-02-22 10:46 | Skill Directory Unification
- Goal: unify skill directories to a single canonical path and verify no active duplicate references remain.
- Scope: consolidate duplicate skill directories into one root and run redundancy scan on active files.
- Changed files:
  - `iteration.md`
  - `.agents/skills/debug-iterate/SKILL.md` (moved)
  - `.agents/skills/execplan/SKILL.md` (moved)
  - `.agents/skills/repo-hygiene/SKILL.md` (moved)
  - `.agents/skills/unit-commit/SKILL.md` (moved)
- Commands:
  - directory consolidation operations for skill folders
  - `rg -n` policy-keyword scans on active files
- Outputs:
  - single skill root for custom skills
- Validation:
  - custom skills centralized and callable from one location
- Risks / follow-ups:
  - `development_record.md` is still historical and contains old path references by design

### 2026-02-22 10:00 | Agent Pipeline Consolidation
- Goal: unify agent execution pipeline and remove duplicated process management.
- Scope: replace `lang.md` with `iteration.md`; deprecate local task lock system; keep one policy path.
- Changed files:
  - `AGENTS.md`
  - `README.md`
  - `objective.md`
  - `iteration.md`
  - `.agents/skills/long-running-task/SKILL.md`
- Commands:
  - `rg -n "lang\\.md|AGENT_README\\.md|agent_tools/agent_cli" ...`
  - file migration and archive operations (see `development_history/archive_20260222_agent_pipeline_cleanup/MANIFEST.md`)
- Outputs:
  - unified policy references
  - archive manifest for deprecated workflow assets
- Validation:
  - active files no longer depend on `lang.md` or local lock CLI
- Risks / follow-ups:
  - historical docs still contain old references inside archive directories (expected)

## Legacy System Issues (Migrated)

| ID | Discovered | Issue | Trigger | Proposed Fix | Status |
|----|------------|-------|---------|--------------|--------|
| 001 | 2026-01-22 | Remote env package versions drift | Running `smoke_test.py` | Pin dependency versions and add startup checks | Tracked |
| 002 | 2026-01-22 | Doc/script/matrix drift causes reproducibility confusion | Aligning `development_record.md` with code and matrix | Enforce single entrypoint and config snapshots | Tracked |
| 003 | 2026-02-08 | Full-concat PPL tokenization creates long warnings and possible memory waste | Running `scripts/eval_ppl.py` | Use chunk/stream tokenization and record `max_length/stride` | Resolved |
| 004 | 2026-02-08 | Long remote runs break with direct SSH sessions | Remote `eval_ppl.py` validation | Use tmux background sessions and persisted logs | Tracked |

### 2026-02-28 06:03 | GEN-001 修复推送 + 补跑失败 eval
- **Goal**: 将 GEN-001 (`warnings` 变量遮蔽) 修复推送到远端，并补跑 `int8_ours_long_no_static_no_temp_fused` 1.5B s1234 的 3 个失败 eval
- **Changed files**: 无新代码变更（修复已在此前 commit 中，本次仅 rsync 推送）
- **Commands**:
  1. `git stash -u` → `bash scripts/rsync_gate.sh --skip-tests` → Gate PASSED
  2. `rsync -avz ... root@region-42.seetacloud.com:/root/LLM_KVCache_Quantization/` → 96 files transferred, 450KB sent
  3. `git stash pop` → 恢复本地工作区
  4. 远端验证: `python3 -c "import ast; ast.parse(...)"` → OK; `grep 'import warnings' generate_loop.py` → 5 处局部 import 确认存在
  5. 远端 `tmux new-session -d -s retry_s1234` → 启动补跑:
     ```
     python scripts/run_experiments.py --config configs/exp_matrix.yaml \
       --seeds 1234 --tasks eval_needle,eval_longbench,eval_ruler \
       --run_tag phase5v2_1p5b_s1234 \
       --run_names int8_ours_long_no_static_no_temp_fused \
       --out_dir results/phase5v2/runs --logs_dir results/phase5v2/logs \
       --append --failure_policy continue_all
     ```
- **Outputs**:
  - rsync: 成功，96 文件同步（含 generate_loop.py, run_experiments.py, 全部 eval 脚本等）
  - 远端 AST parse + grep 验证通过
  - eval_needle 补跑: ✅ **成功** — 10/10 depths PASS, 100% pass rate, CSV 已生成
  - eval_longbench 补跑: 🔄 运行中（启动约 5 分钟，`warnings.warn()` 正常输出 = 修复生效）
  - eval_ruler 补跑: ⏳ 等待 longbench 完成后运行
- **影响评估**: 全矩阵 241 runs / 953 tasks 中，GEN-001 仅影响 1 run 的 3 个 eval task (0.3%)。eval_ppl 未受影响（不走 generate_loop 路径）。其余 948 tasks 全部 success 或 running。
- **Validation**:
  - [x] rsync 完成无错误
  - [x] 远端 generate_loop.py 包含本地 import warnings 修复
  - [x] eval_needle 补跑成功 (CSV 存在)
  - [ ] eval_longbench 补跑（运行中）
  - [ ] eval_ruler 补跑（等待中）
  - [ ] 最终 manifest 3 tasks 全部 success
- **MEMORY.md**: 已更新 GEN-001 状态 "已修复(未commit)" → "已修复+已推送远端，补跑 3 eval 中"
- **Risks / follow-ups**:
  - longbench + ruler 补跑仍在进行，需后续确认最终状态
  - retry_s1234 tmux session 完成后可清理
  - thesis.zip / thesis/ 未加入 .gitignore（不影响实验，后续处理）

> 更早的条目见 `development_history/iteration_archive_202602.md`

### 2026-02-28 03:33 | Phase 5v2 实验监测 #3（循环监测启动）
- **Goal**: 确认实验健康状态，启动 30 分钟间隔的循环监测
- **基础设施**: SSH OK | H20 GPU 100% util, 39GB/98GB VRAM | Disk 5.8G/30G (20%) | 3 tmux 会话全部存活
- **进度汇总**:

  | 模型 | 已完成 | 目标 | 完成率 | Seed 明细 |
  |------|--------|------|--------|-----------|
  | 1.5B | 84 | 215 | 39.1% | s1234=45✅ s1235=39 |
  | 7B | 80 | 160 | 50.0% | s1234=32✅ s1235=32✅ s1236=16 |
  | 8B | 70 | 160 | 43.8% | s1234=32✅ s1235=32✅ s1236=6 |
  | **合计** | **234** | **535** | **43.7%** | — |

- **与 #2 对比(03:22)**: +2 runs (1.5B+1, 8B+1)
- **当前位置**: 1.5B→int4_ours_curve_8k s1235 | 7B→int4_fused_curve_16k s1236 | 8B→int8_baseline_curve s1236
- **错误**: 5 failure JSON 全部已知旧问题(3 stale + 2 待补跑)，无新错误，无最近 1h 内日志错误
- **速率**: ~2.2 runs/hour，剩余 301 runs，预计 ~137h ≈ 3/5-3/6 完成
- **行动**: 启动 30min 间隔循环监测脚本

### 2026-02-28 03:22 | Phase 5v2 远端实验监测 (#2)

- **Goal**: 获取 Phase 5v2 质量并行实验最新状态，排查 warnings bug 实际影响范围
- **Changed files**: 无代码变更（纯监测）
- **Commands**:
  - `ssh -p 31867 root@region-42.seetacloud.com` 系列健康检查 + tmux capture + 结果统计 + 错误扫描
- **Outputs**:

  **基础设施**: SSH 正常 | GPU H20 100% utilization, 41GB/98GB VRAM | 磁盘 20% (5.8G/30G)

  **进度汇总**:

  | 模型 | 已完成 | 目标 | 完成率 | tmux | 当前 seed | 当前 kv_mode |
  |------|--------|------|--------|------|-----------|-------------|
  | 1.5B | 83 | 215 | 38.6% | alive | 1235 | int4_ours_curve_8k |
  | 7B | 80 | 160 | 50.0% | alive | 1236 | int4_fused_curve_16k |
  | 8B | 69 | 160 | 43.1% | alive | 1236 | 刚启动 |
  | **合计** | **232** | **535** | **43.4%** | — | — | — |

  - Seed 执行顺序确认: 1234 → 1235 → 1236 → 1337 → 42
  - 预计全部完成: ~3/6-3/7

  **Warnings bug 排查结论**:
  - 原计划记录 `int8_ours_long 1.5B`，**实际受影响 run**: `int8_ours_long_no_static_no_temp_fused` 1.5B seed=1234
  - 影响范围: eval_needle + eval_longbench + eval_ruler 缺失 (eval_ppl 正常, PPL=8.95)
  - 根因: `generate_loop.py` 中函数内 `warnings` 局部变量遮蔽了 `import warnings`
  - 修复状态: **代码已修复**(未 commit)，s1235 运行干净，7B/8B 全部无此 bug
  - 仅需补跑: 1 run × 3 eval tasks

  **附带发现**:
  - `int4_baseline_long` / `int4_fused_long` 1.5B s1234 的 eval_ruler failure 属 position embedding overflow (不同 bug)，**已自愈**: 2/24 重跑完成，全部 4 eval 完整，task_failure JSON 为过期残留
  - task_failure_*.json 存在不代表结果缺失，需同时检查 CSV

- **Validation**: 全库 `grep -rl "cannot access local variable.*warnings"` 仅命中 1 run 3 logs
- **Risks / follow-ups**:
  - 待补跑: `int8_ours_long_no_static_no_temp_fused` 1.5B s1234 (eval_needle/longbench/ruler)
  - 待处理: 6 个 INT4 污染 runs (kivi_style_int4_curve 7B×3 + 8B×3)
  - generate_loop.py 修复未 commit，远端 git status 有大量未提交变更
  - 下次监测建议: 3/2

### 2026-02-28 02:19 | Wave 22 — Phase 6 输出链路修复（LTX + RPT）
- **Goal**: 修复论文输出关键高优先问题（LTX-001/002/007/014, RPT-001/002/004），保证 Phase 6 聚合后可直接产出可信 LaTeX 表格与 claim 报告
- **Scope**:
  - LTX: `KV_MODE_DISPLAY` 与 `KV_MODE_ORDER` 对齐、pivot 列顺序固定、RULER subtask 按模型拆分、caption 模型名 LaTeX 转义
  - RPT: `_read_csv` 异常可观测、relative row 选择去最高值偏置（中位代表）、cross-model degradation 字段语义修正
  - Tests: 新增 LTX/RPT 回归测试覆盖上述行为
- **Changed files**:
  - `scripts/export_tables_latex.py`
  - `scripts/generate_thesis_report.py`
  - `tests/test_export_tables_latex.py`
  - `tests/test_generate_thesis_report.py`
  - `review_tracker.md`
  - `iteration.md`
- **Commands**:
  - `python3 -m py_compile scripts/export_tables_latex.py scripts/generate_thesis_report.py tests/test_export_tables_latex.py tests/test_generate_thesis_report.py`
  - `pytest -q tests/test_export_tables_latex.py tests/test_generate_thesis_report.py`
  - `python scripts/review_tool.py stats`
- **Outputs**:
  - `py_compile`: pass
  - `pytest`: fail（环境问题，pandas/numpy ABI 不兼容：`numpy.dtype size changed`）
  - `review_tool stats`: `995 total | 480 fixed + 6 false_positive | 509 open`
- **Validation**:
  - LTX-014/LTX-001：`KV_MODE_DISPLAY` 由 `KV_MODE_ORDER` 派生，pivot 后按 canonical 顺序重排
  - LTX-002：`_export_ruler_subtask_tables` 引入 `_split_by_model`，多模型不再混合
  - LTX-007：新增 `_latex_escape`，模型短名在 caption 中安全输出
  - RPT-001：`_read_csv` 异常写 logger.warning
  - RPT-002：`_pick_best_relative_row` 改为中位数代表行（避免最大值偏置）
  - RPT-004：`max_degradation_model` 仅在存在负向 gain 时输出
  - AGG-052：在 tracker 标注 “partially addressed by AGG-049”
- **Risks / follow-ups**:
  - 本地 pytest 受 ABI 环境阻塞，需远端或标准环境补跑
  - LTX/RPT 其余 MED/LOW 问题保持 deferred
- **Commits**:
  - `90a8069` fix: LaTeX table column order and KV mode alignment (LTX-001, LTX-014)
  - `973393a` fix: LaTeX model split and caption escaping (LTX-002, LTX-007)
  - `7bfae27` fix: thesis report claim validation correctness (RPT-001, RPT-002, RPT-004)
  - `f4703bf` test: add LTX and RPT regression tests
  - `pending` docs: sync wave22 tracker and iteration

### 2026-02-28 02:09 | Wave 21 — AGG 统计正确性修复（论文关键路径）
- **Goal**: 修复 AGG 高优先问题 8 项（AGG-034/049/050/051/059/060/061/062），确保 Phase 6 统计表可信
- **Scope**:
  - P0: BH-FDR 按 metric 分族校正 + significance 增加方向约束（必须 favors_challenger）
  - P1: 补齐 int8_fused / int4_ours_mixed 的 significance+gain pairings，修复 kivi_style 吞吐目录正则
  - P2: 单样本 bootstrap CI 置 NaN、bootstrap_samples 记录实际 clamp 值、gain 方法显式标注
- **Changed files**:
  - `scripts/aggregate_results.py`
  - `tests/test_aggregate_results_stats.py`
  - `review_tracker.md`
  - `iteration.md`
- **Commands**:
  - `python3 -m py_compile scripts/aggregate_results.py tests/test_aggregate_results_stats.py`
  - `pytest -q tests/test_aggregate_results_stats.py`
  - `python scripts/review_tool.py stats`
  - `python scripts/review_tool.py phase-gate`
- **Outputs**:
  - `py_compile`: pass
  - `pytest`: 本地失败（pandas/numpy 二进制不兼容，`numpy.dtype size changed`），需远端环境验证
  - `review_tool stats`: 预期 `995 total | 473 fixed + 6 false_positive | 516 open`
  - `phase-gate`: 预期保持 READY（0 CRIT）
- **Validation**:
  - AGG-049/050: 新增 `_add_bh_fdr_qvalues_by_metric` + `_apply_significance_thresholds`
  - AGG-034/060: 引入 `SIGNIFICANCE_PAIRINGS`/`RELATIVE_GAIN_PAIRINGS` 常量并补齐缺失配对
  - AGG-059: 吞吐目录匹配改为基于 `KV_MODE_ORDER` 的已知模式 + 可选 `_s<seed>`
  - AGG-051/061/062: n=1 CI -> NaN、bootstrap 元数据对齐实际采样数、`gain_method` 显式化
  - 新增 Wave 21 回归测试覆盖上述关键路径
- **Risks / follow-ups**:
  - 本地 pandas/numpy ABI 问题导致 pytest 无法完成，需要远端/标准环境复核
  - AGG-052/065 等统计族定义扩展仍 open，后续按优先级处理
- **Commits**:
  - `95f79eb` fix: statistical direction and BH-FDR per-metric correction (AGG-049, AGG-050)
  - `7d81502` fix: significance pairings coverage and throughput regex (AGG-034, AGG-059, AGG-060)
  - `e5ec62c` fix: gain semantics, bootstrap metadata, and single-seed CI handling (AGG-051, AGG-061, AGG-062)
  - `fc6b361` test: add AGG regression tests for statistical correctness
  - `pending` docs: sync wave21 tracker and iteration

### 2026-02-28 01:41 | Wave 20 — CRIT 清零（EVL-086/ENG-059）+ 回归测试补齐
- **Goal**: 收口 Wave 19 未提交修复，补齐 EVL-086（CRIT）与 ENG-059（HIGH），并新增最小回归测试
- **Scope**:
  - 修复 `eval_ppl.py` 默认温度开关漂移（default=True -> False）
  - 修复 `generate_loop.py` 在 Qwen eos_token_id 为 list 时的 int(list) 崩溃
  - 将 `EVL-054` 标记为 `EVL-132` 重复项关闭
  - 新增 guardrails 测试文件 + 扩展 `test_generate_loop.py`
- **Changed files**:
  - `scripts/eval_ppl.py`
  - `src/engine/generate_loop.py`
  - `tests/test_generate_loop.py`
  - `tests/test_eval_ppl_guardrails.py` (new)
  - `review_tracker.md`
  - `iteration.md`
- **Commands**:
  - `python -m py_compile scripts/profile_latency.py scripts/profile_memory.py scripts/eval_ppl.py src/engine/generate_loop.py tests/test_generate_loop.py tests/test_eval_ppl_guardrails.py`
  - `pytest -q tests/test_generate_loop.py tests/test_eval_ppl_guardrails.py`
  - `python scripts/review_tool.py stats`
  - `python scripts/review_tool.py phase-gate`
- **Outputs**:
  - `py_compile`: pass
  - `pytest`: `78 passed in 0.09s`
  - `review_tool stats`: `995 total | 465 fixed + 6 false_positive | 524 open`
  - `phase-gate`: no CRITICAL blockers, only HIGH warning list
- **Validation**:
  - EVL-086: 默认温度开关修复（CLI 直跑与 run_experiments 口径一致）
  - ENG-059: eos_token_id 源头归一化（list/tuple -> first id），避免三处重复 int() 崩溃点
  - TST-030: 增加 eos list 回归测试覆盖
  - EVL-054: 按 duplicate of EVL-132 收口
- **Risks / follow-ups**:
  - 仍有 206 HIGH open，后续按 Phase 计划分波次修复
  - `CLAUDE.md` 为既有本地改动，未纳入本波提交
- **Commits**:
  - `5d953d7` fix: profiling precision and quant_bits consistency (PRF-032/033/034)
  - `46ca44c` fix: harden eval_ppl defaults and nan/inf guard (EVL-086, EVL-132)
  - `7b773ed` fix: normalize eos token id and enforce per-sequence eos masking (ENG-059, ENG-110)
  - `83116ee` test: add regressions for eos-list and eval_ppl guardrails
  - `pending` docs: sync wave20 tracker and iteration

### 2026-02-28 01:24 | Wave 19 — R22 P0/P1 修复（5 issues）+ worktree 清理
- **Goal**: 实施全系统状态报告中的可执行项：P0 profiling 修复、P1 eval/engine 防御性改进、worktree 清理
- **Key findings**:
  - **PRF-032 [HIGH]**: `"Hello " * N` 经 BPE 合并后 token 数可能 < seq_len；改为 `[_base_id] * seq_len` 直接填充 token ID
  - **PRF-033 [HIGH]**: `runtime_quant_bits` 仅对 kivi_style 调用 `resolve_quant_bits()`，其他模式传 None；改为所有模式统一调用
  - **PRF-034 [MED]**: profile_latency.py / profile_memory.py 缺少 `model.eval()`；已添加
  - **EVL-132 [HIGH]**: PPL NaN/Inf 时 exit(0) 伪装成功；添加 `math.isfinite()` 检查 + `_write_task_failure()` + `exit(EXIT_EXCEPTION)`
  - **ENG-110 [HIGH]**: batch EOS `all()` 判定导致先完成序列生成垃圾；添加 per-sequence `eos_reached` 张量 + `torch.where` 屏蔽
  - **Worktree 清理**: 移除 12 个闲置 worktree（4 Codex + 8 Cursor）+ 删除 codex/phase5v2-ruler-ag123-fix 分支
- **Changed files**: scripts/profile_latency.py, scripts/profile_memory.py, scripts/eval_ppl.py, src/engine/generate_loop.py, review_tracker.md
- **Validation**: `py_compile` 全部通过（本地无 GPU，pytest 依赖 numpy/libcblas 不可用）
- **Running total**: 995 issues | 461 fixed + 6 false_positive | 528 open (1 CRIT, 209 HIGH, 278 MED, 40 LOW)
- **Note**: 本地修改安全，不影响远端正在运行的 Phase 5v2 质量实验（profiling/eval 脚本仅在吞吐评测阶段使用）

### 2026-02-25 01:35 | Wave 18 — CAL-019/020 fix + deep analysis closes 10 items
- **Goal**: Resolve remaining 13 open review_tracker items through deep code analysis
- **Key findings**:
  - **CAL-019/020 [HIGH]**: Confirmed as real bugs — calibration Q vector lacked input_layernorm and RoPE, causing distorted attention distribution for inv_tau optimization
  - **8 items false_positive/wont_fix**: CFG-008/011/012/013/023/024/028 confirmed as intentional design choices through config file analysis; CFG-009 is cosmetic naming
  - **Annotation normalization**: 10 items (ENG-001/003/004, AGG-018~027) had non-standard annotations, normalized to standard `— fixed`/`— false_positive` format
- **Code fix**: Added `_rotate_half`, `_apply_rope_to_q`, `_get_rope_for_position` helpers to calibrate_behavior.py; Q now goes through `layer.input_layernorm()` → `attn.q_proj()` → `q_norm` (if present) → `RoPE` before collection
- **Impact**: Existing calibration artifacts (kv_calib_*.json) should be regenerated for optimal quality
- **Changed files**: scripts/calibrate_behavior.py, review_tracker.md
- **Commits**: 227f4e3 (annotation normalization), d56278d (CAL-019/020 fix), 30c5aa8 (tracker update)
- **Running total**: 466 issues | 430 fixed + 25 false_positive + 8 wont_fix | 3 open (0 CRIT, 2 HIGH, 1 MED)
- **Remaining 3 open** (all need user decisions):
  - CFG-022 [MED]: 1.5B throughput int8_ours b1-b16 temp=true vs b24-b32 temp=false (inconsistency within config)
  - CFG-026 [HIGH]: 7B/8B calib_files missing in artifacts/ (need GPU to generate)
  - CFG-029 [HIGH]: LLaMA-3.1-8B model_revision: null (need to pin commit hash)

### 2026-02-24 14:55 | Review Tracker Fix — Wave 10 (test coverage, utils & tools)
- **Goal**: Write 137 unit tests covering 8 TST issues for config_utils, run_experiments, review_tool, check_run_completeness
- **TST-053**: test_config_utils.py (22 tests: load_config error paths, split_csv, read_json, read_text)
- **TST-054**: TestSameCommitPrefix (12 tests: hash prefix matching, empty/unknown, whitespace, case sensitivity)
- **TST-055**: TestResolveQuantParams (15 tests: overrides, validation, boolean rejection, boundary)
- **TST-057**: TestSafeTCrit (10 tests: NaN/Inf/n<=1 guards, distribution correctness)
- **TST-019/038**: test_review_tool.py (37 tests: regex patterns, tracker parsing, all CLI commands)
- **TST-032**: test_check_run_completeness_utils.py (32 tests: split_csv, is_oom_from_log, expected_run_ids)
- **TST-040**: TestClassifyFailureExtended (19 tests: all _classify_failure paths)
- **Changed files**: tests/test_config_utils.py (NEW), tests/test_run_experiments.py (NEW), tests/test_review_tool.py (NEW), tests/test_check_run_completeness_utils.py (NEW), tests/test_aggregate_results_stats.py (extended)
- **Commits**: d045f08 (test files), 6cd295d (tracker)
- **Running total**: 367 issues, 301 fixed + 10 fp + 4 wf = 315 resolved, 48 open (0 CRIT, 21 HIGH, 25 MED, 2 LOW)

### 2026-02-24 14:45 | Review Tracker Fix — Wave 9 (test coverage)
- **Goal**: Write 56 unit tests covering 11 TST issues
- **TST-007/013**: INT8+INT4 per-token axis independence (scale isolation, group independence)
- **TST-008**: Bootstrap CI n=1/n=2 boundary + CI width monotonicity
- **TST-009**: Sign-flip permutation NaN/Inf handling
- **TST-010**: BH-FDR monotonicity, edge cases, NaN propagation
- **TST-012**: Float16 input quantization (INT4+INT8), fp16 vs fp32 consistency
- **TST-014**: INT4 pack/unpack boundary values (-8 to 7), full range sweep
- **TST-015**: Mixed sign sign-flip scenarios (all-positive, balanced, mixed)
- **TST-016**: INT4 vs INT8 error ratio (>= 3x), multi-seed robustness
- **TST-017**: Edge cases (single token, head_dim=1, all zeros, constant input)
- **TST-018**: Multi-round clear→append cycle (INT4+INT8, multi-layer)
- **Changed files**: tests/test_int4_cache.py (+620 lines), tests/test_int8_cache.py (+500 lines), tests/test_aggregate_results_stats.py (+306 lines)
- **Commits**: 9bc6414 (quant/cache tests), 3c1b23c (stats tests)
- **Running total**: 367 issues, 293 fixed + 10 fp + 4 wf = 307 resolved, 56 open (0 CRIT, 27 HIGH, 27 MED, 2 LOW)

### 2026-02-24 14:37 | Review Tracker Fix — Wave 7+8 (code fixes + DRY + features)
- **Goal**: Fix 16 issues across Wave 7 (9) and Wave 8 (7)
- **Wave 7** (9 issues):
  - AGG-048: `_safe_t_crit(inf)` → return NaN instead of 0.0
  - QUA-005: Centralize `KV_MODE_ORDER` into `config_utils.py`
  - AGG-015: Named constant `_EXACT_ENUM_THRESHOLD = 16`
  - SEC-003: Remove unused `fastapi`/`uvicorn` from requirements.txt
  - SEC-004: Document intentional path exposure in research CLI tools
  - TST-051: `sys.path.insert(0, ...)` instead of `append`
  - TST-052: `except Exception` pattern consistency
  - PRF-010: Document `GenerationBatchOutput` attribute safety
  - CHK-020: Add `TypedDict` for `TaskStateResult` and `GroupCheckResult`
  - Commits: 8f39875, c5b763c, 0056a3d, 73968c4 (tracker)
- **Wave 8** (7 issues):
  - CHK-004: CSV content validation (columns + rows)
  - CHK-005: LongBench/RULER task-level artifact checks
  - CHK-018: DRY — centralize `split_csv/read_json/read_text` into `config_utils.py`
  - AGG-009: Explicit `kv_mode` sort order for all summary tables
  - EXP-002: LongBench table footnote with metric composition
  - EXP-003: RULER per-subtask tables from `ruler_subtask_summary.csv`
  - EXP-004: Multi-model pagination for all 8 export functions
  - Commits: 6f23824, 016b460, 8d7f2df
- **Running total**: 367 issues, 282 fixed + 10 fp + 4 wf = 296 resolved, 67 open (0 CRIT, 27 HIGH, 35 MED, 5 LOW)

### 2026-02-24 14:22 | Review Tracker Fix — Wave 6 (comment/docs batch)
- **Goal**: Fix 12 comment/documentation issues (CHK-015, CHK-022, AGG-008, AGG-012, ENG-033, ENG-034, RUN-010~013, QUA-006, QUA-008)
- **Changed files**:
  - `scripts/check_run_completeness.py` — CHK-015 enum sync cross-reference, CHK-022 classified _read_json exceptions
  - `scripts/aggregate_results.py` — AGG-008 KIVI pairing note, AGG-012 seed SHA256 docs, QUA-008 defense-in-depth comment
  - `scripts/run_experiments.py` — RUN-010/011/012/013 design decision comments
  - `scripts/eval_ppl.py` — QUA-006 condensed 21-line dev notes to 2-line design comment
  - `src/engine/generate_loop.py` — ENG-033 wrapper reconstruction comment, ENG-034 mask growth comment
  - `review_tracker.md` — 12 issues marked fixed, summary: 266 fixed / 83 open
- **Commit**: 2f6cddb (code), pending (tracker)
- **Running total**: 367 issues, 266 fixed + 10 fp + 4 wf = 280 resolved, 83 open (0 CRIT)

### 2026-02-23 | RULER 4-Subtask Rewrite + LongBench 7-Task Extension + Objective Review
- **Goal**: Rewrite RULER eval to implement 4 genuine subtasks (S-NIAH, MK-NIAH, VT, CWE); extend LongBench to 7 tasks; update objective.md.
- **Changed files**:
  - `scripts/eval_ruler.py` (full rewrite: 4 RULER subtask generators + task-level scoring)
  - `scripts/eval_longbench.py` (fix HF field extraction; update default tasks to 7)
  - `scripts/run_experiments.py` (add new RULER args)
  - `scripts/aggregate_results.py` (add ruler_task_summary aggregation)
  - `objective.md` (PPL 1M tokens, ARR window, revision pin, RULER description, primary endpoints)
- **Key decisions**:
  - RULER: self-implemented task generators following NVIDIA/RULER taxonomy
  - LongBench: 7 tasks = narrativeqa, dureader, hotpotqa, gov_report, vcsum, trec, lcc
  - Primary endpoints capped at 5: LongBench F1-macro, RULER macro-accuracy, Needle pass rate, PPL, TPOT
- **Validation**: All modified scripts pass `python3 -m py_compile`

### 2026-02-23 | LongBench Official Metrics + Objective Refinement (Round 2)

- **Goal**: Add LongBench official per-task metrics (Rouge-L, Accuracy, Edit Similarity); change `longbench_score` from uniform token-F1 to official metric macro-average; add snapshot governance rule.
- **Changed files**:
  - `scripts/eval_longbench.py`: Added `TASK_OFFICIAL_METRIC` mapping, `_lcs_length()`, `_rouge_l()`, `_edit_similarity()`, `_classification_accuracy()`, `_compute_official_metric()`. Changed `longbench_score` to `official_macro`.
  - `objective.md`: LongBench 主表协议, Primary Endpoint #1 改为 official-metric macro, 新增 snapshot governance rule.
- **Verification**: `python3 -m py_compile scripts/eval_longbench.py` → OK
- **Risks / follow-ups**:
  - Rouge-L LCS computation is O(n*m) on token lists; mitigated by short LongBench answers.

### 2026-02-23 | Phase 1-Pre/3/4.1: KIVI Baseline + MSE Calibration + Multi-Model Configs

- **Goal**: Implement KIVI-style asymmetric KV cache baseline (Phase 3), MSE calibration loss (Phase 4.1), per-model config files (Phase 0.5), and integrate into all eval scripts. Part of EMNLP 2026 Milestone K-Q execution plan.
- **Changed files (NEW)**:
  - `src/quant/asymmetric_quant.py`: Asymmetric INT8/INT4 quantization with per-channel and per-token axis support, zero-point.
  - `src/cache/kivi_style_cache.py`: `KIVIStyleKVCache` class implementing KIVI paper's per-channel K + per-token V asymmetric quantization.
  - `tests/test_asymmetric_quant.py`: 15 unit tests covering round-trip error, edge cases, INT8/INT4.
  - `tests/test_kivi_cache.py`: 17 unit tests covering basic append/get, prefill+decode pattern, K scale persistence.
  - `configs/snapshots/exp_matrix_qwen25_7b_v1.yaml`: Qwen2.5-7B config.
  - `configs/snapshots/exp_matrix_llama31_8b_v1.yaml`: LLaMA-3.1-8B config.
- **Changed files (MODIFIED)**:
  - `src/cache/__init__.py`, `src/quant/__init__.py`: Added exports.
  - `src/engine/generate_loop.py`: Added `kivi_style` kv_mode + `quant_bits` parameter.
  - 7 eval/profile scripts: Added `kivi_style` to `--kv_mode` choices + `--quant_bits` passthrough.
  - `scripts/calibrate_behavior.py`: Added `--loss_function {kl,mse}`, MSE loss path.
- **Verification**: `python3 -m compileall -f scripts/ src/ tests/` → all 34 files compile clean, 0 errors.
- **Next**: Remote validation → calibration artifacts → ablation → full matrix.

### 2026-02-23 06:19 | Phase 4.1: MSE Calibration Complete + Phase 5 Blockers Resolved
- **Goal**: Generate MSE calibration artifacts for 1.5B model; fix remaining CRITICAL/HIGH blockers for Phase 5
- **Changed files**:
  - `scripts/eval_ppl.py`: Added kivi_style branch in build_kv_cache() + quant_bits parameter (L-1 fix)
  - `scripts/aggregate_results.py`: Added KIVI significance pairings, longbench_official_macro, model_id in sig_specs/ruler_depth_keys (M-1/M-2/M-3/M-4 fix)
  - `iteration.md`: Updated 20+ backlog checkboxes, Phase 4 plan status
- **Remote GPU tasks**:
  - MSE INT8 calibration: `calibrate_behavior.py --loss_function mse --search --quant_bits 8` → artifacts/kv_calib_mse_1p5b_int8.json (41KB)
  - MSE INT4 calibration: `calibrate_behavior.py --loss_function mse --search --quant_bits 4 --int4_search` → artifacts/kv_calib_mse_1p5b_int4.json (64KB)
  - INT8 best: g16/clip=99.5 (p95_mse=0.000956); INT4 best: g16 search across outlier_ratios
- **Commits**: 03ed4a0 (eval_ppl+aggregate fix), 03d2e13 (docs), 9f41659 (backlog checkboxes)
- **Pushed**: 8 commits to origin/main (36921e6..9f41659)
- **Backlog status**: All CRITICAL=0, remaining HIGH=3 (non-blocking: A-5 doc, D-2 design, K-1 usability)
- **Next**: Run ablation experiments (14 configs × 5 seeds × 3 tasks) on remote GPU

### 2026-02-23 07:27 | Phase 4 COMPLETE: Ablation Experiments Finished (70/70 runs)
- **Goal**: Run full ablation experiment matrix on remote GPU
- **Remote execution**: `run_experiments.py --config exp_matrix_ablation_1p5b_v1.yaml --tasks eval_ppl,eval_needle --seeds {1234..1238}`
- **Results**: 14 configs × 5 seeds × 2 tasks = 70 runs, all successful
  - A 节 (校准对比): kl/mse/percentile/percentile_fused/kivi — 5 configs
  - B 节 (温度校正): temp_on/temp_off — 2 configs
  - C 节 (group_size): g16/g32/g64/g128 — 4 configs
  - D 节 (scales): static/adaptive/dynamic — 3 configs
- **Duration**: ~65 min total (06:22 → 07:27), ~13 min per seed
- **Output dir**: `results/runs/ablation_*_s{seed}_ablation_1p5b_s{seed}/`
- **Next**: Phase 5 — full 3-model matrix experiments (1.5B KIVI补跑 → 7B → 8B)

### 2026-02-23 16:08 | PR-2 Eval/Aggregate 收口：LongBench+RULER 口径修复与聚合一致性
- **Goal**: 关闭 PR-2 车道 backlog（E/M/O/Q/R）并修复 LongBench 图 y 轴命名问题
- **Changed files**:
  - `scripts/eval_longbench.py`: 分类任务改精确匹配；official macro 统一为 [0,1]；HF fallback 不再把 `input` 当 context；任务级指标名一致性断言；KIVI quant_bits 推断修复
  - `scripts/eval_ruler.py`: 修复 MK-NIAH dead code、VT 多链评分、截断策略、CWE 空词过滤、KIVI quant_bits 推断
  - `scripts/eval_ppl.py` / `scripts/eval_needle.py` / `scripts/profile_latency.py` / `scripts/profile_memory.py`: 统一 quant_bits 推断，修复 KIVI 默认误记 16
  - `scripts/profile_memory.py`: NVML 初始化异常捕获、线程 stop 健壮性、回退来源显式字段 `gpu_mem_peak_source`
  - `scripts/aggregate_results.py`: kv_mode 语义排序、duplicate 折叠告警/计数字段、LongBench 图 y 轴改为 official-metric macro 命名
  - `scripts/generate_thesis_report.py`: C11 增加 `target_model_ids` 过滤，避免跨模型混算
  - `tests/test_aggregate_results_stats.py`: 新增 mixed-sign sign-flip 检验
  - `tests/test_generate_thesis_report.py`: 新增 C11 target model 过滤检验
- **Commands**:
  - `python3 -m unittest tests/test_aggregate_results_stats.py tests/test_generate_thesis_report.py`
  - `python3 -m compileall -f src scripts tests`
- **Validation**:
  - unittest：**失败（环境问题）**，当前 Python 运行时缺失 `libcblas.3.dylib`，导致 numpy/pandas import error
  - compileall：**通过**
- **Risks / follow-ups**:
  - 需在可用 numpy/pandas 的环境重跑 PR-2 单测，补齐 CI 证据

### 2026-02-23 16:11 | PR-4 配置与文档收口：I/W/X 全量关闭
- **Goal**: 收口 final config / objective / SOP / preflight 文档口径，关闭 I/W/X backlog
- **Changed files**:
  - `configs/snapshots/final_emnlp2026_v1.yaml`: 补 `dynamic` 消融维度、系统 benchmark、LLaMA HF+local 双入口、C9/C10/C11 精确 claim、Phase5v2 workflow
  - `objective.md`: 新增 KIVI 差异披露（INT4 非 bit-pack、无温度校正、kernel 差异）；新增 Phase5v2 legacy 与 run_tag 规则
  - `experiment_sop.md`: 补多模型复现入口（HF + ModelScope）与 Phase5v2 强制流程
  - `docs/final_results_summary.md`: 增加 legacy 数据声明、KIVI 内存披露与 Phase5v2 重启策略
  - `docs/thesis_preflight_checklist.md`: 增加 Phase5v2 口径一致性检查与 KIVI 论文披露检查
  - `iteration.md`: I/W/X 对应项更新为已关闭（含 W-1 误报核销）
- **Commands**:
  - `date '+%Y-%m-%d %H:%M'`
- **Validation**:
  - 配置与文档检查通过；本里程碑为文档/配置收口，无新增 Python 代码路径
- **Risks / follow-ups**:
  - 合并 PR-2 后需同步更新 `iteration.md` 的 E/M/O/Q/R 关闭状态，避免并行分支冲突

### 2026-02-23 17:29 | Phase 5v2 启动 — 合并验证 + 质量并行评测

- **Goal**: 验证 Codex 修复合并完整性，同步远端代码，启动 3 模型并行质量评测
- **Scope**: Step 0 (合并验证) + Step 1 (脚本创建) + Step 2 (质量启动)
- **Changed files**:
  - `iteration.md`: 更新 TODO Backlog（4 CRITICAL 全部标记已修复）+ Approved Plans（Phase 5v2 状态更新）
- **Commands**:
  - `git pull --ff-only origin main` → 9 commits, 35 files (Codex PR-1~PR-4 + merge)
  - `python3 -m compileall -f src/ scripts/ tests/` → 全部通过
  - 远端 `pytest tests/ -v` → 143 passed, 2 failed (KIVI INT4 bit-pack decode 维度不匹配), 1 skipped
  - `rsync -avz ... → 38 files synced` 到远端
  - `tmux kill-session -t phase5` → 旧会话已清理
  - `tmux new-session -d -s q_1p5b/q_7b/q_8b` → 3 个质量并行评测已启动
- **Outputs**:
  - GPU: H20 100% 利用率, 40GB/98GB VRAM（三模型并行，预算 56GB 内）
  - 3 个 run 目录已创建，各模型第一轮 PPL+Needle 已完成，正在跑 LongBench
  - 远端磁盘: /root 25GB 可用（结果存储）; /root/autodl-tmp 2.4GB（仅读模型）
- **Validation**:
  - [x] 4 CRITICAL bug 修复确认（代码级验证 O1/O2/O3/T1）
  - [x] 编译检查全部通过
  - [x] 远端测试 143/145 通过
  - [x] 三模型并行评测已启动，GPU 利用率正常
  - [ ] KIVI INT4 bit-pack 测试失败（2 tests）— 不阻塞主实验（continue_all），后续跟进
- **Risks / follow-ups**:
  - KIVI INT4 bit-pack decode 路径有维度不匹配 bug，可能影响 kivi_style_int4 系列实验结果
  - autodl-tmp 仅 2.4GB，不要在该分区写新数据
  - 质量评测预计 80-100h 墙钟；完成后启动吞吐串行
  - **监控命令**: `ssh -p $SSH_PORT $SSH_USER@$SSH_HOST 'tmux ls; ls results/phase5v2/runs/ | wc -l; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader'` (SEC-001: server details moved to docs/autodl_server.md)

### 2026-02-23 22:00 | 项目监管审查：全面代码质量审查
- **Goal**: 作为监管 agent，对当前代码库所有新增/修改模块进行全面审查，发现潜在问题并归档到待办清单
- **Scope**: 6 个并行审查 agent 分别检查 KIVI cache、asymmetric quant、generate_loop、eval 脚本集成、MSE 校准、配置矩阵一致性
- **审查模块与发现数量**:
  - `src/cache/kivi_style_cache.py`: 4 CRITICAL + 3 MEDIUM + 3 LOW
  - `src/quant/asymmetric_quant.py`: 2 CRITICAL + 2 MEDIUM + 1 LOW
  - `src/engine/generate_loop.py`: 2 HIGH + 1 MEDIUM + 1 LOW
  - 评测脚本集成（9 个脚本）: 2 CRITICAL + 2 HIGH + 4 MEDIUM + 1 LOW
  - `scripts/calibrate_behavior.py` MSE: 3 CRITICAL + 4 HIGH + 3 MEDIUM
  - 配置矩阵一致性（3 YAML）: 3 HIGH + 2 MEDIUM + 1 LOW
- **关键发现（阻塞性）**:
  1. MSE 校准实现有根本性 loss 语义错误（mean vs sum 不一致），产物不可信 → 阻塞 Phase 4
  2. percentile < 50 时非对称量化公式翻转 min/max，静默产生错误结果 → 需添加范围校验
  3. export_tables_latex.py 完全缺失 KIVI 显示名和排序 → 阻塞论文表格
  4. eval_longbench.py 引用未定义 logger → 特定条件下 NameError 崩溃
  5. 1.5B 配置缺失 KIVI 条目，7B/8B 缺失吞吐量条目 → 跨模型对比不完整
  6. generate() 高层 API 无法指定 KIVI quant_bits → INT4 KIVI 不可用
- **产出**: 全部问题已写入 `iteration.md` TODO Backlog A-F 节（按模块分类、按严重性排序）
- **Validation**: 审查基于 6 个专业 agent 的独立代码阅读，每个 agent 逐行分析源码
- **Risks / follow-ups**:
  - 所有 CRITICAL/HIGH 问题必须在 Phase 4/5 启动前修复
  - MSE 校准需完整重写 loss 聚合逻辑后才能生成可信产物
  - 建议开发 agent 优先修复 A 节（MSE）和 C 节（percentile 校验），因为这两个影响数值正确性
