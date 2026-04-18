# Phase 2.6 Auto-K Backfill Runbook

> 用途：为 `Wave 1` 与 `Wave 4` 缺失的 auto-k 结果补齐最小 `18-run backfill`。
>
> 这不是新的探索实验，而是当前 `auto-k` 主线的结构性补缺。
> 当前默认顺序与 [docs/mainline_execution_queue.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/mainline_execution_queue.md) 保持一致：
>
> 1. 跟完 `Wave 7b`
> 2. 补 `18-run auto-k backfill`
> 3. 聚合并判读 backfill 结果
> 4. 再接 `Wave 6`

---

## 1. 为什么要补这 18 条

当前 `auto-k` 已经：

- 在 `Wave 5 (Mistral full)` 拿到首轮完整正面 empirical 支持
- 进入了后续自动链

但当前仍有两个关键已完成波次**不包含 auto-k**：

- `Wave 1 (8B extended)`
- `Wave 4 (14B sweep)`

因此最小缺口是：

- `Wave 1`: 3 policies × 3 tasks = 9 runs
- `Wave 4`: 3 policies × 3 tasks = 9 runs
- 合计：**18 runs**

---

## 2. 本次补跑的 policy 集

本次 backfill **只补**：

- `bakv_auto_cov70_max`
- `bakv_auto_cov80_max`
- `bakv_auto_cov90_max`

不重跑：

- `bakv_k*`
- `heuristic_k*`
- `uniform_*`
- `random*`

---

## 3. 18-run matrix

### 3.1 Wave 1 (8B)

#### `narrativeqa`

- `phase2c2b_8b_int4mixedkv_bakv_auto_cov70_max_narrativeqa_n50`
- `phase2c2b_8b_int4mixedkv_bakv_auto_cov80_max_narrativeqa_n50`
- `phase2c2b_8b_int4mixedkv_bakv_auto_cov90_max_narrativeqa_n50`

#### `hotpotqa`

- `phase2c2b_8b_int4mixedkv_bakv_auto_cov70_max_hotpotqa_n50`
- `phase2c2b_8b_int4mixedkv_bakv_auto_cov80_max_hotpotqa_n50`
- `phase2c2b_8b_int4mixedkv_bakv_auto_cov90_max_hotpotqa_n50`

#### `gov_report`

- `phase2c2b_8b_int4mixedkv_bakv_auto_cov70_max_gov_report_n50`
- `phase2c2b_8b_int4mixedkv_bakv_auto_cov80_max_gov_report_n50`
- `phase2c2b_8b_int4mixedkv_bakv_auto_cov90_max_gov_report_n50`

### 3.2 Wave 4 (14B)

#### `narrativeqa`

- `phase2c3_14b_int4mixedkv_bakv_auto_cov70_max_narrativeqa_n50`
- `phase2c3_14b_int4mixedkv_bakv_auto_cov80_max_narrativeqa_n50`
- `phase2c3_14b_int4mixedkv_bakv_auto_cov90_max_narrativeqa_n50`

#### `hotpotqa`

- `phase2c3_14b_int4mixedkv_bakv_auto_cov70_max_hotpotqa_n50`
- `phase2c3_14b_int4mixedkv_bakv_auto_cov80_max_hotpotqa_n50`
- `phase2c3_14b_int4mixedkv_bakv_auto_cov90_max_hotpotqa_n50`

#### `gov_report`

- `phase2c3_14b_int4mixedkv_bakv_auto_cov70_max_gov_report_n50`
- `phase2c3_14b_int4mixedkv_bakv_auto_cov80_max_gov_report_n50`
- `phase2c3_14b_int4mixedkv_bakv_auto_cov90_max_gov_report_n50`

---

## 4. 脚本入口

### 4.1 task-level runner

- [scripts/phase2_backfill_wave1_autok.sh](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/phase2_backfill_wave1_autok.sh)
- [scripts/phase2_backfill_wave4_autok.sh](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/phase2_backfill_wave4_autok.sh)

这两个 runner：

- 只跑 3 个 auto-k policy
- 复用既有 run_name / out_dir / model_id / seed
- 在结束时按 `run_name` 精确核验 profile/task rows，不会把旧整波结果误计入 gate

### 4.2 launcher

- [scripts/phase2_backfill_autok_launcher.sh](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/scripts/phase2_backfill_autok_launcher.sh)

launcher 默认只打印命令，不直接启动。

---

## 5. 推荐执行顺序

### Step 1：在远端预览命令

```bash
bash scripts/phase2_backfill_autok_launcher.sh --wave all
```

### Step 2：先启动 Wave 1

```bash
bash scripts/phase2_backfill_autok_launcher.sh --wave wave1 --run-now
```

### Step 3：确认 Wave 1 三个 task 完成

```bash
tmux ls
tmux capture-pane -pt autok_backfill_wave1_narrativeqa | tail -n 20
tmux capture-pane -pt autok_backfill_wave1_hotpotqa | tail -n 20
tmux capture-pane -pt autok_backfill_wave1_gov_report | tail -n 20
```

预期：三个 pane 最后都出现 `GATE PASS`。

### Step 4：再启动 Wave 4

```bash
bash scripts/phase2_backfill_autok_launcher.sh --wave wave4 --run-now
```

### Step 5：确认 Wave 4 三个 task 完成

```bash
tmux capture-pane -pt autok_backfill_wave4_narrativeqa | tail -n 20
tmux capture-pane -pt autok_backfill_wave4_hotpotqa | tail -n 20
tmux capture-pane -pt autok_backfill_wave4_gov_report | tail -n 20
```

---

## 6. 为什么不建议 `--wave all --run-now`

因为：

- `Wave 1` 需要 3 张 GPU
- `Wave 4` 也需要 3 张 GPU
- 如果一次性并发 6 条 lane，会直接 oversubscribe 当前 3 张卡

因此默认策略是：

> **先补完 `Wave 1`，再补 `Wave 4`。**

---

## 7. 最小验证

### 7.1 远端脚本级验证

```bash
bash -n scripts/phase2_backfill_wave1_autok.sh
bash -n scripts/phase2_backfill_wave4_autok.sh
bash -n scripts/phase2_backfill_autok_launcher.sh
```

### 7.2 结果级验证

三个 runner 结束时会各自输出：

- `Traceback/RT error = 0`
- `Head mismatch = 0`
- `profile rows found = 3`
- `task rows found = 3`
- `GATE PASS`

### 7.3 全局完成判据

当下面两组都完成时，说明 `18-run backfill` 已补齐：

- `Wave 1` 三个 task 的 auto-k backfill 全部 `GATE PASS`
- `Wave 4` 三个 task 的 auto-k backfill 全部 `GATE PASS`

---

## 8. 补跑完成后立刻要做的事

1. 聚合 `Wave 1` 新增 9 条 auto-k 结果
2. 聚合 `Wave 4` 新增 9 条 auto-k 结果
3. 回答三个问题：
   - `auto-k` 在 8B 上相对 `fixed best-k / heuristic` 的位置是什么
   - `auto-k` 在 14B 上是否继续成立
   - `auto-k` 的价值是跨 family 扩张，还是仍主要依赖 Mistral 支持
4. 更新：
   - [docs/thesis_upgrade_live_plan.md](/Users/chenzilang/Desktop/LLM_KVCache_Quantization/docs/thesis_upgrade_live_plan.md)
   - 对应 readout 文档

---

## 9. 当前边界

- 本次 backfill 不进入 `Wave 6`
- 不重跑旧 policy
- 不修改 allocator 核心逻辑
- 不把结果直接写进 thesis 正文
