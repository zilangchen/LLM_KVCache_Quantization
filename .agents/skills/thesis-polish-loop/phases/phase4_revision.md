# Phase 4: Revision（论文修改与精炼）

> 三子阶段：(4a) 内容修改 → (4b) SCUT 格式校验 → (4c) 交叉审核 + AI 痕迹消除。

---

## 输入
- `reports/round_N/expert_reviews.md` — Phase 3 的汇总意见
- `state/scut_baseline_audit.md` — Round 0 的格式基线
- `state/ai_trace_audit.md` — 历史 AI 痕迹模式
- 当前 thesis/chapters/*.tex

## 输出
- 修改后的 thesis/chapters/*.tex
- 每个 milestone 独立 commit
- `state/closed_comments.md` 追加已闭环 issue
- 更新 `state/known_issues.md`

---

## 4a: 内容修改

### Step 4a.1: 筛选本轮可修改的 issues

从 `expert_reviews.md` 中选择 `Needs experiment? = no` 的 issue。按 severity 排序：
1. CRITICAL 必做
2. MAJOR 尽量做
3. MINOR 有时间就做
4. NIT 本轮不做

### Step 4a.2: 按 file 分组修改

对每个 .tex 文件：
1. 读取当前内容
2. 逐个应用 issue 对应的修改
3. 每个大的修改点做一次 xelatex 编译验证
4. 如编译失败 → 立即回滚该次修改，降级严重度，留给下轮

### Step 4a.3: 跨章节一致性维护

每次修改某个数据/术语后：
- grep 该数据/术语在所有 chapters/ 下的出现位置
- 同步更新所有相关位置
- 否则会引入新的不一致

**禁止**：只改一处不改其他，即使"另一处下轮再改"。

---

## 4b: SCUT 格式校验（次要目标）

### Step 4b.1: 基础格式检查（每轮都做）

对修改后的论文运行以下检查：

```bash
# 1. 章节命名
grep -E "\\chapter\{Chapter [0-9]|\\chapter\{第[一二三四五六]章" thesis/chapters/*.tex

# 2. 图表编号
grep -oE "图[0-9]+-[0-9]+|表[0-9]+-[0-9]+|Figure [0-9]+|Table [0-9]+" thesis/chapters/*.tex

# 3. 参考文献数量
grep -c "\\bibitem\|@article\|@inproceedings" thesis/references*.bib

# 4. 正文字数（粗略）
wc -w thesis/chapters/ch[1-5]*.tex thesis/chapters/abstract_zh.tex
# 目标：≥15000 字

# 5. 摘要长度
wc -w thesis/chapters/abstract_zh.tex
# 目标：400-600 字（中文）
```

### Step 4b.2: LaTeX 配置检查

检查 `thesis/main.tex` 或相关 .sty 的 LaTeX 配置是否符合 SCUT 规范：

- `geometry` 包是否设置 25mm 边距
- `fancyhdr` 是否设置奇偶页不同页眉
- `pagestyle` 是否支持罗马/阿拉伯两套页码
- `ctexbook` 的章节字号是否符合 SCUT
  - 一级：小二号黑体
  - 二级：小三号黑体
  - 三级：四号黑体
  - 正文：小四号宋体

### Step 4b.3: 参考文献格式抽检

随机抽 3-5 条 bib 条目，手动比对 SCUT 规范：
```
期刊: [序号] 作者. 题名[J]. 刊名, 年, 卷(期): 页码.
专著: [序号] 作者. 书名[M]. 出版地: 出版单位, 年份: 页码.
学位论文: [序号] 作者. 题名[D]. 单位所在地: 单位, 年.
```

作者数：≤3 全列，≥4 列前 3 + "等"/"et al"。

### Step 4b.4: 开发细节清理

```bash
# 搜索可能混入的开发细节
grep -nE "commit|dirty|hotfix|bug|PRF-|EVL-|CAL-|R[0-9]+ review" thesis/chapters/*.tex
```

任何 match 都要评估：
- 是内部 git commit 引用？→ 删除
- 是对审稿人透明度披露？→ 保留但简化措辞
- 是 CI/CD 状态？→ 删除

### Step 4b.5: 编译验证

```bash
cd thesis && xelatex -interaction=nonstopmode main.tex && bibtex main && xelatex ... && xelatex ...
grep -c "??" thesis/main.aux  # 应为 0
grep "Warning.*undefined" thesis/main.log  # 应为空
```

任何编译错误或 undefined refs → 必须修复后才能进入 4c。

---

## 4c: 交叉审核 + AI 痕迹消除

### Step 4c.1: 识别高风险段落

从 `reports/round_N/paper_review.md` 的 "AI 痕迹热点段落" 清单 + 本轮 Phase 4a 新修改的段落。

### Step 4c.2: 2-Agent Cross Review

对每个高风险段落，**并行**启动 2 个 sub-agent：

**Agent A: 人类读者角色**
```
你是一位 50 岁的资深学术研究者，刚从书架上拿起一篇学生论文翻阅。
请阅读下面的段落，回答一个简单的问题：

"这段话读起来像一个真实的人类研究者写的吗？还是像 AI 写的？"

如果像人写的，回答 YES 并简要说明哪里自然。
如果像 AI，回答 NO 并具体指出：
- 哪句话不自然
- 为什么不自然（句式太均匀？连接词太机械？解释冗余？语气太正式？）

段落：
<粘贴段落内容>
```

**Agent B: AI 痕迹检测器**
```
你是一位专门识别 AI 生成文本痕迹的专家。请分析下面的学术段落：

段落：
<粘贴段落内容>

找出所有可能的 AI 生成痕迹：
1. 机械化连接词（"此外"、"然而"、"因此"密集使用）
2. 句式过于均匀（每句字数相近）
3. 冗余解释（同一观点换几种说法重复）
4. 过度正式（用书面语代替自然表达）
5. 模板化词汇（"显著"、"明显"、"综上所述"、"据悉"等）

如果 CLEAN（无可疑痕迹）→ 回答 CLEAN
如果 HAS TRACES → 列出具体位置和改进建议
```

### Step 4c.3: 判定与修改

- **A=YES 且 B=CLEAN** → 段落通过，进入下一个
- **A=NO 或 B=HAS TRACES** → 根据建议手动重写该段：
  - 不要机械替换词汇（"显著"→"明显"这种是另一种 AI 模板）
  - 尝试改变整体结构（主语/语序/句长），不只是单词
  - 重写后再送一次 2-agent 审核
  - 最多重写 3 次，仍不过 → 记录到 `state/ai_trace_audit.md` 留给下轮

### Step 4c.4: 记录 AI 痕迹模式

每次通过 2-agent 审核的改写都记录到 `state/ai_trace_audit.md`：
```
## Round N — AI Trace Pattern
- Location: ch3:L369-372
- Original: "$\tau^{-1}$ 作为诊断框架的结构性产出呈现"
- A said: NO — 句式太书面语，"呈现" 不像人会用的动词
- B said: HAS TRACES — "结构性产出" 是典型 AI 模板化词汇
- Rewrite: "在做这组实验的过程中，我们意外发现 $\tau^{-1}$ 的这个规律"
- Both pass: YES
```

这个文件随时间累积会形成 **本项目专属的 AI 痕迹词典**，下一轮 Phase 2 可以用它做初筛。

---

## 4d: Commit 每个 milestone

按 file 或 consensus issue group 分组 commit：

```
refactor(thesis): Round N - address <consensus issue summary>

- Issue CONS-001: <description>
- Issue CONS-002: <description>

AI trace removal: X paragraphs rewritten, all pass 2-agent review.

Related: reports/round_N/expert_reviews.md
```

---

## 4e: 更新 state

1. 把本轮已处理的 issues 追加到 `state/closed_comments.md`
2. 未处理的 issues 保留在 `state/known_issues.md`
3. 追加 `state/ai_trace_audit.md`（新模式）

---

## 重要约束

1. **不跳过 4b/4c**：即使时间紧，4b 和 4c 必须执行至少一遍
2. **编译验证是门禁**：任何不能编译的修改不得 commit
3. **数据同步优先**：发现不一致必须全文同步修改
4. **AI 痕迹的判定权在 2 个 agent 一致同意**
5. **时间盒**：90 分钟

---

## 与其他 phase 的交接

- **输入←Phase 3**：expert_reviews.md 的 consensus issues
- **输入←Phase 2**：paper_review.md 的 AI trace hotspots
- **输出→Phase 5**：留给实验的 issues 流入 rerun_queue
- **输出→下一轮**：更新 state/ 所有文件
