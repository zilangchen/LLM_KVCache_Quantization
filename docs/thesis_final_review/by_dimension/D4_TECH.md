# D4 TECH — 技术严谨性审查报告

> **范围**：`thesis/chapters/ch3_method.tex`（1203 行）+ `thesis/chapters/ch2_related_work.tex`（584 行）+ `thesis/chapters/appendix.tex`（743 行）+ `thesis/setup/commands.tex` + 代码交叉验证
> **代码基线**：main @ e379645 / snapshot `snapshot/pre-thesis-review-2026-04-17`
> **审查视角**：L1 宏观（章节逻辑/前向引用/闭合性）→ L2 段落（公式上下文/伪代码一致性）→ L3 句子（公式正确性/记号一致性/数学断言）
> **原则**：技术正确 > 与代码一致 > 与章间交叉 > 排版细节

---

## A. L1 / L2 / L3 发现总览

### A.1 L1 宏观层面

| # | 发现 | 严重度 |
|---|------|--------|
| L1.1 | **章节逻辑流基本闭合**：ch3 三层结构（度量 → 选择协议 → 实例化）清晰，层一 §3.1–3.2 定义 attention-KL 和两阶段搜索；层二 §3.4 基于对称格式给出 INT8；层三 §3.5 非对称 RoleAlign。前向引用全部落地（`\ref{sec:ch3-static-scale}` 等在 ch3 内部都有定义）。 | — |
| L1.2 | **KL 方向**在 ch3 §3.2.1 明确采用 **forward KL** `D_KL(p_ref ‖ p_quant)`，公式 (3-3)，L218-223，与代码 `calibrate_behavior.py:587` 的实现 `p_ref_safe * (log(p_ref_safe) - log(p_quant_safe))` 一致。**但附录 §A.8 的 §Q 预缩放等价性（eq. A-4, L701-705）没有显式指明方向**。 | L |
| L1.3 | **τ / τ⁻¹ 的名称冲突**：ch3 §3.3 L406 标题是 "温度校正 τ⁻¹"，但 L415 说 "τ⁻¹ 最初作为一个补偿工具", 公式 3-5 L420-422 用 `τ⁻¹_{l,h}` 作为乘法因子(与 `softmax(qK^T · τ⁻¹ / √d_k)` 中的 `τ⁻¹ > 1` 锐化一致)。传统上温度 `T`（正温度因子）在分母 (`softmax(x / T)`)，当 `T < 1` 锐化；本文把 `τ⁻¹` 作为分子乘法因子, `τ⁻¹ > 1` 锐化。这其实是把 `τ = 1/(τ⁻¹)` 暗含使用, **但论文未显式给出 `τ` 的定义**，仅用 `τ⁻¹` 这个派生记号。记号 `τ⁻¹` 在 glossary 和符号表中缺失基础定义。 | M |
| L1.4 | **量化区间不一致**：ch3 §3.4 Table 3-1 明确 INT8 对称 `[-127, 127]` + INT4 对称 `[-7, 7]`；代码 `int8_basic.py:98` `[-127, 127]`、`int4_basic.py:102` `[-7, 7]` ✓；但 `asymmetric_quant.py:71` INT8 非对称使用 `[-128, 127]`、`asymmetric_quant.py:83` INT4 非对称 `[-8, 7]`。**ch3 §3.5 从未给出非对称 INT4 的量化区间 `[-8, 7]` 或 zero-point 计算**，与代码实际实现脱节。 | H |
| L1.5 | **"256 vs 15 量化级别"陈述错误**：ch3 L648 "当位宽降至 4 bit 时，量化级别从 **256** 骤降至 **15**"。按本文 INT8 对称 `[-127, 127]` 是 **255** levels（非 256），INT4 对称 `[-7, 7]` 是 **15** levels — 起点数值是错的（256 对应 INT8 **非对称** `[-128, 127]`，但本文 INT8 明确为对称）。 | M |
| L1.6 | **Group size 默认值冲突**：ch3 §3.4 Table 3-1 L537-538 给出 **Group size g = 128**（对 INT8/INT4 均默认），但 §3.10 `M_int8` 示例 L1148 明确 "默认 **g = 16** 下，INT8 的理论显存比值…"；代码 `calibrate_behavior.py:165` 也 fallback=16；配置 `exp_matrix_*.yaml` 主线全部 `group_size=16`。**Table 3-1 默认值错误**（应改 16 且与正文自洽）。 | H |
| L1.7 | **校准数据集陈述与代码矛盾**：ch3 §3.1.2 L137、L152、L166-168 连续声称 "校准使用 **WikiText-103** 的一个子集（n=128）…，而 PPL 评测使用 **WikiText-2** test split。二者同属 WikiText 家族但分属不同 split，不存在文档级重叠"；但 **代码 `calibrate_behavior.py:197`** 实际加载 `wikitext-2-raw-v1, split="test"`；PPL 评测 `eval_ppl.py:954` 也是 `wikitext-2-raw-v1, split="test"`。**两者用同一数据、同一 split，构成严重的 data contamination 问题**，且论文正文做出与代码相反的"无重叠"论断。附录 Table A-3 L79 也标注 "校准数据源 WikiText-103 (test split)" — 同样错误。 | **CRITICAL** |
| L1.8 | **前向引用链完整性**：ch3 所有 `\ref{sec:exp-*}` / `\ref{subsec:exp-*}` 对 ch4 章节有效性未在本审中逐一展开，仅在 L617-618 "向非对称格式的扩展"与 §3.5 入口存在隐式衔接。 | — |

