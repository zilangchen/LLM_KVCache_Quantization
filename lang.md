# Lang.md（新手协作指南 + 全流程任务清单）

> 目标：让你以“新手也能跟得上”的方式，**一步步把这个项目做完**；并且明确“每一步应该怎么安排 agent 写代码/跑实验/记录结果”。  
> 本文件会随着项目推进持续更新：每完成一个阶段，就在“进度追踪”里勾选，并补充“本阶段产物/命令/注意事项”。

---

## 0. 先读懂这个项目要交付什么

你只需要记住 4 句话：

- **研究对象**：`Qwen/Qwen2.5-1.5B-Instruct`
- **主线方法**：KV Cache **INT8** 量化 + **percentile clipping**
  + **per-head / group-wise scaling**
- **评测闭环**：同口径对比 **显存** / **吞吐&延迟** / **生成质量** /
  **长上下文稳定性（needle）**
- **工程硬指标**：至少 **1 个 Triton kernel** 真正接入 **decode 路径**

---

## 1. 和 agent 配合的“最省心工作流”（强烈建议照做）

### 1.1 你每次给 agent 的输入（最小信息集合）

建议你每次提需求都包含下面 5 点（复制模板即可）：

```text
目标：我现在要做什么（1 句话）
当前状态：我已经做到了哪里（例如：baseline 跑通/某脚本报错/有一份结果 csv）
约束：必须遵守什么（例如：只改 src/ 里的实现，不动论文；必须兼容 A100；不创建新文件等）
验收标准：怎么才算完成（例如：跑完脚本输出 results/*.csv 且包含字段 X、Y、Z）
我希望你下一步做：列出 3-5 个最小可执行步骤并直接开始
```

### 1.2 agent 每次工作的固定节奏（你用来检查我有没有跑偏）

你可以用这张“节奏表”监督我：

- **读背景**：先读 `development_record.md` 和 `objective.md`
- **定计划**：把任务拆成可验收的小步（一次只做 1-2 个小步）
- **改代码**：尽量原地修改文件；引入必要的异常处理；避免一次性大改
- **跑验证**：能运行就运行；能测就测；输出关键日志/结果路径
- **写记录**：立刻把修改写进 `development_record.md`

> 备注：如果你让我“跑长时间训练/实验”，我会先给你 dry-run 方案和影响范围。

---

## 2. 全项目阶段任务清单（新手路线）

### 阶段 A：环境与可复现基建（先打地基）

- [ ] **A1. 创建/验证 Python 环境**
  - 你要做：准备虚拟环境（conda/venv 均可）
  - agent 要做：检查 `requirements.txt` 是否可装；补齐缺失依赖
  - 验收：能 `python -c "import torch; import transformers"` 成功

- [ ] **A2. 统一实验输出结构**
  - 你要做：决定结果放哪（建议 `results/` 或 `artifacts/`）
  - agent 要做：实现“实验输出必须有 CSV/JSON + 元信息（commit/硬件/参数）”
  - 验收：任何一次实验都有结构化输出，且可追溯

- [ ] **A3. 配置驱动（exp matrix）跑通**
  - 你要做：确认 `configs/exp_matrix.yaml` 是“真入口”
  - agent 要做：写一个入口脚本，读取矩阵并逐项运行/记录
  - 验收：一条命令能跑完至少 2 组对比实验（例如 FP16 vs INT8-baseline）

---

### 阶段 B：FP16 baseline（先跑通再优化）

- [ ] **B1. 最小可运行推理管线（FP16）**
  - agent 要做：用 Transformers + 自定义 generation loop 跑通 decode
  - 验收：给定 prompt 能生成；并打印/记录吞吐、延迟、显存峰值

- [ ] **B2. 基线测量工具（指标口径固定）**
  - agent 要做：统一计时区间（prefill / decode）、token 统计、显存统计
  - 验收：同一输入多次运行，指标波动在合理范围

---

### 阶段 C：INT8-baseline（先做“能用但不一定最好”的量化）

- [ ] **C1. KV cache 的 INT8 存储（naive）**
  - agent 要做：在 cache 写入时量化、读取时反量化
  - 验收：显存下降明显；生成不崩；能完整跑完一段生成

- [ ] **C2. percentile clipping（全局 or per-layer）**
  - agent 要做：实现 percentile 估计与裁剪策略（可先离线统计）
  - 验收：相比 naive，质量/稳定性提升（至少不更差）

---

### 阶段 D：ours（per-head / group-wise scaling）

- [ ] **D1. per-head scaling**
  - agent 要做：每个 head 独立 scale/zero-point（或对称量化）
  - 验收：对长上下文更稳，或质量提升

- [ ] **D2. group-wise scaling**
  - agent 要做：按 group（例如 hidden_dim 分组）做缩放，权衡开销
  - 验收：更好的精度/性能折中；并在结果里体现

