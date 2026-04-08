# Expert Reviews — Round 1 (Consolidated)

**Generated**: 2026-04-08 12:55
**Target**: abstract_en.tex, abstract_zh.tex, ch1_introduction.tex
**Reviewers**: Codex (skipped due to context budget) + 4 sub-agents (QT, NL, AW, NE) + Phase 2 paper review

---

## Executive Summary

**Total issues**: 52 (aggregated across 5 review sources)
**By severity**: 4 CRITICAL / 14 HIGH / 20 MEDIUM / 14 MINOR/NIT
**Consensus (raised by ≥2 reviewers)**: 9 items
**Overall AI-trace rating**: 7.5/10 (ZH 8.5, EN 7.5, ch1 6.5)

---

## CRITICAL Consensus Issues (Phase 4 必修)

### C-1 [CRITICAL] 中英文摘要段落严重不对齐 — KI-001 + NL-2 + Phase 2
- **EN**: 6 content paragraphs; **ZH**: 4 content paragraphs (merged)
- **ZH C4 (INT4-RoleAlign) 出现在 C5 之后**，顺序颠倒
- **Fix**: 重写 ZH 结构对齐 EN 的 6 段式 + 保持正确的 C1→C2→C3→C4→C5 顺序

### C-2 [CRITICAL] 关键词数量 7 超 SCUT 3-5 上限 — KI-002
- Both EN and ZH list 7 keywords
- **Fix**: Keep 5 core: 大语言模型/键值缓存/量化/行为对齐校准/非对称量化

### C-3 [CRITICAL] σ_eff ∝ σ/√N_rep 公式数学前提不成立 — QT-4 + NL-6 + AW
- Shared KV head 的噪声是 **相关** 而非独立，严格 √N 稀释不成立
- Abstract 用 "consistent with intuition"（hedge 充分）但 ch1 L180 "直觉论证" 仍有公式化表达
- **Fix**: 公式降格为 heuristic，明确"formal derivation requires i.i.d. assumptions that do not strictly hold in GQA"

### C-4 [CRITICAL] 8B INT8 v1 校准 PPL +16% 完全未在 Abstract/Intro 披露 — NE-3 + NE-11
- Abstract "preserves quality across three model families" 给错印象
- Ch1 也未提及 8B 的 v1 校准异常
- **Fix**: Abstract 加 caveat "on Qwen2.5-1.5B/7B"；ch1 L170 附近加一句披露 "8B 对校准数据规模敏感"

---

## HIGH Consensus Issues

### H-1 [HIGH] C5 "贡献五" 编号造成贡献膨胀风险 — NL-1 + Phase 2
- Abstract 正确框为 "second-order finding / 二阶规律"
- Ch1 L173 用 "贡献五" 并列编号 → 读者读到"5 项贡献"
- **Fix**: Ch1 改为"补充发现（诊断副产物）"；保持 "4 primary contributions + 1 byproduct finding" 统一叙事

### H-2 [HIGH] KIVI 差异声明缺失 — QT-6 + NE-15
- Ch1 L98-101 对 KIVI 的定位过简，未说明 RoleAlign 与 KIVI 的核心差异
- **Fix**: 补 "本文继承 KIVI 的 per-channel K + per-token V 格式，但以离线 attention-KL 搜索替代 runtime absmax 估计"

### H-3 [HIGH] "PPL > 15%" 与 1.5B 13.7% 不匹配 — NE-2
- Abstract L15 / Ch1 L43 都写 "over 15%"，但实际 1.5B 最大退化只到 13.7%
- **Fix**: 改为 "up to ~14%" 或 "over 13% on smaller models"

### H-4 [HIGH] Abstract 完全无 seeds/Bootstrap 声明 — NE-8
- **Fix**: Abstract 结尾加一句 "All results across 5 seeds with Bootstrap CI and BH-FDR"

### H-5 [HIGH] "Unified calibration objective" 过度 claim — QT-3
- **Fix**: "unified" → "dual-purpose" 或 "serving both calibration and diagnosis"

