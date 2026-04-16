# 术语统一词表

> **规则**：首次出现给中英对照「中文（English）」，后续用缩写。代码/配置名保持原样。
> **白名单**（不替换）：`\begin{verbatim}`、`\lstlisting`、`\url{}`、`\code{}` 内。

---

## 统一约定

| 术语 | 变体（待统一） | 统一到 | 首次出现建议 | 备注 |
|------|--------------|--------|--------------|------|
| KV Cache | KV Cache / KV cache / kv cache / kv_cache / 键值缓存 | **首次：键值缓存（KV Cache）；后续：KV Cache** | abstract/ch1 | 代码内保留 `kv_cache` / `KVCache` |
| attention-KL | attention-KL / Attention-KL / attention_KL / 注意力 KL | **统一：attention-KL**（首次出现写明"量化前后注意力分布 KL 散度"） | ch1/ch3 | 小写连字符 |
| GQA | GQA / 分组查询注意力 | **首次：分组查询注意力（GQA）；后续：GQA** | ch1/ch2 | — |
| INT8 / INT4 | INT8 / int8 / INT4 / int4 | **文本：INT8/INT4（全大写）；代码：`int8_*` / `int4_*`** | 全文 | `int4_ours_asym` 等 kv_mode 名保持小写 |
| PPL | PPL / 困惑度 / Perplexity | **首次：困惑度（Perplexity, PPL）；后续：PPL** | abstract/ch4 | — |
| per-channel | per-channel / 逐通道 / 逐通道量化 | **首次：逐通道（per-channel）；后续：per-channel** | ch2/ch3 | — |
| 行为对齐 | 行为对齐 / Behavior Alignment | **首次：行为对齐（Behavior Alignment）；后续：行为对齐** | ch1 | — |
| robust selection | robust selection / 鲁棒选择 | **首次：鲁棒选择（robust selection）；后续：鲁棒选择** | ch4 | — |

---

## 术语变体 grep 预扫统计（2026-04-17 04:22）

- 关键词 grep 命中 784 处（各术语混合计数）
- 详细分解由 D2 STYLE agent 在 P1 完成

---

## D2 agent 输出规范

D2 产出时追加此文件的"已定位变体清单"表格：

| 术语 | 出现位置（file:line） | 当前形式 | 建议替换为 | 是否在白名单内 |
|------|---------------------|----------|-----------|---------------|

---

## D2 已定位变体清单（2026-04-17 完成，映射至 D2_STYLE.md Section D）

### T1. KV Cache 系（Section D.D1）

| 术语 | 出现位置（file:line） | 当前形式 | 建议替换为 | 是否在白名单内 |
|------|---------------------|----------|-----------|---------------|
| 键值缓存 | abstract_zh:8; ch1:16, 219; ch2:7; ch3:1183; ch5:220 | 键值缓存 | 首次"键值缓存（KV Cache）"后续统一 **KV Cache** | 否 |
| KV Cache | 全文 ~110 处（ch1-ch5+appendix 全覆盖） | KV Cache | 保留主形式 | 否 |
| KV cache | abstract_en:9, 10, 11, 13, 34 | KV cache | 英文摘要统一为 **KV cache**（小写 c） | 否 |
| kv_cache / kv_mode | ch3:\code{kv\_mode}; ch4:175-195 表格 | `\code{kv\_mode}` | 保持代码名不动 | **白名单** |

### T2. attention-KL 系（Section D.D2）

| 变体 | 出现位置 | 当前形式 | 建议 |
|------|---------|----------|------|
| attention-KL | 22 处 | attention-KL | **保留** |
| Attention-KL | ch3:62 (caption); ch4:1927 | Attention-KL | → attention-KL（两处改） |

### T3. GQA（Section D.D3）

| 变体 | 出现位置 | 当前形式 | 建议 |
|------|---------|----------|------|
| 分组查询注意力（GQA） | ch2:67（首次引入）; ch3:351, 929 | 首次引入完整形式 | 保留 |
| GQA | 全文 ~60 处 | GQA | 保留缩写主形 |

### T4. INT8 / INT4 / 8-bit / 4-bit（Section D.D4）

| 变体 | 出现位置 | 当前形式 | 建议 |
|------|---------|----------|------|
| INT8 / INT4（正文） | 全文 ~500 处 | INT8 / INT4 | **保留**（全大写） |
| \code{int8\_ours} 等 | ch3:1078; ch4:170-196, 1288 等 | `\code{}` 代码模式 | 保持 | **白名单** |
| 4-bit / 8-bit（表格/图） | ch2:137-157, 368-389; ch4:921-924 | 混用 | 位宽时用 INT*，编码位宽用 *-bit；ch2 表格 L387 `4-bit` 保留（量化级别上下文） |

