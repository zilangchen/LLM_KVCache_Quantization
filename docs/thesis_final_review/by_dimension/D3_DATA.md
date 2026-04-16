# D3 DATA — 数据一致性 + 论证链 + 新旧数据入口冲突检测

> **Evidence 规则**：所有新增 issue 的 Evidence **必须**指向 `results/final/final_data/*` 或 `thesis/chapters/*`；**禁止**指向 `results/_canonical/*`（已降级为审计层）。
>
> **Status**: 2026-04-17 审查完成；新增 issues TR-0300 起。
>
> **Baseline**: thesis-final-review-baseline (main @ e379645)；数据冻结日期 2026-04-17。

---

## A. L1 宏观（论证主线 + 章间数据连贯 + 新旧入口引用）

### A.1 5-Claim / 3-Finding 叙事结构

经 ch1 / ch4 / ch5 三章交叉比对：

- **C1 校准目标有效性**：bit-width × 规模双重依赖 ← 证据在 `tab:kl-mse-bitwidth-comparison`（ch4:360）+ `tab:app-7b-kl-mse`（附录:720）。叙事贯通性 **OK**。
- **C2 Key 主导退化 + $H_{kv}$ 结构依赖**：证据链完整 — 对称 INT4 失效（`tab:main-results`）→ K/V 消融（`tab:kv-ablation-ruler/longbench/ppl/14b`）→ 诊断导出 KIVI 格式 → RoleAlign 实例化（`tab:rolealign-results`）。**OK**。
- **C3 RoleAlign 跨 4 模型 Needle 100% + KV 压缩 73%**：`tab:rolealign-results` + 14B Needle+RULER 外部效度。**OK**。
- **C4 PPL/TPOT 能力边界**：`tab:int4-tpot-cross-model` + `tab:phase-boundary`。**OK**。
- **C5 inv_tau × GQA 双向效应**：`tab:invtau-ablation` + GQA 噪声稀释机制论证。**OK**。

论证主线本身闭环，各章 Finding 回扣 RQ 合理。

### A.2 章间数字对齐（交叉扫描）

