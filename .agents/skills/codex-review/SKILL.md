# Codex 交叉审查 Skill

调用 OpenAI Codex (GPT-5.4) 对代码变更进行交叉审查，补充 Claude D1-D7 审查体系的盲区。

---

## 前置条件

- `codex-cli` 已安装且认证已配置（ChatGPT 认证）
- MCP Server 已注册（`~/.mcp.json` 的 `codex` 条目）
- 项目 `.claude/settings.local.json` 中 `enabledMcpjsonServers` 包含 `"codex"`

---

## 调用模式

### 模式 1：MCP 模式（推荐，适合自定义审查指令）

通过 MCP 工具 `mcp__codex__codex` 调用，支持多轮对话。

**启动会话**：
```
mcp__codex__codex(
  prompt: "<审查指令>",
  sandbox: "read-only",
  cwd: "/Users/chenzilang/Desktop/LLM_KVCache_Quantization"
)
```

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `prompt` | string | ✅ | 审查指令（含文件列表、关注点） |
| `sandbox` | enum | ❌ | **始终使用 `read-only`**，不允许写入 |
| `cwd` | string | ❌ | 项目根目录 |
| `model` | string | ❌ | 默认 `gpt-5.4`（由 ~/.codex/config.toml 配置），无需覆盖 |

**返回值**：`{ threadId: string, content: string }`

**追问（多轮对话）**：
```
mcp__codex__codex-reply(
  prompt: "<追问内容>",
  threadId: "<上一轮返回的 threadId>"
)
```

### 模式 2：CLI 模式（适合标准 diff 审查）

直接调用 `codex review` 命令，非交互式输出审查结果。

**审查 commit range**：
```bash
codex review --base <commit_ref> "<自定义审查指令>"
```

**审查未提交变更**：
```bash
codex review --uncommitted "<自定义审查指令>"
```

---

## 审查指令模板

### 通用审查（Review-Coord 调用）

```
审查以下代码变更，重点关注：
1. 数值精度问题（量化误差传播、dtype 不匹配、NaN/Inf 风险）
2. 边界条件（空输入、极端值、溢出）
3. 静默失败（空 catch、不当 fallback、错误吞噬）
4. 接口契约变化（函数签名、行为语义、向后兼容性）
5. 安全漏洞（注入、路径穿越、硬编码凭证）

请按以下格式输出每个发现：
- 严重性：CRITICAL / HIGH / MEDIUM / LOW
- 文件：<file_path:line_range>
- 问题：<简述>
- 建议：<修复方案>
```

### Bug 分析（Supervisor 调用）

```
分析以下 bug 并建议修复方案：

## Bug 描述
<bug 描述>

## 涉及文件
<文件列表>

## 当前行为
<现象描述>

## 期望行为
<预期描述>

请提供：
1. 根因分析
2. 修复方案（具体代码变更）
3. 验证方法
4. 风险评估
```

---

## 输出格式对齐

Codex 返回的发现需转换为项目审查格式，写入 review_tracker.md 时：

- Issue ID 前缀：使用对应模块的标准前缀（如 `QNT-`, `ENG-`, `EVL-`）
- 来源标注：在 issue 描述末尾追加 `[Codex/GPT-5.4]`
- 严重性分级：对齐现有 CRITICAL / HIGH / MEDIUM / LOW 四级
- 文件定位：`file_path:line_range` 格式

**示例**：
```markdown
- [ ] **QNT-042** `[HIGH]` quantize_symmetric() 未处理全零输入导致 scale=0 division — `src/quant/quantize.py:L45-52` [Codex/GPT-5.4]
```

---

## 回退机制

Codex 调用可能因以下原因失败：
- 认证过期（ChatGPT session 超时）
- 网络超时
- Codex CLI 版本不兼容
- MCP Server 未启动

**处理策略**：
1. 设置超时：CLI 模式建议 60s，MCP 模式建议 120s
2. 失败时**跳过 Codex 审查**，仅使用 D1-D7 结果
3. 记录警告到审查报告：`⚠️ Codex 交叉审查跳过：<失败原因>`
4. 不阻塞主审查流程

---

## 安全约束

- **始终使用 `sandbox: "read-only"`** — Codex 不得修改项目文件
- Codex 建议仅作为参考，最终决策权在 Claude Agent（Supervisor/Developer）
- 不向 Codex 发送包含密钥、凭证、服务器地址的内容
- review_tracker.md 中 Codex 发现标注 `[Codex/GPT-5.4]`，可追溯来源
