# 可跑矩阵（Runnable Matrix）— Phase 1 起点

**生成时间**: 2026-04-18 04:50
**对应计划**: `/Users/chenzilang/.claude/plans/partitioned-sparking-newt.md` 编号 1
**冻结起点**: `phase-1-entry-point` tag（commit 2599ef4）

本文件盘点 Phase 1（编号 2-4）**立即可用的模型 / calibration / kv_mode** 组合，
以及已知 gap 与对应处理方案。

---

## 1. eval_longbench.py 官方入口参数

经确认，`scripts/eval_longbench.py` 已原生支持官方 LongBench：

| CLI 参数 | 默认值 | Phase 1 推荐值 |
|---|---|---|
| `--longbench_source` | `synthetic` | **`hf`**（主线）/ `jsonl`（兜底）|
| `--longbench_tasks` | `""` | `narrativeqa,hotpotqa,gov_report` |
| `--longbench_dataset_repo` | `THUDM/LongBench` | 保持默认 |
| `--longbench_dataset_split` | `test` | 保持默认 |
| `--longbench_max_samples` | `32` | **`10`**（冒烟）/ **`50`**（正式）|
| `--longbench_max_new_tokens` | `64` | 按任务默认 |
| `--longbench_allow_synthetic_fallback` | `False` | 保持 False（Phase 1 不允许静默回退） |

其他关键参数：
- `--model_id`（默认 `Qwen/Qwen2.5-1.5B-Instruct`）
- `--kv_mode`、`--calib_file`、`--calib_strategy`
- `--seed`（默认 1234）、`--run_name`、`--out_dir`

---

## 2. 主模型矩阵

| 模型 | HF ID | 层数 | H_kv | Phase 1 优先级 |
|---|---|---|---|---|
| Qwen2.5-1.5B-Instruct | `Qwen/Qwen2.5-1.5B-Instruct` | 28 | 2 | ⭐ 编号 2 主目标 |
| Qwen2.5-7B-Instruct | `Qwen/Qwen2.5-7B-Instruct` | 28 | 4 | ⭐ 编号 4 路线 α |
| LLaMA-3.1-8B-Instruct | modelscope cache / HF | 32 | 8 | 🔸 Phase 2+ |
| Qwen2.5-14B-Instruct | modelscope cache / HF | 48 | 8 | 🔸 Phase 2+ |
| Mistral-7B-Instruct-v0.3 | HF | 32 | 8 | 🔸 对照模型 |

---

## 3. 稳定的 KV 模式集合（Phase 1 用）

| kv_mode | 依赖 calibration | Phase 1 使用 |
|---|---|---|
| `fp16` | 不需要 | ✅ 可直接跑 |
| `int8_ours` | 需要 INT8 KL calibration | ✅ 见下表 |
| `kivi_style` | 不需要（运行时 absmax/min） | ✅ 可直接跑 |
| `int4_ours_asym` (RoleAlign) | 需要 RoleAlign calibration | ⚠️ 1.5B 校准文件缺失（见 §5） |
| `int4_ours` (对称 INT4) | 需要 INT4 KL calibration | ✅ 兜底方案 |
| `int4_baseline` | 不需要（运行时 percentile） | 🔸 可选对照 |

---

## 4. Calibration 产物清单（当前仓库可用）

### 4.1 INT8 Mainline
| 模型 | calibration 文件 | 备注 |
|---|---|---|
| Qwen2.5-1.5B | `artifacts/kv_calib_kl_selected_v2.json` | ✅ 主线 v2（Hour 0-2 已用） |
| Qwen2.5-1.5B | `artifacts/kv_calib_kl_selected_v3_quick.json` | ✅ v3 quick（configs yaml 引用） |
| Qwen2.5-1.5B | `artifacts/kv_calib_kl_selected.json` | v1 legacy |
| Qwen2.5-7B | ❌ **缺失**（待跑 01_calibrate.sh 补） | 或用 `b10_7b_s{16/64/256}.json` 其中之一 |
| LLaMA-3.1-8B | ❌ 缺失 | Phase 2+ 再补 |

### 4.2 INT4 对称
| 模型 | calibration 文件 |
|---|---|
| Qwen2.5-1.5B | `artifacts/kv_calib_kl_int4_selected.json` ✅ |
| Qwen2.5-7B | `artifacts/calibration_postfix_v1/kv_calib_kl_7b_int4_postfix.json` ✅ |
| LLaMA-3.1-8B | `artifacts/calibration_postfix_v1/kv_calib_kl_8b_int4_postfix.json` ✅ |

