*(旧计划内容已清除，以下为历史归档标记)*
- `scripts/phase1_resume_1p5b.sh` — L4, L10, L12
- `scripts/phase1_resume_7b.sh` — L4, L10, L12
- `scripts/phase1_resume_8b.sh` — L4, L10, L12
- `scripts/defense_prep_all.sh` — L72-84（sed 替换 → 参数化调用）

**改法（以 phase1_1p5b.sh 为例）**：
```bash
# 旧（L4, L10, L12）：
export CUDA_VISIBLE_DEVICES=0
CALIB="artifacts/kv_calib_rolealign_1p5b.json"
RD="results/emnlp_rolealign_v2"

# 新（优先级：位置参数 > 环境变量 > 默认值）：
GPU_ID="${1:-${CUDA_VISIBLE_DEVICES:-0}}"
export CUDA_VISIBLE_DEVICES="$GPU_ID"
CALIB="${2:-${PHASE1_CALIB:-artifacts/kv_calib_rolealign_1p5b_v3.json}}"
RD="${3:-${PHASE1_RESULTS_DIR:-results/emnlp_rolealign_v4}}"
```

这样既支持 `bash phase1_1p5b.sh 1 /path/to/calib /path/to/results`，
也支持 `CUDA_VISIBLE_DEVICES=1 bash phase1_1p5b.sh`（外层已设环境变量），
还支持裸跑（全用默认值）。

其他脚本同理，默认 CALIB 路径按模型区分（1p5b/7b/8b），默认 RD 统一为 v4。

**调用方式**：
```bash
bash scripts/phase1_1p5b.sh 0 artifacts/kv_calib_rolealign_1p5b_v3.json results/emnlp_rolealign_v4 &
bash scripts/phase1_7b.sh   1 artifacts/kv_calib_rolealign_7b_v3.json   results/emnlp_rolealign_v4 &
bash scripts/phase1_8b.sh   2 artifacts/kv_calib_rolealign_8b_v3.json   results/emnlp_rolealign_v4 &
```

---

## F2: eval_ppl.py 校准文件显式化（warning + 命令层 fail-fast）

### 问题
`eval_ppl.py` L204-208：当 `--calib_file` 未指定时，int8_ours 默认回退到 `artifacts/kv_calib_kl.json`——这不是 v3_quick，也不是 v5_fixed。用户传了 `--calib_file` 且文件不存在时已有 FileNotFoundError（L210-213），但未传时的静默回退是危险的。

### 修改方案（两层防护）
**层 1（eval_ppl.py 内部）**：对 "ours" 系列 kv_mode，当用户未传 --calib_file 时发出显式 warning：

**修改文件**：`scripts/eval_ppl.py` L203-208 区域

**改法**：
```python
# L203-208 区域改为：
import warnings
# 注意：int4_ours_asym / int4_ours_asym_ba 走独立路径（L367+），
# 不经过 load_calibration()，不要放进这个集合
CALIBRATED_MODES = {"int8_ours", "int4_ours", "int4_fused",
                    "int4_ours_mixed", "int4_kivi_aligned"}
if kv_mode in CALIBRATED_MODES and calib_file is None:
    if kv_mode == "int8_ours":
        default_calib = os.path.join("artifacts", "kv_calib_kl.json")
    else:
        default_calib = os.path.join("artifacts", "kv_calib_kl_int4_selected.json")
    warnings.warn(
        f"No --calib_file specified for calibrated mode '{kv_mode}'. "
        f"Falling back to default: {default_calib}. "
        f"Pass --calib_file explicitly to avoid ambiguity.",
        UserWarning,
    )
elif calib_file is None:
    default_calib = None
else:
    default_calib = None  # calib_file already set
calib_path = calib_file or default_calib
```

**层 2（shell 脚本层 fail-fast）**：在 phase1_*.sh 中添加校准文件存在性检查：
```bash
# 在脚本开头、实际实验之前：
if [ ! -f "$CALIB" ]; then
  echo "FATAL: Calibration file not found: $CALIB" >&2
  exit 1
fi
```
这样即使 Python 内部 warning 被日志淹没，shell 层也会在第一个命令前就拦截。

eval_needle.py、eval_ruler.py、eval_longbench.py 经 Codex 确认无同类静默回退问题，不需修改。

---

## F3: 回归测试

### 问题
CAL-034（RoPE fallback）和 EVL-047/048/070 的修复没有回归测试。直接上 12.5h 大跑风险高。

### 修改方案
在现有测试文件中追加最小测试用例：

**文件 1**：`tests/test_calibrate_behavior.py` — 追加 _get_rope_for_position 测试
```python
def test_get_rope_for_position_with_model_backbone_fallback():
    """CAL-034: rotary_emb moved to model.model in transformers 4.48+."""
    # 用 mock 模拟 attn.rotary_emb=None 但 model_backbone.rotary_emb 存在的场景
    ...
```

