"""
Demo-Daten – füllt eine leere Datenbank mit Beispielaufgaben.
Wird nur beim Start mit DEMO_SEED=1 ausgeführt (im Docker-Image standardmäßig aktiv).
Alle Daten sind relativ zum heutigen Datum, damit Kalender und Statistiken immer gefüllt sind.
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from .models import CheckIn, Period, Task, TaskStatus, TaskType


def seed_demo_data(db: Session, today: date | None = None) -> bool:
    """Legt Beispiel-Tasks samt Check-ins an. Gibt False zurück, wenn bereits Daten existieren."""
    if db.query(Task).first() is not None:
        return False

    today = today or date.today()

    def days_ago(n: int) -> date:
        return today - timedelta(days=n)

    # ── Gewohnheiten mit Check-in-Historie (heute bleibt offen zum Ausprobieren) ──
    habits = [
        ("30 Minuten lesen", Period.monthly, 30, "#22c55e", [days_ago(n) for n in range(1, 13)]),
        (
            "Joggen (3x pro Woche)",
            Period.weekly,
            100,
            "#3b82f6",
            [days_ago(n) for n in range(1, 180) if n % 7 in (1, 3, 5)],
        ),
        ("Meditation", Period.daily, 60, "#8b5cf6", [days_ago(n) for n in range(2, 42, 2)]),
        (
            "2 Liter Wasser trinken",
            Period.daily,
            30,
            "#06b6d4",
            [days_ago(n) for n in range(1, 31) if n not in (6, 13, 20)],
        ),
    ]
    for name, period, target, color, checkin_dates in habits:
        progress = min(len(checkin_dates), target)
        db.add(
            Task(
                name=name,
                type=TaskType.periodic,
                period=period,
                target=target,
                progress=progress,
                color=color,
                status=TaskStatus.completed if progress >= target else TaskStatus.active,
                checkins=[CheckIn(checkin_date=d) for d in checkin_dates],
            )
        )

    # ── Einmalige Aufgaben: heute, bald, überfällig, erledigt, archiviert ──
    once_tasks = [
        ("Wocheneinkauf erledigen", today, "#22c55e", False, False),
        ("Präsentation Web-Technologien vorbereiten", days_ago(-3), "#f59e0b", False, False),
        ("Steuererklärung einreichen", days_ago(-10), "#8b5cf6", False, False),
        ("Zahnarzttermin vereinbaren", days_ago(2), "#ef4444", False, False),
        ("Bewerbung abschicken", days_ago(5), "#3b82f6", True, False),
        ("Alte Notizen aufräumen", days_ago(20), "#64748b", True, True),
    ]
    for name, due_date, color, done, archived in once_tasks:
        db.add(
            Task(
                name=name,
                type=TaskType.once,
                target=1,
                progress=1 if done else 0,
                color=color,
                due_date=due_date,
                status=TaskStatus.completed if done else TaskStatus.active,
                archived=archived,
            )
        )

    db.commit()
    return True
