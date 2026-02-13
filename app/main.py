from __future__ import annotations

import base64
import html
import re

import streamlit as st

from src.adapters.pymupdf_adapter import PyMuPdfAdapter
from src.domain.errors import ValidationError
from src.domain.models import BatchOperationResult, PageRef, WorkspaceFile
from src.infrastructure.config import AppConfig
from src.services.batch_service import BatchService
from src.services.extraction_service import ExtractionService
from src.services.merge_service import MergeService
from src.services.regex_search_service import RegexSearchService
from src.services.validation_service import ValidationService
from src.services.workspace_service import WorkspaceService


def _init_services() -> tuple[
    AppConfig,
    WorkspaceService,
    MergeService,
    ExtractionService,
    RegexSearchService,
    ValidationService,
    BatchService,
]:
    config = AppConfig()
    adapter = PyMuPdfAdapter()
    validation_service = ValidationService(adapter)
    extraction_service = ExtractionService(adapter, validation_service)
    regex_search_service = RegexSearchService(adapter)
    workspace_service = WorkspaceService(adapter, config)
    merge_service = MergeService(adapter)
    batch_service = BatchService(extraction_service, validation_service)
    return (
        config,
        workspace_service,
        merge_service,
        extraction_service,
        regex_search_service,
        validation_service,
        batch_service,
    )


def _init_state() -> None:
    st.session_state.setdefault("workspace_files", [])
    st.session_state.setdefault("page_refs", [])
    st.session_state.setdefault("thumbnail_cache", {})
    st.session_state.setdefault("merged_signature", "")
    st.session_state.setdefault("merged_pdf_bytes", b"")
    st.session_state.setdefault("merged_pdf_name", "merged_output.pdf")
    st.session_state.setdefault("extract_batch_uploader_token", 0)
    st.session_state.setdefault("validate_batch_uploader_token", 0)
    st.session_state.setdefault("regex_batch_uploader_token", 0)


def _thumbnail_bytes(file_id: str, pdf_bytes: bytes, page_index: int, zoom: float = 0.38) -> bytes:
    key = (file_id, page_index, round(zoom, 3))
    thumbnail_cache: dict[tuple[str, int, float], bytes] = st.session_state.thumbnail_cache
    if key not in thumbnail_cache:
        adapter = PyMuPdfAdapter()
        thumbnail_cache[key] = adapter.render_page_thumbnail(pdf_bytes, page_index, zoom=zoom)
    return thumbnail_cache[key]


def _thumbnail_html(image_bytes: bytes, page_number: int) -> str:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return (
        "<div style='border:1px solid rgba(120,120,120,0.35);"
        " border-radius:10px;padding:8px;background:rgba(250,250,250,0.75);'>"
        "<div style='text-align:center;font-size:0.85rem;"
        f"font-weight:600;margin-bottom:6px;'>Page {page_number}</div>"
        "<div style='display:flex;justify-content:center;'>"
        f"<img src='data:image/png;base64,{encoded}' "
        "style='width:100%;height:auto;border-radius:6px;'/>"
        "</div>"
        "</div>"
    )


def _parse_page_range_spec(spec: str, max_page: int) -> tuple[list[int], str | None]:
    cleaned = spec.strip()
    if not cleaned:
        return [], "Enter one or more page numbers or ranges."

    pages: set[int] = set()
    parts = [part.strip() for part in cleaned.split(",") if part.strip()]
    if not parts:
        return [], "Enter one or more page numbers or ranges."

    for part in parts:
        if re.fullmatch(r"\d+", part):
            page = int(part)
            if page < 1 or page > max_page:
                return [], f"Page {page} is out of range (1-{max_page})."
            pages.add(page)
            continue

        range_match = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2))
            if start > end:
                return [], f"Invalid range '{part}'. Start must be <= end."
            if start < 1 or end > max_page:
                return [], f"Range '{part}' is out of range (1-{max_page})."
            pages.update(range(start, end + 1))
            continue

        return [], f"Invalid token '{part}'. Use formats like 1,3,5-7."

    return sorted(pages), None


