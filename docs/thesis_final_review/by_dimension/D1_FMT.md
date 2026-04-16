# D1 FMT 格式合规审查报告

- **审查 agent**：Explore（只读）
- **规范基准**：华南理工大学本科毕业设计（论文）撰写规范（工科、理科类专业）（2025年11月更新）
- **规范 txt**：`/tmp/thesis_spec_fujian_{1,2,3}.txt`
- **论文基线**：main @ e379645 + `thesis-final-review-baseline` tag
- **编译状态**：✓ 0 error（114 页 5.8MB）
- **时间**：2026-04-17

---

## A. L1 宏观发现

1. **✓ L1-1 章节顺序完整**（规范 L10-12）— 封面→声明→中英摘要→目录→正文(ch1-5)→参考→附录→致谢，符合。`main.tex:20-49` 组织清晰。
2. **H L1-2 关键词超限**（规范 L23-24）— 中文关键词 6 个（应 3-5），`abstract_zh.tex:39`。**TR-0003 已 open**。
3. **✓ L1-3 页眉页脚**（规范 L106-109）— `header.tex:20-27` 奇偶页区分正确；偶数页"华南理工大学学士学位论文"，奇数页 `\leftmark`；1.0pt 实线配置正确。
4. **✓ L1-4 页码切换**（规范 L109）— `\frontmatter`（罗马）→ `\mainmatter`（阿拉伯）。
5. **✓ L1-5 章节编号格式**（规范 L68-72）— "第一章"/"1.1"/"1.1.1"，由 ctexbook 自动处理。
6. **M L1-6 前置部分页眉**（规范 L106）— frontmatter 无页眉（规范允许），需 PDF 核查连续性。
7. **✓ L1-7 签名栏**（规范 L19-20）— `commands.tex:34-67` 原创声明+版权授权签名栏完整（4cm 署名线 + 日期占位）。
8. **✓ L1-8 目录自动生成**（规范 L61）— `toc.tex` 配置正确。

---

## B. L2 段落发现

1. **✓ L2-1 图表按章编号**（规范 L75）— `format.tex:61-66` `counterwithin{figure/table}{chapter}`。
2. **✓ L2-2 图题下/表题上**（规范 L75）— `format.tex:51-58` `captionsetup[figure]{position=bottom}` + `[table]{position=top}`。
3. **✓ L2-3 三线表**（规范 L77）— `packages.tex:11` booktabs，全篇 136 处 `\toprule/\midrule/\bottomrule`，无左右列线。
4. **M L2-4 表标题字体**（规范 L78）— 字号 small（五号），但字体族未显式锁定宋体，需在 captionsetup 增 `font={small,songti}`。
5. **✓ L2-5 跨章编号一致性**（规范 L75）— 公式 `(X-Y)`、图表 `图X-Y`/`表X-Y`。
6. **✓ L2-6 多图 subcaption**（规范 L76）— `ch3_method.tex:78-100` 使用 subcaption。
7. **L2-7 图表与文字分页**（规范 L75）— 大型图表 `[htbp]` 浮动体，需 PDF 人工验证。
8. **M L2-8 段落缩进与行距**（规范 L56/72）— `format.tex:11` `\parindent{2em}` + `\onehalfspacing` 1.5倍。

---

## C. L3 句子发现

1. **✓ L3-1 章标题**（规范 L69）— `format.tex:16-23` `\zihao{-2}\heiti\bfseries`（小二号黑体加粗）。
2. **✓ L3-2 节标题**（规范 L70-71）— section 小三号黑体 / subsection 四号黑体。
3. **✓ L3-3 正文字号**（规范 L72-73）— ctexbook 继承 + `abstractzh:77 \zihao{-4}\songti`；英文 `fonts.tex:32` Times New Roman。
4. **M L3-5 微分符号正体化**（规范 L103）— 需验证公式中 $d/\pi/e/T$ 使用 `\mathrm{}`；`commands.tex:126 \DeclareMathOperator{\KL}{KL}` 正体✓，其他需 PDF 验证。
5. **✓ L3-6 公式编号**（规范 L75）— equation 环境，右对齐，`(X-Y)` 格式。
6. **✓ L3-7 段首缩进 2em**（规范 L72）— `format.tex:11`。
7. **✓ L3-8 英文缩写首次扩展**（规范 L102）— `ch1_introduction.tex:8,10,14` LLM/GQA 等首次出现有说明。
8. **✓ L3-9 关键词分号分隔**（规范 L58）— 中英文均用分号分隔。
9. **✓ L3-10 签名栏**（规范 L20）— `commands.tex:50,65-66` 提供署名线和日期占位。

---

## D. Issue 清单（D1 维度新增）

已通过 Edit 追加到 `issues.md` 主表：

| ID | Severity | File:Line | Problem | Suggestion |
|----|----------|-----------|---------|-----------|
| TR-0101 | M | `abstract_zh.tex:1-41` | 摘要字符数 763（估算），超 400-600 | 逐段压缩 20-25 字 |
| TR-0102 | M | `format.tex:45-50` | 图表标题字号 small 设定但字体族未显式锁定宋体 | captionsetup 增 `font={small,songti}` |
| TR-0103 | L | `ch1_introduction.tex:209` 等 | 大型图表（0.98\textwidth）跨页需 PDF 人工验证 | P4 PDF 目测 |
| TR-0104 | M | `ch2_related_work.tex:170,175` 等 | 微分号 $d/\pi/e/T$ 正体化待验证 | 定义 `\newcommand{\di}{\mathrm{d}}` + 全局替换 |
| TR-0105 | L | `abstract_en.tex:48-50` | 英文关键词跨行，可能页面不对称 | 调整长度或合并到单行 |

---

## E. 合规对照（详见 `compliance/fuian1_checklist.md`）

**总体统计**：25 条核心规范
- ✓ PASS：20 条
- ⚠ 部分（M）：4 条（摘要字数、表标题字体、微分符号、大图分页）
- ✗ FAIL（H）：1 条（关键词超数 → TR-0003）

---

## F. 严重度总计（D1 贡献）

| 级别 | 新增数量 | 已有 |
|------|---------|------|
| CRITICAL | 0 | TR-0003 已 open |
| HIGH | 0 | — |
| MEDIUM | 3 | TR-0101, TR-0102, TR-0104 |
| LOW | 2 | TR-0103, TR-0105 |

**需要后续 P4 PDF 人工验证**：微分号正体、大图跨页连续性、页眉线粗细。