**文件 2**：`tests/test_eval_scripts.py` — 追加 EVL 修复测试
```python
def test_cwe_target_frequency_dominates():
    """EVL-047: target words must be more frequent than distractors."""
    ...

def test_mk_niah_needles_at_different_positions():
    """EVL-048: multiple needles must be inserted at distinct positions."""
    ...

def test_s_niah_contains_match_auxiliary():
    """EVL-070: S-NIAH should report contains_match alongside exact_match."""
    ...
```

**文件 3**：`tests/test_eval_ppl_guardrails.py` — 追加校准回退 warning 测试
```python
def test_calibrated_mode_warns_on_missing_calib_file():
    """EVL-037/F2: calibrated modes should warn when no --calib_file."""
    ...
```

---

## F4: RULER 白名单决策

### 决策
- **论文主文**：只报 S-NIAH + MK-NIAH（修复后可信的子任务）
- **附录**：报全 4 子任务 + 注释 CWE/VT 已知局限
- **脚本**：仍跑全 4 子任务（数据完整性），但增加注释说明论文选择
- **聚合脚本**：在 aggregate_results.py 或 generate_thesis_report.py 中增加 `RULER_WHITELIST = ["s_niah", "mk_niah"]` 过滤

### 修改方案
在 phase1_*.sh 的 eval_ruler 调用处增加注释说明：
```bash
# NOTE: 跑全 4 子任务收集完整数据；论文主文只报 s_niah + mk_niah
# CWE/VT 的已知局限见 EVL-047/073/081，附录展示
```

在 `scripts/aggregate_results.py` 中增加 RULER 白名单过滤逻辑（产出 thesis-facing `ruler_task_summary` 子集）。注意：`generate_thesis_report.py` 只吃已聚合的 claim 表，没有子任务过滤入口，白名单必须落在上游的 aggregate 层。

**结构性修正**：F1 参数化完成后，大跑计划中的 G0-4（远程 sed 改脚本路径）不再需要。`defense_prep_all.sh` 应改为带参数调用 phase1 脚本，而非 sed 替换内部变量。

---

## 执行顺序

1. F1: 修改 6 个 phase1 脚本（参数化）
2. F2: 修改 eval_ppl.py 校准回退逻辑（+ 检查其他 eval 脚本）
3. F3: 追加回归测试（3 个测试文件）
4. F4: RULER 白名单注释 + 聚合脚本过滤
5. 验证 Python：`python3 -m compileall -f scripts/ tests/` 全部通过
6. 验证 Shell：`bash -n scripts/phase1_1p5b.sh scripts/phase1_7b.sh scripts/phase1_8b.sh scripts/phase1_resume_1p5b.sh scripts/phase1_resume_7b.sh scripts/phase1_resume_8b.sh` 全部通过
7. 验证测试：本地 `pytest tests/test_calibrate_behavior.py tests/test_eval_scripts.py tests/test_eval_ppl_guardrails.py -v`（如可跑）

---

---
---

# 答辩补救大计划（终极版 v3）

> F1-F4 前置修复已完成（✅）。本计划基于修复后的脚本和已确认的事实制定。

## 已确定事实

- **硬件**：3 × NVIDIA H20 (98GB)，SSH port 31867
- **RoPE**：CAL-034 已修复（commit 278f71d），场景 β 确认 → v2/v3_quick 全部缺 RoPE → 需 v3 重校准
- **阻塞 EVL**：5 个已修复（EVL-037/047/048/053/070），待远程 pytest 验证
- **T3 数据**：全部用 v2 缺 RoPE 产物 → 需用 v3 产物全量重跑
- **RULER 白名单**：主文 S-NIAH + MK-NIAH，附录全 4 子任务（F4 已落地）
- **脚本参数化**：phase1_*.sh 已支持 GPU_ID/CALIB/RD 三参数（F1 已落地）
- **已完成**：叙事重构 ✅ | AI 消除 ✅ | 字体 ✅ | hero figure ✅ | 答辩 QA 初版 ✅

## 待定因素（决定大计划分支走向）

| # | 待定 | 影响 | 确定时间 |
|---|------|------|---------|
| ❶ | Codex review 反馈 | F1-F4 是否需追加修改 | 今天 |
| ❷ | 远程 smoke test | 修复是否真正生效 | rsync 后 ~30min |
| ❸ | KIVI 残差补偿可行性 | Exp-4 编码 or 降级 | Day 5-7（读论文） |
| ❹ | Exp-2 INT8 校准对比 | 主表数据是否切换 → 预案 B | Day 8-9 |
| ❺ | Exp-4 KIVI vs RA | 论文叙事方向 → 预案 C | Day 11-14 |

---

## Gate 0：代码部署 + v3 校准 + 数据冻结（Day 1-4）

### G0-1. rsync F1-F4 + CAL-034 + EVL 修复到远程

```bash
bash scripts/rsync_gate.sh
rsync -avz --exclude='results/' --exclude='.git/' \
  ~/Desktop/LLM_KVCache_Quantization/ root@<host>:/root/LLM_KVCache_Quantization/
```

