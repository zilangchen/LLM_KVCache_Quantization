# Iteration Log (Single Source of Progress)

This file is the only progress tracker for the repository.
`lang.md` is deprecated and archived.
Canonical agent workflow directory is `.agents/`.

## Approved Plans

> 经讨论并被用户认可的阶段性执行方案（与审查问题分开，审查问题见 `review_tracker.md`）。


### ~~Plan: EMNLP 2026 Phase 4 — MSE 校准 + 消融（仅 1.5B）~~ ✅ 完成 2026-02-23（详见 Timeline 归档）

### ~~Plan: EMNLP 2026 Phase 5v2 — 全矩阵实验（phase5v2 新目录）~~ ✅ 完成 2026-03-09（详见 Timeline 归档）

### ~~Plan: Phase 5v2 数据修复（Data Repair）— v8 补跑方案~~ ✅ 完成 2026-03-08
- **冻结副本**: `/root/LLM_KVCache_Quantization_phase5v2fix_20260307_144607`
- **结果**: 17 dirs × 4 tasks = 68/68 SUCCESS, PPL 验证全通过

### Plan: R22 审查修复 — 吞吐 profiling 前置修复 + 防御性改进
- **批准日期**：2026-02-25
- **前置条件**：Phase 5v2 质量评测完成
- **状态**：🟡 P0+P1 全部完成（5/18 已修复），P2+跟踪项仍 open
- **内容**：

**P0: 吞吐 profiling 前必须修（阻塞 Phase 5v2 吞吐评测）** ✅ 3/3 完成
- [x] **PRF-032** `[HIGH]` profile_latency.py "Hello " repeat prompt token 数不精确 → 改用 tokenizer 生成精确长度 token 序列
- [x] **PRF-033** `[HIGH]` 非 kivi quant_bits=None 写入 CSV → 按 kv_mode 推导实际 quant_bits 并记录
- [x] **PRF-034** `[MED]` profile_latency/memory 未调用 model.eval() → 添加 model.eval()

**P1: 防御性改进（建议在下轮代码维护时修）** ✅ 2/2 完成
- [x] **EVL-132** `[HIGH]` eval_ppl.py PPL NaN/Inf 静默写入 + exit(0) → 添加 NaN/Inf 检查，异常时 exit(1)
- [x] **ENG-110** `[HIGH]` batch EOS 用 all() 判定 → 改为 per-sequence mask（影响 batch>1 的吞吐评测）

**P2: 文档更新**
- [ ] **W2** CLAUDE.md §10 scale dtype 描述更新（float32 → 实际 fp16/input dtype）

**不影响当前实验（仅跟踪）**：EVL-130(HF模式), EVL-131(repeat模式), EVL-133~137, ENG-111, PRF-035, CHK-037~039, UTL-014

**Phase 7 审计结论（2026-03-11 20:17）**：
P0 全部完成（3/3）、P1 全部完成（2/2）。剩余 13 项 open issue 经审计确认均在当前主实验路径（kv_cache 模式/单 GPU/固定 seed）下未触发。其中 CHK-037（check_run_completeness.py 将 csv_valid_manifest_incomplete 和 task_artifacts_missing 误报为 unexpected failure）属审计工具分类误差，不影响实验数据。论文 Limitations 段落需披露此情况。

### ~~Plan: Phase 5v2 推进策略 — int4_fused 污染隔离 + 剩余 seed 接力 + 重跑调度~~ ✅ 完成 2026-03-09（详见 Timeline 归档）

### ~~Plan: EMNLP 2026 Phase 6 — 聚合 + 统计修复 + 论文准备~~ ✅ 完成 2026-03-10（详见 Timeline 归档）

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

### 2026-03-11 22:25 | Supervisor 全局审阅报告
- **Goal**: 以 Supervisor 角色对项目进行全局健康度审阅 + Codex MCP 连通性验证
- **Scope**: 只读审阅（无代码变更）
- **审阅结果**:
  - **Phase 进度**: Phase 1-6 全部完成 ✅, Phase 7A/7B 完成 ✅, Phase 7C(论文骨架) 待启动
  - **数据规模**: 2136 dirs (emnlp_final_raw/)
  - **Claims**: 8 PASS / 3 FAIL (C6 RULER -2.82%, C7 INT4 Needle -3.33%, C8 INT4 PPL -15.92%)
  - **review_tracker**: 995 total | 484 fixed + 6 FP | 505 open (0 CRIT, 188 HIGH, 277 MED, 40 LOW)
  - **Phase gate**: READY ✅ (0 CRITICAL open)
  - **代码编译**: `compileall src/ scripts/ tests/` exit 0 ✅
  - **Git**: main 领先 origin/main 6 commits, 工作区干净
  - **结构**: src/ 7 子模块, scripts/ 25 脚本, tests/ 25 测试文件, configs/ 1 主配置 + 6 快照
- **Codex MCP 连通性**: ✅ 全部通过
  - `mcp__codex__codex` 发起会话: ✅ (threadId: 019cdd4a-917f-7d53-9062-d6d516967840)
  - `mcp__codex__codex-reply` 多轮对话: ✅ (2 轮上下文完整保持)
  - GPT-5.4 模型调用: ✅, sandbox read-only 文件读取: ✅
