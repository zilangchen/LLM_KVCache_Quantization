# ARR 2026 Responsible NLP Research Checklist — 本论文对照

**生成日期**: 2026-04-17
**审查对象**: `thesis/main.pdf`（114 页）+ `thesis/chapters/*.tex`
**依据**: ACL Rolling Review 2026 Responsible NLP Research Checklist（ARR 官方模板）

> **定位**: 本文件是 D6_ATK_arr.md 的配套附录，仅服务于未来 ARR 投稿决策。按用户 v5 决策（Q1=A），答辩优先，本清单不驱动论文修改。

---

## Section A — General claims / Scope

| 项目 | 问题 | 论文状态 | 评分 | 备注 |
|------|------|---------|------|------|
| A1 | Claim 与实际结果一致？ | ✅ **Pass** | 5/5 | Abstract → Introduction → Findings 一致，无夸大 |
| A2 | Limitations 显式声明？ | ✅ **Pass** | 5/5 | ch5 §5.2 有专门 "局限性" 章节，覆盖 6 类：INT4-RoleAlign 验证范围、评测完整性、方法边界、校准框架、KIVI 实现差异、BitDecoding 兼容性 |
| A3 | Risk 分析？（如果适用）| ➖ N/A | — | KV cache 量化为系统优化工作，无社会风险 |
| A4 | Negative result 诚实报告？ | ✅ **Pass** | 5/5 | 明确报告：对称 INT4 完全失败 (0% Needle)、LLaMA-3.1-8B INT8 校准次优、BitDecoding 数值错误、cs=1 灾难性退化 |

**Section A 总分**: 20/20（满分）

---

## Section B — Datasets and Artifacts

| 项目 | 问题 | 论文状态 | 评分 | 备注 |
|------|------|---------|------|------|
| B1 | 引用所有使用的 dataset？ | ✅ **Pass** | 5/5 | WikiText-103 (merity2016)、LongBench (bai2024)、RULER (hsieh2024)、Needle (kamradt2023) 均 cite |
| B2 | 使用符合原 license？ | ⚠ **Partial Fail** | 3/5 | 未显式声明 license（WikiText-103: CC BY-SA, LongBench: MIT, RULER: Apache 2.0）。ARR Checklist 明确要求 "Did you cite the creators of artifacts you used?" 和 "Did you discuss whether the license permits you to reuse them?" |
| B3 | Released artifact 说明使用场景？ | ⚠ **Unclear** | — | 作者自己的 artifacts（校准产物 JSON、Triton kernels）是否作为 artifact 发布？未明确。ch4 L59 提到 "项目仓库" 但无 URL |
| B4 | Artifact 的 intended use 与该论文的 use 是否一致？ | ✅ **Pass** | 5/5 | WikiText/LongBench/RULER 都是评测用途，本论文也作评测使用 |
| B5 | 匿名化 / 删除敏感内容？| ➖ N/A | — | 使用公开数据集，无需匿名化 |
| B6 | 数据收集流程说明？| ✅ **Pass** | 5/5 | ch4 L112-131 描述 LongBench 合成数据生成协议（确定性合成 QA 生成器、固定噪声上下文、锚点答案）|
| B7 | 数据 statistics 说明？| ✅ **Pass** | 5/5 | PPL 评测：~302K tokens WikiText-2 test；校准：128 条 WikiText-103 段（ch3 L152）；评测规模明确 |

**Section B 总分**: 18/25（缺 B2 license 显式声明）

---

## Section C — Computational Experiments

| 项目 | 问题 | 论文状态 | 评分 | 备注 |
|------|------|---------|------|------|
| C1 | Hyperparameter search 描述？ | ✅ **Pass** | 5/5 | ch4 L302-303 clip_percentile ∈ {99.0, 99.5, 99.9, 100}, group_size ∈ {16, 32, 64}；BA percentile 搜索网格在 ch3 §3.X 和 configs/exp_matrix_rolealign.yaml |
| C2 | 模型 parameters 数量？| ✅ **Pass** | 5/5 | 1.5B/7B/8B/14B 明确；ch4 L30-53 详细规格（Layer count, H_q, H_kv, d_h）|
| C3 | 实验 infrastructure 描述？ | ✅ **Pass** | 5/5 | ch4 L55-57 "NVIDIA H20 GPU (98GB VRAM), Python 3.12, PyTorch 2.8.0, CUDA 12.8, Transformers, Triton" |
| C4 | **Runtime / compute budget**？ | ❌ **Fail** | 1/5 | **严重缺失**：全文未见 GPU-hours 总量、单次实验时长。Responsible NLP Checklist 明确要求："Did you include the number of GPU/CPU hours needed?" 本论文 717 runs 的 total compute 不明 |
| C5 | 统计检验？ | ✅ **Pass** | 5/5 | Bootstrap CI (10,000 resamples) + sign-flip permutation + BH-FDR (α=0.05)，ch4 L222-238 |
| C6 | 随机种子报告？| ✅ **Pass** | 5/5 | 质量: 1234-1238 (5 seeds)，吞吐: 1234-1241 (8 seeds)，ch4 L82-83 |
| C7 | Validation set 使用说明？| ➖ N/A | — | 训练后量化 (PTQ) 工作，无 validation set（校准集 = WikiText-103 子集，评测集 = WikiText-2/LongBench/RULER/Needle 独立）|
| C8 | Error bars / 统计显著性？ | ⚠ **Partial** | 4/5 | 质量指标有 Bootstrap CI + BH-FDR；PPL 已论证为 deterministic 不需 CI（ch4 L244-250）。但 14B 仅 1 seed，无法算 CI（见 D6_ATK_arr.md C1）|