### G0-2. 远程验证

```bash
# pytest 全量
pytest tests/ -v

# RoPE 修复验证
python3 -c "
from scripts.calibrate_behavior import _get_rope_for_position
from transformers import AutoModelForCausalLM
import torch
model = AutoModelForCausalLM.from_pretrained(
    'Qwen/Qwen2.5-1.5B-Instruct', torch_dtype=torch.float16, device_map='auto')
attn = model.model.layers[0].self_attn
dummy = torch.zeros(1,1,128, device='cuda', dtype=torch.float16)
pos = torch.tensor([[0]], device='cuda')
cos, sin = _get_rope_for_position(attn, dummy, pos, model_backbone=model.model)
assert cos is not None, 'RoPE still broken!'
print(f'RoPE OK: cos shape = {cos.shape}')
"
```

### G0-3. Smoke Test（~30min GPU）

**目的**：用最小成本验证 v3 校准 + EVL 修复是否真正生效。

```bash
# 1. 生成 1.5B v3 校准产物（~20min）
CUDA_VISIBLE_DEVICES=0 python3 scripts/calibrate_behavior.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --role_aware_axes \
  --role_aware_k_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
  --samples 128 --seq_len 512 --seed 1234 \
  --calib_out artifacts/kv_calib_rolealign_1p5b_v3.json

# 2. 用 v3 产物跑单 seed 短序列 RULER（验证 CWE/MK-NIAH 修复）
CUDA_VISIBLE_DEVICES=0 python3 scripts/eval_ruler.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
  --seq_len 4096 --seed 1234 --verbose

# 3. 用 v3 产物跑单 seed PPL（验证校准加载正常）
CUDA_VISIBLE_DEVICES=0 python3 scripts/eval_ppl.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
  --chunk_size 128 --seed 1234

# 4. 检查 v3 产物是否含 RoPE 标记
python3 -c "
import json
d = json.load(open('artifacts/kv_calib_rolealign_1p5b_v3.json'))
print(f'version={d.get(\"version\")}')
print(f'role_aware={\"role_aware\" in d}')
# 对比 v2 vs v3 的 k_scale 差异
"
```

**通过标准**：
- pytest 全量通过
- RoPE 返回 non-None cos/sin
- RULER CWE 得分 >0%（或至少模型输出合理）
- PPL 无 crash，值在合理范围
- v3 校准产物 version=4，含 role_aware section

**失败处理**：如任一项失败 → 停下来诊断，不启动全量重跑。

### G0-4. 生成全部 v3 校准产物（3 卡并行）

smoke test 通过后：
```bash
# GPU-0 已有 1p5b_v3（smoke test 生成的）
# GPU-1: 7B
CUDA_VISIBLE_DEVICES=1 python3 scripts/calibrate_behavior.py \
  --model_id Qwen/Qwen2.5-7B-Instruct \
  --role_aware_axes \
  --role_aware_k_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
  --samples 128 --seq_len 512 --seed 1234 \
  --calib_out artifacts/kv_calib_rolealign_7b_v3.json &

# GPU-2: 8B
CUDA_VISIBLE_DEVICES=2 python3 scripts/calibrate_behavior.py \
  --model_id /root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct \
  --role_aware_axes \
  --role_aware_k_percentile_candidates "95.0,97.0,99.0,99.5,99.9,100.0" \
  --samples 128 --seq_len 512 --seed 1234 \
  --calib_out artifacts/kv_calib_rolealign_8b_v3.json &

# 同时在 GPU-0 生成 INT8 v5 修正产物
CUDA_VISIBLE_DEVICES=0 python3 scripts/calibrate_behavior.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --loss_function kl --quant_bits 8 \
  --samples 128 --seq_len 512 \
  --calib_out artifacts/kv_calib_kl_1p5b_int8_v5_fixed.json &

wait
```

**墙钟**：~1h（3 卡并行）

### G0-5. 数据冻结

- 论文现有数字与 emnlp_final_raw/ 对齐确认
- Tag `thesis-data-freeze-v2`
- 新实验写入 `results/emnlp_rolealign_v4/`（RoleAlign v3 产物）和 `results/emnlp_defense_v1/`（INT8 对比等）

---

## Phase 1：核心实验（Day 5-14）

> **3 卡调度原则**：
> - 质量评测：3 卡各跑 1 个模型并行
> - TPOT profiling：3 卡全部独占
> - 校准：单卡独占（3 卡分 3 模型并行）

### Exp-1. T3 全量重跑（v3 产物 + EVL 修复）🔴

