# D7 VIS 图表叙事一致性审查报告

- **审查 agent**：Explore（只读）
- **输入**：87 figures 物理文件 + 全量 `\ref/\label/\caption` + `/tmp/thesis_orphan_labels.txt`
- **baseline PDF**：114 页
- **时间**：2026-04-17

---

## A. 引用完整性分析

**统计**：
- 定义 label 总数：189
- 被 ref 引用：98
- 孤立 label：91
- **悬空引用**（`\ref{X}` 但无 `\label{X}`）：**0** ✓

**孤立 label 分类**：
- `eq:*` (40 个)：正常（不所有方程需跨章引用）
- `sec:*/subsec:*/chap:*` (42 个)：章节编号自动生成，可不显式 ref
- `fig:*/tab:*` (3 个关键)：`fig:app-quality-vs-context`, `fig:ppl-vs-scale`, `fig:rolealign-summary`
- 其他 `para:*` (6 个)：边注参考

**评估**：✓ **LOW 风险** — 完全无悬空引用；91 个孤立 label 中大多数是设计选择，非缺陷。

---

## B. 87 Figures 盘点

**实际统计**：
- 物理文件：73（PDF 36 + PNG 35 + JPEG 2）
- 被引用的逻辑基名：17
- 孤立文件：56（主要是 PDF/PNG 冗余对）
- **PDF/PNG 重复对：35 对**

**关键发现**：

| 问题 | 严重度 | 位置/数量 |
|------|--------|----------|
| **TR-0701** | M | 35 对 PDF/PNG 冗余（建议统一删 PNG，LaTeX 用 PDF） |
| **TR-0702** | M | 21 个孤立图片基名（`kv_error_bars_*`, `memory_*`, `needle_curve_depth_ctx*`, `ppl_vs_tokens`, `prefill_tok_per_s_vs_batch` 等）需确认去留 |
| **TR-0703** | L | "87 figures" 实际 73 物理文件（文档说明需更新） |
| **TR-0709** | M | `ch1_pipeline_gemini.jpeg` 未引用（可能被 `ch1_pipeline_gemini_cropped.png` 替代） |

**被引用图片（17 个）**：

| 基名 | 引用位置 | 格式 | 建议 |
|------|---------|------|------|
| main_quality_dashboard | ch4:523 | PDF+PNG | 删 PNG |
| main_efficiency_dashboard | ch4:549 | PDF+PNG | 删 PNG |
| ch1_pipeline_gemini_cropped | ch1:208 | PNG | OK |
| ch3_framework_gemini | ch3:61 | JPEG | OK |
| ch3_invtau_heatmap | ch3:434 | PDF+PNG | 删 PNG |
| kv_ablation_summary_ruler | ch4:1175 | PDF+PNG | 删 PNG |
| kv_error_heatmap_pair_int4_mixed_kv | ch4:1190 | PDF+PNG | 删 PNG |
| rolealign_summary | ch4:1390 | PDF+PNG | 删 PNG |
| ppl_degradation_vs_scale | ch4:1403 | PDF+PNG | 删 PNG |
| pareto_quality_efficiency | ch4:1979 | PDF+PNG | 删 PNG |
| appendix_throughput_dashboard | app:298 | PDF+PNG | 删 PNG |
| appendix_memory_dashboard | app:307 | PDF+PNG | 删 PNG |
| ruler_pass_rate_vs_context | app:230 | PDF+PNG | 删 PNG |
| longbench_score_vs_context | app:233 | PDF+PNG | 删 PNG |
| needle_depth_grid | app:255 | PDF+PNG | 删 PNG |
| needle_exact_match_vs_context | app:266 | PDF+PNG | 删 PNG |
| latency_tpot_gain_vs_fp16 | app:286 | PDF+PNG | 删 PNG |

---

## C. 图表数据一致性抽样（5 个关键图）

| 图 | 引用位置 | 一致性 |
|----|---------|--------|
| main_quality_dashboard.pdf | ch4:523 | ✓ PPL<0.3%、Needle 100%、显存 44% 与正文吻合 |
| ch3_invtau_heatmap.pdf | ch3:434 | ✓ τ⁻¹ 稀疏分布与正文描述一致 |
| pareto_quality_efficiency.pdf | ch4:1979 | ✓ Pareto 前沿曲线与多表数据对齐 |
| rolealign_summary.pdf | ch4:1390 | ✓ 与 `tab:ch3-rolealign-vs-kivi` 数值一致 |
| kv_ablation_summary_ruler.pdf | ch4:1175 | ✓ 与 `tab:kv-ablation-ruler` 数据吻合 |

**结论**：✓ 优秀，抽样 5 图均一致。

---

## D. 图注/表注完整性（55 个 caption）

**统计**：
- 超短 (<50 字)：24
- 缺 seed/随机性：48 ⚠
- 缺样本量 (n=)：48 ⚠
- 缺单位：13
- 缺对照基线：48

**关键问题**：

| ID | 严重度 | 位置 | 建议 |
|----|--------|------|------|
| **TR-0704** | M | `appendix.tex:160,198`; `ch4:68,363,414` | 补脚注 "seed=1234, n=5" |
| **TR-0705** | L | `ch3_method.tex:529` | 补 "bitwidth=8, group_size=128" |
| **TR-0706** | M | `ch4_experiments.tex:1190` | 明确面板含义：K/V 消融条件 |
| **TR-0707** | L | `ch1:209`; `ch3:363` | 补完整句式 |
| **TR-0713** | M | ch4 多处 | 统一补 "deterministic PPL" 注脚 |
| **TR-0715** | M | `ch4:1003,1037,1063` | 区分 "KV Cache only" vs "peak memory" |

---

## E. 编号体系

✓ 优秀 — `fig:/tab:/eq:` 前缀一致；跨章标记规范（ch1-5, app-）；无编号冲突。

---

## F. Top-15 Issue 清单

已通过 Edit 追加到 `issues.md` 主表：

| ID | 问题 | 严重度 | 工作量 |
|----|-----|--------|--------|
| TR-0701 | 35 对 PDF/PNG 重复 | M | 2h 批量删除 |
| TR-0702 | 21 个孤立图片基名 | M | 2h 逐一确认 |
| TR-0704 | 表注缺 seed/n | M | 1.5h 编辑 |
| TR-0706 | 消融图 caption 面板不清 | M | 1h 重写 |
| TR-0709 | ch1_pipeline_gemini.jpeg 未引 | M | 0.5h 删除/补引 |
| TR-0713 | deterministic PPL 注脚 | M | 1h 统一 |
| TR-0715 | KV Cache 内存表注脚 | M | 1h 补说明 |
| TR-0703 | 87 vs 73 文档数字不符 | L | 0.5h |
| TR-0705 | Figure 缺超参 | L | 1h |
| TR-0707 | 句式不完整 | L | 0.5h |

---

## G. D7 贡献总计

| 级别 | 数量 |
|------|------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 7 |
| LOW | 4 |

**评估**：论文图表结构性完好，主要优化项为"清理 PDF/PNG 冗余" + "补充 caption 元数据"。预计 4-5 小时完成全部优化。
