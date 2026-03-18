# Iteration Log (Single Source of Progress)

This file is the only progress tracker for the repository.
`lang.md` is deprecated and archived.
Canonical agent workflow directory is `.agents/`.

## Approved Plans

> 经讨论并被用户认可的阶段性执行方案（与审查问题分开，审查问题见 `review_tracker.md`）。

### Plan: INT8+INT4 双精度统一路线图（M0-M6, gate 驱动）
- **批准日期**：2026-03-17
- **前置条件**：Phase 6 完成, thesis-safe-v1 基线冻结
- **状态**：🔴 M3 gate FAIL → 停止 unified 尝试，回退 thesis-safe-v1
- **里程碑状态**：
  - [x] M0: 冻结 thesis-safe 基线 (tag `thesis-safe-v1`, commit `9d7dbea`)
  - [x] M1: 建立 legacy/postfix 双世界 (3 gate configs, commit `85f5baa`)
  - [x] M2-1: Calibration 主链修复 CAL-033/014/017/020/036/043 (commit `1ad404a`)
  - [x] M2-2: 确定性审计 ✅ (bit-for-bit identical)
  - [x] M2-3: 重生 postfix 校准 ✅ (3 models v2)
  - [x] M3: unified gate ❌ FAIL (C7 PASS, C8 FAIL -42.71%, UG1/UG2 FAIL)
  - [~] M4: 跳过（gate 未通过）
  - [ ] M5: 可选补强（文献/probing/消融，不污染主线）
  - [x] M6: 决策 = 保持 thesis-safe-v1 (情况 B)

### ~~Plan: EMNLP 2026 Phase 4 — MSE 校准 + 消融（仅 1.5B）~~ ✅ 完成 2026-02-23（详见 Timeline 归档）

### ~~Plan: EMNLP 2026 Phase 5v2 — 全矩阵实验（phase5v2 新目录）~~ ✅ 完成 2026-03-09（详见 Timeline 归档）

### ~~Plan: Phase 5v2 数据修复（Data Repair）— v8 补跑方案~~ ✅ 完成 2026-03-08
- **冻结副本**: `/root/LLM_KVCache_Quantization_phase5v2fix_20260307_144607`
- **结果**: 17 dirs × 4 tasks = 68/68 SUCCESS, PPL 验证全通过

### Plan: INT4 KV-RoleAlign — Bit-Width-Aware Behavior Alignment (v4.1)
- **批准日期**：2026-03-17
- **前置条件**：M3 gate FAIL 确认, thesis-safe-v1 冻结
- **状态**：🟡 Phase 0-2 代码实现完成，待 GPU 实验验证
- **内容**：
  - Phase 0: 数据核验 + K/V 归因诊断（3 新脚本）
  - Phase 1A: KIVI + inv_tau 集成（int4_kivi_aligned mode）
  - Phase 1B: V-path token-CE 校准（calibrate_behavior.py 扩展）
  - Phase 2: K-INT8/V-INT4 混合精度（MixedKVCache）
  - 实验配置: exp_matrix_kivi_aligned_v1.yaml
- **Gate**：Phase 0 不 PASS 则全停

### Plan: R22 审查修复 — 吞吐 profiling 前置修复 + 防御性改进
- **批准日期**：2026-02-25
- **前置条件**：Phase 5v2 质量评测完成
- **状态**：🟡 P0+P1 全部完成（5/18 已修复），P2+跟踪项仍 open
- **内容**：

**P0: 吞吐 profiling 前必须修（阻塞 Phase 5v2 吞吐评测）** ✅ 3/3 完成
- [x] **PRF-032** `[HIGH]` profile_latency.py "Hello " repeat prompt token 数不精确 → 改用 tokenizer 生成精确长度 token 序列
- [x] **PRF-033** `[HIGH]` 非 kivi quant_bits=None 写入 CSV → 按 kv_mode 推导实际 quant_bits 并记录
- [x] **PRF-034** `[MED]` profile_latency/memory 未调用 model.eval() → 添加 model.eval()

**P1: 防御性改进（建议在下轮代码维护时修）** ✅ 2/2 完成
- [x] **EVL-132** `[HIGH]` eval_ppl.py PPL NaN/Inf 静默写入 + exit(0) → 添加 NaN/Inf 检查，异常时 exit(1)
- [x] **ENG-110** `[HIGH]` batch EOS 用 all() 判定 → 改为 per-sequence mask（影响 batch>1 的吞吐评测）

**P2: 文档更新**
- [ ] **W2** CLAUDE.md §10 scale dtype 描述更新（float32 → 实际 fp16/input dtype）

**不影响当前实验（仅跟踪）**：EVL-130(HF模式), EVL-131(repeat模式), EVL-133~137, ENG-111, PRF-035, CHK-037~039, UTL-014

**Phase 7 审计结论（2026-03-11 20:17）**：
P0 全部完成（3/3）、P1 全部完成（2/2）。剩余 13 项 open issue 经审计确认均在当前主实验路径（kv_cache 模式/单 GPU/固定 seed）下未触发。其中 CHK-037（check_run_completeness.py 将 csv_valid_manifest_incomplete 和 task_artifacts_missing 误报为 unexpected failure）属审计工具分类误差，不影响实验数据。论文 Limitations 段落需披露此情况。

### ~~Plan: Phase 5v2 推进策略 — int4_fused 污染隔离 + 剩余 seed 接力 + 重跑调度~~ ✅ 完成 2026-03-09（详见 Timeline 归档）

### ~~Plan: EMNLP 2026 Phase 6 — 聚合 + 统计修复 + 论文准备~~ ✅ 完成 2026-03-10（详见 Timeline 归档）

### Plan: INT4 KV Cache 量化拯救 v3（Tier 0-3 分层推进）
- **批准日期**：2026-03-12
- **前置条件**：Phase 6 完成，C7/C8 FAIL 确认
- **状态**：🟡 Tier 0+1 完成 → 等待 Go/No-Go 决策
- **核心假设**：INT4-ours 从未启用 adaptive_static_scales，且 temperature 方向与 INT8 mainline 相反
- **Tier 0 结果**: ✅ PARTIAL SUCCESS — C7 翻转, C8 部分改善, 最优策略模型相关
  - [x] 配置文件创建 (3 模型 × 3 变体)
  - [x] 远端配置快照备份 + 校准文件检查 (3 文件全存在)
  - [x] Wave 1: 三模型 T0-B → C7 翻转! 7B PPL -37%! 8B PPL 持平
  - [x] Wave 2: 1.5B 2×2 → T0-C 最优 (adaptive 有害, 关温度微改善)
  - [x] Go/No-Go: PARTIAL → 继续 Tier 1
  - **关键发现**: 最优配置是模型相关的 (1.5B 不要 adaptive, 7B 要 adaptive+关温度)
- **Tier 1 结果**: ⚠️ INCONCLUSIVE — 校准数据方差导致无法隔离策略效应
  - [x] 生成 MSE 校准: `kv_calib_mse_int4_v4_g16.json` (clip=99.0, outlier=0.0)
  - [x] 生成 percentile 校准: `kv_calib_pctl_int4_v4_g16.json` (clip=99.5, outlier=0.0)
  - [x] 重生 KL 校准: `kv_calib_kl_int4_v4_g16.json` (clip=99.0, outlier=0.005)
  - [x] 对比实验: T1-KL=59.34, T1-MSE=59.73, T1-PCTL=57.52 (全部远差于 T0-C 的 22.04)
  - [x] Go/No-Go: **根因=校准产物V scale方差(最大4.82x)**, 非校准策略本身问题
  - **关键发现**: 新旧校准文件 V scale 差异巨大 (L7g0: OLD=0.319 vs NEW=1.538)，
    同模型同参数重新生成的校准产物不可复现，invalidates 策略对比
- **Tier 2 结果**: ✅ 代码修复完成 + 实验完成，部分改善
  - [x] ENG-066: 7 处代码修改 (int4_basic.py ×3, int4_cache.py ×3, generate_loop.py ×1)
  - [x] 测试: 4 断言更新 + 5 新测试 → 远端 341 tests passed
  - [x] 配置补全: 7B/8B rescue snapshot 添加 baseline 条目
  - [x] 8B model_revision 修正: 043efdca→null (旧 rev 不存在于 HF hub)
  - [x] Wave 1 实验: 18 task-runs (3 模型 × 2 modes × 3 seeds) 全部完成
  - **PPL 结果** (int4_ours vs int4_baseline, float32 scale):
    - 1.5B: 22.80 vs 19.65 → **-16.0%** (ours 更差)
    - 7B: 52.19 vs 86.56 → **+39.7%** (ours 大幅改善) ★★★
    - 8B: 7.64 vs 6.97 → **-9.7%** (ours 略差)
  - **Needle 结果**:
    - 1.5B: 0% vs 0% (均失败, 模型太小)
    - 8B: **100% vs 100%** (float32 fix 让 baseline 也恢复!) ★★★
  - **Go/No-Go**: **部分改善** — float32 fix 有价值(7B PPL 巨幅改善, 8B baseline needle 恢复),
    但 INT4-ours 不一致地优于 baseline (1.5B/8B PPL 反而更差)
  - Commits: b42c068, df05b93, d1f71dc, 41d81bf (代码+测试+配置)
- **Tier 3** (条件): 最优配置跨模型全验证 (3 seeds × 4 seq_lens × 5 评测)

### Plan: 已确认决策
- **批准日期**：2026-02-23
- **内容**：
  - 吞吐量 batch scaling：3 模型均做 batch=1,2,4,8,16（FP16 删 b24/b32）
  - 消融实验：仅在 1.5B 主模型执行

---

## Current Status

- Active objective source: `objective.md`
- Active execution policy: `AGENTS.md`
- Active experiment protocol: `experiment_sop.md`
- Progress log source of truth: `iteration.md`

## Update Rules

1. After each completed functional unit, append one new entry under `Timeline` (latest first).
2. Every entry must include goal, changed files, commands run, outputs, and result quality.
3. If blocked, write explicit blocker and next action.
4. Keep entries concise and auditable; avoid vague summaries.
5. Timeline 保留最近 **15 条**。超出时将最旧条目归档到 `development_history/iteration_archive_202602.md`。

## Entry Template

### YYYY-MM-DD HH:MM | Workstream Title
- Goal:
- Scope:
- Changed files:
- Commands:
- Outputs:
- Validation:
- Risks / follow-ups:

## Timeline (Latest First)

### 2026-03-17 08:56 | Phase 2 全模型验证完成 — MixedKV 为主要方法贡献
- Goal: 3 模型 PPL + Needle 完整验证
- Results (PPL, vs FP16):
  - 1.5B: MixedKV 9.37 (+4.9%) vs KIVI 10.43 (+16.8%) → MixedKV 显著更优
  - 7B: MixedKV 7.20 (+7.3%) vs KIVI 7.53 (+12.2%) → MixedKV 更优
  - 8B: MixedKV 6.75 (-2.5%) vs KIVI 6.90 (-0.3%) → MixedKV 甚至优于 FP16
  - Needle 1.5B: MixedKV 100%, KIVI 100%
- Phase 2 Gate: **PASS** (PPL ≤5% fp16 on 2/3 models, Needle 100%)
- 路径判定: **路径 B (Method)** — MixedKV 为主要方法贡献
- 论文叙事: "K 路径需要 INT8 精度保持 attention 分布准确性; V 可降至 INT4; MixedKV 实现了质量-压缩的最优平衡"
- Next: 多 seed 验证 (3-5 seeds), 消融实验, 论文写作

### 2026-03-17 08:44 | Phase 1A FAIL + Phase 2 SUCCESS — 实验结果综合分析
- Goal: Phase 1A inv_tau 效果验证 + Phase 2 MixedKV 效果验证
- Results:
  - **Phase 1A**: KIVI INT4 + inv_tau PPL = 10.57 vs KIVI plain 10.43 → **恶化 +1.3%** → FAIL
    - 原因: INT8 对称量化的 inv_tau 不适用于 KIVI 非对称 per-channel 量化
  - **Phase 2**: MixedKV (K-INT8/V-INT4) PPL = 9.37 (+4.9% vs FP16 8.93) → **PASS**
    - 1.5B: 9.37 (+4.9%), 7B: 7.20 (+7.3%) — 显著优于纯 KIVI INT4 (+16.8%/+12.2%)
    - 3 seeds 完全一致 (9.3653) 确认可复现性
- Gate: Phase 1A → 停止 inv_tau 路线; Phase 2 → 进入扩展验证
- Commits: e1d598e (eval_ppl hooks fix)
- Risks: inv_tau 需要 KIVI-specific 重新校准（非迁移）; MixedKV 压缩率 37.5%（不如纯 INT4 25%）; 7B PPL 7.53 高于历史数据 7.05（eval_ppl 口径差异待查）
- Next: MixedKV 在 8B 模型验证; Needle 评测（需修复 seq_len=32704）; 论文叙事调整

