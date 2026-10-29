"""Application configuration, resolved from the environment.

Held as a plain object so an app can be constructed against a different
endpoint without touching ``os.environ``.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

# Base IRI for the graphs and resources created from uploaded content (`csd:`).
GRAPH_BASE = "https://data.gov.dk/dataset/dictionary/common-semantic-dictionary/"

DEFAULT_QUERY_ENDPOINT = "http://fuseki2:3030/Metadataordbog/sparql"


def _sibling_update_endpoint(query_endpoint: str) -> str:
    """Return the /update path sitting next to a Fuseki query endpoint."""
    if query_endpoint.endswith("/sparql"):
        return query_endpoint[: -len("/sparql")] + "/update"
    return query_endpoint + "/update"


def _read_secret_file(path: str | None) -> str | None:
    """Read a Docker secret file, or return None if it is absent."""
    if path and os.path.exists(path):
        return Path(path).read_text(encoding="utf-8").strip()
    return None


@dataclass
class Config:
    """Everything the app needs to talk to Fuseki and mint IRIs."""

    query_endpoint: str = DEFAULT_QUERY_ENDPOINT
    update_endpoint: str | None = None
    user: str | None = None
    password: str | None = None
    # Base IRI for uploaded source graphs, the per-element graphs split out of
    # them, and evaluations. Dictionary items use the element IRI itself.
    graph_base: str = GRAPH_BASE

    def __post_init__(self) -> None:
        if not self.update_endpoint:
            self.update_endpoint = _sibling_update_endpoint(self.query_endpoint)

    @property
    def auth(self) -> tuple[str, str] | None:
        """Credentials tuple for rdflib's store, or None if unauthenticated."""
        if self.user and self.password:
            return (self.user, self.password)
        return None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Config:
        """Build a config from environment variables.

        A password supplied via ``FUSEKI_PASSWORD_FILE`` (a Docker secret)
        takes precedence over ``FUSEKI_PASSWORD``.
        """
        env = os.environ if env is None else env
        password = _read_secret_file(env.get("FUSEKI_PASSWORD_FILE")) or env.get(
            "FUSEKI_PASSWORD"
        )
        return cls(
            query_endpoint=env.get("FUSEKI_ENDPOINT", DEFAULT_QUERY_ENDPOINT),
            update_endpoint=env.get("FUSEKI_UPDATE_ENDPOINT"),
            user=env.get("FUSEKI_USER"),
            password=password,
        )
