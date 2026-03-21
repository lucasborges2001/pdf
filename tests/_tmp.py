from __future__ import annotations

import tempfile
from pathlib import Path

TMP_ROOT = Path(__file__).resolve().parents[1] / ".tmp_tests"
TMP_ROOT.mkdir(exist_ok=True)


def temporary_directory():
    return tempfile.TemporaryDirectory(dir=TMP_ROOT)
