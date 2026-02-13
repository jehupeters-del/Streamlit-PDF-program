# Streamlit-First Rebuild Requirements

## 1. Document Purpose

This document converts the current behavior baseline into a build-ready specification for a **new repository** that will:

1. Use **Streamlit as the primary deployment target**.
2. Preserve core user outcomes from the legacy desktop app.
3. Establish a **robust, extensible foundation** for a larger future PDF suite.

This is a requirements and architecture handoff, not an implementation lock-in.

---

## 2. Product Intent (v1 Foundation)

The rebuilt app must deliver a clean, production-grade foundation for:

- Multi-PDF page review and editing.
- Page removal and merged output export.
- Question page extraction (single + batch).
- Question continuity validation (single + batch).
- Human-readable results and batch reporting.

It should be designed so additional PDF capabilities can be added without major rewrites.

---

## 3. Scope Definition

## 3.1 In Scope for Initial Rebuild
- Streamlit web app as canonical UI/runtime.
- Functional parity with desktop baseline outcomes (not desktop UI style).
- Production-grade engineering baseline:
  - tests
  - linting/formatting/type checks
  - documentation
  - CI validation
  - Streamlit deployment pipeline

## 3.2 Out of Scope for Initial Rebuild
- Full advanced PDF-suite features beyond current baseline.
- Complex plugin marketplace or multi-tenant SaaS features.
- Enterprise auth/permissions model (can be planned but not required in v1).

---

## 4. Guiding Architecture Principles

1. **Separation of concerns**: UI layer, application services, and PDF domain logic are isolated.
2. **Deterministic core logic**: PDF operations are testable outside Streamlit runtime.
3. **Stateless-by-default services** with explicit state boundaries for session/workspace handling.
4. **Extensibility-first contracts**: operations should be added through clear service interfaces.
5. **Observability and debuggability**: structured logging + predictable error categories.
6. **Safe file handling**: explicit lifecycle for temp artifacts and session workspaces.

---

## 5. Recommended Repository Structure (Target)

```text
pdf-suite-core/
  app/                          # Streamlit UI entry + pages/components
  src/
    domain/                     # Core models, value objects, policies
    services/                   # Use-case orchestration (merge/extract/validate)
    adapters/                   # PDF library adapters, storage adapters
    infrastructure/             # config, logging, temp storage, dependency wiring
  tests/
    unit/
    integration/
    e2e/
  docs/
    architecture/
    decisions/
    runbooks/
  pyproject.toml
  README.md
  CONTRIBUTING.md
  .github/workflows/
```

---

## 6. Functional Epics and Acceptance Criteria

## Epic A — File Workspace and Session Handling

### Requirements
- Users can upload one or many PDFs.
- Files are tracked per user session/workspace.
- Workspace can be reset safely.

### Acceptance Criteria
- Uploading valid PDFs adds them to active workspace list with metadata.
- Invalid files are rejected with clear user-facing error messages.
- Reset action removes active workspace state and temp artifacts.

---

## Epic B — Page Review, Selection, and Removal

### Requirements
- Users can inspect page thumbnails for selected documents.
- Users can remove individual pages and multi-selected pages.

### Acceptance Criteria
- Thumbnails render for loaded pages within acceptable response time.
- Removing pages updates visible counts and downstream merge output.
- State remains consistent after repeated select/remove operations.

---

## Epic C — Merge and Export

### Requirements
- Users can merge retained pages across loaded PDFs.
- Users can download merged output.

### Acceptance Criteria
- Merge reflects current retained-page order and count.
- If no pages remain, merge action is disabled or blocked with clear feedback.
- Downloaded merged file opens successfully in standard PDF viewers.

---

## Epic D — Question Extraction (Single + Batch)

### Requirements
- User can run extraction on one file or batch of files.
- Extraction keeps first page and pages matching question pattern.
- Smart output naming is applied.

### Acceptance Criteria
- Pattern matching is case-insensitive and regex-equivalent to `\bquestion\s+(\d+)\b`.
- Single mode returns downloadable file and summary metrics.
- Batch mode returns per-file status and packaged output access.
- Naming rules support month/year inference and fallback naming.

---

## Epic E — Question Validation (Single + Batch)

### Requirements
- User can validate one file or many files for sequence continuity.
- Report includes validity, missing numbers, and max detected question.

### Acceptance Criteria
- Validation checks continuity from 1 through max detected question.
- “No questions found” is represented explicitly as a non-error state.
- Batch mode provides per-file outcome summaries and exportable report data.

---

## Epic F — Results and Reporting UX

### Requirements
- User sees clear status for success/warning/error outcomes.
- Batch outputs are easy to review and export.

