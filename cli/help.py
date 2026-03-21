from __future__ import annotations

import argparse
from typing import Optional

from ..term.flags import add_common_flags, console_from_args
from ..term.printers import print_help


def main(argv: Optional[list[str]] = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m _pdf.help", description="Lista comandos y flags de _pdf.")
    add_common_flags(ap, include_limits=False)
    args = ap.parse_args(argv)
    print_help(console_from_args(args))
