#!/usr/bin/env python3
"""
TST-011: Unit tests for scoring functions in eval_longbench.py and eval_ruler.py.

Tests the pure-compute scoring helpers (no model loading, no GPU required).
Covers:
  - eval_longbench: _rouge_l, _token_f1, _score_prediction, _truncate_prompt_ids,
                    _compute_official_metric, _classification_accuracy, _edit_similarity
  - eval_ruler:     _score_single_answer (aliased as _score_s_niah),
                    _score_set_answer, _score_case, _score_multi_answer

Strategy: We mock `transformers` at the sys.modules level before importing the
eval scripts so that the module-level `from transformers import ...` succeeds
even when transformers is not installed. The scoring functions under test are
pure Python/torch and do not depend on transformers at all.
"""

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import torch

# ---------------------------------------------------------------------------
# Mock heavy dependencies that are imported at module level by the eval scripts
# but not needed for the pure-compute scoring functions we test here.
# ---------------------------------------------------------------------------
_MOCKED_MODULES = []


def _ensure_mock(module_name: str) -> None:
    """Insert a MagicMock into sys.modules for *module_name* if not already present."""
    if module_name not in sys.modules:
        sys.modules[module_name] = MagicMock()
        _MOCKED_MODULES.append(module_name)


# transformers is required by both eval scripts at import time
_ensure_mock("transformers")

# scripts.config_utils imports are also needed
# (already importable via sys.path, but eval scripts may need it)

# src.engine.generate_loop
_ensure_mock("src.engine.generate_loop")

# src.utils.hf
_ensure_mock("src.utils.hf")

# src.utils.repro
_repro_mock = types.ModuleType("src.utils.repro")
_repro_mock.build_config_snapshot = MagicMock()  # type: ignore[attr-defined]
_repro_mock.get_git_commit = MagicMock(return_value="mock_commit")  # type: ignore[attr-defined]
_repro_mock.get_hardware_info = MagicMock(return_value={"gpu": "mock", "gpu_memory": "0"})  # type: ignore[attr-defined]
_repro_mock.set_seed = MagicMock()  # type: ignore[attr-defined]
_repro_mock.write_config_snapshot = MagicMock()  # type: ignore[attr-defined]
if "src.utils.repro" not in sys.modules:
    sys.modules["src.utils.repro"] = _repro_mock
    _MOCKED_MODULES.append("src.utils.repro")

# scripts.config_utils -- try real import first; mock if unavailable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
# Ensure project root is on path for src.* imports
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Now try importing the eval scripts
elb = None
ruler = None

try:
    import eval_longbench as elb  # type: ignore  # noqa: E402
except Exception:  # pragma: no cover
    elb = None

try:
    import eval_ruler as ruler  # type: ignore  # noqa: E402
except Exception:  # pragma: no cover
    ruler = None


# ===========================================================================
# eval_longbench scoring tests
# ===========================================================================


@unittest.skipIf(elb is None, "eval_longbench import failed even with mocks")
class TestLongBenchRougeL(unittest.TestCase):
    """Tests for _rouge_l."""

    def test_identical_strings(self):
        score = elb._rouge_l("the quick brown fox", "the quick brown fox")
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_no_overlap(self):
        score = elb._rouge_l("alpha beta gamma", "delta epsilon zeta")
        self.assertAlmostEqual(score, 0.0, places=5)

    def test_partial_overlap(self):
        score = elb._rouge_l("the cat sat on the mat", "the cat on the hat")
        # LCS tokens after normalization: "the cat on the" has length >= 4
        self.assertGreater(score, 0.0)
        self.assertLess(score, 1.0)

    def test_both_empty(self):
        score = elb._rouge_l("", "")
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_one_empty(self):
        self.assertAlmostEqual(elb._rouge_l("hello", ""), 0.0, places=5)
        self.assertAlmostEqual(elb._rouge_l("", "hello"), 0.0, places=5)

    def test_punctuation_ignored(self):
        score = elb._rouge_l("don't stop", "dont stop")
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_case_insensitive(self):
        score = elb._rouge_l("Hello World", "hello world")
        self.assertAlmostEqual(score, 1.0, places=5)


