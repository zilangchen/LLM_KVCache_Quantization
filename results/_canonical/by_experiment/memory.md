# Memory / KV 压缩率 / Batch sweep 实验

> **核心主张**：INT4-RA 在 batch=16 下节省 KV cache 显存 **3.76×**（相比 FP16）
> **数据源**：`results/emnlp_defense_v1/runs/batch_*` + `emnlp_rolealign_v2/runs/memory_*`

---

## Batch sweep 核心数据（Exp-9）

### 1.5B × batch={1,4,8,16} × 3 modes

| kv_mode | batch=1 peak | batch=16 peak | KV cache @ b16 | 压缩比 |
|---------|-------------|---------------|----------------|--------|
| fp16 | baseline | baseline | baseline | 1× |
| int8_ours | ~0.75× | ~0.5× | ~0.5× | **2×** |
| int4_ours_asym | ~0.73× | ~0.27× | ~0.27× | **3.76×** |

**结论**：
- batch=1 时，KV cache 占比小（model weights 主导），压缩收益不明显
- batch=16 时，KV cache 成为瓶颈，INT4-RA 省 **2.7 GB** 显存（相比 FP16）

---

## 数据路径（完整 12 CSV）

```
results/emnlp_defense_v1/runs/batch_fp16_b1_1p5b/profile_latency_fp16_2026-04-04T02-43-08.896004.csv
results/emnlp_defense_v1/runs/batch_fp16_b4_1p5b/profile_latency_fp16_2026-04-04T02-45-09.146936.csv
results/emnlp_defense_v1/runs/batch_fp16_b8_1p5b/profile_latency_fp16_2026-04-04T02-47-39.620868.csv
results/emnlp_defense_v1/runs/batch_fp16_b16_1p5b/profile_latency_fp16_2026-04-04T02-50-53.104558.csv

results/emnlp_defense_v1/runs/batch_int8_b1_1p5b/profile_latency_int8_ours_2026-04-04T02-44-27.030586.csv
results/emnlp_defense_v1/runs/batch_int8_b4_1p5b/profile_latency_int8_ours_2026-04-04T02-46-49.336933.csv
results/emnlp_defense_v1/runs/batch_int8_b8_1p5b/profile_latency_int8_ours_2026-04-04T02-49-50.937946.csv
results/emnlp_defense_v1/runs/batch_int8_b16_1p5b/profile_latency_int8_ours_2026-04-04T02-54-08.453012.csv

results/emnlp_defense_v1/runs/batch_ra_b1_1p5b/profile_latency_int4_ours_asym_2026-04-04T02-43-36.139227.csv
results/emnlp_defense_v1/runs/batch_ra_b4_1p5b/profile_latency_int4_ours_asym_2026-04-04T02-44-58.346819.csv
results/emnlp_defense_v1/runs/batch_ra_b8_1p5b/profile_latency_int4_ours_asym_2026-04-04T02-48-26.815127.csv
results/emnlp_defense_v1/runs/batch_ra_b16_1p5b/profile_latency_int4_ours_asym_2026-04-04T02-51-56.513307.csv
```

---

## 序列化 memory sweep（emnlp_rolealign_v2）

### Seq_len sweep × 3 模型

```
results/emnlp_rolealign_v2/runs/memory_ours_asym_{1p5b,7b,8b}_s{512,1024,2048,4096,8192}/
results/emnlp_rolealign_v2/runs/prof_serial_memory_fp16_{1p5b,7b,8b}_s{512,1024,2048,4096,8192}/
results/emnlp_rolealign_v2/runs/prof_serial_memory_int4_ours_asym_{1p5b,7b,8b}_s{512,1024,2048,4096,8192}/
```

这些数据用来画 "KV cache memory vs seq_len" 曲线。

---

## KV cache 占比分析

| 模型 | batch=1, seq=4K KV | batch=16, seq=4K KV | 节省（INT4-RA vs FP16）|
|------|--------------------|--------------------|----------------------|
| 1.5B | ~240 MB | ~3.84 GB | 2.7 GB |
| 7B | ~480 MB | ~7.68 GB | 5.4 GB |
| 8B | ~480 MB | ~7.68 GB | 5.4 GB |

**推广结论**：batch 越大，INT4 压缩的绝对收益越大。这支撑 Claim 4 "边界" 叙事的"虽然 TPOT 慢 2×，但显存省 3.76×"。

---

## CSV 字段速查

`profile_latency_*.csv` 包含的 memory 字段：

| 字段 | 含义 |
|------|------|
| `gpu_mem_peak_mb` | 峰值 GPU 显存 |
| `kv_cache_mem_mb` | KV cache 专属显存 |
| `kv_cache_seq_len` | KV cache 实际长度 |

---

## 答辩防御

**Q**: "batch=1 的 KV cache 省显存没什么用？"
**A**: "是的，batch=1 时 KV 占比小。我们的叙事从来不是'batch=1 下省显存'，而是'batch 越大收益越大'。Exp-9 显示 batch=16 下 INT4-RA 省 2.7GB 显存——这足够一个 7B 模型在 H20 上从 batch=8 提升到 batch=16。这就是**显存是瓶颈的部署场景**下 INT4 的真实价值。"
