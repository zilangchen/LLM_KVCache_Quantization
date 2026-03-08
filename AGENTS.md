# AGENTS.md — Multi-Agent Development Workflow

> 本文件是外部 AI 编码工具（Codex 等）理解本项目多 Agent 协作体系的**唯一入口**。
> 详细编码规范见 `CLAUDE.md`；Agent 内部指令见 `.claude/agents/*.md`（仅 Claude Code 使用）。

---

## 1. Project Snapshot

- **Purpose**: Reproducible KV-cache quantization research pipeline for efficient LLM inference (EMNLP 2026).
- **Stack**: Python 3.12, PyTorch 2.8.0 (CUDA 12.8), Transformers, Triton, numpy/pandas/matplotlib.
- **Key modules**: `src/cache/`, `src/quant/`, `src/kernels/`, `src/engine/`, `scripts/`.
- **Authoritative files**: `objective.md` (goals), `iteration.md` (progress), `review_tracker.md` (issues), `experiment_sop.md` (experiment protocol).

---

## 2. Agent Roster

| # | Agent | Model | Config | Role | Permissions |
|---|-------|-------|--------|------|-------------|
| 1 | **Supervisor** | opus | `.claude/agents/supervisor.md` | 最高权限调度者。目标驱动持续运行，3 模式状态机（Execute/Wait/Monitor），调用 Codex Developer 和 spawn Review-Coord | bypassPermissions, 读写全部文件 |
| 2 | **Developer (Codex)** | GPT-5.4 | `.claude/agents/developer.md` | 编码执行者。由 Supervisor 通过 MCP 工具 `mcp__codex__codex` 调用，直接在 main 修复代码+跑测试，不提交。可读取 tracker（只读），可访问远程服务器。Supervisor 审核后落地 | 直接在 main 操作，Supervisor 审核提交 |
| 3 | **Review-Coord** | opus | `.claude/agents/review-coord.md` | 审查协调员。持续守护事件循环，检测新 commit → 增量审查，空闲时全量深度审查 10 模块 | bypassPermissions, 写 review_tracker + iteration |
| 4 | **D1 review-numerical** | sonnet | `.claude/agents/review-numerical.md` | 数值正确性：量化误差、loss 语义、shape/dtype、NaN/Inf | 只读 + 写 review_tracker.md |
| 5 | **D2 review-silent** | sonnet | `.claude/agents/review-silent.md` | 静默失败：空 catch、不当 fallback、错误吞噬 | 同上 |
| 6 | **D3 review-security** | sonnet | `.claude/agents/review-security.md` | 安全漏洞：注入、路径穿越、反序列化、凭证泄露 | 同上 |
| 7 | **D4 review-contract** | sonnet | `.claude/agents/review-contract.md` | 接口契约：稳定 API 守护、签名/语义变化 | 同上 |
| 8 | **D5 review-boundary** | sonnet | `.claude/agents/review-boundary.md` | 边界鲁棒性：空输入、极端值、dtype/device 不匹配 | 同上 |
| 9 | **D6 review-test** | sonnet | `.claude/agents/review-test.md` | 测试覆盖：缺口评分、回归测试、质量 | 同上 |
| 10 | **D7 review-quality** | sonnet | `.claude/agents/review-quality.md` | 代码质量：死代码、重复、命名、圈复杂度 | 同上 |

---

## 3. Complete Development Logic Chain

### 3.1 End-to-End Flow

```
用户下达目标
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  Supervisor (opus)                                  │
│  读取 objective.md → iteration.md → review_tracker  │
│  评估状态 → 选择最高优先级任务                         │
│                                                     │
│  任务分类:                                           │
│  ┌──────────────┬───────────────────────┐           │
│  │ 简单 (≤1文件  │ 复杂 (跨文件)          │           │
│  │  ≤20行)      │                       │           │
│  │              │ 调用 Codex Developer   │           │
│  │ Supervisor   │ (两阶段流程)           │           │
│  │ 直接在 main  │                       │           │
│  │ 上修改       │ 阶段1: read-only 分析  │           │
│  │              │ 阶段2: main 修复       │           │
│  └──────┬───────┴───────────┬───────────┘           │
│         │                   │                       │
│         ▼                   ▼                       │
│  commit on main    Codex 直接在 main 修复             │
│                    + 跑测试 → 返回结果                │
│                         │                           │
│                         ▼                           │
│                ┌── Supervisor 审核 ──┐               │
│                │ 1. git diff 检查修改                │
│                │ 2. pytest tests/ -v                 │
│                │    ├─ PASS → git add + commit       │
│                │    └─ FAIL → codex-reply 继续迭代   │
│                │ 3. 更新 iteration + tracker         │
│                └────────────────────┘               │
│                                                     │
│  (可选) spawn Review-Coord 触发审查                   │
└─────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  Review-Coord (opus) — 持续守护进程                   │
│                                                     │
│  事件循环:                                           │
│  ┌─ 检测新 commit?                                  │
│  │  YES → 增量审查 (变更文件)                         │
│  │  NO  → 全量深度审查 (下一模块, 共 10 模块)          │
│  │                                                  │
│  ├─ 并行 spawn 7 个专项 Agent (D1-D7)               │
│  │  ┌─────────────────────────────────────────┐     │
│  │  │ D1 数值 │ D2 静默 │ D3 安全 │ D4 契约  │     │
│  │  │ D5 边界 │ D6 测试 │ D7 质量 │          │     │
│  │  └─────────────────────────────────────────┘     │
│  │                                                  │
│  ├─ 汇聚结果 → 去重 → 按严重性排序                    │
│  ├─ 写入 review_tracker.md                          │
│  ├─ 追加 iteration.md 审查摘要                       │
│  └─ 智能休眠 → 继续循环                              │
└─────────────────────────────────────────────────────┘
     │
     ▼ (review 发现问题)
┌─────────────────────────────────────────────────────┐
│  Supervisor 处理审查结果                              │
│  CRITICAL → 调用 Codex Developer 立即修复或自己修     │
│  HIGH     → 加入当前 Phase 修复计划                   │
│  MED/LOW  → 记录，Wait 模式下处理                     │
└─────────────────────────────────────────────────────┘
```

