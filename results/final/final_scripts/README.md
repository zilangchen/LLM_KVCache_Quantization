# 论文实验复现指南

## 环境要求

- NVIDIA H20 GPU (96GB HBM, sm_90) 或同等算力
- Python 3.12, PyTorch 2.8.0 (CUDA 12.8), Transformers, Triton
- 模型权重: Qwen2.5-{1.5B,7B,14B}-Instruct, LLaMA-3.1-8B-Instruct

## 目录结构

```
final_scripts/
├── reproduce/          按编号顺序的复现脚本（清晰命名）
├── configs/            实验配置文件
├── core/               核心工具（实验运行器、校准脚本）
├── eval/               评测脚本（PPL/Needle/RULER/LongBench/latency/memory）
├── plot/               论文绘图脚本
└── batch/              原始 batch_p012 脚本（开发时命名，供溯源）
```

## 复现步骤（按编号顺序执行）

| 脚本 | 产出数据 | 论文章节 | GPU 时间 |
|------|---------|---------|---------|
| `01_calibrate.sh` | artifacts/kv_calib_*.json | Ch3 校准 | ~1h/模型 |
| `02_int8_mainline.sh` | int8_mainline/ | Ch4 §4.2 (C1) | ~12-15h |
| `03_kv_ablation.sh` | kv_ablation/ | Ch4 §4.3 (C2 诊断) | ~8-10h |
| `04_int4_rolealign.sh` | int4_rolealign/ | Ch4 §4.4 (C2 实例化) | ~10-12h |
| `05_backend_tpot.sh` | backend_comparison/tpot_* | Ch4 §4.5.1 (C3 Phase 1) | ~3-4h |
| `06_14b_full.sh` | backend_comparison/{ppl,needle,ruler}_*_14b | Ch4 §4.4 (14B 外部效度) | ~6-8h |
| `07_longseq_tpot.sh` | backend_comparison/longseq_* | Ch4 §4.5.2-3 (C3 长序列) | ~4-6h |
| `08_8b_longseq.sh` | backend_comparison/longseq_*_8b | Ch4 §4.5.4 (Hkv 控制) | ~2h |
| `09_fp16_ruler_baseline.sh` | backend_comparison/ruler_fp16_* | Ch4 §4.4 (FP16 锚点) | ~3h |
| `10_7b_kl_vs_mse.sh` | backend_comparison/ppl_{kl,mse}_7b | Ch4 §4.2 (C1 规模依赖) | ~1h |

**总计约 50-60h GPU 时间（单卡串行）**

## 复现脚本 → 原始脚本映射

| reproduce/ | batch/ (原始开发命名) |
|------------|---------------------|
| 01_calibrate.sh | (新建，原散落在多处) |
| 02_int8_mainline.sh | (新建，原用 run_experiments.py 直接调用) |
| 03_kv_ablation.sh | scripts/archive/expansion_gpu0.sh + expansion_gpu1.sh |
| 04_int4_rolealign.sh | (新建，原用 exp_matrix_rolealign.yaml) |
| 05_backend_tpot.sh | stage1_phase1_rerun.sh + phase1_fix_8b_14b.sh |
| 06_14b_full.sh | stage5_phase4_14b_full.sh |
| 07_longseq_tpot.sh | stage7_rerun.sh |
| 08_8b_longseq.sh | stage_8b_longseq.sh |
| 09_fp16_ruler_baseline.sh | stage_baseline_fp16_ruler.sh |
| 10_7b_kl_vs_mse.sh | stage_c1_kl_vs_mse.sh |

## 数据产出 → 论文表映射

详见 `../final_data/INDEX.md`。

## 注意事项

- TPOT profiling (05/07/08) 需**独占 GPU**，不能与其他实验并行
- 质量评测 (02/03/04/06/09/10) 可以共享 GPU
- 所有脚本使用 greedy 解码 (temp=0, top_p=1, top_k=0)
- 14B RULER 最大测试到 16K（32K 因显存限制未测）