### A.2 L2 段落层面

| # | 发现 | 严重度 |
|---|------|--------|
| L2.1 | **RoleAlign 非对称公式与章节声明矛盾**：ch3 §3.5.1 L659 章节标题 "**从对称到非对称的格式升级**"；但公式 3-10（L674-677）和 3-11（L683-686）给出的是 `s^K = percentile(|K|, p_K) / q_max` 和 `s^V = percentile(|V|, p_V) / q_max` — 都是**对称** `absmax / q_max` 形式，**没有 zero_point**。代码 `asymmetric_quant.py:118` `scale = (t_max - t_min) / (qmax - qmin)` + `zero_point = t_min - qmin * scale` 才是真正的非对称量化。L859 又承认 "且两者均包含 zero-point 偏移" — **公式本身是对称的，但叙述声称非对称，互相冲突**。 | **CRITICAL** |
| L2.2 | **Algorithm 1 伪代码遗漏 clamp**：L379-384 `for each (p_c, g)`: `s = percentile(|K|, p_c) / q_max`（L381）→ `K_hat = round(K/s) · s`（L382）。代码 `int8_basic.py:98-102` 是 `clamp(round(x/s), -127, 127)` 后再 `· s`。**伪代码 L382 遗漏 `clamp(·, -q_max, q_max)` 步骤**，与正文 eq. 3-8 (L515-517) 矛盾。 | M |
| L2.3 | **`\hat{v}_max / \hat{v}_min` 核内近似 percentile 语义模糊**：eq. 3-24（L914-919）`\hat{v}_max ≈ mean(top-2(v_{i, 1:d_k}))`。但"前 2 大"的对象没说清楚：是单 token 的 d_k 维向量内取前 2 个（那这就是逐 token），还是 tile 内跨 token 取前 2 个？按上下文（per-token V Scale）应该是前者，但 `top-2(v_{i, 1:d_k})` 符号 `v_{i, 1:d_k}` 含糊（`v` 的下标 `i` 未先定义）。**公式的物理量含义不清**。 | H |
| L2.4 | **Algorithm 1 τ⁻¹ 搜索循环变量**：L388-397 内循环 "`for each attention head h = 1, ..., H_q`"。代码 `calibrate_behavior.py:387` `for head_idx in range(num_heads)` 遍历 `num_heads = H_q`，一致 ✓。但 L392 `D_KL(p_ref ‖ softmax(q·K_hat^T · τ⁻¹ / √d_k))` 用 `K_hat` 没有先定义 `K_hat` 在 τ⁻¹ loop 中是"上一阶段选出的最优 s 量化后的值" — 这一隐含假设需在算法说明里显式。 | M |
| L2.5 | **GQA 符号下标矛盾**：ch3 §3.2.2 L355 `GQA 映射：第 h 个 Query 头对应的 KV 头索引为 ⌊h/(H_q/H_{kv})⌋`；ch3 §3.7 eq. 3-32（L933-935） `h_{kv} = ⌊h_q / N_rep⌋`，其中 `N_rep = H_q / H_{kv}`。二者一致，但 §3.2.2 L355 的 `h` 与 §3.7 的 `h_q` 混用（前者省略下标），**同一变量在不同章节不同命名**。 | L |
| L2.6 | **内存公式 ch2 vs ch3**：ch2 eq. 2-5（L104-106）`M_KV = 2 × L × h_{KV} × d_h × s × b`；ch3 eq. 3-20（L1126-1128）`M_fp16 = 2 · L · H_{kv} · S · d_k · 2`。符号从 `d_h → d_k`、`s → S`、`h_{KV} → H_{kv}` 全部变化。同一物理量描述，**两套符号**。 | M |
| L2.7 | **INT4 unpack 公式与代码不一致**：ch3 eq. 3-22（L842-848）描述 `high = x_packed >> 4`（算术右移，保留符号位）、`low = (x_packed << 4) >> 4`（先左移再算术右移实现符号扩展）。代码 `int4_basic.py:292-293` 实际是: `unsigned = packed.to(uint8); high = (unsigned >> 4) & 0x0F; low = unsigned & 0x0F`（**逻辑右移，无符号操作**），随后 L301 `(unpacked.to(int16) - 8).to(int8)`（减 8 offset 恢复符号）。两种方法等价但**实现逻辑完全不同**；论文公式描述的是"算术右移"方式，代码是 "+8 offset" 方式。 | M |
| L2.8 | **分块大小启发式数值不明确**：ch3 L828-830 "当上下文长度 ≥ 8192 时使用 B_s = 128，否则使用 B_s = 64"。代码 `triton_decode_attn_int4.py` 与 `triton_decode_attn_int8.py` 通过 `block_size` 参数传入，默认值从 autotune 决定。**论文给出的启发式是否由代码实际使用需核对**（未在 ch3 标注 autotune）。 | L |
| L2.9 | **JSON 大小数值不一致**：ch3 Fig. 3.2 L112 注 "校准产物 JSON (scales + τ⁻¹, **< 10 KB**)"；附录 §A.2 L42 "产出一个 JSON 文件（**< 10 KB**）"；但 ch3 L1177-1178 "以 Qwen2.5-7B 为例, 参数总量约 1,232 个浮点数, JSON 文件约 **30-50 KB**"。**同一文件在不同处给出不同数量级大小**。 | M |
| L2.10 | **`Scale 精度` 表面对 kernel 实际传入冲突**：ch3 Table 3-1 L540 "Scale 精度 float32"；正文 L520-521 "Scale 张量始终以 float32 精度存储"；但 ch3 §3.6.1 L788-789 Triton kernel 输入 `s^K ∈ R^{...}（FP16）`；代码 `triton_decode_attn_int8.py:346-349` 强制 `k_scale.dtype != torch.float16 → ValueError`。**论文未清楚交代 "存储 fp32 → 调用 kernel 前 cast 到 fp16" 的中间转换步骤**（INT8 对称路径），读者看到"始终 float32"会以为 kernel 输入也是 fp32。 | M |
| L2.11 | **"kivi_style 不使用 inv_tau" vs 代码**：ch3 Table 3-2 L746 "KIVI-style 温度校正：不适用"。但代码 `kivi_style_cache.py:99-100` 接受 `inv_tau` 参数且 `use_attn_temperature` 开关，可供 `int4_kivi_aligned` 模式启用。论文 Table 3-2 说 "不适用" 是**默认语义，不是物理上不可能** — 需澄清。 | L |
| L2.12 | **KIVI residual buffer 论文 vs 本文实现**：ch3 L894-898 "与 KIVI Residual Buffer 的对比：KIVI 推荐将最近 R 个 token 保持 FP16（Residual Buffer），…本文的 RoleAlign 采用离线校准确定静态 Scale，所有 token（含 decode 阶段新增 token）均以统一 INT4 格式存储，**无需 Residual Buffer**"。但代码 `kivi_style_cache.py:104-113`、`role_aware_asym_cache.py:55` 明确实现 `residual_length` 参数并在 `_fp16_k_recent/_fp16_v_recent` 存 FP16 的最近 R 个 token。**论文说"无需"，代码支持** — 这是 "本文默认不用" 而非 "无法用"，应澄清。 | M |
| L2.13 | **LLaMA 3.1 8B 头数实例错误**：ch3 §3.6.5 SM 利用率 L971 "H_{kv}=8（H_q=**28** 或更多）时 Grid 更密"。LLaMA-3.1-8B 实际是 `H_q=32, H_{kv}=8`（GQA 4×）；Mistral-7B 也是 `H_q=32, H_{kv}=8`。**没有实验模型是 "H_{kv}=8, H_q=28"**，这是数字错误（可能是从 7B = H_q=28 的记忆错误）。 | M |

