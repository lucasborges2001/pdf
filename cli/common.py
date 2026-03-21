from __future__ import annotations

from typing import List, Optional


def normalize_path_argv(argv: Optional[List[str]], *, flag: str) -> Optional[List[str]]:
    if not argv:
        return argv
    if argv and not argv[0].startswith("-"):
        return [flag, argv[0], *argv[1:]]
    return argv
