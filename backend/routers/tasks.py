"""
Router: /api/tasks
RESTful CRUD nach Kursanforderung
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    TaskCreate, TaskUpdate, TaskResponse,
    TaskListResponse, CheckInCreate, MessageResponse
)
from .. import service

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse, summary="Alle Aufgaben abrufen")
def list_tasks(
    status: Optional[str] = Query(None, description="active | completed | overdue"),
    type: Optional[str] = Query(None, description="once | periodic"),
    archived: bool = Query(False),
    month: Optional[str] = Query(None, description="Format: 2026-04"),
    db: Session = Depends(get_db),
):
    """
    **GET /api/tasks**
    Gibt alle Aufgaben zurück. Optionale Filter:
    - `status`: active, completed, overdue
    - `type`: once, periodic
    - `archived`: true/false
    - `month`: z.B. 2026-04
    """
    tasks = service.get_tasks(db, status=status, task_type=type,
                              archived=archived, month=month)
    return TaskListResponse(
        data=[TaskResponse(**t.to_dict()) for t in tasks],
        total=len(tasks),
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED,
             summary="Neue Aufgabe erstellen")
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """
    **POST /api/tasks**
    Erstellt eine neue Aufgabe oder Gewohnheit.
    """
    task = service.create_task(db, payload)
    return TaskResponse(**task.to_dict())


@router.get("/{task_id}", response_model=TaskResponse, summary="Einzelne Aufgabe abrufen")
def get_task(task_id: int, db: Session = Depends(get_db)):
    """**GET /api/tasks/{id}**"""
    task = service.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} nicht gefunden")
    return TaskResponse(**task.to_dict())


@router.put("/{task_id}", response_model=TaskResponse, summary="Aufgabe aktualisieren")
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    """
    **PUT /api/tasks/{id}**
    Aktualisiert Felder einer Aufgabe (partial update möglich).
    """
    task = service.update_task(db, task_id, payload)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} nicht gefunden")
    return TaskResponse(**task.to_dict())


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Aufgabe löschen")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """**DELETE /api/tasks/{id}**"""
    ok = service.delete_task(db, task_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Task {task_id} nicht gefunden")


@router.post("/{task_id}/archive", response_model=TaskResponse,
             summary="Aufgabe archivieren")
def archive_task(task_id: int, db: Session = Depends(get_db)):
    """**POST /api/tasks/{id}/archive** — weiches Löschen"""
    task = service.archive_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} nicht gefunden")
    return TaskResponse(**task.to_dict())


@router.post("/{task_id}/checkin", response_model=TaskResponse,
             summary="Check-in für heute eintragen")
def checkin(task_id: int, payload: CheckInCreate = CheckInCreate(),
            db: Session = Depends(get_db)):
    """
    **POST /api/tasks/{id}/checkin**
    Trägt einen Check-in ein. Pro Tag max. 1 Check-in (idempotent).
    """
    task = service.checkin_task(db, task_id, payload.checkin_date)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} nicht gefunden")
    return TaskResponse(**task.to_dict())


@router.delete("/{task_id}/checkin", response_model=TaskResponse,
               summary="Check-in rückgängig machen")
def undo_checkin(
    task_id: int,
    checkin_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
):
    """**DELETE /api/tasks/{id}/checkin** — Check-in eines Tages entfernen"""
    task = service.undo_checkin(db, task_id, checkin_date)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} nicht gefunden")
    return TaskResponse(**task.to_dict())
