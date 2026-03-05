import tempfile
import unittest
from pathlib import Path

from _pdf.engine.materia import discover_jobs


class TestBuildMateriaJobs(unittest.TestCase):
    def test_discovers_txt_directly_under_area_and_mirrors_output(self):
        with tempfile.TemporaryDirectory() as td:
            materia = Path(td) / "TL"
            (materia / "Practico").mkdir(parents=True)
            (materia / "Practico" / "01Practico").mkdir(parents=True)

            direct_txt = materia / "Practico" / "Guia.txt"
            nested_txt = materia / "Practico" / "01Practico" / "01Practico.txt"

            direct_txt.write_text('[DOC title="Guia"]\nContenido\n', encoding='utf-8')
            nested_txt.write_text('[DOC title="P1"]\nContenido\n', encoding='utf-8')

            jobs = discover_jobs(materia, area="practico")
            by_name = {job.txt_path.name: job for job in jobs}

            self.assertIn("Guia.txt", by_name)
            self.assertIn("01Practico.txt", by_name)

            guia_job = by_name["Guia.txt"]
            self.assertEqual(
                guia_job.out_dirs,
                (materia / "Resumenes" / "Practico", materia / "Practico"),
            )
            self.assertEqual(guia_job.out_name, "Guia.pdf")

            nested_job = by_name["01Practico.txt"]
            self.assertEqual(
                nested_job.out_dirs,
                (materia / "Resumenes" / "Practico", materia / "Practico" / "01Practico"),
            )
            self.assertEqual(nested_job.out_name, "01Practico.pdf")


if __name__ == "__main__":
    unittest.main()
