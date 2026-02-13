from __future__ import annotations

import uuid

from src.adapters.pymupdf_adapter import PyMuPdfAdapter
from src.domain.errors import ValidationError
from src.domain.models import PageRef, WorkspaceFile
from src.infrastructure.config import AppConfig


class WorkspaceService:
    def __init__(self, adapter: PyMuPdfAdapter, config: AppConfig) -> None:
        self.adapter = adapter
        self.config = config

    def load_files(self, uploaded_files: list[tuple[str, bytes]]) -> list[WorkspaceFile]:
        if not uploaded_files:
            return []

        total_size = sum(len(content) for _, content in uploaded_files)
        if total_size > self.config.max_batch_size_bytes:
            raise ValidationError(f"Batch size exceeds limit of {self.config.max_batch_size_mb} MB")

        workspace_files: list[WorkspaceFile] = []
        for name, content in uploaded_files:
            if not name.lower().endswith(".pdf"):
                raise ValidationError(f"Invalid file type for {name}. Only PDF files are allowed.")
            size_bytes = len(content)
            if size_bytes > self.config.max_pdf_size_bytes:
                raise ValidationError(
                    f"{name} exceeds per-file limit of {self.config.max_pdf_size_mb} MB"
                )
            page_count = self.adapter.get_page_count(content)
            workspace_files.append(
                WorkspaceFile(
                    file_id=str(uuid.uuid4()),
                    name=name,
                    size_bytes=size_bytes,
                    page_count=page_count,
                    content=content,
                )
            )
        return workspace_files

    def initial_page_refs(self, workspace_files: list[WorkspaceFile]) -> list[PageRef]:
        page_refs: list[PageRef] = []
        for workspace_file in workspace_files:
            page_refs.extend(
                PageRef(file_id=workspace_file.file_id, page_index=index)
                for index in range(workspace_file.page_count)
            )
        return page_refs

    def remove_single_page(
        self, page_refs: list[PageRef], file_id: str, page_index: int
    ) -> list[PageRef]:
        return [
            page_ref
            for page_ref in page_refs
            if not (page_ref.file_id == file_id and page_ref.page_index == page_index)
        ]

    def remove_multiple_pages(
        self, page_refs: list[PageRef], file_id: str, page_indices: list[int]
    ) -> list[PageRef]:
        selected = set(page_indices)
        return [
            page_ref
            for page_ref in page_refs
            if not (page_ref.file_id == file_id and page_ref.page_index in selected)
        ]

    def remove_file(
        self, workspace_files: list[WorkspaceFile], page_refs: list[PageRef], file_id: str
    ) -> tuple[list[WorkspaceFile], list[PageRef]]:
        remaining_files = [item for item in workspace_files if item.file_id != file_id]
        remaining_refs = [item for item in page_refs if item.file_id != file_id]
        return remaining_files, remaining_refs
