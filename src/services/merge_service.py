from __future__ import annotations

from src.adapters.pymupdf_adapter import PyMuPdfAdapter
from src.domain.errors import ValidationError
from src.domain.models import MergeResult, PageRef, WorkspaceFile


class MergeService:
    def __init__(self, adapter: PyMuPdfAdapter) -> None:
        self.adapter = adapter

    def merge(self, workspace_files: list[WorkspaceFile], page_refs: list[PageRef]) -> MergeResult:
        if not page_refs:
            raise ValidationError("Cannot merge when no pages remain.")

        by_id = {item.file_id: item for item in workspace_files}
        output = self.adapter.merge_page_refs(by_id, page_refs)
        return MergeResult(
            output_name="merged_output.pdf", output_pdf=output, merged_pages=len(page_refs)
        )
