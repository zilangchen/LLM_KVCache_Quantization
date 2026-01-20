# <Cursor-AI 2026-01-21 03:18:31>
## 修改目的
强化协作与过程记录规范：确保每推进一个步骤，都同步更新 `lang.md` 的进度追踪与更新记录，避免“开发推进了但项目总览不更新”。

## 修改内容摘要
- 更新 `.cursorrules`：新增“步骤7.1 每做完一步必须更新 lang.md（项目进度追踪）”，并在执行检查表中加入对应勾选项。

## 影响范围
- 规则文件：`.cursorrules`
- 开发流程：后续所有代码/文档/实验步骤都必须同步维护 `lang.md`

## 技术细节
- 将 `lang.md` 作为单一事实来源（single source of truth）的新手任务清单与进度板，按“阶段/子任务/更新记录”持续追加。

# <Cursor-AI 2026-01-21 03:20:14>
## 修改目的
将 `objective.md` 升级为仓库内“唯一权威目标文件”，中文化且论文导向，并补充开工前门禁清单，确保后续里程碑与实验口径不跑偏。

## 修改内容摘要
- 重写 `objective.md`：补齐项目定位（与 LMDeploy 边界）、固定决策、研究问题/假设、创新点/贡献、DoD、复现规则、非目标与合规说明。
- 将“开工前门禁清单”写入 `objective.md`，作为进入 Milestone A 前的强制确认项。

## 影响范围
- 文档：`objective.md`
- 项目流程：后续实现与实验需严格对齐 `AGENT_TASKLIST.md` 与 `configs/exp_matrix.yaml` 的固定口径。

## 技术细节
- 关键口径对齐：固定 greedy 解码；结果字段与 tasklist 的 CSV schema 一致；LMDeploy 仅作为可选对照系统且与主线隔离。

# <Cursor-AI 2026-01-21 05:11:35>
## 修改目的
准备仓库初始化全量提交：纳入项目骨架（src/scripts/configs/env/tests 等）与论文相关资料，同时补充忽略规则以避免误提交 Office 临时文件。

## 修改内容摘要
- 更新 `.gitignore`：新增 `~$*` 与 `.~*` 以忽略 Office/WPS 临时文件。
- 计划提交：仓库骨架文件、实验配置与论文材料（由用户要求“全都提交”）。

## 影响范围
- 版本控制：提交范围扩大为仓库内剩余未跟踪文件（除被 `.gitignore` 忽略的临时文件）。
- 文档与工程：后续开发基于已入库的目录结构与配置文件推进。

## 技术细节
- 通过忽略规则避免把 `. ~*` 之类的锁/临时文件纳入版本历史，降低后续冲突与噪声。

# <Cursor-AI 2026-01-21 05:31:34>
## 修改目的
在正式写代码前，把 `objective.md` 细化为“可执行路线图”，将项目推进拆成按里程碑顺序可逐条验收的任务清单，并固化 agent 协作模板与复现口径。

## 修改内容摘要
- 扩展 `objective.md`：新增“稳定接口（Stable APIs）”、“结果与复现口径（单一事实来源）”、“如何驱动 agent 做每一步（统一指令模板）”、“项目执行路线图（Milestone A–J）骨架”。
- 将 A–J 里程碑的每一步明确：子任务顺序、产出物路径、验收命令占位、与 `configs/exp_matrix.yaml` 的对齐点。

## 影响范围
- 文档：`objective.md`
- 开发流程：后续实现需严格按里程碑顺序推进，并以 objective 的模板驱动 agent，避免口径漂移与返工。

## 技术细节
- Stable APIs 直接对齐 `AGENT_TASKLIST.md` 的接口约束；复现口径以 `configs/exp_matrix.yaml` 为唯一入口，并固化 CSV schema 与 run 元信息最小集合。

# <Cursor-AI 2026-01-21 05:55:33>
## 修改目的
根据 AutoDL 运行环境门禁确认结果，统一项目“目标栈”口径为 Python 3.12（镜像基线），并在 `objective.md` 固化联网/pin/最大 seq_len 等关键决策，避免后续实现阶段返工。

## 修改内容摘要
- 更新 `objective.md`：将核心技术栈改为 Python 3.12（AutoDL 镜像）与 PyTorch 2.8.0（CUDA 12.8 runtime），并把 H20 96GB/允许联网/需要 pin/seq_len=32768 等门禁决策写入。
- 更新 `AGENT_TASKLIST.md` 与 `README.md`：将 Python 3.10 的描述统一为 Python 3.12。

## 影响范围
- 文档：`objective.md`、`AGENT_TASKLIST.md`、`README.md`
- 项目口径：后续所有实现、实验与复现记录以 AutoDL 镜像栈为准。

## 技术细节
- `model_revision` 采用“首次下载解析 resolved revision → 写入运行记录并回填配置”的策略，保证严格复现同时减少手工出错。

# <Cursor-AI 2026-01-21 06:10:30>
## 修改目的
固化评测口径选择：明确 PPL 数据集、needle 方案与 TTFT/TPOT 的计时同步规则，确保后续实现与论文实验口径一致且可复现。

## 修改内容摘要
- 更新 `objective.md` 的“评测定义”：PPL 选择 `wikitext-2-raw-v1`；needle 选择方案 A（合成 needle + 字符串命中评分）；TTFT/TPOT 关键计时点前后做 GPU 同步（`torch.cuda.synchronize()` 或 CUDA events）。

## 影响范围
- 文档：`objective.md`
- 实验口径：后续 `eval_ppl.py`、`eval_needle.py`、`profile_latency.py` 的实现需严格遵守上述定义。

## 技术细节
- TTFT/TPOT 计时默认采用同步策略避免 CUDA 异步导致的低估与不稳定；needle 采用可控合成任务以降低数据依赖并提高复现性。

# <Cursor-AI 2026-01-21 03:04:58>
## 修改目的
新增面向新手的项目协作指南，明确“如何分阶段推进 + 如何驱动 agent 写代码”，并提供可持续更新的进度追踪模板，降低后续开发沟通成本。

## 修改内容摘要
- 新增 `lang.md`：包含全流程阶段任务清单（A~G）、每一步的验收标准、与 agent 协作的输入模板、进度追踪区与结果字段约定。

## 影响范围
- 新增文件：`lang.md`
- 文档受众：项目开发/实验推进全程使用

## 技术细节
- `lang.md` 按“阶段 → 子任务 → 验收标准 → 协作范式”的结构组织，后续每推进一个节点可在“更新记录”中追加状态与命令/结果路径。

# <Cursor-AI 2026-01-20 02:44:16>
## 修改目的
初始化 `kvm/` worktree 的研究仓库骨架，使其满足“可复现研究/论文工程化”的最小要求。

## 修改内容摘要
- 新增 `objective.md` 与 `development_record.md`，固化项目目标与开发记录流程。
- 将桌面目录中的 `AGENT_TASKLIST.md` 与 `exp_matrix.yaml`（实验矩阵）纳入本仓库管理（后续在 `configs/` 中使用）。
- 规划并创建最小目录结构（`src/ /scripts/ /configs/ /env/ /results/ /artifacts/` 等）与必要的占位文件。

## 影响范围
- 新增文件：`objective.md`、`development_record.md` 等（详见后续记录）。

## 技术细节
- 时间戳来源于 `date '+%Y-%m-%d %H:%M:%S'` 命令输出，确保记录可追溯。