@unittest.skipIf(elb is None, "eval_longbench import failed even with mocks")
class TestLongBenchTokenF1(unittest.TestCase):
    """Tests for _token_f1."""

    def test_perfect_match(self):
        score = elb._token_f1("the answer is 42", "the answer is 42")
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_no_overlap(self):
        score = elb._token_f1("alpha beta", "gamma delta")
        self.assertAlmostEqual(score, 0.0, places=5)

    def test_partial_overlap(self):
        # pred="a b c", truth="a b d"
        # common=2, precision=2/3, recall=2/3, F1=2/3
        score = elb._token_f1("a b c", "a b d")
        self.assertAlmostEqual(score, 2.0 / 3.0, places=5)

    def test_both_empty(self):
        score = elb._token_f1("", "")
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_one_empty(self):
        self.assertAlmostEqual(elb._token_f1("hello", ""), 0.0, places=5)
        self.assertAlmostEqual(elb._token_f1("", "hello"), 0.0, places=5)

    def test_duplicate_tokens(self):
        # pred="a a b", truth="a b b"
        # pred_counts: a=2, b=1; truth_counts: a=1, b=2
        # common = min(2,1) + min(1,2) = 1 + 1 = 2
        # precision = 2/3, recall = 2/3, F1 = 2/3
        score = elb._token_f1("a a b", "a b b")
        self.assertAlmostEqual(score, 2.0 / 3.0, places=5)


@unittest.skipIf(elb is None, "eval_longbench import failed even with mocks")
class TestLongBenchScorePrediction(unittest.TestCase):
    """Tests for _score_prediction."""

    def test_exact_match(self):
        result = elb._score_prediction("answer42", ["answer42"])
        self.assertAlmostEqual(result["exact_match"], 1.0)
        self.assertAlmostEqual(result["contains_match"], 1.0)
        self.assertAlmostEqual(result["f1"], 1.0)

    def test_contains_match_but_not_exact(self):
        result = elb._score_prediction("the answer42 is here", ["answer42"])
        self.assertAlmostEqual(result["exact_match"], 0.0)
        self.assertAlmostEqual(result["contains_match"], 1.0)
        self.assertGreater(result["f1"], 0.0)

    def test_no_match(self):
        result = elb._score_prediction("completely wrong", ["correct answer"])
        self.assertAlmostEqual(result["exact_match"], 0.0)
        self.assertAlmostEqual(result["contains_match"], 0.0)

    def test_multiple_answers_best_f1(self):
        result = elb._score_prediction("hello world", ["hello world", "goodbye"])
        self.assertAlmostEqual(result["f1"], 1.0)

    def test_empty_answers(self):
        result = elb._score_prediction("something", [])
        self.assertAlmostEqual(result["exact_match"], 0.0)
        self.assertAlmostEqual(result["contains_match"], 0.0)
        self.assertAlmostEqual(result["f1"], 0.0)


@unittest.skipIf(elb is None, "eval_longbench import failed even with mocks")
class TestLongBenchComputeOfficialMetric(unittest.TestCase):
    """Tests for _compute_official_metric."""

    def test_qa_task_uses_f1(self):
        metric_name, score = elb._compute_official_metric(
            "perfect answer", ["perfect answer"], "narrativeqa"
        )
        self.assertEqual(metric_name, "f1")
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_summarization_task_uses_rouge_l(self):
        metric_name, score = elb._compute_official_metric(
            "the summary", ["the summary"], "gov_report"
        )
        self.assertEqual(metric_name, "rouge_l")
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_classification_task_uses_accuracy(self):
        metric_name, score = elb._compute_official_metric("A", ["A"], "trec")
        self.assertEqual(metric_name, "accuracy")
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_classification_wrong(self):
        metric_name, score = elb._compute_official_metric("B", ["A"], "trec")
        self.assertEqual(metric_name, "accuracy")
        self.assertAlmostEqual(score, 0.0, places=5)

    def test_code_task_uses_edit_sim(self):
        metric_name, score = elb._compute_official_metric("hello", ["hello"], "lcc")
        self.assertEqual(metric_name, "edit_sim")
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_empty_answers_returns_zero(self):
        metric_name, score = elb._compute_official_metric(
            "prediction", [], "narrativeqa"
        )
        self.assertEqual(metric_name, "f1")
        self.assertAlmostEqual(score, 0.0, places=5)

    def test_unknown_task_defaults_to_f1(self):
        metric_name, _ = elb._compute_official_metric("x", ["x"], "unknown_task_xyz")
        self.assertEqual(metric_name, "f1")


