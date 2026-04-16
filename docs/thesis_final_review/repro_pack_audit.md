# Repro Pack Audit — 复现包静态审计（P0.5 产物）

> **范围**：`results/final/final_scripts/reproduce/{01..10}*.sh` + `scripts/*.py` + `configs/exp_matrix.yaml` + `configs/snapshots/exp_matrix_*.yaml`
>
> **三类审计维度**：(1) CLI/API 对齐；(2) 实验语义对齐；(3) 冻结目录命名/落点对齐
>
> **结论门禁**：`PASS` / `NEEDS-FIX` / `NEEDS-DISCLOSE`

---

## 首件：Phase 1 疑似 CRITICAL 重核

| 编号 | 项目 | 核实命令 | 现状 | 结论 |
|-----|------|---------|------|------|
| TR-0002 | abstract {zh,en} 7B PPL "6.0%" vs tab:rolealign-results "6.1%" | `Read abstract_zh.tex:20-41 + abstract_en.tex:30-52 + ch4_experiments.tex:1355-1380` | **abstract_zh:31 "7B: 6.0\\%"** / **abstract_en:39 "7B: 6.0\\%"** / ch4:1362 表算 (7.58-7.14)/7.14 = 6.16% ≈ **6.1%** | **仍 open**，已填入 issues.md |
| TR-0003 | abstract 关键词数 | `Read abstract_zh.tex:39 + abstract_en.tex:48-50` | zh 6 个（大语言模型；键值缓存；量化；行为对齐校准；非对称量化；GQA 架构）；en 6 个（Large Language Model; Key-Value Cache; Quantization; Behavior-Aligned Calibration; Asymmetric Quantization; GQA Architecture） | **仍 open**，已填入 issues.md |

---

## 候选表 C1-C6 核实结果

