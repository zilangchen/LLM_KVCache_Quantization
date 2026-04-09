# Claim 3：INT4-RoleAlign 检索恢复

> **论文位置**：`thesis/chapters/ch4_experiments.tex` Claim 3 章节
> **核心主张**：INT4-RoleAlign（`int4_ours_asym`）通过 BA percentile 校准实现 Needle 100%，KV 压缩 ~73%
> **架构事实**：RoleAlign = KIVIStyleKVCache 的子类，**相同 format**（per-channel K + per-token V），差异在校准方式（离线 KL 搜索 vs 运行时 absmax/min）

---

## 核心数据表

| 模型 | H_kv | FP16 PPL | INT4-RA PPL | PPL 降级 | Needle (4K-32K) | KV 压缩 |
|------|------|---------|------------|---------|-----------------|---------|
| Qwen2.5-1.5B | 2 | 9.31 | **10.58** | +13.7% | **100%** | ~73% |
| Qwen2.5-7B | 4 | — | — | +6.1% | **100%** | ~73% |
| LLaMA-3.1-8B | 8 | — | — | +2.4% | **100%** | ~73% |

**关键观察**：PPL 退化呈**反规模依赖**（小模型更差），这是后续 Claim 5（inv_tau × GQA）的前置观察。

---

## 数据路径（emnlp_rolealign_v2 权威冻结 + emnlp_defense_v1 补充）

### INT4-RA PPL（3 seeds × 3 模型）
```
# 1.5B (emnlp_rolealign_v2 权威)
results/emnlp_rolealign_v2/runs/ppl_ours_asym_1p5b_s1234/profile_ppl_int4_ours_asym_*.csv
results/emnlp_rolealign_v2/runs/ppl_ours_asym_1p5b_s1235/profile_ppl_int4_ours_asym_*.csv
results/emnlp_rolealign_v2/runs/ppl_ours_asym_1p5b_s1236/profile_ppl_int4_ours_asym_*.csv

# 7B
results/emnlp_rolealign_v2/runs/ppl_ours_asym_7b_s1234/profile_ppl_int4_ours_asym_*.csv
results/emnlp_rolealign_v2/runs/ppl_ours_asym_7b_s1235/profile_ppl_int4_ours_asym_*.csv
results/emnlp_rolealign_v2/runs/ppl_ours_asym_7b_s1236/profile_ppl_int4_ours_asym_*.csv

# 8B
results/emnlp_rolealign_v2/runs/ppl_ours_asym_8b_s1234/profile_ppl_int4_ours_asym_*.csv
results/emnlp_rolealign_v2/runs/ppl_ours_asym_8b_s1235/profile_ppl_int4_ours_asym_*.csv
results/emnlp_rolealign_v2/runs/ppl_ours_asym_8b_s1236/profile_ppl_int4_ours_asym_*.csv
```

### INT4-RA n=10 补充（emnlp_defense_v1 新增）
```
results/emnlp_defense_v1/runs/ppl_ra_n10_1p5b_s{1239..1243}/profile_ppl_int4_ours_asym_*.csv
results/emnlp_defense_v1/runs/ppl_ra_n10_7b_s{1239..1243}/profile_ppl_int4_ours_asym_*.csv
results/emnlp_defense_v1/runs/ppl_ra_n10_8b_s{1239..1243}/profile_ppl_int4_ours_asym_*.csv
```

### Needle 检索（覆盖 4K/8K/16K/32K 四种长度）
```
results/emnlp_rolealign_v2/runs/needle_ours_asym_*  (v2 权威, 多个 seed)
results/emnlp_defense_v1/runs/needle_ra_n10_*_s{1239..1243}  (n=10 补充)
results/emnlp_defense_v1/runs/needle_ra_v3_ctx{4096,8192,16384}_1p5b/*  (v3 verify)
```

### RULER 分任务分长度
```
results/emnlp_rolealign_v2/runs/ruler_ours_asym_{1p5b,7b,8b}_ctx{4096,8192,16384,32704}_s{1234,1235,1236}/*
results/emnlp_rolealign_v2/runs/ruler_v2fix_{1p5b,7b,8b}_ctx{8192,16384,32704}_s{1234..1236}/*
```

---

## 校准产物

| 模型 | 校准文件 | 用途 |
|------|---------|------|
| 1.5B | `artifacts/kv_calib_rolealign_1p5b_v3.json` | BA percentile 参数（含 RoPE）|
| 7B | `artifacts/kv_calib_rolealign_7b_v3.json` | BA percentile 参数 |
| 8B | `artifacts/kv_calib_rolealign_8b_v3.json` | BA percentile 参数 |

**注意**：BA percentile 参数本质上是 `configs/exp_matrix_rolealign.yaml` 中的 YAML 配置内嵌（不单独存 JSON）。JSON 文件只含 inv_tau 参数。

---

## 与 KIVI 的差异（Claim 3 的完整性辩护）

| 维度 | KIVI | RoleAlign |
|------|------|-----------|
| Cache format | per-channel K + per-token V | **同** |
| 校准方式 | 运行时 absmax/min | **离线 KL 搜索 BA percentile** |
| residual buffer | R=128 | **R=0**（已验证零影响，见 Exp-4）|
| Kernel 路径 | torch_ref | **同** |
| inv_tau 支持 | ❌ | ✅（可选，但见 Claim 5 的 scale 依赖）|

**Exp-4 residual buffer 验证**：
- `ppl_kivi_res0_1p5b`: PPL = 10.43
- `ppl_kivi_res64_1p5b`: PPL = 10.43
- `ppl_kivi_res128_1p5b`: PPL = 10.43
→ 结论：KIVI 的 residual buffer **零影响**，我们的简化基线公平

---

## 答辩防御话术（给 Q&A 题库）

**Q**: "RoleAlign 与 KIVI 只是换了校准方式，创新太薄？"
**A**: "共享相同的 format 是优势不是缺陷——证明 format 已是成熟技术，我们的贡献是 **如何选 scale/zp** 的原则性方法。KIVI 是经验设计，我们是诊断导出（从 attention-KL 诊断推导出 BA percentile 作为最优投影）。相同的硬件和 format 下，我们把"为什么"问清楚了。"

**Q**: "INT4-RA 的 PPL 退化 13.7% 太大？"
**A**: "13.7% 是 1.5B 的最坏情况。8B 模型只退化 2.4%。这是一个**诚实的能力边界**。我们的核心价值不是追求最小 PPL，而是在 73% KV 压缩的代价下保持 **100% Needle 检索能力**——这是许多 INT4 方案做不到的（int4_baseline 会完全失败）。"
