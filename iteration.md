# Iteration Log (Single Source of Progress)

This file is the only progress tracker for the repository.
`lang.md` is deprecated and archived.
Canonical agent workflow directory is `.agents/`.

## TODO Backlog

> **审查问题追踪见 `review_tracker.md`**（根目录权威文件）
>
> ```bash
> python scripts/review_tool.py stats       # 统计
> python scripts/review_tool.py phase-gate  # 门禁
> python scripts/review_tool.py progress    # 各模块进度
> python scripts/review_tool.py open        # 列出 open issues
> python scripts/review_tool.py open --sev HIGH --section AG  # 筛选
> ```

---

## Approved Plans

> 经讨论并被用户认可的阶段性执行方案（与审查问题分开，审查问题见 `review_tracker.md`）。


### Plan: EMNLP 2026 Phase 4 — MSE 校准 + 消融（仅 1.5B） ✅ 已完成
- **批准日期**：2026-02-23
- **完成日期**：2026-02-23 07:27
- **内容**：
  - [x] 生成 MSE 校准产物 — ✅ 完成 2026-02-23 06:03
  - [x] 创建消融配置 — ✅ 完成 commit f07422d
  - [x] 运行消融实验矩阵（PPL+Needle，5 seeds × 14 configs = 70 runs） — ✅ 完成 2026-02-23 07:27

### Plan: EMNLP 2026 Phase 5v2 — 全矩阵实验（phase5v2 新目录）
- **批准日期**：2026-02-23
- **前置条件**：✅ 4 CRITICAL 已修复（Codex PR merge 1aa5c95）；旧 RULER/LongBench 结果标记 legacy
- **状态**：🟢 执行中（质量并行评测已启动 2026-02-23 17:23）
- **内容**：
  - [x] 更新 7B/8B 配置：保留 batch=1,2,4,8,16 吞吐量；FP16 删 b24/b32 避免 OOM；添加 KIVI 条目 — ✅ commit f07422d
  - [x] Codex 全量代码修复（35 files, 4 PR 合并） — ✅ merge commit 1aa5c95
  - [x] 远端代码同步（rsync） — ✅ 2026-02-23 17:22
  - [x] 创建 6 个 runner 脚本（3 质量 + 3 吞吐） — ✅ 2026-02-23 17:22
  - [x] 启动质量并行评测（3 tmux sessions: q_1p5b/q_7b/q_8b） — ✅ 2026-02-23 17:23
  - [x] Cherry-pick Codex RULER 修复到 main（5 commits: b7f4c36→4dbc227） — ✅ 2026-02-24 04:34
  - [x] rsync 修复到远端 — ✅ 2026-02-24 04:38
  - [x] repair int4_baseline_long eval_ruler — ✅ 2026-02-24 05:22 (success, rc=0)
  - [x] repair int4_fused_long eval_ruler — ✅ 2026-02-24 06:35 (success, rc=0)
  - [ ] 质量评测完成（535 runs: 1.5B×215 + 7B×160 + 8B×160）
  - [ ] 吞吐串行评测（565 runs: 1.5B×240 + 7B×200 + 8B×200）（质量完成后启动）
  - [ ] 3 模型延迟/显存 profiling
  - [x] 修复 `export_tables_latex.py`：KV_MODE_ORDER/DISPLAY 缺 kivi_style — ✅ commit 8bf9414
  - [x] 扩展 `generate_thesis_report.py`：claims C7-C11 — ✅ commit 8bf9414

### Plan: EMNLP 2026 Phase 6 — 聚合 + 统计修复 + 论文准备
- **批准日期**：2026-02-23
- **前置条件**：Phase 4 + Phase 5 完成
- **状态**：待执行
- **内容**：
  - [ ] C1 TPOT 统计修复：补 seed 1239-1241 达到 n=8（当前 p=0.0625 因 n=5 硬上限）
  - [ ] 创建 `configs/snapshots/final_emnlp2026_v1.yaml` 统一配置
  - [ ] 合并结果到 `results/emnlp_final/`，运行聚合 + LaTeX + 报告
  - [ ] claim_validation.csv 全部 PASS 或有文档解释

