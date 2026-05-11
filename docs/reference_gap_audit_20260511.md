# Reference Gap Audit 2026-05-11

## Current Coverage

The active thesis bibliography now covers the paper along eight content lines.

| Theme | Active Coverage | Status |
|---|---|---|
| Transformer, GQA, MQA and model sources | Transformer, GQA, MQA, Qwen2.5, Llama 3, Mistral | Covered. Model reports remain technical-source citations because they identify evaluated artifacts. |
| General quantization and PTQ | Gholami survey, Hubara, SmoothQuant, GPTQ, AWQ | Covered by formal sources. |
| KV Cache quantization and K/V role asymmetry | KIVI, KVQuant, AsymKV, AQUA-KV, KVTuner, Outlier Tokens Tracing, SKVQ, QJL, Atom, QServe, RotateKV | Covered with current formal sources and one newly added low-bit recovery citation. |
| Cache eviction, compression and budget allocation | H2O, StreamingLLM, SnapKV, ClusterAttn, DuoAttention, HeadKV, ChunkKV, CacheGen, ThinK, Ada-KV, DynamicKV | Covered. The new Ada-KV and DynamicKV citations better match the thesis budget-allocation discussion. |
| Attention behavior and softmax perturbation | KVTuner, Bondarenko et al., cache-selection studies | Covered enough for the current method framing. |
| Long-context evaluation | LongBench, RULER, Needle, KVCompressionBench, Fang et al. on long-context PPL | Covered. The Needle source remains a technical benchmark source. |
| Statistical protocol | Efron and Tibshirani for Bootstrap, Benjamini and Hochberg for FDR | Covered after this update. |
| Systems and decode backend | FlashAttention, FlashAttention-2, vLLM, Triton, QServe, Rethinking KV cache compression, BitDecoding | Covered with formal systems and serving citations. |

## Added References

| Key | Placement | Reason |
|---|---|---|
| `su2025rotatekv` | Chapter 2 low-bit recovery paragraph | Adds a formal 2-bit KV Cache recovery reference adjacent to QuaRot and GEAR. |
| `feng2025adakv` | Chapter 2 cache-management paragraph | Adds an adaptive budget allocation reference that is closer to the thesis allocator motivation. |
| `zhou2025dynamickv` | Chapter 2 cache-management paragraph | Adds task-aware adaptive KV compression as a neighboring line to model/task-dependent budget choices. |
| `gao2025rethinkingkv` | Chapter 2 system paragraph | Supports the claim that cache-compression quality and system gains must be evaluated together in serving settings. |
| `du2026bitdecoding` | Chapter 2 system paragraph | Supports the low-bit KV decode backend discussion and Tensor Core oriented execution path. |
| `efron1994introduction` | Chapter 4 statistics paragraph | Supports Bootstrap confidence intervals. |
| `benjamini1995controlling` | Chapter 4 statistics paragraph | Supports Benjamini--Hochberg FDR control. |
| `fang2025longppl` | Chapter 4 PPL protocol paragraph | Supports the caution that long-context PPL depends on evaluation protocol details. |

## Candidates Reviewed But Not Added

| Candidate Type | Decision |
|---|---|
| More KV Cache compression papers beyond the current list | Not added. Chapter 2 already covers quantization, eviction, mixed precision, adaptive budget and systems. Additional references would expand taxonomy without serving a concrete sentence. |
| FlashInfer tooling citation | Not added. The current thesis text does not make a source claim that requires FlashInfer, and the available entry is a tooling or arXiv-style source. |
| Broader benchmark-variance literature | Not added. Chapter 4 now cites standard Bootstrap and FDR sources, which are sufficient for the current statistical protocol wording. |
| Additional general quantization classics | Not added. The current PTQ chain is already supported by formal survey and LLM-focused PTQ sources. |

## Remaining Boundary

The active bibliography still includes a small number of technical-source references because the thesis evaluates specific model families or benchmark probes whose official source is a report or repository rather than a formal proceedings paper. These are retained as artifact sources, not as formal method evidence.
