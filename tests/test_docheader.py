import unittest

import tests._path  # noqa: F401

from _pdf.parser.header import parse_doc_header, parse_doc_header_result


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
        attrs, unknown, _rest, err = parse_doc_header(text)
        self.assertIsNone(err)
        self.assertIn("foo", unknown)
        self.assertEqual(attrs["foo"], "bar")

    def test_bad_shlex(self):
        text = '[DOC title="unterminated]\n'
        _attrs, _unknown, _rest, err = parse_doc_header(text)
        self.assertIsNotNone(err)

    def test_invalid_header_without_closing_bracket(self):
        result = parse_doc_header_result('[DOC title="Hola"\nBody')
        self.assertTrue(result.has_header)
        self.assertIsNotNone(result.error)

    def test_missing_title_is_detectable(self):
        result = parse_doc_header_result('[DOC include_toc=true]\nBody')
        self.assertTrue(result.has_header)
        self.assertNotIn("title", result.attrs)


if __name__ == "__main__":
    unittest.main()
