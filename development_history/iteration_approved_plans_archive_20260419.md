# iteration.md Approved Plans Archive

归档日期：2026-04-19 03:12 CST

归档原因：
- 用户授权清理 `iteration.md` 中已经过期的 `Approved Plans`
- 历史计划保留原文，后续查阅统一从本文件进入
- 当前有效执行入口已转移到：
  - `objective.md`
  - `docs/thesis_upgrade_live_plan.md`
  - `docs/mainline_execution_queue.md`
  - `.agents/execplans/`

以下内容从 `iteration.md` 的 `## Approved Plans` 区整体迁入，保留原始顺序与状态标记。

## Approved Plans (Archived from iteration.md)

### ~~Plan: Closure Pack + Expansion Pack 论文收口~~ ✅ Part A 完成 2026-03-19
- **批准日期**：2026-03-18
- **状态**：✅ Part A 全部完成 (GPU 0: 13h04m, GPU 1: 15h22m)
- **Part A (Closure Pack)**:
  - [x] A1: MixedKV LongBench (30 CSVs, 4 models, 零失败)
  - [x] A2: MixedKV RULER (30 CSVs, 4 models, 零失败)
  - [x] A3: C6 INT8 RULER CWE-fix 验证 (15 CSVs)
  - [x] A4: B9 热力图 (6 PDFs, 3 models)
  - [x] A5: B11 INT8 ours vs baseline 对比表 (CSV + LaTeX)
  - [x] A6: 论文数据聚合 (22 paper tables, 4 组)
- **Part B (Expansion, 可选)**:
  - [ ] E2: B10 校准灵敏度消融 (值得做, 3h GPU)
  - [ ] E4: C4 PPL (条件做, 需网络)
- **结果目录**: emnlp_postfix_v2/runs (A1/A2/A4), emnlp_c6_fix/runs (A3)
- **脚本**: closure_gpu0.sh, closure_gpu1.sh, build_int8_comparison.py, build_paper_tables.py

### ~~Plan: Expansion Pack 高信号版 (5 Phases, ~14-17h GPU)~~ ✅ 完成 2026-03-20
- **批准日期**：2026-03-19
- **前置条件**：Closure Pack Part A 完成, Phase 0 gate 通过
- **状态**：✅ 全部完成 (GPU 0: 09:06, GPU 1: 03:59, 零失败, 后处理含 bug fix 已通过)
- **Phase 0**: ✅ 本地验证通过
- **Phase 1**: ✅ B10 校准灵敏度 (18 dirs, 6 calib JSONs)
- **Phase 2**: ✅ K/V 消融 LongBench (36 dirs, 零失败)
- **Phase 3**: ✅ C6 修复 RULER sanity (6 dirs)
- **Phase 4**: ✅ K/V 消融 RULER (27 ruler CSVs)
- **Phase 5**: ✅ B9 Mistral 热力图 (1 JSON → 2 PDFs)
- **后处理**: ✅ bug fix (glob pattern + metric columns) + postprocess 全通过
- **结果目录**: results/emnlp_expansion_v1/ (60 dirs, 111 profile CSVs, 6 calib JSONs, 8 heatmap PDFs)

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

### Plan: Phase 2 编号 7+8 验证版 Run Matrix（Codex 2026-04-18 修正版）
- **批准日期**：2026-04-18 08:40（用户 Q1=a/Q2=a/Q3=yes 三决策隐式 APPROVE）
- **前置条件**：编号 7 M4 完成（硬 Gate 1 PASS k=1；次 Gate FAIL k≥3 tie；max ≈ mean 稳健发现）
- **状态**：🟡 C1 (7B batch3) 执行中
- **核心转向**：不扩故事，专注"验证现有 4 条结论稳定性"。greedy decode 下 BAKV/Heuristic 多 seed 无意义，改用 5 类真实稳定性验证：
  1. Random-k 多 seed (5 seeds)
  2. 扩 n (50→100→200)
  3. Sample offset (0/50/100)
  4. 扩任务 (dureader/vcsum/trec/lcc)
  5. 跨模型 (Qwen 7B → 视结果 LLaMA 8B)
- **LLaMA-8B 资源已定位**（不用下载）：`/root/autodl-tmp/hf_cache/hub/models--meta-llama--Llama-3.1-8B-Instruct` + INT8/INT4 calib `kv_calib_kl_llama31_8b_int{4,8}.json` 已 copy 到 `artifacts/`（num_layers=32）
- **执行顺序（Q2=a 严格按批）**：
  - Pre-0: sample_offset CLI + 3 批 runner 脚本
  - [~] C1: Qwen 7B × 编号 8 完整矩阵 42 runs（进行中 bg `bj9lgkhi9`）
  - [ ] 第一批: 1.5B 稳定性 A1-A4 = 66 runs
  - [ ] 第二批: 扩 4 任务 + B+ Random multi-seed = 32 runs
  - [ ] C2 (LLaMA-8B): 视 C1 结果决定（资源已 ready，预估 ~30 min）
  - [ ] Post: Bootstrap CI + sign test + Pareto
