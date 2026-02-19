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

## 4) 建议表（附录/统计学）

- `tables/significance_summary.csv`
- `tables/relative_gain_summary.csv`
- `tables/needle_curve_by_depth.csv`
- `tables/latency_tpot_gain_vs_fp16.csv`

## 5) LaTeX 直引（论文）

- `latex_tables/all_tables.tex`
- `latex_tables/main_claims_32k.tex`
- `latex_tables/relative_gain_summary.tex`

## 6) 可审计证据（必须）

- `gates/gate0_smoke_test.log`
- `gates/gate1_dry_run.log`
- `gates/gate2_triton_unittest.log`
- `gates/gate3_verify_int8_fused.log`
- `gates/gate3_verify_int8_ours.log`
- （若含 INT4）`gates/gate3_verify_int4_fused.log`、`gates/gate3_verify_int4_ours.log`

## 7) 一键自检命令（生成后执行）

```bash
cd /root/autodl-tmp/LLM_KVCache_Quantization
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