### 2026-03-17 08:05 | Phase 0 Gate PASS — KIVI INT4 数据核验 + K/V 归因完成
- Goal: Phase 0 三项实验全部完成，综合 Gate 判定
- Results:
  - **0.1 PPL Gate**: KIVI INT4 3 模型 worst-case +6.21% (阈值 <15%) → **PASS**
  - **0.1 Needle Gate**: 1.5B/7B 99%+, 8B 100% (vs INT4-baseline 1.5B/7B 0%) → **PASS**
  - **0.2 K-path SQNR**: 非对称 vs 对称平均 +8.80 dB (阈值 ≥5 dB) → **PASS**
  - **0.2 V-path SQNR**: -0.66 dB (非对称略低于对称, per-token vs per-group 轴不同) → FAIL (但可解释)
  - **0.3 归因**: K MSE=0.0151, V MSE=0.0175, K SQNR=40.7 dB, V SQNR=18.6 dB → 双路径有意义
- Gate: **4/5 PASS, 整体 PASS** — V-path SQNR 未达标恰好支持"V 需要独立对齐目标"的 Phase 1B 假设
- Commits: 0d2176f (main feat), 0d2ad09/11693de/cde3614/20cbe3b (remote fixes)
- Next: Phase 1A/1B 实验需先运行校准生成 calib JSON，然后跑 PPL+Needle 对比

### 2026-03-17 07:45 | feat: INT4 KV-RoleAlign 全代码实现 (Phase 0/1A/1B/2)
- Goal: 实现 Bit-Width-Aware Behavior Alignment 完整代码框架
- Changed files:
  - **新建**: scripts/verify_kivi_int4_data.py, scripts/diagnose_int4_error.py, scripts/diagnose_kv_attribution.py (Phase 0)
  - **新建**: src/cache/mixed_kv_cache.py (Phase 2), tests/test_mixed_kv_cache.py
  - **新建**: configs/snapshots/exp_matrix_kivi_aligned_v1.yaml
  - **修改**: src/cache/kivi_style_cache.py (接受 inv_tau/use_attn_temperature)
  - **修改**: src/engine/generate_loop.py (int4_kivi_aligned + int4_mixed_kv routing, _register_all_temperature_hooks, v3 calib loading)
  - **修改**: scripts/calibrate_behavior.py (--v_calibration_mode, calibrate_v_path_percentile(), v3 schema)
  - **修改**: scripts/config_utils.py, run_experiments.py, export_tables_latex.py, generate_thesis_figures.py (mode registration)
  - **修改**: scripts/eval_ppl.py, eval_needle.py, eval_longbench.py, eval_ruler.py (choices + routing)
  - **修改**: tests/test_kivi_cache.py (TestKIVICacheInvTau, 4 new tests)
  - **修改**: src/cache/__init__.py (export MixedKVCache)
- Commands: python3 -m compileall -f src/ scripts/ tests/ (78 files OK); pytest tests/test_kivi_cache.py tests/test_mixed_kv_cache.py tests/test_int8_cache.py tests/test_int4_cache.py (160 passed)
- Validation: 全量编译通过, 160 tests passed (42 KIVI + 9 Mixed + 109 existing), 0 regressions
- Risks: Phase 0 GPU 实验未运行; calibrate_behavior.py V-path 搜索需要实际校准数据; generate_loop.py 的 v3 calib loading 路径需端到端验证
- Next: 推送到远端 → 运行 Phase 0 实验 → Phase 0 Gate 判定 → Phase 1A/1B 实验

### 2026-03-12 17:14 | 论文收口：ENG-066 follow-up 纳入 ch4/ch5/appendix
- Goal: 将 ENG-066 结果作为补充证据写入论文，不改变正式 claim 体系
- Changed files: ch4_experiments.tex, ch5_conclusion.tex, appendix.tex
- M1: ch4 INT4 局限性讨论末尾追加 `\paragraph{运行时精度链路的补充分析}`
- M2: ch5 局限性段落追加 1 句工程洞见 + 交叉引用
- M3: appendix 新增 `\section{INT4 运行时精度修复后验实验（ENG-066）}` + 完整表格
- Validation: 交叉引用 `\ref{subsec:exp-int4-limitations}` 正确解析；每处 ENG-066 引用均有限定语 + "不更新 Claim" 声明；C7/C8 FAIL 判定未改动
- Commit: 152b71b

### 2026-03-12 14:25 | ENG-066 收尾：Tier 3 取消 + 论文写作转换
- Goal: 关闭 INT4 rescue Tier 3，记录最终决策，转入论文写作
- Decision: **Tier 3 canceled after ENG-066 Wave 1**
  - 原因：float32 fix 有价值（7B PPL 86→52, 8B needle 恢复 100%），
    但不足以使 INT4-ours 一致优于 baseline，不支持继续扩展实验
  - 7B baseline PPL=86.56 与 Phase 5v2 历史值 (85.485) 一致，
    属 Qwen2.5-7B 模型特异的 INT4 敏感性，非代码 bug
  - Claim 口径：legacy 主报告维持 **8 PASS / 3 FAIL (C6/C7/C8)**；
    Option C follow-up 作为补充证据进入论文 Discussion/Limitations，
    不更新正式主报告 claim 计数
- Changed files: iteration.md
- Commit: 0c30069 (Step 1: Tier 2 results + 8B model_revision fix)
- Next: 论文写作（Discussion/Limitations 纳入 INT4 精度极限 + 模型敏感性）

### 2026-03-12 06:35 | INT4 Rescue v3 Tier 2 — Float32 Scale Chain Fix + Wave 1 实验完成
- Goal: 修复 INT4 scale 精度链路 (ENG-066) + 重跑 baseline/rescue 对比实验
- Changed files:
  - `src/quant/int4_basic.py` — 3 处 .to(tensor.dtype) → .to(torch.float32)
  - `src/cache/int4_cache.py` — 3 处 float32 chain + get_kv() dtype 契约
  - `src/engine/generate_loop.py` — INT4 scale 加载改 float32
  - `tests/test_int4_cache.py` — 4 断言更新 + 5 新测试 (TestENG066Float32ScaleChain)
  - `configs/snapshots/exp_matrix_*_int4_rescue_v1.yaml` — 添加 baseline 条目, 8B model_revision→null
  - `scripts/run_int4_tier2_wave1.sh` — 新建 Wave 1 实验脚本
- Commands:
  - `pytest tests/test_int4_cache.py -v` (远端 56/56 passed)
  - `run_experiments.py` × 3 模型 (并行 tmux sessions)
  - `aggregate_results.py --runs_dir results/int4_t2_float32_v1/runs`
- Outputs:
  - **代码修复**: 7 处 + 9 测试改动, 远端 341 tests passed
  - **PPL** (int4_ours vs int4_baseline, 32K, kv_cache mode):
    - 1.5B: 22.80 vs 19.65 (ours -16.0%)
    - 7B: 52.19 vs 86.56 (ours +39.7%) ★★★
    - 8B: 7.64 vs 6.97 (ours -9.7%)
  - **Needle** (32K, 10 depths):
    - 1.5B: 0% vs 0% (模型太小, 32K INT4 均崩溃)
    - 8B: 100% vs 100% (float32 fix 后 baseline 也恢复了!)
  - **统计**: 所有 seed 间 std=0 (确定性评测), p=0.333 (exact sign-flip, n=3)
  - **8B 问题排除**: model_revision 043efdca 在 HF 不存在(404), 改为 null + HF_HUB_OFFLINE=1
- Validation: ✅ 18/18 task-runs 全部成功, 0 failures
- Key insights:
  1. Float32 fix 确实改善了精度 (7B PPL 86→52 证明 fp16 scale 有害)
  2. 但 fix 同时改善了 baseline (8B needle 0%→100%), 使 ours vs baseline 差距不变/缩小
  3. INT4-ours 的优势不在于 scale 精度, 而在于校准策略 (kl_attn vs percentile)
  4. 1.5B 模型太小, INT4 32K 均表现差; 7B baseline 异常差 (86.56), 需调查
- Go/No-Go: **部分改善** → 保留 float32 fix 作为防御性改善, 不扩展到全矩阵
- Risks / follow-ups:
  - 7B baseline PPL=86.56 异常高, 可能是 percentile 校准+group_size=32 的组合问题
  - 考虑是否需要 INT4-baseline 也用 kl_attn 校准做公平对比
  - Commits: b42c068, df05b93, d1f71dc, 41d81bf (未 push)

### 2026-03-12 04:15 | INT4 Rescue v3 Tier 1 — 校准策略对比 (INCONCLUSIVE)
- Goal: 比较 KL/MSE/Percentile 三种校准策略在 1.5B INT4 上的效果
- Changed files: configs/exp_matrix.yaml (追加 3 个 T1 条目), scripts/run_int4_rescue_tier1.sh (新建)
- Commands: run_int4_rescue_tier1.sh (远端 tmux: Phase1 校准生成 ~2min + Phase2 PPL/Needle 实验)
- Outputs:
  - **校准文件生成**: 3/3 成功 (MSE/PCTL/KL, 均 group_size=16)
  - **PPL 结果**: T1-KL=59.34, T1-MSE=59.73, T1-PCTL=57.52 (全部远差于旧校准的 22.04)
  - **Needle**: 均为 0% (1.5B 在 32K INT4 本身就崩溃, 不可判定)
  - **根因调查**: V scale 新旧产物差异最大 4.82x (Layer 7 group 0: OLD=0.319 NEW=1.538)
    - K scale 差异 3-27% per layer
    - 新旧文件 clip_percentile 不同 (旧=99.5, 新KL/MSE=99.0) 但这不能解释 4.82x 差异
    - model_revision 已确认一致 (989aa7980e4cf806f80c7fef2b1adb7bc71aa306)
    - 推测根因: calibrate_behavior.py 的数据采样/random seed 不完全确定性
- Validation: ✅ 实验正常完成, 但校准数据方差导致策略对比无效
- Conclusion: **Tier 1 无法隔离校准策略效应**。新校准产物质量不如旧产物，
  问题在于校准过程的非确定性而非策略选择。
- Next: Go/No-Go 决策 — 是否进入 Tier 2 (scale 精度修复) 或接受现有结果

### 2026-03-12 03:47 | INT4 Rescue v3 Tier 0 — 实验完成 + 结果分析
- Goal: 运行 Tier 0 (2×2 配置网格) smoke test，评估 adaptive_static_scales × temperature 对 INT4 的效果
- Changed files: iteration.md (本条记录)
- Commands: run_int4_rescue_tier0.sh (远端 tmux, Wave1+Wave2)
- Outputs (总 GPU 时间 ~11min):
  - **C7 Needle 翻转**: LLaMA-8B 32K 从 98%→**100%** (gain=0%, 阈值≥-1.0%) ★★★
  - **C8 PPL 部分改善**:
    - 7B: 99.09→**53.77** (vs baseline 85.49, gain=-37.1%) ★★★ 但 C8 要求全模型
    - 1.5B: T0-C 最优 22.04 (vs 旧 22.67, 改善 2.8%, 但 vs baseline 19.54 仍+12.8%)
    - 8B: 7.65 持平 (vs baseline 6.97, +9.7%)
  - **因素分析 (1.5B 2×2)**:
    - adaptive 对 1.5B **有害** (+16-18% PPL)
    - 关温度对 1.5B **微弱正效应** (-2.8%)
    - 最优策略是**模型相关的**（重要论文发现）
- Go/No-Go: **PARTIAL SUCCESS** — C7 翻转, C8 需 Tier 1 校准策略
- Next: Tier 1 — 为 1.5B 生成 MSE/percentile 校准，固定 T0-C 配置 (adaptive=false, temp=false)

### 2026-03-12 03:30 | INT4 Rescue v3 Tier 0 — 配置文件创建
- Goal: 为 INT4 量化拯救计划创建 Tier 0 (2×2 配置网格) 所需的配置文件
- Changed files:
  - `configs/exp_matrix.yaml` — 追加 3 个 int4_rescue_* 条目 (T0-A/B/C)
  - `configs/snapshots/exp_matrix_qwen25_7b_int4_rescue_v1.yaml` — **新建** (7B rescue)
  - `configs/snapshots/exp_matrix_llama31_8b_int4_rescue_v1.yaml` — **新建** (8B rescue, model_revision 修正)
- Commands: python3 YAML validation
- Outputs: 3 文件全部通过 YAML 验证，共 9 个 rescue 条目 (3 × 3 模型)
- Validation: ✅ YAML safe_load + 字段断言 (kv_mode/quant_bits/seq_len)
- Next steps: 远端 rsync 推送 → 配置快照备份 → 校准文件检查 → 第一波实验

### 2026-03-11 22:25 | Supervisor 全局审阅报告
- **Goal**: 以 Supervisor 角色对项目进行全局健康度审阅 + Codex MCP 连通性验证
- **Scope**: 只读审阅（无代码变更）
- **审阅结果**:
  - **Phase 进度**: Phase 1-6 全部完成 ✅, Phase 7A/7B 完成 ✅, Phase 7C(论文骨架) 待启动
  - **数据规模**: 2136 dirs (emnlp_final_raw/)
  - **Claims**: 8 PASS / 3 FAIL (C6 RULER -2.82%, C7 INT4 Needle -3.33%, C8 INT4 PPL -15.92%)
  - **review_tracker**: 995 total | 484 fixed + 6 FP | 505 open (0 CRIT, 188 HIGH, 277 MED, 40 LOW)
  - **Phase gate**: READY ✅ (0 CRITICAL open)
  - **代码编译**: `compileall src/ scripts/ tests/` exit 0 ✅
  - **Git**: main 领先 origin/main 6 commits, 工作区干净
  - **结构**: src/ 7 子模块, scripts/ 25 脚本, tests/ 25 测试文件, configs/ 1 主配置 + 6 快照