---

### 阶段 E：Triton kernel 接入真实 decode（硬指标）

- [ ] **E1. 选一个必须加速的点（最小闭环）**
  - 常见选择：attention 中的某个 matmul/融合操作、dequant + gemm 融合等
  - 验收：kernel 确实在 decode path 被调用（可用日志/计数证明）

- [ ] **E2. 正确性验证**
  - agent 要做：对齐 PyTorch 版本输出（允许小误差），并提供误差统计
  - 验收：误差在可控阈值内，且不出现 NaN/Inf

- [ ] **E3. 性能对比**
  - agent 要做：与 torch/naive 实现对比，记录加速比
  - 验收：吞吐提升或延迟降低，且结果可复现

---

### 阶段 F：评测闭环（needle + 质量 + 性能）

- [ ] **F1. 长上下文 needle 评测脚本**
  - agent 要做：实现可复现的 needle 测试数据生成与评分
  - 验收：能输出结构化分数，并纳入 exp matrix

- [ ] **F2. 质量评测（轻量）**
  - 选项：困惑度/少量 benchmark/自定义 QA
  - 验收：同口径对比 FP16 / INT8-baseline / INT8-ours

---

### 阶段 G：论文与答辩材料（最后收口）

- [ ] **G1. 实验表格与图自动生成**
  - agent 要做：从 CSV/JSON 自动出图（吞吐、显存、needle 曲线等）
  - 验收：一键生成论文可用图表

- [ ] **G2. 论文结构对齐学校模板**
  - 你要做：确认学校格式要求与目录结构
  - agent 要做：列出“每章写什么 + 需要哪些图表/实验”
  - 验收：材料齐全，可答辩

---

## 3. 每一步具体怎么让 agent 写代码（操作范式）

### 范式 1：实现一个功能点（最常用）

你发：

```text
目标：实现 KV cache 的 INT8 量化写入/读取（naive）
当前状态：FP16 decode 已跑通；有吞吐&显存统计脚本
约束：不要大重构；改动要可运行；必须加异常处理；输出可复现指标
验收标准：同一 prompt 生成 128 tokens 成功；显存下降；输出 results/*.csv
我希望你下一步做：直接开始改，并给出我该运行的命令
```

agent 的输出应包含：

- **改了哪些文件**
- **怎么运行**
- **预期输出长什么样（字段名）**
- **失败了怎么办（常见报错排查）**

### 范式 2：排查报错（debug）

你发：

```text
我运行命令：<粘贴命令>
报错：<粘贴完整 traceback 或日志片段>
我环境：CUDA/torch/transformers 版本（能贴就贴）
目标：修到能跑通，并解释根因
```

---

## 4. 进度追踪（每完成一步就更新这里）

> 规则：每次推进一个小节点，就在下面新增一条“更新记录”。  
> 你只需要把“你看到的现象/结果文件路径/命令”贴出来，我来帮你写得清清楚楚。

### 4.1 当前里程碑状态

- **A 环境基建**：未完成
- **B FP16 baseline**：未完成
- **C INT8-baseline**：未完成
- **D ours scaling**：未完成
- **E Triton kernel 接入**：未完成
- **F 评测闭环**：未完成
- **G 论文材料**：未完成

### 4.2 更新记录（按时间倒序追加）

（从这里开始追加）

- **2026-01-21 05:11:35**：准备仓库初始化全量提交
  - 完成步骤/子任务：补充 `.gitignore`（忽略 Office/WPS 临时文件），并将剩余仓库骨架/配置/资料纳入版本控制
  - 运行命令：`date '+%Y-%m-%d %H:%M:%S'`
  - 产出物路径：`.gitignore`（以及本次提交纳入的其余文件）
  - 关键摘要：按固定目录结构推进；避免把 `. ~*` 等临时文件写入 git 历史

- **2026-01-21 03:20:14**：完成“目标文件与开工门禁”准备
  - 完成步骤/子任务：重写 `objective.md`（中文论文导向），并将开工前门禁清单写入其中（进入 Milestone A 前强制确认）
  - 运行命令：`date '+%Y-%m-%d %H:%M:%S'`
  - 产出物路径：`objective.md`
  - 关键摘要：明确与 LMDeploy 边界（baseline-only）、固定决策、研究问题/贡献/DoD、复现口径与门禁清单

---

## 5. 约定：结果文件应该包含什么（方便写论文）

建议每次实验都至少输出这些字段（CSV/JSON 都行）：

- **run_id / timestamp**
- **git_commit**
- **model_name**
- **hardware**（GPU 型号、显存）
- **prompt_len / gen_len**
- **prefill_latency_ms / decode_latency_ms**
- **throughput_tok_s**
- **peak_vram_mb**
- **quant_config**（bit、clipping percentile、per-head/group 参数）
- **quality_metrics**（可为空，后续补）

