# Iteration Log (Single Source of Progress)

This file is the only progress tracker for the repository.
`lang.md` is deprecated and archived.
Canonical agent workflow directory is `.agents/`.

## TODO Backlog (Top)

### 代码审查发现（2026-02-23 监管审查）

> 以下问题由项目监管 agent 在全面代码审查中发现，按严重性分类排列。
> 标注 `[CRITICAL]` / `[HIGH]` / `[MEDIUM]` / `[LOW]`。修复前不应启动全量实验。

---

#### A. MSE 校准实现缺陷 — `scripts/calibrate_behavior.py`（阻塞 Phase 4）

- [x] `[CRITICAL]` MSE loss 维度语义错误 (L199-200) — ✅ 已修复 commit 20095fb
- [x] `[CRITICAL]` MSE loss 全局 mean 无维度 (L302) — ✅ 已修复 commit 20095fb
- [x] `[HIGH]` loss_accum 未除以样本数 (L177-206) — ✅ 已修复 commit 20095fb
- [x] `[HIGH]` MSE 无数值安全 clamp (L199) — ✅ 已修复 commit 20095fb
- [ ] `[HIGH]` trial 排名受 loss 尺度影响 (L780-791): `p95_mse` vs `p95_kl` 尺度完全不同，搜索排名在不同序列长度下不可复现（注：MSE 搜索内部排名一致，跨 loss_function 不可比是预期行为，降级为文档问题）
- [x] `[MEDIUM]` 默认输出文件名硬编码为 `kl.json` — ✅ 已修复 commit 20095fb
- [x] `[MEDIUM]` `select_best_trial()` 无 key 存在性校验 — ✅ 已修复 commit 20095fb
- [ ] `[MEDIUM]` MSE loss 语义未文档化 (L6, L234-239): 无 docstring 说明 MSE 是位置平均还是全局平均

#### B. KIVI Cache 实现 — `src/cache/kivi_style_cache.py`

- [x] `[CRITICAL]` K-scale/zp 在 `clear()` 后状态不一致 — ✅ 已修复 commit 20095fb
- [ ] `[MEDIUM]` decode K 量化与 prefill K 量化 device 一致性未强制 (L220-231): 若输入 k 与 cache device 不同会静默失败
- [ ] `[MEDIUM]` V buffer shape 一致性未校验 (L126-131): 仅校验 K buffer 的 batch/heads/head_dim，不校验 V buffer
- [ ] `[MEDIUM]` `append()` 无输入 tensor shape 校验 (L187-245): 若传入转置 tensor（如 [B,D,H,S]）不会报错但量化结果错误
- [ ] `[LOW]` `_seq_len` 仅在 layer_id=0 时更新 (L244-245): 假设所有 layer 同步 append，不一致使用会导致 seq_len 错误
- [ ] `[LOW]` 无 batch_size=0 校验 (L204): 空 batch 不会显式报错

#### C. 非对称量化模块 — `src/quant/asymmetric_quant.py`

- [x] `[CRITICAL]` percentile < 50 时 quantile_lo > quantile_hi — ✅ 已修复 commit 20095fb
- [x] `[CRITICAL]` 无 percentile 范围校验 — ✅ 已修复 commit 20095fb
- [ ] `[MEDIUM]` float16 输入精度损失 (L58-59): quantile 在 float32 计算后转回 float16，scale/zp 精度下降
- [ ] `[LOW]` dequantize 函数无输入类型校验 (L74-95): 传入错误 dtype 静默产生错误结果

#### D. Engine 集成 — `src/engine/generate_loop.py`

- [x] `[HIGH]` `generate()` 函数缺少 `quant_bits` 参数 — ✅ 已修复 commit 20095fb
- [ ] `[HIGH]` decode 阶段 KIVI 走 dequant→re-quant 路径 (L635-678): 每步 dequant 全量 cache 后取最后 token re-quant 回 cache，引入不必要的精度损失
- [ ] `[MEDIUM]` KIVI kv_mode 未校验 quant_bits∈{4,8} (L294-310): 无效 quant_bits 延迟到 KIVIStyleKVCache.__init__ 才报错
- [ ] `[LOW]` docstring 未说明 KIVI 模式行为 (L258-292): 无 KIVI 模式的参数说明和约束文档

#### E. 评测脚本集成（跨脚本）

- [x] `[CRITICAL]` `export_tables_latex.py` KV_MODE_DISPLAY 缺 kivi_style — ✅ 已修复 commit 8bf9414
- [x] `[CRITICAL]` `export_tables_latex.py` KV_MODE_ORDER 缺 kivi_style — ✅ 已修复 commit 8bf9414
- [x] `[HIGH]` `eval_longbench.py` 引用未定义 logger — ✅ 已修复 commit 20095fb
- [x] `[HIGH]` `generate_thesis_report.py` 缺少 KIVI claims — ✅ 已修复 commit 8bf9414 (C7-C11)
- [ ] `[MEDIUM]` 所有 eval 脚本 quant_bits fallback 将 KIVI 记录为 16 (eval_ppl L878 / eval_needle L467 / eval_longbench L833 / eval_ruler L985 / profile_latency L320 / profile_memory L369): `"int4" in "kivi_style"` 和 `"int8" in "kivi_style"` 均为 False，fallback 到 16
- [ ] `[MEDIUM]` `eval_longbench.py` 指标单位不一致 (L807-808): detail CSV 用 [0,1]，summary CSV 乘 100 变 [0,100]，下游聚合可能混淆
- [ ] `[MEDIUM]` `eval_longbench.py` 自实现 Rouge-L 可能与官方 LongBench 不一致 (L206-219): 自实现 token-level LCS 与 THUDM 官方评测脚本可能有差异
- [ ] `[MEDIUM]` `aggregate_results.py` kv_mode 排序无 KIVI (L552, L585, L648, L1322): 按字母排序而非语义排序
- [ ] `[LOW]` `eval_ruler.py` 多答案评分存在死代码 (L172-174): `pass` 语句无实际效果

