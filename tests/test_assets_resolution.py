import unittest
from pathlib import Path
import tempfile

from _pdf.engine.assets import candidate_asset_roots, find_asset

class TestAssetsResolution(unittest.TestCase):
    def test_find_asset_in_txt_dir(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "x.png").write_text("x", encoding="utf-8")
            roots = candidate_asset_roots(txt_dir=d, materia=None, extra_dirs=[])
            self.assertIsNotNone(find_asset("x.png", roots))

if __name__ == "__main__":
    unittest.main()
