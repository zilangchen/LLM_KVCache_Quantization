#!/bin/bash
# Stage 6: Phase 5 7B/8B 杂项
#
# - 7B/8B LongBench official (--longbench_source hf, max_samples 32)
# - 7B/8B Memory/Batch sweep (4 batch sizes)
# 8B 用 local modelscope path 避免 HF download。

set -uo pipefail
cd /root/LLM_KVCache_Quantization

export CUDA_VISIBLE_DEVICES=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

RD="results/emnlp_p012_batch/runs"
MODEL_7B="Qwen/Qwen2.5-7B-Instruct"
MODEL_8B="/root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct"
CALIB_7B="artifacts/kv_calib_rolealign_7b_v3.json"
CALIB_8B="artifacts/kv_calib_rolealign_8b_v3.json"

run_or_skip() {
  local tag="$1"; shift
  local outdir="$RD/$tag"
  if [ -d "$outdir" ] && ls "$outdir"/*.csv >/dev/null 2>&1; then
    echo "  SKIP: $tag (results exist)"
    return 0
  fi
  echo ""; echo "═══ RUN: $tag ═══"
  date '+%Y-%m-%d %H:%M:%S'
  "$@" --save_csv --out_dir "$outdir" 2>&1 | tail -20
  echo "  DONE: $tag"
}

echo ""; echo "═══ Stage 6: Phase 5 7B/8B misc ═══"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"

# 7B LongBench official
echo ""; echo "--- 7B LongBench official ---"
run_or_skip "longbench_official_7b_s1234" \
  python3 scripts/eval_longbench.py --model_id "$MODEL_7B" --kv_mode int4_ours_asym \
    --calib_file "$CALIB_7B" --seq_len 32704 --seed 1234 \
    --longbench_source hf --longbench_max_samples 32

# 8B LongBench official
echo ""; echo "--- 8B LongBench official ---"
run_or_skip "longbench_official_8b_s1234" \
  python3 scripts/eval_longbench.py --model_id "$MODEL_8B" --kv_mode int4_ours_asym \
    --calib_file "$CALIB_8B" --seq_len 32704 --seed 1234 \
    --longbench_source hf --longbench_max_samples 32

# 7B Memory/Batch sweep
echo ""; echo "--- 7B Memory/Batch sweep ---"
for BATCH in 1 4 8 16; do
  run_or_skip "memory_7b_b${BATCH}" \
    python3 scripts/profile_memory.py --model_id "$MODEL_7B" --kv_mode int4_ours_asym \
      --calib_file "$CALIB_7B" --batch "$BATCH" --seq_len 4096
done

# 8B Memory/Batch sweep
echo ""; echo "--- 8B Memory/Batch sweep ---"
for BATCH in 1 4 8 16; do
  run_or_skip "memory_8b_b${BATCH}" \
    python3 scripts/profile_memory.py --model_id "$MODEL_8B" --kv_mode int4_ours_asym \
      --calib_file "$CALIB_8B" --batch "$BATCH" --seq_len 4096
done

echo ""; echo "═══ Stage 6 complete ═══"
date '+%Y-%m-%d %H:%M:%S'
