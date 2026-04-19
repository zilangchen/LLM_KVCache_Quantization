# T3 Cross-Model Main (debug)

## Qwen2.5-3B ($H_{kv}{=}2$)  (best-k: bakv_k1, heur-k: heuristic_k1, autok: bakv_auto_cov80_max)

| Task | Uniform | **BA-k** | Heuristic-k | **BA-AutoK** | Winner |
|---|---|---|---|---|---|
| NarrativeQA (F1) | 4.33 | **7.17** | 3.08 | 6.48 | BA-k |
| HotpotQA (F1) | 2.38 | 4.73 | 1.39 | **4.89** | AutoK |
| GovReport (Rouge-L) | 5.77 | 8.81 | 5.96 | **8.90** | AutoK |

## Llama-3.1-8B ($H_{kv}{=}8$)  (best-k: bakv_k11, heur-k: heuristic_k11, autok: bakv_auto_cov80_max)

| Task | Uniform | **BA-k** | Heuristic-k | **BA-AutoK** | Winner |
|---|---|---|---|---|---|
| NarrativeQA (F1) | 10.24 | **11.14** | 10.47 | 10.74 | BA-k |
| HotpotQA (F1) | 6.73 | **7.88** | 5.68 | 7.57 | BA-k |
| GovReport (Rouge-L) | 9.24 | 9.54 | 9.47 | **9.75** | AutoK |

## Qwen2.5-14B ($H_{kv}{=}8$)  (best-k: bakv_k7, heur-k: heuristic_k7, autok: bakv_auto_cov90_max)

| Task | Uniform | **BA-k** | Heuristic-k | **BA-AutoK** | Winner |
|---|---|---|---|---|---|
| NarrativeQA (F1) | **7.05** | 6.67 | 6.83 | 6.80 | Uniform |
| HotpotQA (F1) | **5.57** | 5.49 | 5.40 | 5.39 | Uniform |
| GovReport (Rouge-L) | 9.09 | 8.95 | 9.03 | **9.27** | AutoK |

## Mistral-7B-v0.3 ($H_{kv}{=}8$)  (best-k: bakv_k3, heur-k: heuristic_k3, autok: bakv_auto_cov80_max)

| Task | Uniform | **BA-k** | Heuristic-k | **BA-AutoK** | Winner |
|---|---|---|---|---|---|
| NarrativeQA (F1) | 15.55 | 15.71 | **17.11** | 16.26 | Heur-k |
| HotpotQA (F1) | 17.81 | 17.78 | 17.84 | **19.08** | AutoK |
| GovReport (Rouge-L) | 8.70 | 8.66 | 8.86 | **8.96** | AutoK |