# Entry Conflicts — 新旧数据入口冲突检测

> **用途**：检查论文是否在 cite / 路径引用 / 叙事层面误用了已降级的数据入口（`results/_canonical/`、`docs/experiment_data_index.md`、`emnlp_*/` 原目录）。
>
> **背景**：2026-04-17 所有权威数据冻结至 `results/final/final_data/`（25 历史目录合并为 4 个子目录：int8_mainline / int4_rolealign / kv_ablation / backend_comparison）。INDEX.md 声明为 "唯一权威入口"。旧入口 `results/_canonical/INDEX.md` 和 `docs/experiment_data_index.md` **已手动追加"已由 results/final/ 替代"的警告横幅**，但未删除。
>
> **更新日期**：2026-04-17

---

## A. 论文正文 cite / 路径引用扫描

### A.1 `\cite` 指向 `_canonical/`

```
Grep 结果：thesis/*.tex + thesis/chapters/*.tex 对 "_canonical" 的匹配
```

**结果**：**无匹配** ✓

论文 `\cite` 全部指向 `references.bib` 中的文献条目，未出现任何指向 `_canonical/` 的 `\cite{claim[1-5]_*}` 或类似形式。

### A.2 论文引用 `docs/experiment_data_index.md`

```
Grep 结果：thesis 目录对 "experiment_data_index" 的匹配
```

**结果**：**无匹配** ✓

论文正文（正式叙事）不引用此文档。

### A.3 论文引用 `_canonical` 字符串

```
Grep 结果：thesis 目录对 "_canonical" 的匹配
```

**结果**：**无匹配** ✓

### A.4 论文引用 `emnlp_defense_v1` / `emnlp_rolealign_v2` / `emnlp_p012_batch` / `emnlp_expansion_v1`

```
Grep 结果：thesis 目录对这 4 个原目录名的匹配
```

**结果**：**2 处匹配** ⚠

1. `thesis/chapters/ch4_experiments.tex:377` — `tab:kl-mse-bitwidth-comparison` 的 tablenotes：
   ```latex
   \texttt{results/emnlp\_defense\_v1/runs/isolation\_\{kl,mse\}\_\{ppl,needle\_8k,ruler\}\_1p5b/}
   ```
   该原目录已迁移到 `results/final/final_data/int8_mainline/runs/isolation_*/`。

2. `thesis/chapters/appendix.tex:736` — `tab:app-7b-kl-mse` 的 tablenotes：
   ```latex
   \code{results/emnlp\_p012\_batch/runs/ppl\_\{kl,mse,fp16\}\_7b\_s*/}
   ```
   该原目录已迁移到 `results/final/final_data/backend_comparison/runs/ppl_{kl,mse,fp16}_7b_s*/`。

已作为 **TR-0300 HIGH** 记录到 issues.md。

### A.5 论文引用 `results/emnlp_*` 广义

```
Grep 结果：thesis 目录对 "results/" 的所有匹配
```

**结果**：正好这 2 处（与 A.4 相同）。未发现其他路径引用。

### A.6 论文引用 `results/final/` 或 `final_data/`

**结果**：**无匹配**。论文正文完全不显式写路径到 `results/final/`——相反地，所有数据路径引用都是在 tablenotes 用 `emnlp_*` 原目录名（或完全不写路径）。

**建议**：若需在 tablenotes 保留路径，统一写 `results/final/final_data/{int8_mainline,int4_rolealign,kv_ablation,backend_comparison}/runs/...`；或干脆删除路径 tablenotes 改为 "完整数据见复现包 `results/final/final_scripts/reproduce/`"。

---

## B. "唯一入口" 声明冲突

### B.1 多文件声明自己是"主入口"

```
Grep: "唯一.*入口" OR "权威.*入口"
```

扫描结果：

| 文件 | 行号 | 声明 |
|------|------|------|
| `results/final/final_data/INDEX.md` | 1 | `# 论文数据索引（唯一权威入口）` |
| `results/final/README.md` | 1 | `# 论文最终数据（唯一权威入口）` |
| `results/_canonical/INDEX.md` | 1 | `# Results Canonical Index（已由 results/final/ 替代）` |
| `results/_canonical/INDEX.md` | 3 | `> **⚠️ 本文件为旧版索引，已于 2026-04-17 被 results/final/final_data/INDEX.md 替代。** > **请使用 results/final/ 作为唯一权威数据入口。**` |
| `docs/experiment_data_index.md` | 1 | `# 实验数据索引（已由 results/final/ 替代）` |
| `docs/experiment_data_index.md` | 3 | `> **⚠️ 本文件为旧版索引，已于 2026-04-17 被 results/final/final_data/INDEX.md 替代。** > **请使用 results/final/ 作为唯一权威数据入口。**` |
| `CLAUDE.md` (project-level MEMORY 引用) | — | MEMORY.md "文件导航" 节点：`🎯 实验数据查询入口: results/_canonical/INDEX.md — 所有实验数据的唯一入口` |

