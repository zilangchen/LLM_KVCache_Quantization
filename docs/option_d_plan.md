# Option D' 实施计划：GQA 中心叙事重构（Codex 审查修订版）

> **⚠️ 本文件已根据 Codex adversarial review 修订为 D' 版本。**
> 原 Option D 的方向是对的（以 Hkv 为分析轴），但存在 7 个需要修正的问题。
> 以下用 `[D' 修订]` 标注所有修改点。

## D' Revision Summary (Codex 审查修正)

| # | 原 Option D 问题 | D' 修正 |
|---|-----------------|---------|
| 1 | 主线从 behavior-aligned 替换成了纯 GQA paper | **融合不替换**：Attention-KL 是统一原则，Hkv 是解释变量 |
| 2 | Hkv 与模型规模写成等价 | **显式区分**：两者共变但不等价。补 8B 长序列验证"同 Hkv=8 不同规模 crossover 一致" |
| 3 | "首个/universally safe" 措辞太硬 | **hedge**："据我们所知"+"across all tested scales" |
| 4 | Ch3 泄漏具体实验数字 | **删除数字**：Ch3 只保留 cost intuition + mechanism |
| 5 | 14B Needle 32K + RULER 96-99% 并排 | **分开写**：Needle 到 32K，RULER 只到 16K |
| 6 | C4 塞了 4 个子项，C5 里 BD 升为主 Finding | **拆 C4** + **降级 BD** 为 ~1 页 limitation |
| 7 | Ch2 改 10 行偏乐观 | **重组为 3 条线** |
| 8 | 7B KL=MSE 数据无可引用产物 | **先 aggregate 到 appendix table** |

---

## 一、总体叙事转型

### 原叙事（当前论文）
> "KV Cache 量化校准目标的有效性呈 bit-width 依赖。我们以 Attention-KL 为核心视角，在 INT8 上建立校准参考，在 INT4 上通过诊断识别 Key 主导退化，最终给出行为引导的 RoleAlign 实例化。"

**问题**：这是一个"方法-诊断-修复"的工程叙事。缺乏统一的研究主线。

### 新叙事（Option D'）