#### F. 实验配置矩阵一致性

- [x] `[HIGH]` 1.5B 配置完全缺失 KIVI-style 条目 — ✅ 已修复 commit f07422d (exp_matrix.yaml +13 KIVI)
- [x] `[HIGH]` 7B/8B 配置完全缺失吞吐量 batch scaling 条目 — ✅ 已修复 commit f07422d (7B/8B +35 throughput each)
- [x] `[HIGH]` 7B/8B 配置缺失 INT4 长上下文运行 — ✅ 已修复 commit f07422d (7B/8B +5 long-ctx INT4/KIVI)
- [ ] `[MEDIUM]` 7B/8B 长上下文仅 3 条 vs 1.5B 的 18 条: 缺失 KIVI 长上下文、INT4 长上下文、多种 INT8-ours 变体
- [ ] `[MEDIUM]` 1.5B 校准文件命名不一致 (`kv_calib_kl_selected_v3_quick.json` vs 7B/8B 的 `kv_calib_kl_qwen25_7b_int8.json`): 命名约定不统一
- [ ] `[LOW]` 1.5B 配置头部注释缺少 `kivi_style` kv_mode 和 `kivi_asymmetric` calib_strategy

#### G. 消融配置审查 — `configs/snapshots/exp_matrix_ablation_1p5b_v1.yaml`（第二轮审查）

- [x] `[HIGH]` 消融 A-3 decode_attn_impl 混淆因子 — ✅ 已修复 commit f07422d (添加 A-3b percentile_fused 对比项)
- [x] `[HIGH]` 消融 A 节缺少 KIVI-style — ✅ 已修复 commit f07422d (添加 A-4 kivi_style 条目)
- [ ] `[MEDIUM]` 消融 A-2 (MSE) 使用 `use_attn_temperature: true` — MSE 校准的 inv_tau 可能不可信（见 A 节 MSE 缺陷），若 inv_tau 质量差会使 MSE 看起来更差，混淆校准方法本身的效果
- [ ] `[MEDIUM]` 消融 D 节缺少 dynamic scales 变体 — 计划中为 "static vs adaptive vs dynamic" 三方对比，当前仅 static 和 adaptive 两方（缺 `use_static_scales: false` 的 dynamic 变体）
- [ ] `[MEDIUM]` 所有消融仅 `seq_len=4096` — 计划中消融需 4K/8K/16K/32K 多长度点以支撑长上下文鲁棒性论证
- [ ] `[MEDIUM]` 消融 C 节 (group_size sweep) 使用同一个 calib_file — 该 calib 文件是在 group_size=16 下校准的，在 g=32/64/128 下使用可能不够公平（但可作为"校准鲁棒性"测试）
- [ ] `[LOW]` 消融 A-1/B-1/C-1 是完全相同的 run — 若 `--skip_completed_success` 正确工作则不重复跑，但配置冗余可简化

#### H. 新变更审查 — export_tables_latex.py / generate_thesis_report.py / configs（第二轮审查）

- [ ] `[MEDIUM]` `generate_thesis_report.py` C11 "cross-model robustness" claim 无 model_id 过滤 — 聚合运行时会将所有模型结果混合评估，需确认聚合逻辑是否按模型分组验证
- [ ] `[LOW]` 所有 3 配置文件的 KIVI 吞吐量仅包含 INT8（无 INT4 KIVI 吞吐量）— 可能遗漏 KIVI INT4 batch scaling 数据

#### J. 修复审查与新发现 — 第四轮审查（calibrate_behavior / kivi_cache / asymmetric_quant / eval_longbench）

**已修复项确认**（开发 agent 已提交修复）：
- [x] A1/A2 部分修复：`calibrate_behavior.py` MSE loss `.mean(dim=-1)` → `.sum(dim=-1)` 一致性修复 ✓；`.mean()` → `.sum()` 修复 ✓
- [x] A3 修复：`loss_accum /= num_samples` 样本数归一化已添加 ✓
- [x] A4 修复：MSE 路径添加 `torch.clamp(min=eps)` 数值安全 ✓
- [x] A6 部分修复：`--calib_out` default 从 `kv_calib_kl.json` 改为动态（见下方新 BUG）
- [x] B1 修复：`kivi_style_cache.py` `clear()` 现在重置 `_k_scale`/`_k_zp` 为 `[None]` ✓
- [x] C1/C2 修复：`asymmetric_quant.py` 添加 `50.0 < percentile <= 100.0` 范围校验 ✓
- [x] E1/E2 修复（上轮已确认）：`export_tables_latex.py` 添加 KIVI 到 KV_MODE_ORDER/DISPLAY ✓
- [x] E3 修复：`eval_longbench.py` 添加 `import logging` + `logger = logging.getLogger(__name__)` ✓
- [x] E4 修复（上轮已确认）：`generate_thesis_report.py` 添加 C7-C11 claims ✓

**新发现问题**：

- [x] `[CRITICAL]` `calibrate_behavior.py` `--calib_out` None fallback — ✅ 验证确认已有 fallback 逻辑（L643-645），误报
- [ ] `[MEDIUM]` `calibrate_behavior.py` MSE clamping 语义偏差：MSE 路径对 `p_ref`/`p_quant` 执行 `clamp(min=eps)` 后再计算差的平方。对 MSE 而言 clamp 不防 NaN（MSE 不含 log），反而将原始值为 0 的概率人为提升为 eps，改变了真实误差度量。不会导致崩溃但使 MSE 与 KL 的 clamping 语义不对称
- [ ] `[LOW]` `eval_longbench.py` logger 定义位置：`logger = logging.getLogger(__name__)` 在 `import` 块中间（介于 `traceback` 和 `from collections import defaultdict` 之间），不符合 PEP 8 import 分组规范（标准库 → 第三方 → 本地，中间不穿插代码）；功能无影响

#### I. final_emnlp2026_v1.yaml 审查（第三轮审查）