### T5. PPL / 困惑度 / Perplexity（Section D.D5）

| 变体 | 出现位置 | 当前形式 | 建议 |
|------|---------|----------|------|
| 困惑度 | ch1:43; ch5:65 | 困惑度 | 首次"困惑度（Perplexity, PPL）"后续 PPL |
| PPL | 全文 ~200 处 | PPL | 保留 |
| perplexity | abstract_en:15 | perplexity | 英文小写 |

### T6. per-channel / 逐通道 系（Section D.D6 — 混用最严重）

| 变体 | 出现位置（file:line） | 当前形式 | 建议 |
|------|---------------------|----------|------|
| 逐通道 | ch1:107; ch2:182, 238; ch2:570 | 逐通道 | 首次"逐通道（per-channel）"后续统一 **per-channel** |
| per-channel | ch1:174; ch2:242, 249; ch3:18, 131, 626, 644, 669-687, 857, 881, 890, 1012, 1070, 1194; ch4:181-182, 1289; ch5:34, 185, 208; appendix:570-591 | per-channel | 保留主形式 |
| 逐 token | ch1:107; ch2:238 | 逐 token | 首次"逐 token（per-token）"后续 per-token |
| per-token | 全文 ~25 处（镜像 per-channel） | per-token | 保留 |
| per-group | ch3:98-109, 528-546, 635; ch4:181-183 | per-group | 保留 |
| 逐组 | ch3:508; ch4:177-180 表格描述 | 逐组 | 表格内列"对称 per-group"与正文描述"逐组"一致性需提升；建议表格 per-group，正文首次使用"逐组（per-group）"，后续 per-group |

### T7. 行为对齐 / behavior-aligned（Section D.D7）

| 变体 | 出现位置 | 当前形式 | 建议 |
|------|---------|----------|------|
| 行为对齐（Behavior Alignment） | ch1:86（首次引入） | 中英对照 | 保留 |
| 行为对齐 | 全文 ~30 处 | 行为对齐 | 保留（主中文形式） |
| Behavior-Aligned Calibration | abstract_en:49 关键词 | 大写 | 保留 |
| behavior-aligned | ch4:1195, 1303, 1320; ch4:1627 | 小写连字符 | 保留小写 |
| BA-guided | ch3:681, 693; ch4:182, 1069, 1303, 1705 | BA-guided | 保留缩写 |

### T8. Tensor Core / CUDA Core（Section D.B3）

| 变体 | 出现位置 | 当前形式 | 建议统一为 |
|------|---------|----------|-----------|
| Tensor-core | ch3:889, 891 | Tensor-core | **Tensor Core**（NVIDIA 官方写法） |
| tensor core | ch4:1607, 1615; ch3:891 | tensor core | **Tensor Core** |
| CUDA-core | ch3:889 | CUDA-core | **CUDA Core** |

### T9. Triton 融合核函数系（Section D.D8）

| 变体 | 出现位置 | 建议 |
|------|---------|------|
| Triton 融合核函数 | ch1:120; ch3:23, 38, 184, 767; ch4:483; ch5:68 等 ~30 处 | **主形式保留** |
| Triton 融合核 | ch3:62 caption; ch4:1903 | → Triton 融合核函数（两处改） |
| triton_fused / triton_ra | ch4:175-183 表格 | 保留（代码） | **白名单** |

### T10. robust selection（Section 未单列，但检测到）

| 变体 | 出现位置 | 当前形式 | 建议 |
|------|---------|----------|------|
| robust selection | ch1:78, 153; ch4:296, 313, 319, 327, 329, 362; ch5:20, 241; ch3:12, 1188 | robust selection | 首次"鲁棒选择（robust selection）"（ch3:321 已有），后续 robust selection |
| 鲁棒性优先策略（robust selection） | ch3:321 | 已引入中文 | 保留作为首次引入 |

---

## 计数汇总（grep 2026-04-17）

- KV cache 系: 153 处
- attention-KL 系: ~22 处
- GQA / 分组查询: ~80 处
- INT8/INT4/8-bit/4-bit: ~558 处（正文 + 代码混合）
- PPL / 困惑度: ~165 处
- per-channel / 逐通道: ~40 处
- 行为对齐 / behavior-aligned: ~40 处
- Triton 融合核*: ~37 处
- 第一人称"我们": 22 处（详见 D2_STYLE.md Section A）
