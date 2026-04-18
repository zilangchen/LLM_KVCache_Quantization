# Phase 2 编号 6：Layer-wise Allocator MVP（2026-04-18）

**实验目录**：`experiments/2026-04-18_phase2_allocator_mvp/`
**对应 Plan**：`.claude/plans/partitioned-sparking-newt.md` Phase 2 编号 6（Codex 修订版 v2）
**前置**：Phase 1 Gate 5 PASS（2026-04-18 06:01）

## 目的与假设

**目的**：将 attention-KL lens 从"解释器"升级为"决策器"——验证"信号最强的 top-k 层多分配 bit，质量 > 随机分配 bit"这个 lens→policy 升级的第一个可证伪假设。

**主要假设**（M4 硬 Gate）：
- H1：BAKV Top-3（attention-KL 选层）平均分 > Random-3（随机选层）
- H2：BAKV Top-3 至少 2/3 tasks 胜出 Random-3

**次要假设**（M4 次 Gate）：
- H3：BAKV Top-3 > Heuristic Top-3（位置启发式 {0, L//2, L-1}）——验证 lens 优于纯位置先验

## 变量（完美对照设计）

| 维度 | 取值 |
|---|---|
| 模型 | `Qwen/Qwen2.5-1.5B-Instruct` |
| 任务 | `narrativeqa`、`hotpotqa`、`gov_report` |
| kv_mode（固定） | `int4_mixed_kv`（所有 5 policies 共享） |
| allocator policy | Uniform INT4 / Uniform INT8 / BAKV Top-3 / Heuristic Top-3 / Random-3 (seed=42) |
| avg_bits | uniform_int4=4.0 / uniform_int8=8.0 / 3 non-uniform = 4.429（相同 budget 控制变量） |
| protected_layers | BAKV `{0, 1, 15}` / Heuristic `{0, 14, 27}` / Random `{2, 18, 20}`（唯一变量） |
| 样本数 | `n=50`/组合 |
| Seed | `1234`（greedy, temp=0, top_p=1, top_k=0） |

## 关键代码改动

- `src/cache/mixed_kv_cache.py`：`__init__` 新增 `per_layer_bits: Optional[List[Tuple[int,int]]]` + `_resolve_bits(layer_id)` 派发；**默认 None 保 backward compat**（eval_ppl 等现有调用不变）
- `src/engine/generate_loop.py`：`int4_mixed_kv` 分支新增 `policy_json` 参数透传
- `scripts/eval_longbench.py`：新增 `--policy_json` CLI
- `scripts/adaptive/behavior_aligned_allocator.py`：新增 `policy_heuristic`（等距选层）
- `tests/test_mixed_kv_cache_per_layer.py`：5 单测（含 backward compat + 非法值校验）
- `scripts/phase2_gen_policies.sh` + `phase2_allocator_mvp.sh` + `aggregate_phase2.py`（含 timestamp dedup）

## M4 实际结果（🟢 硬 Gate PASS，次 Gate 边缘）

### 主表（权威：merged dedup，15 unique rows）

| task | metric | Uniform INT4 | Uniform INT8 | BAKV Top-3 | Heuristic-3 | Random-3 (seed42) |
|---|---|---|---|---|---|---|
| gov_report | ROUGE-L | 5.896 | 9.298 | **8.979** | 9.009 | 6.233 |
| hotpotqa   | F1      | 2.421 | 4.969 | **4.637** | 4.653 | 2.958 |
| narrativeqa| F1      | 5.107 | 6.364 | **6.773** | 6.345 | 4.799 |

### 硬 Gate（BAKV > Random 且 ≥2/3 tasks 胜）：🟢 **3/3 PASS**

- gov_report: BAKV=8.979 vs Random=6.233（**+44%**）
- hotpotqa:   BAKV=4.637 vs Random=2.958（**+57%**）
- narrativeqa: BAKV=6.773 vs Random=4.799（**+41%**）
- 平均：BAKV=6.796 vs Random=4.663（**+46%** 压倒性 lens 信号）

### 次 Gate（BAKV > Heuristic）：⚠️ **边缘（1/3 胜）**

- gov_report: BAKV=8.979 vs Heuristic=9.009 → **-0.3%**（tie）
- hotpotqa:   BAKV=4.637 vs Heuristic=4.653 → **-0.3%**（tie）
- narrativeqa: BAKV=6.773 vs Heuristic=6.345 → **+7%**（BAKV 胜）

## 关键发现

1. **F1（硬 gate PASS）**：attention-KL lens 显著强于随机，"behavior-aligned adaptive allocation 有效"可写入论文主结论
2. **F2（次 gate 边缘，必须诚实报告）**：BAKV `{0,1,15}` vs Heuristic `{0,14,27}` 只共享 layer 0，性能几乎一致——**"保护 3 层"比"具体保护哪 3 层"更重要**。layer-selection 有 soft boundaries
3. **F3（Pareto 上界观察）**：Uniform INT8 (9.30) vs BAKV (8.98) 差 3.4% → "3 层保护" 已接近 full-INT8 的 96.6% 质量
4. **F4（ENG-045-v2 & Codex 巡检）**：
   - M3 首轮遇 bug：`grep -c "ENG-045"` 匹配 0 次返回 exit 1，`pipefail + set -e` 致脚本提前退出；修复 `|| true` 后 M3-v2 完整跑通
   - Codex 巡检提醒 aggregate 的"timestamp dedup"——避免旧 uniform_int4_k4v4 CSV 污染主表；aggregate_phase2.py 的 dedup 逻辑 drop 3 older rows, kept 15 unique

## 复现步骤

```bash
# 1. W1 代码扩展 + W6 单测（远端）
pytest tests/test_mixed_kv_cache_per_layer.py -v   # 5/5 PASS

# 2. W3 5 policy JSON 生成
bash scripts/phase2_gen_policies.sh

# 3. 冒烟（n=5 × BAKV × narrativeqa）
CUDA_VISIBLE_DEVICES=0 python3 scripts/eval_longbench.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct --kv_mode int4_mixed_kv \
    --policy_json artifacts/allocator/bakv_top3.json \
    --longbench_source jsonl --longbench_dataset_path /root/autodl-tmp/longbench_data/data \
    --longbench_tasks narrativeqa --longbench_max_samples 5 --seed 1234 \
    --out_dir results/phase2_smoke/

# 4. M3 3 GPU 按任务并行（每卡 5 policies 串行）
CUDA_VISIBLE_DEVICES=0 bash scripts/phase2_allocator_mvp.sh narrativeqa &
CUDA_VISIBLE_DEVICES=1 bash scripts/phase2_allocator_mvp.sh hotpotqa &
CUDA_VISIBLE_DEVICES=2 bash scripts/phase2_allocator_mvp.sh gov_report &
wait   # ~15 分钟

# 5. 聚合 + Gate 判定
python3 scripts/aggregate_phase2.py \
    --runs_dir results/phase2_allocator_mvp/ \
    --out_csv results/phase2_summary.csv \
    --out_md docs/phase2_main_table.md
```

## 解锁与下一步

M4 硬 Gate PASS → 允许进编号 7（Budget Sweep + 消融 1）。

次 Gate 边缘信号促发编号 7 的核心追问：
- **attention-KL lens 在哪些 budget (k) 下相对位置启发式有独占价值？**
- **max vs mean vs random 三种 sensitivity 代理哪个更 principled？**

详见 Plan 文件编号 7 段（Codex 2026-04-18 06:55 修订版详细 ExecPlan）。

## 主要教训（供后续流水线参考）

1. **pipefail + grep -c 0 匹配** 致脚本提前退出——所有 shell 脚本里的 grep -c 必须 `|| true` 托底（已加入 `memory/debugging-patterns.md §12`）
2. **聚合主键必须 dedup**——实验重启后会留旧 CSV；aggregate 函数必须按 `(key) × timestamp` 保留最新（已加入 aggregate_phase2.py）
3. **Codex 巡检价值**：实验跑完立即看输出目录，比跑完聚合才发现重复行早（Codex 在 M3 中途就发现了 18 CSV vs 预期 15）
