## 项目名称

面向高效推理的大语言模型键值缓存行为对齐量化框架

**目标会议**：EMNLP 2026（会期 2026-10-24 至 10-29，布达佩斯；走 ARR，
以 ARR May 2026 cycle 为主投窗口，Aug 2026 为备选；
commitment deadline 以官方公布为准；里程碑按 ARR cycle 驱动）

---

## 论文定位

本项目提出 **行为对齐校准框架（Behavior-Aligned Calibration Framework）**，
核心思想：以 attention 权重分布的 KL 散度（而非简单数值误差）驱动量化参数选择，
并引入逐层逐头温度校正（per-head `inv_tau`），使同一套校准方法论在
**不同 bit-width（INT8 / INT4）** 和 **不同模型族（Qwen2.5 / LLaMA-3.1）** 下均有效。

与现有工作的差异化：
- 多数 KV Cache 量化方法（KIVI、KVQuant、ZipCache 等）聚焦 **更低的 bit-width**
  或 **更复杂的混合精度策略**，校准方式通常为 MSE 或 percentile；
- 本工作不追求极限压缩率，而是回答一个被忽略的系统性问题：
  **"什么样的校准准则能在质量、显存、速度三者间取得最可解释、最可复现的折中，
  并且能跨 bit-width 和模型族泛化？"**

---

## 固定决策（不可修改）

### 模型

| 模型 | 用途 | Revision |
|------|------|----------|
| `Qwen/Qwen2.5-1.5B-Instruct` | 主模型，全量实验 | 已 pin，见 `configs/snapshots/` |
| `Qwen/Qwen2.5-7B-Instruct` | 同架构放大，验证 scale-up | 首次下载后立即 pin，此后不可变 |
| `meta-llama/Llama-3.1-8B-Instruct` | 跨架构验证，证明泛化性（128K 上下文） | 首次下载后立即 pin，此后不可变 |

> **注意**：原方案中的 LLaMA-3-8B-Instruct 上下文仅 8K，无法支撑 32K 评测，
> 已修正为 **LLaMA-3.1-8B-Instruct**（128K 上下文）。
>
> Qwen2.5-7B-Instruct 默认 `config.json` 的 `max_position_embeddings` 为 32768，
> 主线评测锁定 ≤32K，不启用 YaRN rope_scaling（避免引入长度外推变量）。
>
> 所有模型的 `model_revision`（commit hash）在首次下载后立即 pin 住，
> 写入 `configs/snapshots/` 对应的 YAML 配置文件，确保严格复现。

### 主线实验环境

- 版本以 `env/versions.txt` 和 `env/requirements_freeze.txt` 产物为准
- 当前主线：Python 3.12、PyTorch 2.8.0、CUDA 12.8（AutoDL 镜像）
- 依赖：Transformers、Triton、pynvml、numpy/pandas/matplotlib

### 执行路径

- **研究主路径（唯一）**：Transformers + 自定义 generation loop + 自定义 KV cache
  （服务于算法与 kernel 优化，避免被框架"封装掉关键环节"）

### 解码口径

- 质量评测统一 **greedy 解码**：`temperature=0.0, top_p=1.0, top_k=0`
- 与 `configs/snapshots/` 中实验矩阵对齐

---

## 研究问题与假设

### RQ1：校准泛化性

行为对齐（KL）校准是否在 INT8 和 INT4 上都优于 MSE / percentile 基线？
跨模型族（Qwen2.5 vs LLaMA-3.1）是否成立？

**假设**：以 attention 分布 KL 散度为目标的校准，能同时优化 scale 与 clipping，
比数值 MSE 或固定 percentile 更好地保持注意力分布形态，从而在不同 bit-width 下
产生更稳定的长上下文性能。

### RQ2：逐头温度校正

Per-head `inv_tau` 能否恢复量化后的注意力分布尖锐度，
提升长上下文检索（Needle / RULER）准确率？

**假设**：量化会平坦化 attention logits，导致长上下文检索失败；
通过校准得到的逐层逐头 `inv_tau` 施加温度校正（在 decode 时等价于缩放 Query），
可恢复注意力尖锐度，提升 retrieval 准确率。

### RQ3：系统效率