### 3.2 Codex Developer 调用流程

```
Supervisor 选择 bug 修复
  │
  ├── 阶段 1: 讨论（read-only，安全）
  │   → mcp__codex__codex(prompt="分析此 bug...", sandbox="read-only")
  │   → Codex 返回根因分析 + 修复策略建议
  │   → [可选] codex-reply 继续讨论细节（不限轮次）
  │   → Supervisor 评估方案，确定最终修复策略
  │
  ├── 阶段 1.5: 计划评估（read-only，必须）
  │   → codex-reply(prompt="我计划按此策略修复，请评估风险: ...")
  │   → Codex 返回风险评估 + 改进建议
  │   → Supervisor 综合判断：无风险→阶段2 / 有风险→调整 / 根本问题→回阶段1
  │
  ├── 阶段 2: 执行（danger-full-access）
  │   → mcp__codex__codex(prompt="按以下策略修复: ...", sandbox="danger-full-access")
  │   → Codex 修复代码 + 跑测试 → 返回结果
  │   → [如需] codex-reply 持续迭代（不限轮次）
  │   → Supervisor 审核 git diff + pytest
  │
  └── 落地（Supervisor 执行）
      → 通过 → git add + commit（标注 codex-assisted）
      → 追加 iteration.md + 更新 review_tracker.md

回退: Codex 失败 → Supervisor 自行修复
```

### 3.3 Supervisor 三模式状态机

| 模式 | 触发 | 行为 |
|------|------|------|
| **Execute** | 有即时/短期任务 | 编码/修复/配置/提交，调用 Codex Developer |
| **Wait** | 远程实验运行中 + 有本地填充工作 | 做 MED/LOW 修复、文档、测试补充 |
| **Monitor** | 远程实验运行中 + 无本地工作 | 定期 SSH 检查远程状态 |

---

## 4. Branch & Sandbox Isolation

### 4.1 隔离策略

```
main (稳定，始终 pytest 通过，rsync 唯一来源)
  └── Codex Developer 直接在 main 修复代码（不创建分支）
      → Supervisor 审核 git diff → 通过后在 main 上 commit
      → (Review agents: 只读，不需要分支)
```

- **Codex 直接在 main 操作**：Codex 以 `danger-full-access` 模式运行时，直接修改 main 工作目录中的文件
- **Supervisor 审核后提交**：所有 Codex 修改经 `git diff` 审核 + `pytest` 验证后才提交到 main
- **main 保护**：main 始终保持"pytest 通过"状态

### 4.2 rsync 门禁

推送代码到远程 GPU 前必须执行：

```bash
bash scripts/rsync_gate.sh          # 检查: main 分支 + clean status + pytest
bash scripts/rsync_gate.sh --skip-tests  # 紧急推送跳过测试
```

---

## 5. Data Flow — 谁读写什么

```
                    ┌─────────────────┐
                    │  objective.md   │  目标/边界/成功标准
                    │  (Supervisor R) │  (用户写, Supervisor 仅追加 Decision Log)
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐
  │ iteration.md │  │review_tracker │  │ experiment_sop   │
  │              │  │     .md       │  │     .md          │
  │ Supervisor W │  │ Supervisor W  │  │ (只读参考)        │
  │ Rev-Coord W  │  │ D1-D7 W      │  └──────────────────┘
  │              │  │ Rev-Coord W  │
  └──────────────┘  │ Rev-Coord W  │
                    └──────────────┘

W = 写入  R = 读取
```

| 文件 | Supervisor | Codex Developer | Review-Coord | D1-D7 |
|------|:---:|:---:|:---:|:---:|
| `objective.md` | R + Decision Log | — | — | — |
| `iteration.md` | R/W (Plans + Timeline) | R (只读，汇报 Supervisor 编辑) | W (审查摘要) | — |
| `review_tracker.md` | R/W (标记 [x]) | R (只读，汇报 Supervisor 编辑) | R/W (校验) | W (新发现) |
| `src/` `scripts/` `tests/` | R/W | R/W (直接在 main) | R | R |
| `configs/` | R/W | R (直接在 main) | R | R |
| `.claude/agents/*.md` | R | — | R | R |

