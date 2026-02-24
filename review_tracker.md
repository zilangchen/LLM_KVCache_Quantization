# Code Review Tracker

> 379 issues | 321 fixed + 6 false_positive | 52 open (0 CRIT, 22 HIGH, 27 MED, 3 LOW)
> Phase Gate: **CLEAR** — 0 CRITICAL open
> Last updated: 2026-02-24

---

## Phase Blockers (CRITICAL open)

### CHK. 完整性检查 — `scripts/check_run_completeness.py`

- [x] **CHK-004** `[MED]` 不验证 CSV 内容完整性 (L80) — fixed 6f23824
- [x] **CHK-005** `[MED]` LongBench/RULER 任务级完整性无验证 (L16-23, L146-148) — fixed 6f23824
- [x] **CHK-006** `[MED]` dev agent 仍未确认 O 节 3 CRITICAL + T 节 1 CRITICAL — Phase Gate CLEAR, 所有 CRIT 已解决 -- fixed
- [x] **CHK-015** `[MED]` failure_type 域值枚举与 run_experiments.py _classify_failure() 不同步 (L94-108): 两处独立维护 failure_type 枚举，新增类型时易遗漏。 — D4, confidence: 84% — fixed 2f6cddb
- [x] **CHK-018** `[MED]` _split_csv/_read_json/_read_text 与 run_experiments.py 重复定义 (L27-51): 3 个工具函数在两个脚本中独立实现，修 bug 需改两处。 — D7, confidence: 100% — fixed 6f23824
- [x] **CHK-020** `[LOW]` 返回类型 Dict[str, Any] 无 TypedDict/dataclass 约束 (L168-181, L238-243): 字段名错误无法被静态检查捕获。 — D7, confidence: 80% — fixed 0056a3d
- [x] **CHK-021** `[MED]` 空 manifest + 存在 CSV 被判定为 "success" (check_run_completeness.py:153-156): manifest_status="" + manifest_failure="" 时 state="success"。manifest 损坏或手动拷贝 CSV 时虚假通过，可能导致信任不可靠数据。 — D2 RUN rotation, confidence: 85% -- fixed
- [x] **CHK-022** `[LOW]` _read_json OSError/PermissionError 无日志静默返回 None (check_run_completeness.py:54-55): 仅 JSONDecodeError 有 logger.warning，`except Exception: return None` 对 OSError（权限拒绝、IO 错误）无任何日志。manifest 读取因权限问题失败时与 manifest 不存在无法区分，导致所有任务按"无 manifest"路径分类。 — D2 full-scan, confidence: 83% — fixed 2f6cddb
- [x] **CHK-023** `[HIGH]` _detect_failure_type() canonical 枚举注释缺少 "timeout"，与 run_experiments.py 新增 timeout 路径失同步 (check_run_completeness.py:137-165 vs run_experiments.py:1452-1487): run_experiments.py 新增 timeout 处理分支，将 failure_type="timeout" 直接写入 manifest（L1457-1468），绕过 _classify_failure()。check_run_completeness.py 的 _detect_failure_type() 注释（L149-154）声称列出了 canonical failure_type 枚举集合（oom/interrupt/traceback/runtime_error/unknown），但未包含 "timeout"。实际运行中 manifest_failure="timeout" 会经 L163-164 的 fallback 分支透传输出，功能上不报错；但注释的权威性下降，未来新增 failure_type 时维护者参考注释做 exhaustiveness 检查会遗漏 "timeout"，CHK-015 所述不同步问题因此加剧。修复建议：同步更新 _detect_failure_type() 注释枚举，增加 "timeout" 条目。 — D4, confidence: 91% -- fixed

### EVL. 评测脚本 — `scripts/eval_*.py`

- [x] **EVL-023** `[LOW]` eval_longbench.py logger 定义位置：logger = logging.getLogger(__name__) 在 import 块中间（介于 traceback 和 from collections impor... -- fixed
- [x] **EVL-026** `[LOW]` eval_ruler.py summary row 聚合维度不一致 (L1008-1016): `overall_pass_rate` 基于 task-level macro average（4 tasks），而 `overall_f1` 和 `overall_contains` 基于 depth-level macro average（N depth ratios），同一 summary_row 内三个指标的聚合基底不同。主指标 `ruler_score` 不受影响（等于 task-level pass_rate） -- fixed

---

## Open Issues