def _merge_signature(workspace_files: list[WorkspaceFile], page_refs: list[PageRef]) -> str:
    file_sig = "|".join(item.file_id for item in workspace_files)
    page_sig = "|".join(f"{item.file_id}:{item.page_index}" for item in page_refs)
    return f"{file_sig}::{page_sig}"


def _auto_thumbnail_columns(page_count: int) -> int:
    if page_count <= 1:
        return 1
    if page_count <= 4:
        return 2
    if page_count <= 9:
        return 3
    if page_count <= 16:
        return 4
    if page_count <= 25:
        return 5
    return 6


def _file_map(files: list[WorkspaceFile]) -> dict[str, WorkspaceFile]:
    return {item.file_id: item for item in files}


def _retained_page_counts(page_refs: list[PageRef]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ref in page_refs:
        counts[ref.file_id] = counts.get(ref.file_id, 0) + 1
    return counts


def _validate_upload_limits(config: AppConfig, files: list[tuple[str, bytes]]) -> None:
    total = sum(len(content) for _, content in files)
    if total > config.max_batch_size_bytes:
        raise ValidationError(f"Batch exceeds {config.max_batch_size_mb} MB limit.")
    for name, content in files:
        if len(content) > config.max_pdf_size_bytes:
            raise ValidationError(f"{name} exceeds {config.max_pdf_size_mb} MB limit.")
        if not name.lower().endswith(".pdf"):
            raise ValidationError(f"{name} is not a PDF file.")


def _highlight_snippet(snippet: str, matched_text: str, case_sensitive: bool) -> str:
    escaped_full = html.escape(snippet)
    if not matched_text:
        return escaped_full

    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(re.escape(matched_text), flags)
    chunks: list[str] = []
    last_end = 0
    for match in pattern.finditer(snippet):
        chunks.append(html.escape(snippet[last_end : match.start()]))
        chunks.append(f"<mark>{html.escape(snippet[match.start() : match.end()])}</mark>")
        last_end = match.end()
    if not chunks:
        return escaped_full
    chunks.append(html.escape(snippet[last_end:]))
    return "".join(chunks)


def _render_batch_summary(result: BatchOperationResult, table_key: str) -> None:
    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
    metric_col_1.metric("Success", result.success_count)
    metric_col_2.metric("Warning", result.warning_count)
    metric_col_3.metric("Error", result.error_count)

    rows = []
    for item in result.items:
        rows.append(
            {
                "File": item.source_name,
                "Status": item.status.value.title(),
                "Details": " | ".join(message.text for message in item.messages),
            }
        )

    st.dataframe(rows, use_container_width=True)


def _render_uploaded_file_list(files: list[tuple[str, bytes]], key_prefix: str) -> None:
    if not files:
        return

    page_size = 10
    total_files = len(files)
    total_pages = (total_files + page_size - 1) // page_size

    current_key = f"{key_prefix}_upload_page"
    st.session_state.setdefault(current_key, 1)
    current_page = int(st.session_state[current_key])
    if current_page < 1 or current_page > total_pages:
        current_page = 1
        st.session_state[current_key] = 1

    if total_pages > 1:
        info_col, nav_col = st.columns([3, 2])
        with info_col:
            st.caption(f"Showing page {current_page} of {total_pages}")
        with nav_col:
            selected_page = st.number_input(
                "Uploaded files page",
                min_value=1,
                max_value=total_pages,
                value=current_page,
                step=1,
                key=f"{key_prefix}_upload_page_selector",
            )
            if int(selected_page) != current_page:
                st.session_state[current_key] = int(selected_page)
                st.rerun()

    start = (current_page - 1) * page_size
    end = start + page_size
    page_files = files[start:end]
    st.dataframe(
        [
            {
                "File": name,
                "Size (MB)": round(len(content) / (1024 * 1024), 2),
            }
            for name, content in page_files
        ],
        use_container_width=True,
    )


def _workspace_tab(
    config: AppConfig,
    workspace_service: WorkspaceService,
    merge_service: MergeService,
) -> None:
    st.subheader("Edit and Merge PDFs", anchor=False)
    st.caption("Review all loaded PDFs below, remove unwanted pages, then merge.")

    uploaded = st.file_uploader(
        (
            "Load one or more PDFs "
            f"(max {config.max_pdf_size_mb} MB each, "
            f"{config.max_batch_size_mb} MB total)"
        ),
        type=["pdf"],
        accept_multiple_files=True,
        key="workspace_upload",
    )

    if st.button("Add Uploaded PDFs", type="primary"):
        try:
            files = [(item.name, item.getvalue()) for item in uploaded] if uploaded else []
            loaded = workspace_service.load_files(files)
            if loaded:
                st.session_state.workspace_files.extend(loaded)
                st.session_state.page_refs.extend(workspace_service.initial_page_refs(loaded))
                st.success(f"Loaded {len(loaded)} PDF(s).")
        except Exception as exc:
            st.error(str(exc))

    col_reset, col_limits = st.columns([1, 2])
    with col_reset:
        if st.button("New (Reset Workspace)"):
            st.session_state.workspace_files = []
            st.session_state.page_refs = []
            st.session_state.thumbnail_cache = {}
            st.success("Workspace reset.")
    with col_limits:
        st.caption(
            "Upload limits: "
            f"{config.max_pdf_size_mb} MB per PDF, "
            f"{config.max_batch_size_mb} MB per batch"
        )

    workspace_files: list[WorkspaceFile] = st.session_state.workspace_files
    page_refs: list[PageRef] = st.session_state.page_refs

    if not workspace_files:
        st.info("No PDFs loaded yet.")
        return

    retained_counts = _retained_page_counts(page_refs)

    st.subheader("Pages (all loaded PDFs)", anchor=False)
    for workspace_file in workspace_files:
        file_refs = [ref for ref in page_refs if ref.file_id == workspace_file.file_id]
        st.markdown(
            f"**{workspace_file.name}** "
            f"({retained_counts.get(workspace_file.file_id, 0)} pages retained)"
        )
        if st.button("Remove PDF", key=f"remove_pdf_{workspace_file.file_id}"):
            new_files, new_refs = workspace_service.remove_file(
                workspace_files,
                page_refs,
                workspace_file.file_id,
            )
            st.session_state.workspace_files = new_files
            st.session_state.page_refs = new_refs
            st.session_state.thumbnail_cache = {
                key: value
                for key, value in st.session_state.thumbnail_cache.items()
                if key[0] != workspace_file.file_id
            }
            st.rerun()

        if not file_refs:
            st.caption("No retained pages in this document.")
            st.divider()
            continue

        thumbnails_per_row = _auto_thumbnail_columns(len(file_refs))
        cols = st.columns(thumbnails_per_row, gap="small")
        for index, ref in enumerate(file_refs):
            display_page = index + 1
            with cols[index % thumbnails_per_row]:
                thumbnail = _thumbnail_bytes(
                    workspace_file.file_id,
                    workspace_file.content,
                    ref.page_index,
                )
                st.markdown(_thumbnail_html(thumbnail, display_page), unsafe_allow_html=True)
                if st.button(
                    f"Remove Page {display_page}",
                    key=f"remove_single_{workspace_file.file_id}_{ref.page_index}",
                    use_container_width=True,
                ):
                    st.session_state.page_refs = workspace_service.remove_single_page(
                        st.session_state.page_refs,
                        workspace_file.file_id,
                        ref.page_index,
                    )
                    st.rerun()

        with st.form(key=f"remove_multi_form_{workspace_file.file_id}"):
            page_spec = st.text_input(
                "Select multiple pages to remove",
                placeholder="Examples: 1,3,5-8",
                key=f"multi_select_text_{workspace_file.file_id}",
            )
            st.caption("Type pages and ranges using current page numbers (e.g., 1,3,5-8).")
            submit = st.form_submit_button("Remove Selected Pages")
            if submit:
                selected_pages, error = _parse_page_range_spec(page_spec, len(file_refs))
                if error:
                    st.error(error)
                else:
                    selected_refs = [file_refs[page - 1] for page in selected_pages]
                    page_indices = [item.page_index for item in selected_refs]
                    st.session_state.page_refs = workspace_service.remove_multiple_pages(
                        st.session_state.page_refs,
                        workspace_file.file_id,
                        page_indices,
                    )
                    st.success(f"Removed {len(page_indices)} page(s).")
                    st.rerun()
        st.divider()

    total_pages = len(st.session_state.page_refs)
    st.write(f"Total retained pages across workspace: {total_pages}")

    if total_pages > 0:
        try:
            current_signature = _merge_signature(
                st.session_state.workspace_files,
                st.session_state.page_refs,
            )
            if st.session_state.merged_signature != current_signature:
                result = merge_service.merge(
                    st.session_state.workspace_files,
                    st.session_state.page_refs,
                )
                st.session_state.merged_signature = current_signature
                st.session_state.merged_pdf_bytes = result.output_pdf
                st.session_state.merged_pdf_name = result.output_name

            st.download_button(
                "Merge & Download PDF",
                data=st.session_state.merged_pdf_bytes,
                file_name=st.session_state.merged_pdf_name,
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(str(exc))
    else:
        st.button("Merge & Download PDF", disabled=True, use_container_width=True)


def _extraction_tab(
    config: AppConfig, extraction_service: ExtractionService, batch_service: BatchService
) -> None:
    st.subheader("Extract Questions Only", anchor=False)
    st.caption("Run single or batch extraction and download clean outputs.")
    mode = st.radio("Mode", options=["Single", "Batch"], horizontal=True, key="extract_mode")

    if mode == "Single":
        uploaded_single = st.file_uploader(
            f"Choose a PDF (max {config.max_pdf_size_mb} MB)",
            type=["pdf"],
            key="extract_single",
        )
        if st.button("Run Extraction"):
            if not uploaded_single:
                st.warning("Upload a PDF first.")
                return
            try:
                content = uploaded_single.getvalue()
                _validate_upload_limits(config, [(uploaded_single.name, content)])
                single_result = extraction_service.extract_questions(uploaded_single.name, content)
                st.download_button(
                    "Download Extracted PDF",
                    data=single_result.output_pdf,
                    file_name=single_result.output_name,
                    mime="application/pdf",
                )
                st.success("Extraction complete")
                stat_col_1, stat_col_2, stat_col_3 = st.columns(3)
                stat_col_1.metric("Original pages", single_result.original_pages)
                stat_col_2.metric("Extracted pages", single_result.extracted_pages)
                stat_col_3.metric("Questions found", len(single_result.found_questions))
                st.markdown(f"**Output file:** {single_result.output_name}")
                if single_result.validation.max_question == 0:
                    st.info("No questions found in document (valid by rule).")
                elif single_result.validation.is_valid:
                    st.success("Question sequence is complete.")
                else:
                    st.warning(
                        "Missing questions: " f"{single_result.validation.missing_questions}"
                    )
            except Exception as exc:
                st.error(str(exc))
    else:
        uploaded_batch = st.file_uploader(
            (
                "Choose one or more PDFs "
                f"(max {config.max_pdf_size_mb} MB each, "
                f"{config.max_batch_size_mb} MB total)"
            ),
            type=["pdf"],
            accept_multiple_files=True,
            key=f"extract_batch_{st.session_state.extract_batch_uploader_token}",
        )
        if st.button("Clear All PDFs", key="clear_extract_batch"):
            st.session_state.extract_batch_uploader_token += 1
            st.rerun()
        files = [(item.name, item.getvalue()) for item in uploaded_batch] if uploaded_batch else []
        _render_uploaded_file_list(files, "extract")
        if st.button("Run Batch Extraction"):
            if not files:
                st.warning("Upload at least one PDF.")
                return
            try:
                _validate_upload_limits(config, files)
                progress = st.progress(0)
                batch_result = batch_service.run_extraction_batch(files)
                progress.progress(100)
                _render_batch_summary(batch_result, table_key="extract_batch_summary")
                zip_name, zip_bytes = batch_service.build_zip(batch_result)
                st.download_button(
                    "Download Batch ZIP",
                    data=zip_bytes,
                    file_name=zip_name,
                    mime="application/zip",
                )
            except Exception as exc:
                st.error(str(exc))


def _validation_tab(
    config: AppConfig, validation_service: ValidationService, batch_service: BatchService
) -> None:
    st.subheader("Validate Questions", anchor=False)
    st.caption("Check question sequence continuity with clear summary results.")
    mode = st.radio("Mode", options=["Single", "Batch"], horizontal=True, key="validate_mode")

    if mode == "Single":
        uploaded_single = st.file_uploader(
            f"Choose a PDF (max {config.max_pdf_size_mb} MB)",
            type=["pdf"],
            key="validate_single",
        )
        if st.button("Run Validation"):
            if not uploaded_single:
                st.warning("Upload a PDF first.")
                return
            try:
                content = uploaded_single.getvalue()
                _validate_upload_limits(config, [(uploaded_single.name, content)])
                single_result = validation_service.validate_pdf(content)
                stat_col_1, stat_col_2, stat_col_3 = st.columns(3)
                stat_col_1.metric("Max question", single_result.max_question)
                stat_col_2.metric("Questions found", len(single_result.found_questions))
                stat_col_3.metric("Missing count", len(single_result.missing_questions))
                if single_result.max_question == 0:
                    st.info("No questions found (valid by rule).")
                elif single_result.is_valid:
                    st.success("All questions are present.")
                else:
                    st.warning(f"Missing questions: {single_result.missing_questions}")
                if single_result.found_questions:
                    st.caption(
                        "Detected questions: "
                        + ", ".join(str(number) for number in single_result.found_questions)
                    )
            except Exception as exc:
                st.error(str(exc))
    else:
        uploaded_batch = st.file_uploader(
            (
                "Choose one or more PDFs "
                f"(max {config.max_pdf_size_mb} MB each, "
                f"{config.max_batch_size_mb} MB total)"
            ),
            type=["pdf"],
            accept_multiple_files=True,
            key=f"validate_batch_{st.session_state.validate_batch_uploader_token}",
        )
        if st.button("Clear All PDFs", key="clear_validate_batch"):
            st.session_state.validate_batch_uploader_token += 1
            st.rerun()
        files = [(item.name, item.getvalue()) for item in uploaded_batch] if uploaded_batch else []
        _render_uploaded_file_list(files, "validate")
        if st.button("Run Batch Validation"):
            if not files:
                st.warning("Upload at least one PDF.")
                return
            try:
                _validate_upload_limits(config, files)
                progress = st.progress(0)
                batch_result = batch_service.run_validation_batch(files)
                progress.progress(100)
                _render_batch_summary(batch_result, table_key="validate_batch_summary")

                csv_name, csv_bytes = batch_service.build_validation_csv(batch_result)
                txt_name, txt_summary = batch_service.build_validation_text_summary(batch_result)

                st.download_button(
                    "Download Validation CSV",
                    data=csv_bytes,
                    file_name=csv_name,
                    mime="text/csv",
                )
                st.download_button(
                    "Download Validation TXT",
                    data=txt_summary,
                    file_name=txt_name,
                    mime="text/plain",
                )
                st.text_area(
                    "Copy-ready validation summary",
                    value=txt_summary,
                    height=220,
                    key="validation_copy_summary",
                )
            except Exception as exc:
                st.error(str(exc))


def _regex_extract_tab(
    config: AppConfig,
    regex_search_service: RegexSearchService,
    batch_service: BatchService,
) -> None:
    st.subheader("Regex Page Extractor", anchor=False)
    st.caption("Extract pages matching your regex and download a new PDF.")

    mode = st.radio("Mode", options=["Single", "Batch"], horizontal=True, key="regex_mode")
    pattern = st.text_input(
        "Regex pattern",
        placeholder=r"Example: solution\.",
        key="regex_pattern",
    )
    case_sensitive = st.checkbox("Case-sensitive", key="regex_case_sensitive", value=False)
    keep_first_page = st.checkbox(
        "Keep first page in output",
        key="regex_keep_first_page",
        value=True,
    )

    if mode == "Single":
        uploaded_single = st.file_uploader(
            f"Choose a PDF (max {config.max_pdf_size_mb} MB)",
            type=["pdf"],
            key="regex_single",
        )
        if st.button("Run Regex Extraction", type="primary"):
            if not uploaded_single:
                st.warning("Upload a PDF first.")
                return
            try:
                content = uploaded_single.getvalue()
                _validate_upload_limits(config, [(uploaded_single.name, content)])
                result = regex_search_service.extract_matching_pages(
                    input_name=uploaded_single.name,
                    pdf_bytes=content,
                    pattern=pattern,
                    case_sensitive=case_sensitive,
                    keep_first_page=keep_first_page,
                )

                st.download_button(
                    "Download Matched PDF",
                    data=result.output_pdf,
                    file_name=result.output_name,
                    mime="application/pdf",
                    type="primary",
                )

                stat_col_1, stat_col_2, stat_col_3 = st.columns(3)
                stat_col_1.metric("Original pages", result.original_pages)
                stat_col_2.metric("Matched pages", len(result.matched_pages))
                stat_col_3.metric("Extracted pages", result.extracted_pages)

                if result.matches:
                    st.markdown("**Matched pages with highlighted snippets**")
                    st.dataframe(
                        [
                            {
                                "Page": item.page_number,
                                "Matches": item.match_count,
                                "Snippet": item.snippet,
                            }
                            for item in result.matches
                        ],
                        use_container_width=True,
                    )

                    preview_adapter = PyMuPdfAdapter()
                    preview_columns = st.columns(4, gap="small")
                    for index, item in enumerate(result.matches):
                        with preview_columns[index % 4]:
                            preview = preview_adapter.render_page_thumbnail_with_highlights(
                                pdf_bytes=content,
                                page_index=item.page_number - 1,
                                search_terms=[item.matched_text],
                                zoom=0.38,
                            )
                            st.markdown(
                                _thumbnail_html(preview, item.page_number),
                                unsafe_allow_html=True,
                            )
                            highlighted = _highlight_snippet(
                                item.snippet,
                                item.matched_text,
                                case_sensitive,
                            )
                            st.markdown(highlighted, unsafe_allow_html=True)
                elif keep_first_page:
                    st.info("No page matched regex. Output includes first page only.")
            except Exception as exc:
                st.error(str(exc))
    else:
        uploaded_batch = st.file_uploader(
            (
                "Choose one or more PDFs "
                f"(max {config.max_pdf_size_mb} MB each, "
                f"{config.max_batch_size_mb} MB total)"
            ),
            type=["pdf"],
            accept_multiple_files=True,
            key=f"regex_batch_{st.session_state.regex_batch_uploader_token}",
        )
        if st.button("Clear All PDFs", key="clear_regex_batch"):
            st.session_state.regex_batch_uploader_token += 1
            st.rerun()
        files = [(item.name, item.getvalue()) for item in uploaded_batch] if uploaded_batch else []
        _render_uploaded_file_list(files, "regex")
        if st.button("Run Batch Regex Extraction", type="primary"):
            if not files:
                st.warning("Upload at least one PDF.")
                return
            try:
                _validate_upload_limits(config, files)
                batch_result = regex_search_service.run_batch_extraction(
                    files=files,
                    pattern=pattern,
                    case_sensitive=case_sensitive,
                    keep_first_page=keep_first_page,
                )
                _render_batch_summary(batch_result, table_key="regex_batch_summary")
                zip_name, zip_bytes = batch_service.build_zip(
                    batch_result,
                    zip_name="regex_batch_outputs.zip",
                )
                st.download_button(
                    "Download Batch ZIP",
                    data=zip_bytes,
                    file_name=zip_name,
                    mime="application/zip",
                    type="primary",
                )
            except Exception as exc:
                st.error(str(exc))


def main() -> None:
    st.set_page_config(page_title="PDF Suite Core", layout="wide")
    st.title("PDF Suite Core — Streamlit Rebuild", anchor=False)

    (
        config,
        workspace_service,
        merge_service,
        extraction_service,
        regex_search_service,
        validation_service,
        batch_service,
    ) = _init_services()
    _init_state()

    tab_workspace, tab_extract, tab_validate, tab_regex = st.tabs(
        ["Edit & Merge", "Extract Questions", "Validate Questions", "Regex Extract"]
    )

    with tab_workspace:
        _workspace_tab(config, workspace_service, merge_service)

    with tab_extract:
        _extraction_tab(config, extraction_service, batch_service)

    with tab_validate:
        _validation_tab(config, validation_service, batch_service)

    with tab_regex:
        _regex_extract_tab(config, regex_search_service, batch_service)


if __name__ == "__main__":
    main()
