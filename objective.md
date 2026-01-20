## 项目名称
面向高效推理的大语言模型键值缓存量化方法（本科毕业设计/论文）

---

## 项目定位（与 LMDeploy 的差别）

- **本项目（窄而深，论文导向）**：围绕 KV Cache 量化做“方法 + 系统分析 +
  可复现实验闭环 + 关键 kernel 优化”的研究型工程。重点回答
  “在固定评测口径下，如何在质量/显存/速度之间取得可解释、可复现的最优折中”。
- **LMDeploy（广而全，部署系统）**：通用推理部署框架，KV 量化是其功能之一。
  本项目中 **LMDeploy 仅作为 baseline/对照系统**（可选），用于系统级参考对比；
  主线贡献必须来自本仓库的独立实现，且与 LMDeploy 脚本隔离，避免耦合与归属不清。

---

## 固定决策（不可修改）

- **模型**：`Qwen/Qwen2.5-1.5B-Instruct`
- **核心技术栈**：Python 3.12（以 AutoDL 镜像为准）、PyTorch 2.8.0（CUDA
  12.8 runtime）、Transformers、Triton、FastAPI/Uvicorn、pynvml、
  numpy/pandas/matplotlib
- **两条执行路径**
  - **研究主路径（必须）**：Transformers + 自定义 generation loop +
    自定义 KV cache（服务于算法与 kernel 优化，避免被框架“封装掉关键环节”）。
  - **系统参考路径（可选）**：LMDeploy/TurboMind（仅做 baseline；与主线代码隔离）。
- **复现实验入口**：`configs/exp_matrix.yaml` 作为实验矩阵（可一键复跑）。
- **质量评测解码口径**：固定 greedy（temperature=0.0, top_p=1.0, top_k=0），
  与 `configs/exp_matrix.yaml` 对齐。

---

## 研究问题与假设（论文写作口径）

- **RQ1：长上下文下 INT8 KV 的误差累积与稳定性**  
  假设：KV 的量化误差会随解码步数/上下文长度累积，导致长上下文任务（needle）
  更易出现检索失败或语义漂移。
- **RQ2：percentile clipping 与（per-head / group-wise）scaling 的作用机理**  
  假设：通过 percentile clipping 控制异常值，
  再用 per-head 或 group-wise scaling 进行更细粒度的动态范围匹配，
  能在相同显存预算下显著改善质量与稳定性。
- **RQ3：Triton kernel 能否避免“省显存但速度没了”**  
  假设：将关键的 dequant（及可选融合）放到 Triton kernel，
  可降低 CPU/GPU 调度与 memory-bound 开销，使量化方案在端到端吞吐/延迟上不退化。

---

## 创新点与贡献（避免“只开关对比”）

- **方法层（Algorithm）**
  - 离线校准：percentile clipping 的候选值搜索与推荐区间
  - 量化策略：per-head / group-wise scaling（含消融：不开 clipping、不同 group_size）
  - 输出：可复现的推荐配置与适用边界（对应 `artifacts/kv_calib.json`）
- **系统层（System/Analysis）**
  - 固定口径下给出 **显存/吞吐/延迟/质量/needle** 随序列长度变化的曲线
  - 解释：同显存预算下可支持的最大上下文与并发的变化趋势与原因
- **工程层（Engineering）**
  - 至少 1 个 Triton kernel 真正集成到真实 decode 路径（最低：dequant；
    加分：融合 q_len=1 的 decode-attn 关键路径）

---

## 完成定义（Definition of Done）

对齐 `AGENT_TASKLIST.md` 的里程碑顺序（A–J，H/I 可选），满足：

- **端到端三条管线可跑**：FP16 / INT8-baseline / INT8-ours
- **实验矩阵可复现**：`configs/exp_matrix.yaml` 驱动的一键复跑，产出 tables/plots
- **结构化结果齐全**：每次 run 输出 CSV/JSON，字段口径与 tasklist 中定义一致
  （至少包含：`run_id, model_id, kv_mode, quant_bits, clip_percentile, group_size, dtype,
  seq_len, gen_len, batch, ttft_ms, tpot_ms, tok_per_s, gpu_mem_peak_mb, timestamp,
  git_commit`）
