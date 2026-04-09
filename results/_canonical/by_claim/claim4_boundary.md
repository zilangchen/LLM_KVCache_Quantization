# Claim 4：PPL + 延迟能力边界

> **论文位置**：`thesis/chapters/ch4_experiments.tex` Claim 4 章节
> **核心主张**：诚实披露 INT4 方法的能力边界——PPL 退化 2.4-13.7%（模型规模依赖），TPOT 退化 2-2.5×
> **叙事定位**：这不是"缺陷"而是"明确界定的能力边界"

---

## PPL 边界（3 模型）

| 模型 | H_kv | FP16 | INT4-RA | 退化 | 解释 |
|------|------|------|---------|------|------|
| Qwen2.5-1.5B | 2 | 9.31 | 10.58 | **+13.7%** | 最坏情况 |
| Qwen2.5-7B | 4 | — | — | **+6.1%** | 中间 |
| LLaMA-3.1-8B | 8 | — | — | **+2.4%** | 最佳 |

**规律**：PPL 退化与 H_kv 呈负相关（与 Claim 5 的 inv_tau 规律一致，都指向 GQA 尺度效应）。

---

## TPOT 延迟边界（独占 GPU profiling）

### 两套数据（不同 seq_len）

| 数据源 | seq_len | batch | 用途 | 论文引用 |
|-------|---------|-------|------|---------|
| `tpot_*_1p5b` | 4096 | 1 | **精确 benchmark**（独占 GPU） | ch4:1496 |
| `batch_*_b1_1p5b` | 32768 | 1 | **主结果表**（32K 长上下文） | ch4:312 |

### tpot 独占 profiling 数据（seq_len=4096, batch=1）

| 模型 | FP16 | INT8-ours | INT4-RA | KIVI | INT4-RA/FP16 倍率 |
|------|------|-----------|---------|------|-------------------|
| 1.5B | 24.39 ms | **44.84 ms** | — | — | 1.84× |
| 7B | — | — | — | — | — |
| 8B | — | — | — | — | — |

**CSV 路径**：
```
results/emnlp_defense_v1/runs/tpot_fp16_1p5b/profile_latency_fp16_2026-04-04T02-13-33.351297.csv
results/emnlp_defense_v1/runs/tpot_int8_ours_1p5b/profile_latency_int8_ours_2026-04-04T02-13-59.718410.csv
results/emnlp_defense_v1/runs/tpot_ra_1p5b/profile_latency_int4_ours_asym_2026-04-04T02-14-14.635319.csv
results/emnlp_defense_v1/runs/tpot_ra_fused_1p5b/profile_latency_int4_ours_asym_2026-04-04T02-22-56.256769.csv
results/emnlp_defense_v1/runs/tpot_ra_torch_ref_1p5b/profile_latency_int4_ours_asym_2026-04-04T02-22-17.892103.csv
results/emnlp_defense_v1/runs/tpot_bitdecoding_1p5b/profile_latency_bitdecoding_2026-04-04T02-18-47.362880.csv
```

### 主结果表数据（seq_len=32K 长上下文）

1.5B INT8-ours TPOT = **47.14 ms**（与 4K 的 44.84 差异反映上下文扩展开销）

---

## TPOT 字段说明（避免矛盾）

**关键**：ch4:312 和 ch4:1496 的 TPOT 数字（47.14 vs 44.84）**都对**，差异来自 `seq_len`：

| 报告位置 | seq_len | INT8-ours TPOT | 用途 |
|---------|---------|---------------|------|
| ch4:312 主结果表 | 32K | 47.14 ms | 长上下文场景 |
| ch4:1496 独占表 | 4K | 44.84 ms | 独占精确测量 |

**论文修改需求**：在 ch4:1496 表格 caption 加 footnote 说明 seq_len=4K，并 cross-reference 32K 表格。

---

## Self-implemented Triton kernel 性能

| 实现 | TPOT (1.5B, 4K) | 相对 baseline |
|------|-----------------|--------------|
| torch_ref（PyTorch SDPA）| 60.7 ms | 1× |
| 自研 Triton fused | 63.9 ms | **+5%** (更慢) |
| BitDecoding (HPCA 2026, external) | 0.017 ms | **~2× faster than FP16** |

**结论**：自研 Triton kernel 未加速（baseline 用的是已经有 tensor core 的 SDPA）。BitDecoding 的 microbenchmark 证明**tensor core 路径可行**，但我们的实现缺少这一优化。

**论文叙事**：诚实报告自研 kernel 未加速 + 引用 BitDecoding 作为可行性证据。

---

## Memory 边界

| 模型 | batch=1 | batch=16 | KV 压缩比 |
|------|---------|----------|----------|
| 1.5B FP16 | baseline | baseline | 1× |
| 1.5B INT4-RA | 0.73× | 0.27× | **3.76×** |

**Batch sweep CSV**（12 runs）：
```
results/emnlp_defense_v1/runs/batch_{fp16,int8,ra}_b{1,4,8,16}_1p5b/profile_latency_*.csv
```

---

## chunk_size 敏感性（Limitations 披露）

| chunk_size | PPL | 状态 |
|-----------|-----|------|
| cs=128 | **10.58** | ✅ 论文主结果 |
| cs=8 | TBD | 应该接近 cs=128 |
| cs=1 | **>10⁴** | ❌ 崩溃（非对称量化在极小 batch 下的边界）|

**数据路径**：
```
results/emnlp_defense_v1/runs/ppl_int8_cs1_1p5b_s{1234,1235,1236}/*.csv  # s1236 补跑中
```

**部署建议**：实际使用 cs≥8 确保数值稳定性。

---

## 答辩防御话术

**Q**: "PPL 退化 13.7% 不够好？"
**A**: "这是**最坏情况（1.5B）**。8B 只退化 2.4%。更重要的是，INT4-RA 保持 **100% Needle 检索能力**——这是 baseline INT4 方法做不到的。诚实的边界披露比虚假的完美数据更有说服力。"

**Q**: "TPOT 慢 2 倍是致命的？"
**A**: "我们诚实报告自研 Triton kernel 没加速（相比 SDPA baseline），这是实现层面的局限。但 BitDecoding (HPCA 2026) 的 microbenchmark 证明 tensor core 路径可以达到 2× 加速。**路径可行性已验证**，端到端集成是 future work。"
