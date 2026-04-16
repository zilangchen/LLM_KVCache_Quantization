# 最终合规对照表（交付学校用）

> **版本**：P4 终审通过版（2026-04-17）
> **编译产物**：`thesis/main.pdf`（116 页, 5.86 MB, xelatex 0 error）
> **baseline**：tag `thesis-final-review-baseline`
> **最新 commit**：d48dad2（P3c+P3d 批量，9 commits 自 baseline）

---

## 附件1《华南理工大学本科毕业设计（论文）撰写规范》（2025 年 11 月版）逐条对照

### A. 封面与前置部分

| 条款 | 要求 | 实际状态 | 证据位置 |
|------|------|---------|---------|
| §封面 | 学校名、论文性质、题目、学院、专业、姓名、学号、导师、提交日期 | ✓ | `commands.tex:\makecover` + PDF P1 |
| §原创性声明 | 独立研究 + 引用标注 + 签名栏 + 日期 | ✓ | `commands.tex:\makedeclaration` + PDF P2 |
| §版权使用授权书 | 学校使用权 + 作者签名 + 指导教师签名 | ✓ | `commands.tex:\makedeclaration` + PDF P2 |
| §中文摘要字数 | 400-600 字 | ✓（约 510 字） | `abstract_zh.tex:5-50` + PDF P3 |
| §英文摘要 | 与中文对应 | ✓ | `abstract_en.tex:5-66` + PDF P4 |
| §关键词数量 | 3-5 个，中英对齐 | ✓（5 个：大语言模型；键值缓存量化；行为对齐校准；非对称量化；GQA 架构）| `abstract_zh.tex:48` / `abstract_en.tex:62-64` — **TR-0003 已修复**（原 6 个 → 5 个）|

### B. 字号字体

| 条款 | 要求 | 实际状态 | 证据位置 |
|------|------|---------|---------|
| §章标题 | 小二号黑体，居中 | ✓ | `format.tex:12-18` (`\zihao{-2}\heiti`) |
| §节标题（一级）| 小三号黑体，左对齐 | ✓ | `format.tex:19-25` (`\zihao{-3}\heiti`) |
| §节标题（二级）| 四号黑体 | ✓ | `format.tex:26-32` (`\zihao{4}\heiti`) |
| §正文字体 | 小四号宋体 | ✓ | `format.tex` + 默认 ctexbook 配置 |
| §行距 | 1.5 倍 | ✓ | `format.tex:8` (`\onehalfspacing`) |
| §段落首行缩进 | 2 字符 | ✓ | `format.tex:11` (`\setlength{\parindent}{2em}`) |

### C. 页眉页脚与页码

| 条款 | 要求 | 实际状态 | 证据位置 |
|------|------|---------|---------|
| §页眉 | 双页"华南理工大学学士学位论文"，单页章名 | ✓ | `header.tex:23-27` (`\fancyhead[CE]` + `[CO]`) |
| §页眉线 | 1.0 pt 单线 | ✓ | `header.tex:29` (`\headrulewidth{1.0pt}`) |
| §页脚 | 居中页码五号宋体 | ✓ | `header.tex:28` (`\zihao{5}\thepage`) |
| §前置页码 | 罗马数字（i, ii, iii...）| ✓ | `header.tex:\fancypagestyle{frontmatter}` + PDF 目录 P(iii) |
| §正文页码 | 阿拉伯数字（1, 2, 3...）| ✓ | `header.tex:\fancypagestyle{mainmatter}` + PDF Ch1 P1 |

### D. 图表与公式

| 条款 | 要求 | 实际状态 | 证据位置 |
|------|------|---------|---------|
| §图表按章编号 | X-Y 格式（如 图 3-1, 表 4-2）| ✓ | `format.tex:61-66` (`\counterwithin{figure}{chapter}` + `\thechapter-\arabic{figure}`) |
| §图题位置 | 图下方 | ✓ | `format.tex:49-53` (`captionsetup[figure]{position=bottom}`) |
| §表题位置 | 表上方 | ✓ | `format.tex:54-58` (`captionsetup[table]{position=top}`) |
| §三线表 | 仅顶/中/底三线，无左右列线 | ✓ | `packages.tex:8` (booktabs + `\toprule/\midrule/\bottomrule`) |
| §表注 | `threeparttable` 支持 footnotes | ✓ | `packages.tex:14` (threeparttable 加载) |
| §公式编号 | (X-Y) 右对齐 | ✓ | `format.tex:64,66` (`\counterwithin{equation}{chapter}` + `\theequation`) |
| §图表文字字号 | 五号宋体（小字号 5/7.5/10.5pt 适配）| ✓ | `format.tex:41-46` (`captionsetup{font=small}`) |

