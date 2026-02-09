# KV Cache Layout 设计文档

> 本文档描述本项目 KV Cache 的内存布局、参数和增长策略。

---

## 1. Shape 定义

```
K: [batch, num_kv_heads, seq_len, head_dim]
V: [batch, num_kv_heads, seq_len, head_dim]
```

说明：
- **batch**：批次大小（当前固定为 1）
- **num_kv_heads**：KV 头数量（GQA 模式下小于 attention heads）
- **seq_len**：当前缓存的序列长度（动态增长）
- **head_dim**：每个头的维度

---

## 2. Qwen2.5-1.5B 参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `num_layers` | 28 | Transformer 层数 |
| `num_kv_heads` | 2 | KV 头数量 (GQA) |
| `num_attention_heads` | 12 | Query 头数量 |
| `head_dim` | 128 | 每个头的维度 (1536 / 12) |
| `hidden_size` | 1536 | 隐藏层大小 |
| `max_position_embeddings` | 32768 | 最大序列长度 |

---

## 3. 增长策略

### 3.1 Prefill 阶段

一次性写入 `prompt_len` 个 token 的 KV：

```python
# 输入 prompt 长度为 L
# 输出 K, V shape: [1, num_kv_heads, L, head_dim]
cache.append(layer_id, k, v)  # k, v shape: [1, 2, L, 128]
assert cache.get_seq_len() == L
```

### 3.2 Decode 阶段

每步追加 1 个 token 的 KV：

```python
# 每步生成 1 个 token
# 当前 cache seq_len = prev_len
cache.append(layer_id, k, v)  # k, v shape: [1, 2, 1, 128]
assert cache.get_seq_len() == prev_len + 1
```

---

## 4. 内存估算

### FP16 模式

```
单层 KV 大小 = 2 (K+V) × num_kv_heads × seq_len × head_dim × 2 bytes
           = 2 × 2 × seq_len × 128 × 2
           = 1024 × seq_len bytes
           
总 KV 大小 = 28 layers × 1024 × seq_len bytes
          = 28 KB × seq_len
          
示例：seq_len = 32768
总 KV 大小 = 28 × 1024 × 32768 / (1024^2) ≈ 896 MB
```

### INT8 模式

```
单层 KV 大小 = 2 × 2 × seq_len × 128 × 1 byte + scale 开销
           ≈ 512 × seq_len bytes (不含 scale)
           
总 KV 大小 ≈ 448 MB (seq_len = 32768)
显存下降 ≈ 50%
```

---

## 5. 接口约定

```python
class KVCacheBase(ABC):
    """KV Cache 抽象基类"""
    
    @abstractmethod
    def append(self, layer_id: int, k: Tensor, v: Tensor) -> None:
        """追加 KV 到指定层"""
        pass
    
    @abstractmethod
    def get_kv(self, layer_id: int) -> Tuple[Tensor, Tensor]:
        """获取指定层的 KV"""
        pass
    
    @abstractmethod
    def get_seq_len(self) -> int:
        """当前缓存的序列长度"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""
        pass
```

---

## 6. 量化说明

### INT8 对称量化

```
quantized = round(tensor / scale * 127)
scale = max(abs(tensor)) / 127  # 对称量化

反量化：
tensor = quantized * scale / 127
```

### Group-wise 量化（group_size=128）

- 当 group_size=128 且 head_dim=128 时，退化为 per-head_dim 量化
- 每个 head 有独立的 scale

---

## 7. 文件结构

```
src/cache/
├── README_cache_layout.md  # 本文档
├── __init__.py             # 模块导出
├── fp16_cache.py           # FP16 KV Cache 实现
└── int8_cache.py           # INT8 KV Cache 实现
```
