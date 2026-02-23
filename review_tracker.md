# Code Review Tracker

> 280 issues | 81 fixed + 2 false_positive | 197 open (0 CRIT, 42 HIGH, 114 MED, 41 LOW)
> Phase Gate: **CLEAR** — all CRITICAL resolved
> Last updated: 2026-02-24

---

## Phase Blockers (CRITICAL open)

### CHK. 完整性检查 — `scripts/check_run_completeness.py`

- [x] **CHK-001** `[CRIT]` OOM 分类被 elif 链短路 (L94-109) — fixed commit 1aa5c95 (OOM 检查已移至 if 链首位 L147-148)
- [ ] **CHK-002** `[HIGH]` manifest 无 failure_type 字段 (L85)
- [ ] **CHK-003** `[HIGH]` 不验证 kivi_style 运行完整性
- [ ] **CHK-004** `[MED]` 不验证 CSV 内容完整性 (L80)
- [ ] **CHK-005** `[MED]` LongBench/RULER 任务级完整性无验证 (L16-23, L146-148)
- [ ] **CHK-006** `[MED]` dev agent 仍未确认 O 节 3 CRITICAL + T 节 1 CRITICAL
- [ ] **CHK-007** `[HIGH]` manifest_status="running" + 完整有效 CSV 被错判为 mixed_csv_non_success (L153-159): success 分支要求 manifest_status∈{success,skipped}，"running" 落入 L159 的 mixed 分支。进程在写完 CSV 后崩溃但未更新 manifest 时触发，导致不必要的重跑。 — D2, confidence: 90%
- [ ] **CHK-008** `[HIGH]` 日志 errors="ignore" 掩盖 OOM/traceback 检测 (L49): `_read_text()` 用 `errors="ignore"` 静默丢弃非 UTF-8 字节，若 OOM 关键字跨越被丢弃的字节则 re.search 漏检。应用 `errors="replace"`。 — D2+D5, confidence: 88%
- [ ] **CHK-009** `[HIGH]` JSON manifest 损坏被 except 静默返回 None (L37-42): `_read_json()` 对任何异常（含 JSONDecodeError）返回 None，调用方无法区分"文件不存在"与"文件损坏"。损坏的 manifest 被当作空处理，运行被误判为 missing。 — D2, confidence: 88%
- [ ] **CHK-010** `[HIGH]` 新增任务类型无 CSV 模式和产物验证 → 默认通过 (L17-24, L85-91): TASK_TO_CSV_PATTERN 仅 6 任务，新任务 csv_pattern="" → glob 无匹配 → has_csv=False → "missing"。但 `_has_task_level_artifacts` 对非 LB/RULER 任务返回 True，无实际验证。 — D2+D1+D7, confidence: 95%
- [ ] **CHK-011** `[MED]` CSV 三种失败模式不区分 (L62-74): `_csv_has_rows()` 对文件不存在/仅 header/读取异常均返回 False，调用方合并为 `has_valid_csv=False`，无法针对性修复。 — D2, confidence: 85%
- [ ] **CHK-012** `[MED]` 非整数 seed 参数导致未处理 ValueError (L270): `int(x)` 对 "abc" 等输入直接崩溃，无友好错误提示。 — D2+D5, confidence: 85%
- [ ] **CHK-013** `[MED]` 空 required/stress_run_names 产生虚假 complete=True (L268-269, L318): 空列表 → 空 expected → missing_run_names=[] → required_complete=True。无至少一个 run 的前置检查。 — D2+D5, confidence: 85%
- [ ] **CHK-014** `[MED]` --tasks 默认值与 run_experiments.py 不一致 (L252): check 脚本默认 "profile_latency,profile_memory"(2 任务)，run 脚本默认 4 任务。长实验检查时漏验 eval_ppl/eval_needle。 — D4, confidence: 86%
- [ ] **CHK-015** `[MED]` failure_type 域值枚举与 run_experiments.py _classify_failure() 不同步 (L94-108): 两处独立维护 failure_type 枚举，新增类型时易遗漏。 — D4, confidence: 84%
- [ ] **CHK-016** `[MED]` Traceback 检测大小写敏感 (L58): 使用精确字符串 "Traceback (most recent call last):" 匹配，小写变体漏检。OOM 检测用了 re.IGNORECASE 但 Traceback 没有。 — D7, confidence: 88%
- [ ] **CHK-017** `[MED]` 状态转移链 7 层嵌套无注释 (L147-166): 20 行 elif 链含复杂布尔表达式和多个不可达分支，无状态机文档。维护易引入逻辑错误。 — D7, confidence: 100%
- [ ] **CHK-018** `[MED]` _split_csv/_read_json/_read_text 与 run_experiments.py 重复定义 (L27-51): 3 个工具函数在两个脚本中独立实现，修 bug 需改两处。 — D7, confidence: 100%
- [ ] **CHK-019** `[MED]` L159 中 "skipped" 是不可达分支: has_csv=True + manifest_status="skipped" 总被 L153 先捕获（"skipped" 在 L154 的集合中）。死代码增加阅读困惑。 — D7, confidence: 95%
- [ ] **CHK-020** `[LOW]` 返回类型 Dict[str, Any] 无 TypedDict/dataclass 约束 (L168-181, L238-243): 字段名错误无法被静态检查捕获。 — D7, confidence: 80%

### EVL. 评测脚本 — `scripts/eval_*.py`

- [x] **EVL-001** `[CRIT]` eval_longbench.py _classification_accuracy() 语义变化未文档化 (L265) — fixed commit 52f4abf (CLASSIFICATION_MATCH_POLICY 常量 + docstring + CSV audit 字段)
- [x] **EVL-002** `[CRIT]` **RULER CWE 子任务在 1.5B *_long 配置下触发 max_position_embeddings 溢出** — fixed commit b7f4c36 (_effective_prompt_budget() 确保 prompt + gen ≤ max_model_len)
- [x] **EVL-008** `[HIGH]` **run_experiments.py 预检查遗漏 RULER CWE 的额外 max_new_tokens 开销** (L806-928) — fixed commit b7f4c36 (prelaunch 截断警告 + _effective_prompt_budget)
- [ ] **EVL-013** `[MED]` eval_ruler.py 截断策略 magic numbers (L562-570)
- [ ] **EVL-014** `[MED]` **eval_ruler.py case 循环无 per-case error handling** (L872-908)
- [ ] **EVL-017** `[MED]` eval_longbench.py 自实现 Rouge-L 可能与官方 LongBench 不一致 (L206-219)
- [ ] **EVL-023** `[LOW]` eval_longbench.py logger 定义位置：logger = logging.getLogger(__name__) 在 import 块中间（介于 traceback 和 from collections impor...
- [ ] **EVL-026** `[LOW]` eval_ruler.py summary row 聚合维度不一致 (L1008-1016): `overall_pass_rate` 基于 task-level macro average（4 tasks），而 `overall_f1` 和 `overall_contains` 基于 depth-level macro average（N depth ratios），同一 summary_row 内三个指标的聚合基底不同。主指标 `ruler_score` 不受影响（等于 task-level pass_rate）
- [ ] **EVL-027** `[LOW]` eval_ruler.py `_effective_prompt_budget()` 死存储 (L~550): 函数计算 `available` 后立即被后续逻辑覆盖，中间赋值未被使用。无功能影响但增加阅读困惑。 — D1 incremental, confidence: 85%
- [ ] **EVL-028** `[MED]` eval_ruler.py error case NaN 分数传播风险: per-case 异常处理将 score 设为 NaN，但下游聚合（mean over cases）中 NaN 参与计算导致整个 task 结果为 NaN。应使用 `nanmean` 或在聚合前过滤。 — D1 incremental, confidence: 88%

