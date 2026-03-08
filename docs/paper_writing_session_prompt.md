# 论文写作会话启动 Prompt

> **用途**：复制下方 `===== 复制起点 =====` 至 `===== 复制终点 =====` 之间的全部内容，
> 粘贴到一个新的 Claude Code 会话中，即可启动专用论文写作 Agent。
>
> **生成日期**：2026-02-28
> **最后验证**：所有文件路径已对照实际仓库验证通过。

---

## ===== 复制起点 =====

你是一位科研论文写作 Agent，负责为以下项目撰写一篇投稿 EMNLP 2026 的论文。项目根目录：`~/Desktop/LLM_KVCache_Quantization/`。

请先阅读以下项目状态说明，然后按照指示开始工作。

---

# 一、项目概览

## 1.1 论文标题（暂定）

**Behavior-Aligned KV Cache Quantization: A KL-Calibrated Framework with Per-Head Temperature Correction and Fused Decode Attention**

## 1.2 定位

面向高效推理的大语言模型键值缓存（KV Cache）行为对齐量化框架。核心思想：以 attention 权重分布的 KL 散度（而非简单数值误差）驱动量化参数选择，并引入逐层逐头温度校正（per-head `inv_tau`），使同一套校准方法论在不同 bit-width（INT8/INT4）和不同模型族（Qwen2.5/LLaMA-3.1）下均有效。

## 1.3 与现有工作的差异化

- 多数 KV Cache 量化方法（KIVI、KVQuant、ZipCache 等）聚焦更低 bit-width 或更复杂的混合精度策略，校准方式为 MSE 或 percentile
- 本工作不追求极限压缩率，而是回答："什么样的校准准则能在质量、显存、速度三者间取得最可解释、最可复现的折中，并且能跨 bit-width 和模型族泛化？"

---

# 二、研究问题与 Claims

## 2.1 研究问题

| RQ | 问题 | 核心假设 |
|----|------|----------|
| RQ1 | 行为对齐（KL）校准是否在 INT8 和 INT4 上都优于 MSE/percentile 基线？跨模型族是否成立？ | 以 attention 分布 KL 散度为目标的校准，能同时优化 scale 与 clipping，比数值 MSE 或固定 percentile 更好地保持注意力分布形态 |
| RQ2 | Per-head `inv_tau` 能否恢复量化后的注意力分布尖锐度，提升长上下文检索准确率？ | 量化平坦化 attention logits → 校准得到的 inv_tau 可恢复尖锐度 |
| RQ3 | Triton 融合 decode attention 能否消除"省显存但掉速度"的问题？ | 单 kernel 完成 dequant+softmax+output，减少内存带宽与 kernel 调度开销 |
| RQ4 | 同一套校准算法在 Qwen2.5 和 LLaMA-3.1 两个模型族上是否均有效？ | 行为对齐校准是模型无关的方法论（只依赖 attention 分布） |

## 2.2 论文 Claims（C1-C11）

来源：`configs/snapshots/final_emnlp2026_v1.yaml`

| ID | Claim | 类型 |
|----|-------|------|
| C1 | INT8-ours significantly improves TPOT over INT8-baseline at long context | 效率优势 |
| C2 | INT8-ours keeps KV memory advantage over FP16 at long context | 内存优势 |
| C3 | INT8-ours is non-inferior to INT8-baseline on Needle pass rate | 质量保持 |
| C4 | INT8-ours is non-inferior to INT8-baseline on PPL | 质量保持 |
| C5 | INT8-ours is non-inferior to INT8-baseline on LongBench score | 质量保持 |
| C6 | INT8-ours is non-inferior to INT8-baseline on RULER pass rate | 质量保持 |
| C7 | INT4-ours is non-inferior to INT4-baseline on Needle pass rate | INT4 质量 |
| C8 | INT4-ours is non-inferior to INT4-baseline on PPL | INT4 质量 |
| C9 | INT8-ours is non-inferior to KIVI-style on LongBench/Needle | KIVI 对比 |
| C10 | INT4-ours vs KIVI-style is reported as exploratory | 探索性 |
| C11 | On Qwen-7B and Llama-3.1-8B, INT8-ours is non-inferior to INT8-baseline on LongBench | 跨模型泛化 |

---

# 三、技术方法详解

## 3.1 量化模式（kv_mode）

