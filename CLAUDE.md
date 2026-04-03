# CLAUDE.md — 项目级 Claude Code 指令

默认使用中文输出，用清晰的 Markdown 结构化表达。

---

## 0. 项目概览

面向高效推理的大语言模型键值缓存行为对齐量化框架（KV Cache Quantization）。
目标会议：EMNLP 2026（ARR 投稿）。

技术栈：Python 3.12、PyTorch 2.8.0（CUDA 12.8）、Transformers、Triton、numpy/pandas/matplotlib。
核心模块：`src/cache/`、`src/quant/`、`src/kernels/`、`src/engine/`、`scripts/`。

---

## 1. 权威文件（唯一入口，必须遵守）

| 文件 | 用途 | 规则 |
|------|------|------|
| `objective.md` | 目标/边界/约束/成功标准/决策日志 | 任何任务开始前必须对齐；偏离边界须先确认 |
| `iteration.md` | 进度与迭代记录 | **append-only**，不覆盖历史，只追加 |
| `review_tracker.md` | 代码审查问题追踪 | 根目录权威文件，所有审查 issue 的唯一入口 |
| `experiment_sop.md` | 实验 SOP | 实验目录、命名、复现、数据版本、指标、产物归档 |
| `AGENTS.md` | 开发工作流协议 | 命令入口、目录规范、提交规范 |

当用户说"这个问题先存档"时，将问题记录到 `review_tracker.md`（审查问题）或 `iteration.md`（一般待办）。

**只读文件（不可修改）**：`CLAUDE.md`、`experiment_sop.md`、`.claude/agents/*.md`。
已通过 PreToolUse hook 强制拦截。

**有限写入文件**：
- `objective.md` — 仅追加 Decision Log（修改目标/边界须先确认）
- `iteration.md` — 仅追加 Timeline + 维护 Approved Plans
- `review_tracker.md` — 仅标记修复 `[x]` + 新增 issue

### 1.1 持久化 Memory 维护

Memory 文件位于**项目级**目录: `~/.claude/projects/-Users-chenzilang-Desktop-LLM-KVCache-Quantization/memory/`
（注意：从 home 目录启动的会话加载的是 home 层 memory，不是项目层。必须从项目目录启动才能加载正确的 memory。）

`MEMORY.md` 前 200 行自动注入每次会话上下文。

#### 更新触发时机（必须执行）

| 触发事件 | 更新内容 |
|----------|----------|
| 修复重大 bug（如 CAL-019/020 级别）| debugging-patterns.md 追加根因+修复方案 |
| Phase 推进或实验完成 | experiment-state.md 更新状态 |
| review_tracker summary 变化 | MEMORY.md 更新计数行 |
| 发现新的"反复踩坑"模式 | MEMORY.md 已知陷阱 + 对应专题文件 |
| Agent 协作出现新的失败/成功模式 | agent-coordination.md 更新 |
| 会话结束前（如有重要发现）| 相关专题文件追加 |
| **新增 kv_mode 或 cache 实现文件** | **MEMORY.md kv_modes 列表 + 文件导航** |
| **论文章节完成重大改写/重构** | **MEMORY.md 当前阶段 + experiment-state.md** |
| **源文件重命名/删除** | **MEMORY.md 文件导航** |
| **新增实验结果目录** | **experiment-state.md 结果目录表** |

> **自动检查**：项目级 SessionStart hook (`scripts/check_memory_freshness.sh`) 会在每次会话启动时
> 检测 MEMORY.md 是否引用了不存在的文件、是否遗漏了代码中路由的 kv_mode、以及修改时间是否超过 7 天。
> 检查失败时输出警告注入会话上下文。

#### 约束

- MEMORY.md 严格控制在 **165 行以内**（200 行截断，留 buffer）
- 专题文件各自不超过 150 行，超出时精简旧内容
- 不记录临时状态（当前正在做什么）—— 那是 iteration.md 的职责
- 不复制 CLAUDE.md 已有规范 —— 只记录"经验"和"状态"
- 更新前先 Read 现有内容，避免重复

