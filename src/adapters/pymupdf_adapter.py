from __future__ import annotations

from typing import cast

import fitz  # type: ignore[import-untyped]

from src.domain.errors import ParsingError
from src.domain.models import PageRef, WorkspaceFile


class PyMuPdfAdapter:
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

    def render_page_thumbnail(self, pdf_bytes: bytes, page_index: int, zoom: float = 0.25) -> bytes:
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
                page = document[page_index]
                matrix = fitz.Matrix(zoom, zoom)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                return cast(bytes, pixmap.tobytes("png"))
        except Exception as exc:
            raise ParsingError("Unable to render page thumbnail") from exc

    def merge_page_refs(
        self, workspace_files: dict[str, WorkspaceFile], page_refs: list[PageRef]
    ) -> bytes:
        output = fitz.open()
        try:
            for page_ref in page_refs:
                source = workspace_files[page_ref.file_id]
                with fitz.open(stream=source.content, filetype="pdf") as source_doc:
                    output.insert_pdf(
                        source_doc, from_page=page_ref.page_index, to_page=page_ref.page_index
                    )
            return cast(bytes, output.tobytes(deflate=True, garbage=3))
        except Exception as exc:
            raise ParsingError("Unable to merge selected pages") from exc
        finally:
            output.close()

    def build_pdf_from_indices(self, pdf_bytes: bytes, page_indices: list[int]) -> bytes:
        output = fitz.open()
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as source_doc:
                for index in page_indices:
                    output.insert_pdf(source_doc, from_page=index, to_page=index)
            return cast(bytes, output.tobytes(deflate=True, garbage=3))
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
            return cast(bytes, document.tobytes(deflate=True, garbage=3))
        finally:
            document.close()
