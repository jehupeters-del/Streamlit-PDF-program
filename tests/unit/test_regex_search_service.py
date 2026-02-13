import pytest

from src.adapters.pymupdf_adapter import PyMuPdfAdapter
from src.domain.errors import ValidationError
from src.services.regex_search_service import RegexSearchService


@pytest.mark.unit
def test_regex_single_extract_matches_pages(synthetic_pdf_bytes: bytes) -> None:
    adapter = PyMuPdfAdapter()
    service = RegexSearchService(adapter)

    result = service.extract_matching_pages(
        input_name="sample.pdf",
        pdf_bytes=synthetic_pdf_bytes,
        pattern=r"question",
        case_sensitive=False,
        keep_first_page=True,
    )

    assert result.original_pages == 3
    assert result.matched_pages == [2, 3]
    assert result.extracted_pages == 3
    assert adapter.get_page_count(result.output_pdf) == 3
    assert result.output_name.endswith("_regex_extract_question.pdf")
    assert result.matches[0].matched_text.lower() == "question"


@pytest.mark.unit
def test_regex_single_extract_without_keep_first(synthetic_pdf_bytes: bytes) -> None:
    adapter = PyMuPdfAdapter()
    service = RegexSearchService(adapter)

    result = service.extract_matching_pages(
        input_name="sample.pdf",
        pdf_bytes=synthetic_pdf_bytes,
        pattern=r"question",
        case_sensitive=False,
        keep_first_page=False,
    )

    assert result.matched_pages == [2, 3]
    assert result.extracted_pages == 2
    assert adapter.get_page_count(result.output_pdf) == 2


@pytest.mark.unit
def test_regex_invalid_pattern_raises_validation_error(synthetic_pdf_bytes: bytes) -> None:
    adapter = PyMuPdfAdapter()
    service = RegexSearchService(adapter)

    with pytest.raises(ValidationError):
        service.extract_matching_pages(
            input_name="sample.pdf",
            pdf_bytes=synthetic_pdf_bytes,
            pattern="(",
            case_sensitive=False,
            keep_first_page=True,
        )


@pytest.mark.unit
def test_regex_batch_extraction_produces_artifacts(synthetic_pdf_bytes: bytes) -> None:
    adapter = PyMuPdfAdapter()
    service = RegexSearchService(adapter)

    batch = service.run_batch_extraction(
        files=[("sample_a.pdf", synthetic_pdf_bytes), ("sample_b.pdf", synthetic_pdf_bytes)],
        pattern=r"question",
        case_sensitive=False,
        keep_first_page=True,
    )

    assert len(batch.items) == 2
    assert all(item.artifact_bytes for item in batch.items)
    assert all(item.artifact_name for item in batch.items)
