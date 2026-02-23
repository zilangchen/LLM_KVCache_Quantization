# Code Review Tracker

> 176 issues | 62 fixed + 2 false_positive | 112 open (3 CRIT, 19 HIGH, 61 MED, 29 LOW)
> Phase Gate: **BLOCKED** — T-1, AF-1, AG-1
> Last updated: 2026-02-24

---

## Phase Blockers (CRITICAL open)

### T. check_run_completeness.py — `scripts/check_run_completeness.py`

- [ ] **T-1** `[CRIT]` OOM 分类被 elif 链短路 (L94-109)
- [ ] **T-2** `[HIGH]` manifest 无 failure_type 字段 (L85)
- [ ] **T-3** `[HIGH]` 不验证 kivi_style 运行完整性
- [ ] **T-4** `[MED]` 不验证 CSV 内容完整性 (L80)
- [ ] **T-5** `[MED]` LongBench/RULER 任务级完整性无验证 (L16-23, L146-148)

### AF. Codex PR #5 增量审查 — `eval_longbench.py`

- [ ] **AF-1** `[CRIT]` eval_longbench.py _classification_accuracy() 语义变化未文档化 (L265)
- [ ] **AF-2** `[HIGH]` patch_model.py 移除 kv_heads 默认推理 (L100-108)
- [ ] **AF-3** `[HIGH]` calibrate_behavior.py MSE clamping 移除导致旧校准产物不可复现
- [ ] **AF-4** `[MED]` 全 eval 脚本 _resolve_quant_bits() 重复定义（6 处相同代码，违反 DRY）
- [ ] **AF-5** `[MED]` profile_memory.py GPU 峰值来源判断逻辑 (L383-385)
- [ ] **AF-6** `[MED]` eval_ruler.py 截断策略 magic numbers (L562-570)
- [ ] **AF-7** `[MED]` generate_loop.py batch>1 填充检查移除
- [ ] **AF-8** `[MED]` kivi_style_cache.py clear() 仅重置 K scale/zp 未显式清零 V scale/zp
- [ ] **AF-9** `[MED]` final_emnlp2026_v1.yaml LLaMA 本地路径硬编码
- [ ] **AF-10** `[LOW]` kivi_style_cache.py INT4 head_dim 偶数约束仅在 append 时检查

### AG. RULER 长上下文溢出 — `scripts/eval_ruler.py`

- [ ] **AG-1** `[CRIT]` **RULER CWE 子任务在 1.5B *_long 配置下触发 max_position_embeddings 溢出**
- [ ] **AG-2** `[HIGH]` **run_experiments.py 预检查遗漏 RULER CWE 的额外 max_new_tokens 开销** (L806-928)
- [ ] **AG-3** `[MED]` **eval_ruler.py case 循环无 per-case error handling** (L872-908)

---

## Open Issues

### A. MSE 校准实现缺陷 — `scripts/calibrate_behavior.py`
- [ ] **A-5** `[HIGH]` trial 排名受 loss 尺度影响 (L780-791)
- [ ] **A-8** `[MED]` MSE loss 语义未文档化 (L6, L234-239)

### B. KIVI Cache 实现 — `src/cache/kivi_style_cache.py`
- [ ] **B-5** `[LOW]` _seq_len 仅在 layer_id=0 时更新 (L244-245)
- [ ] **B-6** `[LOW]` 无 batch_size=0 校验 (L204)

### C. 非对称量化模块 — `src/quant/asymmetric_quant.py`
- [ ] **C-3** `[MED]` float16 输入精度损失 (L58-59)
- [ ] **C-4** `[LOW]` dequantize 函数无输入类型校验 (L74-95)

### D. Engine 集成 — `src/engine/generate_loop.py`
- [ ] **D-2** `[HIGH]` decode 阶段 KIVI 走 dequant→re-quant 路径 (L635-678)
- [ ] **D-3** `[MED]` KIVI kv_mode 未校验 quant_bits∈{4,8} (L294-310)
- [ ] **D-4** `[LOW]` docstring 未说明 KIVI 模式行为 (L258-292)

