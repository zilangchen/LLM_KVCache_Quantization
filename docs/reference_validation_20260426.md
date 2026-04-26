# Reference Validation Sweep — 2026-04-26

## Scope

This sweep covers citation keys used by `thesis/chapters/ch1_introduction.tex` through
`thesis/chapters/ch5_conclusion.tex`.

Appendix-only citations are intentionally excluded because `thesis/chapters/appendix.tex`
is currently under separate cleanup. They should be revalidated after the appendix
inventory stabilizes.

## Method

- Extracted all citation keys from Chapter 1--5 and compared them against
  `thesis/references.bib`.
- Checked metadata against primary or near-primary sources: ACL Anthology, PMLR,
  OpenReview, NeurIPS proceedings, MLSys virtual/proceedings pages, ACM proceedings,
  JMLR, and arXiv.
- Updated BibTeX only when the source state was confirmed. When a formal venue could
  not be confirmed, the entry was kept or downgraded to arXiv/preprint wording.

## Key corrections made

| Key | Action |
|---|---|
| `ainslie2023gqa` | Added ACL Anthology pages, publisher, address, and DOI. |
| `bai2024longbench` | Added ACL long-paper venue, pages, publisher, address, and DOI. |
| `liu2024kivi` | Added PMLR series, volume, pages, and publisher. |
| `hooper2024kvquant` | Normalized NeurIPS venue and added volume. |
| `he2024zipcache` | Upgraded from arXiv-only to NeurIPS 2024. |
| `xiao2023smoothquant` | Added PMLR series, volume, pages, and publisher. |
| `qwen2025qwen25` | Replaced group-only author with leading authors and corrected arXiv year to 2024. |
| `kang2024gear` | Upgraded from arXiv-only to ICLR 2025. |
| `liu2024cachegen` | Corrected author list and added SIGCOMM pages/DOI. |
| `hubara2018quantized` | Corrected entry type from `inproceedings` to `article` and moved JMLR to `journal`. |
| `zhang2024h2o` | Corrected NeurIPS year from 2024 to 2023. |
| `xiao2024efficient` | Corrected entry type from `article` to `inproceedings`. |
| `shazeer2019fast` | Corrected arXiv-only MQA entry type from `inproceedings` to `article`. |
| `li2024snapkv` | Corrected author list against the NeurIPS 2024 record. |
| `zandieh2024qjl` | Downgraded unconfirmed ICML venue to arXiv preprint. |
| `ashkboos2024quarot` | Corrected author list against NeurIPS 2024. |
| `agarwal2025qerl` | Updated to ICLR 2026 conference entry. |
| `bondarenko2023softmax` | Updated from workshop/arXiv wording to NeurIPS 2023 proceedings. |
| `gu2025ahakv` | Completed author list from the arXiv/OpenReview record. |
| `tao2024asymkv` | Added COLING pages, publisher, and DOI. |
| `fu2025headkv` | Completed author list from the ICLR 2025 OpenReview record. |
| `su2025outliertoken` | Added ACL 2025 long-paper venue, pages, publisher, and DOI. |
| `liu2025chunkkv` | Normalized NeurIPS 2025 venue and volume. |
| `liu2024intactkv` | Added ACL Findings pages, publisher, and DOI. |
| `yuan2024kvcompressionbench` | Added EMNLP Findings pages, publisher, and DOI. |

## Chapter 1--5 citation inventory

| Key | Status after sweep |
|---|---|
| `agarwal2025qerl` | Verified / updated. |
| `ainslie2023gqa` | Verified / updated. |
| `ashkboos2024quarot` | Verified / updated. |
| `bai2024longbench` | Verified / updated. |
| `bondarenko2023softmax` | Verified / updated. |
| `cai2024pyramidkv` | Verified as arXiv/preprint; no formal venue added. |
| `dao2022flashattention` | Verified; no edit needed. |
| `dao2024flashattention2` | Verified; no edit needed. |
| `dettmers2022gpt3int8` | Verified; no edit needed. |
| `duanmu2024skvq` | Verified as arXiv/preprint; no formal venue added. |
| `frantar2023gptq` | Verified; no edit needed. |
| `fu2025headkv` | Verified / updated. |
| `grattafiori2024llama3` | Verified as arXiv technical report; long author list kept abbreviated. |
| `gu2025ahakv` | Verified / updated. |
| `he2024zipcache` | Verified / updated. |
| `hooper2024kvquant` | Verified / updated. |
| `hubara2018quantized` | Verified / updated. |
| `kang2024gear` | Verified / updated. |
| `kwon2023vllm` | Verified; no edit needed. |
| `li2024snapkv` | Verified / updated. |
| `lin2024awq` | Verified; no edit needed. |
| `lin2024qserve` | Verified / normalized. |
| `liu2024cachegen` | Verified / updated. |
| `liu2024intactkv` | Verified / updated. |
| `liu2024kivi` | Verified / updated. |
| `liu2025chunkkv` | Verified / updated. |
| `nagel2021whitepaper` | Verified as arXiv preprint; no edit needed. |
| `qwen2025qwen25` | Verified / updated. |
| `shazeer2019fast` | Verified / updated. |
| `shutova2025aquakv` | Verified; no edit needed. |
| `su2025outliertoken` | Verified / updated. |
| `tao2024asymkv` | Verified / updated. |
| `tillet2019triton` | Verified; no edit needed. |
| `vaswani2017attention` | Verified; no edit needed. |
| `velickovic2024softmax` | Verified as workshop/OpenReview-style source; no edit needed. |
| `xiao2023smoothquant` | Verified / updated. |
| `xiao2024duoattention` | Verified; no edit needed. |
| `xiao2024efficient` | Verified / updated. |
| `xu2024think` | Verified; no edit needed. |
| `xu2025kvtuner` | Verified; no edit needed. |
| `yuan2024kvcompressionbench` | Verified / updated. |
| `zandieh2024qjl` | Verified / downgraded to arXiv preprint. |
| `zhang2024h2o` | Verified / updated. |
| `zhao2024atom` | Verified; no edit needed. |

## Primary source examples used

- ACL Anthology: `GQA`, `LongBench`, `IntactKV`, `AsymKV`, `Outlier Tokens Tracing`, and `KV Cache Compression Bench`.
  - https://aclanthology.org/2023.emnlp-main.298/
  - https://aclanthology.org/2024.acl-long.172/
  - https://aclanthology.org/2024.findings-acl.460/
  - https://aclanthology.org/2025.coling-main.158/
  - https://aclanthology.org/2025.acl-long.631/
  - https://aclanthology.org/2024.findings-emnlp.266/
- PMLR: `KIVI` and `SmoothQuant`.
  - https://proceedings.mlr.press/v235/liu24bz.html
  - https://proceedings.mlr.press/v202/xiao23c.html
- OpenReview / conference pages: `QeRL`, `QServe`, `GEAR`, `HeadKV`, `DuoAttention`, `ThinK`, `KVTuner`, and `AQUA-KV`.
  - https://openreview.net/forum?id=zw8zxMJJlm
  - https://mlsys.org/virtual/2025/poster/3288
  - https://openreview.net/forum?id=FJFVmeXusW
- ACM/JMLR/arXiv:
  - https://dl.acm.org/doi/10.1145/3651890.3672274
  - https://www.jmlr.org/papers/v18/16-456.html
  - https://arxiv.org/abs/2412.15115
  - https://arxiv.org/abs/2406.03482

## Remaining boundary

This audit does not certify appendix-only citation keys. Once appendix cleanup is
finished, run a second pass over all remaining `references.bib` entries and remove
unused or legacy references if they are no longer cited.
