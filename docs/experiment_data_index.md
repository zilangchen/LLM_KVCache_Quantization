# 实验数据索引 — 唯一权威入口

**最后更新**: 2026-04-12 15:00
**维护者**: 实验协调 Session
**总数据点**: ~270+（含 8B 长序列补跑 16 测试正在进行）

> **所有 session 查找实验数据请先读本文件。**
> 不要去 `emnlp_*/` 历史目录考古。

---

## 一、远端服务器信息

```
SSH: ssh -p 31867 root@region-42.seetacloud.com
密码: 见 docs/autodl_server.md
项目: /root/LLM_KVCache_Quantization
GPU:  NVIDIA H20 96GB (sm_90)
```

## 二、数据根目录

```
/root/LLM_KVCache_Quantization/results/emnlp_p012_batch/runs/
```

**本地没有这些数据**（results/ 在 .gitignore）。必须 SSH 到远端访问。

---

## 三、聚合分析命令

```bash
# SSH 到远端后执行：
cd /root/LLM_KVCache_Quantization
python3 scripts/batch_p012/analyze_current.py

# 输出保存到：
results/emnlp_p012_batch/analysis_full.md
```

脚本覆盖：Phase 1 TPOT + BD/FI quality + 14B quality + K/V ablation + 
fp16 RULER baseline + 长序列 scaling + memory sweep。

---

## 四、实验数据分类清单

### 4.1 Phase 1: TPOT 短序列 (seq=4096)

**实验设置**: gen=128, batch=1, warmup=3, runs=8, seed=1234

| 目录前缀 | 模型 | Backend | 状态 | TPOT (ms) |
|---------|------|---------|------|-----------|
| `tpot_fp16_1p5b` | 1.5B | FP16 | ✅ | 24.36 ± 0.07 |
| `tpot_fp16_7b` | 7B | FP16 | ✅ | 24.82 ± 0.06 |
| `tpot_fp16_8b` | 8B | FP16 | ✅ | 28.55 ± 0.34 |
| `tpot_fp16_14b` | 14B | FP16 | ✅ | 42.58 ± 0.19 |
| `tpot_kivi_1p5b` | 1.5B | KIVI INT4 | ✅ | 36.39 ± 0.49 |
| `tpot_kivi_7b` | 7B | KIVI INT4 | ✅ | 37.41 ± 0.58 |
| `tpot_kivi_8b` | 8B | KIVI INT4 | ✅ | 44.70 ± 0.22 |
| `tpot_kivi_14b` | 14B | KIVI INT4 | ✅ | 68.46 ± 0.27 |
| `tpot_torchref_1p5b` | 1.5B | INT4-RA torch_ref | ✅ | 36.35 ± 0.30 |
| `tpot_torchref_7b` | 7B | INT4-RA torch_ref | ✅ | 37.61 ± 0.07 |
| `tpot_torchref_8b` | 8B | INT4-RA torch_ref | ✅ | 44.88 ± 0.17 |
| `tpot_torchref_14b` | 14B | INT4-RA torch_ref | ✅ | 68.07 ± 0.71 |
| `tpot_triton_ra_1p5b` | 1.5B | INT4-RA Triton | ✅ | 38.68 ± 0.29 |
| `tpot_triton_ra_7b` | 7B | INT4-RA Triton | ✅ | 38.76 ± 0.09 |
| `tpot_triton_ra_8b` | 8B | INT4-RA Triton | ✅ | 44.49 ± 0.54 |
| `tpot_triton_ra_14b` | 14B | INT4-RA Triton | ✅ | 67.67 ± 1.19 |
| `tpot_fi_1p5b` | 1.5B | INT4-RA FlashInfer | ✅ | 43.73 ± 0.22 |
| `tpot_fi_7b` | 7B | INT4-RA FlashInfer | ✅ | 47.07 ± 0.89 |
| `tpot_fi_8b` | 8B | INT4-RA FlashInfer | ✅ | 51.50 ± 0.92 |
| `tpot_fi_14b` | 14B | INT4-RA FlashInfer | ✅ | 85.07 ± 0.42 |
| `tpot_bd_1p5b` | 1.5B | BD adapter (废弃) | ⚠️ | 46.37 (BD GQA bug) |
| `tpot_bd_7b` | 7B | BD adapter (废弃) | ⚠️ | 47.23 (BD GQA bug) |
| `tpot_bd_8b` | 8B | BD adapter (废弃) | ⚠️ | 54.09 (BD GQA bug) |
| `tpot_bd_14b` | 14B | BD adapter (废弃) | ⚠️ | 82.04 (BD GQA bug) |
| `tpot_bd_standalone_1p5b` | 1.5B | BD standalone | ✅ | 24.22 (BD 自己的量化) |