---

## 2. 目录规范

```
src/          — 核心源码（cache / quant / kernels / engine / utils）
scripts/      — 可执行脚本（实验运行、评测、聚合、导出）
tests/        — pytest 测试
configs/      — 实验配置（exp_matrix.yaml + snapshots/）
docs/         — 文档
experiments/  — 实验记录（YYYY-MM-DD_<topic>/）
artifacts/    — 校准产物与中间文件
results/      — 实验输出（runs/tables/plots/logs）— 不提交
.agents/      — Agent 工作区（execplans/skills/）
```

---

## 3. 常用命令

```bash
# 测试（远程）
pytest tests/ -v

# 本地验证替代（macOS 无 GPU，pytest 因 numpy/libcblas 不可用）
python3 -m py_compile <file>
python3 -m compileall -f src/ scripts/ tests/

# Smoke test（需 GPU）
python scripts/smoke_test.py --save_output

# 实验 dry-run
python scripts/run_experiments.py --config configs/exp_matrix.yaml --dry_run

# RoleAlign 实验 dry-run
python scripts/run_experiments.py --config configs/exp_matrix_rolealign.yaml --dry_run

# Triton kernel 单测
python -m unittest tests/test_triton_kernel.py

# 聚合结果
python scripts/aggregate_results.py --runs_dir results/<tag>/runs --tables_dir results/<tag>/tables --plots_dir results/<tag>/plots

# LaTeX 导出
python scripts/export_tables_latex.py --tables_dir results/<tag>/tables --out_dir results/<tag>/latex_tables

# 论文编译
cd thesis && bibtex main && xelatex -interaction=nonstopmode main.tex
```

---

## 4. 任务门禁：先对齐再动手

### 4.1 何时需要 Plan

涉及以下任一情况时，**必须先进入 Plan Mode**（使用 `EnterPlanMode`），输出详细计划并等待用户确认后再实现：

- 新增/修改代码（跨 2+ 文件）
- 运行命令、改依赖/配置
- 改实验流程或仓库结构
- 任何可能偏离 `objective.md` 边界的工作

### 4.2 Plan 必须包含

1. **问题陈述**（现状 → 期望 → 为什么现在做）
2. **objective.md 对齐映射**：服务哪些目标，触碰哪些边界
3. **目标与非目标**（明确不做什么）
4. **约束与假设**
5. **具体工作清单**（按文件/模块/接口列出）
6. **验收标准**（checklist，每条写验证方式）
7. **验证计划**（命令 + 预期输出/阈值）
8. **风险与边界情况**（>= 5 条，含概率/缓解/回滚）
9. **需确认问题**（给选项 + 默认推荐 + 理由）
10. **里程碑拆分**（对应小步提交）

### 4.3 只读分析豁免

纯只读操作（读代码、搜索、分析日志、回答问题）不需要 Plan，可直接执行。

### 4.4 Agent Teams 模式豁免

当以 **主管 Agent** 角色运行（Agent Teams 模式）时，**ExecPlan 门禁完全豁免**。Supervisor 及其调用的 Codex Developer / Sub-Agent 可自主决策并执行，无需输出 ExecPlan、无需等待用户 `APPROVE PLAN`、无需使用 `EnterPlanMode`。仅在触发 `supervisor.md` 中定义的强制上报场景（修改 objective 目标/边界、破坏性操作、研究方向转变、远程实验全部失败）时才暂停询问用户。

### 4.5 Phase 闸门：启动下一 Phase 前必须清空待办

在启动任何新 Phase 之前，**必须先通过 `python scripts/review_tool.py phase-gate` 检查门禁**。
CRITICAL open issues 必须修复才能推进。若某条目因外部依赖无法完成，须在 review_tracker.md 中标注原因并降级，不得无声跳过。

---

## 5. 编码与实现标准

- **正确性第一**：确定性、可复现、输入校验、错误处理、清晰边界
- **小步可审查**：避免巨大 diff；先最小可行实现，再迭代增强
- **测试要求**：
  - 新增功能：关键路径必须有单元测试
  - 修复 bug：必须先构造可复现用例，再修复
