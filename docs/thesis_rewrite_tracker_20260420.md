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

## Codex Review（Phase-level 纪律）

**每段改写完后必须调用 Codex Review**（CLAUDE.md §5.1 双重审查的"审查 1"）。

**具体调用方式、命令对比、正确 prompt 模板、常见错误陷阱** → 见**全局规则 `~/.claude/CLAUDE.md` §4**（2026-04-20 修订，含 Bash companion script 路径、`review` vs `adversarial-review` 区别、Codex 工作原理）。

**本 tracker 不 hardcode 调用方式**（规则在 `~/.claude/CLAUDE.md` §4 单一维护）。

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

## Phase 1 — 研究背景（Ch1 §1.1/§1.2/§1.4；§1.3 contribution 段与 Ch5 一起放 Phase 8）

| # | 任务 | 状态 | 依赖 |
|---|---|---|---|
| 1.1 | Ch1 §1.3 重写 RQ1-3 + C1-3 段 | ⏳ | 延到 Phase 8（与 Ch5/Abstract 一起写） |
| 1.2 | [MOVED TO Phase 8] Ch5 §5.1/§5.4 重写 Contribution Summary | ⏳ | Phase 8 最后写 |
| 1.3 | Ch1 §1.2 改写（error decomp + 假设 H + behavior framework） | ✅ | 2 轮 Codex adversarial-review pass |
| 1.4 | Ch1 §1.3 国内外现状（融合核降 C2 instance） | ✅ | commit `5f8b526` |
| 1.5 | Ch1 §1.4 RQ 段（3 问题 → RQ1-3） | ✅ | commit `5f8b526` |
| 1.6 | Ch1 §1.4 Roadmap（对齐 6 模型 + 5 task） | ✅ | commit `5f8b526` |
| 1.7 | Ch1 xelatex 编译通过 | ⬜ | 延到 Phase 9 统一编译 |
| 1.8 | Phase 1 commit | ✅ | tag `thesis-m-plus-entry-point` |

---

## Phase 2 — 方法层（Ch3 + 图 ① ③）

| # | 任务 | 状态 | 图表 |
|---|---|---|---|
| 2.1 | Ch3 §3.1 problem formulation + 误差分解公式 `eq:ch3-error-decomp` | ✅ | 图 ① 延 Phase 9（TikZ） |
| 2.2 | Ch3 §3.2 calibration method（保留现结构） | ✅ | 图 ③ 延 Phase 9（TikZ） |
| 2.3 | Ch3 §3.3 Behavior-Guided Allocator 3 子节 | ✅ | 无图 |
| 2.4 | Ch3 §3.4 AutoK 段 + cov80 公式 `eq:ch3-autok-cov` | ✅ | 无图 |
| 2.5 | 删除旧 inv_tau subsection（sec:ch3-invtau + figure ch3_invtau_heatmap） | ✅ | — |
| 2.6 | Triton 节 title 降级为 "INT8 Canonical Path 的系统落地" | ✅ | — |
| 2.7 | §本章小结 重写（新 framework 两层叙事） | ✅ | — |
| 2.8 | Ch3 xelatex 通过 | ⬜ | 延到 Phase 9 |
| 2.9 | Phase 2 commit | ✅ | commit `5f8b526` |

---

## Phase 3 — 实验 Part A（Ch4 §4.1-§4.2）