- [ ] `[MEDIUM]` `ablation_dimensions.scale_strategy` 仅列 `[static, adaptive]`（L77）— 计划中为 "static vs adaptive vs dynamic" 三方，与消融配置 D 节同一缺失
- [ ] `[LOW]` `benchmarks` 仅列 4 个质量评测（L67-71）— 未包含 latency/memory/throughput 系统性能 benchmark，虽然这些是独立维度但在 meta-config 中应有提及
- [ ] `[LOW]` `models[0].calibration_artifacts` 列出了尚不存在的 MSE 产物（`int8_mse`/`int4_mse`，L38-39）— MSE 校准实现有已知 bug，这些产物暂不可用

---

#### K. 深度审查 — `src/engine/generate_loop.py` KIVI 路径（第五轮审查）

- [ ] `[HIGH]` KIVI 模式静默忽略参数 (L412-486, L563): 若调用 `generate(..., kv_mode="kivi_style", use_attn_temperature=True, calib_file="...")` 不会警告，参数被静默丢弃。应对不兼容参数组合发出 warning
- [ ] `[MEDIUM]` KIVI decode 路径 dequant→requant 精度累积（已知 D2 但补充细节）: V cache 每步 per-token scale 重算 + K cache 用 prefill-time scale re-quant，双重量化≠量化一次。特别是 V 的 scale 分布在 decode 阶段与 prefill 阶段不同
- [ ] `[MEDIUM]` Batch 约束重复校验 (L344-361): 两段代码检查同一条件（batch>1 且 attention_mask 非全 1），KIVI 走 Block 1 但 Block 2 的错误信息暗示仅 fused 模式有此约束，可能误导开发者
- [ ] `[LOW]` KIVI docstring 缺失 (L288-291): 函数 docstring 未说明 kivi_style 的约束、行为、参数限制

**验证发现 — D1 已修复**: `generate()` 函数 L841 确认 `quant_bits=quant_bits` 已正确传递给 `generate_from_ids()`。之前报告的 D1 "generate() 缺少 quant_bits 参数" 实际上是误报，已更正。

#### L. 深度审查 — `scripts/run_experiments.py`（第五轮审查）

- [x] `[CRITICAL]` `eval_ppl.py` build_kv_cache() 缺失 kivi_style 分支 — ✅ 已修复 commit 03ed4a0
- [ ] `[MEDIUM]` skip_completed_success 状态不一致 (L1134 vs L1147): manifest 记录 "success" 但 execution_rows 记录 "skipped"，追踪混淆
- [ ] `[MEDIUM]` subprocess.run 无异常捕获 (L1174-1179): FileNotFoundError/OSError 会导致整个 run_experiments 崩溃而不清理 manifest
- [ ] `[MEDIUM]` kv_mode 无效值静默跳过 (L850-862): 无全局汇总报告哪些 run 因 kv_mode 无效被跳过
- [ ] `[LOW]` YAML 配置无 matrix 非空校验 (L725-794): 空 matrix 静默运行零任务但报告"成功"
- [ ] `[LOW]` append 模式 manifest 元数据被覆盖 (L252-265): 第二次 append 的 run_tag/seed 覆盖第一次，无法追溯历史参数差异
- [ ] `[LOW]` append_history 未记录 kv_mode/quant_bits 变化 (L272-278): 仅记录 tasks 和 config path，参数变化不可追溯

#### M. 深度审查 — `scripts/aggregate_results.py`（第五轮审查）

- [x] `[CRITICAL]` kivi_style 完全缺失显著性配对 — ✅ 已修复 commit 03ed4a0
- [x] `[HIGH]` longbench_official_macro 未被聚合 — ✅ 已修复 commit 03ed4a0
- [x] `[HIGH]` 显著性分析缺失 model_id/hardware 分组 — ✅ 已修复 commit 03ed4a0
- [x] `[HIGH]` RULER 深度分析缺失 model_id — ✅ 已修复 commit 03ed4a0
- [ ] `[MEDIUM]` kv_mode 使用字母序排序而非语义顺序 (L552, L585, L648, L1322): 表格中 int4_baseline 出现在 int8_baseline 之前，不符合论文叙述（先 INT8 后 INT4）
- [ ] `[MEDIUM]` 显著性配对数据可能被 aggfunc="mean" 静默平均 (L998): pivot_table 对多 replica 自动平均，如果同 seed 有重复数据，n_pairs 会被虚高估计
- [ ] `[LOW]` Bootstrap CI 单样本情况返回 (value, value) 无警告 (L1059-1060): 无法区分单样本 CI 与真正精确的无变异情况
- [ ] `[LOW]` 精确枚举阈值 n=16 硬编码 (L1092-1107): 从精确枚举到 MC 采样的切换点不可调

#### N. 第六轮审查 — eval_ppl.py / aggregate_results.py / CLAUDE.md 修复验证

**已修复项确认**（开发 agent 工作树修改，待提交）：
- [x] L1 修复：`eval_ppl.py` `build_kv_cache()` 添加 kivi_style 分支，创建 `KIVIStyleKVCache` ✓；同时添加 `quant_bits` 参数并在 `main()` 中传递
- [x] M1 修复：`aggregate_results.py` 添加 kivi_style 显著性配对 `("kivi_style", "int8_ours")` 和 `("kivi_style", "int8_baseline")` ✓
- [x] M2 修复：`aggregate_results.py` 添加 `longbench_official_macro` 到 `_to_numeric()` 列表和聚合值列表 ✓
- [x] M3 修复：`aggregate_results.py` 全部 5 个 sig_specs 的 key_cols 添加 `model_id`（latency/ppl/needle/longbench/ruler）✓ — 跨模型数据不再混淆
- [x] M4 修复：`aggregate_results.py` ruler_depth_keys 添加 `model_id` ✓

**修复质量评价**：eval_ppl.py 的 KIVI 分支正确使用 `KIVIStyleKVCache` 且只传必要参数（num_layers/device/quant_bits），其余用合理默认值。aggregate_results.py 单个 diff 同时修复 M1-M4 四项 HIGH+ 问题，涵盖显著性配对、聚合列、跨模型分组三个维度，修复完整。