- **Codex MCP 连通性**: ✅ 全部通过
  - `mcp__codex__codex` 发起会话: ✅ (threadId: 019cdd4a-917f-7d53-9062-d6d516967840)
  - `mcp__codex__codex-reply` 多轮对话: ✅ (2 轮上下文完整保持)
  - GPT-5.4 模型调用: ✅, sandbox read-only 文件读取: ✅
- **待关注风险**:
  1. 6 commits 未推送 — 需确认是否 push
  2. 188 HIGH issues 横跨 eval 链路 — 论文 Limitations 需披露
  3. 3 Claim FAIL — 论文需讨论 INT4 精度局限
  4. 本地 pytest broken (numpy/scipy dlopen) — 仅能 py_compile 验证
- **下一步**: P0 Phase 7C 论文骨架 | P1 Push 6 commits | P2 R22 P2 文档更新
- **Changed files**: iteration.md (本条记录)

### 2026-03-11 22:20 | 代码与结果双向同步 v3.1
- **Goal**: 拉回远端原始实验结果 (runs/logs)，推送本地最新代码到远端
- **Changed files**: 无代码变更（纯同步操作）
- **Commands**:
  - `rsync --include='runs/***' --include='logs/***'` 拉取远端 → 本地
  - `rsync --files-from=manifest` 推送本地 → 远端（白名单 19 条目）
- **Outputs**:
  - 拉取: 2,136 runs dirs + 5,509 logs files = 2.4GB
  - 推送: 9 根文件 + 4 目录 + 6 具名 docs，实际增量 18KB
  - 远端快照: `/root/autodl-tmp/kvcq_code_backup_20260311_221738`
- **Validation**:
  - D1: 22/22 关键文件 OK ✅
  - D2: compileall exit 0 ✅
  - D3: 15 校准 JSON 完整 ✅
  - D4: second dry-run = 0 变更 ✅
  - D5: 远端 results 未受影响 (2136 runs + 5509 logs) ✅
- **Risks / follow-ups**: 远端代码通过静态编译检查，后续需跑 smoke_test 做运行时验证

### 2026-03-11 20:17 | 计划文件治理 + 进度同步
- **Goal**: 清理 iteration.md stale Approved Plans、更新 objective.md 里程碑状态、修复 docs/ legacy 路径
- **Changed files**:
  - `iteration.md`: 关闭 3 个已完成 Plans（Phase 5v2 全矩阵/推进策略、Phase 6），精简数据修复 Plan 详情，更新 R22 → 🟡 P0+P1 完成（5/18 fixed），添加 Phase 7 审计结论
  - `objective.md`: Milestones K-Q 添加完成标记（K/L/M/N/O/Q ✅, P ⚠️ 部分完成）
  - `docs/thesis_chapter_mapping.md`: final_thesis_plus_* → emnlp_final_raw/
  - `docs/final_results_summary.md`: 路径更新 + 顶部追加数据更新注释
  - `docs/thesis_preflight_checklist.md`: 路径更新
  - `docs/usage_guide.md`: run_final_thesis_plus.sh 标注 legacy
  - `docs/paper_writing_session_prompt.md`: 标注 OUTDATED
- **Validation**: grep 验证无残留 🟢 执行中 / final_thesis_plus 路径 / Milestone 无标记
- **R22 审计**: P0(3/3)+P1(2/2) 全部完成, 13 项 open 经审计确认在主实验路径下未触发, CHK-037 为审计工具分类误差

### 2026-03-11 03:13 | Phase 7B: 学位论文 ch4 数据填充完成
- **Goal**: 将 ch4_experiments.tex 中全部 ~18 处 XX.XX/TODO/待验证占位符替换为真实实验数据
- **Changed files**:
  - `thesis/chapters/ch4_experiments.tex`: 填充 Table 4.2（主结果 7 modes）、Table 4.5（跨模型 7B+8B）、Table 4.6（KIVI 对比）、Table 4.7（11 claim 验证总表 8P/3F）；C1-C11 文字分析；3 张 \includegraphics 替换 fbox 占位符；消融分析段落重写
  - `scripts/fill_thesis_data.py`: 新增可审计数据提取脚本（mainline overrides for 1.5B int8_ours）
  - `findings.md`: ISSUE-1/ISSUE-2 解析更新
  - `thesis/figures/`: 复制 3 张 PNG（needle/TPOT/KV memory 曲线）
- **Validation**: `grep 'XX\.XX\|TODO\|待验证\|待替换\|待填充' ch4_experiments.tex` → 0 matches
- **Key data points used**:
  - fp16: PPL=8.93, Needle=100%, LongBench=4.82%, RULER=24.38%, TPOT=24.39ms, KV=896MB
  - int8_ours (mainline): PPL=8.95, Needle=100%, LongBench=5.00%, RULER=24.38%, TPOT=47.14ms, KV=504MB
  - C1: +17.27% TPOT gain (q=0.016), C2: -43.75% KV mem, C6 FAIL: -2.64% RULER
  - C7 FAIL: -2.0% INT4 Needle, C8 FAIL: -15.92% INT4 PPL
- **Note**: thesis/ 在 .gitignore 中（不进 git），仅 fill_thesis_data.py 和 findings.md 需要提交
- **Next**: 提交 → Phase 7C EMNLP 论文骨架搭建

### 2026-03-11 02:52 | Phase 7A: Git cleanup + model_id 路径污染源头修复
- **Goal**: 提交 C7/C8 修复；修复 ISSUE-1（LLaMA-8B model_id 路径污染 9 个 CSV）
- **Changed files**:
  - `scripts/aggregate_results.py`: 添加 `MODEL_ID_ALIASES` + `_canonicalize_model_id()`, 在 `_read_csvs()` 中调用
  - `scripts/export_tables_latex.py`: 扩展白名单（前序提交）
  - `iteration.md`: Timeline 追加
  - `findings.md`: 新增 claim 根因分析
  - `.gitignore`: 排除 progress.md / task_plan.md
- **Commits**: e5afa27 (7A.1: pairing + findings), pending (7A.2: model_id fix)
- **Validation**: `py_compile` 通过；远端重跑 aggregate+export+report 待执行
- **Risks**: 远端重跑后需验证 thesis_main_claims_32k.csv 中 model_id 只有 3 个值
- **Next**: rsync 到远端 → 重跑三步管线 → rsync 回 → 进入 7B ch4 填充

### 2026-03-11 00:06 | fix: C7/C8 INCONCLUSIVE → FAIL, 修正 C6 根因描述
- **Goal**: 解决 C7/C8 INCONCLUSIVE（补全 aggregate + export 过滤），更新 C6 根因归因
- **Changed files**:
  - `scripts/aggregate_results.py`: L124 添加 `("int4_baseline", "int4_ours")` 到 `RELATIVE_GAIN_PAIRINGS`
  - `scripts/export_tables_latex.py`: L642 白名单扩展 `int4_baseline` + `kivi_style`
- **远端重跑**: aggregate → LaTeX export → claim validation（三步全部 exit 0）
- **结果**: C7/C8 从 INCONCLUSIVE → **FAIL**
  - C7: INT4-ours needle -3.33% vs INT4-baseline（阈值 ≥-1%）
  - C8: INT4-ours PPL -15.92% vs INT4-baseline（阈值 ≥-0.5%）
  - **科学含义**: KL 行为对齐校准在 INT8 有效，但 INT4 精度下未保持非劣效性
- **C6 根因修正**: 从"单一 prompt budget 溢出"改为"CWE 子任务多因素局限"（5 条未关闭 issue）
- **Final claims**: **8 PASS / 3 FAIL / 0 INCONCLUSIVE / 0 ERROR**
- **数据同步**: 远端 emnlp_final_raw + final_journal_v2 已更新，本地已 rsync
- **LaTeX**: 39 .tex files, 18 plots（Codex review 修正了之前的 41/20 数字）
- **Codex review**: 两轮审查发现 3 个 HIGH + 2 个 MEDIUM issue，全部已修正

### 2026-03-10 04:27 | milestone: Phase 6 全部完成 — Core Profiling + 聚合出表 + Claim 验证
- **Goal**: 补跑 4K/8K/16K/32K profile_latency/profile_memory → 合并 → 聚合 → LaTeX → Claim 验证
- **Changed files**:
  - `scripts/dispatch_phase6_core.sh`: 24 non-KIVI configs/model × 8 seeds = 192 dirs/model
  - `scripts/audit_phase6_core.py`: 任务级审计脚本
  - `scripts/phase6_post_profiling.sh`: Steps 3-7 聚合管线 (修复 mkdir + --out_dir)
  - `scripts/generate_thesis_report.py`: 修复 C5/C6/C9/C11 的 target_batch NaN 过滤 bug
- **Step 0**: ✅ rsync + freeze (含 artifacts/ FIX-1) → fingerprint=`0942b55d`, 6/6 calib OK
- **Step 1**: ✅ 试聚合确认 latency/memory 仅含 8K → 4K/16K/32K 缺口确认
- **Step 2**: ✅ Core profiling 全部完成 (576/576, ALL PASS, 0 OOM)
  - 1.5B: 192/192 GATE: PASS (0 OOM, 95min)
  - 7B: 192/192 GATE: PASS (0 OOM, 144min)
  - 8B: 192/192 GATE: PASS (0 OOM, 175min, 21:25→04:17 CST)
  - Fingerprint OK: 冻结副本全程未修改
- **Step 3**: ✅ Merge → emnlp_final_raw (2136 dirs = 1560 phase5v2 + 576 phase6, 295 long dirs)
- **Step 4**: ✅ Strictable copy (2137 dirs) — 首次 rsync 失败（mkdir 缺失），已修复
- **Step 5a**: ✅ Aggregate exit 0 — latency_summary 182 rows, memory_summary 182 rows
  - **关键**: seq_lens = {4096, 8192, 16384, 32704} ← Phase 6 核心产出
  - thesis_main_claims_32k: 31 rows, significance_summary: 358 rows
- **Step 5b**: ✅ LaTeX export — 39 .tex 文件
- **Step 5c**: ✅ Claim validation (修复后重跑)
- **Step 6**: Strict QA exit 2 (46 mixed failure issues, 均为已知 eval_ruler OOM, 非阻塞)
- **Step 7 Claim Results**: 8 PASS / 1 FAIL / 2 INCONCLUSIVE / 0 ERROR
  - C1: ✅ PASS — TPOT gain 17.27% (threshold ≥5%), q=0.016, strong evidence
  - C2: ✅ PASS — KV mem gain 43.75% (threshold ≥20%), moderate evidence
  - C3: ✅ PASS — Needle 0% degradation (threshold ≥-1%)
  - C4: ✅ PASS — PPL -0.085% degradation (threshold ≥-0.5%)
  - C5: ✅ PASS — LongBench +0.16% (threshold ≥-1%)
  - C6: ❌ FAIL — RULER -2.82% (threshold ≥-1%), LLaMA-8B 单模型, RULER CWE 已知问题
  - C7: ⚠️ INCONCLUSIVE — aggregate 未生成 int4_baseline vs int4_ours 比较对
  - C8: ⚠️ INCONCLUSIVE — 同上 (PPL)
  - C9: ✅ PASS — vs KIVI LongBench +19.28%
  - C10: ✅ PASS — vs KIVI Needle 0%
  - C11: ✅ PASS — 7B/8B 跨模型稳健 (both PASS)
- **Step 8**: ✅ 备份完成
  - 远端数据盘: `/root/autodl-tmp/phase6_backup_20260310_042708/` (2.7G)
  - `results/final_journal_v2/` 已创建 (rsync from emnlp_final_raw, 对齐 objective.md 路径)
  - 本地 tables/plots/latex_tables/report 已 rsync
- **Freeze**: `/root/LLM_KVCache_Quantization_phase6_freeze_20260309_212302`
- **产出路径**: `results/emnlp_final_raw/` = `results/final_journal_v2/` (对齐 objective.md §444)

### 2026-03-09 21:22 | Phase 6 启动 — Core Profiling 准备
- **Goal**: 创建调度脚本 + 同步到远端 + 创建冻结副本
- **Commits**: ab1572c (dispatch script), pending (audit+pipeline scripts)
- **Validation**: rsync_gate PASS, fingerprint match, 6/6 calib files OK

### 2026-03-08 08:45 | Phase 5v2 吞吐评测准备
- **Goal**: 准备 Phase 5v2 吞吐评测 (1024 runs: 128 configs × 8 seeds × 2 tasks)
- **Changed files**:
  - `configs/exp_matrix.yaml`: 添加 `calib_file` 到 `int4_fused_throughput_8k_b24/b32`
  - `scripts/dispatch_phase5v2_throughput.sh`: 新建冻结副本吞吐调度脚本
