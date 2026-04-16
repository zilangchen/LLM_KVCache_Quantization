# D5 REF — 参考文献合规审查（GB/T 7714-2015 + 附件1 AI 工具引用新规）

> Reviewer: D5 REF agent  
> Date: 2026-04-17  
> Scope: `thesis/references.bib` 78 条 + `thesis/chapters/*.tex` 73 个独立 cite key  
> Spec: GB/T 7714-2015（numerical 数字编号），华南理工大学撰写规范（附件1，§参考文献 + §AI 工具）  
> Bib style: `gbt7714-numerical` + `natbib[numbers,square,super,sort&compress]`（`thesis/setup/packages.tex` L54-55）

---

## A. bib 整体健康度

### A.1 规模与引用闭合

| 指标 | 数值 | 说明 |
|------|------|------|
| bib 条目总数 | **78** | `thesis/references.bib` |
| tex 中独立 cite key | **73** | 来自 `/tmp/thesis_prescan_cites.txt`（119 条 `\cite{...}` 去重后） |
| 未引用的 bib 条目 | **5** | `bai2025longbenchv2`, `fang2025longppl`, `ouyang2025lowbit`, `schuirmann1987tost`, `zhang2024coupled` |
| 缺失的 bib 条目（cite 找不到定义）| **0** | **所有 cite key 在 bib 中均有对应，bib 闭合健康** |
| 外文文献数 | **77**（除 `kamradt2023needle` 为英文 GitHub 链接）| 满足附件1 "外文文献 2 篇以上" 要求 |
| 附件1 最低要求（10 篇参考） | **远超**（78 条 >> 10）| |

**闭合性结论**：bib 与正文引用完全闭合。没有 `\cite{...}` 指向缺失的 key。5 条未引用条目属于"保留的候选文献"，GB/T 7714 规定只列出"文中直接引用的主要参考文献"，**严格来说这 5 条应从 bib 中删除**，否则编译时 natbib 会忽略它们（`bibliographystyle{gbt7714-numerical}` 默认只列出 `\cite{}` 的项），影响不大但属于清理级 LOW 问题。

### A.2 严重度分布（总结）

| 严重度 | 数量 | 主要内容 |
|-------|------|---------|
| **HIGH (H)** | **5** | 自造/严重错误的作者信息（GEAR、ThinK、WKVQuant、QeRL、AI 工具声明缺失） |
| **MEDIUM (M)** | **8** | 已发表论文但 bib 仍标为 arXiv preprint，作者仅前 3 人但写 "others" 违反 GB/T 7714 细则 |
| **LOW (L)** | **5** | arxiv ID 缺失、DOI 缺失、未引用的孤立 bib、排版细节 |

---

## B. Top Issue 清单（TR-0500 起）

### B.1 HIGH 级（阻塞性，必须修复）

#### TR-0500 [H] `luna2024think` 作者完全自造 — 严重学术不规范

