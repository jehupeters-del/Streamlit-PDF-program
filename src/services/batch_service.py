from __future__ import annotations

import csv
import io
import re
import zipfile

from src.domain.models import BatchItemResult, BatchOperationResult, OperationMessage, Status
from src.services.extraction_service import ExtractionService
from src.services.validation_service import ValidationService


class BatchService:
    def __init__(
        self, extraction_service: ExtractionService, validation_service: ValidationService
    ) -> None:
        self.extraction_service = extraction_service
        self.validation_service = validation_service

    def run_extraction_batch(self, files: list[tuple[str, bytes]]) -> BatchOperationResult:
        items: list[BatchItemResult] = []
        for file_name, file_bytes in files:
            try:
                result = self.extraction_service.extract_questions(file_name, file_bytes)
                status = Status.SUCCESS if result.validation.is_valid else Status.WARNING
                messages = [
                    OperationMessage(
                        level="info", text=f"Found {len(result.found_questions)} questions."
                    ),
                ]
                if not result.validation.is_valid:
                    messages.append(
                        OperationMessage(
                            level="warning",
                            text=f"Missing questions: {result.validation.missing_questions}",
                        )
                    )
                items.append(
                    BatchItemResult(
                        source_name=file_name,
                        status=status,
                        messages=messages,
                        metrics={
                            "original_pages": result.original_pages,
                            "extracted_pages": result.extracted_pages,
                            "max_question": result.validation.max_question,
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

    def run_validation_batch(self, files: list[tuple[str, bytes]]) -> BatchOperationResult:
        items: list[BatchItemResult] = []
        for file_name, file_bytes in files:
            try:
                result = self.validation_service.validate_pdf(file_bytes)
                status = Status.SUCCESS if result.is_valid else Status.WARNING
                missing_text = (
                    "None"
                    if not result.missing_questions
                    else ",".join(map(str, result.missing_questions))
                )
                message = (
                    "No questions found (valid by rule)."
                    if result.max_question == 0
                    else f"Max question: {result.max_question}; Missing: {missing_text}"
                )
                items.append(
                    BatchItemResult(
                        source_name=file_name,
                        status=status,
                        messages=[OperationMessage(level="info", text=message)],
                        metrics={
                            "max_question": result.max_question,
                            "missing_questions": missing_text,
                            "found_questions": ",".join(map(str, result.found_questions)),
                        },
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

    @staticmethod
    def _safe_artifact_name(name: str) -> str:
        clean = name.replace("\\", "/").split("/")[-1]
        clean = re.sub(r"[^A-Za-z0-9._() -]", "_", clean).strip()
        return clean or "artifact.pdf"

    @staticmethod
    def build_zip(
        result: BatchOperationResult, zip_name: str = "batch_extraction_outputs.zip"
    ) -> tuple[str, bytes]:
        buffer = io.BytesIO()
        used_names: dict[str, int] = {}
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for item in result.items:
                if item.artifact_name and item.artifact_bytes:
                    safe_name = BatchService._safe_artifact_name(item.artifact_name)
                    stem, dot, extension = safe_name.rpartition(".")
                    if not stem:
                        stem = safe_name
                        dot = ""
                        extension = ""
                    sequence = used_names.get(safe_name, 0)
                    used_names[safe_name] = sequence + 1
                    unique_name = safe_name
                    if sequence > 0:
                        unique_name = f"{stem} ({sequence + 1}){dot}{extension}"
                    archive.writestr(
                        unique_name,
                        item.artifact_bytes,
                    )
        return zip_name, buffer.getvalue()

    @staticmethod
    def build_validation_csv(result: BatchOperationResult) -> tuple[str, bytes]:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "source_name",
                "status",
                "max_question",
                "missing_questions",
                "found_questions",
                "messages",
            ]
        )
        for item in result.items:
            writer.writerow(
                [
                    item.source_name,
                    item.status.value,
                    item.metrics.get("max_question", ""),
                    item.metrics.get("missing_questions", ""),
                    item.metrics.get("found_questions", ""),
                    " | ".join(message.text for message in item.messages),
                ]
            )
        return "validation_batch_report.csv", buffer.getvalue().encode("utf-8")

    @staticmethod
    def build_validation_text_summary(result: BatchOperationResult) -> tuple[str, str]:
        lines: list[str] = []
        lines.append("Validation Batch Summary")
        lines.append(
            "success="
            f"{result.success_count} "
            "warning="
            f"{result.warning_count} "
            "error="
            f"{result.error_count}"
        )
        lines.append("")
        for item in result.items:
            lines.append(f"[{item.status.value.upper()}] {item.source_name}")
            if item.metrics:
                lines.append("metrics: " + ", ".join(f"{k}={v}" for k, v in item.metrics.items()))
            if item.messages:
                lines.extend(f"- {msg.text}" for msg in item.messages)
            lines.append("")
        return "validation_batch_report.txt", "\n".join(lines).rstrip() + "\n"