```bash
# 3 卡并行
bash scripts/phase1_1p5b.sh 0 artifacts/kv_calib_rolealign_1p5b_v3.json results/emnlp_rolealign_v4 &
bash scripts/phase1_7b.sh   1 artifacts/kv_calib_rolealign_7b_v3.json   results/emnlp_rolealign_v4 &
bash scripts/phase1_8b.sh   2 artifacts/kv_calib_rolealign_8b_v3.json   results/emnlp_rolealign_v4 &
wait
```
**墙钟**：~12.5h | **结果**：`results/emnlp_rolealign_v4/runs/`

### Exp-2. INT8 修正校准对比 🔴

```bash
# v5_fixed（含 RoPE）vs v3_quick（缺 RoPE），3 seeds × PPL + Needle
for SEED in 1234 1235 1236; do
  CUDA_VISIBLE_DEVICES=0 python3 scripts/eval_ppl.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct --kv_mode int8_ours \
    --calib_file artifacts/kv_calib_kl_1p5b_int8_v5_fixed.json --seed $SEED \
    --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_int8_v5_1p5b_s${SEED}
  CUDA_VISIBLE_DEVICES=0 python3 scripts/eval_needle.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct --kv_mode int8_ours \
    --calib_file artifacts/kv_calib_kl_1p5b_int8_v5_fixed.json --seed $SEED \
    --save_csv --out_dir results/emnlp_defense_v1/runs/needle_int8_v5_1p5b_s${SEED}
done
```
**墙钟**：~2h

**⚠️ 预案 B**：差异 <0.1% → 附录对比表 | 修正版更好 → 切主表 | 修正版更差 → 两组都报告

### Exp-3. INT8-ours chunk_size=1 PPL 🔴

```bash
# 3 卡并行 3 模型 × 5 seeds，显式 --calib_file
for SEED in 1234 1235 1236 1237 1238; do
  CUDA_VISIBLE_DEVICES=0 python3 scripts/eval_ppl.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct --kv_mode int8_ours \
    --calib_file artifacts/kv_calib_kl_selected_v3_quick.json \
    --chunk_size 1 --seed $SEED \
    --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_int8_cs1_1p5b_s${SEED}
done &
# GPU-1: 7B 同理（--calib_file 用 7B 的校准产物）
# GPU-2: 8B 同理
```
**墙钟**：~2h

**⚠️ 预案 A**：<1% → 附录强化 | 1-5% → 限定 Claim 1 | >5% → 修改表述

### Exp-4. KIVI 增强 + 公平对比 🔴

**Step 1（Day 5-7，本地）**：读 KIVI §3.3 → 评估残差补偿编码量
- ≤3 天 → 编码 `kivi_style_cache.py` + 单测 + rsync
- >3 天 → 降级为论文理论影响分析

**Step 2（Day 8-10，GPU）**：KIVI-enhanced vs RoleAlign-v3
```bash
# 3 模型 × 3 seeds × (PPL cs=128 + PPL cs=1 + Needle)
# 3 卡并行
```
**墙钟**：~3h

**Step 3（Day 10-11，可选）**：LLaMA-8B KIVI 官方代码验证锚点 ~2h

**⚠️ 预案 C（最核心）**：

| 结果 | 论文定位 |
|------|---------|
| **RA > KIVI** | "BA 校准 + 诊断驱动双重优势"，贡献四强化 |
| **RA ≈ KIVI** | 价值 = 诊断动机 + cs=1 鲁棒性（KIVI cs=1 崩溃 9442） |
| **RA < KIVI** | 贡献重心转诊断框架，贡献四降为"验证性探索" |

### Exp-7. 官方 LongBench 子集验证 🔴（从 Phase 2 提升）

**目的**：堵住"合成源不可信"的最大攻击面。只需 3 个任务即可建立外部效度锚点。

```bash
# 在 T3 7B/8B 完成后的空闲 GPU 上跑（~2h）
# FP16 基线
python3 scripts/eval_longbench.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode fp16 --seed 1234 \
  --longbench_source hf \
  --longbench_tasks narrativeqa,hotpotqa,gov_report \
  --longbench_max_samples 50 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/longbench_official_fp16_1p5b

# INT8-ours
python3 scripts/eval_longbench.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int8_ours \
  --calib_file artifacts/kv_calib_kl_selected_v3_quick.json \
  --seed 1234 \
  --longbench_source hf \
  --longbench_tasks narrativeqa,hotpotqa,gov_report \
  --longbench_max_samples 50 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/longbench_official_int8_1p5b
```

**论文改动**：附录增加"官方 LongBench 对照验证"表，正文引用一句。

---

### Exp-8. KV 噪声诊断（G2+G5）🔴

**目的**：
- G2：验证 GQA 1/H_kv 独立性假设——测量跨 KV 头的 INT4 量化误差相关性
- G5：量化 Key vs Value 噪声对注意力输出的相对贡献

```bash
# ~30min，在任意空闲 GPU 上跑
bash scripts/diagnose_kv_noise.sh 0
```

**输出**：`results/emnlp_defense_v1/kv_noise_diagnostic.json`