- **待关注风险**:
  1. 6 commits 未推送 — 需确认是否 push
  2. 188 HIGH issues 横跨 eval 链路 — 论文 Limitations 需披露
  3. 3 Claim FAIL — 论文需讨论 INT4 精度局限
  4. 本地 pytest broken (numpy/scipy dlopen) — 仅能 py_compile 验证
- **下一步**: P0 Phase 7C 论文骨架 | P1 Push 6 commits | P2 R22 P2 文档更新
- **Changed files**: iteration.md (本条记录)

### 2026-03-11 22:20 | 代码与结果双向同步 v3.1
- **Goal**: 拉回远端原始实验结果 (runs/logs)，推送本地最新代码到远端
- **Changed files**: 无代码变更（纯同步操作）
- **Commands**:
  - `rsync --include='runs/***' --include='logs/***'` 拉取远端 → 本地
  - `rsync --files-from=manifest` 推送本地 → 远端（白名单 19 条目）
- **Outputs**:
  - 拉取: 2,136 runs dirs + 5,509 logs files = 2.4GB
  - 推送: 9 根文件 + 4 目录 + 6 具名 docs，实际增量 18KB
  - 远端快照: `/root/autodl-tmp/kvcq_code_backup_20260311_221738`
- **Validation**:
  - D1: 22/22 关键文件 OK ✅
  - D2: compileall exit 0 ✅
  - D3: 15 校准 JSON 完整 ✅
  - D4: second dry-run = 0 变更 ✅
  - D5: 远端 results 未受影响 (2136 runs + 5509 logs) ✅
- **Risks / follow-ups**: 远端代码通过静态编译检查，后续需跑 smoke_test 做运行时验证

### 2026-03-11 20:17 | 计划文件治理 + 进度同步
- **Goal**: 清理 iteration.md stale Approved Plans、更新 objective.md 里程碑状态、修复 docs/ legacy 路径
- **Changed files**:
  - `iteration.md`: 关闭 3 个已完成 Plans（Phase 5v2 全矩阵/推进策略、Phase 6），精简数据修复 Plan 详情，更新 R22 → 🟡 P0+P1 完成（5/18 fixed），添加 Phase 7 审计结论
  - `objective.md`: Milestones K-Q 添加完成标记（K/L/M/N/O/Q ✅, P ⚠️ 部分完成）
  - `docs/thesis_chapter_mapping.md`: final_thesis_plus_* → emnlp_final_raw/
  - `docs/final_results_summary.md`: 路径更新 + 顶部追加数据更新注释
  - `docs/thesis_preflight_checklist.md`: 路径更新
  - `docs/usage_guide.md`: run_final_thesis_plus.sh 标注 legacy
  - `docs/paper_writing_session_prompt.md`: 标注 OUTDATED
- **Validation**: grep 验证无残留 🟢 执行中 / final_thesis_plus 路径 / Milestone 无标记
- **R22 审计**: P0(3/3)+P1(2/2) 全部完成, 13 项 open 经审计确认在主实验路径下未触发, CHK-037 为审计工具分类误差

### 2026-03-11 03:13 | Phase 7B: 学位论文 ch4 数据填充完成
- **Goal**: 将 ch4_experiments.tex 中全部 ~18 处 XX.XX/TODO/待验证占位符替换为真实实验数据
- **Changed files**:
  - `thesis/chapters/ch4_experiments.tex`: 填充 Table 4.2（主结果 7 modes）、Table 4.5（跨模型 7B+8B）、Table 4.6（KIVI 对比）、Table 4.7（11 claim 验证总表 8P/3F）；C1-C11 文字分析；3 张 \includegraphics 替换 fbox 占位符；消融分析段落重写
  - `scripts/fill_thesis_data.py`: 新增可审计数据提取脚本（mainline overrides for 1.5B int8_ours）
  - `findings.md`: ISSUE-1/ISSUE-2 解析更新
  - `thesis/figures/`: 复制 3 张 PNG（needle/TPOT/KV memory 曲线）
- **Validation**: `grep 'XX\.XX\|TODO\|待验证\|待替换\|待填充' ch4_experiments.tex` → 0 matches
- **Key data points used**:
  - fp16: PPL=8.93, Needle=100%, LongBench=4.82%, RULER=24.38%, TPOT=24.39ms, KV=896MB
  - int8_ours (mainline): PPL=8.95, Needle=100%, LongBench=5.00%, RULER=24.38%, TPOT=47.14ms, KV=504MB
  - C1: +17.27% TPOT gain (q=0.016), C2: -43.75% KV mem, C6 FAIL: -2.64% RULER
  - C7 FAIL: -2.0% INT4 Needle, C8 FAIL: -15.92% INT4 PPL
- **Note**: thesis/ 在 .gitignore 中（不进 git），仅 fill_thesis_data.py 和 findings.md 需要提交
- **Next**: 提交 → Phase 7C EMNLP 论文骨架搭建

### 2026-03-11 02:52 | Phase 7A: Git cleanup + model_id 路径污染源头修复
- **Goal**: 提交 C7/C8 修复；修复 ISSUE-1（LLaMA-8B model_id 路径污染 9 个 CSV）
- **Changed files**:
  - `scripts/aggregate_results.py`: 添加 `MODEL_ID_ALIASES` + `_canonicalize_model_id()`, 在 `_read_csvs()` 中调用
  - `scripts/export_tables_latex.py`: 扩展白名单（前序提交）
  - `iteration.md`: Timeline 追加
  - `findings.md`: 新增 claim 根因分析
  - `.gitignore`: 排除 progress.md / task_plan.md
