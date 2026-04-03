---
description: GPU 实验编排器 — 远端状态监测 + 任务调度 + 结果验证
---

# GPU Orchestrator Skill

> 自动监测远端 GPU 服务器状态，根据资源占用和 Plan 待办进行智能任务调度。

---

## 1. 触发与执行方式

```bash
# 手动触发
/gpu-orchestrator

# 定时轮询（推荐：每 10 分钟）
/loop 10m /gpu-orchestrator

# 带参数（指定关注的结果目录）
/gpu-orchestrator results_tag=emnlp_rolealign_v2
```

---

## 2. 监测周期流程

每次触发执行完整的 **采集 → 判读 → 决策 → 执行** 循环：

```
Step 1: 读取连接信息
  └─ Read docs/autodl_server.md → 获取 SSH_HOST/PORT/USER

Step 2: 执行远端采集
  └─ SSH_HOST=xxx SSH_PORT=xxx bash scripts/gpu_orchestrator_check.sh
  └─ 解析输出的结构化数据块

Step 3: 状态判读（见 §3）
  └─ 分类每张 GPU 状态：忙 / 空闲 / 错误

Step 4: 决策分支（见 §4）
  └─ 根据 GPU 状态 + Plan 待办 → 选择行动

Step 5: 执行行动（见 §5）
  └─ 提交任务 / 收割结果 / spawn 验证 / 前台工作

Step 6: 输出报告（见 §7）
  └─ 标准格式摘要
```

---

## 3. 状态判读规则

### GPU 状态分类

| 状态 | 条件 | 含义 |
|------|------|------|
| **忙碌** | 利用率 ≥ 50% **或** 显存占用 > 90% | 有实验正在跑，不宜新增任务 |
| **空闲** | 利用率 < 50% **且** 显存占用 ≤ 90% | 可以分配新任务 |
| **异常** | nvidia-smi 查询失败、温度 > 85°C | 需要告警和干预 |

### tmux 任务状态判断

通过 `<<< TMUX_OUTPUT >>>` 中每个 session 的最近 25 行输出判断：

| 模式 | 判断依据 | 状态 |
|------|---------|------|
| 正在运行 | 输出中有进度指示（seed、step、epoch 变化） | running |
| 已完成 | 输出末尾有 "completed"、"done"、"saved to" | completed |
| 报错 | 输出有 "Error"、"Traceback"、"FAILED" | error |
| 卡住 | session 存在但最近输出时间 > 30min 无变化 | stalled |

### 磁盘告警

磁盘使用率 > 80% 时触发告警，建议清理 `~/.cache/huggingface/` 或旧结果。

---

## 4. 决策树

### 4.1 所有 GPU 忙碌（全部利用率 ≥ 50%）

```
所有 GPU 忙碌
├─ 有任务 completed?
│   └─ 是 → 执行【收割结果】（§5.2）
│        └─ 自动 spawn agent 验证结果合理性（§5.4）
│
├─ 有任务 error/stalled?
│   └─ 是 → 诊断错误原因
│        ├─ 可修复 → 修复代码/配置 → rsync → 重新提交
│        └─ 需排查 → 输出错误详情供用户判断
│
└─ 全部正常 running →【转前台工作】（§5.5）
     ├─ 验证已收割的结果
     ├─ 推进 iteration.md 中的非 GPU 待办
     ├─ 代码审查 / review_tracker 清理
     └─ 论文写作 / 文档更新
```

### 4.2 部分 GPU 空闲（有卡利用率 < 50%）

```
部分 GPU 空闲
├─ 读取 iteration.md → Approved Plans 中的待办任务
├─ 冲突检测（§4.3）
│   ├─ 通过 → 组装命令 → 直接提交到空闲 GPU（无需确认）
│   └─ 冲突 → 报告冲突原因，跳过该任务，尝试下一个
│
├─ 无待办任务?
│   └─ 报告 "GPU 空闲但无待办任务" → 建议用户补充 Plan
│
└─ 同时检查已完成任务 → 收割结果
```

### 4.3 冲突检测规则

新任务提交前必须逐条检查：

| 检查项 | 规则 | 冲突? |
|--------|------|-------|
| 输出目录 | 新任务与运行中任务写同一 `results/<tag>/runs/` 子路径 | ✗ 冲突 |
| profiling | profiling 任务需要所有 GPU 空闲 | ✗ 冲突（除非全空） |
| 模型文件锁 | 同一模型的两个任务可能竞争 HF cache 写锁 | ⚠ 首次下载时冲突 |
| CUDA 设备 | 通过 `CUDA_VISIBLE_DEVICES` 隔离，需确认新任务指定的卡未被占用 | 检查 GPU_PROCESSES |
| 同模型不同 seed | 不同 seed 跑同一模型 | ✓ 可并行 |
| 同模型不同 kv_mode | 不同量化方式跑同一模型 | ✓ 可并行 |
| 不同模型 | 不同模型跑不同卡 | ✓ 可并行 |

### 4.4 全部 GPU 空闲

