import unittest

from _pdf.format.txtfmt import sanitize_para


class TestInlineCodeProtection(unittest.TestCase):
    def test_code_star_does_not_leak_to_italic(self):
        self.assertEqual(
            sanitize_para("`r*` y *hola*"),
            '<font face="Courier">r*</font> y <i>hola</i>',
        )

    def test_italic_then_code_star(self):
        self.assertEqual(
            sanitize_para("*hola* y `r*`"),
            '<i>hola</i> y <font face="Courier">r*</font>',
        )

    def test_code_keeps_markdown_literal(self):
        self.assertEqual(
            sanitize_para("`**x**`"),
            '<font face="Courier">**x**</font>',
        )

    def test_code_keeps_color_tags_literal(self):
        self.assertEqual(
            sanitize_para("`[c=red]x[/c]`"),
            '<font face="Courier">[c=red]x[/c]</font>',
        )

    def test_code_keeps_link_literal(self):
        self.assertEqual(
            sanitize_para("`[a](https://example.com)`"),
            '<font face="Courier">[a](https://example.com)</font>',
        )


if __name__ == "__main__":
    unittest.main()
