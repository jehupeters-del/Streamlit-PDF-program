import pytest

from src.adapters.pymupdf_adapter import PyMuPdfAdapter
from src.infrastructure.config import AppConfig
from src.services.batch_service import BatchService
from src.services.extraction_service import ExtractionService
from src.services.merge_service import MergeService
from src.services.validation_service import ValidationService
from src.services.workspace_service import WorkspaceService


@pytest.mark.integration
def test_adapter_reads_real_world_fixtures(real_world_fixture_paths) -> None:
    adapter = PyMuPdfAdapter()
    for path in real_world_fixture_paths:
        content = path.read_bytes()
        assert adapter.get_page_count(content) > 0
        texts = adapter.extract_text_by_page(content)
        assert len(texts) > 0


@pytest.mark.integration
def test_batch_extraction_and_csv_report(real_world_fixture_paths) -> None:
    adapter = PyMuPdfAdapter()
    validation = ValidationService(adapter)
    extraction = ExtractionService(adapter, validation)
    batch = BatchService(extraction, validation)

    files = [(path.name, path.read_bytes()) for path in real_world_fixture_paths]

    extraction_result = batch.run_extraction_batch(files)
    assert len(extraction_result.items) == len(files)

    zip_name, zip_bytes = batch.build_zip(extraction_result)
    assert zip_name.endswith(".zip")
    assert len(zip_bytes) > 0

    validation_result = batch.run_validation_batch(files)
    csv_name, csv_bytes = batch.build_validation_csv(validation_result)
    assert csv_name.endswith(".csv")
    assert b"source_name,status" in csv_bytes


@pytest.mark.integration
def test_output_size_regression_guard(real_world_fixture_paths) -> None:
    adapter = PyMuPdfAdapter()
    validation = ValidationService(adapter)
    extraction = ExtractionService(adapter, validation)
    merge = MergeService(adapter)
    workspace = WorkspaceService(adapter, AppConfig(max_pdf_size_mb=50, max_batch_size_mb=100))

    source_path = real_world_fixture_paths[0]
    source_bytes = source_path.read_bytes()

    extracted = extraction.extract_questions(source_path.name, source_bytes)
    assert len(extracted.output_pdf) <= int(len(source_bytes) * 1.5)

    loaded = workspace.load_files([(source_path.name, source_bytes)])
    refs = workspace.initial_page_refs(loaded)
    merged = merge.merge(loaded, refs)
    assert len(merged.output_pdf) <= int(len(source_bytes) * 1.5)
