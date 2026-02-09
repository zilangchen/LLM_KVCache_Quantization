---
description: 远程服务器操作 - SSH/tmux/代码同步/资源监控
---

# Remote Server Skill

> 统一 AutoDL 服务器操作规范，包括连接管理、会话管理、代码同步。

---

## 🔗 服务器信息

```bash
# AutoDL 服务器（从 docs/autodl_server.md 读取）
SSH_HOST="region-42.seetacloud.com"
SSH_PORT="31867"
SSH_USER="root"
REMOTE_DIR="/root/LLM_KVCache_Quantization"
```

---

## 🛠️ 核心操作

### 1. 连接健康检查

// turbo
```bash
# 测试连接
ssh -p 31867 root@region-42.seetacloud.com "echo 'SSH OK' && nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv"
```

### 2. GPU 资源监控

// turbo
```bash
# 查看 GPU 状态
ssh -p 31867 root@region-42.seetacloud.com "nvidia-smi"

# 持续监控（每 5 秒）
ssh -p 31867 root@region-42.seetacloud.com "watch -n 5 nvidia-smi"
```

### 3. 进程监控

// turbo
```bash
# 查看 Python 进程
ssh -p 31867 root@region-42.seetacloud.com "ps aux | grep python"

# 查看进程运行时间
ssh -p 31867 root@region-42.seetacloud.com "ps -o pid,etime,cmd -p <PID>"
```

---

## 📦 tmux 会话管理

### 创建新会话

// turbo
```bash
# 创建后台会话运行任务
ssh -p 31867 root@region-42.seetacloud.com "bash -lc 'tmux new -s <session_name> -d \"cd $REMOTE_DIR && python scripts/<script>.py\"'"
```

### 查看会话

// turbo
```bash
# 列出所有会话
ssh -p 31867 root@region-42.seetacloud.com "tmux ls"

# 查看会话输出
ssh -p 31867 root@region-42.seetacloud.com "tmux capture-pane -t <session_name> -p"

# 查看最近 50 行
ssh -p 31867 root@region-42.seetacloud.com "tmux capture-pane -t <session_name> -p -S -50"
```

### 管理会话

// turbo
```bash
# 终止会话（需用户确认）
ssh -p 31867 root@region-42.seetacloud.com "tmux kill-session -t <session_name>"

# 附加到会话（交互式）
ssh -t -p 31867 root@region-42.seetacloud.com "tmux attach -t <session_name>"
```

---

## 🔄 代码同步

### 本地 → 远程

// turbo
```bash
# 同步项目代码（排除大文件和缓存）
rsync -avz --progress \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.venv' \
  --exclude='results/' \
  --exclude='artifacts/' \
  -e "ssh -p 31867" \
  /Users/chenzilang/Desktop/LLM_KVCache_Quantization/ \
  root@region-42.seetacloud.com:/root/LLM_KVCache_Quantization/
```

### 远程 → 本地（结果）

// turbo
```bash
# 同步实验结果
rsync -avz --progress \
  -e "ssh -p 31867" \
  root@region-42.seetacloud.com:/root/LLM_KVCache_Quantization/results/ \
  /Users/chenzilang/Desktop/LLM_KVCache_Quantization/results/
```

---

## 📝 日志获取

// turbo
```bash
# 获取最新日志
ssh -p 31867 root@region-42.seetacloud.com "tail -100 $REMOTE_DIR/logs/<logfile>.log"

# 实时跟踪日志
ssh -p 31867 root@region-42.seetacloud.com "tail -f $REMOTE_DIR/logs/<logfile>.log"
```

---

## ⚠️ 常见问题

### SSH 连接超时
```bash
# 添加 keep-alive
ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -p 31867 ...
```

### 网络加速（AutoDL）
```bash
# 启用 HuggingFace 加速
source /etc/network_turbo
```

### 磁盘空间不足
```bash
# 检查磁盘使用
ssh -p 31867 root@region-42.seetacloud.com "df -h"

# 清理缓存
ssh -p 31867 root@region-42.seetacloud.com "rm -rf ~/.cache/huggingface/hub/models--*/.no_exist"
```

---

## 🚀 快速启动

1. 验证 SSH 连接：`ssh -p 31867 root@region-42.seetacloud.com "echo OK"`
2. 同步代码：使用上述 rsync 命令
3. 创建 tmux 会话运行任务
4. 监控进度和资源使用
