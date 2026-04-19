# Thesis Rewrite Progress Tracker（2026-04-20）

**目标**：按 M+ 方案（8 图 + 9 表 = 17 正文项）把旧版 thesis 重写为新故事线。

**状态图示**：⬜ TODO / 🟡 in-progress / ✅ DONE / ⚠️ BLOCKED

**配套文档**：
- 总计划 → 本 session 输出的 Phase 0-8 路线图
- 叙事主线 → `docs/thesis_story_20260420.md`
- 章节草稿 → `docs/thesis_chapter_drafts_20260420.md`
- 数据资产 → `docs/data_asset_inventory_20260420.md`
- 旧术语 audit → `docs/thesis_legacy_term_audit_20260420.md`

---

## Phase 0 — Pre-flight

| # | 任务 | 状态 | 备注 |
|---|---|---|---|
| 0a | Git safety net（commit 3 份 docs + tag `thesis-m-plus-entry-point`） | ✅ | commit `ab082e5` |
| 0b | `thesis/tables/` 目录（改表输出目标） | ✅ | 实际已存在 |
| 0c | 6 个 calibration JSON 完整性验证 | 🟡 | 1.5B/3B/14B/Mistral ✅；7B/8B 需用 RoleAlign JSON 替代或重新 regen |
| 0d | `references.bib` 核对 | 🟡 | KIVI/KVQuant/KVTuner ✅；TurboQuant/NVFP4/StreamingLLM 缺失（新故事 Ch2 提及，可补可不补） |
| 0e | 旧术语 audit | ✅ | 产出 `docs/thesis_legacy_term_audit_20260420.md` |
| 0f | 改写 tracker | ✅ | 本文档 |
| 0g | `scripts/thesis/_common.py` 共享模板 | 🟡 | 待写 |
| 0h | xelatex 基线编译验证 | ✅ | main.pdf 104 页，2026-04-18 已成功 |

---

## Phase 1 — 叙事骨架（Ch1 §1.3 + Ch6 §6.1）

| # | 任务 | 状态 | 依赖 |
|---|---|---|---|
| 1.1 | Ch1 §1.3 重写 RQ1-3 + C1-3 段 | ⬜ | drafts §2.3 |
| 1.2 | Ch6 §6.1 重写 Contribution Summary | ⬜ | drafts §7.2 |
| 1.3 | Ch1 / Ch6 xelatex 编译通过 | ⬜ | 1.1, 1.2 |
| 1.4 | Phase 1 commit | ⬜ | 1.3 |

---

## Phase 2 — 方法层（Ch3 + 图 ① ③）

| # | 任务 | 状态 | 图表 |
|---|---|---|---|
| 2.1 | Ch3 §3.1 problem formulation + 画 **图 ①** Attention decomp（TikZ） | ⬜ | 图 ① |
| 2.2 | Ch3 §3.2 calibration method + 画 **图 ③** Calibration pipeline（TikZ，去 inv_tau） | ⬜ | 图 ③ |
| 2.3 | Ch3 §3.3 allocator 段 | ⬜ | 无图 |
| 2.4 | Ch3 §3.4 AutoK 段 | ⬜ | 无图 |
| 2.5 | 删除旧 inv_tau heatmap 引用 | ⬜ | audit §Ch3 |
| 2.6 | Ch3 xelatex 通过 + Phase 2 commit | ⬜ | 2.1-2.5 |

---

## Phase 3 — 实验 Part A（Ch4 §4.1-§4.2）

| # | 任务 | 状态 | 图表 |
|---|---|---|---|
| 3.1 | Ch4 §4.1 setup + 手工表 **S1**（模型 GQA 配置，6 模型） | ⬜ | S1 |
| 3.2 | 写 `scripts/thesis/make_table_int8_canonical.py` + 生成 **T1** | ⬜ | T1 |
| 3.3 | Ch4 §4.1 INT8 canonical 段 + 引用 T1 | ⬜ | T1 |
| 3.4 | 写 `scripts/thesis/make_table_int4_kivi.py` + 生成 **T2** | ⬜ | T2 |
| 3.5 | 手工表 **S3** RoleAlign vs KIVI 设计差异 | ⬜ | S3 |
| 3.6 | Ch4 §4.2 INT4 vs KIVI 段 + 引用 T2/S3/图 ⑤ | ⬜ | 图 ⑤ 沿用 |
| 3.7 | Ch4 §4.1-§4.2 xelatex 通过 + Phase 3 commit | ⬜ | 3.1-3.6 |

