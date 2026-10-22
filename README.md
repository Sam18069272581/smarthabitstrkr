# 🌱 SmartHabitTrkr

**To-Do & Habit Tracking Web-App**  
Web-Technologien I — HSBI Sommersemester 2026

---

## Projektübersicht

SmartHabitTrkr ist eine vollständige Web-Applikation zur Verwaltung von Aufgaben und Gewohnheiten. Das System folgt einer strikten **Frontend/Backend-Trennung** mit einer RESTful HTTP-API nach dem **API-First-Prinzip**.

Weitere Projektdokumentation:
- `docs/MIGRATION_PLAN.md` – Migrationsplan FastAPI -> Flask
- `docs/PROJECT_CONTEXT.md` – persistenter Projektkontext und Arbeitsannahmen

### Kernfunktionen
- ✅ **CRUD-Aufgabenverwaltung** — Einmalige Aufgaben & periodische Gewohnheiten
- 📅 **Kalenderansicht** — Dynamischer Monatskalender (Mo–So, europäisch)
- 🍩 **Donut-Fortschrittsanzeige** — Visueller Fortschritt für Gewohnheiten
- 📊 **Statistiken & Diagramme** — Monatsübersicht, KPIs, Streak-Berechnung
- 🌐 **Mehrsprachig** — Deutsch (Standard) & Englisch
- 📱 **Responsive Design** — Mobile & Desktop

---

## Architektur

```
┌─────────────────────────────────────────┐
│          Frontend (HTML/CSS/JS)          │
│   Vanilla JS · Responsive · i18n DE/EN  │
│   Lean Frontend — keine Business-Logik  │
└──────────────┬──────────────────────────┘
               │  HTTP fetch() → RESTful API
               ▼
┌─────────────────────────────────────────┐
│         Backend (Python FastAPI)         │
│   API-First · RESTful CRUD · Pydantic   │
│   Business-Logik im Service-Layer       │
└──────────────┬──────────────────────────┘
               │  SQLAlchemy ORM
               ▼
┌─────────────────────────────────────────┐
│          Datenbank (SQLite)              │
│   Tabellen: tasks · checkins            │
└─────────────────────────────────────────┘
```

---

## API-Endpunkte

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| `GET` | `/api/tasks` | Alle Aufgaben (Filter: status, type, archived, month) |
| `POST` | `/api/tasks` | Neue Aufgabe/Gewohnheit erstellen |
| `GET` | `/api/tasks/{id}` | Einzelne Aufgabe abrufen |
| `PUT` | `/api/tasks/{id}` | Aufgabe aktualisieren (Partial Update) |
| `DELETE` | `/api/tasks/{id}` | Aufgabe löschen |
| `POST` | `/api/tasks/{id}/checkin` | Check-in eintragen (idempotent) |
| `DELETE` | `/api/tasks/{id}/checkin` | Check-in rückgängig machen |
| `POST` | `/api/tasks/{id}/archive` | Aufgabe archivieren (Soft Delete) |
| `GET` | `/api/statistics/monthly` | Monatsstatistiken für Charts |
| `GET` | `/api/health` | System-Status |

**Interaktive Dokumentation:** `http://localhost:8000/docs` (Swagger UI)

---

## Projektstruktur

```
smarthabittrkr/
├── backend/
│   ├── __init__.py
│   ├── flask_app.py     # Paralleler Flask-App-Einstiegspunkt (Migration)
│   ├── main.py          # FastAPI App-Einstiegspunkt, CORS, Routing
│   ├── database.py      # SQLAlchemy Engine, Session, create_tables()
│   ├── flask_api/       # Flask Blueprints für inkrementelle Migration
│   ├── models.py        # ORM-Modelle: Task, CheckIn (mit computed_status)
│   ├── schemas.py       # Pydantic-Schemas für Request/Response-Validierung
│   ├── service.py       # Business-Logik: CRUD, Check-in, Statistiken, Streak
│   ├── routers/
│   │   ├── tasks.py     # REST-Router: /api/tasks/**
│   │   └── statistics.py # REST-Router: /api/statistics/**
│   └── tests/
│       ├── test_unit.py        # 23 Unittests (Business-Logik ohne HTTP)
│       └── test_integration.py # 32 Integrationstests (alle API-Endpunkte)
├── frontend/
│   └── index.html       # Single-Page-App (Vanilla JS, Lean Frontend)
├── requirements.txt
└── README.md
```

