# Cursor Agent Tasklist: KV Cache Quantization for Efficient LLM Inference

> **Project**: Graduation Thesis — 面向高效推理的大语言模型键值缓存量化方法
>
> **Primary goal**: Build an end-to-end inference pipeline (Python + PyTorch) for **Qwen/Qwen2.5-1.5B-Instruct**, implement **KV cache INT8 quantization** with **group-wise quantization**, and evaluate across **memory / speed / quality / long-context stability**. Use **Triton/CUDA** to implement a **fused quantized decode-attention kernel (q_len=1)** and a **behavior-aligned (KL) calibration + per-head temperature** pipeline.
>
> **Non-negotiables**: reproducibility, clear ablations, structured outputs (CSV/JSON), and an execution matrix that can be rerun with one command.

---

## 0. Fixed Decisions (Do Not Change)

### 0.1 Model
- HuggingFace model: `Qwen/Qwen2.5-1.5B-Instruct`

### 0.2 Core Stack
- Python 3.12 (AutoDL image baseline)
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

### Milestone F — Ours: Behavior-aligned Calibration (KL) + Per-head Temperature + Group-wise Quant
**Goal**: Make INT8 KV quantization *stable on long context* by calibrating for behavior similarity, not just value ranges.

Core idea (must implement):
- Use **behavior-aligned calibration**: choose clipping/scales to minimize divergence between FP16 and quantized attention behavior.
- Add **per-head temperature correction** (per layer, per query head) to re-align attention sharpness after quantization.

Deliverables:
- `scripts/calibrate_behavior.py`
  - Inputs: a small prompt set (e.g., ShareGPT subset), `seq_len` targets (4k/8k), candidate percentiles + group sizes.
  - Outputs: `artifacts/kv_calib_kl.json` containing:
    - static `k_scale[layer, kv_head, group]`, `v_scale[layer, kv_head, group]`
    - `inv_tau[layer, q_head]` (per-head attention temperature, stored as 1/tau)
    - chosen `clip_percentile_k`, `clip_percentile_v`, `group_size_k`, `group_size_v`
- `src/quant/clipping.py` (apply calibrated clipping thresholds or implied by scales)
- `src/quant/groupwise.py` (INT8 group-wise quant/dequant; head_dim grouping)
- `src/quant/temperature.py` (apply per-head temperature in both prefill and decode)
- New `kv_mode=int8_ours` that loads `kv_calib_kl.json` and uses these parameters

Calibration objective (implementation spec):
- Align **attention weight distributions** head-wise at decode-like positions.
- For each (layer, head), compute:
  - `p_ref = softmax(logits_fp16)`
  - `p_quant(tau) = softmax(logits_quant * inv_tau)`
  - minimize `KL(p_ref || p_quant)` over tau (grid search is OK).
- Choose clipping percentile / group size by minimizing average KL across layers/heads on the calibration set.

Acceptance:
- `int8_ours` quality >= `int8_baseline` on **needle-in-a-haystack** accuracy trend and/or PPL trend (especially at long context).
- Ablations exist: temperature on/off; KL-calibrated vs fixed-percentile; group_size variants.
- Calibration output is deterministic given a fixed seed and prompt set.

### Milestone G — Triton Mainline: Fused Quantized Decode Attention Kernel (Required)
**Goal**: Make quantized KV not only smaller but also *fast* by avoiding full dequant + separate attention ops during decode.

Minimum requirement (must):
- `src/kernels/triton_decode_attn_int8.py`
  - Implements a **q_len=1** decode attention kernel that:
    - reads **INT8 quantized K/V** cache
    - dequantizes **on-the-fly** (group-wise scales)
    - applies **per-head inv_tau** inside the logits before softmax
    - computes softmax + output accumulation in one kernel (online softmax)
  - Output: FP16/BF16 `attn_out[b, q_head, d]`
- Engine uses this Triton kernel for decode when `kv_mode=int8_ours` (and optionally `int8_baseline`).

Stepping-stone (recommended but not sufficient alone):
- `src/kernels/triton_dequant.py` for fast block dequantization (used for debugging / fallback), but the **fused decode kernel** is the main deliverable.

Kernel integration spec:
- Prefill can stay on torch SDPA/FlashAttention; apply temperature by scaling `Q` per head (broadcast) before SDPA.
- Decode must route to Triton fused kernel when `q_len==1`.
- Must support **GQA** mapping (`n_q_heads` vs `n_kv_heads`) by mapping query head -> kv head in-kernel or via pointer math.

Acceptance:
- Numerical check vs a torch reference decode attention (dequant + matmul + softmax) passes within tolerance.
- End-to-end decode latency (TTFT/TPOT) shows improvement or at least no regression compared with non-fused dequant+attention at long context.
- Kernel is actually used in real inference runs (not a demo script only).

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

