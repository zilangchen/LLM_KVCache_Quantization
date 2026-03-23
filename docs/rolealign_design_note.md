# RoleAlign Design Note — ours_asym vs kivi_style 差异定义

**日期**: 2026-03-24
**前置依赖**: kivi_gap_audit.md (Gap 审计完成)
**目的**: 在写代码前明确定义 ours_asym 与 kivi_style 在设计上到底哪里不同，
防止后续实验叙事塌掉。

---

## 核心问题

> ours_asym 和 kivi_style 都使用 per-channel K + per-token V 非对称量化，
> 两者在设计上到底有什么本质不同？

答案：**量化格式相同，但参数确定范式、设计动机、框架归属和求解机制完全不同。**

---

## 四项明确差异

### 差异 1：校准范式

| 维度 | kivi_style | ours_asym |
|------|-----------|-----------|
| **参数确定方式** | 在线动态计算（运行时 absmax/min） | 离线 BA pipeline（校准集 + KL 搜索） |
| **K scale** | prefill 时从数据 absmax/min 直接计算 | 离线从校准集搜索最优 percentile → 静态 scale |
| **V scale** | append 时逐 token absmax/min 动态计算 | append 时逐 token 动态计算（但 percentile 参数由离线搜索确定）|
| **inv_tau** | 无 | 离线 KL 搜索 + Q 预缩放 |
| **校准数据** | 不需要 | 需要（WikiText-103 子集） |

**核心区别**: kivi_style 的量化参数完全由运行时数据的统计量（max, min）决定，
是无校准（calibration-free）方案；
ours_asym 的量化参数由离线 KL 优化确定（k_percentile、v_percentile、inv_tau），
属于校准引导（calibration-guided）方案。

### 差异 2：设计动机

| 维度 | kivi_style | ours_asym |
|------|-----------|-----------|
| **动机来源** | K/V 统计分布的经验观察 | K/V sensitivity 消融实验的定量结论（§4.7） |
| **推理过程** | "K 通道间分布差异大 → per-channel 量化" <br> "V token 间分布差异大 → per-token 量化" | "对称 INT4 在 K 上崩溃（Needle→0%）" <br> "K/V 消融证明 K>V 敏感性" <br> "→ K 需要更精细的量化轴（per-channel）" <br> "→ V 容忍 per-token 动态" |
| **设计方向** | 从统计观察到量化轴选择（自底向上） | 从任务失败到诊断到量化升级（自顶向下） |

**核心区别**: kivi_style 的非对称设计源于 K/V 统计特性的直觉观察；
ours_asym 的非对称设计源于行为对齐框架的诊断发现
——先通过 KL 分析发现对称量化在 INT4 下的行为失效模式，
再通过受控消融定位 K 是主导因素，
最后吸收 KIVI 的非对称轴策略作为解决方案。

### 差异 3：框架归属

| 维度 | kivi_style | ours_asym |
|------|-----------|-----------|
| **独立方法** | 是——KIVI 是独立提出的完整方案 | 否——是 ours family 的 INT4 升级 |
| **共享组件** | 无（独立于 ours 框架） | BA calibration pipeline、inv_tau 注入接口、统一实验体系 |
| **方法命名** | KIVI (Liu et al., 2024) | INT4-RoleAlign（ours_asym）/ INT4-RoleAlign+（ours_asym_ba）|
| **论文定位** | 强 baseline / SOTA 对照 | 本文方法的 INT4 扩展 |

**核心区别**: ours_asym 不是 "KIVI + BA"，而是 "ours 方法吸收 KIVI 的非对称轴设计思想，
升级为 role-aware asymmetric family"。共享 ours 的整个校准 pipeline。

### 差异 4：参数求解机制（硬差异）

