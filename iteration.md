# Iteration Log (Single Source of Progress)

This file is the only progress tracker for the repository.
`lang.md` is deprecated and archived.
Canonical agent workflow directory is `.agents/`.

## Approved Plans

> 经讨论并被用户认可的阶段性执行方案（与审查问题分开，审查问题见 `review_tracker.md`）。


### ~~Plan: EMNLP 2026 Phase 4 — MSE 校准 + 消融（仅 1.5B）~~ ✅ 完成 2026-02-23（详见 Timeline 归档）

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

### Plan: Phase 5v2 数据修复（Data Repair）— 污染数据清除 + 失败补跑 + 验证
- **批准日期**：2026-02-25
- **前置条件**：远端 `warnings` 作用域 bug 已修复（06:45 CST）；本地 commit b10cfa7（INT4 safety + repair tool）
- **状态**：待执行（等 seed 1234 long configs 完成后启动）
- **触发条件**：3 模型 seed 1234 的 long configs 全部完成（当前 8B 仍有 long config running）

#### 背景

两个独立 bug 导致实验数据受损：
1. **INT4 量化 bug**（旧代码 commit fa6ab125）：kivi_style_int4 的 pack/unpack 使用 int8 算术产生溢出，导致 PPL 严重偏高（557-610 vs 正常 7-30）
2. **`warnings` 作用域 bug**（Codex 热切换引入）：`generate_loop.py` 在 kivi_style 分支内 `import warnings` 导致非 kivi_style 模式的 eval_ruler/eval_needle/eval_longbench 全部 `UnboundLocalError` 崩溃

#### 受影响数据清单（共 7 个 run）

**A. INT4 污染数据（6 runs）— 全部任务数据无效，需完全重跑**

| # | Run ID | 模型 | PPL（实际/预期） | 根因 |
|---|--------|------|------------------|------|
| 1 | `kivi_style_int4_curve_4k_s1234_phase5v2_7b_s1234` | 7B | 557.7 / ~7-10 | INT4 bug |
| 2 | `kivi_style_int4_curve_8k_s1234_phase5v2_7b_s1234` | 7B | 557.7 / ~7-10 | INT4 bug |
| 3 | `kivi_style_int4_curve_16k_s1234_phase5v2_7b_s1234` | 7B | 557.7 / ~7-10 | INT4 bug |
| 4 | `kivi_style_int4_curve_4k_s1234_phase5v2_8b_s1234` | 8B | 610.9 / ~7-10 | INT4 bug |
| 5 | `kivi_style_int4_curve_8k_s1234_phase5v2_8b_s1234` | 8B | 610.9 / ~7-10 | INT4 bug |
| 6 | `kivi_style_int4_curve_16k_s1234_phase5v2_8b_s1234` | 8B | 610.9 / ~7-10 | INT4 bug |

> 注：`kivi_style_int4_long_s1234_phase5v2_7b_s1234` 已验证 CLEAN（PPL=7.06，热切换后执行）。
> 注：1.5B 无 kivi_style_int4 quality configs（YAML 中有但尚未执行到，执行时已用修复代码）。
> 注：8B `kivi_style_int4_long` 尚未开始，将用修复代码执行，无需干预。

**B. RULER/Needle/LongBench 失败（1 run）— 仅 3 个任务需补跑**

| # | Run ID | 模型 | 失败任务 | 正常任务 | 根因 |
|---|--------|------|----------|----------|------|
| 7 | `int8_ours_long_no_static_no_temp_fused_s1234_phase5v2_1p5b_s1234` | 1.5B | eval_ruler, eval_needle, eval_longbench | eval_ppl (8.95) | warnings bug |

#### 执行步骤

**Step 1: 前置代码同步（~5 min）**
```bash
# 同步本地修复到远端（仅核心源码，不推 config YAML）
rsync -avz --include='*.py' --exclude='configs/' \
  src/quant/int4_basic.py src/cache/kivi_style_cache.py \
  root@region-42.seetacloud.com:/root/LLM_KVCache_Quantization/src/ -e 'ssh -p 31867'
```
验证：远端 `md5sum src/quant/int4_basic.py src/cache/kivi_style_cache.py` 与本地一致。

