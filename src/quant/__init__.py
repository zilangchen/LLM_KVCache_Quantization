"""
Quantization utilities for KV Cache.

Symmetric (INT8 / INT4):
- quantize_symmetric_int8 / dequantize_symmetric_int8
- quantize_symmetric_int8_with_scale  (static-scale path)
- quantize_symmetric_int4 / dequantize_symmetric_int4
- quantize_symmetric_int4_with_scale  (static-scale path)
- pack_int4 / unpack_int4             (bit-packing helpers)

Asymmetric (KIVI-style):
- quantize_asymmetric / dequantize_asymmetric          (generic, axis-based)
- quantize_asymmetric_per_channel / dequantize_asymmetric_per_channel  (K cache)
- quantize_asymmetric_per_token / dequantize_asymmetric_per_token      (V cache)
"""

from src.quant.int8_basic import (
    dequantize_symmetric_int8,
    quantize_symmetric_int8,
    quantize_symmetric_int8_with_scale,
)

from src.quant.int4_basic import (
    dequantize_symmetric_int4,
    pack_int4,
    quantize_symmetric_int4,
    quantize_symmetric_int4_with_scale,
    unpack_int4,
)

from src.quant.asymmetric_quant import (
    quantize_asymmetric,
    dequantize_asymmetric,
    quantize_asymmetric_per_channel,
    dequantize_asymmetric_per_channel,
    quantize_asymmetric_per_token,
    dequantize_asymmetric_per_token,
)

__all__ = [
    "quantize_symmetric_int8",
    "dequantize_symmetric_int8",
    "quantize_symmetric_int8_with_scale",
    "quantize_symmetric_int4",
    "dequantize_symmetric_int4",
    "quantize_symmetric_int4_with_scale",
    "pack_int4",
    "unpack_int4",
    "quantize_asymmetric",
    "dequantize_asymmetric",
    "quantize_asymmetric_per_channel",
    "dequantize_asymmetric_per_channel",
    "quantize_asymmetric_per_token",
    "dequantize_asymmetric_per_token",
]
