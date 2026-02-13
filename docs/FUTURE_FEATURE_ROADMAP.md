# Future Feature Roadmap

## Scope
This document captures post-P1 enhancements for the Streamlit PDF program in a prioritized, implementation-ready format.

## Prioritization Framework
- **Priority**: P2 (next), P3 (later)
- **Impact**: User value and operational stability
- **Effort**: S (small), M (medium), L (large)
- **Dependencies**: Technical or UX prerequisites

## Backlog

| ID | Priority | Feature | Impact | Effort | Dependencies | Notes |
|---|---|---|---|---|---|---|
| FF-001 | P2 | Drag-and-drop file reorder (stable reintroduction) | High | M | Regression-safe DnD component strategy; targeted session-state tests | Reintroduce only with crash-proof state handling and fallback controls. |
| FF-002 | P2 | Persisted user preferences | Medium | S | Config schema extension | Save defaults for output naming style, preview toggles, regex defaults, and case sensitivity. |
| FF-003 | P2 | Batch run history panel | Medium | M | Lightweight local metadata store | Show recent runs with timestamp, operation, success rate, and downloadable artifacts. |
| FF-004 | P2 | Enhanced validation report templates | Medium | S | Current report generation service | Offer concise, detailed, and compliance-oriented report variants. |
| FF-005 | P3 | OCR-assisted text fallback | High | L | OCR engine integration and language packs | Use OCR when pages have no extractable text in regex/extract workflows. |
| FF-006 | P3 | Password-protected PDF handling | Medium | M | Secure password prompt and transient secret handling | Allow user-supplied passwords for supported operations without persisting secrets. |
| FF-007 | P3 | Parallelized batch execution mode | Medium | L | Concurrency-safe adapter/service boundaries | Optional faster mode with clear resource controls and deterministic output order. |
| FF-008 | P3 | Job export/import for resumable workflows | Low | M | Stable job schema versioning | Save and restore in-progress batches across sessions and machines. |

## Acceptance Criteria Template
Each feature should define:
1. User-facing behavior and explicit non-goals.
2. Session-state impact and failure recovery behavior.
3. Tests: happy path, cancellation, retry, and corrupted input handling.
4. Performance expectations with representative file sets.
5. Documentation updates (README + operator-facing notes).

## Governance
- Re-evaluate priorities after each production feedback cycle.
- Promote P3 items to P2 only with a concrete use-case and maintenance budget.
- Keep this roadmap aligned with `STREAMLIT_REBUILD_REQUIREMENTS.md` and baseline behavior constraints.
