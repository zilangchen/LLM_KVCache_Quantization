# Phase 1 数据到论文的 3 种集成方案

**生成时间**: 2026-04-18 05:15（编号 2 实验进行中）
**用途**: 不论最终停点在哪里，都有一份现成的论文修改方案可以立即套用。

---

## 场景 A：停在编号 4 —— v6-stable（"诊断 + 官方评测补强"版本）

**触发条件**:
- 编号 5 闸门判据"站得住"但时间/资源不够做 allocator
- 或闸门判据失败但官方 LongBench 上 INT8-Canonical 和 KIVI-style 表现合理

**论文改动清单**:

| 章节 | 改动 | 预估工作量 |
|---|---|---|
| Abstract_zh/en | 新增一句"官方 LongBench 验证" | 15 分钟 |
| Ch1 §1.4 贡献一 | "本文在 Qwen2.5-1.5B 官方 LongBench（NarrativeQA/HotpotQA/GovReport）× 4 kv_mode 上系统验证 attention-KL 框架的评测稳健性" | 20 分钟 |
| **Ch4 新增 §4.x（主要改动）** | 插入在 §4.2 之后：官方 LongBench 主结果 | 90 分钟 |
| Ch4 §4.y（旧 LongBench 合成） | 降级为 "补充实验（合成数据）"，附录引用 | 20 分钟 |
| Ch5 发现二 | 加一句"这一结论经官方 LongBench 三任务验证保持" | 10 分钟 |
| 附录 A LongBench 官方 | 把 §4.x 的附加细节和 details CSV 放进附录 | 30 分钟 |
| references.bib | 无需新增 | - |

**Ch4 §4.x LaTeX 模板**（待填数据）:
```latex
\subsection{官方 LongBench 主结果（Qwen2.5-1.5B）}
\label{subsec:exp-official-longbench}

本节在官方 LongBench~\cite{bai2024longbench} 的三个核心任务
（NarrativeQA / HotpotQA / GovReport）上对 fp16、INT8-Canonical、
KIVI-style 和 INT4-RoleAlign 四种配置进行 $n=50$ 样本级
受控评测。数据来自 THUDM/LongBench 官方 jsonl 发布版，
评测协议固定 seed=1234，gen\_len=64，max\_context=4K。

\begin{table}[!htbp]
\centering
\caption{Qwen2.5-1.5B 在官方 LongBench 上的跨 kv\_mode 对比}
\label{tab:phase1-official-longbench-1p5b}
% 待自动填充（来自 aggregate_phase1.py 输出）
\begin{tabular}{llcccc}
\toprule
任务 & 官方指标 & FP16 & INT8-Canonical & KIVI-style & INT4-RoleAlign \\
\midrule
NarrativeQA & F1  & TBD & TBD & TBD & TBD \\
HotpotQA    & F1  & TBD & TBD & TBD & TBD \\
GovReport   & ROUGE-L & TBD & TBD & TBD & TBD \\
\bottomrule
\end{tabular}
\end{table}
```

---

## 场景 B：停在编号 7-8 —— v7/v8 "behavior-guided adaptive allocation"

**触发条件**:
- 闸门通过 + BAKV Top-3 在 1.5B（编号 6-7）或跨模型（编号 8）显著优于 Random-3

**论文改动清单**:

| 章节 | 改动 | 预估工作量 |
|---|---|---|
| Abstract_zh/en | **主结论升级**: "attention-KL 不仅是诊断透镜，更是 bit 分配的 oracle" | 30 分钟 |
| Ch1 §1.4 贡献二 | 从"INT4-RoleAlign 实例化"改为"BAKV adaptive allocation" | 45 分钟 |
| Ch3 新增 §3.x | "Behavior-Aligned Layer-wise Bit Allocation" 算法 + 伪代码 | 2 小时 |
| Ch4 §4.x 官方主表 | 新增 BAKV Top-3 列 | 30 分钟 |
| Ch4 新增 §4.y | Allocator MVP 结果 + Budget Pareto 图 + 3 类消融 | 2 小时 |
| Ch5 三发现重写 | 主结论从"解耦现象" → "lens 驱动 policy" | 1 小时 |
| INT4-RoleAlign 降级 | 从主角 → "固定 bit 参照实现"/"allocator primitive" | 30 分钟 |
| references.bib | 加 KVTuner、MiniKV、PatternKV 等 | 20 分钟 |

**建议新标题**:
*AlignKV: Behavior-Aligned Layer-wise Bit Allocation for KV Cache Quantization*

---

## 场景 C：停在编号 9-10 —— v9/v10 "跨 benchmark 跨场景 adaptive allocation"

**触发条件**:
- Allocator 在 NoLiMa / BABILong / reasoning model 上也有效

**论文改动清单**:
- 场景 B 全部改动 +
- Ch4 加 §4.z harder benchmark（NoLiMa 主，BABILong 辅）
- Ch4 加 §4.w reasoning 外推（DeepSeek-R1-Distill × MATH-500）
- Ch5 加"跨场景推广性"段

**建议新标题候选**:
- *AlignKV: Adaptive KV Cache Allocation for Reasoning and Long-Context LLMs*
- *From Diagnosis to Policy: Attention-KL Driven KV Cache Allocation at Fixed Budget*

---

## 通用准备（三场景共享）

**数据聚合**:
- 主 CSV: `results/phase1_summary.csv`（aggregate_phase1.py 产出）
- 7B CSV: `results/phase1_summary_7b.csv`
- Markdown 主表: `docs/phase1_main_table.md`（自动生成）

**图表自动生成**（需等数据齐）:
- `scripts/plot_phase1_pareto.py`：画 quality × memory × latency 的三维散点（待写）
- `scripts/plot_bakv_vs_uniform.py`：allocator 对比柱状图（场景 B/C 用）

**LaTeX 表格自动填充**:
- `scripts/render_latex_table.py`：从 summary.csv 直接渲染 booktabs 表（待写，30 分钟即可）

---

## 时间线对照表

| 场景 | 新增章节 | 修改章节 | 总预估工作 |
|---|---|---|---|
| A（v6-stable） | 1 节 + 附录 | abstract/ch1/ch5 各一段 | ~4 小时 |
| B（v7/v8） | 2 节（Ch3 算法 + Ch4 结果）| abstract/ch1/ch4/ch5 整体重写 | ~1-2 天 |
| C（v9/v10） | 4 节 | 全书定位重写 | ~3-5 天 |

**无论停点**: §11-13（收口）都强制执行，不得跳过。