- **代码风格**：PEP8，遵循仓库现有风格，prefer minimal diffs
- **复现性**：固定 seed、记录依赖版本、记录运行命令
- **文档更新**：公共接口/行为变化须更新 docs/ 或 objective.md

### 5.1 代码提交双重审查门禁（强制）

Claude（包括主 session 和 Supervisor）写完代码后，**必须通过双重审查才能提交**。两道审查全部 PASS 才能进入 commit 流程，任一 FAIL 必须修正后重审。

#### 审查流程

```
Claude 写完代码
     │
     ├──→ 审查 1: Codex 审查 (/codex:review)
     │         外部模型独立审查，检查逻辑错误、边界遗漏、假修复
     │
     ├──→ 审查 2: Claude Sub-Agent 自审 (Agent, subagent_type="review-numerical" 或相关维度)
     │         Claude 自己的 sub-agent 从新视角审查，检查数值正确性、接口契约、静默失败
     │
     ▼
  两道全部 PASS？
     ├── 是 → git add + commit
     └── 否 → 修正问题 → 重新提交审查
```

#### 触发条件

以下情况**必须**触发双重审查：
- 修改 `src/` 下的任何 `.py` 文件
- 修改 `scripts/` 下的评测/校准/实验脚本
- 修复 bug（无论大小）

以下情况**豁免**：
- 纯文档修改（`docs/`、`thesis/`、`*.md`）
- 纯配置修改（`configs/*.yaml`、`.gitignore`）
- 仅格式化/注释变更（无逻辑改动）

#### Codex 审查（审查 1）

调用 `/codex:review`，prompt 包含：
- `git diff` 完整输出
- 修改目的（一句话）
- 验证命令及其输出

Codex 返回 PASS 或 CONCERN/REJECT + 具体问题。

#### Claude Sub-Agent 自审（审查 2）

根据修改的文件类型选择 2-4 个相关审查维度 spawn sub-agent（与 review-coord 维度选择表对齐）：

| 修改类型 | 必选维度 | 可选维度 |
|---------|---------|---------|
| `src/quant/` `src/cache/` `src/kernels/` | `review-numerical`(D1) + `review-boundary`(D5) | `review-silent`(D2)、`review-contract`(D4) |
| `src/engine/` | `review-contract`(D4) + `review-silent`(D2) + `review-boundary`(D5) | `review-numerical`(D1) |
| `scripts/eval_*` `scripts/calibrate_*` | `review-numerical`(D1) + `review-silent`(D2) | `review-test`(D6) |
| 跨多模块 / 大范围变更 | 全部 7 个维度 | — |

Sub-agent prompt 必须包含 `git diff` + 修改目的 + "请从你的维度审查这个修改是否引入了新问题"。

#### 回退

- Codex 不可用 → 仅用 Claude Sub-Agent 审查（单重），commit message 标注 `[codex-unavailable]`
- Sub-Agent spawn 失败 → 仅用 Codex 审查（单重），commit message 标注 `[self-review-skipped]`
- 两者都不可用 → commit message 标注 `[unreviewed]`，在 review_tracker.md 追加一条 `[MED]` 待人工复核

### 5.2 Fail-Fast 实验原则（强制）

实验脚本和评测代码**严禁静默 fallback**。检测到异常必须立即报错停止，不允许用默认值或降级路径悄悄继续。

- **禁止静默 fallback**：校准文件缺失/格式错误、模型加载异常、RoPE 不可用等关键前置条件必须 raise/exit，不允许用 fallback 值悄悄继续。历史教训：EVL-037 校准加载失败静默退化为 baseline 导致 PPL 虚假偏低；v3_quick 缺 RoPE 但无 warning 导致全部数据作废
- **实验粒度拆小**：不把 profiling + RULER + PPL 全放在一个巨型脚本里串行跑。拆成独立步骤，每步校验上一步的输出，任何一步失败不影响其他步骤的已有结果
- **前置 smoke test**：大规模重跑（>2h GPU）前必须先跑单模型单 seed 短序列验证，确认修复生效
- **显式参数**：所有实验命令必须显式传 `--calib_file`、`--model_id`、`--kv_mode` 等关键参数，不依赖任何隐式默认值
- **失败样本不隐藏**：评测中样本失败时以 0 分计入（保持分母不变），并在 details CSV 中记录失败信息，不允许静默跳过导致分母缩小、分数虚高