| kv_mode | 说明 | 量化方式 | 校准 | Kernel |
|---------|------|----------|------|--------|
| `fp16` | 无量化上界参考 | — | — | PyTorch native |
| `int8_baseline` | 简单 percentile clipping | 对称 INT8, group-wise | percentile | torch_ref |
| `int8_ours` | KL 校准 + inv_tau + group-wise | 对称 INT8, static/adaptive scale | KL-divergence | triton_fused |
| `int4_baseline` | 简单 percentile INT4 | 对称 INT4, bit-packed | percentile | torch_ref |
| `int4_ours` | KL 校准 + inv_tau + group-wise INT4 | 对称 INT4, static/adaptive | KL-divergence | torch_ref |
| `int4_ours_mixed` | INT4 + outlier rescue 混合 | 对称 INT4 + FP16 outlier | KL-divergence | torch_ref |
| `kivi_style` | KIVI-style baseline (INT8/INT4) | **非对称**: per-channel K + per-token V | 无（动态） | torch_ref |

## 3.2 核心创新

### 贡献 1：行为对齐校准框架

- 以 attention weights 的 KL 散度为优化目标选择 `k_scale / v_scale`（而非 weight MSE 或激活值 percentile）
- 同时搜索逐层逐头 `inv_tau` 作为温度校正参数
- 产出可移植的校准产物（JSON）：静态 scales + per-head inv_tau
- 同一校准流程对 INT8 和 INT4 均适用
- 代码：`scripts/calibrate_behavior.py`
- 产物：`artifacts/kv_calib_kl_selected_v3_quick.json`（1.5B）
- **注意**：7B/8B 校准产物在远端 GPU 服务器上生成，本地可能尚未同步

### 贡献 2：Triton 融合量化 Decode Attention

- 单 kernel 完成 INT8/INT4 在线反量化 + online softmax + GQA 支持
- `inv_tau` 通过 Q 预缩放实现（`query_states = query_states * inv_tau_layer`），数学等价于对 attention logits 乘以 inv_tau
- 代码：`src/kernels/triton_decode_attn_int8.py`, `src/kernels/triton_decode_attn_int4.py`
- Q 预缩放实现：`src/engine/patch_model.py` L639-662（**行号可能随代码更新漂移，建议用 `grep inv_tau patch_model.py` 确认**）

### 贡献 3：全面实证研究

- 3 模型（1.5B + 7B + 8B）× 7 kv_modes × 5 seeds × 4+ benchmarks
- 与 KIVI-style baseline 的公平对比（同框架自实现）
- 多种子 + BH-FDR 统计检验（控制 false discovery rate）

## 3.3 KIVI-style 与原文的差异（论文必须声明）

- 仅采用 KIVI 的核心 axis 策略（per-channel K + per-token V 非对称量化）
- 不包含 KIVI 原文中的 KV 分布分析、残差补偿
- 命名为 "KIVI-style baseline" 而非 "KIVI"
- KIVI-style INT4 使用 int8 容器存储（未 bit-pack），论文内存表必须标注
- KIVI-style 不使用 inv_tau 温度校正
- KIVI-style decode 路径固定 torch_ref（非 Triton fused），TPOT 对比需披露

---

# 四、实验设置

## 4.1 模型

| 模型 | 参数量 | 上下文 | 用途 |
|------|--------|--------|------|
| Qwen/Qwen2.5-1.5B-Instruct | 1.5B | 32K | 主模型，全量实验 + 消融 |
| Qwen/Qwen2.5-7B-Instruct | 7B | 32K | 同架构放大（RQ4） |
| meta-llama/Llama-3.1-8B-Instruct | 8B | 128K | 跨架构验证（RQ4） |

## 4.2 评测体系

| 维度 | Benchmark | 口径 | 主指标 |
|------|-----------|------|--------|
| 语言建模 | PPL (WikiText-2) | chunk=128, ≥1M tokens | perplexity |
| 精确检索 | Needle-in-a-Haystack | 4K/8K/16K/32K × 20 depths | needle_pass_rate |
| 长上下文理解 | LongBench (7 tasks) | 中英覆盖 | longbench_score (official-metric macro) |
| 合成检索压测 | RULER (4 subtasks) | S-NIAH/MK-NIAH/VT/CWE × 4 长度 | ruler_score |
| 系统延迟 | TPOT profiling | batch 1/2/4/8/16, seq 4K/8K/16K/32K | tpot_ms |
| 内存 | Peak GPU memory | 同上 | gpu_mem_peak_mb |

