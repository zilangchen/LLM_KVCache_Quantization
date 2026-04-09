# K/V 量化轴消融（Claim 2 证据）

> **核心发现**：K 是主导误差源，V 是次要。这直接支持 INT4-RA 的 BA percentile 对 K 给更细量化的设计决策。

---

## 核心数据（Exp-11 MixedKV 4 配置）

| 配置 | K bits | V bits | PPL (1.5B) | 相对 FP16 |
|------|--------|--------|------------|-----------|
| k4_v16 | 4 | 16 | **1291** | ❌ 崩溃 |
| k8_v16 | 8 | 16 | ~10 | ~正常 |
| k16_v4 | 16 | 4 | ~10 | ~正常 |
| k16_v8 | 16 | 8 | ~9.5 | 接近 FP16 |

**关键观察**：
- K 从 16 降到 4 → PPL 爆炸（1291）
- V 从 16 降到 4 → PPL 仅轻微上升
- **结论**：**K 是误差主导，V 是次要**

---

## 数据路径

```
results/emnlp_defense_v1/runs/ppl_ablation_k4_v16_1p5b/profile_ppl_int4_mixed_kv_2026-04-03T17-24-34.704772.csv
results/emnlp_defense_v1/runs/ppl_ablation_k8_v16_1p5b/profile_ppl_int4_mixed_kv_2026-04-03T17-33-02.389081.csv
results/emnlp_defense_v1/runs/ppl_ablation_k16_v4_1p5b/profile_ppl_int4_mixed_kv_2026-04-03T17-28-38.924113.csv
results/emnlp_defense_v1/runs/ppl_ablation_k16_v8_1p5b/profile_ppl_int4_mixed_kv_2026-04-03T17-37-01.822391.csv
```

---

## 理论解释（attention-KL 视角）

在 softmax 注意力中：
- K 的量化误差 → 直接改变 logits → softmax 权重分布偏移
- V 的量化误差 → 被 softmax 权重加权平均稀释

**数学直觉**：
```
attention_output = softmax(Q K^T) V
                 = p V          (p = softmax 权重)

K 噪声 → p 偏移 → attention 方向变化（致命）
V 噪声 → 加权平均 → 自然平滑（温和）
```

---

## 相关的 Exp-8（GQA 架构相关性）

| 指标 | 数值 | 解释 |
|------|-----|------|
| K/V 噪声独立性 ρ | 0.024 | 两者**独立**，不是相关噪声 |
| K/V 噪声比 | **2.15×** | K 的噪声幅度是 V 的 2 倍 |

这些数据与 MixedKV 消融的结论一致：K 主导，V 次要。

**数据路径**：
```
results/emnlp_defense_v1/runs/kv_noise_diagnostic.json  # Exp-8 G2 + G5
results/emnlp_defense_v1/runs/kv_noise_g5.json
```

---

## 设计决策导出

基于 K 主导的发现，INT4-RA 的设计是：

1. **K 用 per-channel 量化**（更细，保护 logits 方向）
2. **V 用 per-token 量化**（更粗，由 softmax 平均稀释）
3. **K 的 percentile 用 BA 优化**（比 V 更保守，clip=99.5%）
4. **V 的 percentile 可以更激进**（clip=99.0%）

这是**从诊断结果导出的设计**，而不是随意的 heuristics。

---

## 答辩防御

**Q**: "K 主导的结论只在 1.5B 上验证？"
**A**: "Exp-8 的 K/V 噪声独立性 (ρ=0.024) 和噪声比 (2.15×) 在 3 个模型上都一致。虽然 MixedKV 只在 1.5B 上跑全量，但理论（softmax 数学性质）+ 3 模型的噪声比一致性足以支持跨模型推广。"

**Q**: "为什么不直接 K@INT8+V@INT4？"
**A**: "这是我们的 MixedKV 基线（kv_mode=`mixed_kv`）。问题是它的 KV 压缩率不如纯 INT4-RA——K@INT8 占 50% 空间，远高于 RoleAlign 的 K@INT4（25%）。我们选择 per-channel K@INT4 + BA percentile 作为折中：同样 INT4 压缩率，但 K 的量化误差被 BA percentile 控制住。"
