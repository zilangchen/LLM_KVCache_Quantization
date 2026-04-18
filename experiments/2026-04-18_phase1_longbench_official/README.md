# Phase 1：官方 LongBench 评测底座（2026-04-18）

**实验目录**：`experiments/2026-04-18_phase1_longbench_official/`
**对应 Plan**：`.claude/plans/partitioned-sparking-newt.md` Phase 1（编号 1-5）
**Git tag 起点**：`phase-1-entry-point`（commit 2599ef4）

## 目的与假设

**目的**：在官方 LongBench 三任务（NarrativeQA / HotpotQA / GovReport）上建立 fixed-bit / RoleAlign 路线的评测底座，取代此前 synthetic LongBench fallback，为论文编号 11-12 章节重写提供可信证据。

**主要假设**（Gate 5 判据）：
- H1：至少 1 个量化模式相对 FP16 退化 <20%
- H2：7B 趋势与 1.5B 基本一致（跨模型泛化性）
- H3：无任何关键模式灾难性失效（>50% 退化）

**负面假设**（预期不成立但必须检验）：
- H4：sample-level eval 的显存节省（KV 压缩 ≥30%）能体现在 GPU peak mem 数字上

## 变量

| 维度 | 取值 |
|---|---|
| 模型 | `Qwen/Qwen2.5-1.5B-Instruct`、`Qwen/Qwen2.5-7B-Instruct` |
| 任务 | `narrativeqa`、`hotpotqa`、`gov_report` |
| kv_mode | `fp16`（baseline）、`int8_ours`、`kivi_style`、`int4_ours_asym`（RoleAlign） |
| 样本数 | `n=50`/组合 |
| Seed | `1234`（greedy, temp=0, top_p=1, top_k=0） |
| 序列长度 | `seq_len=4K`, `gen_len=64`（QA）/ `128`（摘要） |
| 数据源 | `--longbench_source jsonl --longbench_dataset_path /root/autodl-tmp/longbench_data/data` |

## 运行环境

- 远端：AutoDL `region-42.seetacloud.com:23129`，3×H20 GPU（各 98GB）
- PyTorch 2.8.0 + CUDA 12.8, Triton 3.4.0, Transformers 4.57.6
- Calibration：
  - `artifacts/kv_calib_kl_selected_v2.json`（INT8-ours, 1.5B）
  - `artifacts/kv_calib_rolealign_1p5b.json`（INT4-RoleAlign, 1.5B）
  - `artifacts/kv_calib_kl_qwen25_7b_int8.json`（INT8-ours, 7B）
  - `artifacts/kv_calib_rolealign_7b_v3.json`（INT4-RoleAlign, 7B）

## 关键产出

### 数据 CSV

| 文件 | 说明 |
|---|---|
| `results/phase1_summary.csv` | 1.5B v1 原始（含 ENG-045 污染的 kivi_style） |
| `results/phase1_summary_merged.csv` | **权威**：1.5B v1+v2 合并（kivi_style 来自 ENG-045-v2 补丁后重跑） |
| `results/phase1_summary_7b.csv` | 7B 4 modes × 3 tasks × n=50 |
| `results/phase1_summary_nokivi.csv` | DEPRECATED（基于错误假设剔除 kivi_style） |
| `results/phase1_gate5_decision.log` | Gate 5 判定决策记录 |
| `results/phase1_official/`、`results/phase1_official_v2/`、`results/phase1_official_7b/` | 原始 run-level CSV |

### 主表 Markdown

| 文件 | 说明 |
|---|---|
| `docs/phase1_main_table_merged.md` | **权威** 1.5B 主表 |
| `docs/phase1_main_table_7b.md` | 7B 主表 |
| `docs/phase1_main_table_v2_nokivi.md` | DEPRECATED |

### LaTeX 产出（用于论文编号 11-12）

| 文件 | 说明 |
|---|---|
| `thesis/tables/phase1_official_longbench_1p5b.tex` | 1.5B 主表 LaTeX |
| `thesis/tables/phase1_official_longbench_7b.tex` | 7B 主表 LaTeX |
| `thesis/tables/phase1_cross_model_consistency.tex` | 跨模型一致性（判据 2 数据） |
| `docs/phase1_scenario_a_latex_template.tex` | 场景 A 章节骨架（v6-stable 文本） |

## 结果摘要

### Gate 5 判定（🟢 PASS, 3/4 可判定判据）

| 判据 | 结果 |
|---|---|
| 1. 至少 1 模式 <20% 退化 | ✅ 9 combinations 退化 <20%（最大 +7.6% int8_ours/hotpotqa 是噪声正向） |
| 5. 无灾难失效 (>50%) | ✅ 所有退化 <10% |
| 4. quality-memory tradeoff | ❌ sample-level eval 下 KV 压缩淹没于模型权重，非 bug |
| 2. 7B↔1.5B 趋势一致 | ✅ 2/3 modes 一致 (kivi_style 最稳 +0.8%↔+0.9%) |
| 3. regime stability | ⏸ 隐式 PASS |
| **总评** | **3/4 PASSED ≥ 2 → 🟢 GATE PASS** |

