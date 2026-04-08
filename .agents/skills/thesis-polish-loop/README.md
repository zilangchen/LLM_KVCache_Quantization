# Thesis Polish Loop — Usage Guide

> 24-hour continuous thesis polishing skill for EMNLP submission quality.
> Primary: international venue quality. Secondary: SCUT undergraduate thesis format compliance.

---

## Quick Start

### 前置条件

1. Mac 持续唤醒（`caffeinate -dims &` 防休眠，或接电源）
2. Worktree 已建立：`/Users/chenzilang/Desktop/LLM_KVCache_Quantization.polish/`
3. Baseline tag 已打：`thesis-polish-baseline`
4. Claude Code client 保持运行（schedule 触发需要）

### 启动 24h 循环

```bash
# Step 1: 切到 worktree
cd /Users/chenzilang/Desktop/LLM_KVCache_Quantization.polish

# Step 2: Round 0 基线扫描（手动触发一次）
/thesis-polish-loop --round 0

# Step 3: 创建 schedule（每 90 分钟自动触发新轮）
/schedule create "thesis-polish" "*/90 * * * *" "/thesis-polish-loop"

# Step 4: 24h 后停止
/thesis-polish-loop --stop
# 或
/schedule delete "thesis-polish"
```

### 手动单轮

```
/thesis-polish-loop              # 执行 1 轮
/thesis-polish-loop --phase 1    # 只执行 Phase 1（调试用）
/thesis-polish-loop --dry        # Dry run，不实际修改
/thesis-polish-loop --resume     # 从 last_checkpoint.json 恢复
```

---

## 监控

```bash
# 查看当前轮次状态
cat .agents/skills/thesis-polish-loop/state/round_counter.json

# 查看待办清单
cat .agents/skills/thesis-polish-loop/state/known_issues.md

# 查看正在运行的实验
cat .agents/skills/thesis-polish-loop/state/running_experiments.json

# 查看每轮报告
ls -la .agents/skills/thesis-polish-loop/reports/

# 查看 git log（每个 commit 对应一个 milestone）
git log --oneline --all thesis-polish-v1
```

---

## 故障恢复

### 场景 1: 单轮中途失败
```bash
# 从 checkpoint 恢复
/thesis-polish-loop --resume
```

### 场景 2: schedule 丢失
```bash
# 列出当前 schedule
/schedule list
# 重新创建
/schedule create "thesis-polish" "*/90 * * * *" "/thesis-polish-loop"
```

### 场景 3: 实验队列僵死
```bash
# 手动清理 running_experiments.json 里已实际终止的条目
# 编辑 state/running_experiments.json，移除 stale entries
```

### 场景 4: 论文状态需要回退
```bash
# 回到基线
cd /Users/chenzilang/Desktop/LLM_KVCache_Quantization.polish
git reset --hard thesis-polish-baseline
```

---

## 目录结构

见 `SKILL.md` 末尾的完整清单。关键目录：

- `phases/`  — 每个 phase 的详细执行指令
- `reviewer_templates/` — 6 个领域 reviewer 的 prompt 模板
- `state/`   — 跨轮次持久化状态
- `reports/` — 每轮产出（round_0/, round_1/, ...）
- `hooks/`   — 外部触发脚本

---

## 关键设计文档

- `SKILL.md`      — 主入口与单轮协议
- `config.yaml`   — 可配置参数
- `venue_catalog.yaml` — 顶级 venue 清单
- `phases/*.md`   — 各 phase 详细指令

---

## 退出条件

Skill 会在以下情况自动停止：

1. 完成 24 轮（约 36 小时）
2. 连续 3 轮 0 CRITICAL 0 MAJOR 意见
3. 同一 phase 连续 3 轮失败
4. 真实时间超过 24 小时
5. 用户手动停止

---

## 与 EMNLP 投稿的关系

- **主目标**：通过多轮审稿人意见将论文质量提升到 EMNLP main track 可接受水平
- **次目标**：在 Phase 4b 顺带把论文格式适配 SCUT 本科毕设规范
- 若两者冲突（例如 SCUT 要求 "第一章" 而 ACL 允许 "Chapter 1"）：
  - 论文主体保持 SCUT 中文章节命名
  - EMNLP 投稿时通过独立 LaTeX macro 切换到英文章节命名
  - `thesis/main_scut.tex` vs `thesis/main_emnlp.tex` 两套入口（Phase 4b 可能新建）
