import unittest
from _pdf.engine.docheader import parse_doc_header

class TestDocHeader(unittest.TestCase):
    def test_parse_simple(self):
        text = '[DOC title="Hola" include_toc=true toc_max_level=2]\n\nBody'
        attrs, unknown, rest, err = parse_doc_header(text)
        self.assertIsNone(err)
        self.assertEqual(attrs["title"], "Hola")
        self.assertEqual(attrs["include_toc"], True)
        self.assertEqual(attrs["toc_max_level"], 2)
        self.assertEqual(unknown, [])
        self.assertIn("Body", rest)

    def test_unknown_keys_warn(self):
        text = '[DOC foo="bar" title="X"]\n'
        attrs, unknown, rest, err = parse_doc_header(text)
        self.assertIsNone(err)
        self.assertIn("foo", unknown)
        self.assertEqual(attrs["foo"], "bar")

    def test_bad_shlex(self):
        text = '[DOC title="unterminated]\n'
        attrs, unknown, rest, err = parse_doc_header(text)
        self.assertIsNotNone(err)

if __name__ == "__main__":
    unittest.main()
