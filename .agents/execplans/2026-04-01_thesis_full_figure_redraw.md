# ExecPlan — Thesis Full Figure Redraw

## 1. 问题陈述

- 现状：
  - 当前论文的文字主线已经基本完成重构，但图系统仍明显滞后于新的 narrative。
  - 主文关键图仍以旧资产为主，`main_quality_dashboard.pdf`、`main_efficiency_dashboard.pdf`、`kv_ablation_summary_ruler.pdf`、`kv_error_heatmap_pair_int4_mixed_kv.pdf`、`ch3_invtau_heatmap.pdf` 等时间戳仍为 2026-03-23；`rolealign_summary.pdf` 为 2026-03-25。
  - 最新 PDF 可编译，但主图仍存在三个系统性问题：
    1. 图的语义层级没有完全对齐“`INT4-RoleAlign` 为主角、`attention-KL` 为统一原则”的新主线；
    2. 多张主图仍为 dashboard / inventory 风格，而不是 thesis / hero / support figure；
    3. 图文件和整页 PDF 中存在字体/编码风险，必须显式验证“无乱码、无遮挡、无裁切、无不合适内容”。
- 期望：
  - 对论文当前引用的全部图进行逐张重绘或重排，使其满足顶刊/顶会发表级别的视觉规范、表达精度和版式一致性要求。
  - 为每一张图建立统一的语义、配色、布局和字体规则；为 AI 辅助制图提供逐图 prompt；最终以脚本可重建的 PDF/SVG 风格输出为准。
  - 主文图应明确分层：
    - Thesis / argument figures：Ch1、Ch3
    - Hero figure：RoleAlign 主结果
    - Support figures：质量、效率、诊断、附录补充
- 为什么现在做：
  - 文字主线已经改对，下一瓶颈就是图没有跟上，直接影响审稿人的第一印象、信息抓取速度和“paperization”程度。
  - 用户已明确要求“逐个绘制每一幅图”，并允许联网参考案例；这是当前最值得集中处理的视觉与表达层改进。

## 2. objective.md 对齐映射

- 服务目标：
  - 对齐 `objective.md` 中的行为对齐框架定位、K/V 诊断结论、MixedKV 实用扩展和 INT4-RoleAlign 低比特扩展。
  - 强化论文对 EMNLP 2026 投稿的发表级质量要求。
  - 保持结果可复现：所有图必须由脚本或 TikZ 源重建，不能依赖手工不可追溯修改。
- 触碰边界：
  - 会修改绘图脚本、TikZ 图、部分 LaTeX caption/引用组织、可能新增统一配色/样式模块与 prompt 文档。
  - 不改实验数据、不新增实验、不改变统计口径、不改变论文核心 scientific claims。
- 已知边界冲突及处理假设：
  - `objective.md` 仍保留“INT8 为主框架 primary validated instance”的表述，而当前论文文本已切到“INT4-RoleAlign 为表层主角”。
  - 本轮仅重绘图，默认**服从当前已合入的论文文本与章节主线**，不额外改写 `objective.md` 的研究定位。

## 3. 目标与非目标

- 目标：
  - 重绘当前论文引用的全部图：
    - Ch1：`fig:ch1-pipeline`
    - Ch3：`fig:ch3-framework`、`fig:ch3-invtau-heatmap`
    - Ch4：`fig:main-quality-dashboard`、`fig:main-efficiency-dashboard`、`fig:kv-ablation-summary-ruler`、`fig:attn-kl-heatmap-pair`、`fig:rolealign-summary`
    - Appendix：`fig:app-ruler-vs-context`、`fig:app-longbench-vs-context`、`fig:app-needle-depth-grid`、`fig:app-needle-exact`、`fig:app-tpot-gain`、`fig:app-throughput-dashboard`、`fig:app-memory-dashboard`
  - 建立统一的图形风格系统：
    - 固定语义色板
    - 统一字体与字号
    - 统一图例、网格线、marker、注释框与 panel tag
    - 明确主文图与附录图的层级差异
  - 为每张图提供 AI 辅助布局 prompt，但最终以可控脚本输出为准。
  - 通过整页渲染验收“无乱码、无遮挡、无裁切、无不合适内容”。
