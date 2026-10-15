"""Ingesting an uploaded vocabulary into the dictionary."""

from __future__ import annotations

import re
from dataclasses import dataclass

from rdflib import Graph
from rdflib.namespace import OWL, RDF

from .repository import DictionaryRepository


@dataclass
class IngestResult:
    """What a successful ingest produced, for display on the upload page."""

    graph_uri: str
    ontology: str
    triple_count: int


def detect_ontology(graph: Graph) -> str | None:
    """Return the IRI of the first owl:Ontology in the graph, or None."""
    for subject in graph.subjects(RDF.type, OWL.Ontology):
        return str(subject)
    return None


class InvalidTurtle(ValueError):
    """The submitted text is not valid Turtle. The message is shown to the user."""


def parse_turtle(ttl_text: str) -> Graph:
    """Parse Turtle into a graph.

    Raises:
        InvalidTurtle with a user-facing message if the text cannot be parsed.
    """
    graph = Graph()
    try:
        graph.parse(data=ttl_text, format="turtle")
    except Exception as exc:  # noqa: BLE001 - rdflib raises several parse error types
        line = re.search(r"line (\d+)", str(exc))
        where = f" (fejl ved linje {line.group(1)})" if line else ""
        raise InvalidTurtle(
            f"TTL-indholdet er ikke gyldig Turtle{where}. "
            "Ret filen eller teksten, og prøv igen."
        ) from exc
    return graph


def guess_namespace(ttl_text: str) -> str | None:
    """Suggest the ontology namespace for Turtle without storing anything.

    Raises:
        InvalidTurtle if the Turtle cannot be parsed.
    """
    return detect_ontology(parse_turtle(ttl_text))


def ingest_turtle(
    repository: DictionaryRepository,
    ttl_text: str,
    ontology: str,
) -> IngestResult:
    """Parse Turtle, load it into a new source graph, and split its elements.

    ``ontology`` is the namespace used to select elements; the editor has
    confirmed it (typically after :func:`guess_namespace`).

    Raises:
        ValueError if the namespace is empty, or InvalidTurtle if the Turtle
        cannot be parsed.
    """
    ontology = ontology.strip()
    if not ontology:
        raise ValueError("Namespace mangler.")

    local = parse_turtle(ttl_text)

    graph_uri = repository.new_graph_iri()
    repository.insert_vocabulary(graph_uri, local)
    repository.split_elements(graph_uri, ontology)

    return IngestResult(
        graph_uri=graph_uri, ontology=ontology, triple_count=len(local)
    )
