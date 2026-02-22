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
| `iteration.md` | 进度与迭代记录 | **append-only**，不覆盖历史，只追加；顶部维护待办清单 |
| `experiment_sop.md` | 实验 SOP | 实验目录、命名、复现、数据版本、指标、产物归档 |
| `AGENTS.md` | 开发工作流协议 | 命令入口、目录规范、提交规范 |

当用户说"这个问题先存档"时，将问题记录到 `iteration.md` 顶部的待办清单。

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
# 测试
pytest tests/ -v

# Smoke test（需 GPU）
python scripts/smoke_test.py --save_output

# 实验 dry-run
python scripts/run_experiments.py --config configs/exp_matrix.yaml --dry_run

# Triton kernel 单测
python -m unittest tests/test_triton_kernel.py

# 聚合结果
python scripts/aggregate_results.py --runs_dir results/<tag>/runs --tables_dir results/<tag>/tables --plots_dir results/<tag>/plots

# LaTeX 导出
python scripts/export_tables_latex.py --tables_dir results/<tag>/tables --out_dir results/<tag>/latex_tables
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

当以 **主管 Agent** 角色运行（Agent Teams 模式 / `/auto-iterate`）时，**ExecPlan 门禁完全豁免**。主管 Agent 及其调度的开发 Agent 可自主决策并执行，无需输出 ExecPlan、无需等待用户 `APPROVE PLAN`、无需使用 `EnterPlanMode`。仅在触发 `auto-iterate` SKILL.md 中定义的强制 Escalation 场景（修改 objective 目标/边界、破坏性操作、研究方向转变）时才暂停询问用户。

### 4.5 Phase 闸门：启动下一 Phase 前必须清空待办

在启动任何新 Phase（如 Phase 5）之前，**必须先解决 `iteration.md` 顶部待办清单中属于当前 Phase 的所有条目**。
若某条目因外部依赖无法完成，须在 iteration.md 中标注原因并降级为下一 Phase 的待办，不得无声跳过。

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

### 7.1 Approved Plans 区块

`iteration.md` 中维护三个独立区块（从上到下）：

1. **TODO Backlog** — 缺陷、待修复项、代码审查发现（仅问题，不含执行方案）
2. **Approved Plans** — 经讨论并被用户认可的阶段性执行计划（含前置条件、状态、checklist）
3. **Timeline** — 实际执行记录（append-only）

规则：
- 当一个 Plan 被用户讨论并认可后，必须追加到 `## Approved Plans` 区块（不要放在 TODO Backlog 里）
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
| 量化方法 | fp16, int8_baseline, int8_ours, int4_baseline, int4_ours, kivi_style |
| 统计框架 | Bootstrap CI + sign-flip permutation + BH-FDR（α=0.05） |

---

## 10. 稳定接口（不可随意破坏）

- **Engine**: `Engine.generate(prompts, generation_config, kv_mode, runtime_config)`
- **KV Cache**: `KVCache.append(layer_id, k, v)` / `KVCache.get_kv(layer_id)`
- **Quantizer**: `quantize_symmetric()` / `dequantize_symmetric()`
- **Kernels**: `src/kernels/triton_decode_attn_int8.py` / `triton_decode_attn_int4.py`
- **校准产物**: JSON 格式，含 per-layer scales + per-head inv_tau

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

本项目支持三种 Agent 角色协作开发。通过 Agent Teams 启动时自动生效。

### 主管 Agent（Supervisor）
- 最高权限，负责从 `objective.md` 拆解目标为任务，通过 Agent Teams 调度开发 Agent 和审查 Agent
- 运行 `/auto-iterate` 模式驱动全局迭代循环
- 仅在以下情况退出：目标全部达成 / 迭代上限 / 必须用户决策的硬阻塞 / 连续 2 轮无进展
- 可授予其他 agent 高级权限（`mode: "bypassPermissions"`）

### 开发 Agent（Developer）
- 高级权限（由主管授予），执行编码、测试、修复、远程 GPU 任务
- 运行 `$auto-iterate` 核心循环，自主调用 `$debug-iterate` / `$unit-commit` / `$repo-hygiene`
- 不需要向用户确认，连续修不好的 bug 上报主管而非用户
- 远程操作参考 `.agents/skills/remote-server/SKILL.md`

### 代码审查 Agent（Reviewer）
- 只读权限为主，可写入 `iteration.md` TODO Backlog
- 通过 `git diff` / `git log` 监控变更，对每次提交进行增量审查
- **空闲时主动对整个代码库进行深度全量审查**（按模块轮转：src/ → scripts/ → tests/ → configs/）
- 发现问题按严重性（CRITICAL/HIGH/MEDIUM/LOW）记录到 TODO Backlog，通知主管
- 审查重点：数值正确性、接口兼容性、边界情况、测试覆盖、配置一致性
- **常驻运行**，仅在用户手动终止 / 主管发送 shutdown / 所有开发任务完成时退出

### 强制规则：每次启动必须读取 iteration.md

**所有角色（主管/开发/审查）在每次启动、每轮迭代开始时，必须先读取 `iteration.md`**，获取：
- TODO Backlog（当前待修复问题）
- Approved Plans（当前待执行计划）
- Timeline 最近条目（上次做到哪里）

这是保持上下文同步的唯一机制，不得跳过。

### 协作流程
```
主管 → 读 iteration.md + objective.md → 拆解任务
  ├── spawn 开发 Agent → 读 iteration.md → 领取任务 → 编码/测试/提交
  ├── spawn 审查 Agent → 读 iteration.md → 监控变更 → 审查 → 写 TODO
  ├── 审查发现问题 → 主管分配修复任务 → 开发 Agent 修复
  └── 循环直到目标达成
```

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
