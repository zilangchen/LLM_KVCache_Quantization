"""
Tests for MixedKVCache per_layer_bits extension (Phase 2 编号 6 W1).

Covers Codex 2026-04-18 修订版 v2 的 5 case 验证：
- happy path: per-layer bit dispatch produces different cache sizes per layer
- backward compatibility: per_layer_bits=None retains pre-change behavior
- invalid length: len(per_layer_bits) != num_layers raises ValueError
- invalid bit: 非 {4, 8, 16} bit 值 raises ValueError
- precedence: per_layer_bits overrides global k_bits/v_bits

Runs on CUDA when available (默认远端 H20)；本地无 GPU 时 pytest 通过 skip。
"""
import pytest
import torch

from src.cache.mixed_kv_cache import MixedKVCache


pytestmark = pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="MixedKVCache requires CUDA for underlying quantize ops",
)


@pytest.fixture
def device():
    return "cuda"


def _make_kv(num_heads=2, seq_len=8, head_dim=128, dtype=torch.float16, device="cuda"):
    """Construct a pair of (k, v) tensors with shape [B=1, H, S, D].

    head_dim defaults to 128 to match the default k_group_size=128 in MixedKVCache
    (head_dim must be divisible by group_size for INT8 symmetric quantization).
    """
    k = torch.randn(1, num_heads, seq_len, head_dim, dtype=dtype, device=device)
    v = torch.randn(1, num_heads, seq_len, head_dim, dtype=dtype, device=device)
    return k, v


def test_per_layer_bits_happy_path(device):
    """Different layers get different bit-widths; append/get_kv round-trips."""
    num_layers = 4
    per_layer = [(8, 8), (4, 4), (8, 8), (4, 4)]
    cache = MixedKVCache(
        num_layers=num_layers, device=device,
        per_layer_bits=per_layer,
    )
    assert cache._per_layer_bits == per_layer
    assert cache._resolve_bits(0) == (8, 8)
    assert cache._resolve_bits(1) == (4, 4)

    for layer_id in range(num_layers):
        k, v = _make_kv(device=device)
        cache.append(layer_id, k, v)
        k_out, v_out = cache.get_kv(layer_id)
        assert k_out.shape == k.shape
        assert v_out.shape == v.shape


def test_per_layer_bits_none_backward_compat(device):
    """per_layer_bits=None retains global k_bits/v_bits behavior (防御 eval_ppl 等现有调用)."""
    cache_none = MixedKVCache(
        num_layers=2, device=device, k_bits=8, v_bits=4,
        per_layer_bits=None,
    )
    cache_default = MixedKVCache(
        num_layers=2, device=device, k_bits=8, v_bits=4,
    )
    assert cache_none._per_layer_bits is None
    assert cache_default._per_layer_bits is None
    # Resolve at any layer should return global values.
    assert cache_none._resolve_bits(0) == (8, 4)
    assert cache_none._resolve_bits(1) == (8, 4)

    # Round-trip smoke: ensure append/get_kv still work in backward compat path.
    k, v = _make_kv(device=device)
    cache_none.append(0, k, v)
    k_out, v_out = cache_none.get_kv(0)
    assert k_out.shape == k.shape
    assert v_out.shape == v.shape


def test_per_layer_bits_invalid_length(device):
    """len(per_layer_bits) != num_layers raises ValueError."""
    with pytest.raises(ValueError, match="length"):
        MixedKVCache(
            num_layers=4, device=device,
            per_layer_bits=[(8, 8), (4, 4)],  # only 2 entries for 4 layers
        )
    with pytest.raises(ValueError, match="length"):
        MixedKVCache(
            num_layers=2, device=device,
            per_layer_bits=[(8, 8), (4, 4), (8, 8)],  # 3 entries for 2 layers
        )


def test_per_layer_bits_invalid_bit(device):
    """Bit values outside {4, 8, 16} or non-tuple entries raise ValueError."""
    # Bit value 3 is not supported
    with pytest.raises(ValueError, match="unsupported bits"):
        MixedKVCache(
            num_layers=2, device=device,
            per_layer_bits=[(8, 8), (3, 4)],
        )
    # Bit value 2 not supported either
    with pytest.raises(ValueError, match="unsupported bits"):
        MixedKVCache(
            num_layers=2, device=device,
            per_layer_bits=[(2, 4), (8, 8)],
        )
    # Non-tuple entry
    with pytest.raises(ValueError, match="2-tuple"):
        MixedKVCache(
            num_layers=2, device=device,
            per_layer_bits=[(8, 8), 4],
        )
    # Wrong tuple length
    with pytest.raises(ValueError, match="2-tuple"):
        MixedKVCache(
            num_layers=2, device=device,
            per_layer_bits=[(8, 8), (4, 4, 4)],
        )


def test_per_layer_bits_precedence(device):
    """per_layer_bits overrides global k_bits/v_bits when provided."""
    cache = MixedKVCache(
        num_layers=3, device=device,
        k_bits=8, v_bits=4,  # global says INT8/INT4
        per_layer_bits=[(4, 4), (8, 8), (16, 16)],  # per-layer overrides
    )
    # Per-layer resolution should beat global attributes.
    assert cache._resolve_bits(0) == (4, 4)
    assert cache._resolve_bits(1) == (8, 8)
    assert cache._resolve_bits(2) == (16, 16)
    # Global fields preserved for inspection/logging/backward lookups.
    assert cache.k_bits == 8 and cache.v_bits == 4
