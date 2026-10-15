"""Uploading a vocabulary as Turtle."""

from __future__ import annotations

from flask import Blueprint, Request, current_app, jsonify, render_template, request

from ..ingest import InvalidTurtle, guess_namespace, ingest_turtle
from . import current_repository

bp = Blueprint("upload", __name__)

# ids of the inputs that field errors attach to (and the error summary links to)
TTL_FIELD = "form-fileinput"
NAMESPACE_FIELD = "ontology"

MISSING_TTL = "Vælg en TTL-fil, eller indsæt TTL-tekst."
MISSING_NAMESPACE = (
    "Angiv et namespace, eller tryk på Gæt namespace for at få et forslag."
)


@bp.route("/upload", methods=["GET", "POST"])
def index():
    """Upload TTL (as a file or pasted text) into a new named graph."""
    errors: dict[str, str] = {}  # input id -> message, in form order
    error = None  # a failure that is not about the user's input
    result = None
    ontology = ""

    if request.method == "POST":
        ttl_text = _submitted_turtle(request)
        ontology = request.form.get("ontology", "").strip()

        if not ttl_text.strip():
            errors[TTL_FIELD] = MISSING_TTL
        if not ontology:
            errors[NAMESPACE_FIELD] = MISSING_NAMESPACE

        if not errors:
            try:
                result = ingest_turtle(current_repository(), ttl_text, ontology)
            except InvalidTurtle as exc:
                errors[TTL_FIELD] = str(exc)
            except Exception as exc:  # noqa: BLE001 - surface the error in the UI
                current_app.logger.exception("Vocabulary ingest failed")
                error = str(exc)

    # Keep what was typed so a failed submit does not lose it (a chosen file
    # cannot be put back); a finished upload starts over with an empty form.
    keep_form = request.method == "POST" and not result

    return render_template(
        "upload.html",
        errors=errors,
        error=error,
        result=result,
        ttl_text=request.form.get("ttl_text", "") if keep_form else "",
        ontology=ontology if keep_form else "",
        ttl_field=TTL_FIELD,
        namespace_field=NAMESPACE_FIELD,
        missing_ttl=MISSING_TTL,
        missing_namespace=MISSING_NAMESPACE,
    )


@bp.route("/upload/guess", methods=["POST"])
def guess():
    """Suggest a namespace for the submitted TTL. Never writes to the store."""
    ttl_text = _submitted_turtle(request)
    if not ttl_text.strip():
        return jsonify(field=TTL_FIELD, error=MISSING_TTL), 400

    try:
        namespace = guess_namespace(ttl_text)
    except InvalidTurtle as exc:
        return jsonify(field=TTL_FIELD, error=str(exc)), 400

    return jsonify(namespace=namespace)


def _submitted_turtle(req: Request) -> str:
    """Return the submitted Turtle: an uploaded file wins over pasted text."""
    uploaded = req.files.get("file")
    if uploaded and uploaded.filename:
        text = uploaded.read().decode("utf-8", errors="replace")
        if text.strip():
            return text
    return req.form.get("ttl_text", "")
