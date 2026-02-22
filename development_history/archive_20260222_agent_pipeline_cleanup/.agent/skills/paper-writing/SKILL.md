---
description: 论文写作辅助 - LaTeX表格生成、图表规范、学校模板
---

# Paper Writing Skill

> 辅助 Milestone J 的论文输出，包括表格生成和图表规范。

---

## 📊 从 CSV 生成 LaTeX 表格

### 基础表格生成

```python
import pandas as pd

def csv_to_latex(csv_path, caption, label):
    """将 CSV 转换为 LaTeX 表格"""
    df = pd.read_csv(csv_path)
    
    latex = df.to_latex(
        index=False,
        caption=caption,
        label=label,
        column_format='l' + 'c' * (len(df.columns) - 1),
        escape=False
    )
    return latex

# 使用示例
latex_table = csv_to_latex(
    "results/runs/exp_summary.csv",
    "KV Cache 量化性能对比",
    "tab:kv_quantization"
)
```

### 论文常用表格模板

```latex
\begin{table}[htbp]
\centering
\caption{不同量化策略的性能对比}
\label{tab:quantization_comparison}
\begin{tabular}{lcccc}
\toprule
\textbf{方法} & \textbf{显存 (GB)} & \textbf{吞吐 (tok/s)} & \textbf{PPL} & \textbf{Needle} \\
\midrule
FP16 Baseline & 12.5 & 45.2 & 5.23 & 98.5\% \\
INT8 Baseline & 8.2 & 42.1 & 5.31 & 94.2\% \\
INT8 Ours & 8.1 & 48.3 & 5.27 & 97.8\% \\
\bottomrule
\end{tabular}
\end{table}
```

---

## 📈 图表生成规范

### 论文图表样式

```python
import matplotlib.pyplot as plt
import matplotlib

# 论文级图表样式
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'axes.labelsize': 14,
    'axes.titlesize': 14,
    'legend.fontsize': 11,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'figure.figsize': (8, 6),
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
})
```

### 常用图表类型

// turbo
```python
# 1. 吞吐-序列长度曲线
def plot_throughput_vs_seqlen(csv_path, output_path):
    df = pd.read_csv(csv_path)
    
    fig, ax = plt.subplots()
    for mode in ['fp16', 'int8_baseline', 'int8_ours']:
        subset = df[df['kv_mode'] == mode]
        ax.plot(subset['seq_len'], subset['tok_per_s'], 
                marker='o', label=mode)
    
    ax.set_xlabel('序列长度')
    ax.set_ylabel('吞吐量 (tokens/s)')
    ax.legend()
    ax.set_xscale('log', base=2)
    plt.savefig(output_path)

# 2. 显存对比柱状图
def plot_memory_comparison(csv_path, output_path):
    df = pd.read_csv(csv_path)
    
    modes = df['kv_mode'].unique()
    mem = df.groupby('kv_mode')['gpu_mem_peak_mb'].mean()
    
    fig, ax = plt.subplots()
    ax.bar(modes, mem / 1024)  # 转换为 GB
    ax.set_ylabel('峰值显存 (GB)')
    plt.savefig(output_path)
```

---

## 📁 论文章节与实验对应

| 章节 | 需要的图表/表格 | 数据来源 |
|------|----------------|----------|
| 方法 | 架构图、流程图 | 手工绘制 |
| 实验设置 | 环境表格 | `env/versions.txt` |
| 主实验 | 性能对比表 | `results/runs/*.csv` |
| 消融实验 | group_size 对比图 | `results/runs/*.csv` |
| 长上下文 | Needle 曲线图 | `results/runs/needle_*.csv` |

---

## 🎓 学校模板检查清单

- [ ] 页边距：上下 2.54cm，左右 3.17cm
- [ ] 正文字体：宋体/Times New Roman 12pt
- [ ] 章节标题：黑体加粗
- [ ] 图表编号：图 X.Y / 表 X.Y 格式
- [ ] 参考文献：GB/T 7714 格式
- [ ] 目录：自动生成

---

## 🚀 快速生成

// turbo
```bash
# 一键生成所有论文图表
python scripts/make_plots.py --input results/runs/ --output results/plots/

# 预期输出文件：
# results/plots/throughput_vs_seqlen.pdf
# results/plots/memory_comparison.pdf
# results/plots/needle_accuracy.pdf
# results/plots/ppl_comparison.pdf
```