- 非目标：
  - 不新增实验结果或重新跑实验。
  - 不重写整篇论文 narrative。
  - 不把本轮工作扩展为“全面改论文语言”或“结构再重排”。
  - 不依赖 AI 直接生成最终数值图，不接受无法编辑、无法复现实验数值的位图成品。

## 4. 约束与假设

- 环境约束：
  - 使用本地 Python + matplotlib + TikZ + LaTeX + Poppler。
  - 网络可用，可浏览官方论文页面/预印本参考案例。
- 仓库约束：
  - 必须遵守项目规则：先计划，待用户 `APPROVE PLAN` 后再实施。
  - 所有代码修改必须使用 `apply_patch`；图生成通过脚本执行，不手工覆盖未知来源文件。
  - `git add .` 禁止；本轮不主动 push。
- 复现性约束：
  - 所有最终图都必须能通过脚本或 LaTeX/TikZ 源重建。
  - 新增 prompt 仅用于辅助草图与布局参考，不作为最终结果唯一来源。
- 视觉约束：
  - 图内原则上只用英文短标签；正文 caption 可保留中文。
  - 输出以 PDF/SVG 风格为主；必要时中间 PNG 仅用于审查。
  - 必须避免乱码、裁切、文字重叠、水印、图例遮挡、过长句注释框。
- 假设：
  - 当前 `results/` 中已有生成这些图所需的数据表和 JSON。
  - 现有 `scripts/generate_thesis_figures.py`、`scripts/plot_attention_kl_heatmap.py`、`scripts/plot_rolealign_summary.py` 是主要改造入口。

## 5. 具体工作清单

### 5.1 参考案例研究（联网）

1. 选择 5–8 篇与本论文最接近、图质量强的顶会/顶刊论文作为视觉与叙事参考：
   - `KIVI`
   - `KVTuner`
   - `SmoothQuant`
   - `vLLM / PagedAttention`
   - `KVQuant`
   - `AWQ` / `QuaRot`
2. 总结可复用的绘图原则：
   - argument figure 的层级组织
   - hero figure 的信息密度
   - support figure 的降噪方式
   - colorblind-safe palette
   - caption 结构
3. 形成一页图形设计准则，作为后续绘图统一依据。

### 5.2 建立统一绘图风格层

修改或新增统一样式入口，供所有脚本复用：
- 统一色板：
  - FP16 / reference
  - INT8-baseline
  - INT8 canonical path
  - symmetric INT4 / failed path
  - MixedKV
  - KIVI-style
  - INT4-RoleAlign
- 统一字体、字号、轴线、网格、图例外置策略、panel tag。
- 统一文件输出规范：
  - PDF 为主
  - 命名稳定
  - 默认白底、无渐变、无 3D、无装饰 icon

### 5.3 逐图重绘：主文

#### Ch1 Argument Figure
- 文件：
  - `thesis/chapters/ch1_introduction.tex`
- 动作：
  - 进一步优化 TikZ 布局与视觉层次。
  - 使其更明确地成为 argument figure，而不是简单的竖向流程图。
  - 突出最终节点 `INT4-RoleAlign`，降低中间节点装饰性。
- 产出：
  - 更顶会化的引言总图。

#### Ch3 Principle Hierarchy Figure
- 文件：
  - `thesis/chapters/ch3_method.tex`
- 动作：
  - 将当前离线/在线 pipeline 重画为三层 hierarchy figure：
    - Principle
    - INT8 canonical path / low-bit diagnosis path
    - INT4-RoleAlign + Triton support
  - `inv_tau` 改为弱化的 optional branch。

#### Ch3 inv_tau Heatmap
- 文件：
  - `scripts/generate_thesis_figures.py` 或新增子函数
  - `thesis/chapters/ch3_method.tex`
- 动作：
  - 将其从“普通密集热力图”改为“稀疏偏离图”。
  - 更强调“只有少数 head 需要校正”的结论。
  - 若主文价值不足，则降级为附录图或主文缩小权重。

#### Ch4 Claim 1 Quality Figure
- 文件：
  - `scripts/generate_thesis_figures.py`
  - `thesis/chapters/ch4_experiments.tex`
- 动作：
  - 重画 `main_quality_dashboard.pdf`。
  - 从“总览 dashboard”改为更明确的 Claim 1 figure：
    - `PPL @32K`
    - `Needle vs context`
    - `LongBench-style synthetic`
    - 视情况保留或移除 `RULER`
  - 方法数压缩到最必要集合，避免视觉稀释。

