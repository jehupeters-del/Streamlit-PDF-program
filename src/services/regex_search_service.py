from __future__ import annotations

import re
from pathlib import Path

from src.adapters.pymupdf_adapter import PyMuPdfAdapter
from src.domain.errors import ValidationError
from src.domain.models import (
    BatchItemResult,
    BatchOperationResult,
    OperationMessage,
    RegexPageMatch,
    RegexSearchResult,
    Status,
)


class RegexSearchService:
    def __init__(self, adapter: PyMuPdfAdapter) -> None:
        self.adapter = adapter

    @staticmethod
    def _compile_pattern(pattern: str, case_sensitive: bool) -> re.Pattern[str]:
        cleaned = pattern.strip()
        if not cleaned:
            raise ValidationError("Enter a regex pattern.")

        flags = re.MULTILINE
        if not case_sensitive:
            flags |= re.IGNORECASE

        try:
            return re.compile(cleaned, flags)
        except re.error as exc:
            raise ValidationError(f"Invalid regex pattern: {exc}") from exc

    @staticmethod
    def _snippet(text: str, match: re.Match[str], radius: int = 70) -> str:
        start = max(0, match.start() - radius)
        end = min(len(text), match.end() + radius)
        raw = text[start:end]
        normalized = re.sub(r"\s+", " ", raw).strip()
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
        return f"{prefix}{normalized}{suffix}"

    @staticmethod
    def _output_name(input_name: str) -> str:
        stem = Path(input_name).stem
        safe_stem = re.sub(r"[^A-Za-z0-9._() -]", "_", stem).strip() or "output"
        return f"{safe_stem}_regex_extract.pdf"

    def extract_matching_pages(
        self,
        input_name: str,
        pdf_bytes: bytes,
        pattern: str,
        case_sensitive: bool,
        keep_first_page: bool,
    ) -> RegexSearchResult:
        regex = self._compile_pattern(pattern, case_sensitive)
        texts = self.adapter.extract_text_by_page(pdf_bytes)

        keep_indices: set[int] = set()
        if texts and keep_first_page:
            keep_indices.add(0)

        matched_pages: list[int] = []
        page_matches: list[RegexPageMatch] = []

        for index, text in enumerate(texts):
            matches = list(regex.finditer(text))
            if not matches:
                continue
            keep_indices.add(index)
            matched_pages.append(index + 1)
            page_matches.append(
                RegexPageMatch(
                    page_number=index + 1,
                    match_count=len(matches),
                    snippet=self._snippet(text, matches[0]),
                )
            )

        if not keep_indices:
            raise ValidationError("No pages matched the regex pattern.")

        ordered_pages = sorted(keep_indices)
        output_pdf = self.adapter.build_pdf_from_indices(pdf_bytes, ordered_pages)

        return RegexSearchResult(
            output_name=self._output_name(input_name),
            output_pdf=output_pdf,
            original_pages=len(texts),
            extracted_pages=len(ordered_pages),
            matched_pages=matched_pages,
            matches=page_matches,
        )

    def run_batch_extraction(
        self,
        files: list[tuple[str, bytes]],
        pattern: str,
        case_sensitive: bool,
        keep_first_page: bool,
    ) -> BatchOperationResult:
        items: list[BatchItemResult] = []

        for file_name, file_bytes in files:
            try:
                result = self.extract_matching_pages(
                    input_name=file_name,
                    pdf_bytes=file_bytes,
                    pattern=pattern,
                    case_sensitive=case_sensitive,
                    keep_first_page=keep_first_page,
                )
                messages: list[OperationMessage] = [
                    OperationMessage(
                        level="info",
                        text=(
                            f"Matched {len(result.matched_pages)} page(s); "
                            f"extracted {result.extracted_pages} page(s)."
                        ),
                    )
                ]
                if not result.matched_pages and keep_first_page:
                    messages.append(
                        OperationMessage(
                            level="warning",
                            text="No regex match found; output includes first page only.",
                        )
                    )

                status = Status.SUCCESS if result.matched_pages else Status.WARNING
                items.append(
                    BatchItemResult(
                        source_name=file_name,
                        status=status,
                        messages=messages,
                        metrics={
                            "original_pages": result.original_pages,
                            "matched_pages": len(result.matched_pages),
                            "extracted_pages": result.extracted_pages,
                        },
                        artifact_name=result.output_name,
                        artifact_bytes=result.output_pdf,
                    )
                )
            except Exception as exc:
                items.append(
                    BatchItemResult(
                        source_name=file_name,
                        status=Status.ERROR,
                        messages=[OperationMessage(level="error", text=str(exc))],
                    )
                )

        return BatchOperationResult(items=items)
