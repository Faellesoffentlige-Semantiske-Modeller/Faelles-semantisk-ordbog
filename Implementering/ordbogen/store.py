"""Access to the Fuseki SPARQL endpoints and to the .rq query templates."""

from __future__ import annotations

from importlib import resources
from string import Template

from rdflib.plugins.stores.sparqlstore import SPARQLStore, SPARQLUpdateStore

from .config import Config


def load_sparql(name: str, **params: str) -> str:
    """Load a .rq template from ``ordbogen/sparql/`` and substitute $params.

    SPARQL uses ``?vars``, so ``$placeholder`` names cannot collide with the
    query's own variables.
    """
    source = (
        resources.files(__package__)
        .joinpath("sparql", name)
        .read_text(encoding="utf-8")
    )
    return Template(source).substitute(**params)


def query_store(config: Config) -> SPARQLStore:
    """Return a read-only store connected to the Fuseki query endpoint."""
    kwargs = {"query_endpoint": config.query_endpoint, "returnFormat": "json"}
    if config.auth:
        kwargs["auth"] = config.auth
    return SPARQLStore(**kwargs)


def update_store(config: Config) -> SPARQLUpdateStore:
    """Return a store that can write to the Fuseki update endpoint."""
    kwargs = {
        "query_endpoint": config.query_endpoint,
        "update_endpoint": config.update_endpoint,
        "autocommit": True,
    }
    if config.auth:
        kwargs["auth"] = config.auth
    return SPARQLUpdateStore(**kwargs)