#### Ch4 Efficiency Figure
- 文件：
  - `scripts/generate_thesis_figures.py`
  - `thesis/chapters/ch4_experiments.tex`
- 动作：
  - 重画 `main_efficiency_dashboard.pdf`。
  - 以 deployability support 为定位，压缩为 2–3 panel。
  - 弱化信息增量低的 panel，例如总峰值显存若区分度不足则转附录。

#### Ch4 K/V Diagnosis Summary
- 文件：
  - `scripts/generate_thesis_figures.py`
  - `thesis/chapters/ch4_experiments.tex`
- 动作：
  - 重画 `kv_ablation_summary_ruler.pdf`。
  - 使其更像 mechanism diagnosis figure，而非结果堆叠柱状图。
  - 减少句子型注释框，用更清晰的分组和视觉语义表示 “Key dominates”.

#### Ch4 Heatmap Pair
- 文件：
  - `scripts/plot_attention_kl_heatmap.py`
  - `thesis/chapters/ch4_experiments.tex`
- 动作：
  - 将当前以 reconstruction MSE 为中心的图改得更接近新的 principle。
  - 若数据允许，切换到 attention-KL / behavior drift 指标；若不允许，则至少在视觉与 caption 上弱化 “MSE 中心论述”。
  - 提升可读性，避免像 internal debug heatmap。

#### Ch4 Hero Figure
- 文件：
  - `scripts/plot_rolealign_summary.py`
  - `thesis/chapters/ch4_experiments.tex`
- 动作：
  - 重画 `rolealign_summary.pdf` 成为全文 hero figure。
  - 引入顶栏 summary ribbon 或等价布局，突出：
    - `Needle 100%`
    - `0.3%–1.2% PPL degradation`
    - `75% KV cache memory reduction`
  - 把 `Needle` 从 caption 搬进图主体。

### 5.4 逐图重绘：附录

- 文件：
  - `scripts/generate_thesis_figures.py`
  - `thesis/chapters/appendix.tex`
- 动作：
  - 统一附录图风格与主文图风格。
  - 明确附录图是 supplementary，不再使用“dashboard”这种过时命名。
  - 重点处理：
    - `ruler_pass_rate_vs_context.pdf`
    - `longbench_score_vs_context.pdf`
    - `needle_depth_grid.pdf`
    - `needle_exact_match_vs_context.pdf`
    - `latency_tpot_gain_vs_fp16.pdf`
    - `appendix_throughput_dashboard.pdf`
    - `appendix_memory_dashboard.pdf`

### 5.5 Prompt 库与图审查文档

- 新增一份逐图 prompt 文档，记录每张图的：
  - 设计目标
  - 推荐布局
  - 配色与视觉 emphasis
  - 英文图内标签约束
  - 禁止项（乱码、编造数值、长句子说明框等）
- 该文档用于后续复用和人工/AI 辅助迭代。

### 5.6 最终全页 PDF 审查

- 重新编译 thesis。
- 将所有含图页面渲染为 PNG。
- 逐页审查：
  - 是否有乱码
  - 是否有裁切
  - 是否有图例遮挡
  - 是否有不合适内容
  - 是否仍有旧 narrative 痕迹

## 6. 验收标准

- 功能验收：
  - 当前论文引用的全部图都完成重绘、重排或样式统一。
  - 图文件均可通过脚本/TikZ 重建。
  - 论文编译通过。
- 视觉验收：
  - 主文关键图达到投稿级学术风格：白底、统一色板、图例清晰、无多余装饰。
  - `INT4-RoleAlign` hero figure 足够突出，能在 5 秒内传达主结果。
  - `Ch1` 和 `Ch3` 图能明显传达 argument / hierarchy，而非旧式流程图。
- 精准表达验收：
  - 图中不夸大 claim，不编造新数字，不把支撑图画成主结果图。
  - `attention-KL`、`INT8 canonical validated instance`、`Key-dominant diagnosis`、`INT4-RoleAlign` 的层级关系在图中清晰。
- 稳定性验收：
  - 无乱码、无裁切、无字体丢失、无水印、无不合适内容。
  - 整页 PNG 检查通过。
- 文档验收：
  - 生成逐图 prompt 库。
  - caption 与图内语言风格统一。

## 7. 验证计划