- **7B 初步发现**：7B BAKV k=3 protected=[0, 3, 27] vs 1.5B [0, 1, 15]——**layer 0 跨规模稳定，中后段选择不同**
- **Plan 文件**：`.claude/plans/partitioned-sparking-newt.md` 编号 7/8 段
- **关键新文件**：`phase2_batch3_cross_model_7b.sh` / `phase2_gen_sweep_policies_7b.sh` / 14 个 7B policy JSON / eval_longbench.py 加 `--longbench_sample_offset`

### ~~Plan: Phase 2 编号 6 — Layer-wise Allocator MVP（Codex 2026-04-18 修订版 v2）~~ ✅ 完成 2026-04-18 06:42
- **批准日期**：2026-04-18 06:20
- **前置条件**：Gate 5 PASS（3/4 可判定判据，2026-04-18 06:01），Phase 1 编号 1-5 全部完成
- **状态**：✅ 全部完成——M1/M2/M3/M4 四 Gate 全 PASS
- **M4 硬 Gate 🟢 PASS**（BAKV 3/3 tasks 胜 Random，平均 +46%）
- **M4 次 Gate ⚠️ 边缘**（BAKV 1/3 tasks 胜 Heuristic；2/3 差 <0.5% tie）
- **关键发现 F1-F4**：见 plan file 编号 6 节详细记录（lens 显著强于 random；与 heuristic 接近平手；Pareto 上界夹挤；Codex 巡检捕到 dedup bug）
- **解锁**：编号 7（Budget Sweep + 消融）授权启动
- **Plan 文件**：`/Users/chenzilang/.claude/plans/partitioned-sparking-newt.md` 编号 6 节
- **核心设计（Codex 修订 4 点）**：
  1. 沿现有 `int4_mixed_kv` 路径最小扩展（`per_layer_bits=None` 保 backward compat）
  2. 5 组 policy 全部由 `behavior_aligned_allocator.py` 生成（含新增 `heuristic` policy）
  3. 聚合主键从 `(task, kv_mode)` 扩到 `(task, kv_mode, policy_name)`
  4. 硬 gate 放宽为"BAKV > Random 且 ≥2/3 tasks 胜"，不强制上下界夹挤
- **里程碑状态**：
  - [~] M1: W1 MixedKVCache 扩展 + W6 5 单测（pytest PASS）— 执行中
  - [ ] M2: W2a/b 路由 + W3 heuristic policy + 冒烟（n=5 × BAKV_Top3 × narrativeqa）
  - [ ] M3: W4 3 GPU × 5 policies × 3 tasks × n=50 = 15 run
  - [ ] M4: W5 聚合 + gate 判定（BAKV > Random? → 编号 7 / v6-stable）
- **关键文件**：
  - 改：`src/cache/mixed_kv_cache.py`、`src/engine/generate_loop.py`、`scripts/eval_longbench.py`、`scripts/adaptive/behavior_aligned_allocator.py`
  - 新：`scripts/phase2_allocator_mvp.sh`、`scripts/aggregate_phase2.py`、`tests/test_mixed_kv_cache_per_layer.py`
- **预估总耗时**：~100 分钟（本地代码 ~60 min + 远端 GPU ~35 min + 聚合 ~5 min）

### Plan: 论文优化 v5.2 — Role-Aware Asymmetric + Behavior Alignment 主线升级
- **批准日期**：2026-03-23
- **前置条件**：v4.1 代码完成, thesis-safe-v1 冻结, Expansion Pack 数据就绪
- **状态**：✅ M0-M4.4 全部完成，Gate 3.5/4A/4C PASS，50 结果目录
- **里程碑状态**：
  - [x] M0: 冻结 fallback (artifacts/2026-03-23_thesis_fallback/)
  - [x] M1: Q1-Q6 文本修复 (ch2/ch3/ch4, 7 处修改)
  - [x] M2: KIVI Gap Audit (docs/kivi_gap_audit.md)
  - [x] M4.0a: 设计文档 (docs/rolealign_design_note.md)
  - [x] M4.0b: 代码实现 (RoleAwareAsymKVCache + 路由 + 校准扩展 + 实验配置)
  - [ ] M3: 补强实验 (GPU)
  - [ ] M3.5: Feasibility Probe (GPU)
  - [ ] M4.2: ours_asym smoke test (GPU)
  - [ ] M4.3: ours_asym_ba (GPU)
  - [ ] M4.4: vs KIVI head-to-head (GPU)
  - [ ] M6: 论文更新 (根据实验结果)
- **关键新文件**: role_aware_asym_cache.py, exp_matrix_rolealign.yaml, kivi_gap_audit.md, rolealign_design_note.md

### ~~Plan: INT4 KV-RoleAlign — Bit-Width-Aware Behavior Alignment (v4.1)~~ → 升级为 v5.2
- **批准日期**：2026-03-17
- **前置条件**：M3 gate FAIL 确认, thesis-safe-v1 冻结
- **状态**：🟡 Phase 0-2 代码实现完成，已升级为 v5.2 计划
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
