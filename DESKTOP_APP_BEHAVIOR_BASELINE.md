# PDF Editor — Current Behavior Baseline (Desktop-First)

## 1. Purpose

This application is a desktop PDF workflow tool designed to help a user:

1. Load one or more PDF documents.
2. Visually review pages as thumbnails.
3. Remove unwanted pages.
4. Merge remaining pages into one output PDF.
5. Extract only pages containing numbered questions.
6. Validate whether question numbering is complete.

The original and canonical product behavior is defined by the local desktop application in `main.py`.

---

## 2. Core User Jobs

The app supports three main jobs:

### A) Edit and Merge PDFs
- Build a working set of PDFs.
- Inspect pages visually.
- Remove pages one-by-one or in multi-select mode.
- Export the final merged PDF.

### B) Extract Question Pages
- Process a single PDF or a batch of PDFs.
- Keep pages that contain `Question <number>`.
- Preserve the first page as a title/cover page.
- Save extracted outputs with smart filenames.
- Show extraction summary and validation results.

### C) Validate Question Continuity
- Process a single PDF or a batch of PDFs.
- Detect question numbers using text pattern matching.
- Report whether the sequence from 1 to max question is complete.
- Highlight missing question numbers (including missing Question 1).
- In batch mode, allow export/copy of report results.

---

## 3. Canonical End-to-End Workflow (Desktop UI)

## 3.1 App Start
- User launches desktop app.
- Main layout opens with:
  - Left sidebar (document list and controls)
  - Main thumbnail grid area
  - Bottom action bar (page count, remove pages, extract, validate, merge)

## 3.2 Build Working Set
- User clicks **Load PDFs** and picks one or more files.
- Each loaded PDF appears in sidebar with name and page count.
- First loaded PDF auto-selects if nothing is selected.

## 3.3 Review and Modify Pages
- Selecting a PDF shows page thumbnails in a grid.
- User can:
  - Remove a single page directly.
  - Click pages to multi-select and then remove selected pages.
- Total page count updates live.
- Merge button enables only when total pages > 0.

## 3.4 Merge Output
- User clicks **Merge & Download PDF**.
- User chooses output file path.
- App writes all remaining pages in current internal order to one merged PDF.
- App shows success or error feedback.

## 3.5 Question Extraction
- User clicks **Extract Questions Only**.
- App prompts for mode: single file or batch files.

Single mode:
- User chooses one input PDF.
- App proposes a smart output filename.
- User chooses save location.
- App extracts question pages and opens a result dialog with:
  - source/output info
  - page reduction stats
  - questions found
  - validation status (all present vs missing list)

Batch mode:
- User chooses multiple input PDFs.
- User chooses one output folder.
- App processes each file and opens a batch result window with per-file cards:
  - success/warning/error state
  - output file name
  - page reduction
  - validation summary

## 3.6 Question Validation
- User clicks **Validate Questions**.
- App prompts for mode: single file or batch files.

Single mode:
- User chooses one PDF.
- App validates and shows a result dialog:
  - no questions found, or
  - all questions present, or
  - missing question list and warning details

Batch mode:
- User chooses multiple PDFs.
- App validates each and opens batch results with per-file cards.
- User can also:
  - export results to a text report
  - copy summary results to clipboard

---

## 4. Inputs

## 4.1 User Inputs
- PDF files selected from local filesystem.
- Output file path for merged file.
- Output path/folder for extracted files.
- UI mode decisions (single vs batch for extraction/validation).
- Page selection/removal actions.

Note: extraction and validation operate on files selected at run time via file dialogs and are independent of the currently loaded editor sidebar working set.

## 4.2 File/Content Inputs
- PDFs may contain text, diagrams, shapes, and images.
- Question detection expects text pattern: `Question <integer>` (case-insensitive).

---

## 5. Outputs

## 5.1 Primary Artifacts
- Merged PDF (`.pdf`) from edited page set.
- Extracted PDF(s) containing selected pages by question detection.
- Optional batch validation text report (`.txt`) in desktop batch validation flow.

## 5.2 On-Screen Results
- Live page counts and control states.
- Success/error dialogs for load/merge/extract/validate actions.
- Extraction summaries (original vs extracted pages, found questions).
- Validation summaries (valid/missing, max question, missing list).