| # | 脚本 | 审计维度 | 结论 | 证据 |
|---|------|---------|------|------|
| C1 | `01_calibrate.sh` | 校准链 JSON 产出 ↔ 02/04 `--calib_file` | **NEEDS-FIX (H)** | (a) 01 产出 3 个 JSON；`kv_calib_kl_selected_v3_quick.json` / `kv_calib_kl_int4_selected.json` 与 `configs/exp_matrix.yaml` L56/231 等对齐，`kv_calib_rolealign_1p5b.json` 与 `configs/exp_matrix_rolealign.yaml` L58/72 对齐。(b) **但 05/07/08 引用 `kv_calib_rolealign_{1p5b,7b,8b,14b}_v3.json`（有 `_v3` 后缀）**；01 产出的 `kv_calib_rolealign_1p5b.json` **无 `_v3`**，命名不匹配。(c) **01 不产出 7B/8B/14B 校准** — L56-58 全部是注释；05/06/07/08 启动后 set -euo pipefail 会因 calib_file 不存在而 fail。(d) calib samples/seq_len（INT8:16/8192, INT4:32/8192, RA:16/512）与论文 ch3:152 "128 条 WikiText-103 样本" / tab:app-search-space "N=128, seq_len=512 tokens" **不一致** — 需 disclose |
| C2 | `02_int8_mainline.sh` / `03_kv_ablation.sh` / `04_int4_rolealign.sh` | config YAML + run_names 一致性 | **PASS** | 02 `--config configs/exp_matrix.yaml` + `--run_names fp16_kv_long,int8_baseline_long_torch,int8_ours_long_fused,kivi_style_int8_long,...throughput_8k_b{1,4,8,16}` 全部匹配 exp_matrix.yaml L740/866/751/1117/288-480/1140-1180。03 `configs/snapshots/exp_matrix_{b10_sens,mixed_kv,qwen25_7b,llama31_8b}_*.yaml` 全部存在；`--run_names k_only_int8_long,v_only_int4_long,k_int4_v_int8_long` 匹配 mixed_kv_1p5b L72/85/98；跨模型 runs 匹配 7B_v1 L393/403/417 + 8B_v1 L401/411/425。04 `--config configs/exp_matrix_rolealign.yaml` + `--run_names int4_ours_sym_ref,int4_ours_asym_long,int4_ours_asym_ba_long,kivi_style_int4_ref` 匹配 L40/55/69/82。`--out_dir` 均指向 `results/final/final_data/{int8_mainline,kv_ablation,int4_rolealign}/runs/`，落点正确 |
| C3 | `05_backend_tpot.sh` | 五后端传参（fp16/kivi/torchref/triton_ra/fi） | **NEEDS-FIX (H)** 传参本身 PASS，但依赖缺失 calib | L44-65 五分支传参全部与 profile_latency.py argparse 对齐（`--model_id/--kv_mode/--calib_file/--decode_attn_impl/--seq_len/--gen_len/--runs/--warmup/--seed/--save_csv/--out_dir`），循环变量 `$MTAG/$MODEL/$CALIB` 正确消费。落点 `results/final/final_data/backend_comparison/runs/tpot_{fp16,kivi,torchref,triton_ra,fi}_{1p5b,7b,8b,14b}/` 与 INDEX.md L55 匹配。**但 C1 的 calib 缺失问题导致：1p5b/7b/8b 三个模型的 torchref/triton_ra/fi 三条 branch 无法执行**（14b 存在 calib 所以可跑）。kvi/fp16 分支无 calib 依赖，可跑 |
| C4 | `06_14b_full.sh` | calib_file/context_len/k_bits/v_bits/out_dir | **PASS** | 14B calib (`kv_calib_rolealign_14b_v3.json`) 存在于 artifacts/。L17 `RA14` 变量、L42/52 `CL`、L53/54 `SL`、L71-73 `KB`/`VB`/`TAG` 循环变量全部正确使用。eval_ppl.py/eval_needle.py/eval_ruler.py/eval_longbench.py 的 `--max_samples/--chunk_size/--context_len/--num_depths/--seq_len/--ruler_context_len/--kv_mode int4_mixed_kv/--k_bits/--v_bits` 全部在 argparse 注册。落点 `backend_comparison/runs/{ppl,needle,ruler,longbench,ppl_ablation}_*_14b_*` 与 INDEX L35/42/43/44 匹配 |
| C5 | `07_longseq_tpot.sh` / `08_8b_longseq.sh` / `09_fp16_ruler_baseline.sh` / `10_7b_kl_vs_mse.sh` | `--out_dir` 存在 + 语义对齐 | **07/08 NEEDS-FIX (H)** 依赖 C1 缺失 calib；**09 PASS**；**10 PASS** 但 Step 1 内联生成 MSE calib | 07/08 `--calib_file` 分别引用 `kv_calib_rolealign_{1p5b,7b,14b,8b}_v3.json`，其中 1p5b/7b/8b v3 不存在（同 C1），14B OK；fp16/kivi 分支无 calib 依赖可跑。09 只用 `kv_mode fp16`，无 calib 依赖，完全自包含。10 `MSE_CALIB="artifacts/kv_calib_mse_7b_int4_rolealign_v1.json"` + `KL_CALIB="artifacts/kv_calib_rolealign_7b_v3.json"`：MSE 通过 Step 1 内联生成（L31-38 `if [ ! -f "$MSE_CALIB" ]; then python3 scripts/calibrate_behavior.py ...`，参数 `--loss_function mse --quant_bits 4 --role_aware_axes --int4_search --samples 128 --seq_len 2048`，与 calibrate_behavior.py argparse 完全对齐）；但 KL 7B v3 仍需外部产出，与 C1 问题耦合。全部 4 个脚本 `--save_csv --out_dir "$outdir"` 传参 CLI 正确 |
| C6 | `final_scripts/` 自包含性 | README 披露 + 论文附录同步 | **NEEDS-DISCLOSE (H)** | README.md L37-44 声明 "`reproduce/*.sh` 是冻结编排入口 ... 这些脚本当前仍调用仓库根目录 `scripts/*` 作为真实 runner；`final_scripts/core\|eval\|configs` 主要用于审计和冻结快照，不是完全独立的 runtime bundle ... 它们不承诺与历史冻结目录逐个同名"；L65-69 披露 `tpot_bd_*` 和 `longbench_official_*` 不在复现范围内。**但论文附录（appendix.tex）无任何对应披露**：L35 仅有"所有实验均采用确定性设置..."一句通用可复现承诺；ch4:60 声称"所有实验结果可通过项目仓库中的原始 CSV 文件复现"，**与 final_scripts subset 的实际范围不一致**。另外 01_calibrate.sh 实际 samples 为 16/32（v3_quick），与 ch3:152 / ch3:166 / tab:app-search-space 声称的 "128 条 WikiText-103 样本" 不符，附录需同步披露。BitDecoding subset 在 `backend_comparison/runs/{longbench,needle,ppl}_bd_1p5b_s*/` 确实存在 20+ 目录但 05 脚本不复现 — 论文附录未说明 |

