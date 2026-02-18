# Agent Startup Guide (Repository Policy)

This repository expects agents (human or AI) to follow the same execution and
reproducibility rules. If you are a new agent session, do this first.

## 1. Boot Checklist (Do This Before Editing Code)

1. Read project goals and fixed constraints: `objective.md`
2. Read current progress and what is "done": `lang.md`
3. Read collaboration + remote execution rules: `docs/AGENT_README.md`
4. Inspect local agent skills (always):
   - list: `ls .agent/skills`
   - read the relevant skill docs:
     - remote server: `.agent/skills/remote-server/SKILL.md`
     - long tasks: `.agent/skills/long-running-task/SKILL.md`
     - reproducibility: `.agent/skills/reproducibility/SKILL.md`
5. Optional but recommended (prints `.agent` contents + SSH health check):
   - `python3 scripts/agent_tools/agent_cli.py bootstrap`

If your task needs GPU or model downloads, you should NOT run it locally.
Use the remote server workflow below.

## 2. Remote Server Workflow (GPU Tasks)

Source of truth for connection details and tmux usage:
- `.agent/skills/remote-server/SKILL.md`
- `docs/autodl_server.md`

Minimum safe sequence:
1. Connection health check (GPU visible):
   - `ssh -p 31867 root@region-42.seetacloud.com "echo 'SSH OK' && nvidia-smi -L"`
2. Start a tmux session for long tasks:
   - `ssh -p 31867 root@region-42.seetacloud.com "bash -lc 'tmux new -s <name> -d \"cd /root/LLM_KVCache_Quantization && <cmd>\"'"`
3. Monitor logs/output:
   - `ssh -p 31867 root@region-42.seetacloud.com "tmux capture-pane -t <name> -p -S -50"`
4. Sync results back:
   - follow the `rsync` recipes in `.agent/skills/remote-server/SKILL.md`

If you use the multi-agent CLI, also follow:
- `docs/AGENT_README.md` and `scripts/agent_tools/agent_cli.py`

## 3. Single Entrypoint For Experiments

The only experiment matrix is:
- `configs/exp_matrix.yaml`

The recommended runner:
- `scripts/run_experiments.py`

Do not use the deprecated root `exp_matrix.yaml`.

## 3.1 Calibration Gate (int8_ours)

`kv_mode=int8_ours` requires a calibration file (default: `artifacts/kv_calib_kl.json`).
Generate it first on the GPU server:
- `python3 scripts/calibrate_behavior.py --config configs/exp_matrix.yaml --run_name int8_ours_kl_temp_fused`

## 4. Reproducibility Minimum Bar

Every run must:
1. be driven by `configs/exp_matrix.yaml` (or a snapshot of it)
2. write outputs under `results/`
3. write a config snapshot (see `src/utils/repro.py`)
4. record `git_commit`, `timestamp`, and hardware info