### E. 评测脚本集成 — `eval_longbench.py`
- [ ] **E-7** `[MED]` eval_longbench.py 自实现 Rouge-L 可能与官方 LongBench 不一致 (L206-219)

### F. 实验配置矩阵一致性 — `configs/`
- [ ] **F-4** `[MED]` 7B/8B 长上下文仅 3 条 vs 1.5B 的 18 条
- [ ] **F-5** `[MED]` 1.5B 校准文件命名不一致 (kv_calib_kl_selected_v3_quick.json vs 7B/8B 的 kv_calib_kl_qwen25_7b_int8.json)
- [ ] **F-6** `[LOW]` 1.5B 配置头部注释缺少 kivi_style kv_mode 和 kivi_asymmetric calib_strategy

### G. 消融配置审查 — `configs/snapshots/exp_matrix_ablation_1p5b_v1.yaml`
- [ ] **G-3** `[MED]` 消融 A-2 (MSE) 使用 use_attn_temperature
- [ ] **G-4** `[MED]` 消融 D 节缺少 dynamic scales 变体
- [ ] **G-5** `[MED]` 所有消融仅 seq_len=4096
- [ ] **G-6** `[MED]` 消融 C 节 (group_size sweep) 使用同一个 calib_file
- [ ] **G-7** `[LOW]` 消融 A-1/B-1/C-1 是完全相同的 run

### H. export/generate/configs 审查 — `generate_thesis_report.py`
- [ ] **H-1** `[MED]` generate_thesis_report.py C11 "cross-model robustness" claim 无 model_id 过滤
- [ ] **H-2** `[LOW]` 所有 3 配置文件的 KIVI 吞吐量仅包含 INT8（无 INT4 KIVI 吞吐量）— 可能遗漏 KIVI INT4 batch scaling 数据

### J. 修复审查与新发现 — `calibrate_behavior.py`
- [ ] **J-2** `[MED]` calibrate_behavior.py MSE clamping 语义偏差：MSE 路径对 p_ref/p_quant 执行 clamp(min=eps) 后再计算差的平方。对 MSE 而言 clamp 不防 NaN（MSE 不含...
- [ ] **J-3** `[LOW]` eval_longbench.py logger 定义位置：logger = logging.getLogger(__name__) 在 import 块中间（介于 traceback 和 from collections impor...

### K. generate_loop.py KIVI 路径 — `src/engine/generate_loop.py`
- [ ] **K-1** `[HIGH]` KIVI 模式静默忽略参数 (L412-486, L563)
- [ ] **K-2** `[MED]` KIVI decode 路径 dequant→requant 精度累积（已知 D2 但补充细节）
- [ ] **K-3** `[MED]` Batch 约束重复校验 (L344-361)
- [ ] **K-4** `[LOW]` KIVI docstring 缺失 (L288-291)

### L. run_experiments.py 审查 — `scripts/run_experiments.py`
- [ ] **L-2** `[MED]` skip_completed_success 状态不一致 (L1134 vs L1147)
- [ ] **L-3** `[MED]` subprocess.run 无异常捕获 (L1174-1179)
- [ ] **L-4** `[MED]` kv_mode 无效值静默跳过 (L850-862)
- [ ] **L-5** `[LOW]` YAML 配置无 matrix 非空校验 (L725-794)
- [ ] **L-6** `[LOW]` append 模式 manifest 元数据被覆盖 (L252-265)
- [ ] **L-7** `[LOW]` append_history 未记录 kv_mode/quant_bits 变化 (L272-278)

### M. aggregate_results.py 审查 — `scripts/aggregate_results.py`
- [ ] **M-8** `[LOW]` Bootstrap CI 单样本情况返回 (value, value) 无警告 (L1059-1060)
- [ ] **M-9** `[LOW]` 精确枚举阈值 n=16 硬编码 (L1092-1107)