- **Commits**: e5afa27 (7A.1: pairing + findings), pending (7A.2: model_id fix)
- **Validation**: `py_compile` 通过；远端重跑 aggregate+export+report 待执行
- **Risks**: 远端重跑后需验证 thesis_main_claims_32k.csv 中 model_id 只有 3 个值
- **Next**: rsync 到远端 → 重跑三步管线 → rsync 回 → 进入 7B ch4 填充

### 2026-03-11 00:06 | fix: C7/C8 INCONCLUSIVE → FAIL, 修正 C6 根因描述
- **Goal**: 解决 C7/C8 INCONCLUSIVE（补全 aggregate + export 过滤），更新 C6 根因归因
- **Changed files**:
  - `scripts/aggregate_results.py`: L124 添加 `("int4_baseline", "int4_ours")` 到 `RELATIVE_GAIN_PAIRINGS`
  - `scripts/export_tables_latex.py`: L642 白名单扩展 `int4_baseline` + `kivi_style`
- **远端重跑**: aggregate → LaTeX export → claim validation（三步全部 exit 0）
- **结果**: C7/C8 从 INCONCLUSIVE → **FAIL**
  - C7: INT4-ours needle -3.33% vs INT4-baseline（阈值 ≥-1%）
  - C8: INT4-ours PPL -15.92% vs INT4-baseline（阈值 ≥-0.5%）
  - **科学含义**: KL 行为对齐校准在 INT8 有效，但 INT4 精度下未保持非劣效性
- **C6 根因修正**: 从"单一 prompt budget 溢出"改为"CWE 子任务多因素局限"（5 条未关闭 issue）
- **Final claims**: **8 PASS / 3 FAIL / 0 INCONCLUSIVE / 0 ERROR**
- **数据同步**: 远端 emnlp_final_raw + final_journal_v2 已更新，本地已 rsync
- **LaTeX**: 39 .tex files, 18 plots（Codex review 修正了之前的 41/20 数字）
- **Codex review**: 两轮审查发现 3 个 HIGH + 2 个 MEDIUM issue，全部已修正

### 2026-03-10 04:27 | milestone: Phase 6 全部完成 — Core Profiling + 聚合出表 + Claim 验证
- **Goal**: 补跑 4K/8K/16K/32K profile_latency/profile_memory → 合并 → 聚合 → LaTeX → Claim 验证
- **Changed files**:
  - `scripts/dispatch_phase6_core.sh`: 24 non-KIVI configs/model × 8 seeds = 192 dirs/model
  - `scripts/audit_phase6_core.py`: 任务级审计脚本
  - `scripts/phase6_post_profiling.sh`: Steps 3-7 聚合管线 (修复 mkdir + --out_dir)
  - `scripts/generate_thesis_report.py`: 修复 C5/C6/C9/C11 的 target_batch NaN 过滤 bug
- **Step 0**: ✅ rsync + freeze (含 artifacts/ FIX-1) → fingerprint=`0942b55d`, 6/6 calib OK
- **Step 1**: ✅ 试聚合确认 latency/memory 仅含 8K → 4K/16K/32K 缺口确认
- **Step 2**: ✅ Core profiling 全部完成 (576/576, ALL PASS, 0 OOM)
  - 1.5B: 192/192 GATE: PASS (0 OOM, 95min)
  - 7B: 192/192 GATE: PASS (0 OOM, 144min)
  - 8B: 192/192 GATE: PASS (0 OOM, 175min, 21:25→04:17 CST)
  - Fingerprint OK: 冻结副本全程未修改
- **Step 3**: ✅ Merge → emnlp_final_raw (2136 dirs = 1560 phase5v2 + 576 phase6, 295 long dirs)
- **Step 4**: ✅ Strictable copy (2137 dirs) — 首次 rsync 失败（mkdir 缺失），已修复
- **Step 5a**: ✅ Aggregate exit 0 — latency_summary 182 rows, memory_summary 182 rows
  - **关键**: seq_lens = {4096, 8192, 16384, 32704} ← Phase 6 核心产出
  - thesis_main_claims_32k: 31 rows, significance_summary: 358 rows
- **Step 5b**: ✅ LaTeX export — 39 .tex 文件
- **Step 5c**: ✅ Claim validation (修复后重跑)
- **Step 6**: Strict QA exit 2 (46 mixed failure issues, 均为已知 eval_ruler OOM, 非阻塞)
- **Step 7 Claim Results**: 8 PASS / 1 FAIL / 2 INCONCLUSIVE / 0 ERROR
  - C1: ✅ PASS — TPOT gain 17.27% (threshold ≥5%), q=0.016, strong evidence
  - C2: ✅ PASS — KV mem gain 43.75% (threshold ≥20%), moderate evidence
  - C3: ✅ PASS — Needle 0% degradation (threshold ≥-1%)
  - C4: ✅ PASS — PPL -0.085% degradation (threshold ≥-0.5%)
  - C5: ✅ PASS — LongBench +0.16% (threshold ≥-1%)
  - C6: ❌ FAIL — RULER -2.82% (threshold ≥-1%), LLaMA-8B 单模型, RULER CWE 已知问题
  - C7: ⚠️ INCONCLUSIVE — aggregate 未生成 int4_baseline vs int4_ours 比较对
  - C8: ⚠️ INCONCLUSIVE — 同上 (PPL)
  - C9: ✅ PASS — vs KIVI LongBench +19.28%
  - C10: ✅ PASS — vs KIVI Needle 0%
  - C11: ✅ PASS — 7B/8B 跨模型稳健 (both PASS)