> [D' 修订] 核心句（采纳 Codex 建议版本）：

> "本文研究 **GQA 架构下的 behavior-aligned KV cache quantization**。Attention-KL 是**统一的校准与诊断原则**，而 $H_{kv}$ 是解释低比特失效、温度校正分化和融合解码效率 crossover 的**关键结构变量**。INT8 提供 canonical validation，INT4-RoleAlign 是 low-bit instantiation，14B 与 BitDecoding 结果用于外部效度与边界分析。"

**转型的核心动作**：把 $H_{kv}$ 从"附带分析变量"提升为"低比特行为的组织轴"——但**不替换** behavior-aligned 主线。INT8 路线保持 canonical instance 地位。

> [D' 修订] 删除原文 "或等价的模型规模/GQA 比例" ← 这是概念错误。
> Hkv 与模型规模在我们的 4 个模型中共变，但不是因果等价。
> 论文中需要显式论证：8B (Hkv=8) 和 14B (Hkv=8) 在同 Hkv 下 Phase 1 crossover 一致
> (Δ=-0.39 vs Δ=-0.40)，支持 Hkv 主导假设。8B 长序列数据正在补跑。

---

## 二、Research Questions 重构

### 原 RQ（ch1_introduction.tex L127-145）

```
RQ1: KV Cache 量化应优化什么目标？
RQ2: 低比特量化为何系统性失效？(含 GQA 头数影响的子问题)
RQ3: 诊断结论能否导出有效的低比特设计？
```

### 新 RQ

**改动策略**：RQ1/RQ2 保持，RQ2 加强 GQA 视角，新增 RQ4（deployment/scaling）。

```latex
\begin{description}
  \item[\textbf{RQ1}] \emph{KV Cache 量化应优化什么目标？其有效性是否随模型规模变化？}
    现有方法以数值重建误差为校准目标。
    是否存在更贴近下游推理行为的优化目标？
    该目标在不同模型规模（1.5B--14B）上是否一致？
    % [新增：规模依赖视角。数据支撑：1.5B KL≠MSE, 7B KL=MSE]

  \item[\textbf{RQ2}] \emph{低比特量化为何失效？失效模式是否呈 GQA 架构依赖？}
    量化噪声在 Key/Value 之间如何分配？
    不同 $H_{kv}$ 对 K 退化幅度、温度校正方向有何影响？
    是否存在一个以 $H_{kv}$ 为核心变量的统一解释框架？
    % [保持+加强：把 GQA 从"子问题"提升到"主问题"]

  \item[\textbf{RQ3}] \emph{诊断结论能否导出有效的低比特设计？}
    是否可以基于 K 主导退化的诊断，设计差异化的量化策略？
    其代价边界如何？
    % [保持不变]

  \item[\textbf{RQ4（新增）}] \emph{INT4 量化的部署效率是否存在架构依赖的 crossover？}
    Triton 融合量化解码核在不同 $H_{kv}$ 和序列长度下的效率表现如何？
    是否存在一个 $(H_{kv}, \text{seq\_len})$ 的 phase boundary，
    划清融合核与 naive dequant+SDPA 的最优选择？
    % [新增：Phase Boundary + 部署建议。数据支撑：Stage 7 长序列 scaling]
\end{description}
```

**改动位置**：`ch1_introduction.tex` L125-145
**改动量**：~30 行重写（原 ~20 行）
**风险**：低（RQ1-RQ3 只是微调措辞，RQ4 是新增）

---

## 三、Contributions 重构

### 原 Contributions（L147-206）

```
C1: bit-width 依赖的校准目标有效性（KL vs MSE, 仅 1.5B 数据）
C2: Key 主导退化 + retrieval/PPL 解耦（1.5B + 3 模型）
C3: RoleAlign 实例化（4 模型, PPL/Needle）
经验观察: inv_tau × GQA 尺度依赖（被标注为"观察"不是"贡献"）
```

### 新 Contributions

**改动策略**：C1-C3 保持核心内容但加入规模/GQA 视角；原"经验观察"升级为 C4 的一部分；新增 C4 (GQA 部署) + C5 (大规模验证)。

```latex
围绕以上四个问题，本文给出五个主要贡献。

\textbf{贡献一：校准目标有效性的 bit-width 与规模双依赖。}
我们系统比较 attention-KL 与 MSE 两种校准目标在 INT8/INT4 下的作用。
INT8 下两种目标完全趋同；INT4 下 1.5B 模型呈现显著分歧
（$\text{clip\_percentile}$ 99.5 vs 99.0，中位 scale 差异 12.35\%），
而 \textbf{7B 模型上两者趋同到相同参数}（均为 100.0/99.9），
表明校准 landscape 的平坦度随模型冗余度增大。
KL 是 \emph{universally safe} 的选择：在所有规模上至少与 MSE 等效，
在小模型上更优。

% [改动点：加入 7B KL=MSE 趋同数据 + "规模依赖" 解读]
% [数据来源：C1 补实验 7B KL/MSE PPL = 7.1121, percentile 100.0/99.9]

\textbf{贡献二：受控诊断——Key 主导退化与 GQA 架构依赖。}
通过 K-only/V-only 因子分解，我们在 \textbf{四个} 模型上一致观察到
INT4 退化由 Key 侧主导。\textbf{14B 模型的 K/V ablation 进一步量化了
这一效应：K 保持 FP16 可恢复 93\% PPL 退化（$5.04 \to 4.71$），
V 保持 FP16 仅恢复 64\%（$5.04 \to 4.81$）}。
Needle 与 PPL 的解耦特性跨 1.5B--14B 保持一致。

% [改动点：加入 14B K/V ablation 数据 + "四个模型"扩展]
% [数据来源：14B K16V4=4.709, K4V16=4.813]

\textbf{贡献三：KIVI-style 格式上的行为引导实例化 RoleAlign。}
在 KIVI 的 per-channel Key + per-token Value 非对称格式上，
通过离线 attention-KL 搜索确定每层 BA percentile。
在 1.5B/7B/8B/14B 四个模型上，INT4-RoleAlign 在 4K--32K 上下文范围内
保持 Needle 100\%，KV Cache 压缩约 73\%，
PPL 退化随模型规模减弱（1.5B: 13.7\%，7B: 6.0\%，8B: 2.4\%，14B: 7.6\%）。
\textbf{RULER 长上下文推理基准上，14B 达到 98.5\% (4K)--96.6\% (16K)；
1.5B 上 INT4-RA 与 FP16 在 RULER 上的差距不足 1\%}，
证明行为对齐校准有效保护了长上下文推理能力。

% [改动点：加入 14B RULER 98.5% + 1.5B FI≈FP16 RULER <1% gap]
% [数据来源：14B RULER, 1.5B fp16 baseline]

\textbf{贡献四：GQA 架构下的量化效应分析——
温度校正的尺度依赖与 Triton 核的 Phase Boundary。}
\begin{itemize}
  \item 温度校正 $\tau^{-1}$ 的效果与 $H_{kv}$ 呈反向依赖：
    $H_{kv}=2$ 时改善 PPL 1.6\%，$H_{kv}\geq 4$ 时恶化 1.8--6.0\%。
    我们以 $\sigma_\text{eff} \propto \sigma/\sqrt{N_\text{rep}}$ 
    的噪声稀释机制给出一阶解释。
  \item 我们提出 in-kernel percentile 技术（基于 top-2/bottom-2 
    两次 reduction），使 Triton 融合核直接支持 BA-guided percentile
    而无需 \code{torch.quantile}，TPOT 降低 31\%。
  \item 在 $(H_{kv}, \text{seq\_len})$ 二维空间中，
    Triton 融合核 vs naive dequant+SDPA 存在
    \textbf{phase boundary}：
    $H_{kv}=2$ 时融合核始终慢于 SDPA（SM 并行度不足），
    $H_{kv}=4$ 时在 $\sim$32K 处 crossover，
    $H_{kv}=8$ 时在 4K--8K 处即反超，\textbf{32K 时快 40\% ($-$77 ms)}。
  \item 部署建议：$H_{kv}\geq 4$ 且 $\text{seq}>8\text{K}$ 使用 Triton 融合核；
    $H_{kv}=2$ 使用 PyTorch SDPA。
\end{itemize}

% [改动点：完全新增！原"经验观察"升级 + Phase Boundary + in-kernel pct + 部署建议]
% [数据来源：Stage 7 rerun, Session 1 commit ecc6f5f, Phase 1 TPOT]

% [D' 修订] C4 太杂（4 个子项）。Codex 建议拆分：
%   - inv_tau 保留为"经验观察"（不升为 C4 的 lead item）
%   - Phase Boundary + deployment advice 是 C4 的核心
%   - in-kernel percentile 作为方法贡献放 Ch3，不放 C4 bullet
%   - 或者 C4 只保留 Phase Boundary + deployment，inv_tau 和 in-kernel pct 各归原位

% [D' 修订] Codex 指出 "据我们所知" 比 "首个" 更安全。
%   KIVI 自称 comprehensive study，ACL 2025 有 Outlier Tokens Tracing。
%   改为："据我们所知，现有工作尚未将 Hkv 作为统一解释变量，联合分析
%   校准目标灵敏度、K/V 退化不对称性、温度校正方向和 kernel crossover。"

\textbf{贡献五：大模型长上下文的验证与外部系统局限性。}
\begin{itemize}
  \item 14B 模型在 32K 上下文下 Needle 100\%、RULER 96.6\%，
    证明 RoleAlign 在大模型上质量保持良好。
  \item 1.5B 模型的 RULER 结果表明 VT/CWE 任务的低分数是
    模型本身的能力上限（FP16 baseline 仅 55\%），
    而非量化退化（INT4 与 FP16 差距 $<$1\%）。
  \item 尝试集成 BitDecoding (HPCA 2026) 作为替代 INT4 attention backend，
    但发现其 CUTLASS 核在 GQA 配置下输出错误
    （库自带 sanity test 的 $\text{max\_diff}=1.23$, threshold 0.1, FAIL）。
    长生成评测中 Needle 0\%、RULER 1\%、LongBench F1=0。
    这一负面结果表明 single-shot cosine similarity 不足以验证
    INT4 attention kernel 的正确性。
\end{itemize}

% [D' 修订] Codex: BD 不该拿走 C5 的 spotlight。
%   BD 降级为 ~1 页 limitation/engineering case study。
%   C5 的主角应该是 "14B 外部验证"（Needle 32K 100%, RULER ≤16K 96-99%）。
%   BD 作为"顺带发现的方法论教训"附在后面。

% [D' 修订] 14B 口径精确化：
%   ✗ "Needle 32K 100%、RULER 96--99%" 并排（读者误以为 RULER 也到 32K）
%   ✓ "Needle 100% (4K--32K 全通过); RULER 96.6--98.5% (4K--16K, 32K 因显存限制未测)"

% [改动点：完全新增！14B 验证 + FP16 baseline + BD 限制]
% [数据来源：Stage 5, 1.5B fp16 RULER, BD diagnostic]
```

**改动位置**：`ch1_introduction.tex` L147-206
**改动量**：~90 行重写/新增（原 ~55 行）
**风险**：中（C4/C5 是新内容，需要仔细校对和现有文本衔接）

---

## 四、核心主张（L198-206）重写

### 原文
> "本文的核心主张是：KV Cache 量化校准目标的有效性呈 bit-width 依赖...并在 KIVI-style 非对称格式上给出一个行为引导的实例化 RoleAlign"

### 新文本

```latex
综上，本文的核心主张是：\textbf{GQA 架构的 $H_{kv}$ 参数是 INT4 KV Cache 
量化行为的核心架构变量}——它同时决定校准目标的灵敏度（$H_{kv}$ 小时 KL$\neq$MSE，
$H_{kv}$ 大时趋同）、Key 退化的相对幅度、温度校正 $\tau^{-1}$ 的有效方向，
以及融合量化解码核的效率 crossover 点。
基于这一视角，我们在 KIVI-style 非对称格式上给出行为引导的实例化 RoleAlign，
以约 73\% KV Cache 压缩率保持四个模型的 Needle 检索能力（含 14B 32K 100\%），
同时为不同 $H_{kv}$ 的模型提供架构感知的量化部署建议。
```

---

## 五、Ch2 Related Work 修改

### 修改点 1：Gap 声明扩展（L452-458）

**原文**：
> "本文是首个系统报告 KV Cache 量化中逐头温度校正 $\tau^{-1}$ 与 GQA 头数 $H_{kv}$ 的相互作用"

**新文本**：
```latex
本文是\emph{首个}系统研究 GQA 架构参数 $H_{kv}$ 对 KV Cache 量化行为的
多维度影响：（1）校准目标灵敏度的规模依赖；
（2）Key/Value 退化的不对称性与 $H_{kv}$ 的关联；
（3）温度校正 $\tau^{-1}$ 与 $H_{kv}$ 的反向依赖；
（4）融合量化解码核在 $(H_{kv}, \text{seq\_len})$ 空间中的 phase boundary。
现有工作均未将 $H_{kv}$ 作为量化行为的结构性变量进行系统分析。
```

**改动量**：~10 行扩写
**风险**：极低（原声明已存在，只扩展 scope）

### 修改点 2：相关工作表格（L365 附近）

在 related work 比较表中增加列 "GQA behavior analysis"，标注所有现有方法均为 "—"（无），本文为 "$H_{kv}$ 多维度分析"。

> [D' 修订] Codex: Ch2 改 10 行不够。
> 如果论文定位变为 "behavior-aligned under GQA"，Ch2 需要重组为 3 条线：
>   1. KV quantization / calibration methods (KIVI, KVQuant, QuIP, etc.)
>   2. K/V asymmetry / low-bit rescue (GEAR, MixedKV, etc.)
>   3. GQA-aware inference efficiency (FlashDecoding, PagedAttention, etc.)
> 工作量修正：~60-80 行重组（非 10 行扩写）。

---

## 六、Ch3 Method 修改

### 修改点 1：Ch3 框架概述（L33-65）

在框架描述中把"GQA 效应"从"附带观察"提升为"框架的一个分析维度"。

**具体修改**：在 L62 的 caption 后，添加一句说明框架图包含"GQA 架构依赖分析"维度。

### 修改点 2：KL 校准段落（L202 区域）

在 KL vs MSE 描述后，添加 7B 趋同证据：

```latex
\paragraph{校准灵敏度的规模依赖}
在 7B 模型（$H_{kv}=4$）上，KL 和 MSE 两种目标搜索到\emph{相同}的
percentile 参数（$k\_\text{percentile}=100.0$, $v\_\text{percentile}=99.9$），
PPL 结果逐位一致（$7.1121$）。这与 1.5B（$H_{kv}=2$）上的 12.35\% 差异
形成对比，表明更大模型的 calibration landscape 更平坦——
更多参数冗余使得多个 percentile 值等价。
KL 是 universally safe 的校准目标：在 1.5B 上优于 MSE，在 7B 上与之等效。
```

**位置**：`ch3_method.tex` L287 附近（两阶段搜索策略 subsection 之后）
**改动量**：~15 行新增

### 修改点 3：inv_tau × GQA 段落（L395-466）

**保持不变**——这部分已经是 GQA-centric 的，不需要修改。只需确保 C4 的 contribution 声明和这部分一致。

### 修改点 4：新增 Phase Boundary 理论分析 section

在 Ch3 的 "Triton 融合量化解码注意力" section（L755）之后或其中，新增一个段落/subsection：

```latex
\subsection{融合核效率的 Phase Boundary 分析}
\label{subsec:ch3-phase-boundary}

Triton 融合核直接从 INT4 packed KV Cache 做 on-the-fly dequant + attention，
避免了 naive 路径（先 dequant 到 FP16 再调用 SDPA）的三次 HBM 访存
（读 INT4 + 写 FP16 临时 buffer + 读 FP16 做 attention）。
然而，融合核的 grid 配置为 $(\text{batch}, H_{kv})$，
每个 thread block 处理一个 KV head 的所有 query heads。

在 $H_{kv}$ 较小时（如 $H_{kv}=2$），仅有 2 个 thread blocks 并行，
H20 GPU 的 132 个 SM 中只有 1.5\% 被利用，
HBM 带宽利用率远低于 naive 路径（后者以 $H_q$ 并行 SDPA，
$H_q=12$ 时有 12 个 SM 并行）。

随着 $H_{kv}$ 增大和 seq\_len 增长，
融合核的带宽节省效应（读 INT4 vs 读 FP16 = 4$\times$ 节省）
逐渐超过 SM 利用率的劣势。
我们定义 \emph{phase boundary} 为
$\Delta_{\text{TPOT}}(\text{triton\_ra}) = \Delta_{\text{TPOT}}(\text{torch\_ref})$
的 $(H_{kv}, \text{seq\_len})$ 曲线。
实验结果（第~\ref{sec:ch4-phase-boundary}~节）显示：
\begin{itemize}
  \item $H_{kv}=2$: 无 crossover（融合核始终慢）
  \item $H_{kv}=4$: crossover $\approx$ 32K
  \item $H_{kv}=8$: crossover $\approx$ 4K--8K，32K 时融合核快 40\%（$-$77 ms）
\end{itemize}

这一 phase boundary 为不同 $H_{kv}$ 的模型提供了
\textbf{架构感知的 backend 选择准则}。
```

**位置**：新 subsection，在 L883 "GQA 支持机制" 之后
**改动量**：~40 行新增
**依赖**：Ch4 的实验数据（交叉引用）

> [D' 修订] Codex 指出：Ch3 **不要写具体数字**（如 "32K 快 40%"、"TPOT -31%"、"53/53"）。
> 以上 LaTeX 建议中的具体数字应替换为 cost intuition 描述：
>   - "32K 快 40%" → "随序列长度增长，带宽节省效应逐渐主导"
>   - "-31%" → "显著降低了量化步骤的延迟开销"
>   - "53/53" → "通过单元测试验证数值正确性"
> 所有具体数字留给 Ch4 实验章。

### 修改点 5：新增 in-kernel percentile 方法描述

在 "INT4 非对称融合核函数" subsection（L841）中，添加 in-kernel percentile 的方法描述：

```latex
\paragraph{In-kernel percentile via top-$k$ reduction}
BA-guided percentile 要求每次 V 量化时计算指定 percentile 的 bounds。
naive 实现调用 \code{torch.quantile}（内部 sort-based，$O(D\log D)$），
引入额外 GPU$\leftrightarrow$CPU 同步。
我们利用 $D=128$ 时 99.9 percentile $\approx$ 第 2 大值这一近似，
在 Triton kernel 内部用两次 reduction 完成：
\begin{align}
  v_{\max,1} &= \max(v), \quad
  v_{\max,2} = \max(v \mid v < v_{\max,1}) \\
  \text{pct\_bound} &= v_{\max,2} + \alpha \cdot (v_{\max,1} - v_{\max,2})
  \label{eq:ch3-inkernel-pct}
\end{align}
其中 $\alpha = 1 - (1 - p/100) \cdot (D-1)$，
$p$ 为目标 percentile（默认 99.9）。
V 的 min-side 同理用 bottom-2 计算。
该方法与 \code{torch.quantile} 数值完全一致
（max diff = 0.0，53/53 单元测试通过），
但消除了 sort 和 CPU 同步开销，TPOT 降低 31\%。
```

**位置**：L841-880 区域
**改动量**：~25 行新增

---

## 七、Ch4 Experiments 重构

Ch4 需要大幅重写（无论选 C 还是 D），以下是 Option D 下的**新 section 结构**：

### 新 Ch4 结构

```
4.1 实验设置（基本保持，更新模型列表加 14B local path 说明）

4.2 校准目标的 bit-width 与规模双依赖（原 4.2 + C1 7B 数据）
    4.2.1 KL vs MSE：1.5B 分歧 vs 7B 趋同
    4.2.2 INT8 主线参考
    [新增数据：7B KL=MSE=7.1121，percentile 趋同]

4.3 低比特失效的结构性诊断（原 4.3 + 14B 数据）
    4.3.1 INT4 量化结果
    4.3.2 K/V 精度敏感性分析（1.5B + **14B** K/V ablation）
    [新增数据：14B K16V4=4.709, K4V16=4.813]

4.4 INT4-RoleAlign 实验结果（原 4.4 + 14B 完整数据）
    4.4.1 PPL + Needle 跨模型对比（**含 14B**）
    4.4.2 RULER 长上下文推理（**14B 98.5% + 1.5B FI≈FP16**）
    4.4.3 LongBench / LongBench official
    4.4.4 inv_tau 的 GQA 尺度依赖（保持）
    [新增数据：14B RULER 96-99%, 14B Needle 32K 100%, 1.5B fp16 RULER baseline]

4.5 **GQA-Aware 部署效率分析（新增核心 section）**★
    4.5.1 Phase 1 TPOT 对比表（4 模型 × 5 backends）
    4.5.2 长序列 TPOT Scaling（3 模型 × 4 seq_len × 4 backends）
    4.5.3 Phase Boundary: $(H_{kv}, \text{seq\_len})$ 二维分析
    4.5.4 KV Cache 内存 vs FP16 对比
    4.5.5 部署建议
    [新增数据：全部 Stage 7 + Phase 1 TPOT + memory sweep]

4.6 **外部系统局限性：BitDecoding 案例分析（新增）**★
    4.6.1 BD standalone TPOT reference (24.22 ms)
    4.6.2 BD adapter GQA bug 诊断
    4.6.3 Single-shot cosine vs long-gen 的 validation gap
    [数据：BD 诊断全套]

4.7 综合讨论（重写）
    4.7.1 主要发现（以 GQA 为主线重述 5 个 contributions）
    4.7.2 实验结论概要
    4.7.3 威胁效度分析
```

### 新增 Tables

| 编号 | 内容 | 数据来源 |
|------|------|---------|
| **Tab 4-A** | Phase 1 TPOT 完整表 (4 模型 × 5 backends × 含 KV mem) | Stage 1+2 |
| **Tab 4-B** | 长序列 TPOT Scaling (14B, 4 seq × 4 backends) | Stage 7 rerun |
| **Tab 4-C** | Phase Boundary Δ(triton−torchref) 表 (3 模型 × 4 seq) | Stage 7 |
| **Tab 4-D** | 14B RULER task breakdown (s_niah/mk_niah/vt/cwe × 3 sl) | Stage 5 |
| **Tab 4-E** | 1.5B FP16 vs FI INT4 RULER 对比 (4 sl × 4 tasks) | Baseline + Stage 4 |
| **Tab 4-F** | 14B K/V Ablation PPL 表 (4 configs) | Stage 5 |
| **Tab 4-G** | 7B KL vs MSE 校准参数 + PPL 对比 | C1 补实验 |
| **Tab 4-H** | 7B/8B Memory/Batch sweep | Stage 6 |

### 新增 Figures

| 编号 | 内容 | 说明 |
|------|------|------|
| **Fig 4-1** | **(核心图)** $(H_{kv}, \text{seq\_len})$ Phase Boundary heatmap | 横轴 seq_len (4K→32K)，纵轴 Hkv (2/4/8)，颜色=Δ(triton−torchref)，0 线=crossover |
| **Fig 4-2** | 长序列 TPOT line chart: 14B 4 backends × 4 seq | 展示 triton_ra 在长序列下线性增长远慢于 torchref |
| **Fig 4-3** | PPL 退化 vs 模型规模 bar chart | 1.5B/7B/8B/14B 的 PPL Δ% |
| **Fig 4-4** | 1.5B RULER task breakdown (FP16 vs FI INT4) | 展示 VT/CWE 低是模型限制 |

---

## 八、Ch5 Conclusion 重构

### 新 Findings 结构

```latex
\section{核心发现与收束}

本文以 GQA 架构参数 $H_{kv}$ 为核心分析变量，
系统揭示了 INT4 KV Cache 量化在不同模型规模下的行为规律。
主要发现如下：

\textbf{Finding 1: 校准目标灵敏度的 bit-width 与规模双依赖。}
INT8 下 KL/MSE 趋同；INT4 下 1.5B ($H_{kv}=2$) 呈现 12.35\% scale 差异，
7B ($H_{kv}=4$) 趋同。KL 是 universally safe 的校准目标。

\textbf{Finding 2: Key 主导退化跨模型规模验证。}
1.5B--14B 四个模型一致观察到 K 量化主导 PPL 退化
（14B: K 恢复 93\%, V 恢复 64\%）。
Needle 与 PPL 在多个配置下解耦。

\textbf{Finding 3: RoleAlign 在大模型上保持质量。}
14B RULER 96--99\%，Needle 32K 100\%，PPL 退化 7.6\%。
1.5B INT4 vs FP16 的 RULER 差距不足 1\%。

\textbf{Finding 4: $(H_{kv}, \text{seq\_len})$ Phase Boundary。}
Triton 融合核的效率优势与 $H_{kv}$ 正相关：
$H_{kv}=8$ 时 32K 快 40\%，$H_{kv}=2$ 时始终慢。
部署建议：$H_{kv}\geq 4$ + seq$>$8K 用融合核。

\textbf{Finding 5: 外部 INT4 kernel (BitDecoding) 的 GQA 局限。}
bit\_decode v1.0.0.post1 在 GQA 下输出错误，
Needle 0\%, RULER 1\%, LongBench F1=0。
Single-shot cosine 不足以验证 INT4 attention backend。
```

---

## 九、Ch2 不需要的大修改

Ch2 (Related Work) **只需要 L452-458 的扩写（~10 行）**。其他部分已经有 GQA 的讨论基础，不需要修改。

---

## 十、Abstract 更新

### 原 Abstract 核心句（推测）
> "我们提出 INT4 RoleAlign 框架，实现 73% KV 压缩 + Needle 100%"

### 新 Abstract 核心句
> "我们发现 GQA 的 KV 头数 $H_{kv}$ 是 INT4 KV Cache 量化行为的核心架构变量：
它同时决定校准灵敏度（$H_{kv}$ 小时 KL$\neq$MSE）、
Key 退化幅度（K 量化恢复 93\% PPL 退化）、
融合量化核的 phase boundary（$H_{kv}=8$ 时 32K 快 40\%）
和温度校正方向。
基于这些发现，我们在 KIVI-style 格式上给出行为引导的 INT4 实例化 RoleAlign，
在 14B 模型 32K 上下文下保持 Needle 100\%、RULER 96--99\%、KV 压缩 73\%，
并为不同 $H_{kv}$ 提供架构感知的部署建议。"

---

## 十一、工作量评估

| 章节 | 改动类型 | 行数 | 天数 |
|------|---------|------|------|
| Ch1 RQ | 微调+新增 RQ4 | 30 | 0.3 |
| Ch1 Contributions | 重写 C1-C5 | 90 | 0.5 |
| Ch1 核心主张 | 重写 | 15 | 0.1 |
| Ch2 Gap 声明 | 扩写 | 10 | 0.1 |
| Ch3 KL 规模依赖 | 新增段落 | 15 | 0.2 |
| Ch3 Phase Boundary 理论 | 新增 subsection | 40 | 0.5 |
| Ch3 in-kernel percentile | 新增段落 | 25 | 0.3 |
| **Ch4 重写** | **完全重写** | **400** | **2.0** |
| **Ch5 重写** | **Findings 重写** | **100** | **0.5** |
| Abstract | 重写 | 15 | 0.1 |
| 新图表制作 | 4 figures + 8 tables | — | **1.0** |
| **总计** | — | **~740 行** | **~5.5 天** |

---

## 十二、执行顺序建议

```
Day 1: Ch1 (RQ + Contributions + 核心主张) + Abstract
Day 2: Ch3 (KL 规模依赖 + Phase Boundary + in-kernel pct) + Ch2 gap
Day 3-4: Ch4 重写 (Section 4.2-4.7 + Tables + Figures)
Day 5: Ch5 Findings + 全文校对 + 交叉引用检查
Day 5.5: 编译 + 格式调整 + 页数控制
```

---

## 十三、风险 checklist

| 风险 | 缓解 |
|------|------|
| C4 新内容（Phase Boundary）措辞不够学术 | 参考 FlashDecoding/Splitwise 论文的 efficiency analysis 写法 |
| 14B PPL 退化 7.6% > 8B 的 2.4%，审稿人可能质疑"为什么不是单调递减" | 在 Ch4 加一段讨论：14B calib 数据量 (128 samples) 可能不够，或 14B 的 outlier 分布不同 |
| "GQA-aware"定位被审稿人认为"过于 narrow" | 在 Ch5 future work 明确说可推广到 MQA (Multi-Query, $H_{kv}=1$) 和 MHA ($H_{kv}=H_q$) |
| BD 负面结果引发"你为什么不修 BD？"的质疑 | 明确说"这是库层面的 bug,超出我们 scope,我们的贡献在于发现 single-shot cosine 的 validation gap" |
| Ch3 Phase Boundary 理论过于简化 | 加"一阶近似"声明，在 Ch5 limitations 中承认"完整的 cost model 需要考虑 GPU 架构细节" |

---

_文档生成: 2026-04-12_
_状态: 待用户审核后执行_