**论文改动**：
- G2 结果写入 ch4 GQA 噪声分析段：如果 correlation < 0.3 → "实证验证了独立性假设的合理性"
- G5 结果写入 ch4 K/V 消融讨论段：V-noise perturbation 数值佐证"Value 对量化鲁棒"

**注意**：G1（KL vs percentile 隔离对比）**不做新实验**——消融表已显示 KL 单独不优于 percentile（Needle 20% vs 100%），KL 的价值在于诊断工具角色，W-8 已正确定位。G3（FlashInfer 对比）不可行，论文 Limitations 处理。

---

### Exp-5. RULER 修复验证 🔴

```bash
python3 scripts/eval_ruler.py --kv_mode fp16 --ruler_tasks cwe,mk_niah \
  --seq_len 4096 --seed 1234 --verbose
```
CWE >0% → 附录恢复 4 子任务 | 仍 0% → 只报白名单

### Exp-6. TPOT 独占重跑 🔴

3 卡全空后独占串行跑。~4h 墙钟。

---

## Phase 1 同步写作（Day 5-14）

| 任务 | 内容 | 耗时 |
|------|------|------|
| W-1 🔴 | 效率 framing：以 FP16 为基准 + batch>1 数据 | 2h |
| W-2 🔴 | S-NIAH 评分差异说明 | 0.5h |
| W-3 🟡 | Related Work 补 TensorRT/QuaRot/FlashInfer | 2h |
| W-4 🟡 | SQNR 推导统一 289x/257x | 1h |
| W-5 🟡 | inv_tau 精简 | 1h |
| W-6 🔴 | RoleAlign vs KIVI 公平讨论（等 Exp-4） | 2h |
| W-7 🟡 | 贡献叙事微调（等 Exp-4） | 1h |
| W-8 🔴 | KL vs MSE/percentile 校准策略对比叙述增强：在 ch4 敏感性分析中明确 int8_ours vs int8_baseline 的对比本质是 KL 目标 vs percentile 目标，引用消融表中 adaptive 是决定因素但 KL 提供更优 scale 选择基础 | 1h |

---

### Exp-11. K/V 消融 PPL（攻击面 6）🔴

**目的**：补充 K/V 消融在 PPL 上的证据。当前消融只有 RULER/LongBench，缺 PPL。

```bash
bash scripts/exp_kv_ablation_ppl.sh [GPU_ID]
# 跑 4 组：K@INT4/V@FP16, K@FP16/V@INT4, K@INT8/V@FP16, K@FP16/V@INT8
```

**GPU 时间**：~2h
**论文改动**：ch4 K/V 消融段增加 PPL 列

---

### Exp-9. Batch>1 INT4-RoleAlign profiling 🟡

**目的**：展示高 batch 下 INT4-RA 的显存优势转化为吞吐优势。

```bash
# 在 Exp-6 TPOT 独占期间一并跑（同一独占窗口）
for BATCH in 1 4 8 16; do
  CUDA_VISIBLE_DEVICES=0 python3 scripts/profile_latency.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode int4_ours_asym --quant_bits 4 \
    --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
    --seq_len 8192 --gen_len 128 --batch $BATCH \
    --warmup 3 --runs 5 --save_csv \
    --out_dir results/emnlp_defense_v1/runs/latency_ra_batch${BATCH}_1p5b
done
# FP16 对照
for BATCH in 1 4 8 16; do
  CUDA_VISIBLE_DEVICES=0 python3 scripts/profile_latency.py \
    --model_id Qwen/Qwen2.5-1.5B-Instruct \
    --kv_mode fp16 \
    --seq_len 8192 --gen_len 128 --batch $BATCH \
    --warmup 3 --runs 5 --save_csv \
    --out_dir results/emnlp_defense_v1/runs/latency_fp16_batch${BATCH}_1p5b
done
```

**GPU 时间**：~2h（在 TPOT 独占窗口内跑）

### Exp-10. chunk_size=1 INT4-RoleAlign vs KIVI 🟡

**目的**：量化 RoleAlign 在 cs=1 下的鲁棒性优势（KIVI cs=1 崩溃 PPL 9442）。

```bash
# INT4-RoleAlign cs=1（如附录没有数据，需要补跑）
CUDA_VISIBLE_DEVICES=0 python3 scripts/eval_ppl.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode int4_ours_asym --quant_bits 4 \
  --calib_file artifacts/kv_calib_rolealign_1p5b_v3.json \
  --chunk_size 1 --max_samples 100 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_ra_cs1_1p5b

# KIVI cs=1 对照（如需）
CUDA_VISIBLE_DEVICES=0 python3 scripts/eval_ppl.py \
  --model_id Qwen/Qwen2.5-1.5B-Instruct \
  --kv_mode kivi_style \
  --chunk_size 1 --max_samples 100 --seed 1234 \
  --save_csv --out_dir results/emnlp_defense_v1/runs/ppl_kivi_cs1_1p5b
```

**GPU 时间**：~1h

---

