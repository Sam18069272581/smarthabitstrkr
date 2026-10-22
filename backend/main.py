"""
SmartHabitTrkr – FastAPI Backend
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .database import SessionLocal, create_tables
from .demo_data import seed_demo_data
from .routers import tasks, statistics


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    if os.getenv("DEMO_SEED") == "1":
        with SessionLocal() as db:
            seed_demo_data(db)
    yield


app = FastAPI(
    title="SmartHabitTrkr API",
    description="""
## To-Do & Habit Tracking – Web-Technologien I (HSBI SS 2026)

### Architektur
- **Backend**: Python + FastAPI (API-First)
- **Datenbank**: SQLite via SQLAlchemy ORM
- **Frontend**: Vanilla HTML/CSS/JS (Responsive Design)
- **Tests**: Unittests (Business-Logik) + Integrationstests (alle API-Endpunkte)

### API-Endpunkte
| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | /api/tasks | Alle Aufgaben (filterbar) |
| POST | /api/tasks | Neue Aufgabe erstellen |
| GET | /api/tasks/{id} | Einzelne Aufgabe |
| PUT | /api/tasks/{id} | Aufgabe aktualisieren |
| DELETE | /api/tasks/{id} | Aufgabe löschen |
| POST | /api/tasks/{id}/checkin | Check-in eintragen |
| DELETE | /api/tasks/{id}/checkin | Check-in rückgängig |
| POST | /api/tasks/{id}/archive | Aufgabe archivieren |
| GET | /api/statistics/monthly | Monatsstatistiken |
    """,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(statistics.router)


@app.get("/api/health", tags=["System"])
def health():
    return {"status": "ok", "service": "SmartHabitTrkr", "version": "1.0.0"}


# Frontend statisch ausliefern
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