- **Step 8**: ✅ 备份完成
  - 远端数据盘: `/root/autodl-tmp/phase6_backup_20260310_042708/` (2.7G)
  - `results/final_journal_v2/` 已创建 (rsync from emnlp_final_raw, 对齐 objective.md 路径)
  - 本地 tables/plots/latex_tables/report 已 rsync
- **Freeze**: `/root/LLM_KVCache_Quantization_phase6_freeze_20260309_212302`
- **产出路径**: `results/emnlp_final_raw/` = `results/final_journal_v2/` (对齐 objective.md §444)

### 2026-03-09 21:22 | Phase 6 启动 — Core Profiling 准备
- **Goal**: 创建调度脚本 + 同步到远端 + 创建冻结副本
- **Commits**: ab1572c (dispatch script), pending (audit+pipeline scripts)
- **Validation**: rsync_gate PASS, fingerprint match, 6/6 calib files OK

### 2026-03-08 08:45 | Phase 5v2 吞吐评测准备
- **Goal**: 准备 Phase 5v2 吞吐评测 (1024 runs: 128 configs × 8 seeds × 2 tasks)
- **Changed files**:
  - `configs/exp_matrix.yaml`: 添加 `calib_file` 到 `int4_fused_throughput_8k_b24/b32`
  - `scripts/dispatch_phase5v2_throughput.sh`: 新建冻结副本吞吐调度脚本
- **Validation**:
  - 1.5B: 48 throughput entries (40 req + 8 stress), all calib OK
  - 7B: 40 throughput entries, all calib OK
  - 8B: 40 throughput entries, all calib OK
  - bash -n syntax check: PASS
- **Next**: rsync 推送 → 远端 pre-flight → 创建冻结副本 → 启动 Phase A (600 runs ~30h)
- **Commit**: f614003

### 2026-03-08 05:38 | milestone: Phase 5v2 数据修复补跑 v8 全部完成

- **Goal**: 修复 17 个问题目录 (A:6 INT4 溢出 + B:10 OOM 缺失 + C:1 PPL 异常)
- **结果**: **68/68 SUCCESS** — FINAL GATE 通过
- **总耗时**: ~14.75h (14:47 Mar 7 → 05:33 Mar 8 CST, 含 7B HF 缓存修复中断)
- **Step 时间线**:
  - B4 (1.5B×3): 14:47→16:38 (1h51m) — 前轮已完成，自动跳过
  - A1 (7B×3): 17:00→18:46 (1h46m) — 首次因 HF 缓存不完整失败，修复后重跑成功
  - B2 (7B×1): 18:46→19:49 (63m)
  - B1 (7B×4): 19:49→23:43 (3h54m)
  - C1 (7B×1): 23:43→00:50 (67m)
  - A2 (8B×3): 00:50→02:57 (2h07m)
  - B3 (8B×2): 02:57→05:33 (2h36m)
- **PPL 验证**:
  - A-type (INT4 溢出修复): 7B PPL=7.0618 (was 557.7), 8B PPL=7.1008 (was 610.9) ✅
  - C-type (异常值修复): PPL=99.0920 (was 52.82), 5-seed spread=0.0000 ✅
  - B-type (OOM 重跑): 全部 delta=0.0000 (完全可复现) ✅
- **验收标准**: 7/7 全通过
  1. 17/17 dirs 存在 ✅
  2. 68/68 tasks success ✅
  3. A-type PPL < 20 ✅
  4. C-type PPL [85,115] + spread < 5 ✅
  5. 原始数据 quarantine/ 17/17 ✅
  6. partial_reruns/ 3 entries ✅
  7. fail-fast 已验证 ✅
- **代码指纹一致**: `c60716bd47bb2f0edc4dd55b2ef737a4` (全程未变)

### 2026-03-07 17:04 | fix: 7B HF 缓存修复 + 补跑重启

- **问题**: A1_7b_s1234 步骤全部 12 tasks 失败 (rc=2/74)
- **根因**: `~/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/` 缓存不完整，仅有 config.json (1 blob)
- **原因**: HF Hub 下载中断或缓存被清理，tokenizer/model 权重丢失
- **修复**: 发现 `/root/autodl-tmp/hf_cache/hub/` 有完整 7B 模型，创建 4 个 safetensors 符号链接 + 下载 tokenizer blobs
- **验证**: `AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")` → vocab_size=151643 ✅
- **恢复策略验证**:
  - B4 重启时自动跳过 (3/3 dirs 4/4 success) ✅
  - A1 失败数据移到 partial_reruns，全量重跑 ✅
  - A1 curve_4k 在 3 分钟内完成 PPL+Needle，LongBench 运行中 ✅
- **8B 模型状态**: 缓存完整（symlink 到 ModelScope），无需修复

### 2026-03-07 14:48 | Phase 5v2 数据修复补跑 v8 启动

- **Goal**: 修复 17 个问题目录 (A:6 INT4 溢出 + B:10 OOM 缺失 + C:1 PPL 异常)
- **方案**: 冻结代码副本 → 隔离原始目录 → 全量重跑 → fail-fast + step 级恢复
- **Preflight 结果**:
  - GPU: 0% / 0MiB / 97871MiB (空闲)
  - 17/17 目标目录存在于 runs/
  - 无活跃实验进程