- **kernel 硬指标达成**：至少 1 个 Triton kernel 被真实推理路径调用，
  且通过数值一致性检查（容忍小误差）与性能对比（不退化或有提升）
- **论文可交付**：依据学校工科/理科格式规范完成论文正文、图表与答辩材料

---

## 复现与记录规则（强制）

- **运行记录**：所有脚本输出结构化结果（CSV/JSON），并记录：
  - `timestamp`（运行时刻）
  - `git_commit`（当前 commit）
  - `hardware`（GPU 型号/显存）、驱动/CUDA/torch/transformers 版本（见 `env/`）
  - 关键参数快照（从 `configs/exp_matrix.yaml` 解析后的 config dump）
- **解码固定**：涉及质量评测时，统一 greedy 解码，禁止临时改采样参数造成口径漂移
- **实验输出路径**：推荐写入 `results/` 下的 runs/tables/plots 子目录
  （具体以 `AGENT_TASKLIST.md` 约定为准）

---

## 非目标（明确边界）

- 不做“全能部署框架”，不以 LMDeploy 为核心交付
- 不追求支持所有模型/所有后端；以固定模型与固定口径完成论文闭环为第一优先级
- 在主线闭环未完成前，不优先做 INT4/mixed 等扩展（对应里程碑 H 为可选）

---

## 开源/学术合规（baseline-only 写法）

- LMDeploy 作为对照系统引用与比较（论文中明确引用与版本信息）
- 主线贡献（算法、实现、实验与结论）必须来自本仓库独立实现与可复现实验
- 对照实验脚本与主线实现保持隔离，避免“对照代码混入主线贡献”的归属风险

---

## 开工前门禁清单（进入 Milestone A 之前必须确认）

- **硬件与环境**
  - 已确认（AutoDL）：H20-NVLink × 1，显存 96GB；CPU 16 核；内存 150GB
  - 已确认：驱动 `580.76.05`；基础镜像 PyTorch 2.8.0 / Python 3.12 /
    CUDA 12.8（Ubuntu 22.04）
  - 已确认：允许联网下载 HuggingFace 模型与评测所需资源
- **模型 pinning（复现强度）**
  - 已确认：需要 pin（严格复现）
  - 待落实：`model_revision` 的具体值（首次下载后解析 resolved revision，
    写入运行记录，并回填到 `configs/exp_matrix.yaml`）
- **评测定义（口径必须固定）**
  - 已确认：TTFT/TPOT 的关键计时点前后都做 GPU 同步（优先 `torch.cuda.synchronize()`；也可用 CUDA events），保证计时可信
  - 已确认：PPL 数据集使用 `wikitext-2-raw-v1`（允许联网下载）
  - 已确认：needle 采用方案 A（合成 needle-in-a-haystack + 字符串命中评分；固定 seed）
  - 吞吐负载：ShareGPT（或本地 prompts）来源与采样策略（固定 seed）
- **实验可行性（显存预算）**
  - 已确认：先以 `seq_lens` 最大 32768 为主线目标
  - 若不可跑：fallback 的最大长度与分阶段策略（先短后长）
  - 校准 prompts 来源与规模（例如 `num_prompts=256`、`max_prompt_tokens=1024`）
- **存储与缓存策略**
  - 已确认：磁盘可扩容，不作为瓶颈
  - 仍建议：将 HF/datasets cache 指向数据盘或扩容盘，避免系统盘 30GB 被写满
- **论文对齐（产出驱动写作）**
  - 计划输出的表格/图表清单与论文章节对应
  - CSV schema 字段与 `AGENT_TASKLIST.md` 的输出字段一致，避免后期返工

---

## 稳定接口（Stable APIs，后续实现必须遵守）

本项目采用“研究主路径（Transformers + 自定义 generation loop + 自定义 KV cache）”，
为保证后续模块可替换、可对比，接口在早期固定，后续实现不得随意破坏。

