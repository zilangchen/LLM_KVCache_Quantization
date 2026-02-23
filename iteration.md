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
  - [ ] rsync 修复到远端 + repair RULER-long 失败
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

---

### 2026-02-24 04:48 | review-coord 持续守护模式改造 + start_agents.sh 修复
- **Goal**: 将 review-coord Agent 从单次审查模式改造为持续运行守护式 Agent，同时修复 start_agents.sh 的三个问题（RVW-010, RVW-015）
- **Changed files**:
  - `.claude/agents/review-coord.md`: 完整重写（162→192 行）
    - 新增持续运行事件循环（变更检测→决定行动→执行审查→智能休眠）
    - 新增状态管理（last_reviewed_commit, reviewed_modules, cycle_count）
    - 审查范围 7→10 模块覆盖全部有效代码
    - 新增自适应休眠策略（不硬编码，agent 自决策）
    - 新增变更打断深度审查的处理规则
  - `scripts/start_agents.sh`: 三处修复
    - L5: 硬编码路径→动态 `$(cd "$(dirname "$0")/.." && pwd)`（RVW-010）
    - L16+L28: `reviewer`→`review-coord`（RVW-015）
    - L33: 启动 prompt 更新为持续审查模式措辞
- **Commands**:
  - `grep -c 'reviewer' scripts/start_agents.sh` → 0
  - `wc -l .claude/agents/review-coord.md` → 192
- **Validation**:
  - review-coord.md 包含完整事件循环伪代码、10 模块定义、休眠策略 ✅
  - start_agents.sh 无硬编码路径、无 `reviewer` 引用 ✅
  - review-coord 注意事项明确"持续运行，仅在用户终止/supervisor shutdown 时退出" ✅
- **Risks / follow-ups**:
  - review_tracker.md 中 RVW-010、RVW-015 应标记为 fixed
  - AGENTS.md 中若有引用旧 reviewer agent 的描述需同步更新

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


> 更早的条目见 `development_history/iteration_archive_202602.md`
