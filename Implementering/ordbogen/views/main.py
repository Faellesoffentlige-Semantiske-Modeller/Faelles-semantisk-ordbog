"""Landing page."""

from __future__ import annotations

from flask import Blueprint, render_template

from . import current_config

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html", endpoint=current_config().query_endpoint)
