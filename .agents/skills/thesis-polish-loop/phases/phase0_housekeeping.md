# Phase 0: Housekeeping（闭环回填 + 状态恢复）

> 每一轮都以 Phase 0 开始。核心职责：(1) 从 state/ 恢复记忆，(2) 回填上轮未闭环的实验。

---

## 输入
- `state/round_counter.json`
- `state/running_experiments.json`
- `state/rerun_queue.json`
- `state/last_checkpoint.json`（若有）

## 输出
- 当前轮次号 N
- 已完成实验的闭环 commit（可能多个）
- 更新后的 state/ 文件

---

## 执行步骤

### Step 0.1: 恢复跨轮记忆
1. Read `state/round_counter.json` → 获取上轮号 N-1、起止时间
2. Read `state/venues_read.json` → 已读 venue 清单
3. Read `state/known_issues.md` → 累积待办
4. Read `state/closed_comments.md` → 已闭环意见
5. Read `state/ai_trace_audit.md` → 历史 AI 痕迹模式
6. 计算当前轮次 N = (N-1) + 1
7. 记录本轮开始时间到 `state/round_counter.json`

### Step 0.2: Round 0 特殊处理（只在首轮执行）
**如果** N == 0（首次运行）：
- 执行 **SCUT 合规基线扫描**（见下方子流程）
- 输出 `state/scut_baseline_audit.md`
- **然后跳过 Step 0.3-0.6**，直接进入 Phase 1

### Step 0.3: 检查中断点恢复
**如果** `state/last_checkpoint.json` 存在且 status != completed：
- 从 checkpoint 的 phase 继续执行（不从 Phase 1 重新开始）
- 报告："从 Round N Phase X 恢复"

### Step 0.4: 扫描已完成实验（闭环回填核心）
对 `state/running_experiments.json` 中的每个 entry：

1. 检查 `expected_output_glob` 是否已存在：
   ```bash
   ls <expected_output_glob> 2>/dev/null
   ```
2. **已存在** → 实验完成：
   - 读取 CSV / JSON 输出文件
   - 提取 `closure_action.instructions` 需要的数据
   - 执行 `closure_action.type` 对应的修改：
     - `update_table_with_data`: 用新数据更新指定表格
     - `add_footnote`: 在指定位置加脚注
     - `add_paragraph`: 在指定位置插入段落
     - `update_number_inline`: 替换正文中的具体数字
   - 运行 xelatex 验证编译通过
   - Commit: `feat(thesis): close R(M)-EXP-XXX — <motivation>`
   - 从 `running_experiments.json` 移除
   - 追加到 `state/closed_comments.md`
3. **未存在** → 检查超时：
   - 若 `N - round_triggered > config.phase5_experiments.timeout_rounds` → 
     - 标记为 `timed_out`
     - 移到 `state/known_issues.md`，作为"待补充实验"
     - 从 `running_experiments.json` 移除
4. **仍在运行** → 保持状态不变

### Step 0.5: 清理孤儿状态
- 扫描 `state/rerun_queue.json` 中 status=queued 但没有对应 running 的条目
- 若存在 → 重新标记为 running（可能上轮触发失败）或 failed（视情况）

### Step 0.6: 写入恢复报告
输出到 `reports/round_N/phase0_housekeeping.md`：
- 恢复的状态摘要
- 本轮闭环的实验数量 + commit hash
- 超时转为 known issue 的数量
- Phase 1 是否可以开始（gate check）

---

## Round 0 子流程：SCUT 合规基线扫描

**仅在首次运行时执行一次**。目的：建立格式偏差基线供后续 Phase 4b 参考。

### 检查清单