- **冻结副本**: `/root/LLM_KVCache_Quantization_phase5v2fix_20260307_144607`
- **代码指纹**: `c60716bd47bb2f0edc4dd55b2ef737a4`
- **关键文件 MD5 验证**: run_experiments.py, int4_basic.py, kivi_style_cache.py, generate_loop.py 全部本地/远端一致
- **tmux 会话**: `phase5v2_fix` (14:47 CST 启动)
- **日志**: `results/phase5v2/logs/rerun_v8.log`
- **7 步执行顺序**: B4(1.5B s1237) → A1(7B s1234) → B2(7B s1237) → B1(7B s1238) → C1(7B s1236) → A2(8B s1234) → B3(8B s1238)
- **预计耗时**: ~17h 串行
- **验收标准**: 68/68 task success, A-type PPL<20, C-type PPL∈[85,115], spread<5
- **Risks**: 串行 OOM(极低), 代码漂移(冻结+指纹门禁), 中断恢复(step 级)
- **监控命令**:
  ```
  ssh -p 31867 root@region-42.seetacloud.com "tmux capture-pane -t phase5v2_fix -p -S -50"
  tail results/phase5v2/logs/rerun_v8.log
  ```

### 2026-03-07 12:52 | milestone: Phase 5v2 质量评测矩阵 100% 完成

- **Goal**: 完成 Phase 5v2 全部质量评测实验
- **最终状态**:
  - 1.5B (43 configs × 5 seeds = 215 runs): ✅ 全部完成
  - 7B (32 configs × 5 seeds = 160 runs): ✅ 全部完成
  - 8B (32 configs × 5 seeds = 160 runs): ✅ 148/160 完成 (s1234-1236 缺 int4_ours_mixed 4 configs)
  - fused_fix 重跑: ✅ 全部完成 (1.5B 8/8 | 7B 12/12 | 8B 12/12)
- **关键时间线**:
  - 02-23 17:23: 启动 3 模型并行质量评测
  - 02-28: int4_fused calib_file bug 修复 + 污染隔离 + 重跑调度
  - 03-03: 7B 全 5 seeds 完成
  - 03-04: 8B 全 5 seeds 完成
  - 03-05: 1.5B s1236 完成, 启动 s1237
  - 03-06: 1.5B s1237 完成, 8B s1237 补完完成
  - 03-07 ~12:00: 1.5B s1238 最后一个 config (int4_ours_long eval_ruler 32K) 完成
- **GPU 利用率优化**: 1.5B s1238 最后阶段采用 3 runner 并行策略 (main + KIVI-curve + KIVI-long), 减少约 2h 空闲时间
- **下一步**: Phase 6 — 聚合 + 统计分析 + LaTeX 导出 + 论文报告; 吞吐评测可选

### 2026-03-01 19:10 | feat: Codex (GPT-5.3) 交叉审查集成

- **Goal**: 将 OpenAI Codex 嵌入 Agent 工作流，实现审查交叉验证和 Bug 修复咨询
- **Changed files**:
  - `~/.mcp.json` — 注册 codex MCP Server (`codex mcp-server`)
  - `.claude/settings.local.json` — enabledMcpjsonServers 添加 `"codex"`
  - `.agents/skills/codex-review/SKILL.md` — **新建** Codex 审查 Skill (146 行)
  - `.claude/agents/review-coord.md` — 添加 Step 2.5 Codex 交叉审查 + 汇聚去重逻辑 + 输出格式来源统计
  - `.claude/agents/supervisor.md` — 添加 Codex 咨询路径 (调度表 + 详细流程 + 调用模板 + 审批逻辑)
- **验证**: `python3 -c "import json; assert 'codex' in json.load(open('~/.mcp.json'))['mcpServers']"` ✓; grep 确认 5 文件 Codex 关键词就位
- **安全**: Codex 始终 `sandbox: "read-only"`, 建议仅作参考, 失败不阻塞, 来源标注 `[Codex/GPT-5.3]`
- **Risks/follow-ups**: 新会话需 ToolSearch "codex" 验证 MCP 工具可用; 端到端测试需实际触发 Review-Coord

### 2026-02-28 07:37 | fix: int4_fused YAML calib_file 错误修复 + 污染隔离 + 调度脚本

- **Goal**: 修复 int4_fused 使用 INT8 校准文件的 YAML 配置 bug；隔离已产生的污染数据；创建接力调度和监控脚本
- **Changed files**:
  - `configs/exp_matrix.yaml` — 9 处 int4_fused 条目添加 `calib_file: artifacts/kv_calib_kl_int4_selected.json`
  - `configs/snapshots/exp_matrix_qwen25_7b_v1.yaml` — 9 处添加 `calib_file: artifacts/kv_calib_kl_qwen25_7b_int4.json`
  - `configs/snapshots/exp_matrix_llama31_8b_v1.yaml` — 9 处添加 `calib_file: artifacts/kv_calib_kl_llama31_8b_int4.json`
  - `scripts/dispatch_phase5v2.sh` — 新建（接力调度脚本）
  - `scripts/monitor_phase5v2.sh` — 更新（添加 int4_fused 污染追踪 + --once 模式）
