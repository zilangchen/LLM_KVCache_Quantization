# LongBench 实验

> **核心**：论文引用的 LongBench 数据有两个来源——synthetic（我们的合成子集）和 official v2（EVL-042 fix 后的官方子集）
> **必须明确标注**哪个字段用于哪个数字

---

## 两个数据源对比

| 数据源 | 路径前缀 | 字段 | 典型数字（INT8-ours 1.5B）|
|-------|---------|------|--------------------------|
| **Synthetic**（我们的合成版本）| `longbench_fp16_32k_*`、`longbench_ra_v3_*` | synthetic metrics | 7.98 |
| **Official v2**（EVL-042 fix）| `longbench_v2_*`、`longbench_official_*` | `longbench_score` / `longbench_contains_macro` | 7.98 / 4.92 |

**⚠️ 数据矛盾的根源**：
- 论文 ch4:312 引用 **4.92%** — 这是 `longbench_contains_macro` 字段
- 原始 CSV `longbench_score` = **7.98** — 这是 raw score
- 两者都**对**，只是不同字段

---

## Official v2 数据路径（EVL-042 fix 权威数据）

```
results/emnlp_defense_v1/runs/longbench_v2_fp16_1p5b/
├── profile_longbench_fp16_2026-04-04T03-38-11.344504.csv
├── longbench_details_fp16_2026-04-04T03-38-11.344504.csv
└── longbench_task_summary_fp16_2026-04-04T03-38-11.344504.csv

results/emnlp_defense_v1/runs/longbench_v2_int8_1p5b/
├── profile_longbench_int8_ours_2026-04-04T03-38-11.287079.csv
├── longbench_details_int8_ours_2026-04-04T03-38-11.287079.csv
└── longbench_task_summary_int8_ours_2026-04-04T03-38-11.287079.csv

results/emnlp_defense_v1/runs/longbench_v2_ra_1p5b/
├── profile_longbench_int4_ours_asym_2026-04-04T03-38-16.844869.csv
├── longbench_details_int4_ours_asym_2026-04-04T03-38-16.844869.csv
└── longbench_task_summary_int4_ours_asym_2026-04-04T03-38-16.844869.csv
```

---

## Synthetic 数据路径（历史，部分已被 v2 替代）

```
results/emnlp_defense_v1/runs/longbench_fp16_32k_1p5b/
results/emnlp_defense_v1/runs/longbench_official_fp16_1p5b/
results/emnlp_defense_v1/runs/longbench_official_int8_1p5b/
results/emnlp_defense_v1/runs/longbench_ra_v3_1p5b/
results/emnlp_defense_v1/runs/longbench_ra_v3_verify/
```

---

## Official v2 CSV 字段说明（**关键：字段语义**）

| 字段 | 含义 | 取值范围 | 论文引用哪个 |
|------|------|---------|-------------|
| `longbench_score` | 原始加权得分 | 0-100 | **主表**：ch4 table main |
| `longbench_em_macro` | Exact Match 宏平均 | 0-1 | 严格口径 |
| `longbench_contains_macro` | Contains 宏平均 | 0-1 | 宽松口径（论文 ch4:312 引 4.92%）|
| `longbench_f1_macro` | F1 宏平均 | 0-1 | 折中口径 |
| `longbench_official_macro` | 官方总分 | 0-1 | official 版本专用 |
| `longbench_task_count` | 任务数 | 16 | 覆盖范围 |
| `longbench_sample_count` | 样本数 | 512 | 统计功效 |
| `longbench_classification_match_policy` | 分类任务匹配策略 | `contains` / `exact` | 评分参数 |

---

## 核心结论

**INT8/INT4-RA ≈ FP16 ± 1pp**（在 LongBench 官方子集上）

这回应了审稿人 "synthetic LongBench 不代表官方" 的质疑——v2 的数据证明 synthetic 结论是可外推的。

---

## 数据矛盾处理

**论文需要修复**：
1. ch4:312 的 4.92% 明确标注是 `longbench_contains_macro`
2. 如果 abstract 引用 LongBench 分数，必须说明 synthetic（不是 official）

**答辩防御**：
- **Q**: "Synthetic LongBench 可信吗？"
- **A**: "我们用 `longbench_v2_*` 在官方子集上验证了结论——synthetic 和 official 两个口径都显示 INT8/INT4-RA ≈ FP16 ± 1pp。两个数据源都有完整 CSV，可复现。"

---

## 主要 CSV 字段精选（int8_ours v2 示例）

```
model_id: Qwen/Qwen2.5-1.5B-Instruct
kv_mode: int8_ours
quant_bits: 8
benchmark: longbench
longbench_score: 7.9847
longbench_task_count: 16
longbench_sample_count: 512
ttft_ms: 170.39
tpot_ms: 62.64
```