### Acceptance Criteria
- Every operation emits user-visible status + machine-readable result object.
- Batch operations include counts for success/warning/error.
- Validation batch results can be exported to text/CSV/JSON (at least one required in v1, others optional).

---

## 7. Non-Functional Requirements (Robust Foundation)

## 7.1 Reliability
- Graceful failure handling for malformed PDFs and I/O errors.
- No orphan temp files after failed operations.
- Idempotent reset/cleanup operations.

## 7.2 Performance
- Thumbnail generation and PDF transforms should avoid blocking the full app UI.
- Batch operations should surface progress and partial outcomes.

## 7.3 Maintainability
- Strict layering with minimal cross-module coupling.
- Clear interfaces for adding new PDF operations.
- Developer onboarding docs and local runbook included.

## 7.4 Security & Safety
- Validate upload type and extension.
- Enforce configurable max file size and batch limits.
- Prevent unsafe path usage and filename injection.
- Avoid persisting sensitive content longer than configured retention.

---

## 8. Technical Baseline Requirements

## 8.1 Python Project Standards
- Use `pyproject.toml` as single project config source.
- Use dependency pinning strategy (exact pins or constrained locks).
- Include reproducible local setup instructions.

## 8.2 Quality Toolchain (Required)
- Linting: `ruff` (or equivalent) with CI enforcement.
- Formatting: `black` (or equivalent) with CI enforcement.
- Type checking: `mypy` (or pyright) for core modules.
- Tests: `pytest` with unit + integration markers.
- Coverage: minimum threshold gate (recommended: 85%+ in core services).

## 8.3 Test Strategy
- **Unit tests** for pure domain/service logic.
- **Integration tests** for PDF adapters against controlled fixtures.
- **E2E smoke tests** for Streamlit critical flows (headless automation or scripted checks).
- Golden fixture tests for extraction/validation determinism.

---

## 9. Streamlit Deployment and CI/CD Requirements

## 9.1 Deployment Model
- Streamlit Community Cloud is primary hosted target.
- App entrypoint and environment config are explicit and documented.

## 9.2 CI Pipeline (Required)
Every pull request must run:

1. Lint
2. Format check
3. Type check
4. Unit/integration tests
5. Build/package sanity check

Main branch should only be deployable when all checks pass.

## 9.3 Release Controls
- Use semantic versioning tags.
- Maintain changelog entries for user-visible behavior changes.
- Keep deployment checklist/runbook in `docs/runbooks`.

---

## 10. Extensibility Contract for Future PDF Suite

The v1 foundation must support expansion into additional capabilities (e.g., OCR, annotations, redaction, form tools, splitting, metadata tools, document pipelines).

## 10.1 Required Extensibility Mechanisms
- Operation registry or service map for adding new PDF capabilities.
- Shared job result schema across operations.
- Common file workspace abstraction reused by all features.
- Centralized error taxonomy (validation error, parsing error, I/O error, system error).

## 10.2 Data Contracts
- Standard operation input model (files + options + context).
- Standard operation output model (artifact references + metrics + messages + status).
- Backward-compatible schema evolution policy.

## 10.3 UI Extensibility
- Reusable Streamlit components for:
  - file upload/workspace view
  - operation options panel
  - progress/status panel
  - results table/cards + downloads

---

## 11. Suggested Implementation Choices (Flexible, Not Mandatory)

These are recommendations to keep options open:

- PDF processing: keep adapter abstraction so libraries can be swapped per operation.
- Async strategy: background worker abstraction for long jobs (thread/process/task queue adaptable).
- Config: environment-driven settings + typed config object.
- Logging: structured JSON-capable logs with request/session correlation IDs.

If a different stack is chosen, it must still satisfy all functional and non-functional requirements above.

---

## 12. Definition of Done (Foundation Release)

The initial rebuild is done when:

1. All Epics A–F acceptance criteria are met.
2. Quality toolchain is enforced in CI.
3. Streamlit deployment is reproducible and documented.
4. Baseline docs exist:
   - Product requirements
   - Architecture overview
   - Local development guide
   - Deployment runbook
   - Test strategy
5. The codebase is structured to add at least one new PDF operation without refactoring core layers.

---

## 13. Build Sequence Recommendation

1. Establish project skeleton + quality gates.
2. Implement domain/service contracts + adapter interfaces.
3. Deliver core workspace and merge flows.
4. Add extraction + validation services.
5. Integrate Streamlit UX around stable service contracts.
6. Add batch reporting/export and polish operational concerns.
7. Freeze v1 baseline and begin advanced feature expansion.

---

## 14. Traceability to Legacy Behavior

Functional parity target comes from `DESKTOP_APP_BEHAVIOR_BASELINE.md`.

- That document defines **what** outcomes must be preserved.
- This document defines **how** to rebuild with production quality and future extensibility.