---

## Installation & Start

### Voraussetzungen
- Python 3.10+

### 1. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

Bevorzugte isolierte Umgebung für dieses Projekt:
```bash
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Hinweis:
Die Projekt-`.venv` liegt eine Ebene über dem Repo unter `D:\Projects\Smarthabittrkr\.venv`.

### 1a. Code-Qualität prüfen (Ruff)
```bash
# Linting
ruff check .

# Automatische Korrekturen, wo sicher möglich
ruff check . --fix

# Formatierung
ruff format .
```

### 2. Backend starten
```bash
# Aus dem smarthabittrkr/ Verzeichnis:
uvicorn backend.main:app --reload --port 8000
```

### 2a. Parallelen Flask-Health-Check starten
```bash
# Startet die inkrementelle Flask-Migrationslinie parallel auf Port 8001
flask --app backend.flask_app:app run --debug --port 8001
```

Aktuell sind in der parallelen Flask-Linie bereits diese Endpunkte migriert:

- `GET /api/health`
- `GET /api/tasks`
- `POST /api/tasks`
- `GET /api/tasks/{id}`
- `PUT /api/tasks/{id}`

Damit sind erste Read-only-Endpunkte bereits parallel testbar.

Danach sind die migrierten Endpunkte hier erreichbar:
```text
http://localhost:8001/api/health
http://localhost:8001/api/tasks
```

### 3. Frontend öffnen
Das Frontend wird automatisch vom Backend ausgeliefert:
```
http://localhost:8000
```

Oder direkt `frontend/index.html` im Browser öffnen (dann API-URL im Code auf `http://localhost:8000` setzen).

### 4. Docker-Start
```bash
docker build -t smarthabittrkr .
docker run --rm -p 8000:8000 smarthabittrkr
```

Der Container liest den Port aus der Umgebungsvariable `PORT` (Fallback `8000`) und füllt eine leere Datenbank beim Start mit Demo-Daten (`DEMO_SEED=1`, deaktivierbar mit `-e DEMO_SEED=0`). Die SQLite-Datei liegt im Container und geht beim Neustart verloren.

### 4a. Online-Deployment (Render)
1. Auf render.com mit GitHub anmelden → **New → Web Service** → dieses Repository wählen
2. Runtime **Docker**, Instance Type **Free** → **Deploy**

Jeder Push auf `main` löst automatisch ein neues Deployment aus. Der Free-Tier schläft nach ca. 15 Minuten ohne Zugriffe ein; danach werden die Demo-Daten neu angelegt.

### 5. Dev Container

Eine minimale Dev-Container-Konfiguration ist vorhanden:

- `Dockerfile`
- `.dockerignore`
- `.devcontainer/devcontainer.json`

Damit kann das Projekt in einer containerisierten Entwicklungsumgebung geöffnet werden. Aktuell startet der Container noch mit dem bestehenden FastAPI-Stack. Bei der späteren Flask-Migration muss primär nur der Startbefehl angepasst werden.

---

## Tests ausführen

```bash
# Alle Tests (Unit + Integration):
python -m pytest backend/tests/ -v

# Nur Unittests (Business-Logik):
python -m pytest backend/tests/test_unit.py -v

# Nur Integrationstests (API-Endpunkte):
python -m pytest backend/tests/test_integration.py -v

# Mit Coverage-Report:
pip install pytest-cov
python -m pytest backend/tests/ --cov=backend --cov-report=term-missing
```

## Entwicklungsstandard

