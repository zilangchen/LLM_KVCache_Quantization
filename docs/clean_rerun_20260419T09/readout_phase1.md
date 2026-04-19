# Clean Rerun Aggregated Summary

## Step 1 Canonical Path

| Model | kv_mode | Task | Metric | Value |
|---|---|---|---|---:|
| 1p5b | `fp16` | gov_report | rouge_l | 9.2121 |
| 1p5b | `fp16` | hotpotqa | f1 | 4.8978 |
| 1p5b | `fp16` | narrativeqa | f1 | 7.0694 |
| 1p5b | `int4_ours_asym` | gov_report | rouge_l | 9.0393 |
| 1p5b | `int4_ours_asym` | hotpotqa | f1 | 5.3504 |
| 1p5b | `int4_ours_asym` | narrativeqa | f1 | 6.9851 |
| 1p5b | `int8_ours` | gov_report | rouge_l | 9.2000 |
| 1p5b | `int8_ours` | hotpotqa | f1 | 4.8754 |
| 1p5b | `int8_ours` | narrativeqa | f1 | 7.1585 |
| 1p5b | `kivi_style` | gov_report | rouge_l | 9.2315 |
| 1p5b | `kivi_style` | hotpotqa | f1 | 4.8659 |
| 1p5b | `kivi_style` | narrativeqa | f1 | 6.9350 |

## Step 2 Cross-Model Compare (Gate P2)

| Model | Policy | narrativeqa | hotpotqa | gov_report | mean |
|---|---|---:|---:|---:|---:|
| 14b | `bakv_auto_cov90_max` | 6.7967 | 5.3856 | 9.2679 | 7.1501 |
| 14b | `bakv_k7` | 6.6684 | 5.4897 | 8.9477 | 7.0353 |
| 14b | `heuristic_k7` | 6.8264 | 5.4045 | 9.0349 | 7.0886 |
| 14b | `uniform_int4_k4v4` | 7.0464 | 5.5711 | 9.0861 | 7.2345 |
| 3b | `bakv_auto_cov80_max` | 6.4780 | 4.8873 | 8.8983 | 6.7545 |
| 3b | `bakv_k1` | 7.1679 | 4.7274 | 8.8115 | 6.9023 |
| 3b | `heuristic_k1` | 3.0791 | 1.3934 | 5.9647 | 3.4791 |
| 3b | `uniform_int4_k4v4` | 4.3299 | 2.3782 | 5.7716 | 4.1599 |
| 8b | `bakv_auto_cov80_max` | 10.7415 | 7.5672 | 9.7543 | 9.3543 |
| 8b | `bakv_k11` | 11.1405 | 7.8840 | 9.5396 | 9.5214 |
| 8b | `heuristic_k11` | 10.4746 | 5.6785 | 9.4718 | 8.5416 |
| 8b | `uniform_int4_k4v4` | 10.2411 | 6.7323 | 9.2359 | 8.7364 |
| mistral7b | `bakv_auto_cov80_max` | 16.2569 | 19.0795 | 8.9555 | 14.7640 |
| mistral7b | `bakv_k3` | 15.7143 | 17.7837 | 8.6647 | 14.0542 |
| mistral7b | `heuristic_k3` | 17.1133 | 17.8386 | 8.8588 | 14.6036 |
| mistral7b | `uniform_int4_k4v4` | 15.5525 | 17.8125 | 8.7002 | 14.0217 |

