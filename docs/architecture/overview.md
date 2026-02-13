# Architecture Overview

## Layers
- `app/`: Streamlit UI and workflow handling.
- `src/domain/`: Core models and error taxonomy.
- `src/services/`: Deterministic business logic for workspace, merge, extraction, validation, batch reporting.
- `src/adapters/`: PyMuPDF adapter boundary.
- `src/infrastructure/`: Configuration.

## Contracts
- Question detection regex: `\\bquestion\\s+(\\d+)\\b` (case-insensitive).
- Validation continuity rule: complete range from `1..max_question`.
- No questions found: valid result with `max_question=0`.
- Extraction keeps first page plus pages containing question matches.

## Extensibility hooks
- New PDF operations can be added as new services that consume domain contracts and adapter interfaces.
- Batch output/reporting helpers are centralized in `BatchService`.