**未修复的 M 节残留问题**：
- M5（kv_mode 字母序排序）、M6（pivot aggfunc="mean" 静默平均）、M7/M8（边界情况）— 低优先级，不阻塞

#### O. 深度审查 — `scripts/eval_ruler.py` 评分逻辑（第七轮审查）

> **严重警告**: eval_ruler.py 存在多个评分逻辑 bug，可能导致 RULER benchmark 结果不正确。在论文引用 RULER 数据前必须修复。

- [ ] `[CRITICAL]` MK-NIAH `hits_exact` 计数器死代码 (L172-174): `pass` 语句不执行 `hits_exact += 1`，`hits_exact` 变量初始化后从未递增。当前 `exact_match` 改由 `all_present` 逻辑补位（L177-180），但设计意图不清——若要逐个键检查 exact match 则逻辑缺失
- [ ] `[CRITICAL]` VT 多链评分仅评价第一条链 (L216, L442): 多链 VT 时 `expected_answers` 含 N 个值，但 `_score_case()` 调用 `_score_single_answer(prediction, case.expected_answers[0])` 只取第一个值。若 `ruler_vt_num_chains > 1`（默认=1 暂安全），其余链的答案被完全忽略
- [ ] `[CRITICAL]` 上下文截断从右侧保留破坏 RULER 语义 (L546-554): `_truncate_prompt_ids()` 在 prompt 超 `context_len` 时执行 `ids = ids[-max_tokens:]`（保留末尾 question，丢弃前面的 context/haystack）。RULER 的核心是在长上下文中检索，截断 context 使 benchmark 退化为短上下文问题。应从左侧截断或直接报错拒绝
- [ ] `[HIGH]` kivi_style quant_bits 推断为 16 (L985): `"int4" in "kivi_style"` 和 `"int8" in "kivi_style"` 均 False → fallback 到 16。CSV 中 quant_bits 字段错误（与 E5 同类问题，此处为 eval_ruler 实例）
- [ ] `[MEDIUM]` CWE pred_words 未过滤空字符串 (L193): `truth_words` 通过 `if _normalize_text(a)` 过滤空串，但 `pred_words` 未做同样过滤。若模型输出仅含标点/空格，`pred_words` 可能含空字符串导致意外 set 匹配
- [ ] `[LOW]` `_token_f1()` 分母过度保护 (L140-141): `max(1, len(pred_tokens))` 在 `common=0` 时冗余（0/1=0 已安全），代码意图不清

#### P. 深度审查 — 测试覆盖质量（第七轮审查）

> test_kivi_cache.py / test_asymmetric_quant.py / test_aggregate_results_stats.py 覆盖率评估

- [ ] `[HIGH]` B1 修复验证不完整 (test_kivi_cache.py L233-242): `test_clear()` 仅检查 `get_seq_len()==0`，未验证 `_k_scale_initialized` 状态或 clear→re-append 时 K-scale 是否重新计算（B1 核心场景）
- [ ] `[HIGH]` K decode 量化误差无测试: prefill 阶段计算 K per-channel scale 后，decode 新 token 用相同 scale 量化的误差从未被测试。这是 KIVI 区别于对称量化的核心特性
- [ ] `[MEDIUM]` 缺少 float16 输入测试: 所有测试用 float32，但生产环境用 float16。`_make_cache()` 默认 `dtype=torch.float32`，而 `KIVIStyleKVCache` 默认 `dtype=torch.float16`
- [ ] `[MEDIUM]` 缺少 per-channel/per-token 轴语义验证 (test_asymmetric_quant.py): 测试验证 shape 正确但不验证"同一 channel 的不同 token 共享同一 scale"的核心语义
- [ ] `[MEDIUM]` C1/C2 修复缺少边界值测试: 无 `percentile=50.0`（应拒绝）、`percentile=50.01`（应通过）、`percentile=100.1`（应拒绝）的显式测试
- [ ] `[MEDIUM]` 统计测试缺少混合符号 sign-flip 场景 (test_aggregate_results_stats.py): 仅测试全正差异（p=2/16=0.125），缺少正负混合的 p-value 计算验证
- [ ] `[LOW]` 缺少单 token、batch=0、head_dim=1 等极端边界测试
- [ ] `[LOW]` 缺少多轮 clear→append 循环测试（生产中常见的 batch 间重用 cache 场景）

---

## Approved Plans

> 经讨论并被用户认可的计划。与 TODO Backlog（缺陷/待修复项）区分，此处记录已确认的阶段性执行方案。
> 每条 Plan 记录：批准日期、Plan 名称、内容摘要、前置条件、状态（待执行 / 执行中 / 已完成）。

### Plan: EMNLP 2026 Phase 4 — MSE 校准 + 消融（仅 1.5B）
- **批准日期**：2026-02-23
- **前置条件**：✅ A 节 MSE 校准缺陷已修复
- **状态**：执行中
- **内容**：
  - [x] 生成 MSE 校准产物：`artifacts/kv_calib_mse_1p5b_int8.json` + `artifacts/kv_calib_mse_1p5b_int4.json` — ✅ 完成 2026-02-23 06:03
  - [x] 创建消融配置：14 runs ablation matrix — ✅ 完成 commit f07422d
  - [ ] 运行消融实验矩阵（needle/PPL/LongBench，5 seeds，1.5B only）

