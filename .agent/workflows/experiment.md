---
description: 运行实验、收集数据、生成图表的工作流
---

# KV Cache 量化项目 - 实验工作流

专门用于运行评测实验和生成论文数据。

---

## 实验入口（唯一）

- 实验矩阵：`configs/exp_matrix.yaml`
- 结果输出：`results/runs/`, `results/tables/`, `results/plots/`

---

## 实验流程

// turbo
### Step 1: 实验配置检查
```bash
# 确认实验矩阵
cat configs/exp_matrix.yaml

# 检查关键参数
# - seed=1234
# - temperature=0.0, top_p=1.0, top_k=0 (greedy)
# - kv_mode: fp16 / int8_baseline / int8_ours
```

// turbo
### Step 2: 环境记录
```bash
# 记录实验环境
nvidia-smi --query-gpu=name,memory.total --format=csv > env/gpu_info.csv
pip freeze > env/requirements_freeze.txt
git rev-parse HEAD > env/git_commit.txt
```

### Step 3: 运行实验（建议使用 screen）
```bash
# 询问用户是否使用 screen
screen -S exp_run

# 运行实验矩阵
python scripts/run_experiments.py --config configs/exp_matrix.yaml

# 或者分步运行
python scripts/profile_latency.py --config <config>
python scripts/profile_memory.py --config <config>
python scripts/eval_ppl.py --config <config>
python scripts/eval_needle.py --config <config>
```

// turbo
### Step 4: 结果验证
```bash
# 检查输出文件
ls -la results/runs/

# 验证 CSV schema
head -1 results/runs/*.csv
# 必须包含：run_id, model_id, kv_mode, quant_bits, clip_percentile,
# group_size, dtype, seq_len, gen_len, batch, ttft_ms, tpot_ms,
# tok_per_s, gpu_mem_peak_mb, timestamp, git_commit

# 验证数据完整性
python -c "import pandas as pd; df=pd.read_csv('results/runs/<file>.csv'); print(df.info())"
```

// turbo
### Step 5: 生成图表
```bash
# 生成论文图表
python scripts/make_plots.py --input results/runs/ --output results/plots/

# 预期输出：
# - memory_vs_seqlen.png
# - throughput_vs_seqlen.png
# - needle_accuracy.png
# - ppl_comparison.png
```

// turbo
### Step 6: 记录实验结果
```
更新 lang.md：
1. 记录运行命令
2. 记录产出物路径
3. 记录关键指标（吞吐、显存、质量）
4. 记录 needle 分数趋势
```

---

## 评测口径（固定）

| 评测项 | 设置 |
|--------|------|
| 解码策略 | greedy (temp=0.0) |
| 随机种子 | 1234 |
| PPL 数据集 | wikitext-2-raw-v1 |
| Needle | 合成 needle-in-a-haystack |
| 计时同步 | torch.cuda.synchronize() |

---

## 结果字段（CSV Schema）

```
run_id, model_id, kv_mode, quant_bits, clip_percentile, group_size,
dtype, seq_len, gen_len, batch, ttft_ms, tpot_ms, tok_per_s,
gpu_mem_peak_mb, timestamp, git_commit
```

---

## 消融实验矩阵

```yaml
kv_modes: [fp16, int8_baseline, int8_ours]
seq_lens: [1024, 2048, 4096, 8192, 16384, 32768]
group_sizes: [32, 64, 128]
clip_percentiles: [99.0, 99.5, 99.9]
use_attn_temperature: [true, false]
```