Triton 融合 decode attention（q_len=1）能否消除"省显存但掉速度"的问题？
吞吐量如何随 batch size 扩展？

**假设**：在 decode 阶段用单个 Triton kernel 完成
"读量化 K/V → group-wise 反量化 → online softmax → 加权输出"，
可减少内存带宽与 kernel 调度开销，使 TPOT 不退化或有提升。

### RQ4：跨模型鲁棒性

同一套校准算法（KL + inv_tau 搜索）与默认超参，在 Qwen2.5 和 LLaMA-3.1
两个不同模型族上，是否均能稳定产生质量-效率的改进？

**假设**：行为对齐校准是模型无关的方法论（只依赖 attention 分布而非特定架构假设），
在不同模型族上仅需重新运行校准脚本即可获得有效参数。
**澄清**：RQ4 验证的是"校准算法的泛化性"，而非"校准产物（scales/inv_tau）
的跨架构可迁移性"——后者因 layer/head 数不同而不成立，也非本文目标。

---

## 创新点与贡献

### 贡献 1：行为对齐校准框架

- 以 attention weights 的 KL 散度为优化目标选择 `k_scale / v_scale`，
  而非传统的 weight MSE 或激活值 percentile
- 同时搜索逐层逐头 `inv_tau` 作为温度校正参数
- 产出可移植的校准产物（JSON）：静态 scales + per-head inv_tau
- **关键性质**：同一校准流程对 INT8 和 INT4 均适用（只需调整量化范围）；
  对不同模型只需重新运行校准脚本

### 贡献 2：Triton 融合量化 decode attention

- 单 kernel 完成 INT8 / INT4 在线反量化 + online softmax + GQA 支持
- 实现位置：`src/kernels/triton_decode_attn_int8.py`（`decode_attn_int8_kernel`）
- INT4 通过先 unpack 为 INT8 后复用同一 kernel
  （`src/kernels/triton_decode_attn_int4.py`）
- **inv_tau 实现说明**：`inv_tau` 通过 Q 预缩放在 `src/engine/patch_model.py`
  第 546-550 行实现（`query_states = query_states * inv_tau_layer`），
  数学上等价于对 attention logits 乘以 `inv_tau`，但不在 kernel 内部实现。
  这一设计使 kernel 签名保持简洁，避免额外 launch 参数

### 贡献 3：全面实证研究

- 3 模型（1.5B + 7B + 8B）× 2 bit-width（INT8 + INT4）
- 3 benchmark 套件：Needle-in-a-Haystack + LongBench + RULER
- 与 KIVI-style baseline 的公平对比（同框架自实现）
- 多种子 + BH-FDR 统计检验（控制 false discovery rate）

---

## 评测体系

### Benchmarks

| 维度 | Benchmark | 口径 | 状态 |
|------|-----------|------|------|
| 长上下文检索 | Needle-in-a-Haystack | 4K/8K/16K/32K，20 depth levels，exact match | ✅ 已有 |
| 长上下文理解 | LongBench（子集） | 7 个代表性任务（见下），中英覆盖 | ✅ 已有 |
| 合成检索压测 | RULER（4 subtasks） | S-NIAH / MK-NIAH / VT / CWE × 4 长度点 | ✅ 已有 |
| 语言建模质量 | PPL (WikiText-2) | chunk=128 主结果 + chunk=1 验证 | ✅ 已有 |
| 系统性能 | Latency/Memory/Throughput | TPOT/TTFT/峰值显存/吞吐 | ✅ 已有 |

