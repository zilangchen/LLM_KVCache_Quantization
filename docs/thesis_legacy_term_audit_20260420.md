# Thesis Legacy Term Audit（2026-04-20）

**目的**：thesis/chapters/*.tex 从旧版（5-Contribution / Finding 4 / inv_tau × GQA）迁移到新版（RQ1-3 + C1-3 / behavior framework / regime map）时，这份文档列出需要**删除 / 改写 / 降级 appendix** 的旧术语位置。

**使用方式**：改某章之前先读这份文档对应章节段，知道哪些地方要动。改完该章后把对应条目标记为 ✅。

**配套**：
- 叙事主线 → `docs/thesis_story_20260420.md` §14（旧论文处理原则）
- 术语冻结 → `docs/thesis_story_20260420.md` §15（Terminology Freeze）
- 章节草稿 → `docs/thesis_chapter_drafts_20260420.md`

---

## 术语分类与处置规则

| 类别 | 旧术语 | 处置 |
|---|---|---|
| **A. inv_tau / τ⁻¹** | `inv_tau`, `\tau^{-1}`, `温度校正`, `逆温度` | **降 appendix diagnostic note**；正文所有涉及段删除或改写 |
| **B. 5-Contribution 结构** | `5-Contribution`, `C1-C5`, `Finding 1-5`, `贡献一/二/三` | **改写为 RQ1-3 + C1-3**（见 thesis_story §9） |
| **C. KL vs MSE ablation** | `KL 校准`, `MSE 对照`, `KL 目标`, `KL vs MSE` | **降 appendix**（非主线 ablation） |
| **D. Key 主导** | `Key 主导失败`, `K 主导`, `Key dominance` | **改写**为 §2.2 K/V role mechanism（保留现象，改 framing） |
| **E. GQA × inv_tau** | `GQA 尺度` + `σ_eff` + `H_kv` 在 inv_tau 语境 | **降 appendix**（Finding 4 降级） |
| **F. attention-KL lens** | `attention-KL lens`, `attention-KL 诊断` | **部分保留**（新故事仍用"behavior lens"概念，改为 attention behavior） |
| **G. 旧硬编码编号** | `图 1/2/3` / `表 1-8` 的硬写（非 \ref） | **改为 \ref{}**，对齐 M+ 方案编号（图 ①②③④⑤⑦⑧⑨ / 表 T0 S1 S3 T1-T6） |

---

## 风险评估（按文件）

| 文件 | 风险级别 | 主要问题 |
|---|---|---|
| `ch3_method.tex` | **HIGHEST** | inv_tau 整个 §2.3-2.4（~110 行相关）需要整体降级到 appendix |
| `ch4_experiments.tex` | **HIGH** | 整个 §4.X inv_tau subsection（L1406-1506）+ KL-MSE ablation + C1-C3 labels 需改写 |
| `ch1_introduction.tex` | MEDIUM | C1-C3 contribution labels 替换 + Key-dominated mechanism 重新 framing |
| `appendix.tex` | MEDIUM | inv_tau full derivation（L631-654）本来就在 appendix 可保留但需重写标签；C1-C3 reference 更新 |
| `ch2_related_work.tex` | LOW | inv_tau findings 引用 + GQA scale gap 声明 |
| `ch5_conclusion.tex` | LOW | Contribution/Finding 引用重写 + Key-dominated conclusion 改 framing |
| `abstract_zh.tex` / `abstract_en.tex` | LOW | 高层 framing 调整（见 `thesis_chapter_drafts` §1 草稿） |

---

## 具体位置清单（关键行号）

> 数据来源：2026-04-20 Explore agent grep。以下为**高优先级位置**，改某章时作为 starting point。

### `thesis/chapters/ch1_introduction.tex`

- **C1-C3 contribution labels**：L133 / L151 / L171 / L194（需要替换成新 C1-3 叙述）
- **Key-dominated framing**：散落在 §1.2 motivation 段
- **旧 figure \ref 引用**：ch1_pipeline.pdf 的引用位置需要改成新 Framework overview 图 ②

### `thesis/chapters/ch2_related_work.tex`

- **inv_tau findings 引用**：少量位置，改为"structural observation related to GQA scale"或直接删除
- **KIVI / KVQuant / KVTuner** 正确引用保留；加 TurboQuant / NVFP4（如有必要）

### `thesis/chapters/ch3_method.tex` **[HIGHEST RISK]**

- **inv_tau 主段**：L24, L61, L70, L100, L129, L131, L150-151（方法层 inv_tau 相关段 → 删除 / 降 appendix）
- **§2.3-2.4 inv_tau 整段**：L267-330（整段降 appendix 或删除）
- **末尾 inv_tau 引用**：L757-758, L810, L922
- **`ch3_framework.pdf` 引用**：L60（此图功能和新图 ② 重叠，考虑合并到新图 ②）
- **图 `ch3_invtau_heatmap.pdf`**：L316（删除，此图降 appendix）

### `thesis/chapters/ch4_experiments.tex` **[HIGH RISK]**

- **C1/C2/C3 contribution labels**：L11, L13, L15, L247, L464（改写为新 C1-3 或 RQ1-3）
- **inv_tau 整个 subsection**：L1406-1506（整段降 appendix 或删除——这是旧 Finding 4 的核心段）
- **注意力调节机制敏感性（Table L597）**：inv_tau 相关，降 appendix
- **KL vs MSE ablation（Table L310）**：降 appendix
- **INT8 vs KIVI Table L785**：降 appendix（新故事 KIVI 对比在 INT4 层面）
- **INT4 三方对比 Table L1596**：废弃（新故事用 cross-model 主表 T3 取代）

### `thesis/chapters/ch5_conclusion.tex`

- **Contribution/Finding 引用**：L36-37（改写为新 C1-3）
- **Key-dominated conclusion 段**：改为 "the K/V asymmetric architecture reflects the distinct error propagation paths shown in §3.1"

### `thesis/chapters/appendix.tex`

- **inv_tau full derivation**：L631-654（可保留在 appendix，但更新标签为"old finding retained as diagnostic note"）
- **C1-C3 reference**：L91-92（更新为新 contribution 结构）
- **7B KL vs MSE 校准对比 Table L670**：保留 appendix（但明确为 reproducibility detail，非主线）
- **主 efficiency dashboards**：保留 appendix（降级自 Ch4 主图）

### `thesis/chapters/abstract_{zh,en}.tex`

- **高层 framing**：需要完全重写，按 `thesis_chapter_drafts_20260420.md` §1.3（中文）/ §1.4（英文）的草稿模板
- **不再出现**："5 contributions" / "C1-C5" / "Finding 1-5" / "inv_tau × GQA" 等旧术语
- **应出现**："RQ1-3" / "C1-3" / "behavior framework" / "regime map" / "INT8 canonical" / "INT4 RoleAlign" / "AutoK"

---

## 改写顺序建议（配合 Phase 1-7）

按 `thesis_story` §14.5 + thesis-rewrite 计划：

1. **Phase 1（调整后）**：Ch1 §1.1/§1.2/§1.4 研究背景与动机，**不含** §1.3 contribution 段。Ch1 §1.3 + Ch5 整章 + Abstract 放 Phase 8 最后写（contribution 和 conclusion 互为镜像，需其它章节稳定后一起写）
2. **Phase 2**：Ch3 全章 → 处理**类别 A + E**（inv_tau 最集中，最高风险）
3. **Phase 3**：Ch4 §4.1-§4.2 → 处理 Ch4 头部 contribution labels（类别 B）
4. **Phase 4**：Ch4 §4.3 → 处理 Ch4 cross-model 部分，不涉及旧术语
5. **Phase 5**：Ch4 §4.5 → 新增 per-model case，无旧术语冲突
6. **Phase 6**：Ch2 + Ch5 + Ch1 §1.4 → 处理**类别 D, F**
7. **Phase 7**：Appendix + Abstract → 整理类别 A 降级到 appendix 的材料 + 重写 abstract

---

## 不动的术语（保留）

- `attention-KL lens` / `attention-KL 诊断` → **保留**，新故事仍用（改写成 "attention behavior lens"）
- `GQA` / `H_kv` → **保留**（不在 inv_tau 语境下时是中性术语）
- `K per-channel + V per-token` → **保留**（RoleAlign 架构基础）
- `Triton 融合核` → **保留**（C2 method instance 的一部分）
- `clean-provenance` / `pin=ddada19` → **保留**（新故事的 reproducibility 基础）

---

## 追踪

改完一章后在此表对应行前面加 ✅：

- [ ] abstract_zh.tex / abstract_en.tex（Phase 7）
- [ ] ch1_introduction.tex（Phase 1 + Phase 6 §1.4）
- [ ] ch2_related_work.tex（Phase 6）
- [ ] ch3_method.tex（Phase 2）**[HIGHEST RISK]**
- [ ] ch4_experiments.tex（Phase 3 + Phase 4 + Phase 5）**[HIGH RISK]**
- [ ] ch5_conclusion.tex（**Phase 8**；保留旧 5 章制的 §1 核心发现 / §2 局限 / §3 Future Work / §4 结语四节结构；每节内容对齐新故事）
- [ ] appendix.tex（Phase 7）

---

**文档结束。**
