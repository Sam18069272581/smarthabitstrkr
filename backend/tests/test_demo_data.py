"""
Unittests – Demo-Daten
Prüft, dass seed_demo_data() nur leere Datenbanken befüllt und konsistente Daten erzeugt.
"""

import os
import sys
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.demo_data import seed_demo_data
from backend.models import Base, Task, TaskType
from backend.service import _is_overdue

TODAY = date(2026, 4, 22)


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def test_seeds_empty_database(db):
    assert seed_demo_data(db, today=TODAY) is True

    tasks = db.query(Task).all()
    assert any(t.type == TaskType.periodic for t in tasks)
    assert any(t.due_date == TODAY for t in tasks)
    assert any(_is_overdue(t) for t in tasks)
    assert any(t.archived for t in tasks)


def test_progress_matches_checkins(db):
    seed_demo_data(db, today=TODAY)

    for task in db.query(Task).filter(Task.type == TaskType.periodic):
        assert task.progress == min(len(task.checkins), task.target)
        assert all(c.checkin_date < TODAY for c in task.checkins)


def test_does_not_touch_existing_data(db):
    db.add(Task(name="Eigene Aufgabe", type=TaskType.once, target=1))
    db.commit()

    assert seed_demo_data(db, today=TODAY) is False
    assert db.query(Task).count() == 1
