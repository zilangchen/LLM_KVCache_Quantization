# 最终结果总结（Final Thesis）

> 注：数据已更新至 Phase 5v2+6 合并结果（2136 dirs，3 模型）。完整 CSV 见 results/emnlp_final_raw/tables/。

## 范围与口径（锁定）
- 主线：`fp16 / int8_baseline / int8_ours`
- 扩展：`int4_fused / int4_ours`（冲优探索，不纳入主结论）
- 模型：`Qwen/Qwen2.5-1.5B-Instruct@989aa7980e4cf806f80c7fef2b1adb7bc71aa306`
- 硬件：NVIDIA H20（96GB）
- 解码：greedy（`temperature=0, top_p=1, top_k=0`）
- 口径修订：PR-2 之后，旧 Phase5 中含 `eval_longbench` / `eval_ruler` 的结果一律视为 **legacy**
  （不进入新聚合，不用于论文主表）

## 最终验收目录（统一引用）
- 远端：`/root/LLM_KVCache_Quantization/results/emnlp_final_raw/`
- 本地（同步后）：`results/emnlp_final_raw/`
- 关键子目录：`tables/`、`plots/`、`latex_tables/`、`gates/`、`env/`、`runs/`、`logs/`

## 硬闸门（可审计）
日志目录：`/root/LLM_KVCache_Quantization/results/emnlp_final_raw/gates/`
- Gate-0：`gate0_smoke_test.log` PASS
- Gate-1：`gate1_dry_run.log` PASS
- Gate-2：`gate2_triton_unittest.log` PASS
- Gate-3：`gate3_verify_int8_fused.log`、`gate3_verify_int8_ours.log`、`gate3_verify_int4_fused.log`、`gate3_verify_int4_ours.log` 均 PASS

## 主线结论（32K，论文可引用）
来源：`/root/LLM_KVCache_Quantization/results/emnlp_final_raw/tables/thesis_main_claims_32k.csv`
- `fp16`：TPOT `30.91ms`，KV 常驻 `896MB`，Needle `100%`，PPL `9.4872`
- `int8_baseline`：TPOT `50.29ms`，KV 常驻 `504MB`，Needle `100%`，PPL `9.4912`
- `int8_ours`：TPOT `39.96ms`，KV 常驻 `504MB`，Needle `100%`，PPL `9.5085`
- 结论：`int8_ours` 相比 `int8_baseline` 在质量基本持平前提下，32K TPOT 改善约 **20.5%**（`(50.29-39.96)/50.29`）。

## 吞吐与容量上限（batch 扩展）
来源：`/root/LLM_KVCache_Quantization/results/emnlp_final_raw/tables/throughput_by_batch.csv`
- 设置：`seq_len=8192, gen_len=128, batch ∈ {1,2,4,8,16,24,32}`
- 代表点（batch=16，总 tok/s）：
  - `fp16`: `350.33`
  - `int8_baseline`: `200.04`
  - `int8_ours`: `460.90`
- 当前已知容量缺口：`int8_baseline@batch=32` OOM（见 `logs/int8_baseline_throughput_8k_b32_.../profile_latency.log`）
- 聚合脚本已新增容量上限摘要：`throughput_capacity_limits.csv`，并在 batch 曲线中标注容量虚线与 OOM/MISS 点。

## INT4 扩展现状（如实披露）
来源：`thesis_main_claims_32k.csv`
- `int4_fused` 与 `int4_ours` 在 32K Needle 为 `0%`，PPL 分别约 `161.83` / `23.41`
- 结论：INT4 路径当前不满足论文主线质量门槛，应作为“扩展尝试 + 失败分析”而非主结论。
- KIVI 披露：KIVI-style INT4 当前为 int8 容器存储（未 bit-packing），内存对比需附注说明。

## Phase5v2 重启计划（并行执行）
- 新目录：`results/phase5v2/`
- 新 tag：`phase5v2_<model>_s<seed>`
- 调度：quality 三模型并行（1.5B/7B/8B），throughput 串行独占 GPU
- 聚合：
  `python3 scripts/aggregate_results.py --runs_dir ${BASE_DIR}/runs --logs_dir ${BASE_DIR}/logs --tables_dir ${BASE_DIR}/tables --plots_dir ${BASE_DIR}/plots --strict`

## 论文引用建议
- 主图目录：`/root/LLM_KVCache_Quantization/results/emnlp_final_raw/plots/`
  - `latency_tpot_vs_seq.png`
  - `memory_kv_cache_vs_seq.png`
  - `needle_pass_rate_vs_context.png`
  - `ppl_vs_tokens.png`
  - `throughput_tok_per_s_vs_batch.png`
- 表格目录：`/root/LLM_KVCache_Quantization/results/emnlp_final_raw/latex_tables/all_tables.tex`
