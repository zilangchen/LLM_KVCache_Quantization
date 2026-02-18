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

### 0.1 文档职责（单一事实来源）
- 规范与口径：`objective.md`
- 任务清单：`AGENT_TASKLIST.md`
- 进度追踪：`lang.md`
- 历史记录：`development_record.md`
- 系统性问题：`iteration.md`

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
- **读协作规范**：读 `AGENTS.md`、`docs/AGENT_README.md`，并检查 `.agent/skills/` 下的 SKILL 文档
- **远程执行**：凡是需要 GPU/模型下载/长任务，必须按 `.agent/skills/remote-server/SKILL.md` 走 SSH + tmux，并用 rsync 同步结果
- **定计划**：把任务拆成可验收的小步（一次只做 1-2 个小步）
- **改代码**：尽量原地修改文件；引入必要的异常处理；避免一次性大改
- **跑验证**：能运行就运行；能测就测；输出关键日志/结果路径
- **写记录**：立刻把修改写进 `development_record.md`

> 备注：如果你让我“跑长时间训练/实验”，我会先给你 dry-run 方案和影响范围。

---

## 2. 全项目阶段任务清单（新手路线）

### 阶段 A：环境与可复现基建（先打地基）

- [x] **A1. 创建/验证 Python 环境**
  - 你要做：准备虚拟环境（conda/venv 均可）
  - agent 要做：检查 `requirements.txt` 是否可装；补齐缺失依赖
  - 验收：能 `python -c "import torch; import transformers"` 成功

- [x] **A2. 统一实验输出结构**
  - 你要做：决定结果放哪（建议 `results/` 或 `artifacts/`）
  - agent 要做：实现“实验输出必须有 CSV/JSON + 元信息（commit/硬件/参数）”
  - 验收：任何一次实验都有结构化输出，且可追溯

- [x] **A3. 配置驱动（exp matrix）跑通**
  - 你要做：确认 `configs/exp_matrix.yaml` 是“真入口”
  - agent 要做：写一个入口脚本，读取矩阵并逐项运行/记录
  - 验收：一条命令能跑完至少 2 组对比实验（例如 FP16 vs INT8-baseline）

---

### 阶段 B：FP16 baseline（先跑通再优化）

- [x] **B1. 最小可运行推理管线（FP16）** ✅
  - agent 要做：用 Transformers + 自定义 generation loop 跑通 decode
  - 验收：给定 prompt 能生成；并打印/记录吞吐、延迟、显存峰值

- [x] **B2. 基线测量工具（指标口径固定）** ✅
  - agent 要做：统一计时区间（prefill / decode）、token 统计、显存统计
  - 验收：同一输入多次运行，指标波动在合理范围（优化后 TPOT 波动 ~4%）

---

### 阶段 C：FP16 Cache (Baseline)

- [x] **C1. KV layout 文档**
  - agent 要做：写清 shape（layer/head/head_dim/seq）、增长策略与内存布局
  - 验收：文档可直接指导实现与测试用例编写

- [x] **C2. FP16 cache 实现**
  - agent 要做：实现 `append/get_kv`；确保长度在 prefill 后等于 prompt_len
  - 验收：生成正确性保持；cache 长度 invariants 通过

---

### 阶段 D：评测与实验框架（关键卡点，必须严格依照 Objective.md）

- [x] **D1 & D2. 性能与显存评测**
  - agent 要做：规范化 `script/profile_latency.py` 和 `script/profile_memory.py`
  - 验收：输出 CSV 包含 ttft, tpot, mem_peak 等关键字段

- [x] **D3. 困惑度评测 (eval_ppl)**
  - agent 要做：实现 `scripts/eval_ppl.py` (wikitext-2, greedy)
  - 验收：输出 PPL 值

- [x] **D4. 大海捞针评测 (eval_needle)**
  - agent 要做：实现 `scripts/eval_needle.py` (Strategy A)
  - 验收：输出 pass rate

---

### 阶段 E：INT8-baseline（功能正确优先）

