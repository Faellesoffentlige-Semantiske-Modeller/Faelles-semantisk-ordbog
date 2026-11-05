"""Browsing the vocabularies (semantic assets) in the dictionary."""

from __future__ import annotations

from flask import Blueprint, current_app, render_template

from . import current_repository

bp = Blueprint("vocabularies", __name__)


@bp.route("/vocabularies", methods=["GET"])
def index():
    """Grid of cards, one per vocabulary, each linking to /items."""
    error = None
    cards = []
    try:
        cards = current_repository().list_vocabularies()
    except Exception as exc:  # noqa: BLE001 - surface the error in the UI
        current_app.logger.exception("Could not list the vocabularies")
        error = str(exc)
    return render_template(
        "vocabularies.html", cards=cards, count=len(cards), error=error
    )