### Plan: 已确认决策
- **批准日期**：2026-02-23
- **内容**：
  - 吞吐量 batch scaling：3 模型均做 batch=1,2,4,8,16（FP16 删 b24/b32）
  - 消融实验：仅在 1.5B 主模型执行

---

## Current Status

- Active objective source: `objective.md`
- Active execution policy: `AGENTS.md`
- Active experiment protocol: `experiment_sop.md`
- Progress log source of truth: `iteration.md`

## Update Rules

1. After each completed functional unit, append one new entry under `Timeline` (latest first).
2. Every entry must include goal, changed files, commands run, outputs, and result quality.
3. If blocked, write explicit blocker and next action.
4. Keep entries concise and auditable; avoid vague summaries.
5. Timeline 保留最近 **15 条**。超出时将最旧条目归档到 `development_history/iteration_archive_202602.md`。

## Entry Template

### YYYY-MM-DD HH:MM | Workstream Title
- Goal:
- Scope:
- Changed files:
- Commands:
- Outputs:
- Validation:
- Risks / follow-ups:

## Timeline (Latest First)

### 2026-02-24 14:14 | 代码审查修复 Wave 3-5 — 30 additional issues fixed

- **Goal**: 继续修复 review_tracker.md 中的 open issues（Wave 2 之后）
- **Wave 3** (10 issues): KVC-017 overflow guard, CHK-023 timeout enum, RUN-020 config validation, QUA-002 logging infra, SMK-002/004, AGG-046/047 bare except+commit semantics, ENG-036 signature cache, RUN-033 classified exceptions
- **Wave 4** (9 issues): QUA-001 centralize get_git_commit (9 scripts → src/utils/repro.py, net -44 lines), KVC-018 zero-length get_kv warning, RUN-034/SMK-005 breaking change docs, AGG-029/037/043/045 statistical fixes, QUA-003 loop extraction
- **Wave 5** (11 issues): ENG-007/008/012/013 docs, QUA-004/007/009/010 code quality, RUN-017/AGG-014/PRF-009 comments
- **Validation**: All modified files pass `python -m py_compile`
- **Commits**:
  - Wave 3: `7e72174`, `f25408f`, `a581bed`
  - Wave 4: `3e6cf12`, `5be2de7`, `242c3e8`, `589356e`
  - Wave 5: `bcc6b98`, `153805c`, `7f58455`
- **Cumulative**: 254 fixed + 10 false_positive + 4 wont_fix = 268 resolved / 367 total (73%)
- **Remaining**: 95 open (0 CRIT, 27 HIGH, 49 MED, 19 LOW) — mostly TST test coverage (48), SEC security decisions (4), CFG config design (8), refactoring (3), architecture decisions (4)

### 2026-02-24 13:54 | 全仓库代码审查修复 Wave 2 — 43 issues 批量修复

- **Goal**: 继续修复 review_tracker.md 中的 open issues（Wave 1 之后的第二轮）
- **Changed files**: 23 files (+931/-181 lines)
  - src/: engine/generate_loop.py, engine/patch_model.py, cache/kivi_style_cache.py, cache/int4_cache.py, cache/int8_cache.py, quant/int4_basic.py, quant/int8_basic.py
  - scripts/: run_experiments.py, aggregate_results.py, smoke_test.py, check_run_completeness.py, config_utils.py, eval_ppl.py, eval_ruler.py, profile_latency.py, profile_memory.py
  - tests/: test_aggregate_results_stats.py, test_triton_kernel.py, test_asymmetric_quant.py, test_int4_cache.py, test_int8_cache.py, test_kivi_cache.py
  - review_tracker.md
- **Method**: 6 并行 dev agents + main thread direct fixes
- **Results**: 43 issues marked fixed, total 228/366 resolved
  - RUN: 13 fixes (018-032) — commit validation, subprocess timeout, param validation
  - AGG: 9 fixes (034-044) — logging, inf guard, readable names, scipy flag
  - ENG: 12 fixes (005-035) — padding check, KIVI validation, dtype contracts
  - SMK: 2 fixes (001, 003) — exit code semantics, token-based slicing
  - TST: 7 fixes (041-050) — t_critical tests, CI95 tests, Phipson-Smyth tests, INT4/INT8 bounds
  - CHK/PRF/EVL/QNT/KVC: 6 fixes
