import pytest

from src.adapters.pymupdf_adapter import PyMuPdfAdapter
from src.services.batch_service import BatchService
from src.services.extraction_service import ExtractionService
from src.services.validation_service import ValidationService


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