### AGG. 聚合 — `scripts/aggregate_results.py`
- [ ] **AGG-002** `[HIGH]` RULER 聚合缺少子任务分拆 (aggregate_results.py
- [ ] **AGG-003** `[HIGH]` 多模型对比缺少分层表
- [x] **AGG-007** `[MED]` LongBench 聚合同时包含 3 个近义指标 (aggregate_results.py — fixed 081e3a9
- [x] **AGG-008** `[MED]` KIVI quant_bits 在 pairings 中未区分 INT8/INT4 (aggregate_results.py — fixed 2f6cddb
- [x] **AGG-009** `[MED]` kv_mode 显示顺序依赖默认排序 (aggregate_results.py — fixed 016b460
- [x] **AGG-012** `[LOW]` Bootstrap seed 基于 SHA256 hash 的独立性 — fixed 2f6cddb
- [x] **AGG-014** `[LOW]` Bootstrap CI 单样本情况返回 (value, value) 无警告 (L1059-1060) -- fixed
- [x] **AGG-015** `[LOW]` 精确枚举阈值 n=16 硬编码 (L1092-1107) — fixed 8f39875
- [x] **AGG-029** `[MED]` gain_pct_mean（跨 seed 配对差均值）vs gain_pct（聚合均值上的单点增益）定义不同 (generate_thesis_report.py:586 vs 356): significance_summary 用 gain_pct_mean，claim_validation 用 gain_pct。Jensen's inequality 下两者不等。同一 claim 在两个表中可能给出矛盾的 practical_pass。 — D4 EXP rotation, confidence: 88% -- fixed
- [x] **AGG-031** `[MED]` sign-flip 双尾检验 + 方向一致性检查 = 事实上 2 倍保守的单尾检验 (aggregate_results.py:1089): sign-flip p 值基于 |mean|（双尾），但 claim 验证要求 significant_q AND favors_challenger（单侧判据）。真正的单尾 p 应为 p_two/2。n=5 下可能导致本应显著的 claim 被误判。 — D1 EXP rotation, confidence: 80% — fixed ccd2cda
- [ ] **AGG-032** `[MED]` main() 函数 955 行含 7 次相同 read→numeric→seed→strict→agg→ci→save 模式 (aggregate_results.py:1539-2493): 无法单独测试、修改任一 benchmark 聚合逻辑需在巨大函数中导航。建议按 benchmark 拆分为独立函数。 — D7 EXP rotation, confidence: 98%
- [x] **AGG-034** `[HIGH]` logger 无 handler 配置，所有 logger.warning/info 被静默丢弃或仅走 lastResort (aggregate_results.py:59): logging.getLogger(__name__) 无 basicConfig()，AGG-020 的修复（加 logger.warning）、merge 膨胀 warning、duplicate warning 在实际运行中全部降级或失效。根因性问题。 — D2 incremental, confidence: 92% -- fixed
- [x] **AGG-035** `[HIGH]` merge key 五处退化到 ["kv_mode"] 无 warning，可致笛卡尔积 (aggregate_results.py:1513-1531): _mk/_nk/_pk/_lk/_rk fallback 时无日志。lat 有 model_id 但 mem 没有时 _has_mid=True → merge_keys=["model_id","kv_mode"] → _mk 退化到 ["kv_mode"]，多模型 lat 行产生笛卡尔积。2 模型时恰好不触发 >2x 警告。 — D2+D5 incremental, confidence: 85% -- fixed
- [x] **AGG-036** `[HIGH]` cnt 列含 inf 时 int(float('inf')) 抛 OverflowError 崩溃 (aggregate_results.py:185): pd.to_numeric(errors="coerce") 将 "inf" 字符串转为 np.inf，n>1 为 True 进入 int(n) 调用。NaN 安全（NaN>1=False）但 inf 不安全。建议 cnt.replace([np.inf,-np.inf], np.nan)。 — D5 incremental, confidence: 88% -- fixed
- [x] **AGG-037** `[MED]` _build_paired_metric_rows 静默丢弃 model_id 维度致跨模型混合 (aggregate_results.py:1188): key_cols 新增 "model_id" 但列不存在时被列表推导过滤，paired pivot 不按模型分组。跨模型数据混为同一 cell 被 aggfunc="mean" 平均。依赖未配置的 logger 报 warning。 — D2 incremental, confidence: 82% -- fixed
- [x] **AGG-038** `[MED]` _t_critical fallback 对 alpha!=0.05 静默返回 z=1.96 而非 t 值 (aggregate_results.py:42-43): scipy 不可用时 alpha=0.01,df=4 返回 1.96 而实际 t=4.604。当前唯一调用点用默认 alpha 不触发，但函数签名暴露 alpha 参数。建议加 warning 或 raise。 — D1+D2 incremental, confidence: 78% -- fixed
- [x] **AGG-039** `[MED]` scipy 路径 df=0 返回 NaN 而 fallback 返回 12.706，行为不一致 (aggregate_results.py:30-32 vs 48-49): 两个分支对 df=0 的语义不同。当前调用方有 max(1,...) 保护，但函数级契约不明确。 — D5 incremental, confidence: 70% -- fixed
- [x] **AGG-040** `[MED]` plt.errorbar NaN yerr 静默跳过 error bar 无视觉提示 (aggregate_results.py:855-859): n<=1 时 ci95_half=NaN 传给 matplotlib errorbar，数据点仍绘制但无 error bar，可能误导读者以为该点精确度极高。 — D4 incremental, confidence: 75% -- fixed
- [x] **AGG-041** `[MED]` 变量命名 _mk/_nk/_pk/_lk/_rk 可读性严重不足 + merge key 逻辑 5 处重复且 fallback 模式不一致 (aggregate_results.py:1513-1531): if-not 与 or 混用，增加出错风险。建议提取 _get_merge_keys helper。 — D7 incremental, confidence: 90% -- fixed
- [x] **AGG-042** `[MED]` 双重定义 _t_critical via try/except 隐式降级无 flag (aggregate_results.py:28-57): 两个同名函数在 try/except 中定义，运行时不会记录"降级到 fallback"。建议用 HAS_SCIPY 标志显式化。 — D7 incremental, confidence: 80% -- fixed
- [x] **AGG-043** `[LOW]` _t_critical df>120 返回 1.96 产生不连续跳变 (aggregate_results.py:50-51): df=120 查表值 1.980，df=121 直接返回 1.96，~1% CI 宽度跳变。建议用 _T_TABLE[120] 作为上界 fallback。 — D2 incremental, confidence: 70% -- fixed
- [x] **AGG-044** `[LOW]` _read_csvs relative_to bare except 无日志 (aggregate_results.py:131-134): AGG-020 修复了 CSV 读取 except 但 relative_to 仍 bare except 静默回退。与 AGG-020 修复精神不一致。 — D2 incremental, confidence: 68% -- fixed
- [x] **AGG-045** `[LOW]` fallback t-table 缺少来源和精度注释 (aggregate_results.py:34-40): 硬编码查表值无来源标注（scipy/R/Stata?），无精度说明，影响可审计性和复现性。 — D7 incremental, confidence: 75% -- fixed
- [x] **AGG-046** `[MED]` _read_json bare except 静默吞掉 JSON 损坏与 IO 错误 (aggregate_results.py:460-461): `except Exception: return {}` 对 JSONDecodeError、PermissionError、OSError 均静默返回空 dict，manifest 读取失败与 manifest 不存在无法区分。run_experiments.py 中对应函数 (RUN-026) 已修复分类 except + 日志，但 aggregate_results.py 仍是 bare except。影响 _strict_manifest_and_artifact_checks、_collect_execution_coverage 的准确性。 — D2 full-scan, confidence: 90% -- fixed
- [x] **AGG-048** `[MED]` _safe_t_crit(inf) 返回 0.0 导致 cnt=inf 时 CI 输出 0.0 而非 NaN，产生"零误差"伪像 (aggregate_results.py:227-233): `_safe_t_crit(inf)` 因 `not np.isfinite(inf)=True` 返回 0.0；`cnt.clip(lower=1)=inf`；`sem=std/sqrt(inf)=0.0`；`ci_half=0.0*0.0=0.0`；`.where(inf>1, np.nan)` 因 inf>1=True 保留 0.0。最终 ci95_half=0.0 在图表中呈现为"精确度极高"而非"数据无效"，误导读者。修复建议：在 _add_ci95_columns 开头添加 `cnt = cnt.replace([np.inf, -np.inf], np.nan)`，使 inf 经 `.where(cnt>1, np.nan)` 变为 NaN。 — D1, confidence: 82% — fixed 8f39875
- [x] **AGG-047** `[MED]` _same_commit_prefix 将 empty/unknown 视为兼容 (aggregate_results.py:465-471): `not a or not b → True`，`a=="unknown" → True`，与 run_experiments.py 中已修复的 RUN-018 语义相反。aggregate_results.py 的 strict 模式 commit 一致性检查对 "unknown" commit 全部静默通过，不同代码版本混入同一 run 无法被检测。 — D2 full-scan, confidence: 85% -- fixed

### CFG. 配置 — `configs/`
- [ ] **CFG-008** `[MED]` 7B/8B 长上下文仅 3 条 vs 1.5B 的 18 条
- [ ] **CFG-009** `[MED]` 1.5B 校准文件命名不一致 (kv_calib_kl_selected_v3_quick.json vs 7B/8B 的 kv_calib_kl_qwen25_7b_int8.json)
- [ ] **CFG-011** `[MED]` 消融 D 节缺少 dynamic scales 变体
- [ ] **CFG-012** `[MED]` 所有消融仅 seq_len=4096
- [ ] **CFG-013** `[MED]` 消融 C 节 (group_size sweep) 使用同一个 calib_file
- [ ] **CFG-022** `[MED]` 1.5B 吞吐量实验 b1-b16 使用 use_attn_temperature:true 而 b24-b32 使用 false，7B/8B 全部 false (exp_matrix.yaml:391-448): 同一模型 throughput 曲线混入 temperature 变量，跨模型对比也不对等。week4/week5 snapshot 同理。 — D1 TST+configs rotation, confidence: 95%
- [ ] **CFG-023** `[LOW]` 7B/8B int4_ours curve 使用 use_attn_temperature:true 但 int8_ours curve 使用 false (exp_matrix_qwen25_7b_v1.yaml:130-180 vs 275-312): INT8 vs INT4 对比中温度策略不同，是混淆变量。 — D1 TST+configs rotation, confidence: 92%
- [ ] **CFG-024** `[LOW]` runtime.quant_defaults use_attn_temperature:true 但 int8_ours curve 运行覆盖为 false (exp_matrix_qwen25_7b_v1.yaml:33): 默认值与实际不一致，新增运行可能意外使用 temperature。 — D1 TST+configs rotation, confidence: 85%
- [x] **CFG-025** `[LOW]` Frozen snapshot configs header comments 含过时 conventions — frozen snapshots 有意保留历史状态，修改会破坏其作为时间快照的意义 -- wont_fix
- [ ] **CFG-026** `[HIGH]` 7B/8B 配置引用的 calib_file 在 artifacts/ 中全部缺失 (exp_matrix_qwen25_7b_v1.yaml:32,132,150,...; exp_matrix_llama31_8b_v1.yaml:35,135,153,...): 4 个文件均不存在 — `artifacts/kv_calib_kl_qwen25_7b_int8.json`、`artifacts/kv_calib_kl_qwen25_7b_int4.json`、`artifacts/kv_calib_kl_llama31_8b_int8.json`、`artifacts/kv_calib_kl_llama31_8b_int4.json`。run_experiments.py L1147-1158 在非 dry_run 时检查 calib_file_path.exists()，缺失则 print error + return 2，7B/8B 所有 int8_ours/int4_ours 运行无法执行。与 objective.md §9（扩展模型实验为已批准目标）直接冲突。 — D4 configs deep review, confidence: 99%
- [x] **CFG-027** `[MED]` ablation 配置头部 conventions 注释 kv_mode 枚举含 `mixed` 但 SUPPORTED_KV_MODES 为 `int4_ours_mixed` (exp_matrix_ablation_1p5b_v1.yaml:19): 注释 `# - kv_mode: fp16 | int8_baseline | int8_ours | int4_baseline | int4_fused | mixed` 中的 `mixed` 与 run_experiments.py SUPPORTED_KV_MODES 中的实际枚举值 `int4_ours_mixed` 不匹配；ablation 矩阵实际上也未使用任何 mixed 模式条目，维护者参考注释添加 mixed 运行时会因 kv_mode 无效被 SUPPORTED_KV_MODES 校验拒绝。 — D4 configs deep review, confidence: 90% — fixed db0b23a
- [ ] **CFG-028** `[MED]` ablation A-2 的 calib_strategy: mse 字段在 generate_loop.py 中无效，MSE 消融结果不反映实际 MSE 校准行为 (exp_matrix_ablation_1p5b_v1.yaml:84): generate_loop.py 的 generate_from_ids() 无 calib_strategy 参数；run_experiments.py 将 calib_strategy 透传给子脚本（L1296），但 eval_ppl.py 等子脚本的 --calib_strategy 参数不影响引擎行为，引擎仅读 calib_file 的 scales。MSE ablation 运行时实际行为由 `artifacts/kv_calib_mse_1p5b_int8.json` 的内容决定，`calib_strategy=mse` 字段被静默忽略，与 RQ1 研究设计意图（对比三种校准方法）不符；若 MSE calib_file 未被正确生成，此运行退化为无 scales 的 int8_ours。 — D4 configs deep review, confidence: 85%
- [ ] **CFG-029** `[HIGH]` LLaMA-3.1-8B 配置 model_revision: null 导致实验无法 pin-revision 复现 (exp_matrix_llama31_8b_v1.yaml:22): run_experiments.py L1287 `if model_revision:` 对 null/None 跳过 `--model_revision` 参数传递，子脚本默认加载 HF Hub main 分支最新版。1.5B 有 pinned revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`，7B 有 `a09a35458c702b33eeacc393d103063234e8bc28`，唯独 LLaMA 为 null，与 objective.md §9"固定决策：revision pinned"直接冲突，存在跨时间/跨机器复现性风险。 — D4 configs deep review, confidence: 95%
- [x] **CFG-030** `[MED]` config_utils.py KV_MODE_ORDER 中 int4_fused 排在 int4_ours_mixed 之后，与 CLAUDE.md §9 标准顺序不一致 (scripts/config_utils.py:21-31): 实际顺序为 `[..., int4_baseline, int4_ours, int4_ours_mixed, int4_fused, kivi_style]`，而 CLAUDE.md §9 量化方法列表为 `fp16, int8_baseline, int8_ours, int4_baseline, int4_fused, int4_ours, int4_ours_mixed, kivi_style`（int4_fused 在 int4_ours 之前）。aggregate_results.py 和 export_tables_latex.py 均从 config_utils 导入 KV_MODE_ORDER 用于论文表格列排序，当前顺序将 int4_fused 置于 int4_ours_mixed 之后，与官方规范不符，可能导致表格展示顺序与论文叙述逻辑不一致。 — D4 configs deep review, confidence: 88% — fixed db0b23a

### ENG. 引擎模块 — `src/engine/`
- [x] **ENG-001** `[HIGH]` patch_model.py 移除 kv_heads 默认推理 (L100-108) — D1 深度验证 2026-02-24: 问题已修复为 false_positive 降级。`apply_int8_fused_patch`（L750-791）现行为：(1) 优先读 `model.config.num_key_value_heads`（L753，`getattr(cfg, "num_key_value_heads", cfg_q_heads)`），Qwen2.5-7B/LLaMA-3.1-8B 等 GQA 模型均在 config 中提供此字段，因此 L770-771 的 `_infer_heads_from_proj` 推断分支对这些模型不会触发；(2) 即便推断失败，L772-786 不再静默降级，改为 `logger.warning` 明确警告并设 `kv_heads = q_heads`；(3) 运行时在 `_resolve_attn_shape_meta`（L509-523）有第二道防护，若 q_heads % kv_heads != 0 则抛 ValueError。对于 Qwen2.5-7B（q=28, kv=4）和 LLaMA-3.1-8B（q=32, kv=8）均能从 config 正确读取，不会触发 fallback。原始 issue 描述的"移除默认推理"已被重构为"有日志的显式 fallback + 运行时校验"，实际风险已消除。降级为 false_positive。 — D1 重新验证, confidence: 92%
- [x] **ENG-003** `[HIGH]` decode 阶段 KIVI 走 dequant→re-quant 路径 (L635-678) — D1 深度验证 2026-02-24: 确认这是 KIVI 设计的固有特性，非实现 bug，降级为 false_positive。代码分析：`kivi_style_cache.py` L317-332，decode append 路径复用 prefill 时计算的 `k_scale/k_zp`（per-channel）直接重新量化新 token，公式 `q = round((k.float() - zp) / s).clamp(qmin, qmax)`，无需先 dequant 再 requant。V cache 走 per-token 量化，每个 decode token 独立计算自己的 scale/zp（L337-340），也不存在 dequant→requant 往返。generate_loop.py L728-734 中 `kivi_style` 的 decode 路径确实调用 `kv_cache.get_kv(i)` 把所有历史 KV dequant 出来传给模型，但这与 tracker 描述的 "L635-678" 无关（那是 fused 路径，KIVI 不走 fused）。真正的精度问题是 K 在 decode 阶段用 prefill scale 对越界值 clamp 而非重新计算 scale，这是 KIVI 论文的设计选择，已在 L319 注释 "ENG-007" 中明确标注。ENG-007 已 fixed。此 issue 行号引用错误且描述的问题（dequant→requant 往返）不成立。降级为 false_positive。 — D1 重新验证, confidence: 88%
- [x] **ENG-004** `[HIGH]` KIVI 模式静默忽略参数 (L412-486, L563) — D1 深度验证 2026-02-24: 确认与 ENG-014 完全重复且 ENG-014 已 fixed，降级为 false_positive。generate_loop.py L342-391 现行为：当 `kv_mode='kivi_style'` 且传入 `calib_file/use_attn_temperature/use_static_scales/adaptive_static_scales/adaptive_static_margin/adaptive_static_k/adaptive_static_v/allow_missing_calib` 时，逐字段检查并将忽略的参数名收集到 `ignored_fields` 列表（L361-378），然后通过 `warnings.warn(..., UserWarning)` 明确告知调用方（L379-383）；`decode_attn_impl` 若非 'torch_ref' 也会发出 warning 并强制覆盖（L385-391）。不存在静默忽略。该 issue 描述的问题在 ENG-014 修复时已一并解决。 — D1 重新验证, confidence: 95%
- [x] **ENG-005** `[MED]` generate_loop.py batch>1 填充检查移除 -- fixed
- [x] **ENG-006** `[MED]` KIVI kv_mode 未校验 quant_bits∈{4,8} (L294-310) -- fixed
- [x] **ENG-007** `[MED]` KIVI decode 路径 dequant→requant 精度累积（已知 D2 但补充细节） -- fixed
- [x] **ENG-008** `[MED]` Batch 约束重复校验 (L344-361) -- fixed
- [x] **ENG-009** `[MED]` kivi_style_cache.py V scale/zp 缓冲区 dtype 隐性转换 (L140-149, L240-241) -- fixed
- [x] **ENG-010** `[MED]` patch_model.py kv_heads 推断失败静默降级 (L473-477) -- fixed
- [x] **ENG-011** `[MED]` patch_model.py KIVI 缓存若被错误路由到 fused forward (L556-567) -- fixed
- [x] **ENG-012** `[LOW]` docstring 未说明 KIVI 模式行为 (L258-292) -- fixed
- [x] **ENG-013** `[LOW]` KIVI docstring 缺失 (L288-291) -- fixed
- [x] **ENG-014** `[LOW]` generate_loop.py kivi_style 接受但静默忽略 calib_file/use_attn_temperature/adaptive_static_scales 参数 (L412-485, L563-566): 已... -- fixed
- [x] **ENG-021** `[MED]` static_k_scale/v_scale 以 fp16 加载，小 scale 精度损失 (generate_loop.py:480-482): 低活跃度 head 的 scale 接近 fp16 subnormal 范围仅 ~3 位有效数字。inv_tau 正确用 float32。 — D1, confidence: 85% -- fixed
- [x] **ENG-023** `[MED]` fused 路径静默忽略 output_attentions=True (patch_model.py:778,808-818): fused path 返回 None 代替 attention weights，可解释性工具得到 None 无报错。 — D2+D4, confidence: 85% -- fixed
- [x] **ENG-025** `[MED]` _q_norm_hook 当 H==S 时布局检测歧义 (generate_loop.py:212-231): `output.shape[1]==H` 和 `shape[2]==H` 都为真时总进入第一分支。若实际 [B,S,H,D] 布局则 inv_tau 应用错误维度。 — D4, confidence: 82% -- fixed
- [x] **ENG-027** `[MED]` past_key_values=None 时静默跳过 KV 缓存填充 (generate_loop.py:614-625): decode 阶段使用空缓存，fused 模式 context_lens=0 可能产生 NaN。 — D2, confidence: 85% -- fixed
- [x] **ENG-029** `[MED]` torch_ref dequant 在 fp16 vs Triton 在 fp32，dump 对比精度差异 (patch_model.py:278-285): 两路径 ~1e-3 差异影响 max_abs_diff 诊断准确性。 — D1, confidence: 82% -- fixed
- [ ] **ENG-030** `[MED]` generate_from_ids 函数过长 535 行 (generate_loop.py:258-793): 8+ 职责耦合在一个函数中，难以单独测试和维护。 — D7, confidence: 95%
- [x] **ENG-032** `[LOW]` _seq_len 仅在 layer_id==0 时更新 — 设计决策注释已添加到 int8_cache.py 和 int4_cache.py -- fixed
- [x] **ENG-033** `[LOW]` INT8CacheWrapperContainer 每 decode step 重新构造 (generate_loop.py:668-671): 每步创建 num_layers 个 INT8CacheWrapper 对象，28-80 层模型生成 512 token 累计 14k-40k 临时对象。 — D4, confidence: 95% — fixed 2f6cddb
- [x] **ENG-034** `[LOW]` attention_mask decode 阶段 O(N^2) 内存分配 (generate_loop.py:724-732): fused path `del attention_mask` 但 generate_loop 仍每步分配增长。长序列累计 ~400MB 无用分配。 — D5, confidence: 88% — fixed 2f6cddb
- [x] **ENG-035** `[LOW]` except TypeError 过于宽泛可能吞掉内核内部错误 (patch_model.py:621-631,647-659): Triton kernel 内部 dtype/shape TypeError 被静默回退到无 debug_stats 调用。 — D7, confidence: 82% -- fixed
- [x] **ENG-036** `[MED]` patch_model.py _fused_forward_impl 改用 inspect.signature 检测 kernel 可选参数，但每次 decode step 均重新调用 inspect.signature()，无缓存 (patch_model.py:629-630): `_int8_sig_params = set(inspect.signature(decode_attn_int8).parameters)` 和 `_int4_sig_params = set(inspect.signature(decode_attn_int4).parameters)` 在 _fused_forward_impl 函数体内（每次 decode 调用），而非模块级缓存。kernel 签名在运行时不会改变，每 step 两次 inspect.signature() 调用产生不必要的开销（尤其 512+ token 生成时累计数千次调用）。这是从 try/except TypeError 改为 inspect.signature 时引入的性能回归，虽行为正确但接口探测应在 patch 时（apply_int8_fused_patch 初始化阶段）一次性缓存。 — D4, confidence: 88% -- fixed

### EXP. 导出/报告 — `scripts/export_*.py`
- [x] **EXP-002** `[MED]` LongBench 表缺少任务指标组成说明 (export_tables_latex.py — fixed 8d7f2df
- [x] **EXP-003** `[MED]` RULER 表仅显示整体 pass rate (export_tables_latex.py — fixed 8d7f2df
- [x] **EXP-004** `[MED]` 多模型表格缺少 per-model 分页 — fixed 8d7f2df
- [x] **EXP-005** `[MED]` C9 对指标名正确 (generate_thesis_report.py — metric="longbench_score" 已验证正确 -- false_positive
- [x] **EXP-006** `[MED]` generate_thesis_report.py C11 已有 target_model_ids=[7B, 8B] 过滤 (L196-199) -- fixed
- [x] **EXP-007** `[LOW]` KIVI 在 KV_MODE_ORDER 和 KV_MODE_DISPLAY 中已完整映射 (export_tables_latex.py -- false_positive
- [x] **EXP-008** `[LOW]` KIVI 吞吐量仅 INT8 — KIVI INT4 不在当前实验矩阵范围内（objective.md Non-goals） -- wont_fix

### KVC. KV Cache — `src/cache/`
- [x] **KVC-002** `[HIGH]` ~~KIVI INT4 未实现 bit-packing~~ **事实已变更**：bit-packing 已实现，pack_int4 offset +7→+8 已修复 (commit a60cbe6)。远端 decode 维度 bug 需远端验证。 -- fixed
- [x] **KVC-016** `[LOW]` INT4 vs INT8 行为切换逻辑正确 -- false_positive
- [x] **KVC-017** `[HIGH]` KIVIStyleKVCache._ensure_capacity grow 路径缺少溢出防护（kivi_style_cache.py:209-237）：grow 分支执行 `new_capacity = max(target_len, capacity*2)` 后再 `min(new_capacity, max_seq_len)` 截断，但**缺少** `if new_capacity < target_len: raise ValueError` 防护（INT8KVCache L179-182 和 INT4KVCache L232-235 均有此检查）。若 max_seq_len 小于 target_len，截断后 new_capacity < target_len，后续切片赋值 `[:, :, old_len:target_len, :]` 在 CUDA 层越界崩溃且错误信息无意义。触发条件：grow 分支（而非初始分配分支）中 max_seq_len 被超过时。 — D5, confidence: 88% -- fixed
- [x] **KVC-018** `[MED]` INT8KVCache/INT4KVCache.get_kv() 在 clear() 后调用时静默返回零长度 tensor（int8_cache.py:394-406, int4_cache.py:437-453）：clear() 将 _layer_seq_lens 清零但保留已分配 buffer（不为 None）。此后 get_kv() 的 `_k_cache[layer_id] is not None` 检查通过，seq_len=0，返回形状 [B,H,0,D] 的空 tensor，下游注意力计算不保证能处理 S=0。批次间复用 cache 实例（clear 不 release）时可触发。 — D5, confidence: 82% -- fixed

### PRF. 性能分析 — `scripts/profile_*.py`
- [x] **PRF-002** `[MED]` quant_bits CSV 推断 fallback 为 16 (eval_ppl.py -- fixed
- [x] **PRF-003** `[MED]` profile_latency.py run 间无显式 CUDA sync (profile_latency.py -- fixed
- [x] **PRF-004** `[MED]` kivi_style decode_attn_impl 参数被静默忽略 (profile_latency.py -- fixed
- [x] **PRF-005** `[MED]` profile_memory.py GPU 峰值来源判断逻辑 (L383-385) -- fixed
- [x] **PRF-009** `[LOW]` calib_file 对 kivi_style 静默无操作 (eval_ppl.py -- fixed
- [x] **PRF-010** `[LOW]` output 属性可靠性 (L348-352) — fixed c5b763c

### QNT. 量化模块 — `src/quant/`
- [x] **QNT-003** `[MED]` 全 eval 脚本 _resolve_quant_bits() 重复定义（6 处相同代码，违反 DRY） — canonical resolve_quant_bits() 已在 src/utils/repro.py 创建，6 处标 DEPRECATED -- fixed
- [x] **QNT-004** `[MED]` float16 输入精度损失 (L58-59) — 精度说明注释已添加 (int8_basic.py, int4_basic.py) -- fixed
- [x] **QNT-006** `[MED]` dequantize_symmetric_int8 多路径判断脆弱 — 三路径综合 docstring + inline 路径标签已添加 -- fixed
- [x] **QNT-007** `[MED]` 缺少 INT8 离群值测试 — fixed 12a62bf
- [x] **QNT-008** `[LOW]` dequantize 函数添加 int8 dtype + float scale 输入校验 (int8_basic.py, int4_basic.py) -- fixed
- [x] **QNT-009** `[LOW]` __init__.py.__all__ 不完整 — 14 exports docstring 已更新 -- fixed
- [x] **QNT-010** `[LOW]` 核心公式验证通过 -- false_positive

### RUN. 实验运行 — `scripts/run_experiments.py`
- [x] **RUN-009** `[MED]` 消融实验仅跑 PPL+Needle，缺少 LongBench — 消融设计决策：1.5B 仅 PPL+Needle 为主指标，已在 objective.md 确认 -- wont_fix
- [x] **RUN-010** `[LOW]` YAML 配置无 matrix 非空校验 (L725-794) — fixed 2f6cddb
- [x] **RUN-011** `[LOW]` append 模式 manifest 元数据被覆盖 (L252-265) — fixed 2f6cddb
- [x] **RUN-012** `[LOW]` append_history 未记录 kv_mode/quant_bits 变化 (L272-278) — fixed 2f6cddb
- [x] **RUN-013** `[LOW]` manifest history 仅保留最近 20 条 (L334) — fixed 2f6cddb
- [x] **RUN-014** `[LOW]` 消融 output dir 命名含双重 seed — run_name 含 seed 是设计意图（消融每 seed 独立 run），不影响功能 -- wont_fix
- [x] **RUN-017** `[LOW]` run_experiments.py RULER 截断 warning 仅 print 未写入 manifest: `_compute_ruler_truncation_warning()` 结果只打印到 stdout，不记录到 `run_manifest.json`。批量实验中 warning 混入大量日志难以追溯。 — D2 incremental, confidence: 82% -- fixed
- [x] **RUN-018** `[HIGH]` _same_commit_prefix 将 empty/unknown 视为兼容，允许跨 commit append 静默通过 (run_experiments.py:152-159): 空字符串和 "unknown" 均返回 True。非 git 环境或 git 损坏时 _get_git_commit 返回 "unknown"，append 校验全部通过，不同代码版本结果可混入同一 run_dir。 — D2+D5 RUN rotation, confidence: 88% -- fixed
- [x] **RUN-019** `[HIGH]` _collect_env_info 静默吞掉 torch/transformers import 错误 (run_experiments.py:84-104): except Exception 设置 "unavailable" 回退值无任何日志。环境根本性损坏（如 CUDA 驱动不匹配）被隐藏，子进程才崩溃导致难以诊断。 — D2 RUN rotation, confidence: 78% -- fixed
- [x] **RUN-020** `[HIGH]` load_config 对空 YAML 返回 None → 后续 .get() 崩溃 (run_experiments.py:819): yaml.safe_load 对空文件/仅注释文件返回 None，L835 config.get("project") 产生 AttributeError，报错信息完全不可理解。 — D5 RUN rotation, confidence: 95% -- fixed
- [x] **RUN-021** `[HIGH]` seq_len/gen_len 无类型和正值校验 (run_experiments.py:971-973): 从 YAML 直接取值无检查，0/负数/字符串可到达子脚本。batch 有 int()+or 1 保护但 seq_len/gen_len 没有。seq_len=0 导致空评估。 — D5 RUN rotation, confidence: 90% -- fixed
- [x] **RUN-022** `[HIGH]` subprocess.run 无 timeout，子任务挂起导致管线无限阻塞 (run_experiments.py:1344-1349): 无 timeout 参数。GPU 死锁、NFS 阻塞、推理无限循环时整个管线停滞，retry 机制无法恢复。特别影响 overnight batch 运行。 — D5 RUN rotation, confidence: 92% -- fixed
- [x] **RUN-023** `[HIGH]` use_attn_temperature 等布尔参数仅发 --no_ flag，True 时不发 flag 形成隐式耦合 (run_experiments.py:1185-1200): 仅在 False 时发 --no_use_attn_temperature，True 时不发任何 flag 依赖子脚本默认值。子脚本默认值变更时行为静默断裂。同理 use_static_scales/adaptive_static_k/v。 — D7 RUN rotation, confidence: 75% -- fixed
- [ ] **RUN-024** `[HIGH]` main() 函数 950 行，混合参数解析/配置校验/运行循环/命令构建/重试逻辑 (run_experiments.py:523-1473): 无法独立单元测试，添加新 benchmark 需在巨型函数中导航。至少应拆分命令构建(L1131-1279)和执行+重试(L1326-1470)。 — D7 RUN rotation, confidence: 95%
- [x] **RUN-025** `[MED]` _classify_failure OOM 检测用 substring "oom" in content 无词边界 (run_experiments.py:278-280): "room"/"bloom"/"zoom" 等词触发假阳性 OOM 分类。对比 check_run_completeness.py L55 正确使用 \boom\b 正则。 — D1 RUN rotation, confidence: 85% -- fixed
- [x] **RUN-026** `[MED]` _read_json bare except 返回 None 吞掉 JSON 损坏/权限错误 (run_experiments.py:107-117): JSONDecodeError 和 PermissionError 均返回 None，_init_manifest 静默覆盖损坏 manifest 销毁取证证据。无任何日志。 — D2 RUN rotation, confidence: 90% -- fixed
- [x] **RUN-027** `[MED]` unknown task name 静默 continue 且 exit 0 (run_experiments.py:1125-1129): TASK_TO_SCRIPT.get(task) 返回 None 时仅 print 到 stdout 后 continue。用户拼错任务名时该任务被跳过，run 以 exit 0 完成。 — D2 RUN rotation, confidence: 92% -- fixed
- [x] **RUN-028** `[MED]` _write_json replace() 失败时遗留 .tmp 文件且原文件不更新 (run_experiments.py:120-125): 跨文件系统 rename 或权限错误时异常传播，.tmp 文件残留。SIGKILL 后 .tmp 存在而 .json 不存在，manifest 丢失。 — D2+D5 RUN rotation, confidence: 70% -- fixed
- [x] **RUN-029** `[MED]` matrix 条目 run_name 缺失/空字符串被静默跳过 (run_experiments.py:959-963): if not run_name: continue 无 warning/error，YAML 配置拼写错误或忘写 run_name 的条目消失于无形。 — D2+D5 RUN rotation, confidence: 88% -- fixed
- [x] **RUN-030** `[MED]` append+retry 模式下日志追加交织导致 failure_type 误分类 (run_experiments.py:1337-1338): log_mode="a" 使旧 OOM/Traceback 信息保留，新失败的 classify_failure 可能检测到旧日志中的模式。 — D5 RUN rotation, confidence: 75% -- fixed
- [x] **RUN-031** `[MED]` safe_prompt_budget 可为负值但无 max(0,...) 防护 (run_experiments.py:251): peak_gen > base_total_budget 时 budget 为负，warning 消息中打印负值无物理意义。 — D1+D5 RUN rotation, confidence: 80% -- fixed
- [x] **RUN-032** `[MED]` resolve_quant_params 不做数值类型和范围校验 (run_experiments.py:460-484): YAML 中 clip_percentile="high" 或 group_size=-1 原样传给子脚本，模型加载后才崩溃浪费 GPU 时间。 — D1+D5 RUN rotation, confidence: 88% -- fixed
- [x] **RUN-033** `[MED]` _existing_result_git_commits bare except 静默跳过损坏 CSV (run_experiments.py:166-167): `except Exception: continue` 无日志，append 时某个 CSV 因损坏/权限无法读取时，该文件的 commit 信息被静默跳过。若所有 CSV 均损坏则返回空列表，_validate_append_commit 无法检测跨 commit 不一致，append 防护失效。 — D2 full-scan, confidence: 82% -- fixed
- [x] **RUN-034** `[HIGH]` --subprocess_timeout 新增参数隐式改变原有"无限等待"行为（breaking change for existing callers），默认 3600s 而非原 None (run_experiments.py:853-861, L1437): 原 subprocess.run 无 timeout（RUN-022 记录）；修复后默认 3600 秒。已有 overnight batch 运行可能在 1 小时后被强制终止（returncode=124, failure_type="timeout"）。影响范围：所有通过 shell 脚本调用 run_experiments.py 的自动化流程，若任务确实需要超过 1 小时（大模型 eval_longbench/eval_ruler 全量评测），必须显式传 --subprocess_timeout 0 或更大值。当前 AGENTS.md / experiment_sop.md 中无相关说明。向后兼容性破坏：调用方若依赖原无限等待语义将静默失败（任务被 timeout 终止但 run_experiments 退出 1）。 — D4, confidence: 88% -- fixed

### SMK. Smoke 测试 — `scripts/smoke_test.py`
- [x] **SMK-001** `[HIGH]` CUDA 不可用时 exit(0) → CI smoke test 假通过 (smoke_test.py:130-135): sys.exit(0) 在 CUDA 不可用时被调用，自动化管线检查 exit code 会认为 smoke test 通过。应 exit 非零或使用特殊 exit code 区分 "跳过" 与 "通过"。 — D2 RUN rotation, confidence: 95% -- fixed
- [x] **SMK-002** `[MED]` get_hardware_info bare except 返回 N/A 无 warning (smoke_test.py:53-61): torch.cuda.is_available()=True 后 get_device_name 失败时静默返回 N/A，设备异常被隐藏。 — D2 RUN rotation, confidence: 78% -- fixed
- [x] **SMK-003** `[MED]` 生成文本提取用 prompt 字符串长度偏移而非 token 偏移 (smoke_test.py:188-190): tokenizer decode 可能因规范化改变文本，len(prompt) 截断不精确。应用 token ID 切片后 decode。 — D1+D2+D5+D7 RUN rotation, confidence: 80% -- fixed
- [x] **SMK-004** `[MED]` 输出 JSON 无 encoding="utf-8"，C/POSIX locale 下非 ASCII 写入失败 (smoke_test.py:245-247): ensure_ascii=False 配合默认 locale 编码，Docker 容器默认 C locale 时中文生成结果触发 UnicodeEncodeError。 — D5 RUN rotation, confidence: 82% -- fixed
- [x] **SMK-005** `[MED]` --cpu-ok 新增参数改变 smoke_test.py CUDA 不可用时的 exit 语义，现有无参数调用方在 CPU-only 环境将从 exit(0) 变为 exit(1) (smoke_test.py:111-119, L145-155): 修复 SMK-001 的方式是引入 --cpu-ok flag：无此 flag 时 CUDA 不可用 exit(1)，有此 flag 时 exit(0)。这是接口行为 breaking change：所有现有 CI 脚本若无参数调用 `python scripts/smoke_test.py` 且运行于 CPU-only 环境，将从静默通过（旧 exit 0）变为失败（exit 1），直至显式加 --cpu-ok。smoke_test.py docstring（L13-14）仅列 --prompt/--max_new_tokens，未展示 --cpu-ok；AGENTS.md、start_agents.sh 等调用入口均未更新。向后兼容性影响：全部 CPU-only CI/CD 对该脚本的无参数调用。 — D4, confidence: 85% -- fixed

### TST. 测试覆盖 — `tests/`
- [ ] **TST-003** `[HIGH]` calibrate_behavior.py 完全无单元测试
- [ ] **TST-004** `[HIGH]` KIVI + asymmetric_quant 端到端集成测试缺失
- [ ] **TST-005** `[HIGH]` B1 修复验证不完整
- [ ] **TST-006** `[HIGH]` K decode 量化误差无测试
- [x] **TST-007** `[MED]` per-channel K 和 per-token V axis 独立性验证缺失 — fixed 9bc6414
- [x] **TST-008** `[MED]` Bootstrap CI n=1 和 n=2 边界测试缺失 — fixed 3c1b23c
- [x] **TST-009** `[MED]` Permutation test NaN 处理测试缺失 — fixed 3c1b23c
- [x] **TST-010** `[MED]` BH-FDR 单调性验证缺失 — fixed 3c1b23c
- [ ] **TST-011** `[MED]` eval_longbench.py / eval_ruler.py 完全无单元测试
- [x] **TST-012** `[MED]` 缺少 float16 输入测试 — fixed 9bc6414
- [x] **TST-013** `[MED]` 缺少 per-channel/per-token 轴语义验证 — fixed 9bc6414
- [x] **TST-014** `[MED]` C1/C2 修复缺少边界值测试 — fixed 9bc6414
- [x] **TST-015** `[MED]` 统计测试缺少混合符号 sign-flip 场景 — fixed 3c1b23c
- [x] **TST-016** `[LOW]` INT4 vs INT8 误差比例测试缺失 — fixed 9bc6414
- [x] **TST-017** `[LOW]` 缺少单 token、batch=0、head_dim=1 等极端边界测试 — fixed 9bc6414
- [x] **TST-018** `[LOW]` 缺少多轮 clear→append 循环测试（生产中常见的 batch 间重用 cache 场景） — fixed 9bc6414
- [x] **TST-019** `[HIGH]` review_tool.py 零测试覆盖 — 无 `tests/test_review_tool.py` (scripts/review_tool.py): 5 个子命令、2 个正则、文件写入逻辑均无自动化测试，任何重构无安全网 — gap_score: 9/10, confidence: 100% — fixed d045f08
- [ ] **TST-020** `[HIGH]` _decode_attn_int8_torch_ref 无独立单元测试 (patch_model.py:215-300): 300 行核心参考实现（含 GQA repeat_interleave、group-wise dequant、fp32 softmax），tests/ 中无直接测试。test_triton_kernel.py 有独立实现但从未对比 patch_model 版本。 — D6, confidence: 95%
- [ ] **TST-021** `[HIGH]` _apply_rope / _rotate_half 无单元测试 (patch_model.py:166-212): RoPE 是 fused decode 关键组件，支持 partial rotary 和多种 cos/sin 形状归一化。错误的 RoPE 导致 decode 注意力完全错误。 — D6, confidence: 95%
- [ ] **TST-022** `[HIGH]` INT8CacheWrapperContainer / INT8CacheWrapper 无测试 (patch_model.py:65-164): HF Cache 适配层含 get_seq_length、get_mask_sizes、update 等，直接影响 attention mask 尺寸计算。off-by-one 错误无法检测。 — D6, confidence: 95%
- [ ] **TST-023** `[MED]` _register_prefill_temperature_hooks 无测试 (generate_loop.py:161-255): 两种路径（q_norm hook vs q_proj hook）+ seq_len<=1 guard + 布局检测逻辑均无测试验证。 — D6, confidence: 90%
- [ ] **TST-024** `[MED]` _cache_stats_from_past_key_values 无测试 (generate_loop.py:44-99): 3 条路径（新 API/legacy tuple/to_legacy_cache 转换）无验证。 — D6, confidence: 90%
- [ ] **TST-025** `[MED]` _to_dynamic_cache_safely 无测试 (generate_loop.py:102-124): fallback 链（from_legacy_cache → ddp_cache_data → RuntimeError）无覆盖。 — D6, confidence: 90%
- [ ] **TST-026** `[MED]` apply_int8_fused_patch monkey-patch 逻辑无测试 (patch_model.py:715-835): forward_proxy cache 类型检测、_filter_kwargs、is_fused 判定等核心调度逻辑零测试。 — D6, confidence: 95%
- [ ] **TST-027** `[MED]` _get_rope_cos_sin 多 fallback 路径无测试 (patch_model.py:398-447): 5 种 fallback 全靠 try-except 消音，无测试验证正确路径被选中。 — D6, confidence: 85%
- [ ] **TST-028** `[MED]` _resolve_attn_shape_meta 头数推断无测试 (patch_model.py:467-502): 6 种 fallback 推断 q_heads/kv_heads/head_dim，错误推断导致 fused attention 输出形状错误。 — D6, confidence: 90%
- [ ] **TST-029** `[MED]` _materialize_int4_cache_as_int8 无测试 (patch_model.py:42-62): bit_packed vs unpacked 两条路径、形状 mismatch 校验无独立测试。 — D6, confidence: 85%
- [x] **TST-030** `[HIGH]` check_run_completeness.py 关键状态路径未测试: _check_task_state() 返回 8 种状态中 task_artifacts_missing、running、mixed_csv_non_success、missing 4 种无直接测试用例。当前仅覆盖 success、oom、csv_invalid、traceback 路径。 — D6 CHK rotation, confidence: 95% — fixed 7b6739c
- [x] **TST-031** `[HIGH]` eval_longbench/eval_ruler 工件检测完全无测试 (check_run_completeness.py:85-90): `_has_task_level_artifacts()` 中 longbench 检查 task_summary CSV、ruler 需同时检查 task_summary + depth_summary，两条分支零测试。 — D6 CHK rotation, confidence: 100% — fixed 7b6739c
- [x] **TST-032** `[MED]` check_run_completeness.py 8 个工具函数无独立单元测试: _split_csv, _read_json, _read_text, _is_oom_from_log, _is_traceback_from_log, _csv_has_rows, _has_task_level_artifacts, _expected_run_ids 均无单元测试，仅通过集成测试间接覆盖。 — D6 CHK rotation, confidence: 90% — fixed d045f08
- [x] **TST-033** `[MED]` check_run_completeness.py 参数组合和错误路径测试不足: allow_oom_completion=False 影响、runs_dir 不存在 exit(2)、logs_dir=None 完整路径、allow_stress_unexpected_failures 标志均无测试。 — D6 CHK rotation, confidence: 88% — fixed 7b6739c
- [x] **TST-034** `[HIGH]` export_tables_latex.py 零测试覆盖: 510 行代码、8 个 export 函数、2 个 helper 函数，tests/ 下无任何对应测试文件。_read_csv bare except、_pivot_metric 多模型平均、LaTeX 特殊字符转义等问题均无回归防护。 — D6 EXP rotation, confidence: 98% — fixed 54f282f
- [x] **TST-035** `[HIGH]` aggregate_results.py 统计函数测试覆盖不足: `_stable_random_seed`、`_cohens_dz`、`_relative_gain_table`、`_build_paired_metric_rows`、`_paired_signflip_pvalue` 等核心统计函数缺少针对性单元测试。现有 test_aggregate_results_stats.py 仅覆盖部分路径。 — D6 EXP rotation, confidence: 92% — fixed 12a62bf
- [ ] **TST-036** `[HIGH]` aggregate_results.py main() 管线无端到端测试: main() 函数 955 行，串联 7+ 子流程（read→CI→paired→claims→latex），无任何 e2e 测试验证从 CSV 输入到最终 tables/plots 产出的完整路径。配置变更可能静默破坏输出。 — D6 EXP rotation, confidence: 95%
- [x] **TST-037** `[HIGH]` smoke_test.py 零测试覆盖: 254 行代码含 get_git_commit、get_hardware_info、main() 生成逻辑、结果保存等关键路径，tests/ 下无对应测试文件。CUDA 不可用 exit(0) 路径特别需要回归测试。 — D6 RUN rotation, confidence: 98% — fixed 12a62bf
- [x] **TST-038** `[HIGH]` review_tool.py 零测试覆盖: 331 行代码含 parse_tracker（核心正则解析器）、cmd_add（文件写入）、cmd_phase_gate（CI gate 判定）、_update_summary 等 8 个函数，全无测试。正则匹配和字符串插入逻辑属高风险易错代码。 — D6 RUN rotation, confidence: 98% — fixed d045f08
- [x] **TST-039** `[HIGH]` run_experiments.py resolve_quant/calib_params + _validate_append_commit 无测试: 量化参数三级 fallback 解析逻辑和 append 模式 git commit/env_hash 一致性校验均为实验正确性核心守卫，当前 test_run_experiments_resilience.py 16 个用例未覆盖。 — D6 RUN rotation, confidence: 92% — fixed 7b6739c
- [x] **TST-040** `[MED]` run_experiments.py _classify_failure 仅测试 2/5 分类路径: 已测试 returncode=73→oom 和 log 含 Traceback→traceback。未测试 returncode=130→interrupt、log 含 "cuda out of memory"→oom、以及 runtime_error/unknown 兜底路径。 — D6 RUN rotation, confidence: 93% — fixed d045f08
- [x] **TST-041** `[HIGH]` _t_critical() 函数无单元测试 — TestTCritical class 已在 test_aggregate_results_stats.py 中添加（8 个测试用例覆盖 df=0/负数/1/120/1000、插值、有限性、alpha 默认值） -- fixed
- [x] **TST-042** `[HIGH]` _add_ci95_columns n<=1→NaN 行为变更无回归测试 — TestAddCI95Columns class 已在 test_aggregate_results_stats.py 中添加（6 个测试用例覆盖 count=0/1/2/5、缺列、空 DataFrame） -- fixed
- [x] **TST-043** `[HIGH]` Phipson-Smyth +1 修正无专门验证测试 — TestPhipsonSmythCorrection class 已在 test_aggregate_results_stats.py 中添加（3 个测试：corrected vs uncorrected 对比、lower bound >0、MC 路径），并更新了 test_exact_signflip_pvalue_known_case/mixed_signs 期望值使用修正公式 -- fixed
- [ ] **TST-044** `[MED]` _main_claims_32k_table 多模型 merge 路径无场景测试: 新增动态 merge_keys 逻辑含 5 处 fallback 到 ["kv_mode"]，无测试覆盖有/无 model_id、混合场景。 — D6 incremental, confidence: 90%
- [x] **TST-045** `[MED]` Triton kernel test randint(-127,127) 上界排他性，永远不生成值 127 (test_triton_kernel.py:88-89,123-124,187-200,269-270): torch.randint 上界排他，实际范围 [-127,126]，而源码 .clamp(-127,127) 可产生 127。修复: 改为 randint(-127,128)。 — D1 TST+configs rotation, confidence: 98% -- fixed
- [x] **TST-046** `[MED]` Long-context test 参考实现使用 fp16 dequant 而主参考用 fp32 (test_triton_kernel.py:229-233): test_long_context_gqa_correctness 参考 k_dequant 在 fp16 精度，而 _torch_ref_decode(L61-62) 使用 fp32。atol=3e-2 宽容差部分源于此精度不一致。 — D1 TST+configs rotation, confidence: 95% — fixed 12a62bf
- [x] **TST-047** `[LOW]` INT4 cache test 添加量化误差上界断言 (err < 0.5) + pack_unpack 范围扩展至 [-8,8) -- fixed
- [x] **TST-048** `[LOW]` INT8 容差 0.1 添加理论上界注释（≈absmax/254≈0.012，0.1 为 ~8× 防抖） -- fixed
- [x] **TST-049** `[LOW]` probability_of_superiority >= 0.99 断言对 n=3 样本过拟合 — 已修改为 >= 0.66（majority criterion），commit c67038c -- fixed
- [x] **TST-050** `[LOW]` 测试 magic numbers 添加理论上界来源注释 (test_int8_cache.py, test_kivi_cache.py) -- fixed
- [x] **TST-051** `[LOW]` test_triton_kernel.py 使用 sys.path.append 而非 insert(0) (L9): 不一致 — D4 TST+configs rotation, confidence: 75% — fixed 0056a3d
- [x] **TST-052** `[LOW]` test_triton_kernel.py except ImportError 而其他文件用 except Exception (L11-16): 模式不统一 — D4 TST+configs rotation, confidence: 70% — fixed 0056a3d
- [x] **TST-053** `[HIGH]` config_utils.load_config 新增异常路径无测试 (scripts/config_utils.py:17-28): 未提交变更新增空文件→ValueError 和非 dict 顶层→ValueError 两个防御分支，无对应测试。load_config 是所有 run_experiments/eval/profile 脚本的共享入口，此分支保护实验管线不在 model.get() 崩溃。需要：test_load_config_empty_file_raises、test_load_config_non_dict_raises、test_load_config_valid_returns_dict。 — gap_score: 8/10, confidence: 95% — fixed d045f08
- [x] **TST-054** `[HIGH]` run_experiments.py _same_commit_prefix 语义反转无回归测试 (scripts/run_experiments.py:169-183): 未提交变更将 empty/unknown 从返回 True（兼容）改为返回 False（不兼容）。这是 RUN-018 修复，行为完全反转。test_run_experiments_resilience.py 中无任何 _same_commit_prefix 测试。若回滚则跨 commit append 校验静默失效。需要：test_same_commit_prefix_empty_is_incompatible、test_same_commit_prefix_unknown_is_incompatible、test_same_commit_prefix_matching_8chars。 — gap_score: 8/10, confidence: 93% — fixed d045f08
- [x] **TST-055** `[HIGH]` run_experiments.py resolve_quant_params 新增数值校验无测试 (scripts/run_experiments.py:506-527): 未提交变更新增 clip_percentile 范围 (0,100] 和 group_size 正整数校验，共 4 个 ValueError 路径，均无测试。TST-039 记录了该函数整体无测试，此次修复增加了高优先级校验逻辑但仍无回归防护。需要：clip_percentile 字符串输入、负值、0 值、group_size 浮点/负数/零 各路径。 — gap_score: 8/10, confidence: 95% — fixed d045f08
- [ ] **TST-056** `[MED]` run_experiments.py seq_len/gen_len 校验逻辑无测试 (scripts/run_experiments.py:1042-1056): 未提交变更新增 seq_len/gen_len 类型和正值校验（非 int 返回 2，<=0 返回 2），校验代码在 main() 内部，当前测试文件仅通过 subprocess 测试集成路径，无法直接单元测试。但 _compute_ruler_truncation_warning 的测试已直接传 seq_len/gen_len，表明可提取可测试 helper。影响：非法配置的 YAML 值将在早期拦截而非 GPU 加载后崩溃。 — gap_score: 6/10, confidence: 85%
- [x] **TST-057** `[MED]` aggregate_results.py _safe_t_crit inf 防护无测试 (scripts/aggregate_results.py:227-230): 未提交变更将 lambda 替换为命名的 _safe_t_crit 函数，新增 not np.isfinite(n) 检查防止 int(inf) OverflowError（AGG-036 修复）。现有 TestAddCI95Columns 仅测试 count=0/1/2/5 正常值，未测试 count=inf 和 count=NaN 的 safe guard 路径。若守护逻辑被回滚，AGG-036 重现。 — gap_score: 6/10, confidence: 88% — fixed d045f08
- [ ] **TST-058** `[MED]` run_experiments.py _write_json 原子写入 tmp 清理逻辑无测试 (scripts/run_experiments.py:130-146): 未提交变更新增 try/except 在 replace() 失败时删除孤立 .tmp 文件（RUN-028 修复）。写入失败场景（磁盘满、跨文件系统）无法在普通测试中复现，但 tmp_path 存在且 replace 抛异常时 unlink 被调用的逻辑路径可用 mock 验证。当前零测试。 — gap_score: 5/10, confidence: 82%
- [x] **TST-059** `[HIGH]` test_run_experiments_resilience.py 中已关闭的 TST-040/054/055 对应测试在文件中无法确认存在 (tests/test_run_experiments_resilience.py): TST-040（_classify_failure 5分类路径）、TST-054（_same_commit_prefix empty/unknown→False）、TST-055（resolve_quant_params 非法输入→ValueError）均标记为 fixed (d045f08)，但当前文件只有 2 个 _classify_failure 用例（returncode=73→oom、Traceback→traceback），无 _same_commit_prefix 测试，无 resolve_quant_params 测试。_same_commit_prefix 是防止跨 commit 数据混入的关键门控，行为语义反转若无回归测试极难被发现。需确认：这些测试是否在其他文件；若不存在则需补写 interrupt/runtime_error/unknown 分类路径、_same_commit_prefix 边界值（empty/unknown/matching）、resolve_quant_params 四条 ValueError 路径。 — gap_score: 9/10, confidence: 95% — false_positive: tests exist in test_run_experiments.py (d045f08), not in resilience file
- [x] **TST-060** `[HIGH]` _cohens_dz 无单元测试且直接影响 claim 验证结论 (scripts/aggregate_results.py): _cohens_dz 计算公式 d_z = mean(diffs) / std(diffs, ddof=1) 是 probability_of_superiority = norm.cdf(d_z / sqrt(2)) 的基础，若 ddof 错误在 n=3 下系统性高估约 23%，可导致 claim 误判为实践意义显著。当前 test_aggregate_results_stats.py 无任何该函数的独立测试。需要：已知值精确比较（mean=1.0, std=1.0 → d_z=1.0）、单样本 std=0 防护测试、全零 diffs → d_z=0.0。 — gap_score: 7/10, confidence: 88% — false_positive: already covered by TST-035 in test_aggregate_results_stats.py (8 tests)
- [ ] **TST-061** `[MED]` test_long_context_gqa_correctness 被环境变量静默跳过且参考实现精度与主参考不一致 (tests/test_triton_kernel.py:172-257): 该测试需 RUN_TRITON_LONG_TEST=1 才运行，常规 CI 永远跳过，32k 序列数值稳定性从未被自动验证。同时 L232-236 的内联参考使用 fp16 dequant，而 _torch_ref_decode 使用 fp32，atol=3e-2 宽容差部分源于此精度差距。建议：添加不依赖环境变量的轻量长序列烟雾测试（seq_len=4096, H=1, kv_heads=1）；统一参考实现精度后再分析是否需要收紧容差。 — gap_score: 7/10, confidence: 90%
- [x] **TST-062** `[MED]` test_check_run_completeness.py 缺少 task_artifacts_missing / running / missing 三种状态的测试场景 (tests/test_check_run_completeness.py): 5个测试全部为 subprocess 集成测试，缺少：(1) task_artifacts_missing：eval_longbench manifest 为 success 但 longbench_task_summary_*.csv 不存在；(2) running：manifest 显示 status=running；(3) missing：run 目录存在但无 manifest 文件。三种状态在生产中均有触发路径，eval_longbench/eval_ruler 部分失败时 task_artifacts_missing 尤为常见，且 _has_task_level_artifacts() 的两条分支（longbench/ruler）均无覆盖（TST-031 仍 open）。 — gap_score: 6/10, confidence: 85% — fixed 7b6739c
- [x] **TST-063** `[MED]` _stable_random_seed 无测试，影响统计推断可复现性 (scripts/aggregate_results.py): _stable_random_seed(run_name, metric_name) 基于 SHA256 hash 生成确定性 seed，是 bootstrap CI 和 sign-flip permutation 可复现的基础（AGG-012 修复相关）。当前无任何测试。需验证：相同输入产生相同 seed（确定性）；不同输入产生不同 seed（冲突抵抗）；seed 在 numpy 合法范围 [0, 2^31) 内；签名变更时 CI 立即报警。若 hash 实现被无声修改，所有历史实验统计结论不可复现但 CI 无警报。 — gap_score: 6/10, confidence: 85% — false_positive: already covered by TST-035 in test_aggregate_results_stats.py (7 tests)
- [ ] **TST-064** `[MED]` INT4KVCache bit_packed=False 模式完全无测试 (tests/test_int4_cache.py): 当前所有 INT4 测试均使用 bit_packed=True，bit_packed=False 路径（不进行 nibble 压缩，直接以 int8 存储 INT4 值）零测试。若该路径 get_kv() 解码逻辑有 bug，测试集完全无法检测。需要：bit_packed=False 的 roundtrip 误差测试、append+get_kv 形状测试、clear→re-append 无污染测试。 — gap_score: 6/10, confidence: 82%
- [ ] **TST-065** `[LOW]` KVC-017 grow 路径越界防护无专用回归测试 (tests/test_kivi_cache.py): KVC-017 修复在 kivi_style_cache.py grow 分支新增 `if new_capacity < target_len: raise ValueError`。现有 test_max_seq_len_enforced 只测直接超限（首次 append 11 tokens, max_seq_len=10），未测 grow 路径中的越界：先 append 少量 token 触发 capacity grow，再 append 使总长超 max_seq_len 且 grow 截断后 new_capacity < target_len 的复合场景。若 fix 回滚则 CUDA 层越界崩溃但 CI 无感知。 — gap_score: 4/10, confidence: 82%

### RVW. 审查工具与配置 — `scripts/review_tool.py`, `.claude/agents/review-*.md`
- [x] **RVW-013** `[LOW]` Resolved KVC-003 前提失效: KVC-003 前提已变更，bit-packing 已实现且 pack offset 已修复 (commit a60cbe6)。论文描述无需注明"无 bit-packing" -- fixed

### QUA. 代码质量增量 — D7 全项目审查 2026-02-24

- [x] **QUA-001** `[HIGH]` `get_git_commit()` 在 9 个脚本中重复定义，无规范化入口 (scripts/eval_ruler.py:607, profile_memory.py:45, profile_latency.py:40, eval_ppl.py:67, smoke_test.py:38, eval_needle.py:39, eval_longbench.py:69, profile_baseline.py:37, collect_env.py:20): 与已规范化的 `get_hardware_info()` (`src/utils/repro.py:42`) 形成对比——后者有标准实现，前者 9 份几乎相同副本。任何修改（增加 `cwd` 参数、修改截断长度）需要改 9 处。建议将 `get_git_commit()` 加入 `src/utils/repro.py` 并替换各脚本的本地副本。 — D7 全项目, confidence: 98% -- fixed

- [x] **QUA-002** `[HIGH]` `run_experiments.py` 完全缺少 `import logging`，全部诊断输出用裸 `print()` (scripts/run_experiments.py:1-20, L92, L103, L121, L125, L176-179): `aggregate_results.py` 在 AGG-034 修复后已使用 `logging.basicConfig` + `logger.warning/info`；`check_run_completeness.py`、`export_tables_latex.py` 均有 `logger`；但 `run_experiments.py` 作为核心编排脚本从未 `import logging`，所有 "Warning:"/"Error:" 均为 `print()`。后果：(1) 无法通过日志级别过滤；(2) 无时间戳；(3) Warning 输出到 stdout（重定向到文件则警告消失）；(4) 与同目录其他脚本日志策略不一致。 — D7 全项目, confidence: 95% -- fixed

- [x] **QUA-003** `[MED]` `_safe_t_crit` 内联函数定义在 `_add_ci95_columns` 循环体内，每列均重建函数对象 (scripts/aggregate_results.py:227-230): `def _safe_t_crit(n: float) -> float:` 定义在 `for col in list(out.columns):` 循环体内，每次迭代都创建新函数对象。该函数不依赖任何循环变量，应提取为模块级私有函数，避免循环内函数定义的反模式。 — D7 全项目, confidence: 90% -- fixed

- [x] **QUA-004** `[MED]` `INT8CacheWrapper` 类含开发时遗留悬挂注释，参数缺少 type hints (src/engine/patch_model.py:64-91): `__init__` 参数 `cache_engine`, `layer_idx` 无类型注释；`update()` 方法注释包含 `"But we handle updates in generate_loop usually?"` 等疑问句开发笔记，在生产代码中不应存留；该类缺少 class-level docstring，仅 `INT8CacheWrapperContainer` 有说明。 — D7 全项目, confidence: 85% -- fixed

- [x] **QUA-005** `[MED]` `KV_MODE_ORDER` 在两处独立定义，两脚本之间无共享源 (scripts/aggregate_results.py:87-97, scripts/export_tables_latex.py:55-65): 当前两处顺序恰好一致，但两处独立维护——若一处新增 kv_mode，另一处不会自动更新，导致排序或显示名不一致。建议提取到 `src/utils/constants.py` 统一管理（`generate_loop.py:316-326` 的 kv_mode 合法值列表也应同步）。 — D7 全项目, confidence: 88% — fixed 8f39875

- [x] **QUA-006** `[MED]` `eval_ppl.py` 文件顶部保留大段开发决策笔记作为行内注释 (scripts/eval_ppl.py:23-43): L23-43 共 21 行注释描述"为何用 HF 滑动窗口而非自定义引擎"，写作风格为开发过程思考（"LIMITATION:", "DECISION:", "Wait, PPL is ..."），不适合留在生产源码顶部，应移入 `docs/` 或作为 ADR 记录。 — D7 全项目, confidence: 82% — fixed 2f6cddb

- [x] **QUA-007** `[MED]` `run_experiments.py` 中 `_timeout` 局部变量以下划线前缀命名，违反 Python 惯例 (scripts/run_experiments.py:1437): `_timeout = int(args.subprocess_timeout) if int(args.subprocess_timeout) > 0 else None`——下划线前缀惯例用于模块级/类级私有名，局部变量无需此前缀。与同函数其他局部变量（`returncode`, `failure_type`, `log_mode`）风格不一致。建议命名为 `timeout_sec`。 — D7 全项目, confidence: 82% -- fixed

- [x] **QUA-008** `[LOW]` `_safe_t_crit` 中 `return 0.0`（n<=1 分支）被后续 `.where(cnt > 1, np.nan)` 覆盖，存在语义冗余 (scripts/aggregate_results.py:227-233): `_safe_t_crit` 在 `n <= 1` 时返回 `0.0`（使 `t_crit * sem = 0`），但紧接着 `ci_half = ci_half.where(cnt > 1, np.nan)` 将 `cnt <= 1` 处强制置 `NaN`，使该返回值永远不进入最终输出。应在注释中说明双重保护的分工，或简化逻辑。 — D7 全项目, confidence: 80% — fixed 2f6cddb

- [x] **QUA-009** `[LOW]` `aggregate_results.py` import 块违反 PEP 8 顺序，标准库 `logging` 插入第三方库块中间 (scripts/aggregate_results.py:14-26): `import logging`（L25）出现在 `matplotlib`（L23）和 `numpy`（L24）第三方库之间，PEP 8 要求标准库导入集中在第三方库之前。应将 `import logging` 上移至标准库导入组（L14-21）。 — D7 全项目, confidence: 90% -- fixed

- [x] **QUA-010** `[LOW]` `profile_latency.py` / `profile_memory.py` 的 `_resolve_quant_bits` DEPRECATED 副本未加 `warnings.warn` (scripts/profile_latency.py:54-66, scripts/profile_memory.py:59-71): `eval_ppl.py:83` 的副本在 PRF-002 修复时加了 `warnings.warn`，但 `profile_latency.py` 和 `profile_memory.py` 的副本仅有注释 `# DEPRECATED`，调用方不会收到运行时提示，与 `eval_ppl.py` 的处理不一致。 — D7 全项目, confidence: 85% -- fixed

### SEC. 安全漏洞 — 全项目 (D3 审查 2026-02-24)

- [x] **SEC-001** `[HIGH]` 服务器地址与 SSH 信息已入 git 历史 (.agents/skills/remote-server/SKILL.md:15-18, iteration.md:319): `.agents/skills/remote-server/SKILL.md` 被 git 追踪（commit a0a32ff），文件明文包含 SSH_HOST/PORT/USER 及完整 rsync/ssh 命令串；`iteration.md` L319 含主机+端口监控命令。`docs/autodl_server.md` 含明文密码 `YLt4oozwKWNg` 但被 `.gitignore` 正确排除（未入库）。利用路径：任何能读仓库者可获服务器连接信息；若密码通过其他渠道泄露（如文件误分享）即可登录 root@GPU 服务器。修复：① 立即更改 AutoDL 密码；② 从 SKILL.md 移除具体 IP/端口，改为引用 `docs/autodl_server.md` 的注释；③ 视暴露范围决定是否用 `git filter-repo` 清理历史中的服务器信息。 — D3, confidence: 95% — fixed 1976051 (current files sanitized; git history needs filter-repo + password rotation)

- [x] **SEC-002** `[MED]` trust_remote_code=True 搭配用户可控 --model_id 构成 RCE 风险（降级：研究 CLI 威胁面低，用户即攻击者） (scripts/smoke_test.py:164,173; eval_ppl.py:701,708; eval_needle.py:339,346; eval_longbench.py:745,752; eval_ruler.py:823,830; profile_latency.py:270,277; profile_memory.py:301,308; calibrate_behavior.py:754,761): 全项目 8 个脚本在模型加载时均设 `trust_remote_code=True`，且 `--model_id` 由命令行接受无白名单校验。该标志会无条件执行模型仓库中的任意 Python 代码（modeling_*.py 等）。利用路径：若 model_id 被攻击者控制（如恶意 YAML 配置或 CI 参数注入），可在 GPU 服务器上执行任意代码获得 root 权限。当前项目固定使用已知安全模型（CLAUDE.md §9），实际风险依赖 model_id 是否被严格管控。修复：在 `run_experiments.py` 中对 model_id 增加白名单校验（参考 `SUPPORTED_KV_MODES` 模式）；或仅对本地已验证路径设 `trust_remote_code=True`。 — D3, confidence: 85% — fixed ccd2cda

- [x] **SEC-003** `[MED]` requirements.txt 无版本 pin 且含未使用 web 框架依赖 (requirements.txt:21-22): 所有依赖均为裸包名，`fastapi` 和 `uvicorn` 在项目代码库中无任何实际使用（无路由定义、无服务启动代码），是冗余攻击面扩大依赖。若被意外加载或在 AutoDL 环境触发，会暴露 HTTP 端口。修复：① 移除 `fastapi` 和 `uvicorn`；② 使用 `env/requirements_freeze.txt` 中的锁定版本替换 `requirements.txt`。 — D3, confidence: 82% — fixed c5b763c

- [x] **SEC-004** `[MED]` 异常信息暴露服务器内部文件系统路径 (scripts/smoke_test.py:179; eval_ppl.py, eval_ruler.py, eval_longbench.py, eval_needle.py 等 except 块): `print(f"  ✗ Model loading failed: {e}")` 中异常对象含完整本地路径（如 `/root/autodl-tmp/hf_cache/...`）。`logs/` 目录已在 `.gitignore` 中，直接风险有限，但属纵深防御缺口。当 CI 输出被截图或分享时服务器路径结构被暴露。修复：在 except 块中对外部输出进行路径脱敏，仅打印异常类型和简短消息，详细信息写入本地日志。 — D3, confidence: 80% — fixed c5b763c

---

## Resolved

<details>
<summary>254 fixed + 10 false_positive + 4 wont_fix (click to expand)</summary>

### AGG. 聚合
- [x] **AGG-001** `[CRIT]` kivi_style 完全缺失显著性配对 — fixed commit 03ed4a0
- [x] **AGG-004** `[HIGH]` longbench_official_macro 未被聚合 — fixed commit 03ed4a0
- [x] **AGG-005** `[HIGH]` 显著性分析缺失 model_id/hardware 分组 — fixed commit 03ed4a0
- [x] **AGG-006** `[HIGH]` RULER 深度分析缺失 model_id — fixed commit 03ed4a0
- [x] **AGG-010** `[MED]` kv_mode 使用字母序排序而非语义顺序 (L552, L585, L648, L1322) — fixed
- [x] **AGG-011** `[MED]` 显著性配对数据可能被 aggfunc="mean" 静默平均 (L998) — fixed
- [x] **AGG-013** `[LOW]` LongBench 图 y 轴标签与新口径不一致 — fixed
- [x] **AGG-016** `[MED]` 显著性 pairings 遗漏 `("int4_baseline", "int4_ours")` (L2207-2212): INT8 有 baseline-vs-ours 配对，INT4 仅有 `("int4_fused", "int4_ours")`。若 Phase5v2 不含 int4_fused 运行，则 INT4 无任何显著性比较 — fixed
- [x] **AGG-017** `[MED]` `_export_per_model_layered_tables()` bare `except` 吞掉 CSV 读取错误 (aggregate_results.py): 空 `except:` 捕获所有异常（包括 CSV 格式损坏、权限错误），静默跳过该模型的表导出。应至少 `except Exception as e:` 并 log warning。 — D2 incremental, confidence: 90% — fixed
- [x] **AGG-018** `[HIGH]` ~~_add_ci95_columns z=1.96 → t 分位数~~ **FIXED** — 改用 _t_critical(df) 函数（scipy + fallback lookup table），n≤1 返回 NaN（同时修复 AGG-027）
- [x] **AGG-019** `[HIGH]` ~~sign-flip exact/MC 分支 p 值不一致~~ **FIXED** — exact 分支加 Phipson-Smyth +1 修正: p=(exceed+1)/(n_enum+1)，与 MC 分支一致
- [x] **AGG-020** `[HIGH]` ~~_read_csvs() bare except 静默跳过~~ **FIXED** — 改为 `except Exception as exc: logger.warning("Skipped unreadable CSV ...")`
- [x] **AGG-021** `[HIGH]` _main_claims_32k_table 混合 outer/left merge 产生幽灵行或丢失数据 (aggregate_results.py:1467-1477): latency+memory 用 outer merge（可能产生 NaN 幽灵行），ppl/longbench/ruler 用 left merge（可能丢弃不在 latency 中的 kv_mode 数据）。无 merge 后行数 sanity check。 — D2 EXP rotation, confidence: 85% — fixed
- [x] **AGG-022** `[HIGH]` _build_paired_metric_rows pivot_table aggfunc="mean" 静默折叠重复 seed 观测 (aggregate_results.py:1144-1153): 重复 (key, seed, kv_mode) 行被均值折叠，仅 print() 警告（非 logging）。折叠后 paired test 的独立性假设被违反，p-value 可能不可靠。 — D2 EXP rotation, confidence: 85% — fixed
- [x] **AGG-023** `[HIGH]` ~~relative_gain pairings 缺少 kivi_style~~ **FIXED** — 添加 ("kivi_style","int8_ours") 和 ("kivi_style","int8_baseline") 到 pairings 列表
- [x] **AGG-024** `[HIGH]` ~~relative_gain key_cols 不含 model_id~~ **FIXED** — 所有 7 个 _relative_gain_table 调用的 key_cols 增加 "model_id" 前缀
- [x] **AGG-025** `[HIGH]` ~~_main_claims_32k_table merge on kv_mode 笛卡尔积~~ **FIXED** — 动态 merge_keys 包含 model_id（当存在时），所有列列表和 merge/drop_duplicates 均使用 model_id
- [x] **AGG-026** `[HIGH]` gain_pct 与 diff 基于不同样本量计算 (aggregate_results.py:1156-1190): baseline=0 时 gain_pct=NaN，dropna(subset=...) 不含 gain_pct 列所以 NaN 行保留。但 _significance_summary 对 gain_pct 做额外 dropna，导致 gain_pct_mean 基于 n-k 样本而 diff_mean 基于 n 样本，n_pairs 不匹配。 — D1/D5 EXP rotation, confidence: 85% — fixed
- [x] **AGG-027** `[MED]` ~~count=1 时 CI 半宽 0.0 → NaN~~ **FIXED** — AGG-018 修复中一并处理，ci_half.where(cnt > 1, np.nan) 替代原 0.0
- [x] **AGG-028** `[MED]` _to_numeric errors="coerce" 将非数值静默转 NaN，无 warning (aggregate_results.py:107-111): 对所有指标列使用 `pd.to_numeric(errors="coerce")`，异常字符串（"N/A"、"err"、空串）变 NaN 后被 groupby 忽略。5-seed 小样本下丢失 1 个点显著影响结论。 — D2 EXP rotation, confidence: 90% — fixed
- [x] **AGG-030** `[MED]` _main_claims_32k_table latency 或 memory 为空即返回完全空表 (aggregate_results.py:1464-1467): 若 latency 数据缺失，即使 needle/ppl/longbench/ruler 完整，main claims 表也为空。无 warning。 — D2 EXP rotation, confidence: 90% — fixed
- [x] **AGG-033** `[CRIT]` 两个 signflip 单元测试断言与 Phipson-Smyth +1 修正不一致 (test_aggregate_results_stats.py:28-29,44-46): test_exact_signflip_pvalue_known_case 期望 0.125 (2/16) 但实际返回 3/17=0.1765；test_exact_signflip_pvalue_mixed_signs 用旧公式 np.mean(>=) 计算期望值。pytest 将直接失败，阻塞 CI。 — D4+D6 incremental, confidence: 99% — fixed

### CAL. 校准模块
- [x] **CAL-001** `[CRIT]` MSE loss 维度语义错误 (L199-200) — fixed commit 20095fb
- [x] **CAL-002** `[CRIT]` MSE loss 全局 mean 无维度 (L302) — fixed commit 20095fb
- [x] **CAL-003** `[CRIT]` calibrate_behavior.py --calib_out None fallback — fixed
- [x] **CAL-004** `[HIGH]` loss_accum 未除以样本数 (L177-206) — fixed commit 20095fb
- [x] **CAL-005** `[HIGH]` MSE 无数值安全 clamp (L199) — fixed commit 20095fb
- [x] **CAL-006** `[HIGH]` trial 排名受 loss 尺度影响 (L780-791) — fixed
- [x] **CAL-007** `[HIGH]` 默认校准路径与 generate_loop 不匹配 (calibrate_behavior.py — fixed
- [x] **CAL-008** `[HIGH]` 加载校准文件时无 loss_function 字段校验 (generate_loop.py — fixed
- [x] **CAL-009** `[HIGH]` calibrate_behavior.py MSE clamping 移除导致旧校准产物不可复现 — fixed
- [x] **CAL-010** `[MED]` 默认输出文件名硬编码为 kl.json — fixed commit 20095fb
- [x] **CAL-011** `[MED]` select_best_trial() 无 key 存在性校验 — fixed commit 20095fb
- [x] **CAL-012** `[MED]` MSE loss 语义未文档化 (L6, L234-239) — fixed
- [x] **CAL-013** `[MED]` inv_tau shape 未在加载时验证 (generate_loop.py — fixed
- [x] **CAL-014** `[MED]` MSE 与 KL loss 量级差异影响搜索行为 (calibrate_behavior.py — fixed
- [x] **CAL-015** `[MED]` evaluate_quant_candidate 不使用 inv_tau (calibrate_behavior.py — fixed
- [x] **CAL-016** `[MED]` calibrate_behavior.py MSE clamping 语义偏差：MSE 路径对 p_ref/p_quant 执行 clamp(min=eps) 后再计算差的平方。对 MSE 而言 clamp 不防 NaN（MSE 不含 — fixed...
- [x] **CAL-017** `[LOW]` loss_accum NaN 无检测 (calibrate_behavior.py — fixed
- [x] **CAL-018** `[LOW]` search_trials.csv 已按 loss_function 区分文件名 (calibrate_behavior.py — false_positive

### CFG. 配置
- [x] **CFG-001** `[HIGH]` 1.5B 配置完全缺失 KIVI-style 条目 — fixed commit f07422d
- [x] **CFG-002** `[HIGH]` 7B/8B 配置完全缺失吞吐量 batch scaling 条目 — fixed commit f07422d
- [x] **CFG-003** `[HIGH]` 7B/8B 配置缺失 INT4 长上下文运行 — fixed commit f07422d
- [x] **CFG-004** `[HIGH]` 消融 A-3 decode_attn_impl 混淆因子 — fixed commit f07422d
- [x] **CFG-005** `[HIGH]` 消融 A 节缺少 KIVI-style — fixed commit f07422d
- [x] **CFG-006** `[HIGH]` 7B/8B 校准产物尚未生成（Phase 2 依赖，非 bug） — false_positive
- [x] **CFG-007** `[MED]` final_emnlp2026_v1.yaml LLaMA 本地路径硬编码 — fixed
- [x] **CFG-010** `[MED]` 消融 A-2 (MSE) 使用 use_attn_temperature — false_positive
- [x] **CFG-014** `[MED]` ablation_dimensions.scale_strategy 仅列 [static, adaptive]（L77）— 计划中为 "static vs adaptive vs dynamic" 三方，与消融配置 D 节同一缺失 — fixed
- [x] **CFG-015** `[MED]` LLaMA-3.1-8B 使用本地路径而非 HF ID — fixed
- [x] **CFG-016** `[MED]` Claims C9-C11 定义不够精确 — fixed
- [x] **CFG-017** `[LOW]` 1.5B 配置头部注释缺少 kivi_style kv_mode 和 kivi_asymmetric calib_strategy — false_positive
- [x] **CFG-018** `[LOW]` 消融 A-1/B-1/C-1 是完全相同的 run — false_positive
- [x] **CFG-019** `[LOW]` benchmarks 仅列 4 个质量评测（L67-71）— 未包含 latency/memory/throughput 系统性能 benchmark，虽然这些是独立维度但在 meta-config 中应有提及 — fixed
- [x] **CFG-020** `[LOW]` models[0].calibration_artifacts 列出了尚不存在的 MSE 产物（int8_mse/int4_mse，L38-39）— MSE 校准实现有已知 bug，这些产物暂不可用 — fixed
- [x] **CFG-021** `[LOW]` meta-config 无执行工作流说明 — fixed

### CHK. 完整性检查
- [x] **CHK-001** `[CRIT]` OOM 分类被 elif 链短路 (L94-109) — fixed commit 1aa5c95 (OOM 检查已移至 if 链首位 L147-148)
- [x] **CHK-002** `[HIGH]` manifest 无 failure_type 字段 (L85) — fixed
- [x] **CHK-003** `[HIGH]` 不验证 kivi_style 运行完整性 — fixed
- [x] **CHK-007** `[HIGH]` manifest_status="running" + 完整有效 CSV 被错判为 mixed_csv_non_success (L153-159): success 分支要求 manifest_status∈{success,skipped}，"running" 落入 L159 的 mixed 分支。进程在写完 CSV 后崩溃但未更新 manifest 时触发，导致不必要的重跑。 — D2, confidence: 90% — fixed
- [x] **CHK-008** `[HIGH]` 日志 errors="ignore" 掩盖 OOM/traceback 检测 (L49): `_read_text()` 用 `errors="ignore"` 静默丢弃非 UTF-8 字节，若 OOM 关键字跨越被丢弃的字节则 re.search 漏检。应用 `errors="replace"`。 — D2+D5, confidence: 88% — fixed
- [x] **CHK-009** `[HIGH]` JSON manifest 损坏被 except 静默返回 None (L37-42): `_read_json()` 对任何异常（含 JSONDecodeError）返回 None，调用方无法区分"文件不存在"与"文件损坏"。损坏的 manifest 被当作空处理，运行被误判为 missing。 — D2, confidence: 88% — fixed
- [x] **CHK-010** `[HIGH]` 新增任务类型无 CSV 模式和产物验证 → 默认通过 (L17-24, L85-91): TASK_TO_CSV_PATTERN 仅 6 任务，新任务 csv_pattern="" → glob 无匹配 → has_csv=False → "missing"。但 `_has_task_level_artifacts` 对非 LB/RULER 任务返回 True，无实际验证。 — D2+D1+D7, confidence: 95% — fixed
- [x] **CHK-011** `[MED]` CSV 三种失败模式不区分 (L62-74): `_csv_has_rows()` 对文件不存在/仅 header/读取异常均返回 False，调用方合并为 `has_valid_csv=False`，无法针对性修复。 — D2, confidence: 85% — fixed
- [x] **CHK-012** `[MED]` 非整数 seed 参数导致未处理 ValueError (L270): `int(x)` 对 "abc" 等输入直接崩溃，无友好错误提示。 — D2+D5, confidence: 85% — fixed
- [x] **CHK-013** `[MED]` 空 required/stress_run_names 产生虚假 complete=True (L268-269, L318): 空列表 → 空 expected → missing_run_names=[] → required_complete=True。无至少一个 run 的前置检查。 — D2+D5, confidence: 85% — fixed
- [x] **CHK-014** `[MED]` --tasks 默认值与 run_experiments.py 不一致 (L252): check 脚本默认 "profile_latency,profile_memory"(2 任务)，run 脚本默认 4 任务。长实验检查时漏验 eval_ppl/eval_needle。 — D4, confidence: 86% — fixed
- [x] **CHK-016** `[MED]` Traceback 检测大小写敏感 (L58): 使用精确字符串 "Traceback (most recent call last):" 匹配，小写变体漏检。OOM 检测用了 re.IGNORECASE 但 Traceback 没有。 — D7, confidence: 88% — fixed
- [x] **CHK-017** `[MED]` 状态转移链 7 层嵌套无注释 (L147-166): 20 行 elif 链含复杂布尔表达式和多个不可达分支，无状态机文档。维护易引入逻辑错误。 — D7, confidence: 100% — fixed
- [x] **CHK-019** `[MED]` L159 中 "skipped" 是不可达分支: has_csv=True + manifest_status="skipped" 总被 L153 先捕获（"skipped" 在 L154 的集合中）。死代码增加阅读困惑。 — D7, confidence: 95% — fixed

### ENG. 引擎模块
- [x] **ENG-002** `[HIGH]` generate() 函数缺少 quant_bits 参数 — fixed commit 20095fb
- [x] **ENG-015** `[HIGH]` Triton kernel 硬编码 fp16 输出与 bf16 输入 dtype 不匹配 (triton_decode_attn_int8.py:285): kernel `tl.store` 强制转 `tl.float16`，但 wrapper 分配 `torch.empty_like(q)` 继承 q 的 dtype。若模型以 bf16 运行，位模式解释错误产生静默数值偏差。当前所有脚本用 fp16 不触发。 — D1, confidence: 92% — fixed
- [x] **ENG-016** `[HIGH]` Triton kernel 在 context_lens=0 时 softmax 除零产生 NaN (triton_decode_attn_int8.py:281): online softmax `l_i=0.0`，无 token 时 `acc/l_i = 0/0 = NaN`；torch_ref 正确返回零向量。两实现边界行为不一致。 — D1, confidence: 95% — fixed
- [x] **ENG-017** `[HIGH]` apply_int8_fused_patch layers=None 后仍硬访问 model.model.layers[0] (patch_model.py:720-755): try 块吞异常设 layers=None，但 L755 在 try 外再次访问同一属性，产生不可理解的 AttributeError 而非清晰的 ValueError。 — D2+D5, confidence: 95% — fixed
- [x] **ENG-018** `[MED]` max_new_tokens=0 时仍生成 1 个 token (generate_loop.py:639,655): prefill 后无条件追加第一个 argmax token，decode loop `range(-1)` 不执行，`gen_len=1` 返回。语义违反 "生成 0 个新 token" 约定。 — D5, confidence: 95% — fixed
- [x] **ENG-019** `[MED]` inv_tau[layer_idx] 无越界校验 (patch_model.py:559): fused decode 直接索引无边界检查，prefill 路径有检查。校准层数不匹配时报无上下文 IndexError。 — D5, confidence: 92% — fixed
- [x] **ENG-020** `[MED]` batch_size=0 / prompt_len=0 未校验 (generate_loop.py:367-374): `input_ids.shape=[0,S]` 或 `[B,0]` 导致下游 IndexError（logits[:,-1,:] 在空维度索引）或未定义行为。 — D5, confidence: 95% — fixed
- [x] **ENG-022** `[MED]` prefill temperature hooks 在 model 结构不标准时静默返回空列表 (generate_loop.py:172-175): 校准文件已加载但 hooks 未注册无 warning，用户以为使用 ours 方法实际无 temperature 校正。 — D2, confidence: 90% — fixed
- [x] **ENG-024** `[MED]` _maybe_dump_fused_decode 类型签名声明 torch.Tensor 但实际可接收 None (patch_model.py:308-309,677-689): `cache_kind=int4` + dump 未启用时传入 None。dump 启用时会 crash。应改为 Optional。 — D4+D2, confidence: 92% — fixed
- [x] **ENG-026** `[MED]` calib_group_k 使用 `or` 运算符，合法值 0 被静默替换 (generate_loop.py:476-477): JSON 中 `"group_size_k": 0` 被 Python `or` 视为 falsy 丢弃。 — D2, confidence: 82% — fixed
- [x] **ENG-028** `[MED]` INT4 动态量化 scale 强制转 fp16 与 INT8 路径不一致 (quant/int4_basic.py:131): INT8 用 `abs_max.to(tensor.dtype)` 保留输入精度，INT4 硬转 `torch.float16`。 — D1, confidence: 88% — fixed
- [x] **ENG-031** `[MED]` kv_mode 集合常量重复硬编码 4 次 (generate_loop.py:398,668,684,701): `["int8_fused","int8_ours","int4_fused","int4_ours","int4_ours_mixed"]` 应提取为模块级 frozenset。 — D7, confidence: 95% — fixed

### EVL. 评测脚本
- [x] **EVL-001** `[CRIT]` eval_longbench.py _classification_accuracy() 语义变化未文档化 (L265) — fixed commit 52f4abf (CLASSIFICATION_MATCH_POLICY 常量 + docstring + CSV audit 字段)
- [x] **EVL-002** `[CRIT]` **RULER CWE 子任务在 1.5B *_long 配置下触发 max_position_embeddings 溢出** — fixed commit b7f4c36 (_effective_prompt_budget() 确保 prompt + gen ≤ max_model_len)
- [x] **EVL-003** `[CRIT]` export_tables_latex.py KV_MODE_DISPLAY 缺 kivi_style — fixed commit 8bf9414
- [x] **EVL-004** `[CRIT]` export_tables_latex.py KV_MODE_ORDER 缺 kivi_style — fixed commit 8bf9414
- [x] **EVL-005** `[CRIT]` MK-NIAH hits_exact 计数器死代码 (L172-174) — fixed
- [x] **EVL-006** `[CRIT]` VT 多链评分仅评价第一条链 (L216, L442) — fixed
- [x] **EVL-007** `[CRIT]` 上下文截断从右侧保留破坏 RULER 语义 (L546-554) — fixed
- [x] **EVL-008** `[HIGH]` **run_experiments.py 预检查遗漏 RULER CWE 的额外 max_new_tokens 开销** (L806-928) — fixed commit b7f4c36 (prelaunch 截断警告 + _effective_prompt_budget)
- [x] **EVL-009** `[HIGH]` eval_longbench.py 引用未定义 logger — fixed commit 20095fb
- [x] **EVL-010** `[HIGH]` generate_thesis_report.py 缺少 KIVI claims — fixed commit 8bf9414
- [x] **EVL-011** `[HIGH]` kivi_style quant_bits 推断为 16 (L985) — fixed
- [x] **EVL-012** `[HIGH]` 分类准确率子串匹配过于宽松 (L252) — fixed
- [x] **EVL-013** `[MED]` eval_ruler.py 截断策略 magic numbers (L562-570) — fixed
- [x] **EVL-014** `[MED]` **eval_ruler.py case 循环无 per-case error handling** (L872-908) — fixed
- [x] **EVL-015** `[MED]` 所有 eval 脚本 quant_bits fallback 将 KIVI 记录为 16 (eval_ppl L878 / eval_needle L467 / eval_longbench L833 / eval_ruler L98... — fixed
- [x] **EVL-016** `[MED]` eval_longbench.py 指标单位不一致 (L807-808) — fixed
- [x] **EVL-017** `[MED]` eval_longbench.py 自实现 Rouge-L 可能与官方 LongBench 不一致 (L206-219) — fixed
- [x] **EVL-018** `[MED]` aggregate_results.py kv_mode 排序无 KIVI (L552, L585, L648, L1322) — fixed
- [x] **EVL-019** `[MED]` CWE pred_words 未过滤空字符串 (L193) — fixed
- [x] **EVL-020** `[MED]` 指标尺度 [0,100] vs objective.md 声称 [0,1] 不一致 (L812, L867-868) — fixed
- [x] **EVL-021** `[MED]` HF 字段提取 fallback 顺序含 "input" 作为 context 候选 (L387) — fixed
- [x] **EVL-022** `[LOW]` eval_ruler.py 多答案评分存在死代码 (L172-174) — fixed
- [x] **EVL-024** `[LOW]` _token_f1() 分母过度保护 (L140-141) — fixed
- [x] **EVL-025** `[LOW]` task_off_name 取 vals[0] 假设同一任务所有样本指标名一致 (L811) — fixed
- [x] **EVL-027** `[LOW]` eval_ruler.py `_effective_prompt_budget()` 死存储 (L~550): 函数计算 `available` 后立即被后续逻辑覆盖，中间赋值未被使用。无功能影响但增加阅读困惑。 — D1 incremental, confidence: 85% — fixed
- [x] **EVL-028** `[MED]` eval_ruler.py error case NaN 分数传播风险: per-case 异常处理将 score 设为 NaN，但下游聚合（mean over cases）中 NaN 参与计算导致整个 task 结果为 NaN。应使用 `nanmean` 或在聚合前过滤。 — D1 incremental, confidence: 88% — fixed

### EXP. 导出/报告
- [x] **EXP-001** `[HIGH]` C11 跨模型验证逻辑缺陷 (generate_thesis_report.py — fixed
- [x] **EXP-009** `[MED]` generate_thesis_report.py 跨模型 claim `gains.min()` 与 `all(practical_pass)` 语义不匹配: `gains.min()` 取数值最小值，但 `practical_pass` 基于阈值判断。当 min gain 远大于阈值但某模型的 practical_pass 因其他原因（如缺数据）为 False 时，两个信号矛盾。 — D1 incremental, confidence: 85% — fixed
- [x] **EXP-010** `[HIGH]` generate_thesis_report.py 单模型路径缺少 `target_model_id` 字段: 当 `--model_ids` 只传一个模型时，`_evaluate_claim_row()` 返回的 dict 不含 `target_model_id` key，但下游 DataFrame 构建假设该列存在，导致 KeyError。跨模型路径正常。 — D1 incremental, confidence: 92% — fixed
- [x] **EXP-011** `[LOW]` generate_thesis_report.py NaN `gain_pct` 被判定为 FAIL 而非 INCONCLUSIVE: 当 baseline 为 0 时 `gain_pct = NaN`，当前逻辑将 NaN 视为未通过阈值 → FAIL。应归类为 INCONCLUSIVE 并在报告中标注。 — D2 incremental, confidence: 85% — fixed
- [x] **EXP-012** `[LOW]` generate_thesis_report.py 单模型 vs 跨模型 claim schema 不一致 (27 vs 29 keys): 单模型 claim dict 缺少 `min_gain_model` 和 `max_degradation_model` 字段，跨模型有。下游若以跨模型 schema 为模板构建 DataFrame，单模型行会出 NaN 列。 — D4 incremental, confidence: 82% — fixed
- [x] **EXP-013** `[HIGH]` export_tables_latex.py `_read_csv()` bare except 返回空 DataFrame，全部下游 export 静默跳过: L66-70 `except: return pd.DataFrame()` 吞掉所有异常（包括 schema 错误、编码错误），8 个 export 函数均依赖此函数，文件损坏或格式变更时无任何警告，产出空 LaTeX 表格。 — D2 EXP rotation, confidence: 95% — fixed
- [x] **EXP-014** `[MED]` export_tables_latex.py `_pivot_metric()` groupby().mean() 静默平均多模型行: L91-126 当输入包含多个 model_id 的数据时，pivot 前的 groupby 会将不同模型的指标平均，产出的 LaTeX 表格数值为多模型混合平均值而非单模型值。当前无 model_id 过滤逻辑。 — D4 EXP rotation, confidence: 90% — fixed
- [x] **EXP-015** `[MED]` export_tables_latex.py LaTeX `--label_prefix` 注入风险: `label_prefix` 参数直接拼入 `\label{}` 命令（L140 等），含特殊字符（如 `}`, `\`）时会破坏 LaTeX 编译。无输入校验或转义。 — D3 EXP rotation, confidence: 85% — fixed
- [x] **EXP-016** `[MED]` export_tables_latex.py export_latency / export_memory 近乎重复的 DRY 违反: L159-225 两函数结构几乎相同（仅 metric_col 和标题不同），约 60 行重复代码。应提取公共 `_export_profile_table()` 函数。 — D7 EXP rotation, confidence: 88% — fixed

### KVC. KV Cache
- [x] **KVC-001** `[CRIT]` K-scale/zp 在 clear() 后状态不一致 — fixed commit 20095fb
- [x] **KVC-003** `[HIGH]` 论文内存对比表必须注明 KIVI INT4 无 bit-packing — fixed
- [x] **KVC-004** `[HIGH]` 论文 Methods 节须披露 K 量化策略差异 — fixed
- [x] **KVC-005** `[MED]` kivi_style_cache.py clear() 仅重置 K scale/zp 未显式清零 V scale/zp — fixed
- [x] **KVC-006** `[MED]` decode K 量化与 prefill K 量化 device 一致性未强制 (L220-231) — fixed
- [x] **KVC-007** `[MED]` V buffer shape 一致性未校验 (L126-131) — fixed
- [x] **KVC-008** `[MED]` append() 无输入 tensor shape 校验 (L187-245) — fixed
- [x] **KVC-009** `[MED]` get_memory_mb() 注释误导 (L307) — fixed
- [x] **KVC-010** `[MED]` INT4 量化精度 edge case 未覆盖 — fixed
- [x] **KVC-011** `[MED]` 论文须披露 KIVI 无温度校正 — fixed
- [x] **KVC-012** `[MED]` 论文须披露 decode kernel 差异 — fixed
- [x] **KVC-013** `[LOW]` kivi_style_cache.py INT4 head_dim 偶数约束仅在 append 时检查 — fixed
- [x] **KVC-014** `[LOW]` _seq_len 仅在 layer_id=0 时更新 (L244-245) — fixed
- [x] **KVC-015** `[LOW]` 无 batch_size=0 校验 (L204) — fixed
- [x] **KVC-017** `[LOW]` KIVI K-scale 内存恒定 vs INT8 随 seq_len 增长 — fixed

### PRF. 性能分析
- [x] **PRF-001** `[HIGH]` kivi_style quant_bits CSV 记录 vs 运行时不一致 (L304/341 vs L369) — fixed
- [x] **PRF-006** `[MED]` pynvml 初始化异常未捕获 (L104-105) — fixed
- [x] **PRF-007** `[MED]` MemoryMonitor.stop() 线程健壮性 (L119-121) — fixed
- [x] **PRF-008** `[MED]` NVML 回退逻辑隐性掩盖不可用 (L381) — fixed

### QNT. 量化模块
- [x] **QNT-001** `[CRIT]` percentile < 50 时 quantile_lo > quantile_hi — fixed commit 20095fb
- [x] **QNT-002** `[CRIT]` 无 percentile 范围校验 — fixed commit 20095fb
- [x] **QNT-005** `[MED]` _normalize_static_scale 3D case 实现错误 — fixed

### RUN. 实验运行
- [x] **RUN-001** `[CRIT]` eval_ppl.py build_kv_cache() 缺失 kivi_style 分支 — fixed commit 03ed4a0
- [x] **RUN-002** `[HIGH]` kivi_style 的 calib_strategy 默认值继承陷阱 (L880-881, L1015-1016) — fixed
- [x] **RUN-003** `[MED]` skip_completed_success 状态不一致 (L1134 vs L1147) — fixed
- [x] **RUN-004** `[MED]` subprocess.run 无异常捕获 (L1174-1179) — fixed
- [x] **RUN-005** `[MED]` kv_mode 无效值静默跳过 (L850-862) — fixed
- [x] **RUN-006** `[MED]` kivi_style decode_attn_impl 无强制验证 (L882-884, L1033-1034) — fixed
- [x] **RUN-007** `[MED]` 无条件传递 quant 参数给所有 kv_mode (L987-998) — fixed
- [x] **RUN-008** `[MED]` skip 时重复标记成功 (L1130-1138) — fixed
- [x] **RUN-015** `[MED]` repair_phase5v2_ruler_light.py JSON parse 异常静默跳过: `json.load()` 失败时 `continue` 跳过该文件无 warning，可能丢失需修复的数据。应 log 文件名和错误原因。 — D2 incremental, confidence: 88% — fixed
- [x] **RUN-016** `[MED]` repair_phase5v2_ruler_light.py `--execute` 模式首次失败即中止: 执行修复命令序列时，任一命令失败立即退出，剩余修复命令丢失。应收集所有失败后统一报告。 — D2 incremental, confidence: 85% — fixed

### RVW. 审查工具与配置
- [x] **RVW-001** `[HIGH]` review_tool.py phase-gate 仅检查 CRIT，遗漏 HIGH (L120): `cmd_phase_gate()` 仅过滤 `severity == "CRIT"`，按 CLAUDE.md §4.5 闸门规则，HIGH 也应阻塞（至少提示）。可能导致存在 HIGH 阻塞项时误判为 CLEAR — fixed
- [x] **RVW-002** `[HIGH]` review_tool.py cmd_add() 文件写入非原子性 (L230-231): `open(path, "w")` 直接覆写，若进程中途崩溃会导致 review_tracker.md 被截断或损坏。应使用 tmpfile + rename 原子写入 — fixed
- [x] **RVW-003** `[MED]` review_tool.py 解析不匹配行静默跳过 (L42-87): 任何不符合 ISSUE_RE 格式的 issue 行会被完全忽略，无警告日志。正则已从 `\w+` 改为 `[A-Z]+` 部分改善，但核心静默跳过问题仍存在 — fixed
- [x] **RVW-004** `[MED]` review_tool.py _update_summary() 格式假设过强 + 双写竞争 (L268-287): `summary_replaced` 标志仅在 "Last updated:" 行后触发，若 header 行顺序变化或新增行则部分 summary 不更新。另外 `cmd_add` 先 write content 再调 `_update_summary`（二次 open+write），后者可能只更新部分摘要行却无返回值通知调用方 — fixed
- [x] **RVW-005** `[MED]` reviewer.md L5 描述引用 "iteration.md TODO Backlog" 应为 "review_tracker.md" (.claude/agents/reviewer.md L5) — fixed
- [x] **RVW-006** `[MED]` reviewer.md YAML 权限与 body 指令矛盾 (.claude/agents/reviewer.md L8 vs L11,L16) — fixed: body 改为"严禁修改源代码（src/、scripts/、tests/、configs/）"，写入权限标注"仅限 review_tracker.md + iteration.md"
- [x] **RVW-007** `[MED]` start_agents.sh L32 developer 启动 prompt 引用 "TODO Backlog" 而非 review_tracker.md (scripts/start_agents.sh L32): 与 developer.md L22 "读取 review_tracker.md" 冲突，可能导致 developer agent 优先遵循启动 prompt 到 iteration.md 而非 review_tracker.md 查找任务 — fixed (prompt 改为 "读 review_tracker.md + iteration.md → 按优先级矩阵领取任务")
- [x] **RVW-008** `[MED]` start_agents.sh L33 reviewer 启动 prompt 未提及 review_tracker.md (scripts/start_agents.sh L33): reviewer.md L21 要求先读 review_tracker.md，但启动 prompt 仅说"读 iteration.md" — fixed commit 3ba38e3 (prompt 已更新为 "读 review_tracker.md → 进入持续监控循环")
- [x] **RVW-009** `[LOW]` settings.json Stop hook "BLOCKED" 字符串匹配过宽 (.claude/settings.json L21): iteration.md 历史条目中若包含 "BLOCKED" 一词（如引用 Phase Gate 状态），会误触发退出许可，应匹配更精确的标记如 "auto-iterate-blocked" — fixed
- [x] **RVW-010** `[LOW]` start_agents.sh 硬编码绝对路径 (scripts/start_agents.sh L5): `PROJECT_DIR="/Users/chenzilang/..."` 不可移植，建议使用 `$(cd "$(dirname "$0")/.." && pwd)` — fixed commit 3ba38e3
- [x] **RVW-011** `[HIGH]` Phase Blocker CHK-001 已修复但未标记 — 独立审查确认 `_check_task_state()` OOM 检查已移至 if 链首位 (check_run_completeness.py L147)，匹配 Codex PR 修复 (merge 1aa5c95)。Phase Gate 状态过期，建议 developer 验证并标记 fixed 以解除 blocker — fixed (supervisor 已验证并标记 CHK-001)
- [x] **RVW-012** `[MED]` 多处 kv_mode 列表遗漏 int4_fused: developer.md L91 和 CLAUDE.md §9 固定决策均缺少 `int4_fused`（仅列 6 项），而 review-numerical.md L122 和代码 generate_loop.py 均包含 `int4_fused`（7 项）。权威文件与实际代码不一致 — fixed
- [x] **RVW-014** `[HIGH]` cmd_add() 在 `## Open Issues` 节缺失时静默无操作 (scripts/review_tool.py L219-235): 当 `re.search(r'^## Open Issues', content)` 返回 None 时，整个写入分支被跳过，函数仍输出 "Added: ..." 并返回 0，issue 实际未写入 — confidence: 97% — fixed
- [x] **RVW-015** `[HIGH]` start_agents.sh L28 `--agent reviewer` 引用已删除的 agent (scripts/start_agents.sh L16,L28): reviewer.md 已被 review-coord.md + 7 专项 Agent 替代，执行该脚本会以不存在的 reviewer agent 启动第三个 pane，审查子系统完全无法工作 — fixed commit 3ba38e3
- [x] **RVW-016** `[MED]` cmd_add() 无重复 ID 检查 (scripts/review_tool.py L192-236): 重复执行相同 `--id` 会产生重复条目，cmd_stats 计数虚高 — confidence: 100% — fixed
- [x] **RVW-017** `[MED]` parse_tracker rest.replace(" — fixed", "") 全局替换可损坏 title (scripts/review_tool.py L63): 若 issue title 本身包含 " — fixed" 子串（如 "partially — fixed workaround"），该子串也会被静默删除 — confidence: 80% — fixed
- [x] **RVW-018** `[MED]` 无效 --sev 参数静默返回空结果 (scripts/review_tool.py L137-139): 传入未知 severity（如 `--sev foo`）时 fallback 为 `"FOO"`，过滤结果为空列表，exit code 仍为 0，用户无法区分"真无结果"与"参数拼写错误" — confidence: 88% — fixed
- [x] **RVW-019** `[MED]` supervisor.md 迭代上限与 auto-iterate SKILL.md 不一致 (supervisor.md L66,L104 vs SKILL.md L85,L95): supervisor.md 声明默认 5 轮，SKILL.md L85 写 8 轮、L95 写 5 轮，SKILL.md 内部亦矛盾 — confidence: 95% — false_positive
- [x] **RVW-020** `[MED]` CLAUDE.md §12 遗漏 review-coord 中间层 (CLAUDE.md L251): 描述为"由 Supervisor 并行调度"7 个审查 Agent，但实际架构是 Supervisor → review-coord → 7 Agent，遗漏了 coordinator 层 — confidence: 90% — fixed
- [x] **RVW-021** `[MED]` cmd_add 无并发写保护，多 Agent 并行添加 issue 可能丢失写入 (review_tool.py:199-231): read→modify→write 无文件锁，两个 review agent 同时执行 add 时，后写者覆盖前者。Agent Teams 场景下可触发。 — D3+D5 RUN rotation, confidence: 75% — fixed
- [x] **RVW-022** `[MED]` _update_summary 遗漏 wont_fix 计数致 summary 算术不一致 (review_tool.py:257-261): res_parts 仅含 fixed+false_positive，wont_fix>0 时 total != fixed+fp+open。cmd_stats 正确计数但 _update_summary 未传播。 — D1 RUN rotation, confidence: 90% — fixed
- [x] **RVW-023** `[MED]` _update_summary 依赖 summary 行顺序，格式变更时静默失效 (review_tool.py:273-283): 仅当 "Last updated:" 行出现后才停止替换，若 header 行顺序变化则部分 summary 不更新，无 warning。 — D1+D7 RUN rotation, confidence: 70% — fixed

### TST. 测试覆盖
- [x] **TST-001** `[HIGH]` KIVI cache zero-point decode 传播测试缺失 — fixed
- [x] **TST-002** `[HIGH]` asymmetric_quant zero-point 公式直接验证缺失 — fixed

</details>
