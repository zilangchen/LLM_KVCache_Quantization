# Phase 2.6 A-Scheme Run — Provenance Manifest

> **目的**：明确标注 2026-04-18 21:32:43 启动的 `phase2_a_chain` 跑的 provenance 等级。
> 本次是 **exploratory / dirty-main run**，**不得**作为最终主表 claim 的唯一证据；
> 若结论进入论文，必须由后续 **clean-provenance 覆盖重跑**（定义见 §4）回填。

---

## 1. 本次 Run 元信息

| 项 | 值 |
|---|---|
| 启动时间 | 2026-04-18 21:32:43 CST |
| 远端 tmux | `phase2_a_chain` |
| CLI | `bash scripts/phase2_a_scheme_rerun.sh --from wave1 --to wave6 --gpus 0,1,2` |
| 预估完成 | 2026-04-19 03:30–04:00 CST（6 h wall-clock）|
| 产出根 | `artifacts/2026-04-18/phase2_a_scheme_rerun/` + 7 wave out_dirs |

---

## 2. 代码 provenance

### 2.1 本地 git 状态（commit pin）

- **Base commit**: `b6d4e54 fix: harden phase2 a-scheme rerun chain`
- **Tracked**: Step 0 全部修复均已 commit 入 b6d4e54
  - `src/quant/_common.py` 含 `_infer_scale_heads` (B2 fix) ✅
  - `scripts/calibrate_behavior.py` 含 `allow_abbrev=False` + `--calib_out` required (B1b/B1c) ✅
  - `scripts/phase2_calibrate_{14b,mistral7b,3b}.sh` 改 `--calib_out` (B1a) ✅
  - `scripts/phase2_gate_lib.sh` pipefail-safe ✅
  - `scripts/phase2_a_scheme_rerun.sh` orchestrator ✅
  - `docs/phase2_6_{contamination_audit,int8_ours_known_issue}.md` A 口径 ✅

### 2.2 本地 vs 远端 MD5 校验（2026-04-18 21:45）

18 个关键路径（16 shell + 1 src + 1 Python）**全部 MATCH**：

```
MATCH  scripts/phase2_a_scheme_rerun.sh
MATCH  scripts/phase2_gate_lib.sh
MATCH  scripts/phase2_c2b_llama8b_extended.sh
MATCH  scripts/phase2_gen_sweep_policies_8b_extended.sh
MATCH  scripts/phase2_7b_random_hardening.sh
MATCH  scripts/phase2_gen_random_seeds_7b.sh
MATCH  scripts/phase2_calibrate_14b.sh
MATCH  scripts/phase2_gen_sweep_policies_14b.sh
MATCH  scripts/phase2_c3_qwen14b.sh
MATCH  scripts/phase2_gen_sweep_policies_mistral7b.sh
MATCH  scripts/phase2_c4_mistral7b_full.sh
MATCH  scripts/phase2_batch4_extend_tasks_7b.sh
MATCH  scripts/phase2_batch5_extend_tasks_8b.sh
MATCH  scripts/phase2_calibrate_3b.sh
MATCH  scripts/phase2_gen_sweep_policies_3b.sh
MATCH  scripts/phase2_c5_qwen3b.sh
MATCH  src/quant/_common.py
MATCH  scripts/calibrate_behavior.py
```

→ **远端跑的字节级等同于本地 b6d4e54 工作树**。

### 2.3 Provenance 缺陷项（2026-04-18 22:00 Codex 纠偏后修订）

尽管 2.1/2.2 MD5 看起来干净，**真实远端状态**让本次 run **不够干净**：

| # | 缺陷 | 影响 |
|---|---|---|
| **P1 (纠偏版)** | **远端 git HEAD = `fa6ab12 feat(A1): add smoke_test.py and collect_env.py for Milestone A`，不是 b6d4e54**。b6d4e54 虽已 push 到 origin，但远端执行的**不是** `git checkout b6d4e54` 的 clean worktree，而是 "fa6ab12 + rsync 18 文件 + 累积 295 dirty + 249 untracked"。rsync 部分 provenance 只覆盖显式同步的文件 | 非 rsync 文件的状态需要逐一 MD5 核查（见 P1b）|
| **P1b** | Critical runtime 13 文件 MD5 对比结果：**12 MATCH + 1 DIFF**（`src/engine/patch_model.py`：local `fe85847…` vs remote `1c9a405…`）。其他 12 文件（含 `generate_loop.py` / `eval_longbench.py` / 8 个 cache/quant 核心）均与 local b6d4e54 字节一致 | patch_model.py drift 是**既存**远端 drift（非本次引入）；Wave 2 sanity + Mistral smoke 都已在该状态 PASS，说明运行层面可用 |
| P2 | 本地 `working tree` 仍有 7 M + ~30 untracked；**其中 eval_longbench/generate_loop/mixed_kv_cache 等核心文件经 MD5 反而 MATCH**（它们 git 看似 dirty，但实际内容等于 b6d4e54；可能是 CRLF / trailing 等元数据差异）| 工作树 git-dirty 但语义一致，需 `git diff` 逐个确认 |
| P3 | Calib 文件（`kv_calib_kl_{qwen25_14b,mistral7b,qwen25_3b_int8}.json`）**来自污染窗口**（2026-04-18 15:50–16:00）| metadata 正确 + B2 runtime 校验兜底 + Mistral smoke 已验证行为非 degenerate，但纪律上应在干净 wrapper 下重产 |
| P4 | 旧 quarantine 目录（`*_20260418_quarantine/`）**未进入 git 也未进入远端长期归档** | 审计链只能靠本地 MANIFEST.md，不可跨机复现 |

