# 最终结果总结（Final Thesis）

## 范围与口径（锁定）
- 模式：`fp16 / int8_baseline / int8_ours`
- 模型：`Qwen/Qwen2.5-1.5B-Instruct@989aa7980e4cf806f80c7fef2b1adb7bc71aa306`
- 硬件：NVIDIA H20 (96GB)
- 解码口径：greedy（temperature=0, top_p=1, top_k=0）

## 本次论文验收“最终目录”（统一引用）
- `results/final_thesis_20260214_094156/`
  - `tables/`：聚合表（CSV）
  - `plots/`：论文主图（PNG）
  - `latex_tables/`：论文可直接引用的 LaTeX 表（由 `scripts/export_tables_latex.py` 生成）
  - `gates/`：四闸门日志（可审计证据）
  - `env/`：环境冻结（`versions.txt` / `requirements_freeze.txt`）+ git 状态（含未提交 patch）
  - `runs/`：每个 run 的原始输出（CSV + config_snapshot）
  - `logs/`：每个 run 的任务日志 + `_pipeline.log`

## 硬闸门（Gates，可审计）
日志统一落盘在：`results/final_thesis_20260214_094156/gates/`
- Gate-0 `scripts/smoke_test.py`：PASS（`gate0_smoke_test.log`）
- Gate-1 `scripts/run_experiments.py --dry_run`：PASS（`gate1_dry_run.log`）
- Gate-2 `tests/test_triton_kernel.py`（含 GQA）：PASS（`gate2_triton_unittest.log`）
- Gate-3 `scripts/verify_fused_decode.py`：PASS（`KV_FUSED_DEBUG=1` 可证明 Triton 被真实调用）
  - `int8_fused`：`max_abs_diff=0.080078`, `mean_abs_diff=0.014450`, `top1_match=True`
  - `int8_ours`（`kv_calib_kl_selected_v3_quick.json`, `--no_use_attn_temperature --adaptive_static_scales`）：`max_abs_diff=0.121094`, `mean_abs_diff=0.019974`, `top1_match=True`

## 当前主线配置（论文对照用）
- `int8_ours` 校准文件：`artifacts/kv_calib_kl_selected_v3_quick.json`
- 量化：`group_size=16`，`clip_percentile=99.5`
- 温度：`use_attn_temperature=false`（温度作为 ablation 保留，不进入主线推荐配置）
- 标定尺度：`use_static_scales=true` + `adaptive_static_scales=true`（静态标定 + 运行时安全护栏）
- decode(q_len=1)：`decode_attn_impl=triton_fused`

## 质量（Needle + PPL）

### Needle（长上下文稳定性）
- 评测点：`seq_len ∈ {4096, 8192, 16384, 32704}`
- 评测设置：`seeds={1234,1235,1236}`，`num_depths=20`，短上下文 `depth_batch=2`，32K `depth_batch=1`
- 结果：三种模式在四个上下文长度上 **全部 100%**（见 `results/final_thesis_20260214_094156/tables/needle_summary.csv`）

### PPL（kv_cache 流式口径，chunk 加速）
> 说明：`ppl_mode=kv_cache` 会真实走自定义 KV cache（含量化/反量化），是更贴近 decode-like 的“流式”口径；为减少 Python 开销，启用 `chunk_size=128`。

- 评测设置：`max_length=1024, stride=512, chunk_size=128, max_samples=64`
- `tokens_evaluated=65535`
- 结果（见 `results/final_thesis_20260214_094156/tables/ppl_summary.csv`）：
  - `fp16`: `9.4872`
  - `int8_baseline`: `9.4912`
  - `int8_ours`: `9.5085`

## 性能与显存（关键结论）

### 32K 长上下文（`seq_len=32704, gen_len=64, batch=1, warmup=2, runs=3`）
来源：`results/final_thesis_20260214_094156/tables/latency_summary.csv` 与 `results/final_thesis_20260214_094156/tables/memory_summary.csv`
- TPOT（ms/token，越低越好）：
  - `fp16`: `30.88`
  - `int8_baseline`: `50.10`
  - `int8_ours`: `39.03`（相对 baseline：约 **-22%**）
- KV cache 常驻内存（MB，越低越好）：
  - `fp16`: `896`
  - `int8_baseline`: `504`
  - `int8_ours`: `504`（相对 fp16：约 **-43.8%**）
- 峰值显存（NVML peak, MB）：三者接近（权重/激活/临时张量主导峰值）；**KV 常驻内存曲线**更能反映“cache 省显存”的真实收益。

## 吞吐（系统分析补充：batch 扩展）
来源：`results/final_thesis_20260214_094156/tables/throughput_by_batch.csv`
- 设置：`seq_len=8192, gen_len=128, batch ∈ {1,2,4,8,16}`
- 代表点（batch=16，总 tok/s）：
  - `fp16`: `350.52 tok/s`
  - `int8_baseline`: `199.41 tok/s`
  - `int8_ours`: `441.97 tok/s`

## 论文引用建议（最小集合）
- 主图（PNG）：`results/final_thesis_20260214_094156/plots/`
  - `latency_tpot_vs_seq.png`
  - `memory_kv_cache_vs_seq.png`
  - `needle_pass_rate_vs_context.png`
  - `ppl_vs_tokens.png`
  - `throughput_tok_per_s_vs_batch.png`
- 表格（LaTeX）：`results/final_thesis_20260214_094156/latex_tables/all_tables.tex`
