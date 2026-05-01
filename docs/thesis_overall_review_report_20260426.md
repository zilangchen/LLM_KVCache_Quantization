# 论文总体审批评审报告

生成时间：2026-05-01 13:36
报告范围：`thesis/chapters/*.tex`、`thesis/tables/*.{tex,md}`、论文编译产物 `thesis/main.pdf`
本轮任务：完善 P0 阻塞项，并通过多轮 Agent 复审确认 P0 清零。

## 0. 最终审批结论

**P0 审批结论：通过。**

本轮已经完成 P0 级别的三条主线修订：

1. **去工程化与内部命名清理**：正文、附录和 standalone tables 中不再暴露开发阶段命名、配置字段、内部实验代号或代码后端键名。
2. **PPL 与统计口径修正**：PPL 已明确为固定输入序列上的 likelihood 累计，不绑定贪心解码，不作为 `n=5` 统计重复，不进入 sign-flip / BH-FDR / p/q 显著性结论。
3. **论文级表达与正向口吻修正**：清理“赢家、输赢、回救、Rescue、胜出、击败、压倒、story、case/node”等竞赛化、复盘化或内部写作口吻。

因此，论文当前已经满足本轮定义的 P0 发表前门槛：**不泄露内部开发过程、不把 PPL 统计口径写错、不以负向或工程复盘口吻承载主结论。**

需要说明：P0 通过不等于全文已经无需 polish。后续仍建议进入 P1/P2：压缩冗余、统一术语密度、检查所有图表版式与 cross-reference 读感。

## 1. 多 Agent 复审结论

本轮采用多轮 Agent 复审，每轮只读审查，发现 P0 后立即修订，再重新扫描、编译和复审。

| 审查维度 | 初始状态 | 主要阻塞 | 最终状态 |
|---|---:|---|---:|
| 内部泄露与论文属性 | FAIL | `seq_len/gen_len`、`eng066`、`phase1`、旧 label 与 standalone table 阶段命名 | PASS |
| PPL 与统计口径 | FAIL | PPL 被总述句误带入贪心解码；PPL 与 `n=5`、BH-FDR/sign-flip 的表头距离过近 | PASS |
| 文本质量与发表口吻 | FAIL | “赢家/输赢/回救/Rescue/击败/压倒/最强/case/node”等读者可见表达 | PASS |

最终复审记录：

- 内部命名 P0-only 复审：PASS。
- 写作口吻 P0-only 复审：PASS。
- PPL 统计 P0-only 复审：PASS。

## 2. 本轮具体改动

### 2.1 摘要

修改文件：

- `thesis/chapters/abstract_zh.tex`
- `thesis/chapters/abstract_en.tex`

主要改动：

- 将“回救区间”改为“早层保护主导的适用区间”。
- 将英文摘要中的 `positive case`、`recovery`、`winner` 类口径改成 `evidence`、`accuracy preservation`、`single cross-task optimum` 等论文级表达。
- 保留 AutoK、RoleAlign、跨模型 regime map 的贡献，但不使用竞赛化胜负叙述。

新口径：

> 摘要只表达“结构证据与适用区间”，不表达“全局赢家”或“补救式恢复故事”。

### 2.2 第三章方法口径

修改文件：

- `thesis/chapters/ch3_method.tex`
- `thesis/tables/table_ch3_runtime_paths.tex`

主要改动：

- 将 AutoK 阈值从 `cov80/cov85/cov90` 这类内部命名，统一改为 80% / 85% / 90% 覆盖率阈值。
- 将运行路径描述改为论文级“参考路径 / Triton 融合路径 / 后端组合”，避免暴露内部后端键名。

新口径：

> AutoK 是基于行为敏感度画像覆盖率的预算建议器；阈值按覆盖率解释，不按内部配置代号解释。

### 2.3 第四章实验章

修改文件：

- `thesis/chapters/ch4_experiments.tex`

主要改动：

- PPL：明确为固定输入序列、固定 tokenization、固定窗口与固定 loss mask 下的 deterministic likelihood；seed 只做实现路径一致性核验。
- 统计：任务级分数和 TPOT 进入 Bootstrap / sign-flip / BH-FDR；PPL 只读效应量，不读 p/q 显著性。
- 内部命名：清理 `seq=`, `gen=`, `seq_len`, `gen_len`, `kv_mode`, `triton_ra`, `torch_ref`, `uniform_int4_k4v4` 等工程字段。
- 表达口吻：将“普适赢家”“KL 赢了多少”“主表输赢”“大幅击败 heuristic”“回救区间”“Rescue Δ”等改为“单一普适最优策略”“KL 与 MSE 的差异幅度”“主表相对表现”“显著优于/质量提升”“早层保护有效区间”“Quality Δ”。
- 标签：将 `ch4-case-*`、`tab:ch4-case-*` 改为 `profile` 语义，避免源文件里继续保留复盘式 `case` 命名。

新口径：

> 第四章不再讲“谁赢谁输”，而是讲“哪些结构证据成立、适用到哪里、在哪些条件下出现相对优势或策略簇”。

### 2.4 附录

修改文件：

- `thesis/chapters/appendix.tex`

主要改动：

