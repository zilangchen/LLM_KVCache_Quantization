# [DEPRECATED 2026-04-18 05:46] Phase 1 官方 LongBench 主表 v2（Qwen2.5-1.5B，已排除 kivi_style）

> ⚠️ **此文件已废弃** — 取代者：`phase1_main_table_merged.md`。
> 废弃原因：ENG-045-v2 补丁后重跑证实修前/修后 kivi_style 分数精确一致（9.23/4.87/6.93 完全匹配），
> 证明 ENG-045 是**保守告警**而非"silent data loss"，kivi_style 数据**完全可信**无需隔离。
> 保留此文件仅作诊断过程的历史档案。
>
> **原隔离假设（已被证伪）**：ENG-045 在 LongBench 非 fused 路径下静默丢 token（每个 decode step 丢弃 4096 个历史 token），结果不可信，已隔离等待修复后重跑。

| task | metric | fp16 | int8_ours | int4_ours_asym |
|---|---|---|---|---|
| gov_report | rouge_l | 9.21 | 9.25 | 8.83 |
| ↳ Δ vs fp16 |  | (基线) | +0.4% | -4.1% |
| hotpotqa | f1 | 4.90 | 5.27 | 4.96 |
| ↳ Δ vs fp16 |  | (基线) | +7.6% | +1.2% |
| narrativeqa | f1 | 7.07 | 7.13 | 7.05 |
| ↳ Δ vs fp16 |  | (基线) | +0.8% | -0.2% |

## 诊断记录

- **kivi_style ENG-045 触发**（2026-04-18 远端实证）：
  - gov_report: 7056 次 warning
  - hotpotqa: 5292 次 warning
  - narrativeqa: 1764 次 warning
- 根因：generate_loop.py:1294-1315 non-fused 路径 k.shape[2]=4097 时只追加最后 1 token
- 原始（含 kivi_style 污染）主表保留在 docs/phase1_main_table.md，不作为闸门判据
