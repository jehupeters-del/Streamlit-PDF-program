# Contributing

## Prerequisites
- Python 3.13
- pip

## Setup
1. Create virtual environment.
2. Install development dependencies:
   - `pip install -r requirements-dev.txt`

## Development standards
- Keep business logic in `src/services` and `src/domain`.
- Keep PDF-library details inside `src/adapters`.
- Keep Streamlit UX in `app`.

## Required checks before PR
- `ruff check .`
- `black --check .`
- `mypy src app`
- `pytest`
