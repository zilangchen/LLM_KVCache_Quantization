# Wave 6 Offline Pre-Check Runbook

> 用途：在恢复 `Wave 6 (Qwen-3B sweep)` 之前，先验证离线缓存与运行环境，避免再次出现 `HF_HUB_OFFLINE=1` 下的模型缺失崩溃。

---

## 1. 背景

上一轮 `Wave 6` 的失败根因是：

- `phase2_calibrate_3b.sh` 启用了：
  - `HF_HUB_OFFLINE=1`
  - `TRANSFORMERS_OFFLINE=1`
- 远端当时没有本地缓存 `Qwen/Qwen2.5-3B-Instruct`
- `calibrate_behavior.py` 在 model load 阶段直接 `LocalEntryNotFoundError`

当前已知新状态：

- `Qwen/Qwen2.5-3B-Instruct` 的缓存目录**已经存在**
- 但在真正重启 `Wave 6` 前，仍必须做一次**同环境 offline pre-check**

---

## 2. 目标

在真正启动以下脚本前：

- `scripts/phase2_calibrate_3b.sh`
- `scripts/phase2_c5_qwen3b.sh`

先验证：

1. cache 路径存在
2. 离线模式下能成功 resolve config / tokenizer
3. 运行环境使用的是正确的 conda / python

---

## 3. 预检查步骤

### 3.1 进入与正式运行一致的环境

```bash
cd /root/LLM_KVCache_Quantization

if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then
  source /root/miniconda3/etc/profile.d/conda.sh
  conda activate base
fi

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/autodl-tmp/hf_cache
unset HF_ENDPOINT
```

### 3.2 检查缓存目录是否存在

```bash
find /root/autodl-tmp/hf_cache -maxdepth 4 -path '*Qwen2.5-3B-Instruct*'
```

预期：

- 至少看到：
  - `models--Qwen--Qwen2.5-3B-Instruct`
  - `snapshots/<hash>`

### 3.3 配置与 tokenizer 离线解析检查

```bash
python3 - <<'PY'
import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HOME"] = "/root/autodl-tmp/hf_cache"

from transformers import AutoConfig, AutoTokenizer

model_id = "Qwen/Qwen2.5-3B-Instruct"
cfg = AutoConfig.from_pretrained(model_id, local_files_only=True)
tok = AutoTokenizer.from_pretrained(model_id, local_files_only=True)

print("CONFIG_OK", getattr(cfg, "model_type", "unknown"))
print("TOKENIZER_OK", tok.__class__.__name__)
PY
```

预期：

- 输出 `CONFIG_OK`
- 输出 `TOKENIZER_OK`
- 不出现 `LocalEntryNotFoundError`

---

## 4. 强一点的检查（可选，但推荐）

如果希望进一步确认模型权重文件确实齐全，可检查 snapshot 下是否有权重索引或权重分片：

```bash
find /root/autodl-tmp/hf_cache -path '*Qwen2.5-3B-Instruct/snapshots/*' | head
find /root/autodl-tmp/hf_cache -path '*Qwen2.5-3B-Instruct/snapshots/*' | grep -E 'model|safetensors|index'
```

---

## 5. 启动门槛

只有满足以下条件，才应恢复 `Wave 6`：

1. `Wave 4 auto-k backfill` 已完成
2. `Wave 1 + Wave 4` 已做一轮统一 readout
3. 第 3 节的 offline pre-check 全部通过

---

## 6. 最小恢复顺序

推荐顺序：

1. 先跑 `phase2_calibrate_3b.sh`
2. 校验 `artifacts/kv_calib_kl_qwen25_3b_int8.json`
3. 再跑 `phase2_gen_sweep_policies_3b.sh`
4. 再启动 `phase2_c5_qwen3b.sh`

---

## 7. 后续修复建议

后续应把这套 pre-check 固化为显式门禁，而不是依赖人工记忆。最小修复方向是：

1. 在 `phase2_calibrate_3b.sh` 开头增加 cache existence 检查
2. 在 `HF_HUB_OFFLINE=1` 时，若本地快照不存在则直接 fail-fast
3. 让报错信息显式指出：
   - 缺哪个 model
   - 当前 `HF_HOME`
   - 当前是否 offline
