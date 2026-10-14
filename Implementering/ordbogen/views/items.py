"""Browsing dictionary items and editing their evaluations."""

from __future__ import annotations

from flask import Blueprint, current_app, redirect, render_template, request, url_for
from werkzeug.datastructures import MultiDict

from ..models import EvaluationSubmission
from ..repository import DictionaryRepository
from . import current_repository

bp = Blueprint("items", __name__)


@bp.route("/items")
def index():
    """Grid of cards, one per dictionary item, each linking to its detail page."""
    error = None
    cards = []
    try:
        cards = current_repository().list_items()
    except Exception as exc:  # noqa: BLE001 - surface the error in the UI
        current_app.logger.exception("Could not list the dictionary items")
        error = str(exc)
    return render_template("items.html", cards=cards, count=len(cards), error=error)


@bp.route("/item/<item_uuid>", methods=["GET", "POST"])
def detail(item_uuid):
    """Display a DictionaryItem and let its evaluation be added/edited."""
    repository = current_repository()
    error = None

    if request.method == "POST":
        try:
            _submit_evaluation(repository, item_uuid, request.form)
            return redirect(url_for("items.detail", item_uuid=item_uuid))
        except Exception as exc:  # noqa: BLE001 - surface the error in the UI
            # Fall through to re-render the page with the error shown.
            current_app.logger.exception("Could not save the evaluation")
            error = str(exc)

    item = None
    try:
        item = repository.get_item(item_uuid)
    except Exception as exc:  # noqa: BLE001 - surface the error in the UI
        current_app.logger.exception("Could not read dictionary item %s", item_uuid)
        error = error or str(exc)

    return render_template(
        "item.html",
        error=error,
        item=item,
        item_uuid=item_uuid,
        item_iri=repository.item_iri(item_uuid),
    )


def _submit_evaluation(
    repository: DictionaryRepository, item_uuid: str, form: MultiDict
) -> None:
    """Apply an evaluation form submission to the item.

    The "add" action only creates an empty evaluation; any other action
    writes the submitted field values, creating the evaluation first if the
    item does not have one yet.
    """
    item_iri = repository.item_iri(item_uuid)

    if form.get("action") == "add":
        repository.create_evaluation(item_iri)
        return

    repository.save_evaluation(
        item_iri,
        form.get("evaluation", "").strip(),
        EvaluationSubmission(
            comment=form.get("comment", "").strip(),
            comment_lang=form.get("comment_lang", "").strip(),
            creator=form.get("creator", "").strip(),
            date=form.get("date", "").strip(),
        ),
    )
