# 使用指南：KV Cache 量化实验管线

## 项目概述

本项目是面向高效推理的大语言模型 KV Cache 量化研究管线，基于 `Qwen/Qwen2.5-1.5B-Instruct` 模型，实现 KV Cache 的 INT8/INT4 量化。核心技术包括：

- **KL 行为对齐校准** + **per-head temperature**：提升长上下文量化稳定性
- **Triton 融合量化 Attention Kernel**：decode 阶段（q_len=1）的高性能 fused kernel
- **四维评测**：显存 / 吞吐延迟 / 质量（PPL） / 长上下文稳定性（Needle）

## 固定约束

- 模型：`Qwen/Qwen2.5-1.5B-Instruct`（revision pin: `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`）
- Python：3.12（以 AutoDL 镜像为准）
- 评测：以 `configs/exp_matrix.yaml` 为唯一实验入口

## 环境准备

### 依赖安装

```bash
pip install -r requirements.txt
```

### 缓存配置（推荐写入 `.bashrc`）

```bash
export HF_HOME=/root/autodl-tmp/hf_cache
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/hub
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets
export TRITON_CACHE_DIR=/root/autodl-tmp/triton_cache

# 模型/数据缓存齐全后开启离线模式
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
```

### 冻结环境（复现基线）

```bash
python scripts/collect_env.py
```

## 快速开始

### 1. Smoke Test（最小验证）

```bash
python scripts/smoke_test.py --save_output
```

确保模型能正常加载并生成文本，无报错即通过。

### 2. 四个硬闸门（Gates）

在跑正式实验前必须通过：

| 闸门 | 命令 | 说明 |
|------|------|------|
| Gate-0 | `python scripts/smoke_test.py --save_output` | 最小生成 |
| Gate-1 | `python scripts/run_experiments.py --config configs/exp_matrix.yaml --dry_run` | 矩阵 dry-run |
| Gate-2 | `python -m unittest tests/test_triton_kernel.py` | Triton 单测 |
| Gate-3 | `KV_FUSED_DEBUG=1 python scripts/verify_fused_decode.py --kv_mode int8_fused` | Fused 正确性 |

所有闸门返回退出码 0 即为通过。

### 3. 一键全量复现（推荐）

```bash
bash scripts/run_final_thesis_plus.sh  <!-- legacy: 当前使用 dispatch_phase5v2_*.sh + dispatch_phase6_core.sh -->
```

自动完成：闸门检查 → 主线实验 → batch 扩展 → 聚合出表出图 → LaTeX 导出。

## 分步操作

### 校准（Calibration）

`int8_ours` / `int4_ours` 模式需要先运行 KL 校准生成校准文件：

**INT8 校准：**
```bash
python scripts/calibrate_behavior.py \
  --search \
  --samples 16 \
  --seq_len 8192 \
  --calib_out artifacts/kv_calib_kl_selected_v3_quick.json
```

**INT4 校准：**
```bash
python scripts/calibrate_behavior.py \
  --quant_bits 4 \
  --search \
  --samples 32 \
  --seq_len 8192 \
  --search_group_sizes 8,16,32,64 \
  --search_clip_percentiles 99.0,99.5,99.9,100.0 \
  --search_outlier_ratios 0,0.0025,0.005,0.01 \
  --calib_out artifacts/kv_calib_kl_int4_selected.json
```

校准会自动搜索每层最优的 `group_size`、`clip_percentile` 等超参。

### 运行实验矩阵

唯一入口：`scripts/run_experiments.py` + `configs/exp_matrix.yaml`

```bash
python scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks <任务列表> \
  --run_names <实验名列表> \
  --out_dir results/<run_tag>/runs \
  --logs_dir results/<run_tag>/logs
```

**支持的任务类型：**

| 任务 | 说明 |
|------|------|
| `profile_latency` | 测量 TTFT（首 token 延迟）和 TPOT（每 token 延迟） |
| `profile_memory` | 测量显存占用（峰值 + KV Cache 部分） |
| `eval_ppl` | WikiText-2 困惑度评测 |
| `eval_needle` | Needle-in-a-Haystack 长上下文检索测试 |

**支持的 KV 模式：**

| 模式 | 量化位宽 | 校准策略 | Decode 实现 | 说明 |
|------|---------|----------|------------|------|
| `fp16` | 16 | 无 | torch_ref | 基线，无量化 |
| `int8_baseline` | 8 | percentile | torch_ref | INT8 percentile 量化基线 |
| `int8_ours` | 8 | kl_attn | triton_fused | 本文方法：KL 校准 + fused decode |
| `int4_baseline` | 4 | percentile | torch_ref | INT4 percentile 量化基线 |
| `int4_fused` | 4 | percentile | triton_fused | INT4 + Triton fused decode |
| `int4_ours` | 4 | kl_attn | triton_fused | INT4 本文方法 |

