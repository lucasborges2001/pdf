import tempfile
import unittest
from pathlib import Path

import tests._path  # noqa: F401
from tests._tmp import temporary_directory

from _pdf.pipeline.assets import candidate_asset_roots, find_asset


class TestAssetsResolution(unittest.TestCase):
    def test_find_asset_in_txt_dir(self):
        with temporary_directory() as td:
            directory = Path(td)
            (directory / "x.png").write_text("x", encoding="utf-8")
            roots = candidate_asset_roots(txt_dir=directory, materia=None, extra_dirs=[])
            self.assertIsNotNone(find_asset("x.png", roots))


if __name__ == "__main__":
    unittest.main()
