# ExecPlan — Thesis Figure Optimization

## 1. Task Alignment

- Goal:
  - 将论文图像从“可用”提升到“投稿级/高质量学位论文可读”，重点解决主文图分散、位图缩放后发虚、信息密度不足、图例依赖过强、K/V 机制图表达不直观的问题。
- Non-goals:
  - 不新增实验，不修改实验数据，不改结论口径。
  - 不迁移论文模板，不做整篇结构重写。
  - 不追求“保留所有旧图文件”；允许用更高信息密度的新图替换旧图。
- Background:
  - 当前主文与附录共引用 20+ 张图，主文关键图主要来自 `scripts/generate_thesis_figures.py`，统一性已有基础，但大多数为 PNG 输出；heatmap 由 `scripts/plot_attention_kl_heatmap.py` 单独生成，风格与主图不统一。
  - 主文当前将质量与效率结论拆成多张单图，读者需要来回跳图；附录存在 4 张 Needle depth 热图和 5 张 batch 扩展图，重复度高。

## 2. Constraints

- Environment constraints:
  - 只使用现有 `results/*/tables`、`results/attention_kl/*.json` 和 `results/plots/attention_kl/*.pdf` / `thesis/figures/*` 数据源。
  - 本地可运行 Python / matplotlib / xelatex / bibtex。
- Repository constraints:
  - 遵守 `objective.md`：主线突出 `INT8-ours`，`MixedKV` 为诊断驱动扩展，K/V 敏感性为诊断结论，不新增方法主张。
  - 只在统一脚本中生成图片，不手工改导出图。
  - 采用最小 diff：优先重用现有 figure 数据流与命名约定。
- Reproducibility constraints:
  - 所有新图必须可由脚本一键重建。
  - 主文和附录引用的最终图必须全部来自仓库脚本输出。
- Risk constraints:
  - 不允许因为图重排引入新的正文逻辑错误、缺图或 LaTeX 交叉引用错误。
  - 不允许为追求“好看”而降低数值可读性或删掉关键对照。

## 3. Deliverables

- Files to modify:
  - `scripts/generate_thesis_figures.py`
  - `scripts/plot_attention_kl_heatmap.py`
  - `thesis/chapters/ch4_experiments.tex`
  - `thesis/chapters/appendix.tex`
  - 如需要：`thesis/chapters/ch3_method.tex`（仅当 `ch3_invtau_heatmap` 路径/格式同步调整）
- Files to add:
  - 无强制新脚本；优先在现有脚本内扩展。
  - 允许新增少量新图文件名，例如：
    - `thesis/figures/main_quality_dashboard.pdf`
    - `thesis/figures/main_efficiency_dashboard.pdf`
    - `thesis/figures/kv_ablation_summary_ruler.pdf`
    - `thesis/figures/needle_depth_grid.pdf`
    - `thesis/figures/appendix_throughput_dashboard.pdf`
    - `thesis/figures/appendix_memory_dashboard.pdf`
    - `thesis/figures/kv_error_heatmap_pair_int4_mixed_kv.pdf`
- Expected outputs/artifacts:
  - 主文由分散单图改为 2 个 dashboard + 1 个 K/V 机制总结图 + 1 个配对 heatmap。
  - 附录将 4 张 Needle depth 热图压缩为 1 张 2×2 图，将 5 张 batch 线图压缩为 2 张 dashboard。
  - 折线图/柱状图/分面图默认输出为 PDF 矢量；仅保留必要 PNG 预览或 heatmap 内部 raster。

## 4. Acceptance Criteria

- Functional checks:
  - `scripts/generate_thesis_figures.py` 能生成主文与附录所需新图。
  - `scripts/plot_attention_kl_heatmap.py` 能生成统一风格的双模型配对 heatmap 图。
  - `ch4_experiments.tex` 与 `appendix.tex` 的 `\includegraphics` 全部指向存在的文件。
