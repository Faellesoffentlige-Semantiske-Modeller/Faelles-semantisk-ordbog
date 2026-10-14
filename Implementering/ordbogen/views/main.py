"""Landing page and the raw graph browsers."""

from __future__ import annotations

from flask import Blueprint, current_app, render_template

from . import current_config, current_repository

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html", endpoint=current_config().query_endpoint)


@bp.route("/default")
def default_graph():
    """Display all triples from the default graph."""
    error = None
    triples = []
    try:
        triples = current_repository().default_graph_triples()
    except Exception as exc:  # noqa: BLE001 - surface the error in the UI
        current_app.logger.exception("Could not read the default graph")
        error = str(exc)
    return render_template(
        "default.html", triples=triples, count=len(triples), error=error
    )


@bp.route("/graph")
def named_graphs():
    """Display the names of all named graphs."""
    error = None
    graphs = []
    try:
        graphs = current_repository().named_graph_names()
    except Exception as exc:  # noqa: BLE001 - surface the error in the UI
        current_app.logger.exception("Could not list the named graphs")
        error = str(exc)
    return render_template(
        "graphs.html", graphs=graphs, count=len(graphs), error=error
    )
