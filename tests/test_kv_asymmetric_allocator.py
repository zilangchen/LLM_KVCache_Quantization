import json
from pathlib import Path

import pytest

from scripts.adaptive.behavior_aligned_allocator import (
    assign_kv_bit_pairs,
    export_kv_asymmetric_policy,
    score_kv_roles,
)


@pytest.fixture
def mock_calib():
    return {
        "model_id": "mock-model",
        "num_layers": 4,
        "k_scale": [
            [[4.0, 2.0], [1.0, 1.0]],
            [[2.0, 1.0], [1.0, 1.0]],
            [[1.0, 1.0], [1.0, 1.0]],
            [[0.5, 0.5], [0.5, 0.5]],
        ],
        "v_scale": [
            [[1.0, 1.0], [1.0, 1.0]],
            [[3.0, 2.0], [1.0, 1.0]],
            [[2.0, 2.0], [2.0, 2.0]],
            [[0.5, 0.5], [0.5, 0.5]],
        ],
    }


def test_score_kv_roles_outputs_parallel_scores(mock_calib):
    scores = score_kv_roles(mock_calib, agg="max", k_bias=1.2, v_bias=1.0)
    assert len(scores["k_score"]) == mock_calib["num_layers"]
    assert len(scores["v_score"]) == mock_calib["num_layers"]
    assert len(scores["combined_score"]) == mock_calib["num_layers"]
    assert len(scores["importance_tier"]) == mock_calib["num_layers"]
    # layer 0 is K-dominant, layer 2 is V-dominant
    assert scores["k_score"][0] > scores["v_score"][0]
    assert scores["v_score"][2] >= scores["k_score"][2]


def test_score_kv_roles_applies_k_bias(mock_calib):
    scores_equal = score_kv_roles(mock_calib, agg="mean", k_bias=1.0, v_bias=1.0)
    scores_biased = score_kv_roles(mock_calib, agg="mean", k_bias=1.3, v_bias=1.0)
    assert scores_biased["k_score"][0] > scores_equal["k_score"][0]
    assert scores_biased["v_score"][0] == pytest.approx(scores_equal["v_score"][0])


def test_assign_kv_bit_pairs_avg_bits_budget(mock_calib):
    scores = score_kv_roles(mock_calib)
    assignment = assign_kv_bit_pairs(scores, budget_mode="avg_bits", budget_value=5.0)
    assert assignment["role_slots"] == 2
    assert assignment["avg_bits"] == pytest.approx(5.0)
    assert len(assignment["per_layer_bits"]) == mock_calib["num_layers"]
    assert set(assignment["per_layer_bits"]).issubset({(4, 4), (8, 4), (4, 8), (8, 8)})


def test_assign_kv_bit_pairs_role_slots(mock_calib):
    scores = score_kv_roles(mock_calib)
    assignment = assign_kv_bit_pairs(scores, budget_mode="role_slots", budget_value=3)
    assert assignment["role_slots"] == 3
    upgraded = [pair for pair in assignment["per_layer_bits"] if pair != (4, 4)]
    assert len(upgraded) >= 2


def test_export_kv_asymmetric_policy_schema(tmp_path: Path, mock_calib):
    out_path = tmp_path / "policy.json"
    policy = export_kv_asymmetric_policy(
        mock_calib,
        out_path=out_path,
        budget_mode="avg_bits",
        budget_value=5.0,
        agg="max",
        k_bias=1.15,
        v_bias=1.0,
    )
    assert out_path.exists()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["policy_type"] == "kv_asymmetric_layerwise"
    assert payload["num_layers"] == mock_calib["num_layers"]
    assert len(payload["per_layer_bits"]) == mock_calib["num_layers"]
    assert payload["avg_bits"] == pytest.approx(policy["avg_bits"])
    assert "k_score" in payload and "v_score" in payload
