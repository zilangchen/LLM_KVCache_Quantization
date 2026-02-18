---
description: 自动开发、测试、交付完整功能的工作流
---

# KV Cache 量化项目 - 自动开发工作流

专为本项目定制的自动化开发流程，严格遵循 `objective.md` 和 `AGENT_TASKLIST.md` 规范。

---

## 执行前检查（强制）

// turbo
### Step 0A: Agent 协作与远程规范（先做这个）
```bash
# 新 agent session 必须先读规范
sed -n '1,200p' AGENTS.md
sed -n '1,200p' docs/AGENT_README.md

# 每次都要检查并阅读 .agent/skills 里的相关 SKILL
ls .agent/skills
sed -n '1,200p' .agent/skills/remote-server/SKILL.md
sed -n '1,200p' .agent/skills/long-running-task/SKILL.md

# GPU/模型下载/长任务：先做远端连接健康检查（GPU 可见）
ssh -p 31867 root@region-42.seetacloud.com "echo 'SSH OK' && nvidia-smi -L"
```

// turbo
### Step 0B: 环境与上下文检查
```bash
# 读取项目目标和任务清单
cat objective.md | head -100
cat AGENT_TASKLIST.md | head -50

# 读取开发记录
cat development_record.md | tail -50

# 检查当前里程碑进度
cat lang.md | grep -A 20 "进度追踪"
```

---

## 开发流程

### Step 1: 需求分析与计划
```
1. 确认用户需求对应哪个 Milestone（A-J）
2. 检查 AGENT_TASKLIST.md 中该 Milestone 的验收标准
3. 确认输出文件路径与 CSV schema（如需要）
4. 创建实现计划（重大变更需用户确认）
```

// turbo
### Step 2: 接口对齐检查
```python
# 确保新代码遵循稳定接口（objective.md Section: 稳定接口）
# Engine: generate(prompts, generation_config, kv_mode, runtime_config)
# KVCache: append(layer_id, k, v), get_kv(layer_id)
# Quantizer: quantize_kv(k, v, meta), dequantize_kv(qk, qv, qmeta)
# Kernels: Triton wrapper 必须在 src/kernels/
```

// turbo
### Step 3: 代码实现
```
1. 遵循 PEP8（79 字符行宽）
2. 添加完整的类型注解
3. 编写清晰的 docstring
4. 添加异常处理（OOM/CUDA/网络失败）
5. 使用项目现有依赖（torch/transformers/triton）
```

// turbo
### Step 4: 质量检查
```bash
# Linter 检查
python -m flake8 <文件路径> --max-line-length=120
python -m black --check <文件路径>
python -m isort --check-only <文件路径>

# 类型检查（如可用）
python -m mypy <文件路径> --ignore-missing-imports
```

// turbo
### Step 5: 单元测试
```bash
# 运行相关测试
pytest tests/ -v -k "<模块名>"

# 如果没有现成测试，运行基本验证
python -c "from src.<模块> import <类>; print('Import OK')"

# 数值一致性检查（量化相关）
# 确保误差在可接受范围内
```

// turbo
### Step 6: 集成验证
```bash
# 端到端测试（基于里程碑验收标准）
# Milestone A: python scripts/smoke_test.py
# Milestone B-D: 自定义 generation loop + 评测脚本
# Milestone E-F: kv_mode 切换测试
# Milestone G: Triton kernel 数值对齐
```

// turbo
### Step 7: 错误修复循环
```
IF 测试失败:
  1. 分析错误根因（1-2 句话）
  2. 定位问题代码位置
  3. 实施最小修复
  4. 重新运行测试
  5. 最多重试 3 次
```

---

## 交付与记录（强制）

// turbo
### Step 8: 更新开发记录
```bash
# 获取当前时间
date '+%Y-%m-%d %H:%M:%S'

# 在 development_record.md 添加记录
# 格式：# <Antigravity YYYY-MM-DD HH:MM:SS>
```

// turbo
### Step 9: 更新进度追踪
```
更新 lang.md：
1. 勾选完成的子任务
2. 在"更新记录"中追加本次完成内容
3. 记录产出物路径和关键指标
```

// turbo
### Step 10: 结果输出检查
```bash
# 确认结果符合项目规范
ls -la results/runs/
# CSV 必须包含字段：
# run_id, model_id, kv_mode, quant_bits, clip_percentile, group_size,
# dtype, seq_len, gen_len, batch, ttft_ms, tpot_ms, tok_per_s,
# gpu_mem_peak_mb, timestamp, git_commit
```

---

## 结果交付清单

```
✅ 代码符合 PEP8 规范
✅ 通过单元测试
✅ 符合稳定接口约定
✅ 输出结构化结果（CSV/JSON）
✅ 更新 development_record.md
✅ 更新 lang.md 进度追踪
✅ 提示用户是否 Git 提交
```

---

## 使用方式

直接描述你想实现的功能，我会自动：
1. 确认对应的 Milestone 和验收标准
2. 按规范实现代码
3. 运行测试验证
4. 自动修复问题
5. 更新项目记录
6. 交付可用结果
