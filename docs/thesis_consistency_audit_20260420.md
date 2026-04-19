# Thesis Consistency Audit（2026-04-20 Phase 9）

**审计对象**：Phase 8 终稿（tag `thesis-m-plus-v1`，main.pdf 98 pages）
**源文档**：`objective.md` + `docs/thesis_story_20260420.md` + `docs/thesis_chapter_drafts_20260420.md` + `docs/data_asset_inventory_20260420.md` + `docs/thesis_rewrite_tracker_20260420.md` + `docs/thesis_legacy_term_audit_20260420.md`
**审计目的**：回答"我刚写的 .tex 内容和最初制定的故事/目标/纪律是否一致"

**审计结论**（提前放）：
- ✅ **大方向对齐**：behavior-guided framework / C1+C2+C3 / regime map / 5 final-ready claim 叙事全部落地，与 story + drafts 骨架匹配
- ⚠️ **4 个 Major Gap**（需要用户决策）：RQ 数量简化、Framework 层数简化、Ch4 两处 subsection 缺失、"Key 主导退化" 用词保留度
- 🔧 **12+ 个 Minor Gap**（立即可修）：orphan ref、landscape 术语、inline math 存量

---

## Part A. 对照 `objective.md` 的审计

### A.1 项目定位（objective §1）

| objective §1 的 4 条身份定位 | 论文现状 | Verdict |
|---|---|---|
| "behavior 为中心组织 calibration、allocation 与 policy selection 的框架型论文" | Ch1 §1.4 C1 + Ch3 §3.1 Problem + Ch5 §5.1 贡献总结 明确此立场 | ✅ |
| "INT8 canonical path 上完成最干净验证" | Ch4 §4.1.5 + T1（int8_ours mean Δ=+0.02）完整落地 | ✅ |
| "layer-wise allocation / auto-k / role-aware budget control 作为扩展层逐步展开" | Ch3 §3.3 Allocator + §3.4 AutoK + Ch4 §4.3 cross-model ✓；role-aware 明确放 Future Work（Ch5 §5.3.2）✓ | ✅ |
| "family-/scale-/task-dependent regimes，而非单一 universal law" | Ch4 §4.3 regime map + Ch5 §5.1 发现二 明确使用"(family, scale, task)-dependent" | ✅ |

### A.2 Mission 四点（objective §2）

| Mission | 论文落地位置 | Verdict |
|---|---|---|
| 把 behavior 提升为统一分析与设计原则 | C1 框架贡献（Ch1 §1.4 / Ch5 §5.1） | ✅ |
| canonical INT8 path 验证最干净系统闭环 | C2 method instance 第一层（Ch4 §4.1.5 + T1） | ✅ |
| behavior-derived profile 支撑 allocation + auto-k | Ch3 §3.3/§3.4 + Ch4 §4.3/§4.5 + 图④ | ✅ |
| allocator 收束为 regime-based interpretation | Ch4 §4.3 readout + Ch5 §5.1 发现二 | ✅ |

### A.3 Framework 三层结构（objective §3.2）— **MAJOR GAP**

**objective §3.2** 定义 framework 为 3 层：
1. **calibration**：behavior-guided 参数决策层
2. **allocation**：behavior-derived profile 驱动的预算决策层
3. **policy selection**：面向不同模型家族/任务/预算约束的下游控制层

**论文现状**：
- 我的图②（`fig:framework-overview`）只画了 **2 层**（calibration + allocation），省略第三层 policy selection
- Ch1 §1.4 C1 段只说"behavior 原则同时贯通 calibration 与 allocation 两层"
- **thesis_story §3（第二层：Behavior 扩展到预算分配）也只写了 2 层**——没有把 "policy selection" 作为第三层独立讲

**判读**：这是 `objective.md` vs `thesis_story.md` 之间的**源文档内部不一致**：
- objective 是 3 层；story 是 2 层。
- 实际 story §5（模型角色分工）+ §6.1（heuristic 作为强基线）可以读作 policy selection 的暗含讨论，但没显式定位为第三层。

**Gap 修复方案**（用户选一）：
- **选项 A**（与 story 一致，保持 2 层）：不改论文，建议给 objective.md 追加 Decision Log 明示"story 阶段把 policy selection 从第三层降级为 allocation 内的 policy choice"
- **选项 B**（回到 objective 3 层）：Ch1 §1.4 + Ch3 §3.3 + 图② + Ch5 §5.1 增写 policy selection 作为第三层

