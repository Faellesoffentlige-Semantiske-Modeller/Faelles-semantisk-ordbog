"""Uploading a vocabulary as Turtle."""

from __future__ import annotations

from flask import Blueprint, Request, current_app, render_template, request

from ..ingest import ingest_turtle
from . import current_repository

bp = Blueprint("upload", __name__)


@bp.route("/upload", methods=["GET", "POST"])
def index():
    """Upload TTL (as a file or pasted text) into a new named graph."""
    error = None
    result = None

    if request.method == "POST":
        ttl_text = _submitted_turtle(request)
        # Optional manual override of the ontology namespace.
        ontology_override = request.form.get("ontology", "").strip()

        if not ttl_text.strip():
            error = "Angiv enten en TTL-fil eller indsæt TTL-tekst."
        else:
            try:
                result = ingest_turtle(
                    current_repository(), ttl_text, ontology_override
                )
            except Exception as exc:  # noqa: BLE001 - surface the error in the UI
                current_app.logger.exception("Vocabulary ingest failed")
                error = str(exc)

    return render_template("upload.html", error=error, result=result)


def _submitted_turtle(req: Request) -> str:
    """Return the submitted Turtle: an uploaded file wins over pasted text."""
    uploaded = req.files.get("file")
    if uploaded and uploaded.filename:
        text = uploaded.read().decode("utf-8", errors="replace")
        if text.strip():
            return text
    return req.form.get("ttl_text", "")
