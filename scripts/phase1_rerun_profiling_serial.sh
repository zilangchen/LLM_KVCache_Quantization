#!/bin/bash
# Phase 1 补跑: TPOT + Memory profiling (串行, 独占 GPU)
# 必须在所有 RULER 完成后、无其他 GPU 进程时运行
set -euo pipefail
export CUDA_VISIBLE_DEVICES=0
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true
export HF_HUB_OFFLINE=1

RD="results/emnlp_rolealign_v2"
mkdir -p "$RD/runs" "$RD/logs"

# 预检: 确保 GPU 空闲
GPU_PROCS=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)
if [ "$GPU_PROCS" -gt 0 ]; then
  echo "ERROR: GPU has $GPU_PROCS running processes. Must be exclusive!"
  nvidia-smi
  exit 1
fi
echo "GPU exclusive check: OK (0 processes)"

MODELS=(
  "Qwen/Qwen2.5-1.5B-Instruct|artifacts/kv_calib_rolealign_1p5b.json|1p5b"
  "Qwen/Qwen2.5-7B-Instruct|artifacts/kv_calib_rolealign_7b.json|7b"
  "/root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct|artifacts/kv_calib_rolealign_8b.json|8b"
)

echo "=== Serial Profiling Start: $(date '+%Y-%m-%d %H:%M:%S') ==="

for entry in "${MODELS[@]}"; do
  IFS='|' read -r MODEL_ID CALIB TAG <<< "$entry"
  echo ""
  echo "========== ${TAG} (exclusive GPU) =========="

  for KV_MODE in int4_ours_asym fp16; do
    MODE_LABEL="${KV_MODE}"
    CALIB_ARG=""
    BITS_ARG=""
    if [ "$KV_MODE" = "int4_ours_asym" ]; then
      CALIB_ARG="--calib_file $CALIB"
      BITS_ARG="--quant_bits 4"
    fi

    for SL in 512 1024 2048 4096 8192; do
      echo ">>> ${TAG} TPOT ${MODE_LABEL} seq=${SL}"
      python3 scripts/profile_latency.py \
        --model_id "$MODEL_ID" \
        --kv_mode "$KV_MODE" \
        $BITS_ARG $CALIB_ARG \
        --seq_len "$SL" --gen_len 128 \
        --batch 1 --warmup 3 --runs 8 \
        --save_csv \
        --out_dir "$RD/runs/prof_serial_latency_${MODE_LABEL}_${TAG}_s${SL}" \
        2>&1 | tee -a "$RD/logs/prof_serial_${TAG}.log"

      # Inline validation: check TPOT is reasonable
      CSV=$(ls "$RD/runs/prof_serial_latency_${MODE_LABEL}_${TAG}_s${SL}"/profile_latency_*.csv 2>/dev/null | tail -1)
      if [ -n "$CSV" ]; then
        python3 -c "
import csv
rows = list(csv.DictReader(open('$CSV')))
tpot = float(rows[0]['tpot_ms'])
print(f'  VALIDATE: TPOT={tpot:.1f}ms (${MODE_LABEL} ${TAG} seq=${SL})')
if tpot > 500:
    print('  *** ALERT: TPOT > 500ms, suspiciously high ***')
if tpot < 1:
    print('  *** ALERT: TPOT < 1ms, suspiciously low ***')
"
      fi
    done

    for SL in 512 1024 2048 4096 8192; do
      echo ">>> ${TAG} Memory ${MODE_LABEL} seq=${SL}"
      python3 scripts/profile_memory.py \
        --model_id "$MODEL_ID" \
        --kv_mode "$KV_MODE" \
        $BITS_ARG $CALIB_ARG \
        --seq_len "$SL" --gen_len 128 \
        --batch 1 \
        --save_csv \
        --out_dir "$RD/runs/prof_serial_memory_${MODE_LABEL}_${TAG}_s${SL}" \
        2>&1 | tee -a "$RD/logs/prof_serial_${TAG}.log"
    done
  done

  echo "[${TAG}] profiling done: $(date '+%H:%M:%S')"
done

echo ""
echo "=== Serial Profiling ALL DONE: $(date '+%Y-%m-%d %H:%M:%S') ==="