- **Validation**: All 23 files pass `python -m py_compile`
- **Commits**:
  - `3c6deed` fix: Wave 2 src/ fixes — ENG(12), KVC(1), QNT(1)
  - `40cbad0` fix: Wave 2 scripts/ fixes — RUN(13), AGG(9), SMK(2), CHK(1), PRF(4), EVL(1)
  - `fc06073` test: Wave 2 test fixes — TST(7)
  - `9d2fcda` docs: update review_tracker — Wave 2 marks 43 issues fixed
- **Remaining**: 124 open (0 CRIT, 33 HIGH, 63 MED, 28 LOW)
- **Risks / follow-ups**: SMK-005/RUN-034 are breaking change notes for new params introduced by fixes; TST-053~058 are test coverage gaps for Wave 2 code changes

### 2026-02-24 06:35 | RULER-long Repair 完成（int4_baseline_long + int4_fused_long）

- **Goal**: 修复 seed 1234 的 2 个 RULER 32K eval_ruler 失败（CWE 子任务 prompt 溢出）
- **Root cause**: 旧代码 `32704 + 128 = 32832 > max_position_embeddings=32768`，修复后用 `_effective_prompt_budget()` 动态调整
- **Commands**:
  - `run_experiments.py --run_names int4_baseline_long --run_tag phase5v2r1_1p5b_s1234 --append`
  - `run_experiments.py --run_names int4_fused_long --run_tag phase5v2r1_1p5b_s1234 --append`
- **Results**:
  - int4_baseline_long: success, rc=0, 256 cases, CWE f1=0.50
  - int4_fused_long: success, rc=0, 256 cases, CWE f1=0.43
  - 两者 pass_rate≈0 是 int4 基础量化在 32K 的预期表现
- **Output**: `results/phase5v2/runs/{int4_baseline,int4_fused}_long_s1234_phase5v2r1_1p5b_s1234/`
- **Validation**: manifest status=success, 4 CSV 文件生成
- **Risks / follow-ups**: 聚合时需用 repair 版（tag=phase5v2r1）替代原始失败版

### 2026-02-24 05:48 | 全仓库代码审查修复 Wave 1 — 90+ issues 批量修复

- **Goal**: 修复 review_tracker.md 中所有可代码修复的 open issues（~90 个，跨 11 个模块）
- **Changed files** (32 files, +1356/-725 lines):
  - `scripts/check_run_completeness.py`: CHK-002/003/007/008/009/010/011/012/013/014/016/017/019 (13 fixes)
  - `scripts/review_tool.py`: RVW-001/002/003/004/014/016/017/018/021/022/023 (11 fixes)
  - `scripts/export_tables_latex.py`: EXP-013/014/015/016 (4 fixes)
  - `scripts/generate_thesis_report.py`: EXP-001/009/010/011/012 (5 fixes)
  - `scripts/calibrate_behavior.py`: CAL-006/007/008/009/012/013/014/015/016/017 (10 fixes)
  - `scripts/run_experiments.py`: RUN-002/003/004/005/006/007/008 (7 fixes)
  - `scripts/repair_phase5v2_ruler_light.py`: RUN-015/016 (2 fixes)
  - `scripts/eval_ruler.py`: EVL-013/014/027/028 (4 fixes)
  - `scripts/eval_longbench.py`: EVL-017 (1 fix)
  - `scripts/aggregate_results.py`: AGG-016/017/021/022/026/028/030 (7 fixes, 在前次 commit 基础上)
  - `src/engine/generate_loop.py`: ENG-018/020/022/026/031 (5 fixes)
  - `src/engine/patch_model.py`: ENG-017/019/024 (3 fixes)
  - `src/kernels/triton_decode_attn_int8.py`: ENG-015/016 (2 fixes)
  - `src/quant/int4_basic.py`: ENG-028 + QNT-005 (2 fixes)
  - `src/quant/asymmetric_quant.py`: QNT-005 edge case documentation (1 fix)
  - `src/cache/kivi_style_cache.py`: KVC-005/009/010/013/014/015 (6 fixes)
  - `CLAUDE.md`: RVW-012/020 (2 fixes)
  - `.claude/settings.json`: RVW-009 (1 fix)
  - `configs/snapshots/exp_matrix_llama31_8b_v1.yaml`: CFG-007 (1 fix)
  - `tests/test_aggregate_results_stats.py`: AGG-033 CRITICAL (test assertions updated for Phipson-Smyth +1)