```
全部 GPU 空闲
├─ Plan 中有 profiling 任务待执行?
│   └─ 是 → 优先执行 profiling（需独占）
│
└─ 否 → 按 Plan 优先级批量提交任务
      └─ 每张卡分配一个任务，最大化利用率
```

---

## 5. 执行动作

### 5.1 提交新任务

```bash
# 1. 确保代码已同步
bash scripts/rsync_gate.sh --skip-tests  # 或完整 gate
rsync -avz --progress \
  --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='.venv' --exclude='results/' --exclude='artifacts/' \
  -e "ssh -p $SSH_PORT" \
  ./ $SSH_USER@$SSH_HOST:$REMOTE_DIR/

# 2. 创建 tmux session 运行任务
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST \
  "bash -lc 'tmux new -s <session_name> -d \"cd $REMOTE_DIR && CUDA_VISIBLE_DEVICES=<gpu_id> <command>\"'"
```

**session 命名规范**: `<model_short>_<task>_<detail>`
- 例: `1p5b_ppl_s1234`, `7b_ruler_asym`, `profiling_tpot`

### 5.2 收割结果

```bash
# 1. 同步结果到本地
rsync -avz --progress \
  -e "ssh -p $SSH_PORT" \
  $SSH_USER@$SSH_HOST:$REMOTE_DIR/results/<tag>/ \
  results/<tag>/

# 2. 验证完整性
python scripts/check_run_completeness.py --runs_dir results/<tag>/runs

# 3. 如有已完成的 tmux session，清理
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "tmux kill-session -t <completed_session>"
```

### 5.3 错误处理

```
发现 error/stalled 任务
├─ 获取错误详情: tmux capture-pane -t <session> -p -S -100
├─ 分析根因:
│   ├─ OOM → 降低 batch size 或换更大显存的卡
│   ├─ CUDA error → 重启 session
│   ├─ 代码 bug → 修复 → rsync → 重新提交
│   └─ 数据/校准文件缺失 → 检查 artifacts/ 同步
└─ 修复后重新提交（复用原 tmux session 名称）
```

### 5.4 结果验证（自动 spawn agent）

收割结果后，自动 spawn agent 进行合理性检验：

```
spawn Agent (subagent_type: general-purpose) 执行:
1. 读取结果 CSV/JSON
2. 与已有 baseline 对比（PPL 退化幅度、Needle 准确率等）
3. 搜索相关论文数据对比（WebSearch）
4. 判断结果是否在合理范围内
5. 输出验证报告：通过/可疑/异常 + 理由
```

验证维度:
- PPL 退化: INT8 应 < 1%, INT4-RoleAlign < 15% (模型规模依赖)
- Needle: 所有方法应 ≥ 95%, RoleAlign 应 100%
- RULER: INT8 与 fp16 差距应 < 5 分
- 吞吐: Triton 融合核应比 torch_ref 快 8-38%

### 5.5 前台工作（GPU 全忙时）

按优先级选择:
1. 验证刚收割的实验结果
2. 推进 iteration.md Approved Plans 中的非 GPU 任务
3. review_tracker.md 中的待修复 issue
4. 论文写作/文档更新
5. 代码审查和清理

---

## 6. 与现有 Skill 的关系

| Skill | 关系 |
|-------|------|
| `remote-server` | 引用其 SSH/tmux/rsync 命令模板，不重复定义 |
| `long-running-task` | 提交的任务如果是长时间运行，遵循其 checkpoint/resume 协议 |
| `reproducibility` | 提交任务时确保满足其 seed/config 固定要求 |
| `execplan` | 任务来源是 Plan，遵循 Plan 的优先级和依赖关系 |

---

## 7. 报告格式

每次轮询结束输出标准摘要:

```markdown
### GPU Orchestrator Report — <timestamp>

**GPU 状态**:
| GPU | 型号 | 利用率 | 显存 | 温度 | 状态 |
|-----|------|--------|------|------|------|
| 0 | H20 | 85% | 45/96 GB | 62°C | 忙碌 |
| 1 | H20 | 12% | 2/96 GB | 38°C | 空闲 |
| 2 | H20 | 92% | 78/96 GB | 71°C | 忙碌 |

**tmux 任务**:
| Session | GPU | 状态 | 进度摘要 |
|---------|-----|------|---------|
| 1p5b_ppl_s1234 | 0 | running | seed 1234, step 450/1000 |
| 7b_ruler_asym | 2 | running | 3/6 subtasks done |

**本轮决策**:
- [x] GPU 1 空闲 → 提交 `8b_ppl_s1235` (CUDA_VISIBLE_DEVICES=1)
- [x] 收割 `1p5b_needle` 结果 → spawn 验证 agent
- [ ] 磁盘 72% — 正常

**下次轮询**: 10 分钟后
```

---

## 8. 安全约束

- **不修改远端已有结果**: 只读取/同步，不删除远端 results/
- **不杀运行中的任务**: 只有 completed/error 的 session 才可 kill
- **profiling 独占**: 3 张 GPU 全部空闲才可提交 profiling
- **rsync 方向明确**: 代码 local→remote，结果 remote→local，不混用
- **遵守 rsync_gate**: 代码推送前必须过 gate（至少 --skip-tests）
