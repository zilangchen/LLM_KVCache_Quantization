## tests/
这里放最小但关键的测试（先把正确性锁住，再做性能优化）：
- quant/dequant 数值误差上界与 dtype/shape 不变性
- KV cache append/get 的 shape 与长度不变量
- Triton kernel 与 torch 参考实现的一致性（容差内）

