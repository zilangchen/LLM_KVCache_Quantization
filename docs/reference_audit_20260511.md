# Reference Audit 2026-05-11

## Scope

- Main compile inputs checked: `thesis/main.tex`, `thesis/chapters/`, `thesis/figures/`, `thesis/tables/`, `thesis/setup/`.
- Excluded generated or temporary sources: `thesis/_pandoc_tmp/`, `thesis/backups/`.
- Citation closure after this update: 51 cited keys, 51 active BibTeX entries, 0 missing entries, 0 uncited active entries.
- Source classification after this update: 46 formal publications or accepted records, 5 technical or artifact sources retained for models, benchmark probes, or foundational architecture context.
- Temporary `_pandoc_tmp` keys not added to the formal bibliography: `aminabadi2022deepspeed`, `chen2023longlora`, `dettmers2024qlora`, `ding2024longrope`, `egiazarian2024aqlm`, `luna2024think`, `peng2023yarn`, `press2022train`, `shao2024omniquant`, `sheng2023flexgen`, `tseng2024quipsharp`, `yue2024wkvquant`, `zhang2024gear`, `zheng2024sglang`.

## Policy

Formal references use conference proceedings, journals, PMLR, ACL Anthology, OpenReview accepted records, ACM, IEEE, AAAI, NeurIPS, ICLR, ICML, COLM, MLSys, or other proceedings sources. arXiv, GitHub, blogs, and technical reports are retained only when the cited object is a model, benchmark repository, or foundational technical source without a formal substitute.

## Applied Changes

| Key | Status Before | Verified Source | Action |
|---|---|---|---|
| `nagel2021whitepaper` | arXiv-only survey | Formal book chapter by Gholami et al., DOI `10.1201/9781003162810-13` | Replaced with `gholami2022survey` in text and BibTeX |
| `cai2024pyramidkv` | arXiv-only cache-management citation | Formal ACL 2025 cache-compression work `ClusterAttn` | Replaced text citation with `zhang2025clusterattn` |
| `kang2024gear` | Venue/title metadata inaccurate | PMLR volume 262 workshop proceedings | Updated title, venue, pages, URL |
| `duanmu2024skvq` | arXiv entry and wrong author list | OpenReview accepted COLM 2024 record | Updated authors, venue, URL |
| `zandieh2024qjl` | arXiv entry | AAAI 2025 proceedings, DOI `10.1609/aaai.v39i24.34773` | Updated venue, pages, DOI |
| `shutova2025aquakv` | Minimal ICML metadata | PMLR volume 267, pages 55451--55473 | Updated full PMLR metadata |
| `xu2025kvtuner` | Minimal ICML metadata with arXiv note | PMLR volume 267, pages 36451--36485 | Updated full PMLR metadata |
| `hsieh2024ruler` | COLM entry with arXiv note | OpenReview accepted COLM 2024 record | Added official URL and removed arXiv note |
| `qwen2025qwen25` | arXiv article-like entry | Model technical report | Reclassified as `@misc` |
| `grattafiori2024llama3` | arXiv article-like entry | Model technical report | Reclassified as `@misc` |
| `jiang2023mistral` | arXiv article-like entry | Model technical report | Reclassified as `@misc` |
| `agarwal2025qerl` | Weakly related adjacent citation | Not needed for current Ch2 argument | Removed from active bibliography and text citation |
| `gu2025ahakv` | arXiv-only adjacent citation | Not needed for current Ch2 argument | Removed from active bibliography and text citation |
| `velickovic2024softmax` | Workshop/arXiv adjacent citation | Not needed for current Ch2 argument | Removed from active bibliography and text citation |
| `migacz2017tensorrt` | NVIDIA GTC/blog source, uncited | Not used by current main compile | Removed from active bibliography |
| 14 uncited local-library entries | Active BibTeX but not cited by `main.tex` compile path | Mixed formal and technical sources | Archived to `development_history/reference_archive_20260511.bib` |

## Gap Additions Applied

| Key | Source | Why Added |
|---|---|---|
| `su2025rotatekv` | IJCAI 2025 proceedings, DOI `10.24963/ijcai.2025/690` | Supports the low-bit KV recovery discussion around rotations, outlier-aware processing, and 2-bit KV Cache |
| `feng2025adakv` | NeurIPS 2025 accepted OpenReview record | Supports adaptive KV budget allocation as adjacent work to the thesis allocator line |
| `zhou2025dynamickv` | ACL Anthology, Findings of EMNLP 2025, DOI `10.18653/v1/2025.findings-emnlp.426` | Supports task-aware adaptive KV budget adjustment |
| `gao2025rethinkingkv` | MLSys 2025 proceedings | Supports the serving-level claim that quality, compression, and system gains must be jointly checked |
| `du2026bitdecoding` | IEEE HPCA 2026 publication record | Supports low-bit KV decode systems and Tensor Core friendly execution paths |
| `efron1994introduction` | Chapman and Hall/CRC book | Supports Bootstrap confidence intervals in Chapter 4 |
| `benjamini1995controlling` | Journal of the Royal Statistical Society Series B | Supports Benjamini--Hochberg false discovery rate control in Chapter 4 |
| `fang2025longppl` | ICLR 2025 accepted OpenReview record | Supports the long-context PPL protocol-sensitivity discussion |

## Main Cited References After Audit

