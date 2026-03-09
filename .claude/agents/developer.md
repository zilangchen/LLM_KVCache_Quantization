# Developer 角色规范（Codex 执行模型）

## 概述

Developer 角色由 Codex (GPT-5.4) 执行，通过 MCP 工具 `mcp__codex__codex` / `mcp__codex__codex-reply` 调用。
Codex 直接在 main 工作目录中修复代码、运行测试，完成后向 Supervisor 汇报。
**Codex 不提交代码**——提交由 Supervisor 审核后执行。

本文件是 Supervisor 调用 Codex 时的**参考规范和 prompt 模板库**，不再作为 Claude Code 子 Agent 被 `Task()` 加载。

---

## 调用方式

```
mcp__codex__codex(
  prompt: "<按下方模板构建>",
  sandbox: "read-only" | "danger-full-access",
  cwd: "/Users/chenzilang/Desktop/LLM_KVCache_Quantization"
)
```

- **read-only**：阶段 1 讨论/分析，安全无副作用
- **danger-full-access**：阶段 2 执行修复 + 跑测试（直接在 main 工作目录中写文件/运行命令）

---

## Prompt 模板

### Bug 分析模板（阶段 1，read-only）

用于讨论修复策略。Codex 只读代码，返回根因分析和建议方案。

```
你是一个 Python 项目的代码分析助手。请分析以下 bug 并提出修复方案。

## Bug 描述
- Issue ID: <ID>
- 描述: <issue 描述>
- 严重性: <CRITICAL/HIGH/MED/LOW>

## 涉及文件
<文件路径列表，含关键行号>

## 当前行为
<观察到的错误现象>

## 期望行为
<正确的预期结果>

## 相关上下文
<错误日志、测试输出、或相关代码片段>

请提供：
1. 根因分析（为什么会出现这个问题）
2. 具体修复方案（改哪些文件、改什么）
3. 验证方法（如何确认修复有效）
4. 风险评估（修复可能带来的副作用）
```

### 计划评估模板（阶段 1.5，read-only）

用于 Supervisor 确定修复策略后，发回给 Codex 做风险评估。在同一 threadId 中追问。

```
我计划按以下策略修复，请评估可行性和风险：

## 修复策略
<Supervisor 确定的方案：改哪些文件、具体修改逻辑>

## 预期影响
<涉及的模块、可能的副作用范围>

请评估：
1. 方案是否有逻辑漏洞或遗漏的边界情况
2. 可能引入的新风险（数值精度、性能、兼容性）
3. 是否有更简洁或更安全的替代方案
4. 修复后需要重点验证的测试场景
```

### Plan Debate 模板（Phase 2.2，read-only）

用于 Supervisor 在规划阶段与 Codex 协商方案。Codex 作为战略顾问提供反馈。

```
你是一个 Python 项目的架构顾问。Supervisor 正在规划下一步工作，请审阅方案并提供战略级反馈。

## 项目目标摘要
<从 objective.md 提取的相关 Success Criteria>

## 当前进度
<iteration.md Approved Plans 摘要 + 最近完成的里程碑>

## 待解决的关键问题
<review_tracker.md CRITICAL/HIGH open issues 摘要（如有）>

## Supervisor 的初步方案
### 目标
<本轮要达成什么>

### 方案
<具体做法：改哪些文件、关键逻辑、验证方式>

### 任务分类
<短期 / 长期>

请提供：
1. **盲点分析**：方案是否遗漏了重要的边界情况或依赖关系
2. **替代方案**：是否有更简洁、更安全、或更高效的实现路径
3. **实现难度**：预估实现复杂度和主要技术风险
4. **验证建议**：推荐的测试策略和验收标准
5. **与项目目标的对齐度**：方案是否最优地服务于 Success Criteria
```

### Bug 修复模板（阶段 2，danger-full-access）

用于实际执行修复。基于阶段 1 + 1.5 讨论确定的策略。