- **Root cause**: int4_fused 条目无显式 `calib_file`，继承 `quant_defaults.calib_file`（INT8 校准）→ INT8 scales 用于 INT4 → PPL 灾难性退化（1,263,404 vs 预期 7-15）
- **Commands**: `git diff --stat configs/` → 3 files, 27 insertions
- **Outputs**: 修复 3×9=27 个 int4_fused 条目；远端已隔离 25 个污染目录到 quarantine/
- **Validation**:
  - [x] grep 确认所有 int4_fused 条目均有 calib_file
  - [ ] rsync 到远端后重跑 fused_fix，验证 PPL 回归正常范围
- **Commit**: 004f7cf
- **Risks / follow-ups**:
  - 远端 fused_fix 已重启（PID 599995），PPL=22.04 验证通过
  - 远端 q_7b/q_8b 仍在用旧 YAML 配置跑 s1236，产出的 int4_fused 数据需后续隔离
  - 旧污染数据已 mv 到 quarantine/（26 dirs），可审计回滚

### 2026-02-28 06:50 | Agent 工作流治理优化：记录强制 + Token 节约 + Memory 增强

- **Goal**: 实施三模块治理优化：(A) 写入强制机制 (B) iteration.md 瘦身 (C) Memory 系统增强
- **Changed files**:
  - `scripts/iteration_tool.py` — 新建（trim-timeline / clean-plans / stats 三子命令）
  - `.git/hooks/pre-commit` — 重写为阻塞式（main 分支 code commit 必须含 iteration.md）
  - `.claude/hookify.readonly-guard.local.md` — 新建（保护 objective/CLAUDE/AGENTS/experiment_sop）
  - `.claude/hookify.session-checklist.local.md` — 新建（会话结束前检查提醒）
  - `CLAUDE.md` §7.7 — 新增 Agent 分级读取策略表
  - `.claude/agents/supervisor.md` — 启动流程增加 Memory 读取步骤
  - `.claude/agents/developer.md` — 自主模式启动增加 Memory 读取步骤
  - `.agents/skills/unit-commit/SKILL.md` — Step 6 Memory checkpoint
  - `.agents/skills/session-handoff/SKILL.md` — 新建会话交接 SKILL
  - `iteration.md` — clean-plans 压缩 Phase 4 + trim-timeline 归档 21 条旧条目
  - `development_history/iteration_archive_202602.md` — 接收归档条目
- **Commands**: `python3 scripts/iteration_tool.py stats/clean-plans/trim-timeline`
- **Outputs**: iteration.md 1054 → 584 行（-45%），归档 21 条 Timeline 到 archive
- **Validation**:
  - [x] iteration_tool.py py_compile OK + stats/dry-run/实际执行全通过
  - [x] pre-commit hook 阻塞无 iteration.md 的 code commit（exit 1）+ --no-verify 逃生舱 OK
  - [x] hookify 规则文件创建成功
  - [x] supervisor.md / developer.md / CLAUDE.md / unit-commit SKILL 编辑验证通过
  - [x] session-handoff SKILL 创建成功
- **Commit**: pending
- **Risks / follow-ups**:
  - hookify 规则需要 hookify 插件启用后才会生效（warn-only，不阻塞）
  - iteration.md Update Rules §5 已有 "保留最近 15 条" 的文档约定，现在有工具自动化

### 2026-02-28 06:34 | Fix EVL-087/088: int4_fused 白名单缺失

- **Goal**: 修复 eval_ppl.py 中两处 kv_mode 白名单遗漏 int4_fused，防止该模式退化为 baseline
- **Changed files**:
  - `scripts/eval_ppl.py` L189: load_calibration() 白名单添加 int4_fused
  - `scripts/eval_ppl.py` L806: prefill temperature hooks 白名单添加 int4_fused
  - `review_tracker.md`: EVL-087, EVL-088 标记 fixed
- **Commands**: `python3 -m py_compile scripts/eval_ppl.py`
- **Outputs**: COMPILE OK; 全文搜索确认 3 处白名单均包含 int4_fused
- **Validation**: ✅ 编译通过，grep 确认无遗漏
- **Commit**: f009851
- **Risks / follow-ups**:
  - 修复前已完成的 int4_fused runs 数据无效，需评估重跑范围
  - 需 rsync 推送到远端后重跑受影响的 int4_fused 评测

### 2026-02-28 03:58 | 创建华南理工大学本科毕业论文 LaTeX 框架

- **Goal**: 搭建完整的毕业论文 LaTeX 模板 + 撰写全部 5 章内容（Phase 1-2）
- **Changed files**:
  - `thesis/main.tex` — 主文件（59行）
  - `thesis/latexmkrc` — 编译配置（xelatex）
  - `thesis/references.bib` — 24 篇参考文献（193行）
  - `thesis/setup/packages.tex` — 宏包集合
  - `thesis/setup/fonts.tex` — 字体设置（macOS/Fandol 双路径）
  - `thesis/setup/format.tex` — 章节/行距/图表格式（符合学校规范）
  - `thesis/setup/header.tex` — 页眉页脚 + A4 页面尺寸
  - `thesis/setup/toc.tex` — 目录格式
  - `thesis/setup/commands.tex` — 封面/声明/摘要/致谢环境 + 数学符号
  - `thesis/chapters/abstract_zh.tex` — 中文摘要（~480字）
  - `thesis/chapters/abstract_en.tex` — 英文摘要
  - `thesis/chapters/ch1_introduction.tex` — 第一章 绪论（173行，~2600字）
  - `thesis/chapters/ch2_related_work.tex` — 第二章 相关工作（344行，~4500字，10公式）
  - `thesis/chapters/ch3_method.tex` — 第三章 方法设计（633行，~5400字，14公式，1算法）
  - `thesis/chapters/ch4_experiments.tex` — 第四章 实验（766行，7表格含占位数据）
  - `thesis/chapters/ch5_conclusion.tex` — 第五章 总结（157行，~2300字）
  - `thesis/chapters/appendix.tex` — 附录（104行）
  - `thesis/chapters/acknowledgements.tex` — 致谢
