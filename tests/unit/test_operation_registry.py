import pytest

from src.domain.models import (
    OperationContext,
    OperationInput,
    OperationMessage,
    OperationResult,
    Status,
    WorkspaceFile,
)
from src.services.operation_registry import OperationRegistry


@pytest.mark.unit
def test_operation_registry_register_run_and_has() -> None:
    registry = OperationRegistry(_operations={})

    def handler(operation_input: OperationInput) -> OperationResult:
        return OperationResult(
            status=Status.SUCCESS,
            messages=[OperationMessage(level="info", text=operation_input.context.operation_name)],
            metrics={"count": len(operation_input.files)},
        )

    registry.register("validate", handler)
    assert registry.has("validate")

    operation_input = OperationInput(
        files=[
            WorkspaceFile(
                file_id="1",
                name="a.pdf",
                size_bytes=10,
                page_count=1,
                content=b"x",
            )
        ],
        options={"strict": True},
        context=OperationContext(session_id="s1", operation_name="validate"),
    )

    result = registry.run("validate", operation_input)
    assert result.status == Status.SUCCESS
    assert result.metrics["count"] == 1


@pytest.mark.unit
def test_operation_registry_missing_operation_raises() -> None:
    registry = OperationRegistry(_operations={})
    with pytest.raises(KeyError):
        registry.run(
            "missing",
            OperationInput(
                files=[],
                options={},
                context=OperationContext(session_id="s1", operation_name="missing"),
            ),
        )
