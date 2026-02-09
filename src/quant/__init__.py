"""
Quantization utilities for KV Cache.

Available functions:
- quantize_symmetric_int8: Symmetric INT8 quantization with percentile clipping
- dequantize_symmetric_int8: Dequantize INT8 back to FP16/FP32
- quantize_symmetric_int4: Symmetric INT4 quantization (more aggressive)
- dequantize_symmetric_int4: Dequantize INT4 back to FP16/FP32
"""

from src.quant.int8_basic import (
    dequantize_symmetric_int8,
    quantize_symmetric_int8,
    quantize_symmetric_int8_with_scale,
)

from src.quant.int4_basic import (
    dequantize_symmetric_int4,
    quantize_symmetric_int4,
)

__all__ = [
    "quantize_symmetric_int8", 
    "dequantize_symmetric_int8",
    "quantize_symmetric_int8_with_scale",
    "quantize_symmetric_int4",
    "dequantize_symmetric_int4",
]
