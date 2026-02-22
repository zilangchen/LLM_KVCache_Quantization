# 执行 Agent 指令：阶段 C - INT8-baseline KV Cache 量化

> **任务 ID**：`milestone-c`
> **任务类型**：Milestone C - INT8 量化基线实现
> **创建时间**：2026-01-21 15:26
> **状态**：待执行
> **预计时间**：3-4 小时

---

## 目标

实现 INT8-baseline KV cache 量化（naive 量化存储 + percentile 裁剪 + group_size=128），作为后续 ours 方案的对照基线。

---

## 前置条件

- ✅ 阶段 A 已完成（环境验证通过）
- ✅ 阶段 B 已完成（FP16 baseline 推理管线就绪）
- ✅ `src/engine/generate_loop.py` 已实现
- ✅ FP16 baseline：TPOT ~16ms, 吞吐 ~62 tok/s (H20 96GB)

---

## 执行步骤

### Step 1：创建 KV Cache Layout 文档

创建 `src/cache/README_cache_layout.md`：

```markdown
# KV Cache Layout 设计文档

## Shape 定义
- K: [batch, num_kv_heads, seq_len, head_dim]
- V: [batch, num_kv_heads, seq_len, head_dim]

## Qwen2.5-1.5B 参数
- num_layers: 28
- num_kv_heads: 2 (GQA)
- num_attention_heads: 12
- head_dim: 128
- hidden_size: 1536

## 增长策略
- Prefill: 一次性写入 prompt_len 个 token 的 KV
- Decode: 每步追加 1 个 token 的 KV
```

**验收**：文档清晰描述 shape 和增长策略

---

### Step 2：实现 FP16 KV Cache

创建 `src/cache/fp16_cache.py`：

```python
class FP16KVCache:
    """FP16 KV Cache 实现"""
    
    def __init__(self, num_layers: int, max_seq_len: int, ...):
        pass
    
    def append(self, layer_id: int, k: Tensor, v: Tensor):
        """追加 KV 到指定层"""
        pass
    
    def get_kv(self, layer_id: int) -> Tuple[Tensor, Tensor]:
        """获取指定层的 KV"""
        pass
    
    def get_seq_len(self) -> int:
        """当前缓存的序列长度"""
        pass
```

**验收**：
- append/get_kv 接口正确
- prefill 后 seq_len == prompt_len
- decode 每步 seq_len += 1

---

### Step 3：实现 INT8 基础量化器

创建 `src/quant/int8_basic.py`：

```python
def quantize_symmetric_int8(
    tensor: Tensor,
    percentile: float = 99.9,
    group_size: int = 128,
) -> Tuple[Tensor, Tensor]:
    """
    对称 INT8 量化
    
    Args:
        tensor: 输入张量
        percentile: 裁剪百分位数（用于动态范围计算）
        group_size: 分组大小（128 时退化为 per-head_dim）
    
    Returns:
        quantized: INT8 量化张量
        scale: 缩放因子
    """
    pass

def dequantize_symmetric_int8(
    quantized: Tensor,
    scale: Tensor,
) -> Tensor:
    """INT8 反量化"""
    pass
```

**验收**：
- 量化后值域在 [-127, 127]
- 反量化误差可控（相对误差 < 1%）

---

### Step 4：实现 INT8 KV Cache

创建 `src/cache/int8_cache.py`：

```python
class INT8KVCache:
    """INT8 KV Cache 实现（append 时量化，get 时反量化）"""
    
    def __init__(
        self,
        num_layers: int,
        max_seq_len: int,
        clip_percentile: float = 99.9,
        group_size: int = 128,
        ...
    ):
        pass
    
    def append(self, layer_id: int, k: Tensor, v: Tensor):
        """量化并追加 KV"""
        # 1. 量化 k, v
        # 2. 存储量化后的 qk, qv 和 scale
        pass
    
    def get_kv(self, layer_id: int) -> Tuple[Tensor, Tensor]:
        """反量化并返回 KV"""
        pass
```

**验收**：
- 存储为 INT8（显存下降 ~50%）
- 反量化后可正常用于 attention

---

### Step 5：更新 Generation Loop

修改 `src/engine/generate_loop.py`：

