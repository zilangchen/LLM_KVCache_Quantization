#!/usr/bin/env python3
"""
Shared helpers for INT8 and INT4 quantization modules.
"""

import warnings

import torch
from torch import Tensor


def _check_quantize_input(tensor: Tensor, func_name: str = "quantize") -> None:
    """QNT-021: Reject NaN/Inf inputs that would produce silently corrupt output."""
    if tensor.numel() == 0:
        return
    if torch.isnan(tensor).any():
        raise ValueError(f"{func_name}: input contains NaN — refusing to quantize corrupt data")
    if torch.isinf(tensor).any():
        raise ValueError(f"{func_name}: input contains Inf — refusing to quantize corrupt data")


def _normalize_static_scale(
    scale: Tensor,
    batch: int,
    heads: int,
    seq_len: int,
    num_groups: int,
) -> Tensor:
    """
    Normalize static scale to shape [B, H, S, num_groups, 1].

    Accepts scale in one of the following shapes:
    - [H, num_groups]                   (2D, broadcast over batch & seq)
    - [B, H, G] / [1, H, G]            (3D, broadcast over seq)
    - [H, 1, G] / [H, G, 1]            (3D legacy, broadcast over batch & seq)
    - [1, H, 1, num_groups]             (4D, broadcast over batch & seq)
    - [B, H, S, num_groups]             (4D, no broadcast needed)
    - [B, H, S, num_groups, 1]          (5D, already target shape)
    """
    if scale.ndim == 2:
        # [H, G] -> [1, H, 1, G, 1]
        scale_view = scale[None, :, None, :, None]
    elif scale.ndim == 4:
        # [B, H, S, G] -> [B, H, S, G, 1]
        scale_view = scale[..., None]
    elif scale.ndim == 5:
        scale_view = scale
    elif scale.ndim == 3:
        # Several 3D layouts are supported.
        # Dispatch is by matching shape dims against (batch, heads, num_groups).
        #
        # QNT-032: When batch == heads (and potentially == num_groups), multiple
        # branches could match.  We use specificity ordering (most constrained
        # first) and emit a warning for the genuinely ambiguous case so callers
        # can supply a 4D/5D scale to avoid it.
        d0, d1, d2 = scale.shape

        # Legacy layouts are tested first because they have a structural marker
        # (a dim == 1) that makes them unambiguous even when batch == heads.
        if d2 == num_groups and d0 == heads and d1 == 1:
            # [H, 1, G] (legacy) -> [1, H, 1, G, 1]
            scale_view = scale[:, 0, :][None, :, None, :, None]
        elif d1 == num_groups and d0 == heads and d2 == 1:
            # [H, G, 1] (legacy) -> [1, H, 1, G, 1]
            scale_view = scale[..., 0][None, :, None, :, None]
        elif d2 == num_groups and d0 == 1 and d1 == heads:
            # [1, H, G] -> [1, H, 1, G, 1]; final expand handles batch.
            scale_view = scale[:, :, None, :, None]
        elif d2 == num_groups and d0 == batch and d1 == heads:
            # [B, H, G] -> [B, H, 1, G, 1]
            if batch == heads and batch == num_groups:
                warnings.warn(
                    f"_normalize_static_scale: 3D scale shape {scale.shape} is "
                    f"ambiguous because batch==heads==num_groups=={batch}. "
                    "Interpreting as [B, H, G]. Use 4D/5D scale to avoid ambiguity.",
                    stacklevel=2,
                )
            scale_view = scale[:, :, None, :, None]
        else:
            raise ValueError(
                f"Unsupported 3D scale shape: {scale.shape} for "
                f"batch={batch}, heads={heads}, num_groups={num_groups}"
            )
    else:
        raise ValueError(f"Unsupported scale ndim={scale.ndim}, shape={tuple(scale.shape)}")

    # QNT-042: Device consistency check — scale on CPU + tensor on GPU would
    # succeed through expand() but fail later during division, with an error
    # message pointing far from the root cause.  Validate early.
    # NOTE: We cannot check tensor device here (scale-only function), but the
    # caller (quantize_*_with_scale) should ensure device consistency before
    # calling.  This expand will naturally raise if scale is on a different
    # device than the allocation target, but the error is not always clear.
    scale_view = scale_view.expand(batch, heads, seq_len, num_groups, 1)
    return scale_view