**LongBench 主表任务**（7 个，覆盖中英 × 检索/总结/推理/代码；
任务名与 [THUDM/LongBench](https://github.com/THUDM/LongBench) 官方数据集对齐）：
- 单文档 QA：`narrativeqa` (EN)、`dureader` (ZH)
- 多文档 QA：`hotpotqa` (EN)
- 摘要：`gov_report` (EN)、`vcsum` (ZH)
- 少样本学习：`trec` (EN)
- 代码：`lcc` (EN)
- 全量 LongBench（21 个任务）结果放附录
- **主表汇总协议**：每任务使用 LongBench 官方评测指标——QA 类（narrativeqa/hotpotqa）为 token-F1，
  中文 QA（dureader）与摘要类（gov_report/vcsum）为 Rouge-L，
  分类类（trec）为 Accuracy，代码类（lcc）为 Edit Similarity。
  主表分数 `longbench_score` 定义为 7 个任务官方指标的 macro-average（各指标已归一化到 [0,1]）。
  CSV 同时保留统一 token-F1（`longbench_f1_macro`）以供向后兼容与消融对照；
  单任务原始指标（含 `official_metric_name` 与 `official_metric_value`）在附录表中提供。
  指标映射表位于 `scripts/eval_longbench.py` 的 `TASK_OFFICIAL_METRIC` 字典

**RULER 主表子任务**（参照 [NVIDIA/RULER](https://github.com/NVIDIA/RULER)
(Hsieh et al., 2024) 的任务分类体系，自行实现确定性合成 task generator，
独立于 RULER 官方运行框架，集成到本项目的 `generate_from_ids()` 推理管线中）：
- **Retrieval**：S-NIAH（单 passkey 检索）、MK-NIAH（多 key-value 并发检索，默认 4 keys）
- **Multi-hop Tracing**：VT（Variable Tracking，链式变量赋值，默认 4 hops）
- **Aggregation**：CWE（Common Words Extraction，频率聚合，默认 top-10）
- 长度点：4K / 8K / 16K / 32K
- 实现位置：`scripts/eval_ruler.py`

### PPL 评测口径

- **主结果**：`chunk_size=128, max_length=1024, stride=512, target_tokens=1_000_000`
  - 所有方法（FP16 / INT8 / INT4 / KIVI-style）统一使用同一 chunk_size
  - 论文中须声明：chunk=128 意味着 chunk 内 token 间用 float KV（未量化），
    跨 chunk 的 token 经过量化 KV cache
  - `target_tokens` 确保每个 setting 评测 ≥1M tokens，提供稳定的 PPL 估计
- **快速验证模式**：`max_samples=64`（约 65K tokens），用于 smoke test 与开发迭代
- **辅助验证**：在 Qwen2.5-1.5B 上额外跑 `chunk_size=1`（max_samples=64），
  确认 PPL 差异趋势与 chunk=128 一致，作为严格性验证

### SOTA 对照基线

| 方法 | 说明 | 状态 |
|------|------|------|
| FP16 | 无量化，上界参考 | ✅ 已有 |
| INT8 naive percentile | 简单 percentile clipping，下界参考 | ✅ 已有 |
| INT8-ours | KL 校准 + inv_tau + group-wise + Triton fused | ✅ 已有 |
| INT4-baseline | 简单 percentile INT4 | ✅ 已有 |
| INT4-ours | KL 校准 + inv_tau + group-wise INT4 | ✅ 已有 |
| KIVI-style baseline | 受 KIVI 启发的异轴量化对照（per-channel K + per-token V，自实现简化版；与 KIVI 原文差异见下） | 🆕 需新增 |

**KIVI-style baseline 与 KIVI 原文的差异声明**：
- 本实现仅采用 KIVI 的核心 axis 策略（per-channel K + per-token V 非对称量化），
  不包含 KIVI 原文中的 KV 分布分析、残差补偿等完整方法细节
- 命名为 "KIVI-style baseline" 而非 "KIVI"，避免不忠实复现的审稿风险
- KIVI 原文作为 Related Work 引用，论文中明确列出与官方实现的差异与限制
- 若后续官方 KIVI 实现可在本框架内运行，优先使用官方实现

### 统计框架

- **Bootstrap CI**（95%）+ **sign-flip permutation test** + **BH-FDR q-value**（α=0.05）
- Family 范围：按主表定义（每张主表为一个 family），避免跨表展开导致比较数爆炸
- 已在 `scripts/aggregate_results.py` 中实现（`_add_bh_fdr_qvalues` 函数）
- **不使用 Holm-Bonferroni**：BH-FDR 控制 false discovery rate（而非 FWER），
  在 NLP/ML 实验中为标准做法，检验力更优

### Primary Endpoints（≤5 条）

论文主结论仅基于以下 primary endpoints，避免多重比较导致结论发散：

1. **LongBench official-metric macro**（`longbench_score`）— 长上下文理解质量（按官方指标）
2. **RULER macro-accuracy**（`ruler_score`）— 合成检索与推理质量
3. **Needle pass rate**（`needle_pass_rate`）— 精确检索保真度
4. **PPL**（`perplexity`）— 语言建模质量
5. **TPOT**（`tpot_ms`）— 系统效率（decode 阶段延迟）

### 种子

- **主实验**：5 个种子（1234, 1235, 1236, 1237, 1238）
- **吞吐测试**：8 个种子（1234–1241）

---

## 完成定义（Definition of Done）

- **全管线可跑**：3 模型 × {FP16, INT8-baseline, INT8-ours, INT4-baseline,
  INT4-ours, KIVI-style} 全部产出结构化结果（CSV/JSON）
- **评测齐全**：LongBench（子集）+ Needle + RULER（子集）+ PPL 全部通过
- **统计严谨**：所有主表结果附带 Bootstrap CI 和 BH-FDR q-value
- **可复现**：实验矩阵配置文件 + 一键复跑脚本 + env freeze + git commit pin
- **LaTeX-ready**：自动导出论文表格和图表
- **消融完整**：KL vs MSE vs percentile、group_size、temperature 开关、
  static vs adaptive scales 等系统性消融
- **2-bit 拓展**（可选 stretch goal）

---

## 复现与记录规则（强制）

### 实验入口

- 以 `configs/snapshots/` 下的 YAML 配置文件为实验矩阵定义
  （当前版本：`exp_matrix_week5_external_validity_v1.yaml`）
- 一键复跑脚本：`scripts/run_week5_external_validity_v1.sh`
- 关键口径锁定（与配置对齐）：
  - greedy decoding：`temperature=0.0, top_p=1.0, top_k=0`
  - 多种子运行（见上述种子定义）
- **snapshot 治理**：论文主结论必须引用且仅引用一个带 `final` 前缀的配置快照
  （如 `final_emnlp2026_v1.yaml`）。新建 snapshot 时须在文件头注明变更点与前序版本，
  避免入口爆炸导致不可复现

### 运行记录

所有脚本输出结构化结果（CSV/JSON），并记录：
- `timestamp`（运行时刻）
- `git_commit`（当前 commit）
- `hardware`（GPU 型号/显存）、驱动/CUDA/torch/transformers 版本（见 `env/`）
- 关键参数快照（从配置文件解析后的 config dump）

### 解码固定

涉及质量评测时，统一 greedy 解码，禁止临时改采样参数造成口径漂移。

### 实验输出路径

- `results/`（禁止手写散落到其他目录）
  - `results/runs/`：每次运行的 CSV/JSON
  - `results/tables/`：论文表格
  - `results/plots/`：论文图
  - `results/logs/`：脚本运行日志
- `artifacts/`：校准与中间产物（例如 `artifacts/kv_calib_kl_selected_v3_quick.json`）

### 结构化结果字段（CSV schema）

所有 profile/eval 脚本必须输出 `results/runs/*.csv`，字段至少包含：

`run_id, model_id, kv_mode, quant_bits, clip_percentile, group_size, dtype,
seq_len, gen_len, batch, ttft_ms, tpot_ms, tok_per_s, gpu_mem_peak_mb,
timestamp, git_commit`

---

## 非目标（明确边界）

- 不做"全能部署框架"；以固定模型和固定口径完成论文闭环为第一优先级
- **2-bit / 1-bit 量化为拓展 / 未来工作，非核心贡献**
- 不涉及多 GPU / 分布式推理
- 不涉及模型训练或微调
- 不做服务端并发压测（Milestone I 从主线中移除）

---

## 稳定接口（Stable APIs）

本项目采用"研究主路径（Transformers + 自定义 generation loop + 自定义 KV cache）"，
接口在早期固定，后续实现不得随意破坏。

### Engine

- `Engine.generate(prompts, generation_config, kv_mode, runtime_config) -> GenerationOutput`

### KV Cache

- `KVCache.append(layer_id, k, v)`
- `KVCache.get_kv(layer_id) -> (k, v)`
- 约束：
  - 必须支持 decode 过程中按步增长（每步追加 1 token 的 KV）
  - 必须能在 `kv_mode` 切换时替换实现
    （fp16 / int8_baseline / int8_ours / int4_baseline / int4_ours / kivi_style）
- 实现位置：
  - `src/cache/fp16_cache.py`
  - `src/cache/int8_cache.py`（含静态/自适应 scales、per-head temperature）
  - `src/cache/int4_cache.py`（含 outlier rescue、mixed rescue）

### Quantizer

- `quantize_symmetric(tensor, percentile, group_size) -> (quantized, scale)`
- `dequantize_symmetric(quantized, scale) -> tensor`
- INT8 实现：`src/quant/int8_basic.py`
- INT4 实现：`src/quant/int4_basic.py`（含 pack_int4 / unpack_int4）
- 静态 scale 支持：`quantize_symmetric_int8_with_scale` / `quantize_symmetric_int4_with_scale`

### Kernels

- Triton kernels 位于 `src/kernels/`
- INT8：`triton_decode_attn_int8.py`（`decode_attn_int8_kernel` + `decode_attn_int8` wrapper）
- INT4：`triton_decode_attn_int4.py`（先 unpack 为 INT8 后复用同一 kernel）

### 校准产物

- 格式：JSON
- 典型路径：`artifacts/kv_calib_kl_selected_v3_quick.json`
- 内容：per-layer `k_scale`、`v_scale`（group-wise）、`inv_tau`（per-head）
- 生成脚本：`scripts/calibrate_behavior.py`

---

## 项目执行路线图

### 已完成里程碑

| 里程碑 | 内容 | 关键产出 |
|--------|------|----------|
| A ✅ | 环境与 Smoke Test | `env/versions.txt`、`scripts/smoke_test.py` |
| B ✅ | 自定义 Generation Loop | `src/engine/generate_loop.py`，prefill + decode 分离 |
| C ✅ | FP16 KV Cache Baseline | `src/cache/fp16_cache.py` |
| D ✅ | 评测框架 | `profile_latency.py`、`profile_memory.py`、`eval_ppl.py`、`eval_needle.py` |
| E ✅ | INT8 Baseline | `src/quant/int8_basic.py`、`src/cache/int8_cache.py` |
| F ✅ | INT8-ours（KL 校准 + inv_tau + group-wise） | `scripts/calibrate_behavior.py`、`artifacts/kv_calib_kl*.json` |
| G ✅ | Triton 融合 Decode Kernel（INT8） | `src/kernels/triton_decode_attn_int8.py` |
| H ✅ | INT4 实现 | `src/quant/int4_basic.py`、`src/cache/int4_cache.py`、`src/kernels/triton_decode_attn_int4.py` |
| J（部分）✅ | 实验矩阵 & 可复现流水线 | `scripts/run_experiments.py`、`scripts/run_final_journal_v1.sh`、`scripts/aggregate_results.py` |

### 新增里程碑（期刊扩展）

#### Milestone K：多模型支持

- **目标**：在 Qwen2.5-7B 和 LLaMA-3.1-8B 上复现校准 + 全量实验
- **子任务**：
  - K1：模型下载与 revision pin
  - K2：分别运行 `calibrate_behavior.py` 生成校准产物
  - K3：验证 INT8 + INT4 管线在两个新模型上端到端跑通
  - K4：跑完整实验矩阵（needle + PPL + latency + memory）
- **验收**：3 模型均产出结构化结果，且 INT8-ours 在所有模型上 needle 不劣于 baseline

#### Milestone L：LongBench 集成

- **目标**：接入 LongBench 评测，7 任务代表性子集作为主表
- **子任务**：
  - L1：数据集下载与预处理（7 个任务）✅
  - L2：编写 `scripts/eval_longbench.py` ✅
  - L3：接入实验矩阵（configs 新增 LongBench runs）✅
  - L4：全量 LongBench 作为附录（可选）
- **验收**：3 模型 × 6 kv_mode × 7 任务均产出结果

#### Milestone M：RULER 集成

- **目标**：接入 RULER 4 subtask 合成 benchmark（S-NIAH/MK-NIAH/VT/CWE）
- **子任务**：
  - M1：自实现 4 个 RULER 子任务的确定性 task generator ✅
  - M2：编写 `scripts/eval_ruler.py`（集成 4 subtasks）✅
  - M3：接入实验矩阵 ✅
- **验收**：3 模型 × 6 kv_mode × 4 任务 × 4 长度点均产出结果

#### Milestone N：KIVI Baseline 实现

- **目标**：在本框架内自实现 KIVI-style baseline 作为 SOTA 对照
- **子任务**：
  - N1：实现 per-channel K quantization + per-token V quantization（KIVI 核心 axis 策略）
  - N2：编写 `src/cache/kivi_style_cache.py`
  - N3：接入 `kv_mode=kivi_style`
  - N4：在 3 个模型上跑完整评测
  - N5：文档化与 KIVI 原文的差异
- **验收**：KIVI-style 管线端到端可跑，产出结构化结果

#### Milestone O：INT4 补全

- **目标**：确保 INT4 在 3 个模型上全部跑通，质量可控
- **子任务**：
  - O1：在 7B 和 8B 模型上验证 INT4 量化 + 校准
  - O2：修复可能的 INT4 数值问题
  - O3：完善 INT4 消融（pack/unpack 正确性、outlier rescue 效果）
- **验收**：INT4-ours 在所有模型上 needle/PPL 有合理结果

#### Milestone P：系统性消融实验

- **目标**：产出消融表，支撑论文的方法选择论证
- **消融维度**：
  - 校准方法：KL vs MSE vs percentile（RQ1 核心）
  - group_size：16 / 32 / 64 / 128
  - temperature：开 / 关（RQ2 核心）
  - scales：static vs adaptive vs dynamic
  - bit-width：INT8 vs INT4（同一校准框架下）
- **验收**：每个消融对产出结构化结果 + 统计显著性

#### Milestone Q：最终实验 & 论文表格

- **目标**：3 模型全矩阵运行 + 统计聚合 + LaTeX 导出
- **子任务**：
  - Q1：运行完整实验矩阵（含 throughput repair loop）
  - Q2：`aggregate_results.py` 生成全部表格（含 BH-FDR q-value）
  - Q3：`export_tables_latex.py` 导出 LaTeX
  - Q4：`generate_thesis_report.py` 生成汇总报告
- **验收**：`results/final_journal_v2/` 目录完整，所有 LaTeX 表格可编译

#### Milestone R（拓展）：2-bit 量化

- **目标**：探索 INT2 的可行性，作为论文的 future work 实验支撑
- **子任务**：
  - R1：INT2 量化模块（`src/quant/int2_basic.py`）
  - R2：Triton 2-bit decode kernel（或复用 INT8 kernel + unpack）
  - R3：校准适配（calibrate_behavior.py 支持 2-bit 范围）
  - R4：在 1.5B 模型上运行 needle + PPL
- **验收**：有初步结果可报告（即使质量下降明显也属预期）

---

## 如何驱动 agent 做每一步（统一指令模板）

### 模板 A：实现一个功能点

```text
目标：<1 句话描述本次要完成的子任务>
当前状态：<已完成到哪里；相关文件/分支/结果路径>
约束：
  - 必须对齐：objective.md / configs/snapshots/
  - 代码风格：PEP8（79 字符），不要引入未使用依赖
  - 必须加异常处理：文件/网络/显存不足/缺少 CUDA 等
验收标准：
  - 命令：<我将运行的命令>
  - 预期输出：<终端关键输出> + <结果文件路径> + <CSV 字段必须包含哪些>
我希望你下一步做：列出 3-5 个最小可执行步骤并直接开始
```

agent 输出必须包含：
- 改了哪些文件（精确路径）
- 我该运行哪些命令（复制即可运行）
- 预期输出长什么样（关键日志 + 文件路径 + CSV/JSON 字段）
- 失败了怎么办（2-3 个最常见报错的定位与修复）

### 模板 B：排查报错

```text
我运行命令：<粘贴命令>
报错：<粘贴完整 traceback 或日志片段>
环境：<CUDA/torch/transformers 版本；GPU 型号；是否离线>
目标：修到能跑通，并解释根因；补上必要的异常处理与提示信息
```

agent 输出必须包含：
- 根因（用 1-2 句话说清）
- 修复方案（最小改动优先）
- 我该运行的复现/验证命令
