# ADR 0001: Foundation Decisions

- Status: Accepted
- Date: 2026-02-13

## Decisions
- Python target: 3.13
- Dependency management: plain pip with `requirements.txt` and `requirements-dev.txt`
- Primary PDF adapter: PyMuPDF
- Batch extraction packaging: ZIP
- Batch validation export baseline: CSV
- Upload size defaults: 50 MB per PDF, 100 MB per batch
- Fixture approach: synthetic fixtures plus a small set of real-world-style fixtures