| 数字 | abstract_en/zh | ch1 | ch4 | ch5 | 权威值（final_data） | 结论 |
|------|---------------|-----|-----|-----|---------------------|------|
| 1.5B PPL deg | 13.7% | 13.7% | 13.7% | 13.7% | **13.68%** (10.5824/9.3088-1) | **一致** ✓ |
| 7B PPL deg | 6.0% (en+zh) | **6.0%** | **6.1%**（4 处）/ 6.0%（2 处，L1941/L1965）| **6.0%** | **6.13%** (7.5787/7.1407-1) | **不一致 → TR-0002** |
| 8B PPL deg | 2.4% | 2.4% | 2.4% | 2.4% | **2.43%** (6.8963/6.733-1) | **一致** ✓ |
| 14B PPL deg | (缺省） | (缺省） | 7.6% | (缺省） | **7.58%** (5.0399/4.685-1) | **一致** ✓ |
| Needle 100% 4 模型 | ✓ | ✓ | ✓ | ✓ | 14B 32K = 100% ✓ | **一致** ✓ |
| KV 压缩 73% | ✓ | ✓ | 73.4% (`tab:kv-memory-sweep`) | 73% | 30.73/115.47 = 73.39% | **一致** ✓ |
| 32K triton_ra 14B 加速 | 40% | 40% | 40% | 40% | (190.23-113.16)/190.23=40.5% | **一致** ✓ |
| RULER 14B 4K–16K | 96.6-98.5% | 96.6-98.5% | 96.6-98.5% | 96.6-98.5% | 4K=98.5% / 8K=98.2% / 16K=96.6%（3 seed 均值） | **一致** ✓ |

**发现**：除 TR-0002（7B PPL 6.0/6.1 矛盾）已由主会话确认外，ch4_experiments.tex 内部自身在 L1941/L1965（Findings / 结论概要段）与 L1278/L1353/L1700 也存在 6.0 vs 6.1 矛盾。

### A.3 论文对已降级入口的 cite / 路径引用

Grep 结果：

| 规则 | 结果 |
|------|------|
| 论文 `\cite` 指向 `_canonical/*` | **无** ✓ |
| 论文引用 `docs/experiment_data_index.md` | **无** ✓ |
| 论文引用 `_canonical` 字符串 | **无** ✓ |
| 论文正文引用 `results/emnlp_*` 历史原目录 | **2 处** → **TR-0300 HIGH** |

具体位置：
- `thesis/chapters/ch4_experiments.tex:377`：`\texttt{results/emnlp\_defense\_v1/runs/isolation\_\{kl,mse\}\_\{ppl,needle\_8k,ruler\}\_1p5b/}` — `tab:kl-mse-bitwidth-comparison` 的 tablenotes。原目录 `emnlp_defense_v1/` 已于 2026-04-17 重命名并迁入 `results/final/final_data/int8_mainline/`。
- `thesis/chapters/appendix.tex:736`：`\code{results/emnlp\_p012\_batch/runs/ppl\_\{kl,mse,fp16\}\_7b\_s*/}` — `tab:app-7b-kl-mse` 的 tablenotes。原目录 `emnlp_p012_batch/` 已迁入 `results/final/final_data/backend_comparison/`。

---

## B. L2 段落（表内自洽 + 图表 ref/描述方向 + 统计语言一致性）

### B.1 `\begin{table}` 内部自洽抽样

| 表 | 行列合计 | 单位 | baseline 对照 | 问题 |
|----|---------|------|--------------|------|
| `tab:main-results` (ch4:411) | ✓ | ✓ | fp16 行齐全 | **LongBench 4.82 说明有坑**：tablenotes 标"`longbench_contains_macro` 字段宏平均（×100）"，但附录 `tab:app-longbench-full` FP16 contains_match = **99.9\%**（不是 4.82）。实际 4.82 = `longbench_score` × 100（0.0482 → 4.82）。**tablenotes 说明错误 → TR-0301 MED** |
| `tab:kl-mse-bitwidth-comparison` (ch4:360) | ✓ | ✓ | KL vs MSE 对照完整 | 注释已引用 `emnlp_defense_v1/`（见 TR-0300） |
| `tab:rolealign-results` (ch4:1322) | ✓ | ✓ | FP16/KIVI/ours 三行齐全 | **PPL 列混用**：1.5B/7B/8B PPL 行用 `int4_rolealign/ppl_ours_asym_*` 数据（WikiText-2 全量 301827 tokens），14B PPL 用 `backend_comparison/ppl_ra_14b_*`（32767 tokens 子集），**tokens_evaluated 不同但同表对比未标注** → TR-0302 HIGH |
| `tab:14b-kv-ablation` (ch4:1127) | ✓ | ✓ | FP16 行 4.685 + Full INT4 5.040 | 14B FP16 PPL = 4.685（`ppl_fp16_14b_s1234` tokens=32767）与 ch4_experiments.tex 文本"14B 上保持 Key 为 FP16 可恢复 93% 的 PPL 退化"一致。但 `int8_mainline/ppl_fp16_14b_s1234` FP16=5.455（tokens=301827）→ 两份 14B FP16 基线（4.685 vs 5.455）→ TR-0303 HIGH |
| `tab:kivi-int4-threeway` (ch4:1643) | — | — | 三行 | `int4_kivi_aligned` 整行 PPL/LB 为 `---`，脚注 `\dagger` 承认未完整评测。**诚实披露，OK** |
| `tab:phase1-tpot` (ch4:1778) | ✓ | ms | FP16 + 4 INT4 backends | 数据匹配 `tpot_*_{1p5b,7b,8b}` 权威 CSV（抽样验证通过） |
| `tab:longseq-tpot-14b` (ch4:1809) | ✓ | ms | 4 backends | 32K triton_ra=113.16 vs CSV mean=113.15 ✓ |
| `tab:temp-ablation` (ch4:658) | ✓ | % | 4 配置 | mainline 与 static_v2_adaptive 两行 Needle 均为 100.0 ± 0.0 — **冗余但无错误** |
| `tab:cross-model` (ch4:768) | ✓ | — | 6 列均齐 | 7B/8B TPOT=60.52/91.77（baseline），50.07/57.23（ours），匹配 `tab:app-sig-tpot` |

### B.2 `\ref{fig:,tab:}` 前后描述方向一致性

抽查 20+ 表/图引用：

| 位置 | 引用 | 描述方向 | 结论 |
|------|------|---------|------|
| ch4:1091 | tab:kv-ablation-ruler + longbench | "揭示了一个清晰而一致的模式" | 数据确实一致 ✓ |
| ch4:1098-1108 | (承接上述) | K@INT8/V@INT4 微退化，K@INT4 崩溃 | 匹配 1.5B/7B K4V8 RULER=0.00（数据） ✓ |
| ch4:1115 | (承接) | "LLaMA-3.1-8B（$H_{kv}=8$）上 K4V8 RULER 仍为 31.12%" | 3-seed 均值 =(31.64+30.08+31.64)/3=31.12 ✓ |
| ch4:1146 | tab:14b-kv-ablation | "K16V4 可恢复 93% 的 PPL 退化" | (5.040-4.709)/(5.040-4.685)=0.9324 ≈93% ✓ |
| ch4:1148 | (同) | "K4V16 仅恢复 64%" | (5.040-4.813)/(5.040-4.685)=0.6394 ≈64% ✓ |
| ch4:1384 | tab:rolealign-results | "98.5%（4K）、98.2%（8K）、96.6%（16K）" | 3-seed 均值验证（上方数据）✓ |
| ch4:1385 | (同) | "1.5B FP16 RULER baselines（60.3%、58.5%、56.3%、55.2% at 4K–32K）" | 需要验证，未在此次抽样内，**TR-0304 MED**（未抽样） |
| ch4:1386 | (同) | "INT4-RoleAlign FlashInfer 后端（60.2%、58.0%、56.8%、55.6%）" | 同上 |
| ch4:1815 | tab:longseq-tpot-14b | "32K 时 triton_ra 比 torch_ref 快 40%" | (190.23-113.16)/190.23=40.5% ✓ |

### B.3 "显著/提升/优于" 的统计语言

抽样 10 处：

| 位置 | 语言 | 是否附统计 |
|------|------|------------|
| ch4:481 | "加速 8.3%（q=0.016）" | ✓ q 值附上 |
| ch4:795 | "Qwen2.5-7B … TPOT 降低 17.3%（q=0.016）" | ✓ q 值 |
| ch4:808 | "LLaMA-3.1-8B … TPOT 加速达到 37.6%（三个模型中最大，q=0.016）" | ✓ q 值 |
| ch4:802 | "INT8-ours … PPL 退化不足 0.3%" | **无 p/q 值**（但 PPL 为确定量，L240-260 已说明免除，**OK**） |
| ch4:883 | "符号翻转检验 p=0.091（q=0.144），差异不显著" | ✓ p + q |
| ch4:498 | "PPL 退化幅度在 −0.09% 至 −0.26% 范围内" + 显式脚注 "deterministic effect size on greedy-decoded PPL" | ✓ 明确标注确定性 |
| ch4:1414 | "从 per-group 对称切换到 per-channel/per-token 非对称后，Needle 通过率均为 100%（3 seeds 一致）" | Needle 是显式比较；**无统计检验**，但后文解释 Needle 满分无从做假设检验，**OK** |
| ch4:1679 | "三方对比表明 BA-guided percentile 校准提供了一个与本文诊断一致的参数化路径，并在当前设置下带来小幅 LongBench 改善" | **无统计检验**，但 4.83 vs 4.92 的绝对差很小 → **TR-0305 MED**（改善性语言但无统计支撑） |
| ch4:1882 | "INT4 量化在所有模型上均实现约 73% 的 KV Cache 压缩率" | **事实性声明**，由位宽决定 ✓ |

---

## C. L3 句子（逐数字对账）

### C.1 PPL 退化核心数字对账

权威计算：`PPL_quant / PPL_fp16 - 1`（同协议，同 tokens_evaluated）。

| 模型 | FP16 PPL（权威来源） | INT4-RA PPL（权威来源） | 计算退化率 | 论文值 | 对齐 |
|------|---------------------|------------------------|-----------|--------|------|
| 1.5B | 9.3088（`int8_mainline/ppl_fp16_baseline_1p5b`，301827 tok）| 10.5824（`int4_rolealign/ppl_ours_asym_1p5b_s1234`，301827 tok）| **13.68%** | 13.7% | ✓ |
| 7B | 7.1407（`int8_mainline/ppl_fp16_n10_7b_s1239`，301827 tok）| 7.5787（`int4_rolealign/ppl_ours_asym_7b_s1234`，301827 tok）| **6.13%** | 6.1% (ch4) / 6.0% (摘要+ch1+ch5) | ⚠ 摘要/ch1/ch5 取 6.0 偏低，应统一为 6.1 |
| 8B | 6.733（`int8_mainline/ppl_fp16_n10_8b_s1239`，291825 tok）| 6.8963（`int4_rolealign/ppl_ours_asym_8b_s1234`，291825 tok）| **2.43%** | 2.4% | ✓ |
| 14B | 4.685（`backend_comparison/ppl_fp16_14b_s1234`，32767 tok）| 5.0399（`backend_comparison/ppl_ra_14b_s1234`，32767 tok）| **7.58%** | 7.6% | ✓ |

### C.2 百分比/绝对值混用审查

- `tab:main-results` LongBench 列：标题"(%)"但数值 4.82 = longbench_score × 100。**看起来是百分比但实际是分数×100**，tablenotes 已说明"LongBench score …（×100 显示；合成数据源）"，但不同表（tab:app-longbench-full）直接写 `0.0482` 而非 4.82 → 单位不统一 → TR-0306 MED
- `tab:kv-ablation-longbench` 标题"（×100，32K 上下文，3 seeds）" ✓ 明确
- `tab:kv-ablation-ruler` 标题"通过率（%，32K 上下文）" ✓

### C.3 小数位一致性

- `tab:main-results`: PPL 两位小数、CI 两位小数 ✓
- `tab:rolealign-results`: PPL 14B 用 `5.04`（两位）但 1.5B/7B/8B 用 `10.58`/`7.58`/`6.90`（两位）✓
- `tab:14b-kv-ablation`: PPL **三位小数**（4.685 / 4.709 / 4.764 / 4.813 / 4.815 / 5.040） vs `tab:rolealign-results` 14B 用两位小数（5.04）→ TR-0307 LOW
- `tab:phase1-tpot`: TPOT 两位小数 ms ✓
- `tab:int4-tpot-cross-model`: TPOT 两位小数 ✓

### C.4 种子数披露

- `tab:rolealign-results` caption 明确："1.5B/7B/8B 为 3 seeds，14B 为 1 seed" ✓
- `tab:kv-ablation-ppl` caption 明确："单 seed（1234）报告，理由见 ... PPL 确定性说明" ✓
- `tab:kv-ablation-ruler/longbench` caption "3 seeds" ✓
- `tab:main-results` caption 注 "5 seeds" ✓
- **14B 样本差异**：14B PPL/Needle 用 `seq_len=1024, chunk_size=128, tokens_evaluated=32767`，而 1.5B/7B/8B PPL 用 `tokens_evaluated=301827` 或 `291825`（完整 wikitext-2）→ 14B 实际是子集而非全量。ch4:1327-1329 声明"WikiText-2 测试集全量（~302K tokens，chunk_size=128）"，但数据显示 14B 只有 32K tokens → TR-0308 HIGH（披露不足）

---

## D. Top-20 Issue 摘要（详见 issues.md TR-0300+）

> 所有 Evidence 严格指向 `final_data/*` 或 `thesis/chapters/*`，不引 `_canonical/`。

| ID | Severity | 描述 | File:Line | Evidence |
|----|----------|------|-----------|----------|
| TR-0300 | HIGH | 论文仍引用已迁移的 `emnlp_defense_v1/` 和 `emnlp_p012_batch/` 原目录路径 | ch4_experiments.tex:377 + appendix.tex:736 | final/final_data/int8_mainline/runs/isolation_*/ + final/final_data/backend_comparison/runs/ppl_*_7b_*/ |
| TR-0301 | MED | `tab:main-results` tablenotes "longbench_contains_macro × 100 宏平均" 与附录 tab:app-longbench-full `contains_match_rate=99.9%` 矛盾，实际 4.82 = longbench_score × 100 | ch4_experiments.tex:455-460 | final/final_data/int8_mainline/runs/longbench_fp16_32k_1p5b/profile_longbench_*.csv (contains=45.08 / score=3.9976) vs 5-seed avg score=0.0482 (appendix) |
| TR-0302 | HIGH | `tab:rolealign-results` 14B PPL (5.04) 与 1.5B/7B/8B PPL (10.58/7.58/6.90) 使用不同 tokens_evaluated (32767 vs 301827)，同表横向对比但未标注 | ch4_experiments.tex:1322-1363 | final/final_data/backend_comparison/runs/ppl_ra_14b_s1234/profile_ppl_*.csv (tokens=32767) vs int4_rolealign/runs/ppl_ours_asym_*_s1234/*.csv (tokens=301827) |
| TR-0303 | HIGH | 14B FP16 PPL 存在两个权威值：4.685（`backend_comparison/ppl_fp16_14b_s1234`，tokens=32767）vs 5.455（`int8_mainline/ppl_fp16_14b_s1234`，tokens=301827）；论文用 4.685，但 INDEX.md L73 未列为"关键注意事项" | ch4_experiments.tex:1137,1361 + appendix.tex 未标注 | final/final_data/backend_comparison/runs/ppl_fp16_14b_s1234/profile_ppl_*.csv vs int8_mainline/runs/ppl_fp16_14b_s1234/profile_ppl_*.csv |
| TR-0304 | MED | 1.5B FP16 RULER baselines（60.3/58.5/56.3/55.2%）和 RoleAlign FI 后端（60.2/58.0/56.8/55.6%）未找到明确 CSV 数据源（非本次抽样范围） | ch4_experiments.tex:1384-1386 | final/final_data/backend_comparison/runs/ruler_fp16_1p5b_*/ + ruler_fi_1p5b_*/ 需抽样验证 |
| TR-0305 | MED | ch4:1679 "BA-guided percentile 校准…带来小幅 LongBench 改善"（4.83→4.92）未附 bootstrap CI 或 p 值 | ch4_experiments.tex:1679-1684 | final/final_data/int8_mainline/runs/longbench_*/ |
| TR-0306 | MED | LongBench 列单位不统一：tab:main-results 用 "4.82"（score×100）但附录 tab:app-longbench-full 用 "0.0482"（原始 longbench_score）；跨表读者无法直接对齐 | ch4_experiments.tex:413-470 vs appendix.tex:101-145 | final/final_data/int8_mainline/runs/longbench_fp16_32k_1p5b/profile_longbench_*.csv (longbench_score 列) |
| TR-0307 | LOW | 14B PPL 小数位不一致：tab:14b-kv-ablation 用三位（4.685）但 tab:rolealign-results 用两位（5.04）；同模型同协议 | ch4_experiments.tex:1127-1144 vs 1322-1363 | 同上数据 |
| TR-0308 | HIGH | `tab:rolealign-results` caption L1327 声明 "WikiText-2 测试集全量（~302K tokens, chunk_size=128）"，但 14B 行实际 tokens_evaluated=32767（30K，10× 差距）；未披露 14B 使用子集 | ch4_experiments.tex:1324-1332 | final/final_data/backend_comparison/runs/ppl_ra_14b_s1234/profile_ppl_*.csv (seq_len=1024, tokens=32767) |
| TR-0309 | MED | ch4:1941 + ch4:1965（Findings/结论概要）用 "7B: 6.0%" 与 ch4 正文 L1278/L1353/L1700（tab:rolealign-results 表行 + 边界声明）用 "7B: 6.1%" 矛盾（同章内部）| ch4_experiments.tex:1941 + 1965 vs 1278 + 1353 + 1700 | final/final_data/int4_rolealign/runs/ppl_ours_asym_7b_*/profile_ppl_*.csv (7.5787/7.1407-1=6.13%) |
| TR-0310 | MED | tab:main-results KIVI-style Needle "99.0±2.3" 与 int8_mainline/needle_kivi_*_postfix/ 数据显示 4K/8K/16K/32K 全部 100% 矛盾 | ch4_experiments.tex:447-448 | final/final_data/int8_mainline/runs/needle_kivi_4k_postfix/ + needle_kivi_ctx{8192,16384}_1p5b/ + needle_kivi_32k_postfix/（全部 100%）vs 早期 `needle_kivi_int4_32k_1p5b/`（3 个均 0%，疑似已废弃） |
| TR-0311 | MED | 7B/8B KIVI INT4 PPL（7.53 / 6.90 in tab:rolealign-results）在 `final_data` 中**未找到对应 CSV**（只有 1.5B KIVI INT4 PPL=10.4294 in `ppl_kivi_int4_1p5b_s1234`）| ch4_experiments.tex:1352,1357 | final/final_data/ 全局 find 仅 1.5B KIVI INT4 runs |
| TR-0312 | MED | tab:main-results PPL (1.5B INT8-ours=8.95) 与 tab:invtau-ablation / `final_data` 的 INT8 PPL=9.34 (同模型同模式) 不一致；附录 L576-578 承认"使用不同的 max_length/stride 配置"，但主表未在 caption 披露 | ch4_experiments.tex:434 + 507 vs final_data 9.3399 | final/final_data/int8_mainline/runs/ppl_int8_n10_1p5b_s1239/profile_ppl_*.csv (9.3399) + ppl_int8_v3_reverify_1p5b_s1234 (9.3399) |
| TR-0313 | LOW | ch4:1946 (Finding 3) "H_kv=8 在 32K 下延迟减少约 40%" — 单点数值应配 tab:longseq-tpot-14b $\Delta$(%) 列 -40% 的明确 ref | ch4_experiments.tex:1946 | final/final_data/backend_comparison/runs/longseq_{triton_ra,torchref}_14b_s32704/ |
| TR-0314 | MED | tab:chunksize-results INT4-RoleAlign cs=1 用 ">10,000"（附录 L563），KIVI 用具体数 10,332；**未统一披露粒度**（ours 模糊、KIVI 精确）| appendix.tex:560-584 | final/final_data/int8_mainline/runs/ppl_kivi_int4_cs1_1p5b/profile_ppl_*.csv (10332.1162) vs int4_rolealign cs=1 未找具体值 |
| TR-0315 | MED | ch4:1564 "INT4-RoleAlign 的 torch_ref 解码路径 TPOT 为 FP16 的 2.4–2.6x" 但 tab:int4-tpot-cross-model 数据显示 1.5B 58.97/24.57=2.40x，7B 61.80/24.47=2.53x，8B 70.56/27.41=2.57x — 用 "2.4–2.6" 是向下取整，丢失 1.5B 的 "仅 2.40x" 事实 | ch4_experiments.tex:1562-1564 | final/final_data/int4_rolealign/runs/prof_serial_latency_* |
| TR-0316 | LOW | tab:cross-model 的 8B RULER INT8-ours 退化 31.25 vs FP16 31.48（-0.73%），但 ch4:810 声称 "RULER 退化 -4.05% 超出非劣性阈值"；文本用 mean-混合（mainline + ablation）而表格用 mainline，需在文本附近明确披露 | ch4_experiments.tex:810 vs tab:cross-model + tab:app-sig-quality L183 (8B ruler -4.05% 来自 31.25 vs 32.58 baseline) | final/final_data/int8_mainline/runs/ + 4.05% 具体来自非 mainline 拉低 |
| TR-0317 | MED | ch4:1825 "4K 处 $\Delta$=−0.44ms 在噪声范围内" 和 ch4:1830 "4K 处各模型的差异均在 2ms 以内，不声称为显著 crossover" — **14B 4K $\Delta$=−0.44 已标 n.s.**，但 ch4:1870 却用 14B 4K 数据论证 "8B 与 14B 同 $H_{kv}$=8 crossover 一致"（都 n.s.）→ 论证力度应软化 | ch4_experiments.tex:1868-1873 | tab:phase-boundary (两个 n.s. 4K 值被用作正向论证) |
| TR-0318 | MED | ch4:1255-1256 "Qwen2.5-1.5B 仅 PPL 退化 4.9%"（MixedKV）— 计算 9.37/8.93=1.0493 → 4.93%（应写 4.9%）✓；但同段 "Qwen2.5-7B 出现 Needle 72.4% 的中等退化" — 72.4 来自单 seed；未标 3-seed mean ± std | ch4_experiments.tex:1229 (MixedKV 7B Needle 72.4) | final/final_data/kv_ablation/runs/k_int4_v_int8_long_s*_7b/ 需校验 3 seeds 均值 |
| TR-0319 | MED | appendix.tex:410 "7B baseline PPL=86.56 与主实验数据（85.49）量级一致"—两个值（86.56 vs 85.49）且都未标 tokens_evaluated；eng066 补充实验的对照锚点不透明 | appendix.tex:410-422 | final/final_data/ 未抽样到 eng066 对照数据 |

---

## E. 关键发现小结

1. **入口冲突最小化**：论文正文已基本切换到 `results/final/final_data/` 语义入口，**无直接 cite** 指向 `_canonical/` 或 `docs/experiment_data_index.md`。但 **2 处 tablenotes 路径**仍引用原目录名（TR-0300）。
2. **7B PPL 退化 6.0 vs 6.1** 在摘要、ch1、ch4 内部、ch5 之间三向矛盾（已由 TR-0002 / TR-0309 捕获）；真实值 6.13% 应统一取 6.1%。
3. **14B tokens_evaluated 子集化未披露**（TR-0308）是最严重的潜在可攻击点：表头 caption 声称"全量 302K tokens"但 14B 实际为 32K 子集（10× 差距）。
4. **两份 14B FP16 PPL**（4.685 vs 5.455）并存，应在 INDEX.md 明示"论文使用 4.685（batch_p012 32K 子集评测协议）"。
5. **tab:main-results 的 PPL 8.95 vs final_data 9.34** 差异源于附录 L576 承认的 max_length/stride 差异，但主表未显式披露，需 caption 级别补注。
6. **KIVI 4K–32K Needle 全 100%** 已由 postfix run 确认；tab:main-results "99±2.3" 属早期版本旧数据（TR-0310）。
7. 图表 ref/描述 方向性一致性整体良好（20 处抽样均无反向错误）。
8. 统计语言（显著/提升）整体规范（Bootstrap CI + q 值），只有 1 处（ch4:1679）"小幅 LongBench 改善"未附检验（TR-0305）。

---

## F. 建议修复顺序（for P3）

1. **P3a CRITICAL**：TR-0002（已记录，主会话处理）
2. **P3b HIGH**：TR-0300（引用路径）、TR-0302 + TR-0308（14B 子集披露）、TR-0303（14B FP16 二义）
3. **P3c MED**：TR-0301/0306（LongBench 单位）、TR-0309（7B 内部矛盾）、TR-0310（KIVI Needle）、TR-0311（KIVI 7B/8B 数据源）、TR-0312（INT8 PPL 二义）、TR-0314（cs=1 粒度）、TR-0315（TPOT 范围）、TR-0317（4K n.s. 论证）、TR-0318（Needle 72.4 单 seed）、TR-0319（86.56 vs 85.49 未披露）
4. **P3d LOW**：TR-0307（小数位）、TR-0313（Finding 3 ref）、TR-0304（未抽样）、TR-0316（8B RULER 4.05 披露）

