---
description: 多Agent协作系统 - 管理Agent和执行Agent的协作工作流
---

# Multi-Agent 协作系统 Skill

> 工业级多Agent协作框架。

---

## 🚀 快速开始

**执行 Agent 入口**：阅读 `docs/AGENT_README.md`

**核心命令**：
```bash
# 查看任务
python3 scripts/agent_tools/agent_cli.py tasks

# 开始任务
python3 scripts/agent_tools/agent_cli.py start <task_id> <agent_id>

# 更新心跳（长任务每10分钟）
python3 scripts/agent_tools/agent_cli.py heartbeat <task_id> <agent_id> "进度"

# 完成任务
python3 scripts/agent_tools/agent_cli.py finish <task_id> <agent_id> "结果"
```

---

## 📁 核心文件

| 文件 | 用途 |
|------|------|
| `docs/AGENT_README.md` | 唯一规范文档 |
| `docs/current_task.md` | 当前任务详情 |
| `docs/autodl_server.md` | 服务器配置 |

---

## ⚠️ 强制规范

1. **必须使用 CLI** - 禁止手动编辑状态文件
2. **长任务用 tmux** - 防止 SSH 断开
3. **长任务更新心跳** - 每 10 分钟
4. **完成后更新文档** - development_record.md + lang.md