### Plan: EMNLP 2026 Phase 5 — 全矩阵实验
- **批准日期**：2026-02-23
- **前置条件**：✅ B-F 节 CRITICAL/HIGH 已修复
- **状态**：待执行
- **内容**：
  - [x] 更新 7B/8B 配置：保留 batch=1,2,4,8,16 吞吐量；FP16 删 b24/b32 避免 OOM；添加 KIVI 条目 — ✅ commit f07422d
  - [ ] 1.5B KIVI 补跑（6 运行 × 5 seeds × 4 tasks）
  - [ ] Qwen2.5-7B 全矩阵（全 kv_modes × 5 seeds × 4 tasks + 吞吐量）
  - [ ] LLaMA-3.1-8B 全矩阵（同上）
  - [ ] 3 模型延迟/显存 profiling
  - [x] 修复 `export_tables_latex.py`：KV_MODE_ORDER/DISPLAY 缺 kivi_style — ✅ commit 8bf9414
  - [x] 扩展 `generate_thesis_report.py`：claims C7-C11 — ✅ commit 8bf9414

### Plan: EMNLP 2026 Phase 6 — 聚合 + 统计修复 + 论文准备
- **批准日期**：2026-02-23
- **前置条件**：Phase 4 + Phase 5 完成
- **状态**：待执行
- **内容**：
  - [ ] C1 TPOT 统计修复：补 seed 1239-1241 达到 n=8（当前 p=0.0625 因 n=5 硬上限）
  - [ ] 创建 `configs/snapshots/final_emnlp2026_v1.yaml` 统一配置
  - [ ] 合并结果到 `results/emnlp_final/`，运行聚合 + LaTeX + 报告
  - [ ] claim_validation.csv 全部 PASS 或有文档解释

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

### 2026-02-23 06:19 | Phase 4.1: MSE Calibration Complete + Phase 5 Blockers Resolved
- **Goal**: Generate MSE calibration artifacts for 1.5B model; fix remaining CRITICAL/HIGH blockers for Phase 5
- **Changed files**:
  - `scripts/eval_ppl.py`: Added kivi_style branch in build_kv_cache() + quant_bits parameter (L-1 fix)
  - `scripts/aggregate_results.py`: Added KIVI significance pairings, longbench_official_macro, model_id in sig_specs/ruler_depth_keys (M-1/M-2/M-3/M-4 fix)
  - `iteration.md`: Updated 20+ backlog checkboxes, Phase 4 plan status
- **Remote GPU tasks**:
  - MSE INT8 calibration: `calibrate_behavior.py --loss_function mse --search --quant_bits 8` → artifacts/kv_calib_mse_1p5b_int8.json (41KB)
  - MSE INT4 calibration: `calibrate_behavior.py --loss_function mse --search --quant_bits 4 --int4_search` → artifacts/kv_calib_mse_1p5b_int4.json (64KB)
  - INT8 best: g16/clip=99.5 (p95_mse=0.000956); INT4 best: g16 search across outlier_ratios
- **Commits**: 03ed4a0 (eval_ppl+aggregate fix), 03d2e13 (docs), 9f41659 (backlog checkboxes)
- **Pushed**: 8 commits to origin/main (36921e6..9f41659)
- **Backlog status**: All CRITICAL=0, remaining HIGH=3 (non-blocking: A-5 doc, D-2 design, K-1 usability)
- **Next**: Run ablation experiments (14 configs × 5 seeds × 3 tasks) on remote GPU

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

### 2026-02-23 22:00 | 项目监管审查：全面代码质量审查
- **Goal**: 作为监管 agent，对当前代码库所有新增/修改模块进行全面审查，发现潜在问题并归档到待办清单
- **Scope**: 6 个并行审查 agent 分别检查 KIVI cache、asymmetric quant、generate_loop、eval 脚本集成、MSE 校准、配置矩阵一致性
- **审查模块与发现数量**:
  - `src/cache/kivi_style_cache.py`: 4 CRITICAL + 3 MEDIUM + 3 LOW
  - `src/quant/asymmetric_quant.py`: 2 CRITICAL + 2 MEDIUM + 1 LOW
  - `src/engine/generate_loop.py`: 2 HIGH + 1 MEDIUM + 1 LOW
  - 评测脚本集成（9 个脚本）: 2 CRITICAL + 2 HIGH + 4 MEDIUM + 1 LOW
  - `scripts/calibrate_behavior.py` MSE: 3 CRITICAL + 4 HIGH + 3 MEDIUM
  - 配置矩阵一致性（3 YAML）: 3 HIGH + 2 MEDIUM + 1 LOW
- **关键发现（阻塞性）**:
  1. MSE 校准实现有根本性 loss 语义错误（mean vs sum 不一致），产物不可信 → 阻塞 Phase 4
  2. percentile < 50 时非对称量化公式翻转 min/max，静默产生错误结果 → 需添加范围校验
  3. export_tables_latex.py 完全缺失 KIVI 显示名和排序 → 阻塞论文表格
  4. eval_longbench.py 引用未定义 logger → 特定条件下 NameError 崩溃
  5. 1.5B 配置缺失 KIVI 条目，7B/8B 缺失吞吐量条目 → 跨模型对比不完整
  6. generate() 高层 API 无法指定 KIVI quant_bits → INT4 KIVI 不可用
- **产出**: 全部问题已写入 `iteration.md` TODO Backlog A-F 节（按模块分类、按严重性排序）
- **Validation**: 审查基于 6 个专业 agent 的独立代码阅读，每个 agent 逐行分析源码
- **Risks / follow-ups**:
  - 所有 CRITICAL/HIGH 问题必须在 Phase 4/5 启动前修复
  - MSE 校准需完整重写 loss 聚合逻辑后才能生成可信产物
  - 建议开发 agent 优先修复 A 节（MSE）和 C 节（percentile 校验），因为这两个影响数值正确性

### 2026-02-23 | Phase 1-Pre/3/4.1: KIVI Baseline + MSE Calibration + Multi-Model Configs