### 4.3 INT4 RoleAlign（非对称）
| 模型 | calibration 文件 | 状态 |
|---|---|---|
| Qwen2.5-1.5B | `artifacts/kv_calib_rolealign_1p5b.json` | ❌ **yaml 引用但文件不存在** |
| Qwen2.5-14B | `artifacts/kv_calib_rolealign_14b_v3.json` | ✅ |
| 7B/8B | ❌ 缺失 | 见 §5 gap 处理 |

### 4.4 B10 校准灵敏度消融
| 模型 | 样本数集合 |
|---|---|
| 1.5B | s ∈ {16, 64, 256} × `kv_calib_kl_b10_1p5b_s*.json` |
| 7B | s ∈ {16, 64, 256} × `kv_calib_kl_b10_7b_s*.json` |

---

## 5. 已知 Gap 与处理方案

### Gap 1: 1.5B RoleAlign 校准文件缺失
**症状**：`configs/exp_matrix_rolealign.yaml` 引用的 `artifacts/kv_calib_rolealign_1p5b.json` 不存在。

**影响范围**：编号 2 的 `int4_ours_asym` 行跑不起来。

**处理方案**（按优先级）：
- **A. 跑 RoleAlign 校准**（推荐）：`bash results/final/final_scripts/reproduce/01_calibrate.sh`（需确认脚本生成 1.5B RoleAlign 文件）
- **B. 替代模式**：编号 2 先用 `int4_ours`（对称 INT4）替代 `int4_ours_asym`，保持 4 模式规模
- **C. 降级到 3 模式**：编号 2 只跑 `fp16 / int8_ours / kivi_style`，接受编号 2 降级

### Gap 2: 7B INT8 校准文件缺失
**症状**：`artifacts/` 下无 `kv_calib_kl_7b_int8.json` 或类似命名。

**影响范围**：编号 4 路线 α（7B 复核）的 `int8_ours` 行跑不起来。

**处理方案**：
- 用 B10 系列（`kv_calib_kl_b10_7b_s64.json`，样本 n=64）作为 7B INT8 校准
- 或跑一次 01_calibrate.sh 的 7B 分支

---

## 6. Phase 1 编号 2 命令模板（已更新为 jsonl 源）

正式编号 2（12 组合，需 GPU，远端执行）：

```bash
# 每组合 ≈ 30-60 秒 @ max_samples=50（1.5B 模型、seq 4K、jsonl 源 I/O 飞快）
for KV_MODE in fp16 int8_ours kivi_style int4_ours_asym; do
  for TASK in narrativeqa hotpotqa gov_report; do
    python3 scripts/eval_longbench.py \
        --model_id Qwen/Qwen2.5-1.5B-Instruct \
        --kv_mode $KV_MODE \
        --calib_file <依据 §4 选对应文件，fp16/kivi_style 省略> \
        --longbench_source jsonl \
        --longbench_dataset_path /root/autodl-tmp/longbench_data/data \
        --longbench_tasks $TASK \
        --longbench_max_samples 50 \
        --seed 1234 \
        --out_dir results/phase1_official/ \
        --run_name phase1_1p5b_${KV_MODE}_${TASK}_n50
  done
done
```

---

## 7. 闸门保护

**编号 1 闸门（本矩阵的作用）**：
- ✅ 冒烟通过 → 进编号 2
- ❌ 冒烟失败 → 先修脚本链路（网络 / 数据加载 / kv_mode 路由），**不得扩大实验**

**编号 5 闸门**：在编号 4 完成前，**绝不修改 `src/cache/mixed_kv_cache.py` 的 `__init__` 签名**。

---

## 8. 本地冒烟结果（2026-04-18 04:55）

由于本地 macOS 无 GPU 且未装 `triton`，无法直接跑真 LongBench。
改做**链路级冒烟**：

| 检查项 | 命令 | 结果 |
|---|---|---|
| 语法正确性 | `python3 -m py_compile scripts/eval_longbench.py` | ✅ PASS |
| argparse 加载 | `python3 scripts/eval_longbench.py --help` | ⚠️ 本地失败（triton 模块缺失），**在 GPU 环境下应可通过** |
| CSV 字段定义位置 | grep 代码 | ✅ 已定位（L1047-1091）|

