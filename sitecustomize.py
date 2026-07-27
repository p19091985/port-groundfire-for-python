from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
PYTHON_VERSION_DIR = ROOT_DIR / "versao-python"

if (PYTHON_VERSION_DIR / "src").exists():
    python_version_path = str(PYTHON_VERSION_DIR)
    if python_version_path not in sys.path:
        sys.path.insert(0, python_version_path)
