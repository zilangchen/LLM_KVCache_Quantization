## 1. Task Alignment

- Goal:
  - 在不破坏当前论文关键资产、不中断 Closure Pack 前提下，缓解远端 `/root/autodl-tmp` 数据盘 99% 占用问题。
  - 采用“优先迁移冷数据到系统盘、仅在必要时清理明确可放弃缓存”的方式，恢复可继续运行实验的安全余量。
- Non-goals:
  - 不修改研究代码、实验逻辑、配置矩阵或论文内容。
  - 不触碰 `claude/*` 分支、不做 git 清理、不删除本地仓库历史。
  - 不尝试一次性解决所有远端存储治理问题，只解决当前 Closure Pack 的磁盘阻塞。
- Background:
  - 远端系统盘（`/root` 所在 overlay）约 30G，总体约 17G 可用。
  - 远端数据盘（`/root/autodl-tmp`）100G，仅剩约 2G。
  - 审计确认大头为：
    - `/root/autodl-tmp/hf_cache` ≈ 65G
    - `/root/autodl-tmp/modelscope_cache` ≈ 30G
    - `/root/autodl-tmp/phase6_backup_20260310_042708` ≈ 2.7G
    - `/root/autodl-tmp/phase5v2_backup_20260309_125340` ≈ 188M
  - 审计还确认：
    - `Qwen2.5-14B` HF 缓存约 21G，且存在 `.incomplete` 残留。
    - `modelscope_cache` 中的 `Llama-3.1-8B-Instruct` 约 30G，看起来是当前 8B 核心模型缓存，不应贸然动。

## 2. Constraints

- Environment constraints:
  - 数据盘只剩 2G，任何跨盘迁移都必须分批进行，避免临时文件把盘打爆。
  - 系统盘只有约 17G 余量，不能承接大模型主缓存。
  - 远端网络不稳定，重新下载模型成本高。
- Repository constraints:
  - 不改 repo 代码；若必须记录操作，仅限生成审计日志到远端临时位置或 `artifacts/`。
  - 不影响当前 `results/emnlp_final_raw` 与 `results/emnlp_postfix_v2` 的论文资产可用性。
- Reproducibility constraints:
  - 不删除 Closure Pack 当前仍依赖的核心模型缓存：Qwen 1.5B / 7B、Llama-3.1-8B、Mistral-7B。
  - 不删除当前唯一有效的结果目录。
  - 若迁移目录，必须校验源/目标文件数量与大小一致后才删除源。
- Risk constraints:
  - 跨挂载点 `mv` 风险高；应优先使用 `rsync` + 校验 + 删除源的三段式流程。
  - 不进行“系统盘兜底接管 20G+ 缓存”的高风险操作。

## 3. Deliverables

- Files to modify:
  - 无 repo 源码文件变更。
- Files to add:
  - 可选：远端审计/迁移日志，例如 `/root/autodl-tmp/disk_rebalance_20260318.log`。
- Expected outputs/artifacts:
  - 数据盘释放到安全余量（目标至少 10G，可取 15G+）。
  - 一份迁移/清理执行记录：迁移了哪些目录、释放了多少空间、保留了哪些关键缓存。

## 4. Acceptance Criteria

- Functional checks:
  - `/root/autodl-tmp` 可用空间 ≥ 10G；理想 ≥ 15G。
  - Closure Pack 仍可访问其依赖的模型缓存与结果目录。
- Regression checks:
  - `results/emnlp_final_raw`、`results/emnlp_postfix_v2` 目录结构未损坏。
  - 核心模型缓存仍存在并可离线加载至少 1 个模型 smoke check。
- Reproducibility checks:
  - 迁移的目录在目标盘文件数、总大小与源一致。
  - 删除的仅限明确可放弃缓存或已完成校验的已迁移冷备份。
- Documentation checks:
  - 记录最终空间变化、删除/迁移清单、风险说明。

## 5. Execution Steps