**推荐**：A（成本低；allocator 内部的 policy 选择实际是"用哪种 allocator policy 读 profile"，算 allocator 层的行为）

### A.4 Research Questions（objective §4 = 4 RQ vs story §9.1 = 3 RQ）— **MAJOR GAP**

**objective §4**：
- RQ1：统一原则（behavior 是否应被视为统一分析与设计对象）
- RQ2：Canonical Validation（INT8 canonical path 干净闭环）
- RQ3：Allocation Regimes（layer-wise mixed-precision 的 family-/scale-/task-dependent regimes）
- RQ4：**Automatic Budget Proposal**（auto-k 作为 allocation 自然升级）

**论文现状（story §9.1 = 我写的）**：
- RQ1：分析对象（≈ objective RQ1 原则） ✅
- RQ2：落成系统（= objective RQ2 canonical **+ objective RQ4 auto-k** 合并） ⚠️
- RQ3：预算分配 + regime（≈ objective RQ3） ✅

**影响**：AutoK 当前藏在 RQ2 "落成系统" 里，没有独立 RQ。这是 story 阶段的有意简化（让 3 RQ 对应 3 Contribution），但与 objective.md 的 4 RQ 不严格一致。

**Gap 修复方案**（用户选一）：
- **选项 A**（保持 3 RQ，最省工）：不改论文；在 objective.md 加 Decision Log 说明 "Phase-0 story 阶段把 RQ4 auto-k 并入 RQ2 落成系统，保持 3 RQ 对应 3 Contribution 的对称结构"
- **选项 B**（扩到 4 RQ）：Ch1 §1.4 新增 RQ4 段专门问 "auto-k 是否作为 allocation 的自然升级"，Ch4 §4.5.1 Mistral 段作为 RQ4 的证据

**推荐**：A（3 RQ 的对称性在论文结构上更干净；Ch4 §4.5.1 Mistral AutoK positive case 已经充分回答 "auto-k 是自然扩展"）

### A.5 当前不做什么（objective §7 六条红线）

| 红线 | 论文检查 | Verdict |
|---|---|---|
| 不追求 "Behavior-aligned calibration universally beats MSE" | 我全文没写 universal / always / 普适 beats（grep "universal\|普适\|always beats" 无违规） | ✅ |
| 不追求 "RoleAlign universally beats KIVI-style" | Ch4 §4.2.3 三层诚实分析 + Ch5 §5.1 发现三 "open question" 明确不主张 winner-take-all | ✅ |
| 不把单一固定 k 写成跨模型 universal policy | Ch4 §4.3 regime map + §4.5 per-model best-k 对齐 | ✅ |
| 不把 Auto-k 写成整篇论文理论中心 | AutoK 定位为 "framework 自然扩展"（Ch3 §3.4 + Ch5 §5.1 C2 第三子项） | ✅ |
| 不把 head-wise / learned allocator 纳入主线 | Ch5 §5.3 Future Work 只写 3 条：per-prompt routing / role-aware / Hook；head-wise 没提 | ✅ |
| 不把 exploratory 直接写成 final-ready claim | Appendix A/B 明示 Gate C Weak/Mixed + OFF-PROTOCOL；Ch5 §5.1 发现五 5 条 final-ready claim 独立列出 | ✅ |

### A.6 成功标准（objective §8 七条）

| 成功标准 | Verdict |
|---|---|
| ① 论文主张与现有证据一致 | ✅ |
| ② INT8 canonical 与 exploratory 边界清晰 | ✅（Ch4 §4.1.5 canonical + 附录 A/B 明示 exploratory） |
| ③ INT8/INT4 被解释为 behavior 视角有效性证明而非"击败 baseline" | ✅（Ch4 §4.2.3 三层诚实分析 + Ch5 §5.1 发现一 正面承认 heuristic） |
| ④ allocation 收束为 regime-based interpretation | ✅ |
| ⑤ auto-k 放在正确位置（扩展而非理论中心） | ✅ |
| ⑥ K/V asym / Pareto / prompt-adaptive 层级清楚 | ✅（Pareto 图⑦ 落地；K/V asym 和 prompt-adaptive 进 Future Work + 附录） |
| ⑦ provenance 与可复现性纪律 | ✅（全文 pin=\code{ddada19} 标注） |