**常用实验参数：**

| 参数 | 说明 |
|------|------|
| `--seeds 1234,1235,1236` | 多 seed 运行（支持统计显著性检验） |
| `--latency_warmup 2` | 延迟测量预热轮数 |
| `--latency_runs 3` | 延迟测量正式轮数 |
| `--ppl_mode kv_cache` | PPL 评测模式（kv_cache 流式口径） |
| `--ppl_chunk_size 128` | PPL 评测 chunk 加速 |
| `--needle_num_depths 20` | Needle 测试深度点数 |
| `--needle_depth_batch 2` | Needle 测试每批深度数 |
| `--append` | 追加到已有结果目录 |
| `--dry_run` | 只生成命令不执行 |

### 聚合出表出图

```bash
python scripts/aggregate_results.py \
  --runs_dir results/<tag>/runs \
  --tables_dir results/<tag>/tables \
  --plots_dir results/<tag>/plots \
  --significance_min_pairs 3 \
  --significance_alpha 0.05 \
  --strict
```

**产出：**

表格（CSV）：
- `latency_summary.csv` — 延迟汇总
- `memory_summary.csv` — 显存汇总
- `needle_summary.csv` — Needle 测试汇总
- `ppl_summary.csv` — PPL 汇总
- `throughput_by_batch.csv` — 吞吐 vs batch size
- `significance_summary.csv` — 统计显著性检验
- `thesis_main_claims_32k.csv` — 论文主结论验证

图表（PNG）：
- `latency_tpot_vs_seq.png` — TPOT vs 序列长度
- `memory_kv_cache_vs_seq.png` — KV Cache 显存 vs 序列长度
- `needle_pass_rate_vs_context.png` — Needle 通过率 vs 上下文长度
- `ppl_vs_tokens.png` — PPL vs token 数
- `throughput_tok_per_s_vs_batch.png` — 吞吐 vs batch size

报告：
- `claim_validation.csv` — 主结论验证（PASS/FAIL/INCONCLUSIVE）
- `paper_ready_summary.md` — 论文"实验结论"草稿模板

### 导出 LaTeX 表格

```bash
python scripts/export_tables_latex.py \
  --tables_dir results/<tag>/tables \
  --out_dir results/<tag>/latex_tables
```

## 目录结构

```
├── src/                  # 核心源码
│   ├── cache/            # KV Cache 管理
│   ├── quant/            # 量化逻辑（INT8/INT4，group-wise scale）
│   ├── kernels/          # Triton 融合 kernel
│   └── engine/           # 推理引擎
├── scripts/              # 所有实验脚本入口
│   ├── run_experiments.py        # 实验 runner
│   ├── aggregate_results.py      # 聚合出表出图
│   ├── export_tables_latex.py    # LaTeX 导出
│   ├── calibrate_behavior.py     # KL 校准
│   ├── smoke_test.py             # 最小验证
│   ├── verify_fused_decode.py    # Fused decode 正确性
│   └── run_final_thesis_plus.sh  # 一键全量复现 (legacy: 当前使用 dispatch_phase5v2_*.sh + dispatch_phase6_core.sh)
├── configs/
│   └── exp_matrix.yaml   # 唯一实验配置文件
├── artifacts/            # 校准文件（JSON）
├── results/              # 实验输出
├── tests/                # 单元测试
├── docs/                 # 文档
├── experiment_sop.md     # 实验复现协议
├── iteration.md          # 迭代进度追踪
└── README.md
```

## 典型工作流示例

### 对比 FP16 vs INT8 在 8K 上下文的延迟和显存

```bash
python scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks profile_latency,profile_memory \
  --run_names fp16_kv_curve_8k,int8_baseline_curve_8k,int8_ours_curve_8k_static_v3_no_temp_adaptive_fused \
  --seeds 1234,1235,1236 \
  --out_dir results/my_test/runs

python scripts/aggregate_results.py \
  --runs_dir results/my_test/runs \
  --tables_dir results/my_test/tables \
  --plots_dir results/my_test/plots
```

### 评测长上下文（32K）Needle 表现

```bash
python scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks eval_needle \
  --run_names fp16_kv_long,int8_baseline_long_torch,int8_ours_long_static_v3_no_temp_adaptive_fused \
  --needle_num_depths 20 \
  --needle_depth_batch 1 \
  --out_dir results/my_test/runs
```