### A.3 L3 句子层面

| # | 发现 | 严重度 |
|---|------|--------|
| L3.1 | **ch2 GQA 符号大小写不统一**：ch2 L63 `$h_Q = h_K = h_V = h$`；L69 `$H_q$、$H_{kv}$`；L70 `$h_Q / h_{KV}$`（后文未再出现 h_Q/h_KV 大小写组合）；L105、L111 `$h_{KV}$`。**同一章内 6 次出现中，至少三种大小写风格混用**（h_Q / H_q / h_{KV} / H_{kv}）。 | H |
| L3.2 | **ch3 GQA 符号大小写**：ch3 全文使用 `$H_q$` 和 `$H_{kv}$`（一致），与 ch2 的 `h_{KV}` 变体冲突。 | 同 L3.1 |
| L3.3 | **eq. 3-3 KL 截断未形式化**：ch3 §3.2.1 L270-284 描述 ε=10⁻⁶ 截断，eq. 3-4（L273-278）`D_KL ≈ Σ p̃_ref (ln p̃_ref − ln p̃_quant)`，其中 `p̃ = max(p, ε)`. 代码 `calibrate_behavior.py:585-587` `clamp(p, min=eps)` 正是此意，但**代码注释 CAL-026 承认 "**破坏了归一化不变量 sum(p)=1, 使计算的 KL 成为已知近似而非真 KL**"**；论文 L283-284 仅说 "截断仅在极端尾部生效，对 KL 值的相对影响 <0.1%，在实际中可以忽略" — **未披露归一化破坏**。 | M |
| L3.4 | **Forward KL 的 "zero-avoiding" 解释正确**：ch3 §3.2 paragraph L253-268 对 forward KL 的 zero-avoiding 性质描述正确（`p_ref > 0 ∧ p_quant → 0` 时 KL → +∞）。 | ✓ |
| L3.5 | **KL 散度的凸性隐含假设**：论文未明示 "KL(p ‖ q) 凸于 q"，仅隐含在 "网格搜索求 argmin" 的可行性中。数学上 forward KL 关于 q 非凸（仅 `−log q_i` 部分 convex in q_i），但对 **σ 绑定到量化 Scale 的子空间** 是凸的 — 这是可 argmin 的微妙数学前提，论文未讨论。 | L |
| L3.6 | **eq. 3-5 `\bm{p}_corrected` 与 eq. A-4 语义**：ch3 eq. 3-5（L420-422）`p_corrected = softmax(qK̂^T · τ⁻¹_{l,h} / √d_k)`，appendix eq. A-2（L691-694）**完全一样**（复制粘贴）。eq. A-4 Q 预缩放等价性不含 `τ⁻¹` **下标 l,h** — 隐式广播但未说明。 | L |
| L3.7 | **均匀分布近似的数值**：ch3 L280-283 "对于 32K 序列，均匀分布下的单 token 概率约 3×10⁻⁵"。核对: 1/32768 = 3.05×10⁻⁵ ✓。 | ✓ |
| L3.8 | **`σ_eff ∝ σ/√N_rep` 规律推导**：ch3 §3.3 L462-471 的直觉论证采用 "independent noise + CLT" 假设。论文 L464-471 正确地披露了 "query heads 共享同一 K 张量, 噪声实际 pairwise 相关, 削弱 1/√N_rep 稀释" — 但随后仍报告 `1/√N_rep` 作为机制归因, 未给出相关性对消耗的定量分析。 | M |
| L3.9 | **eq. 2-8 ch2 非对称 scale 公式正确**：ch2 L168-170 `s = (max(x) − min(x)) / (2^n − 1)`, `z = clamp(⌊−min(x)/s⌋, 0, 2^n−1)`。代码 `asymmetric_quant.py:118, 136` `(t_max − t_min) / (qmax − qmin)`、`zero_point = t_min − qmin · scale`。**ch2 的 z 定义与代码不同**：ch2 z 是 "整数编码"，代码 zp 是 "**浮点偏移量**（见 ENG-047 注释 L119-135）"。本实现用的是浮点偏移而非整数 zp，这是代码级实现细节；但 ch2 描述的 "整数 z" 才是 KIVI 论文的原始定义 — **实现偏离了文献描述**，且在 ch3 §3.5 实例化章节没有交代此偏离。 | **H** |
| L3.10 | **`ln` vs `log`**：ch3 KL 公式（eq. 3-3, 3-4）使用 `ln`（自然对数），单位 "nat" (L238 "信息论解释...nat")；代码 `calibrate_behavior.py:587` `torch.log`（默认自然对数 ✓）。 | ✓ |
| L3.11 | **算术强度 AI 公式正确**：ch3 eq. 3-36（L1162-1167）`AI = 4B_s·d_k / (2B_s·d_k(1 + 4/g)) = 2/(1 + 4/g)`。g=16 时: 2/(1+0.25) = 1.6 ✓。 | ✓ |
| L3.12 | **INT8 mem 理论比值数值一致性**：ch3 L1148 "默认 g=16 下, INT8 的理论显存比值为 (1+4/g)/2 = **62.5%**". 核算: (1 + 4/16)/2 = 1.25/2 = 0.625 = 62.5% ✓; 但 FP16 基准 = 100%, 节省 = 37.5% ✓。 | ✓ |
| L3.13 | **ch3 Table 3-1 Scale 形状 `[B,H,S,D/g]` 与 kernel 输入 `[B,Hkv,S,G]` 对应**：Table 3-1 L542 `Scale 形状 [B, H, S, D/g]` — 与 ch3 L788 kernel 输入 `s^K ∈ R^{B × H_kv × S × G}` 同义（`G = D/g`）。**但 "H" 符号对应的是 H_kv 还是 H_q 未说明** — Table 3-1 用"H"（模糊），kernel 定义明确是 `H_kv`；读者可能误以为 Scale 按 `H_q` 存储。 | M |
| L3.14 | **INT4 范围标注冲突**：ch3 L842 "解包后的 INT8 张量…值域 **[−8, 7]**" — 这里的 INT4 是**非对称的全范围**；但 L512 "INT4: q_max = 7" → 对称路径只到 [−7, 7]。论文**没有澄清** "对称 INT4 值域 [−7, 7] / 非对称 INT4 值域 [−8, 7]" 的区别，仅在 unpack 公式边上 L842 提一笔 `[−8, 7]` 让人困惑。 | H |
| L3.15 | **`1/√N_rep` 的 "N_rep = H_q/H_kv" 使用**：ch3 L463 "σ_eff ∝ σ/√N_rep"。实际 Qwen2.5-1.5B N_rep=6 → 1/√6≈0.408, 7B N_rep=7 → 1/√7≈0.378, LLaMA-3.1-8B N_rep=4 → 1/√4=0.5. **N_rep 不是单调于 H_kv** (H_kv=2, N_rep=6; H_kv=4, N_rep=7; H_kv=8, N_rep=4), 直觉"H_kv 增大 → N_rep 变化 → τ⁻¹ 效果变弱"需小心；论文把 "H_kv" 作为主要关联变量, 但机制归因是 N_rep。二者**非单调关联**，论文未明确解释这个混杂。 | M |

