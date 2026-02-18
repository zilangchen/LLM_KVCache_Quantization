# 最终复现实验协议（KV Cache Quantization）

> 目标：在远端 H20 环境一键复现 `fp16 / int8_baseline / int8_ours` 的质量（needle + PPL）与性能（latency + memory）曲线，并生成论文可直接引用的表格与图。

论文验收最终产物目录（本地已同步）：`results/final_thesis_20260214_094156/`（见 `docs/final_results_summary.md`）。

## 1) 环境（固定）
- 远端解释器：`/root/miniconda3/bin/python`（Python 3.12 / Torch 2.8.0 + cu128 / CUDA 12.8）
- 仓库目录：`/root/autodl-tmp/LLM_KVCache_Quantization`
- 模型：`Qwen/Qwen2.5-1.5B-Instruct`
- 模型 revision（已 pin）：`989aa7980e4cf806f80c7fef2b1adb7bc71aa306`

## 2) 缓存与离线（强烈建议）

把 HF / datasets / triton cache 都写到数据盘，并在模型/数据缓存齐全后启用离线，避免网络波动：

```bash
export HF_HOME=/root/autodl-tmp/hf_cache
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/hub
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets
export TRITON_CACHE_DIR=/root/autodl-tmp/triton_cache

# 模型与数据缓存齐全后建议开启（否则首次会报找不到）
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
```

如需首次下载模型/数据集，可临时关闭离线并启用网络加速：
```bash
unset HF_HUB_OFFLINE
unset TRANSFORMERS_OFFLINE
source /etc/network_turbo
```

## 3) 冻结环境（复现最小门槛）
```bash
cd /root/autodl-tmp/LLM_KVCache_Quantization
/root/miniconda3/bin/python scripts/collect_env.py
```

## 4) 四个硬闸门（跑出 0 退出码才能信结果）
建议把闸门输出也落盘到最终目录，答辩/验收时可直接展示。

创建最终目录（建议固定 `final_thesis_*` 前缀）：
```bash
cd /root/autodl-tmp/LLM_KVCache_Quantization
RUN_TAG="final_thesis_$(date +%Y%m%d_%H%M%S)"
BASE_DIR="results/${RUN_TAG}"
mkdir -p "${BASE_DIR}"/{runs,logs,tables,plots,latex_tables,gates,env}
echo "${BASE_DIR}"
```

冻结环境到最终目录：
```bash
cd /root/autodl-tmp/LLM_KVCache_Quantization
/root/miniconda3/bin/python scripts/collect_env.py
cp -f env/versions.txt "${BASE_DIR}/env/versions.txt"
cp -f env/requirements_freeze.txt "${BASE_DIR}/env/requirements_freeze.txt"

# 可选：记录 git 工作区（推荐，避免“commit 对不上代码”）
git rev-parse HEAD > "${BASE_DIR}/env/git_commit_full.txt"
git status --porcelain > "${BASE_DIR}/env/git_status_porcelain.txt"
git diff > "${BASE_DIR}/env/uncommitted_changes.patch" || true
```

四闸门（日志落盘到 `${BASE_DIR}/gates/`）：
```bash
cd /root/autodl-tmp/LLM_KVCache_Quantization

# Gate-0: 最小生成
/root/miniconda3/bin/python scripts/smoke_test.py --save_output --model_revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 \
  > "${BASE_DIR}/gates/gate0_smoke_test.log" 2>&1

# Gate-1: 矩阵 dry-run（检查命令生成与 kv_mode 支持）
/root/miniconda3/bin/python scripts/run_experiments.py --config configs/exp_matrix.yaml --dry_run \
  > "${BASE_DIR}/gates/gate1_dry_run.log" 2>&1

# Gate-2: Triton 单测（含 GQA）
/root/miniconda3/bin/python -m unittest tests/test_triton_kernel.py \
  > "${BASE_DIR}/gates/gate2_triton_unittest.log" 2>&1

# Gate-3: fused correctness + “确实命中 Triton”
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 KV_FUSED_DEBUG=1 \
  /root/miniconda3/bin/python scripts/verify_fused_decode.py \
  --model_revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 \
  --kv_mode int8_fused \
  > "${BASE_DIR}/gates/gate3_verify_int8_fused.log" 2>&1

HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 KV_FUSED_DEBUG=1 \
  /root/miniconda3/bin/python scripts/verify_fused_decode.py \
  --model_revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 \
  --kv_mode int8_ours \
  --calib_file artifacts/kv_calib_kl_selected_v3_quick.json \
  --no_use_attn_temperature \
  --adaptive_static_scales \
  > "${BASE_DIR}/gates/gate3_verify_int8_ours.log" 2>&1
```

