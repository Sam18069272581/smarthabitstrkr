"""
Unittests – Business-Logik
Testet interne Funktionen in service.py OHNE HTTP-Stack und OHNE echte DB.
Kursanforderung: Backend-Logik muss durch Unittests abgedeckt sein.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

# Direkte Imports der Business-Logik-Funktionen
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.service import (
    _is_overdue,
    _calc_progress_percentage,
    _calc_longest_streak,
)
from backend.models import Task, TaskType, TaskStatus, Period, CheckIn


# ── Hilfsfunktion: Mock-Task erstellen ───────────────────────

def make_task(progress=0, target=10, due_date=None) -> Task:
    task = Task()
    task.progress = progress
    task.target = target
    task.due_date = due_date
    task.type = TaskType.once
    task.archived = False
    return task


# ── _is_overdue() Tests ───────────────────────────────────────

class TestIsOverdue:
    def test_no_due_date_never_overdue(self):
        task = make_task(progress=0, target=5, due_date=None)
        assert _is_overdue(task) is False

    def test_future_due_date_not_overdue(self):
        task = make_task(due_date=date.today() + timedelta(days=7))
        assert _is_overdue(task) is False

    def test_past_due_date_is_overdue(self):
        task = make_task(due_date=date.today() - timedelta(days=1))
        assert _is_overdue(task) is True

    def test_completed_task_not_overdue(self):
        """Abgeschlossene Aufgaben gelten nie als überfällig."""
        task = make_task(progress=10, target=10,
                         due_date=date.today() - timedelta(days=5))
        assert _is_overdue(task) is False

    def test_today_due_not_overdue(self):
        """Heute fällig = noch nicht überfällig."""
        task = make_task(due_date=date.today())
        assert _is_overdue(task) is False


# ── _calc_progress_percentage() Tests ────────────────────────

class TestProgressPercentage:
    def test_zero_progress(self):
        assert _calc_progress_percentage(0, 28) == 0

    def test_half_progress(self):
        assert _calc_progress_percentage(14, 28) == 50

    def test_full_progress(self):
        assert _calc_progress_percentage(28, 28) == 100

    def test_over_target_capped_at_100(self):
        """Darf nie über 100% gehen."""
        assert _calc_progress_percentage(30, 28) == 100

    def test_zero_target_returns_zero(self):
        """Division durch 0 wird sicher abgefangen."""
        assert _calc_progress_percentage(5, 0) == 0

    def test_rounding(self):
        assert _calc_progress_percentage(1, 3) == 33   # 33.33... → 33

    def test_weekly_habit(self):
        assert _calc_progress_percentage(3, 4) == 75


# ── _calc_longest_streak() Tests ─────────────────────────────

class TestLongestStreak:
    def _mock_db(self, dates: list) -> MagicMock:
        """Erstellt eine Mock-DB, die die gegebenen Daten zurückgibt."""
        db = MagicMock()
        db.query.return_value.all.return_value = [(d,) for d in dates]
        return db

    def test_empty_checkins_returns_zero(self):
        db = self._mock_db([])
        assert _calc_longest_streak(db) == 0

    def test_single_day(self):
        db = self._mock_db([date(2026, 4, 1)])
        assert _calc_longest_streak(db) == 1

    def test_consecutive_3_days(self):
        dates = [date(2026, 4, 1), date(2026, 4, 2), date(2026, 4, 3)]
        db = self._mock_db(dates)
        assert _calc_longest_streak(db) == 3

    def test_gap_resets_streak(self):
        dates = [
            date(2026, 4, 1), date(2026, 4, 2),  # streak 2
            date(2026, 4, 5), date(2026, 4, 6), date(2026, 4, 7),  # streak 3
        ]
        db = self._mock_db(dates)
        assert _calc_longest_streak(db) == 3

    def test_cross_month_streak(self):
        """Kursanforderung: Streak über Monatsgrenzen hinweg korrekt berechnen."""
        dates = [
            date(2026, 3, 30),
            date(2026, 3, 31),
            date(2026, 4, 1),
            date(2026, 4, 2),
        ]
        db = self._mock_db(dates)
        assert _calc_longest_streak(db) == 4

    def test_cross_year_streak(self):
        """Streak über Jahresgrenzen (31.12 → 01.01)."""
        dates = [date(2025, 12, 31), date(2026, 1, 1), date(2026, 1, 2)]
        db = self._mock_db(dates)
        assert _calc_longest_streak(db) == 3

    def test_unordered_dates(self):
        """Unsortierte Eingabe muss korrekt verarbeitet werden."""
        dates = [date(2026, 4, 3), date(2026, 4, 1), date(2026, 4, 2)]
        db = self._mock_db(dates)
        assert _calc_longest_streak(db) == 3

    def test_duplicate_dates_handled(self):
        """Doppelte Daten (verschiedene Tasks am gleichen Tag) dürfen Streak nicht aufblasen."""
        dates = [date(2026, 4, 1), date(2026, 4, 1), date(2026, 4, 2)]
        db = self._mock_db(dates)
        assert _calc_longest_streak(db) == 2


# ── Task computed_status Tests ───────────────────────────────

class TestTaskComputedStatus:
    def test_active_task(self):
        task = make_task(progress=5, target=10,
                         due_date=date.today() + timedelta(days=10))
        assert task.computed_status == TaskStatus.active

    def test_completed_when_progress_equals_target(self):
        task = make_task(progress=10, target=10)
        assert task.computed_status == TaskStatus.completed

    def test_archived_overrides_all(self):
        task = make_task(progress=0, target=10,
                         due_date=date.today() - timedelta(days=5))
        task.archived = True
        assert task.computed_status == TaskStatus.archived