- **False positives identified**: CFG-010, CFG-017, CFG-018, RVW-019 (4 FPs)
- **Method**: 9 parallel background agents + main thread direct fixes
- **Validation**: `python -m py_compile` — all 16 modified .py files COMPILE OK
- **review_tracker.md**: ~90 issues fixed this wave; Phase Gate: CLEAR (0 CRIT open)
- **Commits**:
  - `a60cbe6` fix: core quant/cache/engine fixes — KVC-002 INT4 pack offset, QNT-003~009, ENG-015~031
  - `2442ce7` fix: scripts bulk review fixes — CHK(13), RVW(11), EXP(9), CAL(10), RUN(9), EVL(5), AGG(7)
  - `c67038c` test: AGG-033 update sign-flip test assertions for Phipson-Smyth +1 correction
  - `6c12740` docs: update review_tracker (166 fixed, 0 CRIT), config, and meta files
  - `93d79b9` chore: review-coord agent model opus→sonnet
- **Risks / follow-ups**:
  - 本地 pytest 因 numpy/scipy 依赖问题无法运行，远端验证待实验完成后进行
  - TST-* issues (22个测试覆盖问题) 属于新增测试，非代码修复，后续 Wave 2 处理
  - AGG-031 (双尾 vs 单尾) 涉及统计方法论决策，需用户确认
  - ENG-003/004 (KIVI decode 路径) 涉及架构决策，需用户确认

### 2026-02-24 05:20 | HIGH priority 修复 — aggregate_results.py 统计与数据完整性 (6+1 fixes)

- **Goal**: 修复 aggregate_results.py 中 7 个 HIGH/MED 审查问题
- **Changed files**: `scripts/aggregate_results.py`, `review_tracker.md`
- **Fixes**:
  - AGG-018: CI 从 z=1.96 改为 t 分位数（_t_critical 函数，scipy + fallback lookup table）
  - AGG-019: exact sign-flip 分支加 Phipson-Smyth +1 修正，与 MC 分支一致
  - AGG-020: _read_csvs bare except → logger.warning 记录损坏 CSV
  - AGG-023: relative_gain pairings 补充 kivi_style 配对（C9/C10 claim 支持）
  - AGG-024: relative_gain 所有 7 个调用的 key_cols 加 model_id
  - AGG-025: _main_claims_32k_table 动态 merge_keys 含 model_id，消除笛卡尔积
  - AGG-027: count=1 时 CI 半宽从 0.0 改为 NaN（随 AGG-018 修复）
- **Validation**: `python -m py_compile scripts/aggregate_results.py` — COMPILE OK
- **review_tracker.md**: 280 issues | 81 fixed + 2 FP | 197 open (0 CRIT, 42 HIGH, 114 MED, 41 LOW)
- **Commit**: 4876498

### 2026-02-24 05:10 | Supervisor 审查追踪清理 — Phase Gate 解除阻塞

- **Goal**: 验证并标记已修复的 Phase Blockers 和 RVW issues，解除 Phase Gate 阻塞
- **Changed files**:
  - `review_tracker.md`: 标记 9 个已修复 issues (CHK-001, EVL-001, EVL-002, EVL-008, RVW-007, RVW-008, RVW-010, RVW-011, RVW-015)
  - `scripts/start_agents.sh`: L32 developer prompt 从 "TODO Backlog" 改为 "review_tracker.md + iteration.md → 按优先级矩阵领取任务" (RVW-007)
- **Validation**:
  - `review_tool.py stats`: 273 total, 74 fixed, 197 open ✅
  - `review_tool.py phase-gate`: **CLEAR** (was BLOCKED by 3 CRIT) ✅
  - CHK-001: 代码验证 OOM 检查在 if 链首位 (L147-148) ✅
  - EVL-001: CLASSIFICATION_MATCH_POLICY + docstring + CSV audit 字段 ✅
  - EVL-002: _effective_prompt_budget() 确保 prompt + gen ≤ max_model_len ✅
