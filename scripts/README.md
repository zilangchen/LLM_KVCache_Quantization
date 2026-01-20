## scripts/
这里放可执行脚本（评测、跑实验矩阵、出图、校准、服务压测等）。

约定：
- 所有脚本都应接受 `--config`（或读取 `configs/exp_matrix.yaml`）和 `--out_dir`
- 输出统一写入 `results/`（结构化 CSV/JSON），不要把结果散落在工作目录

