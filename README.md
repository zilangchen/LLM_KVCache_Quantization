## 项目概述
毕业设计/论文：**面向高效推理的大语言模型键值缓存量化方法**

本仓库目标：基于 `Qwen/Qwen2.5-1.5B-Instruct` 构建 **可复现** 的推理研究管线，实现 KV Cache **INT8** 量化（含 **percentile clipping** 与 **per-head / group-wise scaling**），并在 **显存 / 吞吐延迟 / 质量 / 长上下文稳定性** 四维进行评测。至少集成 1 个 Triton kernel 到真实 decode 路径。

## 固定约束（不要改）
- 模型：`Qwen/Qwen2.5-1.5B-Instruct`
- Python：3.12（以 AutoDL 镜像为准）
- 评测：以 `configs/exp_matrix.yaml` 为唯一实验入口（跑矩阵→产出 CSV/图表）

## 目录结构
参见 `AGENT_TASKLIST.md` 的 “Repository Layout”。

## 快速开始（占位）
后续将补齐：
- 依赖安装（`requirements.txt`）
- `scripts/smoke_test.py`、`scripts/run_experiments.py`
- `env/versions.txt` 与 `env/requirements_freeze.txt` 的生成方式

