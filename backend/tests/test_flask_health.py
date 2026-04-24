"""Minimal Flask endpoint coverage for the parallel migration path."""
from backend.flask_app import create_app


def test_flask_health_endpoint():
    app = create_app({"INITIALIZE_DB": False})

    with app.test_client() as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "service": "SmartHabitTrkr",
        "version": "1.0.0",
    }