- 命令：
  - `python scripts/generate_thesis_figures.py`
  - `python scripts/plot_attention_kl_heatmap.py ...`
  - `python scripts/plot_rolealign_summary.py`
  - `cd thesis && latexmk -g -xelatex main.tex`
  - `rg -n "includegraphics|fig:" thesis/chapters`
  - `pdftoppm -png thesis/main.pdf tmp/thesis_pages/page`
  - `pdftotext -f <page> -l <page> thesis/main.pdf -`
- 预期：
  - 全部目标图成功生成。
  - thesis 编译通过，无新增 undefined。
  - 关键图页无乱码、无遮挡、无裁切。
  - 图内文本全部可读、无异常符号。

## 8. 风险与边界情况

- 风险 1：图全量重绘会引入新的风格不一致
  - 概率：中
  - 影响：论文看起来像多套模板拼接
  - 缓解：先建立统一 style layer，再逐图改
  - 回滚：保留旧图文件与分支内 diff

- 风险 2：AI prompt 生成的草图存在错误标签或乱码
  - 概率：高
  - 影响：不满足投稿级精度要求
  - 缓解：AI 仅用于布局参考；最终图全部由脚本/TikZ 重建
  - 回滚：丢弃 AI 草图，只保留 prompt 文档

- 风险 3：Ch3/Ch4 图重构后与正文 claim 不完全一致
  - 概率：中
  - 影响：图文冲突
  - 缓解：每张图重绘后同步检查对应 caption 和正文前后文
  - 回滚：按图为单位逐个恢复

- 风险 4：Heatmap 指标升级到 attention-KL 需要额外数据整理
  - 概率：中
  - 影响：进度延迟
  - 缓解：先检查现有 JSON 是否包含 attention-KL；若缺失，采用“保留数据、重构视觉与 caption”的保守方案
  - 回滚：继续使用现有 MSE 数据，但明确降级为 support figure

- 风险 5：附录图全量重绘耗时大，挤压主文关键图时间
  - 概率：高
  - 影响：主图改完，附录风格仍旧混乱
  - 缓解：分两层优先级，先主文 8 张，再附录 7 张
  - 回滚：附录只做风格统一，不做大结构重画

- 风险 6：字体链或 CJK 输出在 PDF 中再次出现伪乱码
  - 概率：中
  - 影响：最终 PDF 质量不达标
  - 缓解：图内优先英文；用整页 PNG 审查而不是只看独立图
  - 回滚：切换到更稳的英文字体 + 中文只放 caption

- 风险 7：objective.md 与当前论文 narrative 有轻微不一致
  - 概率：中
  - 影响：图定位选择时出现摇摆
  - 缓解：本轮默认服从当前已合入的论文文本和最新章节叙事
  - 回滚：若用户要求回归 objective 原始定位，再单独调整图 hierarchy

## 9. 需确认问题

- 问题 1：图内文字语言
  - 选项 A：图内全部英文，caption 中文解释
  - 选项 B：图内继续保留中英混合
  - 默认推荐：A
  - 理由：最稳，最能避免乱码和字体兼容问题，也更接近顶会风格

- 问题 2：主文图是否允许替换现有图结构，而不是只做美化
  - 选项 A：允许按新 narrative 重构图结构
  - 选项 B：只允许保留原结构换样式
  - 默认推荐：A
  - 理由：仅美化无法解决当前 thesis / hero / support 层级错位问题

- 问题 3：附录图是否要求全部彻底重绘
  - 选项 A：主文彻底重绘，附录以风格统一为主
  - 选项 B：主文与附录全部同等力度重绘
  - 默认推荐：A
  - 理由：主文收益最高，附录先保证统一和无乱码即可

- 问题 4：AI prompt 的交付形式
  - 选项 A：写入仓库文档，逐图长期复用
  - 选项 B：仅在会话回复中给出
  - 默认推荐：A
  - 理由：便于复审、复用和交接

## 10. 里程碑拆分

1. 里程碑 1：参考案例研究 + 统一 style layer + prompt 文档骨架
2. 里程碑 2：重绘 Ch1 / Ch3 两张主结构图
3. 里程碑 3：重绘 Ch4 的 quality / efficiency / diagnosis / hero 四类主图
4. 里程碑 4：重绘或统一附录图
5. 里程碑 5：编译 thesis + 全页 PNG 审查 + caption/术语统一收尾