### 5.3 GPU 利用与远程执行规范（强制）

**GPU 最大化利用**：3 张 GPU 不允许任何一张空闲。
- **跨阶段流水线化**：不要等一个阶段全部完成才启动下一阶段。只要某个模型的前置条件满足，立即启动该模型的后续实验
- **自动接续**：每张 GPU 上的任务链设计为自动衔接（tmux session 中串行 `cmd1 && cmd2`，或用监控脚本等前序 session 结束后自动启动下一个）
- **TPOT profiling 独占**：3 卡全部无进程时才可跑 profiling

**远程执行**：
- **禁止 SSH heredoc 临时脚本**：所有远程执行的脚本必须作为仓库内的正式文件（`scripts/*.sh`），通过 rsync 同步到远程后执行。历史教训：heredoc 中 f-string/引号被破坏导致 smoke test 中途失败
- **简单单行命令**（如 `nvidia-smi`、`ls`、`tail`）可直接 SSH 执行

**不要空闲等待**：
- 启动远程后台任务后必须设自动轮询监控
- **轮询间歇期必须做其他工作**：推进写作任务、读论文、审查计划、更新 iteration.md——永远不能出现"什么都不做只等轮询回来"的状态

---

## 6. 失败处理：Debug+Iterate Loop

当出现命令失败、测试失败、指标不达标、输出不稳定时，**必须循环迭代直到达标**：

1. 精确捕获失败（命令、exit code、关键日志）
2. 最小复现（缩小到最小 failing case）
3. 根因分析（假设 → 证据 → 排除）
4. 最小修复补丁（优先修根因）
5. 重新验证
6. 仍失败则继续迭代；**不得放弃/跳过/假装通过**

仅在缺少关键输入/权限/外部依赖时才允许停下提问，且必须给选项与默认推荐。

---

## 7. Git + iteration.md + 仓库卫生

每完成一个里程碑（functional unit），按顺序执行：

### 7.1 iteration.md 区块结构

`iteration.md` 中维护两个独立区块（从上到下）：

1. **Approved Plans** — 经讨论并被用户认可的阶段性执行计划（含前置条件、状态、checklist）
2. **Timeline** — 实际执行记录（append-only）

规则：
- 所有代码审查问题追踪在 `review_tracker.md`（不在 iteration.md）
- 当一个 Plan 被用户讨论并认可后，必须追加到 `## Approved Plans` 区块
- 每条 Plan 记录：批准日期、Plan 名称、前置条件、状态（待执行/执行中）、具体 checklist
- **Plan 完成后从 Approved Plans 区块删除**，在 Timeline 中记录完成摘要即可

### 7.2 iteration.md 追加记录

**时间戳必须使用系统真实时间**：写入 iteration.md 前，必须先执行 `date '+%Y-%m-%d %H:%M'` 获取真实时间，禁止自行编造或估算时间。

```markdown
### <执行 date 命令获取的真实时间> | 标题
- Goal:
- Changed files:
- Commands:
- Outputs:
- Validation:
- Risks / follow-ups:
```

### 7.3 运行验证命令

至少跑 `pytest tests/ -v`（如涉及相关模块）。

### 7.4 提交规范

- **禁止** `git add .` —— 必须按语义分组 add
- commit message 前缀：`feat:` / `fix:` / `refactor:` / `test:` / `docs:` / `chore:`
- commit 后把 hash 写入 iteration.md 对应条目
- **不主动 push**，除非用户明确要求

### 7.5 仓库卫生

