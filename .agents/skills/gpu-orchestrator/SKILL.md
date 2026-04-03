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
├─ 读取 task_plan.md + iteration.md Approved Plans → 获取待办任务
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

### 5.4 主动结果检测

**不等任务完成**——每次轮询周期都主动拉取远端已产出的数据：

```bash
# 增量同步远端结果（包括运行中任务的部分输出）
rsync -avz --progress --ignore-existing \
  -e "ssh -p $SSH_PORT" \
  $SSH_USER@$SSH_HOST:$REMOTE_DIR/results/ \
  results/
```

检测新数据的判断：
- 对比本地 `results/` 目录的文件列表与上次轮询的快照
- 新增或修改的 CSV/JSON/log 文件即为"新数据"
- 即使任务仍在运行，已输出的 seed/subtask 结果也可以提前验证

**触发验证的条件**（满足任一即触发 §5.5 多 Agent 验证）：
- 检测到新的 `*_results.csv` 或 `*_summary.json`
- 某个 tmux session 状态变为 completed
- 累积新增 ≥ 3 个 run 目录

### 5.5 多 Agent 并行验证（自动 spawn）

检测到新结果后，**并行 spawn 多个 agent**，从不同角度分析数据合理性：

```
                    检测到新结果数据
                         │
            ┌────────────┼────────────┐────────────┐
            ▼            ▼            ▼            ▼
      [Agent A]    [Agent B]    [Agent C]    [Agent D]
       统计验证      文献对比      跨模型一致性    异常检测
            │            │            │            │
            └────────────┴────────────┴────────────┘
                         │
                    汇总验证报告
```

#### Agent A: 统计验证

```
spawn Agent (subagent_type: general-purpose, name: "verify-stats")
prompt:
  读取 results/<tag>/runs/ 中的新增结果 CSV，执行以下检查：
  1. 各 kv_mode 的 PPL 退化幅度是否在预期范围内
     - INT8-ours: < 1%
     - INT4-RoleAlign (int4_ours_asym): < 15%（模型规模依赖：1.5B ~13.7%, 7B ~6.1%, 8B ~2.4%）
  2. Needle-in-a-Haystack 准确率：RoleAlign 应 100%，其他 ≥ 95%
  3. 同一配置多 seed 结果的方差是否合理（CV < 5% 为正常）
  4. Bootstrap CI 区间是否覆盖预期值
  输出：每项检查的 PASS/WARN/FAIL + 具体数值
```

#### Agent B: 文献对比

```
spawn Agent (subagent_type: general-purpose, name: "verify-literature")
prompt:
  针对以下实验结果，搜索相关论文进行对比：
  - 用 WebSearch 搜索 "KV cache quantization INT4 perplexity degradation"
  - 搜索 "KIVI quantization results" 和 "KVQuant results"
  - 搜索目标模型（Qwen2.5/LLaMA-3.1）的已知量化 benchmark
  对比维度：
  1. 我们的 INT4 PPL 退化 vs 论文中报告的同等位宽退化
  2. 我们的 KV 压缩比 vs 论文声称的压缩比
  3. 我们的 Needle 准确率 vs 论文中的长序列保真度
  如果我们的结果明显好于或差于论文 → 标记为需要解释的异常
  输出：论文对比表 + 我们数据的合理性评估
```

#### Agent C: 跨模型一致性

```
spawn Agent (subagent_type: general-purpose, name: "verify-consistency")
prompt:
  读取所有模型（1.5B, 7B, 8B）的结果，检查跨模型一致性：
  1. PPL 退化的模型规模依赖性：大模型退化应更小（1.5B > 7B ≈ 8B）
  2. Needle 准确率应跨模型一致（不应出现大模型反而更差）
  3. RULER 各子任务的排序应跨模型一致
  4. 吞吐加速比应与 head_dim/num_heads 相关
  如果发现违反规模缩放规律的异常 → 重点标记
  输出：跨模型一致性矩阵 + 异常点列表
```

#### Agent D: 异常检测

```
spawn Agent (subagent_type: general-purpose, name: "verify-anomaly")
prompt:
  扫描所有新增结果数据，寻找以下异常模式：
  1. 离群值：某个 seed 的结果与同配置其他 seed 偏差 > 2σ
  2. 全零/全满分：PPL=0 或 Needle=0% 或 100%（非 RoleAlign）可能是 bug
  3. NaN/Inf：结果中出现非法数值
  4. 异常快/慢：某个 run 的时间与同配置差异 > 50%
  5. 文件不完整：CSV 行数不足、JSON 格式错误
  6. task_failure_*.json：检查是否有新增失败记录
  输出：异常清单（严重/警告/正常）+ 每条异常的可能原因
```

#### 汇总

4 个 agent 全部返回后，Claude 汇总为统一报告：

```markdown
### 验证报告 — <timestamp>

**总体评估**: ✅ 通过 / ⚠️ 有警告 / ❌ 有异常

| 维度 | 结果 | 关键发现 |
|------|------|---------|
| 统计验证 | ✅/⚠️/❌ | ... |
| 文献对比 | ✅/⚠️/❌ | ... |
| 跨模型一致性 | ✅/⚠️/❌ | ... |
| 异常检测 | ✅/⚠️/❌ | ... |

**需要关注的问题**:
1. ...
2. ...

**建议行动**:
- ...
```

