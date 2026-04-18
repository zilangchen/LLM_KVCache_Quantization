# Phase 2.6 流程违规审计表（A 方案口径，2026-04-18 20:10 改写）

> **口径**：按用户 2026-04-18 选择的 **A 方案** — 流程干净 + 数据干净优先。
> 凡在 `int8_ours` bug 未修复、未严格串行 smoke → wave 的状态下产生的 run，**一律 quarantine**，
> 不因「后验 grep 显示数据干净」而恢复使用。
>
> **历史档案**：本文件原 B 方案版本（2026-04-18 19:50）已废弃，见下方 §「废弃的 B 方案口径」。

## A 方案核心纪律（不可协商）

1. **数据完整性 ≠ 流程合规**：即使某批 run 的 CSV/log 机器 grep 显示 `0 Traceback / 0 failed metric`，只要它是在「前置 smoke 失败 + daemon 违反 fail-fast」的窗口内产生的，就**不得**用于主表 / readout / aggregate。
2. **Quarantine = do-not-use-for-claims/readout/aggregate**：物理目录隔离 + MANIFEST 标记，工具链必须显式排除。
3. **恢复路径 = 完整重跑**，不是「后验确认数据干净就解禁」。
4. **修复顺序锁死**：Step 0 修 `int8_ours` bug（wrapper `--out` → `--calib_out` + `allow_abbrev=False` + 禁 default fallback + `_normalize_static_scale` heads 校验）→ Wave 2 sanity（**默认 4 runs**：`fp16 + int8_ours × {trec, vcsum}`，与后文 §执行状态一致）→ Mistral smoke → 其他 Wave 串行重跑。

## Quarantine 目录清单（全部 do-not-use）

| 原目录 | Quarantine 目录 | Run 数 | MANIFEST 状态 |
|---|---|---|---|
| `results/phase2_c2b_llama8b_extended` | `..._20260418_quarantine` | 21 | ✅ |
| `results/phase2_7b_random_hardening` | `..._20260418_quarantine` | 24 | ✅ |
| `results/phase2_c3_qwen14b` | `..._20260418_quarantine` | 36 | ✅ |
| `results/phase2_batch4_extend_tasks_7b` | `..._20260418_quarantine` | 32 | ✅ |
| `results/phase2_batch5_extend_tasks_8b` | `..._20260418_quarantine` | 36 | ✅ |
| `results/phase2_c4_mistral7b` | `..._20260418_quarantine` | 19 (含 smoke 3 failed) | ✅ |
| `results/phase2_trec_vcsum_sanity` | `..._20260418_quarantine` | 3 (含 int8_ours × trec n=50 failed metric) | ✅ |
| **合计** | | **171 runs** | |

**每个 quarantine 目录的 MANIFEST.md 内容**（统一格式）：
- 原目录名 + rename 时间戳
- Run 数 + CSV/log 文件清单
- Prohibited uses: 不得用于主表 / readout / aggregate / 论文 claim
- 恢复条件: 仅在 int8_ours bug 修复 + 严格重跑通过后，由用户显式批准

## 机器 grep 数字（仅作审计记录，不作为恢复依据）

> **警告**：以下机器 grep 数字**不构成 quarantine 恢复理由**。A 方案明确拒绝「数据干净就保留」。
> 保留这些数字仅用于审计追溯，让未来知道 bug 污染范围与数据完整性脱钩。

```bash
# grep 审计命令（事后只读核查）：
csv_n   = ls <dir>/longbench_task_summary_*.csv | wc -l
err_n   = grep -l "RuntimeError|Traceback|failed:" <dir>/*.log | wc -l
fail_n  = awk -F, 'NR>1 && $10=="failed"' <dir>/longbench_task_summary_*.csv | wc -l
```

| 类别 | Quarantine 目录 | CSV | error log | failed metric |
|---|---|---|---|---|
| 审计（非保留）| Wave 1 (8B extended) | 21 | 0 | 0 |
| 审计（非保留）| Wave 3 (7B random) | 24 | 0 | 0 |
| 审计（非保留）| Wave 4 (14B sweep) | 36 | 0 | 0 |
| 审计（非保留）| Wave 7a (7B extend) | 32 | 0 | 0 |
| 审计（非保留）| Wave 7b (8B extend) | 36 | 0 | 0 |
| 审计（非保留）| Mistral full (partial) | 19 | 0 | 0 |
| 审计（failed）| sanity int8_ours trec | 1 | 1 | 1 (all 50 samples RuntimeError) |
| 审计（failed）| Mistral smoke int8_ours hotpotqa | 1 | 1 | 1 |
| 审计（failed）| Mistral smoke int8_ours gov_report | 1 | 1 | 1 |

