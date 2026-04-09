# TPOT（Time per Output Token）延迟实验

> **权威目录**：`results/emnlp_defense_v1/runs/tpot_*` + `batch_*` + `emnlp_rolealign_v2/runs/prof_serial_*`
> **重要**：TPOT 有两个 seq_len 条件（4K 和 32K），论文不同位置引用不同数字——**都对**

---

## ⚠️ TPOT 数字矛盾的根源

| 论文位置 | 数字 | 条件 | 说明 |
|---------|------|------|------|
| `ch4_experiments.tex:312` 主表 | **47.14 ms** | seq_len=32K, batch=1 | INT8-ours 主结果 |
| `ch4_experiments.tex:1496` 跨模型 | **44.84 ms** | seq_len=4K, batch=1 | 独占 profiling 精确测量 |

**修复需求**：ch4:1496 的表格 caption 必须加 footnote 说明 seq_len=4K 条件，并 cross-reference 32K 主表。

---

## 独占 profiling 数据（seq_len=4K, batch=1）

### TPOT 数据表

| 模型 | FP16 | INT8-ours | INT4-RA | KIVI | INT4-RA/FP16 倍率 |
|------|------|-----------|---------|------|-------------------|
| Qwen2.5-1.5B | 24.39 ms | 44.84 ms | 60.7 ms | ~55 ms | **2.49×** |
| Qwen2.5-7B | — | — | — | — | — |
| LLaMA-3.1-8B | — | — | — | — | — |

**注**：上述数字需从 CSV 实际读取填充。`tpot_int8_ours_7b` vs `tpot_int8_ours_7b_v2` 有重测（v2 是权威）。

---

## 数据路径（完整 17 个 TPOT CSV）

### FP16 baseline
```
results/emnlp_defense_v1/runs/tpot_fp16_1p5b/profile_latency_fp16_2026-04-04T02-13-33.351297.csv
results/emnlp_defense_v1/runs/tpot_fp16_7b/profile_latency_fp16_2026-04-04T02-16-15.196589.csv
results/emnlp_defense_v1/runs/tpot_fp16_8b/profile_latency_fp16_2026-04-04T02-26-14.390647.csv
```

### INT8-ours
```
results/emnlp_defense_v1/runs/tpot_int8_ours_1p5b/profile_latency_int8_ours_2026-04-04T02-13-59.718410.csv
results/emnlp_defense_v1/runs/tpot_int8_ours_7b_v2/profile_latency_int8_ours_2026-04-04T02-23-38.240500.csv  ← 权威
results/emnlp_defense_v1/runs/tpot_int8_ours_8b/profile_latency_int8_ours_2026-04-04T02-26-50.251101.csv

# 7B 旧版本（有问题，不要用）
results/emnlp_defense_v1/runs/tpot_int8_ours_7b/*  ⚠️ 被 _v2 替代
```

### INT4-RoleAlign
```
results/emnlp_defense_v1/runs/tpot_ra_1p5b/profile_latency_int4_ours_asym_2026-04-04T02-14-14.635319.csv
results/emnlp_defense_v1/runs/tpot_ra_7b/profile_latency_int4_ours_asym_2026-04-04T02-17-19.039887.csv
results/emnlp_defense_v1/runs/tpot_ra_8b/profile_latency_int4_ours_asym_2026-04-04T02-27-39.968872.csv
```

### KIVI
```
results/emnlp_defense_v1/runs/tpot_kivi_1p5b/profile_latency_kivi_style_2026-04-04T02-15-27.334917.csv
results/emnlp_defense_v1/runs/tpot_kivi_7b/profile_latency_kivi_style_2026-04-04T02-25-23.035602.csv
results/emnlp_defense_v1/runs/tpot_kivi_8b/profile_latency_kivi_style_2026-04-04T02-28-44.513133.csv
```

### Triton kernel vs torch_ref 对比
```
results/emnlp_defense_v1/runs/tpot_ra_fused_1p5b/profile_latency_int4_ours_asym_2026-04-04T02-22-56.256769.csv      # Triton fused
results/emnlp_defense_v1/runs/tpot_ra_torch_ref_1p5b/profile_latency_int4_ours_asym_2026-04-04T02-22-17.892103.csv  # torch_ref baseline
results/emnlp_defense_v1/runs/tpot_fp16_e4_ref_1p5b/profile_latency_fp16_2026-04-04T05-08-39.901147.csv             # FP16 参考
```

### BitDecoding 外部参考
```
results/emnlp_defense_v1/runs/tpot_bitdecoding_1p5b/profile_latency_bitdecoding_2026-04-04T02-18-47.362880.csv
```

---

## 关键发现

### 1. 自研 Triton kernel 未加速
- `tpot_ra_fused_1p5b`: 63.9 ms
- `tpot_ra_torch_ref_1p5b`: 60.7 ms
- **Δ = +5%**（fused 比 ref 慢）

**原因**：torch_ref 用的是 PyTorch SDPA（已经利用 tensor core），自研 Triton 分通道 kernel 缺少 tensor core 优化。

### 2. BitDecoding microbenchmark 证明可行性
- BitDecoding TPOT: **0.017 ms**
- FP16 SDPA: **0.033 ms**
- **BitDecoding 比 FP16 快 2×**

**证据用途**：论文 ch4 边界段引用 BitDecoding 作为"tensor core 路径可行性"证据，说明我们的 Triton kernel 只是实现不够优，路径是对的。

---

## Batch sweep（Exp-9）— 12 CSV

| config | b=1 | b=4 | b=8 | b=16 |
|--------|-----|-----|-----|------|
| fp16 | 24.39 | — | — | — |
| int8_ours | 44.84 | — | — | — |
| int4_ra | 60.7 | — | — | — |

```
results/emnlp_defense_v1/runs/batch_fp16_b{1,4,8,16}_1p5b/profile_latency_fp16_*.csv
results/emnlp_defense_v1/runs/batch_int8_b{1,4,8,16}_1p5b/profile_latency_int8_ours_*.csv
results/emnlp_defense_v1/runs/batch_ra_b{1,4,8,16}_1p5b/profile_latency_int4_ours_asym_*.csv
```

---

## Profiling 序列化数据（emnlp_rolealign_v2）

```
results/emnlp_rolealign_v2/runs/prof_serial_latency_fp16_{1p5b,7b,8b}_s{512,1024,2048,4096,8192}/
results/emnlp_rolealign_v2/runs/prof_serial_latency_int4_ours_asym_{1p5b,7b,8b}_s{512,1024,2048,4096,8192}/
```

这 60 个目录是 TPOT 随序列长度变化的 sweep（用于画 latency vs seq_len 曲线）。

---

## CSV 字段速查

```
run_id, model_id, run_name, kv_mode, quant_bits, seq_len, gen_len, batch,
ttft_ms, tpot_ms, prefill_tok_per_s, tok_per_s, tok_per_s_per_seq,
gpu_mem_peak_mb, kv_cache_mem_mb, kv_cache_seq_len,
timestamp, git_commit, seed, replica_id
```

**重点字段**：
- `tpot_ms` — 主延迟指标
- `ttft_ms` — first token 延迟（不是本节重点）
- `kv_cache_mem_mb` — KV cache 显存占用
- `replica_id` — 多次 replica 测量（取 mean/median）