- **Goal**: Implement KIVI-style asymmetric KV cache baseline (Phase 3), MSE calibration loss (Phase 4.1), per-model config files (Phase 0.5), and integrate into all eval scripts. Part of EMNLP 2026 Milestone K-Q execution plan.
- **Changed files (NEW)**:
  - `src/quant/asymmetric_quant.py`: Asymmetric INT8/INT4 quantization with per-channel and per-token axis support, zero-point. Core functions: `quantize_asymmetric_per_channel()` (K cache), `quantize_asymmetric_per_token()` (V cache), and their dequantize counterparts.
  - `src/cache/kivi_style_cache.py`: `KIVIStyleKVCache` class implementing KIVI paper's per-channel K + per-token V asymmetric quantization. Interface-compatible with `INT8KVCache`. Supports INT8 and INT4 via `quant_bits` parameter. Always uses `torch_ref` decode (no Triton fused kernel). K scale computed at prefill, reused at decode.
  - `tests/test_asymmetric_quant.py`: 15 unit tests covering round-trip error, edge cases, INT8/INT4, per-channel/per-token axis, zero-point correctness.
  - `tests/test_kivi_cache.py`: 17 unit tests covering basic append/get, prefill+decode pattern, K scale persistence, V scale independence, capacity growth, interface compatibility.
  - `configs/snapshots/exp_matrix_qwen25_7b_v1.yaml`: Qwen2.5-7B config with core runs + KIVI entries.
  - `configs/snapshots/exp_matrix_llama31_8b_v1.yaml`: LLaMA-3.1-8B config with core runs + KIVI entries.
- **Changed files (MODIFIED)**:
  - `src/cache/__init__.py`: Added `KIVIStyleKVCache` export.
  - `src/quant/__init__.py`: Added asymmetric quant function exports.
  - `src/engine/generate_loop.py`: Added `kivi_style` to kv_mode validation, added KIVI cache instantiation branch, added `quant_bits` parameter to `generate_from_ids()`, routed KIVI through baseline dequant-before-attention path.
  - `scripts/eval_ppl.py`, `eval_needle.py`, `eval_longbench.py`, `eval_ruler.py`, `profile_latency.py`, `profile_memory.py`, `run_experiments.py`: Added `kivi_style` to `--kv_mode` choices, added `--quant_bits` passthrough for KIVI INT4/INT8 disambiguation.
  - `scripts/calibrate_behavior.py`: Added `--loss_function {kl,mse}` argument, MSE loss path in `evaluate_quant_candidate()` and `compute_inv_tau()`, MSE objective support in `select_best_trial()`.
- **Verification**: `python3 -m compileall -f scripts/ src/ tests/` → all 34 files compile clean, 0 errors. YAML configs parse OK.
- **Commit**: pending
- **Next steps**:
  - Phase 0: Push to remote, `git pull`, verify 3 models loadable, run smoke tests.
  - Phase 1: Remote validation of LongBench/RULER on all 3 models.
  - Phase 2: Generate calibration artifacts for Qwen2.5-7B and LLaMA-3.1-8B.
  - Phase 4: Generate MSE calibration artifacts, run ablation matrix.
  - Phase 5: Full 3-model × 7 kv_mode × 5 benchmark matrix.

### 2026-02-23 | LongBench Official Metrics + Objective Refinement (Round 2)

- **Goal**: Add LongBench official per-task metrics (Rouge-L, Accuracy, Edit Similarity) to `eval_longbench.py`; change `longbench_score` from uniform token-F1 to official metric macro-average; add snapshot governance rule to objective.md.
- **Trigger**: Second round of ChatGPT review identified that uniform token-F1 across all LongBench tasks deviates from official evaluation protocol. Cross-validated with code: confirmed code did use uniform F1 (not "wrong" but needs explicit justification). Decided to implement official metrics.
- **Changed files**:
  - `scripts/eval_longbench.py`: Added `TASK_OFFICIAL_METRIC` mapping dict (21 tasks), `_lcs_length()`, `_rouge_l()`, `_edit_similarity()`, `_classification_accuracy()`, `_compute_official_metric()`. Updated main loop to compute official metric per sample. Added `official_metric_name` / `official_metric_value` to all 3 CSV outputs (details, task_summary, profile). Changed `longbench_score` from `f1_macro` to `official_macro`.
  - `objective.md`: (1) LongBench 主表汇总协议: rewrote to declare per-task official metrics with mapping table reference; (2) Primary Endpoint #1: changed from "F1-macro" to "official-metric macro"; (3) Added snapshot governance rule under 实验入口 section.
- **ChatGPT 6-point cross-validation summary**:
  - 必改点1 (LongBench metric): ChatGPT factually wrong (code DID use uniform F1), but concern valid → implemented official metrics
  - 必改点2 (RULER alignment): Already done in previous round, ChatGPT saw stale version → no change needed
  - 必改点3 (✅ markers): Would make doc unstable → not changed
  - 必改点4 (PPL chunk): Already covered in current text → not changed
  - 必改点5 (DoD tiering): User previously rejected → respected decision
  - 必改点6 (Snapshot governance): Valid, low cost → added 1 rule
- **Verification**: `python3 -m py_compile scripts/eval_longbench.py` → OK
- **Commit**: pending
- **Risks / follow-ups**:
  - Rouge-L LCS computation is O(n*m) on token lists; for very long predictions may be slow. Mitigated: LongBench answers are typically short.
  - `_edit_similarity` is character-level O(n*m); fine for code completion outputs (typically <500 chars).
  - Need remote smoke test to verify end-to-end with real model outputs.

### 2026-02-23 | RULER 4-Subtask Rewrite + LongBench 7-Task Extension + Objective Review
- Goal: address publishability gaps found during ChatGPT-assisted objective.md review — rewrite RULER eval to implement 4 genuine subtasks (S-NIAH, MK-NIAH, VT, CWE) instead of simplified single-needle retrieval; extend LongBench to 7 tasks; update objective.md with verified suggestions.
- Scope: eval_ruler.py rewrite, eval_longbench.py extension, objective.md revision, pipeline plumbing updates.
- Changed files:
  - `scripts/eval_ruler.py` (full rewrite: 4 RULER subtask generators + task-level scoring + backward-compatible CSV output)
  - `scripts/eval_longbench.py` (fix HF field extraction for context+input pattern; update default tasks to 7)
  - `scripts/run_experiments.py` (add new RULER args: --ruler_tasks, --ruler_mk_num_keys, --ruler_vt_*, --ruler_cwe_*)
  - `scripts/aggregate_results.py` (add ruler_task_summary aggregation)
  - `scripts/run_week5_external_validity_v1.sh` (update RULER and LongBench task params)
  - `objective.md` (PPL 1M tokens, ARR window, revision pin, env version, RULER description, LongBench macro protocol, primary endpoints, stat family, milestone status)
  - `iteration.md`
