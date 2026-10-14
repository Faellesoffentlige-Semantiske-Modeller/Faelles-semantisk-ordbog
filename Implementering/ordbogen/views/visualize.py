"""Uploading a vocabulary as Turtle."""

from __future__ import annotations

from flask import Blueprint, Request, current_app, render_template, request

from ..ingest import ingest_turtle
from . import current_repository

bp = Blueprint("visualize", __name__)

@bp.route("/visualize/<item_uuid>", methods=["GET"])
def detail(item_uuid):
    return render_template("visualize.html")