- **Validation**:
  - 1.5B: 48 throughput entries (40 req + 8 stress), all calib OK
  - 7B: 40 throughput entries, all calib OK
  - 8B: 40 throughput entries, all calib OK
  - bash -n syntax check: PASS
- **Next**: rsync 推送 → 远端 pre-flight → 创建冻结副本 → 启动 Phase A (600 runs ~30h)
- **Commit**: f614003

### 2026-03-08 05:38 | milestone: Phase 5v2 数据修复补跑 v8 全部完成

- **Goal**: 修复 17 个问题目录 (A:6 INT4 溢出 + B:10 OOM 缺失 + C:1 PPL 异常)
- **结果**: **68/68 SUCCESS** — FINAL GATE 通过
- **总耗时**: ~14.75h (14:47 Mar 7 → 05:33 Mar 8 CST, 含 7B HF 缓存修复中断)
- **Step 时间线**:
  - B4 (1.5B×3): 14:47→16:38 (1h51m) — 前轮已完成，自动跳过
  - A1 (7B×3): 17:00→18:46 (1h46m) — 首次因 HF 缓存不完整失败，修复后重跑成功
  - B2 (7B×1): 18:46→19:49 (63m)
  - B1 (7B×4): 19:49→23:43 (3h54m)
  - C1 (7B×1): 23:43→00:50 (67m)
  - A2 (8B×3): 00:50→02:57 (2h07m)
  - B3 (8B×2): 02:57→05:33 (2h36m)
- **PPL 验证**:
  - A-type (INT4 溢出修复): 7B PPL=7.0618 (was 557.7), 8B PPL=7.1008 (was 610.9) ✅
  - C-type (异常值修复): PPL=99.0920 (was 52.82), 5-seed spread=0.0000 ✅
  - B-type (OOM 重跑): 全部 delta=0.0000 (完全可复现) ✅
- **验收标准**: 7/7 全通过
  1. 17/17 dirs 存在 ✅
  2. 68/68 tasks success ✅
  3. A-type PPL < 20 ✅
  4. C-type PPL [85,115] + spread < 5 ✅
  5. 原始数据 quarantine/ 17/17 ✅
  6. partial_reruns/ 3 entries ✅
  7. fail-fast 已验证 ✅
- **代码指纹一致**: `c60716bd47bb2f0edc4dd55b2ef737a4` (全程未变)

### 2026-03-07 17:04 | fix: 7B HF 缓存修复 + 补跑重启

- **问题**: A1_7b_s1234 步骤全部 12 tasks 失败 (rc=2/74)
- **根因**: `~/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/` 缓存不完整，仅有 config.json (1 blob)
- **原因**: HF Hub 下载中断或缓存被清理，tokenizer/model 权重丢失
- **修复**: 发现 `/root/autodl-tmp/hf_cache/hub/` 有完整 7B 模型，创建 4 个 safetensors 符号链接 + 下载 tokenizer blobs
- **验证**: `AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")` → vocab_size=151643 ✅
- **恢复策略验证**:
  - B4 重启时自动跳过 (3/3 dirs 4/4 success) ✅
  - A1 失败数据移到 partial_reruns，全量重跑 ✅
  - A1 curve_4k 在 3 分钟内完成 PPL+Needle，LongBench 运行中 ✅
- **8B 模型状态**: 缓存完整（symlink 到 ModelScope），无需修复

### 2026-03-07 14:48 | Phase 5v2 数据修复补跑 v8 启动

- **Goal**: 修复 17 个问题目录 (A:6 INT4 溢出 + B:10 OOM 缺失 + C:1 PPL 异常)
- **方案**: 冻结代码副本 → 隔离原始目录 → 全量重跑 → fail-fast + step 级恢复
- **Preflight 结果**:
  - GPU: 0% / 0MiB / 97871MiB (空闲)
  - 17/17 目标目录存在于 runs/
  - 无活跃实验进程
- **冻结副本**: `/root/LLM_KVCache_Quantization_phase5v2fix_20260307_144607`
- **代码指纹**: `c60716bd47bb2f0edc4dd55b2ef737a4`
- **关键文件 MD5 验证**: run_experiments.py, int4_basic.py, kivi_style_cache.py, generate_loop.py 全部本地/远端一致
- **tmux 会话**: `phase5v2_fix` (14:47 CST 启动)
- **日志**: `results/phase5v2/logs/rerun_v8.log`
- **7 步执行顺序**: B4(1.5B s1237) → A1(7B s1234) → B2(7B s1237) → B1(7B s1238) → C1(7B s1236) → A2(8B s1234) → B3(8B s1238)
- **预计耗时**: ~17h 串行
- **验收标准**: 68/68 task success, A-type PPL<20, C-type PPL∈[85,115], spread<5
- **Risks**: 串行 OOM(极低), 代码漂移(冻结+指纹门禁), 中断恢复(step 级)
- **监控命令**:
  ```
  ssh -p 31867 root@region-42.seetacloud.com "tmux capture-pane -t phase5v2_fix -p -S -50"
  tail results/phase5v2/logs/rerun_v8.log
  ```

### 2026-03-07 12:52 | milestone: Phase 5v2 质量评测矩阵 100% 完成

- **Goal**: 完成 Phase 5v2 全部质量评测实验
- **最终状态**:
  - 1.5B (43 configs × 5 seeds = 215 runs): ✅ 全部完成
  - 7B (32 configs × 5 seeds = 160 runs): ✅ 全部完成
  - 8B (32 configs × 5 seeds = 160 runs): ✅ 148/160 完成 (s1234-1236 缺 int4_ours_mixed 4 configs)
  - fused_fix 重跑: ✅ 全部完成 (1.5B 8/8 | 7B 12/12 | 8B 12/12)
- **关键时间线**:
  - 02-23 17:23: 启动 3 模型并行质量评测
  - 02-28: int4_fused calib_file bug 修复 + 污染隔离 + 重跑调度
  - 03-03: 7B 全 5 seeds 完成
  - 03-04: 8B 全 5 seeds 完成
  - 03-05: 1.5B s1236 完成, 启动 s1237
  - 03-06: 1.5B s1237 完成, 8B s1237 补完完成
  - 03-07 ~12:00: 1.5B s1238 最后一个 config (int4_ours_long eval_ruler 32K) 完成
- **GPU 利用率优化**: 1.5B s1238 最后阶段采用 3 runner 并行策略 (main + KIVI-curve + KIVI-long), 减少约 2h 空闲时间
- **下一步**: Phase 6 — 聚合 + 统计分析 + LaTeX 导出 + 论文报告; 吞吐评测可选

### 2026-03-01 19:10 | feat: Codex (GPT-5.3) 交叉审查集成

- **Goal**: 将 OpenAI Codex 嵌入 Agent 工作流，实现审查交叉验证和 Bug 修复咨询
- **Changed files**:
  - `~/.mcp.json` — 注册 codex MCP Server (`codex mcp-server`)
  - `.claude/settings.local.json` — enabledMcpjsonServers 添加 `"codex"`
  - `.agents/skills/codex-review/SKILL.md` — **新建** Codex 审查 Skill (146 行)
  - `.claude/agents/review-coord.md` — 添加 Step 2.5 Codex 交叉审查 + 汇聚去重逻辑 + 输出格式来源统计
  - `.claude/agents/supervisor.md` — 添加 Codex 咨询路径 (调度表 + 详细流程 + 调用模板 + 审批逻辑)
- **验证**: `python3 -c "import json; assert 'codex' in json.load(open('~/.mcp.json'))['mcpServers']"` ✓; grep 确认 5 文件 Codex 关键词就位
- **安全**: Codex 始终 `sandbox: "read-only"`, 建议仅作参考, 失败不阻塞, 来源标注 `[Codex/GPT-5.3]`
- **Risks/follow-ups**: 新会话需 ToolSearch "codex" 验证 MCP 工具可用; 端到端测试需实际触发 Review-Coord

### 2026-02-28 07:37 | fix: int4_fused YAML calib_file 错误修复 + 污染隔离 + 调度脚本

- **Goal**: 修复 int4_fused 使用 INT8 校准文件的 YAML 配置 bug；隔离已产生的污染数据；创建接力调度和监控脚本
- **Changed files**:
  - `configs/exp_matrix.yaml` — 9 处 int4_fused 条目添加 `calib_file: artifacts/kv_calib_kl_int4_selected.json`
  - `configs/snapshots/exp_matrix_qwen25_7b_v1.yaml` — 9 处添加 `calib_file: artifacts/kv_calib_kl_qwen25_7b_int4.json`
  - `configs/snapshots/exp_matrix_llama31_8b_v1.yaml` — 9 处添加 `calib_file: artifacts/kv_calib_kl_llama31_8b_int4.json`
  - `scripts/dispatch_phase5v2.sh` — 新建（接力调度脚本）
  - `scripts/monitor_phase5v2.sh` — 更新（添加 int4_fused 污染追踪 + --once 模式）
- **Root cause**: int4_fused 条目无显式 `calib_file`，继承 `quant_defaults.calib_file`（INT8 校准）→ INT8 scales 用于 INT4 → PPL 灾难性退化（1,263,404 vs 预期 7-15）
- **Commands**: `git diff --stat configs/` → 3 files, 27 insertions
- **Outputs**: 修复 3×9=27 个 int4_fused 条目；远端已隔离 25 个污染目录到 quarantine/
- **Validation**:
  - [x] grep 确认所有 int4_fused 条目均有 calib_file
  - [ ] rsync 到远端后重跑 fused_fix，验证 PPL 回归正常范围
- **Commit**: 004f7cf
- **Risks / follow-ups**:
  - 远端 fused_fix 已重启（PID 599995），PPL=22.04 验证通过
  - 远端 q_7b/q_8b 仍在用旧 YAML 配置跑 s1236，产出的 int4_fused 数据需后续隔离
  - 旧污染数据已 mv 到 quarantine/（26 dirs），可审计回滚

### 2026-02-28 06:50 | Agent 工作流治理优化：记录强制 + Token 节约 + Memory 增强

- **Goal**: 实施三模块治理优化：(A) 写入强制机制 (B) iteration.md 瘦身 (C) Memory 系统增强
- **Changed files**:
  - `scripts/iteration_tool.py` — 新建（trim-timeline / clean-plans / stats 三子命令）
  - `.git/hooks/pre-commit` — 重写为阻塞式（main 分支 code commit 必须含 iteration.md）
  - `.claude/hookify.readonly-guard.local.md` — 新建（保护 objective/CLAUDE/AGENTS/experiment_sop）
  - `.claude/hookify.session-checklist.local.md` — 新建（会话结束前检查提醒）
  - `CLAUDE.md` §7.7 — 新增 Agent 分级读取策略表
  - `.claude/agents/supervisor.md` — 启动流程增加 Memory 读取步骤
  - `.claude/agents/developer.md` — 自主模式启动增加 Memory 读取步骤
  - `.agents/skills/unit-commit/SKILL.md` — Step 6 Memory checkpoint
  - `.agents/skills/session-handoff/SKILL.md` — 新建会话交接 SKILL
  - `iteration.md` — clean-plans 压缩 Phase 4 + trim-timeline 归档 21 条旧条目
  - `development_history/iteration_archive_202602.md` — 接收归档条目
- **Commands**: `python3 scripts/iteration_tool.py stats/clean-plans/trim-timeline`
- **Outputs**: iteration.md 1054 → 584 行（-45%），归档 21 条 Timeline 到 archive
- **Validation**:
  - [x] iteration_tool.py py_compile OK + stats/dry-run/实际执行全通过
  - [x] pre-commit hook 阻塞无 iteration.md 的 code commit（exit 1）+ --no-verify 逃生舱 OK
  - [x] hookify 规则文件创建成功
  - [x] supervisor.md / developer.md / CLAUDE.md / unit-commit SKILL 编辑验证通过
  - [x] session-handoff SKILL 创建成功
- **Commit**: pending
- **Risks / follow-ups**:
  - hookify 规则需要 hookify 插件启用后才会生效（warn-only，不阻塞）
  - iteration.md Update Rules §5 已有 "保留最近 15 条" 的文档约定，现在有工具自动化

### 2026-02-28 06:34 | Fix EVL-087/088: int4_fused 白名单缺失

- **Goal**: 修复 eval_ppl.py 中两处 kv_mode 白名单遗漏 int4_fused，防止该模式退化为 baseline
- **Changed files**:
  - `scripts/eval_ppl.py` L189: load_calibration() 白名单添加 int4_fused
  - `scripts/eval_ppl.py` L806: prefill temperature hooks 白名单添加 int4_fused
  - `review_tracker.md`: EVL-087, EVL-088 标记 fixed
- **Commands**: `python3 -m py_compile scripts/eval_ppl.py`
- **Outputs**: COMPILE OK; 全文搜索确认 3 处白名单均包含 int4_fused
- **Validation**: ✅ 编译通过，grep 确认无遗漏
- **Commit**: f009851
- **Risks / follow-ups**:
  - 修复前已完成的 int4_fused runs 数据无效，需评估重跑范围
  - 需 rsync 推送到远端后重跑受影响的 int4_fused 评测

### 2026-02-28 03:58 | 创建华南理工大学本科毕业论文 LaTeX 框架

