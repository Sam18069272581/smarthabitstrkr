# SmartHabitTrkr Project Context

## Purpose

This file stores the stable collaboration context for this project so future sessions can continue with less re-explaining.

It is the durable version of our working context.

## Project Snapshot

- Project name: `SmartHabitTrkr`
- Type: To-do and habit tracking web app
- Frontend: vanilla `HTML/CSS/JS`
- Backend today: `FastAPI`
- Target backend direction: evaluate and likely migrate to `Flask`
- ORM: `SQLAlchemy`
- Validation/contracts: `Pydantic`
- Database today: `SQLite`

## Current User Goals

- align backend framework with the teacher's course project expectations
- analyze and plan migration from `FastAPI` to `Flask`
- keep the project defensible under the `API-First` principle
- prepare the app for cloud-friendly `Docker` and `.devcontainer` development
- standardize Python code with `Ruff`

## Working Assumptions

- preserving API compatibility is more important than preserving FastAPI internals
- the frontend should continue to consume the backend over the same REST endpoints
- business logic should remain outside the frontend
- business logic should remain centralized in the service layer
- code quality and course defensibility matter, not just "it runs"

## Non-Negotiable Principles

- `API-First`
- stable REST contract
- thin route/controller layer
- service-layer business logic
- test coverage for business rules and API behavior
- containerized developer workflow

## Important Codebase Facts

- `backend/service.py` contains most of the business logic and is the main reusable migration asset
- `backend/routers/` is the main FastAPI-coupled layer and will need the largest rewrite
- `backend/tests/test_integration.py` is coupled to FastAPI test tooling
- `frontend/index.html` consumes the backend only through HTTP endpoints, which is good for migration
- the repo now includes a baseline `pyproject.toml` for Ruff plus minimal `Dockerfile` and `.devcontainer` scaffolding

## Collaboration Preferences

Based on the current interaction, prefer:

- Chinese for planning and discussion
- practical, implementation-oriented recommendations
- direct risk assessment instead of vague "maybe" answers
- preserving a strong project context across steps

## Q&A Working Style

When continuing work on this repository, optimize for:

- first understanding the current codebase
- then proposing the smallest safe change set
- keeping course constraints visible
- calling out tradeoffs clearly
- converting important decisions into repo docs when useful

## Decision Log

### 2026-04-24

- user requested a migration difficulty analysis from FastAPI to Flask
- conclusion: migration difficulty is `medium to medium-high`
- reason: business logic is already well separated, but FastAPI currently provides validation, docs, and test conveniences
- decision: create a written migration plan before changing framework code
- decision: create a persistent project context document to reduce repeated onboarding in future sessions
- decision: start with the lowest-risk changes that do not affect the running backend framework
- implemented: `pyproject.toml` with Ruff baseline rules
- implemented: root `.gitignore` for Python/cache/database artifacts
- implemented: minimal container scaffolding via `Dockerfile`, `.dockerignore`, and `.devcontainer/devcontainer.json`
- implemented: parallel Flask app factory in `backend/flask_app.py`
- implemented: first migrated Flask endpoint `/api/health`
- implemented: first minimal Flask-side test in `backend/tests/test_flask_health.py`
- implemented: migrated Flask read endpoints `GET /api/tasks` and `GET /api/tasks/{id}`
- implemented: migrated Flask write endpoint `POST /api/tasks`
- implemented: migrated Flask update endpoint `PUT /api/tasks/{id}`
- implemented: Flask-side task endpoint coverage in `backend/tests/test_flask_tasks.py`
- implemented: cross-platform fix for integration test database path using `tempfile.gettempdir()`
- implemented: isolated dependency installation and verification using sibling `.venv`
- verified: current backend test suite passes with `67` tests total

## Constraints To Re-check During Implementation

- keep `/docs` or an equivalent Swagger/OpenAPI experience
- avoid weakening validation compared with the current FastAPI version
- avoid breaking frontend API calls
- avoid treating SQLite container storage as production-safe by default

## Suggested Persistent Workflow

For future sessions:

1. read this file first
2. read `docs/MIGRATION_PLAN.md`
3. read `docs/BUG_LEARNINGS.md`
4. inspect current repo state
5. implement the next smallest safe slice
6. update this file if priorities or constraints change

## Note About Memory

The most reliable long-term memory is repository memory.

This file is the project-side memory anchor we can keep refining together.