---

## B. 公式勘误表

| 公式编号 | 章节 | 当前形式 | 问题 | 建议修正 |
|---------|------|---------|------|---------|
| 算法 3-1 L382 | ch3 §3.2.3 | `K̂ = round(K/s) · s` | 遗漏 clamp 步骤，与正文 eq. 3-8 不一致 | `K̂ = clamp(round(K/s), -q_max, q_max) · s` |
| eq. 3-10 L674-677 | ch3 §3.5.1 | `s^K_{l,j} = percentile(\|K_{:,j}\|, p_K) / q_max` | 对称 absmax 形式，但章节声称"非对称量化" | 改用非对称 per-channel 形式：`s^K_{l,j} = (max(K_{:,j}) − min(K_{:,j})) / (q_max − q_min)`，并显式给出 `zp^K_{l,j} = min(K_{:,j}) − q_min · s^K_{l,j}`；若保留 `p_K percentile` 裁剪，改为 `quantile(K_{:,j}, 1−p_K/100)`/`quantile(K_{:,j}, p_K/100)` |
| eq. 3-11 L683-686 | ch3 §3.5.1 | `s^V_{l,t} = percentile(\|V_{t,:}\|, p_V) / q_max` | 同 eq. 3-10 — 对称表达但章节是非对称 | 同上，per-token 版本 |
| eq. 3-22 L842-848 | ch3 §3.6.3 | `high = x_packed >> 4`（算术右移）, `low = (x_packed << 4) >> 4` | 代码实现是 "+8 offset" 方式（`int4_basic.py:261-263, 299-301`），与公式描述不同 | 改为描述 +8 offset 方式：`high = (x_packed_unsigned >> 4) − 8; low = (x_packed_unsigned & 0x0F) − 8`，并注明两种方式等价 |
| eq. 3-24 L914-919 | ch3 §3.6.3 core percentile | `v̂_max ≈ mean(top-2(v_{i, 1:d_k}))` | `v_{i, 1:d_k}` 下标 `i` 先未定义，"top-2" 的对象集合含糊 | 明确 `v_i ∈ R^{d_k}` 为单个 token 的 d_k-维向量；`top-2(v_i)` 为该向量中数值最大的 2 个元素；或改用 `v_{i, c_1}, v_{i, c_2}` 明确 "channel c₁, c₂ 为最大的两个 channel" |
| Table 3-1 L537-538 | ch3 §3.4 | Group size `g = 128`（INT8 & INT4） | 与代码 fallback 16、主线 config 16、§3.10 L1148 "默认 g=16" 全部冲突 | 修正为 `g = 16`（或说明 g 为超参数，默认 16） |
| L648 | ch3 §3.5 | "量化级别从 **256** 骤降至 **15**" | INT8 对称是 255 levels（非 256）；256 对应 INT8 非对称 [−128, 127] | 改为 "量化级别从 **255** 骤降至 **15**"（或分别说明 symmetric/asymmetric） |
| Table 3-1 L542 | ch3 §3.4 | Scale 形状 `[B, H, S, D/g]` | 符号 `H` 歧义（H_q 还是 H_kv） | 明确为 `[B, H_{kv}, S, D/g]` |
| eq. 3-20~22 L1126-1146 | ch3 §3.10.2 | 使用 `H_{kv}, d_k, S` | 与 ch2 eq. 2-5 (`h_{KV}, d_h, s, b`) 符号不统一 | 统一全文 GQA 记号；建议以 ch3 全大写风格 (`H_{kv}`、`d_k`、`S`) 为准，同步修改 ch2 |
| L971 | ch3 §3.6.5 SM 利用率 | "H_{kv}=8（H_q=**28** 或更多）" | 无实验模型具有此参数；LLaMA-3.1-8B/Mistral-7B 是 H_q=32 | 改为 "H_{kv}=8（H_q=32）" 并标注模型 |