```
├─ [ ] 摘要字数是否在 400-600 之间（中文）
│     grep -c: wc -w thesis/chapters/abstract_zh.tex
├─ [ ] 中英文摘要内容是否完全一致（段落数对齐）
├─ [ ] 关键词数量是否 3-5 个
│     grep -oE "\\keywords[a-z]+\\{[^}]+\\}"
├─ [ ] 正文总字数是否 ≥15000
│     wc -w thesis/chapters/ch*.tex
├─ [ ] 章节命名是否使用"第X章"（SCUT 要求）
│     grep "第一章|第二章|第三章|第四章|第五章" thesis/chapters/*.tex
├─ [ ] 图表编号是否按章（图X-Y / 表X-Y）
│     grep -oE "(图|表)[0-9]+-[0-9]+" thesis/chapters/*.tex
├─ [ ] 参考文献总数是否 ≥10
│     grep -c "\\bibitem" thesis/references*.bib OR count in .bbl
├─ [ ] 外文参考文献是否 ≥2
├─ [ ] 参考文献格式是否符合 SCUT 模板（[序号] 作者. 题名[J]. 刊名 年 卷(期): 页码.）
├─ [ ] 页眉奇偶页是否正确设置
│     grep "fancyhead" thesis/main.tex OR thesis/*.sty
├─ [ ] 页码两套是否正确（摘要罗马，正文阿拉伯）
├─ [ ] 页面边距是否 25mm（SCUT 要求）
│     grep "geometry" thesis/main.tex
├─ [ ] 字体字号是否符合 SCUT 规范
│     检查一级标题是否小二号黑体，正文是否小四号宋体
├─ [ ] iteration.md 级别的开发细节是否混入正文
│     grep "commit|dirty|hotfix|PRF-|EVL-|CAL-" thesis/chapters/*.tex
└─ [ ] 外文翻译（5000 汉字）是否已准备
```

### 输出
`state/scut_baseline_audit.md`：

```markdown
# SCUT Baseline Audit — Round 0

Generated: YYYY-MM-DD HH:MM
Thesis HEAD: <commit-hash>

## Compliance Status

| # | Check | Status | Details | Priority |
|---|-------|--------|---------|----------|
| 1 | 摘要字数 400-600 | ✅/❌ | 当前 X 字 | HIGH |
| 2 | 中英文摘要一致 | ✅/❌ | ... | HIGH |
| 3 | 关键词 3-5 个 | ✅/❌ | 中文 X，英文 Y | MEDIUM |
| 4 | 正文 ≥15000 字 | ✅/❌ | 当前 X 字 | HIGH |
| 5 | 章节命名 "第X章" | ✅/❌ | ... | MEDIUM |
| 6 | 图表按章编号 | ✅/❌ | ... | MEDIUM |
| 7 | 参考文献 ≥10 | ✅/❌ | X 篇 | HIGH |
| 8 | 外文参考 ≥2 | ✅/❌ | X 篇 | HIGH |
| 9 | 参考文献格式 | ✅/❌ | ... | MEDIUM |
| 10 | 页眉奇偶页 | ✅/❌ | ... | LOW |
| 11 | 页码两套 | ✅/❌ | ... | LOW |
| 12 | 页面边距 25mm | ✅/❌ | ... | MEDIUM |
| 13 | 字号字体 | ✅/❌ | ... | MEDIUM |
| 14 | 无开发细节 | ✅/❌ | ... | HIGH |
| 15 | 外文翻译 | ⏸ | 作为 known issue | HIGH |

## Priority Action Items

**HIGH (Round 1 必须开始处理)**:
- ...

**MEDIUM (Round 2-3 处理)**:
- ...

**LOW (Round 4+ 或保留现状)**:
- ...

## Known Limitations

- 外文翻译独立材料，不在 skill 自动化范围内，需手动准备
```

---

## 退出条件

- Phase 0 完成后 → 进入 Phase 1
- 如果 Round 0 基线扫描发现 HIGH 级别不达标 → 生成 known_issues 后仍继续
- 如果 housekeeping 发现无法恢复的损坏状态 → 报告 + 退出，等待用户介入