| 参数 | kivi_style | ours_asym / ours_asym_ba |
|------|-----------|--------------------------|
| **k_percentile** | 100.0（默认，无裁剪） | 离线 KL 搜索确定（role-aware）|
| **v_percentile** | 100.0（默认，无裁剪） | 离线 V-path 搜索确定（attention-weighted MSE）|
| **inv_tau** | 无 | 离线逐头 KL 搜索（共享 ours 的 inv_tau pipeline）|
| **K scale** | `absmax/min(K_prefill)` 即时计算 | `absmax/min(K_prefill)` BUT 使用搜索得到的 k_percentile 裁剪 |
| **V scale** | `absmax/min(V_token)` 即时计算 | `absmax/min(V_token)` BUT 使用搜索得到的 v_percentile 裁剪 |
| **搜索算法** | 无（启发式） | 统一 behavior-aligned pipeline：<br>1) Scale 搜索（KL grid search）<br>2) inv_tau 搜索（per-head KL）<br>3) V-path percentile 搜索（attention-weighted MSE）|

**核心区别**: kivi_style 的所有量化参数由运行时启发式机制决定（absmax/min），
没有离线搜索过程；
ours_asym 通过统一的 behavior-aligned 离线搜索范式确定 role-aware 超参数
（k_percentile、v_percentile、inv_tau），
参数注入、评估、搜索和结果聚合统一纳入 ours pipeline。

---

## 方法命名映射

| 代码名 (kv_mode) | 论文展示名 | 含义 |
|------------------|-----------|------|
| `int4_ours` | INT4-BA | 对称 per-group + BA（现有方法） |
| `int4_ours_asym` | INT4-RoleAlign | 非对称 per-channel K / per-token V，BA 校准的 percentile，**无** inv_tau |
| `int4_ours_asym_ba` | INT4-RoleAlign+ | 非对称 + BA 校准的 percentile + inv_tau（完整新主方法） |
| `kivi_style` (INT4) | KIVI-style INT4 | 非对称，无校准，强 baseline |
| `int4_kivi_aligned` | KIVI+τ⁻¹ | KIVI 骨架 + 仅 inv_tau（过渡方案，非主线） |

---

## 实现策略

### 优先薄封装

```
RoleAwareAsymKVCache(KIVIStyleKVCache):
    - 继承: append(), get_kv(), get_seq_len(), clear(), release()
    - Override: __init__() 接受 BA 校准参数
    - 新增: 无（利用父类已有的 k_percentile/v_percentile/inv_tau 接口）
```

**关键洞察**: `KIVIStyleKVCache` 已经接受 `k_percentile`、`v_percentile`、
`inv_tau`、`use_attn_temperature` 参数（L54-65）！
ours_asym 的核心区别不在缓存实现，而在**这些参数的求解方式**。

因此实现策略是：
1. `RoleAwareAsymKVCache` 仅是一个薄 subclass，标记 decode_attn_impl 和框架归属
2. 核心差异在 `calibrate_behavior.py` 的 `--role_aware_axes` 模式
3. 路由在 `generate_loop.py` 中注册新 kv_mode

### 校准扩展

```python
# calibrate_behavior.py --role_aware_axes 模式
# 在 per-channel K + per-token V 轴策略下：
# 1. 搜索 k_percentile（KL grid search，与现有 Key scale 搜索共享代码）
# 2. 搜索 v_percentile（attention-weighted V 搜索，复用 calibrate_v_path_percentile）
# 3. 搜索 inv_tau（per-head KL 优化，与现有 inv_tau 搜索共享代码）
# 输出: role_aware_calib_*.json
```

---

## 论文叙事结构

```
ch4 §4.X "Role-Aware Asymmetric Quantization"

4.X.1 动机：对称 INT4 的边界（已有数据 → int4_ours 失败）
4.X.2 设计：吸收 KIVI 非对称轴 + BA 校准
    - 表：ours_asym vs kivi_style 四维差异对照表
4.X.3 实验：ours_asym → ours_asym_ba → vs kivi_style
    - Gate 驱动，逐层递进
4.X.4 讨论：BA 在非对称 family 上的增益分析
```
