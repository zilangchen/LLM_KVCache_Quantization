"""
Tests for behavior_aligned_allocator.py --sensitivity_agg extension (编号 7 W1).

覆盖 Codex 2026-04-18 06:55 修订版 4 case：
- test_sensitivity_agg_max_backward_compat: agg="max" 与旧默认行为完全等价
- test_sensitivity_agg_mean_differs_from_max: agg="mean" 产出不同 sensitivity（k_scale 非均匀时）
- test_sensitivity_agg_invalid_raises: 非法值（如 "random"）抛 ValueError（防 Codex 修订前 random 语义混淆）
- test_top_k_with_mean_selects_mean_highest: top_k + mean 选出 mean 最大的 k 层（非 max 最大）

本测试只用 numpy，不需要 torch/GPU——可在远端 conda base 或任意 numpy 环境跑。
"""
import numpy as np
import pytest

from scripts.adaptive.behavior_aligned_allocator import (
    compute_layer_sensitivity,
    policy_top_k,
)


@pytest.fixture
def mock_calib():
    """构造 4 层 × 2 头 × 2 组的假 k_scale：
    - layer 0: [[10, 0.1], [0.1, 0.1]] → max=10, mean=2.58
    - layer 1: [[1, 1], [1, 1]]        → max=1,  mean=1.0
    - layer 2: [[0.5, 5], [0.5, 0.5]]  → max=5,  mean=1.625
    - layer 3: [[3, 3], [3, 3]]        → max=3,  mean=3.0
    按 max 排序: L0 > L2 > L3 > L1
    按 mean 排序: L3 > L0 > L2 > L1
    top-2 选择：max → {0, 2}; mean → {3, 0}
    """
    return {
        "num_layers": 4,
        "model_id": "mock",
        "k_scale": [
            [[10.0, 0.1], [0.1, 0.1]],
            [[1.0, 1.0], [1.0, 1.0]],
            [[0.5, 5.0], [0.5, 0.5]],
            [[3.0, 3.0], [3.0, 3.0]],
        ],
    }


def test_sensitivity_agg_max_backward_compat(mock_calib):
    """agg=max (新默认) 与旧调用 compute_layer_sensitivity(calib) 的行为等价。"""
    sens_new_default = compute_layer_sensitivity(mock_calib)           # 新默认 agg="max"
    sens_explicit_max = compute_layer_sensitivity(mock_calib, agg="max")
    np.testing.assert_array_equal(sens_new_default, sens_explicit_max)
    # 且结果与手算 max 一致
    expected = np.array([10.0, 1.0, 5.0, 3.0])
    np.testing.assert_allclose(sens_explicit_max, expected)


def test_sensitivity_agg_mean_differs_from_max(mock_calib):
    """agg=mean 产出不同于 max 的 sensitivity（验证 agg 参数确实生效）。"""
    sens_max = compute_layer_sensitivity(mock_calib, agg="max")
    sens_mean = compute_layer_sensitivity(mock_calib, agg="mean")
    # 两者不应逐点相同（至少一层的 max > mean）
    assert not np.allclose(sens_max, sens_mean)
    expected_mean = np.array([(10.0 + 0.1 + 0.1 + 0.1) / 4,
                              1.0,
                              (0.5 + 5.0 + 0.5 + 0.5) / 4,
                              3.0])
    np.testing.assert_allclose(sens_mean, expected_mean)


def test_sensitivity_agg_invalid_raises(mock_calib):
    """非法 agg 值抛 ValueError，特别是 'random'（Codex 修订：random 走独立 random_k policy）。"""
    with pytest.raises(ValueError, match="must be 'max' or 'mean'"):
        compute_layer_sensitivity(mock_calib, agg="random")
    with pytest.raises(ValueError, match="must be 'max' or 'mean'"):
        compute_layer_sensitivity(mock_calib, agg="median")
    with pytest.raises(ValueError, match="must be 'max' or 'mean'"):
        compute_layer_sensitivity(mock_calib, agg="foo")


def test_top_k_with_mean_selects_mean_highest(mock_calib):
    """top_k + mean 选出 mean 最大的 k 层（应与 max 的 top-k 不同）。"""
    sens_max = compute_layer_sensitivity(mock_calib, agg="max")
    sens_mean = compute_layer_sensitivity(mock_calib, agg="mean")

    # 用 k=2 各自跑 top_k
    per_layer_max = policy_top_k(sens_max, k=2, high_bits=(8, 8), low_bits=(4, 4))
    per_layer_mean = policy_top_k(sens_mean, k=2, high_bits=(8, 8), low_bits=(4, 4))

    protected_max = sorted([i for i, b in enumerate(per_layer_max) if b == (8, 8)])
    protected_mean = sorted([i for i, b in enumerate(per_layer_mean) if b == (8, 8)])

    # max 选择 layer 0, 2（top-2 by max=10, 5）
    assert protected_max == [0, 2], f"max top-2 expected [0, 2], got {protected_max}"
    # mean 选择 layer 0, 3（top-2 by mean=2.58, 3.0）
    assert protected_mean == [0, 3], f"mean top-2 expected [0, 3], got {protected_mean}"
    # 两者至少差一个 layer
    assert set(protected_max) != set(protected_mean)


def test_sensitivity_agg_preserves_shape(mock_calib):
    """无论 agg 方式，sensitivity 输出 shape 都是 (L,)。"""
    L = mock_calib["num_layers"]
    for agg in ("max", "mean"):
        sens = compute_layer_sensitivity(mock_calib, agg=agg)
        assert sens.shape == (L,), f"agg={agg}: expected shape ({L},), got {sens.shape}"
