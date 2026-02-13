from __future__ import annotations

from typing import cast

import fitz  # type: ignore[import-untyped]

from src.domain.errors import ParsingError
from src.domain.models import PageRef, WorkspaceFile


class PyMuPdfAdapter:
    @staticmethod
    def _optimized_bytes(document: fitz.Document) -> bytes:
        return cast(
            bytes,
            document.tobytes(
                garbage=4,
                clean=True,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
            ),
        )

    def get_page_count(self, pdf_bytes: bytes) -> int:
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
                return int(document.page_count)
        except Exception as exc:
            raise ParsingError("Unable to read PDF page count") from exc

    def extract_text_by_page(self, pdf_bytes: bytes) -> list[str]:
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
                return [document[index].get_text("text") for index in range(document.page_count)]
        except Exception as exc:
            raise ParsingError("Unable to extract PDF text") from exc

    def render_page_thumbnail(self, pdf_bytes: bytes, page_index: int, zoom: float = 0.45) -> bytes:
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
                page = document[page_index]
                matrix = fitz.Matrix(zoom, zoom)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                return cast(bytes, pixmap.tobytes("png"))
        except Exception as exc:
            raise ParsingError("Unable to render page thumbnail") from exc

    def render_page_thumbnail_with_highlights(
        self,
        pdf_bytes: bytes,
        page_index: int,
        search_terms: list[str],
        zoom: float = 0.45,
    ) -> bytes:
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
                page = document[page_index]
                for term in search_terms:
                    if not term.strip():
                        continue
                    rectangles = page.search_for(term)
                    for rectangle in rectangles:
                        annotation = page.add_highlight_annot(rectangle)
                        if annotation is not None:
                            annotation.update()
                matrix = fitz.Matrix(zoom, zoom)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                return cast(bytes, pixmap.tobytes("png"))
        except Exception as exc:
            raise ParsingError("Unable to render highlighted page thumbnail") from exc

    def merge_page_refs(
        self, workspace_files: dict[str, WorkspaceFile], page_refs: list[PageRef]
    ) -> bytes:
        output = fitz.open()
        source_docs: dict[str, fitz.Document] = {}
        try:
            runs: list[tuple[str, int, int]] = []
            if page_refs:
                run_file = page_refs[0].file_id
                run_start = page_refs[0].page_index
                run_end = page_refs[0].page_index
                for page_ref in page_refs[1:]:
                    if page_ref.file_id == run_file and page_ref.page_index == run_end + 1:
                        run_end = page_ref.page_index
                        continue
                    runs.append((run_file, run_start, run_end))
                    run_file = page_ref.file_id
                    run_start = page_ref.page_index
                    run_end = page_ref.page_index
                runs.append((run_file, run_start, run_end))

            for file_id, from_page, to_page in runs:
                if file_id not in source_docs:
                    source = workspace_files[file_id]
                    source_docs[file_id] = fitz.open(stream=source.content, filetype="pdf")
                output.insert_pdf(source_docs[file_id], from_page=from_page, to_page=to_page)

            return self._optimized_bytes(output)
        except Exception as exc:
            raise ParsingError("Unable to merge selected pages") from exc
        finally:
            for source_doc in source_docs.values():
                source_doc.close()
            output.close()

    def build_pdf_from_indices(self, pdf_bytes: bytes, page_indices: list[int]) -> bytes:
        output = fitz.open()
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as source_doc:
                if page_indices:
                    run_start = page_indices[0]
                    run_end = page_indices[0]
                    for index in page_indices[1:]:
                        if index == run_end + 1:
                            run_end = index
                            continue
                        output.insert_pdf(source_doc, from_page=run_start, to_page=run_end)
                        run_start = index
                        run_end = index
                    output.insert_pdf(source_doc, from_page=run_start, to_page=run_end)
            return self._optimized_bytes(output)
        except Exception as exc:
            raise ParsingError("Unable to build extracted PDF") from exc
        finally:
            output.close()

    def create_pdf_from_text_pages(self, pages: list[str]) -> bytes:
        document = fitz.open()
        try:
            for text in pages:
                page = document.new_page()
                page.insert_text((72, 72), text)
            return self._optimized_bytes(document)
        finally:
            document.close()