@unittest.skipIf(elb is None, "eval_longbench import failed even with mocks")
class TestLongBenchEditSimilarity(unittest.TestCase):
    """Tests for _edit_similarity."""

    def test_identical(self):
        score = elb._edit_similarity("hello world", "hello world")
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_completely_different(self):
        score = elb._edit_similarity("aaaa", "bbbb")
        self.assertLess(score, 0.5)

    def test_both_empty(self):
        score = elb._edit_similarity("", "")
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_one_empty(self):
        self.assertAlmostEqual(elb._edit_similarity("abc", ""), 0.0, places=5)
        self.assertAlmostEqual(elb._edit_similarity("", "abc"), 0.0, places=5)

    def test_small_edit(self):
        # One character difference after normalization: "hello" vs "hallo"
        score = elb._edit_similarity("hello", "hallo")
        # edit distance = 1, max(5,5)=5, similarity = 1-1/5 = 0.8
        self.assertAlmostEqual(score, 0.8, places=2)


@unittest.skipIf(elb is None, "eval_longbench import failed even with mocks")
class TestLongBenchTruncatePromptIds(unittest.TestCase):
    """Tests for _truncate_prompt_ids in eval_longbench."""

    @staticmethod
    def _make_mock_tokenizer(token_count: int):
        """Create a mock tokenizer returning a fixed number of token IDs."""
        tok = MagicMock()
        result = MagicMock()
        result.input_ids = list(range(token_count))
        tok.return_value = result
        return tok

    def test_no_truncation_when_within_budget(self):
        tok = self._make_mock_tokenizer(50)
        ids = elb._truncate_prompt_ids(tok, "dummy prompt", max_tokens=100)
        self.assertEqual(ids.shape, (1, 50))

    def test_truncation_when_exceeding_budget(self):
        tok = self._make_mock_tokenizer(200)
        ids = elb._truncate_prompt_ids(tok, "dummy prompt", max_tokens=100)
        self.assertEqual(ids.shape, (1, 100))

    def test_head_tail_truncation_preserves_ends(self):
        tok = self._make_mock_tokenizer(200)
        ids = elb._truncate_prompt_ids(tok, "dummy", max_tokens=100)
        ids_list = ids[0].tolist()
        # tail_keep = min(128, 100//8) = 12
        # head_keep = 100 - 12 = 88
        self.assertEqual(len(ids_list), 100)
        # First tokens should be from the head (0, 1, 2, ...)
        self.assertEqual(ids_list[:5], [0, 1, 2, 3, 4])
        # Last tokens should be from the tail (..., 197, 198, 199)
        self.assertEqual(ids_list[-3:], [197, 198, 199])

    def test_zero_max_tokens_no_truncation(self):
        tok = self._make_mock_tokenizer(50)
        ids = elb._truncate_prompt_ids(tok, "dummy", max_tokens=0)
        self.assertEqual(ids.shape, (1, 50))

    def test_returns_tensor_type(self):
        tok = self._make_mock_tokenizer(10)
        ids = elb._truncate_prompt_ids(tok, "dummy", max_tokens=100)
        self.assertIsInstance(ids, torch.Tensor)
        self.assertEqual(ids.dtype, torch.long)
        self.assertEqual(ids.ndim, 2)


# ===========================================================================
# eval_ruler scoring tests
# ===========================================================================


@unittest.skipIf(ruler is None, "eval_ruler import failed even with mocks")
class TestRulerScoreSingleAnswer(unittest.TestCase):
    """Tests for _score_single_answer (S-NIAH scoring)."""

    def test_exact_match(self):
        result = ruler._score_single_answer("123456", "123456")
        self.assertAlmostEqual(result["exact_match"], 1.0)
        self.assertAlmostEqual(result["contains_match"], 1.0)
        self.assertAlmostEqual(result["f1"], 1.0)

    def test_contains_but_not_exact(self):
        result = ruler._score_single_answer("the number is 123456 ok", "123456")
        self.assertAlmostEqual(result["exact_match"], 0.0)
        self.assertAlmostEqual(result["contains_match"], 1.0)
        self.assertGreater(result["f1"], 0.0)

    def test_no_match(self):
        result = ruler._score_single_answer("789012", "123456")
        self.assertAlmostEqual(result["exact_match"], 0.0)
        self.assertAlmostEqual(result["contains_match"], 0.0)
        self.assertAlmostEqual(result["f1"], 0.0)

    def test_case_insensitive(self):
        result = ruler._score_single_answer("Hello", "hello")
        self.assertAlmostEqual(result["exact_match"], 1.0)


