# Phase 1 官方 LongBench 主表（Qwen2.5-1.5B-Instruct）

| task | metric | fp16 | int8_ours | kivi_style | int4_ours_asym |
|---|---|---|---|---|---|
| gov_report | rouge_l | 8.94 | 8.90 | 8.79 | 8.68 |
| ↳ Δ vs fp16 |  | (基线) | -0.4% | -1.6% | -2.9% |
| hotpotqa | f1 | 4.83 | 4.78 | 5.06 | 4.84 |
| ↳ Δ vs fp16 |  | (基线) | -1.1% | +4.6% | +0.2% |
| narrativeqa | f1 | 6.90 | 6.54 | 6.50 | 6.48 |
| ↳ Δ vs fp16 |  | (基线) | -5.3% | -5.8% | -6.1% |
