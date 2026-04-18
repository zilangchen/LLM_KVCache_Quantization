# 🟢 Phase 8 自动队列完成报告

**启动时间**: (见日志头)
**完成时间**: 2026-04-18 13:44:46

## 阶段执行状态

| 阶段 | 状态 | CSV count |
|---|---|---|
| C2 LLaMA-8B k-scan (39 runs) | ✅ | 39 / 39 |
| 8B mean_k1 补丁 (条件) | ⏭️ SKIP | - |
| 8A batch1 (1.5B 60 runs) | ✅ | 60 / 60 |
| 8B batch2 (扩任务 32 runs) | ✅ | 28 / 32 |

## 判读决策

```
bakv_max_k1_avg=8.495 heur_k1_avg=8.383 rel=+1.3% need_patch=NO
```

## 最终 Gate Log

```
======================================================================
Phase 2 编号 8 边界型 Gate 判定（Codex 2026-04-18 09:15 版）
======================================================================

## F1 稳定（Random 多 seed）
结论: FAIL
2/3 (task,k) combos: BAKV > mean(Random 多 seed)
  gov_report/k=1: BAKV=7.777 vs mean(Random[8 seeds])=6.748 → +15.2%
  hotpotqa/k=1: BAKV=4.255 vs mean(Random[8 seeds])=3.565 → +19.3%
  narrativeqa/k=1: BAKV=4.354 vs mean(Random[8 seeds])=5.152 → +-15.5%

## F2 Scale-Shift（跨模型 best-k 分化）
结论: PASS
scale-shift 成立: 2 models, unique best-k=[5, 7]; ≥1 model 的 best-k 上 3/3 胜
  LLaMA-3.1-8B: best-k=7 → BAKV avg=8.577, Heuristic avg=8.647 (Δ=-0.8%, wins=1/3)
    k=1: BAKV=8.495 vs Heur=8.383 (Δ=+1.3%, w=3/3)
    k=3: BAKV=8.160 vs Heur=8.772 (Δ=-7.0%, w=0/3)
    k=5: BAKV=8.182 vs Heur=8.809 (Δ=-7.1%, w=0/3)
    k=7: BAKV=8.577 vs Heur=8.647 (Δ=-0.8%, w=1/3) ← best
  Qwen2.5-7B: best-k=5 → BAKV avg=7.029, Heuristic avg=6.785 (Δ=+3.6%, wins=3/3)
    k=1: BAKV=2.616 vs Heur=3.385 (Δ=-22.7%, w=0/3)
    k=3: BAKV=6.856 vs Heur=6.867 (Δ=-0.2%, w=2/3)
    k=5: BAKV=7.029 vs Heur=6.785 (Δ=+3.6%, w=3/3) ← best
    k=7: BAKV=6.945 vs Heur=6.920 (Δ=+0.4%, w=1/3)

## F2 扩任务（4 new tasks）
结论: PASS
BAKV ≥ Heuristic: 4/4 new tasks (gate: ≥3/4)
  dureader: BAKV=11.324 vs Heuristic=1.657
  lcc: BAKV=12.928 vs Heuristic=9.148
  trec: BAKV=0.000 vs Heuristic=0.000
  vcsum: BAKV=0.000 vs Heuristic=0.000

## F2 sample offset（方向一致）
结论: FAIL
BAKV vs Heuristic Δ 方向一致: 2/3 tasks
  gov_report: offsets=[(0, 2.173), (50, 1.6799), (100, 2.2358000000000002)] signs=[1, 1, 1] → 一致
  hotpotqa: offsets=[(0, 0.6413000000000002), (50, 0.6644999999999999), (100, 1.4050000000000002)] signs=[1, 1, 1] → 一致
  narrativeqa: offsets=[(0, 1.2207), (50, -0.2529999999999992), (100, 2.2478000000000002)] signs=[1, 1, -1] → 翻转

## F3 收敛（k≥3 tie）
结论: PASS
k≥3 收敛证据: 13/18 (model,task,k) tie (<5% Δ)
  ('Qwen2.5-7B', 'gov_report', 3): |Δ|=3.5% (tie)
  ('Qwen2.5-7B', 'gov_report', 5): |Δ|=0.2% (tie)
  ('Qwen2.5-7B', 'gov_report', 7): |Δ|=4.3% (tie)
  ('Qwen2.5-7B', 'hotpotqa', 3): |Δ|=2.5% (tie)
  ('Qwen2.5-7B', 'hotpotqa', 5): |Δ|=2.8% (tie)
  ('Qwen2.5-7B', 'hotpotqa', 7): |Δ|=2.9% (tie)
  ('Qwen2.5-7B', 'narrativeqa', 3): |Δ|=2.2% (tie)
  ('Qwen2.5-7B', 'narrativeqa', 5): |Δ|=8.6% (diff)
  ('Qwen2.5-7B', 'narrativeqa', 7): |Δ|=2.0% (tie)
  ('LLaMA-3.1-8B', 'gov_report', 3): |Δ|=3.1% (tie)
  ('LLaMA-3.1-8B', 'gov_report', 5): |Δ|=4.3% (tie)
  ('LLaMA-3.1-8B', 'gov_report', 7): |Δ|=2.0% (tie)
  ('LLaMA-3.1-8B', 'hotpotqa', 3): |Δ|=11.2% (diff)
  ('LLaMA-3.1-8B', 'hotpotqa', 5): |Δ|=9.5% (diff)
  ('LLaMA-3.1-8B', 'hotpotqa', 7): |Δ|=0.5% (tie)
  ('LLaMA-3.1-8B', 'narrativeqa', 3): |Δ|=8.0% (diff)
  ('LLaMA-3.1-8B', 'narrativeqa', 5): |Δ|=8.2% (diff)
  ('LLaMA-3.1-8B', 'narrativeqa', 7): |Δ|=3.7% (tie)

## [Legacy] F2 k=1 硬编码（已过时仅参考）
结论: FAIL
[legacy k=1 only] wins=0/3, avg Δ=-26.6%
  gov_report: BAKV=4.470 vs Heuristic=4.563 → Δ=-2.0%
  hotpotqa: BAKV=2.187 vs Heuristic=3.713 → Δ=-41.1%
  narrativeqa: BAKV=1.191 vs Heuristic=1.878 → Δ=-36.6%

======================================================================
综合: 3 PASS, 0 PENDING, 3 FAIL
🔴 编号 8 Gate FAIL → publishable finding + 论文缩窄到具体边界
======================================================================
```

## 产出文件

- 本地 CSV: `results/phase2_c2_local/phase2_verify_all.csv`
- 本地 Gate log: `results/phase2_c2_local/phase2_final_gate.log`
- 最终技术报告: `docs/phase2_verify_final_report.md`
- C2 中间报告: `docs/phase2_c2_report.md`
- 本脚本日志: `/tmp/auto_queue.log`

## 已停止，未触发

- ❌ NoLiMa / BABILong (编号 9)
- ❌ K/V 非对称 allocator (编号 10)
- ❌ 任何新方法实验

---
*生成于 `auto_queue_phase8.sh` (PID 20410)*