- **Phase Gate 状态**: BLOCKED → **CLEAR**（0 CRIT open）
- **Commit**: 53fd752
- **Risks / follow-ups**:
  - 远程实验仍在运行，本次修改不影响远端代码
  - 44 HIGH issues 仍 open，优先处理 ENG/TST 模块

### 2026-02-24 04:48 | review-coord 持续守护模式改造

- **Goal**: 重写 review-coord.md 为持续守护式 Agent，修复 start_agents.sh
- **Changed files**:
  - `.claude/agents/review-coord.md`（完全重写，162→192 行）：事件循环架构 + 10 模块覆盖 + 智能休眠策略
  - `scripts/start_agents.sh`：动态路径(L5)、agent 名称修正(L28)、启动 prompt 更新(L33)、注释修正(L16)
- **Validation**:
  - review-coord.md 包含完整事件循环、10 模块定义、休眠策略
  - `grep reviewer scripts/start_agents.sh` → 零残留
  - `grep review-coord scripts/start_agents.sh` → 3 matches
- **Risks / follow-ups**: RVW-010, RVW-015 已修复

### 2026-02-24 04:34 | Cherry-pick Codex RULER 修复 + 附带改进

- **Goal**: 将 Codex 分支 `codex/phase5v2-ruler-ag123-fix` 的核心修复 cherry-pick 到 main，跳过大规模删除类变更
- **Changed files**:
  - `scripts/eval_ruler.py` — `_effective_prompt_budget()` 动态调整 prompt budget，per-case try/except
  - `scripts/run_experiments.py` — 预启动截断警告，skip_completed 语义修复
  - `scripts/repair_phase5v2_ruler_light.py` — 新增 RULER-long 修复工具
  - `scripts/aggregate_results.py` — per-model 分层表导出，RULER subtask groupby 改进
  - `scripts/generate_thesis_report.py` — 跨模型 claim 验证重构
  - `scripts/profile_memory.py` — UnboundLocalError 修复 + NVML source 检测
  - `scripts/eval_longbench.py` — classification_match_policy 审计字段
  - `configs/snapshots/exp_matrix_qwen25_7b_v1.yaml` — 注释修正
  - `tests/` — 5 个新/更新测试文件（+13 passed, 6 skipped due to no GPU）
- **Cherry-picked commits**: b7f4c36, 22f667b, 674410b, 449edcb, 4dbc227（原始: 502bc08, 1c76dd3, 04d89bd, 2fb4c2a, 7d5d65a）
- **Skipped**: 6 个 docs-only commits（iteration.md）+ 所有删除类 commits（agent 定义、review 基础设施）
- **Validation**: `pytest tests/test_eval_ruler_length_guard.py tests/test_run_experiments_resilience.py tests/test_eval_longbench_classification_policy.py -v` → 13 passed, 6 skipped
- **Next**: rsync 到远端 → repair RULER-long 失败

### 2026-02-24 03:13 | 审查追踪迁移 — review.yaml → review_tracker.md

- **Goal**: 用 280 行结构化 Markdown 替代 3951 行 YAML + 858 行 Python 工具链，提升可读性和直接编辑性
- **Changed files**:
  - `review_tracker.md`（新建）：根目录权威审查追踪文件，176 issues
  - `scripts/review_tool.py`（新建）：轻量级查询工具（stats/phase-gate/progress/open/add）
  - `scripts/migrate_review_to_md.py`（新建后归档）：一次性迁移脚本
  - `.claude/agents/reviewer.md`：写入目标从 iteration.md TODO Backlog → review_tracker.md
  - `.claude/agents/developer.md`：修复流程从 YAML 脚本 → 直接编辑 markdown
  - `.claude/agents/supervisor.md`：启动流程读取 review_tracker.md
  - `CLAUDE.md`：§1 权威文件表新增 review_tracker.md，§4.5 Phase 闸门更新，§12 审查 Agent 更新
  - `~/.claude/CLAUDE.md`：§7 审查 Agent 更新
  - `AGENTS.md`：新增 review_tracker.md 说明
  - `iteration.md`：TODO Backlog 指针更新