### E. 参考文献（GB/T 7714）

| 条款 | 要求 | 实际状态 | 证据位置 |
|------|------|---------|---------|
| §引用格式 | 正文右上角数字 [X] | ✓ | `packages.tex:54-55` (`natbib, numbers, square, super, sort&compress`) |
| §文献样式 | GB/T 7714-2015 顺序编码制 | ✓ | `packages.tex:56` (`\bibliographystyle{gbt7714-numerical}`) |
| §多重引用合并 | [1-3] 连续合并 | ✓ | `packages.tex:54` (`sort&compress`) |
| §文献类型标识 | [M]/[J]/[C]/[A] 分类 | ✓ | PDF P87-93 参考文献页 — `gbt7714-numerical` 自动加 |
| §作者真实性 | Author 字段必须真实 | ✓ | **TR-0500 (ThinK) + TR-0501 (GEAR) + TR-0502 (WKVQuant) 三条伪造已修复，commit 8771e79** |
| §至少 3 作者列 et al. | "..., and others" | 部分 ✓ | TR-0506 仍有 6 条 `and others` 只列单作者（MED 级遗留，不阻塞提交）|
| §DOI 补全 | 建议但不强制 | 部分 | TR-0507 大多数条目无 DOI（MED 级遗留）|
| §无 dangling citation | `\cite` 全部在 bib 定义 | ✓ | 核查：73 cite + 78 bib = 0 undefined + 5 uncited（TR-0508 已知）|

### F. AI 工具声明（2025-11 新规）

| 条款 | 要求 | 实际状态 | 证据位置 |
|------|------|---------|---------|
| §AI 工具使用披露 | 致谢中声明使用的 AI 工具 + 具体用途 | ✓ | `acknowledgements.tex:15-26` + PDF P108 — **TR-0504 已修复** |
| §AI 工具列表 | 具体工具名 + 公司 | ✓ | ChatGPT (OpenAI)、Claude (Anthropic)、Gemini (Google)、GitHub Copilot (GitHub/OpenAI) |
| §用途分类 | 明确哪些用途使用 AI | ✓ | (1) 代码辅助 (2) 文献检索/术语解释/英文润色 (3) LaTeX 纠错 (4) 图像素材生成 |
| §独立性声明 | 核心研究思路由作者独立完成 | ✓ | `acknowledgements.tex:24-25` "所有核心研究思路、问题提出、方法设计、实验方案、数据分析与结论均由作者独立完成，AI 工具仅承担辅助角色" |

### G. 数据一致性（P3 修复后）

| 条款 | 要求 | 实际状态 | 证据位置 |
|------|------|---------|---------|
| §数据一致性 | 摘要/正文/结论数字一致 | ✓ | **7B PPL 退化 6.1% 全文 0 处 6.0% 残留**（TR-0002/0309 已修复）|
| §校准数据披露 | 校准/评测数据集明确 | ✓ | **WikiText-2 test split 12 处一致，不再有 -103 残留**（TR-0400 已修复，commit 9be37d8）|
| §14B 数据披露 | PPL 评测 tokens 数子集说明 | ✓ | **tab:rolealign-results 脚注 b 披露 14B 32767 tokens 对应完整 split 前缀**（TR-0303/0308 已修复）|
| §FP16 权威值 | 双协议披露 | ✓ | `INDEX.md:L73` 披露 14B FP16 4.685（32K 子集）/ 5.455（302K 完整）|
| §RoleAlign 限定 | 未跑赢 KIVI 的诚实披露 | ✓ | 摘要 L40-42 + ch4:1448-1457 明确"INT4-RoleAlign 相对 KIVI-style baseline 在 PPL 数值上未体现一致优势"（TR-0605 已修复）|

### H. 复现包（TR-0010/0011/0012 修复后）

| 条款 | 要求 | 实际状态 | 证据位置 |
|------|------|---------|---------|
| §复现脚本入口 | 一键复现主线实验 | ✓ | `REPRODUCE.md` 根目录 + `results/final/final_scripts/reproduce/*.sh` 10 脚本 |
| §校准文件命名 | 脚本引用一致 | ✓ | **01_calibrate 产出 + 05/07/08 引用 `kv_calib_rolealign_*_v3.json` 对齐**（TR-0010 已修复）|
| §前置产物披露 | 7B/8B/14B 校准脚本可用 | ✓ | **01_calibrate.sh 已启用 7B/8B/14B 校准命令 + README 顶部披露**（TR-0011 已修复，commit 2b8596c）|
| §subset 复现披露 | 附录明确说明复现包范围 | ✓ | **appendix.tex:38-82 新增 §A.2 "复现脚本与覆盖范围"**（TR-0012 已修复，commit 7f58a1c）|
| §N=128 vs N=16 披露 | 正文与实际校准参数对齐 | ✓ | appendix.tex:72-81 明确 B10 消融验证 N=16 已进入平坦收敛域 |

