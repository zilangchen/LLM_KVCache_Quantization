# T4 Mistral-7B AutoK 5-Task (debug)

| Task | Uniform | BA-$k_3$ | Heur-$k_3$ | **BA-AutoK** |
|---|---|---|---|---|
| NarrativeQA (F1) | 15.55 | 15.71 | **17.11** | 16.26 |
| HotpotQA (F1) | 17.81 | 17.78 | 17.84 | **19.08** |
| GovReport (Rouge-L) | 8.70 | 8.66 | 8.86 | **8.96** |
| DuReader (Rouge-L) | 7.35 | 8.64 | 7.97 | **11.62** |
| LCC (EditSim) | 21.38 | **22.10** | 20.30 | 19.77 |