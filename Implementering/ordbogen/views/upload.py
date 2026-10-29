"""Uploading a vocabulary as Turtle."""

from __future__ import annotations

from flask import Blueprint, Request, current_app, jsonify, render_template, request

from ..ingest import (
    InvalidNamespace,
    InvalidTurtle,
    VocabularyForm,
    detect_ontology,
    ingest_turtle,
    is_safe_iri,
    parse_turtle,
    read_vocabulary_metadata,
)
from ..models import Term, local_name, prefer_language
from . import current_repository

bp = Blueprint("upload", __name__)

# ids of the inputs that field errors attach to (and the error summary links to)
TTL_FIELD = "form-fileinput"
NAMESPACE_FIELD = "ontology"
DOWNLOAD_URL_FIELD = "download_url"
PAGE_FIELD = "page"

MISSING_TTL = "Vælg en TTL-fil, eller indsæt TTL-tekst."
MISSING_NAMESPACE = (
    "Angiv et namespace, eller tryk på Gæt namespace for at få et forslag."
)
NOT_A_WEB_URL = "Angiv en hel webadresse, der starter med http:// eller https://."


@bp.route("/upload", methods=["GET", "POST"])
def index():
    """Upload TTL (as a file or pasted text) into a new named graph."""
    errors: dict[str, str] = {}  # input id -> message, in form order
    error = None  # a failure that is not about the user's input
    result = None
    ontology = ""
    vocabulary = VocabularyForm()

    if request.method == "POST":
        ttl_text = _submitted_turtle(request)
        ontology = request.form.get("ontology", "").strip()
        vocabulary = _submitted_vocabulary(request)

        if not ttl_text.strip():
            errors[TTL_FIELD] = MISSING_TTL
        if not ontology:
            errors[NAMESPACE_FIELD] = MISSING_NAMESPACE
        if vocabulary.download_url and not _is_web_url(vocabulary.download_url):
            errors[DOWNLOAD_URL_FIELD] = NOT_A_WEB_URL
        if vocabulary.page and not _is_web_url(vocabulary.page):
            errors[PAGE_FIELD] = NOT_A_WEB_URL

        if not errors:
            try:
                result = ingest_turtle(
                    current_repository(), ttl_text, ontology, vocabulary
                )
            except InvalidTurtle as exc:
                errors[TTL_FIELD] = str(exc)
            except InvalidNamespace as exc:  # includes AlreadyUploaded
                errors[NAMESPACE_FIELD] = str(exc)
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
        # (item type name, count) for the success message, e.g. ("Class", 12)
        item_counts=sorted(
            (local_name(item_type), count)
            for item_type, count in (result.item_counts if result else {}).items()
        ),
        ttl_text=request.form.get("ttl_text", "") if keep_form else "",
        ontology=ontology if keep_form else "",
        vocabulary=vocabulary if keep_form else VocabularyForm(),
        ttl_field=TTL_FIELD,
        namespace_field=NAMESPACE_FIELD,
        download_url_field=DOWNLOAD_URL_FIELD,
        page_field=PAGE_FIELD,
        missing_ttl=MISSING_TTL,
        missing_namespace=MISSING_NAMESPACE,
    )


@bp.route("/upload/guess", methods=["POST"])
def guess():
    """Suggest a namespace, label, description and version for the submitted TTL.

    The values are read from the file's owl:Ontology. Never writes to the store.
    """
    ttl_text = _submitted_turtle(request)
    if not ttl_text.strip():
        return jsonify(field=TTL_FIELD, error=MISSING_TTL), 400

    try:
        graph = parse_turtle(ttl_text)
    except InvalidTurtle as exc:
        return jsonify(field=TTL_FIELD, error=str(exc)), 400

    namespace = detect_ontology(graph)
    # Without an owl:Ontology, read the header of the namespace the user typed.
    header = read_vocabulary_metadata(
        graph, namespace or request.form.get("ontology", "")
    )
    return jsonify(
        namespace=namespace,
        label=_preferred_text(header.labels),
        description=_preferred_text(header.descriptions),
        version=_preferred_text(header.versions),
    )


def _submitted_turtle(req: Request) -> str:
    """Return the submitted Turtle: an uploaded file wins over pasted text."""
    uploaded = req.files.get("file")
    if uploaded and uploaded.filename:
        text = uploaded.read().decode("utf-8", errors="replace")
        if text.strip():
            return text
    return req.form.get("ttl_text", "")


def _submitted_vocabulary(req: Request) -> VocabularyForm:
    """The "Om vokabularet" fields. The ingest code never sees the request."""
    return VocabularyForm(
        label=req.form.get("label", "").strip(),
        description=req.form.get("description", "").strip(),
        version=req.form.get("version", "").strip(),
        download_url=req.form.get("download_url", "").strip(),
        page=req.form.get("page", "").strip(),
    )


def _is_web_url(text: str) -> bool:
    """Whether the text is an absolute http(s) URL that is safe to store as an IRI."""
    return text.startswith(("http://", "https://")) and is_safe_iri(text)


def _preferred_text(literals) -> str:
    """The value of the literal in the best language, or "" if there are none."""
    terms = prefer_language(
        [Term(str(lit), lang=lit.language or "") for lit in literals]
    )
    return terms[0].value if terms else ""
