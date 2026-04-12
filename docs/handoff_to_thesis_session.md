# 跨 Session 交接报告：论文叙事升级

**日期**: 2026-04-12 14:34
**发送方**: 实验协调 Session（本 session 做了 250+ 实验 + bug 修复 + 叙事分析）
**接收方**: 论文写作 Session（你的任务：执行 Option D 论文重构）
**仓库**: main 分支，最新 commit `b14bc31`

---

## TL;DR — 你需要知道什么

1. **所有实验数据已全部跑完**（250+ 数据点），GPU 空闲，不需要再跑任何东西
2. **论文叙事方向已确定**：Option D "GQA 中心叙事"——以 $H_{kv}$ 为核心变量重构论文
3. **详细实施计划在** `docs/option_d_plan.md`（~350 行，含每章修改点 + LaTeX 建议文本）
4. **关键发现汇总在** `docs/session_findings_2026-04-12.md`（~600 行，16 Parts，含所有数据表）
5. **代码修复已完成**：v_percentile bug 修复 + BD adapter 删除 + dispatch 清理

---

## 一、仓库当前状态

### Git

```
最新 commit: b14bc31 (main, origin/main)
分支: main (只有这一个活跃分支)

关键 commits (时间倒序):
b14bc31 feat: complete INT4 backend pipeline — 250+ experiments, BD removal
b6ee998 fix(bd-adapter): revert to Layout A
df80ed8 Merge remote-tracking branch 'origin/main'
93bc1ee docs: handoff report for other sessions — Phase 1 fix verified
ecc6f5f perf(cache): in-kernel percentile via top-2/bottom-2 — triton_ra -31% TPOT
5c5ec27 fix(cache): Triton V kernel now handles v_percentile<100
```

### 代码变更摘要

| 类别 | 文件 | 状态 |
|------|------|------|
| **删除** | `src/kernels/adapters/bitdecoding_adapter.py` | BD adapter (GQA bug) 已删 |
| **修改** | `src/engine/patch_model.py` | BD dispatch 分支删除 |
| **修改** | `src/engine/generate_loop.py` | "bitdecoding" 从 _valid_impls 删除 |
| **修改** (other session) | `src/cache/kivi_style_cache.py` | v_percentile 守卫修复 (in-kernel percentile) |
| **修改** (other session) | `src/kernels/triton_quantize_pack_int4.py` | top-2/bottom-2 fused kernel |
| **保留** | `scripts/tpot_bitdecoding_e2e.py` | BD standalone TPOT reference (24.22 ms) |
| **保留** | `scripts/test_bitdecoding.py` | BD bug 证据 (max_diff=1.23 FAIL) |

### 远端服务器

- SSH: `ssh -p 31867 root@region-42.seetacloud.com` (密码见 `docs/autodl_server.md`)
- GPU: H20 96GB, **当前完全空闲**
- 项目路径: `/root/LLM_KVCache_Quantization`
- 远端代码和本地 main **md5 一致**（已验证 3 个核心文件）
- 注意：远端 git 状态是脏的（rsync 部署，不通过 git），但文件内容是最新的

---

## 二、实验数据全景

### 数据位置

所有实验结果在远端 `/root/LLM_KVCache_Quantization/results/emnlp_p012_batch/runs/`

### 数据完整性

| 类别 | 目录前缀 | 测试数 | 状态 | 关键结果 |
|------|---------|--------|------|---------|
| **Phase 1 TPOT** (4K, 4模型×6backend) | `tpot_*` | 24 | ✅ | triton_ra crossover at 8B |
| **Phase 2 BD 1.5B quality** | `{ppl,needle,ruler,longbench}_bd_1p5b_*` | 39 | ⚠️ 废弃 | BD broken (GQA bug) |
| **Phase 3 FI 1.5B quality** | `{ppl,needle,ruler,longbench}_fi_1p5b_*` | 39 | ✅ | FI ≈ FP16 on RULER (<1%) |
| **Phase 4 14B full** | `{ppl,needle,ruler,longbench}_*_14b_*` + `ppl_ablation_*_14b_*` | 70 | ✅ | RULER 98.5%, K恢复93% |
| **Phase 5 7B/8B misc** | `memory_{7b,8b}_*` | 8 | ✅ | Memory sweep data |
| **Stage 7 Long-seq** (v2 rerun) | `longseq_*` | 48 | ✅ | 14B 32K triton 快 40% |
| **1.5B fp16 RULER baseline** | `ruler_fp16_1p5b_*` | 12 | ✅ | VT/CWE 低是模型限制 |
| **14B fp16 RULER baseline** | `ruler_fp16_14b_*` | 9 | ✅ | 对照组 |
| **C1 KL vs MSE 7B** | `ppl_{kl,mse}_7b_*` + `needle_{kl,mse}_7b_*` + `ppl_fp16_7b_*` | 13 | ✅ | KL=MSE趋同 (7B) |
| BD standalone TPOT | `tpot_bd_standalone_1p5b` | 1 | ✅ | 24.22 ms reference |
| **总计** | — | **~260** | — | — |