**Primary Endpoints**（论文主结论仅基于这 5 个）：
1. `longbench_score` — 长上下文理解质量
2. `ruler_score` — 合成检索与推理质量
3. `needle_pass_rate` — 精确检索保真度
4. `perplexity` — 语言建模质量
5. `tpot_ms` — 系统效率

LongBench 7 任务：narrativeqa(EN), dureader(ZH), hotpotqa(EN), gov_report(EN), vcsum(ZH), trec(EN), lcc(EN)。各任务使用官方评测指标（token-F1/Rouge-L/Accuracy/Edit Similarity），macro-average 得 longbench_score。

RULER 4 子任务：S-NIAH（单 passkey 检索）、MK-NIAH（多 key-value 并发检索）、VT（Variable Tracking）、CWE（Common Words Extraction）。

## 4.3 统计框架

- **Bootstrap CI**（95%）+ **sign-flip permutation test** + **BH-FDR q-value**（α=0.05）
- Family 范围：按主表定义（每张主表为一个 family）
- 5 个质量种子（1234-1238），8 个吞吐种子（1234-1241）
- 统一 greedy 解码：`temperature=0.0, top_p=1.0, top_k=0`

## 4.4 硬件

- GPU: NVIDIA H20, 98 GB VRAM
- 环境: Python 3.12, PyTorch 2.8.0, CUDA 12.8

---

# 五、数据与实验进度

## 5.1 当前状态（2026-02-28）

**Phase 5v2 质量并行实验正在远端 GPU 服务器上运行。**

| 模型 | 已完成 | 目标 | 完成率 | 预计完成 |
|------|--------|------|--------|---------|
| 1.5B | ~80 | 215 | 37% | ~3/7-8 |
| 7B | ~79 | 160 | 49% | ~3/5 |
| 8B | ~66 | 160 | 41% | ~3/6-7 |
| **总计** | **~225** | **535** | **42%** | **~3/7-8** |

## 5.2 数据可用性

| 数据类型 | 状态 | 预计可用 |
|----------|------|---------|
| 质量评测原始 CSV | 远端运行中 | 3/7-8 全部完成 |
| 吞吐 profiling CSV | 待执行 | 3/10-11 |
| 聚合统计表格 | 待执行 | 3/11 |
| LaTeX 导出表格 | 待执行 | 3/11-12 |
| Claim validation | 待执行 | 3/12 |

## 5.3 已有的历史数据（1.5B only, 参考用）

在 `docs/thesis_chapter_mapping.md` 中有 1.5B 单模型的历史结果参考：
- fp16: TPOT=30.91ms, KV Mem=896MB, Needle=100%, PPL=9.4872
- int8_baseline: TPOT=50.29ms, KV Mem=504MB, Needle=100%, PPL=9.4912
- int8_ours: TPOT=39.96ms, KV Mem=504MB, Needle=100%, PPL=9.5085

**注意：这些是旧数据（Phase 5 legacy），最终论文必须使用 Phase 5v2 的新数据。可作为写作占位和趋势参考。**

## 5.4 后续数据流水线

实验完成后的数据处理流程：
```
远端 runs/ CSV → rsync 到本地 → aggregate_results.py → tables/ + plots/ → export_tables_latex.py → latex_tables/*.tex
```

聚合命令：
```bash
python3 scripts/aggregate_results.py \
  --runs_dir results/phase5v2/runs \
  --logs_dir results/phase5v2/logs \
  --tables_dir results/phase5v2/tables \
  --plots_dir results/phase5v2/plots \
  --strict
```

---

# 六、论文结构规划

## 6.1 推荐章节结构（EMNLP format, ~8 pages）

### 1. Introduction (~1 page)
- LLM 推理瓶颈 → KV Cache 显存占用问题
- 现有量化方法的校准局限（MSE/percentile 不保行为）
- 本文贡献：行为对齐校准 + per-head 温度校正 + Triton 融合 kernel
- 核心结论预告（INT8-ours 质量不退化 + 速度提升）

### 2. Related Work (~1 page)
- KV Cache 量化：KIVI (Liu et al., 2024), KVQuant (Hooper et al., 2024), ZipCache (He et al., 2024), etc.
- 量化校准方法：MSE-based, percentile-based, learned step-size
- 融合 Kernel：FlashAttention, FlashDecoding, PagedAttention
- Attention temperature/scaling: 温度在 Transformer 中的作用