---

## C. 记号一致性表（主要数学符号）

| 符号 | 首次定义处 | 后续使用 | 是否一致 | 备注 |
|------|-----------|---------|---------|------|
| `bq, bK, bV, bQ, bO` | commands.tex L118-124 | ch2/ch3 全文 | ✓ | 粗体向量/矩阵 |
| `bm{p}_ref, bm{p}_quant` | ch3 eq. 3-1, 3-2 (L208, 215) | ch3 全章 + appendix | ✓ | 首次定义后延续使用 |
| `n`（序列长度） | ch3 eq. 3-1 后 (L211) | ch3 §3.3 + §3.10 | ⚠ | ch3 §3.10 用 `n`、`S` 混用（eq. 3-20 L1127 `S`, L1097 `n`） |
| `d_k`（头维度） | ch3 eq. 3-1 后 (L211) | ch3 + appendix | ✓ | ch3 一致；ch2 L103 `d_h` 是重复定义且同义 |
| `d_h` | ch2 L103 | 仅 ch2 | ✗ | **与 ch3 `d_k` 同义异名** |
| `h`（query head idx） | ch3 L354 | ch3 §3.2 + §3.7 | ⚠ | §3.7 用 `h_q` 带下标 |
| `H_q`（Q head 总数） | ch2 L69 | ch2 + ch3 | ⚠ | ch2 另有 `h_Q` 大写 (L63, 70, 75) — 大小写混用 |
| `H_{kv}`（KV head 总数） | ch2 L69 | ch2 + ch3 + appendix | ⚠ | ch2 L70, 75, 105, 111 用 `h_{KV}`; ch2 L102, 232, 392 用 `H_{kv}` — **同章内并存** |
| `N_rep` | ch3 eq. 3-31 (L931) | ch3 §3.3, §3.7 | ✓ | 定义明确 `N_rep = H_q / H_{kv}` |
| `g`（group size） | ch3 eq. 3-6 L506 | ch3 §3.4 + §3.10 | ⚠ | Table 3-1 默认 128，公式章节默认 16 |
| `p_c, p_K, p_V`（percentile） | ch3 L170, eq. 3-10 L679, 3-11 L688 | ch3 + appendix Table A-3 | ✓ | 清晰区分 |
| `τ⁻¹_{l,h}` | ch3 eq. 3-5 (L420-423) | ch3 §3.3, algorithm 3-1, Table 3-2, appendix §A.8 | ⚠ | `τ` 本身从未定义；仅使用派生记号 `τ⁻¹` |
| `s`（Scale） | ch3 eq. 3-6 L506 | ch3 全章 | ✓ | 对称路径 |
| `s^K_{l,j}, s^V_{l,t}` | ch3 eq. 3-10, 3-11 | ch3 §3.5 | ✓ | |
| `zero_point / zp` | 从未在 ch3 §3.5 公式化定义 | 仅 L859, L906, L909 散见叙述 | ✗ | **ch3 §3.5 声称非对称但未给 zero_point 公式**；ch2 eq. 2-8 有定义但未在 ch3 复用 |
| `B_s`（block size） | ch3 §3.6.1 L795-829 | ch3 §3.6 | ✓ | |
| `q_max`（量化上界） | ch3 L316 | ch3 全章 | ✓ | 对称路径 |
| `q_min`（量化下界） | **从未明确定义** | — | ✗ | 非对称路径需要，论文缺失 |

