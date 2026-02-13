from __future__ import annotations

import os
from dataclasses import dataclass


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


@dataclass(frozen=True)
class AppConfig:
    max_pdf_size_mb: int = _get_int_env("PDF_SUITE_MAX_PDF_MB", 50)
    max_batch_size_mb: int = _get_int_env("PDF_SUITE_MAX_BATCH_MB", 100)

    @property
    def max_pdf_size_bytes(self) -> int:
        return self.max_pdf_size_mb * 1024 * 1024

    @property
    def max_batch_size_bytes(self) -> int:
        return self.max_batch_size_mb * 1024 * 1024
