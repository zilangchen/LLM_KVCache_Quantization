# Phase 5: Experiments（实验触发 + 生命周期管理）

> 将 reviewer 提出的"需要实验数据"的 comment 转化为真实的实验任务，并通过跨轮次闭环回填到论文。

---

## 核心设计：实验生命周期

```
Queued (Phase 3 发现) → Running (Phase 5 触发) → Completed (Phase 0 检测) → Closed (Phase 0 回填)
```

每个实验在整个 lifecycle 中保持 motivation + original_target 不变，确保闭环。

---

## 输入
- `state/rerun_queue.json` — 待跑实验队列（由 Phase 3 填充）
- `state/running_experiments.json` — 当前 running 快照
- `docs/autodl_server.md` — 远端服务器连接信息

## 输出
- 更新的 `state/rerun_queue.json`（queued → running）
- 更新的 `state/running_experiments.json`
- `reports/round_N/experiments_triggered.md`

---

## 执行步骤

### Step 5.1: 选择本轮可触发的实验

从 `state/rerun_queue.json` 中 filter `status == "queued"` 的条目。

优先级排序（高到低）：
1. CRITICAL severity 的 reviewer 意见对应的实验
2. MAJOR severity 的 reviewer 意见
3. 预期时长短的实验（<30 min > <60 min > <2h）
4. 本轮新增的（较旧的可能已被后续意见覆盖）

根据 `config.yaml` 的 `phase5_experiments.max_experiments_per_round`（默认 3），选择前 N 个。

### Step 5.2: 实验条目结构化

每个 queued 实验必须有完整的元数据：

```json
{
  "id": "R3-EXP-001",
  "round_triggered": 3,
  "severity": "MAJOR",
  "motivation": "statistical_methods reviewer 质疑 n=5 下 Bootstrap CI 的功效",
  "reviewer_comment_id": "R3-stat-04",
  "original_target": {
    "file": "thesis/chapters/ch4_experiments.tex",
    "location": "L185-190",
    "description": "统计框架段需要加入 n=10 seeds 的 CI 半宽"
  },
  "command": "bash scripts/ruler_n10_rerun.sh",
  "script_path": "scripts/ruler_n10_rerun.sh",
  "expected_output_glob": "results/emnlp_defense_v1/runs/ruler_n10_*/*.csv",
  "expected_duration_min": 45,
  "closure_action": {
    "type": "update_table_with_data",
    "instructions": "从 ruler_n10_*.csv 提取 n=10 的 RULER 均值和 bootstrap CI 半宽，更新 ch4:L185-190 的统计框架段",
    "verification": "grep 新数字是否出现，确保未遗漏"
  },
  "status": "queued",
  "tmux_session": null,
  "started_at": null,
  "completed_at": null,
  "closure_commit": null
}
```

**重要**：如果某个条目缺少 `motivation` 或 `closure_action` → 拒绝触发，回退到 `known_issues.md` 作为"意图不清晰的 reviewer 意见"。

### Step 5.3: 创建执行脚本（如果不存在）

对每个要触发的实验：

1. 检查 `script_path` 是否已存在
2. 不存在则**自动生成**：
   - 根据 reviewer 意见推断需要跑什么
   - 参考 `scripts/exp*.sh` 的格式
   - 脚本内容：远端环境 setup + 执行命令 + 输出到指定目录
3. 生成后执行 `bash -n <script>` 语法检查
4. 若语法检查通过 → 加入待触发队列

### Step 5.4: 远端触发实验

对每个要触发的实验：

1. **rsync 脚本到远端**（参考 `.agents/skills/remote-server/SKILL.md`）：
   ```bash
   scp -P <PORT> scripts/<script>.sh <USER>@<HOST>:/root/LLM_KVCache_Quantization/scripts/
   ```

2. **启动 tmux session**：
   ```bash
   ssh -p <PORT> <USER>@<HOST> "cd /root/LLM_KVCache_Quantization && tmux new-session -d -s <EXP_ID> 'bash scripts/<script>.sh > logs/<EXP_ID>.log 2>&1'"
   ```