## Phase 2：增强实验 + INT4 Kernel（Day 15-22）

### E-2. Forward vs Reverse KL 消融 🟡

1.5B INT8，对比 forward KL vs reverse KL 校准的 PPL/Needle 差异。
**GPU 时间**：~1h

### E-3. n=10 seeds 🟡

Claim 1 核心指标（PPL + Needle）增加 seed 1239-1243。
**GPU 时间**：~2h（3 卡并行）

### E-4. INT4 Triton Kernel 🔴（方案 B：数据冻结后实现）

**目标**：在 Triton kernel 内实现 INT4 in-kernel unpacking，消除延迟退化。

**实现步骤**（Day 15-18）：
1. Day 15：理解 INT8 kernel 内存布局 + 设计 INT4 unpack 策略
2. Day 16：实现 in-kernel bit unpack（`(packed >> 4) & 0xF` / `packed & 0xF`）
3. Day 17：数值正确性验证（对比 torch_ref，max diff < 1e-3）
4. Day 18：性能 profiling（TPOT 对比 FP16 / INT8 fused / INT4 fused）

**成功标准**：
- INT4 fused TPOT ≤ FP16 TPOT（消除延迟退化）
- 数值一致性：与 torch_ref 的 max abs diff < 1e-3

**论文改动（如成功）**：
- ch3 增加 INT4 融合 kernel 设计小节
- ch4 更新 INT4-RoleAlign 效率数据
- 结论从"延迟增加 2-2.5x"改为"融合 kernel 消除延迟退化"

**如果失败**：论文保持现有 Limitations 描述，不影响已冻结数据。

### E-5. Batch>1 INT4 Fused Profiling（依赖 E-4）

如果 INT4 Triton kernel 完成，用 fused 路径重跑 batch=1/4/8/16 profiling。
**GPU 时间**：~2h

> 注：E-1 官方 LongBench 已提升到 Phase 1（Exp-7）。

---

## Phase 3：答辩准备（Day 23-28+）

- **D-1**：答辩 Q&A 更新（Obsidian 已有基础上补新数据）
- **D-2**：答辩 PPT 7 张核心幻灯片
- **D-3**：论文终版（LaTeX + 数字一致性）

---

## 3 GPU 调度甘特图

```
         Day  1   2   3   4   5   6   7   8   9  10  11  12  13  14
GPU-0:  [rsync+pytest ][smoke+v3校准 ][Exp-3 cs=1→Exp-2→T3 1.5B    ][Exp-4 KIVI  ]
GPU-1:  [   (等待)     ][v3校准 7B   ][Exp-1 T3 7B        ][Exp-7 LB][Exp-4 KIVI  ]
GPU-2:  [   (等待)     ][v3校准 8B   ][Exp-1 T3 8B                  ][Exp-4 KIVI  ]
                                                        ↓ Exp-6 TPOT 独占 ~4h
本地:   [Codex review  ][❶ 结果处理  ][W-1/W-2    ][KIVI编码 ][W-3~W-5      ]
                                                               [W-6/W-7 等Exp-4]

         Day 15  16  17  18  19  20  21  22  23  24  25  26  27  28+
GPU-0:  [KIVI官方验证 ][E-1 LongBench   ][         空                 ]
GPU-1:  [E-2 KL消融   ][E-1 LongBench   ][E-3 n=10                   ]
GPU-2:  [Exp-5 CWE    ][E-1 LongBench   ][E-4 INT4 kernel(可选)      ]
本地:   [叙事微调      ][D-1 Q&A        ][D-2 PPT     ][D-3 终版    ]
```

---

## GPU 时间汇总

| 实验 | 总 GPU·h | 墙钟(3卡) | 独占 |
|------|---------|-----------|------|
| G0 v3 校准 | ~2.5h | ~1h | 每卡独占 |
| G0 smoke test | ~0.5h | ~0.5h | 单卡 |
| Exp-1 T3 重跑 | ~27h | ~12.5h | 否 |
| Exp-2 INT8 对比 | ~2h | ~2h | 否 |
| Exp-3 INT8 cs=1 | ~6h | ~2h | 否 |
| Exp-4 KIVI 对比 | ~8h | ~3h | 否 |
| Exp-5 RULER | ~0.5h | ~0.5h | 否 |
| Exp-6 TPOT | ~4h | ~4h | **3卡全空** |
| E-1 LongBench | ~6h | ~2h | 否 |
| E-2 KL 消融 | ~1h | ~1h | 否 |
| E-3 n=10 | ~6h | ~2h | 否 |
| **总计** | **~64h** | **~31h** | |

---

## 重大发现与计划变更（2026-04-03 22:15 更新）

### 发现 1: v3 校准对 INT4-RA 零影响 → 论文数据全部有效
- PPL v3=10.5823 = v2=10.58（3 seeds 完全一致）
- 原因：INT4-RA 用 BA percentile (wMSE)，不依赖 RoPE/attention-KL
- **结论：v2 论文数据不需要更新，T3 v4 重跑主要用于 RULER/Needle 交叉验证**

