#!/usr/bin/env python3
"""
Mixed KV Cache: configurable K/V precision for hybrid quantization and ablations.

Default mode (k_bits=8, v_bits=4):
  K @ INT8 symmetric per-group, V @ INT4 asymmetric per-token.
  ~37.5% of FP16 memory (K@50% + V@25%).

Ablation modes:
  k_bits=8, v_bits=16  → K-only quantization (V stays FP16)
  k_bits=16, v_bits=4  → V-only quantization (K stays FP16)
  k_bits=4, v_bits=8   → Counterfactual (K@INT4, V@INT8)

When bits=16, the corresponding cache stores raw FP16 tensors without quantization.

Interface is compatible with KIVIStyleKVCache and INT8KVCache:
append(), get_kv(), get_seq_len(), clear(), release(), get_memory_mb().
"""

import warnings
from typing import Dict, List, Optional, Tuple

import torch
from torch import Tensor

from src.quant.int8_basic import quantize_symmetric_int8, dequantize_symmetric_int8
from src.quant.asymmetric_quant import (
    dequantize_asymmetric_per_token,
    quantize_asymmetric_per_token,
)

_SUPPORTED_BITS = {4, 8, 16}


class MixedKVCache:
    """
    Mixed-precision KV Cache with configurable K/V bit-widths.

    Args:
        k_bits: Bit-width for K cache (4, 8, or 16). Default 8.
            16 = FP16 passthrough (no quantization).
            8  = INT8 symmetric per-group.
            4  = INT4 asymmetric per-token.
        v_bits: Bit-width for V cache (4, 8, or 16). Default 4.
            16 = FP16 passthrough (no quantization).
            8  = INT8 symmetric per-group.
            4  = INT4 asymmetric per-token.
    """

    def __init__(
        self,
        num_layers: int,
        device: str = "cuda",
        dtype: torch.dtype = torch.float16,
        max_seq_len: Optional[int] = None,
        k_group_size: int = 128,
        v_group_size: Optional[int] = None,
        k_clip_percentile: float = 99.9,
        v_percentile: float = 100.0,
        k_bits: int = 8,
        v_bits: int = 4,
        per_layer_bits: Optional[List[Tuple[int, int]]] = None,
    ):
        if num_layers <= 0:
            raise ValueError(f"num_layers must be > 0, got {num_layers}")
        if k_bits not in _SUPPORTED_BITS:
            raise ValueError(f"k_bits must be one of {_SUPPORTED_BITS}, got {k_bits}")
        if v_bits not in _SUPPORTED_BITS:
            raise ValueError(f"v_bits must be one of {_SUPPORTED_BITS}, got {v_bits}")

        # Phase 2 编号 6: per-layer bit allocation for behavior-aligned allocator.
        # When None, behaves exactly as before (backward compat for existing
        # int4_mixed_kv callers like eval_ppl / run_experiments).
        # When provided, overrides (k_bits, v_bits) per layer.
        if per_layer_bits is not None:
            if len(per_layer_bits) != num_layers:
                raise ValueError(
                    f"per_layer_bits length {len(per_layer_bits)} must equal "
                    f"num_layers {num_layers}"
                )
            for i, entry in enumerate(per_layer_bits):
                if (not isinstance(entry, (tuple, list))) or len(entry) != 2:
                    raise ValueError(
                        f"per_layer_bits[{i}] must be a 2-tuple (k_bits, v_bits), got {entry!r}"
                    )
                kb, vb = entry
                if kb not in _SUPPORTED_BITS or vb not in _SUPPORTED_BITS:
                    raise ValueError(
                        f"per_layer_bits[{i}]=({kb},{vb}) contains unsupported bits; "
                        f"allowed values: {_SUPPORTED_BITS}"
                    )
            # Normalize to list of tuples for consistent indexing.
            self._per_layer_bits: Optional[List[Tuple[int, int]]] = [
                (int(kb), int(vb)) for (kb, vb) in per_layer_bits
            ]
        else:
            self._per_layer_bits = None

        self.num_layers = num_layers
        self.device = device
        self.dtype = dtype
        self.max_seq_len = int(max_seq_len) if max_seq_len is not None else None
        self.k_group_size = k_group_size
        # KVC-082: Independent V group size. Defaults to k_group_size for
        # backward compatibility, but allows independent tuning (e.g. K@g128, V@g64).
        self.v_group_size = v_group_size if v_group_size is not None else k_group_size
        self.k_clip_percentile = k_clip_percentile
        self.v_percentile = v_percentile
        self.k_bits = k_bits
        self.v_bits = v_bits

        # Interface compatibility
        self.decode_attn_impl = "torch_ref"
        self.inv_tau = None
        self.use_attn_temperature = False

        # K cache storage
        self._k_cache: List[Optional[Tensor]] = [None] * num_layers
        self._k_scale: List[Optional[Tensor]] = [None] * num_layers
        self._k_zp: List[Optional[Tensor]] = [None] * num_layers  # only for k_bits=4

        # V cache storage
        self._v_cache: List[Optional[Tensor]] = [None] * num_layers
        self._v_scale: List[Optional[Tensor]] = [None] * num_layers
        self._v_zp: List[Optional[Tensor]] = [None] * num_layers  # only for asymmetric (4-bit)

        self._layer_seq_lens: List[int] = [0] * num_layers
        self._seq_len: int = 0

        # Decode stats (compatible interface)
        self.decode_stats: Dict[str, object] = {
            "fused_decode_calls": 0, "triton_kernel_calls": 0,
            "torch_ref_calls": 0, "layer_hits": {}, "triton_layer_hits": {},
        }

    # ------------------------------------------------------------------
    # Internal quantize/dequantize dispatch
    # ------------------------------------------------------------------

    def _resolve_bits(self, layer_id: int) -> Tuple[int, int]:
        """Return (k_bits, v_bits) for a given layer.

        When per_layer_bits is provided (Phase 2 allocator mode), the per-layer
        override is used; otherwise falls back to the global (k_bits, v_bits).
        """
        if self._per_layer_bits is not None:
            return self._per_layer_bits[layer_id]
        return self.k_bits, self.v_bits

    def _quantize_k(self, k: Tensor, k_bits: int) -> Tuple[Tensor, Tensor, Optional[Tensor]]:
        """Quantize K tensor according to k_bits. Returns (data, scale, zp)."""
        if k_bits == 16:
            return k.to(self.dtype), None, None
        elif k_bits == 8:
            q_k, k_scale = quantize_symmetric_int8(
                k, percentile=self.k_clip_percentile, group_size=self.k_group_size
            )
            return q_k, k_scale.to(torch.float32), None  # Codex WARN: align with KVC-066 fp32 convention
        else:  # k_bits == 4
            return quantize_asymmetric_per_token(
                k, quant_bits=4, percentile=self.k_clip_percentile
            )

    def _quantize_v(self, v: Tensor, v_bits: int) -> Tuple[Tensor, Tensor, Optional[Tensor]]:
        """Quantize V tensor according to v_bits."""
        if v_bits == 16:
            return v.to(self.dtype), None, None
        elif v_bits == 8:
            q_v, v_scale = quantize_symmetric_int8(
                v, percentile=self.v_percentile, group_size=self.v_group_size
            )
            return q_v, v_scale, None
        else:  # v_bits == 4
            return quantize_asymmetric_per_token(
                v, quant_bits=4, percentile=self.v_percentile
            )

    def _dequantize_k(self, layer_id: int, k_bits: int) -> Tensor:
        """Dequantize K tensor from cache using the layer's configured k_bits."""
        q_k = self._k_cache[layer_id]
        k_scale = self._k_scale[layer_id]
        if k_bits == 16:
            return q_k.to(self.dtype)
        elif k_bits == 8:
            return dequantize_symmetric_int8(q_k, k_scale).to(self.dtype)
        else:  # k_bits == 4
            k_zp = self._k_zp[layer_id]
            return dequantize_asymmetric_per_token(q_k, k_scale, k_zp).to(self.dtype)

    def _dequantize_v(self, layer_id: int, v_bits: int) -> Tensor:
        """Dequantize V tensor from cache using the layer's configured v_bits."""
        q_v = self._v_cache[layer_id]
        v_scale = self._v_scale[layer_id]
        if v_bits == 16:
            return q_v.to(self.dtype)
        elif v_bits == 8:
            return dequantize_symmetric_int8(q_v, v_scale).to(self.dtype)
        else:  # v_bits == 4
            v_zp = self._v_zp[layer_id]
            return dequantize_asymmetric_per_token(q_v, v_scale, v_zp).to(self.dtype)

    def append(self, layer_id: int, k: Tensor, v: Tensor) -> None:
        """Quantize and append KV tensors according to configured bit-widths."""
        if layer_id < 0 or layer_id >= self.num_layers:
            raise ValueError(f"layer_id {layer_id} out of range [0, {self.num_layers})")
        if k.ndim != 4 or v.ndim != 4:
            raise ValueError(f"k/v must be 4D [B,H,S,D], got k={tuple(k.shape)} v={tuple(v.shape)}")
        if tuple(k.shape) != tuple(v.shape):
            raise ValueError(f"k/v shape mismatch: {tuple(k.shape)} vs {tuple(v.shape)}")

        # Resolve bit-widths for this layer (per_layer_bits override or global).
        k_bits_layer, v_bits_layer = self._resolve_bits(layer_id)

        # Quantize K
        q_k, k_scale, k_zp = self._quantize_k(k, k_bits_layer)

        # Quantize V
        q_v, v_scale, v_zp = self._quantize_v(v, v_bits_layer)

        # KVC-081: PERF WARNING — torch.cat per step is O(S^2) cumulative memory
        # copies. For long-sequence workloads this is a bottleneck. A pre-allocated
        # buffer + slice-write approach (like INT8KVCache._ensure_capacity) would
        # reduce this to O(S), but the mixed-type buffer layout (INT8 scales have a
        # group dim, INT4/FP16 have different shapes, zp may be None) makes a
        # unified _ensure_capacity non-trivial. Revisit if profiling shows this
        # cache type on the critical path for long sequences.
        if self._k_cache[layer_id] is None:
            self._k_cache[layer_id] = q_k
            self._k_scale[layer_id] = k_scale
            self._k_zp[layer_id] = k_zp
            self._v_cache[layer_id] = q_v
            self._v_scale[layer_id] = v_scale
            self._v_zp[layer_id] = v_zp
        else:
            self._k_cache[layer_id] = torch.cat([self._k_cache[layer_id], q_k], dim=2)
            if k_scale is not None and self._k_scale[layer_id] is not None:
                self._k_scale[layer_id] = torch.cat([self._k_scale[layer_id], k_scale], dim=2)
            if k_zp is not None and self._k_zp[layer_id] is not None:
                self._k_zp[layer_id] = torch.cat([self._k_zp[layer_id], k_zp], dim=2)
            self._v_cache[layer_id] = torch.cat([self._v_cache[layer_id], q_v], dim=2)
            if v_scale is not None and self._v_scale[layer_id] is not None:
                self._v_scale[layer_id] = torch.cat([self._v_scale[layer_id], v_scale], dim=2)
            if v_zp is not None and self._v_zp[layer_id] is not None:
                self._v_zp[layer_id] = torch.cat([self._v_zp[layer_id], v_zp], dim=2)

        new_len = self._k_cache[layer_id].shape[2]
        self._layer_seq_lens[layer_id] = new_len
        self._seq_len = max(self._layer_seq_lens)

    def get_kv(self, layer_id: int) -> Tuple[Tensor, Tensor]:
        """Dequantize and return KV tensors."""
        if layer_id < 0 or layer_id >= self.num_layers:
            raise ValueError(f"layer_id {layer_id} out of range [0, {self.num_layers})")
        if self._k_cache[layer_id] is None:
            raise ValueError(f"Cache for layer {layer_id} is empty")

        k_bits_layer, v_bits_layer = self._resolve_bits(layer_id)
        k = self._dequantize_k(layer_id, k_bits_layer)
        v = self._dequantize_v(layer_id, v_bits_layer)

        return k, v

    def get_seq_len(self) -> int:
        return self._seq_len

    def clear(self) -> None:
        """Clear all cached data and reset lengths.

        KVC-083: For torch.cat-based caches, clear() must nil out tensor
        references because append() uses `is None` to detect first-write.
        Keeping stale references would cause torch.cat onto old data.
        Functionally equivalent to release() for this cache type.
        """
        for i in range(self.num_layers):
            self._k_cache[i] = self._k_scale[i] = self._k_zp[i] = None
            self._v_cache[i] = self._v_scale[i] = self._v_zp[i] = None
        self._layer_seq_lens = [0] * self.num_layers
        self._seq_len = 0

    def release(self) -> None:
        """Release all buffers and reset state completely.

        KVC-083: Unlike clear(), this also resets internal list structures,
        matching the semantics of INT8KVCache.release() and
        KIVIStyleKVCache.release().
        """
        self._k_cache = [None] * self.num_layers
        self._v_cache = [None] * self.num_layers
        self._k_scale = [None] * self.num_layers
        self._v_scale = [None] * self.num_layers
        self._k_zp = [None] * self.num_layers
        self._v_zp = [None] * self.num_layers
        self._layer_seq_lens = [0] * self.num_layers
        self._seq_len = 0

    def get_memory_mb(self) -> float:
        total = 0
        for i in range(self.num_layers):
            for t in [self._k_cache[i], self._k_scale[i], self._k_zp[i],
                       self._v_cache[i], self._v_scale[i], self._v_zp[i]]:
                if t is not None:
                    total += t.numel() * t.element_size()
        return total / (1024 * 1024)

    # --- Decode stats interface (compatible) ---

    def record_fused_decode(self, layer_id: int, decode_impl: str) -> None:
        pass

    def record_triton_kernel_call(self, layer_id=None) -> None:
        pass

    def reset_decode_stats(self) -> None:
        pass

    def get_decode_stats(self) -> Dict[str, object]:
        return self.decode_stats

    # ---- KVC-078: HuggingFace past_key_values interop ----

    def to_tuple(self) -> Tuple[Tuple[Tensor, Tensor], ...]:
        """
        Convert cache to HuggingFace past_key_values format.

        Each layer's K/V is dequantized before returning, so the output is a
        tuple of (k_float, v_float) tuples identical to ``get_kv()`` per layer.

        Returns:
            Tuple of (k, v) tuples for each layer.

        Raises:
            ValueError: If any layer cache is empty.
        """
        result = []
        for i in range(self.num_layers):
            if self._k_cache[i] is None:
                raise ValueError(f"Layer {i} cache is empty")
            result.append(self.get_kv(i))
        return tuple(result)
