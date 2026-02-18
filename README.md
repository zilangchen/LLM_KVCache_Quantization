## 项目概述
毕业设计/论文：**面向高效推理的大语言模型键值缓存量化方法**

本仓库目标：基于 `Qwen/Qwen2.5-1.5B-Instruct` 构建 **可复现** 的推理研究管线，实现 KV Cache **INT8** 量化（静态 group-wise scale），并以 **KL 行为对齐校准 + per-head temperature** 提升长上下文稳定性；decode 阶段（q_len=1）使用 **Triton 融合量化 attention kernel**。在 **显存 / 吞吐延迟 / 质量 / 长上下文稳定性** 四维进行评测。

## 固定约束（不要改）
- 模型：`Qwen/Qwen2.5-1.5B-Instruct`
- Python：3.12（以 AutoDL 镜像为准）
- 评测：以 `configs/exp_matrix.yaml` 为唯一实验入口（跑矩阵→产出 CSV/图表）

## 目录结构
参见 `AGENT_TASKLIST.md` 的 “Repository Layout”。

## 当前进展
进度追踪以 `lang.md` 为准；历史记录见 `development_record.md`。

## 文档与模板
- 提示词模板：`docs/prompt_templates.md`
- 学校材料归档：`docs/school/`

## 快速开始
本项目的 GPU 实验默认在远端 AutoDL(H20) 上运行（见 `AGENTS.md`）。

### 1) 远端最小验证（Smoke Test）
```bash
cd /root/autodl-tmp/LLM_KVCache_Quantization
/root/miniconda3/bin/python scripts/smoke_test.py --save_output
```

### 2) 一键复现论文最终表图（推荐）
- 复现协议：`docs/final_experiment_protocol.md`
- 最终验收目录（本地已同步）：`results/final_thesis_20260214_094156/`
  - 表格：`results/final_thesis_20260214_094156/tables/`
  - 图：`results/final_thesis_20260214_094156/plots/`
  - LaTeX 表：`results/final_thesis_20260214_094156/latex_tables/all_tables.tex`
  - Gates：`results/final_thesis_20260214_094156/gates/`

### 3) 实验入口（唯一）
- 矩阵配置：`configs/exp_matrix.yaml`
- Runner：`scripts/run_experiments.py`
- 聚合出图：`scripts/aggregate_results.py`
- 导出 LaTeX 表：`scripts/export_tables_latex.py`

## 工作区整理与历史归档
- 当前保留的活跃结果目录：
  - `results/final_thesis_20260214_094156/`
  - `results/int4_fused_round_20260219_0315/`
- 历史实验与过时材料已归档到：
  - `development_history/archive_20260219_041537/`
  - 归档清单：`development_history/archive_20260219_041537/MANIFEST.md`
