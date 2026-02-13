# Implementation Kickoff Plan (Streamlit PDF Rebuild)

## Goal
Create a clean, extensible Streamlit-first repository that preserves baseline outcomes:
- Multi-PDF edit + merge
- Question extraction (single + batch)
- Question continuity validation (single + batch)
- Human-readable result summaries and exportable batch reporting

## Phase 0 — Foundation Setup
1. Initialize repository and baseline docs.
2. Create project skeleton:
   - app/
   - src/domain/
   - src/services/
   - src/adapters/
   - src/infrastructure/
   - tests/unit/
   - tests/integration/
   - tests/e2e/
   - docs/architecture/
   - docs/decisions/
   - docs/runbooks/
3. Add pyproject with:
   - runtime deps (streamlit + chosen PDF libs)
   - dev deps (pytest, ruff, black, mypy, coverage)
   - tool configs and test markers
4. Add .gitignore tuned for Python + Streamlit + temp artifact outputs.

## Phase 1 — Domain and Contracts
1. Define core models:
   - WorkspaceFile
   - PageRef
   - OperationInput / OperationResult
   - ValidationResult / ExtractionResult / MergeResult
2. Define error taxonomy:
   - ValidationError
   - ParsingError
   - IOErrorCategory
   - SystemError
3. Define service interfaces:
   - WorkspaceService
   - MergeService
   - ExtractionService
   - ValidationService
4. Define adapter interface for PDF engine abstraction.

## Phase 2 — Core Services
1. Implement workspace/session file lifecycle with cleanup.
2. Implement merge over retained-page order.
3. Implement extraction:
   - always retain first page
   - retain pages matching regex: \\bquestion\\s+(\\d+)\\b (case-insensitive)
   - smart naming rules (month/year + fallback)
4. Implement validation:
   - detect all question numbers
   - continuity check from 1..max
   - no-questions-found as valid with max=0

## Phase 3 — Streamlit UI
1. Upload/workspace panel with metadata and reset.
2. Thumbnail page review + single/multi page removal.
3. Merge panel + download output.
4. Extraction panel:
   - single mode summary + download
   - batch mode per-file status + output package
5. Validation panel:
   - single mode result summary
   - batch mode per-file status + report export

## Phase 4 — Quality and Delivery
1. Unit tests for domain + services.
2. Integration tests with PDF fixtures.
3. E2E smoke test path for critical Streamlit flows.
4. CI workflow:
   - lint
   - format check
   - type check
   - tests + coverage gate
   - build/package sanity
5. Deployment runbook for Streamlit Community Cloud.

## Initial Acceptance Slice (MVP-to-Baseline path)
1. End-to-end upload -> remove pages -> merge -> download.
2. End-to-end extraction single mode + summary.
3. End-to-end validation single mode + summary.
4. Batch extraction and validation with report export.

## Decisions Needed Before Coding Starts
1. Preferred Python version target (recommend 3.11 or 3.12).
2. Preferred PDF stack (PyMuPDF vs pypdf+pdfplumber/hybrid).
3. Batch output packaging preference (zip vs per-file download table).
4. Report export default format (txt, csv, or json).
5. Strict pinning strategy (exact pins vs constrained ranges + lock).

## Suggested First Build Sprint
1. Repo scaffold + pyproject + CI + quality tools.
2. Domain contracts and error taxonomy.
3. Merge + validation service + unit tests.
4. Minimal Streamlit screen proving upload, merge, validate.
