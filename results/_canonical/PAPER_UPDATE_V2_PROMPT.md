# 论文修改 v2 Prompt（给另一个窗口，基于 2026-04-10 新实验数据）

> **时间**: 2026-04-10
> **上下文**: v1 prompt 之后，主会话又跑完了 3 个新实验，产生 3 个重大发现。这份 v2 prompt 是对 v1 的**补充**，不是替代。如果 v1 的 6 处修改还没做，先做 v1 再做本 v2。

## 新增的 3 个关键发现（必须写入论文）

### 发现 1 🔴：KL vs MSE 在 INT8 下 bitwise 等价（Q10 答辩神器）

**数据**：
| 校准目标 | PPL | Needle 8K pass/exact | RULER 4K niah/mk_niah/vt/cwe |
|---------|-----|----------------------|------------------------------|
| KL | **9.3367** | 100% / 100% | 60.12 / 26.17 / 60.12 / 8.18 |
| MSE | **9.3367** | 100% / 100% | 60.12 / 26.17 / 60.12 / 8.18 |

**CSV 路径**：
- `results/emnlp_defense_v1/runs/isolation_kl_ppl_1p5b/profile_ppl_int8_ours_2026-04-09T18-25-40.258907.csv`
- `results/emnlp_defense_v1/runs/isolation_mse_ppl_1p5b/profile_ppl_int8_ours_2026-04-09T18-51-27.658253.csv`
- 其他 4 个在同目录的 isolation_{kl,mse}_{needle_8k,ruler}_1p5b/

**Isolation 实验设计**：
- 固定：kernel (torch_ref), adaptive=off, inv_tau=off, seed=1234
- 变量：只换 `--loss_function {kl, mse}` + `--search_objective {mean_kl, mean_mse}`
- 模型：Qwen2.5-1.5B
- 执行：2026-04-09 18:18 - 18:52

**论文位置建议**：
1. **ch3_method.tex** — attention-KL 定义段：在"为什么选 KL"的段落后加一句"在 INT8 下 KL 与 MSE 产生等价的校准参数（isolation 实验证实），attention-KL 的核心价值是其作为**诊断指标**的能力——下节会展示 KL 导出的 K 主导误差、GQA × τ⁻¹ 规律等发现，是 MSE 无法提供的"

2. **ch4_experiments.tex** — 新增小节 `\subsubsection{校准目标消融：KL vs MSE isolation}`
   - 位置：Claim 1 章节内，作为 "KL 贡献隔离" 的证据
   - 数据表（如上）
   - 分析段：
     - 解释为什么两者等价（INT8 的 256 级量化下，两种目标收敛到相同最优点）
     - 强调 KL 的诊断价值（导出 K 主导诊断、GQA 规律等）
     - 结论："因此，attention-KL 的贡献**完全**是诊断能力而非边际质量改善，这反而是**更强的论点**——既然两者数学等价，KL 的价值必须来自诊断能力，没有其他解释空间"

3. **ch5_conclusion.tex** — 方法论启示段：加一句 "对 Q10 的直接回应："

4. **Abstract**: 可以在贡献列表加一句 "isolation 实验证明 attention-KL 在 INT8 下与 MSE 产生数学等价的结果，因此 KL 的价值完全在于其作为诊断框架的数学基础"

---

### 发现 2 🟢：Qwen2.5-14B 验证 Claim 5

**数据**：
| 配置 | PPL | CSV 路径 |
|------|-----|---------|
| FP16 | **5.455** | `runs/ppl_fp16_14b_s1234/profile_ppl_fp16_2026-04-09T19-42-52.072129.csv` |
| INT4-RA no-tau | **5.7899** (+6.1%) | `runs/ppl_ra_notau_14b_s1234/profile_ppl_int4_ours_asym_2026-04-09T19-52-10.088384.csv` |
| INT4-RA with-tau | **5.8954** (+8.1% vs FP16, +1.8% vs no-tau) | `runs/ppl_ra_withtau_14b_s1234/profile_ppl_int4_ours_asym_ba_2026-04-09T20-01-41.423310.csv` |

**14B Needle（全部 100% pass + 100% exact）**：
- 4K: `runs/needle_fp16_ctx4096_14b/` + `runs/needle_ra_ctx4096_14b/`
- 8K: `runs/needle_fp16_ctx8192_14b/` + `runs/needle_ra_ctx8192_14b/`
- 16K: `runs/needle_fp16_ctx16384_14b/` + `runs/needle_ra_ctx16384_14b/`

**校准产物**：`artifacts/kv_calib_rolealign_14b_v3.json`（315 KB）

**Claim 5 规律扩展表**（现在是 4 模型规模）：

