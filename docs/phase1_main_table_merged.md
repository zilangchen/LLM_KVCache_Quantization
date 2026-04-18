# Phase 1 官方 LongBench 主表（Qwen2.5-1.5B, ENG-045-v2 修后合并）

数据源: v1 `results/phase1_official` (fp16/int8_ours/int4_ours_asym) + v2 `results/phase1_official_v2` (kivi_style 重跑)

| task | metric | fp16 | int8_ours | kivi_style | int4_ours_asym | source (kivi_style) |
|---|---|---|---|---|---|---|
| gov_report | rouge_l | 9.21 | 9.25 | 9.23 | 8.83 | phase1_official_v2 |
| ↳ Δ vs fp16 |  | (基线) | +0.4% | +0.2% | -4.1% |  |
| hotpotqa | f1 | 4.90 | 5.27 | 4.87 | 4.96 | phase1_official_v2 |
| ↳ Δ vs fp16 |  | (基线) | +7.6% | -0.7% | +1.2% |  |
| narrativeqa | f1 | 7.07 | 7.13 | 6.93 | 7.05 | phase1_official_v2 |
| ↳ Δ vs fp16 |  | (基线) | +0.8% | -1.9% | -0.2% |  |
