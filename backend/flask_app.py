"""
Parallel Flask app entrypoint used for incremental migration from FastAPI.
"""

from typing import Any

from flask import Flask

from .database import SessionLocal, create_tables
from .flask_api.health import health_bp
from .flask_api.tasks import tasks_bp


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)

    app.config.setdefault("SESSION_FACTORY", SessionLocal)
    app.config.setdefault("INITIALIZE_DB", True)

    if config:
        app.config.update(config)

    if app.config["INITIALIZE_DB"]:
        create_tables()

    app.register_blueprint(health_bp)
    app.register_blueprint(tasks_bp)

    return app


app = create_app()