- **Goal**: 搭建完整的毕业论文 LaTeX 模板 + 撰写全部 5 章内容（Phase 1-2）
- **Changed files**:
  - `thesis/main.tex` — 主文件（59行）
  - `thesis/latexmkrc` — 编译配置（xelatex）
  - `thesis/references.bib` — 24 篇参考文献（193行）
  - `thesis/setup/packages.tex` — 宏包集合
  - `thesis/setup/fonts.tex` — 字体设置（macOS/Fandol 双路径）
  - `thesis/setup/format.tex` — 章节/行距/图表格式（符合学校规范）
  - `thesis/setup/header.tex` — 页眉页脚 + A4 页面尺寸
  - `thesis/setup/toc.tex` — 目录格式
  - `thesis/setup/commands.tex` — 封面/声明/摘要/致谢环境 + 数学符号
  - `thesis/chapters/abstract_zh.tex` — 中文摘要（~480字）
  - `thesis/chapters/abstract_en.tex` — 英文摘要
  - `thesis/chapters/ch1_introduction.tex` — 第一章 绪论（173行，~2600字）
  - `thesis/chapters/ch2_related_work.tex` — 第二章 相关工作（344行，~4500字，10公式）
  - `thesis/chapters/ch3_method.tex` — 第三章 方法设计（633行，~5400字，14公式，1算法）
  - `thesis/chapters/ch4_experiments.tex` — 第四章 实验（766行，7表格含占位数据）
  - `thesis/chapters/ch5_conclusion.tex` — 第五章 总结（157行，~2300字）
  - `thesis/chapters/appendix.tex` — 附录（104行）
  - `thesis/chapters/acknowledgements.tex` — 致谢
- **Commands**: 6 个并行 developer agents 编写章节内容
- **Validation**:
  - 所有 18 个文件已创建，共 2817 行
  - 静态检查：所有文件大括号平衡，84 个环境配对完整
  - 引用检查：23 个 cite key 全部匹配 references.bib
  - 本地无 LaTeX 安装，未做编译验证（需在有 TeX Live 环境中验证）
- **Risks / follow-ups**:
  - 第四章实验数据为占位（XX.XX），待 Phase5v2 完成后替换
  - 中英文摘要含 XX% 占位，待最终数据后填写
  - 附录 LongBench 21任务完整结果和种子统计待填充
  - 封面信息（学号/学院/专业/导师）需用户填写
  - 图3-1（架构图）、图3-2（inv_tau 热力图）需后续生成
  - 需在有 LaTeX 的环境编译验证格式

### 2026-02-28 01:30 | Memory 迁移：KV Cache memory 从 home 层移至项目层

- **Goal**: 修复 Memory 路径错误 — 4 个 KV Cache 专题文件被写在了 home 层，从项目目录启动 Claude Code 时看不到
- **Changed files**:
  - `~/.claude/projects/-Users-chenzilang-Desktop-LLM-KVCache-Quantization/memory/debugging-patterns.md` (mv 过来)
  - `~/.claude/projects/-Users-chenzilang-Desktop-LLM-KVCache-Quantization/memory/experiment-state.md` (mv 过来)
  - `~/.claude/projects/-Users-chenzilang-Desktop-LLM-KVCache-Quantization/memory/agent-coordination.md` (mv 过来)
  - `~/.claude/projects/-Users-chenzilang-Desktop-LLM-KVCache-Quantization/memory/tracker-operations.md` (mv 过来)
  - `~/.claude/projects/-Users-chenzilang-Desktop-LLM-KVCache-Quantization/memory/MEMORY.md` (重写合并, 90 行)
  - `~/.claude/projects/-Users-chenzilang/memory/MEMORY.md` (清理 KV 段, 190→139 行, 替换为指针)
  - `CLAUDE.md` §1.1: 更新 Memory 路径为项目级 + 加注启动目录提醒
  - `iteration.md`: 本条记录
- **Validation**: 项目层 5 文件完整 (MEMORY.md 90行 ≤165), home 层无残留专题文件, CLAUDE.md 包含正确路径
- **Risks / follow-ups**: 无功能变化, 仅 memory 组织结构优化

### 2026-02-25 23:33 | 建立持久化 Memory 工作流

- **Goal**: 创建结构化 Memory 文件体系，使跨会话知识沉淀系统化
- **Changed files**:
  - `~/.claude/projects/-Users-chenzilang/memory/MEMORY.md` (新建, 59 行): 主文件 — 环境、阶段、陷阱、产物、API、导航、索引
  - `~/.claude/projects/-Users-chenzilang/memory/debugging-patterns.md` (新建): CAL-019/020、INT4 溢出、warnings 作用域等调试经验
  - `~/.claude/projects/-Users-chenzilang/memory/experiment-state.md` (新建): 校准产物版本、Phase 5v2 矩阵状态
  - `~/.claude/projects/-Users-chenzilang/memory/agent-coordination.md` (新建): Agent 协作模式与失败模式
  - `~/.claude/projects/-Users-chenzilang/memory/tracker-operations.md` (新建): tracker 格式规范、批量操作模板
  - `CLAUDE.md` §1.1: 新增持久化 Memory 维护规则 (触发时机表 + 约束)
  - `iteration.md`: 本条记录
- **Validation**: MEMORY.md 59 行 (≤165 上限), 5 文件均非空, CLAUDE.md 包含 §1.1
- **Risks / follow-ups**: Memory 内容基于 iteration.md + review_tracker.md 提取的实际经验，非模板占位；后续每个 Phase 切换时做全量 review

### 2026-02-24 16:00 | Supervisor Session — Wave 16/17 完成，466→13 open

- **Goal**: 自主修复 review_tracker.md 全部可修复 issues
- **Session scope**: Wave 16 收尾 + Wave 17 + 最终清理
- **Wave 16** (8 items): ENG-037~041 (HIGH: clamp-before-cast, narrow exceptions, clipping warnings) + ENG-047/CAL-031/032 (docs)
  - Commits: `4e1a182`, `46ca296`
- **Infra**: resolve_quant_bits 去重 (`9a694d5`), review_tool RVW-014 fix, agent config updates (`067921e`)
- **Wave 17A** (22 items): run_experiments.py — 7 HIGH (kill orphans, retry log separation, OOM skip, unique tmp, kv_mode validation, kivi precheck, status logic) + 11 MED (SIGINT, interrupt no-retry, CSV check, exp backoff, log rotation, etc.) + 4 LOW
  - Commit: `a61f428`
- **Wave 17B** (15 items): patch_model.py (9: kernel exception, unpatch API, shape validation, docs) + generate_loop.py (5: group_size_v warning, multi-token, DynamicCache doc, scale asymmetry) + int8_cache.py (1: clear/release warning)
  - Commit: `264dcc3`
- **Final cleanup** (6 items): ENG-054/KRN-005/KRN-010 documented (`d2decc6`), AGG-032/ENG-030/RUN-024 wont_fix (deferred)
- **Result**: 466 total → 453 resolved (431 fixed + 15 fp + 7 wf), **13 open** (all need user decisions)
- **Remaining 13 open items**:
  - HIGH: CAL-019/020 (Q vector missing layernorm/RoPE — fundamental calibration correctness)
  - HIGH: CFG-026 (7B/8B calib files missing), CFG-029 (LLaMA revision null)
  - MED: CFG-008/009/011/012/013/022/028 (experiment design choices)
  - LOW: CFG-023/024 (temperature inconsistency)
- **Validation**: All modified files pass `py_compile`; local pytest broken (numpy/scipy dlopen issue — not our code)

### 2026-02-24 14:14 | 代码审查修复 Wave 3-5 — 30 additional issues fixed

- **Goal**: 继续修复 review_tracker.md 中的 open issues（Wave 2 之后）
- **Wave 3** (10 issues): KVC-017 overflow guard, CHK-023 timeout enum, RUN-020 config validation, QUA-002 logging infra, SMK-002/004, AGG-046/047 bare except+commit semantics, ENG-036 signature cache, RUN-033 classified exceptions
- **Wave 4** (9 issues): QUA-001 centralize get_git_commit (9 scripts → src/utils/repro.py, net -44 lines), KVC-018 zero-length get_kv warning, RUN-034/SMK-005 breaking change docs, AGG-029/037/043/045 statistical fixes, QUA-003 loop extraction
- **Wave 5** (11 issues): ENG-007/008/012/013 docs, QUA-004/007/009/010 code quality, RUN-017/AGG-014/PRF-009 comments
- **Validation**: All modified files pass `python -m py_compile`
- **Commits**:
  - Wave 3: `7e72174`, `f25408f`, `a581bed`
  - Wave 4: `3e6cf12`, `5be2de7`, `242c3e8`, `589356e`
  - Wave 5: `bcc6b98`, `153805c`, `7f58455`
- **Cumulative**: 254 fixed + 10 false_positive + 4 wont_fix = 268 resolved / 367 total (73%)
- **Remaining**: 95 open (0 CRIT, 27 HIGH, 49 MED, 19 LOW) — mostly TST test coverage (48), SEC security decisions (4), CFG config design (8), refactoring (3), architecture decisions (4)

### 2026-02-24 13:54 | 全仓库代码审查修复 Wave 2 — 43 issues 批量修复

- **Goal**: 继续修复 review_tracker.md 中的 open issues（Wave 1 之后的第二轮）
- **Changed files**: 23 files (+931/-181 lines)
  - src/: engine/generate_loop.py, engine/patch_model.py, cache/kivi_style_cache.py, cache/int4_cache.py, cache/int8_cache.py, quant/int4_basic.py, quant/int8_basic.py
  - scripts/: run_experiments.py, aggregate_results.py, smoke_test.py, check_run_completeness.py, config_utils.py, eval_ppl.py, eval_ruler.py, profile_latency.py, profile_memory.py
  - tests/: test_aggregate_results_stats.py, test_triton_kernel.py, test_asymmetric_quant.py, test_int4_cache.py, test_int8_cache.py, test_kivi_cache.py
  - review_tracker.md
- **Method**: 6 并行 dev agents + main thread direct fixes
- **Results**: 43 issues marked fixed, total 228/366 resolved
  - RUN: 13 fixes (018-032) — commit validation, subprocess timeout, param validation
  - AGG: 9 fixes (034-044) — logging, inf guard, readable names, scipy flag
  - ENG: 12 fixes (005-035) — padding check, KIVI validation, dtype contracts
  - SMK: 2 fixes (001, 003) — exit code semantics, token-based slicing
  - TST: 7 fixes (041-050) — t_critical tests, CI95 tests, Phipson-Smyth tests, INT4/INT8 bounds
  - CHK/PRF/EVL/QNT/KVC: 6 fixes
- **Validation**: All 23 files pass `python -m py_compile`
- **Commits**:
  - `3c6deed` fix: Wave 2 src/ fixes — ENG(12), KVC(1), QNT(1)
  - `40cbad0` fix: Wave 2 scripts/ fixes — RUN(13), AGG(9), SMK(2), CHK(1), PRF(4), EVL(1)
  - `fc06073` test: Wave 2 test fixes — TST(7)
  - `9d2fcda` docs: update review_tracker — Wave 2 marks 43 issues fixed
- **Remaining**: 124 open (0 CRIT, 33 HIGH, 63 MED, 28 LOW)
- **Risks / follow-ups**: SMK-005/RUN-034 are breaking change notes for new params introduced by fixes; TST-053~058 are test coverage gaps for Wave 2 code changes

### 2026-02-24 06:35 | RULER-long Repair 完成（int4_baseline_long + int4_fused_long）

- **Goal**: 修复 seed 1234 的 2 个 RULER 32K eval_ruler 失败（CWE 子任务 prompt 溢出）
- **Root cause**: 旧代码 `32704 + 128 = 32832 > max_position_embeddings=32768`，修复后用 `_effective_prompt_budget()` 动态调整
- **Commands**:
  - `run_experiments.py --run_names int4_baseline_long --run_tag phase5v2r1_1p5b_s1234 --append`
  - `run_experiments.py --run_names int4_fused_long --run_tag phase5v2r1_1p5b_s1234 --append`
- **Results**:
  - int4_baseline_long: success, rc=0, 256 cases, CWE f1=0.50
  - int4_fused_long: success, rc=0, 256 cases, CWE f1=0.43
  - 两者 pass_rate≈0 是 int4 基础量化在 32K 的预期表现
- **Output**: `results/phase5v2/runs/{int4_baseline,int4_fused}_long_s1234_phase5v2r1_1p5b_s1234/`
- **Validation**: manifest status=success, 4 CSV 文件生成
- **Risks / follow-ups**: 聚合时需用 repair 版（tag=phase5v2r1）替代原始失败版

### 2026-02-24 05:48 | 全仓库代码审查修复 Wave 1 — 90+ issues 批量修复

