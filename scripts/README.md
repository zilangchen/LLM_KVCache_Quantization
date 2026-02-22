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
- `scripts/generate_thesis_report.py`：基于 `tables/` 生成顶会写作所需的证据报告（`reports/claim_validation.csv`、`reports/statistical_decision_summary.csv`、`reports/paper_ready_summary.md`）
- `scripts/check_run_completeness.py`：检查指定 `run_tag` 的 required/stress 任务是否完整，输出可机读 `completion_report.json`，并返回稳定退出码供自动补跑循环使用。
- 评测脚本支持 `--adaptive_static_scales`（仅 `int8_ours`）：在使用静态 scale 时按 token 自适应抬升 scale，降低长上下文 clip 风险。

说明：
- `scripts/profile_baseline.py` 为历史脚本（保留用于对照旧结果）；新评测请用 `profile_latency.py/profile_memory.py` 或直接跑 `run_experiments.py`。
- `scripts/aggregate_results.py`：聚合 `results/runs/*.csv` 生成 `results/tables/` 与 `results/plots/`
- `scripts/run_experiments.py` 支持 `--run_tag/--append`：可复用同一个 `run_id=<run_name>_<run_tag>`，分多次追加不同 tasks（避免输出目录碎片化）。
- `scripts/run_experiments.py` 新增稳定失败策略参数：
  - `--failure_policy {abort,continue_on_oom,continue_all}`
  - `--max_retries/--retry_backoff_sec`
  - `--skip_completed_success`（append 模式下跳过已成功任务，支持断点恢复）
  - `--summary_json`（输出任务级执行摘要，便于审计）
