---
description: 远程服务器操作 - SSH/tmux/代码同步/资源监控
---

# Remote Server Skill

> 统一 AutoDL 服务器操作规范，包括连接管理、会话管理、代码同步。

---

## 🔗 服务器信息

**SEC-001: 服务器连接信息已移至 `docs/autodl_server.md`（被 .gitignore 保护）。**

使用前请先从该文件读取连接参数：

```bash
# 从 docs/autodl_server.md 读取（该文件不入 git）
# SSH_HOST=<see docs/autodl_server.md>
# SSH_PORT=<see docs/autodl_server.md>
# SSH_USER=<see docs/autodl_server.md>
REMOTE_DIR="/root/LLM_KVCache_Quantization"
```

以下命令中 `$SSH_HOST`、`$SSH_PORT`、`$SSH_USER` 均为占位符，
实际值请从 `docs/autodl_server.md` 获取后替换。

---

## 🛠️ 核心操作

### 1. 连接健康检查

// turbo
```bash
# 测试连接
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "echo 'SSH OK' && nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv"
```

### 2. GPU 资源监控

// turbo
```bash
# 查看 GPU 状态
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "nvidia-smi"

# 持续监控（每 5 秒）
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "watch -n 5 nvidia-smi"
```

### 3. 进程监控

// turbo
```bash
# 查看 Python 进程
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "ps aux | grep python"

# 查看进程运行时间
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "ps -o pid,etime,cmd -p <PID>"
```

---

## 📦 tmux 会话管理

### 创建新会话

// turbo
```bash
# 创建后台会话运行任务
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "bash -lc 'tmux new -s <session_name> -d \"cd $REMOTE_DIR && python scripts/<script>.py\"'"
```

### 查看会话

// turbo
```bash
# 列出所有会话
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "tmux ls"

# 查看会话输出
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "tmux capture-pane -t <session_name> -p"

# 查看最近 50 行
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "tmux capture-pane -t <session_name> -p -S -50"
```

### 管理会话

// turbo
```bash
# 终止会话（需用户确认）
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "tmux kill-session -t <session_name>"

# 附加到会话（交互式）
ssh -t -p $SSH_PORT $SSH_USER@$SSH_HOST "tmux attach -t <session_name>"
```

---

## 🔄 代码同步

### 本地 → 远程

**前置门禁**（推送前必须执行）：
```bash
bash scripts/rsync_gate.sh          # 检查分支 + git status + 运行 pytest
bash scripts/rsync_gate.sh --skip-tests  # 跳过测试（紧急推送）
```

通过后再执行 rsync：

// turbo
```bash
# 同步项目代码（排除大文件和缓存）
# LOCAL_PROJECT_DIR: 你的本地项目路径
rsync -avz --progress \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.venv' \
  --exclude='results/' \
  --exclude='artifacts/' \
  -e "ssh -p $SSH_PORT" \
  $LOCAL_PROJECT_DIR/ \
  $SSH_USER@$SSH_HOST:$REMOTE_DIR/
```

### 远程 → 本地（结果）

// turbo
```bash
# 同步实验结果
rsync -avz --progress \
  -e "ssh -p $SSH_PORT" \
  $SSH_USER@$SSH_HOST:$REMOTE_DIR/results/ \
  $LOCAL_PROJECT_DIR/results/
```

---

## 🔔 等待远端长任务（强制：后台 watchdog，禁止定时 wakeup）

### 原则

**禁止**用 `ScheduleWakeup(delaySeconds=...)` 或任何定时器去周期性"回来检查"
远端 GPU 任务是否跑完。原因：

1. Anthropic prompt cache TTL 仅 5 分钟；每次超过 300s 的 wakeup 都破坏缓存，
   重读完整对话上下文 ≫ 一次后台 watchdog 的开销
2. 时间猜错就双重浪费：任务提前完成要干等，任务延迟完成又要再设一次 wakeup
3. 唤醒时刻与任务结束时刻不对齐，会错过错误的早期信号或白白等超

**必须**改用一次性的本地后台 watchdog，由 Claude Code runtime 的
"background bash 完成通知"机制在任务**实际结束瞬间**唤醒 agent。

### 标准 watchdog：`scripts/remote_watchdog.sh`

脚本位于 `scripts/remote_watchdog.sh`，行为：

- 按 comma-separated tmux session 名列表持续 `tmux ls` 轮询（远端）
- 任何被 watch 的 session 还在就继续 sleep（默认 60s 间隔）
- 全部 session 消失即 exit 0，并打印日志尾部快照

### 启动流程

```bash
# 通过 Bash 工具以 run_in_background=true 启动
SSH_HOST=<从 docs/autodl_server.md 读> \
SSH_PORT=<...> \
SSH_USER=<...> \
SSH_PASSWORD=<...> \
bash scripts/remote_watchdog.sh \
  "svk_smoke_1p5b,svk_smoke_8b" \
  "/root/.../logs/smoke_1p5b_gpu0.log,/root/.../logs/smoke_8b_gpu1.log" \
  60
```

启动后立刻结束本轮；Claude Code 的 runtime 在 watchdog 进程退出时会主动
推一条完成通知到 agent，不需要 agent 自己 poll。

### 何时允许 ScheduleWakeup

只有在**没有可监听的明确终止信号**时才用（例如：等一个外部人类 review、
等一个基于时钟的 cron 触发）。对"远端有 tmux session 在跑，要等它死掉"
这一类场景，一律走 watchdog。

### 轮询间歇期的行为

启动 watchdog 后本地 agent 的空闲期**必须做别的事**（推进写作、更新
文档、review plan、整理 memory），不准坐等 watchdog。等待期间本地
cache 自然冻结直到 watchdog 通知到达。

---

## 📝 日志获取

// turbo
```bash
# 获取最新日志
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "tail -100 $REMOTE_DIR/logs/<logfile>.log"

# 实时跟踪日志
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "tail -f $REMOTE_DIR/logs/<logfile>.log"
```

---

## ⚠️ 常见问题

### SSH 连接超时
```bash
# 添加 keep-alive
ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -p $SSH_PORT ...
```

### 网络加速（AutoDL）
```bash
# 启用 HuggingFace 加速
source /etc/network_turbo
```

### 磁盘空间不足
```bash
# 检查磁盘使用
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "df -h"

# 清理缓存
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "rm -rf ~/.cache/huggingface/hub/models--*/.no_exist"
```

---

## 🚀 快速启动

1. 从 `docs/autodl_server.md` 获取 SSH_HOST/PORT/USER
2. 验证 SSH 连接：`ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "echo OK"`
3. 同步代码：使用上述 rsync 命令
4. 创建 tmux 会话运行任务
5. 监控进度和资源使用