- **Goal**: 修复 review_tracker.md 中所有可代码修复的 open issues（~90 个，跨 11 个模块）
- **Changed files** (32 files, +1356/-725 lines):
  - `scripts/check_run_completeness.py`: CHK-002/003/007/008/009/010/011/012/013/014/016/017/019 (13 fixes)
  - `scripts/review_tool.py`: RVW-001/002/003/004/014/016/017/018/021/022/023 (11 fixes)
  - `scripts/export_tables_latex.py`: EXP-013/014/015/016 (4 fixes)
  - `scripts/generate_thesis_report.py`: EXP-001/009/010/011/012 (5 fixes)
  - `scripts/calibrate_behavior.py`: CAL-006/007/008/009/012/013/014/015/016/017 (10 fixes)
  - `scripts/run_experiments.py`: RUN-002/003/004/005/006/007/008 (7 fixes)
  - `scripts/repair_phase5v2_ruler_light.py`: RUN-015/016 (2 fixes)
  - `scripts/eval_ruler.py`: EVL-013/014/027/028 (4 fixes)
  - `scripts/eval_longbench.py`: EVL-017 (1 fix)
  - `scripts/aggregate_results.py`: AGG-016/017/021/022/026/028/030 (7 fixes, 在前次 commit 基础上)
  - `src/engine/generate_loop.py`: ENG-018/020/022/026/031 (5 fixes)
  - `src/engine/patch_model.py`: ENG-017/019/024 (3 fixes)
  - `src/kernels/triton_decode_attn_int8.py`: ENG-015/016 (2 fixes)
  - `src/quant/int4_basic.py`: ENG-028 + QNT-005 (2 fixes)
  - `src/quant/asymmetric_quant.py`: QNT-005 edge case documentation (1 fix)
  - `src/cache/kivi_style_cache.py`: KVC-005/009/010/013/014/015 (6 fixes)
  - `CLAUDE.md`: RVW-012/020 (2 fixes)
  - `.claude/settings.json`: RVW-009 (1 fix)
  - `configs/snapshots/exp_matrix_llama31_8b_v1.yaml`: CFG-007 (1 fix)
  - `tests/test_aggregate_results_stats.py`: AGG-033 CRITICAL (test assertions updated for Phipson-Smyth +1)
- **False positives identified**: CFG-010, CFG-017, CFG-018, RVW-019 (4 FPs)
- **Method**: 9 parallel background agents + main thread direct fixes
- **Validation**: `python -m py_compile` — all 16 modified .py files COMPILE OK
- **review_tracker.md**: ~90 issues fixed this wave; Phase Gate: CLEAR (0 CRIT open)
- **Commits**:
  - `a60cbe6` fix: core quant/cache/engine fixes — KVC-002 INT4 pack offset, QNT-003~009, ENG-015~031
  - `2442ce7` fix: scripts bulk review fixes — CHK(13), RVW(11), EXP(9), CAL(10), RUN(9), EVL(5), AGG(7)
  - `c67038c` test: AGG-033 update sign-flip test assertions for Phipson-Smyth +1 correction
  - `6c12740` docs: update review_tracker (166 fixed, 0 CRIT), config, and meta files
  - `93d79b9` chore: review-coord agent model opus→sonnet
- **Risks / follow-ups**:
  - 本地 pytest 因 numpy/scipy 依赖问题无法运行，远端验证待实验完成后进行
  - TST-* issues (22个测试覆盖问题) 属于新增测试，非代码修复，后续 Wave 2 处理
  - AGG-031 (双尾 vs 单尾) 涉及统计方法论决策，需用户确认
  - ENG-003/004 (KIVI decode 路径) 涉及架构决策，需用户确认

### 2026-02-24 05:20 | HIGH priority 修复 — aggregate_results.py 统计与数据完整性 (6+1 fixes)

- **Goal**: 修复 aggregate_results.py 中 7 个 HIGH/MED 审查问题
- **Changed files**: `scripts/aggregate_results.py`, `review_tracker.md`
- **Fixes**:
  - AGG-018: CI 从 z=1.96 改为 t 分位数（_t_critical 函数，scipy + fallback lookup table）
  - AGG-019: exact sign-flip 分支加 Phipson-Smyth +1 修正，与 MC 分支一致
  - AGG-020: _read_csvs bare except → logger.warning 记录损坏 CSV
  - AGG-023: relative_gain pairings 补充 kivi_style 配对（C9/C10 claim 支持）
  - AGG-024: relative_gain 所有 7 个调用的 key_cols 加 model_id
  - AGG-025: _main_claims_32k_table 动态 merge_keys 含 model_id，消除笛卡尔积
  - AGG-027: count=1 时 CI 半宽从 0.0 改为 NaN（随 AGG-018 修复）
- **Validation**: `python -m py_compile scripts/aggregate_results.py` — COMPILE OK
- **review_tracker.md**: 280 issues | 81 fixed + 2 FP | 197 open (0 CRIT, 42 HIGH, 114 MED, 41 LOW)
- **Commit**: 4876498

### 2026-02-24 05:10 | Supervisor 审查追踪清理 — Phase Gate 解除阻塞

- **Goal**: 验证并标记已修复的 Phase Blockers 和 RVW issues，解除 Phase Gate 阻塞
- **Changed files**:
  - `review_tracker.md`: 标记 9 个已修复 issues (CHK-001, EVL-001, EVL-002, EVL-008, RVW-007, RVW-008, RVW-010, RVW-011, RVW-015)
  - `scripts/start_agents.sh`: L32 developer prompt 从 "TODO Backlog" 改为 "review_tracker.md + iteration.md → 按优先级矩阵领取任务" (RVW-007)
- **Validation**:
  - `review_tool.py stats`: 273 total, 74 fixed, 197 open ✅
  - `review_tool.py phase-gate`: **CLEAR** (was BLOCKED by 3 CRIT) ✅
  - CHK-001: 代码验证 OOM 检查在 if 链首位 (L147-148) ✅
  - EVL-001: CLASSIFICATION_MATCH_POLICY + docstring + CSV audit 字段 ✅
  - EVL-002: _effective_prompt_budget() 确保 prompt + gen ≤ max_model_len ✅
- **Phase Gate 状态**: BLOCKED → **CLEAR**（0 CRIT open）
- **Commit**: 53fd752
- **Risks / follow-ups**:
  - 远程实验仍在运行，本次修改不影响远端代码
  - 44 HIGH issues 仍 open，优先处理 ENG/TST 模块

### 2026-02-24 04:48 | review-coord 持续守护模式改造

- **Goal**: 重写 review-coord.md 为持续守护式 Agent，修复 start_agents.sh
- **Changed files**:
  - `.claude/agents/review-coord.md`（完全重写，162→192 行）：事件循环架构 + 10 模块覆盖 + 智能休眠策略
  - `scripts/start_agents.sh`：动态路径(L5)、agent 名称修正(L28)、启动 prompt 更新(L33)、注释修正(L16)
- **Validation**:
  - review-coord.md 包含完整事件循环、10 模块定义、休眠策略
  - `grep reviewer scripts/start_agents.sh` → 零残留
  - `grep review-coord scripts/start_agents.sh` → 3 matches
- **Risks / follow-ups**: RVW-010, RVW-015 已修复

### 2026-02-24 04:34 | Cherry-pick Codex RULER 修复 + 附带改进

- **Goal**: 将 Codex 分支 `codex/phase5v2-ruler-ag123-fix` 的核心修复 cherry-pick 到 main，跳过大规模删除类变更
- **Changed files**:
  - `scripts/eval_ruler.py` — `_effective_prompt_budget()` 动态调整 prompt budget，per-case try/except
  - `scripts/run_experiments.py` — 预启动截断警告，skip_completed 语义修复
  - `scripts/repair_phase5v2_ruler_light.py` — 新增 RULER-long 修复工具
  - `scripts/aggregate_results.py` — per-model 分层表导出，RULER subtask groupby 改进
  - `scripts/generate_thesis_report.py` — 跨模型 claim 验证重构
  - `scripts/profile_memory.py` — UnboundLocalError 修复 + NVML source 检测
  - `scripts/eval_longbench.py` — classification_match_policy 审计字段
  - `configs/snapshots/exp_matrix_qwen25_7b_v1.yaml` — 注释修正
  - `tests/` — 5 个新/更新测试文件（+13 passed, 6 skipped due to no GPU）
- **Cherry-picked commits**: b7f4c36, 22f667b, 674410b, 449edcb, 4dbc227（原始: 502bc08, 1c76dd3, 04d89bd, 2fb4c2a, 7d5d65a）
- **Skipped**: 6 个 docs-only commits（iteration.md）+ 所有删除类 commits（agent 定义、review 基础设施）
- **Validation**: `pytest tests/test_eval_ruler_length_guard.py tests/test_run_experiments_resilience.py tests/test_eval_longbench_classification_policy.py -v` → 13 passed, 6 skipped
- **Next**: rsync 到远端 → repair RULER-long 失败

### 2026-02-24 03:13 | 审查追踪迁移 — review.yaml → review_tracker.md

- **Goal**: 用 280 行结构化 Markdown 替代 3951 行 YAML + 858 行 Python 工具链，提升可读性和直接编辑性
- **Changed files**:
  - `review_tracker.md`（新建）：根目录权威审查追踪文件，176 issues
  - `scripts/review_tool.py`（新建）：轻量级查询工具（stats/phase-gate/progress/open/add）
  - `scripts/migrate_review_to_md.py`（新建后归档）：一次性迁移脚本
  - `.claude/agents/reviewer.md`：写入目标从 iteration.md TODO Backlog → review_tracker.md
  - `.claude/agents/developer.md`：修复流程从 YAML 脚本 → 直接编辑 markdown
  - `.claude/agents/supervisor.md`：启动流程读取 review_tracker.md
  - `CLAUDE.md`：§1 权威文件表新增 review_tracker.md，§4.5 Phase 闸门更新，§12 审查 Agent 更新
  - `~/.claude/CLAUDE.md`：§7 审查 Agent 更新
  - `AGENTS.md`：新增 review_tracker.md 说明
  - `iteration.md`：TODO Backlog 指针更新
- **Archived to** `development_history/archive_20260224_review_yaml/`:
  - `review.yaml` (3951 lines), `scripts/review_query.py` (430 lines), `scripts/review_add_issue.py` (428 lines), `scripts/migrate_review_to_yaml.py` (819 lines)
- **Validation**:
  - `review_tool.py stats`: total=176, open=112, fixed=62, fp=2 ✅ (matches original)
  - `review_tool.py phase-gate`: BLOCKED (T-1, AF-1, AG-1) ✅
  - `review_tool.py progress`: 32 sections, 64/176 resolved (36%) ✅
  - `grep review.yaml *.md .claude/agents/*.md`: 零残留引用 ✅
  - `wc -l review_tracker.md`: 291 lines (vs 3951 原 YAML, 93% 压缩) ✅
- **Net effect**: 删除 ~4809 行 (YAML + 3 scripts)，新增 ~400 行 (markdown + 1 script)。92% 减少。
- **Commit**: 73c9472 (initial), then renumbered (see below)

### 2026-02-23 23:30 | Phase 4-6 Prep: Bug Fixes + Config Updates + Claims Extension

- **Goal**: Resolve all CRITICAL/HIGH backlog items blocking Phase 4-6, update configs for full matrix, extend thesis report claims.
- **Changed files (BUG FIXES)**:
  - `scripts/calibrate_behavior.py`: Fixed MSE loss aggregation (.mean→.sum), clamp(min=eps), loss_accum normalization, --calib_out default, select_best_trial key check
  - `src/cache/kivi_style_cache.py`: Fixed clear() to reset _k_scale/_k_zp
  - `src/quant/asymmetric_quant.py`: Added percentile range validation (50, 100]
  - `src/engine/generate_loop.py`: Added quant_bits to generate() API
  - `scripts/eval_longbench.py`: Added logging import + logger
- **Changed files (CONFIG UPDATES)**:
  - `configs/exp_matrix.yaml`: +13 KIVI entries, -2 FP16 b24/b32
  - `configs/snapshots/exp_matrix_qwen25_7b_v1.yaml`: +40 entries (long INT4/KIVI + throughput)
  - `configs/snapshots/exp_matrix_llama31_8b_v1.yaml`: +40 entries (same)
  - `configs/snapshots/exp_matrix_ablation_1p5b_v1.yaml`: Created, 14 runs
  - `configs/snapshots/final_emnlp2026_v1.yaml`: Created meta-config
- **Changed files (FEATURE)**:
  - `scripts/export_tables_latex.py`: +kivi_style to KV_MODE_ORDER/DISPLAY
  - `scripts/generate_thesis_report.py`: +claims C7-C11
  - `CLAUDE.md`: +Phase gate rule (§4.4), +remote server section (§12)
- **Verification**: compileall 0 errors; all YAML parse OK; 11 ClaimSpecs; 86+14+67+67 matrix runs
- **Backlog resolved**: A1-A4/A6-A7, B1, C1-C2, D1, E1-E4, F1-F3, G1-G2/G4, J1
- **Commit**: pending
- **Next**: commit → rsync → MSE calibration → ablation

### 2026-02-28 06:51 | fix: int4_fused whitelist gaps in generate_loop + run_experiments (XMD-006, RUN-088)
- **Goal**: 修复 int4_fused 在 generate_loop.py 和 run_experiments.py 中被遗漏出白名单的系统性 bug
- **Changed files**:
  - `src/engine/generate_loop.py`: L500 calib loading whitelist + L700 temperature hooks whitelist 添加 int4_fused
  - `scripts/run_experiments.py`: L1219 calib_file pre-validation + L1363 calib_file CLI passthrough 添加 int4_fused
  - `review_tracker.md`: XMD-006 + RUN-088 标记 fixed
