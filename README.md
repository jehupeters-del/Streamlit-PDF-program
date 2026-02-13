# PDF Suite Core (Streamlit)

Streamlit-first rebuild of the legacy desktop PDF workflow with production-oriented structure and quality gates.

## Features in this baseline
- Multi-PDF workspace loading with per-file and batch upload limits.
- Thumbnail-based page review with single and multi-page removal.
- Merge retained pages and download merged PDF.
- Question extraction (single and batch) using regex `\\bquestion\\s+(\\d+)\\b`.
- Validation (single and batch) with missing-number continuity checks.
- Batch extraction ZIP download and batch validation CSV/TXT export.
- Copy-ready validation batch summary panel for clipboard workflows.

## Tech stack
- Python 3.13
- Streamlit
- PyMuPDF
- pytest + coverage, ruff, black, mypy

## Local setup
1. Create and activate a Python 3.13 virtual environment.
2. Install dependencies:
   - `pip install -r requirements-dev.txt`
3. Run app:
   - `streamlit run streamlit_app.py`

## Launch locally anytime
- Default launch:
   - `streamlit run streamlit_app.py`
- Explicit host/port launch:
   - `python -m streamlit run streamlit_app.py --server.headless true --server.port 8501`

## Test and quality checks
- `flake8 app src tests`
- `black --check .`
- `mypy src app`
- `pytest`

## Configuration
Optional environment variables:
- `PDF_SUITE_MAX_PDF_MB` (default: `50`)
- `PDF_SUITE_MAX_BATCH_MB` (default: `100`)

## Deployment (Streamlit Community Cloud)
- Main entrypoint: `streamlit_app.py`
- Dependencies: `requirements.txt`
- See deployment runbook in `docs/runbooks/deploy_streamlit_cloud.md`.
