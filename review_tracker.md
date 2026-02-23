# Code Review Tracker

> 188 issues | 64 fixed + 2 false_positive | 122 open (3 CRIT, 22 HIGH, 65 MED, 32 LOW)
> Phase Gate: **BLOCKED** — CHK-001, EVL-001, EVL-002
> Last updated: 2026-02-24

---

## Phase Blockers (CRITICAL open)

### CHK. 完整性检查 — `scripts/check_run_completeness.py`

- [ ] **CHK-001** `[CRIT]` OOM 分类被 elif 链短路 (L94-109)
- [ ] **CHK-002** `[HIGH]` manifest 无 failure_type 字段 (L85)
- [ ] **CHK-003** `[HIGH]` 不验证 kivi_style 运行完整性
- [ ] **CHK-004** `[MED]` 不验证 CSV 内容完整性 (L80)
- [ ] **CHK-005** `[MED]` LongBench/RULER 任务级完整性无验证 (L16-23, L146-148)
- [ ] **CHK-006** `[MED]` dev agent 仍未确认 O 节 3 CRITICAL + T 节 1 CRITICAL

### EVL. 评测脚本 — `scripts/eval_*.py`

- [ ] **EVL-001** `[CRIT]` eval_longbench.py _classification_accuracy() 语义变化未文档化 (L265)
- [ ] **EVL-002** `[CRIT]` **RULER CWE 子任务在 1.5B *_long 配置下触发 max_position_embeddings 溢出**
- [ ] **EVL-008** `[HIGH]` **run_experiments.py 预检查遗漏 RULER CWE 的额外 max_new_tokens 开销** (L806-928)
- [ ] **EVL-013** `[MED]` eval_ruler.py 截断策略 magic numbers (L562-570)
- [ ] **EVL-014** `[MED]` **eval_ruler.py case 循环无 per-case error handling** (L872-908)
- [ ] **EVL-017** `[MED]` eval_longbench.py 自实现 Rouge-L 可能与官方 LongBench 不一致 (L206-219)
- [ ] **EVL-023** `[LOW]` eval_longbench.py logger 定义位置：logger = logging.getLogger(__name__) 在 import 块中间（介于 traceback 和 from collections impor...
- [ ] **EVL-026** `[LOW]` eval_ruler.py summary row 聚合维度不一致 (L1008-1016): `overall_pass_rate` 基于 task-level macro average（4 tasks），而 `overall_f1` 和 `overall_contains` 基于 depth-level macro average（N depth ratios），同一 summary_row 内三个指标的聚合基底不同。主指标 `ruler_score` 不受影响（等于 task-level pass_rate）

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

### EXP. 导出/报告 — `scripts/export_*.py`
- [ ] **EXP-001** `[HIGH]` C11 跨模型验证逻辑缺陷 (generate_thesis_report.py
- [ ] **EXP-002** `[MED]` LongBench 表缺少任务指标组成说明 (export_tables_latex.py
- [ ] **EXP-003** `[MED]` RULER 表仅显示整体 pass rate (export_tables_latex.py
- [ ] **EXP-004** `[MED]` 多模型表格缺少 per-model 分页
- [ ] **EXP-005** `[MED]` C9 对指标名正确 (generate_thesis_report.py
- [ ] **EXP-006** `[MED]` generate_thesis_report.py C11 "cross-model robustness" claim 无 model_id 过滤
- [ ] **EXP-007** `[LOW]` KIVI 在 KV_MODE_ORDER 和 KV_MODE_DISPLAY 中已完整映射 (export_tables_latex.py
- [ ] **EXP-008** `[LOW]` 所有 3 配置文件的 KIVI 吞吐量仅包含 INT8（无 INT4 KIVI 吞吐量）— 可能遗漏 KIVI INT4 batch scaling 数据

### KVC. KV Cache — `src/cache/`
- [ ] **KVC-002** `[HIGH]` KIVI INT4 未实现 bit-packing，内存与 INT8 相同 (L84, L90, L138-143)
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

### RVW. 审查工具与配置 — `scripts/review_tool.py`, `.claude/agents/review-*.md`
- [ ] **RVW-001** `[HIGH]` review_tool.py phase-gate 仅检查 CRIT，遗漏 HIGH (L120): `cmd_phase_gate()` 仅过滤 `severity == "CRIT"`，按 CLAUDE.md §4.5 闸门规则，HIGH 也应阻塞（至少提示）。可能导致存在 HIGH 阻塞项时误判为 CLEAR
- [ ] **RVW-002** `[HIGH]` review_tool.py cmd_add() 文件写入非原子性 (L230-231): `open(path, "w")` 直接覆写，若进程中途崩溃会导致 review_tracker.md 被截断或损坏。应使用 tmpfile + rename 原子写入
- [ ] **RVW-003** `[MED]` review_tool.py 解析不匹配行静默跳过 (L42-87): 任何不符合 ISSUE_RE 格式的 issue 行会被完全忽略，无警告日志。正则已从 `\w+` 改为 `[A-Z]+` 部分改善，但核心静默跳过问题仍存在
- [ ] **RVW-004** `[MED]` review_tool.py _update_summary() 格式假设过强 (L274-283): `summary_replaced` 标志仅在 "Last updated:" 行后触发，若 header 行顺序变化或新增行则部分 summary 不更新
- [x] **RVW-005** `[MED]` reviewer.md L5 描述引用 "iteration.md TODO Backlog" 应为 "review_tracker.md" (.claude/agents/reviewer.md L5) — fixed
- [x] **RVW-006** `[MED]` reviewer.md YAML 权限与 body 指令矛盾 (.claude/agents/reviewer.md L8 vs L11,L16) — fixed: body 改为"严禁修改源代码（src/、scripts/、tests/、configs/）"，写入权限标注"仅限 review_tracker.md + iteration.md"
- [ ] **RVW-007** `[MED]` start_agents.sh L32 developer 启动 prompt 引用 "TODO Backlog" 而非 review_tracker.md (scripts/start_agents.sh L32): 与 developer.md L22 "读取 review_tracker.md" 冲突，可能导致 developer agent 优先遵循启动 prompt 到 iteration.md 而非 review_tracker.md 查找任务
- [ ] **RVW-008** `[MED]` start_agents.sh L33 reviewer 启动 prompt 未提及 review_tracker.md (scripts/start_agents.sh L33): reviewer.md L21 要求先读 review_tracker.md，但启动 prompt 仅说"读 iteration.md"
- [ ] **RVW-009** `[LOW]` settings.json Stop hook "BLOCKED" 字符串匹配过宽 (.claude/settings.json L21): iteration.md 历史条目中若包含 "BLOCKED" 一词（如引用 Phase Gate 状态），会误触发退出许可，应匹配更精确的标记如 "auto-iterate-blocked"
- [ ] **RVW-010** `[LOW]` start_agents.sh 硬编码绝对路径 (scripts/start_agents.sh L5): `PROJECT_DIR="/Users/chenzilang/..."` 不可移植，建议使用 `$(cd "$(dirname "$0")/.." && pwd)`
- [ ] **RVW-011** `[HIGH]` Phase Blocker CHK-001 已修复但未标记 — 独立审查确认 `_check_task_state()` OOM 检查已移至 if 链首位 (check_run_completeness.py L147)，匹配 Codex PR 修复 (merge 1aa5c95)。Phase Gate 状态过期，建议 developer 验证并标记 fixed 以解除 blocker

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