**Section C 总分**: 25/35（C4 严重扣分）

---

## Section D — Reproducibility

| 项目 | 问题 | 论文状态 | 评分 | 备注 |
|------|------|---------|------|------|
| D1 | Code 公开？ | ❌ **Fail** | 1/5 | **全文无 GitHub URL**。ch4 L60 仅说 "可通过项目仓库中的原始 CSV 文件复现"，但不给地址。ARR 投稿时必须提供 anonymized code repo |
| D2 | Model 公开？ | ➖ N/A | — | 使用开源模型（Qwen2.5, LLaMA-3.1），revisions 已 pin (ch4 L33 "revision \code{989aa7}") |
| D3 | Dependencies / Environment？| ✅ **Pass** | 5/5 | env/versions.txt + env/requirements_freeze.txt (ch4 L58-59)|
| D4 | 复现指令？| ⚠ **Partial** | 3/5 | 正文提到产物路径和脚本名，但未见完整 reproduction command table。对外部 reviewer 门槛略高 |
| D5 | Evaluation metrics 明确？| ✅ **Pass** | 5/5 | PPL / Needle pass rate / LongBench token-F1+Rouge-L+Acc+Edit Sim / RULER 4-subtask macro / TPOT+KV Mem 都明确定义 |

**Section D 总分**: 14/20（D1 严重扣分）

---

## Section E — Ethics (Human Subjects / Bias / etc.)

| 项目 | 问题 | 论文状态 | 评分 | 备注 |
|------|------|---------|------|------|
| E1 | Human subjects 研究？| ➖ N/A | — | 无 human subjects |
| E2 | Crowdsourcing？| ➖ N/A | — | 无 crowdsourcing |
| E3 | IRB approval？| ➖ N/A | — | 无需 IRB |
| E4 | Potential harm / misuse discussion？| ➖ N/A | — | 系统优化工作，无 direct harm vector（量化不引入 bias/harm 能力）|
| E5 | Bias evaluation？| ➖ N/A | — | 不产生 language generation risk（评测任务为事实检索/困惑度）|

**Section E 总分**: N/A（系统优化论文，Section E 整体豁免）

---

## Section F — Use of AI Assistants in Research

| 项目 | 问题 | 论文状态 | 评分 | 备注 |
|------|------|---------|------|------|
| F1 | 使用 AI assistant (e.g., ChatGPT, Claude, Copilot) 写作？ | ⚠ **Unclear** | — | 论文未声明。若实际使用需披露（ARR 2026 新增要求）|
| F2 | AI assistant 的使用范围（coding / writing / ideation）？| ⚠ **Unclear** | — | 同上 |

**Section F 总分**: 待补充（ARR 投稿前必须声明）

---

## 总体评分

| Section | 得分 | 满分 | 备注 |
|---------|------|------|------|
| A (General Claims) | 20 | 20 | 优秀 |
| B (Datasets & Artifacts) | 18 | 25 | 缺 license 显式声明 |
| C (Computational Experiments) | 25 | 35 | **compute budget 缺失严重** |
| D (Reproducibility) | 14 | 20 | **code repo URL 缺失严重** |
| E (Ethics) | N/A | N/A | 豁免 |
| F (AI Assistants) | 待补充 | — | ARR 2026 新增要求 |
| **Total (excl. E)** | **77** | **100** | **77%**：系统性工作扎实但 Responsible NLP Checklist 覆盖有 3 项严重缺失 |

---

## ARR 投稿前必修清单（若决定投稿）

**Critical (必须修)**:
1. **[D1]** 创建 anonymized code repository（OSF / anonymous.4open.science）并在 abstract footnote 或 §1.4 引用
2. **[C4]** 附录加 "Computational Budget" 表：717 runs 总 GPU-hours、单次典型实验时长、H20 功耗估算
3. **[F1-F2]** 声明 AI assistant 使用（如果有）：写作阶段使用 Claude/ChatGPT 的范围、编程阶段 Copilot 使用等

**High Priority (强烈建议修)**:
4. **[B2]** 附录或 §4.1 显式列出所有 dataset 的 license（WikiText-103: CC BY-SA 3.0; LongBench: MIT; RULER: Apache 2.0; Needle: MIT）
5. **[D4]** 加入完整 reproduction command table（appendix）：每个主表对应的 3-5 行 bash 命令

**Medium Priority (可选)**:
6. **[C8]** 14B 补跑 2 seed 使其可计算 CI（见 D6_ATK_arr.md C1）

---

## 与答辩视角的冲突标注

根据用户 v5 决策（Q1=A），以下 ARR 修复与答辩视角无冲突，可提前准备不影响答辩进度：

| # | 修复项 | 与答辩冲突？ | 建议 |
|---|--------|-------------|------|
| 1 | D1 创建 anonymized repo | 不冲突 | 答辩后统一处理，ARR 投稿时再公开 |
| 2 | C4 Compute budget 表 | 不冲突 | 答辩版可加入附录，不影响主文 |
| 3 | F1-F2 AI 声明 | 不冲突 | 答辩版可加入（acknowledgements 或附录）|
| 4 | B2 License 声明 | 不冲突 | 答辩版可加入附录 |

**结论**：ARR 修复清单中的 Critical 项目（D1, C4, F1）对答辩无负面影响，可作为答辩前的 low-cost 补充动作（总工作量 ~2 hours）。
