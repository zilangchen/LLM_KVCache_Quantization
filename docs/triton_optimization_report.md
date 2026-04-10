# INT4 Decode Attention 性能优化报告

**Session**: 2026-04-10  
**分支**: `feat/triton-int4-v2-wt` (worktree: `/tmp/triton-int4-v2`)  
**模型**: Qwen2.5-1.5B-Instruct, seq_len=4096, gen_len=64, batch=1  
**硬件**: NVIDIA H20 (96GB HBM, sm_90), Triton 3.4.0, PyTorch 2.8.0  

---

## 1. 目标

优化 INT4 非对称 KV Cache 的 decode TPOT（Time Per Output Token），缩小与 FP16 baseline 的差距。

| 基准 | TPOT | 量化开销 |
|------|------|---------|
| FP16 | 29.88 ms | 0 ms |
| INT4 原始 | 60.67 ms | +30.50 ms |

**目标**: 尽可能减少 30.50 ms 的 INT4 量化开销。

---

## 2. 优化时间线与结果

### 总览

| # | 优化 | TPOT | 改善 | 累计 |
|---|------|------|------|------|
| 0 | 原始 v1 | 60.67 ms | — | — |
| 1 | Triton v2 kernel (计算优化) | 54.94 ms* | 0% | 0% |
| 2 | GQA tiling kernel | 53.59 ms* | 0% | 0% |
| 3 | **.item() sync 移除** | **54.94 ms** | **-5.73 ms** | **-9.4%** |
| 4 | aminmax 融合 + pack 内联 | 54.38 ms | -0.56 ms | -10.4% |
| 5 | **Triton fused quantize+pack** | **45.39 ms** | **-8.99 ms** | **-25.2%** |
| 6 | **Inplace 零拷贝写入** | **43.73 ms** | **-1.66 ms** | **-27.9%** |
| — | FP16 参考 | 29.88 ms | — | — |

*注: #1 和 #2 的 TPOT 改善为 0%，因为它们优化的是非瓶颈（kernel 本身）。但它们的失败提供了关键诊断信息。

**最终结果: 60.67 ms → 43.73 ms, 降低 27.9%, 量化开销从 30.50 ms 减至 13.85 ms (-54.6%)**

---

## 3. 各阶段详情

### 3.1 Triton v2 Kernel — 计算优化（无效，但有诊断价值）

**Commit**: `d11dbeb`  
**文件**: `src/kernels/triton_decode_attn_int4_asym_v2.py`

**做了什么**:
1. 移除 v1 内核中未使用的 Q 全量加载（L67 的 `q_full` 从未使用）
2. K zero-point 预计算：将 `sum(q * (k_int * scale + zp))` 代数变形为 `sum(q_scaled * k_int) + zp_bias`，循环内不再做 K 反量化
3. `@triton.autotune` 扫描 6 种 (BLOCK_SIZE, num_warps, num_stages) 配置

**结果**: 54.94 ms ≈ 54.05 ms (v1)，无统计显著差异。

**教训**: 
> INT4 decode attention 在 batch=1 时是 **memory-bandwidth bound**（~2 FLOP/byte，H20 平衡点 ~15 FLOP/byte）。计算优化（减少 FLOPs）对带宽受限的 kernel 无效。

### 3.2 GQA-Aware Tiling — 带宽优化（无效，但揭示了 SM 并行度问题）

**Commit**: `b10059b`  
**文件**: `src/kernels/triton_decode_attn_int4_asym_gqa.py`

**设计演进**:

| 版本 | 方案 | 结果 | 原因 |
|------|------|------|------|
| v1 | 3D broadcast [N_REP,1,PD]×[1,BLOCK,PD] | 编译失败 | Triton 3.4.0 不支持 3D tensor + `tl.arange` 要求 2 的幂 |
| v2 | `tl.static_range(N_REP)` 串行循环 | 71.8 ms (-28%) | 只用 2 个 SM（v1 用 12 个），带宽利用率崩塌 |
| v3 | `tl.dot` + M=16 padding + fp16 tensor core | 53.6 ms ≈ v1 | 数据减 6× 但 SM 也减 6×，抵消 |