- [x] **E1. Baseline Quantizer & Cache**
  - agent 要做：简单对称量化，append 时量化
  - 验收：`kv_mode=int8_baseline` 可跑通

- [x] **E2. Engine 接入**
  - agent 要做：支持 kv_mode 切换
  - 验收：能跑通生成

---

### 阶段 F：INT8-ours（KL校准 + Temp + Group-wise）

- [x] **F1. 行为对齐校准脚本**
- [x] **F2. Group-wise INT8**
- [x] **F3. Per-head Temperature**
- [x] **F4. 集成验证**

---

### 阶段 G：Triton 融合 Decode Kernel (Required)

- [x] **G1. Fused Kernel 实现**
- [x] **G2. 强制接入 Decode**
- [x] **G3. 对齐 Torch Reference**
- [x] **G4. 性能回归**

---

### 阶段 H：INT4 / Mixed（可选）

- [x] **H1. INT4 或 Mixed 精度策略**
  - agent 要做：定义策略并保证与主线口径一致
  - 验收：可复现实验对比（显存/质量/速度）

---

### 阶段 I：服务化与压测（可选）

- [ ] **I1. 服务端推理**
  - agent 要做：实现 OpenAI-like 接口与 streaming
  - 验收：可稳定返回与 engine 一致的结果

- [ ] **I2. 并发压测**
  - agent 要做：脚本化压测与日志输出
  - 验收：稳定性与吞吐可量化

---

### 阶段 J：论文与答辩材料（最后收口）

- [x] **J1. 实验表格与图自动生成**
  - agent 要做：从 CSV/JSON 自动出图（吞吐、显存、needle 曲线等）
  - 验收：一键生成论文可用图表

- [ ] **J2. 论文结构对齐学校模板**
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

- **A 环境与冒烟**：✅ 已完成
- **B 自定义生成循环**：✅ 已完成
- **C FP16 KV Cache**：✅ 已完成
- **D 评测框架**：✅ 已完成
- **E INT8-baseline**：✅ 已完成
- **F INT8-ours（KL+Temp+Group-wise）**：✅ 已完成（校准产物 + 温度/静态 scale 消融齐备）
- **G Triton 融合 Decode**：✅ 已完成（单测 + verify_fused_decode 通过，且可证明命中 Triton）
- **H INT4 / Mixed（可选）**：✅ 已实现（可选）
- **I 服务化与压测（可选）**：未开始
- **J 实验矩阵一键复现 + 出图**：✅ 已完成（matrix + aggregate_results 出表出图）

### 4.2 更新记录（按时间倒序追加）

（从这里开始追加）

- **2026-02-19 04:36:00**：完成“INT4 主线增强 + 统计增强（开发中阶段验收）”✅
  - 代码能力：
    - 新增 `kv_mode=int4_ours/int4_ours_mixed`（生成、PPL、Needle、verify、runner 全链路可用）
    - `calibrate_behavior.py` 新增 `--quant_bits 4` + outlier rescue 搜索参数，并可输出 `selection`
    - `aggregate_results.py` 新增 95%CI、seed 配对差异表、prefill 吞吐曲线
  - 远端验证（H20）：
    - `tests/test_int4_cache.py` 通过
    - `tests/test_triton_kernel.py` 通过（含 INT4 wrapper 用例）
    - `verify_fused_decode.py --kv_mode int4_fused/int4_ours/int4_ours_mixed` 通过并命中 fused
  - 试跑目录（远端）：
    - `results/int4_ours_smoke/`（含 runs/logs/tables/plots/latex_tables）
  - 说明：
    - 当前 quick 校准参数下，INT4 needle 质量仍需继续收敛（此轮以“链路打通+可观测性增强”为目标）。

