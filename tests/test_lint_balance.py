import unittest
from pathlib import Path
import tempfile

from _pdf.engine.scanlib import lint_txt

class TestLintBalance(unittest.TestCase):
    def test_unclosed_fence(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.txt"
            p.write_text('[DOC title="X"]\n```\ncode\n', encoding="utf-8")
            issues = lint_txt(txt_path=p, materia=None)
            self.assertTrue(any(i.severity == "ERROR" and "```" in i.msg for i in issues))

    def test_callout_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "b.txt"
            p.write_text('[DOC title="X"]\n[NOTE]\nhi\n[/TIP]\n', encoding="utf-8")
            issues = lint_txt(txt_path=p, materia=None)
            self.assertTrue(any(i.severity == "ERROR" and "no matchea" in i.msg for i in issues))

if __name__ == "__main__":
    unittest.main()