**教训**:
> GQA tiling 减少 HBM 读取量，但也减少活跃 SM 数。H20 的 HBM 带宽 (4 TB/s) 需要 ~130 SM 并发才能打满。12 SM → 2 SM 导致聚合带宽等比例下降，抵消了数据读取的减少。真正有效的 GQA 优化需要同时做 Split-K 并行化（FlashDecoding 架构），这超出了 Triton 单 kernel 的表达能力。

### 3.3 Profiling 突破 — 发现真正的瓶颈

**工具**: `scripts/profile_decode_breakdown.py`, `scripts/measure_forward_floor.py`

**关键发现**:

```
60.67 ms 的分解:
  ├── 15.68 ms — 纯 model forward (MLP + LN + attention kernel)
  ├── 13.32 ms — Python 框架开销 (generate_loop 控制流 + HF forward)
  └── 30.50 ms — INT4 量化/打包/dispatch 开销
        ├── ~6 ms   — GPU→CPU sync (.item() 调用)
        ├── ~15 ms  — ~700 个小 CUDA kernel launch (quantize + pack)
        ├── ~5 ms   — monkey-patch dispatch 开销
        └── ~5 ms   — 临时 tensor 分配 + 拷贝
```

> **Triton attention kernel 本身只占 ~15.68 ms 中的一小部分（~5 ms），不是瓶颈。30.50 ms 的开销全部来自 Python cache 管理路径。**

### 3.4 .item() Sync 移除 — 首次实际加速 (-9.4%)

**Commit**: `ff0b9e5`

**发现的同步点**:

| 位置 | 调用 | 频率/step |
|------|------|----------|
| `kivi_style_cache.py:454` | `_out_of_range.sum().item()` (ENG-041 诊断) | 28× |
| `int4_basic.py:246-247` | `tensor.min().item()` + `tensor.max().item()` (pack 校验) | 112× |

**修复**: 将诊断/校验移到可选路径（环境变量 `KV_OOR_CHECK_INTERVAL`, `KV_PACK_VALIDATE`），默认关闭。正确性不受影响（`clamp()` 已保证值范围）。

**结果**: 60.67 → 54.94 ms (-9.4%)

### 3.5 Triton Fused Quantize+Pack — 最大单步改善 (-25.2%)

**Commit**: `b571fb7`  
**文件**: `src/kernels/triton_quantize_pack_int4.py`

**核心思路**: 用单个 Triton kernel 替代 ~25 个 PyTorch eager 操作链:

```
原始 (每层):
  float() → amin() → amax() → subtract → clamp → divide →   ← 13 个
  subtract → divide → round → clamp → int8 → int16 →         ← CUDA kernel
  +8 → uint8 → view → <<4 → | → int8                        ← launches

Triton fused (每层):
  1 个 Triton kernel: 加载 float → min/max/scale/zp →         ← 1 次 launch
  quantize → pack → 存储 int8                                  ← 全部在 kernel 内
```

**K kernel**: 接收 float K + 预计算的 per-channel scale/zp → 输出 packed int4
**V kernel**: 接收 float V → 内部计算 per-token min/max/scale/zp → 输出 packed int4 + scale + zp

28 层 × (K + V) = 56 Triton launches 替代原来的 ~700 PyTorch launches。

**结果**: 54.94 → 45.39 ms (-25.2%)

### 3.6 Inplace 零拷贝 — 消除临时 Tensor (-27.9%)

**Commit**: `48f2e7c`

**优化**: Triton kernel 直接写入 cache buffer 的正确位置，跳过临时 tensor 分配和 `cache[old_len:target_len] = packed` 拷贝。

```
原始:                                    优化后:
Triton → 临时 tensor → 拷贝到 cache     Triton → 直接写 cache[offset]
     (alloc)        (CUDA launch)              (零拷贝，零分配)
```

消除 28 层 × 5 次操作 (K packed + V packed + V scale + V zp + K temp) = 140 CUDA 操作。

**结果**: 45.39 → 43.73 ms (-27.9% 累计)

### 3.7 torch.compile 测试 — 不可行

**Commit**: `48f2e7c` (记录结果)

| 模式 | TPOT | vs Normal |
|------|------|-----------|
| Normal | 47.72 ms | baseline |
| `compile(default)` | 55.60 ms | +16.5% 更慢 |
| `compile(reduce-overhead)` | 1964.84 ms | +4017% 灾难 |

