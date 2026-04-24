"""Flask health endpoint."""
from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "SmartHabitTrkr", "version": "1.0.0"})