---

## Open Issues

### AGG. 聚合 — `scripts/aggregate_results.py`
- [ ] **AGG-002** `[HIGH]` RULER 聚合缺少子任务分拆 (aggregate_results.py
- [ ] **AGG-003** `[HIGH]` 多模型对比缺少分层表
- [ ] **AGG-007** `[MED]` LongBench 聚合同时包含 3 个近义指标 (aggregate_results.py
- [ ] **AGG-008** `[MED]` KIVI quant_bits 在 pairings 中未区分 INT8/INT4 (aggregate_results.py
- [ ] **AGG-009** `[MED]` kv_mode 显示顺序依赖默认排序 (aggregate_results.py
- [ ] **AGG-012** `[LOW]` Bootstrap seed 基于 SHA256 hash 的独立性
- [ ] **AGG-014** `[LOW]` Bootstrap CI 单样本情况返回 (value, value) 无警告 (L1059-1060)
- [ ] **AGG-015** `[LOW]` 精确枚举阈值 n=16 硬编码 (L1092-1107)
- [ ] **AGG-016** `[MED]` 显著性 pairings 遗漏 `("int4_baseline", "int4_ours")` (L2207-2212): INT8 有 baseline-vs-ours 配对，INT4 仅有 `("int4_fused", "int4_ours")`。若 Phase5v2 不含 int4_fused 运行，则 INT4 无任何显著性比较
- [ ] **AGG-017** `[MED]` `_export_per_model_layered_tables()` bare `except` 吞掉 CSV 读取错误 (aggregate_results.py): 空 `except:` 捕获所有异常（包括 CSV 格式损坏、权限错误），静默跳过该模型的表导出。应至少 `except Exception as e:` 并 log warning。 — D2 incremental, confidence: 90%
- [x] **AGG-018** `[HIGH]` ~~_add_ci95_columns z=1.96 → t 分位数~~ **FIXED** — 改用 _t_critical(df) 函数（scipy + fallback lookup table），n≤1 返回 NaN（同时修复 AGG-027）
- [x] **AGG-019** `[HIGH]` ~~sign-flip exact/MC 分支 p 值不一致~~ **FIXED** — exact 分支加 Phipson-Smyth +1 修正: p=(exceed+1)/(n_enum+1)，与 MC 分支一致
- [x] **AGG-020** `[HIGH]` ~~_read_csvs() bare except 静默跳过~~ **FIXED** — 改为 `except Exception as exc: logger.warning("Skipped unreadable CSV ...")`
- [ ] **AGG-021** `[HIGH]` _main_claims_32k_table 混合 outer/left merge 产生幽灵行或丢失数据 (aggregate_results.py:1467-1477): latency+memory 用 outer merge（可能产生 NaN 幽灵行），ppl/longbench/ruler 用 left merge（可能丢弃不在 latency 中的 kv_mode 数据）。无 merge 后行数 sanity check。 — D2 EXP rotation, confidence: 85%
- [ ] **AGG-022** `[HIGH]` _build_paired_metric_rows pivot_table aggfunc="mean" 静默折叠重复 seed 观测 (aggregate_results.py:1144-1153): 重复 (key, seed, kv_mode) 行被均值折叠，仅 print() 警告（非 logging）。折叠后 paired test 的独立性假设被违反，p-value 可能不可靠。 — D2 EXP rotation, confidence: 85%
- [x] **AGG-023** `[HIGH]` ~~relative_gain pairings 缺少 kivi_style~~ **FIXED** — 添加 ("kivi_style","int8_ours") 和 ("kivi_style","int8_baseline") 到 pairings 列表
- [x] **AGG-024** `[HIGH]` ~~relative_gain key_cols 不含 model_id~~ **FIXED** — 所有 7 个 _relative_gain_table 调用的 key_cols 增加 "model_id" 前缀
- [x] **AGG-025** `[HIGH]` ~~_main_claims_32k_table merge on kv_mode 笛卡尔积~~ **FIXED** — 动态 merge_keys 包含 model_id（当存在时），所有列列表和 merge/drop_duplicates 均使用 model_id
- [ ] **AGG-026** `[HIGH]` gain_pct 与 diff 基于不同样本量计算 (aggregate_results.py:1156-1190): baseline=0 时 gain_pct=NaN，dropna(subset=...) 不含 gain_pct 列所以 NaN 行保留。但 _significance_summary 对 gain_pct 做额外 dropna，导致 gain_pct_mean 基于 n-k 样本而 diff_mean 基于 n 样本，n_pairs 不匹配。 — D1/D5 EXP rotation, confidence: 85%
- [x] **AGG-027** `[MED]` ~~count=1 时 CI 半宽 0.0 → NaN~~ **FIXED** — AGG-018 修复中一并处理，ci_half.where(cnt > 1, np.nan) 替代原 0.0
- [ ] **AGG-028** `[MED]` _to_numeric errors="coerce" 将非数值静默转 NaN，无 warning (aggregate_results.py:107-111): 对所有指标列使用 `pd.to_numeric(errors="coerce")`，异常字符串（"N/A"、"err"、空串）变 NaN 后被 groupby 忽略。5-seed 小样本下丢失 1 个点显著影响结论。 — D2 EXP rotation, confidence: 90%
- [ ] **AGG-029** `[MED]` gain_pct_mean（跨 seed 配对差均值）vs gain_pct（聚合均值上的单点增益）定义不同 (generate_thesis_report.py:586 vs 356): significance_summary 用 gain_pct_mean，claim_validation 用 gain_pct。Jensen's inequality 下两者不等。同一 claim 在两个表中可能给出矛盾的 practical_pass。 — D4 EXP rotation, confidence: 88%
- [ ] **AGG-030** `[MED]` _main_claims_32k_table latency 或 memory 为空即返回完全空表 (aggregate_results.py:1464-1467): 若 latency 数据缺失，即使 needle/ppl/longbench/ruler 完整，main claims 表也为空。无 warning。 — D2 EXP rotation, confidence: 90%
- [ ] **AGG-031** `[MED]` sign-flip 双尾检验 + 方向一致性检查 = 事实上 2 倍保守的单尾检验 (aggregate_results.py:1089): sign-flip p 值基于 |mean|（双尾），但 claim 验证要求 significant_q AND favors_challenger（单侧判据）。真正的单尾 p 应为 p_two/2。n=5 下可能导致本应显著的 claim 被误判。 — D1 EXP rotation, confidence: 80%
- [ ] **AGG-032** `[MED]` main() 函数 955 行含 7 次相同 read→numeric→seed→strict→agg→ci→save 模式 (aggregate_results.py:1539-2493): 无法单独测试、修改任一 benchmark 聚合逻辑需在巨大函数中导航。建议按 benchmark 拆分为独立函数。 — D7 EXP rotation, confidence: 98%

### CAL. 校准模块 — `scripts/calibrate_behavior.py`
- [ ] **CAL-006** `[HIGH]` trial 排名受 loss 尺度影响 (L780-791)
- [ ] **CAL-007** `[HIGH]` 默认校准路径与 generate_loop 不匹配 (calibrate_behavior.py
- [ ] **CAL-008** `[HIGH]` 加载校准文件时无 loss_function 字段校验 (generate_loop.py
- [ ] **CAL-009** `[HIGH]` calibrate_behavior.py MSE clamping 移除导致旧校准产物不可复现
- [ ] **CAL-012** `[MED]` MSE loss 语义未文档化 (L6, L234-239)
- [ ] **CAL-013** `[MED]` inv_tau shape 未在加载时验证 (generate_loop.py
- [ ] **CAL-014** `[MED]` MSE 与 KL loss 量级差异影响搜索行为 (calibrate_behavior.py
- [ ] **CAL-015** `[MED]` evaluate_quant_candidate 不使用 inv_tau (calibrate_behavior.py
- [ ] **CAL-016** `[MED]` calibrate_behavior.py MSE clamping 语义偏差：MSE 路径对 p_ref/p_quant 执行 clamp(min=eps) 后再计算差的平方。对 MSE 而言 clamp 不防 NaN（MSE 不含...
- [ ] **CAL-017** `[LOW]` loss_accum NaN 无检测 (calibrate_behavior.py

### CFG. 配置 — `configs/`
- [ ] **CFG-007** `[MED]` final_emnlp2026_v1.yaml LLaMA 本地路径硬编码
- [ ] **CFG-008** `[MED]` 7B/8B 长上下文仅 3 条 vs 1.5B 的 18 条
- [ ] **CFG-009** `[MED]` 1.5B 校准文件命名不一致 (kv_calib_kl_selected_v3_quick.json vs 7B/8B 的 kv_calib_kl_qwen25_7b_int8.json)
- [ ] **CFG-010** `[MED]` 消融 A-2 (MSE) 使用 use_attn_temperature
- [ ] **CFG-011** `[MED]` 消融 D 节缺少 dynamic scales 变体
- [ ] **CFG-012** `[MED]` 所有消融仅 seq_len=4096
- [ ] **CFG-013** `[MED]` 消融 C 节 (group_size sweep) 使用同一个 calib_file
- [ ] **CFG-017** `[LOW]` 1.5B 配置头部注释缺少 kivi_style kv_mode 和 kivi_asymmetric calib_strategy
- [ ] **CFG-018** `[LOW]` 消融 A-1/B-1/C-1 是完全相同的 run

### ENG. 引擎模块 — `src/engine/`
- [ ] **ENG-001** `[HIGH]` patch_model.py 移除 kv_heads 默认推理 (L100-108)
- [ ] **ENG-003** `[HIGH]` decode 阶段 KIVI 走 dequant→re-quant 路径 (L635-678)
- [ ] **ENG-004** `[HIGH]` KIVI 模式静默忽略参数 (L412-486, L563)
- [ ] **ENG-005** `[MED]` generate_loop.py batch>1 填充检查移除
- [ ] **ENG-006** `[MED]` KIVI kv_mode 未校验 quant_bits∈{4,8} (L294-310)
- [ ] **ENG-007** `[MED]` KIVI decode 路径 dequant→requant 精度累积（已知 D2 但补充细节）
- [ ] **ENG-008** `[MED]` Batch 约束重复校验 (L344-361)
- [ ] **ENG-009** `[MED]` kivi_style_cache.py V scale/zp 缓冲区 dtype 隐性转换 (L140-149, L240-241)
- [ ] **ENG-010** `[MED]` patch_model.py kv_heads 推断失败静默降级 (L473-477)
- [ ] **ENG-011** `[MED]` patch_model.py KIVI 缓存若被错误路由到 fused forward (L556-567)
- [ ] **ENG-012** `[LOW]` docstring 未说明 KIVI 模式行为 (L258-292)
- [ ] **ENG-013** `[LOW]` KIVI docstring 缺失 (L288-291)
- [ ] **ENG-014** `[LOW]` generate_loop.py kivi_style 接受但静默忽略 calib_file/use_attn_temperature/adaptive_static_scales 参数 (L412-485, L563-566): 已...
- [ ] **ENG-015** `[HIGH]` Triton kernel 硬编码 fp16 输出与 bf16 输入 dtype 不匹配 (triton_decode_attn_int8.py:285): kernel `tl.store` 强制转 `tl.float16`，但 wrapper 分配 `torch.empty_like(q)` 继承 q 的 dtype。若模型以 bf16 运行，位模式解释错误产生静默数值偏差。当前所有脚本用 fp16 不触发。 — D1, confidence: 92%
- [ ] **ENG-016** `[HIGH]` Triton kernel 在 context_lens=0 时 softmax 除零产生 NaN (triton_decode_attn_int8.py:281): online softmax `l_i=0.0`，无 token 时 `acc/l_i = 0/0 = NaN`；torch_ref 正确返回零向量。两实现边界行为不一致。 — D1, confidence: 95%
- [ ] **ENG-017** `[HIGH]` apply_int8_fused_patch layers=None 后仍硬访问 model.model.layers[0] (patch_model.py:720-755): try 块吞异常设 layers=None，但 L755 在 try 外再次访问同一属性，产生不可理解的 AttributeError 而非清晰的 ValueError。 — D2+D5, confidence: 95%
- [ ] **ENG-018** `[MED]` max_new_tokens=0 时仍生成 1 个 token (generate_loop.py:639,655): prefill 后无条件追加第一个 argmax token，decode loop `range(-1)` 不执行，`gen_len=1` 返回。语义违反 "生成 0 个新 token" 约定。 — D5, confidence: 95%
- [ ] **ENG-019** `[MED]` inv_tau[layer_idx] 无越界校验 (patch_model.py:559): fused decode 直接索引无边界检查，prefill 路径有检查。校准层数不匹配时报无上下文 IndexError。 — D5, confidence: 92%
- [ ] **ENG-020** `[MED]` batch_size=0 / prompt_len=0 未校验 (generate_loop.py:367-374): `input_ids.shape=[0,S]` 或 `[B,0]` 导致下游 IndexError（logits[:,-1,:] 在空维度索引）或未定义行为。 — D5, confidence: 95%
- [ ] **ENG-021** `[MED]` static_k_scale/v_scale 以 fp16 加载，小 scale 精度损失 (generate_loop.py:480-482): 低活跃度 head 的 scale 接近 fp16 subnormal 范围仅 ~3 位有效数字。inv_tau 正确用 float32。 — D1, confidence: 85%
- [ ] **ENG-022** `[MED]` prefill temperature hooks 在 model 结构不标准时静默返回空列表 (generate_loop.py:172-175): 校准文件已加载但 hooks 未注册无 warning，用户以为使用 ours 方法实际无 temperature 校正。 — D2, confidence: 90%
- [ ] **ENG-023** `[MED]` fused 路径静默忽略 output_attentions=True (patch_model.py:778,808-818): fused path 返回 None 代替 attention weights，可解释性工具得到 None 无报错。 — D2+D4, confidence: 85%
- [ ] **ENG-024** `[MED]` _maybe_dump_fused_decode 类型签名声明 torch.Tensor 但实际可接收 None (patch_model.py:308-309,677-689): `cache_kind=int4` + dump 未启用时传入 None。dump 启用时会 crash。应改为 Optional。 — D4+D2, confidence: 92%
- [ ] **ENG-025** `[MED]` _q_norm_hook 当 H==S 时布局检测歧义 (generate_loop.py:212-231): `output.shape[1]==H` 和 `shape[2]==H` 都为真时总进入第一分支。若实际 [B,S,H,D] 布局则 inv_tau 应用错误维度。 — D4, confidence: 82%
- [ ] **ENG-026** `[MED]` calib_group_k 使用 `or` 运算符，合法值 0 被静默替换 (generate_loop.py:476-477): JSON 中 `"group_size_k": 0` 被 Python `or` 视为 falsy 丢弃。 — D2, confidence: 82%
- [ ] **ENG-027** `[MED]` past_key_values=None 时静默跳过 KV 缓存填充 (generate_loop.py:614-625): decode 阶段使用空缓存，fused 模式 context_lens=0 可能产生 NaN。 — D2, confidence: 85%
- [ ] **ENG-028** `[MED]` INT4 动态量化 scale 强制转 fp16 与 INT8 路径不一致 (quant/int4_basic.py:131): INT8 用 `abs_max.to(tensor.dtype)` 保留输入精度，INT4 硬转 `torch.float16`。 — D1, confidence: 88%
- [ ] **ENG-029** `[MED]` torch_ref dequant 在 fp16 vs Triton 在 fp32，dump 对比精度差异 (patch_model.py:278-285): 两路径 ~1e-3 差异影响 max_abs_diff 诊断准确性。 — D1, confidence: 82%
- [ ] **ENG-030** `[MED]` generate_from_ids 函数过长 535 行 (generate_loop.py:258-793): 8+ 职责耦合在一个函数中，难以单独测试和维护。 — D7, confidence: 95%
- [ ] **ENG-031** `[MED]` kv_mode 集合常量重复硬编码 4 次 (generate_loop.py:398,668,684,701): `["int8_fused","int8_ours","int4_fused","int4_ours","int4_ours_mixed"]` 应提取为模块级 frozenset。 — D7, confidence: 95%
- [ ] **ENG-032** `[LOW]` _seq_len 仅在 layer_id==0 时更新 (int8_cache.py:376-377, int4_cache.py:419-420): 非顺序 append 时 get_seq_len 返回过时值。正常 generate_loop 总按 layer 0..N-1 顺序。 — D1, confidence: 85%
- [ ] **ENG-033** `[LOW]` INT8CacheWrapperContainer 每 decode step 重新构造 (generate_loop.py:668-671): 每步创建 num_layers 个 INT8CacheWrapper 对象，28-80 层模型生成 512 token 累计 14k-40k 临时对象。 — D4, confidence: 95%
- [ ] **ENG-034** `[LOW]` attention_mask decode 阶段 O(N^2) 内存分配 (generate_loop.py:724-732): fused path `del attention_mask` 但 generate_loop 仍每步分配增长。长序列累计 ~400MB 无用分配。 — D5, confidence: 88%
- [ ] **ENG-035** `[LOW]` except TypeError 过于宽泛可能吞掉内核内部错误 (patch_model.py:621-631,647-659): Triton kernel 内部 dtype/shape TypeError 被静默回退到无 debug_stats 调用。 — D7, confidence: 82%

### EXP. 导出/报告 — `scripts/export_*.py`
- [ ] **EXP-001** `[HIGH]` C11 跨模型验证逻辑缺陷 (generate_thesis_report.py
- [ ] **EXP-002** `[MED]` LongBench 表缺少任务指标组成说明 (export_tables_latex.py
- [ ] **EXP-003** `[MED]` RULER 表仅显示整体 pass rate (export_tables_latex.py
- [ ] **EXP-004** `[MED]` 多模型表格缺少 per-model 分页
- [ ] **EXP-005** `[MED]` C9 对指标名正确 (generate_thesis_report.py
- [ ] **EXP-006** `[MED]` generate_thesis_report.py C11 "cross-model robustness" claim 无 model_id 过滤
- [ ] **EXP-007** `[LOW]` KIVI 在 KV_MODE_ORDER 和 KV_MODE_DISPLAY 中已完整映射 (export_tables_latex.py
- [ ] **EXP-008** `[LOW]` 所有 3 配置文件的 KIVI 吞吐量仅包含 INT8（无 INT4 KIVI 吞吐量）— 可能遗漏 KIVI INT4 batch scaling 数据
- [ ] **EXP-009** `[MED]` generate_thesis_report.py 跨模型 claim `gains.min()` 与 `all(practical_pass)` 语义不匹配: `gains.min()` 取数值最小值，但 `practical_pass` 基于阈值判断。当 min gain 远大于阈值但某模型的 practical_pass 因其他原因（如缺数据）为 False 时，两个信号矛盾。 — D1 incremental, confidence: 85%
- [ ] **EXP-010** `[HIGH]` generate_thesis_report.py 单模型路径缺少 `target_model_id` 字段: 当 `--model_ids` 只传一个模型时，`_evaluate_claim_row()` 返回的 dict 不含 `target_model_id` key，但下游 DataFrame 构建假设该列存在，导致 KeyError。跨模型路径正常。 — D1 incremental, confidence: 92%
- [ ] **EXP-011** `[LOW]` generate_thesis_report.py NaN `gain_pct` 被判定为 FAIL 而非 INCONCLUSIVE: 当 baseline 为 0 时 `gain_pct = NaN`，当前逻辑将 NaN 视为未通过阈值 → FAIL。应归类为 INCONCLUSIVE 并在报告中标注。 — D2 incremental, confidence: 85%
- [ ] **EXP-012** `[LOW]` generate_thesis_report.py 单模型 vs 跨模型 claim schema 不一致 (27 vs 29 keys): 单模型 claim dict 缺少 `min_gain_model` 和 `max_degradation_model` 字段，跨模型有。下游若以跨模型 schema 为模板构建 DataFrame，单模型行会出 NaN 列。 — D4 incremental, confidence: 82%
- [ ] **EXP-013** `[HIGH]` export_tables_latex.py `_read_csv()` bare except 返回空 DataFrame，全部下游 export 静默跳过: L66-70 `except: return pd.DataFrame()` 吞掉所有异常（包括 schema 错误、编码错误），8 个 export 函数均依赖此函数，文件损坏或格式变更时无任何警告，产出空 LaTeX 表格。 — D2 EXP rotation, confidence: 95%
- [ ] **EXP-014** `[MED]` export_tables_latex.py `_pivot_metric()` groupby().mean() 静默平均多模型行: L91-126 当输入包含多个 model_id 的数据时，pivot 前的 groupby 会将不同模型的指标平均，产出的 LaTeX 表格数值为多模型混合平均值而非单模型值。当前无 model_id 过滤逻辑。 — D4 EXP rotation, confidence: 90%
- [ ] **EXP-015** `[MED]` export_tables_latex.py LaTeX `--label_prefix` 注入风险: `label_prefix` 参数直接拼入 `\label{}` 命令（L140 等），含特殊字符（如 `}`, `\`）时会破坏 LaTeX 编译。无输入校验或转义。 — D3 EXP rotation, confidence: 85%
- [ ] **EXP-016** `[MED]` export_tables_latex.py export_latency / export_memory 近乎重复的 DRY 违反: L159-225 两函数结构几乎相同（仅 metric_col 和标题不同），约 60 行重复代码。应提取公共 `_export_profile_table()` 函数。 — D7 EXP rotation, confidence: 88%

### KVC. KV Cache — `src/cache/`
- [ ] **KVC-002** `[HIGH]` ~~KIVI INT4 未实现 bit-packing~~ **事实已变更**：当前代码已实现 bit-packing (L75 `bit_packed=True` for INT4, L300/306 `pack_int4`, L344-345/354-355 `unpack_int4`)。但远端测试显示 decode 路径有维度不匹配 bug（2 tests failed, iteration.md 2026-02-23 17:29）。建议降级为 MED 并改描述为"KIVI INT4 bit-pack decode 维度不匹配"
- [ ] **KVC-005** `[MED]` kivi_style_cache.py clear() 仅重置 K scale/zp 未显式清零 V scale/zp
- [ ] **KVC-009** `[MED]` get_memory_mb() 注释误导 (L307)
- [ ] **KVC-010** `[MED]` INT4 量化精度 edge case 未覆盖
- [ ] **KVC-013** `[LOW]` kivi_style_cache.py INT4 head_dim 偶数约束仅在 append 时检查
- [ ] **KVC-014** `[LOW]` _seq_len 仅在 layer_id=0 时更新 (L244-245)
- [ ] **KVC-015** `[LOW]` 无 batch_size=0 校验 (L204)
- [ ] **KVC-016** `[LOW]` INT4 vs INT8 行为切换逻辑正确

### PRF. 性能分析 — `scripts/profile_*.py`
- [ ] **PRF-002** `[MED]` quant_bits CSV 推断 fallback 为 16 (eval_ppl.py
- [ ] **PRF-003** `[MED]` profile_latency.py run 间无显式 CUDA sync (profile_latency.py
- [ ] **PRF-004** `[MED]` kivi_style decode_attn_impl 参数被静默忽略 (profile_latency.py
- [ ] **PRF-005** `[MED]` profile_memory.py GPU 峰值来源判断逻辑 (L383-385)
- [ ] **PRF-009** `[LOW]` calib_file 对 kivi_style 静默无操作 (eval_ppl.py
- [ ] **PRF-010** `[LOW]` output 属性可靠性 (L348-352)

### QNT. 量化模块 — `src/quant/`
- [ ] **QNT-003** `[MED]` 全 eval 脚本 _resolve_quant_bits() 重复定义（6 处相同代码，违反 DRY）
- [ ] **QNT-004** `[MED]` float16 输入精度损失 (L58-59)
- [ ] **QNT-005** `[MED]` _normalize_static_scale 3D case 实现错误
- [ ] **QNT-006** `[MED]` dequantize_symmetric_int8 多路径判断脆弱
- [ ] **QNT-007** `[MED]` 缺少 INT8 离群值测试
- [ ] **QNT-008** `[LOW]` dequantize 函数无输入类型校验 (L74-95)
- [ ] **QNT-009** `[LOW]` __init__.py.__all__ 不完整
- [ ] **QNT-010** `[LOW]` 核心公式验证通过

### RUN. 实验运行 — `scripts/run_experiments.py`
- [ ] **RUN-002** `[HIGH]` kivi_style 的 calib_strategy 默认值继承陷阱 (L880-881, L1015-1016)
- [ ] **RUN-003** `[MED]` skip_completed_success 状态不一致 (L1134 vs L1147)
- [ ] **RUN-004** `[MED]` subprocess.run 无异常捕获 (L1174-1179)
- [ ] **RUN-005** `[MED]` kv_mode 无效值静默跳过 (L850-862)
- [ ] **RUN-006** `[MED]` kivi_style decode_attn_impl 无强制验证 (L882-884, L1033-1034)
- [ ] **RUN-007** `[MED]` 无条件传递 quant 参数给所有 kv_mode (L987-998)
- [ ] **RUN-008** `[MED]` skip 时重复标记成功 (L1130-1138)
- [ ] **RUN-009** `[MED]` 消融实验仅跑 PPL+Needle，缺少 LongBench
- [ ] **RUN-010** `[LOW]` YAML 配置无 matrix 非空校验 (L725-794)
- [ ] **RUN-011** `[LOW]` append 模式 manifest 元数据被覆盖 (L252-265)
- [ ] **RUN-012** `[LOW]` append_history 未记录 kv_mode/quant_bits 变化 (L272-278)
- [ ] **RUN-013** `[LOW]` manifest history 仅保留最近 20 条 (L334)
- [ ] **RUN-014** `[LOW]` 消融 output dir 命名含双重 seed
- [ ] **RUN-015** `[MED]` repair_phase5v2_ruler_light.py JSON parse 异常静默跳过: `json.load()` 失败时 `continue` 跳过该文件无 warning，可能丢失需修复的数据。应 log 文件名和错误原因。 — D2 incremental, confidence: 88%
- [ ] **RUN-016** `[MED]` repair_phase5v2_ruler_light.py `--execute` 模式首次失败即中止: 执行修复命令序列时，任一命令失败立即退出，剩余修复命令丢失。应收集所有失败后统一报告。 — D2 incremental, confidence: 85%
- [ ] **RUN-017** `[LOW]` run_experiments.py RULER 截断 warning 仅 print 未写入 manifest: `_compute_ruler_truncation_warning()` 结果只打印到 stdout，不记录到 `run_manifest.json`。批量实验中 warning 混入大量日志难以追溯。 — D2 incremental, confidence: 82%

### TST. 测试覆盖 — `tests/`
- [ ] **TST-003** `[HIGH]` calibrate_behavior.py 完全无单元测试
- [ ] **TST-004** `[HIGH]` KIVI + asymmetric_quant 端到端集成测试缺失
- [ ] **TST-005** `[HIGH]` B1 修复验证不完整
- [ ] **TST-006** `[HIGH]` K decode 量化误差无测试
- [ ] **TST-007** `[MED]` per-channel K 和 per-token V axis 独立性验证缺失
- [ ] **TST-008** `[MED]` Bootstrap CI n=1 和 n=2 边界测试缺失
- [ ] **TST-009** `[MED]` Permutation test NaN 处理测试缺失
- [ ] **TST-010** `[MED]` BH-FDR 单调性验证缺失
- [ ] **TST-011** `[MED]` eval_longbench.py / eval_ruler.py 完全无单元测试
- [ ] **TST-012** `[MED]` 缺少 float16 输入测试
- [ ] **TST-013** `[MED]` 缺少 per-channel/per-token 轴语义验证
- [ ] **TST-014** `[MED]` C1/C2 修复缺少边界值测试
- [ ] **TST-015** `[MED]` 统计测试缺少混合符号 sign-flip 场景
- [ ] **TST-016** `[LOW]` INT4 vs INT8 误差比例测试缺失
- [ ] **TST-017** `[LOW]` 缺少单 token、batch=0、head_dim=1 等极端边界测试
- [ ] **TST-018** `[LOW]` 缺少多轮 clear→append 循环测试（生产中常见的 batch 间重用 cache 场景）
- [ ] **TST-019** `[HIGH]` review_tool.py 零测试覆盖 — 无 `tests/test_review_tool.py` (scripts/review_tool.py): 5 个子命令、2 个正则、文件写入逻辑均无自动化测试，任何重构无安全网 — gap_score: 9/10, confidence: 100%
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
- [ ] **TST-030** `[HIGH]` check_run_completeness.py 关键状态路径未测试: _check_task_state() 返回 8 种状态中 task_artifacts_missing、running、mixed_csv_non_success、missing 4 种无直接测试用例。当前仅覆盖 success、oom、csv_invalid、traceback 路径。 — D6 CHK rotation, confidence: 95%
- [ ] **TST-031** `[HIGH]` eval_longbench/eval_ruler 工件检测完全无测试 (check_run_completeness.py:85-90): `_has_task_level_artifacts()` 中 longbench 检查 task_summary CSV、ruler 需同时检查 task_summary + depth_summary，两条分支零测试。 — D6 CHK rotation, confidence: 100%
- [ ] **TST-032** `[MED]` check_run_completeness.py 8 个工具函数无独立单元测试: _split_csv, _read_json, _read_text, _is_oom_from_log, _is_traceback_from_log, _csv_has_rows, _has_task_level_artifacts, _expected_run_ids 均无单元测试，仅通过集成测试间接覆盖。 — D6 CHK rotation, confidence: 90%
- [ ] **TST-033** `[MED]` check_run_completeness.py 参数组合和错误路径测试不足: allow_oom_completion=False 影响、runs_dir 不存在 exit(2)、logs_dir=None 完整路径、allow_stress_unexpected_failures 标志均无测试。 — D6 CHK rotation, confidence: 88%
- [ ] **TST-034** `[HIGH]` export_tables_latex.py 零测试覆盖: 510 行代码、8 个 export 函数、2 个 helper 函数，tests/ 下无任何对应测试文件。_read_csv bare except、_pivot_metric 多模型平均、LaTeX 特殊字符转义等问题均无回归防护。 — D6 EXP rotation, confidence: 98%
- [ ] **TST-035** `[HIGH]` aggregate_results.py 统计函数测试覆盖不足: `_stable_random_seed`、`_cohens_dz`、`_relative_gain_table`、`_build_paired_metric_rows`、`_paired_signflip_pvalue` 等核心统计函数缺少针对性单元测试。现有 test_aggregate_results_stats.py 仅覆盖部分路径。 — D6 EXP rotation, confidence: 92%
- [ ] **TST-036** `[HIGH]` aggregate_results.py main() 管线无端到端测试: main() 函数 955 行，串联 7+ 子流程（read→CI→paired→claims→latex），无任何 e2e 测试验证从 CSV 输入到最终 tables/plots 产出的完整路径。配置变更可能静默破坏输出。 — D6 EXP rotation, confidence: 95%

### RVW. 审查工具与配置 — `scripts/review_tool.py`, `.claude/agents/review-*.md`
- [ ] **RVW-001** `[HIGH]` review_tool.py phase-gate 仅检查 CRIT，遗漏 HIGH (L120): `cmd_phase_gate()` 仅过滤 `severity == "CRIT"`，按 CLAUDE.md §4.5 闸门规则，HIGH 也应阻塞（至少提示）。可能导致存在 HIGH 阻塞项时误判为 CLEAR
- [ ] **RVW-002** `[HIGH]` review_tool.py cmd_add() 文件写入非原子性 (L230-231): `open(path, "w")` 直接覆写，若进程中途崩溃会导致 review_tracker.md 被截断或损坏。应使用 tmpfile + rename 原子写入
- [ ] **RVW-003** `[MED]` review_tool.py 解析不匹配行静默跳过 (L42-87): 任何不符合 ISSUE_RE 格式的 issue 行会被完全忽略，无警告日志。正则已从 `\w+` 改为 `[A-Z]+` 部分改善，但核心静默跳过问题仍存在
- [ ] **RVW-004** `[MED]` review_tool.py _update_summary() 格式假设过强 + 双写竞争 (L268-287): `summary_replaced` 标志仅在 "Last updated:" 行后触发，若 header 行顺序变化或新增行则部分 summary 不更新。另外 `cmd_add` 先 write content 再调 `_update_summary`（二次 open+write），后者可能只更新部分摘要行却无返回值通知调用方
- [x] **RVW-005** `[MED]` reviewer.md L5 描述引用 "iteration.md TODO Backlog" 应为 "review_tracker.md" (.claude/agents/reviewer.md L5) — fixed
- [x] **RVW-006** `[MED]` reviewer.md YAML 权限与 body 指令矛盾 (.claude/agents/reviewer.md L8 vs L11,L16) — fixed: body 改为"严禁修改源代码（src/、scripts/、tests/、configs/）"，写入权限标注"仅限 review_tracker.md + iteration.md"
- [x] **RVW-007** `[MED]` start_agents.sh L32 developer 启动 prompt 引用 "TODO Backlog" 而非 review_tracker.md (scripts/start_agents.sh L32): 与 developer.md L22 "读取 review_tracker.md" 冲突，可能导致 developer agent 优先遵循启动 prompt 到 iteration.md 而非 review_tracker.md 查找任务 — fixed (prompt 改为 "读 review_tracker.md + iteration.md → 按优先级矩阵领取任务")
- [x] **RVW-008** `[MED]` start_agents.sh L33 reviewer 启动 prompt 未提及 review_tracker.md (scripts/start_agents.sh L33): reviewer.md L21 要求先读 review_tracker.md，但启动 prompt 仅说"读 iteration.md" — fixed commit 3ba38e3 (prompt 已更新为 "读 review_tracker.md → 进入持续监控循环")
- [ ] **RVW-009** `[LOW]` settings.json Stop hook "BLOCKED" 字符串匹配过宽 (.claude/settings.json L21): iteration.md 历史条目中若包含 "BLOCKED" 一词（如引用 Phase Gate 状态），会误触发退出许可，应匹配更精确的标记如 "auto-iterate-blocked"
- [x] **RVW-010** `[LOW]` start_agents.sh 硬编码绝对路径 (scripts/start_agents.sh L5): `PROJECT_DIR="/Users/chenzilang/..."` 不可移植，建议使用 `$(cd "$(dirname "$0")/.." && pwd)` — fixed commit 3ba38e3
- [x] **RVW-011** `[HIGH]` Phase Blocker CHK-001 已修复但未标记 — 独立审查确认 `_check_task_state()` OOM 检查已移至 if 链首位 (check_run_completeness.py L147)，匹配 Codex PR 修复 (merge 1aa5c95)。Phase Gate 状态过期，建议 developer 验证并标记 fixed 以解除 blocker — fixed (supervisor 已验证并标记 CHK-001)
- [ ] **RVW-012** `[MED]` 多处 kv_mode 列表遗漏 int4_fused: developer.md L91 和 CLAUDE.md §9 固定决策均缺少 `int4_fused`（仅列 6 项），而 review-numerical.md L122 和代码 generate_loop.py 均包含 `int4_fused`（7 项）。权威文件与实际代码不一致
- [ ] **RVW-013** `[LOW]` Resolved KVC-003 前提失效: KVC-003 "论文须注明 KIVI INT4 无 bit-packing" 已标记 fixed，但当前代码已实现 bit-packing (L75, L300)。论文描述应更新为"KIVI INT4 使用 bit-packing"。此项记录前提变更，非新 bug
- [ ] **RVW-014** `[HIGH]` cmd_add() 在 `## Open Issues` 节缺失时静默无操作 (scripts/review_tool.py L219-235): 当 `re.search(r'^## Open Issues', content)` 返回 None 时，整个写入分支被跳过，函数仍输出 "Added: ..." 并返回 0，issue 实际未写入 — confidence: 97%
- [x] **RVW-015** `[HIGH]` start_agents.sh L28 `--agent reviewer` 引用已删除的 agent (scripts/start_agents.sh L16,L28): reviewer.md 已被 review-coord.md + 7 专项 Agent 替代，执行该脚本会以不存在的 reviewer agent 启动第三个 pane，审查子系统完全无法工作 — fixed commit 3ba38e3
- [ ] **RVW-016** `[MED]` cmd_add() 无重复 ID 检查 (scripts/review_tool.py L192-236): 重复执行相同 `--id` 会产生重复条目，cmd_stats 计数虚高 — confidence: 100%
- [ ] **RVW-017** `[MED]` parse_tracker rest.replace(" — fixed", "") 全局替换可损坏 title (scripts/review_tool.py L63): 若 issue title 本身包含 " — fixed" 子串（如 "partially — fixed workaround"），该子串也会被静默删除 — confidence: 80%
- [ ] **RVW-018** `[MED]` 无效 --sev 参数静默返回空结果 (scripts/review_tool.py L137-139): 传入未知 severity（如 `--sev foo`）时 fallback 为 `"FOO"`，过滤结果为空列表，exit code 仍为 0，用户无法区分"真无结果"与"参数拼写错误" — confidence: 88%
- [ ] **RVW-019** `[MED]` supervisor.md 迭代上限与 auto-iterate SKILL.md 不一致 (supervisor.md L66,L104 vs SKILL.md L85,L95): supervisor.md 声明默认 5 轮，SKILL.md L85 写 8 轮、L95 写 5 轮，SKILL.md 内部亦矛盾 — confidence: 95%
- [ ] **RVW-020** `[MED]` CLAUDE.md §12 遗漏 review-coord 中间层 (CLAUDE.md L251): 描述为"由 Supervisor 并行调度"7 个审查 Agent，但实际架构是 Supervisor → review-coord → 7 Agent，遗漏了 coordinator 层 — confidence: 90%

---

## Resolved

<details>
<summary>64 fixed + 2 false_positive (click to expand)</summary>

### AGG. 聚合
- [x] **AGG-001** `[CRIT]` kivi_style 完全缺失显著性配对 — fixed commit 03ed4a0
- [x] **AGG-004** `[HIGH]` longbench_official_macro 未被聚合 — fixed commit 03ed4a0
- [x] **AGG-005** `[HIGH]` 显著性分析缺失 model_id/hardware 分组 — fixed commit 03ed4a0
- [x] **AGG-006** `[HIGH]` RULER 深度分析缺失 model_id — fixed commit 03ed4a0
- [x] **AGG-010** `[MED]` kv_mode 使用字母序排序而非语义顺序 (L552, L585, L648, L1322) — fixed
- [x] **AGG-011** `[MED]` 显著性配对数据可能被 aggfunc="mean" 静默平均 (L998) — fixed
- [x] **AGG-013** `[LOW]` LongBench 图 y 轴标签与新口径不一致 — fixed

### CAL. 校准模块
- [x] **CAL-001** `[CRIT]` MSE loss 维度语义错误 (L199-200) — fixed commit 20095fb
- [x] **CAL-002** `[CRIT]` MSE loss 全局 mean 无维度 (L302) — fixed commit 20095fb
- [x] **CAL-003** `[CRIT]` calibrate_behavior.py --calib_out None fallback — fixed
- [x] **CAL-004** `[HIGH]` loss_accum 未除以样本数 (L177-206) — fixed commit 20095fb
- [x] **CAL-005** `[HIGH]` MSE 无数值安全 clamp (L199) — fixed commit 20095fb
- [x] **CAL-010** `[MED]` 默认输出文件名硬编码为 kl.json — fixed commit 20095fb
- [x] **CAL-011** `[MED]` select_best_trial() 无 key 存在性校验 — fixed commit 20095fb
- [x] **CAL-018** `[LOW]` search_trials.csv 已按 loss_function 区分文件名 (calibrate_behavior.py — false_positive

### CFG. 配置
- [x] **CFG-001** `[HIGH]` 1.5B 配置完全缺失 KIVI-style 条目 — fixed commit f07422d
- [x] **CFG-002** `[HIGH]` 7B/8B 配置完全缺失吞吐量 batch scaling 条目 — fixed commit f07422d
- [x] **CFG-003** `[HIGH]` 7B/8B 配置缺失 INT4 长上下文运行 — fixed commit f07422d
- [x] **CFG-004** `[HIGH]` 消融 A-3 decode_attn_impl 混淆因子 — fixed commit f07422d
- [x] **CFG-005** `[HIGH]` 消融 A 节缺少 KIVI-style — fixed commit f07422d
- [x] **CFG-006** `[HIGH]` 7B/8B 校准产物尚未生成（Phase 2 依赖，非 bug） — false_positive
- [x] **CFG-014** `[MED]` ablation_dimensions.scale_strategy 仅列 [static, adaptive]（L77）— 计划中为 "static vs adaptive vs dynamic" 三方，与消融配置 D 节同一缺失 — fixed
- [x] **CFG-015** `[MED]` LLaMA-3.1-8B 使用本地路径而非 HF ID — fixed
- [x] **CFG-016** `[MED]` Claims C9-C11 定义不够精确 — fixed
- [x] **CFG-019** `[LOW]` benchmarks 仅列 4 个质量评测（L67-71）— 未包含 latency/memory/throughput 系统性能 benchmark，虽然这些是独立维度但在 meta-config 中应有提及 — fixed
- [x] **CFG-020** `[LOW]` models[0].calibration_artifacts 列出了尚不存在的 MSE 产物（int8_mse/int4_mse，L38-39）— MSE 校准实现有已知 bug，这些产物暂不可用 — fixed
- [x] **CFG-021** `[LOW]` meta-config 无执行工作流说明 — fixed

### ENG. 引擎模块
- [x] **ENG-002** `[HIGH]` generate() 函数缺少 quant_bits 参数 — fixed commit 20095fb

### EVL. 评测脚本
- [x] **EVL-003** `[CRIT]` export_tables_latex.py KV_MODE_DISPLAY 缺 kivi_style — fixed commit 8bf9414
- [x] **EVL-004** `[CRIT]` export_tables_latex.py KV_MODE_ORDER 缺 kivi_style — fixed commit 8bf9414
- [x] **EVL-005** `[CRIT]` MK-NIAH hits_exact 计数器死代码 (L172-174) — fixed
- [x] **EVL-006** `[CRIT]` VT 多链评分仅评价第一条链 (L216, L442) — fixed
- [x] **EVL-007** `[CRIT]` 上下文截断从右侧保留破坏 RULER 语义 (L546-554) — fixed
- [x] **EVL-009** `[HIGH]` eval_longbench.py 引用未定义 logger — fixed commit 20095fb
- [x] **EVL-010** `[HIGH]` generate_thesis_report.py 缺少 KIVI claims — fixed commit 8bf9414
- [x] **EVL-011** `[HIGH]` kivi_style quant_bits 推断为 16 (L985) — fixed
- [x] **EVL-012** `[HIGH]` 分类准确率子串匹配过于宽松 (L252) — fixed
- [x] **EVL-015** `[MED]` 所有 eval 脚本 quant_bits fallback 将 KIVI 记录为 16 (eval_ppl L878 / eval_needle L467 / eval_longbench L833 / eval_ruler L98... — fixed
- [x] **EVL-016** `[MED]` eval_longbench.py 指标单位不一致 (L807-808) — fixed
- [x] **EVL-018** `[MED]` aggregate_results.py kv_mode 排序无 KIVI (L552, L585, L648, L1322) — fixed
- [x] **EVL-019** `[MED]` CWE pred_words 未过滤空字符串 (L193) — fixed
- [x] **EVL-020** `[MED]` 指标尺度 [0,100] vs objective.md 声称 [0,1] 不一致 (L812, L867-868) — fixed
- [x] **EVL-021** `[MED]` HF 字段提取 fallback 顺序含 "input" 作为 context 候选 (L387) — fixed
- [x] **EVL-022** `[LOW]` eval_ruler.py 多答案评分存在死代码 (L172-174) — fixed
- [x] **EVL-024** `[LOW]` _token_f1() 分母过度保护 (L140-141) — fixed
- [x] **EVL-025** `[LOW]` task_off_name 取 vals[0] 假设同一任务所有样本指标名一致 (L811) — fixed

### KVC. KV Cache
- [x] **KVC-001** `[CRIT]` K-scale/zp 在 clear() 后状态不一致 — fixed commit 20095fb
- [x] **KVC-003** `[HIGH]` 论文内存对比表必须注明 KIVI INT4 无 bit-packing — fixed
- [x] **KVC-004** `[HIGH]` 论文 Methods 节须披露 K 量化策略差异 — fixed
- [x] **KVC-006** `[MED]` decode K 量化与 prefill K 量化 device 一致性未强制 (L220-231) — fixed
- [x] **KVC-007** `[MED]` V buffer shape 一致性未校验 (L126-131) — fixed
- [x] **KVC-008** `[MED]` append() 无输入 tensor shape 校验 (L187-245) — fixed
- [x] **KVC-011** `[MED]` 论文须披露 KIVI 无温度校正 — fixed
- [x] **KVC-012** `[MED]` 论文须披露 decode kernel 差异 — fixed
- [x] **KVC-017** `[LOW]` KIVI K-scale 内存恒定 vs INT8 随 seq_len 增长 — fixed

### PRF. 性能分析
- [x] **PRF-001** `[HIGH]` kivi_style quant_bits CSV 记录 vs 运行时不一致 (L304/341 vs L369) — fixed
- [x] **PRF-006** `[MED]` pynvml 初始化异常未捕获 (L104-105) — fixed
- [x] **PRF-007** `[MED]` MemoryMonitor.stop() 线程健壮性 (L119-121) — fixed
- [x] **PRF-008** `[MED]` NVML 回退逻辑隐性掩盖不可用 (L381) — fixed

### QNT. 量化模块
- [x] **QNT-001** `[CRIT]` percentile < 50 时 quantile_lo > quantile_hi — fixed commit 20095fb
- [x] **QNT-002** `[CRIT]` 无 percentile 范围校验 — fixed commit 20095fb

### RUN. 实验运行
- [x] **RUN-001** `[CRIT]` eval_ppl.py build_kv_cache() 缺失 kivi_style 分支 — fixed commit 03ed4a0

### TST. 测试覆盖
- [x] **TST-001** `[HIGH]` KIVI cache zero-point decode 传播测试缺失 — fixed
- [x] **TST-002** `[HIGH]` asymmetric_quant zero-point 公式直接验证缺失 — fixed

</details>
