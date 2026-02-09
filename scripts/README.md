## scripts/
这里放可执行脚本（评测、跑实验矩阵、出图、校准、服务压测等）。

约定：
- 统一入口：`scripts/run_experiments.py`（读取 `configs/exp_matrix.yaml`）
- 评测类脚本需接受 `--config`/`--run_name` 与 `--out_dir`
- 输出统一写入 `results/`（结构化 CSV/JSON），不要把结果散落在工作目录

补充工具：
- `scripts/calibrate_behavior.py`：输出 `artifacts/kv_calib_kl.json`
- `scripts/verify_fused_decode.py`：校验 fused decode 路径与参考路径一致性