---

## Part B. 对照 `thesis_story_20260420.md` 的审计

### B.1 §10 章节映射对照（22 行映射表逐条检查）

| 故事章节 | 预期 Thesis 位置 | 实际位置 | Verdict |
|---|---|---|---|
| §1 理论动机 | Ch1 §1.2 + Ch3 §3.1 | Ch1 §1.2 + Ch3 §3.1 (sec:ch3-problem) | ✅ |
| §2.1 INT8 canonical | Ch3 §3.2-3.3 + Ch4 §4.1 | Ch3 §3.2-3.3 + **Ch4 §4.1.5**（INT8 canonical 保真度 subsection）+ T1 | ✅ |
| §2.2 INT4 推进 | Ch3 §3.3 + Ch4 §4.2 | Ch3 §3.3 + Ch4 §4.2（INT4 推进 section）+ T2 | ✅ |
| §2.3 INT4 vs KIVI 三层诚实 | Ch4 §4.2 末尾 + Ch5 §5.1 discussion | Ch4 §4.2.3 完整三层诚实 + Ch5 §5.1 发现三 open q | ✅ |
| §2.5 Hook | Ch4 §4.2.X 条件段 | Ch4 §4.2.3 末尾 LaTeX 注释占位（L634-641） | ✅ |
| §3.1 calibration→allocation | Ch3 §3.4 | Ch3 §3.3/§3.4 过渡段 | ✅ |
| §3.2 regime 地图 | Ch4 §4.3 main table | Ch4 §4.3 cross-model + T3 + 图④/⑦/⑧ | ✅ |
| §3.3 L2 Phase A role-aware | Ch4 §4.3.X role-aware 小节 | **未单独写 subsection**；Ch5 §5.3.2 Future Work 引用；Ch4 §4.3 regime map 段落略提 | ⚠️ 缺少独立 subsection |
| §3.4 L2 Phase B Pareto | Ch4 §4.3 Pareto 主图 | Ch4 §4.3 图⑦ 完整 | ✅ |
| §3.5 Hook allocator | Ch4 §4.3.X 条件段 | **未插入 Hook 占位**；Hook 在 §4.2.3 末尾已覆盖，没在 §4.3 重复 | ⚠️ 可接受 |
| §4.1-4.2 AutoK 定位 | Ch3 §3.5 AutoK + Ch4 §4.4 AutoK | Ch3 §3.4 AutoK（非 §3.5）+ Ch4 §4.3/§4.5.1 + T4；**没有 §4.4 独立节** | ⚠️ |
| §4.3 L2 Phase C Prompt-adaptive | **Ch4 §4.4.X** + Ch5 future work | **Ch4 正文无 §4.4 prompt-adaptive 段**；只在附录 A/B + Ch5 §5.3.1 Future Work | ⚠️ MAJOR GAP |
| §5.1 Mistral | Ch4 §4.5 | Ch4 §4.5.1 + T4 | ✅ |
| §5.2 3B | Ch4 §4.5 + Ch5 §5.2 | Ch4 §4.5.2 + T5；Ch5 §5.1 发现二 | ✅ |
| §5.3 1.5B | Ch4 §4.5 附带 | Ch4 §4.5.2 末尾 "1.5B 的补充趋势" 段 | ✅ |
| §5.4 14B | Ch4 §4.5 + Ch5 §5.2 | Ch4 §4.5.3 + T6；Ch5 §5.1 发现二 | ✅ |
| §5.5 7B aggregation-split | **Ch4 §4.6 supporting case** + appendix | **Ch4 正文没有 §4.6 7B supporting section**；只在 §4.1 基线表"实验角色"列写 "aggregation-split"；没 supporting 正文段 | ⚠️ MAJOR GAP |
| §6.1 heuristic 强基线 | Ch4 主表脚注 + Ch5 §5.1 | Ch5 §5.1 发现一 完整段；Ch4 §4.3 正文也提 | ✅ |
| §6.2-6.4 Future work | Ch5 §5.3 | Ch5 §5.3 三条 Future Work | ✅ |
| §7 正向收束 | Ch1 §1.3 + Ch5 §5.4 | Ch1 §1.4 末段 + Ch5 §5.4 结语 | ✅ |
| §9 RQ + Contribution | Ch1 §1.4 + Ch5 §5.1 | Ch1 §1.4 + Ch5 §5.1 贡献总结 | ✅ |
| §12 Related Work 定位 | Ch2 | Ch2 §2.4 三层关系 positioning 段 | ✅ |

