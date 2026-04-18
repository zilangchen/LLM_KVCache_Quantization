# 答辩 Q&A 卡片 v6（Phase 1 官方 LongBench 纳入后）

**目标**: 在 10 分钟 Q&A 环节里，每张卡片限 30-45 秒复述。
**数据状态**: Phase 1 编号 2 刚跑完，具体数字以 `results/phase1_summary.csv` 为准。

---

## Q1 [基础必答]: 你这篇论文解决什么问题？

**一句话答案**: 大模型长上下文推理时 KV Cache 显存爆炸，INT4 压缩能省 75% 显存但在 Needle 上从 100% 掉到 0%；本文提出以 attention-KL 为诊断透镜 + 校准目标，在官方 LongBench 三任务上系统验证并给出落地方案。

---

## Q2 [归属必答]: Needle 从 0%→100% 是不是 KIVI 的功劳？

**一句话答案**: 是。这是 KIVI 的非对称格式（per-channel K + per-token V）本身的贡献。
**本文的独立贡献**（3 句话）:
1. 首次用 attention-KL 为 KIVI 格式提供机制性解释（从经验 → 诊断推论）
2. 用可审计的离线 KL 搜索替代运行时 absmax/min（部署可复现）
3. [**场景 B/C 若 allocator 成立**] 把 lens 升级为 bit 分配 oracle

---

## Q3 [硬问题]: 官方 LongBench 上的结果对 INT4 有多严重的打击？

**答题要点**（待数据填入）:
- 官方 LongBench NarrativeQA FP16 F1 = **[填 phase1_summary 数据]**
- INT8-Canonical 相对 FP16 退化 = **[填]%**
- KIVI-style 相对 FP16 退化 = **[填]%**
- INT4-RoleAlign 相对 FP16 退化 = **[填]%**
- **坦率结论**: INT4 确实有 X% 退化（比 synthetic 更严格），但 KV 压缩 73% 是硬收益

---

## Q4 [统计]: 你在 Phase 1 只用了 n=50 样本，够不够？

**答题要点**:
- 目的是**定位方向**，不是 SOTA 数字
- 3 任务 × 4 模式 × 50 样本 = 600 总数据点
- 若 Phase 1 结果"值得继续"，后续 allocator 阶段会扩到 n=100+
- 对比工业论文：LongBench 官方典型 n=100-500，本文 n=50 是 Phase 1 筛查级而非最终声明

---

## Q5 [过度诚实的反问]: 你说自己在 PPL 上不如 KIVI，那为什么还要做这篇论文？

**答题要点**:
- 方法论贡献 ≠ 数字 SOTA
- 本文的**实际价值**是"诊断→决策"方法论（attention-KL lens）
- KIVI 的格式是经验观察，我给出**可复现的机制性解释**
- 为合规部署场景提供可审计的离线校准接口
- [场景 B/C] 同时证明了 lens 可以驱动 adaptive allocation

---

## Q6 [实验设计]: 你为什么只测 1.5B 和 7B？（编号 4 完成后）

**答题要点**:
- Phase 1 的目的是"验证评测底座"，不是"全模型扫描"
- 1.5B 提供最低成本 × 最多消融的批量验证点
- 7B 提供跨规模复核（同 Qwen 族，H_kv 从 2 → 4）
- 更大模型（14B / 70B）作为 future work 或外部效度锚点

---

## Q7 [部署问题]: 你的方法能不能直接上 vLLM / TensorRT-LLM？

**答题要点**（诚实）:
- 当前实现基于 Transformers 自定义 generation loop
- **不能**直接 plug-into vLLM 的 PagedAttention（kernel 不兼容）
- 但本文的校准产物 JSON 是**通用接口**，可被未来 vLLM INT4 集成复用
- 属于"科研级 PoC"，工业级落地需 3-6 月工程

---

## Q8 [致命点]: chunk_size=1 流式推理下你崩了，这是生死问题吗？

**答题要点**:
- cs=1 下 per-channel K scale 只基于首个 token 建立，后续值 100% 溢出 → PPL > 10⁴
- **这是非对称 per-channel K 格式的共同边界**（KIVI 原论文也会，除非启用 Residual Buffer）
- 本文主线使用 cs=128（与大多数 serving workload 一致）
- 流式 cs=1 的真正解决方案是 KIVI 原论文的 FP16 Residual Buffer（R=128），留作后续工作
- **不是生死问题**: 大多数 serving 场景（chat / batch inference）都可 ≥ cs=128

---

## Q9 [方法论]: attention-KL 相对 MSE 真的好吗？

**答题要点**（Phase 1 后更新）:
- INT8 下两者在鲁棒选择协议下产生逐位一致校准产物（共同约束所致）
- INT4 下 1.5B（$H_{kv}=2$）两者分化，7B（$H_{kv}=4$）再次收敛
- **这不是单调"KL 总是更优"**，而是 bit-width × 规模依赖
- Phase 1 官方 LongBench 验证这个结论在 real-world benchmark 上也成立

---

## Q10 [陷阱题]: 如果我只用 KIVI-style + 运行时 absmax，我能达到你的效果吗？

**答题要点**（最难答）:
- 数字上：几乎一样（PPL 持平或略劣 0.05-0.15）
- **但**:
  - KIVI 的运行时 absmax 每次 prefill 都重新算，不可固化
  - 合规场景（金融、医疗）需要量化参数可审计
  - 本文的离线 KL 搜索提供 JSON 化校准产物
- [场景 B/C] 如果 allocator 成立：**本文额外提供"分配给哪些层多少 bit"的能力**，这是 KIVI 做不到的

---

## 编号 5 闸门不通过时的答辩 fallback

若 Phase 1 判"站不住"（跳编号 11），论文重定位为：

**"Behavior-Aligned Diagnostics Meet Reality: Why INT4 KV Cache Quantization Fails on Official Long-Context Tasks"**

- 贡献一：attention-KL 作为诊断透镜（保留）
- **新贡献二**: 首次在官方 LongBench 上系统报告 INT4 方法在真实长上下文任务上的系统性失效
- **新贡献三**: 为领域提供 "synthetic-vs-official" 失效模式的实证基线

**实证论文也能发表**（arXiv / workshop），避免 "0 产出" 的最坏情况。

---

## 使用说明

- Phase 1 数据到位后，用 `results/phase1_summary.csv` 填 Q3 的占位
- 若 Phase 2 allocator 成立，改写 Q2/Q5/Q10 的"本文独立贡献"部分
- 答辩前 48 小时：把所有 [TBD] 替换为真实数字