### 1.5B 主表（merged）

| task | fp16 | int8_ours | kivi_style | int4_ours_asym |
|---|---|---|---|---|
| narrativeqa (F1) | 7.07 | 7.13 (+0.8%) | 6.93 (-1.9%) | 7.05 (-0.2%) |
| hotpotqa (F1) | 4.90 | 5.27 (+7.6%) | 4.87 (-0.7%) | 4.96 (+1.2%) |
| gov_report (ROUGE-L) | 9.21 | 9.25 (+0.4%) | 9.23 (+0.2%) | 8.83 (-4.1%) |

### 7B 主表

| task | fp16 | int8_ours | kivi_style | int4_ours_asym |
|---|---|---|---|---|
| narrativeqa (F1) | 6.90 | 6.54 (-5.3%) | 6.50 (-5.8%) | 6.48 (-6.1%) |
| hotpotqa (F1) | 4.83 | 4.78 (-1.1%) | 5.06 (+4.6%) | 4.84 (+0.2%) |
| gov_report (ROUGE-L) | 8.94 | 8.90 (-0.4%) | 8.79 (-1.6%) | 8.68 (-2.9%) |

## 诊断记录

### ENG-045 从"HIGH silent data loss"到"保守告警"的验证链

1. **触发**：kivi_style 日志刷 7056/5292/1764 次 warning（`k.shape[2]=4097 > 1, only last token appended`）
2. **第一反应（错误）**：HIGH severity，从 gate 判据剔除 kivi_style，review_tracker Phase Gate BLOCKED
3. **用户点破**：分数与 fp16 差距仅 0.7-1.9%（不是崩到随机水平）——如果真的每步丢 4096 tokens，分数应跌到接近 0
4. **修复 (ENG-045-v2)**：generate_loop.py:1246-1361 三分状态机（Case A 增量返回 / Case B 累积返回无告警 / Case C-D 真异常）
5. **验证**：ENG-045-v2 补丁后 kivi_style 重跑，分数与修前**精确一致**（小数点后 2 位匹配）
6. **根因解释**：非 fused 路径下 attention 实际用模型返回的 `outputs.past_key_values` tuple，kv_cache 对象的中间态"错了"但不影响模型实际看到的 cache

**教训**：区分真 bug vs 噪声告警——看数字稳定性，不看 warning 数量。详见 `memory/debugging-patterns.md §ENG-045-v2`。

## 复现步骤

```bash
# 1. 冒烟（确认数据源就绪）
bash scripts/phase1_smoke.sh   # 1.5B × FP16 × NarrativeQA × n=10，~20 秒

# 2. 1.5B 主实验（3 GPU 按任务并行）
CUDA_VISIBLE_DEVICES=0 bash scripts/phase1_run_task.sh narrativeqa &
CUDA_VISIBLE_DEVICES=1 bash scripts/phase1_run_task.sh hotpotqa &
CUDA_VISIBLE_DEVICES=2 bash scripts/phase1_run_task.sh gov_report &
wait   # ~15 分钟

# 3. 7B 跨模型复核
CUDA_VISIBLE_DEVICES=0 bash scripts/phase1_run_task_7b.sh narrativeqa &
CUDA_VISIBLE_DEVICES=1 bash scripts/phase1_run_task_7b.sh hotpotqa &
CUDA_VISIBLE_DEVICES=2 bash scripts/phase1_run_task_7b.sh gov_report &
wait   # ~15 分钟

# 4. 聚合 + Gate 判定
python3 scripts/aggregate_phase1_merged.py \
    --runs_dirs results/phase1_official results/phase1_official_v2 \
    --out_csv results/phase1_summary_merged.csv \
    --out_md docs/phase1_main_table_merged.md

bash scripts/phase1_gate5_run.sh   # aggregate 7B + gate check

# 5. LaTeX 导出
python3 scripts/export_phase1_latex.py \
    --summary_1p5b results/phase1_summary_merged.csv \
    --summary_7b results/phase1_summary_7b.csv \
    --out_dir thesis/tables/
```

## 结论

Gate 5 PASS 解锁 Phase 2 编号 6（Allocator MVP）。按 plan 判据分叉：
- ✅ 站得住 → 进编号 6（BAKV Top-3 vs Random-3 对比验证 attention-KL lens 是否能做决策）
- 若 Phase 2 M4 硬 Gate FAIL → 回退此 Phase 1 结果收口为 v6-stable

**论文定位**（若最终停点为编号 4-5）：
"Behavior-Aligned Diagnostics for KV Cache Quantization: An Official LongBench Validation"
贡献一：attention-KL 诊断透镜（现有）；贡献二：官方 LongBench 系统性验证（新）；贡献三：ENG-045 案例记录（新）。
