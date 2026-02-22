---
description: Triton kernel 开发和调试工作流
---

# KV Cache 量化项目 - Triton Kernel 开发工作流

专门用于 Triton kernel 的开发、测试和优化。

---

## 执行前检查（强制）

1. 先读规范：`AGENTS.md` 与 `docs/AGENT_README.md`
2. 先查本仓库技能库：`ls .agent/skills`，并至少阅读：
   - `.agent/skills/remote-server/SKILL.md`（kernel 编译/跑测试需要 GPU）
   - `.agent/skills/long-running-task/SKILL.md`
3. 先做远端连接健康检查（GPU 可见），并在 tmux 内跑测试/benchmark：
```bash
ssh -p 31867 root@region-42.seetacloud.com "echo 'SSH OK' && nvidia-smi -L"
```

---

## Kernel 目标（Milestone G）

实现融合量化 decode attention (q_len=1)：
- 读取 INT8 K/V cache
- Group-wise 反量化
- 融合 per-head inv_tau
- Online softmax + 输出累加
- 支持 GQA 映射

---

## 开发流程

// turbo
### Step 1: Torch 参考实现
```python
# 先写 Torch 参考实现用于验证
def torch_ref_decode_attn(q, k_int8, v_int8, k_scale, v_scale, inv_tau):
    """
    Args:
        q: [batch, n_q_heads, 1, head_dim]
        k_int8: [batch, n_kv_heads, seq_len, head_dim] int8
        v_int8: [batch, n_kv_heads, seq_len, head_dim] int8
        k_scale: [n_kv_heads, n_groups] or per-head
        v_scale: [n_kv_heads, n_groups] or per-head
        inv_tau: [n_layers, n_q_heads]
    Returns:
        out: [batch, n_q_heads, 1, head_dim]
    """
    # Dequantize
    k_fp = k_int8.float() * k_scale
    v_fp = v_int8.float() * v_scale
    
    # Attention with temperature
    logits = torch.matmul(q, k_fp.transpose(-1, -2))
    logits = logits * inv_tau  # per-head temperature
    weights = F.softmax(logits, dim=-1)
    out = torch.matmul(weights, v_fp)
    return out
```

// turbo
### Step 2: Triton Kernel 骨架
```python
# src/kernels/triton_decode_attn_int8.py
import triton
import triton.language as tl

@triton.jit
def fused_decode_attn_int8_kernel(
    Q, K_int8, V_int8, K_scale, V_scale, inv_tau, Out,
    stride_qb, stride_qh, stride_qd,
    stride_kb, stride_kh, stride_ks, stride_kd,
    # ... more strides
    seq_len, head_dim, n_groups,
    BLOCK_SEQ: tl.constexpr, BLOCK_D: tl.constexpr,
):
    # 实现 online softmax + fused dequant
    pass
```

// turbo
### Step 3: 数值一致性测试
```python
# tests/test_triton_kernel.py
def test_fused_decode_attn_correctness():
    # 固定 seed
    torch.manual_seed(1234)
    
    # 准备输入
    q = torch.randn(...)
    k_int8 = torch.randint(-128, 127, ..., dtype=torch.int8)
    v_int8 = torch.randint(-128, 127, ..., dtype=torch.int8)
    
    # Torch 参考
    out_ref = torch_ref_decode_attn(...)
    
    # Triton 实现
    out_triton = triton_decode_attn(...)
    
    # 误差检查
    assert torch.allclose(out_ref, out_triton, atol=1e-3, rtol=1e-3)
```

// turbo
### Step 4: 性能测试
```python
# 延迟对比
def bench_decode_attn():
    # Baseline: dequant + torch SDPA
    # Ours: fused Triton kernel
    
    for seq_len in [1024, 4096, 16384, 32768]:
        t_baseline = benchmark(baseline_fn, ...)
        t_ours = benchmark(triton_fn, ...)
        speedup = t_baseline / t_ours
        print(f"seq_len={seq_len}: {speedup:.2f}x")
```

// turbo
### Step 5: 集成到推理路径
```python
# 在 decode 阶段强制使用 Triton kernel
# src/engine/generate_loop.py

if kv_mode == "int8_ours" and q_len == 1:
    attn_out = triton_decode_attn_int8(...)
else:
    attn_out = torch_attention(...)
```

// turbo
### Step 6: 端到端验证
```bash
# 运行完整推理
python scripts/smoke_test.py --kv_mode int8_ours

# 验证输出质量
python scripts/eval_ppl.py --kv_mode int8_ours
python scripts/eval_needle.py --kv_mode int8_ours
```

---

## 关键检查点

| 检查项 | 验收标准 |
|--------|----------|
| 数值一致性 | atol=1e-3, rtol=1e-3 |
| 性能 | 不退化，最好有提升 |
| GQA 支持 | 正确映射 q_head → kv_head |
| 真实路径 | decode 时被实际调用 |

---

## 常见问题

### Triton 编译错误
```bash
# 检查 Triton 版本
pip show triton

# 清理缓存
rm -rf ~/.triton/cache
```

### 数值不一致
```python
# 检查 dtype 是否一致
# 检查 scale 计算是否正确
# 检查 group 边界处理
```

### 性能不理想
```python
# 调整 BLOCK_SEQ, BLOCK_D
# 检查内存访问模式
# 使用 triton.autotune
```