### 发现 2: cs=1 PPL 数据全部来自 v1 INT8 回退 → 论文已修正
- v1 eval_ppl.py 缺 int4_ours_asym 分支，静默回退 INT8
- INT4-RA cs=1 真实 PPL > 10000（与 KIVI 9442 同级崩溃）
- **结论：cs=1 下 per-channel K Scale 是所有 INT4 非对称方法的共同边界**
- 论文附录已修正（commit d6546fb）

### 发现 3: KIVI 基线是简化实现（无 residual buffer, 无分组 scale 更新）
- 调研发现 KIVI 原版有 R=128 FP16 residual buffer + 分组 scale 更新
- 我们的 kivi_style 一次性冻结 scale → cs=1 崩溃是实现差异而非方法缺陷
- **结论：论文已披露差异（commit a2b05dd），Exp-4 residual 实验变得更重要**

### 发现 4: 文献调研强力支撑论文结论
- Needle 100% + PPL 13.7% 解耦：ACL Findings 2024 间接支持，我们是首个定量分析
- 规模依赖性 PPL 退化：ACL 2025 scaling law (ΔLoss~a/N^0.23) 完全吻合
- 对称 0% vs 非对称 100%：SageAttention2/CQ 理论解释 + 我们的 controlled ablation 最清晰
- KIVI PPL：KVTuner (ICML 2025) 独立复现 Qwen 上 KIVI 崩溃（PPL>220），我们的 RA 远优于此

### 发现 5: KIVI NameError bug 来自 residual_length 代码修改
- generate_from_ids() 无 runtime_config 参数 → KIVI/int4_kivi_aligned 全部 NameError
- 已修复（commit 3e1bed8），KIVI Needle 4K 10/10 pass 验证

---

### 任务状态重新评估

| 原计划任务 | 新状态 | 理由 |
|-----------|--------|------|
| Exp-1 T3 全量重跑 | ✅ **全部完成** (7B 28 + 8B 28 + 1.5B 28 = 84 dirs) | GPU 已释放 |
| Exp-2 INT8 v5 vs v3 | ❌ **降级** | dtype bug 需深入诊断 HF 4.57 cache API；v3 对 INT4-RA 零影响说明 INT8 差异也可能极小；降为 Phase 2 |
| Exp-3 INT8 cs=1 | ✅ 完成 | PPL=9.27 (+3.6%) |
| Exp-4 KIVI residual | 🔴→🟡 **重新定义** | 调研显示 KIVI 原版有 R=128 residual，Exp-4 应测试 residual_length=128 下 KIVI PPL/Needle 是否改善；代码已就绪但 NameError 刚修好 |
| Exp-5 RULER 修复 | ✅ 完成 | CWE 0%→38%，EVL-047 有效 |
| Exp-6 TPOT 独占 | 🔴 **待定** | T3 1.5B 完成后 GPU-0 空闲，但 GPU-1/2 仍有 cs=1 PPL；需等全空 |
| Exp-7 官方 LB | ✅ 完成 | INT8≈FP16 ±0.5pp |
| Exp-8 KV 诊断 | ✅ 完成 | G2 ρ=0.024, G5 K/V=2.15x |
| Exp-9 Batch>1 | 🟡 **在 TPOT 窗口** | 与 Exp-6 一起跑 |
| Exp-10 cs=1 RA vs KIVI | 🟡→**重新解读** | RA cs=1 也崩溃(>10000)，不再是 "RA 稳定" 的证据；现在用于验证 KIVI cs=1 旧数据(9442)的量级 |
| Exp-11 K/V 消融 PPL | ✅ 完成 | K@INT4 PPL=1291 |
| W-6 RA vs KIVI 讨论 | 🟡→**可部分完成** | 调研提供了文献框架，但需要 Exp-4 residual 数据做最终定位 |
| W-7 贡献叙事 | 🟡→**可开始** | 调研明确了贡献定位（诊断框架+controlled ablation），不完全依赖 Exp-4 |
| E-2 KL 消融 | 🟡→✅ **理论完成** | 论文已添加 forward KL 理论讨论 + ch5 未来工作，GPU 实验降为 Phase 3 |
| E-3 n=10 seeds | 🟡→❌ **取消** | PPL 确定性（CI=0），Needle CI 已够窄，n=10 无额外价值 |
| E-4 INT4 Triton kernel | 🟡→❌ **降级为论文 Limitations** | 时间不够，且调研显示不是答辩核心攻击面 |

---

## 验证 Checklist（2026-04-04 03:15 最终更新）

### Gate 0 ✅ | Gate 0+ ✅ — 全部完成，不再列出

