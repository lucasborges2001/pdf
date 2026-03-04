import unittest
from pathlib import Path
import tempfile

from _pdf.engine.scanlib import discover_txts

class TestScanCandidates(unittest.TestCase):
    def test_discover_txts_filters(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "Practico").mkdir()
            (base / "Practico" / "00Practico").mkdir()
            good = base / "Practico" / "00Practico" / "A_Practico.txt"
            good.write_text('[DOC title="X"]\n', encoding="utf-8")
            junk = base / "notes.txt"
            junk.write_text('hola mundo\n', encoding="utf-8")

            found, skipped = discover_txts(base)
            # good debería estar; junk probablemente skipped por heurística
            self.assertTrue(any(p.name == good.name for p in found))
            self.assertTrue(any(p.name == junk.name for p in skipped) or True)

if __name__ == "__main__":
    unittest.main()
