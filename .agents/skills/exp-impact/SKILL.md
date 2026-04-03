---
name: exp-impact
description: >
  代码变更实验影响分析。对比本地 HEAD 与远端基线 commit，识别 eval/profile/calibrate 脚本变更，
  映射到受影响的实验类型，生成影响矩阵和可复制的 prompt 给远端 session。
  触发: "实验影响"、"需要重跑吗"、"rsync 前检查"、"exp impact"、"/exp-impact"。
---

# 代码变更实验影响分析

## 执行流程

### 1. 确定基线
```bash
# 远端最后同步的 commit（从 memory 或用户指定）
REMOTE_BASE="278f71d"  # 默认值，用户可覆盖
git log --oneline $REMOTE_BASE..HEAD | wc -l
git diff --stat $REMOTE_BASE..HEAD
```

### 2. 识别变更的关键脚本

| 脚本 | 影响的实验类型 |
|------|--------------|
| eval_ppl.py | PPL |
| eval_ruler.py | RULER (S-NIAH, MK-NIAH, CWE, VT) |
| eval_longbench.py | LongBench |
| eval_needle.py | Needle |
| profile_latency.py | Latency/TPOT |
| profile_memory.py | Memory |
| calibrate_behavior.py | 校准产物 |
| generate_loop.py | 所有实验的推理引擎 |
| patch_model.py | Fused decode 路径 |
| src/cache/*.py | Cache 行为 |
| src/quant/*.py | 量化精度 |

### 3. 分析每个变更的影响

对每个变更的脚本，分类:
- **数据正确性**: 评分逻辑、PPL 计算、指标定义变化 → 🔴 必须重跑
- **默认值变化**: argparse default 改变 → 🟡 仅影响直接 CLI 调用
- **防御性/安全性**: assert、try/except、warning → 🟢 不影响数据
- **性能**: 内存/速度优化 → 🟢 不影响数据正确性

### 4. 生成影响矩阵

```
| 实验类型 | 受影响？ | 原因 | 建议 |
|---------|---------|------|------|
| RULER   | 🔴/🟡/🟢 | EVL-XXX | 必须重跑/检查/安全 |
```

### 5. 输出 prompt

生成可直接复制给远端 session 的 Markdown 文本:
- 变更清单（Bug ID + 一句话描述）
- 影响矩阵
- 决策建议（哪些实验重跑、哪些安全）
- rsync 注意事项（排除 results/、.git/）

## 远端信息获取（可选）
```bash
sshpass -p '$PASSWORD' ssh -p $PORT root@$HOST \
  'nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader; \
   echo "---"; ps aux | grep python | grep -v grep | head -5; \
   echo "---"; tmux list-sessions 2>/dev/null'
```
SSH 信息见 `docs/autodl_server.md`。
