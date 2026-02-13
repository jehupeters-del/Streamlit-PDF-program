from __future__ import annotations

from src.adapters.pymupdf_adapter import PyMuPdfAdapter
from src.domain.models import ExtractionResult
from src.services.question_utils import find_question_numbers, infer_smart_output_name
from src.services.validation_service import ValidationService


class ExtractionService:
    def __init__(self, adapter: PyMuPdfAdapter, validation_service: ValidationService) -> None:
        self.adapter = adapter
        self.validation_service = validation_service

    def extract_questions(self, input_name: str, pdf_bytes: bytes) -> ExtractionResult:
        texts = self.adapter.extract_text_by_page(pdf_bytes)
        keep_pages: set[int] = set()
        found: list[int] = []

        if texts:
            keep_pages.add(0)

        for index, text in enumerate(texts):
            page_questions = find_question_numbers(text)
            if page_questions:
                keep_pages.add(index)
                found.extend(page_questions)

        ordered_pages = sorted(keep_pages)
        output_pdf = self.adapter.build_pdf_from_indices(pdf_bytes, ordered_pages)
        validation = self.validation_service.validate_pdf(pdf_bytes)

        return ExtractionResult(
            output_name=infer_smart_output_name(input_name),
            output_pdf=output_pdf,
            original_pages=len(texts),
            extracted_pages=len(ordered_pages),
            found_questions=sorted(set(found)),
            validation=validation,
        )