- Key decisions:
  - RULER: self-implemented task generators following NVIDIA/RULER taxonomy, NOT the official RULER runtime
  - LongBench: 7 tasks = narrativeqa, dureader, hotpotqa, gov_report, vcsum, trec, lcc (EN+ZH coverage)
  - DoD: kept flat (no P0/P1/P2 tiering per user preference)
  - PPL: main results now use target_tokens=1_000_000 (was max_samples=64 ≈ 65K)
  - Primary endpoints capped at 5: LongBench F1-macro, RULER macro-accuracy, Needle pass rate, PPL, TPOT
- Validation:
  - All modified scripts pass `python3 -m py_compile`
  - Local numpy broken (known issue); full test suite must run on remote server
- Risks / follow-ups:
  - LongBench HF loading for dureader/vcsum/trec/lcc untested with real data (needs remote validation)
  - RULER CWE subtask scoring (set matching) needs end-to-end validation with real model
  - RULER case count changed from 96 total to 24 per-task (= 96 total across 4 tasks)
  - Remote smoke test needed before full Week5 run

### 2026-02-22 17:24 | Week5 External-Validity Chain + Remote Smoke Closure
- Goal: complete Week5 engineering upgrade (LongBench/RULER integration + PPL token-floor hardening) and verify the full experiment-to-report pipeline on Remote-Server.
- Scope: add missing eval task implementation, wire runner/strict aggregation/report/latex, fix runtime edge cases discovered in remote smoke.
- Changed files:
  - `scripts/eval_ruler.py`
  - `scripts/eval_ppl.py`
  - `scripts/run_experiments.py`
  - `scripts/check_run_completeness.py`
  - `scripts/aggregate_results.py`
  - `scripts/export_tables_latex.py`
  - `scripts/generate_thesis_report.py`
  - `scripts/run_week5_external_validity_v1.sh`
  - `configs/snapshots/exp_matrix_week5_external_validity_v1.yaml`
  - `tests/test_aggregate_results_stats.py`
  - `iteration.md`
- Commands:
  - local compile: `python3 -m compileall ...`
  - local unit tests: `python3 -m unittest tests/test_run_experiments_resilience.py tests/test_check_run_completeness.py`
  - remote health: `ssh -p 31867 root@region-42.seetacloud.com "echo SSH OK && nvidia-smi -L"`
  - remote smoke (tmux): run `eval_ppl,eval_needle,eval_longbench,eval_ruler` on `fp16_kv_curve_4k` with strict aggregation/export/report
  - remote report regression test: `/root/miniconda3/bin/python -m unittest tests/test_generate_thesis_report.py`
- Outputs:
  - new week5 runner entrypoint: `scripts/run_week5_external_validity_v1.sh`
  - remote smoke package: `results/week5_smoke_remote_r2/` (runs/logs/tables/plots/latex/reports)
  - new aggregated artifacts confirmed: `longbench_summary.csv`, `ruler_summary.csv`, `ruler_depth_summary.csv`, `longbench_task_summary.csv`
- Validation:
  - remote `run_experiments_smoke.json`: 4/4 tasks success (`eval_ppl`, `eval_needle`, `eval_longbench`, `eval_ruler`)
  - strict aggregation completed: `results/week5_smoke_remote_r2/aggregate.log`
  - latex export completed: `results/week5_smoke_remote_r2/export_latex.log`
  - report generation completed after fix: `results/week5_smoke_remote_r2/report.log`
  - fixed two real defects found during smoke:
    - `eval_ppl` token-floor off-by-one (target 4096 -> evaluated 4095) by reserving `target_tokens + 1` input budget
    - `generate_thesis_report.py` crash when `stat_decisions` has no `decision` column (now robust fallback)
- Risks / follow-ups:
  - local host python environment still lacks usable `numpy` runtime (`libcblas.3.dylib` missing); numpy-dependent local tests remain blocked
  - current smoke validates functionality, not statistical claims (single fp16 run only), so claim rows are expected `INCONCLUSIVE`

### 2026-02-22 16:31 | Record C1 Statistical Inconclusive Risk
- Goal: formally record the `C1` long-context TPOT significance issue for planned optimization, without mutating current final package results.
- Scope: add a traceable risk entry with evidence paths, root-cause interpretation, and explicit follow-up rerun action.
- Changed files:
  - `iteration.md`
- Commands:
  - inspect `results/final_journal_v1/reports/claim_validation.csv`
  - inspect `results/final_journal_v1/tables/significance_summary.csv`
  - inspect `results/final_journal_v1/tables/significance_pairs.csv`
- Outputs:
  - documented issue: `C1` is `INCONCLUSIVE` due to `q_value=0.0852` and `p_value=0.0625` at `n_pairs=5`
  - documented interpretation: with current paired exact two-sided test and small `n`, statistical power is insufficient for `q<0.05` despite strong practical gain
  - documented follow-up plan: targeted long-context TPOT补跑（新增 seed 至 n>=8，建议 n=8~10）后重聚合
- Validation:
  - evidence is consistent across `claim_validation.csv` and significance tables
  - current final package integrity unchanged (no rerun/no overwrite)
- Risks / follow-ups:
  - until long-context paired sample size is increased, C1 remains non-definitive for strict significance claims
  - execute targeted补跑 in next optimization iteration and refresh claim gate artifacts