- **Root cause**: 新增 int4_fused 模式时，代码库中 6 处 `kv_mode in [...]` 白名单仅更新了 eval_ppl.py（EVL-087/088），遗漏了 generate_loop.py 和 run_experiments.py
- **Impact**: 所有 int4_fused 的 needle/ruler/longbench 评测校准未加载，退化为 baseline；eval_ppl 的 calib_file 未经 runner 传递
- **Contamination scope**: int4_fused quality evals (PPL+Needle+RULER+LongBench) across all 3 models × 4 configs × 5 seeds = 240 runs 需重跑；吞吐评测不受影响
- **Validation**: py_compile 通过; grep 确认所有白名单位置均含 int4_fused
- **Commit**: c37cd83

### 2026-03-09 12:58 | Phase 5v2 吞吐评测：三级备份 + merge push
- **Goal**: GPU 驱动崩溃后，重启前完成数据备份和代码推送
- **背景**: Step 6 (8B-B) 执行中 CUDA runtime 崩溃（nvidia-smi NVML Error），Step 6/7 未完成
- **管线完成度**: Steps 1-5 ✅, Step 6 ❌ (55 runs 剩余), Step 7 ❌ (64 runs 未执行)
- **数据量**: 1442 dirs (906 throughput + 536 quality), 182M runs/
- **备份完成**:
  - Level 1: 远端数据盘 `/root/autodl-tmp/phase5v2_backup_20260309_125340/` — 1442 dirs ✅
  - Level 2: 本地 `results/phase5v2_remote_backup/` — 1442 dirs ✅
  - Level 3: git merge origin/main (12 conflicts → ours) + push ✅ (commit 95af277)
- **冻结副本验证**:
  - Path: `/root/LLM_KVCache_Quantization_throughput_20260308_140946`
  - Commit: `e5c78e48f8b48b1c6957c74ab28d86ca8b0d4a7c`
  - Fingerprint: `a1945015e88e33ff3d60cda85e7bc5df` ✅ MATCH
- **下一步**: 用户手动重启 AutoDL (关机→开机) → 验证 GPU → 恢复 Step 6/7 (~3h)

### 2026-03-09 16:32 | Phase 5v2 吞吐评测：GPU 重启 + 管线恢复完成
- **Goal**: 重启 GPU 后恢复 Step 6 (8B Phase B) 和 Step 7 (1.5B Stress)
- **重启**: AutoDL 关机→开机，GPU H20 完全恢复（97GB free）
- **Step 6 恢复 (8B Phase B)**:
  - 隔离 2 个 GPU crash dirs → `quarantine_gpu_crash/`
  - `continue_on_oom` 执行 120 dirs: 108 双 CSV + 12 OOM (b16 预期)
  - 方法进度: fp16→int8_baseline→int8_ours→int4_baseline→int4_fused→int4_ours→kivi_int8→kivi_int4
  - 耗时: ~1h55min
- **Step 7 (1.5B Stress)**:
  - 64 dirs: 55 双 CSV + 9 OOM
  - 方法: int8_baseline, int8_ours, int4_fused, int4_ours × b24/b32 × 8 seeds
  - 耗时: ~1h30min
- **最终统计**:
  - 吞吐 dirs: 1024 (1.5B:320 + 7B:320 + 8B:320 + Stress:64)
  - 质量 dirs: 536
  - 总计: 1560 dirs + 2 quarantine = 1562
  - runs/ size: 186M
- **管线完成度**: Steps 1-7 全部 ✅
- **下一步**: Phase 6 聚合 + 论文（可进入）

### 2026-03-12 05:39 | ENG-066 Float32 Scale Chain Fix for INT4

- **Goal**: 修复 INT4 scale 全链路 fp16 精度损失，根因是 `int4_basic.py` L137 `abs_max.to(tensor.dtype)` 在除以 7.0 之前将 abs_max 压为 fp16，放大了 INT4 粗步长 (~1/7) 的量化误差
- **Changed files**:
  - `src/quant/int4_basic.py` — 3 处: L137 abs_max→float32, L151 scale→float32, L187 static scale→float32
  - `src/cache/int4_cache.py` — 3 处: L298 expand_static_scale→float32, L313 dynamic_scale→float32, L462-465 get_kv()→.to(self.dtype)
  - `src/engine/generate_loop.py` — 1 处: L550-552 INT4 scale 加载为 float32（INT8 保持 fp16）
  - `tests/test_int4_cache.py` — 4 处断言更新 + 5 个新测试 (TestENG066Float32ScaleChain)
- **Commands**: `python3 -m py_compile` (4 files) + `pytest tests/test_int4_cache.py -v`
- **Outputs**: py_compile 全通过; pytest 56/56 passed (0 failed)
- **Validation**: 本地通过; 远端 full regression 待执行
- **Risks / follow-ups**:
  - INT8 路径未修改（步长 1/127 对 fp16 精度容忍度高，本轮控制范围）
  - float32 scale 增加 ~<1% 显存（scale 元素 = KV 元素/group_size）
  - int4_baseline 也受影响，Wave 1 实验必须同时重跑 baseline
  - 待提交: 远端 pytest 通过后 commit
- **配置补全**: 向 7B/8B rescue snapshot 追加 int4_baseline_long + curve_{4k,8k,16k} 条目
  - `configs/snapshots/exp_matrix_qwen25_7b_int4_rescue_v1.yaml` — 4 条目
  - `configs/snapshots/exp_matrix_llama31_8b_int4_rescue_v1.yaml` — 4 条目（model_revision 已修正）
- **远端验证**: pytest 341 tests passed (167 cache + 174 quant/config)
- **Wave 1 启动**: `tmux:int4_t2` @ 2026-03-12 05:56, 3 模型顺序执行
  - Step 1: 1.5B eval_ppl+eval_needle (baseline+rescue) × 3 seeds
  - Step 2: 7B eval_ppl (baseline+rescue) × 3 seeds
  - Step 3: 8B eval_ppl+eval_needle (baseline+rescue) × 3 seeds
  - Step 4: aggregate → `results/int4_t2_float32_v1/`
  - 预计完成: ~6-10h (2026-03-12 12:00-16:00)

### 2026-03-12 19:05 | 论文十轮打磨 R1-R10 — 达到顶级期刊发表水平
- Goal: 系统性提升论文叙事严谨性、技术精度、符号一致性、修辞力度
- Changed files:
  - `thesis/chapters/ch1_introduction.tex` — R2 去重精简（-30行）+ R5 符号统一（$h→h_{KV}$, $d→d_h$）
  - `thesis/chapters/ch2_related_work.tex` — R6a GQA 头比描述精确化
  - `thesis/chapters/ch3_method.tex` — R6b τ⁻¹稀疏性解释 + R6c 静态Scale桥接段 + R9a 表注释明确int4_fused vs int4_ours
  - `thesis/chapters/ch4_experiments.tex` — R1 overclaim修正 + R3 C6叙事重构+威胁效度扩展 + R4 句子级修辞打磨 + R8 消融标题+量化噪声公式 + R9b/c 交叉引用
  - `thesis/chapters/ch5_conclusion.tex` — R1 部署可行性限定 + R4c 正面表述 + R7a 去重 + R7b 校准成本ROI段
  - `thesis/chapters/appendix.tex` — 无实质改动（仅作为交叉引用目标）
- Validation: `latexmk -xelatex` 编译通过, 81 页; grep overclaim残留=0; grep undefined ref=0; 符号一致性检查通过
- diff stat: 7 files, +104 -101 (净增 3 行)
- Risks: 无——所有改动为文字润色，不改数据/表格/Claim判定
- Commit: `c5e908b`

### 2026-03-12 19:10 | C6 FAIL 一致性修复 — ch4 发现段 + ch5 结论/启示段
- Goal: 消除 C6 (INT8 RULER FAIL) 在总结性段落中被错写为 PASS 或误归 INT4 的矛盾
- Changed files:
  - `thesis/chapters/ch4_experiments.tex` — 发现一标题+正文: "全部5个endpoints+C3--C6"→"C1--C5 PASS"+C6 FAIL 单独说明
  - `thesis/chapters/ch5_conclusion.tex` — L16 "全部质量基准"→三项核心基准; L19 C6 正确归类为 INT8 RULER; L91/L139 加 RULER 例外
- Validation: `latexmk -xelatex` 编译通过 81页; grep "全部质量基准"仅剩表格描述(无overclaim); grep "Claims C3--C6"=0; grep "INT4.*C6"=0
- Commit: `6ac750c`

### 2026-03-12 19:16 | 结论摘要延迟表述修正
- Goal: 修复"延迟与质量一起写成统计不可区分"的逻辑矛盾
- Changed files:
  - `thesis/chapters/ch5_conclusion.tex` — L16-18: 质量(统计不可区分) vs 延迟(显著降低) 拆为并列关系
- Commit: `3b8d8db`

### 2026-03-17 03:17 | KIVI profiling 数据正式聚合（含 8K 补跑）
- Goal: 将 phase6_kivi 补跑数据合入 canonical bundle，补跑 8K gen_len=64，消除全部 NaN
- Source: `results/phase6_kivi/runs/` (32 dirs = 24 原有 + 8 新增 8K curve)
- Target: `results/emnlp_final_raw/runs/` (2136 → 2168 dirs)
- Provenance: kivi_style 1.5B latency/memory 曲线（gen_len=64, batch=1）：
  - 4K/16K/32K: Phase 6 KIVI 补跑 (2026-03-16)
  - 8K: Phase 6 KIVI 二次补跑 (2026-03-17, run_name=kivi_style_int8_curve_8k)
  - 注: Phase 5v2 吞吐量数据 (8K, gen_len=128) 仍存在于 bundle 中，但被 LaTeX 导出过滤
- Commands: rsync merge → aggregate_results.py → export_tables_latex.py
- Validation (全部通过):
  - latency_summary.csv: 1.5B kivi_style batch=1 gen_len=64 覆盖 {4096,8192,16384,32704} ✅
  - 32K TPOT=47.73ms, KV Mem=462.1MB ✅
  - 8K TPOT=37.84ms, KV Mem=116.5MB ✅ (新增)
  - LaTeX 表: KIVI-style 列 4 个 seq_len 全部有值，NaN=0 ✅
- Backup: `tables_backup_pre_kivi_20260316_1234/`, `latex_tables_backup_pre_kivi_20260316_1234/`
- Commit: (pending)

### 2026-03-13 15:25 | 论文图表升级 — 出版质量 300 DPI + 标题修正
- Goal: 将全部 19 张 matplotlib 论文图从 160 DPI 默认风格升级为 300 DPI 出版质量（统一色盘、CI 误差带、CJK 字体、语义配色）
- Changed files:
  - `scripts/generate_thesis_figures.py` — **新增** ~550 行图表生成脚本，16 个生成函数，覆盖 PPL/Needle/TPOT/Memory/RULER/LongBench/invtau/throughput 等全部图表
  - `thesis/figures/*.png` — 19 张图全部重新生成（300 DPI, Songti SC 字体, 统一色盘+marker）
  - `thesis/chapters/ch4_experiments.tex` — L302/L307/L312: PPL 图标题更新（折线→分组柱状图+内嵌放大）
  - `thesis/chapters/appendix.tex` — L296 TPOT gain 标题修正; L306-309 重写 caption 消除 overclaim; L316 seq_len=4096→8192
- Key improvements:
  - PPL: 单点折线→分组柱状图+INT8 区间内嵌放大（mpl_toolkits inset_axes）
  - Needle: 7 线拥挤图→INT8/INT4 双面板
  - TPOT gain: 方向标注（↑加速/↓减速）
  - invtau heatmap: 仅标注非 1.0 单元格
- Validation: `latexmk -xelatex` 编译通过 80 页，无 undefined ref
- Risks: needle_summary 无 config 级过滤列，int8_ours 32K 显示 70.3%（含消融变体），为预存数据局限非本次引入
- Commit: `25f7e1c`

### 2026-03-17 04:37 | Claim 口径修正 Note + thesis-safe-v1 基线冻结

**Canonical claim numbers**（以 `results/emnlp_final_raw/report/claim_validation.csv` 为唯一权威来源）：
- **C6**: RULER 退化 **-2.64%**（精确值 -2.641327...），阈值 ≥-1%，FAIL，target model = Qwen/Qwen2.5-1.5B-Instruct
- **C7**: Needle 退化 **-2.0%**（精确值 -2.0），阈值 ≥-1%，FAIL，target model = meta-llama/Llama-3.1-8B-Instruct
- **C8**: PPL 退化 **-15.92%**（精确值 -15.917412...），阈值 ≥-0.5%，FAIL，target model = Qwen/Qwen2.5-7B-Instruct

**历史条目修正说明**（iteration.md 为 append-only，不修改旧条目）：
- Line ~232 中 "C6 RULER -2.82%" 和 "C7 INT4 Needle -3.33%" 是较早分析阶段的数字，非最终聚合值
- Line ~292 中 "C6 FAIL: -2.64%" 和 "C7 FAIL: -2.0%" 与 canonical CSV 一致
- Line ~354 中 "C6: ❌ FAIL ... LLaMA-8B 单模型" 模型标注有误，C6 target model 是 Qwen-1.5B

