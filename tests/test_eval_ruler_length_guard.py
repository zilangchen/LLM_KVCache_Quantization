"""Unit tests for length-budget guard helpers in scripts/eval_ruler.py."""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) in sys.path:
    sys.path.remove(str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

try:
    import eval_ruler as ruler  # noqa: E402
except Exception:  # pragma: no cover - environment dependent
    ruler = None


@unittest.skipIf(ruler is None, "eval_ruler dependencies are unavailable in this environment.")
class TestEvalRulerLengthGuard(unittest.TestCase):
    def test_budget_cwe_long_32k(self):
        # gen_len removed; base = min(seq_len + gen_tokens_case, max_model_len)
        budget, base = ruler._effective_prompt_budget(  # pylint: disable=protected-access
            requested_context_len=32704,
            seq_len=32704,
            gen_tokens_case=128,
            max_model_len=32768,
        )
        self.assertEqual(base, 32768)
        self.assertEqual(budget, 32640)

    def test_budget_non_cwe_long_32k(self):
        budget, base = ruler._effective_prompt_budget(  # pylint: disable=protected-access
            requested_context_len=32704,
            seq_len=32704,
            gen_tokens_case=64,
            max_model_len=32768,
        )
        self.assertEqual(base, 32768)
        self.assertEqual(budget, 32704)

    def test_budget_uses_runtime_gen_tokens_case(self):
        budget, base = ruler._effective_prompt_budget(  # pylint: disable=protected-access
            requested_context_len=32704,
            seq_len=32704,
            gen_tokens_case=256,
            max_model_len=32768,
        )
        self.assertEqual(base, 32768)
        self.assertEqual(budget, 32512)

    def test_budget_respects_model_cap_even_if_model_is_larger(self):
        # base = min(32704 + 128, 131072) = 32832
        # budget = min(32704, 32832 - 128) = 32704
        budget, base = ruler._effective_prompt_budget(  # pylint: disable=protected-access
            requested_context_len=32704,
            seq_len=32704,
            gen_tokens_case=128,
            max_model_len=131072,
        )
        self.assertEqual(base, 32832)
        self.assertEqual(budget, 32704)


if __name__ == "__main__":
    unittest.main()
