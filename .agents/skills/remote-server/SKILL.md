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