### 聚合分析脚本

```bash
# 远端运行，输出 markdown 格式的全数据分析
cd /root/LLM_KVCache_Quantization
python3 scripts/batch_p012/analyze_current.py
# 输出也保存在: results/emnlp_p012_batch/analysis_full.md
```

---

## 三、核心发现（5 条）

### Finding 1: 校准目标有效性的规模依赖

| 模型 | KL percentile | MSE percentile | PPL(KL) | PPL(MSE) |
|------|--------------|----------------|---------|----------|
| 1.5B (Hkv=2) | 99.5 | 99.0 | 不同 | 不同 |
| **7B (Hkv=4)** | **100.0** | **100.0** | **7.1121** | **7.1121** |

**解读**: 小模型 KL≠MSE（KL 更优），大模型趋同。KL 是 universally safe choice。

### Finding 2: K 主导退化（跨规模验证）

| Model | K16V4 PPL | K4V16 PPL | Full INT4 | K 恢复 |
|-------|-----------|-----------|-----------|--------|
| 1.5B | — | — | 9.63 | — |
| **14B** | **4.709** | **4.813** | **5.040** | **93%** |

### Finding 3: RoleAlign 质量保持

| 模型 | Needle (32K) | RULER (4K) | PPL 退化 |
|------|-------------|-----------|----------|
| 1.5B | 100% | 60.2% (FP16=60.3%) | 13.7% |
| **14B** | **100%** | **98.5%** | **7.6%** |

### Finding 4: Phase Boundary $(H_{kv}, \text{seq\_len})$

**triton_ra vs torchref 的 Δ(ms)**:

| Model (Hkv) | 4K | 8K | 16K | 32K |
|-------------|-----|-----|-----|------|
| 1.5B (Hkv=2) | +1.67 | +4.23 | +9.78 | **+15.92** |
| 7B (Hkv=4) | +1.03 | +1.56 | +0.55 | **-4.90 (-7%)** |
| **14B (Hkv=8)** | -0.44 | **-14.54** | **-33.26** | **-77.08 (-40%)** |

**Phase Boundary 理论**: Triton kernel grid=(B, Hkv)，SM 利用率 ∝ Hkv/130。
Hkv=2 → 1.5% SM → 始终输。Hkv=8 → 6% SM + 4x bandwidth saving → 长序列大赢。

### Finding 5: BitDecoding GQA Bug

- bit_decode v1.0.0.post1 自带 test: max_diff=1.23, **FAIL** (阈值 0.1)
- 所有长生成评测: Needle 0%, RULER 1%, LongBench F1=0
- **lesson**: single-shot cosine (0.99) 是 insufficient validation

---

## 四、Phase 1 完整 TPOT 表 (论文核心数据)

seq=4096, gen=128, batch=1, warmup=3, runs=8

| backend | 1.5B | 7B | 8B | 14B |
|---------|------|-----|-----|------|
| **fp16** | 24.36 ± 0.07 | 24.82 ± 0.06 | 28.55 ± 0.34 | 42.58 ± 0.19 |
| **torchref** | 36.35 ± 0.30 | 37.61 ± 0.07 | 44.88 ± 0.17 | 68.07 ± 0.71 |
| **kivi** | 36.39 ± 0.49 | 37.41 ± 0.58 | 44.70 ± 0.22 | 68.46 ± 0.27 |
| **triton_ra** | 38.68 ± 0.29 | 38.76 ± 0.09 | **44.49 ± 0.54** | **67.67 ± 1.19** |
| fi | 43.73 ± 0.22 | 47.07 ± 0.89 | 51.50 ± 0.92 | 85.07 ± 0.42 |

KV cache: fp16 115-792 MB → INT4 31-211 MB (73.4% 压缩)

---

## 五、长序列 TPOT 表 (论文核心数据)

gen=64, runs=10, warmup=5, **数据稳定 (std < 1.5 ms)**

### 14B (最重要)

| seq | fp16 | kivi | torchref | **triton_ra** |
|-----|------|------|----------|------------|
| 4K | 42.28 | 68.07 | 68.17 | **67.73** |
| 8K | 42.81 | 86.02 | 86.08 | **71.53** |
| 16K | 42.64 | 121.49 | 119.83 | **86.56** |
| 32K | 43.13 | 187.82 | 190.23 | **113.16** |

### 7B

| seq | torchref | triton_ra | Δ |
|-----|----------|-----------|---|
| 4K | 37.15 | 38.18 | +1.03 |
| 8K | 39.56 | 41.11 | +1.56 |
| 16K | 49.10 | 49.66 | +0.55 |
| 32K | 69.67 | **64.77** | **-4.90** |

### 1.5B

| seq | torchref | triton_ra | Δ |
|-----|----------|-----------|---|
| 4K | 36.44 | 38.11 | +1.67 |
| 32K | 48.94 | 64.86 | +15.92 |

---

## 六、论文叙事方向已确定：Option D

### 核心转型

**原定位**: "KV Cache 量化框架 + 发现"
**新定位**: "**GQA 架构下的 INT4 量化行为研究**"

