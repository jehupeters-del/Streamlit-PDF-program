# Implementation Decisions (Locked for Initial Build)

Date: 2026-02-13

## Confirmed Choices
- Python target: 3.13
- Primary PDF adapter stack: PyMuPDF (fitz)
- Batch extraction output delivery: single ZIP download
- Validation batch report baseline format: CSV
- Dependency management: plain pip + requirements files
- Test fixtures: both synthetic fixtures and a small set of real-world fixtures
- Upload limits: 50 MB per PDF, 100 MB per batch

## Implications for Scaffold
- Configure project and CI against Python 3.13.
- Design adapter boundary so additional PDF libraries can be added later.
- Include ZIP packaging utility in batch extraction workflow.
- Include CSV serializer for validation batch results in v1 baseline.
- Use requirements files for runtime and development dependencies.
- Build fixture strategy with deterministic synthetic files and representative real-world samples.
- Enforce configurable size guards with generous defaults from user constraints.

## Next Implementation Step
Create repository skeleton, requirements files, and quality toolchain (ruff, black, mypy, pytest, coverage), then implement core domain/service contracts aligned with these decisions.
