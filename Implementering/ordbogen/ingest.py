"""Ingesting an uploaded vocabulary into the dictionary."""

from __future__ import annotations

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


def ingest_turtle(
    repository: DictionaryRepository,
    ttl_text: str,
    ontology_override: str = "",
) -> IngestResult:
    """Parse Turtle, load it into a new source graph, and split its elements.

    The namespace used to select elements is the explicit override if given,
    otherwise the uploaded file's own ``owl:Ontology`` declaration.

    Raises:
        rdflib parse errors if the Turtle is invalid, or ValueError if no
        ontology namespace can be resolved.
    """
    local = Graph()
    local.parse(data=ttl_text, format="turtle")

    ontology = ontology_override or detect_ontology(local)
    if not ontology:
        raise ValueError(
            "Kunne ikke finde en owl:Ontology i TTL-indholdet, og der er ikke "
            "angivet en ontologi. Angiv en ontologi-URI i feltet ovenfor."
        )

    graph_uri = repository.new_graph_iri()
    repository.insert_vocabulary(graph_uri, local)
    repository.split_elements(graph_uri, ontology)

    return IngestResult(
        graph_uri=graph_uri, ontology=ontology, triple_count=len(local)
    )