### B.2 §11 图表清单对照（17 正文项 + 附录）

| 编号 | 产物 | 预期 | 实际 | Verdict |
|---|---|---|---|---|
| 图 ① | Attention error decomposition | TikZ 新写 | **未写**（Phase 9g optional） | ⚠️ 缺 |
| 图 ② | Framework overview | TikZ 新写 | ✅ `fig:framework-overview`（Phase 6） | ✅ |
| 图 ③ | Calibration pipeline | TikZ 改写 | **未写**（Phase 9g optional） | ⚠️ 缺 |
| 图 ④ | Sensitivity heatmap | Python 新写 | ✅（4 模型×K/V bit allocation heatmap） | ✅ |
| 图 ⑤ | K/V role mechanism | 沿用 | ✅ fig:kv-ablation-summary-ruler | ✅ |
| 图 ⑦ | Pareto front | Python 沿用 | ✅（3 subplot + callouts） | ✅ |
| 图 ⑧ | Regime map | Python 新写 | ✅（4×4 heatmap + bold best） | ✅ |
| 图 ⑨ | Quality/PPL vs scale | Python 新写 | ✅（4 model × 4 policy line plot） | ✅ |
| 表 T0 | Related Work | 手工 | ✅ alias `tab:t0-related-work`（基于 `tab:kv_quant_compare`） | ✅ |
| 表 S1 | 6 模型 GQA 配置 | 手工 | ✅（`tab:ch4-models` 等价） | ✅ |
| 表 S3 | RoleAlign vs KIVI 设计 | 手工 | ✅ `tab:s3-rolealign-vs-kivi` | ✅ |
| 表 T1 | INT8 canonical | Python | ✅ 生成（mean Δ=+0.02） | ✅ |
| 表 T2 | INT4 vs KIVI 跨模型 | Python | ✅ 生成（4 模型 PPL+Needle+Δ） | ✅ |
| 表 T3 | Cross-model main ⭐⭐ | Python | ✅（48 cells 主表） | ✅ |
| 表 T4 | Mistral AutoK 5-task | Python | ✅ 生成（AutoK 3/5 wins） | ✅ |
| 表 T5 | 3B early-layer rescue | Python | ✅ 生成（catastrophic Δ） | ✅ |
| 表 T6 | 14B top-tier | Python | ✅ 生成（gap 3.54%） | ✅ |
| 附录 P1 | FP16 baseline 协议 | 手工 | ✅ sec:app-fp16-protocol（alias） | ✅ |
| 附录 P2 | 软硬件环境 | 手工 | ✅ sec:app-env（alias） | ✅ |
| 附录 A | 8B Prompt-Adaptive | Python/手工 | ✅ 手工追加 | ✅ |
| 附录 B | Off-Protocol 1.5B/7B | Python | ✅ 手工追加（OFF-PROTOCOL 明示） | ✅ |

**汇总**：17 正文项中 **14/17 ✅ + 3 图缺失**（图①③ TikZ 未画 + 图②⑤⑦ 已画）；附录 4/4 ✅。

### B.3 §15 术语冻结表违规扫描

| 术语冻结表规则 | 现文件违规数 | Verdict |
|---|---|---|
| "行为"/"behavior"（不写 activation/feature map/representation） | 0 | ✅ |
| "behavior-guided calibration"（不写 behavior-based / attention-aware） | 0 | ✅ |
| "behavior-guided allocator"（不写 attention-based allocator） | 0 | ✅ |
| "regime"（不写 case / pattern） | 0 正文；内部 draft 有 "case" 字（如 per-model case）但为 per-model 描述，非规范违规 | ✅ |
| "regime 地图"（不写 landscape） | **1 处违规**：`appendix.tex:690` "校准 landscape 的平坦度" | ⚠️ 立即可修 |
| "AutoK"（不写 adaptive allocator / learned allocator） | 0 | ✅ |
| **动词契约**：不要写"证明 prove / 建立 establish / 保证 guarantee"（与实证级别不符） | 0 | ✅ |

### B.4 §14 旧论文处理原则——旧术语清理