- **2026-02-19 04:15:37**：完成“激进归档清理（第一轮）”✅
  - 归档目录：`development_history/archive_20260219_041537/`
  - 归档清单：`development_history/archive_20260219_041537/MANIFEST.md`
  - 执行内容：
    - `results/` 仅保留 `final_thesis_20260214_094156` 与 `int4_fused_round_20260219_0315`
    - 迁移 `logs/remote_review_*`、`env/remote_review_*`、`env/review_fix_*`
    - 迁移过时文档 `docs/review_report_remote_20260210.md`
    - 迁移废弃入口 `exp_matrix.yaml`（根目录）
  - 当前约束：实验入口唯一为 `configs/exp_matrix.yaml`

- **2026-02-12 23:48:34**：完成“final matrix → 出表出图 → 文档收口”✅
  - 关键修复：
    - 修复 `scripts/eval_needle.py` 在 `depth=100%` 时 needle 被截断导致“必失败”的评测 bug（旧的 66.67% 结论已作废）
    - KV cache 扩容策略加入 `max_seq_len` cap（对齐 `max_position_embeddings`），避免 32K 附近无意义 2x 超配导致 KV 内存统计失真
  - Final 结果目录（远端）：`results/final_20260212_230755/`
    - 表格：`results/final_20260212_230755/tables/`
    - 图：`results/final_20260212_230755/plots/`
  - 关键结论（32K，`seq_len=32704, gen_len=64, warmup=2, runs=3`）：
    - TPOT：`fp16=30.88ms`，`int8_baseline=50.64ms`，`int8_ours=39.12ms`（ours 相比 baseline -22.7%）
    - KV 常驻内存：`fp16=896MB`，`int8_baseline/int8_ours=504MB`（相比 fp16 -43.8%）
    - Needle：在 `4k/8k/16k/32k` 四点三种模式均为 `100%`
  - 文档更新：`docs/final_experiment_protocol.md`、`docs/final_results_summary.md`
  - 运行建议：kv_cache PPL 为 token-by-token 口径非常慢，已将 `scripts/run_experiments.py --ppl_max_samples` 默认值收紧为 4，避免无界长跑

- **2026-02-10 04:46:38**：补齐 `.agent/workflows` 与 `agent_cli` 的远端 SSH 自检 ✅  
  - 关键动作：`.agent/workflows/*` 增加“执行前检查（强制）”，统一要求先读 `AGENTS.md`/`docs/AGENT_README.md` 并跑 SSH 健康检查；实验/调试/kernel/milestone/auto-dev 全部对齐 tmux 远端执行  
  - 协作门禁：`scripts/agent_tools/agent_cli.py` 新增 `bootstrap/ssh-check`，`start` 默认自动执行（列出 `.agent/skills/.agent/workflows` + SSH 健康检查），降低新 agent 漏掉远端环境连接的概率  

- **2026-02-10 04:02:46**：补齐“新 Agent 自动走远程环境”的流程门禁 ✅  
  - 关键动作：新增 `AGENTS.md`；更新 `.cursorrules`/`docs/AGENT_README.md`/`lang.md` 强制先查阅 `.agent/skills/` 并按 SSH+tmux 执行 GPU 任务  
  - 工程修正：`decode_attn_impl` 变为真实开关（`triton_fused|torch_ref`）；`int8_ours` 缺校准文件默认直接失败；`run_experiments.py --dry_run` 本地无 torch 可用  

- **2026-02-09 03:00:00**：新增 fused decode 一致性验证入口 ✅  
  - 关键动作：增加 `verify_fused_decode.py`，对比 fused 与参考路径 logits 差异  
  - 说明：需要 GPU 环境运行，默认参考路径为 int8_dequant

- **2026-02-09 02:00:00**：PPL 支持量化 KV 路径 ✅  
  - 关键动作：`eval_ppl.py` 新增 kv-cache 模式，int8_baseline/int8_ours 可直接评测  
  - 说明：输出新增 `ppl_mode/tokens_evaluated`，用于区分评测路径与计数口径

- **2026-02-09 01:00:00**：KL 校准与 `inv_tau` 输出接入 `int8_ours` ✅  
  - 关键动作：新增静态 scale 量化与 `inv_tau` 注入，`calibrate_behavior.py` 输出 `kv_calib_kl.json`  
  - 说明：`inv_tau` 当前仅在 fused decode 路径生效，需后续验证质量与性能

