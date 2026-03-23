#!/usr/bin/env python3
"""
Role-Aware Asymmetric KV Cache — ours_asym / ours_asym_ba.

Thin subclass of KIVIStyleKVCache that marks framework affiliation
with the behavior-aligned (BA) quantization family.

The quantization format is identical to KIVIStyleKVCache:
  - K: per-channel asymmetric quantization
  - V: per-token asymmetric quantization

The key difference is HOW the quantization parameters are determined:
  - kivi_style: online heuristic (runtime absmax/min, no calibration)
  - ours_asym:  offline BA pipeline (KL-guided k_percentile, v_percentile, inv_tau)

See docs/rolealign_design_note.md for the full design rationale.
"""

from typing import Optional

import torch
from torch import Tensor

from src.cache.kivi_style_cache import KIVIStyleKVCache


class RoleAwareAsymKVCache(KIVIStyleKVCache):
    """
    Role-Aware Asymmetric KV Cache.

    Inherits all storage and quantization logic from KIVIStyleKVCache.
    Adds framework metadata to distinguish ours_asym from kivi_style
    in the generate_loop routing and experiment tracking.

    Attributes (beyond parent):
        framework: str — "ours_asym" or "ours_asym_ba"
        ba_calibrated: bool — whether BA-calibrated percentiles are active
    """

    def __init__(
        self,
        num_layers: int,
        device: str = "cuda",
        dtype: torch.dtype = torch.float16,
        max_seq_len: Optional[int] = None,
        quant_bits: int = 4,
        k_percentile: float = 100.0,
        v_percentile: float = 100.0,
        inv_tau: Optional[Tensor] = None,
        use_attn_temperature: bool = False,
        framework: str = "ours_asym",
    ):
        super().__init__(
            num_layers=num_layers,
            device=device,
            dtype=dtype,
            max_seq_len=max_seq_len,
            quant_bits=quant_bits,
            k_percentile=k_percentile,
            v_percentile=v_percentile,
            inv_tau=inv_tau,
            use_attn_temperature=use_attn_temperature,
        )
        self.framework = framework
        # Mark whether BA-calibrated percentiles are in use
        # (vs default 100.0 which means no calibration = plain KIVI behavior)
        self.ba_calibrated = (k_percentile != 100.0) or (v_percentile != 100.0)