- Regression checks:
  - 论文重新编译成功，无新增 `undefined reference` / `undefined citation`。
  - 不引入新的大 overfull；主文图页不因 dashboard 过宽而版式失衡。
  - 旧关键结论图仍有覆盖：质量保持、效率/显存、K/V 机制、heatmap。
- Reproducibility checks:
  - 所有最终引用图都可通过脚本重建，不依赖手工导出。
  - 新图的来源 CSV / JSON 在 caption 中可追溯。
- Documentation checks:
  - 主文和附录 caption 使用统一模板：对象 + 数据范围/单位 + 来源 + takeaway。
  - 主图和附录图的变量命名、单位格式、图例顺序一致。

## 5. Execution Steps

1. 重构 `scripts/generate_thesis_figures.py` 的全局风格系统：
   - 统一字体、线宽、marker、网格、图例、色板。
   - 默认输出 PDF；保留按需 PNG 兼容开关。
   - 补充 reusable helper：panel 布局、终点标注、关键数值标注、共享 legend、共享 colorbar。

2. 重构主文图：
   - 新增 `main_quality_dashboard.pdf`：
     - 2×2 panel，包含 `Needle vs context`、`LongBench vs context`、`RULER vs context`、`PPL main-result comparison`。
     - 核心模式限制为 `FP16`、`INT8-baseline`、`INT8-ours`、`KIVI-style`，如图不拥挤则加入 `MixedKV`；INT4 失败模式只在最能说明边界的 panel 中出现。
   - 新增 `main_efficiency_dashboard.pdf`：
     - 默认 1×3 panel，包含 `TPOT vs context`、`KV memory vs context`、`peak memory vs context`。
     - 不再在主文中单独放 `latency_tpot_gain_vs_fp16`；若需要 gain，改为作为 panel inset 或附录补充。
   - 新增 `kv_ablation_summary_ruler.pdf`：
     - 使用 `results/emnlp_expansion_v1/tables/kv_ablation_ruler.csv`；
     - 形式采用分组条形图；
     - 每组为模型（1.5B / 7B / 8B），组内展示 `K-only`、`V-only`、`K4V8`、`MixedKV`；
     - 主文优先使用 RULER 版，LongBench 版若需要则下沉附录。

3. 重构 heatmap：
   - 扩展 `scripts/plot_attention_kl_heatmap.py`，支持同时接收 Qwen 与 LLaMA 两个 JSON，生成 `kv_error_heatmap_pair_int4_mixed_kv.pdf`。
   - 配对图统一 colormap、colorbar range、轴方向与标题模板。
   - 在图中增加轻量视觉提示：高误差层段框标或箭头，以及 layer-wise mean strip。
   - 旧单模型 heatmap 文件可保留，但主文默认改引用配对图；单模型图转附录或不再引用。

4. 压缩附录图：
   - 将 `needle_curve_depth_ctx4096/8192/16384/32704.png` 合并为 `needle_depth_grid.pdf`（2×2，共享 colorbar）。
   - 将 `throughput_tok_per_s_vs_batch`、`throughput_tok_per_s_per_seq_vs_batch`、`prefill_tok_per_s_vs_batch` 合并为 `appendix_throughput_dashboard.pdf`。
   - 将 `memory_kv_cache_vs_batch`、`memory_peak_vs_batch` 合并为 `appendix_memory_dashboard.pdf`。
   - 删除或停止引用与主文重复、但信息增量很小的单独图；保留 `needle_exact_match_vs_context` 仅在确有附录价值时继续引用，否则移除引用。

5. 调整 LaTeX 编排：
   - 在 `ch4_experiments.tex` 中按“主结果 → 质量总览 → 效率总览 → K/V 机制 → 配对 heatmap → MixedKV”顺序重排 figure。
   - 在 `appendix.tex` 中按“补充质量 → 扩展性 → 热图/机制补充”归类。
   - 全部新图 caption 统一说明：
     - 展示对象；
     - 模型/上下文/单位；
     - 数据来源（如 `results/emnlp_final_raw/tables/per_model/...` 或 `results/emnlp_expansion_v1/tables/...`）；
     - 一句 takeaway。

