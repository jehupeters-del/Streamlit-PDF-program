# Streamlit Community Cloud Deployment Runbook

## Preconditions
- Repository is pushed to GitHub.
- CI checks pass on the target branch.

## Deploy steps
1. In Streamlit Community Cloud, create a new app from this repository.
2. Set:
   - Main file path: `streamlit_app.py`
   - Python version: `3.13`
3. Ensure dependency install uses `requirements.txt`.
4. Configure optional environment variables:
   - `PDF_SUITE_MAX_PDF_MB`
   - `PDF_SUITE_MAX_BATCH_MB`
5. Deploy and verify smoke checks:
   - upload PDF
   - remove page
   - merge download
   - extraction single + batch zip
   - validation single + batch CSV

## Rollback
- Redeploy previous known-good commit/tag.
