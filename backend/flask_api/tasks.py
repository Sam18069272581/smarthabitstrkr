"""Flask task endpoints migrated incrementally from FastAPI."""

import json
from http import HTTPStatus

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from .. import service
from ..schemas import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate

tasks_bp = Blueprint("tasks", __name__)


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_session():
    session_factory = current_app.config["SESSION_FACTORY"]
    return session_factory()


def _validation_error_response(exc: ValidationError):
    errors = json.loads(exc.json())
    return (
        jsonify({"detail": "Validation failed", "errors": errors}),
        HTTPStatus.UNPROCESSABLE_ENTITY,
    )


@tasks_bp.get("/api/tasks")
def list_tasks():
    status = request.args.get("status")
    task_type = request.args.get("type")
    archived = _parse_bool(request.args.get("archived"), default=False)
    month = request.args.get("month")

    db = _get_session()
    try:
        tasks = service.get_tasks(
            db,
            status=status,
            task_type=task_type,
            archived=archived,
            month=month,
        )
        payload = TaskListResponse(
            data=[TaskResponse(**task.to_dict()) for task in tasks],
            total=len(tasks),
        )
        return jsonify(payload.model_dump(mode="json"))
    finally:
        db.close()


@tasks_bp.post("/api/tasks")
def create_task():
    payload = request.get_json(silent=True) or {}
    try:
        task_create = TaskCreate.model_validate(payload)
    except ValidationError as exc:
        return _validation_error_response(exc)

    db = _get_session()
    try:
        task = service.create_task(db, task_create)
        response = TaskResponse(**task.to_dict())
        return jsonify(response.model_dump(mode="json")), HTTPStatus.CREATED
    finally:
        db.close()


@tasks_bp.get("/api/tasks/<int:task_id>")
def get_task(task_id: int):
    db = _get_session()
    try:
        task = service.get_task_by_id(db, task_id)
        if not task:
            return jsonify({"detail": f"Task {task_id} nicht gefunden"}), 404

        payload = TaskResponse(**task.to_dict())
        return jsonify(payload.model_dump(mode="json"))
    finally:
        db.close()


@tasks_bp.put("/api/tasks/<int:task_id>")
def update_task(task_id: int):
    payload = request.get_json(silent=True) or {}
    try:
        task_update = TaskUpdate.model_validate(payload)
    except ValidationError as exc:
        return _validation_error_response(exc)

    db = _get_session()
    try:
        task = service.update_task(db, task_id, task_update)
        if not task:
            return jsonify({"detail": f"Task {task_id} nicht gefunden"}), HTTPStatus.NOT_FOUND

        response = TaskResponse(**task.to_dict())
        return jsonify(response.model_dump(mode="json"))
    finally:
        db.close()
