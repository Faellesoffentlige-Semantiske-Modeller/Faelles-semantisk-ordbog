"""Ordbogen — a Flask UI for the Fuseki 'Metadataordbog' dataset."""

from __future__ import annotations

from flask import Flask

from .config import Config

__all__ = ["Config", "create_app"]


def create_app(config: Config | None = None) -> Flask:
    """Build the application.

    Passing a :class:`~ordbogen.config.Config` bypasses the environment and
    points the app at a different endpoint.
    """
    app = Flask(__name__)
    app.config["ORDBOGEN"] = config or Config.from_env()

    from .views import items, main, upload, visualize

    app.register_blueprint(main.bp)
    app.register_blueprint(items.bp)
    app.register_blueprint(upload.bp)
    app.register_blueprint(visualize.bp)

    return app
