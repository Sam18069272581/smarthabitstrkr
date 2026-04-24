"""
Pydantic-Schemas – API-Kontrakt für Request & Response
Strikte Validierung aller Ein- und Ausgaben.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from .models import Period, TaskStatus, TaskType

# ── Task Schemas ──────────────────────────────────────────────


class TaskCreate(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=200, json_schema_extra={"example": "Täglich lesen"}
    )
    type: TaskType = TaskType.once
    period: Period | None = None
    target: int = Field(default=1, ge=1, le=1000)
    color: str = Field(default="#22c55e")
    due_date: date | None = None

    @model_validator(mode="after")
    def period_required_for_periodic(self):
        if self.type == TaskType.periodic and self.period is None:
            raise ValueError("period muss bei Typ 'periodic' angegeben werden")
        return self


class TaskUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    type: TaskType | None = None
    period: Period | None = None
    target: int | None = Field(None, ge=1, le=1000)
    color: str | None = None
    due_date: date | None = None
    status: TaskStatus | None = None
    archived: bool | None = None


class TaskResponse(BaseModel):
    id: int
    name: str
    type: str
    period: str | None
    target: int
    progress: int
    percentage: int
    color: str
    due_date: date | None
    status: str
    archived: bool
    checkins: list[str]
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


# ── CheckIn Schemas ───────────────────────────────────────────


class CheckInCreate(BaseModel):
    checkin_date: date = Field(default_factory=date.today)


class CheckInResponse(BaseModel):
    id: int
    task_id: int
    checkin_date: date
    created_at: datetime | None

    model_config = {"from_attributes": True}


# ── Statistics Schemas ────────────────────────────────────────


class HabitStat(BaseModel):
    id: int
    name: str
    progress: int
    target: int
    percentage: int
    color: str


class MonthlyDataPoint(BaseModel):
    month: str  # "2026-04"
    label: str  # "Apr"
    checkin_count: int


class MonthlyStats(BaseModel):
    total_tasks: int
    completed_tasks: int
    active_tasks: int
    archived_tasks: int
    periodic_habits: int
    overdue_tasks: int
    longest_streak: int
    habits: list[HabitStat]
    monthly_data: list[MonthlyDataPoint]


# ── Generic Response Wrappers ─────────────────────────────────


class TaskListResponse(BaseModel):
    data: list[TaskResponse]
    total: int


class MessageResponse(BaseModel):
    message: str
    id: int | None = None