1. 冻结目标与候选清单：
   - 将远端目录分成三类：
     - 必保留：核心模型缓存、论文结果目录。
     - 冷数据可迁移：`phase6_backup_20260310_042708`、`phase5v2_backup_20260309_125340` 等备份。
     - 明确可放弃：`Qwen2.5-14B` 未完成缓存（若你批准清理）。
2. 先做低风险跨盘迁移：
   - 使用 `rsync -a --info=progress2` 将冷备份从 `/root/autodl-tmp/...` 迁移到 `/root/...` 或 `/root/archive/...`。
   - 校验目标大小/文件计数后，再删除数据盘源目录。
3. 复测空间并判断是否足够：
   - 若仅靠迁移即可达到 ≥ 10G，停止，不做缓存删除。
   - 若仍不足，则进入受控缓存清理。
4. 受控清理（推荐仅 14B）：
   - 删除 `/root/autodl-tmp/hf_cache/hub/models--Qwen--Qwen2.5-14B-Instruct`。
   - 复测空间，确认达到 Closure Pack 安全阈值。
5. 最终验证：
   - 重新执行 `df -h`。
   - 对保留的 1-2 个关键模型做离线加载或目录存在性检查。
   - 输出最终报告。

## 6. Verification Commands

- Command:
  - `df -h /root /root/autodl-tmp`
  - `du -sh <moved_src> <moved_dst>`
  - `find <moved_src> | wc -l && find <moved_dst> | wc -l`
  - `du -sh /root/autodl-tmp/hf_cache/hub/models--Qwen--Qwen2.5-14B-Instruct`
- Expected result:
  - 系统盘仍有安全余量。
  - 数据盘恢复到至少 10G 可用。
  - 迁移目录前后大小/文件数一致。
  - 若执行 14B 清理，该目录不存在且释放约 21G。

## 7. Risk Register

- Risk:
  - 跨盘迁移中断导致目标不完整。
  - Impact:
    - 冷备份损坏或需要重新拷贝。
  - Mitigation:
    - 用 `rsync` 分阶段复制；校验完成前不删源。

- Risk:
  - 系统盘剩余空间不足以承接迁移目录。
  - Impact:
    - 系统盘被打满，影响 shell/服务。
  - Mitigation:
    - 先估算系统盘余量；仅迁移约 3G 级冷备份，不迁大模型缓存。

- Risk:
  - 错删 Closure Pack 还要用的模型缓存。
  - Impact:
    - 后续实验无法离线继续。
  - Mitigation:
    - 只把 `Qwen2.5-14B` 列为可删候选；核心四模型全部保留。

- Risk:
  - 误删论文关键结果目录。
  - Impact:
    - 结果不可复现、论文证据丢失。
  - Mitigation:
    - 不动 `results/emnlp_final_raw` 与 `results/emnlp_postfix_v2`。

- Risk:
  - 清理后仍然空间不足。
  - Impact:
    - 还需要额外清理，造成反复操作。
  - Mitigation:
    - 分两段：先迁移冷备份，再按需清理 14B 缓存；每一步后复测。

- Risk:
  - `modelscope_cache` 与 HF cache 存在隐式依赖，误判为重复。
  - Impact:
    - 8B 模型加载失败。
  - Mitigation:
    - 本轮明确不动 `modelscope_cache`。

## 8. Open Questions (Need Re-confirmation)

- Question:
  - 是否允许在“迁移冷备份到系统盘”之外，删除 `Qwen2.5-14B` 的未完成缓存来一次性释放 21G？
  - Option A:
    - 允许。推荐。
    - 理由：Closure Pack 不依赖 14B，且你此前已接受 14B 可后置/不做。
  - Option B:
    - 不允许。仅迁移冷备份。
    - 理由：保留未来做 14B 的可能，但只能释放约 3G，磁盘压力仍高。

- Question:
  - 系统盘上是否接受新建一个归档目录（例如 `/root/archive_autodl/`）承接冷备份？
  - Option A:
    - 接受。推荐。
    - 理由：避免直接散落在 `/root`，便于后续统一回收。
  - Option B:
    - 不接受。
    - 理由：如果你只想清理不想迁移，则可跳过本步。
