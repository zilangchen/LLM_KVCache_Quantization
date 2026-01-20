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
- **核心技术栈**：Python 3.10、PyTorch(CUDA)、Transformers、Triton、
  FastAPI/Uvicorn、pynvml、numpy/pandas/matplotlib
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
  - GPU 型号/显存（例如 4090 24GB / A100 80GB）
  - 驱动版本、CUDA 版本、Python 环境方式（conda/venv）
  - 是否允许联网下载模型（HuggingFace）
- **模型 pinning（复现强度）**
  - 是否在 `configs/exp_matrix.yaml` 固定 `model_revision`
  - 是否需要本地缓存/镜像源（离线环境）
- **评测定义（口径必须固定）**
  - TTFT/TPOT 的测量点与同步规则（是否 `torch.cuda.synchronize()`）
  - PPL 数据集选择与切分（以及是否允许下载）
  - needle 任务定义与判定规则（命中判定、容错、随机种子）
  - 吞吐负载：ShareGPT（或本地 prompts）来源与采样策略（固定 seed）
- **实验可行性（显存预算）**
  - `seq_lens`（例如 4096–32768）对当前 GPU 是否可跑
  - 若不可跑：fallback 的最大长度与分阶段策略（先短后长）
  - 校准 prompts 来源与规模（例如 `num_prompts=256`、`max_prompt_tokens=1024`）
- **论文对齐（产出驱动写作）**
  - 计划输出的表格/图表清单与论文章节对应
  - CSV schema 字段与 `AGENT_TASKLIST.md` 的输出字段一致，避免后期返工

