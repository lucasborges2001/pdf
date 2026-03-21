import importlib.util
import unittest
from pathlib import Path

import tests._path  # noqa: F401

REPORTLAB_AVAILABLE = importlib.util.find_spec("reportlab") is not None
if REPORTLAB_AVAILABLE:
    from reportlab.platypus import ListFlowable, Paragraph

    from _pdf.parser.flowables import txt_to_flowables
    from _pdf.runtime.core import PdfTheme
    from _pdf.runtime.ctx import PdfCtx


@unittest.skipUnless(REPORTLAB_AVAILABLE, "reportlab no está instalado")
class TestHeadingListDisambiguation(unittest.TestCase):
    def setUp(self):
        self.ctx = PdfCtx(PdfTheme())

    def _parse(self, text: str):
        return txt_to_flowables(
            self.ctx,
            text,
            resolve_pdf=lambda _: Path("dummy.pdf"),
        )

    def test_simple_numeric_section_heading_is_preserved(self):
        story = self._parse("1. INTRODUCCIÓN\nTexto base")
        self.assertGreaterEqual(len(story), 2)
        self.assertIsInstance(story[0], Paragraph)
        self.assertTrue(getattr(story[0], "_fbd_is_heading", False))

    def test_simple_numeric_items_are_ordered_list(self):
        story = self._parse(
            "1. Ejecución de programas: cargar, iniciar y terminar.\n"
            "2. Operaciones de E/S: acceso controlado a dispositivos."
        )
        self.assertEqual(len(story), 1)
        self.assertIsInstance(story[0], ListFlowable)

    def test_hierarchical_numeric_heading_is_heading(self):
        story = self._parse("2.1. Procesos")
        self.assertEqual(len(story), 1)
        self.assertIsInstance(story[0], Paragraph)
        self.assertTrue(getattr(story[0], "_fbd_is_heading", False))


if __name__ == "__main__":
    unittest.main()