- **2026-02-09 00:00:00**：扩展实验入口支持 `int8_ours/int8_fused` ✅  
  - 关键动作：`run_experiments.py` 放开 kv_mode 过滤；评测脚本新增 `int8_ours/int8_fused` 选项  
  - 说明：当前 `int8_ours` 仍临时映射到 `int8_fused`，等待 KL 校准与温度修正接入

- **2026-02-08 22:57:53**：记录远程验证超时的系统性问题 ✅  
  - 关键动作：`iteration.md` 新增 ID=004，统一远程验证采用 tmux + 日志  
  - 说明：避免前台 SSH 超时中断长任务

- **2026-02-08 22:45:05**：修复 PPL 评测超长警告与内存浪费问题 ✅  
  - 关键动作：`eval_ppl.py` 改为分块/流式 tokenization，避免全量拼接  
  - 结果：PPL 评测更稳，避免超长警告并降低峰值内存

- **2026-02-08 22:37:52**：记录新的系统性问题（PPL 超长警告）  
  - 关键动作：在 `iteration.md` 新增 ID=003，提示 `eval_ppl` 需改为分块/流式 tokenization  
  - 说明：避免全量拼接导致超长警告与潜在内存浪费

- **2026-01-22 03:46:53**：修复仓库复现入口与 baseline 口径不一致 ✅  
  - 新增统一入口 `scripts/run_experiments.py`，评测脚本支持 `--config/--run_name/--out_dir`  
  - 量化口径贯通：`clip_percentile/group_size` 全链路透传，写入 config snapshot  

- **2026-01-22 03:58:13**：修复远程验证中的确定性与 dtype 问题 ✅  
  - 关键动作：补齐 `CUBLAS_WORKSPACE_CONFIG`，修复量化 dtype 与 smoke_test 导入  
  - 结果：A–F 评测流水线已跑通，日志与结果已同步到本地  

- **2026-01-22 03:20:40**：以 `development_record.md` 为最高参考完成仓库一致性核查 ✅  
  - 关键动作：记录系统性问题到 `iteration.md`，并输出“单一入口 + baseline 口径对齐优先”的检查建议  
  - 说明：已完成静态审阅与脚本/矩阵/实现对照检查，等待下一步对齐落地

- **2026-01-22 03:27:52**：根据用户确认将系统性问题标记为已记录 ✅  
  - 关键动作：`iteration.md` 中 ID=002 状态更新为“已记录”

- **2026-01-21 15:43:00**：Milestone C 实现完成（INT8-baseline KV Cache）✅
  - 完成步骤/子任务：实现 naive 量化存储、Percentile 裁剪、Group-wise scaling (gp=128)
  - 运行命令：`python3 -m py_compile src/cache/*.py src/quant/*.py`（本地验证）
  - 产出物路径：
    - `src/cache/README_cache_layout.md`（内存布局文档）
    - `src/cache/fp16_cache.py`（FP16实现）
    - `src/cache/int8_cache.py`（INT8实现）
    - `src/quant/int8_basic.py`（量化算子）
    - `results/run/profile_int8_baseline_*.csv`（服务器验证后生成）
  - 关键摘要：显存预期下降 30-50%，功能代码已就绪，等待服务器运行 profile 验证显存收益

- **2026-01-21 15:03:47**：Milestone B 优化完成 ✅
  - 完成步骤/子任务：增强 OOM 预警 + warmup 默认改为 3
  - 运行命令：`python3 scripts/profile_baseline.py --seq_len 512 --gen_len 64 --runs 3`
  - 产出物路径：`results/runs/profile_baseline_2026-01-21T15-02-54.*.csv`
  - 关键摘要：TPOT 波动从 ~15% 降至 ~4%，吞吐稳定在 61-64 tok/s

