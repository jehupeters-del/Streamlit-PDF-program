from __future__ import annotations

from src.adapters.pymupdf_adapter import PyMuPdfAdapter
from src.domain.models import ValidationResult
from src.services.question_utils import find_question_numbers, validate_sequence


class ValidationService:
    def __init__(self, adapter: PyMuPdfAdapter) -> None:
        self.adapter = adapter

    def validate_pdf(self, pdf_bytes: bytes) -> ValidationResult:
        texts = self.adapter.extract_text_by_page(pdf_bytes)
        found: list[int] = []
        for text in texts:
            found.extend(find_question_numbers(text))

        is_valid, max_question, missing = validate_sequence(found)
        return ValidationResult(
            found_questions=sorted(set(found)),
            max_question=max_question,
            missing_questions=missing,
            is_valid=is_valid,
        )