---

## Phase 4 — 实验 Part B（Ch4 §4.3 主章，最重要）

| # | 任务 | 状态 | 图表 |
|---|---|---|---|
| 4.1 | 写 `scripts/thesis/make_table_cross_model_compare.py` + 生成 **T3** ⭐⭐ | ⬜ | T3 |
| 4.2 | 写 `scripts/thesis/plot_sensitivity_heatmap.py` + 生成 **图 ④** ⭐⭐ | ⬜ | 图 ④（需 6 calibration JSON） |
| 4.3 | 核实 `scripts/plot_l2_pareto.py` 生成 thesis-grade **图 ⑦** | ⬜ | 图 ⑦ 沿用 |
| 4.4 | 写 `scripts/thesis/plot_regime_map.py` + 生成 **图 ⑧** | ⬜ | 图 ⑧ |
| 4.5 | Ch4 §4.3 cross-model regime 段 + 引用 T3/图 ④/图 ⑦/图 ⑧ | ⬜ | 4 项 |
| 4.6 | Ch4 §4.3 xelatex 通过 + Phase 4 commit | ⬜ | 4.1-4.5 |

---

## Phase 5 — 实验 Part C（Ch4 §4.5 per-model + 图 ⑨）

| # | 任务 | 状态 | 图表 |
|---|---|---|---|
| 5.1 | 写 `scripts/thesis/make_table_mistral_autok.py` + **T4** | ⬜ | T4 |
| 5.2 | 写 `scripts/thesis/make_table_3b_early_layer.py` + **T5** | ⬜ | T5 |
| 5.3 | 写 `scripts/thesis/make_table_14b_toptier.py` + **T6** | ⬜ | T6 |
| 5.4 | 写 `scripts/thesis/plot_scale_trend.py` + **图 ⑨** | ⬜ | 图 ⑨ |
| 5.5 | Ch4 §4.5.1 Mistral 段（T4）+ §4.5.2 3B（T5）+ §4.5.3 14B（T6） | ⬜ | 3 表 |
| 5.6 | Ch4 §4.5 末尾插入图 ⑨ | ⬜ | 图 ⑨ |
| 5.7 | Ch4 §4.5 xelatex 通过 + Phase 5 commit | ⬜ | 5.1-5.6 |

---

## Phase 6 — Related Work + Discussion + Framework 图

| # | 任务 | 状态 | 图表 |
|---|---|---|---|
| 6.1 | Ch2 Related Work 重写 + 手工表 **T0** | ⬜ | T0 |
| 6.2 | Ch5 Discussion 重写（§5.1 heuristic / §5.2 regime map / §5.3 INT4 open question / §5.4 limitations / §5.5 implications） | ⬜ | 引用 T3 等 |
| 6.3 | Ch1 §1.4 Roadmap + 画 **图 ②** Framework overview（TikZ，最后画） | ⬜ | 图 ② |
| 6.4 | Ch2 + Ch5 + Ch1 §1.4 xelatex 通过 + Phase 6 commit | ⬜ | 6.1-6.3 |

---

## Phase 7 — Appendix + Abstract

| # | 任务 | 状态 | 图表 |
|---|---|---|---|
| 7.1 | Appendix 清理：删除 inv_tau / KL-MSE / efficiency TPOT 等废弃表 | ⬜ | N/A |
| 7.2 | 附录 P1：FP16 基线 + 评测协议 | ⬜ | N/A |
| 7.3 | 附录 P2：实验软硬件环境 | ⬜ | N/A |
| 7.4 | 附录 A：Prompt-adaptive 8B 5-task matrix | ⬜ | 附录表 A |
| 7.5 | 附录 B：Off-Protocol 1.5B/7B prompt-adaptive | ⬜ | 附录表 B |
| 7.6 | Abstract 中文重写（按 drafts §1.3） | ⬜ | 草稿已有 |
| 7.7 | Abstract 英文重写（按 drafts §1.4） | ⬜ | 草稿已有 |
| 7.8 | 完整 xelatex 编译 + PDF 目视检查 | ⬜ | 全章依赖 |
| 7.9 | Phase 7 commit | ⬜ | 7.1-7.8 |

---

## Phase 8 — 收尾

| # | 任务 | 状态 |
|---|---|---|
| 8.1 | iteration.md append Timeline entry（整个重写完成） | ⬜ |
| 8.2 | review_tracker.md 更新（如新 issue） | ⬜ |
| 8.3 | 打 tag `thesis-m-plus-v1` | ⬜ |
| 8.4 | （可选）thesis-m-plus-v1 PDF 备份 | ⬜ |