**核心 message**: GQA 的 $H_{kv}$ 是 INT4 量化行为的核心架构变量——决定校准灵敏度、Key 退化幅度、kernel 效率 crossover 和温度校正方向。

### 新 Contributions (5 条)

| # | 标题 | 核心数据 |
|---|------|---------|
| C1 | 校准目标的 bit-width 与规模双依赖 | 1.5B KL≠MSE, 7B KL=MSE |
| C2 | Key 主导退化 + GQA 架构依赖 | 14B K 恢复 93%, V 恢复 64% |
| C3 | RoleAlign 跨模型规模验证 | 14B RULER 98.5%, 1.5B FI≈FP16 |
| **C4** | **GQA 架构效应: inv_tau + Phase Boundary + in-kernel pct** | **14B 32K triton 快 40%, Phase Boundary 二维图** |
| **C5** | **大模型验证 + BD 外部系统局限** | **BD GQA bug, 14B 32K Needle 100%** |

### 为什么 Option D 可行？

**论文已经有 40+ 处 GQA 讨论**散落在 Ch1/Ch2/Ch3：
- Ch1 L136: "不同 GQA 头数 $H_{kv}$ 对量化容忍度有何影响？" ← **已是研究问题**
- Ch2 L454: "本文是首个系统报告 $\tau^{-1}$ 与 GQA 头数的相互作用" ← **已声称首创**
- Ch3 L883: 独立的 "GQA 支持机制" subsection ← **已有架构讨论**

Option D 不是"生搬硬套 GQA"，而是**把已有的 GQA 线索从 supporting dimension 提升为 primary narrative**。

---

## 七、你的任务

### 必读文档

1. **`docs/option_d_plan.md`** — 详细实施计划（~350 行）
   - 每章具体修改点（含行号）
   - 完整的 LaTeX 建议文本（可直接复制）
   - 新 Ch4 section 结构
   - 新增 Tables/Figures 清单
   - 工作量评估 (~5.5 天)
   - 风险 checklist

2. **`docs/session_findings_2026-04-12.md`** — 本 session 所有发现（~600 行）
   - 16 Parts，含所有数据表
   - Bug 深度诊断（v_percentile + BD）
   - 开发纪律教训

3. **`docs/handoff_report_2026-04-11.md`** — Session 1 的 Triton 优化报告
   - 4 个 commit 的优化时间线
   - in-kernel percentile 方法细节
   - 修复后 Phase 1 数据

### 执行顺序建议

```
Day 1: Ch1 (RQ + Contributions + 核心主张) + Abstract
Day 2: Ch3 (KL 规模依赖 + Phase Boundary 理论 + in-kernel pct) + Ch2 gap 声明
Day 3-4: Ch4 重写 (新 section 结构 + 所有 Tables + Figures)
Day 5: Ch5 Findings + 全文校对 + 交叉引用
Day 5.5: 编译 + 格式 + 页数
```

### 关键约束

- **不需要再跑任何实验**——250+ 数据点已全部就绪
- **不修改 src/ 代码**——代码层面修复已完成
- **论文在 `thesis/chapters/` 下**——5 个 .tex 文件
- **编译命令**: `cd thesis && xelatex -interaction=nonstopmode main.tex`
- **当前论文约 96 页**——目标 ≤ 120 页

### 你需要的数据获取方式

```bash
# 远端运行聚合分析（最新数据）
ssh -p 31867 root@region-42.seetacloud.com
cd /root/LLM_KVCache_Quantization
python3 scripts/batch_p012/analyze_current.py > results/emnlp_p012_batch/analysis_full.md
cat results/emnlp_p012_batch/analysis_full.md

# 或者本地读已有的 findings 文档
cat docs/session_findings_2026-04-12.md
```

---

## 八、不要碰的东西

| 文件 | 原因 |
|------|------|
| `CLAUDE.md` | 只读，不可修改 |
| `experiment_sop.md` | 只读 |
| `src/` 下所有 .py | 代码修复已完成，不需要改 |
| `results/emnlp_p012_batch/runs/_archive_*` | 旧数据归档，不要删 |
| `artifacts/kv_calib_*.json` | 校准产物，frozen |

---

## 九、论文现有 Contribution 位置速查

| Contribution | Ch1 声明 | Ch3 方法 | Ch4 实验 |
|-------------|---------|---------|---------|
| C1 KL vs MSE | L149-158 | L202-280 (KL 目标) | L289-396 (对比实验) |
| C2 Key 主导 | L160-170 | L611-646 (RoleAlign) | L903-963 (诊断) |
| C3 RoleAlign | L172-184 | L648-753 (BA percentile) | L1231-1428 (结果) |
| C4 inv_tau (原观察) | L186-196 | L395-466 (GQA 尺度) | L1429-1515 (消融) |
| C4 Phase Boundary (新) | 需新增 | 需新增 subsection | 需新增 section |
| C5 BD limitation (新) | 需新增 | — | 需新增 section |

---

_最后更新: 2026-04-12 14:34_
_状态: 所有实验完成, 论文方向确定, 待新 session 执行 Option D_