Python-Code wird über `Ruff` vereinheitlicht.

- Konfiguration: `pyproject.toml`
- Erste aktivierte Regelgruppen: `E`, `F`, `I`, `UP`, `B`
- Ziel: konsistente Imports, Basis-Linting, einfache Modernisierung und weniger vermeidbare Fehler

Empfohlener Ablauf vor Commits:

```bash
ruff check . --fix
ruff format .
python -m pytest backend/tests/ -v
```

### Testergebnisse (aktuell)
```
67 passed in 2.87s

Unittests (23):        _is_overdue, _calc_progress_percentage, _calc_longest_streak, computed_status
FastAPI-Integration (32): Health, CRUD Tasks, CheckIn/Undo, Archive, Statistics
Flask-Tests (12):      Health, Task-Liste, Archiv-Filter, Task-Details, 404, Create, Validation, Update
```

---

## Kursanforderungen — Erfüllungsmatrix

| Anforderung | Status | Details |
|-------------|--------|---------|
| RESTful CRUD API | ✅ | GET/POST/PUT/DELETE für alle Ressourcen |
| API-First Prinzip | ✅ | API unabhängig von Frontend nutzbar |
| Script-Client Kompatibilität | ✅ | JSON API, testbar mit curl/httpx |
| Frontend (kein Business-Logic) | ✅ | Lean Frontend, nur UI + Input-Validierung |
| Responsive Design | ✅ | Mobile + Desktop via CSS Media Queries |
| Datenpersistenz | ✅ | SQLite via SQLAlchemy ORM |
| Unittests (Business-Logik) | ✅ | 23 Tests: Streak, Fortschritt, Überfälligkeitslogik |
| Integrationstests (API) | ✅ | 32 Tests: alle CRUD-Endpunkte |
| Mehrsprachigkeit | ✅ | Deutsch (Standard) + Englisch |

---

## Technologie-Stack

| Schicht | Technologie | Begründung |
|---------|-------------|------------|
| Backend | Python + FastAPI | Schnell, typsicher, automatische API-Doku, bekannt aus Studium |
| ORM | SQLAlchemy 2.0 | Datenbankabstraktion, einfache Migration zu PostgreSQL |
| Datenbank | SQLite | Kein Setup nötig, ideal für Entwicklung |
| Validierung | Pydantic v2 | Automatische Request/Response-Validierung |
| Frontend | Vanilla HTML/CSS/JS | Keine Framework-Abhängigkeit, leichtgewichtig |
| Tests | pytest + httpx | Standard-Teststack für Python/FastAPI |

---

## Script-Client Beispiel (curl)

```bash
# Alle Aufgaben abrufen
curl http://localhost:8000/api/tasks

# Neue Gewohnheit erstellen
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"name": "Täglich lesen", "type": "periodic", "period": "monthly", "target": 28}'

# Check-in eintragen
curl -X POST http://localhost:8000/api/tasks/1/checkin \
  -H "Content-Type: application/json" \
  -d '{"checkin_date": "2026-04-22"}'

# Statistiken abrufen
curl http://localhost:8000/api/statistics/monthly
```

---

## Datenbankschema

```sql
CREATE TABLE tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(200) NOT NULL,
    type        VARCHAR(10)  -- 'once' | 'periodic'
    period      VARCHAR(10)  -- 'daily' | 'weekly' | 'monthly'
    target      INTEGER DEFAULT 1,
    progress    INTEGER DEFAULT 0,
    color       VARCHAR(10) DEFAULT '#22c55e',
    due_date    DATE,
    status      VARCHAR(10) DEFAULT 'active',
    archived    BOOLEAN DEFAULT 0,
    created_at  DATETIME,
    updated_at  DATETIME
);

CREATE TABLE checkins (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id      INTEGER NOT NULL REFERENCES tasks(id),
    checkin_date DATE NOT NULL,
    created_at   DATETIME
);
```

---

*HSBI — Sommersemester 2026 — Web-Technologien I*
