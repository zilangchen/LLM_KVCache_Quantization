# L2 Spec: K/V Asymmetric Allocator

> 角色：implementation spec  
> 对应高层计划：`docs/l2_kv_asymmetric_allocator_plan.md`

---

## 1. 目标

把当前项目已有的：

- `K > V` 敏感性诊断
- `(k_bits, v_bits)` 路由能力
- MixedKV 执行路径

推进成一个**显式的 role-aware allocator MVP**。

这里的 MVP 目标不是学习复杂控制器，而是：

> 在保持 `layer-wise` 粒度不变的前提下，让每层的 `K` 与 `V` 获得可分离的预算决策。

---

## 2. MVP 范围

### 2.1 本轮只做什么

1. `layer-wise` 粒度
2. 显式 `(k_bits, v_bits)` policy
3. 独立的 `K-score / V-score`
4. 少量离散 bit pair：
   - `(8,8)`
   - `(8,4)`
   - `(4,8)`
   - `(4,4)`

### 2.2 本轮不做什么

1. 不做 head-wise
2. 不做 learned allocator
3. 不做 token-region allocation
4. 不改 kernel 基本接口

---

## 3. 设计对象

### 3.1 输入

来自现有 calibration / profile 的 layer 级信息：

- 当前 layer sensitivity
- K/V 非对称性先验
- 预算上限（总 bit budget / protected layer count）

### 3.2 输出

一个 role-aware policy：

```json
{
  "policy_type": "kv_asymmetric_layerwise",
  "layers": [
    {"layer": 0, "k_bits": 8, "v_bits": 4},
    {"layer": 1, "k_bits": 4, "v_bits": 4}
  ]
}
```

实现上允许继续复用当前 `(k_bits, v_bits)` 消费路径；  
若需要，可在 policy metadata 中附加：

- `k_score`
- `v_score`
- `tier`

---

## 4. 决策逻辑（MVP）

### 4.1 推荐的最小逻辑

先不要追求复杂学习器，MVP 用规则式两阶段决策：

1. 先决定层是否属于：
   - high importance
   - medium importance
   - low importance
2. 再依据 `K > V` 先验与 role score 决定该层使用：
   - `(8,8)`
   - `(8,4)`
   - `(4,8)`
   - `(4,4)`

### 4.2 默认偏置

在无强反证前，默认偏置应为：

- 高重要层优先考虑 `K` 保护
- `V` 的升级应更保守

也就是说，MVP 的默认世界观是：

> role-aware allocator 主要先回答“哪些层的 `K` 值得升 bit”，再回答“哪些层的 `V` 也需要升 bit”。

---

## 5. 实现接口建议

### 5.1 主要对接点

- `scripts/adaptive/behavior_aligned_allocator.py`
- `src/engine/generate_loop.py`
- `src/cache/mixed_kv_cache.py`

### 5.2 推荐拆分

1. `score_kv_roles(...)`
   - 输出每层 `k_score / v_score`
2. `assign_kv_bit_pairs(...)`
   - 按预算将层分配到离散 bit pair
3. `export_kv_asymmetric_policy(...)`
   - 输出标准 policy JSON

---

## 6. 最小实验矩阵

### 6.1 优先模型

1. `1.5B`
2. `7B`
3. `8B`

### 6.2 优先任务

先只跑 core tasks：

- `narrativeqa`
- `hotpotqa`
- `gov_report`

### 6.3 对照组

1. `uniform_int4_k4v4`
2. 当前 `layer-wise` allocator
3. `auto-k` 强配置
4. role-aware asymmetric allocator

---

## 7. 成功判据

MVP 只要满足下面其中两条，就算值得继续：

1. 在至少一个模型上，role-aware 优于当前 `layer-wise` allocator
2. 在相近预算下，role-aware 的 task-level 解释更清楚
3. 能明确回答哪些层更适合 `K-only` 升级

---

## 8. 输出物

应至少产出：

1. 一个可运行的 role-aware policy schema
2. 一组最小结果表
3. 一段回答“它比当前 layer-wise 多带来了什么”的结论