- **2026-01-21 14:51:37**：Milestone B 完成（FP16 Baseline 推理管线）✅
  - 完成步骤/子任务：创建自定义 Generation Loop + 计时工具 + profile 脚本
  - 运行命令：`python3 scripts/profile_baseline.py --seq_len 1024 --gen_len 128`
  - 产出物路径：
    - `src/utils/timing.py`（CUDA 同步计时工具）
    - `src/engine/generate_loop.py`（prefill + decode 循环）
    - `scripts/profile_baseline.py`（性能测试脚本）
    - `results/runs/profile_baseline_2026-01-21T14-51-34.044991.csv`
  - 关键摘要：H20 GPU 测试通过，TTFT=37.63ms, TPOT=17.33ms, 吞吐=57.69 tok/s, 显存峰值=3208.46MB

- **2026-01-21 14:29:38**：Milestone A Phase 2 完成（服务器验证）✅
  - 完成步骤/子任务：在 AutoDL 服务器验证 `collect_env.py` 和 `smoke_test.py`
  - 运行命令：`source /etc/network_turbo && python scripts/smoke_test.py --save_output`
  - 产出物路径：`env/versions.txt`、`results/runs/smoke_test_2026-01-21T14-24-37.680990.json`
  - 关键摘要：环境确认 H20 96GB + torch 2.8.0 + triton 3.4.0；模型加载和生成验证通过；网络问题通过 AutoDL 内置加速解决

- **2026-01-21 07:29:15**：Milestone A Phase 1 完成（本地开发）
  - 完成步骤/子任务：创建 `scripts/collect_env.py` 和 `scripts/smoke_test.py`
  - 运行命令：`python3 -m py_compile scripts/*.py`（语法验证通过）
  - 产出物路径：`scripts/collect_env.py`、`scripts/smoke_test.py`
  - 关键摘要：两个脚本包含完整异常处理、参数对齐 exp_matrix.yaml；等待服务器验证

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

- **2026-01-21 16:04:23**：完成 Milestone C (INT8 Baseline) 验证
  - 完成步骤/子任务：解决 OOM 与 API 兼容性问题，成功在 remote H20 上跑通 fp16 与 int8_baseline 对比
  - 运行命令：`python3 scripts/profile_baseline.py ...`
  - 产出物路径：`results/milestone_c/*.csv`, `docs/milestone_c_verification.md`
  - 关键摘要：功能正确；显存未降（符合预期，待 Kernel 优化）；Baseline 性能数据已归档

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


# <Antigravity 2026-01-21 16:04:23>
## 修改目的
验证 Milestone C (INT8 Baseline) 的功能正确性与性能基线，解决 `DynamicCache` 兼容性问题与 OOM 显存泄露。

## 修改内容摘要
- **Bug 修复 (OOM & Crash)**：
  - 修复 `src/engine/generate_loop.py` 中 `transformers 4.37+` 引入的 `DynamicCache` 兼容性问题（`AttributeError`）。
  - 发现并修复远程验证中的 OOM 问题（94GB+ leak）：根因为 `DynamicCache` 迭代时返回全量历史导致 `kv_cache` 指数级重复存储；通过切片 `k[:,:,-1:,:]` 解决。
  - 增加激进的 GC 与显式内存清理 `kv_cache.clear(); del kv_cache; torch.cuda.empty_cache()`。
- **验证执行**：
  - 远程 H20 GPU 验证通过。
  - FP16 Baseline: 60 tok/s, 3.2GB Mem.
  - INT8 Baseline: 45 tok/s, 3.2GB Mem.
- **记录产出**：
  - 生成 `results/milestone_c/` 下的对比 CSV。
  - 创建 `milestone_c_verification.md` 详细分析报告（显存无下降符合 non-kernel 预期）。

## 影响范围
- 核心引擎：`src/engine/generate_loop.py`（健壮性提升）
- 验证脚本：`scripts/profile_baseline.py`（增加 GC）
- 文档：更新 `lang.md` 状态

## 技术细节
- `DynamicCache.from_legacy_cache` 会将 tuple 转换为全量 Cache，若在 loop 中不加区分地 append，会导致 KV 历史在每一步被完整复制一遍。必须检查 `k.shape[2]` 并仅提取新 token。