**问题**：bib 条目作者为 `Luna, Yuhui and Li, Zhe and Qu, Yifei and Chen, Tianlong and Chen, Beidi`，但论文 [arXiv:2407.21018](https://arxiv.org/abs/2407.21018) / [ICLR 2025](https://openreview.net/forum?id=n0OtGl6VGb) 真实作者为 **Yuhui Xu, Zhanming Jie, Hanze Dong, Lei Wang, Xudong Lu, Aojun Zhou, Amrita Saha, Caiming Xiong, Doyen Sahoo**。bib 中的 "Luna, Yuhui" 像是虚构 — Yuhui 是 first name, Xu 是 last name，误作 "Luna" 严重背离真实情况。

**修复建议**：
```bibtex
@inproceedings{luna2024think,
  title     = {{ThinK}: Thinner Key Cache by Query-Driven Pruning},
  author    = {Xu, Yuhui and Jie, Zhanming and Dong, Hanze and Wang, Lei and Lu, Xudong and Zhou, Aojun and Saha, Amrita and Xiong, Caiming and Sahoo, Doyen},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2025},
  note      = {arXiv:2407.21018},
}
```
同时将 bib key 改名为 `xu2025think` 或保留 `luna2024think` 以避免修改正文（建议保留 key，只改字段）。

**Evidence**：[ICLR 2025 proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/file/8edb116d5b288b6a9bba4c16ab647702-Paper-Conference.pdf)、[GitHub SalesforceAIResearch/ThinK](https://github.com/SalesforceAIResearch/ThinK)。

---

#### TR-0501 [H] `zhang2024gear` 作者完全错误 — 疑似自造

**问题**：bib 作者为 `Zhang, Hao and Song, Zhenglun and Li, Zhe and Wang, Yiming and Gao, Dayou and Han, Song and Ren, Fang and Lin, Yingyan Celine`；真实作者（[arXiv:2403.05527](https://arxiv.org/abs/2403.05527)）为 **Hao Kang, Qingru Zhang, Souvik Kundu, Geonhwa Jeong, Zaoxing Liu, Tushar Krishna, Tuo Zhao**。bib 中仅 `Han, Song` 一人在真实作者列表中出现（还是错位到倒数第三位）。venue 也错（标 ICML 但实际是 arXiv preprint，尚未确认 ICML 接收）。

**修复建议**：
```bibtex
@article{zhang2024gear,
  title   = {{GEAR}: An Efficient {KV} Cache Compression Recipe for Near-Lossless Generative Inference of {LLM}},
  author  = {Kang, Hao and Zhang, Qingru and Kundu, Souvik and Jeong, Geonhwa and Liu, Zaoxing and Krishna, Tushar and Zhao, Tuo},
  journal = {arXiv preprint arXiv:2403.05527},
  year    = {2024},
}
```
建议 bib key 改为 `kang2024gear`（与作者首字母一致），或保留原 key 仅改字段。

**Evidence**：[arXiv:2403.05527](https://arxiv.org/abs/2403.05527)、[GitHub opengear-project/GEAR](https://github.com/opengear-project/GEAR)。

---

#### TR-0502 [H] `yue2024wkvquant` 作者 first name 错误 + title 不完整

**问题**：
- bib 作者 `Yue, Jiashu and Yuan, Jiayi and Liu, Zirui and Chen, Beidi`；真实 first author 是 **Yuxuan Yue**（不是 "Jiashu Yue"），合作者也不对。
- bib title 为 `{WKVQuant}: Quantizing Weight and Key/Value Cache for Large Language Models`；实际完整 title 为 `...Large Language Models Gains More`（缺 "Gains More"）。

**Evidence**：[arXiv:2402.12065](https://arxiv.org/abs/2402.12065)。完整作者需在线核验（Yue et al.）。

**修复建议**：至少修正 first author 和 title：
```bibtex
@article{yue2024wkvquant,
  title   = {{WKVQuant}: Quantizing Weight and Key/Value Cache for Large Language Models Gains More},
  author  = {Yue, Yuxuan and ...},
  journal = {arXiv preprint arXiv:2402.12065},
  year    = {2024},
}
```

---

#### TR-0503 [H] `agarwal2025qerl` 严重多字段错误

**问题**：
1. **Title 错**：bib 为 `{QeRL}: Efficient Reinforcement Learning for LLMs via Quantized Entropy Regularization`；真实 title 是 `QeRL: Beyond Efficiency -- Quantization-enhanced Reinforcement Learning for LLMs`（完全不同的副标题）。
2. **Author 错**：bib 写 `Agarwal, Rishabh and others`；arxiv ADS 显示 first author 是 "H" 开头（2025arXiv251011696H）— 完全不是 Agarwal。
3. **Venue 错**：bib 标 "International Conference on Learning Representations (ICLR), year 2026"，但 [arXiv:2510.11696](https://arxiv.org/abs/2510.11696) 目前只是 2025-10-13 的预印本，没有 ICLR 2026 接收证据。

**修复建议**：
```bibtex
@article{agarwal2025qerl,
  title   = {{QeRL}: Beyond Efficiency -- Quantization-Enhanced Reinforcement Learning for {LLMs}},
  author  = {Huang, ... and others},  % 需在线补全
  journal = {arXiv preprint arXiv:2510.11696},
  year    = {2025},
}
```
或若要保留 ICLR 2026 立场，必须在 note 中加 "under review" 标注。强烈建议降级为 arXiv preprint。

**影响**：`ch2_related_work.tex:432` 称 "QeRL（ICLR 2026）" — 若实为 arXiv，论文正文表述也需一致修订。

---

#### TR-0504 [H] 致谢 / 全文缺少 AI 工具使用声明 — 违反附件1 2025-11 新规

**问题**：华南理工大学本科毕业设计（论文）撰写规范（附件1）§参考文献明确规定"AI工具"参考文献的书写格式：
> `[序号]"使用的提示词"提示.AI工具名称，版本，公司，日期，网址.`

该要求对应 2025-11 对论文写作过程使用 AI 辅助的明确披露规则。本论文：
- **致谢**（`thesis/chapters/acknowledgements.tex` 仅 17 行）未提及任何 AI 工具。
- **bib** 中没有符合附件1 AI 工具格式的条目。
- 但 MEMORY.md 明确记录了本论文的开发使用 `claude-in-chrome`、Codex Plugin、Codex MCP、sub-agents、`iteration.md` 记载 Bootstrap 使用 Claude Code 等 AI 工具进行写作辅助、论文审查、数据分析。
- 实际 `thesis/figures/` 目录下存在 `ch1_pipeline_gemini_cropped.png`、`ch3_framework_gemini.jpeg` 等图，明显由 Gemini 生成。

**修复建议**：
1. 在 `acknowledgements.tex` 末尾增加 AI 工具声明段，例如：
   > "本论文的文献调研、数据分析脚本编写、图表绘制过程中使用了 Claude Code（Anthropic，2026）、OpenAI Codex（OpenAI，2026）等 AI 编程辅助工具，图 1-5 与图 3-1 的流程示意图由 Gemini（Google，2026）生成初稿并经作者手动修订。所有最终的实验结果、数据分析结论和学术观点均由作者独立完成与验证。"
2. 若使用过提示词类产出的文字/公式/结论，须按附件1 格式在参考文献中加 AI 工具条目，例如：
```bibtex
@misc{ai_claude_code_2026,
  author = {Anthropic},
  title  = {``审阅本章 GQA 论述的数学一致性''},
  note   = {Claude Code CLI 使用提示},
  year   = {2026},
  howpublished = {Claude Sonnet 4.5, Anthropic, \url{https://www.anthropic.com/claude-code}},
}
```

**Evidence**：附件1 §参考文献 "AI工具：[序号]'使用的提示词'提示.AI工具名称，版本，公司，日期，网址."；`thesis/chapters/acknowledgements.tex` 全文 17 行无 AI 声明；`thesis/figures/ch1_pipeline_gemini_cropped.png` / `ch3_framework_gemini.jpeg` 文件名直接透露 Gemini 参与。

**严重度**：HIGH（这是 2025-11 合规硬性要求）。

---

### B.2 MEDIUM 级（影响规范性）

#### TR-0505 [M] 多条已正式发表但仍标 arXiv preprint（需更新 venue）

| bib key | 当前 venue | 实际 venue | Evidence |
|---------|-----------|-----------|----------|
| `hooper2024kvquant` | `arXiv:2401.18079` | **NeurIPS 2024** | [SqueezeAILab/KVQuant](https://github.com/SqueezeAILab/KVQuant) |
| `liu2024intactkv` | `arXiv:2403.01241` | **ACL 2024 Findings** | [aclanthology.org/2024.findings-acl.460](https://aclanthology.org/2024.findings-acl.460/) |
| `xiao2024duoattention` | `arXiv:2410.10819` | **ICLR 2025** | [openreview cFu7ze7xUm](https://openreview.net/forum?id=cFu7ze7xUm) |
| `lin2024qserve` | `arXiv:2405.04532` | **MLSys 2025** | [mlsys.org/virtual/2025/poster/3288](https://mlsys.org/virtual/2025/poster/3288) |
| `shutova2025aquakv` | `arXiv:2501.19392` | **ICML 2025** | [icml.cc/virtual/2025/poster/46067](https://icml.cc/virtual/2025/poster/46067) |
| `tao2024asymkv` | `arXiv:2410.13212` | **COLING 2025** | [aclanthology.org/2025.coling-main.158](https://aclanthology.org/2025.coling-main.158/) |
| `liu2024cachegen` | `Proceedings of the ACM SIGCOMM Conference`（缺地址）| **ACM SIGCOMM 2024, Sydney** | DOI: [10.1145/3651890.3672274](https://dl.acm.org/doi/10.1145/3651890.3672274) |
| `li2024snapkv` | `Advances in Neural Information Processing Systems, vol 37` | 确认 NeurIPS 2024 但缺 note/DOI | [arXiv:2404.14469](https://arxiv.org/abs/2404.14469) |

**修复建议**：统一改为 `@inproceedings` 或 `@article`，用 `booktitle` 填写正式会议名，保留 `arXiv:XXXX.XXXXX` 在 `note` 字段作为备查。示例：
```bibtex
@inproceedings{hooper2024kvquant,
  title     = {...},
  author    = {...},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS)},
  volume    = {37},
  year      = {2024},
  note      = {arXiv:2401.18079},
}
```

---

#### TR-0506 [M] 作者列表使用 `and others` 违反 GB/T 7714 "前 3 名 + et al." 规则

**问题**：GB/T 7714-2015 明确规定参考文献作者"三名以内的全部列出，四名以上的列前三名，中文后加'等'，英文后加'et al'"。BibTeX 的 `and others` 会被 `gbt7714-numerical` style 自动渲染为 "et al."，但**前提必须显式列出前 3 名**。目前以下条目前 3 名不完整就立即 `others`，违反规则：

| bib key | 当前作者字段 | 问题 |
|---------|------------|------|
| `grattafiori2024llama3` | `Grattafiori, Aaron and Dubey, Abhimanyu and Jauhri, Abhinav and others` | ✓ 合规（前 3 + et al.） |
| `jiang2023mistral` | 完整列出 10 人后 `and others` | ✓ 合规 |
| `agarwal2025qerl` | `Agarwal, Rishabh and others` | ✗ **仅 1 人**就 `others`（且作者本身错，见 TR-0503） |
| `du2026bitdecoding` | `Du, Dayou and others` | ✗ 仅 1 人就 `others` |
| `gu2025ahakv` | `Gu, Yifeng and others` | ✗ 仅 1 人就 `others` |
| `tao2024asymkv` | `Tao, Qian and others` | ✗ 仅 1 人就 `others` — 真实作者仅 3 人（Qian Tao, Wenyuan Yu, Jingren Zhou），应全列 |
| `fu2025headkv` | `Fu, Yu and others` | ✗ 仅 1 人就 `others` |
| `fogliato2024precise` | `Fogliato, Riccardo and others` | ✗ 仅 1 人就 `others`（真实作者仅 4 人，应列前 3） |

**修复建议**：对每个条目在线查全真实作者，至少列出前 3 名再加 `and others`（或全列）。

**BitDecoding 完整作者**（需补）：[arXiv:2503.18773](https://arxiv.org/abs/2503.18773) 首页列出的完整作者。  
**AsymKV 完整作者**：Qian Tao, Wenyuan Yu, Jingren Zhou（仅 3 人，应全列，不加 `and others`）。  
**HeadKV 完整作者**：Yu Fu, Zefan Cai, Abedelkadir Asi, Wayne Xiong, Yue Dong, Wen Xiao（应列前 3 + `and others`）。

---

#### TR-0507 [M] DOI 字段缺失（仅 1 条有 DOI）

GB/T 7714-2015 虽不强制 DOI，但对已发表期刊/会议论文建议提供 DOI 以增强可追溯性。当前 bib 中仅 `ouyang2025lowbit` 提供了 DOI（`10.18653/v1/2025.acl-long.1555`），其余 77 条全部无 DOI。

**修复建议**：至少为已正式发表的 EMNLP/ACL/NeurIPS/ICML/ICLR/MLSys 论文补充 DOI，例如：
- `hooper2024kvquant` → 查 NeurIPS 2024 proceedings DOI
- `liu2024cachegen` → `10.1145/3651890.3672274`
- `kwon2023vllm` → `10.1145/3600006.3613165`
- `fogliato2024precise` → `10.18653/v1/2024.emnlp-main.536`
- `bai2024longbench` → EMNLP 主会 DOI

严重度 MEDIUM（合规建议，非硬性）。

---

#### TR-0508 [M] 5 条 bib 未被引用 — 应从 bib 中删除或补充引用

未被引用的 bib key：

| bib key | 说明 | 处理建议 |
|---------|------|---------|
| `bai2025longbenchv2` | LongBench v2 | 若正文应有引用（实验章节讨论 LongBench 时）则补入；否则删除 |
| `fang2025longppl` | LongPPL 关于 PPL 问题 | 若 §4 关于 PPL 退化的讨论应引此文，补入；否则删除 |
| `ouyang2025lowbit` | Low-Bit Quantization Favors Undertrained LLMs（ACL 2025）| 该文对第 4 章 "大模型退化 < 小模型" 的讨论非常相关，**建议补入 ch4 或 ch5 正文** |
| `schuirmann1987tost` | TOST 等价性检验 | 第 4 章若用到 TOST 应引；否则删除 |
| `zhang2024coupled` | Coupled Quantization | 补入 ch2 related work；否则删除 |

GB/T 7714 规定只列出"文中直接引用的主要参考文献"，这 5 条未引用属于"bib 冗余"，`gbt7714-numerical` 默认不渲染，严重度 MEDIUM。

---

### B.3 LOW 级（细节）

#### TR-0509 [L] `velickovic2024softmax` title 大小写与 arxiv 版本不完全一致

**问题**：bib title 为 `softmax is not enough (for sharp out-of-distribution)`（小写 + out-of-distribution），但 arXiv 已更新为 `Softmax Is Not Enough (for Sharp Size Generalisation)`（同一 arxiv ID 2410.01104 的不同版本）。

**建议**：保留 arxiv v1 workshop 版本（现 bib 的），或改为最新 v2，并在 note 中注明版本。

---

#### TR-0510 [L] 中文化标识缺失（外文文献类型符号）

GB/T 7714-2015 规定中文文献需在 title 后加类型符号 `[J]`（期刊）/ `[C]`（会议录）/ `[M]`（专著）/ `[R]`（报告）/ `[D]`（学位论文）。对外文文献，`gbt7714-numerical` style 默认不输出这些符号。检查 bib 中无中文文献，**该项不适用**。

#### TR-0511 [L] 若干条目 arxiv ID 缺失

`liu2025chunkkv`（应补 `note = {arXiv:2502.00299}`）、`li2024snapkv`（应补 `note = {arXiv:2404.14469}`）、`cai2024pyramidkv`（应补 arxiv ID）等条目缺 arxiv ID，不阻塞编译但影响可追溯性。

#### TR-0512 [L] `kamradt2023needle` 缺 journal/booktitle 字段

当前：
```bibtex
@article{kamradt2023needle,
  title   = {...},
  author  = {Kamradt, Greg},
  year    = {2023},
  note    = {\url{https://github.com/gkamradt/LLMTest\_NeedleInAHaystack}},
}
```
`@article` 类型要求 `journal` 字段，但这是 GitHub 仓库项目。建议改为 `@misc` 类型：
```bibtex
@misc{kamradt2023needle,
  title        = {Needle in a Haystack --- Pressure Testing {LLMs}},
  author       = {Kamradt, Greg},
  year         = {2023},
  howpublished = {\url{https://github.com/gkamradt/LLMTest_NeedleInAHaystack}},
}
```

#### TR-0513 [L] `migacz2017tensorrt` 标注不完整

当前使用 `@inproceedings` + `booktitle = {GPU Technology Conference (GTC)}`，但 GTC 是产业展会非同行评议，严格说应标 `@misc`：
```bibtex
@misc{migacz2017tensorrt,
  title        = {8-bit Inference with {TensorRT}},
  author       = {Migacz, Szymon},
  year         = {2017},
  howpublished = {NVIDIA GPU Technology Conference (GTC) Talk},
}
```

---

## C. 抽样在线核验结果表（10 条关键引用）

| bib key | bib 记录 | 在线真实信息 | 结论 | Evidence URL |
|---------|---------|------------|------|--------------|
| `liu2024kivi` | ICML 2024, author list 完整 | ICML 2024（第 41 届）author 完整匹配 | ✓ PASS | [proceedings.mlr.press/v235/liu24bz.html](https://proceedings.mlr.press/v235/liu24bz.html) |
| `ainslie2023gqa` | EMNLP 2023, author 完整 | EMNLP 2023 Main pp.4895-4901，author 完整匹配 | ✓ PASS | [aclanthology.org/2023.emnlp-main.298](https://aclanthology.org/2023.emnlp-main.298/) |
| `dao2022flashattention` | NeurIPS 2022 vol 35 | NeurIPS 2022, 5 作者完整匹配 | ✓ PASS | [proceedings.neurips.cc/paper_files/paper/2022/hash/67d57c32e20fd0a7a302cb81d36e40d5](https://proceedings.neurips.cc/paper_files/paper/2022/hash/67d57c32e20fd0a7a302cb81d36e40d5-Abstract-Conference.html) |
| `du2026bitdecoding` | HPCA 2026, author `Du, Dayou and others` | HPCA 2026 确认（`OpenBitSys/BitDecoding`）| ⚠ WARN — author 过简，建议补 | [arxiv 2503.18773](https://arxiv.org/abs/2503.18773) |
| `xiao2023smoothquant` | ICML 2023 | ICML 2023 第 40 届，author 完整匹配 | ✓ PASS | [proceedings.mlr.press/v202/xiao23c](https://proceedings.mlr.press/v202/xiao23c.html) |
| `ashkboos2024quarot` | NeurIPS 2024 vol 37 | NeurIPS 2024 poster 94328，author 完整匹配 | ✓ PASS | [neurips.cc/virtual/2024/poster/94328](https://neurips.cc/virtual/2024/poster/94328) |
| `hsieh2024ruler` | arXiv:2404.06654 | COLM 2024，author 完整匹配（bib 显示 `arXiv preprint` 略滞后于最终发表）| ⚠ WARN — 可更新为 COLM | [arxiv 2404.06654](https://arxiv.org/abs/2404.06654) |
| `luna2024think` | `Luna, Yuhui` | **真实作者为 Yuhui Xu et al. —— 严重错误** | ✗ FAIL（见 TR-0500） | [arxiv 2407.21018](https://arxiv.org/abs/2407.21018) |
| `zhang2024gear` | `Zhang, Hao` | **真实 first author 是 Hao Kang** | ✗ FAIL（见 TR-0501） | [arxiv 2403.05527](https://arxiv.org/abs/2403.05527) |
| `agarwal2025qerl` | `ICLR 2026`, title "Quantized Entropy Regularization" | **venue 未确认接收 + title 错 + author 错** | ✗ FAIL（见 TR-0503） | [arxiv 2510.11696](https://arxiv.org/abs/2510.11696) |

**核验 pass 率：7/10（70%）** — 3 条严重错误，1 条警告。

---

## D. 排序与编号合规性

- **编号方式**：`gbt7714-numerical` style + `natbib[numbers,square,super,sort&compress]` 配置等价于 GB/T 7714 数字编号，按**正文中首次出现的顺序**编号，上标方括号 `[n]` 放引用处右上角 — ✓ 符合华南理工附件1 §参考文献 "正文中应按顺序在引用参考文献处的文字右上角用 [] 标明，[] 中序号应与参考文献中序号一致"。
- **`sort&compress`**：将同时引用的多个编号排序合并（如 `[1,2,3]` → `[1-3]`）— GB/T 7714 允许，符合规范。
- **参考文献区域字号字体**：由 `gbt7714-numerical.bst` 控制，需确认编译后实际输出为"小四号宋体，1.5 倍行距"（该项不在 bib/tex 范围内，由 `\bibliography` 所在页面的段落格式决定，属 D2 FMT 审查范围）。

**结论**：排序/编号全部合规。

---

## E. 总结与优先级建议

1. **必须立即修复（投稿前阻塞）**：TR-0500（ThinK 作者自造）、TR-0501（GEAR 作者自造）、TR-0502（WKVQuant first name 错）、TR-0503（QeRL 多字段错）、TR-0504（AI 工具声明缺失）。
2. **强烈建议修复**：TR-0505（8 条 venue 需更新）、TR-0506（6 条 `and others` 违 GB/T 7714 前 3 规则）、TR-0508（5 条未引用 bib 清理）。
3. **建议补全**：TR-0507（DOI 字段）、TR-0509-0513（细节）。

修复工作量估算：~3 小时（主要在 TR-0500/0501/0502 的作者在线核对 + TR-0504 致谢重写 + TR-0505 的 note 字段批量改 venue）。

---

## 附：核验方法论

- **静态对比**：
  - `grep '^@' thesis/references.bib` → 提取 78 个 bib key
  - `grep -oE '\\cite[tp]?\{[^}]+\}' thesis/chapters/*.tex` → 提取 119 个 cite 实例，去重后 73 个 key
  - `comm` 对比 → 5 条 bib 未被引用 + 0 条 cite 缺失
- **在线核验**：对 10 条关键引用使用 WebSearch 核验 venue / author / title，来源限制为 arxiv.org、aclanthology.org、proceedings.neurips.cc、proceedings.mlr.press、icml.cc、neurips.cc、iclr.cc、mlsys.org、dl.acm.org、openreview.net。
- **规范对标**：附件1《华南理工大学本科毕业设计（论文）撰写规范》§参考文献 + §AI 工具 + §字号字体。

_本审查由 D5 REF agent 完成于 2026-04-17。所有 Evidence URL 均来自公开来源（arxiv、ACL Anthology、会议官网），可独立核验。_