如果总体评估为 ❌：暂停提交同类新任务，优先排查问题。

### 5.6 前台工作：深度思考 + 主动规划

GPU 全忙的等待期**不是空闲期**——这是做深度思考和推进非 GPU 工作的黄金时间。

#### Phase A: 全局状态审视（每次进入前台工作前必做）

```
Read 以下文件，构建当前项目的完整画面：
1. task_plan.md — Plan Mode 生成的当前计划（阶段、步骤、依赖）
2. iteration.md — Approved Plans + Timeline 最近 10 条
3. review_tracker.md — open issues 概况
4. progress.md — 如果存在，读取当前进度状态
5. 远端正在运行的任务列表（刚采集的）
```

然后进行一次**主动思考**，回答以下问题：

```
深度思考清单：
┌─────────────────────────────────────────────────────┐
│ 1. 目前什么在阻塞项目推进？                            │
│    → 是等 GPU 结果？等人工决策？还是有前置任务没做？       │
│                                                     │
│ 2. 远端任务跑完后，下一步需要什么准备？                   │
│    → 聚合脚本是否就绪？LaTeX 表格模板是否需要更新？       │
│    → 结果目录结构是否需要调整？                         │
│                                                     │
│ 3. 有没有可以并行推进的非 GPU 工作？                    │
│    → 论文中哪些章节可以先写框架、等数据填入？             │
│    → review_tracker 中哪些 issue 与当前跑的实验无关？    │
│                                                     │
│ 4. 当前实验设计是否有隐患？                            │
│    → 配置文件是否完整？seed 列表是否覆盖？               │
│    → 是否有已知的 bug 可能影响正在运行的实验？            │
│                                                     │
│ 5. 有没有可以提前做的质量保障工作？                     │
│    → 写/更新测试用例？                               │
│    → 检查 experiment_sop 的复现步骤是否完整？           │
│                                                     │
│ 6. 距离目标 deadline（EMNLP ARR）还有哪些 gap？       │
│    → 论文完成度如何？                                 │
│    → 还缺哪些实验数据？                               │
│    → 缺口和当前 GPU 任务的关系是什么？                  │
└─────────────────────────────────────────────────────┘
```

#### Phase B: 选择最高价值行动

基于 Phase A 的思考结果，选择**此刻最有价值**的工作。不是按固定列表走，而是根据项目实际状态判断。

常见的高价值行动模式：

| 项目状态 | 最有价值的行动 |
|---------|--------------|
| 远端即将跑完，本地缺聚合脚本 | 准备/调试聚合和绘图脚本 |
| 论文实验章节缺数据描述框架 | 先写文字框架，留数据占位符 |
| review_tracker 有与当前实验相关的 open issue | 优先修复（可能影响结果有效性） |
| 上一轮结果验证发现可疑数据 | 深入分析根因，准备重跑方案 |
| 目标 deadline 临近但论文进度落后 | 推进论文写作，不做低优先级代码清理 |
| 所有前台工作都已完成 | 对已有全量结果做深度分析和可视化 |

#### Phase C: 执行 + 为下一轮轮询做准备

执行选定的工作，同时：
- 如果发现了影响远端运行实验的问题 → 记录，等该任务完成后处理（不中断运行中的实验）
- 如果发现了可以在下一轮提交的新任务 → 准备好命令和配置
- 将思考结论和行动记录到轮询报告中（§7 报告新增"前台工作"段）

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
- [x] 收割 `1p5b_needle` 结果 → spawn 4 个验证 agent
- [ ] 磁盘 72% — 正常

**结果验证** (如有):
| 维度 | Agent | 结果 | 关键发现 |
|------|-------|------|---------|
| 统计验证 | verify-stats | ✅ | PPL 退化 1.5B=13.2% 在预期内 |
| 文献对比 | verify-literature | ⚠️ | 我们的 INT4 PPL 优于 KIVI 报告值，需确认是否因模型不同 |
| 跨模型一致性 | verify-consistency | ✅ | 规模缩放趋势正常 |
| 异常检测 | verify-anomaly | ✅ | 无离群值 |

**前台思考**:
- 当前阻塞: 等 7B RULER 跑完才能完成论文 Table 3
- 最有价值行动: 先写 Table 3 框架 + 完成 1.5B 行的数据填充
- 下轮准备: 聚合脚本已调试就绪，7B 完成后可立即聚合

**下次轮询**: 10 分钟后
```

---

## 8. 安全约束

- **不修改远端已有结果**: 只读取/同步，不删除远端 results/
- **不杀运行中的任务**: 只有 completed/error 的 session 才可 kill
- **profiling 独占**: 3 张 GPU 全部空闲才可提交 profiling
- **rsync 方向明确**: 代码 local→remote，结果 remote→local，不混用
- **遵守 rsync_gate**: 代码推送前必须过 gate（至少 --skip-tests）