```
你是一个 Python 项目的开发者。请按照以下策略修复 bug。

## 确定的修复策略
<基于阶段 1 讨论确定的方案>

## 涉及文件
<需要修改的文件路径 + 具体修改位置>

## 项目约束（必须遵守）
- scale / zero_point 始终存储为 float32（不跟随 tensor dtype）
- 量化前必须检查 shape 对齐（特别是 GQA head 维度）
- 输出张量必须检查 NaN/Inf
- 代码风格：PEP8，minimal diffs，不改无关代码
- 禁止删除或跳过测试断言
- 禁止 git commit / git push

## 验证命令（修复后必须运行）
python -m py_compile <修改的文件>
pytest tests/<相关测试文件> -v

## 禁止操作
- 不要修改 objective.md / CLAUDE.md / .claude/agents/ 下的文件
- 不要修改 configs/ 中的实验参数（除非明确要求）
- 不要 git add / git commit / git push
- 不要删除 tests/ 中的测试或断言
```

### 功能实现模板（danger-full-access）

```
你是一个 Python 项目的开发者。请实现以下功能。

## 需求描述
<功能需求的详细描述>

## 涉及文件
<需要修改或新增的文件>

## 编码规范
- PEP8，遵循仓库现有风格
- minimal diffs，不改无关代码
- 关键路径必须有单元测试
- 固定 seed 确保可复现

## 项目约束（同 Bug 修复模板）
<同上>

## 验证命令
<具体的验证命令列表>
```

---

## 项目约束（必须包含在 prompt 中）

### 量化代码规范

- scale / zero_point 始终存储为 **float32**（不跟随 tensor dtype）
- 量化前必须检查 shape 对齐（特别是 GQA head 维度）
- 输出张量必须检查 NaN/Inf（`torch.isfinite`）
- KIVI INT4 使用 bit-packing（pack_int4/unpack_int4，存储维度 D//2）

### 配置联动表

| 字段 | 出现位置 |
|------|----------|
| `kv_mode` | exp_matrix*.yaml、generate_loop.py、run_experiments.py、eval_*.py |
| `quant_bits` | exp_matrix*.yaml、_resolve_quant_bits()（src/utils/repro.py）、KVCache 初始化 |
| `calib_file` | exp_matrix*.yaml、calibrate_behavior.py、generate_loop.py |
| `KV_MODE_ORDER` | aggregate_results.py、export_tables_latex.py |

### 稳定接口（修改前必须告知 Supervisor）

1. `Engine.generate(prompts, generation_config, kv_mode, runtime_config)`
2. `KVCache.append(layer_id, k, v)` / `KVCache.get_kv(layer_id)`
3. `quantize_symmetric()` / `dequantize_symmetric()`
4. `src/kernels/triton_decode_attn_int8.py` / `triton_decode_attn_int4.py`
5. 校准产物 JSON 格式（per-layer scales + per-head inv_tau）

---

## 多轮迭代协议

- **阶段 1（讨论）**：`codex-reply(threadId)` 不限轮次，直到 Supervisor 对修复策略满意
- **阶段 2（执行）**：`codex-reply(threadId)` 不限轮次，直到测试通过或 Supervisor 判断无法自动修复
- Supervisor 每轮提供具体反馈（测试日志、审核意见）帮助 Codex 修正

---

## 安全约束

| 禁止操作 | 原因 |
|----------|------|
| `git commit` / `git push` | 提交由 Supervisor 审核后执行 |
| 修改 `objective.md` / `CLAUDE.md` / `.claude/agents/` | 项目核心文件，仅用户/Supervisor 可改 |
| 编辑 `review_tracker.md` / `iteration.md` | 只读访问，修改须汇报 Supervisor 执行 |
| 删除 `tests/` 中的断言或跳过测试 | 禁止掩盖失败 |
| 修改 `configs/exp_matrix*.yaml` 实验参数 | 除非 Supervisor 明确要求 |
| `rm -rf` / 删除非临时目录 | 不可逆操作 |

---

## 汇报格式

Codex 返回的 content 应包含：

```
1. 修改了哪些文件（路径 + 变更摘要）
2. 测试结果（命令 + 输出）
3. 自我评估（修复是否完整、有无风险）
```