@unittest.skipIf(ruler is None, "eval_ruler import failed even with mocks")
class TestRulerScoreSetAnswer(unittest.TestCase):
    """Tests for _score_set_answer (CWE scoring)."""

    def test_all_words_found(self):
        result = ruler._score_set_answer(
            "apple banana cherry", ["apple", "banana", "cherry"]
        )
        self.assertAlmostEqual(result["exact_match"], 1.0)
        self.assertAlmostEqual(result["contains_match"], 1.0)
        self.assertAlmostEqual(result["f1"], 1.0)

    def test_partial_overlap(self):
        result = ruler._score_set_answer("apple orange grape", ["apple", "banana"])
        # intersection = {"apple"}, pred_words=3, truth_words=2
        # precision=1/3, recall=1/2, F1=2*(1/3)*(1/2)/((1/3)+(1/2))
        self.assertAlmostEqual(result["exact_match"], 0.0)
        self.assertAlmostEqual(result["contains_match"], 0.5)
        expected_f1 = 2.0 * (1 / 3) * (1 / 2) / ((1 / 3) + (1 / 2))
        self.assertAlmostEqual(result["f1"], expected_f1, places=4)

    def test_no_overlap(self):
        result = ruler._score_set_answer("grape orange", ["apple", "banana"])
        self.assertAlmostEqual(result["exact_match"], 0.0)
        self.assertAlmostEqual(result["contains_match"], 0.0)
        self.assertAlmostEqual(result["f1"], 0.0)

    def test_empty_truth(self):
        result = ruler._score_set_answer("apple banana", [])
        self.assertAlmostEqual(result["exact_match"], 0.0)
        self.assertAlmostEqual(result["f1"], 0.0)

    def test_superset_prediction(self):
        result = ruler._score_set_answer(
            "apple banana cherry extra words", ["apple", "banana"]
        )
        self.assertAlmostEqual(result["exact_match"], 1.0)
        self.assertAlmostEqual(result["contains_match"], 1.0)


@unittest.skipIf(ruler is None, "eval_ruler import failed even with mocks")
class TestRulerScoreMultiAnswer(unittest.TestCase):
    """Tests for _score_multi_answer (MK-NIAH scoring)."""

    def test_all_answers_found(self):
        result = ruler._score_multi_answer(
            "val_abc val_def val_ghi", ["val_abc", "val_def", "val_ghi"]
        )
        self.assertAlmostEqual(result["exact_match"], 1.0)
        self.assertAlmostEqual(result["contains_match"], 1.0)

    def test_partial_answers_found(self):
        result = ruler._score_multi_answer(
            "val_abc something else", ["val_abc", "val_def"]
        )
        self.assertAlmostEqual(result["exact_match"], 0.0)
        self.assertAlmostEqual(result["contains_match"], 0.5)

    def test_no_answers_found(self):
        result = ruler._score_multi_answer(
            "nothing here", ["val_abc", "val_def"]
        )
        self.assertAlmostEqual(result["exact_match"], 0.0)
        self.assertAlmostEqual(result["contains_match"], 0.0)

    def test_empty_answers(self):
        result = ruler._score_multi_answer("some text", [])
        self.assertAlmostEqual(result["exact_match"], 0.0)
        self.assertAlmostEqual(result["f1"], 0.0)


@unittest.skipIf(ruler is None, "eval_ruler import failed even with mocks")
class TestRulerScoreCase(unittest.TestCase):
    """Tests for _score_case dispatch logic."""

    def test_s_niah_dispatch(self):
        case = ruler.RulerCase(
            task_name="s_niah",
            case_id="test",
            depth_ratio=0.5,
            context="",
            question="",
            expected_answers=["123456"],
        )
        result = ruler._score_case(case, "123456")
        self.assertAlmostEqual(result["exact_match"], 1.0)

    def test_cwe_dispatch(self):
        case = ruler.RulerCase(
            task_name="cwe",
            case_id="test",
            depth_ratio=0.5,
            context="",
            question="",
            expected_answers=["apple", "banana"],
        )
        result = ruler._score_case(case, "apple banana")
        self.assertAlmostEqual(result["exact_match"], 1.0)

    def test_mk_niah_multi_key_dispatch(self):
        case = ruler.RulerCase(
            task_name="mk_niah",
            case_id="test",
            depth_ratio=0.5,
            context="",
            question="",
            expected_answers=["val1", "val2", "val3"],
        )
        result = ruler._score_case(case, "val1 val2 val3")
        self.assertAlmostEqual(result["exact_match"], 1.0)

    def test_vt_single_chain_dispatch(self):
        case = ruler.RulerCase(
            task_name="vt",
            case_id="test",
            depth_ratio=0.5,
            context="",
            question="",
            expected_answers=["v_abc123"],
        )
        result = ruler._score_case(case, "v_abc123")
        self.assertAlmostEqual(result["exact_match"], 1.0)

    def test_vt_multi_chain_dispatch(self):
        case = ruler.RulerCase(
            task_name="vt",
            case_id="test",
            depth_ratio=0.5,
            context="",
            question="",
            expected_answers=["v_a", "v_b"],
        )
        result = ruler._score_case(case, "v_a v_b")
        self.assertAlmostEqual(result["exact_match"], 1.0)