**注意**: `tpot_bd_*` (非 standalone) 的数据基于已删除的 BD adapter，输出不正确。只有 standalone 有效。

**CSV 字段**: `tpot_ms`, `ttft_ms`, `gpu_mem_peak_mb`, `kv_cache_mem_mb`, `model_id`, `kv_mode`, `seed`

### 4.2 长序列 TPOT Scaling (Stage 7 Rerun v2)

**实验设置**: gen=64, batch=1, warmup=5, runs=10, seed=1234

| 目录前缀 | 模型 | seq_len 范围 | Backend 列表 | 状态 |
|---------|------|------------|------------|------|
| `longseq_fp16_{model}_s{seq}` | 1.5B/7B/14B | 4096-32704 | FP16 | ✅ |
| `longseq_kivi_{model}_s{seq}` | 1.5B/7B/14B | 4096-32704 | KIVI | ✅ |
| `longseq_torchref_{model}_s{seq}` | 1.5B/7B/14B | 4096-32704 | torch_ref | ✅ |
| `longseq_triton_ra_{model}_s{seq}` | 1.5B/7B/14B | 4096-32704 | triton_ra | ✅ |
| `longseq_*_8b_s{seq}` | **8B** | 4096-32704 | 4 backends | 🔄 **补跑中** |

**关键数据 (14B)**:

| seq | fp16 | torchref | triton_ra | Δ(triton−torch) |
|-----|------|----------|-----------|-----------------|
| 4K | 42.28 | 68.17 | 67.73 | -0.44 |
| 8K | 42.81 | 86.08 | 71.53 | **-14.54 (-17%)** |
| 16K | 42.64 | 119.83 | 86.56 | **-33.26 (-28%)** |
| 32K | 43.13 | 190.23 | 113.16 | **-77.08 (-40%)** |

**旧数据归档**: `_archive_stage7_v1_20260412/` (warmup 不足的 v1 数据，不要用)

### 4.3 BD Adapter 1.5B Quality (废弃)

| 目录前缀 | 测试数 | 状态 | 原因 |
|---------|--------|------|------|
| `ppl_bd_1p5b_s{seed}` | 10 | ⚠️ 废弃 | BD GQA kernel bug |
| `needle_bd_1p5b_c{ctx}_s{seed}` | 12 | ⚠️ 废弃 | Needle 0% (生成乱码) |
| `ruler_bd_1p5b_sl{sl}_s{seed}` | 12 | ⚠️ 废弃 | RULER 1% |
| `longbench_bd_1p5b_s{seed}` | 5 | ⚠️ 废弃 | F1=0 |

**不要引用这些数据**。BD adapter 已从代码中删除。

### 4.4 FlashInfer 1.5B Quality

| 目录前缀 | 测试数 | 状态 | 关键结果 |
|---------|--------|------|---------|
| `ppl_fi_1p5b_s{seed}` | 10 | ✅ | PPL = 9.6311 |
| `needle_fi_1p5b_c{ctx}_s{seed}` | 12 | ✅ | 100% (所有 ctx) |
| `ruler_fi_1p5b_sl{sl}_s{seed}` | 12 | ✅ | 60.2% (4K), 55.6% (32K) |
| `longbench_fi_1p5b_s{seed}` | 5 | ✅ | F1 = 0.036 |

**CSV 字段 (PPL)**: `perplexity`, `ppl_ci95_low`, `ppl_ci95_high`, `seed`
**CSV 字段 (Needle details)**: `context_len`, `depth`, `passed`, `generated_text`
**CSV 字段 (RULER summary)**: `ruler_pass_rate` (0-100 scale!), `ruler_f1_mean`, `ruler_score`
**CSV 字段 (LongBench details)**: `task_name`, `f1`, `official_metric_value`, `prediction`

### 4.5 14B 全套 Quality (Phase 4)

| 目录前缀 | 测试数 | 状态 | 关键结果 |
|---------|--------|------|---------|
| `ppl_ra_14b_s{seed}` | 10 | ✅ | PPL = 5.0399 |
| `ppl_fp16_14b_s{seed}` | 10 | ✅ | PPL = 4.6850 |
| `needle_ra_14b_c{ctx}_s{seed}` | 12 | ✅ | 100% (4K-32K) |
| `needle_fp16_14b_c{ctx}_s{seed}` | 12 | ✅ | 100% (4K-32K) |
| `ruler_ra_14b_sl{sl}_s{seed}` | 9 | ✅ | 98.5% (4K), 96.6% (16K) |
| `longbench_ra_14b_s{seed}` | 5 | ✅ | F1 = 0.046 |
| `ppl_ablation_K4V16_14b_s{seed}` | 3 | ✅ | PPL = 4.8131 |
| `ppl_ablation_K16V4_14b_s{seed}` | 3 | ✅ | PPL = 4.7094 (K恢复93%) |
| `ppl_ablation_K8V4_14b_s{seed}` | 3 | ✅ | PPL = 4.7644 |
| `ppl_ablation_K4V8_14b_s{seed}` | 3 | ✅ | PPL = 4.8147 |