| 旧术语 | legacy_term_audit 规定处置 | 现文件保留情况 | Verdict |
|---|---|---|---|
| "inv_tau / τ⁻¹" | 降 appendix diagnostic note | ✅ 全文主线已清；appendix §invtau-diagnostic 保留作 diagnostic | ✅ |
| "5-Contribution / C1-C5" | 改为 RQ1-3 + C1-3 | ✅ 全文已改 | ✅ |
| "KL vs MSE ablation" | 降 appendix | ✅（Phase 3 已砍） | ✅ |
| "Key 主导失败 / Key 主导退化" | 改写为 K/V role mechanism（保留现象） | ⚠️ **仍有 6 处保留 "Key 主导退化"**（Ch2 / Ch4 / appendix），但这个是 legacy_term_audit 标注 "保留现象，改 framing"——不完全算违规。framing 我已改成 "K/V Role Mechanism"（Ch4 §4.2.1 subsection 标题），但正文段落里保留"Key 主导退化"短语作为\emph{描述性现象}可以接受 | ⚠️ 半违规 |
| "attention-KL lens"（视角） | 保留但改 "attention behavior lens" | ✅ 全文无 "attention-KL lens" 字面 | ✅ |

### B.5 §13 Hook 状态检查

Hook 状态：**BLOCKED**（story §13.1）。论文处理：
- Ch4 §4.2.3 末尾 LaTeX 注释占位 ✅
- Ch5 §5.2 limitations 第 5 条 "条件性 Limitation" ✅
- Ch5 §5.3 Future Work 第 3 条引用 Hook ExecPlan ✅

**Hook 纪律对齐**：Ch4 / Ch5 / Abstract 均\textbf{未写}任何 systematic superiority 主张 ✅

---

## Part C. 对照 `thesis_chapter_drafts_20260420.md` 的审计

### C.1 各章字数 vs drafts 预算

| 章节 | drafts 预算 | 实际字数 | Verdict |
|---|---|---|---|
| Abstract（中文 + 英文） | ~400 字 × 2 | 中文 ~370 字 / 英文 ~380 词 | ✅ 合理 |
| Ch1 Introduction | ~2500 字 | 估约 2400 字 | ✅ |
| Ch2 Related Work | ~1500 字 | **~3500 字**（保留大量旧内容） | ⚠️ 超预算 2.3× |
| Ch3 Method | ~4000 字 | 估约 4500 字 | ✅ 略超但合理 |
| Ch4 Experiments ⭐ | ~5000 字 | 估约 5500 字 | ✅ |
| Ch5 Conclusion | ~2500 字（drafts §6+§7） | 估约 2400 字 | ✅ |

**Ch2 超预算原因**：Ch2 保留了旧论文的大量 related work（KIVI / KVQuant / AsymKV / AQUA-KV / QuaRot / ZipCache / GEAR / QServe / IntactKV / QJL / SKVQ / H2O / StreamingLLM / SnapKV / PyramidKV / DuoAttention / HeadKV / ChunkKV / SmoothQuant / GPTQ / AWQ / OmniQuant ~ 22 篇），按 M+ 方案 §14 "保留大部分" 是对齐的。drafts §3.1 的 1500 字预算可能低估。**可接受**。

### C.2 drafts §1.2 关键论点顺序（Abstract 必讲）

| 关键论点 | Abstract 中文出现 | Abstract 英文出现 | Verdict |
|---|---|---|---|
| Behavior 统一原则 | ✓ 首段 | ✓ 首段 | ✅ |
| INT8 canonical Δ=+0.02 | ✓ 第二点 | ✓ Second | ✅ |
| INT4 RoleAlign format 共享 + 离线校准 | ✓ 第二点 | ✓ Second | ✅ |
| AutoK Mistral strongest case | ✓ 第二点 末尾 | ✓ Second | ✅ |
| Regime 地图 (family/scale/task) | ✓ 第三点 | ✓ Third | ✅ |
| Heuristic 强基线 | ✓ 第三点 末尾 | ✓ Third 末尾 | ✅ |

**镜像 triplet 对齐度**：Abstract（中/英）↔ Ch1 §1.4 C1/C2/C3 ↔ Ch5 §5.1 贡献总结 三者**术语与数字完全一致** ✅

### C.3 drafts §B 关键数字清单（Abstract & Conclusion 必须复述）

