# Local Development Runbook

## Setup
1. Create a Python 3.13 environment.
2. Install dependencies:
   - `pip install -r requirements-dev.txt`

## Run app
- `streamlit run streamlit_app.py`

## Run quality checks
- `ruff check .`
- `black --check .`
- `mypy src app`
- `pytest`
