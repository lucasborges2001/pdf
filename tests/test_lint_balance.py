import unittest
from pathlib import Path

import tests._path  # noqa: F401
from tests._tmp import temporary_directory

from _pdf.pipeline.scan import lint_txt


class TestLintBalance(unittest.TestCase):
    def test_unclosed_fence(self):
        with temporary_directory() as td:
            path = Path(td) / "a.txt"
            path.write_text('[DOC title="X"]\n```\ncode\n', encoding="utf-8")
            issues = lint_txt(txt_path=path, materia=None)
            self.assertTrue(any(issue.severity == "ERROR" and "```" in issue.msg for issue in issues))

    def test_callout_mismatch(self):
        with temporary_directory() as td:
            path = Path(td) / "b.txt"
            path.write_text('[DOC title="X"]\n[NOTE]\nhi\n[/TIP]\n', encoding="utf-8")
            issues = lint_txt(txt_path=path, materia=None)
            self.assertTrue(any(issue.severity == "ERROR" and "no matchea" in issue.msg for issue in issues))

    def test_missing_title_is_reported_early(self):
        with temporary_directory() as td:
            path = Path(td) / "c.txt"
            path.write_text('[DOC include_toc=true]\nContenido\n', encoding="utf-8")
            issues = lint_txt(txt_path=path, materia=None)
            self.assertTrue(any(issue.severity == "ERROR" and "debe incluir title" in issue.msg for issue in issues))


if __name__ == "__main__":
    unittest.main()
