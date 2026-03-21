import unittest
from pathlib import Path

import tests._path  # noqa: F401
from tests._tmp import temporary_directory

from _pdf.pipeline.discovery import discover_txt_inventory


class TestScanCandidates(unittest.TestCase):
    def test_discover_txt_inventory_filters(self):
        with temporary_directory() as td:
            base = Path(td)
            (base / "Practico").mkdir()
            (base / "Practico" / "00Practico").mkdir()
            good = base / "Practico" / "00Practico" / "A_Practico.txt"
            good.write_text('[DOC title="X"]\n', encoding="utf-8")
            junk = base / "notes.txt"
            junk.write_text("hola mundo\n", encoding="utf-8")

            discovery = discover_txt_inventory(base)
            self.assertTrue(any(path.name == good.name for path in discovery.candidates))
            self.assertTrue(any(path.name == junk.name for path in discovery.skipped))


if __name__ == "__main__":
    unittest.main()