**注意**: 14B RULER **只到 16K**（32K 因 max_position_embeddings 限制未测）。Needle 到 32K。

### 4.6 FP16 RULER Baseline

| 目录前缀 | 模型 | 测试数 | 状态 | 用途 |
|---------|------|--------|------|------|
| `ruler_fp16_1p5b_sl{sl}_s{seed}` | 1.5B | 12 | ✅ | 证明 VT/CWE 低是模型限制 |
| `ruler_fp16_14b_sl{sl}_s{seed}` | 14B | 9 | ✅ | 14B fp16 baseline |

**1.5B FP16 RULER 关键数据**:

| sl | OVERALL | s_niah | mk_niah | vt | cwe |
|----|---------|--------|---------|-----|-----|
| 4K | 60.3% | 100% | 100% | 0% | 41% |
| 8K | 58.5% | 100% | 99.3% | 0% | 34.5% |
| 16K | 56.3% | 100% | 99.9% | 3.1% | 22.4% |
| 32K | 55.2% | 100% | 99.0% | 7.3% | 14.7% |

### 4.7 C1 KL vs MSE 7B 对比

| 目录前缀 | 测试数 | 状态 | 结果 |
|---------|--------|------|------|
| `ppl_mse_7b_s{seed}` | 3 | ✅ | PPL = 7.1121 |
| `ppl_kl_7b_s{seed}` | 3 | ✅ | PPL = 7.1121 (与 MSE 完全一致) |
| `ppl_fp16_7b_s1234` | 1 | ✅ | PPL = 6.7097 |
| `needle_mse_7b_c4096_s{seed}` | 3 | ✅ | 100% |
| `needle_kl_7b_c4096_s{seed}` | 3 | ✅ | 100% |

**关键发现**: KL 和 MSE 搜索到相同 percentile (k=100.0, v=99.9) → PPL 完全一致。

**MSE calib 文件**: `artifacts/kv_calib_mse_7b_int4_rolealign_v1.json`
**KL calib 文件**: `artifacts/kv_calib_rolealign_7b_v3.json`

### 4.8 Memory/Batch Sweep

| 目录前缀 | 模型 | batch sizes | 状态 |
|---------|------|------------|------|
| `memory_7b_b{1,4,8,16}` | 7B | 1/4/8/16 | ✅ |
| `memory_8b_b{1,4,8,16}` | 8B | 1/4/8/16 | ✅ |

**CSV 字段**: `gpu_mem_peak_mb`, `torch_peak_mb`, `kv_cache_mem_mb`

### 4.9 归档/废弃数据（不要用）

| 目录 | 内容 | 原因 |
|------|------|------|
| `_archive_pre_fix_20260411/` | Phase 1 修复前的旧 TPOT | v_percentile bug 影响 |
| `_archive_stage7_v1_20260412/` | Stage 7 v1 数据 | warmup=2 不足，std 高 20x |
| `_archive_phase2_polluted_20260411/` | Phase 2 BD quality 混合污染 | BD adapter rsync 中途替换 |

---

## 五、校准产物 (Calibration Artifacts)

位置: `/root/LLM_KVCache_Quantization/artifacts/`

| 文件 | 模型 | Loss | 用途 |
|------|------|------|------|
| `kv_calib_rolealign_1p5b_v3.json` | 1.5B | KL | 主 RoleAlign calib |
| `kv_calib_rolealign_7b_v3.json` | 7B | KL | 主 RoleAlign calib |
| `kv_calib_rolealign_8b_v3.json` | 8B | KL | 主 RoleAlign calib |
| `kv_calib_rolealign_14b_v3.json` | 14B | KL | 主 RoleAlign calib |
| `kv_calib_mse_7b_int4_rolealign_v1.json` | 7B | MSE | C1 KL vs MSE 对照 |
| `kv_calib_mse_1p5b_int4.json` | 1.5B | MSE | C1 历史 MSE 对照 |

---

## 六、模型路径 (远端)