| # | 任务 | 状态 | 图表 |
|---|---|---|---|
| 3.1 | Ch4 preamble 重写（3-Contribution → RQ1-3 + C1-3） | ✅ | — |
| 3.2 | Ch4 §4.1 模型表扩到 6 模型（加 Qwen2.5-3B）+ clean-provenance pin 说明 | ✅ | tab:ch4-models |
| 3.3 | Ch4 §4.1 基线表清理 inv_tau 温度校正列 | ✅ | tab:kv-modes |
| 3.4 | 写 `scripts/thesis/make_table_int8_canonical.py` + 生成 **T1** | ✅ | T1（int8_ours mean Δ=+0.02 加粗） |
| 3.5 | Ch4 §4.1.5 INT8 Canonical Path 保真度段 + 引用 T1 | ✅ | T1 |
| 3.6 | 写 `scripts/thesis/make_table_int4_kivi.py` + 生成 **T2** | ✅ | T2（4 模型 PPL+Needle+Δ） |
| 3.7 | 手工表 **S3** RoleAlign vs KIVI 设计差异 | ✅ | S3（5 维度对比） |
| 3.8 | Ch4 §4.2 大砍 + 重写（1470 行 → 450 行，-55%） | ✅ | — |
| 3.9 | Ch4 §4.2.1 K/V Role Mechanism（保留图 ⑤ 数据+改 framing） | ✅ | 图 ⑤ 沿用 |
| 3.10 | Ch4 §4.2.2 INT4 跨模型对比（引用 T2+S3） | ✅ | T2, S3 |
| 3.11 | Ch4 §4.2.3 三层诚实分析（L1/L2/L3）+ §2.5 Hook 占位注释 | ✅ | — |
| 3.12 | Ch4 §4.1-§4.2 xelatex 通过 | ⬜ | 延到 Phase 9 |
| 3.13 | Phase 3 commit | 🟡 | 本 commit |

---

## Phase 4 — 实验 Part B（Ch4 §4.3 主章，最重要）✅

| # | 任务 | 状态 | 图表 |
|---|---|---|---|
| 4.1 | 写 `scripts/thesis/make_table_cross_model_compare.py` + 生成 **T3** ⭐⭐ | ✅ | T3（48 cells） |
| 4.2 | 写 `scripts/thesis/plot_sensitivity_heatmap.py` + 生成 **图 ④** ⭐⭐ | ✅ | 图 ④（4 模型 per-layer bits allocator decision） |
| 4.3 | 写 `scripts/thesis/plot_l2_pareto.py`（story 说"沿用"但实际需新写）+ 生成 **图 ⑦** | ✅ | 图 ⑦（3 subplot + callouts） |
| 4.4 | 写 `scripts/thesis/plot_regime_map.py` + 生成 **图 ⑧** | ✅ | 图 ⑧（4×4 heatmap + 红色 winner box） |
| 4.5 | Ch4 §4.3 cross-model regime 段 + 引用 T3/图 ④/图 ⑦/图 ⑧ | ✅ | 4 项；+2 display math equations（遵守新格式规则） |
| 4.6 | Ch4 §4.3 xelatex smoke PASS + Phase 4 commit | ✅ | main.pdf 90 → 93 pages |

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

## 最后一次更新：2026-04-20 22:XX — Hook L4_CLOSED + Codex 7 issues 全修

**Phase 后续修订（Phase 3-10 之后的修订）**：
- Hook closure（commit `1a65d46`）：Allocator-vs-KIVI 条件性语言全部清除，allocator 作为方法贡献保留
- Codex 7 issues 全修：provenance 口径精确化 / matched-budget → budget band 改口径 /
  Prompt-adaptive 附录 A/B 用 frozen CSV 重生 / Ch4 §4.6 从旧叙事 summary 重写为 behavior framework 贯通三层 /
  Ch3 tau⁻¹ 主体清理（在线推理段 + 两阶段搜索 subsection + 复杂度段 + 产物存储）/
  §4.1 scope 分层（6 model / 4 main / 1.5B canonical / 7B supporting + 5-task main 从 7-task benchmark 中选取）/
  附录 internal terms 清零（Gate C / OFF-PROTOCOL / idle-time）

**当前图表与画图文档的对齐说明**：
图表实际产出（main.pdf）的成图形态与本文档 §16 早期 spec 之间存在因数据可行性导致的调整，
正文 caption 已按实际成图对齐；
若后续需要重新生成任一图表，以 scripts/thesis/plot_*.py 的实际输出为准，
本文档 §11 / §16 的早期 spec 仅保留作设计意图参考。

## 前期更新：2026-04-20 04:31 — Phase 1 + Phase 2 + Phase 3 完成

- Phase 1 ✅ Ch1 §1.2 / §1.3 / §1.4（Codex adversarial-review 2 轮 pass）
- Phase 2 ✅ Ch3 全章重写（+140 行）
- Phase 3 ✅ Ch4 §4.1-§4.2 重写（1977 → 884 行，-55%）+ T1 / T2 / S3
- 下一步：Phase 4 = Ch4 §4.3 cross-model（T3 + 图④ + 图⑦ + 图⑧）