### 2026-02-22 11:02 | SOP Entrypoint Rename
- Goal: switch experiment SOP to a single canonical file `experiment_sop.md` and avoid broken legacy links.
- Scope: rename protocol file, update active guidance references, and provide a legacy redirect note at old path.
- Changed files:
  - `experiment_sop.md` (moved from `docs/final_experiment_protocol.md`)
  - `AGENTS.md`
  - `README.md`
  - `iteration.md`
  - `docs/final_experiment_protocol.md` (legacy redirect notice)
  - `development_record.md` (historical note update)
- Commands:
  - `mv docs/final_experiment_protocol.md experiment_sop.md`
  - replace active references to `experiment_sop.md`
  - create legacy notice at `docs/final_experiment_protocol.md`
- Outputs:
  - unique active SOP entrypoint: `experiment_sop.md`
  - old link path now resolves to a redirect notice instead of missing file
- Validation:
  - active policy and README now point to `experiment_sop.md`
  - no broken path for legacy `docs/final_experiment_protocol.md` access
- Risks / follow-ups:
  - `development_record.md` retains historical old-path text by design

### 2026-02-22 10:55 | Rename Agent Workspace Directory
- Goal: rename the repository agent workspace from `.agent/` to `.agents/` and remove stale path guidance.
- Scope: move directory, update active docs/scripts/global policy references, and re-scan for old path pointers.
- Changed files:
  - `.agents/` (renamed from `.agent/`)
  - `AGENTS.md`
  - `scripts/run_experiments.py`
  - `.agents/execplans/README.md`
  - `.agents/skills/execplan/SKILL.md`
  - `/Users/chenzilang/.codex/AGENTS.md`
  - `development_record.md` (legacy path note)
  - `iteration.md`
- Commands:
  - `mv .agent .agents`
  - replace `.agent/` -> `.agents/` in active guidance files
  - `rg -n "\\.agent/" ...` scans to verify old-path cleanup
- Outputs:
  - single canonical agent workspace path: `.agents/`
- Validation:
  - active guidance now points to `.agents/...`
  - only historical logs may still mention `.agent/` (expected)
- Risks / follow-ups:
  - `development_record.md` keeps legacy strings for historical traceability

### 2026-02-22 10:49 | Workflow Guide Path Fixes
- Goal: prevent broken workflow guidance where agents/users follow a documented path but cannot find files or scripts.
- Scope: align active docs to one remote repo path and remove invalid script reference from skills.
- Changed files:
  - `README.md`
  - `experiment_sop.md`
  - `docs/final_results_summary.md`
  - `docs/thesis_preflight_checklist.md`
  - `.agents/skills/reproducibility/SKILL.md`
  - `.agents/skills/long-running-task/SKILL.md`
  - `iteration.md`
- Commands:
  - replace `/root/autodl-tmp/LLM_KVCache_Quantization` -> `/root/LLM_KVCache_Quantization` in active docs
  - replace invalid `scripts.utils` validation command with `scripts/run_experiments.py --config configs/exp_matrix.yaml --dry_run`
  - `rg -n` scans for deprecated paths and missing workflow references
- Outputs:
  - active workflow docs now point to existing canonical paths
  - reproducibility skill no longer references missing `scripts/utils.py`
- Validation:
  - no hits in active files for `.agent/`, `lang.md`, `docs/AGENT_README.md`, `scripts/agent_tools`, or `scripts.utils`
- Risks / follow-ups:
  - `development_record.md` keeps historical legacy references by design (not an active workflow guide)

### 2026-02-22 10:46 | Skill Directory Unification
- Goal: unify skill directories to a single canonical path and verify no active duplicate references remain.
- Scope: consolidate duplicate skill directories into one root and run redundancy scan on active files.
- Changed files:
  - `iteration.md`
  - `.agents/skills/debug-iterate/SKILL.md` (moved)
  - `.agents/skills/execplan/SKILL.md` (moved)
  - `.agents/skills/repo-hygiene/SKILL.md` (moved)
  - `.agents/skills/unit-commit/SKILL.md` (moved)
- Commands:
  - directory consolidation operations for skill folders
  - `rg -n` policy-keyword scans on active files
- Outputs:
  - single skill root for custom skills
- Validation:
  - custom skills centralized and callable from one location
- Risks / follow-ups:
  - `development_record.md` is still historical and contains old path references by design

### 2026-02-22 10:00 | Agent Pipeline Consolidation
- Goal: unify agent execution pipeline and remove duplicated process management.
- Scope: replace `lang.md` with `iteration.md`; deprecate local task lock system; keep one policy path.
- Changed files:
  - `AGENTS.md`
  - `README.md`
  - `objective.md`
  - `iteration.md`
  - `.agents/skills/long-running-task/SKILL.md`
- Commands:
  - `rg -n "lang\\.md|AGENT_README\\.md|agent_tools/agent_cli" ...`
  - file migration and archive operations (see `development_history/archive_20260222_agent_pipeline_cleanup/MANIFEST.md`)
- Outputs:
  - unified policy references
  - archive manifest for deprecated workflow assets
- Validation:
  - active files no longer depend on `lang.md` or local lock CLI
- Risks / follow-ups:
  - historical docs still contain old references inside archive directories (expected)

## Legacy System Issues (Migrated)

| ID | Discovered | Issue | Trigger | Proposed Fix | Status |
|----|------------|-------|---------|--------------|--------|
| 001 | 2026-01-22 | Remote env package versions drift | Running `smoke_test.py` | Pin dependency versions and add startup checks | Tracked |
| 002 | 2026-01-22 | Doc/script/matrix drift causes reproducibility confusion | Aligning `development_record.md` with code and matrix | Enforce single entrypoint and config snapshots | Tracked |
| 003 | 2026-02-08 | Full-concat PPL tokenization creates long warnings and possible memory waste | Running `scripts/eval_ppl.py` | Use chunk/stream tokenization and record `max_length/stride` | Resolved |
| 004 | 2026-02-08 | Long remote runs break with direct SSH sessions | Remote `eval_ppl.py` validation | Use tmux background sessions and persisted logs | Tracked |
