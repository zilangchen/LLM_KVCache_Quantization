# 论文章节 - 图表映射（Thesis Chapter Mapping）

> 用途：明确论文每一章需要引用哪些实验数据、图表和代码，确保写作时不遗漏。
> 数据来源：`results/final_thesis_plus_20260219_045623/`

---

## 第 1 章 绪论

- **内容**：研究背景（LLM 推理瓶颈 → KV Cache 显存占用）、问题定义、本文贡献
- **所需图表**：无实验数据
- **引用**：可引用 `objective.md` 中的研究问题（RQ1-RQ3）

---

## 第 2 章 相关工作

- **内容**：KV Cache 量化综述（INT8/INT4/Mixed）、校准方法、融合 Kernel 技术
- **所需图表**：无实验数据
- **参考文献**：KIVI、KVQuant、FlexGen、SmoothQuant 等

---

## 第 3 章 方法设计

### 3.1 KL 行为对齐校准

- **代码**：`scripts/calibrate_behavior.py`
- **产物**：`artifacts/kv_calib_kl_selected_v3_quick.json`
- **所需图表**：
  - [需新增] `inv_tau` 分布热力图（per-layer per-head）→ `scripts/plot_calib_analysis.py`
  - [可选] 校准搜索过程的 KL 收敛曲线

### 3.2 Per-head Temperature（inv_tau）

- **代码**：`src/engine/patch_model.py`（L546-L550）、`src/engine/generate_loop.py`（prefill hook）
- **公式**：$\text{attn}(\tau^{-1} \cdot Q, K, V)$
- **所需图表**：
  - [需新增] `inv_tau` 值分布直方图
  - [已有历史数据] 温度消融对比（with temp vs without temp）
    - 数据源：`results/runs/int8_ours_kl_temp_fused_*`（有 temp）vs 主线 `no_temp`

### 3.3 静态 Scale + 自适应保护

- **代码**：`src/cache/int8_cache.py`（`_expand_static_scale_for_tensor`、`_compute_dynamic_group_scale`）
- **关键参数**：`adaptive_static_margin=1.0`
- **所需图表**：[可选] 自适应 vs 纯静态 scale 的 PPL/Needle 对比

### 3.4 Triton 融合 Decode Attention Kernel

- **代码**：`src/kernels/triton_decode_attn_int8.py`
- **所需图表**：
  - [可用 mermaid] Kernel 架构示意图（read int8 KV → group dequant → online softmax → output）
  - [已有] TPOT 对比（fp16 vs int8_baseline vs int8_ours）

---

## 第 4 章 实验与分析

### 4.1 实验设置

- **内容**：模型、硬件、评测口径、实验矩阵说明
- **引用**：
  - 模型：`Qwen/Qwen2.5-1.5B-Instruct`
  - 硬件：NVIDIA H20 96GB
  - 配置：`configs/exp_matrix.yaml`
  - 环境：`results/final_thesis_plus_20260219_045623/env/versions.txt`

### 4.2 主线性能对比（核心表格）

- **表格**：`tables/thesis_main_claims_32k.csv` → `latex_tables/main_claims_32k.tex`
- **关键数据（32K, batch=1）**：

| kv_mode | TPOT (ms) | KV Mem (MB) | Needle | PPL |
|---------|-----------|-------------|--------|-----|
| fp16 | 30.91 | 896 | 100% | 9.4872 |
| int8_baseline | 50.29 | 504 | 100% | 9.4912 |
| int8_ours | 39.96 | 504 | 100% | 9.5085 |

### 4.3 延迟与显存随序列长度变化

- **图**：`plots/latency_tpot_vs_seq.png`
- **图**：`plots/memory_kv_cache_vs_seq.png`
- **图**：`plots/memory_peak_vs_seq.png`
- **表**：`tables/latency_summary.csv`、`tables/memory_summary.csv`

### 4.4 质量评估

- **图**：`plots/needle_pass_rate_vs_context.png`
- **图**：`plots/ppl_vs_tokens.png`
- **表**：`tables/needle_summary.csv`、`tables/ppl_summary.csv`
- **统计**：`tables/significance_summary.csv`（含 CI95 + 配对差异）

### 4.5 吞吐扩展（Batch Scaling）

- **图**：`plots/throughput_tok_per_s_vs_batch.png`
- **图**：`plots/throughput_tok_per_s_per_seq_vs_batch.png`
- **图**：`plots/prefill_tok_per_s_vs_batch.png`
- **表**：`tables/throughput_by_batch.csv`
- **关键数据（batch=16, 8K）**：
  - fp16: 350.33 tok/s
  - int8_baseline: 200.04 tok/s
  - int8_ours: 460.90 tok/s

### 4.6 消融分析

- **温度消融**：
  - 主线（no_temp）数据：`results/final_thesis_plus_20260219_045623/`
  - 对比（with_temp）数据：`results/runs/int8_ours_kl_temp_fused_*`、`results/runs/int8_ours_long_fused_*`
  - [需整理] 提取历史数据做对比表格
- **Group size 敏感性**：[需补跑或从历史数据提取]
  - 候选数据源：`results/iter_loop7_gs_isolation/`

### 4.7 INT4 扩展与局限

- **数据**：`tables/thesis_main_claims_32k.csv`（int4_fused / int4_ours 行）
- **关键发现**：
  - INT4 32K Needle = 0%，PPL 显著恶化
  - 结论：INT4 在当前参数下不满足主线质量门槛，作为局限性讨论

---

## 第 5 章 总结与展望

- **内容**：总结贡献、局限性、未来工作
- **无需新数据**

---

## 附录

### A. 可审计证据

- `gates/gate0_smoke_test.log`
- `gates/gate1_dry_run.log`
- `gates/gate2_triton_unittest.log`
- `gates/gate3_verify_int8_fused.log`
- `gates/gate3_verify_int8_ours.log`

### B. 完整结果表格

- `tables/relative_gain_summary.csv` → `latex_tables/relative_gain_summary.tex`
- `tables/latency_tpot_gain_vs_fp16.csv`

### C. 补充图表

- `plots/needle_exact_match_vs_context.png`
- `plots/latency_tpot_gain_vs_fp16.png`
- `plots/memory_peak_vs_batch.png`
- `plots/memory_kv_cache_vs_batch.png`

---

## 缺口总结（需要新增的产物）

1. **`inv_tau` 分布可视化**：从 `artifacts/kv_calib_kl_selected_v3_quick.json` 生成热力图/直方图
2. **温度消融对比表**：从历史 runs 提取 with_temp 数据，与主线 no_temp 对比
3. **[可选] Group size 敏感性图**：需补跑或从 `results/iter_loop7_gs_isolation/` 提取
4. **[可选] Triton Kernel 架构图**：mermaid 或手绘