---

## 图表最终产出清单（M+ 方案 17 项对照 status）

| 编号 | 产物 | Phase | 脚本 / 来源 | Status |
|---|---|---|---|---|
| 图 ① | Attention error decomp | Phase 2 | `thesis/figures/fig1_error_decomposition.tex` (TikZ 新写) | ⬜ |
| 图 ② | Framework overview | Phase 6 | `thesis/figures/fig2_framework.tex` (TikZ 新写) | ⬜ |
| 图 ③ | Calibration pipeline | Phase 2 | `thesis/figures/fig3_calib_pipeline.tex` (TikZ 改写) | ⬜ |
| 图 ④ | Sensitivity heatmap | Phase 4 | `scripts/thesis/plot_sensitivity_heatmap.py` (新写) | ⬜ |
| 图 ⑤ | K/V role mechanism | Phase 3 | `thesis/figures/kv_ablation_summary_ruler.pdf` (沿用) | ⬜ |
| 图 ⑦ | Pareto front plot ⭐ | Phase 4 | `scripts/plot_l2_pareto.py` (沿用) | ⬜ |
| 图 ⑧ | Regime map viz | Phase 4 | `scripts/thesis/plot_regime_map.py` (新写) | ⬜ |
| 图 ⑨ | Quality/PPL vs Scale | Phase 5 | `scripts/thesis/plot_scale_trend.py` (新写) | ⬜ |
| 表 T0 | Related Work 对比 | Phase 6 | 手工 LaTeX | ⬜ |
| 表 S1 | 模型 GQA 配置 | Phase 3 | 手工 LaTeX | ⬜ |
| 表 S3 | RoleAlign vs KIVI 差异 | Phase 3 | 手工 LaTeX | ⬜ |
| 表 T1 | INT8 Canonical vs FP16 | Phase 3 | `scripts/thesis/make_table_int8_canonical.py` (新写) | ⬜ |
| 表 T2 | INT4 vs KIVI Cross-Model | Phase 3 | `scripts/thesis/make_table_int4_kivi.py` (新写) | ⬜ |
| 表 T3 | Cross-Model Main ⭐⭐ | Phase 4 | `scripts/thesis/make_table_cross_model_compare.py` (新写) | ⬜ |
| 表 T4 | Mistral AutoK | Phase 5 | `scripts/thesis/make_table_mistral_autok.py` (新写) | ⬜ |
| 表 T5 | 3B Early-Layer Rescue | Phase 5 | `scripts/thesis/make_table_3b_early_layer.py` (新写) | ⬜ |
| 表 T6 | 14B Top-Tier | Phase 5 | `scripts/thesis/make_table_14b_toptier.py` (新写) | ⬜ |
| 附录 A | Prompt-adaptive 8B | Phase 7 | `scripts/thesis/make_appendix_prompt_adaptive.py` (新写) | ⬜ |
| 附录 B | Off-Protocol | Phase 7 | `scripts/thesis/make_appendix_prompt_adaptive_offprotocol.py` (新写) | ⬜ |

---

## Blocker 记录

**当前 blocker**：无硬 blocker，但有以下 **soft blocker** 需要改章节时 decision：

1. **7B/8B INT8 KL calibration JSON**（图 ④ 依赖）：
   - 7B 有 `kv_calib_kl_b10_7b_s*` 但不是 pin=`ddada19` 版本
   - 8B **无 INT8 KL calibration**（只有 `kv_calib_rolealign_8b_v3.json` INT4）
   - **决策**：Phase 4 改图 ④ 时如果 6 模型 sensitivity 需要同构化，可能需要从 RoleAlign JSON 里抽 sensitivity proxy；或者图 ④ 降为 5 模型（暂跳过 8B）。
   - **替代方案**：改 `plot_sensitivity_heatmap.py` 先用可用的 5 模型（1.5B/3B/7B/14B/Mistral，去掉 8B）画，Caption 注明"8B sensitivity 因 calibration 格式差异未纳入"。

2. **TurboQuant / NVFP4 cite**（Ch2 §2.2 提及）：
   - 不强依赖（新故事只在 Discussion 提及）
   - 如果 Ch2 写作时决定保留这两项 cite，需要补 bib entry。

---

## 最后一次更新：2026-04-20 Phase 0 完成时