---

## D. 算法伪代码 vs 代码

| 伪代码块 | 位置 | 代码对应 | 一致性 |
|----------|------|----------|--------|
| **阶段 0: 采集校准样本** | ch3 Algorithm 3-1 L373-377 | `calibrate_behavior.py:collect_samples_*` (近似对应 get_calibration_dataset + forward hook) | ✓ Q 需 layernorm+RoPE 论文和代码都说明，但**实际校准产物 v3_quick 未应用 RoPE**（ch3 L143-152 自陈）→ 论文陈述 vs 实际产物不一致 |
| **阶段 1: Scale 搜索** | Algorithm 3-1 L379-385 | `calibrate_behavior.py:evaluate_quant_candidate` + `select_best_trial` | **✗ 遗漏 `clamp` 步骤**（见 B 表） |
| **阶段 1 robust selection** | ch3 §3.2.2 L321-326 | `calibrate_behavior.py:select_best_trial`（L618-650+） | ✓ "可行集 + P95 KL 升序"，代码实现此策略 |
| **阶段 2: τ⁻¹ 优化** | Algorithm 3-1 L388-397 | `calibrate_behavior.py:compute_inv_tau` (L345-470) | ✓ 代码 L395-425 与伪代码一致；**GQA 映射** (代码 L388 `kv_head = head_idx // kv_ratio`) 与论文 eq. 3-32 一致 |
| **INT4 non-symmetric fused kernel (split-channel)** | ch3 §3.6.3 L864-884 | 未在本审中读取完整 CUDA 实现，但 `triton_decode_attn_int4.py:62-121` 是**通过 materialize INT4 → INT8 后调用 INT8 kernel**，**不是** "split-channel 直接在 kernel 内 nibble 解析" | **⚠** 论文描述的 split-channel 方案与代码 int4 wrapper 通过 INT8 kernel 的 "先物化后复用" 路径不同 — 需确认是否有专用 INT4 asym kernel（可能在其他文件），或论文描述过度工程化 |
| **INT8 融合核函数 online softmax** | ch3 eq. 3-17 L812-819 | `triton_decode_attn_int8.py:254-265` | ✓ `m', α, β, l'` 更新与代码 L255-264 严格对应 |

**重大警示 — split-channel kernel 实现验证**：
论文 ch3 §3.6.3 L862-888 详述 "split-channel 设计方案，在 kernel 内部直接对 packed INT4 字节进行 nibble 解析和非对称反量化"。但目前审查的 `triton_decode_attn_int4.py` 只是**把 packed INT4 unpack 成 INT8 后调用 INT8 kernel**（L99-121）。**论文描述的 split-channel kernel 可能根本未实现，或在代码库其他位置** — 建议 P3 修复时核对代码路径与声明一致性。TR-0407 已记录。

---

## E. Top issue 清单（TR-0400+，追加到 issues.md）

