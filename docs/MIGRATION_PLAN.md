# SmartHabitTrkr Migration Plan

## Goal

Migrate the backend from `FastAPI` to `Flask` while keeping:

- the existing REST API contract stable
- the `API-First` development principle
- cloud-friendly containerized development via `Docker` and `.devcontainer`
- Python code standardized with `Ruff`

This plan is tailored to the current codebase, where:

- business logic already lives in `backend/service.py`
- SQLAlchemy models are independent from FastAPI
- the frontend talks to the backend only via HTTP
- the main FastAPI coupling is in `backend/main.py`, `backend/routers/`, and integration tests

## Migration Difficulty

Overall difficulty: `medium to medium-high`

Why it is manageable:

- `service.py` can mostly be reused
- `models.py` and most of `database.py` can mostly be reused
- frontend endpoints can remain unchanged

Why it is not trivial:

- FastAPI currently provides validation, error handling, and docs automatically
- `/docs` and OpenAPI are part of the current API-first story
- integration tests depend on `fastapi.testclient.TestClient`

## Target Architecture

Suggested backend target:

- `Flask` for the HTTP app
- `Blueprint` for route grouping
- `Pydantic` retained for request and response schema validation
- `SQLAlchemy` retained as-is
- OpenAPI generated explicitly instead of relying on FastAPI defaults

Suggested structure:

```text
backend/
  app.py                 # Flask app factory
  extensions.py          # db/session/shared setup if needed
  database.py            # engine/session helpers
  models.py              # SQLAlchemy ORM
  schemas.py             # Pydantic request/response contracts
  service.py             # business logic
  api/
    tasks.py             # Flask Blueprint for /api/tasks
    statistics.py        # Flask Blueprint for /api/statistics
    health.py            # Flask Blueprint for /api/health
  tests/
```

## Non-Negotiables

The following should not change during migration:

- API paths: `/api/tasks`, `/api/tasks/{id}`, `/api/statistics/monthly`, `/api/health`
- HTTP methods and main response shapes
- frontend fetch usage in `frontend/index.html`
- service-layer ownership of business logic
- automated tests for business rules and HTTP endpoints

## Recommended Migration Strategy

### Phase 1: Freeze the API contract

Before switching frameworks, explicitly document:

- request payloads
- query parameters
- success responses
- error responses
- validation behavior

Deliverables:

- an OpenAPI source of truth or a contract document
- a list of endpoints and example payloads
- a short compatibility checklist for the frontend

Reason:

This reduces the risk that the framework migration silently changes behavior.

### Phase 2: Introduce Flask with an app factory

Create a new Flask entrypoint and route registration model.

Tasks:

- add a Flask app factory
- add blueprints for `tasks`, `statistics`, and `health`
- keep static frontend serving in Flask
- move startup table creation to Flask startup/app init flow

Notes:

- keep route URLs unchanged
- keep JSON response bodies unchanged where possible

### Phase 3: Preserve validation with Pydantic

Do not replace contract validation with ad hoc `request.json` parsing.

Tasks:

- keep `TaskCreate`, `TaskUpdate`, `CheckInCreate`, and response schemas
- validate request bodies manually in Flask endpoints using Pydantic
- normalize validation errors into a stable JSON format

Recommended response style:

```json
{
  "detail": "Validation failed",
  "errors": [...]
}
```

Reason:

FastAPI currently gives you strong validation for free. If you drop this, the migration will weaken the API-first story.

### Phase 4: Replace FastAPI-specific dependencies

Current FastAPI-specific pieces to replace:

- `Depends(get_db)`
- `Query(...)`
- `HTTPException`
- `response_model=...`
- `TestClient`
- automatic `/docs`

Flask replacements:

- DB session context manager or per-request session helper
- query parsing via `request.args`
- JSON error helpers plus error handlers
- explicit `model_validate` and `model_dump`
- Flask test client
- explicit OpenAPI + Swagger UI integration

### Phase 5: Rebuild API documentation

To keep `API-First` credible in Flask, add explicit API documentation support.

Recommended options:

- `flask-openapi3`
- `apispec` + `marshmallow` or `pydantic` bridge
- `connexion` if you want OpenAPI-first routing

