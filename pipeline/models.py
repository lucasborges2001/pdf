from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple


@dataclass(frozen=True)
class BuildJob:
    txt_path: Path
    area: str
    out_dirs: Tuple[Path, ...]
    out_name: str


@dataclass(frozen=True)
class Issue:
    severity: str
    file: Path
    line: int
    msg: str

    def fmt(self) -> str:
        return f"[{self.severity}] {self.file}:{self.line}  {self.msg}"


@dataclass(frozen=True)
class ScanFileResult:
    path: Path
    issues: List[Issue]

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "ERROR")

    @property
    def warn_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "WARN")


@dataclass(frozen=True)
class ScanReport:
    scanned_files: List[ScanFileResult]
    txt_total: int = 0
    txt_candidates: int = 0
    skipped_files: List[Path] = field(default_factory=list)

    @property
    def files(self) -> int:
        return len(self.scanned_files)

    @property
    def errors(self) -> int:
        return sum(result.error_count for result in self.scanned_files)

    @property
    def warns(self) -> int:
        return sum(result.warn_count for result in self.scanned_files)
