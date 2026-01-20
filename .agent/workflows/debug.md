---
description: 排查报错和调试问题的工作流
---

# KV Cache 量化项目 - 调试工作流

专门用于排查和修复项目中的报错。

---

## 调试输入模板

用户应提供：
```
运行命令：<粘贴命令>
报错信息：<粘贴完整 traceback>
环境信息：<CUDA/torch/GPU 版本>
```

---

## 调试流程

// turbo
### Step 1: 错误分类
```
常见错误类型：
- OOM（显存不足）
- CUDA 错误（算子不兼容/设备问题）
- Shape 不匹配（tensor 维度错误）
- 量化误差（数值精度问题）
- 模型下载失败（网络/缓存问题）
- 导入错误（依赖缺失）
```

// turbo
### Step 2: 环境检查
```bash
# GPU 状态
nvidia-smi

# CUDA 版本
nvcc --version

# PyTorch 版本
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"

# 显存使用
python -c "import torch; print(f'显存: {torch.cuda.memory_allocated()/1e9:.2f}GB')"
```

// turbo
### Step 3: 根因分析
```
1. 定位出错代码行（traceback 分析）
2. 确认变量状态和预期值
3. 检查上游数据流
4. 归纳根因（1-2 句话）
```

// turbo
### Step 4: 最小修复
```
原则：
- 最小改动优先
- 不破坏现有功能
- 添加必要的异常处理
- 保持代码风格一致
```

// turbo
### Step 5: 验证修复
```bash
# 重新运行原命令
<原始命令>

# 确认问题已解决
# 如果仍失败，回到 Step 3
```

// turbo
### Step 6: 记录修复
```
更新 development_record.md：
- 问题描述
- 根因分析
- 修复方案
- 防止再次发生的措施
```

---

## 常见问题快速修复

### OOM 显存不足
```python
# 减少 batch_size
# 减小 seq_len
# 启用 gradient_checkpointing
# torch.cuda.empty_cache()
```

### CUDA 错误
```bash
# 检查 CUDA 版本兼容性
# 重启 kernel/进程
# 更新 GPU 驱动
```

### Shape 不匹配
```python
# 打印 tensor.shape 定位问题
# 检查 reshape/view/transpose 操作
# 确认 GQA 头映射正确
```

### 量化误差过大
```python
# 检查 scale 计算
# 验证 clipping percentile
# 对比 FP16 参考输出
```
