# 论文写作前置清单（Final Thesis Plus）

> 目的：在正式写论文前，确保“图表是否齐全、口径是否一致、复现是否可审计”。
> 本清单对应 `results/final_thesis_plus_*` 目录。

## 1) 必需图（主文）

### 性能与显存
- `plots/latency_tpot_vs_seq.png`
- `plots/memory_kv_cache_vs_seq.png`
- `plots/memory_peak_vs_seq.png`

### 质量
- `plots/needle_pass_rate_vs_context.png`
- `plots/ppl_vs_tokens.png`

### 并发/吞吐
- `plots/throughput_tok_per_s_vs_batch.png`
- `plots/throughput_tok_per_s_per_seq_vs_batch.png`
- `plots/prefill_tok_per_s_vs_batch.png`

## 2) 建议图（附录/答辩）

- `plots/needle_exact_match_vs_context.png`
- `plots/latency_tpot_gain_vs_fp16.png`
- `plots/memory_peak_vs_batch.png`
- `plots/memory_kv_cache_vs_batch.png`
- `plots/needle_curve_depth_ctx4096.png`
- `plots/needle_curve_depth_ctx8192.png`
- `plots/needle_curve_depth_ctx16384.png`
- `plots/needle_curve_depth_ctx32704.png`

## 3) 必需表（主文）

- `tables/latency_summary.csv`
- `tables/memory_summary.csv`
- `tables/needle_summary.csv`
- `tables/ppl_summary.csv`
- `tables/throughput_by_batch.csv`
- `tables/thesis_main_claims_32k.csv`
- `tables/execution_coverage.csv`
- `tables/failure_registry.csv`

## 4) 建议表（附录/统计学）

- `tables/significance_summary.csv`
- `tables/significance_coverage.csv`
- `tables/significance_pairs.csv`
- `tables/relative_gain_summary.csv`
- `tables/needle_curve_by_depth.csv`
- `tables/latency_tpot_gain_vs_fp16.csv`

## 5) LaTeX 直引（论文）

- `latex_tables/all_tables.tex`
- `latex_tables/main_claims_32k.tex`
- `latex_tables/relative_gain_summary.tex`

## 6) 论文结论报告（Week-3，建议主文直接引用）

- `reports/claim_validation.csv`
- `reports/statistical_decision_summary.csv`
- `reports/reproducibility_gate.csv`
- `reports/paper_ready_summary.md`

## 7) 可审计证据（必须）

- `gates/gate0_smoke_test.log`
- `gates/gate1_dry_run.log`
- `gates/gate2_triton_unittest.log`
- `gates/gate3_verify_int8_fused.log`
- `gates/gate3_verify_int8_ours.log`
- （若含 INT4）`gates/gate3_verify_int4_fused.log`、`gates/gate3_verify_int4_ours.log`

## 8) 口径一致性额外检查（Phase5v2）
- [ ] 旧 Phase5 中包含 `eval_longbench` / `eval_ruler` 的运行已标记 legacy，且未参与新聚合
- [ ] 新聚合只读取 `results/phase5v2/runs` 与 `results/phase5v2/logs`
- [ ] quality 运行总数 = `107 × 5 = 535`
- [ ] throughput 运行总数 = `113 × 5 = 565`
- [ ] LongBench 图 y 轴标签为 `official-metric macro`（非 `macro F1`）

## 9) 论文披露检查（KIVI 对照）
- [ ] Methods 明确写出：KIVI-style INT4 当前未 bit-packing（int8 容器存储）
- [ ] Methods 明确写出：KIVI-style 不使用 `inv_tau` 温度校正
- [ ] Systems 明确写出：KIVI-style decode 固定 `torch_ref`，INT8-ours 可用 `triton_fused`
- [ ] C11 结论文本明确限定为 Qwen-7B / LLaMA-3.1-8B 两模型

## 10) 一键自检命令（生成后执行）

```bash
cd /root/LLM_KVCache_Quantization
BASE_DIR="results/final_thesis_plus_YYYYMMDD_HHMMSS"

python - <<'PY'
from pathlib import Path
base = Path("results/final_thesis_plus_YYYYMMDD_HHMMSS")
required = [
    "tables/latency_summary.csv",
    "tables/memory_summary.csv",
    "tables/needle_summary.csv",
    "tables/ppl_summary.csv",
    "tables/throughput_by_batch.csv",
    "tables/thesis_main_claims_32k.csv",
    "plots/latency_tpot_vs_seq.png",
    "plots/memory_kv_cache_vs_seq.png",
    "plots/needle_pass_rate_vs_context.png",
    "plots/ppl_vs_tokens.png",
    "plots/throughput_tok_per_s_vs_batch.png",
    "latex_tables/all_tables.tex",
    "gates/gate0_smoke_test.log",
    "gates/gate1_dry_run.log",
    "gates/gate2_triton_unittest.log",
]
missing = [p for p in required if not (base / p).exists()]
print("MISSING:", missing if missing else "None")
PY
```
