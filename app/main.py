from __future__ import annotations

import streamlit as st

from src.adapters.pymupdf_adapter import PyMuPdfAdapter
from src.domain.errors import ValidationError
from src.domain.models import BatchOperationResult, PageRef, WorkspaceFile
from src.infrastructure.config import AppConfig
from src.services.batch_service import BatchService
from src.services.extraction_service import ExtractionService
from src.services.merge_service import MergeService
from src.services.validation_service import ValidationService
from src.services.workspace_service import WorkspaceService


def _init_services() -> tuple[
    AppConfig,
    WorkspaceService,
    MergeService,
    ExtractionService,
    ValidationService,
    BatchService,
    PyMuPdfAdapter,
]:
    config = AppConfig()
    adapter = PyMuPdfAdapter()
    validation_service = ValidationService(adapter)
    extraction_service = ExtractionService(adapter, validation_service)
    workspace_service = WorkspaceService(adapter, config)
    merge_service = MergeService(adapter)
    batch_service = BatchService(extraction_service, validation_service)
    return (
        config,
        workspace_service,
        merge_service,
        extraction_service,
        validation_service,
        batch_service,
        adapter,
    )


def _init_state() -> None:
    st.session_state.setdefault("workspace_files", [])
    st.session_state.setdefault("page_refs", [])


@st.cache_data(show_spinner=False)
def _thumbnail_bytes(pdf_bytes: bytes, page_index: int) -> bytes:
    adapter = PyMuPdfAdapter()
    return adapter.render_page_thumbnail(pdf_bytes, page_index, zoom=0.38)


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


def _render_batch_summary(result: BatchOperationResult) -> None:
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


def _workspace_tab(
    config: AppConfig,
    workspace_service: WorkspaceService,
    merge_service: MergeService,
) -> None:
    st.subheader("Edit and Merge PDFs")

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

    st.write("### Pages (all loaded PDFs)")
    for workspace_file in workspace_files:
        file_refs = sorted(
            [ref for ref in page_refs if ref.file_id == workspace_file.file_id],
            key=lambda ref: ref.page_index,
        )
        header_col_1, header_col_2 = st.columns([3, 1])
        with header_col_1:
            st.markdown(
                f"**{workspace_file.name}** "
                f"({retained_counts.get(workspace_file.file_id, 0)} pages retained)"
            )
        with header_col_2:
            if st.button("Remove PDF", key=f"remove_pdf_{workspace_file.file_id}"):
                new_files, new_refs = workspace_service.remove_file(
                    workspace_files,
                    page_refs,
                    workspace_file.file_id,
                )
                st.session_state.workspace_files = new_files
                st.session_state.page_refs = new_refs
                st.rerun()

        if not file_refs:
            st.caption("No retained pages in this document.")
            st.divider()
            continue

        cols = st.columns(5, gap="small")
        for index, ref in enumerate(file_refs):
            with cols[index % 5]:
                thumbnail = _thumbnail_bytes(workspace_file.content, ref.page_index)
                st.image(thumbnail, caption=f"Page {ref.page_index + 1}", width=125)
                if st.button(
                    f"Remove Page {ref.page_index + 1}",
                    key=f"remove_single_{workspace_file.file_id}_{ref.page_index}",
                ):
                    st.session_state.page_refs = workspace_service.remove_single_page(
                        st.session_state.page_refs,
                        workspace_file.file_id,
                        ref.page_index,
                    )
                    st.rerun()

        page_choices = [ref.page_index + 1 for ref in file_refs]
        selected_to_remove = st.multiselect(
            "Select multiple pages to remove",
            options=page_choices,
            key=f"multi_select_{workspace_file.file_id}",
        )
        if st.button("Remove Selected Pages", key=f"remove_multi_{workspace_file.file_id}"):
            zero_based = [value - 1 for value in selected_to_remove]
            st.session_state.page_refs = workspace_service.remove_multiple_pages(
                st.session_state.page_refs,
                workspace_file.file_id,
                zero_based,
            )
            st.success(f"Removed {len(zero_based)} page(s).")
            st.rerun()
        st.divider()

    total_pages = len(st.session_state.page_refs)
    st.write(f"Total retained pages across workspace: {total_pages}")

    if st.button("Merge & Download PDF", disabled=total_pages == 0):
        try:
            result = merge_service.merge(
                st.session_state.workspace_files, st.session_state.page_refs
            )
            st.download_button(
                "Download Merged PDF",
                data=result.output_pdf,
                file_name=result.output_name,
                mime="application/pdf",
            )
            st.success(f"Merge complete ({result.merged_pages} page(s)).")
        except Exception as exc:
            st.error(str(exc))


def _extraction_tab(
    config: AppConfig, extraction_service: ExtractionService, batch_service: BatchService
) -> None:
    st.subheader("Extract Questions Only")
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
            key="extract_batch",
        )
        if st.button("Run Batch Extraction"):
            files = (
                [(item.name, item.getvalue()) for item in uploaded_batch] if uploaded_batch else []
            )
            if not files:
                st.warning("Upload at least one PDF.")
                return
            try:
                _validate_upload_limits(config, files)
                progress = st.progress(0)
                batch_result = batch_service.run_extraction_batch(files)
                progress.progress(100)
                _render_batch_summary(batch_result)
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
    st.subheader("Validate Questions")
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
            key="validate_batch",
        )
        if st.button("Run Batch Validation"):
            files = (
                [(item.name, item.getvalue()) for item in uploaded_batch] if uploaded_batch else []
            )
            if not files:
                st.warning("Upload at least one PDF.")
                return
            try:
                _validate_upload_limits(config, files)
                progress = st.progress(0)
                batch_result = batch_service.run_validation_batch(files)
                progress.progress(100)
                _render_batch_summary(batch_result)

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


def main() -> None:
    st.set_page_config(page_title="PDF Suite Core", layout="wide")
    st.title("PDF Suite Core — Streamlit Rebuild")

    (
        config,
        workspace_service,
        merge_service,
        extraction_service,
        validation_service,
        batch_service,
        adapter,
    ) = _init_services()
    _init_state()

    tab_workspace, tab_extract, tab_validate = st.tabs(
        ["Edit & Merge", "Extract Questions", "Validate Questions"]
    )

    with tab_workspace:
        _workspace_tab(config, workspace_service, merge_service)

    with tab_extract:
        _extraction_tab(config, extraction_service, batch_service)

    with tab_validate:
        _validation_tab(config, validation_service, batch_service)


if __name__ == "__main__":
    main()
