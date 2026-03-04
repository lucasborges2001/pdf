#!/usr/bin/env python3
"""_pdf/help.py

Solo imprime cómo usar los comandos del paquete en un formato legible.
(no escanea, no genera PDFs)
"""

from __future__ import annotations

import argparse
from typing import Optional

from .term.flags import add_common_flags, console_from_args
from .term.printers import print_help


def main(argv: Optional[list[str]] = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m _pdf.help", description="Lista comandos y flags de _pdf.")
    # flags de presentación (no tiene sentido max-issues aquí)
    add_common_flags(ap, include_limits=False)
    args = ap.parse_args(argv)

    c = console_from_args(args)
    print_help(c)


if __name__ == "__main__":
    main()
