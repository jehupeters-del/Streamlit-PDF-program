import pytest

from src.domain.models import BatchItemResult, BatchOperationResult, OperationMessage, Status
from src.services.batch_service import BatchService


@pytest.mark.unit
def test_validation_text_summary_contains_counts_and_items() -> None:
    result = BatchOperationResult(
        items=[
            BatchItemResult(
                source_name="a.pdf",
                status=Status.SUCCESS,
                messages=[OperationMessage(level="info", text="ok")],
                metrics={"max_question": 2},
            ),
            BatchItemResult(
                source_name="b.pdf",
                status=Status.WARNING,
                messages=[OperationMessage(level="warning", text="missing 3")],
                metrics={"missing_questions": "3"},
            ),
        ]
    )

    name, text = BatchService.build_validation_text_summary(result)
    assert name.endswith(".txt")
    assert "success=1" in text
    assert "[SUCCESS] a.pdf" in text
    assert "[WARNING] b.pdf" in text


@pytest.mark.unit
def test_safe_artifact_name_strips_paths() -> None:
    sanitized = BatchService._safe_artifact_name("../../unsafe\\path/evil?.pdf")
    assert "/" not in sanitized
    assert "\\" not in sanitized
    assert "?" not in sanitized


@pytest.mark.unit
def test_build_zip_avoids_name_collisions() -> None:
    result = BatchOperationResult(
        items=[
            BatchItemResult(
                source_name="a.pdf",
                status=Status.SUCCESS,
                artifact_name="January 2019 solutions.pdf",
                artifact_bytes=b"A",
            ),
            BatchItemResult(
                source_name="b.pdf",
                status=Status.SUCCESS,
                artifact_name="January 2019 solutions.pdf",
                artifact_bytes=b"B",
            ),
        ]
    )

    _, zip_bytes = BatchService.build_zip(result)
    import io
    import zipfile

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as archive:
        names = archive.namelist()
        assert "January 2019 solutions.pdf" in names
        assert "January 2019 solutions (2).pdf" in names
