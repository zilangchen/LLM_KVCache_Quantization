---
description: 长时间任务管理 - 检查点机制、断点续传、错误恢复
---

# Long-Running Task Skill

> 解决 Agent 在长时间任务中遇到错误停止需要 retry 的痛点。

---

## 🎯 核心原则

1. **任务分解**：将大任务拆分为可验证的小步骤
2. **状态持久化**：每个检查点自动保存进度
3. **断点续传**：从上次中断点恢复
4. **优雅降级**：错误时保留已完成工作

---

## 📋 使用场景

- 校准脚本运行（`calibrate_behavior.py`）
- 实验矩阵执行（`run_experiments.py`）
- 长时间推理/评测任务
- 大规模数据处理

---

## 🔧 工作流程

### Step 1: 任务分解

将任务拆分为原子步骤，每个步骤：
- 有明确的输入/输出
- 可独立验证
- 失败不影响已完成步骤

```
示例：实验矩阵执行
├── 步骤1: 加载配置 ✓
├── 步骤2: 环境检查 ✓
├── 步骤3: 运行 exp_001 ✓
├── 步骤4: 运行 exp_002 ← 当前
├── 步骤5: 运行 exp_003
└── 步骤6: 汇总结果
```

### Step 2: 创建检查点文件

// turbo
```bash
# 创建任务状态文件
cat > .task_checkpoint.json << 'EOF'
{
  "task_id": "exp_matrix_run_001",
  "created_at": "2026-01-21T14:40:00",
  "total_steps": 6,
  "completed_steps": 0,
  "current_step": 1,
  "status": "running",
  "checkpoints": []
}
EOF
```

### Step 3: 执行任务并更新检查点

// turbo
```python
# 伪代码：每完成一步更新检查点
import json
from datetime import datetime

def save_checkpoint(step_id, result, checkpoint_file=".task_checkpoint.json"):
    with open(checkpoint_file, "r") as f:
        state = json.load(f)
    
    state["completed_steps"] = step_id
    state["current_step"] = step_id + 1
    state["checkpoints"].append({
        "step": step_id,
        "time": datetime.now().isoformat(),
        "result": str(result)[:200]  # 截断避免过大
    })
    
    with open(checkpoint_file, "w") as f:
        json.dump(state, f, indent=2)
```

### Step 4: 断点续传

// turbo
```python
def resume_from_checkpoint(checkpoint_file=".task_checkpoint.json"):
    """从检查点恢复任务"""
    if not os.path.exists(checkpoint_file):
        return 1  # 从头开始
    
    with open(checkpoint_file, "r") as f:
        state = json.load(f)
    
    print(f"恢复任务: {state['task_id']}")
    print(f"已完成: {state['completed_steps']}/{state['total_steps']}")
    
    return state["current_step"]
```

### Step 5: 同步更新项目记录

// turbo
```bash
# 每个重要检查点后更新 lang.md
echo "- **$(date '+%Y-%m-%d %H:%M:%S')**: 任务进度 - 步骤 N/M 完成" >> lang.md

# 更新 development_record.md
echo "# <Antigravity $(date '+%Y-%m-%d %H:%M:%S')>" >> development_record.md
```

---

## ⚠️ 错误恢复策略

### 策略 1: 自动重试（最多 3 次）
```python
for attempt in range(3):
    try:
        result = run_step(step_id)
        break
    except Exception as e:
        if attempt == 2:
            save_error_state(step_id, e)
            raise
        time.sleep(5 * (attempt + 1))  # 指数退避
```

### 策略 2: 降级执行
```python
try:
    result = run_full_experiment()
except OOMError:
    result = run_with_smaller_batch()
```

### 策略 3: 保留已完成工作
```python
try:
    run_all_experiments()
except Exception:
    # 即使失败也保存已完成的结果
    save_partial_results()
    raise
```

---

## 📁 检查点文件结构

```
.task_checkpoint.json
{
  "task_id": "string",
  "created_at": "ISO datetime",
  "total_steps": int,
  "completed_steps": int,
  "current_step": int,
  "status": "running|completed|failed",
  "checkpoints": [
    {"step": int, "time": "ISO datetime", "result": "string"}
  ],
  "error": null | {"step": int, "message": "string"}
}
```

---

## 🚀 快速启动

1. 确认任务可以分解为多个步骤
2. 为每个步骤定义验收条件
3. 在关键位置插入检查点保存
4. 开始执行，失败后可从检查点恢复
