# PPL（Perplexity）实验全集

> **权威目录**：`results/emnlp_defense_v1/runs/` + `results/emnlp_rolealign_v2/runs/`
> **所有 PPL 实验使用 greedy decoding**，因此在相同 seed 下 bitwise 一致

---

## 主表数据（3 模型 × 3-4 modes）

### Qwen2.5-1.5B

| kv_mode | PPL | n seeds | 数据来源 |
|---------|-----|---------|---------|
| fp16 | 9.31 | 10 | `ppl_fp16_n10_1p5b_s{1234..1243}` |
| int8_ours | 9.34 | 10 | `ppl_int8_n10_1p5b_s{1234..1243}` |
| int4_ours_asym (INT4-RA) | 10.58 | 10 | `ppl_ra_n10_1p5b_s{1234..1243}` |
| int4_ours_asym_ba (with tau) | 10.41 | 1 | `tau_ablation_ra_withtau_ppl/` |
| kivi_style | 10.43 | 1 | `ppl_kivi_res*_1p5b/` (res=0/64/128 全一致) |

### Qwen2.5-7B

| kv_mode | PPL 相对 FP16 | 数据来源 |
|---------|--------------|---------|
| int8_ours | 近 FP16 | `ppl_int8_n10_7b_s{1239..1243}` |
| int4_ours_asym | +6.1% | `ppl_ra_n10_7b_s{1239..1243}` + rolealign_v2 |

### LLaMA-3.1-8B

| kv_mode | PPL 相对 FP16 | 数据来源 |
|---------|--------------|---------|
| int8_ours | 近 FP16 | `ppl_int8_n10_8b_s{1239..1243}` |
| int4_ours_asym | +2.4% | `ppl_ra_n10_8b_s{1239..1243}` + rolealign_v2 |

---

## n=10 seeds 验证（答辩补强：n=10 确定性）

**结论**：所有 5 个新 seed (s1239-s1243) 的 PPL 与原 5 seed (s1234-s1238) **bitwise 完全一致**。greedy decoding 下 PPL 零方差。

### 1.5B 所有 modes × 10 seeds 路径
```
results/emnlp_defense_v1/runs/ppl_fp16_n10_1p5b_s{1239..1243}/profile_ppl_fp16_*.csv
results/emnlp_defense_v1/runs/ppl_int8_n10_1p5b_s{1239..1243}/profile_ppl_int8_ours_*.csv
results/emnlp_defense_v1/runs/ppl_ra_n10_1p5b_s{1239..1243}/profile_ppl_int4_ours_asym_*.csv
```

原 5 seeds (s1234-s1238) 在 `emnlp_rolealign_v2/` 或 `emnlp_defense_v1/` 中对应。

---

## chunk_size sweep（Exp-3）

| chunk_size | kv_mode | PPL (1.5B) | 说明 |
|-----------|---------|------------|------|
| 128 | int8_ours | 9.34 | 主结果 |
| 1 | int8_ours | **9.2673** (s1234) | 接近 |
| 1 | int8_ours | **9.2673** (s1235) | 一致 |
| 1 | int8_ours | TBD (s1236 补跑中) | ⏳ |
| 128 | int4_ours_asym | 10.58 | 主结果 |
| 1 | int4_ours_asym | **>10⁴** | ❌ 崩溃（非对称量化边界）|

**数据路径**：
```
results/emnlp_defense_v1/runs/ppl_int8_cs1_1p5b_s1234/profile_ppl_int8_ours_2026-04-03T12-13-25.989463.csv
results/emnlp_defense_v1/runs/ppl_int8_cs1_1p5b_s1235/profile_ppl_int8_ours_2026-04-03T14-42-48.069704.csv
results/emnlp_defense_v1/runs/ppl_int8_cs1_1p5b_s1236/                   # ⏳ 补跑中 (tmux s1236)
results/emnlp_defense_v1/runs/ppl_int8_cs8_1p5b/                          # cs=8 参考
```

---

## K/V 量化轴消融（Exp-11）

| 配置 | K bits | V bits | PPL (1.5B) | 说明 |
|------|--------|--------|------------|------|
| MixedKV k4v16 | 4 | 16 | **1291** | K 崩溃 → 证明 K 主导 |
| MixedKV k8v16 | 8 | 16 | 低 | K 保护 → 恢复 |
| MixedKV k16v4 | 16 | 4 | 低 | V 便宜 |
| MixedKV k16v8 | 16 | 8 | ≈ FP16 | 两者高精度 |

```
results/emnlp_defense_v1/runs/ppl_ablation_k{4,8,16}_v{4,8,16}_1p5b/profile_ppl_int4_mixed_kv_*.csv
```