---

## Subset 定位

**reproduce = 论文主线 subset，非 frozen 1:1。**
- `backend_comparison/runs/{longbench,needle,ppl}_bd_1p5b_*` 等 BitDecoding runs 保留为**历史数据**
- `backend_comparison/runs/longbench_official_{7b,8b}_s1234` 因 HF_HUB_OFFLINE 限制未完成
- 不纳入 reproduce 闭环
- 必须在**论文附录（实验环境/复现说明节）**同步披露此 subset 选择 — 当前**未披露**

---

## 最终结论

- [ ] **PASS** — 候选表全部 ✓，论文可直接进入 P1
- [x] **NEEDS-FIX** — 有 H 级问题，在 P2 前修复（C1 校准产物命名+缺失、C3/C5 依赖性 fail-fast）
- [x] **NEEDS-DISCLOSE** — 已知限制写入论文附录（C6 subset + samples 数）

---

## 修复动作（按严重度列）

### HIGH（H）— P2 前必须处理

1. **TR-0010（C1）校准产物命名与 `_v3` 后缀不匹配**
   - 问题：01_calibrate.sh 产出 `kv_calib_rolealign_1p5b.json`（无 `_v3`），但 05/07/08 引用 `kv_calib_rolealign_1p5b_v3.json`
   - 修复选项 A：把 01_calibrate.sh L53 的 `--calib_out` 改为 `kv_calib_rolealign_1p5b_v3.json` + 对齐 `configs/exp_matrix_rolealign.yaml` L58/72 指向 `..._v3.json`
   - 修复选项 B：把 05/07/08 的 `CALIB_1P5B` 改为 `kv_calib_rolealign_1p5b.json`（去掉 `_v3` 后缀）
   - 推荐 B（改动范围小，只动 reproduce/ 3 个脚本）

2. **TR-0011（C1/C3/C5）01_calibrate.sh 缺失 7B/8B/14B 校准脚本**
   - 问题：L56-58 7B/8B/14B 校准代码被注释掉；但 05/06/07/08/10 依赖 `kv_calib_rolealign_{7b,8b,14b}_v3.json`（其中 14B 存在 artifacts/，7B/8B 不存在）
   - 14B 校准必须在 01 中补齐命令（14B 已存在 artifacts/ 但脚本不应假设）；7B/8B 补齐或在对应脚本的"前置依赖"段显式给出
   - 或在 README.md 中显式说明"01_calibrate.sh 只产出 1.5B；7B/8B/14B 校准需用户另行执行"并给出命令

3. **TR-0012（C6）论文附录缺失 subset / 非自包含 / samples 数披露**
   - 问题：appendix.tex 第一节无对应 README.md L37-44、L65-69 的披露；ch4:60 的"所有实验结果可通过项目仓库中的原始 CSV 文件复现"与实际 subset 范围冲突
   - 修复：在 `appendix.tex` 第 "实验环境详情" 节之后新增一小节（如 "\section{复现脚本与覆盖范围}"），披露：
     - `results/final/final_scripts/reproduce/01..10_*.sh` 是冻结编排 subset，覆盖论文主线
     - 不复现范围：BitDecoding `*_bd_*`、`longbench_official_*`
     - 复现脚本依赖 `scripts/*.py` runner（非独立 runtime bundle）
     - 真实校准 samples（v3_quick 模式下 INT8=16/INT4=32/RA=16）；论文 ch3:152/166/tab:app-search-space "N=128" 对应 B10 消融设置，v3_quick 用 16 是经消融确认不敏感后的效率选择

### MEDIUM（M）— 可进入 P1 再修

4. **TR-0013（C6）ch4:60 "所有实验结果可通过项目仓库中的原始 CSV 文件复现" 过度承诺**
   - 问题：与 reproduce/ subset 范围冲突，可能被答辩评委质疑"全量复现是否等于 subset 复现"
   - 修复：改为"主线实验结果可通过 `results/final/final_scripts/reproduce/` 下的冻结脚本复现；历史探索性 runs 见 `results/final/final_data/` 归档"

### LOW（L）— 仅注释瑕疵

（无 LOW 级）
