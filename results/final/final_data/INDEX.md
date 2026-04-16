# 论文数据索引（唯一权威入口）

冻结日期: 2026-04-17 | 总实验 runs: 717 (202+171+60+284)

所有路径相对于 `results/final/final_data/`。

---

## Ch4 Section 4.1 实验设置

| 论文表 | 数据目录 | 说明 |
|--------|---------|------|
| tab:decoding-params | — | 参数配置，非实验产出 |
| tab:kv-modes | int8_mainline/ | 量化模式总览 |

## Ch4 Section 4.2 校准目标 bit-width 与规模依赖

| 论文表 | 数据目录 | CSV 模式 | 说明 |
|--------|---------|---------|------|
| tab:kl-mse-bitwidth-comparison | int8_mainline/runs/ | isolation_{kl,mse}_*/ | KL vs MSE 对比 |
| tab:main-results | int8_mainline/runs/ | 各评测 profile_*.csv | INT8 主表 (1.5B 全量) |
| tab:temp-ablation | int8_mainline/runs/temp_ablation/ | profile_*.csv | 温度消融 |
| tab:b10-sensitivity | kv_ablation/runs/calib_b10_ablation/ | profile_*.csv | B10 校准消融 |
| tab:cross-model | int8_mainline/runs/cross_model/ | profile_*.csv | 跨模型泛化 |
| tab:kivi-comparison | int8_mainline/ | 对比 kivi 相关 runs | INT8 vs KIVI |
| **7B KL=MSE 趋同** | backend_comparison/runs/ppl_{kl,mse,fp16}_7b_*/ | profile_ppl*.csv | PPL=7.1121 |

## Ch4 Section 4.3 低比特失效诊断

| 论文表 | 数据目录 | CSV 模式 | 说明 |
|--------|---------|---------|------|
| tab:kv-ablation-ppl | kv_ablation/runs/kv_ablation_ppl/ | profile_ppl*.csv | 1.5B/7B/8B K/V 消融 PPL |
| tab:kv-ablation-ruler | kv_ablation/runs/kv_ablation_ruler/ | profile_ruler*.csv | K/V 消融 RULER |
| tab:kv-ablation-longbench | kv_ablation/runs/kv_ablation_longbench/ | profile_longbench*.csv | K/V 消融 LongBench |
| tab:mixedkv-cross-model | kv_ablation/runs/mixedkv/ | profile_*.csv | MixedKV 跨模型 |
| **tab:14b-kv-ablation** | backend_comparison/runs/ppl_ablation_{K*}_14b_*/ | profile_ppl*.csv | **14B K/V 消融** (新增) |

## Ch4 Section 4.4 INT4-RoleAlign 结果

| 论文表 | 数据目录 | CSV 模式 | 说明 |
|--------|---------|---------|------|
| tab:rolealign-results (1.5B/7B/8B) | int4_rolealign/runs/ppl_ours_asym_*/ | profile_ppl*.csv | PPL + Needle |
| tab:rolealign-results (14B) | backend_comparison/runs/ppl_ra_14b_*/ | profile_ppl*.csv | **14B PPL=5.04** |
| 14B Needle | backend_comparison/runs/needle_ra_14b_*/ | profile_needle*.csv | **4K-32K 100%** |
| 14B RULER | backend_comparison/runs/ruler_ra_14b_*/ | ruler_task_summary*.csv | **4K-16K 96.6-98.5%** |
| **1.5B FP16 RULER baseline** | backend_comparison/runs/ruler_fp16_1p5b_*/ | ruler_task_summary*.csv | **FP16 anchor** |
| **1.5B FI INT4 RULER** | backend_comparison/runs/ruler_fi_1p5b_*/ | ruler_task_summary*.csv | **FI 后端, ≈FP16** |
| tab:invtau-ablation | int4_rolealign/runs/ppl_ours_asym_*/ | profile_ppl*.csv | tau 消融 |
| tab:int4-tpot-cross-model | int4_rolealign/runs/prof_serial_latency_*/ | profile_latency*.csv | INT4 串行 profiling |
| tab:kivi-int4-threeway | int4_rolealign/runs/ruler_v2fix_*/ | profile_ruler*.csv | 三方 RULER 对比 |

## Ch4 Section 4.5 GQA-Aware 部署效率

| 论文表 | 数据目录 | CSV 模式 | 说明 |
|--------|---------|---------|------|
| tab:phase1-tpot | backend_comparison/runs/tpot_{fp16,torchref,kivi,triton_ra,fi}_*/ | profile_latency*.csv | Phase 1 TPOT (4 模型 × 5 后端) |
| tab:longseq-tpot-14b | backend_comparison/runs/longseq_{fp16,kivi,torchref,triton_ra}_14b_*/ | profile_latency*.csv | 14B 长序列 |
| tab:phase-boundary | backend_comparison/runs/longseq_*/ | profile_latency*.csv | 3 模型 × 4 seq |
| tab:kv-memory-sweep | backend_comparison/runs/memory_*/ | profile_memory*.csv | 内存对比 |

## 附录

| 论文表 | 数据目录 | 说明 |
|--------|---------|------|
| tab:app-7b-kl-mse | backend_comparison/runs/ppl_{kl,mse}_7b_*/ | 7B KL=MSE 趋同 |
| tab:chunksize-results | int4_rolealign/ (cs=1 压力测试) | chunk_size 鲁棒性 |

---

## ⚠️ 关键注意事项

1. **1.5B RULER "<1% gap" claim**：此比较使用 **FlashInfer 后端** (`ruler_fi_1p5b_*`)，不是 torch_ref 后端 (`ruler_ours_asym_*`)。后者因 seq_len bug 和后端差异导致数值不同。
2. **14B 所有数据**均来自 `backend_comparison/`（原 emnlp_p012_batch），不在 int4_rolealign/ 中。
3. **PPL 标准值**: 1.5B 13.7%, 7B 6.0%(散文)/6.1%(表格), 8B 2.4%, 14B 7.6%
