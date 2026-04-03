"""TST-073: Centralized pytest configuration for the test suite.

Provides unified sys.path setup so individual test files do not need to
maintain their own path injection variants.
"""

import sys
from pathlib import Path

# Project layout:
#   tests/conftest.py  ->  tests/ is one level below project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Ensure project root, src/, and scripts/ are importable
for _p in (str(PROJECT_ROOT), str(SRC_DIR), str(SCRIPTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
