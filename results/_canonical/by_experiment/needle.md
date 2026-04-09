# Needle 检索实验全集

> **权威目录**：`results/emnlp_defense_v1/runs/` + `results/emnlp_rolealign_v2/runs/`
> **评分口径**：exact-match（已统一，解决 S-NIAH vs Needle 矛盾）

---

## 核心结论

**所有 3 模型 × 所有 kv_mode × 所有 seq_len（4K-32K）的 Needle 得分均为 100%**（INT4-baseline 除外）

这是论文最强的 headline：INT4-RA 在 73% KV 压缩下保持 100% 检索能力。

---

## 数据表（按模型 × kv_mode 分组）

### Qwen2.5-1.5B

| kv_mode | seq_len 4K | 8K | 16K | 32K | n seeds |
|---------|-----------|-----|-----|-----|---------|
| fp16 | 100% | 100% | 100% | 100% | 多 |
| int8_ours | 100% | 100% | 100% | 100% | 10 |
| int4_ours_asym | 100% | 100% | 100% | 100% | 10 |
| kivi_style | 100% | 100% | 100% | 100% | 多 |

### Qwen2.5-7B

| kv_mode | 4K-32K | n seeds |
|---------|--------|---------|
| int8_ours | 100% | 10 |
| int4_ours_asym | 100% | 10 |

### LLaMA-3.1-8B

| kv_mode | 4K-32K | n seeds |
|---------|--------|---------|
| int8_ours | 100% | 10 |
| int4_ours_asym | 100% | 10 |

---

## 数据路径（按模型分组）

### 1.5B Needle 完整路径

**n=10 seeds 补充（5 新 seed）**：
```
# FP16
results/emnlp_defense_v1/runs/needle_fp16_ctx{4096,8192,16384}_1p5b/
results/emnlp_defense_v1/runs/needle_fp16_32k_verify/

# INT8-ours n=10
results/emnlp_defense_v1/runs/needle_int8_n10_1p5b_s{1239..1243}/profile_needle_int8_ours_*.csv

# INT4-RA n=10
results/emnlp_defense_v1/runs/needle_ra_n10_1p5b_s{1239..1243}/profile_needle_int4_ours_asym_*.csv

# INT4-RA v3 context sweep
results/emnlp_defense_v1/runs/needle_ra_v3_ctx{4096,8192,16384}_1p5b/
results/emnlp_defense_v1/runs/needle_ra_v3_32k_verify/

# KIVI residual 验证
results/emnlp_defense_v1/runs/needle_kivi_res{0,64,128}_1p5b/profile_needle_kivi_style_*.csv
```

### 7B Needle 完整路径
```
results/emnlp_defense_v1/runs/needle_int8_n10_7b_s{1239..1243}/profile_needle_int8_ours_*.csv
results/emnlp_defense_v1/runs/needle_ra_n10_7b_s{1239..1243}/profile_needle_int4_ours_asym_*.csv
```

### 8B Needle 完整路径
```
results/emnlp_defense_v1/runs/needle_int8_n10_8b_s{1239..1243}/profile_needle_int8_ours_*.csv
results/emnlp_defense_v1/runs/needle_ra_n10_8b_s{1239..1243}/profile_needle_int4_ours_asym_*.csv
```

---

## Needle tau 消融（Claim 5 证据）

```
# 1.5B tau 消融
results/emnlp_defense_v1/runs/tau_ablation_int8_notau_needle/needle_details_*.csv
results/emnlp_defense_v1/runs/tau_ablation_int8_withtau_needle/needle_details_*.csv
results/emnlp_defense_v1/runs/tau_ablation_ra_notau_needle/needle_details_*.csv
results/emnlp_defense_v1/runs/tau_ablation_ra_withtau_needle/needle_details_*.csv

# 7B tau 消融
results/emnlp_defense_v1/runs/tau_full_ra_notau_needle_7b/
results/emnlp_defense_v1/runs/tau_full_ra_withtau_needle_7b/

# 8B tau 消融
results/emnlp_defense_v1/runs/tau_full_ra_notau_needle_8b/
results/emnlp_defense_v1/runs/tau_full_ra_withtau_needle_8b/
```

**结论**：tau on/off 对 Needle 得分无影响（都是 100%），差异只体现在 PPL 上。

---

## 扩展数据（2026-04-09 新增）

### 64K Context 在 8B 模型（`needle_*64k_8b`）

| 模型 | kv_mode | seq_len | pass_rate | exact_match |
|------|---------|---------|-----------|-------------|
| LLaMA-3.1-8B | fp16 | **65536** | **100%** | 0% |
| LLaMA-3.1-8B | int4_ours_asym | **65536** | **100%** | 0% |

**路径**：
```
results/emnlp_defense_v1/runs/needle_fp16_64k_8b/profile_needle_fp16_2026-04-09T18-39-16.173638.csv
results/emnlp_defense_v1/runs/needle_ra_64k_8b/profile_needle_int4_ours_asym_2026-04-09T18-43-52.072609.csv
```

**注意**：`exact_match=0` 是因为 8B 在 64K 下倾向生成解释性文字（模型行为），FP16 也是 0%。`pass_rate` 使用 contains-match，两种量化方式都 100%。INT4-RA 在 64K 上**与 FP16 完全等价**。

### 14B 模型（`needle_*_ctx*_14b`）

| kv_mode | ctx=4K | ctx=8K | ctx=16K |
|---------|--------|--------|---------|
| fp16 | **100% / 100%** | **100% / 100%** | **100% / 100%** |
| int4_ours_asym | **100% / 100%** | **100% / 100%** | **100% / 100%** |

格式：`pass_rate / exact_match`。**14B 所有 context 下 INT4-RA 的 exact match 都是 100%**（与 8B 在 64K 上的 0% exact 形成对比——14B 输出更专注于裸 needle）。

**路径**：
```
results/emnlp_defense_v1/runs/needle_{fp16,ra}_ctx{4096,8192,16384}_14b/profile_needle_*.csv
```

---

## 评分口径（解决 S-NIAH vs Needle 矛盾）

**历史问题**：早期论文中 "S-NIAH" 子任务得分看起来低（~50%），但 "Needle" 主结果是 100%——这造成矛盾。

**解决**：统一用 **exact-match** 评分口径：
- `needle_exact_score` — 精确匹配（我们的主口径）
- `needle_contains_score` — 包含匹配（更宽松，RULER 用）

两个字段都在 CSV 中存在，论文引用时明确标注用哪个。

---

## CSV 字段速查

```
run_id, model_id, kv_mode, quant_bits, seq_len, seed,
needle_exact_score, needle_contains_score,
needle_details_json, ...
```

**重点字段**：
- `needle_exact_score` — 主要口径（0-1）
- `needle_contains_score` — 宽松口径
- `needle_depth_sweep` — 按 depth 位置（0-1）的细分分数
