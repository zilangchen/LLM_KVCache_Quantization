# 历史实验脚本归档

**归档日期**: 2026-04-17
**说明**: 以下脚本来自早期开发轮次，已被 `scripts/batch_p012/`（最终批次）替代。

## 分类

- `gpu0_*.sh / gpu1_*.sh / gpu2_*.sh` — 早期 3-GPU 并行调度
- `phase1_*.sh` — 初版阶段性实验
- `exp*.sh / e3_*.sh / e4_*.sh / f6_*.sh` — 编号实验（INT8 对比、校准消融等）
- `rolealign_*.sh` — 早期 RoleAlign 实验
- `inv_tau_*.sh` — 温度校正消融
- `pipeline_*.sh / closure_*.sh / expansion_*.sh / dispatch_*.sh` — 中期流水线调度
- `defense_prep_all.sh` — 答辩补强实验
- `isolation_kl_vs_mse.sh` — KL vs MSE 隔离实验
- `launch_t3_*.sh / gate0_*.sh` — 触发器脚本
- 其他一次性脚本

## 最终版脚本

最终产出论文数据的脚本在 `results/final/final_scripts/batch/`（来自 `scripts/batch_p012/`）。
