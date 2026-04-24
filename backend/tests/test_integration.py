"""
Integrationstests – HTTP-API
Testet alle CRUD-Endpunkte über echte HTTP-Requests gegen eine Test-DB.
Kursanforderung: Alle API-Endpunkte müssen durch Integrationstests abgedeckt sein.
"""

import os
import sys
import tempfile
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.database import get_db
from backend.main import app
from backend.models import Base

# ── Test-Datenbank: Datei-SQLite (vermeidet In-Memory Verbindungsprobleme) ────
TEST_DB_PATH = Path(tempfile.gettempdir()) / "test_smarthabit.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH.as_posix()}"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Erstellt alle Tabellen vor jedem Test, löscht sie danach."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# Client wird nach dem Override erstellt
client = TestClient(app)


# ── Hilfsfunktionen ──────────────────────────────────────────


def create_sample_task(name="Test Aufgabe", task_type="once", **kwargs) -> dict:
    payload = {"name": name, "type": task_type, **kwargs}
    r = client.post("/api/tasks", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def create_periodic_task(name="Monatlich lesen", target=28) -> dict:
    return create_sample_task(
        name=name, task_type="periodic", period="monthly", target=target, color="#22c55e"
    )


# ── Health Check ─────────────────────────────────────────────


class TestHealth:
    def test_health_endpoint(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ── POST /api/tasks ───────────────────────────────────────────


class TestCreateTask:
    def test_create_once_task(self):
        r = client.post("/api/tasks", json={"name": "Emails beantworten", "type": "once"})
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Emails beantworten"
        assert data["type"] == "once"
        assert data["progress"] == 0
        assert data["status"] == "active"

    def test_create_periodic_task(self):
        r = client.post(
            "/api/tasks",
            json={
                "name": "Täglich lesen",
                "type": "periodic",
                "period": "monthly",
                "target": 28,
                "color": "#22c55e",
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["target"] == 28
        assert data["percentage"] == 0

    def test_create_task_empty_name_fails(self):
        r = client.post("/api/tasks", json={"name": "", "type": "once"})
        assert r.status_code == 422

    def test_create_periodic_without_period_fails(self):
        # Pydantic validator checks this — period required for periodic
        r = client.post("/api/tasks", json={"name": "X", "type": "periodic", "period": None})
        assert r.status_code == 422

    def test_create_task_negative_target_fails(self):
        r = client.post(
            "/api/tasks", json={"name": "X", "type": "periodic", "period": "monthly", "target": -1}
        )
        assert r.status_code == 422


# ── GET /api/tasks ────────────────────────────────────────────


class TestListTasks:
    def test_empty_list(self):
        r = client.get("/api/tasks")
        assert r.status_code == 200
        assert r.json()["data"] == []
        assert r.json()["total"] == 0

    def test_list_returns_all_tasks(self):
        create_sample_task("Task 1")
        create_sample_task("Task 2")
        r = client.get("/api/tasks")
        assert r.json()["total"] == 2

    def test_filter_by_type_periodic(self):
        create_periodic_task()
        create_sample_task("Einmalig")
        r = client.get("/api/tasks?type=periodic")
        data = r.json()["data"]
        assert all(t["type"] == "periodic" for t in data)

    def test_filter_archived_false_default(self):
        task = create_sample_task()
        client.post(f"/api/tasks/{task['id']}/archive")
        r = client.get("/api/tasks")
        ids = [t["id"] for t in r.json()["data"]]
        assert task["id"] not in ids

    def test_filter_archived_true(self):
        task = create_sample_task()
        client.post(f"/api/tasks/{task['id']}/archive")
        r = client.get("/api/tasks?archived=true")
        ids = [t["id"] for t in r.json()["data"]]
        assert task["id"] in ids


# ── GET /api/tasks/{id} ───────────────────────────────────────


class TestGetTask:
    def test_get_existing_task(self):
        task = create_sample_task("Meine Aufgabe")
        r = client.get(f"/api/tasks/{task['id']}")
        assert r.status_code == 200
        assert r.json()["name"] == "Meine Aufgabe"

    def test_get_nonexistent_returns_404(self):
        r = client.get("/api/tasks/99999")
        assert r.status_code == 404


# ── PUT /api/tasks/{id} ───────────────────────────────────────


class TestUpdateTask:
    def test_update_name(self):
        task = create_sample_task("Alt")
        r = client.put(f"/api/tasks/{task['id']}", json={"name": "Neu"})
        assert r.status_code == 200
        assert r.json()["name"] == "Neu"

    def test_partial_update(self):
        task = create_periodic_task(target=10)
        r = client.put(f"/api/tasks/{task['id']}", json={"target": 20})
        assert r.status_code == 200
        assert r.json()["target"] == 20

    def test_update_nonexistent_returns_404(self):
        r = client.put("/api/tasks/99999", json={"name": "X"})
        assert r.status_code == 404

    def test_update_color(self):
        task = create_sample_task()
        r = client.put(f"/api/tasks/{task['id']}", json={"color": "#3b82f6"})
        assert r.json()["color"] == "#3b82f6"


# ── DELETE /api/tasks/{id} ────────────────────────────────────


class TestDeleteTask:
    def test_delete_existing_task(self):
        task = create_sample_task()
        r = client.delete(f"/api/tasks/{task['id']}")
        assert r.status_code == 204
        r2 = client.get(f"/api/tasks/{task['id']}")
        assert r2.status_code == 404

    def test_delete_nonexistent_returns_404(self):
        r = client.delete("/api/tasks/99999")
        assert r.status_code == 404


# ── POST /api/tasks/{id}/checkin ─────────────────────────────


class TestCheckIn:
    def test_checkin_increments_progress(self):
        task = create_periodic_task(target=5)
        r = client.post(
            f"/api/tasks/{task['id']}/checkin", json={"checkin_date": str(date.today())}
        )
        assert r.status_code == 200
        assert r.json()["progress"] == 1

    def test_checkin_idempotent_same_day(self):
        """Zweiter Check-in am selben Tag darf Fortschritt nicht erhöhen."""
        task = create_periodic_task(target=5)
        today = str(date.today())
        client.post(f"/api/tasks/{task['id']}/checkin", json={"checkin_date": today})
        r = client.post(f"/api/tasks/{task['id']}/checkin", json={"checkin_date": today})
        assert r.json()["progress"] == 1  # nicht 2!

    def test_checkin_completes_task_when_target_reached(self):
        task = create_periodic_task(target=1)
        r = client.post(
            f"/api/tasks/{task['id']}/checkin", json={"checkin_date": str(date.today())}
        )
        assert r.json()["status"] == "completed"

    def test_checkin_stores_date_in_checkins_list(self):
        task = create_periodic_task(target=5)
        today = str(date.today())
        r = client.post(f"/api/tasks/{task['id']}/checkin", json={"checkin_date": today})
        assert today in r.json()["checkins"]

    def test_checkin_nonexistent_task_404(self):
        r = client.post("/api/tasks/99999/checkin", json={"checkin_date": str(date.today())})
        assert r.status_code == 404

    def test_undo_checkin_decrements_progress(self):
        task = create_periodic_task(target=5)
        today = str(date.today())
        client.post(f"/api/tasks/{task['id']}/checkin", json={"checkin_date": today})
        r = client.delete(f"/api/tasks/{task['id']}/checkin?checkin_date={today}")
        assert r.status_code == 200
        assert r.json()["progress"] == 0


# ── POST /api/tasks/{id}/archive ─────────────────────────────


class TestArchive:
    def test_archive_task(self):
        task = create_sample_task()
        r = client.post(f"/api/tasks/{task['id']}/archive")
        assert r.status_code == 200
        assert r.json()["archived"] is True
        assert r.json()["status"] == "archived"

    def test_archived_task_not_in_default_list(self):
        task = create_sample_task()
        client.post(f"/api/tasks/{task['id']}/archive")
        r = client.get("/api/tasks")
        ids = [t["id"] for t in r.json()["data"]]
        assert task["id"] not in ids


# ── GET /api/statistics/monthly ──────────────────────────────


class TestStatistics:
    def test_stats_empty_db(self):
        r = client.get("/api/statistics/monthly")
        assert r.status_code == 200
        data = r.json()
        assert data["total_tasks"] == 0
        assert data["longest_streak"] == 0

    def test_stats_counts_tasks(self):
        create_sample_task("T1")
        create_periodic_task("H1")
        r = client.get("/api/statistics/monthly")
        data = r.json()
        assert data["total_tasks"] == 2
        assert data["periodic_habits"] == 1

    def test_stats_completed_count(self):
        task = create_periodic_task(target=1)
        client.post(f"/api/tasks/{task['id']}/checkin", json={"checkin_date": str(date.today())})
        r = client.get("/api/statistics/monthly")
        assert r.json()["completed_tasks"] == 1

    def test_stats_monthly_data_has_7_months(self):
        r = client.get("/api/statistics/monthly")
        assert len(r.json()["monthly_data"]) == 7

    def test_stats_habits_list_contains_periodic_only(self):
        create_periodic_task("Gewohnheit")
        create_sample_task("Einmalig")
        r = client.get("/api/statistics/monthly")
        habits = r.json()["habits"]
        assert len(habits) == 1
        assert habits[0]["name"] == "Gewohnheit"
