"""
Business-Logik – Service Layer
Alle Berechnungen passieren hier, NICHT in den Routen.
Dadurch sind Unittests ohne HTTP-Stack möglich.
"""
from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import extract, func

from .models import Task, CheckIn, TaskType, TaskStatus, Period
from .schemas import (
    TaskCreate, TaskUpdate, MonthlyStats,
    HabitStat, MonthlyDataPoint
)


# ── Task CRUD ─────────────────────────────────────────────────

def get_tasks(
    db: Session,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    archived: bool = False,
    month: Optional[str] = None,   # Format: "2026-04"
) -> List[Task]:
    """GET /api/tasks — mit optionalen Filtern."""
    q = db.query(Task).filter(Task.archived == archived)

    if task_type:
        q = q.filter(Task.type == task_type)

    if month:
        try:
            year, m = map(int, month.split("-"))
            q = q.filter(
                extract("year", Task.due_date) == year,
                extract("month", Task.due_date) == m,
            )
        except ValueError:
            pass  # ungültiges Format ignorieren

    tasks = q.order_by(Task.created_at.desc()).all()

    # Status-Filter wird nach Abruf angewendet (computed property)
    if status == "completed":
        tasks = [t for t in tasks if t.progress >= t.target]
    elif status == "overdue":
        tasks = [t for t in tasks if _is_overdue(t)]
    elif status == "active":
        tasks = [t for t in tasks if not t.progress >= t.target and not _is_overdue(t)]

    return tasks


def get_task_by_id(db: Session, task_id: int) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id).first()


def create_task(db: Session, payload: TaskCreate) -> Task:
    """POST /api/tasks"""
    task = Task(
        name=payload.name,
        type=payload.type,
        period=payload.period,
        target=payload.target,
        color=payload.color,
        due_date=payload.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task_id: int, payload: TaskUpdate) -> Optional[Task]:
    """PUT /api/tasks/{id}"""
    task = get_task_by_id(db, task_id)
    if not task:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int) -> bool:
    """DELETE /api/tasks/{id}"""
    task = get_task_by_id(db, task_id)
    if not task:
        return False
    db.delete(task)
    db.commit()
    return True


def archive_task(db: Session, task_id: int) -> Optional[Task]:
    """POST /api/tasks/{id}/archive — weiches Löschen"""
    task = get_task_by_id(db, task_id)
    if not task:
        return None
    task.archived = True
    db.commit()
    db.refresh(task)
    return task


# ── Check-In Logic ────────────────────────────────────────────

def checkin_task(db: Session, task_id: int, checkin_date: date) -> Optional[Task]:
    """
    POST /api/tasks/{id}/checkin
    Business-Regeln:
      - Pro Tag max. 1 Check-in
      - Fortschritt wird erhöht
      - Bei Erreichen des Ziels: Status → completed
    """
    task = get_task_by_id(db, task_id)
    if not task:
        return None

    # Duplikat-Check
    existing = db.query(CheckIn).filter(
        CheckIn.task_id == task_id,
        CheckIn.checkin_date == checkin_date,
    ).first()

    if existing:
        return task  # idempotent: kein Fehler, einfach zurückgeben

    checkin = CheckIn(task_id=task_id, checkin_date=checkin_date)
    db.add(checkin)

    task.progress = min(task.progress + 1, task.target)
    if task.progress >= task.target:
        task.status = TaskStatus.completed

    db.commit()
    db.refresh(task)
    return task


def undo_checkin(db: Session, task_id: int, checkin_date: date) -> Optional[Task]:
    """DELETE /api/tasks/{id}/checkin — Check-in rückgängig machen"""
    task = get_task_by_id(db, task_id)
    if not task:
        return None

    checkin = db.query(CheckIn).filter(
        CheckIn.task_id == task_id,
        CheckIn.checkin_date == checkin_date,
    ).first()

    if checkin:
        db.delete(checkin)
        task.progress = max(task.progress - 1, 0)
        if task.progress < task.target:
            task.status = TaskStatus.active
        db.commit()
        db.refresh(task)

    return task


# ── Statistics ────────────────────────────────────────────────

def get_monthly_stats(db: Session) -> MonthlyStats:
    """GET /api/statistics/monthly"""
    all_tasks = db.query(Task).filter(Task.archived == False).all()

    total = len(all_tasks)
    completed = sum(1 for t in all_tasks if t.progress >= t.target)
    archived_count = db.query(Task).filter(Task.archived == True).count()
    periodic = [t for t in all_tasks if t.type == TaskType.periodic]
    overdue = sum(1 for t in all_tasks if _is_overdue(t))

    habits = [
        HabitStat(
            id=t.id,
            name=t.name,
            progress=t.progress,
            target=t.target,
            percentage=round(t.progress / t.target * 100) if t.target else 0,
            color=t.color,
        )
        for t in periodic
    ]

    monthly_data = _build_monthly_data(db)
    streak = _calc_longest_streak(db)

    return MonthlyStats(
        total_tasks=total,
        completed_tasks=completed,
        active_tasks=total - completed,
        archived_tasks=archived_count,
        periodic_habits=len(periodic),
        overdue_tasks=overdue,
        longest_streak=streak,
        habits=habits,
        monthly_data=monthly_data,
    )


# ── Interne Hilfsfunktionen (für Unittests direkt testbar) ────

def _is_overdue(task: Task) -> bool:
    """
    Business-Regel: Eine Aufgabe gilt als überfällig wenn:
    - due_date gesetzt und bereits vergangen
    - Fortschritt noch nicht abgeschlossen
    """
    if not task.due_date:
        return False
    if task.progress >= task.target:
        return False
    return task.due_date < date.today()


def _calc_progress_percentage(progress: int, target: int) -> int:
    """Fortschritt in Prozent – sicher gegen Division durch 0."""
    if target <= 0:
        return 0
    return min(round(progress / target * 100), 100)


def _calc_longest_streak(db: Session) -> int:
    """
    Berechnet die längste aufeinanderfolgende Check-in-Kette über alle Tasks.
    Kurs-Anforderung: Cross-month calculation.
    """
    all_dates = db.query(func.distinct(CheckIn.checkin_date)).all()
    date_set = {row[0] for row in all_dates}

    if not date_set:
        return 0

    sorted_dates = sorted(date_set)
    max_streak = 1
    current = 1

    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 1

    return max_streak


def _build_monthly_data(db: Session) -> List[MonthlyDataPoint]:
    """Aggregiert Check-ins pro Monat für die letzten 7 Monate."""
    today = date.today()
    result = []

    month_labels = [
        "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
        "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"
    ]

    for offset in range(6, -1, -1):
        # Monat berechnen (rückwärts)
        year = today.year
        month = today.month - offset
        while month <= 0:
            month += 12
            year -= 1

        month_str = f"{year}-{month:02d}"
        count = db.query(CheckIn).filter(
            extract("year", CheckIn.checkin_date) == year,
            extract("month", CheckIn.checkin_date) == month,
        ).count()

        result.append(MonthlyDataPoint(
            month=month_str,
            label=month_labels[month - 1],
            checkin_count=count,
        ))

    return result
