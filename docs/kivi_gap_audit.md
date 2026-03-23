# KIVI Gap Audit — 本项目 kivi_style 实现 vs KIVI 原论文

**日期**: 2026-03-24
**目的**: 诚实记录本项目 kivi_style baseline 与 KIVI (Liu et al., 2024) 原论文的实现差异，
为论文写作和后续 ours_asym 设计提供参考。

---

## 1. 已实现的 KIVI 核心特性 ✅

| 特性 | KIVI 原论文 | 本项目实现 | 验证状态 |
|------|------------|-----------|---------|
| **K: per-channel 非对称量化** | 沿 seq_len 聚合 absmax/min → 每通道独立 scale/zp | `quantize_asymmetric_per_channel()` in `src/quant/asymmetric_quant.py` | ✅ 测试通过 |
| **V: per-token 非对称量化** | 沿 head_dim 聚合 → 每 token 独立 scale/zp | `quantize_asymmetric_per_token()` | ✅ 测试通过 |
| **K scale prefill 静态复用** | prefill 一次计算，decode 复用 | `_k_scale_initialized` flag in `kivi_style_cache.py` L312-319 | ✅ |
| **V scale 逐 token 动态** | 每 append 独立计算 | `quantize_asymmetric_per_token()` per-call in L362 | ✅ |
| **INT4 bit-packing** | 2 值/字节存储 | `pack_int4()` / `unpack_int4()` in `src/quant/int4_basic.py` | ✅ |
| **Percentile 裁剪** | clip outlier 控制 scale | `k_percentile` / `v_percentile` 参数 | ✅ |
| **Zero-point** | 非对称量化需要 zp | float32 存储，per-channel K / per-token V | ✅ |
| **GQA 支持** | 多 Q 头共享 KV 头 | 通过 `patch_model.py` 中的 GQA 映射 | ✅ |

## 2. 未实现的 KIVI 原论文特性 ❌

### 2.1 残差缓冲区（Residual Buffer）— **可能影响质量**

KIVI 原论文提到可选的残差缓冲机制：保留最近 N 个 token 的 FP16 KV，
仅对较旧的 token 执行量化。这提供了一个"热区"缓冲，
减少最近 token 的量化误差对注意力的影响。

**本项目**: 全量量化，无残差缓冲。所有 token 在 append 时立即量化。

**影响评估**: 残差缓冲主要改善 decode 阶段最近 token 的精度，
对长距离检索任务（如 Needle）影响较小，但可能改善 PPL 等全局指标。
**不影响本轮实验设计**——我们的 KIVI baseline 是保守估计。

### 2.2 Decode K Scale 自适应更新 — **已知风险已记录**

KIVI 原论文 §3.2 讨论了 decode 阶段 K scale 的可选更新机制。

**本项目**: K scale 在 prefill 后冻结，decode token 若超出 prefill scale 范围
则被静默截断（`kivi_style_cache.py` L342-356, ENG-041）。
仅在截断率 >5% 时发出运行时警告。

**影响评估**: 长序列中 K 分布漂移可能导致注意力精度降低。
已记录为已知风险（ENG-041），在当前 32K 评测中未观察到显著退化。

### 2.3 异步量化 Pipeline — **仅影响效率**

KIVI 原论文提到异步解码-量化流水线，可隐藏量化延迟。

**本项目**: 同步顺序处理。

**影响评估**: 仅影响推理延迟（TPOT），不影响量化质量。
论文中 KIVI-style 的 TPOT 对比应注明此差异。
**已在 ch4 KIVI 对比节声明**。

### 2.4 Token 分级存储 — **可能影响质量**

部分 KIVI 变体支持基于注意力权重的 token 重要性评分，
为高重要性 token 保留更高精度。

**本项目**: 统一精度，无 token 分级。

**影响评估**: 分级存储本质上类似 ZipCache 的混合精度策略，
与本文的均匀量化设计目标不同。不影响核心对比结论。

### 2.5 逐层策略差异化 — **未实现但影响小**

KIVI 原论文允许不同层使用不同量化粒度。

**本项目**: 全网络统一 KIVI 参数（k_percentile, v_percentile）。

**影响评估**: 统一参数是保守选择，可能略低估 KIVI 在逐层优化下的潜力。

## 3. 额外实现（超出原论文）

| 特性 | 说明 |
|------|------|
| **int4_kivi_aligned** | KIVI INT4 + 行为对齐 inv_tau Q 预缩放（本项目扩展） |
| **V-path BA 校准** | 通过 calibrate_behavior.py 为 V 搜索最优 percentile（扩展） |
| **ENG-041 截断警告** | decode K 截断率监控（原论文无此机制） |
| **Float32 scale 强制** | ENG-009: scale/zp 强制 float32 存储（精度保障） |

## 4. 本轮实验的影响评估

对于 ours_asym 与 kivi_style 的对比实验：

- **质量对比是公平的**: 两者使用相同的 generate_loop 框架、相同的 torch_ref decode 路径
- **KIVI baseline 是保守估计**: 缺少残差缓冲和分级存储意味着完整 KIVI 可能更优
- **效率对比需注明**: 两者都不使用 Triton 融合，TPOT 差异仅来自量化轴设计
- **如果 ours_asym_ba > kivi_style**: 结论更强（即便面对不完整的 KIVI 都能赢）
- **如果 ours_asym_ba ≈ kivi_style**: 需要更谨慎的措辞

## 5. 论文声明建议

在 ch4 KIVI 对比节（已有）和新增的 ours_asym 实验节中应包含：

> 本文的 KIVI-style baseline 采用 KIVI 的核心量化轴策略
> （per-channel K + per-token V 非对称量化），
> 但不包含原论文中的残差缓冲区、异步量化流水线和 token 分级存储等
> 工程优化，因此本文的 KIVI-style 实验结果应理解为
> 对 KIVI 核心算法思想的验证，而非完整系统性能的严格复现。

---

## 文件索引

| 文件 | 内容 |
|------|------|
| `src/cache/kivi_style_cache.py` | KIVI 缓存完整实现 |
| `src/quant/asymmetric_quant.py` | 非对称量化函数 |
| `src/engine/generate_loop.py` L414-522 | KIVI 路由逻辑 |
| `src/engine/patch_model.py` L821-903 | KIVI 缓存创建 + inv_tau hook |
| `configs/snapshots/exp_matrix_kivi_aligned_v1.yaml` | KIVI INT4 实验配置 |
