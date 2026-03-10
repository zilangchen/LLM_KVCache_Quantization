# Findings

## Research & Discovery Log

### 2026-03-11 | C7/C8 Resolved → FAIL (INT4 Calibration Limitation)
- **C7 FAIL**: INT4-ours needle_pass_rate -3.33% vs INT4-baseline (threshold ≥-1%)
  - 1.5B: -100% (complete failure), 7B: NaN (no valid data), 8B: -3.33%
- **C8 FAIL**: INT4-ours perplexity -15.92% vs INT4-baseline (threshold ≥-0.5%)
  - All 3 models: -10% to -16% degradation
- **Root cause**: KL-divergence behavior-aligned calibration effective at INT8, but does NOT maintain non-inferiority at INT4 precision
- **Paper implication**: Discuss as bit-width sensitivity limitation in Section 5 + Appendix
- **Fix applied**: Added `("int4_baseline", "int4_ours")` to `RELATIVE_GAIN_PAIRINGS` in aggregate_results.py + expanded export_tables_latex.py filter to include `int4_baseline` and `kivi_style`

### 2026-03-11 | C6 Root Cause — Multi-Factor (Corrected)
- **Previous assessment**: "唯一根因 = prompt budget 溢出" — **过度简化**
- **Corrected**: C6 FAIL (-2.82%) has multiple contributing factors:
  - EVL-047 [HIGH]: CWE distractor freq ~90x vs target 30x
  - EVL-074 [HIGH]: token/word=2 assumption causes ~35% padding underestimate
  - EVL-079 [HIGH]: cwe_max_tokens=128 but budget uses gen_len=64
  - EVL-050 [MED]: underscore removal breaks CWE token matching
  - EVL-075 [MED]: set dedup inflates CWE precision
- **Paper implication**: Write as "multiple contributing factors in CWE subtask", not single root cause

### 2026-03-10 | Phase 6 Claim Validation Results
- **C1 TPOT**: 17.27% gain over INT8-baseline at 32K (q=0.016, strong)
- **C2 Memory**: 43.75% KV cache reduction vs FP16 at 32K
- **C6 FAIL**: RULER pass_rate -2.82% on LLaMA-3.1-8B (threshold: -1%)
- **NaN batch filter bug**: `generate_thesis_report.py` quality claims had `target_batch=1` but LongBench/RULER/Needle data has batch=NaN → all rows filtered out

### Key Data Points
- Final claim status: **8 PASS / 3 FAIL / 0 INCONCLUSIVE / 0 ERROR**
- Total experimental dirs: 2136 (1560 phase5v2 + 576 phase6)
- Latency/memory seq_lens: {4096, 8192, 16384, 32704}
- Zero OOM across all 576 phase6 core profiling runs (H20 96GB sufficient)
- LaTeX tables: 39 .tex files, Plots: 18 .png files
