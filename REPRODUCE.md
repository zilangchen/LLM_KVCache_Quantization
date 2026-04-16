# 论文实验复现指南（主线 subset 冻结入口）

本文件为 LLM_KVCache_Quantization 仓库的主线实验复现入口。
冻结日期：2026-04-17。完整数据与冻结脚本位于：

- **数据入口**：`results/final/final_data/INDEX.md`
- **脚本入口**：`results/final/final_scripts/reproduce/`
- **详细脚本说明**：`results/final/final_scripts/README.md`

---

## 快速开始（minimal one-click）

### 环境要求

- NVIDIA H20 GPU (96~GB HBM, sm\_90) 或同等算力
- Python 3.12, PyTorch 2.8.0 (CUDA 12.8), Transformers, Triton
- 模型权重：Qwen/Qwen2.5-{1.5B,7B,14B}-Instruct, meta-llama/Meta-Llama-3.1-8B-Instruct

### 执行

```bash
cd /path/to/LLM_KVCache_Quantization
bash results/final/final_scripts/reproduce/01_calibrate.sh         # 校准（约 1h/模型）
bash results/final/final_scripts/reproduce/02_int8_mainline.sh     # Ch4 §4.2 主线（12--15h）
bash results/final/final_scripts/reproduce/03_kv_ablation.sh       # Ch4 §4.3 诊断（8--10h）
bash results/final/final_scripts/reproduce/04_int4_rolealign.sh    # Ch4 §4.4 RoleAlign（10--12h）
bash results/final/final_scripts/reproduce/05_backend_tpot.sh      # Ch4 §4.5.1 Phase 1 TPOT（3--4h）
bash results/final/final_scripts/reproduce/06_14b_full.sh          # Ch4 §4.4 14B 外部效度（6--8h）
bash results/final/final_scripts/reproduce/07_longseq_tpot.sh      # Ch4 §4.5.2--3 长序列 TPOT（4--6h）
bash results/final/final_scripts/reproduce/08_8b_longseq.sh        # Ch4 §4.5.4 H_kv 控制（2h）
bash results/final/final_scripts/reproduce/09_fp16_ruler_baseline.sh  # Ch4 §4.4 FP16 RULER 锚点（3h）
bash results/final/final_scripts/reproduce/10_7b_kl_vs_mse.sh      # Ch4 §4.2 7B KL=MSE 趋同（1h）
```

总计约 50--60~h GPU 时间（单 H20 串行）。

---

## 复现覆盖范围与限制

### 属于冻结主线 subset（上述 10 个脚本覆盖）

- Ch4 §4.2 校准目标 bit-width 与规模依赖（C1）
- Ch4 §4.3 K/V 消融诊断（C2 诊断）
- Ch4 §4.4 INT4-RoleAlign + 14B 外部效度（C2 实例化 + 外部效度锚点）
- Ch4 §4.5.1--4 Phase 1/长序列 TPOT + H\_kv=8 控制对比（C3）
- 附录 tab:app-7b-kl-mse（7B KL=MSE 趋同）

### 不在复现 subset 中（数据冻结，但不由 reproduce/ 脚本生成）

- **BitDecoding 工程案例**（`*_bd_*` 系列 runs）——Ch4 §4.8 BitDecoding 讨论使用，
  依赖外部 CUTLASS 库特定版本与 NVFP4 数值格式，不保证可复现
- **LongBench official v2**（`longbench_official_*` 系列）——仅作 EVL-042 bug 修复验证，
  论文主结果使用自研 LongBench-style 合成评测
- **v3\_quick 校准 N=128 与实际实参的差异**——
  论文正文引用 N=128 作为校准样本规模；
  实际 `01_calibrate.sh` 执行的校准样本数为 INT8=16、INT4=32、RoleAlign=16；
  这一差异经 B10 敏感性消融（`kv_ablation/runs/int8_ours_b10_s{16,64,256}_*_exp_b10_*`）
  确认对结果不敏感（详见 Ch4 §4.2 校准样本数量敏感性分析与附录 tab:b10-sensitivity）。

### 执行契约说明

- `reproduce/*.sh` 是**冻结编排入口**，固定 `run_tag` 与输出目录层级，
  输出落在 `results/final/final_data/*/runs/` 下
- 这些脚本**非独立 runtime bundle**：仍依赖仓库根目录 `scripts/*` 作为真实 runner
  （`final_scripts/core|eval|configs` 为审计快照）
- 生成的输出**不承诺**与历史冻结目录（如 `emnlp_defense_v1/`、`emnlp_rolealign_v2/`）
  逐个同名；跨目录一致性由 `results/final/final_data/INDEX.md` 维护

---

## 数据一致性验证

复现产物可与 `results/final/final_data/` 下冻结 CSV 逐字节校验：

```bash
diff -r results/final/final_data/int8_mainline/runs/<tag>/ \
       <重新生成后的对应目录>/
```

在相同硬件（NVIDIA H20）与软件栈（PyTorch 2.8.0 + CUDA 12.8 + 相同模型权重）下，
PPL/Needle 数值在 greedy 解码 + 固定 seed 条件下位级可重现；
TPOT 数值受 GPU 负载轻微影响，典型方差 $<$2\%。

---

## 审计与故障排查

- 冻结脚本与原始开发脚本的映射见 `results/final/final_scripts/README.md` §复现脚本→原始脚本映射
- 完整数据索引（论文每张表/图 → 对应 CSV 路径）见 `results/final/final_data/INDEX.md`
- 实验 SOP 与命名规范见仓库根目录 `experiment_sop.md`
