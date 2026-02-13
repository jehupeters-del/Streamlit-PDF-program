# Test Strategy

## Scope
- Unit tests validate deterministic logic in domain and service modules.
- Integration tests validate PDF adapter behavior and batch packaging/reporting on fixtures.
- E2E smoke tests validate critical end-to-end flows at service level.

## Fixtures
- Synthetic fixtures are generated in-memory for deterministic behavior checks.
- Real-world-style fixtures are stored under `tests/fixtures/real_world/` for representative scenarios.

## Coverage policy
- Coverage gate is enforced in `pyproject.toml` at 85% minimum for `src`.

## CI execution
- Tests run on pull requests and main branch pushes through `.github/workflows/ci.yml`.