```python
def generate(
    model,
    tokenizer,
    prompt: str,
    max_new_tokens: int = 128,
    kv_mode: str = "fp16",  # 新增支持: "int8_baseline"
    clip_percentile: float = 99.9,
    group_size: int = 128,
) -> GenerationOutput:
    """
    根据 kv_mode 选择 FP16 或 INT8 KV cache
    """
```

**验收**：
- `kv_mode="fp16"` 使用 FP16KVCache
- `kv_mode="int8_baseline"` 使用 INT8KVCache
- 两种模式都能完整生成

---

### Step 6：更新 Profile 脚本

修改 `scripts/profile_baseline.py`：

```python
parser.add_argument("--kv_mode", type=str, default="fp16",
                    choices=["fp16", "int8_baseline"])
parser.add_argument("--clip_percentile", type=float, default=99.9)
parser.add_argument("--group_size", type=int, default=128)
```

**验收**：
```bash
# FP16 baseline
python3 scripts/profile_baseline.py --kv_mode fp16 --seq_len 512 --gen_len 64

# INT8 baseline
python3 scripts/profile_baseline.py --kv_mode int8_baseline --seq_len 512 --gen_len 64
```

输出 CSV 包含新字段：`kv_mode, quant_bits, clip_percentile, group_size`

---

### Step 7：验证显存收益

运行对比测试：

```bash
# 对比 FP16 vs INT8 显存
python3 scripts/profile_baseline.py --kv_mode fp16 --seq_len 4096 --gen_len 128
python3 scripts/profile_baseline.py --kv_mode int8_baseline --seq_len 4096 --gen_len 128
```

**验收**：
- INT8 模式显存下降 30%+ (KV cache 部分减半)
- 生成质量无明显退化（人工检查生成文本）

---

## 约束

1. **代码风格**：PEP8（79 字符行宽）
2. **异常处理**：shape 不匹配、量化溢出需有清晰错误提示
3. **服务器执行**：代码修改在本地完成后同步
4. **tmux 长任务**：测试使用 tmux 运行

---

## 预期产出物

| 文件 | 状态 | 说明 |
|------|------|------|
| `src/cache/README_cache_layout.md` | 新建 | KV cache 设计文档 |
| `src/cache/__init__.py` | 新建 | 模块初始化 |
| `src/cache/fp16_cache.py` | 新建 | FP16 KV cache 实现 |
| `src/cache/int8_cache.py` | 新建 | INT8 KV cache 实现 |
| `src/quant/__init__.py` | 新建 | 模块初始化 |
| `src/quant/int8_basic.py` | 新建 | INT8 量化/反量化 |
| `src/engine/generate_loop.py` | 修改 | 添加 kv_mode 支持 |
| `scripts/profile_baseline.py` | 修改 | 添加量化参数 |

---

## 服务器操作命令

**同步代码到服务器**：
```bash
rsync -avz --exclude='.git' --exclude='__pycache__' \
  /Users/chenzilang/Desktop/LLM_KVCache_Quantization/ \
  root@region-42.seetacloud.com:/root/LLM_KVCache_Quantization/ \
  -e 'ssh -p 31867'
```

**服务器运行测试**：
```bash
ssh -p 31867 root@region-42.seetacloud.com
tmux new -s milestone-c
source /etc/network_turbo
cd /root/LLM_KVCache_Quantization
python3 scripts/profile_baseline.py --kv_mode int8_baseline --seq_len 512 --gen_len 64
```

---

## 结果报告模板

```markdown
## 执行结果

**执行时间**：[YYYY-MM-DD HH:MM:SS]
**执行者**：[Agent ID]
**Git Commit**：[commit hash]

### 产出物
- src/cache/*.py：[已创建]
- src/quant/*.py：[已创建]
- src/engine/generate_loop.py：[已更新]

### 测试结果对比

| 模式 | seq_len | gen_len | TPOT (ms) | 吞吐 (tok/s) | 显存峰值 (MB) |
|------|---------|---------|-----------|--------------|---------------|
| FP16 | 4096 | 128 | [xx] | [xx] | [xx] |
| INT8 | 4096 | 128 | [xx] | [xx] | [xx] |

### 显存收益
- 下降比例：[xx]%

### 总结
- 整体状态：[通过/失败]
```

---

## 执行结果

（待执行 Agent 填写）
