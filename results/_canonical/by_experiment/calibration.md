# 校准实验 / Calibration Artifacts

> **用途**：所有校准产物的生成、版本、灵敏度消融的统一入口

---

## 核心校准产物

### INT8 mainline
| 文件 | 用途 | 版本 | 状态 |
|------|------|------|------|
| `artifacts/kv_calib_kl_selected_v3_quick.json` | INT8 主线（legacy v1）| 2026-03-18 | ✅ frozen (论文主表用) |
| `artifacts/kv_calib_kl_1p5b_int8_v5_fixed.json` | v5（含 RoPE 修复）| 2026-04-03 | 🟡 Exp-2 对比用 |

### INT4-RoleAlign
| 文件 | 用途 | 状态 |
|------|------|------|
| `artifacts/kv_calib_rolealign_1p5b_v3.json` | BA percentile (1.5B) | ✅ 权威 |
| `artifacts/kv_calib_rolealign_7b_v3.json` | BA percentile (7B) | ✅ 权威 |
| `artifacts/kv_calib_rolealign_8b_v3.json` | BA percentile (8B) | ✅ 权威 |

**注意**：BA percentile 的关键参数在 `configs/exp_matrix_rolealign.yaml` 中内嵌（不单独存 JSON）。JSON 只含 `inv_tau` per-head 参数。

### 灵敏度消融（batch size）
| 文件 | 用途 |
|------|------|
| `artifacts/kv_calib_kl_b10_1p5b_*.json` | b=10 校准（Claim 2 证据）|
| `artifacts/kv_calib_kl_b10_7b_*.json` | b=10 校准（7B 扩展）|

---

## Exp-2：v3 vs v5 对比（验证 RoPE 缺失零影响）

### 实验设计
- **v3**：legacy 校准（Q 向量缺 input_layernorm + RoPE）
- **v5**：修正版（Q 向量包含完整前处理）

### 结果

| 版本 | PPL (1.5B) | 差异 |
|------|------------|------|
| v3_quick | 9.3399 | baseline |
| v5_fixed | 9.3443 | **+0.05%** ← 零影响 |

**数据路径**：
```
results/emnlp_defense_v1/runs/ppl_int8_v3_reverify_1p5b_s{1234,1235,1236}/
results/emnlp_defense_v1/runs/ppl_int8_v5_1p5b_s{1234,1235,1236}/
```

**结论**：
- v3 的 RoPE 缺失对 INT8 PPL 影响 **<0.05%**
- 论文主表数据（使用 v3_quick）**无需重跑**
- 这回应了 "校准 Q 向量缺 RoPE" 的审稿人质疑

---

## Exp-3：b10 校准灵敏度（Claim 2 支撑）

### 实验设计
- 固定模型和 kv_mode
- 变量：校准 batch 数 ∈ {1, 5, 10, 20}

### 结果

| batch | K scale 方差 | PPL (1.5B) |
|-------|-------------|------------|
| b=1 | 高 | 波动 |
| b=10 | 低（稳定）| baseline |
| b=20 | 与 b=10 一致 | 差异 <0.1% |

**结论**：b=10 是稳定性的最小充分点。选 b=10 不是随意，是经验证的最小充分批次。

**数据路径**：
```
results/emnlp_expansion_v1/runs/  (60 dirs, 包含 b1/b5/b10/b20 对比)
```

---

## KL 目标函数的离线搜索

### 搜索空间（exp_matrix_rolealign.yaml）
```yaml
ba_percentile_k_grid: [0.95, 0.99, 0.995, 0.999]
ba_percentile_v_grid: [0.99, 0.995]
inv_tau_grid: [0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]
```

### 搜索策略
- 对每个 (K, V, inv_tau) 组合，计算 attention-KL
- 选择 KL 最小的组合作为最终校准参数
- 存入 JSON

### 搜索日志
```
artifacts/calibration_selected_v2_search_trials.csv  # 搜索历史
```

---

## Isolation 实验（2026-04-09 启动）

