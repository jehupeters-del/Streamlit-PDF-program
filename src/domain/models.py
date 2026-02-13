from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Status(str, Enum):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class WorkspaceFile:
    file_id: str
    name: str
    size_bytes: int
    page_count: int
    content: bytes


@dataclass(frozen=True)
class OperationContext:
    session_id: str
    operation_name: str


@dataclass(frozen=True)
class OperationInput:
    files: list[WorkspaceFile]
    options: dict[str, str | int | bool]
    context: OperationContext


@dataclass(frozen=True)
class OperationResult:
    status: Status
    messages: list["OperationMessage"]
    metrics: dict[str, int | str] = field(default_factory=dict)
    artifact_name: str | None = None
    artifact_bytes: bytes | None = None


@dataclass(frozen=True)
class PageRef:
    file_id: str
    page_index: int


@dataclass(frozen=True)
class ValidationResult:
    found_questions: list[int]
    max_question: int
    missing_questions: list[int]
    is_valid: bool


@dataclass(frozen=True)
class ExtractionResult:
    output_name: str
    output_pdf: bytes
    original_pages: int
    extracted_pages: int
    found_questions: list[int]
    validation: ValidationResult


@dataclass(frozen=True)
class MergeResult:
    output_name: str
    output_pdf: bytes
    merged_pages: int


@dataclass(frozen=True)
class OperationMessage:
    level: str
    text: str


@dataclass(frozen=True)
class BatchItemResult:
    source_name: str
    status: Status
    messages: list[OperationMessage] = field(default_factory=list)
    metrics: dict[str, int | str] = field(default_factory=dict)
    artifact_name: str | None = None
    artifact_bytes: bytes | None = None


@dataclass(frozen=True)
class BatchOperationResult:
    items: list[BatchItemResult]

    @property
    def success_count(self) -> int:
        return len([item for item in self.items if item.status == Status.SUCCESS])

    @property
    def warning_count(self) -> int:
        return len([item for item in self.items if item.status == Status.WARNING])

    @property
    def error_count(self) -> int:
        return len([item for item in self.items if item.status == Status.ERROR])
