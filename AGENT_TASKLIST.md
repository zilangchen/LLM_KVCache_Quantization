# Cursor Agent Tasklist: KV Cache Quantization for Efficient LLM Inference

> **Project**: Graduation Thesis — 面向高效推理的大语言模型键值缓存量化方法
>
> **Primary goal**: Build an end-to-end inference pipeline (Python + PyTorch) for **Qwen/Qwen2.5-1.5B-Instruct**, implement **KV cache INT8 quantization** with **percentile clipping** and **per-head / group-wise scaling**, and evaluate across **memory / speed / quality / long-context stability**. Use **Triton/CUDA** to optimize at least one critical kernel.
>
> **Non-negotiables**: reproducibility, clear ablations, structured outputs (CSV/JSON), and an execution matrix that can be rerun with one command.

---

## 0. Fixed Decisions (Do Not Change)

### 0.1 Model
- HuggingFace model: `Qwen/Qwen2.5-1.5B-Instruct`

### 0.2 Core Stack
- Python 3.10
- PyTorch (CUDA)
- Transformers
- Triton
- FastAPI + Uvicorn (service)
- pynvml (GPU memory sampling)
- numpy/pandas/matplotlib

### 0.3 Two Execution Paths
- **Research path (must)**: Transformers + custom generation loop + custom KV cache implementation (for algorithm + kernel work).
- **System reference path (optional)**: LMDeploy (TurboMind) for extra system-level baselines; keep scripts separate so the core project remains independent.

---

## 1. Repository Layout (Create First)

Create this structure before implementing logic:

```
.
├── src/
│   ├── model/
│   ├── engine/
│   ├── cache/
│   ├── quant/
│   ├── kernels/
│   └── server/
├── scripts/
├── tests/
├── configs/
├── artifacts/
├── results/
│   ├── runs/
│   ├── logs/
│   ├── tables/
│   └── plots/
├── env/
└── README.md
```

Required files:
- `configs/exp_matrix.yaml` (experiment matrix)
- `env/versions.txt` (GPU/driver/CUDA/torch versions)
- `env/requirements_freeze.txt` (pip freeze)
- `requirements.txt` (or `environment.yml`)

---

## 2. Stable APIs (Define Early)

These are the stable interfaces every module must follow.

### 2.1 Engine
- `Engine.generate(prompts, generation_config, kv_mode, runtime_config) -> GenerationOutput`
- Support streaming (server) and non-streaming (scripts)

### 2.2 KV Cache
- `KVCache.append(layer_id, k, v)`
- `KVCache.get_kv(layer_id) -> (k, v)`
- Must support incremental growth during decode.

### 2.3 Quantizer
- `Quantizer.quantize_kv(k, v, meta) -> (qk, qv, qmeta)`
- `Quantizer.dequantize_kv(qk, qv, qmeta) -> (k, v)`

### 2.4 Kernels
- Triton kernels must have python wrappers in `src/kernels/`.
- At least one kernel must be called in the real inference path.

---

## 3. Milestones (Implement in This Order)

### Milestone A — Environment + Smoke Test
**Goal**: Project installs and runs a single prompt.

Deliverables:
- `scripts/smoke_test.py` (greedy generation)
- `requirements.txt` and version records in `env/`

Acceptance:
- `python scripts/smoke_test.py` prints a non-empty output.

### Milestone B — Custom Generation Loop (No `model.generate`)
**Goal**: Controlled prefill + decode loop so KV cache can be replaced.

Deliverables:
- `src/engine/generate_loop.py` implementing:
  - prefill
  - decode (token-by-token)
  - greedy decoding mode (temperature=0)
  - TTFT/TPOT time measurements

Acceptance:
- Output matches `model.generate` in greedy mode (minor differences allowed, but must be explained).

### Milestone C — FP16 KV Cache (Baseline)
**Goal**: Correct KV caching with fixed layout.

Deliverables:
- `src/cache/fp16_cache.py`
- KV layout document in `src/cache/README_cache_layout.md`

Acceptance:
- Cache length equals prompt length after prefill; increments by 1 per decode step.
- Generation correctness preserved.

### Milestone D — Measurement & Evaluation Suite (Fix the Metrics Early)
**Goal**: Build the evaluation harness before quantization so all later comparisons are fair.