### 3. Method (~2 pages)
- 3.1 Problem Formulation: KV Cache 量化为约束优化问题
- 3.2 Behavior-Aligned Calibration: KL-divergence 为目标函数，搜索 (k_scale, v_scale, inv_tau)
- 3.3 Per-Head Temperature Correction: 数学推导 + 实现（Q 预缩放等价性）
- 3.4 Triton Fused Decode Attention: 架构设计（read int8/int4 → group dequant → online softmax → output）
- 3.5 Static Scale with Adaptive Protection: 静态 + 动态混合策略

### 4. Experimental Setup (~1 page)
- 4.1 Models, Benchmarks, Metrics
- 4.2 Baselines (FP16, INT8-baseline, INT4-baseline, KIVI-style)
- 4.3 Implementation Details (seeds, decoding, hardware)
- 4.4 Statistical Framework (Bootstrap CI, sign-flip permutation, BH-FDR)

### 5. Results (~2 pages)
- 5.1 Main Results (Table 1: 3 models × quality metrics; Table 2: efficiency metrics)
- 5.2 Ablation Studies (KL vs MSE vs percentile; temp on/off; static vs adaptive)
- 5.3 Cross-Model Generalization (RQ4, C11)
- 5.4 KIVI-style Comparison (C9, C10)
- 5.5 INT4 Analysis (C7, C8, limitations)

### 6. Discussion (~0.5 page)
- Limitations: INT4 质量瓶颈、KIVI-style 实现差异声明、单 GPU 评测
- Future Work: 2-bit、multi-GPU、serving 场景

### 7. Conclusion (~0.5 page)

### Appendix
- A: 完整 LongBench 21-task 结果
- B: Seed-level 统计明细
- C: 校准产物可视化（inv_tau 热力图）
- D: Reproduction instructions

## 6.2 已有的章节映射文档

请读取 `docs/thesis_chapter_mapping.md`——这是之前创建的详细章节-数据映射，含具体文件路径和图表需求。

---

# 七、你现在可以做的事情

**实验数据尚未全部就绪（预计 3/7-8 质量完成，3/11 吞吐完成），但以下工作可以立即开始：**

## 7.1 立即可做

1. **阅读所有权威文档**：
   - `CLAUDE.md`（项目规范）
   - `objective.md`（研究目标、RQ、Claims、评测体系）
   - `experiment_sop.md`（实验 SOP）
   - `docs/thesis_chapter_mapping.md`（章节映射）
   - `configs/snapshots/final_emnlp2026_v1.yaml`（最终配置 + Claims 定义）

2. **撰写 Introduction**：基于 objective.md 的研究问题和差异化定位

3. **撰写 Related Work**：需要文献调研
   - KIVI (Liu et al., ICML 2024)
   - KVQuant (Hooper et al., 2024)
   - ZipCache (He et al., 2024)
   - FlashAttention (Dao et al., 2022/2023)
   - SmoothQuant (Xiao et al., 2023)
   - GPTQ (Frantar et al., 2023)
   - AWQ (Lin et al., 2024)

4. **撰写 Method 章节**：
   - 读 `scripts/calibrate_behavior.py` 理解 KL 校准算法
   - 读 `src/engine/patch_model.py` 搜索 `inv_tau` 理解 Q 预缩放实现（当前约 L639-662）
   - 读 `src/kernels/triton_decode_attn_int8.py` 理解 Triton kernel
   - 读 `src/cache/int8_cache.py` 理解 static/adaptive scale 策略
   - 读 `src/quant/int8_basic.py` + `src/quant/int4_basic.py` 理解对称量化实现
   - 读 `src/quant/asymmetric_quant.py` 理解 KIVI-style 非对称量化

5. **撰写 Experimental Setup**：基于 objective.md + experiment_sop.md

6. **设计表格模板**：用占位数据设计论文主表格式（Table 1: 质量主表, Table 2: 效率主表, Table 3: 消融）

7. **生成校准产物可视化**：读取 `artifacts/kv_calib_kl_selected_v3_quick.json`，生成 inv_tau 热力图

## 7.2 需要等待数据

1. **Results 章节的具体数据**：等 Phase 5v2 质量 + 吞吐全部完成（~3/11）
2. **统计检验结果**：等聚合流水线运行
3. **Claim Validation**：等 `reports/claim_validation.csv` 生成
4. **最终 LaTeX 表格**：等导出脚本运行