| ID | Dim | Sev | File:Line | Problem | Suggestion | Evidence |
|----|-----|-----|-----------|---------|------------|----------|
| TR-0400 | D4 | **CRITICAL** | ch3_method.tex:137,152,166-168; appendix.tex:79 | 论文声明校准用 WikiText-103，代码实际加载 WikiText-2 test split；PPL 评测也用 WikiText-2 test → **data contamination + 论文陈述错误** | 二选一: (a) 更正论文叙述为 "校准与评测均使用 wikitext-2 test split，但采样的片段不同(前 128 个 > 10 字符样本 vs 按 stride 切分全文)"; 或 (b) 重跑校准改用 wikitext-103 并更新产物 | calibrate_behavior.py:195-197; eval_ppl.py:952-954 |
| TR-0401 | D4 | **CRITICAL** | ch3_method.tex:659-689 | §3.5.1 "非对称格式升级" 章节，公式 eq. 3-10/3-11 仍是**对称** `percentile(\|K\|, p) / q_max` 形式；L859 又说 "均含 zero-point" — **公式描述与章节主张矛盾** | 改写 eq. 3-10/3-11 为标准非对称量化 `s = (max−min)/(q_max−q_min), zp = min − q_min·s`；加入显式公式展示 `q = round((x−zp)/s)` | asymmetric_quant.py:118,136 |
| TR-0402 | D4 | HIGH | ch3_method.tex:537-538,1148 | Table 3-1 默认 Group size=128，§3.10 公式默认 g=16；实际代码/config 都是 16 | 将 Table 3-1 Group size 改为 `16`（与实验默认一致）；或加脚注 "g=128 为历史 INT4 路径, 主实验 g=16" | configs/exp_matrix_*.yaml; calibrate_behavior.py:165 |
| TR-0403 | D4 | HIGH | ch3_method.tex:62-76,102-111 | ch2 内部 GQA 符号大小写混用（`h_Q / H_q / h_{KV} / H_{kv}`）；ch2 eq. 2-5 `d_h, s, h_{KV}` 与 ch3 eq. 3-20 `d_k, S, H_{kv}` 同义异名 | 全文统一为 `H_q, H_{kv}, d_k, S`；在 ch2 首次定义处加 "本文后续统一使用 H_q/H_{kv}" | ch2_related_work.tex:63,69,70,75,105,111 |
| TR-0404 | D4 | HIGH | ch3_method.tex:859,906,909; ch2_related_work.tex:168-170 | 论文多处提 "zero-point"，但 ch3 §3.5 **未给非对称量化公式**；ch2 eq. 2-8 定义 z 为 "整数编码"，而代码 `asymmetric_quant.py:136` 用 "浮点偏移" — 实现偏离文献描述且未交代 | 在 ch3 §3.5.1 开头新增 "非对称量化回顾" 小节, 引用 ch2 eq. 2-8 并**明确说明本文实现使用浮点 zero_point (= t_min − q_min·s)，与 KIVI 原始定义的整数 zp 等价但实现路径不同**；或仅改代码补 round 变整数以匹配文献 | asymmetric_quant.py:119-136 注释 ENG-047 |
| TR-0405 | D4 | HIGH | ch3_method.tex:842,856,648 | INT4 值域 `[−7,7]` (对称) vs `[−8,7]` (非对称) 共存，但论文**从未明确给出"非对称 INT4 值域 [−8,7]"**；只有 unpack 公式旁 L842 提一次 | 在 Table 3-1 加第二列 "INT4 非对称" 或在 §3.5 首段显式给出量化区间；L648 "256 → 15" 改为 "255 → 15" | asymmetric_quant.py:83; int4_basic.py:98 |
| TR-0406 | D4 | HIGH | ch3_method.tex:914-919 | eq. 3-24 `top-2(v_{i, 1:d_k})` 下标与 "top-2" 对象含糊，无法从公式唯一还原算法意图 | 改为 `v_i ∈ R^{d_k}; v̂_{max,i} ≈ mean(sort(v_i, descending)[:2])`, 或直接给出 pseudocode 片段 | — |
| TR-0407 | D4 | HIGH | ch3_method.tex:864-888 | 论文详述 "split-channel kernel 直接在 kernel 内部 nibble 解析"，但审查的 `triton_decode_attn_int4.py` 实际是 "先 materialize INT4→INT8 后调用 INT8 kernel" — 可能论文描述的 kernel **未实现** | 核对代码库是否存在另一专用 INT4 asym kernel（如 triton_decode_attn_int4_asym.py）；若无，修正论文描述；若有，补充文件路径 | triton_decode_attn_int4.py:62-121 |
| TR-0408 | D4 | MED | ch3_method.tex:382 | Algorithm 3-1 伪代码 `K̂ = round(K/s) · s` 遗漏 clamp | `K̂ = clamp(round(K/s), −q_max, q_max) · s` | int8_basic.py:98 |
| TR-0409 | D4 | MED | ch3_method.tex:648 | "量化级别从 **256** 骤降至 **15**" (INT8 对称是 255 levels) | 改 "从 **255** 骤降至 **15**" | Table 3-1 L537 量化范围 [−127,127] |
| TR-0410 | D4 | MED | ch3_method.tex:971 | "H_{kv}=8（H_q=**28** 或更多）" — 无实验模型具有此参数 | 改 "H_{kv}=8（H_q=32, 如 LLaMA-3.1-8B）" | ch2 L75 Qwen2.5-7B 28 Q heads |
| TR-0411 | D4 | MED | ch3_method.tex:842-848 | eq. 3-22 unpack 公式描述 "算术右移"，代码实际用 +8 offset 方式 | 改公式为 `h = (x_uint >> 4) − 8; l = (x_uint & 0x0F) − 8`，注 "与算术右移方式等价" | int4_basic.py:291-301 |
| TR-0412 | D4 | MED | ch3_method.tex:112,1177-1178; appendix.tex:42 | 校准产物 JSON 大小叙述冲突：`<10 KB` vs `30-50 KB` | 统一: 以 appendix `<10 KB` 为准, 或具体说明 "小模型 (1.5B) ~10KB, 大模型 (7B) ~30-50KB" | — |
| TR-0413 | D4 | MED | ch3_method.tex:520-521,540,788-789 | Table 3-1 "Scale 精度 float32" vs Triton kernel 输入 FP16 — 论文未说明中间 cast | 在 §3.6.1 或 Table 3-1 脚注加 "Triton kernel 调用前 cast 至 FP16" | triton_decode_attn_int8.py:346-349 |
| TR-0414 | D4 | MED | ch3_method.tex:894-898 | "RoleAlign 无需 Residual Buffer" vs 代码 `residual_length` 参数已实现 | 改为 "RoleAlign 默认不启用 Residual Buffer, 实现上支持但主实验未开启" | kivi_style_cache.py:104-113 |
| TR-0415 | D4 | MED | ch3_method.tex:462-471,1199 | `H_{kv}` 作为关联变量与 `N_rep` 作为机制变量非单调（H_kv=2 ↔ N_rep=6, H_kv=4 ↔ N_rep=7, H_kv=8 ↔ N_rep=4），但论文按 `H_kv` 单调线性叙述 | 在 §3.3 "机制直觉" 段补：注意 N_rep 和 H_kv 不单调；若用 σ_eff ∝ σ/√N_rep 机制, 应按 N_rep 排序（6, 7, 4 → 1.5B/7B/8B 对应 σ_eff 系数 0.408/0.378/0.5），与 H_kv 单调叙述不一致 | — |
| TR-0416 | D4 | MED | ch3_method.tex:406,415 | τ 本身从未定义，仅用派生 τ⁻¹；读者无法从论文内推出 "τ⁻¹ > 1 意味 τ < 1" | 在 §3.3 首段加："设 τ > 0 为 softmax 温度，本文直接使用 `τ⁻¹` 作为乘法因子以避免在 softmax 分母中除法。` τ⁻¹ > 1` 等价于 `τ < 1`, 对应分布锐化" | — |
| TR-0417 | D4 | MED | ch3_method.tex:270-284 | eq. 3-4 KL 截断 `p̃ = max(p, ε)` **破坏归一化** (sum p̃ ≠ 1)，代码 CAL-026 承认为 "已知近似"，论文未披露 | 加一句 "截断 clamp 操作使 Σp̃ 轻微偏离 1, 按 CAL-026 分析对相对 KL 误差 <0.1%，对 argmin 决策无实质影响" | calibrate_behavior.py:581-584 注释 |
| TR-0418 | D4 | LOW | ch3_method.tex:542 | Table 3-1 Scale 形状 "H" 歧义 | 明确为 `H_{kv}` | — |
| TR-0419 | D4 | LOW | ch3_method.tex:355 | `⌊h/(H_q/H_{kv})⌋` 中 `h` 未带下标，与 §3.7 `h_q` 并存 | 统一为 `h_q` | — |
| TR-0420 | D4 | LOW | ch3_method.tex:24 | `τ⁻¹` 作为"诊断过程中观察到的启发式呈现" — 在本章总纲中唯一出现；下游章节大量使用 | 无动作；叙述定位准确 | — |