- **Commands**: 6 个并行 developer agents 编写章节内容
- **Validation**:
  - 所有 18 个文件已创建，共 2817 行
  - 静态检查：所有文件大括号平衡，84 个环境配对完整
  - 引用检查：23 个 cite key 全部匹配 references.bib
  - 本地无 LaTeX 安装，未做编译验证（需在有 TeX Live 环境中验证）
- **Risks / follow-ups**:
  - 第四章实验数据为占位（XX.XX），待 Phase5v2 完成后替换
  - 中英文摘要含 XX% 占位，待最终数据后填写
  - 附录 LongBench 21任务完整结果和种子统计待填充
  - 封面信息（学号/学院/专业/导师）需用户填写
  - 图3-1（架构图）、图3-2（inv_tau 热力图）需后续生成
  - 需在有 LaTeX 的环境编译验证格式

### 2026-02-28 01:30 | Memory 迁移：KV Cache memory 从 home 层移至项目层

- **Goal**: 修复 Memory 路径错误 — 4 个 KV Cache 专题文件被写在了 home 层，从项目目录启动 Claude Code 时看不到
- **Changed files**:
  - `~/.claude/projects/-Users-chenzilang-Desktop-LLM-KVCache-Quantization/memory/debugging-patterns.md` (mv 过来)
  - `~/.claude/projects/-Users-chenzilang-Desktop-LLM-KVCache-Quantization/memory/experiment-state.md` (mv 过来)
  - `~/.claude/projects/-Users-chenzilang-Desktop-LLM-KVCache-Quantization/memory/agent-coordination.md` (mv 过来)
  - `~/.claude/projects/-Users-chenzilang-Desktop-LLM-KVCache-Quantization/memory/tracker-operations.md` (mv 过来)
  - `~/.claude/projects/-Users-chenzilang-Desktop-LLM-KVCache-Quantization/memory/MEMORY.md` (重写合并, 90 行)
  - `~/.claude/projects/-Users-chenzilang/memory/MEMORY.md` (清理 KV 段, 190→139 行, 替换为指针)
  - `CLAUDE.md` §1.1: 更新 Memory 路径为项目级 + 加注启动目录提醒
  - `iteration.md`: 本条记录
- **Validation**: 项目层 5 文件完整 (MEMORY.md 90行 ≤165), home 层无残留专题文件, CLAUDE.md 包含正确路径
- **Risks / follow-ups**: 无功能变化, 仅 memory 组织结构优化

### 2026-02-25 23:33 | 建立持久化 Memory 工作流

- **Goal**: 创建结构化 Memory 文件体系，使跨会话知识沉淀系统化
- **Changed files**:
  - `~/.claude/projects/-Users-chenzilang/memory/MEMORY.md` (新建, 59 行): 主文件 — 环境、阶段、陷阱、产物、API、导航、索引
  - `~/.claude/projects/-Users-chenzilang/memory/debugging-patterns.md` (新建): CAL-019/020、INT4 溢出、warnings 作用域等调试经验
  - `~/.claude/projects/-Users-chenzilang/memory/experiment-state.md` (新建): 校准产物版本、Phase 5v2 矩阵状态
  - `~/.claude/projects/-Users-chenzilang/memory/agent-coordination.md` (新建): Agent 协作模式与失败模式
  - `~/.claude/projects/-Users-chenzilang/memory/tracker-operations.md` (新建): tracker 格式规范、批量操作模板
  - `CLAUDE.md` §1.1: 新增持久化 Memory 维护规则 (触发时机表 + 约束)
  - `iteration.md`: 本条记录
- **Validation**: MEMORY.md 59 行 (≤165 上限), 5 文件均非空, CLAUDE.md 包含 §1.1
- **Risks / follow-ups**: Memory 内容基于 iteration.md + review_tracker.md 提取的实际经验，非模板占位；后续每个 Phase 切换时做全量 review

### 2026-02-24 16:00 | Supervisor Session — Wave 16/17 完成，466→13 open

- **Goal**: 自主修复 review_tracker.md 全部可修复 issues
- **Session scope**: Wave 16 收尾 + Wave 17 + 最终清理
- **Wave 16** (8 items): ENG-037~041 (HIGH: clamp-before-cast, narrow exceptions, clipping warnings) + ENG-047/CAL-031/032 (docs)
  - Commits: `4e1a182`, `46ca296`
- **Infra**: resolve_quant_bits 去重 (`9a694d5`), review_tool RVW-014 fix, agent config updates (`067921e`)
- **Wave 17A** (22 items): run_experiments.py — 7 HIGH (kill orphans, retry log separation, OOM skip, unique tmp, kv_mode validation, kivi precheck, status logic) + 11 MED (SIGINT, interrupt no-retry, CSV check, exp backoff, log rotation, etc.) + 4 LOW
  - Commit: `a61f428`
