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

## 快速开始（占位）
后续将补齐：
- 依赖安装（`requirements.txt`）
- `scripts/smoke_test.py`、`scripts/run_experiments.py`
- `env/versions.txt` 与 `env/requirements_freeze.txt` 的生成方式
