# Agent 协作系统

> **执行 Agent 必读**：这是多 Agent 协作的唯一规范文档。

---

## 🚀 快速开始（3 步）

```bash
# 1. 开始任务（自动验证 + 锁定）
python3 scripts/agent_tools/agent_cli.py start <task_id> <your_agent_id>

# 2. 执行任务（见下方详细说明）

# 3. 完成任务（自动释放 + 提示更新文档）
python3 scripts/agent_tools/agent_cli.py finish <task_id> <your_agent_id> "结果说明"
```

---

## 📋 CLI 命令速查

| 命令 | 用途 | 示例 |
|------|------|------|
| `tasks` | 查看任务队列 | `agent_cli.py tasks` |
| `start` | 开始任务 | `agent_cli.py start milestone-c exec-001` |
| `bootstrap` | 启动清单 + SSH 健康检查 | `agent_cli.py bootstrap` |
| `ssh-check` | 仅做 SSH 健康检查 | `agent_cli.py ssh-check` |
| `heartbeat` | 更新心跳 | `agent_cli.py heartbeat milestone-c exec-001 "进度50%"` |
| `finish` | 完成任务 | `agent_cli.py finish milestone-c exec-001 "已完成"` |
| `status` | 查看锁状态 | `agent_cli.py status` |

---

## ⚠️ 强制规范

1. **必须使用 CLI** - 禁止手动编辑状态文件
2. **长任务（>5分钟）使用 tmux** - 防止 SSH 断开
3. **长任务每 10 分钟更新心跳** - 防止被判定为超时
4. **完成后必须更新文档** - `development_record.md` 和 `lang.md`

---

## 🖥️ 服务器操作

**连接：**
```bash
ssh -p 31867 root@region-42.seetacloud.com
```

**执行命令（必须用 bash -lc）：**
```bash
bash -lc 'source /etc/network_turbo && cd /root/LLM_KVCache_Quantization && python3 xxx.py'
```

**tmux 长任务：**
```bash
tmux new -s <task_id> -d 'command'     # 后台运行
tmux capture-pane -t <task_id> -p      # 查看输出
tmux kill-session -t <task_id>         # 结束会话
```

---

## 📁 核心文件

| 文件 | 用途 |
|------|------|
| `AGENTS.md` | 新 Agent 启动清单（先读这个） |
| `docs/AGENT_README.md` | 本文件（唯一规范） |
| `docs/current_task.md` | 当前任务详情 |
| `docs/autodl_server.md` | 服务器配置 |
| `.agent/skills/*` | Agent 技能库（SSH/tmux/长任务/复现等规范） |
| `objective.md` | 项目目标 |
| `lang.md` | 进度追踪 |
| `development_record.md` | 开发记录 |

---

## 🔄 完整工作流程

### Step 1：查看任务
```bash
python3 scripts/agent_tools/agent_cli.py tasks
cat docs/current_task.md
```

### Step 2：开始任务
```bash
python3 scripts/agent_tools/agent_cli.py start <task_id> <agent_id>
```
> 此命令会：验证任务存在 → 检查未被锁定 → 锁定任务 → 显示任务详情 → 自动执行 `bootstrap`（列出 `.agent/skills` + 做 SSH 健康检查）

### Step 3：执行任务
1. 连接服务器
2. 长任务使用 tmux
3. 每 10 分钟更新心跳：
```bash
python3 scripts/agent_tools/agent_cli.py heartbeat <task_id> <agent_id> "进度说明"
```

### Step 4：完成任务
```bash
python3 scripts/agent_tools/agent_cli.py finish <task_id> <agent_id> "完成说明"
```

### Step 5：更新文档
1. 更新 `development_record.md`（按模板格式）
2. 更新 `lang.md` 进度状态
3. 如有产出物，确保已提交到服务器

---

## ❌ 禁止事项

- ❌ 手动编辑 `docs/.agent_state/` 下的文件
- ❌ 不使用 `start` 命令直接执行任务
- ❌ 不使用 `finish` 命令直接离开
- ❌ 长任务不更新心跳