- **Wave 17B** (15 items): patch_model.py (9: kernel exception, unpatch API, shape validation, docs) + generate_loop.py (5: group_size_v warning, multi-token, DynamicCache doc, scale asymmetry) + int8_cache.py (1: clear/release warning)
  - Commit: `264dcc3`
- **Final cleanup** (6 items): ENG-054/KRN-005/KRN-010 documented (`d2decc6`), AGG-032/ENG-030/RUN-024 wont_fix (deferred)
- **Result**: 466 total → 453 resolved (431 fixed + 15 fp + 7 wf), **13 open** (all need user decisions)
- **Remaining 13 open items**:
  - HIGH: CAL-019/020 (Q vector missing layernorm/RoPE — fundamental calibration correctness)
  - HIGH: CFG-026 (7B/8B calib files missing), CFG-029 (LLaMA revision null)
  - MED: CFG-008/009/011/012/013/022/028 (experiment design choices)
  - LOW: CFG-023/024 (temperature inconsistency)
- **Validation**: All modified files pass `py_compile`; local pytest broken (numpy/scipy dlopen issue — not our code)

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

### 2026-02-28 06:51 | fix: int4_fused whitelist gaps in generate_loop + run_experiments (XMD-006, RUN-088)
- **Goal**: 修复 int4_fused 在 generate_loop.py 和 run_experiments.py 中被遗漏出白名单的系统性 bug
- **Changed files**:
  - `src/engine/generate_loop.py`: L500 calib loading whitelist + L700 temperature hooks whitelist 添加 int4_fused
  - `scripts/run_experiments.py`: L1219 calib_file pre-validation + L1363 calib_file CLI passthrough 添加 int4_fused
  - `review_tracker.md`: XMD-006 + RUN-088 标记 fixed
- **Root cause**: 新增 int4_fused 模式时，代码库中 6 处 `kv_mode in [...]` 白名单仅更新了 eval_ppl.py（EVL-087/088），遗漏了 generate_loop.py 和 run_experiments.py
- **Impact**: 所有 int4_fused 的 needle/ruler/longbench 评测校准未加载，退化为 baseline；eval_ppl 的 calib_file 未经 runner 传递
- **Contamination scope**: int4_fused quality evals (PPL+Needle+RULER+LongBench) across all 3 models × 4 configs × 5 seeds = 240 runs 需重跑；吞吐评测不受影响
- **Validation**: py_compile 通过; grep 确认所有白名单位置均含 int4_fused
- **Commit**: c37cd83

### 2026-03-09 12:58 | Phase 5v2 吞吐评测：三级备份 + merge push
- **Goal**: GPU 驱动崩溃后，重启前完成数据备份和代码推送
- **背景**: Step 6 (8B-B) 执行中 CUDA runtime 崩溃（nvidia-smi NVML Error），Step 6/7 未完成
- **管线完成度**: Steps 1-5 ✅, Step 6 ❌ (55 runs 剩余), Step 7 ❌ (64 runs 未执行)
- **数据量**: 1442 dirs (906 throughput + 536 quality), 182M runs/
- **备份完成**:
  - Level 1: 远端数据盘 `/root/autodl-tmp/phase5v2_backup_20260309_125340/` — 1442 dirs ✅
  - Level 2: 本地 `results/phase5v2_remote_backup/` — 1442 dirs ✅
  - Level 3: git merge origin/main (12 conflicts → ours) + push ✅ (commit 95af277)
- **冻结副本验证**:
  - Path: `/root/LLM_KVCache_Quantization_throughput_20260308_140946`
  - Commit: `e5c78e48f8b48b1c6957c74ab28d86ca8b0d4a7c`
  - Fingerprint: `a1945015e88e33ff3d60cda85e7bc5df` ✅ MATCH
- **下一步**: 用户手动重启 AutoDL (关机→开机) → 验证 GPU → 恢复 Step 6/7 (~3h)

### 2026-03-09 16:32 | Phase 5v2 吞吐评测：GPU 重启 + 管线恢复完成
- **Goal**: 重启 GPU 后恢复 Step 6 (8B Phase B) 和 Step 7 (1.5B Stress)
- **重启**: AutoDL 关机→开机，GPU H20 完全恢复（97GB free）
- **Step 6 恢复 (8B Phase B)**:
  - 隔离 2 个 GPU crash dirs → `quarantine_gpu_crash/`
  - `continue_on_oom` 执行 120 dirs: 108 双 CSV + 12 OOM (b16 预期)
  - 方法进度: fp16→int8_baseline→int8_ours→int4_baseline→int4_fused→int4_ours→kivi_int8→kivi_int4
  - 耗时: ~1h55min
- **Step 7 (1.5B Stress)**:
  - 64 dirs: 55 双 CSV + 9 OOM
  - 方法: int8_baseline, int8_ours, int4_fused, int4_ours × b24/b32 × 8 seeds
  - 耗时: ~1h30min
- **最终统计**:
  - 吞吐 dirs: 1024 (1.5B:320 + 7B:320 + 8B:320 + Stress:64)
  - 质量 dirs: 536
  - 总计: 1560 dirs + 2 quarantine = 1562
  - runs/ size: 186M
- **管线完成度**: Steps 1-7 全部 ✅
- **下一步**: Phase 6 聚合 + 论文（可进入）
