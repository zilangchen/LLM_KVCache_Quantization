"""Regression tests for LongBench classification policy."""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) in sys.path:
    sys.path.remove(str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

try:
    import eval_longbench as elb  # type: ignore  # noqa: E402
except Exception:  # pragma: no cover - optional in CPU-only dev envs.
    elb = None


@unittest.skipIf(elb is None, "eval_longbench dependencies unavailable in current environment")
class TestLongBenchClassificationPolicy(unittest.TestCase):
    def test_classification_uses_exact_match(self):
        self.assertEqual(elb._classification_accuracy("A", ["A"]), 1.0)  # pylint: disable=protected-access

    def test_classification_rejects_substring_match(self):
        self.assertEqual(
            elb._classification_accuracy("category_a_extended", ["category_a"]),  # pylint: disable=protected-access
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