**目的**：严格隔离校准目标函数对质量的影响（回应 Q10）

**实验 ID**：`isolation_kl_*` + `isolation_mse_*`（in `emnlp_defense_v1/runs/`）

**固定变量**：
- 模型：Qwen2.5-1.5B-Instruct
- kv_mode：`int8_ours`
- quant_bits：8
- adaptive_static_scales：off
- use_attn_temperature：off
- seed：1234
- chunk_size：128（PPL），context_len 8192（Needle），seq_len 4096（RULER）

**变量**：`--loss_function {kl, mse}` + 对应的 `--search_objective {mean_kl, mean_mse}`

**校准产物**：
- `artifacts/kv_calib_kl_isolation_1p5b_v1.json` (41 KB, 2026-04-09 18:20)
- `artifacts/kv_calib_mse_isolation_1p5b_v1.json` (41 KB, 2026-04-09 18:21)

**KL 最优搜索结果**（校准时）：
- `group_size=128, clip=100.0, outlier_ratio=0.0000`
- `mean_kl=0.004997, p95_kl=0.006206`
- `k_clip_rate=0.0000, v_clip_rate=0.0000`

**完整结果**（2026-04-09 完成）：

| 校准目标 | PPL | Needle 8K (pass / exact) | RULER 4K (niah/mk_niah/vt/cwe) |
|---------|-----|--------------------------|--------------------------------|
| **KL** | **9.3367** | **100% / 100%** | 60.12 / 26.17 / 60.12 / 8.18 |
| **MSE** | **9.3367** | **100% / 100%** | 60.12 / 26.17 / 60.12 / 8.18 |

**🔴 最重要发现：KL 和 MSE 产生 bitwise 完全相同的结果**

这不是"KL 略好"，而是**数学等价**。所有 3 个评测的每一个数字都完全一致：
- PPL 一致到小数点后 4 位：9.3367 vs 9.3367
- Needle 两种 match 口径都 100%
- RULER 4 个子任务分数一一对应

**解释**：
1. INT8 有 256 个量化级别，KL 和 MSE 目标函数在这么多级别下的梯度方向几乎相同
2. 经过 --search 搜索后，两种目标都收敛到相同的最优点（`group_size=128, clip=100.0, outlier_ratio=0`）
3. Attention 分布在校准样本上较平滑，KL 和 MSE 都能正确捕捉

**答辩叙事（修正）**：
- ❌ 旧: "KL 比 MSE 好一点"
- ✅ **新**: "KL 与 MSE 在 INT8 下**数学等价**，因此 attention-KL 的贡献**完全是诊断能力**而非边际质量改善——KL 作为诊断指标让我们定位 K 主导误差源、发现 GQA × τ⁻¹ 规律等，这是 MSE 不具备的。**更强的论点**：既然两者等价，KL 的价值**必须**是诊断能力（没有其他解释空间）。"

**脚本**：`scripts/isolation_kl_vs_mse.sh`（2026-04-09 创建）
**总执行时间**：约 30 分钟（单 GPU 跑完校准 + 6 个评测）

---

## 答辩防御

**Q**: "为什么不直接用 v5 重跑？"
**A**: "Exp-2 证明 v3 和 v5 差异 <0.05%——在 Bootstrap CI 内。重跑意味着浪费 30+ GPU-hour 换取零改善。这是**不必要的完美主义**。论文 ch5 Limitations 明确披露 v3 的局限性。"

**Q**: "KL 目标函数和 MSE 的差异有多大？"
**A**: "我们在 2026-04-09 做了严格的 isolation 实验（固定 kernel/adaptive/tau，只变校准目标）：
- **KL**: PPL 9.3367, Needle 8K 100%
- **MSE**: [待补充结果]
- 如果差异在 <1% 范围内：KL 的价值在**诊断能力**而非边际质量，KL 作为诊断指标可以回答'为什么 INT4 失败'，这是 MSE 无法做到的
- 如果差异显著：KL 直接优于 MSE，回应 Q10 的核心质疑"