- **Archived to** `development_history/archive_20260224_review_yaml/`:
  - `review.yaml` (3951 lines), `scripts/review_query.py` (430 lines), `scripts/review_add_issue.py` (428 lines), `scripts/migrate_review_to_yaml.py` (819 lines)
- **Validation**:
  - `review_tool.py stats`: total=176, open=112, fixed=62, fp=2 ✅ (matches original)
  - `review_tool.py phase-gate`: BLOCKED (T-1, AF-1, AG-1) ✅
  - `review_tool.py progress`: 32 sections, 64/176 resolved (36%) ✅
  - `grep review.yaml *.md .claude/agents/*.md`: 零残留引用 ✅
  - `wc -l review_tracker.md`: 291 lines (vs 3951 原 YAML, 93% 压缩) ✅
- **Net effect**: 删除 ~4809 行 (YAML + 3 scripts)，新增 ~400 行 (markdown + 1 script)。92% 减少。
- **Commit**: 73c9472 (initial), then renumbered (see below)

### 2026-02-23 23:30 | Phase 4-6 Prep: Bug Fixes + Config Updates + Claims Extension

- **Goal**: Resolve all CRITICAL/HIGH backlog items blocking Phase 4-6, update configs for full matrix, extend thesis report claims.
- **Changed files (BUG FIXES)**:
  - `scripts/calibrate_behavior.py`: Fixed MSE loss aggregation (.mean→.sum), clamp(min=eps), loss_accum normalization, --calib_out default, select_best_trial key check
  - `src/cache/kivi_style_cache.py`: Fixed clear() to reset _k_scale/_k_zp
  - `src/quant/asymmetric_quant.py`: Added percentile range validation (50, 100]
  - `src/engine/generate_loop.py`: Added quant_bits to generate() API
  - `scripts/eval_longbench.py`: Added logging import + logger
- **Changed files (CONFIG UPDATES)**:
  - `configs/exp_matrix.yaml`: +13 KIVI entries, -2 FP16 b24/b32
  - `configs/snapshots/exp_matrix_qwen25_7b_v1.yaml`: +40 entries (long INT4/KIVI + throughput)
  - `configs/snapshots/exp_matrix_llama31_8b_v1.yaml`: +40 entries (same)
  - `configs/snapshots/exp_matrix_ablation_1p5b_v1.yaml`: Created, 14 runs
  - `configs/snapshots/final_emnlp2026_v1.yaml`: Created meta-config
- **Changed files (FEATURE)**:
  - `scripts/export_tables_latex.py`: +kivi_style to KV_MODE_ORDER/DISPLAY
  - `scripts/generate_thesis_report.py`: +claims C7-C11
  - `CLAUDE.md`: +Phase gate rule (§4.4), +remote server section (§12)
- **Verification**: compileall 0 errors; all YAML parse OK; 11 ClaimSpecs; 86+14+67+67 matrix runs
- **Backlog resolved**: A1-A4/A6-A7, B1, C1-C2, D1, E1-E4, F1-F3, G1-G2/G4, J1
- **Commit**: pending
- **Next**: commit → rsync → MSE calibration → ablation

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
  - **监控命令**: `ssh -p 31867 root@region-42.seetacloud.com 'tmux ls; ls results/phase5v2/runs/ | wc -l; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader'`

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

### 2026-02-23 | LongBench Official Metrics + Objective Refinement (Round 2)

- **Goal**: Add LongBench official per-task metrics (Rouge-L, Accuracy, Edit Similarity); change `longbench_score` from uniform token-F1 to official metric macro-average; add snapshot governance rule.
- **Changed files**:
  - `scripts/eval_longbench.py`: Added `TASK_OFFICIAL_METRIC` mapping, `_lcs_length()`, `_rouge_l()`, `_edit_similarity()`, `_classification_accuracy()`, `_compute_official_metric()`. Changed `longbench_score` to `official_macro`.
  - `objective.md`: LongBench 主表协议, Primary Endpoint #1 改为 official-metric macro, 新增 snapshot governance rule.
- **Verification**: `python3 -m py_compile scripts/eval_longbench.py` → OK
- **Risks / follow-ups**:
  - Rouge-L LCS computation is O(n*m) on token lists; mitigated by short LongBench answers.

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

> 更早的条目见 `development_history/iteration_archive_202602.md`
