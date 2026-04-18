# Known Issue: `int8_ours` run-time RuntimeError (A 方案口径, 2026-04-18 20:10 改写)

> **口径**：按用户 2026-04-18 选择的 **A 方案** — 修 bug + 严格串行重跑 + quarantine 不恢复。
> 本文档原 B 方案口径（「不修 cache 代码」「用 fp16+int4 替代 int8」）已作废，见下方 §「废弃的 B 方案口径」。

## 症状（机器 grep 确认）

在长 prompt（seq ≥ 2000）+ `kv_mode=int8_ours` 下，样本级别触发：

```
RuntimeError: The expanded size of the tensor (2) must match the existing size (8)
  at non-singleton dimension 1.
  Target sizes: [1, 2, 4096, 4, 1]
  Tensor sizes: [1, 8, 1, 4, 1]
```

- **Target sizes** `[1, 2, ...]` 中的 `2` = Qwen2.5-1.5B 的 H_kv = 2（正确）
- **Tensor sizes** `[1, 8, ...]` 中的 `8` = **错误来源的 scale shape**（Mistral-7B / Llama-3.1-8B / Qwen2.5-14B 都是 H_kv=8）

## 真根因假设（Day 1 Step 1 证据驱动，2026-04-18 20:10）

> **推翻原假设**（"int8_ours GQA expand code bug"），Day 1 Step 1 最小复现证据表明：

### 证据 1：默认路径 `artifacts/kv_calib_kl.json` 当前不存在

```bash
$ ls artifacts/kv_calib_kl.json
ls: cannot access 'artifacts/kv_calib_kl.json': No such file or directory
```

但 sanity 15:50 运行时必然存在（否则报 `FileNotFoundError` 而非 `RuntimeError`）。

### 证据 2：我的最小复现用**显式正确 1.5B INT8 calib** 无法触发 bug

```bash
python3 scripts/eval_longbench.py \
    --kv_mode int8_ours \
    --calib_file artifacts/kv_calib_kl_1p5b_int8_v5_fixed.json  # 显式指定 1.5B calib
    ... (其他参数与 sanity 相同)
# 结果: F1=0.0 但未 RuntimeError crash（模型退化输出但不崩溃）
```

### 证据 3：原 sanity 脚本**没有传 `--calib_file`**

```bash
# scripts/phase2_trec_vcsum_sanity.sh
python3 scripts/eval_longbench.py \
    --kv_mode int8_ours \
    --longbench_tasks $TASK \
    --longbench_max_samples $N_SAMPLES \
    # ... 无 --calib_file 参数 → 走 default 路径 artifacts/kv_calib_kl.json
```

### 证据 4：`calibrate_behavior.py --out` 参数被当成 directory（已知 bug）

Phase 2.6 daemon 运行期间，14B / Mistral-7B / 3B 的 3 个 wrapper（`phase2_calibrate_{14b,mistral7b,3b}.sh`）错误地传了 `--out`：
```bash
python3 scripts/calibrate_behavior.py --model_id <X> --out artifacts/kv_calib_kl_<X>_int8.json
```

但 `calibrate_behavior.py` 的**正式 CLI 参数**只有 `--out_dir` 与 `--calib_out`，**从不存在 `--out`**。argparse 默认启用 `allow_abbrev=True`，因此 `--out` 被前缀匹配到 `--out_dir`：`$OUT_CALIB` 的 JSON 路径被当作输出目录传给 `args.out_dir` 并被 `mkdir -p` 建成真目录，而 `args.calib_out` 保持 `None` → 原脚本 L1272 的 default fallback 触发，calibration 始终写入硬编码共享路径 `artifacts/kv_calib_kl.json`。

所以**每次**重新 calibrate 大模型，都会**覆盖** default 路径的内容。

### 推断时序

1. 15:50 — sanity 启动前，default 路径已被 Phase 2.5 的某次 calibrate 写入 H_kv=8 的模型 calib（Mistral-7B / LLaMA-8B 之一）
2. 15:50 — sanity int8_ours × trec × n=50 加载 default → scale shape H=8，target tensor H_kv=2（1.5B）→ 每个 sample broadcast mismatch → 50 failures
3. 15:58 — 14B calibrate 再次覆盖 default，内容继续是 H_kv=8（14B 也是 H_kv=8）
4. 之后我做 14B calib 修复时 rename 了 default 到别的名字，导致当前 default 路径不存在

## 双重 bug 清单（已修复，2026-04-18 20:25）

| Bug | 位置 | 真实修复 |
|---|---|---|
| **B1a** wrapper 传 `--out`（不存在于 CLI） | `scripts/phase2_calibrate_{14b,mistral7b,3b}.sh` | `--out "$OUT_CALIB"` → `--calib_out "$OUT_CALIB"`（首要修复点）|
| **B1b** argparse 默认 `allow_abbrev=True` 把 `--out` 前缀匹配到 `--out_dir` | `scripts/calibrate_behavior.py` L1048 | `ArgumentParser(..., allow_abbrev=False)` — 静默前缀匹配永远失效 |
| **B1c** `--calib_out is None` 时硬编码 fallback 到共享 `artifacts/kv_calib_kl.json` | `scripts/calibrate_behavior.py` L1271-1272 | 改 `raise ValueError("--calib_out is required ...")` + 目录误用检测 |
| **B2** quant 路径 expand 前不校验 scale.shape[H] 与 model heads 对齐 | `src/quant/_common.py:94` `_normalize_static_scale` | 前置 `_infer_scale_heads` + heads 校验 + `ValueError` 携带 `context` 审计（expected / actual / model_id / calib_path / layer_id）|

