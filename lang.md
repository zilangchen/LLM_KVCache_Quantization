# Lang.md（新手协作指南 + 全流程任务清单）

> 目标：让你以“新手也能跟得上”的方式，**一步步把这个项目做完**；并且明确“每一步应该怎么安排 agent 写代码/跑实验/记录结果”。  
> 本文件会随着项目推进持续更新：每完成一个阶段，就在“进度追踪”里勾选，并补充“本阶段产物/命令/注意事项”。

---

## 0. 先读懂这个项目要交付什么

你只需要记住 4 句话：

- **研究对象**：`Qwen/Qwen2.5-1.5B-Instruct`
- **主线方法**：KV Cache **INT8** 量化（静态 group-wise scale）
  + **KL 行为对齐校准** + **per-head temperature（inv_tau）**
  + decode（q_len=1）使用 **Triton 融合量化 attention kernel**
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

- [ ] **C2. baseline 量化口径固定（percentile + group_size=128）**
  - agent 要做：实现 percentile 裁剪 + group-wise（但用 group_size=128 退化为 per-head_dim）
  - 验收：作为 baseline 可复现跑通，并能与 ours 做清晰对照

---

### 阶段 D：ours（KL 行为对齐校准 + per-head temperature + group-wise INT8）

- [ ] **D1. KL 行为对齐校准脚本**
  - agent 要做：实现 `scripts/calibrate_behavior.py`，输出 `artifacts/kv_calib_kl.json`
  - 验收：固定 seed 下可复现；包含 `k_scale/v_scale` 与 `inv_tau[layer, head]`

- [ ] **D2. 温度校正（prefill + decode 一致生效）**
  - agent 要做：实现 `src/quant/temperature.py` 并接入 prefill（缩放 Q）与 decode（供 fused kernel 使用）
  - 验收：打开/关闭温度开关的消融可跑，且结果字段可追踪

- [ ] **D3. group-wise INT8 量化实现与接入**
  - agent 要做：实现 `src/quant/groupwise.py` 与 `src/quant/clipping.py`，并在 `kv_mode=int8_ours` 加载校准文件
  - 验收：`int8_ours` 可跑通，needle/PPL 趋势不劣于 baseline（尤其长上下文）

---

### 阶段 E：Triton 融合 decode attention（q_len=1，硬指标）

- [ ] **E1. 实现 fused kernel**
  - agent 要做：实现 `src/kernels/triton_decode_attn_int8.py`（读 int8 K/V + group-wise scale + online softmax + 输出累加，并融合 `inv_tau`）
  - 验收：数值对齐 torch reference（固定 seed，误差阈值可控）

- [ ] **E2. 正确性验证**
  - agent 要做：补齐测试用例（GQA 映射、mask、不同 seq_len），并提供误差统计
  - 验收：误差在可控阈值内，且不出现 NaN/Inf

- [ ] **E3. 性能对比**
  - agent 要做：与 `decode_attn_impl=torch_ref` 对比 TPOT（长上下文）
  - 验收：至少不退化；最好有提升；结果可复现

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

- **2026-01-21 07:06:35**：仓库结构整理与归档
  - 完成步骤/子任务：删除重复(1)文件；迁移学校材料到 `docs/school/`；迁移提示词模板到 `docs/prompt_templates.md`；建立目录骨架；统一入口为 `configs/exp_matrix.yaml`
  - 运行命令：`date '+%Y-%m-%d %H:%M:%S'`
  - 产出物路径：`docs/`、`README.md`、`lang.md`、`development_record.md`
  - 关键摘要：根目录不再堆放学校材料；规划/入口清晰，避免后续口径冲突

- **2026-01-21 06:44:34**：项目目标升级为“两条主线必做”（KL 校准 + fused decode kernel）
  - 完成步骤/子任务：同步更新 `AGENT_TASKLIST.md`、`configs/exp_matrix.yaml`、`objective.md`、`lang.md`，消除与新主线规格的口径冲突
  - 运行命令：`date '+%Y-%m-%d %H:%M:%S'`
  - 产出物路径：`AGENT_TASKLIST.md`、`configs/exp_matrix.yaml`、`objective.md`、`lang.md`
  - 关键摘要：Milestone F=KL 行为对齐校准 + per-head temperature；Milestone G=triton_fused decode-attn（q_len=1）

- **2026-01-21 06:10:30**：锁定评测口径（PPL/needle/计时同步）
  - 完成步骤/子任务：PPL 选择 `wikitext-2-raw-v1`；needle 选择方案 A；TTFT/TPOT 关键计时点前后 GPU 同步
  - 运行命令：`date '+%Y-%m-%d %H:%M:%S'`
  - 产出物路径：`objective.md`
  - 关键摘要：评测口径固定后，后续脚本实现按此执行，避免返工与口径漂移

- **2026-01-21 05:55:33**：确认 AutoDL 环境并统一目标栈为 Python 3.12
  - 完成步骤/子任务：在 `objective.md` 写入 H20 96GB/联网/Pin/seq_len=32768 等门禁决策，并统一仓库文档的 Python 版本口径
  - 运行命令：`date '+%Y-%m-%d %H:%M:%S'`
  - 产出物路径：`objective.md`、`AGENT_TASKLIST.md`、`README.md`
  - 关键摘要：以镜像为准（Python 3.12 + Torch 2.8.0 + CUDA 12.8 runtime），后续实现按此口径推进

- **2026-01-21 05:31:34**：细化 `objective.md` 为可执行路线图（A–J）
  - 完成步骤/子任务：新增 Stable APIs、复现口径、agent 指令模板、Milestone A–J 路线图骨架
  - 运行命令：`date '+%Y-%m-%d %H:%M:%S'`
  - 产出物路径：`objective.md`
  - 关键摘要：objective=权威规范；lang=进度板；后续按里程碑逐章细化并推进实现

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