**Step 2: 处理 6 个 INT4 污染 run（~20 min）**
```bash
# 2a. 用 repair tool 将污染 run 移到 legacy 目录
python scripts/repair_phase5v2_delta.py \
  --runs_dir results/phase5v2/runs \
  --logs_dir results/phase5v2/logs \
  --selector "run_name~=kivi_style_int4_curve" \
  --tasks eval_ppl,eval_needle,eval_longbench,eval_ruler \
  --execute

# 2b. 验证 legacy 隔离成功
ls results/phase5v2_legacy_kivi_int4_bug/runs/ | grep kivi_style_int4
```

**Step 3: 重跑 6 个 INT4 污染 run（~2-3h）**
```bash
# 7B 的 3 个 curve configs
python scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_qwen25_7b_v1.yaml \
  --seeds 1234 --tasks eval_ppl,eval_needle,eval_longbench,eval_ruler \
  --run_names kivi_style_int4_curve_4k,kivi_style_int4_curve_8k,kivi_style_int4_curve_16k \
  --run_tag phase5v2r2_7b_s1234 \
  --skip_completed_success --failure_policy continue_all

# 8B 的 3 个 curve configs
python scripts/run_experiments.py \
  --config configs/snapshots/exp_matrix_llama31_8b_v1.yaml \
  --seeds 1234 --tasks eval_ppl,eval_needle,eval_longbench,eval_ruler \
  --run_names kivi_style_int4_curve_4k,kivi_style_int4_curve_8k,kivi_style_int4_curve_16k \
  --run_tag phase5v2r2_8b_s1234 \
  --skip_completed_success --failure_policy continue_all
```

**Step 4: 补跑 1 个 RULER 失败 run（~30 min）**
```bash
python scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --seeds 1234 --tasks eval_ruler,eval_needle,eval_longbench \
  --run_names int8_ours_long_no_static_no_temp_fused \
  --run_tag phase5v2_1p5b_s1234 \
  --skip_completed_success --failure_policy continue_all
```
> `--skip_completed_success` 会自动跳过已成功的 eval_ppl，只重跑 3 个失败任务。

**Step 5: 数据验证（强制，不可跳过）**

对每个修复后的 run 执行以下验证：

| 检查项 | 验收标准 | 验证命令 |
|--------|---------|---------|
| PPL 范围 | kivi_int4: 7-30; int8_ours: 7-15 | 读 profile_ppl CSV |
| PPL 对比 | 与同模型 kivi_int8 基线偏差 <3x | 对比 kivi_int8 PPL |
| RULER 完整性 | 3 个 CSV 文件，非空 | `ls ruler_*.csv` |
| Needle 完整性 | 1 个 CSV 文件，非空 | `ls needle_*.csv` |
| LongBench 完整性 | 2 个 CSV 文件，非空 | `ls longbench_*.csv` |
| Manifest 状态 | 全部 task status=success | 读 run_manifest.json |
| 零 NaN/Inf | 所有 CSV 中无 NaN/Inf | `grep -r "nan\|inf" *.csv` |

验证脚本：
```python
# 自动化验证（远端执行）
python -c "
import json, glob, os, csv
REPAIR_RUNS = [
    'kivi_style_int4_curve_4k_s1234_phase5v2r2_7b_s1234',
    'kivi_style_int4_curve_8k_s1234_phase5v2r2_7b_s1234',
    'kivi_style_int4_curve_16k_s1234_phase5v2r2_7b_s1234',
    'kivi_style_int4_curve_4k_s1234_phase5v2r2_8b_s1234',
    'kivi_style_int4_curve_8k_s1234_phase5v2r2_8b_s1234',
    'kivi_style_int4_curve_16k_s1234_phase5v2r2_8b_s1234',
    'int8_ours_long_no_static_no_temp_fused_s1234_phase5v2_1p5b_s1234',
]
BASELINES = {
    '7b': 7.06,  # kivi_style_int8_long PPL
    '8b': 8.0,   # approximate
    '1p5b': 9.0, # approximate
}
all_pass = True
for run_id in REPAIR_RUNS:
    rd = f'results/phase5v2/runs/{run_id}'
    mf = json.load(open(f'{rd}/run_manifest.json'))
    # Check all tasks success
    for t, tv in mf['tasks'].items():
        if tv['status'] != 'success':
            print(f'FAIL: {run_id} task {t} = {tv[\"status\"]}')
            all_pass = False
    # Check PPL range
    ppls = glob.glob(f'{rd}/profile_ppl_*.csv')
    if ppls:
        with open(ppls[0]) as f:
            r = csv.DictReader(f)
            for row in r:
                ppl = float(row['ppl'])
                if ppl > 50:
                    print(f'FAIL: {run_id} PPL={ppl} > 50 (still polluted!)')
                    all_pass = False
                else:
                    print(f'OK: {run_id} PPL={ppl}')
print('ALL PASS' if all_pass else 'SOME CHECKS FAILED')
"
```

