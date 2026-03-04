"""Terminal output utilities for _pdf CLI.

This package centralizes all terminal formatting, colors, tables and printers.
"""

from .console import Console, ConsoleOpts
from .printers import (
    print_help,
    print_scan_report,
    print_build_summary,
)
from .flags import add_common_flags, console_from_args, verbosity_from_args