## 5) 校准（`int8_ours` 必需）

默认主线校准文件：
- `artifacts/kv_calib_kl_selected_v3_quick.json`（`group_size=16`，fused 友好）

如果需要重新生成（GPU 上）：
```bash
cd /root/autodl-tmp/LLM_KVCache_Quantization
/root/miniconda3/bin/python scripts/calibrate_behavior.py \
  --search \
  --samples 16 \
  --seq_len 8192 \
  --calib_out artifacts/kv_calib_kl_selected_v3_quick.json
```

## 6) 运行 final matrix（论文验收版：同一目录完整闭环）

> 说明：本协议默认把所有输出写入 `${BASE_DIR}`，并最终用 `scripts/aggregate_results.py` 聚合到 `${BASE_DIR}/tables` 与 `${BASE_DIR}/plots`。

### (A) 性能 + 显存（batch=1 曲线 + 32K 点）
```bash
/root/miniconda3/bin/python scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks profile_latency,profile_memory \
  --run_tag "${RUN_TAG}" \
  --append \
  --run_names fp16_kv_curve_4k,fp16_kv_curve_8k,fp16_kv_curve_16k,fp16_kv_long,int8_baseline_curve_4k,int8_baseline_curve_8k,int8_baseline_curve_16k,int8_baseline_long_torch,int8_ours_curve_4k_static_v3_no_temp_adaptive_fused,int8_ours_curve_8k_static_v3_no_temp_adaptive_fused,int8_ours_curve_16k_static_v3_no_temp_adaptive_fused,int8_ours_long_static_v3_no_temp_adaptive_fused \
  --latency_warmup 2 \
  --latency_runs 3 \
  --out_dir "${BASE_DIR}/runs" \
  --logs_dir "${BASE_DIR}/logs"
```

### (B) Needle（短上下文：depth_batch=2；长上下文：depth_batch=1）
短上下文（4K/8K/16K）：
```bash
/root/miniconda3/bin/python scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks eval_needle \
  --run_tag "${RUN_TAG}" \
  --append \
  --run_names fp16_kv_curve_4k,fp16_kv_curve_8k,fp16_kv_curve_16k,int8_baseline_curve_4k,int8_baseline_curve_8k,int8_baseline_curve_16k,int8_ours_curve_4k_static_v3_no_temp_adaptive_fused,int8_ours_curve_8k_static_v3_no_temp_adaptive_fused,int8_ours_curve_16k_static_v3_no_temp_adaptive_fused \
  --seeds 1234,1235,1236 \
  --needle_num_depths 20 \
  --needle_depth_batch 2 \
  --needle_max_new_tokens 64 \
  --out_dir "${BASE_DIR}/runs" \
  --logs_dir "${BASE_DIR}/logs"
```

长上下文（32K，保守：depth_batch=1）：
```bash
/root/miniconda3/bin/python scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks eval_needle \
  --run_tag "${RUN_TAG}" \
  --append \
  --run_names fp16_kv_long,int8_baseline_long_torch,int8_ours_long_static_v3_no_temp_adaptive_fused \
  --seeds 1234,1235,1236 \
  --needle_num_depths 20 \
  --needle_max_new_tokens 64 \
  --needle_depth_batch 1 \
  --out_dir "${BASE_DIR}/runs" \
  --logs_dir "${BASE_DIR}/logs"
```