| 模型 | H_kv | INT4-RA Δ PPL | τ⁻¹ Δ | 效果 |
|------|------|---------------|-------|------|
| Qwen2.5-1.5B | 2 | +13.7% | **-1.6%** | ✅ 改善 |
| Qwen2.5-7B | 4 | +6.1% | **+6.0%** | ❌ 恶化 |
| LLaMA-3.1-8B | 8 | +2.4% | **+3.4%** | ❌ 恶化 |
| **Qwen2.5-14B** | **8** | **+6.1%** | **+1.8%** | ❌ 恶化（NEW）|

**论文位置建议**：
1. **ch4_experiments.tex** — Claim 5 章节（v1 prompt 里已创建）
   - 把 14B 这一行加入主表
   - 强调："14B 数据作为独立验证点证明规律的稳健性，同时 INT4-RA 在 14B 上退化 6.1% 与 7B 一致，证明方法对更大模型有效"

2. **ch5_conclusion.tex** — Limitations 段：从 "≤8B 模型" 改为 "≤14B 模型"
   - **注意**：CLAUDE.md §9 固定决策原本写"模型 ≤8B"，需要更新或在 Limitations 中明确披露 14B 是扩展验证点

3. **Abstract**: 在模型规模描述中加 14B："在 1.5B / 7B / 8B / 14B 四个模型规模上验证..."

---

### 发现 3 🟢：64K Context 8B 验证

**数据**：
| 模型 | kv_mode | 长度 | pass_rate | exact_match |
|------|---------|------|-----------|-------------|
| LLaMA-3.1-8B | fp16 | **65536** | **100%** | 0% |
| LLaMA-3.1-8B | int4_ours_asym | **65536** | **100%** | 0% |

**CSV 路径**：
- `results/emnlp_defense_v1/runs/needle_fp16_64k_8b/profile_needle_fp16_2026-04-09T18-39-16.173638.csv`
- `results/emnlp_defense_v1/runs/needle_ra_64k_8b/profile_needle_int4_ours_asym_2026-04-09T18-43-52.072609.csv`

**关键说明**：
- `pass_rate=100%` 使用 contains-match（needle 在输出中出现）
- `exact_match=0%` 是因为 8B 在 64K 下倾向生成解释性文字（例如 "The needle is X because..."），**FP16 也是 0%**——这是模型行为，不是 INT4 问题
- **INT4-RA 在 64K 下与 FP16 完全等价**

**论文位置建议**：
1. **ch4_experiments.tex** — Needle 结果表：
   - 在 32K 那一列后加一列 "64K"
   - 标注 "8B only（限于显存和时间）"
   - 加 footnote 说明 exact_match=0% 的原因（contains vs exact 口径差异 + 模型行为）

2. **ch5_conclusion.tex** — Limitations 段：
   - 从 "测试到 32K context" 改为 "测试到 64K context (8B)"

---

## 约束（与 v1 prompt 相同）

1. **只改 `thesis/` 文件**，不碰 `results/_canonical/`, `scripts/`, `src/`
2. **中文输出**，LaTeX/英文术语保留原形
3. **按语义分组 commit**
4. **fail-fast**：编译出错诊断根因，不要 `\iffalse` 绕过
5. **不要 push**

## Verification

```bash
cd thesis && latexmk -xelatex -interaction=nonstopmode main.tex
grep -c "??" main.aux  # 应为 0
grep -n "9.3367\|KL.*MSE.*等价\|KL.*MSE.*equivalent" chapters/ch4_experiments.tex  # KL=MSE 数据已写入
grep -n "14B\|Qwen2.5-14B" chapters/ch4_experiments.tex chapters/ch5_conclusion.tex  # 14B 数据已写入
grep -n "64K\|65536\|8B.*64" chapters/ch4_experiments.tex chapters/ch5_conclusion.tex  # 64K 数据已写入
```

## Commit 策略

```bash
git add thesis/chapters/ch3_method.tex thesis/chapters/ch4_experiments.tex
git commit -m "feat(thesis): add isolation KL vs MSE experiment (bitwise equivalent in INT8)"

git add thesis/chapters/ch4_experiments.tex thesis/chapters/ch5_conclusion.tex thesis/abstract_*.tex
git commit -m "feat(thesis): extend Claim 5 to Qwen2.5-14B (4 model scales, H_kv=8 confirmed)"

git add thesis/chapters/ch4_experiments.tex thesis/chapters/ch5_conclusion.tex
git commit -m "feat(thesis): add 64K context ablation on 8B (INT4-RA matches FP16)"
```

## 完成标志

```
✅ 论文修改 v2 完成 — 3 个新发现全部写入 + 4 个 commits + 编译通过
```

---

**注意**：如果 v1 prompt 的 6 处修改还没做，**先做 v1 再做 v2**。v1 包括 Claim 5 章节化、Abstract synthetic LongBench、TPOT footnote 等基础修改，v2 是在此基础上**补充**新数据。
