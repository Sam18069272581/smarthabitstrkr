"""
Datenbankmodelle – SmartHabitTrkr
SQLAlchemy ORM für SQLite
"""
from datetime import date, datetime
from sqlalchemy import (
    Column, Integer, String, Date, DateTime,
    Boolean, Enum, ForeignKey, func
)
from sqlalchemy.orm import relationship, DeclarativeBase
import enum


class Base(DeclarativeBase):
    pass


class TaskType(str, enum.Enum):
    once = "once"
    periodic = "periodic"


class Period(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class TaskStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    archived = "archived"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(Enum(TaskType), nullable=False, default=TaskType.once)
    period = Column(Enum(Period), nullable=True)          # nur bei periodic
    target = Column(Integer, nullable=False, default=1)   # Ziel-Anzahl
    progress = Column(Integer, nullable=False, default=0) # aktueller Stand
    color = Column(String(10), default="#22c55e")
    due_date = Column(Date, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.active)
    archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    checkins = relationship(
        "CheckIn", back_populates="task",
        cascade="all, delete-orphan"
    )

    @property
    def computed_status(self) -> TaskStatus:
        """Business-Logik: Status wird serverseitig berechnet."""
        if self.archived:
            return TaskStatus.archived
        if self.progress >= self.target:
            return TaskStatus.completed
        if self.due_date and self.due_date < date.today():
            return TaskStatus.active   # overdue bleibt active, Frontend zeigt Warnung
        return TaskStatus.active

    def to_dict(self) -> dict:
        checkin_dates = [c.checkin_date.isoformat() for c in self.checkins]
        pct = round(self.progress / self.target * 100) if self.target else 0
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "period": self.period.value if self.period else None,
            "target": self.target,
            "progress": self.progress,
            "percentage": pct,
            "color": self.color,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.computed_status.value,
            "archived": self.archived,
            "checkins": checkin_dates,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CheckIn(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    checkin_date = Column(Date, nullable=False, default=date.today)
    created_at = Column(DateTime, default=func.now())

    task = relationship("Task", back_populates="checkins")