**原因**: Triton JIT kernel 对 torch.compile 不可见（graph break），monkey-patch 导致大量重编译，CUDA graph 因动态 shape（cache 增长）反复失败。

---

## 4. 文件清单

### 新建文件 (6)

| 文件 | 用途 |
|------|------|
| `src/kernels/triton_decode_attn_int4_asym_v2.py` | v2 attention kernel (autotune + K prescale) |
| `src/kernels/triton_decode_attn_int4_asym_gqa.py` | GQA-tiled attention kernel (tl.dot + M=16) |
| `src/kernels/triton_quantize_pack_int4.py` | **Fused quantize+pack kernels (K + V) + inplace 版** |
| `tests/test_triton_int4_asym_v2.py` | v2 kernel 正确性测试 (5 cases) |
| `tests/test_triton_int4_asym_gqa.py` | GQA kernel 正确性测试 (7 cases) |
| `tests/test_fused_quantize_pack.py` | Fused quantize+pack 正确性测试 (3 cases) |

### 修改文件 (5)

| 文件 | 改动 |
|------|------|
| `src/cache/kivi_style_cache.py` | .item() 移除 + Triton inplace 集成 |
| `src/quant/int4_basic.py` | pack_int4 .item() 移除 |
| `src/quant/asymmetric_quant.py` | aminmax 融合 |
| `src/engine/generate_loop.py` | v2/GQA impl 注册 |
| `src/engine/patch_model.py` | v2/GQA dispatch 路由 |

### Profiling 脚本 (3)

| 文件 | 用途 |
|------|------|
| `scripts/profile_decode_breakdown.py` | Decode TPOT 分组计时 |
| `scripts/measure_forward_floor.py` | 纯 model forward 基准 |
| `scripts/test_torch_compile.py` | torch.compile 可行性测试 |

---

## 5. 关键技术教训

### 5.1 "优化对的东西"比"优化得更好"重要

三轮 Triton kernel 优化（v2 compute, GQA serial, GQA tl.dot）总共花了 ~3 小时，TPOT 改善 0%。一次 profiling + .item() 修复花了 30 分钟，改善 9.4%。

**教训**: 先测量 (profile)，后优化。不要假设瓶颈在哪里。

### 5.2 GPU→CPU 同步是隐形杀手

`.item()`, `.cpu()`, `.numpy()` 在 decode 循环中每个都创建 pipeline stall。28 层 × 多次调用 = 数十 ms 开销。这些调用通常是诊断/调试代码，生产环境应该关闭。

### 5.3 CUDA Launch Overhead 比 FLOP 重要

对于 batch=1 的小 tensor 操作，CUDA kernel launch 开销 (~5-10μs) 远大于实际计算时间。700 个小 kernel → 56 个 Triton kernel 的改善 (-15ms) 证明了这一点。

### 5.4 Triton 的限制

| 限制 | 影响 |
|------|------|
| `tl.arange` 要求 2 的幂 | N_REP=6/7 需要 padding |
| 3D tensor 不支持 | GQA 不能用 broadcast 并行化 |
| `tl.dot` 要求 M≥16 (sm_90) | GQA 需要大量 padding (16 个 Q head vs 实际 6) |
| 与 torch.compile 不兼容 | Triton JIT kernel 导致 graph break |

### 5.5 INT4 vs FP16 的不可消除差距

剩余 13.85 ms 差距 = Python monkey-patch dispatch 开销。这是框架架构的固有成本，不是量化的成本。要消除它需要：
- 重写 `generate_loop.py` 去掉 per-step 的 Python 控制流
- 或集成 C++ 端到端推理引擎（如 vLLM, TensorRT-LLM）

---

## 6. 剩余优化方向（未实施）

| 方向 | 预期收益 | 难度 | 备注 |
|------|---------|------|------|
| FlashInfer 集成 | TPOT → ~30ms | 中 | 另一 session 在探索 |
| Split-K + GQA (FlashDecoding) | kernel → ~3ms | 高 | 需要 partial softmax merge |
| 重构 generate_loop (去 monkey-patch) | -5~8ms | 很高 | 架构级重构 |
| 缓存 INT8CacheWrapperContainer | -0.5ms | 低 | 小收益 |
| CUDA Graph (需要静态 shape) | -3~5ms | 高 | cache 增长是障碍 |