| 模型 | HF ID / 本地路径 | 说明 |
|------|-----------------|------|
| 1.5B | `Qwen/Qwen2.5-1.5B-Instruct` | HF cache |
| 7B | `Qwen/Qwen2.5-7B-Instruct` | HF cache (symlink → autodl-tmp) |
| 8B | `/root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct` | modelscope local (HF cache 损坏) |
| 14B | `/root/autodl-tmp/modelscope_cache/qwen/Qwen2___5-14B-Instruct` | modelscope local |

**注意**: 8B 和 14B **必须用本地路径**，不能用 HF model_id（HF mirror 代理挂了）。

---

## 七、实验脚本索引

| 脚本 | 用途 | 产出 |
|------|------|------|
| `scripts/batch_p012/analyze_current.py` | 聚合所有数据生成 markdown | analysis_full.md |
| `scripts/batch_p012/stage1_phase1_rerun.sh` | Phase 1 1.5B/7B TPOT 重测 | tpot_*_{1p5b,7b} |
| `scripts/batch_p012/phase1_fix_8b_14b.sh` | Phase 1 8B/14B TPOT 补跑 | tpot_*_{8b,14b} |
| `scripts/batch_p012/stage3_phase2_bd_quality.sh` | BD 1.5B quality (废弃) | *_bd_1p5b_* |
| `scripts/batch_p012/stage4_phase3_fi_quality.sh` | FI 1.5B quality | *_fi_1p5b_* |
| `scripts/batch_p012/stage5_phase4_14b_full.sh` | 14B 全套 quality | *_14b_* |
| `scripts/batch_p012/stage6_phase5_misc.sh` | 7B/8B memory sweep | memory_* |
| `scripts/batch_p012/stage7_rerun.sh` | 长序列 TPOT v2 | longseq_* |
| `scripts/batch_p012/stage_8b_longseq.sh` | 8B 长序列 (Hkv 因果分离) | longseq_*_8b_* |
| `scripts/batch_p012/stage_baseline_fp16_ruler.sh` | FP16 RULER baseline | ruler_fp16_* |
| `scripts/batch_p012/stage_c1_kl_vs_mse.sh` | C1 KL vs MSE 7B 对比 | ppl_{kl,mse}_7b_*, needle_{kl,mse}_7b_* |
| `scripts/batch_p012/extract_phase1_table.py` | Phase 1 TPOT 表提取 | stdout |
| `scripts/batch_p012/diag_bd_needle.py` | BD Needle 诊断 | stdout |

---

## 八、RULER pass_rate 注意事项

**RULER CSV 的 `ruler_pass_rate` 列是 0-100 scale（百分数），不是 0-1 fraction！**

```python
# 正确读法：
df = pd.read_csv("profile_ruler_*.csv")
pass_rate = df["ruler_pass_rate"].iloc[0]  # 已经是 98.5 (= 98.5%)
# 不要再乘 100！

# RULER 每个目录有 4 个 CSV：
#   profile_ruler_*.csv      — summary (1 行，含 ruler_pass_rate)
#   ruler_task_summary_*.csv — per-task breakdown (4 行: s_niah/mk_niah/vt/cwe)
#   ruler_depth_summary_*.csv — per-depth breakdown
#   ruler_details_*.csv      — per-sample details
```

---

## 九、快速访问命令

```bash
# SSH 连接
sshpass -p 'YLt4oozwKWNg' ssh -p 31867 root@region-42.seetacloud.com

# 进入项目
cd /root/LLM_KVCache_Quantization

# 看所有结果目录
ls results/emnlp_p012_batch/runs/ | grep -v _archive | sort

# 看某个测试的 CSV 内容
cat results/emnlp_p012_batch/runs/tpot_triton_ra_14b/*.csv

# 跑聚合分析
python3 scripts/batch_p012/analyze_current.py

# 看 GPU 状态
nvidia-smi --query-compute-apps=pid,used_memory --format=csv

# 看正在跑的实验
ps -eo pid,etime,cmd | grep python3 | grep -v tensorboard | grep -v grep
```

---

## 十、相关文档

| 文档 | 内容 |
|------|------|
| `docs/session_findings_2026-04-12.md` | 本 session 所有发现 (16 Parts, 600 行) |
| `docs/option_d_plan.md` | Option D' 论文重构计划 (Codex 审查修订版) |
| `docs/handoff_to_thesis_session.md` | 跨 session 交接报告 |
| `docs/handoff_report_2026-04-11.md` | Session 1 Triton 优化报告 |
| `docs/triton_optimization_report.md` | Triton 优化全程记录 |

---

_本文件是实验数据的唯一权威索引。如有新实验产出，请更新本文件。_