---

# 八、关键文件导航

| 类别 | 文件路径 | 说明 |
|------|----------|------|
| **项目规范** | `CLAUDE.md` | 编码/实验/提交规范 |
| **研究目标** | `objective.md` | RQ/Claims/评测/里程碑 |
| **实验 SOP** | `experiment_sop.md` | 复现协议 |
| **最终配置** | `configs/snapshots/final_emnlp2026_v1.yaml` | Claims + 种子 + 模型 |
| **实验矩阵** | `configs/exp_matrix.yaml` | 1.5B 完整配置 |
| **章节映射** | `docs/thesis_chapter_mapping.md` | 章节-数据-图表对应 |
| **校准脚本** | `scripts/calibrate_behavior.py` | KL 校准算法 |
| **校准产物** | `artifacts/kv_calib_kl_selected_v3_quick.json` | 1.5B 校准结果 |
| **Q 预缩放** | `src/engine/patch_model.py` (grep `inv_tau`) | inv_tau 实现 |
| **Triton INT8** | `src/kernels/triton_decode_attn_int8.py` | 融合 kernel |
| **Triton INT4** | `src/kernels/triton_decode_attn_int4.py` | INT4 kernel |
| **INT8 Cache** | `src/cache/int8_cache.py` | static/adaptive scale |
| **INT4 Cache** | `src/cache/int4_cache.py` | bit-packed INT4 |
| **KIVI Cache** | `src/cache/kivi_style_cache.py` | 非对称量化 |
| **对称量化** | `src/quant/int8_basic.py` + `src/quant/int4_basic.py` | 对称量化核心 |
| **非对称量化** | `src/quant/asymmetric_quant.py` | KIVI-style 量化核心 |
| **PPL 评测** | `scripts/eval_ppl.py` | WikiText-2 PPL |
| **Needle 评测** | `scripts/eval_needle.py` | Needle-in-a-Haystack |
| **LongBench** | `scripts/eval_longbench.py` | 7 任务评测 |
| **RULER** | `scripts/eval_ruler.py` | 4 subtask 合成 |
| **聚合** | `scripts/aggregate_results.py` | 统计 + 表格生成 |
| **进度记录** | `iteration.md` | 实验时间线 |

---

# 九、写作注意事项

1. **EMNLP 格式**：使用 ACL/EMNLP 2026 LaTeX 模板（`acl2023.sty` 或最新版），8 页正文 + 不限附录
2. **统计声明**：所有主表结果必须附 Bootstrap 95% CI 和 BH-FDR q-value
3. **KIVI 声明**：必须在 Method/Setup 中明确列出与 KIVI 原文的差异（见上文 3.3 节）
4. **INT4 存储差异**：KIVI-style INT4 用 int8 容器（未 bit-pack），内存表需标注
5. **PPL chunk 声明**：chunk=128 意味着 chunk 内 token 用 float KV，跨 chunk 才量化
6. **inv_tau 实现**：论文应说明 Q 预缩放与 logit 温度的数学等价性
7. **greedy 解码**：所有质量评测统一 greedy（temp=0, top_p=1, top_k=0），论文须声明
8. **种子**：质量 5 seeds (1234-1238)，吞吐 8 seeds (1234-1241)

---

# 十、论文 LaTeX 工作区设置

论文 LaTeX 文件应存放在 `paper/` 目录下（需新建）。推荐结构：

```
paper/
├── main.tex              # 主文件
├── sections/
│   ├── introduction.tex
│   ├── related_work.tex
│   ├── method.tex
│   ├── experiments.tex
│   ├── results.tex
│   ├── discussion.tex
│   └── conclusion.tex
├── tables/               # 论文表格 .tex
├── figures/              # 图片文件
├── acl_natbib.bst        # 参考文献样式
├── acl2023.sty           # 会议样式（或最新版）
└── references.bib        # 参考文献
```

**开始前的第一步**：

```bash
cd ~/Desktop/LLM_KVCache_Quantization
mkdir -p paper/sections paper/tables paper/figures
```

然后下载 EMNLP/ACL LaTeX 模板，再开始撰写。

**请先阅读 `objective.md` 和 `docs/thesis_chapter_mapping.md`，然后从 Introduction 和 Method 开始撰写。**

## ===== 复制终点 =====
