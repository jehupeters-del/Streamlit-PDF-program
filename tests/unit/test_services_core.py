import pytest

from src.adapters.pymupdf_adapter import PyMuPdfAdapter
from src.infrastructure.config import AppConfig
from src.services.extraction_service import ExtractionService
from src.services.merge_service import MergeService
from src.services.validation_service import ValidationService
from src.services.workspace_service import WorkspaceService


@pytest.mark.unit
def test_validation_service_detects_missing(synthetic_pdf_bytes: bytes) -> None:
    adapter = PyMuPdfAdapter()
    service = ValidationService(adapter)

    result = service.validate_pdf(synthetic_pdf_bytes)

    assert result.max_question == 4
    assert result.missing_questions == [3]
    assert not result.is_valid


@pytest.mark.unit
def test_extraction_service_keeps_cover_and_question_pages(synthetic_pdf_bytes: bytes) -> None:
    adapter = PyMuPdfAdapter()
    validation_service = ValidationService(adapter)
    extraction_service = ExtractionService(adapter, validation_service)

    result = extraction_service.extract_questions("january_2025_input.pdf", synthetic_pdf_bytes)

    assert result.output_name == "January 2025 solutions.pdf"
    assert result.original_pages == 3
    assert result.extracted_pages == 3
    assert result.found_questions == [1, 2, 4]


@pytest.mark.unit
def test_workspace_and_merge_flow(synthetic_pdf_bytes: bytes) -> None:
    adapter = PyMuPdfAdapter()
    config = AppConfig(max_pdf_size_mb=50, max_batch_size_mb=100)
    workspace = WorkspaceService(adapter, config)
    merge = MergeService(adapter)

    loaded = workspace.load_files([("sample.pdf", synthetic_pdf_bytes)])
    refs = workspace.initial_page_refs(loaded)
    refs = workspace.remove_single_page(refs, loaded[0].file_id, 1)

    merged = merge.merge(loaded, refs)

    assert merged.merged_pages == 2
    assert adapter.get_page_count(merged.output_pdf) == 2
