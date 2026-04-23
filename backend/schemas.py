"""
Pydantic-Schemas – API-Kontrakt für Request & Response
Strikte Validierung aller Ein- und Ausgaben.
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from .models import TaskType, Period, TaskStatus


# ── Task Schemas ──────────────────────────────────────────────

class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, json_schema_extra={"example": "Täglich lesen"})
    type: TaskType = TaskType.once
    period: Optional[Period] = None
    target: int = Field(default=1, ge=1, le=1000)
    color: str = Field(default="#22c55e")
    due_date: Optional[date] = None

    @field_validator("period")
    @classmethod
    def period_required_for_periodic(cls, v, info):
        if info.data.get("type") == TaskType.periodic and v is None:
            raise ValueError("period muss bei Typ 'periodic' angegeben werden")
        return v


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[TaskType] = None
    period: Optional[Period] = None
    target: Optional[int] = Field(None, ge=1, le=1000)
    color: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    archived: Optional[bool] = None


class TaskResponse(BaseModel):
    id: int
    name: str
    type: str
    period: Optional[str]
    target: int
    progress: int
    percentage: int
    color: str
    due_date: Optional[date]
    status: str
    archived: bool
    checkins: List[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ── CheckIn Schemas ───────────────────────────────────────────

class CheckInCreate(BaseModel):
    checkin_date: date = Field(default_factory=date.today)


class CheckInResponse(BaseModel):
    id: int
    task_id: int
    checkin_date: date
    created_at: Optional[datetime]

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
    month: str          # "2026-04"
    label: str          # "Apr"
    checkin_count: int


class MonthlyStats(BaseModel):
    total_tasks: int
    completed_tasks: int
    active_tasks: int
    archived_tasks: int
    periodic_habits: int
    overdue_tasks: int
    longest_streak: int
    habits: List[HabitStat]
    monthly_data: List[MonthlyDataPoint]


# ── Generic Response Wrappers ─────────────────────────────────

class TaskListResponse(BaseModel):
    data: List[TaskResponse]
    total: int


class MessageResponse(BaseModel):
    message: str
    id: Optional[int] = None
