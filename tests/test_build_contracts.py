import unittest
from pathlib import Path

import tests._path  # noqa: F401

from _pdf.parser.header import parse_doc_header_result
from _pdf.pipeline.compile import build_doc_spec, build_error_for_header
from _pdf.pipeline.errors import PdfBuildError


class TestBuildContracts(unittest.TestCase):
    def test_missing_header_is_rejected_before_docspec(self):
        header = parse_doc_header_result("Texto suelto\n")
        err = build_error_for_header(Path("doc.txt"), header)
        self.assertIn("Falta header", err or "")

    def test_missing_title_is_rejected_before_docspec(self):
        header = parse_doc_header_result('[DOC include_toc=true]\nBody')
        err = build_error_for_header(Path("doc.txt"), header)
        self.assertIn("debe incluir title", err or "")

    def test_unknown_keys_do_not_break_docspec_construction(self):
        header = parse_doc_header_result('[DOC title="Hola" foo="bar"]\nBody')
        spec = build_doc_spec(source_path=Path("doc.txt"), out_path=Path("doc.pdf"), header=header)
        self.assertEqual(spec.title, "Hola")
        self.assertFalse(hasattr(spec, "foo"))

    def test_invalid_header_raises_build_error(self):
        header = parse_doc_header_result('[DOC title="Hola"\nBody')
        with self.assertRaises(PdfBuildError):
            build_doc_spec(source_path=Path("doc.txt"), out_path=Path("doc.pdf"), header=header)


if __name__ == "__main__":
    unittest.main()