**上 GPU 后真冒烟结果（2026-04-18 05:03 已通过）**：

| 指标 | 值 |
|---|---|
| 耗时 | **20 秒**（模型+数据均本地缓存）|
| Qwen2.5-1.5B FP16 NarrativeQA F1 | 7.7126（官方 metric）|
| TPOT | 24.87 ms |
| GPU 峰值显存 | 4.39 GB |
| 产出 CSV | 3 个：profile / task_summary / details |

**关键发现**：
- ❌ `--longbench_source hf` 在远端 datasets 4.5.0 + 代理失效环境下**不可用**
- ✅ **必须用** `--longbench_source jsonl --longbench_dataset_path /root/autodl-tmp/longbench_data/data`
- 本地 jsonl 已齐备：34 个文件，含 narrativeqa/hotpotqa/gov_report 等官方全集

**正确的冒烟命令**（已写入 `scripts/phase1_smoke.sh` 并提交仓库）：
```bash
python3 scripts/eval_longbench.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode fp16 \
    --longbench_source jsonl \
    --longbench_dataset_path /root/autodl-tmp/longbench_data/data \
    --longbench_tasks narrativeqa \
    --longbench_max_samples 10 \
    --seed 1234 \
    --out_dir results/phase1_smoke/ \
    --run_name smoke_1p5b_fp16_narrativeqa_n10
```

---

## 9. CSV schema 对照 Phase 1 要求

`scripts/eval_longbench.py` 输出三个 CSV：
- `profile_longbench_*.csv`（运行环境）
- `longbench_task_summary_*.csv`（**Phase 1 主表数据源**，每任务一行）
- `longbench_details_*.csv`（逐样本明细）

**`task_summary` 字段（L1047-1065）**：
```
run_id, task_name, kv_mode, seq_len, gen_len, sample_count,
exact_match_rate, contains_match_rate, f1_mean,
official_metric_name, official_metric_value,
seed, replica_id, timestamp, git_commit
```

**`summary_row` 字段（每次运行一行，L1069-1091）**：
```
run_id, model_id, run_name, benchmark, longbench_source,
kv_mode, quant_bits, clip_percentile, group_size, dtype, hardware,
seq_len, gen_len, batch,
ttft_ms, tpot_ms, tok_per_s, gpu_mem_peak_mb,
timestamp, git_commit, seed, replica_id
```

**Phase 1 要求的统一 schema 对照**：
| 要求字段 | 来源字段 | 状态 |
|---|---|---|
| `model` | `summary_row.model_id` | ✅ |
| `task` | `task_rows.task_name` | ✅ |
| `kv_mode` | 两处都有 | ✅ |
| `score` | `task_rows.official_metric_value` | ✅ |
| `metric_name` | `task_rows.official_metric_name` | ✅ |
| `n_samples` | `task_rows.sample_count` | ✅ |
| `latency_ms` | `summary_row.tpot_ms` | ✅ |
| `kv_memory_mb` | `summary_row.gpu_mem_peak_mb` 推导 | ⚠️ 需要在 aggregate 阶段单独计算（或用整段 peak mem 近似） |

**结论**：11/12 字段直接可用，`kv_memory_mb` 需要 `scripts/aggregate_phase1.py`（编号 3 新建）
做一次 `peak_mem - model_weight_mb` 的二次计算。其他字段**完全不需要改 eval 脚本**。

---

## 10. 编号 1 完成状态

| 子项 | 状态 |
|---|---|
| 冻结起点（git tag）| ✅ `thesis-v5-POSITIVE` + `phase-1-entry-point` 已推送 |
| 列出可跑矩阵 | ✅ 本文件 §1-§7 |
| 识别 gap 与处理方案 | ✅ §5 记录了 1.5B RoleAlign + 7B INT8 两个 gap |
| 本地链路级冒烟 | ✅ py_compile PASS |
| CSV schema 对齐 | ✅ §9 确认 11/12 字段兼容 |
| GPU 真冒烟 | ⏳ 待上 GPU 后跑 §8 的命令（3-5 分钟） |

**阻塞 GPU 真冒烟的唯一条件**：上 GPU 机器。完成后即可进入编号 2。