| Key | Class | Verified Source | Result |
|---|---|---|---|
| `vaswani2017attention` | Formal | NeurIPS 2017 proceedings | Keep |
| `ainslie2023gqa` | Formal | ACL Anthology, EMNLP 2023, DOI `10.18653/v1/2023.emnlp-main.298` | Keep |
| `liu2024kivi` | Formal | PMLR ICML 2024 | Keep |
| `hooper2024kvquant` | Formal | NeurIPS 2024 / OpenReview record | Keep |
| `he2024zipcache` | Formal | NeurIPS 2024 | Keep |
| `xiao2023smoothquant` | Formal | PMLR ICML 2023 | Keep |
| `frantar2023gptq` | Formal | ICLR 2023 | Keep |
| `lin2024awq` | Formal | MLSys 2024 | Keep |
| `dao2022flashattention` | Formal | NeurIPS 2022 | Keep |
| `dao2024flashattention2` | Formal | ICLR 2024 | Keep |
| `tillet2019triton` | Formal | ACM MAPL 2019 | Keep |
| `bai2024longbench` | Formal | ACL Anthology, ACL 2024, DOI `10.18653/v1/2024.acl-long.172` | Keep |
| `hsieh2024ruler` | Formal | OpenReview accepted COLM 2024 | Updated |
| `kamradt2023needle` | Technical source | GitHub benchmark repository | Keep as benchmark source |
| `qwen2025qwen25` | Technical source | Qwen2.5 technical report | Keep as model source |
| `grattafiori2024llama3` | Technical source | Llama 3 technical report | Keep as model source |
| `kwon2023vllm` | Formal | ACM SOSP 2023 | Keep |
| `kang2024gear` | Formal | PMLR volume 262 | Updated |
| `lin2024qserve` | Formal | MLSys 2025 proceedings | Keep |
| `liu2024cachegen` | Formal | ACM SIGCOMM 2024 | Keep |
| `zhao2024atom` | Formal | MLSys 2024 | Keep |
| `gholami2022survey` | Formal | Low-Power Computer Vision book chapter | Added |
| `hubara2018quantized` | Formal | JMLR 2018 | Keep |
| `zhang2024h2o` | Formal | NeurIPS 2023 | Keep |
| `xiao2024efficient` | Formal | ICLR 2024 | Keep |
| `shazeer2019fast` | Technical source | arXiv-only MQA paper | Keep as foundational architecture source |
| `xu2024think` | Formal | ICLR 2025 | Keep |
| `liu2024intactkv` | Formal | ACL Findings 2024, DOI `10.18653/v1/2024.findings-acl.460` | Keep |
| `xiao2024duoattention` | Formal | ICLR 2025 | Keep |
| `li2024snapkv` | Formal | NeurIPS 2024 | Keep |
| `zhang2025clusterattn` | Formal | ACL Anthology, ACL 2025, DOI `10.18653/v1/2025.acl-long.703` | Added |
| `zandieh2024qjl` | Formal | AAAI 2025 proceedings | Updated |
| `duanmu2024skvq` | Formal | OpenReview accepted COLM 2024 | Updated |
| `jiang2023mistral` | Technical source | Mistral 7B technical report | Keep as model source |
| `ashkboos2024quarot` | Formal | NeurIPS 2024 | Keep |
| `xu2025kvtuner` | Formal | PMLR ICML 2025 | Updated |
| `bondarenko2023softmax` | Formal | NeurIPS 2023 | Keep |
| `tao2024asymkv` | Formal | ACL Anthology, COLING 2025, DOI `10.18653/v1/2025.coling-main.158` | Keep |
| `fu2025headkv` | Formal | ICLR 2025 | Keep |
| `su2025outliertoken` | Formal | ACL Anthology, ACL 2025, DOI `10.18653/v1/2025.acl-long.631` | Keep |
| `shutova2025aquakv` | Formal | PMLR ICML 2025 | Updated |
| `liu2025chunkkv` | Formal | NeurIPS 2025 | Keep |
| `yuan2024kvcompressionbench` | Formal | ACL Anthology, EMNLP Findings 2024, DOI `10.18653/v1/2024.findings-emnlp.266` | Keep |
| `su2025rotatekv` | Formal | IJCAI 2025 proceedings | Added |
| `feng2025adakv` | Formal | NeurIPS 2025 accepted OpenReview record | Added |
| `zhou2025dynamickv` | Formal | ACL Anthology, EMNLP Findings 2025 | Added |
| `gao2025rethinkingkv` | Formal | MLSys 2025 proceedings | Added |
| `du2026bitdecoding` | Formal | IEEE HPCA 2026 publication record | Added |
| `efron1994introduction` | Formal | Chapman and Hall/CRC book | Added |
| `benjamini1995controlling` | Formal | Journal of the Royal Statistical Society Series B | Added |
| `fang2025longppl` | Formal | ICLR 2025 accepted OpenReview record | Added |

## Archived Entries

The following entries are not active thesis references after this update and were moved to `development_history/reference_archive_20260511.bib`.

`dao2023flashdecoding`, `dettmers2022gpt3int8`, `schuirmann1987tost`, `jacob2018quantization`, `su2024rope`, `merity2016wikitext`, `ye2025flashinfer`, `madaan2024variance`, `fogliato2024precise`, `song2025nondeterminism`.

## Follow-Up Candidates Not Added

| Candidate | Source | Decision |
|---|---|---|
| FlashInfer | arXiv/tooling source in local BibTeX | Archived because the current thesis text does not cite this backend as a source claim |
| `fogliato2024precise` / `song2025nondeterminism` | Formal evaluation-method papers | Archived because the current statistics paragraph is already supported by standard methods and does not need broader benchmark-variance discussion |
| `jacob2018quantization` / `dettmers2022gpt3int8` | Formal quantization references | Archived because Chapter 2 already cites a focused PTQ/LLM quantization chain through SmoothQuant, GPTQ, AWQ, Gholami and Hubara |
