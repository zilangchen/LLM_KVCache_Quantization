# Claim 2：诊断透镜定位 INT4 失效根因

> **论文位置**：`thesis/chapters/ch4_experiments.tex` Claim 2 章节
> **核心主张**：基于 attention-KL 的诊断透镜识别出 INT4 失效的根因是 **Key 主导**（而非 Value）
> **证据**：K/V 消融 + GQA 架构相关性 + b10 校准灵敏度

---

## 核心数据

### K/V 消融（Exp-11）— MixedKV 4 配置

| 配置 | K bits | V bits | PPL | 说明 |
|------|--------|--------|-----|------|
| K@INT4 / V@INT16 | 4 | 16 | **1291** | K 是关键（崩溃）|
| K@INT8 / V@INT4 | 8 | 4 | 低 | K 保护即可 |
| K@INT16 / V@INT4 | 16 | 4 | 低 | V 可以便宜 |
| K@INT16 / V@INT8 | 16 | 8 | ≈ FP16 | 两者都高精度 |

**诊断结论**：**K 是主导误差源**。这直接导出 RoleAlign 的 BA percentile 设计（给 K 更细的量化）。

### 数据路径（K/V ablation CSVs）
```
results/emnlp_defense_v1/runs/ppl_ablation_k4_v16_1p5b/profile_ppl_int4_mixed_kv_2026-04-03T17-24-34.704772.csv
results/emnlp_defense_v1/runs/ppl_ablation_k8_v16_1p5b/profile_ppl_int4_mixed_kv_2026-04-03T17-33-02.389081.csv
results/emnlp_defense_v1/runs/ppl_ablation_k16_v4_1p5b/profile_ppl_int4_mixed_kv_2026-04-03T17-28-38.924113.csv
results/emnlp_defense_v1/runs/ppl_ablation_k16_v8_1p5b/profile_ppl_int4_mixed_kv_2026-04-03T17-37-01.822391.csv
```

---

## GQA 架构相关性（Exp-8）

| 指标 | 数值 | 解释 |
|------|-----|------|
| G2: K/V 独立性 ρ | 0.024 | K 和 V 的误差**独立**（不是相关噪声）|
| G5: K/V 噪声比 | **2.15×** | K 的量化噪声是 V 的 2 倍以上 |

这些数据支持 Claim 2 的诊断结论：K 主导，V 次要。

---

## 校准灵敏度（b10 消融）

**实验**：不同校准 batch 数量（b=1, 5, 10, 20）对校准产物的影响

| batch | K scale 稳定性 | PPL 差异 |
|-------|---------------|---------|
| b=1 | 差（方差大） | +2-5% |
| b=10 | 好 | baseline |
| b=20 | 与 b=10 一致 | ≈0% |

**校准产物路径**：
```
artifacts/kv_calib_kl_b10_1p5b_*.json  # 1.5B b10
artifacts/kv_calib_kl_b10_7b_*.json    # 7B b10
```

**数据路径**（b10 灵敏度消融）：
```
results/emnlp_expansion_v1/runs/  (60 dirs, K/V ablation + b10 calibration)
```

---

## 答辩防御话术

**Q**: "为什么不直接给 V 也高精度？"
**A**: "因为 V 的误差贡献被注意力的 softmax 加权平均稀释，而 K 的误差直接改变 softmax 的权重分布。诊断透镜通过 attention-KL 把这个区分量化了——K 的噪声幅度是 V 的 2.15× (Exp-8 G5)，且两者独立 (ρ=0.024)。这是经验发现，不是理论假设。"

**Q**: "b10 校准消融的增益有多大？"
**A**: "b10 和 b20 差异 <0.1%，但 b1 的方差足以掩盖校准质量的真实差异。我们选 b10 是**稳定性的最小充分点**，而不是一个随意数。"