6. 生成与编译验证：
   - 重生成图；
   - 编译 thesis；
   - 检查图路径、分页、overfull、caption 自包含与视觉可读性。

## 6. Verification Commands

- Command:
  - `python scripts/generate_thesis_figures.py`
  - `python scripts/plot_attention_kl_heatmap.py --input results/attention_kl/attention_kl_int4_mixed_kv_qwen*.json results/attention_kl/attention_kl_int4_mixed_kv_*Llama*.json --out_dir thesis/figures`
  - `cd thesis && xelatex main.tex && bibtex main && xelatex main.tex && xelatex main.tex`
  - `rg -n "includegraphics" thesis/chapters/*.tex`
  - `rg -n "Overfull|Underfull|undefined" thesis/main.log`
- Expected result:
  - 新 dashboard / summary / pair heatmap 图全部生成成功。
  - thesis 编译成功，零 undefined。
  - 不出现缺图；overfull 不显著增加。
  - 主文图数量减少或持平，但质量/效率/KV 机制三条主线更集中。

## 7. Risk Register

- Risk:
  - Dashboard 信息过密，导致比原来更难读。
  - Impact:
    - 主文图虽然更少，但每张图阅读负担变大。
  - Mitigation:
    - 每个 dashboard 最多 3–4 panel；每 panel 最多 5 个方法；主角直接标注，非主角减少文本。

- Risk:
  - PDF 矢量输出引发字体嵌入或 CJK 字体兼容问题。
  - Impact:
    - 图内中文或数学符号在 LaTeX 中显示异常。
  - Mitigation:
    - 统一使用现有 matplotlib 字体链；必要时仅图内标题英文、caption 中文解释；保留兼容 PNG fallback 开关。

- Risk:
  - Heatmap 配对图统一 color scale 后，某一模型局部结构不明显。
  - Impact:
    - 可比性增强但单图内部细节变弱。
  - Mitigation:
    - 使用共享主色标 + layer-wise mean strip；必要时附录保留单模型图。

- Risk:
  - 附录删减过度，丢失完整性证据。
  - Impact:
    - 审稿人若追细节，证据不足。
  - Mitigation:
    - 只合并、不丢掉高信息量内容；被压缩的图保留可脚本重建能力。

- Risk:
  - LaTeX figure 重排导致浮动体位置异常或 overfull 回潮。
  - Impact:
    - 版面恶化、图文错位。
  - Mitigation:
    - 控制图宽两档；逐步编译检查；必要时使用 `figure*`/分页微调但不大改模板。

- Risk:
  - 新增 K/V summary 图与现有表结论不完全一致。
  - Impact:
    - 机制图反而造成表图冲突。
  - Mitigation:
    - 明确主文优先展示 RULER 版 summary，数据直接从 `kv_ablation_ruler.csv` 读取；LongBench 版仅在附录或不默认上线。

## 8. Open Questions (Need Re-confirmation)

- Question:
  - 主文是否允许将现有多张单图合并为 dashboard，并因此重排 figure 编号？
  - Option A:
    - 允许，按信息密度优先（推荐）
  - Option B:
    - 不允许，只在现有编号下做局部美化

- Question:
  - K/V 机制图主文优先展示哪一项？
  - Option A:
    - `RULER` 版 summary（推荐，机制更直观）
  - Option B:
    - `LongBench` 版 summary

- Question:
  - 附录是否允许删掉重复度高的旧单图，仅保留 dashboard 与高信息量图？
  - Option A:
    - 允许（推荐）
  - Option B:
    - 不允许，必须保留旧图并额外新增 dashboard
