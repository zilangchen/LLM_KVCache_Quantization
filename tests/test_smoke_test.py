"""TST-037: Unit tests for scripts/smoke_test.py utility functions.

Tests cover:
- get_git_commit(): returns commit hash or "unknown"
- get_hardware_info(): returns dict with expected keys
- Main flow mocking: CUDA unavailable exit(0) path with --cpu-ok
"""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Only add PROJECT_ROOT (not SRC_DIR) to avoid src.cache vs cache conflict
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# NOTE: We import src.utils.repro lazily (inside each test method) instead of
# at module level.  Other test files (e.g. test_eval_ppl_guardrails) may
# monkey-patch attributes on the real src.utils.repro module at collection time
# and restore them in tearDownModule.  A module-level `from src.utils.repro
# import get_git_commit` would capture the mock reference before tearDown runs,
# causing spurious failures.


def _get_git_commit():
    """Lazy accessor that always reads the current module attribute."""
    import src.utils.repro as _repro
    return _repro.get_git_commit()


def _get_hardware_info():
    """Lazy accessor that always reads the current module attribute."""
    import src.utils.repro as _repro
    return _repro.get_hardware_info()


class TestGetGitCommit(unittest.TestCase):
    """Tests for get_git_commit() from src/utils/repro.py."""

    def test_returns_string(self):
        """get_git_commit() must always return a string."""
        from src.utils.repro import get_git_commit
        result = get_git_commit()
        self.assertIsInstance(result, str)

    def test_returns_hash_or_unknown(self):
        """Return value must be either a short hex hash or 'unknown'."""
        from src.utils.repro import get_git_commit
        result = get_git_commit()
        if result != "unknown":
            # Should be a hex string of length <= 8
            self.assertLessEqual(len(result), 8)
            self.assertTrue(
                all(c in "0123456789abcdef" for c in result),
                f"Expected hex chars, got '{result}'",
            )

    @patch("src.utils.repro.subprocess.run")
    def test_git_available_returns_hash(self, mock_run):
        """When git succeeds, return first 8 chars of the hash."""
        from src.utils.repro import get_git_commit
        mock_run.return_value = MagicMock(
            stdout="abcdef1234567890\n",
            returncode=0,
        )
        result = get_git_commit()
        self.assertEqual(result, "abcdef12")

    @patch("src.utils.repro.subprocess.run", side_effect=FileNotFoundError)
    def test_git_not_found_returns_unknown(self, mock_run):
        """When git is not installed (FileNotFoundError), return 'unknown'."""
        from src.utils.repro import get_git_commit
        result = get_git_commit()
        self.assertEqual(result, "unknown")

    @patch(
        "src.utils.repro.subprocess.run",
        side_effect=subprocess.CalledProcessError(128, "git"),
    )
    def test_not_a_repo_returns_unknown(self, mock_run):
        """When not in a git repo (CalledProcessError), return 'unknown'."""
        from src.utils.repro import get_git_commit
        result = get_git_commit()
        self.assertEqual(result, "unknown")


class TestGetHardwareInfo(unittest.TestCase):
    """Tests for get_hardware_info() from src/utils/repro.py."""

    def test_returns_dict(self):
        """get_hardware_info() must return a dict."""
        from src.utils.repro import get_hardware_info
        result = get_hardware_info()
        self.assertIsInstance(result, dict)

    def test_has_expected_keys(self):
        """Result dict must contain 'gpu' and 'gpu_memory' keys."""
        from src.utils.repro import get_hardware_info
        result = get_hardware_info()
        self.assertIn("gpu", result)
        self.assertIn("gpu_memory", result)

    def test_values_are_strings(self):
        """All values in the returned dict must be strings."""
        from src.utils.repro import get_hardware_info
        result = get_hardware_info()
        for key, value in result.items():
            self.assertIsInstance(value, str, f"Value for key '{key}' is not a string")

    @patch("src.utils.repro.torch")
    def test_no_cuda_returns_na(self, mock_torch):
        """When CUDA is not available, gpu and gpu_memory should be 'N/A'."""
        from src.utils.repro import get_hardware_info
        mock_torch.cuda.is_available.return_value = False
        result = get_hardware_info()
        self.assertEqual(result["gpu"], "N/A")
        self.assertEqual(result["gpu_memory"], "N/A")

    @patch("src.utils.repro.torch")
    def test_cuda_available_returns_gpu_info(self, mock_torch):
        """When CUDA is available, gpu and gpu_memory should be populated."""
        from src.utils.repro import get_hardware_info
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_name.return_value = "NVIDIA A100"
        mock_props = MagicMock()
        mock_props.total_memory = 80.0e9  # 80 GB
        mock_torch.cuda.get_device_properties.return_value = mock_props
        result = get_hardware_info()
        self.assertEqual(result["gpu"], "NVIDIA A100")
        self.assertIn("80.0", result["gpu_memory"])


class TestSmokeTestMainCudaUnavailable(unittest.TestCase):
    """TST-037/TST-067: Tests for main() when CUDA is not available.

    Fixed: The original implementation returned main_fn outside the patch.dict
    scope, so mocked modules were already restored when main() ran, causing
    ImportError for transformers.  Now main() is called *inside* the patched
    context.
    """

    def _load_and_run_main(self, cli_args):
        """Load smoke_test.py with fully mocked deps and call main().

        Returns the SystemExit code, or None if main() did not call sys.exit().
        """
        import importlib
        import importlib.util

        mock_torch = MagicMock()
        mock_torch.__version__ = "2.0.0"
        mock_torch.cuda.is_available.return_value = False

        mock_repro = MagicMock()
        mock_repro.get_git_commit.return_value = "abc12345"
        mock_repro.get_hardware_info.return_value = {"gpu": "N/A", "gpu_memory": "N/A"}
        mock_repro.set_seed = MagicMock()

        mock_hf = MagicMock()
        mock_hf.resolve_pretrained_path.return_value = "mock_path"

        mock_config_utils = MagicMock()
        mock_config_utils.ALLOWED_MODEL_IDS = ["Qwen/Qwen2.5-1.5B-Instruct"]

        patched_modules = {
            "torch": mock_torch,
            "torch.nn": MagicMock(),
            "torch.cuda": MagicMock(),
            "transformers": MagicMock(),
            "src": MagicMock(),
            "src.utils": MagicMock(),
            "src.utils.repro": mock_repro,
            "src.utils.hf": mock_hf,
            "scripts": MagicMock(),
            "scripts.config_utils": mock_config_utils,
        }

        scripts_dir = PROJECT_ROOT / "scripts"
        spec = importlib.util.spec_from_file_location(
            "smoke_test_mod",
            str(scripts_dir / "smoke_test.py"),
        )

        with patch.dict("sys.modules", patched_modules):
            with patch("sys.argv", ["smoke_test.py"] + cli_args):
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                # Call main() INSIDE the patched context so mocks are active
                try:
                    mod.main()
                except SystemExit as exc:
                    return exc.code
        return None

    def test_cuda_unavailable_cpu_ok_exits_zero(self):
        """With --cpu-ok and no CUDA, main should call sys.exit(0)."""
        code = self._load_and_run_main(["--cpu-ok"])
        self.assertEqual(code, 0)

    def test_cuda_unavailable_no_cpu_ok_exits_one(self):
        """Without --cpu-ok and no CUDA, main should call sys.exit(1)."""
        code = self._load_and_run_main([])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