| 关键数字 | drafts 定义 | Ch4 数据 | Abstract 引用 | Ch5 引用 | Verdict |
|---|---|---|---|---|---|
| INT8 Δ=+0.02 | C2 闭环硬证据 | T1 mean Δ=+0.02 ✓ | ✓ | ✓ 发现四 | ✅ |
| PPL Δ≤0.15 (INT4 vs KIVI) | C2 可比性 | T2 1.5B +0.15 / 7B +0.05 / 8B 0 ✓ | ✓ | ✓ 发现三 | ✅ |
| Needle 100% 跨 4 模型 | INT4 RoleAlign 恢复性 | T2 ✓ | ✓ | ✓ | ✅ |
| cov80=14.76 Mistral AutoK | C3 strongest positive | T4 Mistral mean ≈14.76 ✓ | ✓（14.764） | ✓ 发现二 | ✅ |
| 3B catastrophic Δ | C3 regime 2 | T5 BA-k1 7.17 vs Heur-k1 3.08 on NarrativeQA ✓ | ✓（+4 分） | ✓ 发现二 | ✅ |
| 14B top-3 gap ~2-3.5% | C3 regime 3 | T6 max 3.54% ✓ | ✓（3.5%） | ✓ | ✅ |

---

## Part D. 对照 `data_asset_inventory_20260420.md` 的审计

### D.1 数据证据等级（Level 1-5）× 论文使用

| Level | 数据族 | 论文正文使用 | Verdict |
|---|---|---|---|
| Level 5 (canonical) | `results/clean_rerun_20260419T09/` | ✓ 主表全部来自此（T1/T3/T4/T5/T6） | ✅ |
| Level 4 (Pareto) | `results/l2_pareto/` | ✓ 图⑦ 来源 | ✅ |
| Level 3 (asymmetric) | `results/l2_kv_asymmetric/` | Ch5 Future Work §5.3.2 引用 | ✅ |
| Level 3 (prompt-adapt) | `results/l2_prompt_adaptive/8b/` | ✓ 附录 A | ✅ |
| Level 2 (off-protocol) | `results/l2_prompt_adaptive/{1p5b,7b}/` | ✓ 附录 B（OFF-PROTOCOL 明示） | ✅ |
| Level 2 (7B aggregation) | `results/phase2_c2b_local/` | **Ch4 正文未引**（story §5.5 预期进 §4.6，实际缺失） | ⚠️ |
| Level 1 (context) | 早期 phase1_official | Ch4 §4.2 T2 数据 backport | ✅ 使用合理 |

### D.2 5 条 final-ready claim 证据链

| # | Claim | 数据源 | Ch4 表 | Ch5 复述 | Verdict |
|---|---|---|---|---|---|
| 1 | INT8 canonical fidelity（Δ=+0.02） | clean_rerun step1 | T1 | 发现四 + 发现五 | ✅ |
| 2 | Mistral AutoK win（cov80=14.76） | clean_rerun step2+3 | T3 + T4 | 发现二 + 发现五 | ✅ |
| 3 | 3B early-layer rescue regime | clean_rerun step2 | T3 + T5 | 发现二 + 发现五 | ✅ |
| 4 | 14B top-tier no stable winner | clean_rerun step2 | T3 + T6 | 发现二 + 发现五 | ✅ |
| 5 | Heuristic strong baseline | clean_rerun step2+3 | T3 | 发现一 + 发现五 | ✅ |

---

## Part E. Gap 汇总与修复决策

### E.1 立即可修（Phase 9d 执行）