---

## 6. Functional Rules (Product-Level)

## 6.1 PDF Loading and State
- Each loaded PDF gets a unique internal ID.
- Pages are tracked as individual units that can be removed independently.
- Removing pages updates both total page count and per-PDF page count.

## 6.2 Merge Behavior
- Merge includes all currently retained pages across loaded PDFs.
- Output is written as one PDF file.
- If no pages are present, merge is blocked by UI.

## 6.3 Question Detection Rule
- Detection pattern is text-based: `\bquestion\s+(\d+)\b`.
- Matching is case-insensitive.
- Duplicate question numbers are accepted as present.
- Validation expects complete coverage from `1..max_question_found`.

## 6.4 Extraction Rule
- First page is retained as title/cover context.
- Pages containing one or more question numbers are retained.
- Non-question pages are excluded from extracted output.
- Output is saved with PDF optimization/compression settings.

## 6.5 Validation Rule
- Returns:
  - validity flag
  - missing question numbers list
  - maximum question number found
- If no questions are found, result is treated as valid with max = 0.

## 6.6 Smart Output Naming
- Extraction output names attempt to infer month/year from input filename.
- Typical format: `<Month> <Year> solutions.pdf`.
- If only month is inferred: `<Month> solutions.pdf`.
- If only year is inferred: `<Year> solutions.pdf`.
- Falls back to original base name + `_solutions.pdf` when no month/year pattern is found.

---

## 7. UX Surface Summary (Desktop)

## 7.1 Main Controls
- **New**: clears current working set.
- **Load PDFs**: imports PDFs.
- **Remove Selected PDF**: removes current document.
- **Remove Selected Pages**: removes multi-selected thumbnails.
- **Extract Questions Only**: starts extraction mode flow.
- **Validate Questions**: starts validation mode flow.
- **Merge & Download PDF**: exports merged PDF.

## 7.2 Feedback Patterns
- Modal dialogs for confirms/warnings/errors.
- Dedicated result windows for extraction and validation summaries.
- Batch result windows with per-file status cards.
- Buttons temporarily disabled during background processing operations.

---

## 8. Data and Processing Model

- Processing is local and file-based.
- PDF operations are performed in-process via Python libraries.
- Long-running operations run in background threads to keep UI responsive.
- No external API or remote service is required for core functionality.

---

## 9. Components and Responsibility Split

- `main.py`
  - Desktop UI workflow orchestration.
  - User interactions, dialog flows, and result presentation.

- `pdf_manager.py`
  - Core PDF operations:
    - load/remove page model
    - merge
    - question extraction
    - question continuity validation
    - smart extraction filename generation

- `pdf_viewer.py`
  - Thumbnail generation and thumbnail widget construction.

---

## 10. Behavior Signals from Tests

The existing test suite reinforces the following product expectations:

- Loading/removing PDFs and pages updates counts correctly.
- Merge output page count reflects retained pages.
- Validation identifies missing numbers accurately.
- Validation works regardless of question case and page order.
- Extraction preserves question-bearing content and typically reduces page count.
- Desktop flow supports batch validation result export/copy behavior.

These tests are useful as behavior anchors for a clean rebuild.

---

## 11. Relationship to Flask and Streamlit Versions

- Flask and Streamlit versions are derivative implementations of the same core concept.
- For rebuild planning, desktop behavior should be treated as canonical source of product workflow.
- Web implementations can inform wording and UX alternatives, but should not override desktop workflow intent in this baseline.
- Current divergence: web implementations retain core edit/extract/validate goals, but do not fully mirror desktop batch-result utilities and desktop-style popup reporting workflows.

---

## 12. Rebuild Baseline Summary

If rebuilding from scratch, the minimum product to match current intent is:

1. Multi-PDF load + page thumbnail review.
2. Page deletion (single and multi-select).
3. Merged export of retained pages.
4. Question extraction (single + batch).
5. Question continuity validation (single + batch).
6. Human-readable extraction and validation summaries.
7. Batch validation report export/copy capability.

This is the current application behavior baseline to carry forward into a new, cleaner repository.
