## scripts/
这里放可执行脚本（评测、跑实验矩阵、出图、校准、服务压测等）。

约定：
- 统一入口：`scripts/run_experiments.py`（读取 `configs/exp_matrix.yaml`）
- 评测类脚本需接受 `--config`/`--run_name` 与 `--out_dir`
- 输出统一写入 `results/`（结构化 CSV/JSON），不要把结果散落在工作目录

补充工具：
- `scripts/calibrate_behavior.py`：输出 `artifacts/kv_calib_kl.json`（支持 `--search_objective robust`，并产出 `search_trials.csv` 便于对比候选）
- `scripts/verify_fused_decode.py`：校验 fused decode 路径与参考路径一致性
- `scripts/analyze_needle_errors.py`：聚合 `needle_details_*.csv` 与可选 fused dump JSON，输出 `results/tables/fused_error_diagnosis.csv`
- `scripts/export_tables_latex.py`：将 `aggregate_results.py` 产出的 `tables/*.csv` 导出为论文可直接引用的 LaTeX 表格（booktabs）
- 评测脚本支持 `--adaptive_static_scales`（仅 `int8_ours`）：在使用静态 scale 时按 token 自适应抬升 scale，降低长上下文 clip 风险。

说明：
- `scripts/profile_baseline.py` 为历史脚本（保留用于对照旧结果）；新评测请用 `profile_latency.py/profile_memory.py` 或直接跑 `run_experiments.py`。
- `scripts/aggregate_results.py`：聚合 `results/runs/*.csv` 生成 `results/tables/` 与 `results/plots/`
- `scripts/run_experiments.py` 支持 `--run_tag/--append`：可复用同一个 `run_id=<run_name>_<run_tag>`，分多次追加不同 tasks（避免输出目录碎片化）。
