---
description: 实验复现保证 - 环境快照、配置验证、结果校验
---

# Reproducibility Skill

> 确保所有实验可复现，符合论文可重复性要求。

---

## 🎯 复现性三要素

1. **环境可复现**：相同的软硬件环境
2. **配置可追溯**：所有参数有记录
3. **结果可验证**：输出可对比校验

---

## 📋 环境快照

### 自动记录环境

// turbo
```bash
# 运行环境收集脚本
python scripts/collect_env.py

# 预期输出：env/versions.txt
# 包含：Python版本、PyTorch版本、CUDA版本、GPU型号、关键依赖版本
```

### 环境文件结构

```
env/
├── versions.txt          # 核心版本信息
├── requirements_freeze.txt  # pip freeze 输出
├── gpu_info.csv          # GPU 详细信息
└── git_commit.txt        # 当前 commit hash
```

---

## ⚙️ 配置验证

### 实验配置检查

// turbo
```python
def validate_config(config_path="configs/exp_matrix.yaml"):
    """验证配置文件符合项目规范"""
    import yaml
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # 必须存在的字段
    required = ['project', 'runtime', 'experiments']
    for key in required:
        assert key in config, f"缺少必需字段: {key}"
    
    # 固定参数检查
    runtime = config['runtime']
    assert runtime['seed'] == 1234, "seed 必须为 1234"
    assert runtime['decoding']['temperature'] == 0.0, "必须使用 greedy 解码"
    
    print("✓ 配置验证通过")
```

### Git 状态检查

// turbo
```bash
# 确保工作区干净
git status --porcelain

# 获取当前 commit
git rev-parse HEAD > env/git_commit.txt

# 记录未提交的修改（如有）
git diff > env/uncommitted_changes.patch
```

---

## 🔢 随机性控制

### 固定所有随机种子

```python
import random
import numpy as np
import torch

def set_seed(seed=1234):
    """固定所有随机种子"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    
    # 确保确定性（可能略微降低性能）
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
```

### 验证可重复性

// turbo
```python
def verify_reproducibility(run_fn, n_runs=3, seed=1234):
    """验证多次运行结果一致"""
    results = []
    for i in range(n_runs):
        set_seed(seed)
        result = run_fn()
        results.append(result)
    
    # 检查结果一致性
    for i in range(1, n_runs):
        assert results[i] == results[0], f"Run {i} 结果不一致"
    
    print(f"✓ {n_runs} 次运行结果一致")
```

---

## 📊 结果校验

### CSV Schema 验证

// turbo
```python
REQUIRED_FIELDS = [
    'run_id', 'model_id', 'kv_mode', 'quant_bits', 
    'clip_percentile', 'group_size', 'dtype', 'seq_len', 
    'gen_len', 'batch', 'ttft_ms', 'tpot_ms', 'tok_per_s',
    'gpu_mem_peak_mb', 'timestamp', 'git_commit'
]

def validate_csv_schema(csv_path):
    """验证 CSV 包含所有必需字段"""
    import pandas as pd
    df = pd.read_csv(csv_path)
    
    missing = set(REQUIRED_FIELDS) - set(df.columns)
    if missing:
        raise ValueError(f"缺少字段: {missing}")
    
    # 检查无空值
    for field in REQUIRED_FIELDS:
        if df[field].isna().any():
            print(f"⚠ 字段 {field} 含有空值")
    
    print(f"✓ CSV schema 验证通过: {csv_path}")
```

### 结果 Hash 校验

// turbo
```python
import hashlib

def compute_result_hash(csv_path):
    """计算结果文件的 hash 用于对比"""
    import pandas as pd
    df = pd.read_csv(csv_path)
    
    # 排除时间戳等易变字段
    stable_cols = [c for c in df.columns if c not in ['timestamp', 'run_id']]
    content = df[stable_cols].to_csv(index=False)
    
    return hashlib.md5(content.encode()).hexdigest()
```

---

## ✅ 复现检查清单

每次实验前后执行：

- [ ] `env/versions.txt` 已更新
- [ ] `env/git_commit.txt` 记录当前 commit
- [ ] `configs/exp_matrix.yaml` 参数正确
- [ ] seed=1234 已设置
- [ ] 结果 CSV 包含所有必需字段
- [ ] 结果已同步到 `results/runs/`

---

## 🚀 快速验证

// turbo
```bash
# 完整复现性检查
python scripts/collect_env.py
git rev-parse HEAD > env/git_commit.txt
python -c "from scripts.utils import validate_config; validate_config()"

echo "✓ 复现性检查完成"
```