- `git status` 必须干净
- 临时输出归档到 `artifacts/YYYY-MM-DD/<topic>/`
- 实验产物归档到 `experiments/YYYY-MM-DD_<topic>/`（遵守 experiment_sop.md）
- 需长期忽略的文件更新 `.gitignore`
- **不执行破坏性命令**（`rm -rf` / `git reset --hard` / `sudo`）除非用户明确批准

### 7.6 分支隔离规范

- **main 分支保护**：main 始终保持"pytest 通过"状态，是 rsync 推送的唯一来源
- **Developer 隔离**：Developer 角色由 Codex 通过 Codex Plugin 命令调用（`/codex:review`、`/codex:rescue` 等，插件不可用时回退 MCP），直接在 main 工作目录中操作（非 sandbox 隔离），不创建分支。Codex 修改后由 Supervisor 审核 `git diff` + `pytest` 验证，通过后在 main 上提交
- **小修复豁免**：≤1 文件、≤20 行的配置/文档修改可由 Supervisor 直接在 main 操作
- **rsync 安全**：推送代码到远程前必须执行 `scripts/rsync_gate.sh` 门禁检查

### 7.7 Agent 分级读取策略

不同 Agent 按角色读取 iteration.md 的不同范围，减少 token 消耗：

| Agent | 读取范围 | 估算 tokens |
|-------|----------|-------------|
| Supervisor 首轮 | Approved Plans 全量 + Timeline 最近 5 条 | ~1,200 |
| Supervisor 后续 | Approved Plans + `git log -3` | ~600 |
| Codex Developer | 不读 iteration.md（Supervisor prompt 自包含上下文） | 0 |
| Review-Coord | Timeline 最近 1 条（确认 baseline） | ~80 |
| D1-D7 审查 Agent | 不读 iteration.md | 0 |

Timeline 归档工具：`python scripts/iteration_tool.py trim-timeline --keep 15`

---

## 8. 实验规范（与 experiment_sop.md 对齐）

- 实验目录：`experiments/YYYY-MM-DD_<topic>/`
- 必须包含 README（目的/假设/变量/seed/指标/结果/结论/复现步骤）
- 固定 seed（主实验：1234-1238；吞吐：1234-1241）
- 统一 greedy 解码：`temperature=0.0, top_p=1.0, top_k=0`
- 结果路径：`results/`（runs/tables/plots/logs）
- 校准产物：`artifacts/`（如 `kv_calib_kl_selected_v3_quick.json`）
- 实验结论改变方向时必须更新 objective.md Decision Log

---

## 9. 固定决策（不可修改）

| 项目 | 值 |
|------|-----|
| 主模型 | `Qwen/Qwen2.5-1.5B-Instruct`（revision pinned） |
| 扩展模型 | `Qwen/Qwen2.5-7B-Instruct`、`LLaMA-3.1-8B-Instruct` |
| Python | 3.12 |
| 解码 | greedy（temp=0, top_p=1, top_k=0） |
| 研究路径 | Transformers + 自定义 generation loop + 自定义 KV cache |
| 量化方法 | fp16, int8_baseline, int8_ours, int4_baseline, int4_fused, int4_ours, int4_ours_mixed, **int4_ours_asym**, int4_ours_asym_ba, int4_kivi_aligned, int4_mixed_kv, kivi_style |
| 统计框架 | Bootstrap CI + sign-flip permutation + BH-FDR（α=0.05） |

---

## 10. 稳定接口（不可随意破坏）