### Engine

- `Engine.generate(prompts, generation_config, kv_mode, runtime_config) -> GenerationOutput`
- 必须同时支持：
  - 脚本离线调用（non-streaming）
  - 服务端流式输出（streaming，Milestone I）

### KV Cache

- `KVCache.append(layer_id, k, v)`
- `KVCache.get_kv(layer_id) -> (k, v)`
- 约束：
  - 必须支持 decode 过程中按步增长（每步追加 1 token 的 KV）
  - 必须能在 `kv_mode` 切换时替换实现（fp16 / int8_baseline / int8_ours）

### Quantizer

- `Quantizer.quantize_kv(k, v, meta) -> (qk, qv, qmeta)`
- `Quantizer.dequantize_kv(qk, qv, qmeta) -> (k, v)`
- 约束：
  - 量化配置（bits、clipping percentile、group_size 等）必须可序列化写入结果与
    artifacts，确保复现

### Kernels

- Triton kernels 必须提供 python wrapper，放在 `src/kernels/`
- 至少 1 个 kernel 必须在真实 decode 路径被调用（不仅是 demo）

---

## 结果与复现口径（单一事实来源）

### 实验入口（唯一）

- 以 `configs/exp_matrix.yaml` 为唯一实验入口：跑矩阵 → 产出 CSV/图表
- 关键口径锁定（与 `configs/exp_matrix.yaml` 对齐）：
  - `seed=1234`
  - greedy decoding：`temperature=0.0, top_p=1.0, top_k=0`

### 输出位置与结构（约定）

- `results/`（禁止手写散落到其他目录）
  - `results/runs/`：每次运行的 CSV/JSON（每个 run 一套）
  - `results/tables/`：论文表格
  - `results/plots/`：论文图
  - `results/logs/`：脚本运行日志（如有）
- `artifacts/`：校准与中间产物（例如 `artifacts/kv_calib.json`）

### 结构化结果字段（CSV schema）

所有 profile/eval 脚本必须输出 `results/runs/*.csv`，字段至少包含：

`run_id, model_id, kv_mode, quant_bits, clip_percentile, group_size, dtype, seq_len, gen_len, batch, ttft_ms, tpot_ms, tok_per_s, gpu_mem_peak_mb, timestamp, git_commit`

### 每次运行必须记录的元信息（最少集合）

- `timestamp`：运行时刻（写入 CSV/JSON）
- `git_commit`：当前 commit（写入 CSV/JSON）
- `hardware`：GPU 型号/显存（写入 JSON 或 CSV 扩展字段）
- `config_dump`：本次 run 的配置快照（从 `configs/exp_matrix.yaml` 解析后写入 JSON）

---

## 如何驱动 agent 做每一步（统一指令模板）

后续每个 Milestone 的每个子任务，都用下面模板驱动 agent，保证“实现—验收—记录”
闭环，不靠临时口头约定。

### 模板 A：实现一个功能点（功能/重构/新增脚本）

你发给 agent 的输入（复制后填空）：

```text
目标：<1 句话描述本次要完成的子任务>
当前状态：<已完成到哪里；相关文件/分支/结果路径>
约束：
  - 必须对齐：objective.md / AGENT_TASKLIST.md / configs/exp_matrix.yaml
  - 代码风格：PEP8（79 字符），不要引入未使用依赖
  - 必须加异常处理：文件/网络/显存不足/缺少 CUDA 等
验收标准：
  - 命令：<我将运行的命令>
  - 预期输出：<终端关键输出> + <结果文件路径> + <CSV 字段必须包含哪些>
我希望你下一步做：列出 3-5 个最小可执行步骤并直接开始
```

agent 输出必须包含：

- 改了哪些文件（精确路径）
- 我该运行哪些命令（复制即可运行）
- 预期输出长什么样（关键日志 + 文件路径 + CSV/JSON 字段）
- 失败了怎么办（2-3 个最常见报错的定位与修复）

### 模板 B：排查报错（debug）

你发给 agent 的输入：