**注解**：即使数据机器干净，也不代表过程合规。A 方案只承认「修复 + 严格串行重跑」后产生的新 run 进入主结论。

## 执行状态（2026-04-18 20:25 同步）

| 阶段 | 状态 |
|---|---|
| Quarantine 物理隔离 | ✅ 7 目录全部 rename + MANIFEST.md |
| Day 1 Step 1：最小复现 + 带行号 stack trace | ✅ **completed**（定位到 `src/quant/_common.py:94` expand） |
| Step 0 B1 (calibrate_behavior.py argparse + wrapper `--out`→`--calib_out`) | ✅ **completed** |
| Step 0 B2 (_normalize_static_scale shape 校验 + audit context) | ✅ **completed** |
| 最小验证 (B1 真实 calib 路径落地 / B2 fail-fast 正反回归) | ✅ **PASS** |
| Wave 2 sanity 严格重跑（用户批准 = 4 runs） | ⏸️ 待启动（条件齐备） |
| 后续 wave 重跑 | ⏸️ 待 Wave 2 sanity 通过 |

**纪律锁**：在 Wave 2 sanity **完整通过**（默认 `fp16 + int8_ours × {trec, vcsum} = 4 runs`, 0 Traceback, 0 failed metric, 0 head-mismatch ValueError）之前，**不启动任何后续 wave**。

**Wave 2 执行口径**：用户批准 = 4 runs（`fp16 + int8_ours × {trec, vcsum}`）。可选扩展为 6 runs（加 `int4_mixed_kv × {trec, vcsum}`），但**未批准**，仅作参考。默认按 4 runs 执行。

## Aggregate 排除规则（强化 A 口径）

在 `aggregate_phase2_verify.py` 全量聚合时必须显式排除**所有 quarantine 目录**：

```python
# A 方案 quarantine 强制排除（2026-04-18 20:10）
# 所有 *_20260418_quarantine 目录全量排除，不依赖 metric_name 过滤
QUARANTINE_DIRS = {
    'phase2_c2b_llama8b_extended_20260418_quarantine',
    'phase2_7b_random_hardening_20260418_quarantine',
    'phase2_c3_qwen14b_20260418_quarantine',
    'phase2_batch4_extend_tasks_7b_20260418_quarantine',
    'phase2_batch5_extend_tasks_8b_20260418_quarantine',
    'phase2_c4_mistral7b_20260418_quarantine',
    'phase2_trec_vcsum_sanity_20260418_quarantine',
}
# aggregator 的 --sweep_dirs 必须显式过滤掉这些目录
```

## 审计签名

- 版本：A 方案口径 v1
- 生成时间：2026-04-18 20:10
- 替代文件：本文件（同名）的 19:50 B 方案版本
- 相关 known-issue：`docs/phase2_6_int8_ours_known_issue.md`（A 方案口径）

---

## 废弃的 B 方案口径（历史档案，仅供追溯）

> 以下 B 方案原口径在 2026-04-18 20:10 被用户明确拒绝，保留仅用于审计溯源。
> **不要**引用 B 方案的任何结论（「148 clean 保留」「3 runs 排除」等），论文与 aggregate 一律按 A 方案。

**废弃内容摘要**：
- ❌ 「CLEAN int4_mixed_kv 148 runs 保留使用」→ **A 方案拒绝**，全部 quarantine
- ❌ 「只排除 3 个 int8_ours failed runs」→ **A 方案拒绝**，不依赖 `metric_name='failed'` 过滤
- ❌ 「不扩散（修 int8_ours bug out of scope）」→ **A 方案拒绝**，Step 0 必修
- ❌ 「改 sanity 用 fp16 + int4_mixed_kv 作 baseline」→ **A 方案拒绝**，sanity 必须包含 int8_ours 本身

B 方案原文见 git `d9cb50e` 之前版本或 `archive/` 归档。
