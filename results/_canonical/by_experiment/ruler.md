# RULER 长上下文实验

> **权威目录**：`results/emnlp_rolealign_v2/runs/ruler_*` + `results/emnlp_defense_v1/runs/ruler_*_fix_verify`
> **关键修复**：EVL-042（总分口径）+ EVL-047（CWE 子任务 prompt budget 溢出）

---

## 核心数据

### 主结果（1.5B，多 context × 多 seed）

| 模型 | kv_mode | 4K | 8K | 16K | 32K |
|------|---------|----|----|-----|-----|
| 1.5B | fp16 | 24.38 ± 0.81 | — | — | — |
| 1.5B | int8_ours | **24.45** ± 0.65 | — | — | — |
| 1.5B | int4_ours_asym | TBD | TBD | TBD | TBD |

**注意**：ch4:306 和 ch4:312 已更新为正确数字（24.38 / 24.45），旧值 24.38 (INT8) 是复制错误。

---

## 数据路径（权威冻结）

### 1.5B RULER context sweep
```
results/emnlp_rolealign_v2/runs/ruler_ours_asym_1p5b_ctx{4096,8192,16384,32704}_s{1234,1235,1236}/
results/emnlp_rolealign_v2/runs/ruler_v2fix_1p5b_ctx{8192,16384,32704}_s{1234,1235,1236}/
```

### 7B RULER context sweep
```
results/emnlp_rolealign_v2/runs/ruler_ours_asym_7b_ctx{4096,8192,16384,32704}_s{1234,1235,1236}/
results/emnlp_rolealign_v2/runs/ruler_v2fix_7b_ctx{8192,16384,32704}_s{1234,1235,1236}/
```

### 8B RULER context sweep
```
results/emnlp_rolealign_v2/runs/ruler_ours_asym_8b_ctx{4096,8192,16384,32704}_s{1234,1235,1236}/
results/emnlp_rolealign_v2/runs/ruler_v2fix_8b_ctx{8192,16384,32704}_s{1234,1235,1236}/
```

### EVL fix 验证（emnlp_defense_v1）
```
results/emnlp_defense_v1/runs/ruler_fp16_fix_verify/profile_ruler_fp16_*.csv
results/emnlp_defense_v1/runs/ruler_ra_fix_verify/profile_ruler_int4_ours_asym_*.csv
results/emnlp_defense_v1/runs/ruler_ra_v3_ctx{8192,16384,32704}_1p5b/
results/emnlp_defense_v1/runs/ruler_kivi_4k_1p5b/
```

---

## 分任务成绩（NIAH / VT / CWE / QA）

| 子任务 | 4K FP16 | 4K INT8-ours | 修复前 | 修复后 |
|--------|---------|--------------|-------|-------|
| S-NIAH | 100% | 100% | — | — |
| MK-NIAH | 98.8% | 98.8% | — | — |
| VT | ~70% | ~70% | — | — |
| **CWE** | 38% | 38% | **0%** | **38%** (EVL-047 fix) |
| QA | ~30% | ~30% | — | — |

**EVL-047 修复详情**：CWE 子任务在 32K 上触发 prompt budget 溢出 (32704+128>32768)。修复用 `_effective_prompt_budget()` 动态计算。

---

## 评分口径

- `ruler_score` — 总分（所有子任务加权平均）
- `ruler_{niah,vt,cwe,qa}_score` — 单个子任务分数

**所有数字使用 EVL-042 修复后的计算口径**（之前的 legacy 数据因总分 bug 偏低 2-3pp）。

---

## 答辩防御点

**Q**: "RULER 为什么比 FP16 略高？"
**A**: "24.45 vs 24.38 的差异在 Bootstrap CI 内（±0.81）。不是 INT8 更好，而是统计噪声。但重要的是**没有显著降级**——这是 Claim 1 的证据。"

**Q**: "CWE 子任务以前 0% 是怎么回事？"
**A**: "EVL-047 bug：CWE 子任务在 seq_len=32K 时触发 prompt budget 溢出（32704+128>32768），所有样本失败。修复后稳定在 38%——这个数字本身反映了 CWE 任务的固有难度，不是 INT8 的问题。"
