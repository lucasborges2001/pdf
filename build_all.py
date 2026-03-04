#!/usr/bin/env python3
"""_pdf/build_all.py (DEPRECATED)

Compatibilidad histórica. Usar:
  python -m _pdf.build_materia <RUTA_MATERIA>
"""

from __future__ import annotations

from .build_materia import main

if __name__ == "__main__":
    main()