**发现 1**：`results/_canonical/INDEX.md:1,3` 和 `docs/experiment_data_index.md:1,3` 均已**添加降级警告横幅**，文字明确指向 `results/final/final_data/INDEX.md`。✓ 不是"静默保留的旧入口"。

**发现 2**：唯一仍声称 `_canonical` 是"唯一入口"的是 **MEMORY.md 文件导航节**（CLAUDE.md 持久 memory 层）。但该层在论文层不可见，只影响 agent/cross-session 导航——属于仓库治理层问题，不影响论文合规性。

### B.2 `results/final/final_data/INDEX.md` vs `results/final/README.md` 的重合/冗余

两个文件都声称"唯一权威入口"。核对内容：

- `results/final/README.md`（50 行）：项目级总览（目录结构 + 原目录映射 + 注意事项）。
- `results/final/final_data/INDEX.md`（73 行）：论文表 → CSV 具体映射表。

两者**功能互补、非冲突**。README 是 narrative 层，INDEX.md 是 dispatcher 层。建议 README.md 明确指向 INDEX.md："论文表 → 数据路径对照请见 `final_data/INDEX.md`"。目前 README 没有这句链接，但目录结构声明了 `INDEX.md` 的存在。可选清理项。

---

## C. `_canonical/` 内部现状分析

`results/_canonical/INDEX.md` 虽已加降级横幅但未删除，内部继续存在：

- `by_claim/claim[1-5]_*.md` 5 个 Claim 证据文件（仍指向 `emnlp_*/` 原目录路径）
- `by_experiment/*.md` 9 个实验类型索引
- `appendix_freshness.md` 历史目录活跃度分类

**现状**：论文本身不 cite 这些文件（A.3 已验证），但它们仍存在且内容未同步到 `results/final/final_data/`。

**风险**：
- Agent cross-session 导航（通过 MEMORY.md）仍可能被引导回 `_canonical/`（已在 B.1 发现）。
- 评委若翻阅仓库结构，可能疑惑"为什么有两个 INDEX 声称自己是权威"。
- `by_claim/claim[1-5]_*.md` 证据文件的数值若与 `final_data` 不一致，会造成冗余数据源。

**建议**：
1. **论文层（本次审查范围内）**：无行动必要（A.1-A.5 确认无 cite）。
2. **仓库治理层（后续会话）**：
   - 选项 A（推荐）：将 `_canonical/` 完整目录移到 `archive/_canonical_deprecated_20260417/`（保留历史可查，清空当前 `_canonical` 路径）。
   - 选项 B：保留 `_canonical/INDEX.md` 降级横幅，但删除 `by_claim/` / `by_experiment/` 子目录（减少数据源冗余）。
   - 选项 C：最低介入 — 更新 `CLAUDE.md` MEMORY.md 的文件导航行，从 "`_canonical/INDEX.md` — 所有实验数据的唯一入口" 改为 "`results/final/final_data/INDEX.md` — 所有实验数据的唯一入口"。

---

## D. 清理建议（按优先级）

### D.1 论文层（对本次审查关键）

| 优先级 | 建议 | 文件 | 位置 |
|--------|------|------|------|
| **P3b HIGH** (TR-0300) | 将 `results/emnlp\_defense\_v1/runs/isolation\_...` 改为 `results/final/final_data/int8\_mainline/runs/isolation\_...` | ch4_experiments.tex | L377 |
| **P3b HIGH** (TR-0300) | 将 `results/emnlp\_p012\_batch/runs/ppl\_...` 改为 `results/final/final_data/backend\_comparison/runs/ppl\_...` | appendix.tex | L736 |
| P3c MED | 添加一个 appendix 小节（或 ch4 开头脚注）声明 "本文所有数据路径相对 `results/final/final_data/`" | appendix.tex 新增节 | — |

### D.2 仓库治理层（建议异步推进）

| 优先级 | 建议 | 文件 |
|--------|------|------|
| MED | 更新 MEMORY.md 文件导航：`_canonical/INDEX.md` → `results/final/final_data/INDEX.md` | `~/.claude/projects/.../memory/MEMORY.md` |
| LOW | 归档 `results/_canonical/` 到 `results/archive/` 下；保留 README 一句话指向 `final/` | — |
| LOW | 归档 `docs/experiment_data_index.md`（已降级）到 `docs/archive/`，或保留作历史参照 | — |
| LOW | 在 `results/final/README.md` 添加一句 "论文表 → 数据路径对照请见 `final_data/INDEX.md`" | `results/final/README.md` |

---

## E. 验证命令（P3 修复后使用）

```bash
# 验证 thesis 已无降级入口引用
rg -n "_canonical|emnlp_defense_v1|emnlp_rolealign_v2|emnlp_p012_batch|emnlp_expansion_v1|experiment_data_index" thesis/

# 预期：只有 references.bib 如果未改 cite key；正文 tablenotes 应全部切换到 results/final/final_data/
```

```bash
# 验证 results/final/ 仍为唯一声称入口
rg -n "唯一.*入口|权威.*入口" results/ docs/

# 预期：final_data/INDEX.md L1 + results/final/README.md L1；_canonical 和 docs/experiment_data_index 应只在降级横幅中出现
```