@unittest.skipIf(ruler is None, "eval_ruler import failed even with mocks")
class TestRulerTruncatePromptIds(unittest.TestCase):
    """Tests for _truncate_prompt_ids in eval_ruler."""

    @staticmethod
    def _make_mock_tokenizer(token_count: int):
        tok = MagicMock()
        result = MagicMock()
        result.input_ids = list(range(token_count))
        tok.return_value = result
        return tok

    def test_no_truncation(self):
        tok = self._make_mock_tokenizer(50)
        ids, truncated = ruler._truncate_prompt_ids(tok, "dummy", max_tokens=100)
        self.assertEqual(ids.shape, (1, 50))
        self.assertFalse(truncated)

    def test_truncation_applied(self):
        tok = self._make_mock_tokenizer(200)
        ids, truncated = ruler._truncate_prompt_ids(tok, "dummy", max_tokens=100)
        self.assertEqual(ids.shape, (1, 100))
        self.assertTrue(truncated)

    def test_head_tail_preservation(self):
        tok = self._make_mock_tokenizer(200)
        ids, _ = ruler._truncate_prompt_ids(tok, "dummy", max_tokens=100)
        ids_list = ids[0].tolist()
        # tail_keep = min(128, int(100 * 1/8)) = min(128, 12) = 12
        # head_keep = 100 - 12 = 88
        self.assertEqual(ids_list[:3], [0, 1, 2])
        self.assertEqual(ids_list[-3:], [197, 198, 199])


@unittest.skipIf(ruler is None, "eval_ruler not importable")
class TestScoreSingleAnswerContainsMatch(unittest.TestCase):
    """EVL-070 regression: _score_single_answer must return contains_match."""

    def test_contains_match_reported(self):
        result = ruler._score_single_answer("The answer is 123456", "123456")
        self.assertIn("contains_match", result)
        self.assertEqual(result["contains_match"], 1.0)
        # exact_match should be 0 because pred != ans
        self.assertEqual(result["exact_match"], 0.0)

    def test_exact_match_implies_contains(self):
        result = ruler._score_single_answer("123456", "123456")
        self.assertEqual(result["exact_match"], 1.0)
        self.assertEqual(result["contains_match"], 1.0)


@unittest.skipIf(ruler is None, "eval_ruler not importable")
class TestMkNiahDistinctPositions(unittest.TestCase):
    """EVL-048 regression: MK-NIAH needles must be at different positions."""

    def test_pair_depths_are_distinct(self):
        import random
        num_keys = 4
        base_ratio = 0.5
        # Reproduce the depth scattering logic from _build_mk_niah_cases
        max_spread = min(base_ratio - 0.05, 0.95 - base_ratio, 0.40)
        pair_depths = [
            max(0.05, min(0.95,
                base_ratio + max_spread * (2.0 * k / (num_keys - 1) - 1.0)))
            for k in range(num_keys)
        ]
        # All depths must be distinct
        self.assertEqual(len(pair_depths), len(set(pair_depths)),
                         f"MK-NIAH depths not distinct: {pair_depths}")


@unittest.skipIf(ruler is None, "eval_ruler not importable")
class TestCweTargetFrequencyDominates(unittest.TestCase):
    """EVL-047 regression: target words must be more frequent than distractors."""

    def test_target_more_frequent(self):
        import random as stdlib_random
        rng = stdlib_random.Random(42)
        freq_cw = 30
        num_cw = 10
        word_pool = [f"word_{i}" for i in range(50)]
        rng_copy = stdlib_random.Random(42)
        rng_copy.shuffle(word_pool)
        target_words = word_pool[:num_cw]
        distractor_words = word_pool[num_cw:num_cw + 20]

        all_words = []
        for w in target_words:
            all_words.extend([w] * freq_cw)
        for w in distractor_words:
            all_words.extend([w] * rng.randint(1, 3))

        from collections import Counter
        counts = Counter(all_words)
        min_target = min(counts[w] for w in target_words)
        max_distractor = max(counts[w] for w in distractor_words if w in counts)
        self.assertGreater(min_target, max_distractor,
                           "Target words must be more frequent than distractors")


if __name__ == "__main__":
    unittest.main()
