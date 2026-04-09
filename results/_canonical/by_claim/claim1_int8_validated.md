# Claim 1：INT8 行为对齐校准有效性

> **论文位置**：`thesis/chapters/ch4_experiments.tex` Claim 1 章节
> **核心主张**：基于 attention-KL 的行为对齐校准在 INT8 下是 canonical validated instance
> **证据等级**：3 模型 × 5 seeds (n=10 验证) × 4 benchmarks

---

## 核心数据

### PPL（n=10 seeds 验证 bitwise 一致）

| 模型 | H_kv | FP16 baseline | INT8-ours | 相对降级 | 状态 |
|------|------|--------------|-----------|---------|------|
| Qwen2.5-1.5B | 2 | 9.31 | **9.34** | +0.3% | ✅ |
| Qwen2.5-7B | 4 | — | TBD from CSV | — | ✅ |
| LLaMA-3.1-8B | 8 | — | TBD from CSV | — | ✅ |

**n=10 确定性验证**：所有 5 个新 seed (s1239-s1243) 与原 5 seed (s1234-s1238) 的 PPL **bitwise 完全一致**，证实 greedy decoding 下 PPL 零方差。

### 数据路径（CSV 精确位置）

#### 1.5B FP16 PPL（n=10，5 新 seeds）
```
results/emnlp_defense_v1/runs/ppl_fp16_n10_1p5b_s1239/profile_ppl_fp16_2026-04-04T04-19-30.581193.csv
results/emnlp_defense_v1/runs/ppl_fp16_n10_1p5b_s1240/profile_ppl_fp16_2026-04-04T04-40-33.470731.csv
results/emnlp_defense_v1/runs/ppl_fp16_n10_1p5b_s1241/profile_ppl_fp16_2026-04-04T04-54-48.053154.csv
results/emnlp_defense_v1/runs/ppl_fp16_n10_1p5b_s1242/profile_ppl_fp16_2026-04-04T05-05-35.132877.csv
results/emnlp_defense_v1/runs/ppl_fp16_n10_1p5b_s1243/profile_ppl_fp16_2026-04-04T05-16-25.545241.csv
```

#### 1.5B INT8-ours PPL（n=10，5 新 seeds）
```
results/emnlp_defense_v1/runs/ppl_int8_n10_1p5b_s1239/profile_ppl_int8_ours_2026-04-04T04-05-50.536047.csv
results/emnlp_defense_v1/runs/ppl_int8_n10_1p5b_s1240/profile_ppl_int8_ours_2026-04-04T04-28-39.384152.csv
results/emnlp_defense_v1/runs/ppl_int8_n10_1p5b_s1241/profile_ppl_int8_ours_2026-04-04T04-47-10.070023.csv
results/emnlp_defense_v1/runs/ppl_int8_n10_1p5b_s1242/profile_ppl_int8_ours_2026-04-04T04-58-50.605013.csv
results/emnlp_defense_v1/runs/ppl_int8_n10_1p5b_s1243/profile_ppl_int8_ours_2026-04-04T05-09-35.737444.csv
```

#### 7B 所有 modes（15 CSVs）
```
results/emnlp_defense_v1/runs/ppl_fp16_n10_7b_s{1239..1243}/profile_ppl_fp16_*.csv
results/emnlp_defense_v1/runs/ppl_int8_n10_7b_s{1239..1243}/profile_ppl_int8_ours_*.csv
```

#### 8B 所有 modes（15 CSVs）
```
results/emnlp_defense_v1/runs/ppl_fp16_n10_8b_s{1239..1243}/profile_ppl_fp16_*.csv
results/emnlp_defense_v1/runs/ppl_int8_n10_8b_s{1239..1243}/profile_ppl_int8_ours_*.csv
```

---

## Needle 检索（3 模型 × n=10）

**关键结论**：INT8-ours 在所有模型的 Needle 得分 **=100%**（与 FP16 一致）

```
results/emnlp_defense_v1/runs/needle_int8_n10_1p5b_s{1239..1243}/profile_needle_int8_ours_*.csv
results/emnlp_defense_v1/runs/needle_int8_n10_7b_s{1239..1243}/profile_needle_int8_ours_*.csv
results/emnlp_defense_v1/runs/needle_int8_n10_8b_s{1239..1243}/profile_needle_int8_ours_*.csv
```

---

## RULER 长上下文（分任务 NIAH/VT/CWE/QA）

EVL-042 + EVL-047 修复后的权威数据：

```
results/emnlp_defense_v1/runs/ruler_ra_fix_verify/profile_ruler_*.csv
results/emnlp_defense_v1/runs/ruler_fp16_fix_verify/profile_ruler_*.csv
```

**关键数字**：
- FP16 RULER = 24.38 ± 0.81
- INT8-ours RULER = **24.45** ± 0.65（略优于 FP16，差异在 CI 内）
- 注意：ch4:312 写的是 24.45（已更新）

---

## LongBench v2（EVL-042 fix 后的权威数据）

```
results/emnlp_defense_v1/runs/longbench_v2_fp16_1p5b/profile_longbench_fp16_*.csv
results/emnlp_defense_v1/runs/longbench_v2_int8_1p5b/profile_longbench_int8_ours_*.csv
```

**字段说明**（避免数据矛盾的关键）：
- `longbench_score` = **7.98**（这是原始分数）
- `longbench_contains_macro` = **4.92**（这是宽松匹配宏平均）
- 论文 ch4:312 引用的是 `longbench_contains_macro` = 4.92%
- 两个字段都有效，取决于评测口径

---

## 相关 commit / PR 引用

- 2026-04-04 TPOT 独占 profiling commit: PRF-036 修复后
- 2026-04-04 n=10 seeds 补跑 commit
- 2026-04-04 LongBench v2 (EVL-042 fix) 数据回收
