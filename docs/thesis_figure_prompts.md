# 论文配图 Prompt 库

> 适用对象：`thesis/` 主文与附录中的全部核心图。  
> 使用原则：Prompt 只用于生成布局与视觉草图，最终定稿必须由脚本或 TikZ 重建，不允许直接把 AI 生成图当作终稿提交。

## 全局约束

以下约束适用于所有 prompt：

```text
Create a publication-quality vector scientific figure for a top-tier ML/NLP paper. Use a white background, clean academic styling, editable sans-serif text, English labels only, embedded fonts, no Chinese text inside the figure, no garbled characters, no clipping, no watermark, no emoji, no decorative icons, no 3D, and no invented numbers. Use a colorblind-safe palette with fixed semantic mapping: FP16 #334155, INT8-Baseline #F59E0B, INT8-Canonical #10B981, Symmetric INT4 #EF4444, MixedKV #8B5E34, KIVI-style #E11D48, INT4-RoleAlign #0F766E. Use thin axes, restrained grid lines, one shared legend outside the plotting area, and export in PDF/SVG style.
```

## 配色语义

| 语义 | 颜色 |
|---|---|
| FP16 / Reference | `#334155` |
| INT8-Baseline | `#F59E0B` |
| INT8-Canonical | `#10B981` |
| Symmetric INT4 / Failed path | `#EF4444` |
| MixedKV | `#8B5E34` |
| KIVI-style | `#E11D48` |
| INT4-RoleAlign | `#0F766E` |

## 图 1：引言论证总图

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch1_introduction.tex`

**目标**
- 把旧 roadmap / pipeline 图改成 argument figure。
- 明确 `INT4-RoleAlign` 是最终主结果，`INT8` 只是 canonical validation。

**Prompt**

```text
Design a left-to-right or top-to-bottom scientific argument figure with five rounded rectangular nodes connected by thin arrows. The nodes should read: “Wrong Numerical Proxy”, “Behavior-Aligned Principle”, “INT8 Canonical Validation”, “Key-Dominant Diagnosis”, and a visually emphasized final node “INT4-RoleAlign”. Intermediate nodes should use muted academic colors, while the final node should use a strong dark-teal highlight. The figure must read as a thesis argument map rather than a workflow diagram. Keep each node to at most two short lines.
```

## 图 2：方法层级总图

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/chapters/ch3_method.tex`

**目标**
- 表达 `attention-KL` 的 hierarchy，而不是离线/在线 flat pipeline。
- `inv_tau` 明确为 optional branch。
- `Triton` 明确为 deployability support。

**Prompt**

```text
Design a hierarchical scientific framework figure with three layers. Top layer: one central principle box labeled “Attention-KL as Calibration Objective and Diagnostic Lens”. Middle layer: two branches, “INT8 Canonical Path” and “Low-Bit Diagnosis Path”. Bottom layer: a large highlighted box “INT4-RoleAlign” as the main method outcome, and a smaller secondary box “Triton Deployability Support”. Add a dashed optional branch “Inverse Temperature Correction (Optional)” with visibly weaker emphasis. The figure should look like a principle hierarchy, not a flat pipeline.
```

## 图 3：`inv_tau` 稀疏热图

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/ch3_invtau_heatmap.pdf`

**目标**
- 强调“只有少数 head 被校正”的稀疏性。
- 明确这是 optional enhancement，而不是主方法。

**Prompt**

```text
Create a sparse scientific heatmap showing per-layer per-head inverse temperature deviations from 1.0. Most cells should be neutral light gray to indicate “no correction needed”, and only a handful of active cells should be highlighted with annotated values such as 0.50, 0.70, or 0.85. Add a compact side annotation panel reading “few adjusted heads” with a percentage summary. The visual message should be sparsity, not a dense heatmap.
```

## 图 4：Claim 1 主质量图

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/main_quality_dashboard.pdf`

**目标**
- 只服务 Claim 1。
- 明确 `attention-KL` 是正确对象，`INT8` 是 canonical validated instance。
- 去掉旧 dashboard 负担，不再主打 RULER。

**Prompt**

```text
Create a clean publication-quality multi-panel figure for Claim 1 only. Panel (a): perplexity at 32K. Panel (b): Needle pass rate versus context length. Panel (c): LongBench-style synthetic proxy score versus context length. Show only FP16, INT8-Baseline, INT8-Canonical, KIVI-style, and one symmetric INT4 failure anchor. The figure should emphasize principle validation rather than act as a full experiment dashboard.
```

## 图 5：主效率图

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/main_efficiency_dashboard.pdf`

**目标**
- 作为 deployability support。
- 只保留最关键的两个维度：TPOT 与 KV memory。

**Prompt**

```text
Create a two-panel scientific efficiency figure. Panel (a): decode latency versus context length. Panel (b): KV-cache memory versus context length. Focus on FP16, INT8-Baseline, INT8-Canonical, and optionally one low-bit reference. Add one concise annotation at 32K highlighting the speed difference and memory reduction. The figure should read as deployment evidence, not a dashboard.
```

## 图 6：K/V 机制诊断图

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/kv_ablation_summary_ruler.pdf`

