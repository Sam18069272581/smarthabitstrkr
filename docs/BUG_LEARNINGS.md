# SmartHabitTrkr Bug Learnings

## Purpose

This file accumulates concrete bugs, regressions, and environment issues we hit during migration and how we fixed them.

The goal is to reduce repeat mistakes and make future debugging faster.

## Working Rule

When a bug is found, try to record:

- what failed
- where it failed
- root cause
- fix
- prevention note

## Entries

### 2026-04-24: Global Python environment drift

- Symptom: project verification in the global Python environment required package installs that conflicted with unrelated packages
- Area: local developer environment
- Root cause: dependencies were installed into the machine-wide interpreter instead of a project-isolated environment
- Fix: switched to the sibling virtual environment at `D:\Projects\Smarthabittrkr\.venv`
- Prevention: prefer `.venv` or the dev container for all future installs, tests, and tooling runs

### 2026-04-24: Windows test DB path incompatibility

- Symptom: FastAPI integration tests failed with `sqlite3.OperationalError: unable to open database file`
- Area: `backend/tests/test_integration.py`
- Root cause: tests used a Linux-style `/tmp/test_smarthabit.db` path, which is not portable on Windows
- Fix: replaced the hard-coded path with `tempfile.gettempdir()` and `Path(...)`
- Prevention: use platform-aware temp/file APIs in tests instead of hard-coded OS-specific paths

### 2026-04-24: Pydantic periodic-task validation gap

- Symptom: creating a periodic task without `period` could slip through when the field was omitted instead of explicitly set to `null`
- Area: `backend/schemas.py`
- Root cause: the old validation used a field-level validator on `period`, which did not reliably enforce the cross-field rule when the field was absent
- Fix: replaced it with a model-level validator that checks `type == periodic` and `period is None`
- Prevention: use model-level validation for cross-field rules

### 2026-04-24: Flask validation error serialization failure

- Symptom: Flask `POST /api/tasks` returned `500` instead of `422` for some invalid payloads
- Area: `backend/flask_api/tasks.py`
- Root cause: `exc.errors()` included objects that Flask JSON serialization could not encode directly
- Fix: converted the validation error payload through `exc.json()` and `json.loads(...)`
- Prevention: normalize framework-facing validation errors into plain JSON-safe structures before returning them

### 2026-04-24: Ruff glob parsing with unusual directory name

- Symptom: Ruff failed while parsing the exclude glob for the unusual `{backend` directory
- Area: `pyproject.toml`
- Root cause: the raw `{` in the exclude pattern was interpreted as an unclosed alternate glob group
- Fix: escaped it via `[{]backend`
- Prevention: escape special glob characters in tool configs when unusual directory names are present

### 2026-04-24: Flask tests polluted each other through a shared SQLite file

- Symptom: Flask tests that passed individually became flaky in broader runs, including failures like non-empty "empty list" results and `table tasks already exists`
- Area: `backend/tests/test_flask_tasks.py`
- Root cause: multiple tests reused the same fixed temporary SQLite filename, so data and schema state leaked across test runs
- Fix: switched the Flask test fixture to create a unique SQLite database file per test via `uuid4()`
- Prevention: give each test its own isolated DB file or transaction sandbox when building incremental API test suites