**重要纠偏**：初版 manifest 把 P1 错写为 "b6d4e54 未 push"。真实问题是 **rsync-based partial deployment** 而非 push 缺失。

---

## 3. 本次 run 的定位：**Exploratory**（数据可用，claim 不可依赖）

本次 run 的产物**可用于**：
- ✅ 验证 B1+B2 修复在 end-to-end 6 h 大规模 run 下稳定（工程结论）
- ✅ 观察 scale × aggregation regime 在 5 model × 7 task 空间的 qualitative 模式
- ✅ 发现新现象 / 驱动后续 plan 调整

本次 run 的产物**不得用于**：
- ❌ 论文最终主表数字（除非 §4 clean-provenance 覆盖重跑回填）
- ❌ 单独作为 publishable claim 的唯一证据
- ❌ 声称"跨模型完整实验"的 gold-standard

---

## 4. Clean-Provenance 覆盖重跑（Phase 2.6B，未来执行）

### 4.1 Pre-requisites（覆盖重跑启动前必做）

1. **Git pin + clean checkout at remote**（**核心**）：
   - 本地：`git add` + `git commit` + `git tag phase2.6-a-scheme-v1`
   - 本地：`git push origin main phase2.6-a-scheme-v1`
   - 远端：`cd /root/LLM_KVCache_Quantization && git fetch && git stash && git checkout <pin_commit>`
   - 远端：验证 `git status --short | wc -l` → 理想 = 0（或极少量特定产物目录）
   - → **整个 worktree 与 pin_commit 字节一致**（而非本次 run 的 "rsync 18 文件 + base commit 漂移"）

2. **重新 calibrate 5 模型**（用修好的 wrapper，干净路径）：
   - `bash scripts/phase2_calibrate_14b.sh`（wave4 会 SKIP if calib exists → 先 `rm artifacts/kv_calib_kl_qwen25_14b_int8.json`）
   - `bash scripts/phase2_calibrate_mistral7b.sh`（同）
   - `bash scripts/phase2_calibrate_3b.sh`（同）
   - 1.5B 和 7B 已有历史干净 calib（Feb/Mar），可保留
   - 8B calib (`kv_calib_kl_llama31_8b_int8.json`)：来自 Apr 18 08:44，**早于污染窗口**，可保留

3. **Quarantine 旧产物进 git/archive**：
   - `git add results/*_20260418_quarantine/MANIFEST.md`（只 commit MANIFEST）
   - 或 tar 归档到 `archive/phase2.6_quarantine_20260418.tar.gz`

4. **Clean checkout 验证**：
   - 在干净 worktree `git clone ...` 然后 `git checkout <pin_commit>`
   - 完整 rsync 干净脚本 + 重新 calibrated 的 calib 文件

### 4.2 覆盖重跑 CLI

```bash
# (假设在干净 worktree 下)
tmux new-session -d -s phase2_a_chain_clean \
  'cd /root/LLM_KVCache_Quantization && \
   bash scripts/phase2_a_scheme_rerun.sh --from wave1 --to wave6 --gpus 0,1,2 \
   2>&1 | tee artifacts/$(date +%F)/phase2_a_scheme_rerun_clean.log'
```

### 4.3 覆盖重跑完成后交叉对齐

- 对比 `phase2_a_chain` (exploratory) 与 `phase2_a_chain_clean` (gold) 的 6 wave metric，检查：
  - gate 项是否都 PASS（CSV count / Traceback / head-mismatch / failed metric）
  - official_metric_value 在 **noise floor** 内一致（±1% 是 deterministic greedy 的合理阈值）
- 若一致 → exploratory 结论由 gold 背书，可用于主表
- 若不一致 → 记录差异来源（P1-P4 哪一项）并重新分析

---

## 5. 本文档的提交策略

- 本 manifest 本身 → 下一个 commit（`docs(phase2.6): provenance manifest for A-scheme exploratory run`）
- 全部 Step 0 相关变化一起 push 到 origin
- 若 origin 未设，先记录"pending push"于 iteration.md

---

## 6. 签名

- 生成时间：2026-04-18 21:45 CST（22:00 Codex 纠偏版本）
- 生成工具：手动（Claude 协助）+ MD5 机器校验
- 对应 run：`phase2_a_chain` in tmux, started 21:32:43
- Intended base commit：`b6d4e54 fix: harden phase2 a-scheme rerun chain`（已 push 到 origin）
- **实际远端状态**：`HEAD=fa6ab12` + rsync 了 18 orchestrator 文件 + 既存工作树漂移（其中 12/13 critical runtime 文件与 b6d4e54 一致，`patch_model.py` drift 1 个）
- 本 manifest 是 Codex 建议 "dirty-main run with rsynced scripts matching local b6d4e54" 的落地版本；22:00 纠偏后从"orchestrator-path-pinned, remote-unpushed"修正为"rsync-based partial provenance over fa6ab12 base, 12/13 critical runtime MATCH b6d4e54, 1 drift (patch_model.py), pushed-but-not-checked-out"
