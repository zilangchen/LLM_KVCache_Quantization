"""
Tests for coverage-based auto-k range proposer.

覆盖目标：
- coverage-based auto-k 不输出单点神谕，而是输出 candidate range
- 80% coverage 作为 recommended_k
- auto-k 单点 policy 与 range proposal 一致
"""

import numpy as np
import pytest

from scripts.adaptive.behavior_aligned_allocator import (
    policy_auto_k_coverage,
    propose_auto_k_range,
    select_top_k_by_coverage,
)


@pytest.fixture
def mock_sens():
    # 排序后 cumulative coverage:
    # [5,4,3,2,1] / 15
    # k=2 -> 9/15 = 0.60
    # k=3 -> 12/15 = 0.80
    # k=4 -> 14/15 = 0.9333
    return np.array([5.0, 4.0, 3.0, 2.0, 1.0], dtype=float)


def test_select_top_k_by_coverage_hits_smallest_k(mock_sens):
    k, protected, achieved = select_top_k_by_coverage(mock_sens, coverage=0.8)
    assert k == 3
    assert protected == [0, 1, 2]
    assert achieved == pytest.approx(12.0 / 15.0)


def test_select_top_k_by_coverage_validates_range(mock_sens):
    with pytest.raises(ValueError, match="coverage must be in"):
        select_top_k_by_coverage(mock_sens, coverage=0.0)
    with pytest.raises(ValueError, match="coverage must be in"):
        select_top_k_by_coverage(mock_sens, coverage=1.2)


def test_propose_auto_k_range_outputs_candidate_band(mock_sens):
    proposal = propose_auto_k_range(mock_sens, coverage_targets=[0.7, 0.8, 0.9])
    assert proposal["candidate_ks"] == [3, 4]
    assert proposal["recommended_k"] == 3
    assert proposal["recommended_coverage"] == pytest.approx(0.8)
    assert [round(item["coverage"], 1) for item in proposal["proposals"]] == [0.7, 0.8, 0.9]
    assert [item["selected_k"] for item in proposal["proposals"]] == [3, 3, 4]


def test_policy_auto_k_coverage_builds_per_layer_bits(mock_sens):
    per_layer, selected_k, protected, achieved = policy_auto_k_coverage(
        mock_sens,
        coverage=0.8,
        high_bits=(8, 8),
        low_bits=(4, 4),
    )
    assert selected_k == 3
    assert protected == [0, 1, 2]
    assert achieved == pytest.approx(12.0 / 15.0)
    assert per_layer == [(8, 8), (8, 8), (8, 8), (4, 4), (4, 4)]


def test_auto_k_range_supports_k_bounds(mock_sens):
    proposal = propose_auto_k_range(
        mock_sens,
        coverage_targets=[0.7, 0.8, 0.9],
        min_k=2,
        max_k=3,
    )
    assert proposal["candidate_ks"] == [3]
    assert proposal["recommended_k"] == 3
    assert [item["selected_k"] for item in proposal["proposals"]] == [3, 3, 3]