**目标**
- 强调 `Key-dominant`。
- MixedKV 作为 bridge，而不是与 RoleAlign 平级的方法图。

**Prompt**

```text
Create a grouped-bar diagnosis figure for Key-versus-Value sensitivity in low-bit KV quantization. X-axis: three model families. Bars: K-only, V-only, K4V8, and MixedKV. Y-axis: one robust degradation metric such as perplexity degradation or retrieval pass rate. The visual takeaway must be that Key-side low-bit perturbation dominates failure. Keep labels short and remove any sentence-length note boxes.
```

## 图 7：K/V 支撑热图

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/kv_error_heatmap_pair_int4_mixed_kv.pdf`

**目标**
- 作为 supporting evidence，不抢 Claim 1 的 `attention-KL` 主位。
- 如果没有真实 `attention-KL` 数据，则明确画成 reconstruction-error comparison。

**Prompt**

```text
Create a three-panel mechanistic diagnosis figure. Left panel: layer-head heatmap for Key-side reconstruction error or behavior drift. Middle panel: corresponding Value-side heatmap. Right panel: layer-wise mean comparison showing stronger Key-side degradation concentration. Use one shared colorbar, a clean sequential colormap such as cividis, and generous spacing. Avoid the look of an internal debugging heatmap.
```

## 图 8：RoleAlign 主结果 Hero Figure

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/rolealign_summary.pdf`

**目标**
- 成为全文最强视觉锚点。
- 直接强化三组 headline：`Needle 100%`、`0.3%–1.2% PPL degradation`、`75% KV compression`。

**Prompt**

```text
Create a hero figure for the main result “INT4-RoleAlign”. Use a polished vector style with a narrow top summary ribbon and two or three main panels below. The ribbon should visually highlight: “100% Needle Pass Rate”, “0.3%–1.2% PPL Degradation”, and “75% KV Cache Compression”. Panel (a): retrieval or PPL comparison across three model families. Panel (b): LongBench-style synthetic quality versus KIVI-style INT4. INT4-RoleAlign must be the most visually salient method in the entire figure.
```

## 附录图 1：RULER 曲线

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/ruler_pass_rate_vs_context.pdf`

**Prompt**

```text
Create a compact appendix line chart for RULER pass rate versus context length. Show only FP16, INT8-Canonical, symmetric INT4, KIVI-style, and INT4-RoleAlign where available. Use a minimal legend outside the plot and emphasize supplementary comparison rather than headline presentation.
```

## 附录图 2：LongBench-style synthetic 曲线

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/longbench_score_vs_context.pdf`

**Prompt**

```text
Create an appendix-quality line chart titled “LongBench-style Synthetic Score vs Context Length”. Show only a reduced set of methods, use a tighter y-axis to reveal small differences, and place one shared legend below the plot. Make sure the title explicitly says “LongBench-style Synthetic”.
```

## 附录图 3：Needle depth heatmap

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/needle_depth_grid.pdf`

**Prompt**

```text
Create a 2x2 appendix heatmap figure for retrieval pass rate over needle depth and context length. Keep only informative methods, remove constant-success rows, and annotate only exceptional cells rather than all cells. Use a colorblind-safe sequential colormap such as viridis, with the 32K panel as the visual focal point.
```

## 附录图 4：Needle exact-match 曲线

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/needle_exact_match_vs_context.pdf`

**Prompt**

```text
Create a clean appendix line chart for exact-match retrieval versus context length. Limit the methods to the most informative subset, replace the large boxed legend with endpoint labels where possible, and emphasize that this is a stricter supplementary metric.
```

## 附录图 5：TPOT gain 相对图

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/latency_tpot_gain_vs_fp16.pdf`

**Prompt**

```text
Create an appendix-quality diverging chart for relative TPOT change versus FP16. Use a strong zero line, clear positive/negative semantics, and concise endpoint annotations only at the final context length. The plot should immediately distinguish speedup from slowdown.
```

## 附录图 6：吞吐量三联图

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/appendix_throughput_dashboard.pdf`

**Prompt**

```text
Create a three-panel appendix throughput figure with aligned panel widths and one shared legend below. Panels: total throughput, per-sequence throughput, and prefill throughput versus batch size. Highlight only the most important methods in strong colors and render secondary methods in muted gray.
```

## 附录图 7：显存二联图

**对应文件**
- `/Users/chenzilang/Desktop/LLM_KVCache_Quantization/thesis/figures/appendix_memory_dashboard.pdf`

**Prompt**

```text
Create a two-panel appendix memory figure matching the style of the throughput appendix figure exactly. Panel (a): KV-cache memory versus batch size. Panel (b): peak GPU memory or relative memory savings, whichever yields clearer separation. Emphasize how memory savings translate into larger supported batch sizes.
```

## 禁止项清单

以下内容在所有图中都禁止出现：

- 中文直接渲染进图中
- 乱码、裁切、字体缺失、线条重叠
- 水印、品牌 logo、emoji、装饰性 icon
- 3D、渐变、发光、厚阴影
- AI 虚构数据、虚构坐标、虚构公式
- 长段注释框、整句堆叠到图内
- 与论文主线不一致的命名