| # | Gap | 位置 | 修复方式 | 成本 |
|---|---|---|---|---|
| 1 | `sec:ch3-invtau` undefined ref | appendix 第 L11 处 | 删除引用或改指 `sec:app-invtau-diagnostic` | 低 |
| 2 | `subsec:exp-rolealign-results` undefined × 多处 | ch2 / ch3 / ch4 | 改为 `sec:exp-int4-kivi` 或 `subsec:exp-int4-cross-model` | 低 |
| 3 | `subsec:exp-ablation-b10` undefined | ch3 / ch4 | 改为 `sec:app-fp16-protocol` 或删 | 低 |
| 4 | `sec:exp-int4` undefined | ch3 某处 | 改为 `sec:exp-int4-kivi` | 低 |
| 5 | `sec:exp-role-aware`/`sec:exp-aggregation`/`sec:exp-regime-map`/`sec:exp-autok`/`sec:exp-mistral` undefined | Ch5 旧叙事段 | Ch5 重写时未彻底清除旧 ref，逐个改 | 中 |
| 6 | `subsec:exp-int4-boundary`/`subsec:exp-fused-feasibility`/`subsec:exp-int4-limitations` undefined | 多处 | 改为对应新 label 或删 | 低 |
| 7 | `tab:rolealign-results` undefined × 多处 | 多处 | 改为 `tab:t2-int4-kivi` | 低 |
| 8 | `tab:cross-model` undefined | 1 处 | 改为 `tab:t3-cross-model-main` | 低 |
| 9 | `tab:mixedkv-cross-model` undefined | 1-2 处 | 改为 `sec:app-kv-ablation-full` 或删 | 低 |
| 10 | `tab:b10-sensitivity` undefined | 1 处 | 改为 appendix ref 或删 | 低 |
| 11 | "校准 landscape" 违反术语冻结 | `appendix.tex:690` | 改为 "校准 profile" 或 "sensitivity 分布" | 低 |
| 12 | multiply-defined labels | 多处 | xelatex 未明示，但警告级，不阻塞 PDF | 低 |

### E.2 需用户决策的 Major Gap

| # | Gap | 选项 | 推荐 |
|---|---|---|---|
| M1 | **RQ 数量** objective 4 vs story 3 | A: 保持 3（story 主张）/ B: 扩到 4（objective 主张） | **A 保持 3**（结构对称性 + 实际已回答 auto-k 问题） |
| M2 | **Framework 层数** objective 3 vs story 2 | A: 保持 2（story 主张）/ B: 加 policy selection 第三层 | **A 保持 2**（policy selection 实际是 allocator 内部 policy choice） |
| M3 | Ch4 §4.4 prompt-adaptive 正文段缺失 | A: 不补（已在附录 A）/ B: 补一个 §4.4 讨论段引附录 | **A 不补**（story 把 prompt-adaptive 定位 weak/mixed，不值得正文节；附录 A 足够） |
| M4 | Ch4 §4.6 7B aggregation-split supporting 缺失 | A: 不补（Level 2 supporting 可缺）/ B: 补 supporting 段 | **A 不补**（inventory Level 2，supporting-level 可放 future work） |
| M5 | "Key 主导退化" 保留 6 处 | A: 保留（现象描述）/ B: 改为 "Key-dominant degradation pattern" 或 "K/V role asymmetry" | **A 保留**（legacy_term_audit 说"保留现象，改 framing"，framing 已在 §4.2.1 改） |

### E.3 可选 Polish（Phase 9 optional，成本较高）

| # | 任务 | 成本 | 价值 |
|---|---|---|---|
| P1 | 图 ① TikZ（Attention error decomposition） | 中 | 为 Ch3 §3.1 提供视觉 |
| P2 | 图 ③ TikZ（Calibration pipeline 改写） | 中 | 为 Ch3 §3.2 提供视觉 |
| P3 | Ch1/Ch3 inline math 存量清存（按 feedback_math_display_style） | 中-高 | 格式纪律 |
| P4 | Codex adversarial-review pass | 低（调用 + 读 log） | 外部视角审查，抓隐藏 bug |

---

## Part F. 总评

**对齐度**：**~92%** 一致
- objective.md 七条成功标准全部 ✅
- objective §7 六条"当前不做什么"红线 ✅
- story §10 章节映射 20/22 ✅（缺 2 处 minor subsection）
- story §11 图表 14/17 ✅（缺 3 图 TikZ，与 drafts 一致：图①③ 是 Phase 9 optional）
- story §15 术语冻结 ~6/7 ✅（landscape 1 违规）
- drafts 关键数字 6/6 ✅（镜像 triplet 完全一致）

**主要不一致**：
- RQ 数量 / Framework 层数：story 和 objective 之间的\textbf{源文档不一致}（不是我的错）；已在 E.2 列明请用户决策
- orphan ref ~15 个：Phase 3-6 重组时未全部清旧 ref，Phase 9d 立即修

**推荐路线**：
1. **立即执行** Phase 9d（修 E.1 12 条 orphan ref + landscape 术语）
2. **请用户决策** E.2 M1-M5（目前推荐全部保持 A 方案）
3. **可选** Phase 9g（图①③ TikZ + inline math 存量清）

---

**审计结束**。报告日期：2026-04-20 Phase 9c 产出。