---

## 6. Review System — 10 Modules × 7 Dimensions

### 审查覆盖矩阵

| # | 模块 | 文件 glob |
|---|------|-----------|
| 1 | src/cache | `src/cache/*.py` |
| 2 | src/quant | `src/quant/*.py` |
| 3 | src/kernels | `src/kernels/*.py` |
| 4 | src/engine | `src/engine/*.py` |
| 5 | src/misc | `src/model/*.py` + `src/server/*.py` + `src/utils/*.py` |
| 6 | scripts/eval | `scripts/eval_*.py` |
| 7 | scripts/calib+prof | `scripts/calibrate_*.py` + `scripts/profile_*.py` |
| 8 | scripts/agg+export | `scripts/aggregate_*.py` + `scripts/export_*.py` + `scripts/generate_*.py` |
| 9 | scripts/runner | `scripts/run_*.py` + `scripts/check_*.py` + `scripts/smoke_test.py` + `scripts/review_tool.py` |
| 10 | tests+configs | `tests/*.py` + `configs/*.yaml` |

### 7 审查维度

| ID | Agent | 关注点 |
|----|-------|--------|
| D1 | review-numerical | 量化误差传播、loss 语义、shape/dtype 对齐、NaN/Inf、确定性 |
| D2 | review-silent | 空 catch、不当 fallback、条件短路、静默数据丢弃、错误吞噬 |
| D3 | review-security | 注入攻击、路径穿越、反序列化、信息泄露、凭证硬编码 |
| D4 | review-contract | 稳定 API 签名、行为语义变化、跨文件配置对齐、向后兼容 |
| D5 | review-boundary | 空/零输入、极端值、dtype/device 不匹配、整数溢出、资源泄漏 |
| D6 | review-test | 测试缺口评分、回归测试、关键路径覆盖、测试质量 |
| D7 | review-quality | 死代码、重复代码、命名规范、圈复杂度、魔法数字 |

### Issue 严重性分级

| 级别 | 处理方式 |
|------|----------|
| **CRITICAL** | 阻塞 Phase 推进，Supervisor 调用 Codex Developer 或自行修复 |
| **HIGH** | 当前 Phase 必须修复 |
| **MEDIUM** | 不阻塞，Wait 模式下修复 |
| **LOW** | 记录，空闲时修复 |

---

## 7. Commands

```bash
# 测试
pytest tests/ -v

# Smoke test (需 GPU)
python scripts/smoke_test.py --save_output

# 实验 dry-run
python scripts/run_experiments.py --config configs/exp_matrix.yaml --dry_run

# 审查统计
python scripts/review_tool.py stats
python scripts/review_tool.py phase-gate    # Phase 门禁检查
python scripts/review_tool.py progress      # 修复进度

# rsync 门禁
bash scripts/rsync_gate.sh                  # 推送前检查

# 聚合结果
python scripts/aggregate_results.py --runs_dir results/<tag>/runs --tables_dir results/<tag>/tables --plots_dir results/<tag>/plots
```

---

## 8. Repo Hygiene

- **Never** `git add .` — stage files in semantic groups.
- Commit prefix: `feat:` / `fix:` / `refactor:` / `test:` / `docs:` / `chore:`
- Generated outputs → `results/<tag>/` or `artifacts/` (not committed).
- Historical materials → `development_history/archive_<YYYYMMDD>_<topic>/`.
- Timestamps: always use `date '+%Y-%m-%d %H:%M'` (never fabricate).
- **Never** push without explicit user approval.
- **Never** `rm -rf`, `git push --force`, `git reset --hard` without explicit user approval.

---

## 9. Stable Interfaces (Do Not Break)

| Interface | Signature |
|-----------|-----------|
| Engine | `Engine.generate(prompts, generation_config, kv_mode, runtime_config)` |
| KV Cache | `KVCache.append(layer_id, k, v)` / `KVCache.get_kv(layer_id)` |
| Quantizer | `quantize_symmetric()` / `dequantize_symmetric()` |
| Kernels | `src/kernels/triton_decode_attn_int8.py` / `triton_decode_attn_int4.py` |
| Calibration | JSON format with per-layer scales + per-head inv_tau |

---

## 10. Fixed Decisions

| Item | Value |
|------|-------|
| Primary model | `Qwen/Qwen2.5-1.5B-Instruct` (revision pinned) |
| Extended models | `Qwen/Qwen2.5-7B-Instruct`, `LLaMA-3.1-8B-Instruct` |
| Python | 3.12 |
| Decoding | Greedy (temp=0, top_p=1, top_k=0) |
| kv_modes | fp16, int8_baseline, int8_ours, int4_baseline, int4_fused, int4_ours, int4_ours_mixed, kivi_style |
| Statistics | Bootstrap CI + sign-flip permutation + BH-FDR (α=0.05) |