---

## F. 综合结论

### F.1 严重度汇总
- **CRITICAL（2）**：TR-0400（data 描述矛盾）、TR-0401（§3.5 非对称公式对称化）
- **HIGH（6）**：TR-0402, TR-0403, TR-0404, TR-0405, TR-0406, TR-0407
- **MEDIUM（10）**：TR-0408~TR-0417
- **LOW（3）**：TR-0418, TR-0419, TR-0420

### F.2 优先级建议
1. **立即处理 (P3a CRITICAL)**：TR-0400 (数据集声明) + TR-0401 (非对称公式) — 这两项是"**方法论的主要卖点**（RoleAlign 非对称格式 + 行为对齐校准），公式与章节主张不一致会被审阅人判定为严谨性不足
2. **P3b HIGH**：TR-0402 (g=16)、TR-0403 (GQA 符号)、TR-0404 (zero_point)、TR-0405 (INT4 值域)、TR-0406 (top-2 含糊)、TR-0407 (kernel 实现 vs 描述核对)
3. **P3c MED**：TR-0408~TR-0417，多数为公式细节补完/澄清
4. **P3d LOW**：TR-0418~TR-0420，排版/记号微调

### F.3 与其他维度的交叉
- TR-0400 与 **D3 DATA** 可能交叉（PPL 数值来源）
- TR-0401 与 **D6 ATK** 交叉（审阅人/答辩直接攻击点）
- TR-0403 与 **D1 FMT** 可能有记号统一规范的交集

### F.4 闭合评价
论文章节推理 **L1 宏观逻辑闭合** (3 层框架清晰), 但 **L2 / L3 层面存在多处关键公式错误或与代码脱节**。最严重的是 `§3.5 RoleAlign` — 作为论文核心贡献之一，其关键公式 3-10/3-11 竟是对称量化形式而非非对称 — 这在 blind review 时会立刻被挑出，**必须在交稿前修正**。

---

_审查生成时间：2026-04-17_
_Reviewer: D4 TECH agent_
_交叉验证代码分支: main @ e379645_