```text
我运行命令：<粘贴命令>
报错：<粘贴完整 traceback 或日志片段>
环境：<CUDA/torch/transformers 版本；GPU 型号；是否离线>
目标：修到能跑通，并解释根因；补上必要的异常处理与提示信息
```

agent 输出必须包含：

- 根因（用 1-2 句话说清）
- 修复方案（最小改动优先）
- 我该运行的复现/验证命令

---

## 项目执行路线图（Milestone A–J）

说明：先把 A–J 的“骨架版”写全，确保路径完整；后续我们按顺序逐章细化到
“agent 可直接照做 + 你可直接运行验收命令”的粒度。

### Milestone A：环境与 Smoke Test

- **目标**：项目可安装、可加载模型、可对单条 prompt 进行 greedy 生成。
- **子任务**
  - **A1 依赖安装与版本记录**
    - 产出物：`requirements.txt`、`env/versions.txt`、`env/requirements_freeze.txt`
    - 实现方法要点：写脚本/命令自动收集 torch/CUDA/GPU 信息并落盘
    - 异常处理与降级：无 GPU/无 CUDA/离线下载失败时给出清晰提示与替代方案
    - 验收标准（命令）：`python -c "import torch; import transformers"`
  - **A2 最小生成脚本**
    - 产出物：`scripts/smoke_test.py`
    - 实现方法要点：固定 greedy；打印输出文本与关键元信息（commit/硬件）
    - 异常处理与降级：OOM/模型下载失败时给出提示与 retry 参数
    - 验收标准（命令）：`python scripts/smoke_test.py` 输出非空文本
- **与矩阵对齐点**：对齐 `configs/exp_matrix.yaml: project.model_id, runtime.decoding`
- **完成后更新记录**
  - `development_record.md`：记录环境信息落盘方式与 smoke test 命令
  - `lang.md`：更新 A1/A2/A3 的状态与追加一条更新记录

### Milestone B：自定义 Generation Loop（不使用 `model.generate`）

- **目标**：实现可控的 prefill + token-by-token decode，为替换 KV cache 做准备。
- **子任务**
  - **B1 generate_loop 骨架**
    - 产出物：`src/engine/generate_loop.py`
    - 实现方法要点：prefill + decode 分离；greedy；返回结构化输出
    - 异常处理与降级：超长输入/显存不足时给出可读错误与建议（缩短 seq_len）
    - 验收标准（命令）：提供最小脚本调用并能生成非空文本
  - **B2 计时口径（TTFT/TPOT）**
    - 产出物：计时工具函数（位置后续细化）
    - 实现方法要点：定义 TTFT/TPOT 的同步点（是否 `torch.cuda.synchronize()`）
    - 验收标准（命令）：同一输入多次运行，波动可解释且输出字段齐全
- **与矩阵对齐点**：对齐 `runtime.decoding` 与 `seed`
- **完成后更新记录**：同上

### Milestone C：FP16 KV Cache（Baseline）

- **目标**：在固定 layout 下实现正确的 KV caching，并可在 decode 中按步增长。
- **子任务**
  - **C1 KV layout 文档**
    - 产出物：`src/cache/README_cache_layout.md`
    - 实现方法要点：写清 shape（layer/head/head_dim/seq）、增长策略与内存布局
    - 验收标准：文档可直接指导实现与测试用例编写
  - **C2 FP16 cache 实现**
    - 产出物：`src/cache/fp16_cache.py`
    - 实现方法要点：实现 `append/get_kv`；确保长度在 prefill 后等于 prompt_len，
      decode 每步 +1
    - 异常处理与降级：shape 不匹配时抛出清晰错误（包含 layer_id/期望 shape）
    - 验收标准：生成正确性保持；cache 长度 invariants 通过
- **与矩阵对齐点**：kv_mode=fp16

### Milestone D：评测与实验框架（先锁口径）

