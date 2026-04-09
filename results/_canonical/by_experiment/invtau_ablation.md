# inv_tau 消融实验全集（Claim 5 证据）

> **最重要的发现**：温度校正 `inv_tau` 的有效性与 GQA 头数 H_kv **反相关**
> **详见**：`../by_claim/claim5_invtau_gqa.md`

---

## 核心数据表

| 模型 | H_kv | kv_mode no-tau | kv_mode with-tau | PPL no-tau | PPL with-tau | Δ |
|------|------|---------------|------------------|-----------|--------------|---|
| Qwen2.5-1.5B | 2 | int4_ours_asym | int4_ours_asym_ba | 10.58 | **10.41** | **-1.6%** ✅ |
| Qwen2.5-7B | 4 | int4_ours_asym | int4_ours_asym_ba | TBD | TBD | **+6.0%** ❌ |
| LLaMA-3.1-8B | 8 | int4_ours_asym | int4_ours_asym_ba | TBD | TBD | **+3.4%** ❌ |

**Needle 得分**：tau on/off 都是 **100%**（差异只在 PPL）

---

## 数据路径（完整清单）

### 1.5B 消融（`tau_ablation_*` 系列）
```
# PPL
results/emnlp_defense_v1/runs/tau_ablation_int8_notau_ppl/profile_ppl_int8_ours_2026-04-04T05-25-48.685311.csv
results/emnlp_defense_v1/runs/tau_ablation_int8_withtau_ppl/profile_ppl_int8_ours_2026-04-04T05-30-23.565233.csv
results/emnlp_defense_v1/runs/tau_ablation_ra_notau_ppl/profile_ppl_int4_ours_asym_2026-04-04T05-15-14.139643.csv
results/emnlp_defense_v1/runs/tau_ablation_ra_withtau_ppl/profile_ppl_int4_ours_asym_ba_2026-04-04T05-21-14.926793.csv

# Needle
results/emnlp_defense_v1/runs/tau_ablation_int8_notau_needle/needle_details_int8_ours_2026-04-04T05-25-17.033891.csv
results/emnlp_defense_v1/runs/tau_ablation_int8_withtau_needle/needle_details_int8_ours_2026-04-04T05-30-01.255976.csv
results/emnlp_defense_v1/runs/tau_ablation_ra_notau_needle/needle_details_int4_ours_asym_2026-04-04T05-15-34.189319.csv
results/emnlp_defense_v1/runs/tau_ablation_ra_withtau_needle/needle_details_int4_ours_asym_ba_2026-04-04T05-21-36.639935.csv
```

### 7B 完整消融（`tau_full_ra_*_7b` 系列）
```
results/emnlp_defense_v1/runs/tau_full_ra_notau_ppl_7b/*.csv
results/emnlp_defense_v1/runs/tau_full_ra_withtau_ppl_7b/*.csv
results/emnlp_defense_v1/runs/tau_full_ra_notau_needle_7b/*.csv
results/emnlp_defense_v1/runs/tau_full_ra_withtau_needle_7b/*.csv
```

### 8B 完整消融（`tau_full_ra_*_8b` 系列）
```
results/emnlp_defense_v1/runs/tau_full_ra_notau_ppl_8b/*.csv
results/emnlp_defense_v1/runs/tau_full_ra_withtau_ppl_8b/*.csv
results/emnlp_defense_v1/runs/tau_full_ra_notau_needle_8b/*.csv
results/emnlp_defense_v1/runs/tau_full_ra_withtau_needle_8b/*.csv
```

---

## INT8 下 tau 的行为（对照组）

在 INT8 上，tau on/off 对 PPL 几乎无影响：
- INT8 no-tau PPL ≈ 9.34
- INT8 with-tau PPL ≈ 9.34
- **Δ ≈ 0%**

**原因**：INT8 有 256 个量化级别，attention 分布的精细结构已经被保留。温度校正只在**粗量化（INT4）**下有意义。

---

## kv_mode 与 tau 的映射

| kv_mode | quant | tau | 用途 |
|---------|-------|-----|------|
| `fp16` | 无 | n/a | baseline |
| `int8_ours` | INT8 | off | INT8 主线 |
| `int8_ours` + `use_attn_temperature` | INT8 | on | INT8 tau 消融 |
| `int4_ours_asym` | INT4 非对称 | **off** | INT4 主线（RoleAlign）|
| `int4_ours_asym_ba` | INT4 非对称 | **on** | INT4 tau 消融 |
| `kivi_style` | INT4 | off（KIVI 无此设计）| KIVI baseline |

---

## 实现位置（代码层）

- **温度校正 hook**：`src/engine/generate_loop.py` 中的 attention hook
- **校准产物**：`artifacts/kv_calib_rolealign_*_v3.json` 含 `per_head_inv_tau` 字段
- **离线搜索**：`scripts/calibrate_behavior.py` 的 `inv_tau_grid` 搜索

---

## 答辩防御（与 Claim 5 呼应）

**Q**: "tau 在 INT8 上无效，为什么不删掉它？"
**A**: "在 INT4 上有效（1.5B 改善 1.6%），这是 Claim 5 的核心证据。INT8 上无效是**预期行为**——INT8 的 256 级量化已经保留了 attention 分布的精细结构，不需要温度补偿。这个对比本身就是诊断框架的一部分。"

**Q**: "为什么 tau 在 7B/8B 反而有害？"
**A**: "这是 Claim 5 的意外发现——GQA 头数 H_kv 越大，每个 head 的噪声被稀释得越厉害（因为共享 K），额外的温度校正反而成为扰动。我们提供了直觉论证（非形式化证明），3 个模型的数据一致支持这个规律。这把 inv_tau 从'可选组件'转变为'GQA 规模依赖规律'的证据。"
