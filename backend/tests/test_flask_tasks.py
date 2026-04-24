"""Flask task endpoint coverage for the incremental migration path."""

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import service
from backend.flask_app import create_app
from backend.models import Base
from backend.schemas import TaskCreate


@pytest.fixture
def test_app():
    db_path = Path(tempfile.gettempdir()) / f"test_smarthabit_flask_{uuid4().hex}.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    app = create_app({"INITIALIZE_DB": False, "SESSION_FACTORY": test_session_local})
    try:
        yield app, test_session_local
    finally:
        test_engine.dispose()
        if db_path.exists():
            db_path.unlink()


def test_flask_list_tasks_empty(test_app):
    app, _ = test_app

    with app.test_client() as client:
        response = client.get("/api/tasks")

    assert response.status_code == 200
    assert response.get_json() == {"data": [], "total": 0}


def test_flask_list_tasks_filters_archived(test_app):
    app, test_session_local = test_app

    db = test_session_local()
    try:
        task = service.create_task(db, TaskCreate(name="Archived task", type="once"))
        service.archive_task(db, task.id)
    finally:
        db.close()

    with app.test_client() as client:
        default_response = client.get("/api/tasks")
        archived_response = client.get("/api/tasks?archived=true")

    assert default_response.status_code == 200
    assert default_response.get_json() == {"data": [], "total": 0}

    archived_payload = archived_response.get_json()
    assert archived_response.status_code == 200
    assert archived_payload["total"] == 1
    assert archived_payload["data"][0]["name"] == "Archived task"
    assert archived_payload["data"][0]["archived"] is True


def test_flask_get_task_by_id(test_app):
    app, test_session_local = test_app

    db = test_session_local()
    try:
        task = service.create_task(db, TaskCreate(name="Fetch me", type="once"))
        task_id = task.id
    finally:
        db.close()

    with app.test_client() as client:
        response = client.get(f"/api/tasks/{task_id}")

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["id"] == task_id
    assert payload["name"] == "Fetch me"
    assert payload["type"] == "once"


def test_flask_get_task_by_id_returns_404(test_app):
    app, _ = test_app

    with app.test_client() as client:
        response = client.get("/api/tasks/99999")

    assert response.status_code == 404
    assert response.get_json() == {"detail": "Task 99999 nicht gefunden"}


def test_flask_create_once_task(test_app):
    app, _ = test_app

    with app.test_client() as client:
        response = client.post("/api/tasks", json={"name": "Created in Flask", "type": "once"})

    payload = response.get_json()
    assert response.status_code == 201
    assert payload["name"] == "Created in Flask"
    assert payload["type"] == "once"
    assert payload["progress"] == 0
    assert payload["status"] == "active"


def test_flask_create_task_empty_name_fails(test_app):
    app, _ = test_app

    with app.test_client() as client:
        response = client.post("/api/tasks", json={"name": "", "type": "once"})

    payload = response.get_json()
    assert response.status_code == 422
    assert payload["detail"] == "Validation failed"
    assert len(payload["errors"]) >= 1


def test_flask_create_periodic_without_period_fails(test_app):
    app, _ = test_app

    with app.test_client() as client:
        response = client.post("/api/tasks", json={"name": "Habit", "type": "periodic"})

    payload = response.get_json()
    assert response.status_code == 422
    assert payload["detail"] == "Validation failed"
    assert len(payload["errors"]) >= 1


def test_flask_update_task_name(test_app):
    app, test_session_local = test_app

    db = test_session_local()
    try:
        task = service.create_task(db, TaskCreate(name="Original", type="once"))
        task_id = task.id
    finally:
        db.close()

    with app.test_client() as client:
        response = client.put(f"/api/tasks/{task_id}", json={"name": "Updated"})

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["id"] == task_id
    assert payload["name"] == "Updated"
    assert payload["type"] == "once"


def test_flask_update_task_partial_fields(test_app):
    app, test_session_local = test_app

    db = test_session_local()
    try:
        task = service.create_task(
            db,
            TaskCreate(name="Periodic", type="periodic", period="weekly", target=5),
        )
        task_id = task.id
    finally:
        db.close()

    with app.test_client() as client:
        response = client.put(
            f"/api/tasks/{task_id}",
            json={"target": 12, "color": "#3b82f6"},
        )

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["target"] == 12
    assert payload["color"] == "#3b82f6"
    assert payload["period"] == "weekly"


def test_flask_update_task_returns_404(test_app):
    app, _ = test_app

    with app.test_client() as client:
        response = client.put("/api/tasks/99999", json={"name": "Missing"})

    assert response.status_code == 404
    assert response.get_json() == {"detail": "Task 99999 nicht gefunden"}


def test_flask_update_task_validation_error(test_app):
    app, test_session_local = test_app

    db = test_session_local()
    try:
        task = service.create_task(db, TaskCreate(name="Needs validation", type="once"))
        task_id = task.id
    finally:
        db.close()

    with app.test_client() as client:
        response = client.put(f"/api/tasks/{task_id}", json={"name": ""})

    payload = response.get_json()
    assert response.status_code == 422
    assert payload["detail"] == "Validation failed"
    assert len(payload["errors"]) >= 1