- **目标**：在做量化前先把 memory/speed/quality/needle 的评测闭环跑通。
- **子任务**
  - **D1 profile_latency**
    - 产出物：`scripts/profile_latency.py` + `results/runs/*.csv`
    - 验收标准：CSV 含 `ttft_ms/tpot_ms/tok_per_s` 等字段
  - **D2 profile_memory**
    - 产出物：`scripts/profile_memory.py` + `results/runs/*.csv`
    - 实现方法要点：pynvml 采样/峰值统计；记录 `gpu_mem_peak_mb`
  - **D3 eval_ppl**
    - 产出物：`scripts/eval_ppl.py` + `results/runs/*.csv`
    - 说明：数据集选择与下载方式在门禁清单中先确定
  - **D4 eval_needle**
    - 产出物：`scripts/eval_needle.py` + `results/runs/*.csv`
    - 实现方法要点：可复现生成与评分；固定 seed
- **与矩阵对齐点**：`experiments[*].tasks` 与 CSV schema

### Milestone E：INT8-baseline（功能正确优先）

- **目标**：实现可跑的 int8 KV（baseline），并可通过 kv_mode 切换进入推理路径。
- **子任务**
  - **E1 baseline quantizer**
    - 产出物：`src/quant/int8_basic.py`
    - 实现方法要点：先做最简单（per-tensor 或 per-head）的对称量化/反量化
  - **E2 int8 cache**
    - 产出物：`src/cache/int8_cache.py`
    - 实现方法要点：append 时量化，get 时反量化（或延迟到 attention）
  - **E3 engine kv_mode 切换**
    - 产出物：engine 增加 `kv_mode=fp16/int8_baseline`
    - 验收标准：`kv_mode=int8_baseline` 可端到端跑通
- **与矩阵对齐点**：kv_mode=int8_baseline，quant_bits=8

### Milestone F：INT8-ours（clipping + group-wise / per-head scaling）

- **目标**：实现论文主线，并提供消融开关与推荐配置产物。
- **子任务**
  - **F1 校准脚本**
    - 产出物：`scripts/calibrate_kv.py` → `artifacts/kv_calib.json`
    - 与矩阵对齐点：`calibration.*`
  - **F2 clipping**
    - 产出物：`src/quant/clipping.py`
    - 与矩阵对齐点：`clip_percentile`
  - **F3 group-wise scaling**
    - 产出物：`src/quant/groupwise.py`
    - 与矩阵对齐点：`group_size`
  - **F4 kv_mode=int8_ours**
    - 验收标准：needle 或 PPL 趋势上不劣于 baseline（至少在长上下文设置）

### Milestone G：Triton kernel（至少 1 个进真实 decode）

- **目标**：至少实现 `triton_dequant` 并在真实 decode 路径调用，保证正确性与性能不退化。
- **子任务**
  - **G1 triton_dequant**
    - 产出物：`src/kernels/triton_dequant.py`
  - **G2 集成到 decode**
    - 产出物：engine/attention 路径调用；提供计数/日志证明
  - **G3 正确性测试**
    - 产出物：`tests/` 下的数值一致性测试（误差阈值）
  - **G4 性能对比**
    - 产出物：profiling CSV（对比 torch 实现）

### Milestone H（可选）：INT4 / Mixed Precision

- **目标**：在主线闭环后扩展研究深度（只在需要时做）。
- **子任务**（占位）：kv_mode=int4/mixed、mixed policy、同口径评测

### Milestone I（可选）：服务化与压测

- **目标**：可演示的服务端推理与并发压测。
- **子任务**（占位）：`src/server/app.py`、`scripts/load_test.py`、对齐 engine 输出

### Milestone J：实验矩阵一键复现 + 出图（论文交付）

- **目标**：一条命令跑矩阵并产出论文表格/图表。
- **子任务**
  - **J1 run_experiments**
    - 产出物：`scripts/run_experiments.py`（读取 `configs/exp_matrix.yaml`）
  - **J2 make_plots**
    - 产出物：`scripts/make_plots.py` → `results/plots/*`
  - **J3 paper-ready 输出组织**
    - 产出物：`results/tables/*` + 图表清单与章节映射（后续细化）