- 将总述中的“所有实验采用固定随机种子与贪心解码”拆开：生成式质量评测与吞吐评测使用固定种子；PPL 独立为固定输入序列 likelihood。
- 将 PPL 行从生成式质量 `n=5` 分组中拆出，PPL 显著性列使用 `N/A`。
- 将 `7.14` 与 `6.7097` 的差异解释为 full test split 与 paired diagnostic subset 的样本覆盖/聚合人口差异，而不是方法差异。
- 将 `eng066` label/ref 改为 `scale-precision` 论文语义命名。
- 将 `seq_len=8192`、`gen_len=128`、`gen_len=64` 等配置字段改为“序列长度”“生成长度”的自然语言表述。

新口径：

> 附录是复现材料索引与补充诊断，不是内部实验日志；PPL 是 deterministic likelihood 读数，不参与随机种子显著性流程。

### 2.5 Standalone Tables

修改/重命名文件：

- `thesis/tables/table_official_longbench_1p5b.tex`
- `thesis/tables/table_official_longbench_7b.tex`
- `thesis/tables/table_cross_model_consistency.tex`
- `thesis/tables/table_s3_rolealign_vs_kivi.tex`
- `thesis/tables/table_t1_int8_canonical.{tex,md}`
- `thesis/tables/table_t2_int4_kivi.{tex,md}`
- `thesis/tables/table_t3_cross_model_main.{tex,md}`
- `thesis/tables/table_t4_mistral_autok.{tex,md}`
- `thesis/tables/table_t5_3b_early_layer.{tex,md}`
- `thesis/tables/table_t6_14b_toptier.{tex,md}`

主要改动：

- `phase1_*` 文件改名为论文级 `table_*` 文件，并同步 label。
- `INT8-ours` 改为 `INT8-Canonical`。
- `Winner` 改为 `Highest reading`。
- `Rescue` 改为 `Early-Layer Protection Effect`。
- K/V 校准表统一为 RoleAlign 的离线 K/V 分路径校准：K-path 使用 attention-distribution KL 代理，V-path 使用 output-perturbation 代理；KIVI-style 表述为运行时统计更新。

新口径：

> 表格只承载论文概念和结果读数，不保留阶段名、开发名、脚本名或内部实验键。

## 3. 全局新口径

本轮之后，全文应统一使用以下口径：

1. **RoleAlign**：行为引导的 KV-cache 量化框架实例，不是工程配置名。
2. **INT8-Canonical**：基础保真验证路径，用于确认行为引导校准不破坏基础推理语义。
3. **INT4-RoleAlign**：角色感知低比特实例；其贡献是格式、离线校准与后续分配接口的组织化，而不是无条件击败 KIVI-style。
4. **KIVI-style**：运行时统计更新的对照路径，使用中性表述。
5. **PPL**：固定输入序列 likelihood 累计；seed 只做一致性核验；不读 p/q 显著性。
6. **AutoK**：profile-guided allocator，描述适用区间与覆盖率预算，不宣称全局最优。
7. **Heuristic baseline**：强基线，是适用区间图谱的一部分，不作为负向论证对象。
8. **Deployment**：参考路径、Triton 融合路径、后端组合；不暴露内部后端键名。

## 4. 分章节 P0 状态

| 部分 | P0 状态 | 说明 |
|---|---:|---|
| 摘要 | PASS | 清理补救/赢家叙事，改为证据与适用区间。 |
| 第一章 | PASS | 本轮未发现 P0 阻塞；现有改动保持论文级目标表述。 |
| 第三章 | PASS | AutoK 与运行路径命名去工程化。 |
| 第四章 | PASS | PPL、口吻、内部字段、部署条件和 cross-model 叙事均已收口。 |
| 第五章 | PASS | “普适赢家/胜负裁决/结构足迹”等已改为学术口径。 |
| 附录 | PASS | PPL 统计、scale 诊断、部署配置字段和 label 均已修正。 |
| Tables | PASS | 阶段命名、Winner/Rescue、INT8-ours、K/V 校准旧口径已清理。 |

## 5. 验证结果

已执行验证：

```bash
rg -n "<内部命名与工程字段集合>" thesis/chapters thesis/tables
rg -n "<竞赛化/复盘口吻集合>" thesis/chapters thesis/tables
rg -n "<PPL 统计误绑定集合>" thesis/chapters thesis/tables
git diff --check -- thesis/chapters thesis/tables
cd thesis && latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

实际结果：

- 内部命名扫描：PASS，0 命中。
- 写作口吻扫描：PASS，0 命中。
- PPL 统计误绑定扫描：PASS，0 命中。
- `git diff --check`：PASS。
- `latexmk`：PASS，`main.pdf` 成功生成，106 页；仅有既有 Underfull warnings，无 LaTeX error。
- 多 Agent 最终复审：三项 P0 均 PASS。

## 6. 剩余风险与下一步

P0 已清零，但仍建议后续做 P1/P2：

- P1：压缩第四章和第五章中过多的边界说明，减少“不是 X，而是 Y”的密度。
- P1：继续统一 `behavior-guided`、`profile`、`regime map` 在中英文段落中的译名。
- P2：检查所有图表 caption 的长度与版式，减少 Underfull hbox/vbox。
- P2：全文通读一次，重点检查“贡献句”和“边界句”的比例。

当前结论：**允许进入下一阶段论文级 polish；P0 不再阻塞。**
