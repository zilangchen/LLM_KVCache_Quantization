# 论文最终数据（唯一权威入口）

**冻结日期**: 2026-04-17
**状态**: 所有实验已完成，数据已冻结，不再更新

## 目录结构

```
final/
├── final_data/           论文使用的全部实验数据
│   ├── int8_mainline/    INT8 主表、n=10 PPL、tau ablation、跨模型泛化
│   ├── int4_rolealign/   INT4-RoleAlign PPL/Needle/RULER/serial profiling
│   ├── kv_ablation/      K/V 消融、B10 校准扩展、MixedKV
│   ├── backend_comparison/ 14B 外部效度、长序列 TPOT、FP16 baseline、FI/BD 对比
│   └── INDEX.md          表→CSV 权威映射
└── final_scripts/        论文图表生成的关键脚本
    ├── eval/             评测脚本（PPL/Needle/RULER/LongBench/latency/memory）
    └── aggregate/        结果聚合与分析
```

## 数据来源与原目录映射

| final_data 子目录 | 原目录名 | runs 数 | 覆盖内容 |
|-------------------|---------|---------|---------|
| int8_mainline | emnlp_defense_v1 | 202 | INT8 主线全量实验 |
| int4_rolealign | emnlp_rolealign_v2 | 171 | INT4-RoleAlign 跨模型 |
| kv_ablation | emnlp_expansion_v1 | 60 | K/V 消融 + B10 校准 |
| backend_comparison | emnlp_p012_batch | 284 | 14B + 长序列 + 后端对比 |

## 历史数据

已归档至 `results/archive/`，按开发轮次组织（round1-round4）。
详见 `results/archive/README.md`。

## 注意事项

- 任何 agent 或 session 需要查找实验数据时，从本目录的 `INDEX.md` 开始
- 不要引用 `results/archive/` 中的数据用于论文
- `results/_canonical/` 为旧版索引，已被本目录替代
