# P2 汇总去重报告

- **时间**：2026-04-17
- **输入**：7 by_dimension/D*.md + repro_pack_audit.md
- **状态**：✅ 所有 P1 agents + P0.6 完成

---

## 严重度总览

| 级别 | 主表计数 | 维度文件累计 | 备注 |
|------|---------|------------|------|
| CRITICAL | 4 | 4 | 全部入主表 |
| HIGH | 25 | 90 | D2/D7 未入主表（保留在维度文件） |
| MEDIUM | 28 | 57 | 同上 |
| LOW | 6 | 9 | 同上 |
| **Total** | **63 主表** | **162 全量** | — |

**P2 决策**：CRIT/HIGH 应全部进主表；MED/LOW 可保留在维度文件（指针引用）。

---

## CRITICAL 4 条（P3a 必须手动修）

| ID | Dim | File:Line | 问题 | 修复策略 |
|----|-----|-----------|------|---------|
| **TR-0002** | D3 | `abstract_zh.tex:31`; `abstract_en.tex:39` | 摘要 7B PPL 退化 "6.0\\%" 与主表 "6.1\\%" 冲突 | Edit 两处改为 "6.1\\%"；中英统一 |
| **TR-0003** | D1 | `abstract_zh.tex:39`; `abstract_en.tex:48-50` | 中英文关键词 6 个超附件1 3-5 上限 | 保留 4 个（大语言模型/键值缓存/行为对齐校准/GQA）中英对齐 |
| **TR-0400** | D4 | `ch3_method.tex:137,152,166-168`; `appendix.tex:79`; `calibrate_behavior.py:197`; `eval_ppl.py:954` | 论文声称 "WikiText-103 校准"，代码实际用 wikitext-2-raw-v1 test split（PPL 评测同 split → 数据污染） | 选项 A：修论文改为"wikitext-2"并声明 split 管理；选项 B：修代码用 WikiText-103（但重跑成本高）→**推荐 A** |
| **TR-0401** | D4 | `ch3_method.tex:674-686` (eq 3-10/3-11); `ch3_method.tex:859`; `asymmetric_quant.py:118,136` | §3.5 章节声称"从对称到非对称"但公式 eq 3-10/3-11 写成对称 absmax（无 zero_point） | 重写公式加入 zero_point 项 `s,z = min-max → q = round((x-z)/s)`；对齐 L859 "含 zero-point" + 代码 |

---

## HIGH 25 条（P3b agent 提案→主审→apply）

### D2 STYLE（主表仅记 D6a 追加；D2 本体在 D2_STYLE.md）
- 第一人称"我们"22 处批量（TR-0200-0220）→ P3d sed 批量 `我们 → 本文`
- "据我们所知"4 处（ch2:395,455; ch3:474; ch4:1544）
- 章节首尾重复（ch3:6↔1185; ch4:9↔263）打散

### D3 DATA（主表 TR-0300/0302/0303/0308）
- TR-0300：2 处 tablenotes 路径指向已降级原目录（ch4:377 + appendix:736）
- TR-0302/0308：14B PPL caption 声称 "302K tokens 全量" 但实际 32767（10× cherry-pick 风险）
- TR-0303：14B FP16 PPL 两份权威值冲突（4.685 vs 5.455）

### D4 TECH（TR-0402-0407）
- TR-0402 Group size 128/16 冲突
- TR-0403 GQA 符号 H_q/h_Q 大小写混用
- TR-0404 zero-point 在非对称章节从未公式化
- TR-0405 INT4 值域 [-7,7] vs [-8,7]；"256→15" 量化级别起点错
- TR-0406 eq 3-24 `top-2(v_{i,1:d_k})` 语义含糊
- TR-0407 split-channel kernel 论文详述但代码可能未对应

### D5 REF（TR-0500-0504）
- TR-0500 `luna2024think` 作者完全自造（真 Yuhui Xu 等）
- TR-0501 `zhang2024gear` 作者完全错（真 Hao Kang 等）
- TR-0502 `yue2024wkvquant` first author first name 错
- TR-0503 `agarwal2025qerl` 三重错误
- TR-0504 AI 工具声明缺失 + `*gemini*` 文件名暴露

### D6a 答辩（TR-0600-0606）
- TR-0600 摘要"四个模型"未限定 14B（1 seed）
- TR-0601 摘要 PPL 单调趋势违背 14B 非单调
- TR-0602 项目根缺 user-facing reproduce 脚本
- TR-0603 bug 披露补救路径模糊
- TR-0604 Needle/PPL 解耦 claim 未限定 RoleAlign
- TR-0605 摘要未披露 PPL 未跑赢 KIVI
- TR-0606 K/V 消融单 seed 风险

### P0.6 复现包（TR-0010-0012）
- TR-0010 `_v3` 后缀命名不匹配（01 vs 05/07/08）
- TR-0011 01 的 7B/8B/14B 校准命令全注释（artifacts 只有 14B）
- TR-0012 论文 appendix 缺 subset/非自包含披露

---

## MEDIUM 28 条 + LOW 6 条（P3c/P3d 批量）

详见 by_dimension/D*.md。主要批量项：
- **P3c 按章**：摘要压缩（TR-0101）、图注补 seed/n（TR-0704）、消融图 caption 重写（TR-0706）、内存表注脚（TR-0715）、deterministic PPL 注脚（TR-0713）
- **P3d sed 批量**：
  - 第一人称 `我们→本文`（22 处）
  - 术语统一 `Attention-KL→attention-KL`（2 处）
  - 术语统一 `Tensor-core/tensor core→Tensor Core`（5 处）
  - 术语统一 `CUDA-core→CUDA Core`
  - 删 35 对冗余 PNG（TR-0701）
  - `\newcommand{\di}{\mathrm{d}}` + 公式微分符号（TR-0104）

---

## P3 分批计划

| 批次 | 内容 | 执行者 | 预计时间 | Commit 粒度 |
|------|------|--------|---------|-----------|
| **P3a CRIT (4)** | TR-0002/0003/0400/0401 | 主会话手动 Edit | 60-90 min | 每条独立 commit `fix(thesis): [TR-XXXX]` |
| **P3b HIGH (25)** | agent 提案 diff → 主审 → apply | general-purpose agent + 主审 | 2-3 h | 按章或维度 commit |
| **P3c MED (28)** | 按章批量（P3c1 ch1, P3c2 ch2, ...）| agent 按章 | 1-2 h | 按章 commit |
| **P3d LOW (6) + sed 批量** | 术语 / 第一人称 / 空格 | sed + dry-run → apply | 30 min | 单 commit `style(thesis): batch normalize` |

**每批后**：`latexmk -xelatex -interaction=nonstopmode main.tex` 回归编译。

---

## Approve 请求

**Auto mode 下主会话将**：
1. 立即进入 P3a 修 4 条 CRITICAL（每条 snapshot 可回滚）
2. 完成后主会话报告 diff + commit 给用户，再进 P3b
3. 若用户在任何时刻课程修正，立即停

**Top-5 建议重点关注**（来自 D6a 评分诊断，若不修答辩/投稿都有风险）：
1. TR-0002 摘要 PPL 6.0→6.1
2. TR-0003 关键词 6→4
3. TR-0400 数据污染（WikiText-103 vs wikitext-2）
4. TR-0401 非对称公式写成对称形式
5. TR-0600 摘要"四个模型"未限定 14B
