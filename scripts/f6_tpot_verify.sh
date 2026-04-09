#!/bin/bash
# F6: TPOT verification for tab:int4-tpot-cross-model
# Goal: determine whether paper numbers (58.97/61.80/70.56 ms for 1.5B/7B/8B
# RoleAlign) correspond to seq_len=4096 or seq_len=8192 in v2 raw data.
#
# Usage: tmux new -s f6_tpot -d 'bash scripts/f6_tpot_verify.sh 2>&1 | tee /tmp/f6_tpot.log'
#
# Must be run on a dedicated GPU (no other tenants) per CLAUDE.md §5.3.
set -euo pipefail
cd /root/LLM_KVCache_Quantization
source /etc/network_turbo 2>/dev/null || true

OUT_DIR="results/f6_tpot_verify/runs"
mkdir -p "$OUT_DIR"

MODELS=(
  "Qwen/Qwen2.5-1.5B-Instruct"
  "Qwen/Qwen2.5-7B-Instruct"
  "/root/autodl-tmp/modelscope_cache/LLM-Research/Meta-Llama-3___1-8B-Instruct"
)
SHORTS=("1p5b" "7b" "8b")
CALIBS=(
  "artifacts/kv_calib_rolealign_1p5b_v3.json"
  "artifacts/kv_calib_rolealign_7b_v3.json"
  "artifacts/kv_calib_rolealign_8b_v3.json"
)

# Paper claims seq_len=4096 in the caption; verify against both 4096 and 8192
# in case the paper data came from 8192 (v2 raw suggests this).
SEQ_LENS=(4096 8192)

echo "===== F6 TPOT Verification ====="
echo "Started: $(date)"
echo "Goal: verify tab:int4-tpot-cross-model numbers against seq_len=4096 vs 8192"
echo "GPU: $(nvidia-smi --query-gpu=index,name --format=csv,noheader | head -1)"
echo ""

for seq in "${SEQ_LENS[@]}"; do
  for i in 0 1 2; do
    MODEL="${MODELS[$i]}"
    SHORT="${SHORTS[$i]}"
    CALIB="${CALIBS[$i]}"
    TAG="f6_${SHORT}_s${seq}"

    # Skip 1.5B s=4096 (already completed before crash)
    if [ "$SHORT" = "1p5b" ] && [ "$seq" = "4096" ]; then
      echo "===== SKIP $TAG (already done) ====="
      continue
    fi
    # Skip 7B s=4096 FP16/RoleAlign (already done); only need 8B + seq=8192
    if [ "$SHORT" = "7b" ] && [ "$seq" = "4096" ]; then
      echo "===== SKIP $TAG (FP16 + RoleAlign already done before crash) ====="
      continue
    fi

    echo "===== $TAG ====="
    echo "Start: $(date)"

    # FP16 baseline
    echo "--- FP16 ---"
    python3 scripts/profile_latency.py \
      --model_id "$MODEL" --kv_mode fp16 \
      --seq_len "$seq" --gen_len 128 --batch 1 \
      --warmup 3 --runs 8 --save_csv \
      --out_dir "$OUT_DIR/${TAG}_fp16" 2>&1 | tail -5

    # INT4-RoleAlign (torch_ref)
    echo "--- INT4-RoleAlign ---"
    python3 scripts/profile_latency.py \
      --model_id "$MODEL" --kv_mode int4_ours_asym --quant_bits 4 \
      --calib_file "$CALIB" \
      --seq_len "$seq" --gen_len 128 --batch 1 \
      --warmup 3 --runs 8 --save_csv \
      --out_dir "$OUT_DIR/${TAG}_int4_ours_asym" 2>&1 | tail -5

    # INT8-ours removed from this rerun: v1 legacy calib has shape mismatch
    # issue on 7B/8B (H_kv != 2). Not needed for F6 TPOT verification target.

    echo "End: $(date)"
    echo ""
  done
done

echo "===== F6 TPOT Verification DONE ====="
echo "Finished: $(date)"
echo ""
echo "Summary:"
for seq in "${SEQ_LENS[@]}"; do
  for short in "${SHORTS[@]}"; do
    for mode in fp16 int4_ours_asym int8_ours; do
      f="$OUT_DIR/f6_${short}_s${seq}_${mode}"
      csv=$(ls "$f"/profile_latency_${mode}_*.csv 2>/dev/null | head -1)
      if [ -n "$csv" ]; then
        mean=$(awk -F',' 'NR>1 {v[NR-1]=$14; n++} END {sum=0; for (i=4; i<=n; i++) sum+=v[i]; printf "%.2f", sum/(n-3)}' "$csv")
        echo "$short seq=$seq $mode: TPOT mean(exclude first 3 warmup)=$mean ms"
      fi
    done
  done
done