- **Engine**: `Engine.generate(prompts, generation_config, kv_mode, runtime_config)`
- **KV Cache（对称）**: `INT8KVCache.append(layer_id, k, v)` / `INT8KVCache.get_kv(layer_id)` — INT4KVCache 同接口
- **KV Cache（非对称）**: `KIVIStyleKVCache.append(layer_id, k, v)` / `KIVIStyleKVCache.get_kv(layer_id)` — RoleAwareAsymKVCache 继承同接口
- **MixedKVCache**: `MixedKVCache.append(layer_id, k, v)` / `MixedKVCache.get_kv(layer_id)` — K@INT8 + V@INT4
- **Quantizer（对称）**: `quantize_symmetric_int8()` / `dequantize_symmetric_int8()` — int4 同命名模式
- **Quantizer（非对称）**: `quantize_asymmetric_per_channel()` / `quantize_asymmetric_per_token()` — KIVI/RoleAlign 使用
- **Kernels**: `src/kernels/triton_decode_attn_int8.py` / `triton_decode_attn_int4.py`
- **校准产物**: JSON 格式（per-layer scales + per-head inv_tau）；RoleAlign 的 BA percentile 内嵌于 `configs/exp_matrix_rolealign.yaml`

---

## 11. 输出格式（强制）

每次实施输出必须包含：
1. **变更摘要**（本次做了什么）
2. **如何验证**（具体命令）
3. **实际结果**（通过/失败 + 关键日志）
4. **iteration.md/commit/仓库卫生状态**
5. **下一步计划**

---

## 12. Agent 角色体系（Agent Teams 模式）

本项目支持三种 Agent 角色协作开发，详细定义见 `.claude/agents/*.md`。

- **主管 Agent**（supervisor.md）：最高权限，单任务模式（接收用户交付的具体任务，完成即退出）。支持 Execute/Wait 两模式（本地执行 + 远程 GPU 等待）。通过 Codex Plugin 协作（Plan Debate + Developer + Fix Review），Phase 4.5 强制 Codex 交叉验证防假修复。批量 bug 修复时进入闭环流水线（修复→审查→PASS 继续/REJECT 重修）
- **开发 Agent / Codex Developer**（developer.md）：由 Codex (GPT-5.4) 执行，Supervisor 通过 Codex Plugin 命令调用（`/codex:review` 分析、`/codex:rescue` 执行）。两阶段流程：read-only 分析 → 直接在 main 修复+测试。Codex 不提交代码，由 Supervisor 审核后落地
- **审查协调 Agent**（review-coord.md）：事件驱动的审查协调员，检测新 commit → 并行 spawn D1-D7 审查，无变更时逐模块全量深度审查。由用户按需启动，Supervisor 不主动触发
- **审查 Agent 集群**（7 个专项 Agent，各司其职）：
  - `review-numerical`：D1 数值正确性（量化误差、loss 语义、NaN 防护）
  - `review-silent`：D2 静默失败猎手（空 catch、不当 fallback、错误吞噬）
  - `review-security`：D3 安全漏洞扫描（注入、穿越、反序列化）
  - `review-contract`：D4 接口契约（稳定 API 守护、签名/语义变化）
  - `review-boundary`：D5 边界鲁棒性（空输入、极端值、溢出）
  - `review-test`：D6 测试覆盖（缺口评分、回归测试、质量）
  - `review-quality`：D7 代码质量（死代码、重复、命名、注释）
  - 全部只读 + 仅写 `review_tracker.md`，由 `review-coord`（审查协调 Agent）统一调度，Supervisor 通过 review-coord 间接管理

**启动规则**：所有 Claude Code Agent 角色（Supervisor、Review-Coord、D1-D7）启动时必须先读取 `review_tracker.md` 和 `iteration.md`，这是保持上下文同步的唯一机制。Codex Developer 不"启动"——它通过 Codex Plugin 命令按需调用（插件不可用时回退 MCP），由 Supervisor prompt 提供上下文。

---

## 13. 远程服务器

所有 GPU 实验在 AutoDL 远程服务器上运行。连接方式、tmux 会话管理、代码同步（rsync）、日志获取等操作规范见 `.agents/skills/remote-server/SKILL.md`，每次需要远程操作时必须参考该文件。

---

## 14. 安全红线

- 不提交密钥、凭证、服务器地址到 git
- 不在代码中硬编码 API key / password
- 不执行 `rm -rf`、`git push --force`、`git reset --hard` 除非用户明确批准
- 不修改 `.gitignore` 中已忽略的敏感文件
- 网络请求仅限 HuggingFace Hub（模型/数据集下载）