### P. 测试覆盖质量 — `test_kivi_cache.py`
- [ ] **P-1** `[HIGH]` B1 修复验证不完整
- [ ] **P-2** `[HIGH]` K decode 量化误差无测试
- [ ] **P-3** `[MED]` 缺少 float16 输入测试
- [ ] **P-4** `[MED]` 缺少 per-channel/per-token 轴语义验证
- [ ] **P-5** `[MED]` C1/C2 修复缺少边界值测试
- [ ] **P-6** `[MED]` 统计测试缺少混合符号 sign-flip 场景
- [ ] **P-7** `[LOW]` 缺少单 token、batch=0、head_dim=1 等极端边界测试
- [ ] **P-8** `[LOW]` 缺少多轮 clear→append 循环测试（生产中常见的 batch 间重用 cache 场景）

### R. profile_memory.py 内存测量 — `scripts/profile_memory.py`
- [ ] **R-5** `[LOW]` output 属性可靠性 (L348-352)

### S. run_experiments.py 实验运行器 — `scripts/run_experiments.py`
- [ ] **S-1** `[HIGH]` kivi_style 的 calib_strategy 默认值继承陷阱 (L880-881, L1015-1016)
- [ ] **S-2** `[MED]` kivi_style decode_attn_impl 无强制验证 (L882-884, L1033-1034)
- [ ] **S-3** `[MED]` 无条件传递 quant 参数给所有 kv_mode (L987-998)
- [ ] **S-4** `[MED]` skip 时重复标记成功 (L1130-1138)
- [ ] **S-5** `[LOW]` manifest history 仅保留最近 20 条 (L334)

### U. generate_loop + patch_model KIVI — `kivi_style_cache.py`
- [ ] **U-1** `[MED]` kivi_style_cache.py V scale/zp 缓冲区 dtype 隐性转换 (L140-149, L240-241)
- [ ] **U-2** `[MED]` patch_model.py kv_heads 推断失败静默降级 (L473-477)
- [ ] **U-3** `[MED]` patch_model.py KIVI 缓存若被错误路由到 fused forward (L556-567)
- [ ] **U-4** `[LOW]` generate_loop.py kivi_style 接受但静默忽略 calib_file/use_attn_temperature/adaptive_static_scales 参数 (L412-485, L563-566): 已...

### V. KIVI INT4 路径 — `src/cache/kivi_style_cache.py`
- [ ] **V-1** `[HIGH]` KIVI INT4 未实现 bit-packing，内存与 INT8 相同 (L84, L90, L138-143)
- [ ] **V-2** `[MED]` get_memory_mb() 注释误导 (L307)
- [ ] **V-3** `[MED]` INT4 量化精度 edge case 未覆盖
- [ ] **V-4** `[LOW]` INT4 vs INT8 行为切换逻辑正确

### Y. 对称量化核心模块 — `(int8_basic.py`
- [ ] **Y-1** `[MED]` _normalize_static_scale 3D case 实现错误
- [ ] **Y-2** `[MED]` dequantize_symmetric_int8 多路径判断脆弱
- [ ] **Y-3** `[MED]` 缺少 INT8 离群值测试
- [ ] **Y-4** `[LOW]` __init__.py.__all__ 不完整
- [ ] **Y-5** `[LOW]` 核心公式验证通过

### Z. Phase 4 完成验证 — `scripts/`
- [ ] **Z-1** `[MED]` 消融实验仅跑 PPL+Needle，缺少 LongBench
- [ ] **Z-2** `[MED]` dev agent 仍未确认 O 节 3 CRITICAL + T 节 1 CRITICAL
- [ ] **Z-3** `[LOW]` 消融 output dir 命名含双重 seed