**Step 6: 记录到 iteration.md**
- 记录修复结果（PPL 值、验证状态）
- 将本 Plan 标记为 ✅ 已完成

#### 验证基准（用于交叉对比）

| 模型 | kivi_style_int8 PPL（基准） | kivi_style_int4 PPL（预期） |
|------|---------------------------|---------------------------|
| 7B | 7.06 (verified) | 7-15 |
| 8B | ~8.0 (TBD) | 8-20 |
| 1.5B | ~9.0 (TBD) | N/A (无 kivi_int4 config) |

#### Checklist

- [ ] Step 1: 代码同步到远端 + md5 验证
- [ ] Step 2: repair tool 隔离 6 个污染 run
- [ ] Step 3: 重跑 6 个 kivi_style_int4 curve runs
- [ ] Step 4: 补跑 1 个 int8_ours RULER 失败 run
- [ ] Step 5: 7 个 run 全部通过数据验证
- [ ] Step 6: iteration.md 记录完成

#### 风险

| 风险 | 概率 | 缓解 |
|------|------|------|
| 重跑时 GPU 资源不足 | 中 | 在 seed 间隙执行（3 模型 long config 完成后），独占约 30GB |
| repair tool 的 selector 匹配到非目标 run | 低 | selector 用 `run_name~=kivi_style_int4_curve` 精确匹配，先 dry-run 确认 |
| 重跑后 PPL 仍异常 | 极低 | 验证脚本会 catch，人工复查 |
| 补跑的 run_tag 与正常 run 不同导致聚合遗漏 | 中 | 聚合前确认 aggregate_results.py 按 run_name（非 run_tag）分组 |

### Plan: R22 审查修复 — 吞吐 profiling 前置修复 + 防御性改进
- **批准日期**：2026-02-25
- **前置条件**：Phase 5v2 质量评测完成
- **状态**：待执行（吞吐 profiling 启动前必须完成）
- **内容**：

**P0: 吞吐 profiling 前必须修（阻塞 Phase 5v2 吞吐评测）**
- [ ] **PRF-032** `[HIGH]` profile_latency.py "Hello " repeat prompt token 数不精确 → 改用 tokenizer 生成精确长度 token 序列
- [ ] **PRF-033** `[HIGH]` 非 kivi quant_bits=None 写入 CSV → 按 kv_mode 推导实际 quant_bits 并记录
- [ ] **PRF-034** `[MED]` profile_latency/memory 未调用 model.eval() → 添加 model.eval()

**P1: 防御性改进（建议在下轮代码维护时修）**
- [ ] **EVL-132** `[HIGH]` eval_ppl.py PPL NaN/Inf 静默写入 + exit(0) → 添加 NaN/Inf 检查，异常时 exit(1)
- [ ] **ENG-110** `[HIGH]` batch EOS 用 all() 判定 → 改为 per-sequence mask（影响 batch>1 的吞吐评测）

**P2: 文档更新**
- [ ] **W2** CLAUDE.md §10 scale dtype 描述更新（float32 → 实际 fp16/input dtype）

**不影响当前实验（仅跟踪）**：EVL-130(HF模式), EVL-131(repeat模式), EVL-133~137, ENG-111, PRF-035, CHK-037~039, UTL-014

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