### Phase 1 实验 — ✅ 全部完成
- [x] Exp-1 T3 全量重跑 ✅ (84 dirs)
- [x] Exp-3 INT8 cs=1 ✅ PPL=9.27
- [x] Exp-5 RULER FP16 修复 ✅ CWE 38%
- [x] Exp-6 TPOT 独占 ✅ 3模型×4配置=12 runs
- [x] Exp-7 官方 LongBench ✅ INT8≈FP16 ±0.5pp
- [x] Exp-8 KV 噪声诊断 ✅ G2 ρ=0.024, G5 2.15x
- [x] Exp-9 Batch>1 ✅ 4 batch×3 configs=12 runs
- [x] Exp-10 cs=1 全部 ✅ RA>10000, KIVI=10332, INT8=10073
- [x] Exp-11 K/V 消融 PPL ✅
- [x] cs 敏感性表完整 ✅ (cs=128/8/1 × FP16/INT8/RA/KIVI 全 12 格)
- [x] v3 校准验证 ✅ (PPL/Needle/RULER 全一致)
- [x] KIVI Needle 全上下文 ✅ (4K/8K/16K/32K 全 100%)
- [x] KIVI RULER 4K ✅ (S-NIAH 100%, MK 98.4%)

### Phase 1 实验 — 降级/跳过
- [ ] Exp-2 INT8 v5 vs v3 → ❌ dtype bug，降级（非核心）
- [ ] Exp-4 KIVI residual_length → 🟡 代码就绪但需修改 generate_from_ids（非核心）

### Phase 1 写作 — ✅ 全部完成
- [x] W-1~W-8 全部完成
- [x] W-6 RA vs KIVI 讨论 ✅ (commit dfffe4b，调研文献锚点)
- [x] W-7 贡献叙事 ✅ (commit dfffe4b，scaling law + CQ 引用)

### 论文改进（本会话 10 commits）
- [x] 14 项答辩批判回应（RQ, FP8, KL方向, 统计, KIVI 9442, 结语...）
- [x] cs=1 数据修正（v1 INT8 回退发现 + 论文更新）
- [x] cs 敏感性表完整（INT8 cs=8 + RA cs=8 + KIVI cs=1）
- [x] KIVI 差异声明扩展（residual buffer + 分组 scale）
- [x] 评测完整性段落（silent fallback lessons）
- [x] 调研文献集成（KVTuner, CQ, Scaling Law）

### 代码修复（本会话 7 commits）
- [x] KVC-090 CRIT + KVC-085/089/091/092 + NameError + GPU 脚本

### Phase 2 — 重新定义后状态
- [x] E-2 KL 消融 → ✅ 理论完成
- [x] E-3 n=10 → ❌ 取消
- [x] E-4 Triton kernel → ❌ 降级 Limitations
- [x] Exp-6 TPOT → ✅ 已完成
- [x] Exp-9 Batch>1 → ✅ 已完成

### 剩余工作（全部本地）

| # | 任务 | 优先级 | 预计 |
|---|------|--------|------|
| 1 | **data-freeze-v2 tag** | P0 | 5min |
| 2 | **Exp-6/9 TPOT 数据写入论文** | P0 | 2h |
| 3 | **cs 敏感性分析写入论文附录** | P0 | 1h |
| 4 | **Batch>1 效率分析写入论文** | P1 | 1h |
| 5 | **答辩 Q&A 更新**（调研+新数据） | P1 | 3h |
| 6 | **全文数字一致性最终检查** | P1 | 1h |
| 7 | **答辩 PPT** | P2 | 4h |
| 8 | Exp-2 dtype bug 诊断（可选）| P3 | — |
| 9 | Exp-4 KIVI residual（可选）| P3 | — |

### 本会话关键数据产出

**TPOT (3模型, v3校准, 独占GPU)**:
| 方法 | 1.5B | 7B | 8B |
|------|------|-----|-----|
| FP16 | 24.24ms | 24.46ms | 27.43ms |
| INT8-ours | 44.38ms | 45.72ms | 51.20ms |
| KIVI INT4 | 51.75ms | 54.54ms | 61.84ms |
| INT4-RA | 58.09ms | 62.06ms | 70.32ms |

**Batch>1 (1.5B, 8K seq)**:
| Batch | FP16 TPOT | INT4-RA TPOT | FP16 KV | RA KV | RA/FP16 KV |
|-------|-----------|-------------|---------|-------|------------|
| 1 | 24.78ms | 60.18ms | 227MB | 60MB | 3.78x |
| 4 | 24.65ms | 73.17ms | 910MB | 242MB | 3.76x |
| 8 | 24.21ms | 93.07ms | 1820MB | 484MB | 3.76x |
| 16 | 24.23ms | 134.46ms | 3640MB | 968MB | 3.76x |

**cs 敏感性**:
| 方法 | cs=128 | cs=8 | cs=1 |
|------|--------|------|------|
| FP16 | 9.31 | 9.31 | 9.31 |
| INT8 | 8.95 | 9.34 | 9.27 |
| INT4-RA | 10.58 | 62.10 | >10000 |
| KIVI | 10.43 | 60.54 | 10332 |
