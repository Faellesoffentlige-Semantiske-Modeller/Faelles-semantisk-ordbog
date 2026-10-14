"""HTTP layer: one blueprint per group of routes.

View functions read request data, delegate to the repository, and render a
template. They hold no SPARQL.
"""

from __future__ import annotations

from flask import current_app

from ..config import Config
from ..repository import DictionaryRepository


def current_config() -> Config:
    """The configuration the active app was created with."""
    return current_app.config["ORDBOGEN"]


def current_repository() -> DictionaryRepository:
    """A repository bound to the active app's configuration."""
    return DictionaryRepository(current_config())