### AA. calibrate_behavior MSE 审查 — `(calibrate_behavior.py`
- [ ] **AA-1** `[HIGH]` 默认校准路径与 generate_loop 不匹配 (calibrate_behavior.py
- [ ] **AA-2** `[HIGH]` 加载校准文件时无 loss_function 字段校验 (generate_loop.py
- [ ] **AA-3** `[MED]` inv_tau shape 未在加载时验证 (generate_loop.py
- [ ] **AA-4** `[MED]` MSE 与 KL loss 量级差异影响搜索行为 (calibrate_behavior.py
- [ ] **AA-5** `[MED]` evaluate_quant_candidate 不使用 inv_tau (calibrate_behavior.py
- [ ] **AA-6** `[LOW]` loss_accum NaN 无检测 (calibrate_behavior.py

### AB. aggregate_results KIVI/多模型 — `aggregate_results.py`
- [ ] **AB-1** `[HIGH]` RULER 聚合缺少子任务分拆 (aggregate_results.py
- [ ] **AB-2** `[HIGH]` 多模型对比缺少分层表
- [ ] **AB-3** `[MED]` LongBench 聚合同时包含 3 个近义指标 (aggregate_results.py
- [ ] **AB-4** `[MED]` KIVI quant_bits 在 pairings 中未区分 INT8/INT4 (aggregate_results.py
- [ ] **AB-5** `[MED]` kv_mode 显示顺序依赖默认排序 (aggregate_results.py
- [ ] **AB-6** `[LOW]` Bootstrap seed 基于 SHA256 hash 的独立性

### AC. export_tables + generate_thesis_report — `generate_thesis_report.py`
- [ ] **AC-1** `[HIGH]` C11 跨模型验证逻辑缺陷 (generate_thesis_report.py
- [ ] **AC-2** `[MED]` LongBench 表缺少任务指标组成说明 (export_tables_latex.py
- [ ] **AC-3** `[MED]` RULER 表仅显示整体 pass rate (export_tables_latex.py
- [ ] **AC-4** `[MED]` 多模型表格缺少 per-model 分页
- [ ] **AC-5** `[MED]` C9 对指标名正确 (generate_thesis_report.py
- [ ] **AC-6** `[LOW]` KIVI 在 KV_MODE_ORDER 和 KV_MODE_DISPLAY 中已完整映射 (export_tables_latex.py

### AD. eval_ppl + profile_latency KIVI — `(eval_ppl.py`
- [ ] **AD-1** `[MED]` quant_bits CSV 推断 fallback 为 16 (eval_ppl.py
- [ ] **AD-2** `[MED]` profile_latency.py run 间无显式 CUDA sync (profile_latency.py
- [ ] **AD-3** `[MED]` kivi_style decode_attn_impl 参数被静默忽略 (profile_latency.py
- [ ] **AD-4** `[LOW]` calib_file 对 kivi_style 静默无操作 (eval_ppl.py

### AE. 测试套件覆盖缺口 — `calibrate_behavior.py`
- [ ] **AE-3** `[HIGH]` calibrate_behavior.py 完全无单元测试
- [ ] **AE-4** `[HIGH]` KIVI + asymmetric_quant 端到端集成测试缺失
- [ ] **AE-5** `[MED]` per-channel K 和 per-token V axis 独立性验证缺失
- [ ] **AE-6** `[MED]` Bootstrap CI n=1 和 n=2 边界测试缺失
- [ ] **AE-7** `[MED]` Permutation test NaN 处理测试缺失
- [ ] **AE-8** `[MED]` BH-FDR 单调性验证缺失
- [ ] **AE-9** `[MED]` eval_longbench.py / eval_ruler.py 完全无单元测试
- [ ] **AE-10** `[LOW]` INT4 vs INT8 误差比例测试缺失

---

## Resolved

<details>
<summary>62 fixed + 2 false_positive (click to expand)</summary>

### A. MSE 校准实现缺陷
- [x] **A-1** `[CRIT]` MSE loss 维度语义错误 (L199-200) — fixed commit 20095fb
- [x] **A-2** `[CRIT]` MSE loss 全局 mean 无维度 (L302) — fixed commit 20095fb
- [x] **A-3** `[HIGH]` loss_accum 未除以样本数 (L177-206) — fixed commit 20095fb
- [x] **A-4** `[HIGH]` MSE 无数值安全 clamp (L199) — fixed commit 20095fb
- [x] **A-6** `[MED]` 默认输出文件名硬编码为 kl.json — fixed commit 20095fb
- [x] **A-7** `[MED]` select_best_trial() 无 key 存在性校验 — fixed commit 20095fb

### B. KIVI Cache 实现
- [x] **B-1** `[CRIT]` K-scale/zp 在 clear() 后状态不一致 — fixed commit 20095fb
- [x] **B-2** `[MED]` decode K 量化与 prefill K 量化 device 一致性未强制 (L220-231) — fixed
- [x] **B-3** `[MED]` V buffer shape 一致性未校验 (L126-131) — fixed
- [x] **B-4** `[MED]` append() 无输入 tensor shape 校验 (L187-245) — fixed

### C. 非对称量化模块
- [x] **C-1** `[CRIT]` percentile < 50 时 quantile_lo > quantile_hi — fixed commit 20095fb
- [x] **C-2** `[CRIT]` 无 percentile 范围校验 — fixed commit 20095fb

### D. Engine 集成
- [x] **D-1** `[HIGH]` generate() 函数缺少 quant_bits 参数 — fixed commit 20095fb

### E. 评测脚本集成
- [x] **E-1** `[CRIT]` export_tables_latex.py KV_MODE_DISPLAY 缺 kivi_style — fixed commit 8bf9414
- [x] **E-2** `[CRIT]` export_tables_latex.py KV_MODE_ORDER 缺 kivi_style — fixed commit 8bf9414
- [x] **E-3** `[HIGH]` eval_longbench.py 引用未定义 logger — fixed commit 20095fb
- [x] **E-4** `[HIGH]` generate_thesis_report.py 缺少 KIVI claims — fixed commit 8bf9414
- [x] **E-5** `[MED]` 所有 eval 脚本 quant_bits fallback 将 KIVI 记录为 16 (eval_ppl L878 / eval_needle L467 / eval_longbench L833 / eval_ruler L98... — fixed
- [x] **E-6** `[MED]` eval_longbench.py 指标单位不一致 (L807-808) — fixed
- [x] **E-8** `[MED]` aggregate_results.py kv_mode 排序无 KIVI (L552, L585, L648, L1322) — fixed
- [x] **E-9** `[LOW]` eval_ruler.py 多答案评分存在死代码 (L172-174) — fixed

### F. 实验配置矩阵一致性
- [x] **F-1** `[HIGH]` 1.5B 配置完全缺失 KIVI-style 条目 — fixed commit f07422d
- [x] **F-2** `[HIGH]` 7B/8B 配置完全缺失吞吐量 batch scaling 条目 — fixed commit f07422d
- [x] **F-3** `[HIGH]` 7B/8B 配置缺失 INT4 长上下文运行 — fixed commit f07422d

### G. 消融配置审查
- [x] **G-1** `[HIGH]` 消融 A-3 decode_attn_impl 混淆因子 — fixed commit f07422d
- [x] **G-2** `[HIGH]` 消融 A 节缺少 KIVI-style — fixed commit f07422d

### I. final_emnlp2026_v1.yaml 审查
- [x] **I-1** `[MED]` ablation_dimensions.scale_strategy 仅列 [static, adaptive]（L77）— 计划中为 "static vs adaptive vs dynamic" 三方，与消融配置 D 节同一缺失 — fixed
- [x] **I-2** `[LOW]` benchmarks 仅列 4 个质量评测（L67-71）— 未包含 latency/memory/throughput 系统性能 benchmark，虽然这些是独立维度但在 meta-config 中应有提及 — fixed
- [x] **I-3** `[LOW]` models[0].calibration_artifacts 列出了尚不存在的 MSE 产物（int8_mse/int4_mse，L38-39）— MSE 校准实现有已知 bug，这些产物暂不可用 — fixed

### J. 修复审查与新发现
- [x] **J-1** `[CRIT]` calibrate_behavior.py --calib_out None fallback — fixed

### L. run_experiments.py 审查
- [x] **L-1** `[CRIT]` eval_ppl.py build_kv_cache() 缺失 kivi_style 分支 — fixed commit 03ed4a0

### M. aggregate_results.py 审查
- [x] **M-1** `[CRIT]` kivi_style 完全缺失显著性配对 — fixed commit 03ed4a0
- [x] **M-2** `[HIGH]` longbench_official_macro 未被聚合 — fixed commit 03ed4a0
- [x] **M-3** `[HIGH]` 显著性分析缺失 model_id/hardware 分组 — fixed commit 03ed4a0
- [x] **M-4** `[HIGH]` RULER 深度分析缺失 model_id — fixed commit 03ed4a0
- [x] **M-5** `[MED]` kv_mode 使用字母序排序而非语义顺序 (L552, L585, L648, L1322) — fixed
- [x] **M-6** `[MED]` 显著性配对数据可能被 aggfunc="mean" 静默平均 (L998) — fixed
- [x] **M-7** `[LOW]` LongBench 图 y 轴标签与新口径不一致 — fixed

### O. eval_ruler.py 评分逻辑
- [x] **O-1** `[CRIT]` MK-NIAH hits_exact 计数器死代码 (L172-174) — fixed
- [x] **O-2** `[CRIT]` VT 多链评分仅评价第一条链 (L216, L442) — fixed
- [x] **O-3** `[CRIT]` 上下文截断从右侧保留破坏 RULER 语义 (L546-554) — fixed
- [x] **O-4** `[HIGH]` kivi_style quant_bits 推断为 16 (L985) — fixed
- [x] **O-5** `[MED]` CWE pred_words 未过滤空字符串 (L193) — fixed
- [x] **O-6** `[LOW]` _token_f1() 分母过度保护 (L140-141) — fixed

### Q. eval_longbench.py 评分指标
- [x] **Q-1** `[HIGH]` 分类准确率子串匹配过于宽松 (L252) — fixed
- [x] **Q-2** `[MED]` 指标尺度 [0,100] vs objective.md 声称 [0,1] 不一致 (L812, L867-868) — fixed
- [x] **Q-3** `[MED]` HF 字段提取 fallback 顺序含 "input" 作为 context 候选 (L387) — fixed
- [x] **Q-4** `[LOW]` task_off_name 取 vals[0] 假设同一任务所有样本指标名一致 (L811) — fixed

### R. profile_memory.py 内存测量
- [x] **R-1** `[HIGH]` kivi_style quant_bits CSV 记录 vs 运行时不一致 (L304/341 vs L369) — fixed
- [x] **R-2** `[MED]` pynvml 初始化异常未捕获 (L104-105) — fixed
- [x] **R-3** `[MED]` MemoryMonitor.stop() 线程健壮性 (L119-121) — fixed
- [x] **R-4** `[MED]` NVML 回退逻辑隐性掩盖不可用 (L381) — fixed

### W. final_emnlp2026_v1.yaml 最终配置
- [x] **W-1** `[HIGH]` 7B/8B 校准产物尚未生成（Phase 2 依赖，非 bug） — false_positive
- [x] **W-2** `[MED]` LLaMA-3.1-8B 使用本地路径而非 HF ID — fixed
- [x] **W-3** `[MED]` Claims C9-C11 定义不够精确 — fixed
- [x] **W-4** `[LOW]` meta-config 无执行工作流说明 — fixed

### X. INT8KVCache vs KIVIStyleKVCache 对比
- [x] **X-1** `[HIGH]` 论文内存对比表必须注明 KIVI INT4 无 bit-packing — fixed
- [x] **X-2** `[HIGH]` 论文 Methods 节须披露 K 量化策略差异 — fixed
- [x] **X-3** `[MED]` 论文须披露 KIVI 无温度校正 — fixed
- [x] **X-4** `[MED]` 论文须披露 decode kernel 差异 — fixed
- [x] **X-5** `[LOW]` KIVI K-scale 内存恒定 vs INT8 随 seq_len 增长 — fixed

### AA. calibrate_behavior MSE 审查
- [x] **AA-7** `[LOW]` search_trials.csv 已按 loss_function 区分文件名 (calibrate_behavior.py — false_positive

### AE. 测试套件覆盖缺口
- [x] **AE-1** `[HIGH]` KIVI cache zero-point decode 传播测试缺失 — fixed
- [x] **AE-2** `[HIGH]` asymmetric_quant zero-point 公式直接验证缺失 — fixed

</details>
