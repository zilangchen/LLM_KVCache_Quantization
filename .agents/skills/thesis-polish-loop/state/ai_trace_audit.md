# AI Trace Audit Log

> Cumulative log of AI-trace patterns detected and rewritten across rounds.
> This file accumulates a project-specific dictionary of AI traces, which
> becomes more useful each round.

---

## How to read this file

Each entry represents a paragraph or sentence that failed the 2-agent cross review (Phase 4c):

```
### AT-NNN — Round N
- Location: file:line
- Original: <verbatim>
- Agent A (human reader) said: NO/YES + reason
- Agent B (AI detector) said: CLEAN/HAS_TRACES + reason
- Rewrite: <new version>
- Both pass: YES/NO (if NO, needs another round)
```

---

## Pattern Catalog (observed across rounds)

- **Mechanical connectives**: "此外" / "然而" / "因此" / "综上所述" density
- **Template formulas**: "作为 X...作为 Y..." symmetric structures
- **Over-hedging**: excessive "可能" / "或许" / "在某种程度上"
- **Redundant restatement**: same idea said 2-3 different ways
- **Over-formal openers**: "在执行...时" / "针对...问题" / "对...进行研究"

---

## Round-by-round Log

### AT-001 — Round 3 (Phase 4c, 2026-04-09)

- **Location**: `thesis/chapters/ch4_experiments.tex` L862-868（边界小结段落）
- **Original (after 2 rewrite rounds)**:
  ```
  INT4-RoleAlign 把 Needle 拉回 100%、RULER s_niah 保持在 ≥99%、KV 显存压缩到原始的 27%，
  代价是 PPL 上涨 2.4-13.7%、参考实现下 TPOT 增加 2-2.5×。
  我们不回避这一代价：
  对以长文本检索为主要目标、且对 PPL 有一定容忍度的部署场景，RoleAlign 是可以选择的；
  若目标是严格保持 FP16 的语言建模质量或对延迟敏感，当前版本并不合适。
  TPOT 方面的差距可由第 X 节的 Triton INT4 融合核函数承接，
  PPL 方面则需要更细粒度的比特分配策略（例如按 H_kv 自适应），这两点留给后续工作。
  ```
- **Round 2 Agent A (human 50yo reviewer POV)**: NATURAL — "我们不回避这一代价/并不合适/留给后续工作 口吻直接，数据与判断衔接自然"
- **Round 2 Agent B (mechanical detector)**: HAS TRACES × 2
  1. "我们不回避这一代价" — flagged as "修辞性填充套话"（over-hedging variant）
  2. "TPOT 方面...PPL 方面...这两点留给后续工作" — flagged as 2-branch parallel approaching 3-point template
- **Decision**: ACCEPT CURRENT (human POV takes precedence)
- **Reasoning**:
  - Agent A is simulating 50-year senior reviewer's actual reading experience, which is the final judgment authority
  - Agent B's mechanical rule cannot distinguish "template rhetoric" from "information structure": any N-branch list of technical points would be flagged as pattern, but TPOT vs PPL are two genuinely different technical problems that must be named separately
  - "我们不回避这一代价" is the directness pattern feedback_ai_trace_removal.md advocates for (as opposed to LLM-style hedging), not a violation
  - 3-iteration rule per SKILL.md: this paragraph B underwent 2 rewrite passes; a third pass risks degrading into anti-pattern overcorrection
- **Follow-up for Round 4+**: if future rounds detect this same pattern with independent reviewer consensus (not just mechanical Agent B), revisit. Otherwise treat as stable baseline.

### AT-001-companion — Round 3 Phase 4c paragraphs A + C (PASS)

For reference, 段落 A (§exp-int4-limitations L862 "三层叠加" rewrite) and 段落 C (§exp-rolealign-results L1289 "RoleAlign 与 KIVI 关系" rewrite) both achieved Round 3 PASS:
- Round 3 Agent A (human POV): ACCEPT
- Round 3 Agent B (mechanical): CLEAN
- Status: both paragraphs clean of detectable LLM patterns after 3 rewrite iterations.