### (C) PPL（kv_cache 流式口径 + chunk 加速）
> kv_cache PPL 支持 **chunked** 加速（`--ppl_chunk_size`），会显著减少 Python 循环次数并提高 GPU 利用率。  
> - 复现实验推荐：`--ppl_chunk_size 128`  
> - 严格 token-by-token（最慢）：`--ppl_chunk_size 1`

```bash
/root/miniconda3/bin/python scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks eval_ppl \
  --run_tag "${RUN_TAG}" \
  --append \
  --run_names fp16_kv_curve_4k,int8_baseline_curve_4k,int8_ours_curve_4k_static_v3_no_temp_adaptive_fused \
  --ppl_mode kv_cache \
  --ppl_max_length 1024 \
  --ppl_stride 512 \
  --ppl_chunk_size 128 \
  --ppl_max_samples 64 \
  --out_dir "${BASE_DIR}/runs" \
  --logs_dir "${BASE_DIR}/logs"
```

### (D) Throughput vs Batch（充分利用 H20，系统分析补充）
> 这些 run 只跑 `profile_latency/profile_memory`，用于生成：
> - `tables/throughput_by_batch.csv`
> - `plots/throughput_tok_per_s_vs_batch.png`
> - `plots/memory_peak_vs_batch.png`
> - `plots/memory_kv_cache_vs_batch.png`

```bash
/root/miniconda3/bin/python scripts/run_experiments.py \
  --config configs/exp_matrix.yaml \
  --tasks profile_latency,profile_memory \
  --run_tag "${RUN_TAG}" \
  --append \
  --run_names fp16_throughput_8k_b1,fp16_throughput_8k_b2,fp16_throughput_8k_b4,fp16_throughput_8k_b8,fp16_throughput_8k_b16,int8_baseline_throughput_8k_b1,int8_baseline_throughput_8k_b2,int8_baseline_throughput_8k_b4,int8_baseline_throughput_8k_b8,int8_baseline_throughput_8k_b16,int8_ours_throughput_8k_b1,int8_ours_throughput_8k_b2,int8_ours_throughput_8k_b4,int8_ours_throughput_8k_b8,int8_ours_throughput_8k_b16 \
  --latency_warmup 2 \
  --latency_runs 3 \
  --out_dir "${BASE_DIR}/runs" \
  --logs_dir "${BASE_DIR}/logs"
```

## 7) 聚合出表出图
```bash
cd /root/autodl-tmp/LLM_KVCache_Quantization
/root/miniconda3/bin/python scripts/aggregate_results.py \
  --runs_dir "${BASE_DIR}/runs" \
  --tables_dir "${BASE_DIR}/tables" \
  --plots_dir "${BASE_DIR}/plots"
```

产出至少包括：
- tables: `latency_summary.csv`, `memory_summary.csv`, `needle_summary.csv`, `ppl_summary.csv`
- tables: `throughput_by_batch.csv`
- plots: `latency_tpot_vs_seq.png`, `memory_kv_cache_vs_seq.png`, `needle_pass_rate_vs_context.png`, `ppl_vs_tokens.png`
- plots: `throughput_tok_per_s_vs_batch.png`, `memory_peak_vs_batch.png`, `memory_kv_cache_vs_batch.png`

## 8) 导出 LaTeX 表格（论文直接引用）
```bash
cd /root/autodl-tmp/LLM_KVCache_Quantization
/root/miniconda3/bin/python scripts/export_tables_latex.py \
  --tables_dir "${BASE_DIR}/tables" \
  --out_dir "${BASE_DIR}/latex_tables"
```

## 9) 可选：fused dump（用于定点诊断）
```bash
cd /root/autodl-tmp/LLM_KVCache_Quantization
KV_FUSED_DUMP_DIR=results/fused_dumps KV_FUSED_DUMP_LAYER=0 KV_FUSED_DUMP_STEP=32704 \
  /root/miniconda3/bin/python scripts/eval_needle.py \
  --kv_mode int8_ours \
  --context_len 32704 \
  --num_depths 3 \
  --needle_max_new_tokens 64 \
  --calib_file artifacts/kv_calib_kl_selected_v3_quick.json \
  --seed 1234
```