### I. §3.5 非对称公式完整性（TR-0401 修复后）

| 条款 | 要求 | 实际状态 | 证据位置 |
|------|------|---------|---------|
| §非对称公式完整性 | Scale + zero-point 完整定义 | ✓ | **ch3_method.tex:679-710 (`eq:ch3-perchannel-k` + `eq:ch3-pertoken-v`) 含 min/max + $s$ + $z$ 完整定义**（TR-0401 已修复，commit 80e88e5）|
| §q_min/q_max 明确 | INT4/INT8 整数值域 | ✓ | ch3:691 `q_min=-8, q_max=7`（INT4），`q_min=-128, q_max=127`（INT8）|
| §量化规则 | 量化 + 反量化完整 | ✓ | ch3:693-695 `q = clamp(round((x-z)/s), q_min, q_max)`, `x̂ = q·s + z` |
| §退化为 KIVI | $(p_K, p_V)=(100,100)$ 与 KIVI 重合披露 | ✓ | ch3:707 "对应 KIVI-style absmin/absmax 配置" |

### J. 页数与结构

| 条款 | 要求 | 实际状态 | 证据位置 |
|------|------|---------|---------|
| §页数 | 推荐 40-120 页 | ✓（116 页） | `ls main.pdf` + `main.log` 最后 "Output written on main.xdv (116 pages)" |
| §章节完整性 | Ch1-Ch5 + 附录齐全 | ✓ | ToC P(iii)-(viii) |
| §独立声明 | 原创声明 + 版权授权 | ✓ | PDF P2 双签名栏齐全 |
| §致谢 | 独立致谢段 | ✓ | PDF P108（新含 AI 工具声明）|

---

## 合规分布统计（J 类条款）

| 类别 | 条款数 | ✓ 完全满足 | 部分 ⚠ | ✗ 未满足 |
|------|-------|-----------|--------|---------|
| A. 封面前置 | 6 | 6 | 0 | 0 |
| B. 字号字体 | 6 | 6 | 0 | 0 |
| C. 页眉页脚 | 5 | 5 | 0 | 0 |
| D. 图表公式 | 7 | 7 | 0 | 0 |
| E. 参考文献 | 8 | 6 | 2（TR-0506 `and others`, TR-0507 DOI）| 0 |
| F. AI 工具声明 | 4 | 4 | 0 | 0 |
| G. 数据一致性 | 5 | 5 | 0 | 0 |
| H. 复现包 | 5 | 5 | 0 | 0 |
| I. §3.5 公式 | 4 | 4 | 0 | 0 |
| J. 页数结构 | 4 | 4 | 0 | 0 |
| **总计** | **54** | **52（96.3%）** | **2（3.7%）** | **0（0%）** |

---

## 签收

- 指导教师签名：________________ 日期：______年______月______日
- 评阅教师签名：________________ 日期：______年______月______日
- 答辩秘书签名：________________ 日期：______年______月______日

---

## 附：P3 修复 commit 追踪（便于答辩现场证据展示）

| Commit | 内容 | 修复 TR |
|--------|------|---------|
| b035700 | 7B PPL degradation 6.0% → 6.1% | TR-0002 |
| 0dee068 | Keywords 6 → 5（附件1 §3.4）| TR-0003 |
| 9be37d8 | WikiText-103 → WikiText-2 + 数据污染披露 | TR-0400 |
| 80e88e5 | §3.5 非对称公式 min-max + zero_point | TR-0401 |
| 8771e79 | bib 作者修正（GEAR/ThinK/WKVQuant）| TR-0500/0501/0502 |
| 2b8596c | 复现脚本 calib 命名对齐 + 7B/8B 披露 | TR-0010/0011 |
| 2eafdeb | P3b-1 HIGH 14 类 | TR-0302/0309/0310/0312/0314/0315/0402/0403/0406/0407/0600/0601/0602/0603 |
| 7f58a1c | P3b-2 HIGH 9 类（含 AI 声明/复现披露）| TR-0012/0301/0318/0404/0405/0408/0504/0604/0605 |
| d48dad2 | P3c+P3d MED/LOW 20 类 + 35 图片 | TR-0306/0307/0311/0313/0316/0317/0319/0409-0420 |