Deliverables:
- `scripts/profile_latency.py`
- `scripts/profile_memory.py`
- `scripts/eval_ppl.py`
- `scripts/eval_needle.py`

Output format requirements:
- Write structured outputs to `results/runs/*.csv` with fields:
  `run_id, model_id, kv_mode, quant_bits, clip_percentile, group_size, dtype, seq_len, gen_len, batch, ttft_ms, tpot_ms, tok_per_s, gpu_mem_peak_mb, timestamp, git_commit`

Acceptance:
- FP16 baseline runs end-to-end and outputs consistent CSV schemas.

### Milestone E — INT8 Baseline Quantization (Functional First)
**Goal**: INT8 KV cache that runs correctly.

Deliverables:
- `src/quant/int8_basic.py` (per-tensor or per-head)
- `src/cache/int8_cache.py`
- Switchable `kv_mode` in engine: `fp16`, `int8_baseline`

Acceptance:
- `kv_mode=int8_baseline` runs without crashing.
- Quality degradation is within acceptable range on small eval.

### Milestone F — Ours: Clipping + Per-head / Group-wise Scaling
**Goal**: Implement the thesis mainline.

Deliverables:
- `scripts/calibrate_kv.py` producing `artifacts/kv_calib.json`
- `src/quant/clipping.py`
- `src/quant/groupwise.py` (head_dim grouping)
- New `kv_mode=int8_ours`

Acceptance:
- `int8_ours` quality >= `int8_baseline` on needle or PPL trend (at least on long-context settings).
- Ablation toggles exist (clipping on/off, group_size variants).

### Milestone G — Triton Optimization (At Least One Real Kernel)
**Goal**: Use Triton to speed up a real bottleneck.

Minimum requirement:
- `src/kernels/triton_dequant.py` implementing int8 -> fp16 dequantization with scale.
- Engine calls Triton dequant during decode (not just a demo).

Stretch:
- `src/kernels/triton_decode_attn.py` for q_len=1 fused dequant + attention.

Acceptance:
- Triton kernel passes numerical checks against torch implementation.
- Profiling shows speedup or at least no regression while reducing CPU overhead.

### Milestone H — INT4 + Mixed Precision (Optional, Only After Mainline Works)
**Goal**: Add research depth.

Deliverables (optional):
- `kv_mode=int4` and/or `kv_mode=mixed`
- Clear policy definition (which layers/heads are int8 vs int4)

Acceptance:
- Mixed precision improves memory at similar quality, or improves quality at similar memory.

### Milestone I — Service + Load Test
**Goal**: Deployable inference service for demonstration.

Deliverables:
- `src/server/app.py` with endpoints:
  - `/health`
  - `/v1/chat/completions` (OpenAI-like)
  - streaming SSE
- `scripts/load_test.py` for concurrency tests

Acceptance:
- Service can be started and queried reliably.
- Outputs match engine outputs.

### Milestone J — Experiment Runner + Plotting (Paper-Ready Outputs)
**Goal**: One command to reproduce key tables and figures.

Deliverables:
- `scripts/run_experiments.py` reading `configs/exp_matrix.yaml`
- `scripts/make_plots.py` producing:
  - memory vs seq_len
  - tok/s vs seq_len
  - needle accuracy vs seq_len
  - PPL comparisons

Acceptance:
- Running the matrix generates all tables/plots under `results/`.

---

## 4. Testing Policy (Required)

Create tests early and keep them running:
- Quantize/dequantize error bounds
- Cache append/get shape invariants
- Triton output correctness within tolerance

Command:
- `pytest -q` must pass before advancing milestones.

---

## 5. Reproducibility Rules

- All scripts accept a config path and output folder.
- Every run writes a config snapshot JSON and CSV results.
- Fix decoding parameters (greedy) when measuring quality.
- Record `git_commit` and timestamp for every run.

---

## 6. Definition of “Done”

The project is considered complete when:
1) FP16, INT8-baseline, INT8-ours pipelines run end-to-end.
2) At least one Triton kernel is integrated in the real decode path.
3) Results include memory/speed/quality + long-context needle, with repeatable scripts.
4) `configs/exp_matrix.yaml` reproduces key results with one command.

