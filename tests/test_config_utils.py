"""TST-053: Unit tests for scripts/config_utils.py — load_config error paths
and shared IO helpers (split_csv, read_json, read_text)."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) in sys.path:
    sys.path.remove(str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from config_utils import load_config, read_json, read_text, split_csv  # noqa: E402


# ---------------------------------------------------------------------------
# TST-053: load_config error paths
# ---------------------------------------------------------------------------


class TestLoadConfigErrorPaths(unittest.TestCase):
    """Verify load_config raises on empty, non-dict, and missing files,
    and returns a dict for valid YAML."""

    def test_empty_file_raises_value_error(self):
        """An empty YAML file (yaml.safe_load returns None) must raise ValueError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("")  # completely empty
            tmp_path = f.name
        try:
            with self.assertRaises(ValueError) as ctx:
                load_config(tmp_path)
            self.assertIn("empty", str(ctx.exception).lower())
        finally:
            os.unlink(tmp_path)

    def test_comment_only_file_raises_value_error(self):
        """A file with only YAML comments (safe_load returns None) must raise ValueError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("# just a comment\n# another comment\n")
            tmp_path = f.name
        try:
            with self.assertRaises(ValueError):
                load_config(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_non_dict_top_level_raises_value_error(self):
        """A YAML file whose top-level is a list (not a mapping) must raise ValueError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("- item1\n- item2\n")
            tmp_path = f.name
        try:
            with self.assertRaises(ValueError) as ctx:
                load_config(tmp_path)
            self.assertIn("mapping", str(ctx.exception).lower())
        finally:
            os.unlink(tmp_path)

    def test_scalar_top_level_raises_value_error(self):
        """A YAML file whose top-level is a scalar must raise ValueError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("42\n")
            tmp_path = f.name
        try:
            with self.assertRaises(ValueError):
                load_config(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_valid_yaml_returns_dict(self):
        """A valid YAML mapping must be returned as a dict."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("project:\n  model_id: test-model\nruntime:\n  seed: 42\n")
            tmp_path = f.name
        try:
            result = load_config(tmp_path)
            self.assertIsInstance(result, dict)
            self.assertIn("project", result)
            self.assertEqual(result["project"]["model_id"], "test-model")
            self.assertEqual(result["runtime"]["seed"], 42)
        finally:
            os.unlink(tmp_path)

    def test_nonexistent_file_raises_file_not_found_error(self):
        """Loading from a path that does not exist must raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_config("/tmp/_nonexistent_yaml_file_that_does_not_exist_12345.yaml")


# ---------------------------------------------------------------------------
# TST-053: split_csv tests
# ---------------------------------------------------------------------------


class TestSplitCSV(unittest.TestCase):
    """Tests for the split_csv shared helper."""

    def test_normal_csv(self):
        result = split_csv("a,b,c")
        self.assertEqual(result, ["a", "b", "c"])

    def test_csv_with_whitespace(self):
        result = split_csv(" a , b , c ")
        self.assertEqual(result, ["a", "b", "c"])

    def test_none_returns_empty(self):
        result = split_csv(None)
        self.assertEqual(result, [])

    def test_empty_string_returns_empty(self):
        result = split_csv("")
        self.assertEqual(result, [])

    def test_single_item(self):
        result = split_csv("only_one")
        self.assertEqual(result, ["only_one"])

    def test_trailing_comma_no_empty_tokens(self):
        """Trailing commas should not produce empty strings."""
        result = split_csv("a,b,")
        self.assertEqual(result, ["a", "b"])

    def test_multiple_commas_no_empty_tokens(self):
        """Multiple consecutive commas should not produce empty strings."""
        result = split_csv("a,,b,,,c")
        self.assertEqual(result, ["a", "b", "c"])


# ---------------------------------------------------------------------------
# TST-053: read_json tests
# ---------------------------------------------------------------------------


class TestReadJson(unittest.TestCase):
    """Tests for the read_json shared helper."""

    def test_valid_json_dict(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump({"key": "value", "num": 42}, f)
            tmp_path = f.name
        try:
            result = read_json(Path(tmp_path))
            self.assertIsInstance(result, dict)
            self.assertEqual(result["key"], "value")
            self.assertEqual(result["num"], 42)
        finally:
            os.unlink(tmp_path)

    def test_nonexistent_file_returns_none(self):
        result = read_json(Path("/tmp/_nonexistent_json_file_12345.json"))
        self.assertIsNone(result)

    def test_non_dict_json_returns_none(self):
        """A JSON file containing a list (not a dict) must return None."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump([1, 2, 3], f)
            tmp_path = f.name
        try:
            result = read_json(Path(tmp_path))
            self.assertIsNone(result)
        finally:
            os.unlink(tmp_path)

    def test_invalid_json_returns_none(self):
        """Malformed JSON content must return None (not raise)."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("{invalid json content!!!}")
            tmp_path = f.name
        try:
            result = read_json(Path(tmp_path))
            self.assertIsNone(result)
        finally:
            os.unlink(tmp_path)

    def test_empty_file_returns_none(self):
        """An empty JSON file must return None (JSONDecodeError)."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("")
            tmp_path = f.name
        try:
            result = read_json(Path(tmp_path))
            self.assertIsNone(result)
        finally:
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# TST-053: read_text tests
# ---------------------------------------------------------------------------


class TestReadText(unittest.TestCase):
    """Tests for the read_text shared helper."""

    def test_valid_text_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("hello world\n")
            tmp_path = f.name
        try:
            result = read_text(Path(tmp_path))
            self.assertEqual(result, "hello world\n")
        finally:
            os.unlink(tmp_path)

    def test_nonexistent_file_returns_empty(self):
        result = read_text(Path("/tmp/_nonexistent_text_file_12345.txt"))
        self.assertEqual(result, "")

    def test_empty_file_returns_empty(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("")
            tmp_path = f.name
        try:
            result = read_text(Path(tmp_path))
            self.assertEqual(result, "")
        finally:
            os.unlink(tmp_path)

    def test_binary_content_uses_replacement(self):
        """Non-UTF-8 bytes should be replaced with U+FFFD, not raise."""
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".txt", delete=False
        ) as f:
            # Write valid UTF-8 + invalid byte sequence
            f.write(b"hello \xff\xfe world\n")
            tmp_path = f.name
        try:
            result = read_text(Path(tmp_path))
            # Should not raise, and should contain replacement characters
            self.assertIn("\ufffd", result)
            self.assertIn("hello", result)
            self.assertIn("world", result)
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