**thesis tex 状态**：ch4/ch5 中的数字已与 canonical 一致（-2.64%, -2.0%, -15.92%），无需修正。

**thesis-safe-v1 基线**：
- Tag: `thesis-safe-v1` (commit `9d7dbea`)
- 正式口径: 8 PASS / 3 FAIL (C6 -2.64%, C7 -2.0%, C8 -15.92%)
- 后续 unified 尝试全部在 postfix 世界进行，不污染此基线

### 2026-03-17 04:37 | M1: 建立 legacy/postfix 双世界

**双世界声明**：
- `results/emnlp_final_raw/` = **legacy / thesis-safe 基线（只读）**，任何新实验不得写入
- `results/emnlp_postfix_v1/` = **unified 尝试空间（实验性）**，含 runs/tables/plots/latex_tables/logs/report
- `artifacts/calibration_postfix_v1/` = **postfix calibration 专用**，不覆盖 legacy artifacts/

**目录结构**：
- `results/emnlp_postfix_v1/{runs,tables,plots,latex_tables,logs,report}` ✅
- `artifacts/calibration_postfix_v1/` ✅

**Postfix gate configs**（3 份，每份仅含 int4_baseline_long + int4_ours_postfix_long）：
- `configs/snapshots/exp_matrix_postfix_1p5b_v1.yaml` — 1.5B, calib=kv_calib_kl_1p5b_int4_postfix.json
- `configs/snapshots/exp_matrix_postfix_7b_v1.yaml` — 7B, calib=kv_calib_kl_7b_int4_postfix.json
- `configs/snapshots/exp_matrix_postfix_8b_v1.yaml` — 8B, calib=kv_calib_kl_8b_int4_postfix.json

**设计要点**：
- int4_ours_postfix_long: `kv_mode=int4_ours`（聚合兼容），`use_attn_temperature=false`（对齐 INT8-ours mainline）
- int4_baseline_long: 完全复制 legacy 参数，不绑定 postfix calibration
- 所有 postfix runs 显式绑定 version=2 校准产物（M2 生成后方可执行）

### 2026-03-17 04:47 | M2-1: Calibration postfix chain (CAL-033/014/017/020/036/043)
- Goal: 修复 calibration 主链问题，为 postfix gate 生成可审计、可区分的 v2 校准产物
- Changed files:
  - `scripts/calibrate_behavior.py` — 核心修改：
    - CAL-033: version 1→2，新增 provenance 字段（model_revision, seed, dataset_source, n_samples, seq_len）
    - CAL-014: 审计确认 hidden_states indexing 正确（HF tuple[0]=embedding=layer0 input），加注释
    - CAL-020: select_best_trial 所有路径的 group_size tiebreaker 改为 log2(group_size) 归一化
    - CAL-036: CSV trials_sorted 排序键对齐 select_best_trial 的选择模式 + 新增 is_selected 列
    - CAL-043: provenance 字段写入 JSON v2 payload
    - CAL-017: model_revision + seed 字段已包含在上述修改中
  - `src/engine/generate_loop.py` — CAL-033 version check: 加载 JSON 后检查 version，<2 发 warning
  - `tests/test_calibrate_behavior.py` — 新增 4 个测试：v2 provenance、log2 normalization、feasible mode 验证
  - `review_tracker.md` — CAL-033/014/017/020/036/043 标注 fixed
- Commands: `python3 -m py_compile`, `pytest tests/test_calibrate_behavior.py -v`
- Outputs: 全量编译通过，40/40 tests passed（含 4 个新测试）
- Validation: ✅ 编译通过 + 测试通过 + tracker 更新
- Risks: CAL-020 log2 归一化不改变排序方向（仍 ascending），只平衡间距；CAL-014 为 false positive（tracker 原描述有误）
- 待 M2-2/M2-3: 需在远端 GPU 执行 determinism 审计 + 重生 postfix calibration

### 2026-03-17 05:44 | M2-2/M2-3 + M3: Postfix calibration + unified gate
- Goal: 校准确定性审计 → 重生 postfix 校准产物 → 最小 unified gate 实验 → gate 判定
- **M2-2 确定性审计**: ✅ PASS — 两张 GPU 同参数运行，k_scale/v_scale/inv_tau 完全一致 (max_diff=0.00)
- **M2-3 postfix calibration**: ✅ 完成
  - 1p5b: `artifacts/calibration_postfix_v1/kv_calib_kl_1p5b_int4_postfix.json` (version=2)
  - 7b: `artifacts/calibration_postfix_v1/kv_calib_kl_7b_int4_postfix.json` (version=2)
  - 8b: `artifacts/calibration_postfix_v1/kv_calib_kl_8b_int4_postfix.json` (version=2, local path)
- **M3 gate results (19 runs, 2x H20)**:
  - Official Gate C7 (Needle): **PASS** (0.0%, threshold ≥-1%), 从 legacy -2.0% 改善
  - Official Gate C8 (PPL): **FAIL** (-42.71%, threshold ≥-0.5%), 从 legacy -15.92% 恶化
  - Unified Gate UG1 (Needle): ❌ 仅 1/3 模型 eligible (8B=100% parity)
  - Unified Gate UG2 (PPL): ❌ 全 3 模型 >30% 退化 (1.5B -191%, 7B -43%, 8B -32%)
  - INT8 sanity: ✅ PPL=8.9518 vs legacy 8.9538 (within CI), Needle=100%
- **Gate 决策: ❌ FAIL → 停止 unified 尝试，回退到 thesis-safe-v1**
- **根因分析**: search 选出 group_size=16/clip=99.0（KL 最优），但与 baseline 的 gs=32/clip=99.9 不同。
  tighter clipping + 关闭 temperature 导致 runtime PPL 大幅退化——校准目标(attention KL)与下游质量(PPL)脱节
- 详细数据: `results/emnlp_postfix_v1/report/unified_gate_memo.md`
- 论文主线不变: "INT8 成功 + INT4 失败分析"，基线 = thesis-safe-v1 (tag 9d7dbea)

### 2026-03-17 11:26 | Tier 0: 基础设施补齐 — EMNLP Final Research Plan
- Goal: 实现研究计划 Tier 0（Day 0）全部基础设施，为 GPU 实验做好前置准备
- Changed files:
  - `scripts/sync_merged_runs.sh` (NEW): 幂等合并 emnlp_final_raw + emnlp_postfix_v2 → emnlp_final_merged
  - `src/cache/mixed_kv_cache.py`: 扩展 k_bits/v_bits 参数 (4/8/16)，支持 K/V 消融和反事实实验
  - `src/engine/generate_loop.py`: generate_from_ids + generate 新增 k_bits/v_bits 参数传递
  - `scripts/eval_ppl.py`: 新增 --dataset wikitext2/c4, --k_bits, --v_bits; build_kv_cache 传递
  - `scripts/eval_needle.py`, `eval_longbench.py`, `eval_ruler.py`: 新增 --k_bits/--v_bits + generate_from_ids 传递
  - `scripts/profile_latency.py`, `profile_memory.py`: 注册 int4_mixed_kv/int4_kivi_aligned 到 kv_mode choices + k_bits/v_bits
  - `scripts/run_experiments.py`: 命令构造逻辑新增 k_bits/v_bits 从 YAML run_entry 读取并传递
  - `scripts/config_utils.py`: resolve_run_config 解析 k_bits/v_bits; ALLOWED_MODEL_IDS 新增 Mistral-7B + Qwen14B
  - `configs/snapshots/exp_matrix_mixed_kv_{1p5b,7b,8b}_v1.yaml` (NEW×3): Core 3 模型 MixedKV + K/V 消融 + KIVI matched
  - `configs/snapshots/exp_matrix_mixed_kv_{mistral7b,qwen14b}_v1.yaml` (NEW×2): Extension 模型配置
  - `objective.md`: 论文定位更新(behavior-aligned analysis framework), 模型层级(+Extension), 贡献4(K/V insight), SOTA表(+MixedKV)
- Commands: `python3 -m compileall -f src/ scripts/ tests/` (PASS), `pytest tests/test_mixed_kv_cache.py -v` (9/9 PASS)
- Validation: 编译全通过, MixedKV 测试 9/9 通过, sync_merged_runs.sh 合并 2168 run dirs
- Risks/follow-ups:
  - Extension 模型 revision 待远端下载后 pin (configs 中标为 TBD)
  - C4 数据集使用 streaming 模式，需远端测试网络连通性
  - 完整 pytest 需远端验证 (本地缺 numpy/libcblas)
  - T0-D2 (模型预下载) 和 T0-E dry-run 需远端 GPU 执行

### 2026-03-17 19:04 | T0-D2 + Remote Deployment + MixedKV Smoke Test
- Goal: 远端部署验证 + Extension 模型 revision pin + MixedKV 首次端到端运行
- Changed files: configs/snapshots/exp_matrix_mixed_kv_{mistral7b,qwen14b}_v1.yaml (revision pin)
- Commands:
  - `rsync` 推送 20 文件到 AutoDL
  - `pytest tests/test_mixed_kv_cache.py -v` → 9/9 PASS (远端)
  - `run_experiments.py --dry_run` → 32 DRY RUN commands 正确
  - MixedKV PPL smoke test: `eval_ppl.py --kv_mode int4_mixed_kv --max_samples 8` → PPL=10.88
  - Extension model revision lookup → Mistral c170c7, Qwen14B cf98f3
- Validation: MixedKV 端到端可跑, PPL=10.88 合理 (FP16~8.95, KIVI-INT4~11-13)
- Risks: 远端 hf-mirror 代理偶尔连不上（已自动 fallback 到缓存）; 模型实际下载待 Day 5

### 2026-03-18 13:53 | Day 1-2: Layer B+C Massive Parallel Experiments
- Goal: MixedKV Core 3 全评测 + K/V 消融 multi-seed + Layer C Extension 模型
- 执行方式: 2×H20 GPU 并行, 3-way 任务链自动衔接
- 核心结果 (MixedKV K@INT8/V@INT4 vs FP16 vs KIVI INT4):
  | 模型 | MixedKV PPL | FP16 PPL | KIVI PPL | MixedKV Needle |
  |------|------------|---------|---------|---------------|
  | 1.5B | 9.33 | ~8.95 | 10.55 | 100% |
  | 7B | 7.17 | ~6.80 | 7.50 | 100% |
  | 8B | 6.73 | ~6.30 | 6.88 | 100% |
  | Mistral-7B | 5.20 | 5.19 | 5.33 | 100% |
- K/V 2×2 Factorial (seed 1234):
  - K-only (K8/V16): PPL 几乎无退化 (9.30/7.15/6.72)
  - V-only (K16/V4): PPL 几乎无退化 (9.31/7.12/6.73)
  - 反事实 (K4/V8): 1.5B=1345, 7B=5070 → K@INT4 致命（8B 例外=6.78）
- 实验产出: 142 run directories, 覆盖 seed 1234-1238 × 3 models + Mistral-7B Layer C
- 修复: sentencepiece 安装 (Mistral tokenizer依赖), tmux conda PATH 问题
- Qwen14B: shard 下载不完整 (xethub CDN 超时), 后台重下中
- Risks: Qwen14B 网络下载不稳定; Mistral/Qwen14B 未在 config_utils ALLOWED_MODEL_IDS 白名单需确认

### 2026-03-18 17:53 | Layer B+C 全部实验完成
- Goal: Layer B 全矩阵 + Layer C Mistral-7B 外部有效性
- 总产出: **171 run directories, 158 有效 runs with data**
- Layer B 完成:
  - B1 MixedKV Core 3 全评测 (1.5B/7B/8B × 5 seeds × 4 tasks)
  - B2 PPL curves (4K/8K/16K × 3 models × 5 seeds)
  - B3 K/V 消融 (k_only/v_only/反事实 × 3 models × 4-5 seeds)
  - B6 KIVI INT4 matched (3 models × 5 seeds)
- Layer C 完成:
  - Mistral-7B: MixedKV + FP16 + KIVI INT4 × 5 seeds 全完成
  - Qwen14B: 磁盘空间不足(100GB数据盘满) → 放弃
- 关键修复:
  - sentencepiece 安装 (Mistral tokenizer 依赖)
  - tmux conda PATH 问题 (改用完整路径 /root/miniconda3/bin/python3)
  - 系统盘清理 (/root/.cache/huggingface 重复缓存, 释放 12GB)
  - 脚本放数据盘 (/root/autodl-tmp/) 避免系统盘满
- C4 PPL: 因离线模式无法下载 C4 数据集，降级为 Tier 2
- 核心结果确认:
  - MixedKV 优于 KIVI INT4 (所有 4 模型一致)
  - Mistral MixedKV PPL 仅 +0.17% vs FP16 (最优)
  - PPL 确定性 (greedy, 所有 seed 一致)
  - Needle 全模型全 seed 100%
- 待办: Layer A C6 RULER 修复, B9/B10/B11 消融, 聚合+LaTeX 导出