### H-6 [HIGH] 双面镜 "as X / as Y" 对称结构 (AI 痕迹) — AW Hotspot A + D + Phase 2
- abs_en L17-24 "as a calibration objective, it...; as a diagnostic lens, it..."
- abs_zh L15-18 "作为校准目标...作为诊断透镜..."
- **Fix**: 打破对称，合并为单句

### H-7 [HIGH] "Complete evidence chain" / "closed loop" meta 叙述 — AW Hotspot B + C
- abs_en L38 / L60-64 都有典型 AI 元叙述
- **Fix**: 删除 meta 声明，直接陈述事实

### H-8 [HIGH] Needle 0→100 baseline label 缺失 — NE-1 + NE-7
- 读者可能混淆 "INT4-RA 曾经 0%" 与 "symmetric INT4 是 0%"
- **Fix**: 加 "(vs symmetric INT4 baseline)"

---

## MEDIUM Issues (Phase 4 选修)

- M-1 [NL-4] RQ ↔ Claim 显式映射句缺失 — 加一句 "C1+C2 回应 RQ1，C3 回应 RQ2，C4 回应 RQ3"
- M-2 [NL-5] Abstract hook 前置 — 把"反直觉 Needle 0%"放到第二句
- M-3 [QT-13] Ch1 L46-47 "无法解释" 过度 claim
- M-4 [QT-5] "asymmetric" vs "granularity" 术语混淆
- M-5 [NE-12] Abstract 只提 Needle，未提 RULER/LongBench
- M-6 [QT-7] KVTuner / BitDecoding 未在 ch1 引用

---

## AI Hotspots (Phase 4c 2-agent 审核必查)

1. **abs_en L17-24** 双面镜 (H-6)
2. **abs_en L38-42** complete evidence chain (H-7)
3. **abs_en L60-64** closed loop 结尾 (H-7)
4. **abs_zh L15-18** 双面镜中文版 (H-6)
5. **abs_zh L33-35** "二阶价值" 空洞 meta
6. **abs_zh L47-48** "贯通递进逻辑链路" 空洞收尾
7. **ch1 L44-50** "这个矛盾暴露了...盲点" 套话
8. **ch1 L143-183** 五条贡献等长方阵 (H-1)
9. **ch1 L190-198** "综上"+两次"同时" run-on 段

---

## Phase 1 Literature Borrowable Templates

- **KVQuant opening**: "X surface as the dominant contributor to..." — 用于 hook
- **KIVI finding-first**: "Our findings indicate..." — 用于 Intro motivation
- **RotateKV gap articulation**: "Existing X is sub-optimal because..." — 用于 related work gap
- **ZipCache concision**: 2-sentence problem + 2-sentence gap + 2-sentence method
- **Key phrases**: "Somewhat surprisingly" / "This observation motivates..." / "Our core idea is to..."

---

## Phase 4 执行优先级

### Must Fix (10 items, Phase 4a)
1. C-1 Abstract ZH 重写为 6 段对齐 EN
2. C-2 关键词精简到 5
3. C-3 σ_eff 公式降格为 heuristic
4. C-4 8B INT8 v1 披露（ch1 Limitations forward pointer）
5. H-1 ch1 C5 去编号化 → "补充发现"
6. H-2 ch1 补 KIVI delta
7. H-3 "15%" → "13.7%" 或 "约 14%"
8. H-4 Abstract 加 seeds/Bootstrap 声明
9. H-5 "unified" → "dual-purpose"
10. H-6+H-7 AW hotspots A-D-E-F 重写（双面镜 + meta 删除）

### Should Fix (3 items, Phase 4a)
11. H-8 Needle 0→100 加 baseline label
12. M-1 RQ ↔ Claim 显式映射
13. M-3 "无法解释" → "未能预防或定位"

### Can Defer (Phase 5 或下轮)
- M-2 hook 前置（结构改动较大）
- M-4 granularity 术语
- M-5 Abstract 加 RULER/LongBench (信息密度已高)
- M-6 KVTuner/BitDecoding 引用（ch2 更合适）
- 其他 NIT 项

### Phase 4b (编译验证)
- xelatex 编译通过
- KI-005 章节命名渲染检查
- KI-006 bib style 抽检

### Phase 4c (AI 痕迹 2-agent 审核)
- 对修改后的 3-5 个关键段落做 2-agent cross review