---

## INT8 v3 vs v5 校准对比（Exp-2）

**实验**：v3_quick（legacy, 缺 RoPE）vs v5（含 input_layernorm + RoPE）

| 校准版本 | PPL (1.5B) | 差异 |
|---------|------------|------|
| v3_quick | 9.3399 | baseline |
| v5_fixed | 9.3443 | **+0.05%** ← 零影响 |

**数据路径**：
```
results/emnlp_defense_v1/runs/ppl_int8_v3_reverify_1p5b_s{1234..1236}/
results/emnlp_defense_v1/runs/ppl_int8_v5_1p5b_s{1234..1236}/
```

**结论**：v3 的 RoPE 缺失对论文主表**零影响**（差异 0.05%）。不需要用 v5 重跑。

---

## 14B 扩展 PPL（2026-04-09 新增，Claim 5 验证）

| kv_mode | PPL | 相对 FP16 |
|---------|-----|----------|
| fp16 | **5.455** | baseline |
| int4_ours_asym (no-tau) | **5.7899** | **+6.1%** |
| int4_ours_asym_ba (with-tau) | **5.8954** | **+8.1%** (vs fp16) / **+1.8%** (vs no-tau) |

**与其他模型对比**：14B 的 INT4-RA PPL 退化 **6.1%** 与 7B 完全相同，远优于 1.5B 的 13.7%。这证明 INT4-RA 方法**对更大模型依然有效**。

**τ⁻¹ 效果**：与 Claim 5 预期一致——H_kv=8 的 14B 模型不从 τ⁻¹ 获益（反而恶化 1.8%）。

**路径**：
```
results/emnlp_defense_v1/runs/ppl_fp16_14b_s1234/profile_ppl_fp16_2026-04-09T19-42-52.072129.csv
results/emnlp_defense_v1/runs/ppl_ra_notau_14b_s1234/profile_ppl_int4_ours_asym_2026-04-09T19-52-10.088384.csv
results/emnlp_defense_v1/runs/ppl_ra_withtau_14b_s1234/profile_ppl_int4_ours_asym_ba_2026-04-09T20-01-41.423310.csv
```

---

## Isolation KL vs MSE（2026-04-09 新增，Q10 答辩证据）

严格隔离校准目标函数的影响：

| 校准目标 | PPL | Needle 8K | RULER 4K niah/mk_niah/vt/cwe |
|---------|-----|-----------|---------|
| KL | **9.3367** | 100% | 60.12/26.17/60.12/8.18 |
| MSE | **9.3367** | 100% | 60.12/26.17/60.12/8.18 |

**所有数字 bitwise 一致**。详见 `by_experiment/calibration.md` 的 Isolation 段。

**路径**：
```
results/emnlp_defense_v1/runs/isolation_{kl,mse}_{ppl,needle_8k,ruler}_1p5b/profile_*.csv
```

---

## KIVI residual buffer 验证（Exp-4）

| residual_length | PPL (1.5B) | 结论 |
|----------------|------------|------|
| 0 | **10.4294** | baseline |
| 64 | **10.4294** | = 0 |
| 128 | **10.4294** | = 0 |

**结论**：KIVI residual buffer 对质量**零影响**。回应 "KIVI 基线被削弱" 质疑。

**数据路径**：
```
results/emnlp_defense_v1/runs/ppl_kivi_res0_1p5b/profile_ppl_kivi_style_*.csv
results/emnlp_defense_v1/runs/ppl_kivi_res64_1p5b/profile_ppl_kivi_style_*.csv
results/emnlp_defense_v1/runs/ppl_kivi_res128_1p5b/profile_ppl_kivi_style_*.csv
```

---

## CSV 字段速查

所有 PPL CSV 共享同一 schema（26 列）：

```
run_id, model_id, kv_mode, quant_bits, clip_percentile, group_size,
dtype, hardware, seq_len, gen_len, batch, ttft_ms, tpot_ms, tok_per_s,
gpu_mem_peak_mb, timestamp, git_commit, seed, replica_id,
perplexity, ppl_ci95_low, ppl_ci95_high, ppl_mode,
tokens_evaluated, chunk_size, target_tokens
```

**重点字段**：
- `perplexity` — 主 PPL 值
- `ppl_mode` — `hf` (HuggingFace) 或 `kv_cache`（自定义路径）
- `chunk_size` — 关键参数，cs=1 vs cs=128 在 INT4-RA 下差异巨大
- `seed` — 相同 seed 的 PPL bitwise 一致（greedy）
