"""
KV Cache implementations for LLM inference.

Available caches:
- FP16KVCache: Standard FP16 KV cache
- INT8KVCache: INT8 quantized KV cache with group-wise scaling
- INT4KVCache: INT4 quantized KV cache (more aggressive compression)
- KIVIStyleKVCache: KIVI-style asymmetric quantization
- MixedKVCache: Configurable K/V precision hybrid
- RoleAwareAsymKVCache: Role-aware asymmetric (BA-guided)
- RoleAwareAllocatorKVCache: Role-aware allocator-enabled asymmetric backend

All cache classes conform to KVCacheProtocol (KVC-078).
"""

from src.cache.fp16_cache import FP16KVCache
from src.cache.int8_cache import INT8KVCache
from src.cache.int4_cache import INT4KVCache
from src.cache.kivi_style_cache import KIVIStyleKVCache
from src.cache.mixed_kv_cache import MixedKVCache
from src.cache.role_aware_asym_cache import RoleAwareAsymKVCache
from src.cache.role_aware_allocator_cache import RoleAwareAllocatorKVCache
from src.cache.protocol import KVCacheProtocol

__all__ = [
    "KVCacheProtocol",
    "FP16KVCache",
    "INT8KVCache",
    "INT4KVCache",
    "KIVIStyleKVCache",
    "MixedKVCache",
    "RoleAwareAsymKVCache",
    "RoleAwareAllocatorKVCache",
]