**B1 是污染源**（错配 calib 被写入共享 default），**B2 是漏洞**（让污染传播到 expand 深处才炸）。**真实修复组合：wrapper 首要修（B1a），本体 allow_abbrev=False + 禁 default fallback 作 defense-in-depth（B1b/B1c），B2 负责把任何未来错配变成 fail-fast 可审计异常。**

## 触发条件（精确版）

| 条件 | 是否必需 |
|---|---|
| `--kv_mode int8_ours` 且**不传** `--calib_file` | ✅ 必需（走 default 路径） |
| `artifacts/kv_calib_kl.json` 存在且是**错模型**的 calib（H 不匹配目标模型） | ✅ 必需 |
| 运行的模型 H_kv ≠ calib 记录的 H | ✅ 必需 |
| 长 prompt | ❌ 不必需（n=50 sample 里 seq=2058 也触发） |

## 受影响的 kv_mode（修订）

| kv_mode | cache class | 是否受影响 |
|---|---|---|
| `int8_ours` | `INT8KVCache` | 🔴 受影响（走 default calib 路径时） |
| `int4_mixed_kv` | `MixedKVCache` | ⚠️ **可能同样受影响**（如走类似 default calib 加载路径且无 shape 校验），待验证 |
| `int4_ours_asym` | `RoleAwareAsymKVCache` | ⚠️ 待验证 |
| `kivi_style` | `KIVIStyleKVCache` | ✅ 运行时 absmax/min，不读 calib 文件 |
| `fp16` | `FP16KVCache` | ✅ 无 calib |

> **注**：原 B 方案假设「int4_mixed_kv 严格不受影响」——A 方案口径下必须重新验证，不默认 trust。

## 处理方式（A 方案，修订后 — 2026-04-18 20:25 状态同步）

1. ✅ **物理 quarantine**：所有 Phase 2.6 违规窗口内 run 已隔离（见 `phase2_6_contamination_audit.md`，7 目录 171 runs）
2. ✅ **Day 1 Step 1 completed**：最小复现 + 带行号 stack trace，精确定位 `src/quant/_common.py:94` expand 点
3. ✅ **Step 0 completed (B1 + B2 + 最小验证)**：
   - B1a fix：`calibrate_behavior.py` `allow_abbrev=False` 防 argparse prefix match
   - B1b fix：3 个 wrapper（phase2_calibrate_{14b,mistral7b,3b}.sh）`--out` → `--calib_out`（首要修复点，Codex 纠偏确认）
   - B1c fix：`calibrate_behavior.py` 禁 default fallback，`--calib_out is None` 时 raise ValueError
   - B2 fix：`src/quant/_common.py` `_normalize_static_scale` 前置 heads 校验 + audit context（expected / actual / model_id / calib_path / layer_id）
   - 最小验证：B2 fail-fast 正反回归 PASS；B1 wrapper 真实 calibration 输出落在 `/tmp/test_calib_B1_fix.json`，`artifacts/kv_calib_kl.json` 不再被污染
4. ⏸️ **Wave 2 sanity 严格重跑（用户批准口径 = 4 runs）**：
   - **核准执行版本**：`fp16 + int8_ours × {trec, vcsum} = 4 runs`
   - **可选扩展（需用户再次批准）**：加入 `int4_mixed_kv × {trec, vcsum}` 变 6 runs（A 方案拒绝 B 方案「用 fp16+int4 替代 int8_ours」，但是否扩入 int4_mixed_kv 作为对照尚未批准）
   - **默认按 4 runs 执行**，6 runs 仅作可选扩展建议标注
5. ⏸️ **Mistral smoke 严格重跑**：通过才启 Mistral full
6. ⏸️ **逐个 wave 串行重跑**：Wave 2 → Mistral smoke → Wave 1 / 3 / 4 / 7a / 7b / Mistral full
7. **论文 Threats to Validity**：记录双重 bug + A 方案 quarantine 纪律

## 重跑验收条件（每 wave）

- 0 Traceback / 0 RuntimeError / 0 failed metric
- 0 OOM / 0 Killed / 0 zero-byte CSV
- Int8_ours 在相同 task 上 F1 > 0 且合理范围内（对比 fp16 退化）
- iteration.md Timeline 条目记录 wall-clock + 验收证据

---

## 废弃的 B 方案口径（历史档案）

> 以下 B 方案原文（2026-04-18 19:50）在 2026-04-18 20:10 被用户明确拒绝：

**废弃内容摘要**：
- ❌ 「不修 cache 代码（out of scope；本 issue 为 pre-existing）」→ **A 方案拒绝**，必修
- ❌ 「改 sanity 用 fp16 + int4_mixed_kv 作 baseline」→ **A 方案拒绝**，sanity 必须含 int8_ours
- ❌ 「int8_ours bug 严格孤立在 INT8KVCache 代码路径」→ **A 方案拒绝**，未对 int4_mixed_kv 做 shape 校验审计
- ❌ 「论文主张均基于 int4_mixed_kv，不依赖 int8_ours」→ 仍然成立，但**不作为跳过修 bug 的理由**
- ❌ 「本 issue 不影响任何已产出的 scale × aggregation 结论」→ **A 方案拒绝**，所有违规窗口 run 都 quarantine

B 方案原文见 git `d9cb50e` 之前版本或 `archive/` 归档。
