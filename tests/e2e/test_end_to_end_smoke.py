import pytest

from src.adapters.pymupdf_adapter import PyMuPdfAdapter
from src.infrastructure.config import AppConfig
from src.services.batch_service import BatchService
from src.services.extraction_service import ExtractionService
from src.services.merge_service import MergeService
from src.services.validation_service import ValidationService
from src.services.workspace_service import WorkspaceService


@pytest.mark.e2e
def test_service_level_e2e_smoke(synthetic_pdf_bytes: bytes) -> None:
    adapter = PyMuPdfAdapter()
    config = AppConfig(max_pdf_size_mb=50, max_batch_size_mb=100)

    workspace = WorkspaceService(adapter, config)
    validation = ValidationService(adapter)
    extraction = ExtractionService(adapter, validation)
    merge = MergeService(adapter)
    batch = BatchService(extraction, validation)

    loaded = workspace.load_files([("sample.pdf", synthetic_pdf_bytes)])
    refs = workspace.initial_page_refs(loaded)
    merged = merge.merge(loaded, refs)
    assert adapter.get_page_count(merged.output_pdf) == 3

    extraction_result = extraction.extract_questions("sample.pdf", synthetic_pdf_bytes)
    assert extraction_result.extracted_pages >= 1

    validation_result = validation.validate_pdf(synthetic_pdf_bytes)
    assert validation_result.max_question == 4

    batch_result = batch.run_validation_batch([("sample.pdf", synthetic_pdf_bytes)])
    assert len(batch_result.items) == 1