3. **记录 tmux_session_id**：
   - 更新 rerun_queue entry: `status: queued → running`
   - 填入 `tmux_session`, `started_at`
   - 移动到 `running_experiments.json`

4. **不等待结果**：立即进入下一个实验或下一 phase
   - 实验完成的检测在下一轮 Phase 0 进行

### Step 5.5: 对无法自动化的实验

某些实验 skill 无法自动化（例如"需要改 src/ 源代码后重跑"）：
- 标记为 `needs_manual`
- 写入 `state/known_issues.md` + 详细说明
- **不**触发，等用户介入

### Step 5.6: 输出 experiments_triggered.md

```markdown
# Experiments Triggered — Round N

Generated: YYYY-MM-DD HH:MM

---

## Triggered This Round (3)

### R3-EXP-001 [MAJOR] — n=10 seeds for RULER CI
- **Motivation**: statistical_methods reviewer 质疑 n=5 功效
- **Script**: scripts/ruler_n10_rerun.sh
- **Remote**: tmux session `R3-EXP-001` on AutoDL
- **Started**: 2026-04-08T14:30:00
- **Expected duration**: 45 min
- **Closure target**: ch4:L185-190
- **Status**: running

### R3-EXP-002 [MAJOR] — BitDecoding format compatibility check
- ...

### R3-EXP-003 [MINOR] — ...

---

## Skipped This Round (2)

### R3-EXP-004 [MINOR] — Mistral-7B LongBench rerun
- **Reason**: 超过 max_experiments_per_round 限制
- **Action**: 保留在 rerun_queue.json 等下轮

### R3-EXP-005 [NIT] — ...
- **Reason**: needs_manual（需要修改 src/ 源代码）
- **Action**: 已写入 known_issues.md

---

## Current Running Experiments (5, including prior rounds)

| ID | Round | Status | Started | Expected Closure |
|----|-------|--------|---------|------------------|
| R1-EXP-003 | 1 | running | 6h ago | next round housekeeping |
| R2-EXP-001 | 2 | running | 3h ago | ... |
| R3-EXP-001 | 3 | running | just now | round 4 |
| R3-EXP-002 | 3 | running | just now | round 4 |
| R3-EXP-003 | 3 | running | just now | round 4 |

---

## Queue Status After Trigger

- Queued: 5 → 2 (3 moved to running)
- Running: 2 → 5
- Completed: 1 (R1-EXP-001 from last round)
- Closed: 1 (R1-EXP-001 closure action done in Phase 0 this round)

---

## Remote Server Health Check

- ssh connectivity: ✅
- GPU availability: 2 of 3 free
- Disk space: 45% used
```

---

## 重要约束

1. **每个实验必须有闭环**：缺少 motivation 或 closure_action 则拒绝触发
2. **资源保护**：
   - 每轮最多触发 3 个新实验
   - 总 running 实验数不超过 6（防止远端 GPU 过载）
3. **超时处理**：
   - 实验跑超 `timeout_rounds` （默认 3 轮 ≈ 4.5 小时）仍未出结果
   - 标记为 `timed_out`，写入 known_issues
4. **远端连接失败**：
   - ssh 失败 → skip 本轮 Phase 5，不影响其他 phase
   - 下轮重试
5. **时间盒**：30 分钟（触发只是 rsync + tmux start，不需要等待结果）

---

## 与其他 phase 的交接

- **输入←Phase 3**：expert_reviews.md 中的 experiment queue candidates
- **输出→Phase 0**（下一轮）：running_experiments 等待检测闭环
- **输出→状态**：rerun_queue.json, running_experiments.json
- **不直接影响 Phase 4**：实验结果要等到下一轮才能回填论文

---

## 错误恢复

- **tmux session 创建失败** → 回滚：status 从 running 改回 queued
- **script 生成失败** → 写入 known_issues.md，不触发
- **远端磁盘满** → 停止本轮触发新实验，发送警告
- **ssh key 过期** → 提示用户，skip 本轮