Best fit for this project:

- `flask-openapi3` or `connexion`

Why:

- both keep the contract visible
- both support Swagger/OpenAPI workflows better than plain Flask
- both are easier to defend academically than undocumented Flask routes

If course expectations are simple:

- keep a generated `/openapi.json`
- expose Swagger UI at `/docs`

### Phase 6: Migrate tests

Testing should be updated in two layers.

Unit tests:

- mostly keep as-is because they target `service.py`

Integration tests:

- replace `fastapi.testclient.TestClient` with Flask test client
- replace dependency override logic with test app/session injection
- keep endpoint assertions identical wherever possible

Success criterion:

- all current HTTP behaviors still covered after framework swap

### Phase 7: Add Ruff-based standardization

Move Python tooling into `pyproject.toml`.

Recommended Ruff scope:

- lint
- import sorting
- pyupgrade-style modernizations
- selected formatting if you want one-tool standardization

Suggested initial rules:

- `E`, `F`, `I`, `UP`, `B`

Suggested workflow:

```bash
ruff check .
ruff check . --fix
ruff format .
```

Apply Ruff after the Flask migration skeleton is in place, not before large route rewrites.

### Phase 8: Add Docker and Dev Container

Create:

- `Dockerfile`
- `.dockerignore`
- `.devcontainer/devcontainer.json`
- optional `docker-compose.yml`

Recommended dev-container shape:

- Python base image
- installs `requirements.txt`
- mounts workspace
- exposes port `8000`
- runs Flask app in debug/dev mode

Recommended production shape:

- run behind `gunicorn`
- persist database via mounted volume if SQLite remains

Important caveat:

- SQLite is fine for development and coursework demos
- for real cloud persistence, PostgreSQL is safer than SQLite-on-container-filesystem

## Proposed Dependency Changes

Replace:

- `fastapi`
- `uvicorn`

Add:

- `flask`
- `gunicorn`
- one OpenAPI/Swagger integration package
- `ruff`

Keep:

- `sqlalchemy`
- `pydantic`
- `pytest`
- `httpx` only if still needed

Potential future cleanup:

- remove `pytest-asyncio` if no async code remains

## Sequence of Work

Recommended order:

1. write down the API contract
2. scaffold Flask app factory and blueprints
3. migrate health endpoint
4. migrate task routes
5. migrate statistics route
6. wire request validation and error format
7. restore frontend static serving
8. migrate integration tests
9. add OpenAPI + Swagger UI
10. add Ruff config and run fixes
11. add Docker and `.devcontainer`
12. update README for the new developer workflow

## Risks

### Risk 1: Validation regression

Without explicit schema handling in Flask, invalid payloads may stop returning proper `422`-like behavior.

Mitigation:

- keep Pydantic
- write explicit validation tests

### Risk 2: API doc regression

If `/docs` disappears, the project becomes harder to defend as API-first.

Mitigation:

- choose an OpenAPI-capable Flask integration from day one

### Risk 3: Test instability

The current integration suite is tightly coupled to FastAPI test helpers.

Mitigation:

- migrate test infrastructure early, not at the very end

### Risk 4: Cloud persistence with SQLite

SQLite inside ephemeral containers can lose data if not mounted persistently.

Mitigation:

- mount a data volume for development
- consider PostgreSQL for cloud deployment

## Acceptance Criteria

The migration is complete when:

- all existing REST endpoints still work under Flask
- frontend works without changing its endpoint calls
- API documentation is available again at `/docs`
- unit tests pass
- integration tests pass
- project opens in a dev container
- app runs in Docker
- Ruff passes cleanly

## Estimated Effort

For this specific repo:

- Flask migration only: `1-2 days`
- API-first docs and tests stabilization: `1-2 days`
- Ruff + Docker + devcontainer + README updates: `1 day`

Realistic total:

- `3-5 days`

## Recommended Next Implementation Slice

If we implement this incrementally, the safest first slice is:

1. add `pyproject.toml` with Ruff
2. scaffold Flask app factory and blueprints beside the existing FastAPI app
3. migrate only `/api/health` first
4. add Docker and `.devcontainer`
5. then migrate task/statistics routes

This gives a reversible path instead of a single risky cutover.
