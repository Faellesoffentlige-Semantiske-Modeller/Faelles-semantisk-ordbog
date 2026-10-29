"""Ingesting an uploaded vocabulary into the dictionary."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DC, DCTERMS, OWL, RDF, RDFS, SKOS, FOAF, XSD

from datetime import datetime, timezone
from .namespaces import MDC, MDV, ADMS
from .repository import DictionaryRepository


@dataclass
class IngestResult:
    """What a successful ingest produced, for display on the upload page."""

    graph_uri: str
    ontology: str
    triple_count: int
    # mdv:itemType IRI -> number of dictionary items of that type
    item_counts: dict[str, int] = field(default_factory=dict)

@dataclass
class VocabularyHeader:

    namespace: str
    labels: list[Literal]
    descriptions: list[Literal]
    versions: list[Literal]


# For each field, the predicates to read it from, in order of preference. The
# first predicate with any values wins, and all of its values are kept.
_LABEL_PREDICATES = (DCTERMS.title, DC.title, RDFS.label, SKOS.prefLabel)
_DESCRIPTION_PREDICATES = (DCTERMS.description, DC.description, RDFS.comment)
_VERSION_PREDICATES = (OWL.versionInfo, DCTERMS.hasVersion)


@dataclass
class VocabularyForm:
    """Vocabulary metadata typed in on the upload page. Empty means not given."""
    label: str = ""
    description: str = ""
    version: str = ""
    download_url: str = ""
    page: str = ""

def detect_ontology(graph: Graph) -> str | None:
    """Return the IRI of the first owl:Ontology in the graph, or None."""
    for subject in graph.subjects(RDF.type, OWL.Ontology):
        return str(subject)
    return None


class InvalidTurtle(ValueError):
    """The submitted text is not valid Turtle. The message is shown to the user."""


class InvalidNamespace(ValueError):
    """The namespace cannot be used. The message is shown to the user."""


class AlreadyUploaded(InvalidNamespace):
    """The dictionary already has items in the namespace."""


# An absolute IRI with none of the characters SPARQL forbids inside <...>.
# Text that is put into a query must pass this, so it cannot change the query.
_SAFE_IRI = re.compile(r'[A-Za-z][A-Za-z0-9+.\-]*:[^\s<>"{}|^`\\]+')


def is_safe_iri(text: str) -> bool:
    """Whether the text is an absolute IRI that can be put into a SPARQL query."""
    return _SAFE_IRI.fullmatch(text) is not None


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


def read_vocabulary_metadata(graph: Graph, namespace: str) -> VocabularyHeader:
    namespace = namespace.strip()
    header = _namespace_resource(graph, namespace)
    if header is None:
        return VocabularyHeader(namespace, labels=[], descriptions=[], versions=[])
    return VocabularyHeader(
        namespace,
        labels=_first_literals(graph, header, _LABEL_PREDICATES),
        descriptions=_first_literals(graph, header, _DESCRIPTION_PREDICATES),
        versions=_first_literals(graph, header, _VERSION_PREDICATES),
    )


def _namespace_resource(graph: Graph, namespace: str) -> URIRef | None:
    """The subject in the graph that names the namespace, or None."""
    for candidate in dict.fromkeys([namespace, namespace.rstrip("/#")]):
        subject = URIRef(candidate)
        if candidate and (subject, None, None) in graph:
            return subject
    return None


def _first_literals(graph: Graph, subject: URIRef, predicates) -> list[Literal]:
    """The literal values of the first predicate in order that has any."""
    for predicate in predicates:
        values = [o for o in graph.objects(subject, predicate) if isinstance(o, Literal)]
        if values:
            return values
    return []

def vocabulary_metadata(
    vocabulary: URIRef, header: VocabularyHeader, form: VocabularyForm
) -> Graph:
    """The default-graph triples about the vocabulary itself."""
    g = Graph()
    g.add((vocabulary, RDF.type, MDV.SemanticAsset))
    g.add((vocabulary, DCTERMS.type, MDC.Vocabulary))
    g.add((vocabulary, ADMS.status, MDC.evaluationProposed))
    g.add((vocabulary, MDV.downloadTime,
           Literal(datetime.now(timezone.utc).replace(microsecond=0))))

    _add_texts(g, vocabulary, RDFS.label, header.labels, form.label, lang="da")
    _add_texts(g, vocabulary, DCTERMS.description, header.descriptions, form.description, lang="da")
    _add_texts(g, vocabulary, OWL.versionInfo, header.versions, form.version, lang=None)

    if form.download_url:
        g.add((vocabulary, MDV.downloadURL, Literal(form.download_url, datatype=XSD.anyURI)))
    if form.page:
        g.add((vocabulary, FOAF.page, URIRef(form.page)))
    return g

def _add_texts(g, subject, predicate, from_file, typed, lang):
    for value in from_file:
        g.add((subject, predicate, value))
    if typed and typed not in (str(value) for value in from_file):
        g.add((subject, predicate, Literal(typed, lang=lang)))

def ingest_turtle(
    repository: DictionaryRepository,
    ttl_text: str,
    ontology: str,
    form: VocabularyForm | None = None,
) -> IngestResult:
    """Parse Turtle and load it, its metadata, element graphs and items.
    """
    ontology = ontology.strip()
    if not ontology:
        raise InvalidNamespace("Namespace mangler.")
    if not is_safe_iri(ontology):
        raise InvalidNamespace(
            "Namespace skal være en hel IRI, fx http://xmlns.com/foaf/0.1/, "
            'uden mellemrum og uden tegnene < > " { } | ^ ` \\.'
        )

    local = parse_turtle(ttl_text)

    # Re-uploads are not supported yet
    if repository.has_items_in_namespace(ontology):
        raise AlreadyUploaded(
            "Der findes allerede ordbogselementer for dette namespace. "
            "Genupload er ikke understøttet endnu."
        )

    graph_uri = repository.new_graph_iri()
    header = read_vocabulary_metadata(local, ontology)
    metadata = vocabulary_metadata(URIRef(graph_uri), header, form or VocabularyForm())
    repository.ingest_vocabulary(graph_uri, local, metadata, ontology)

    return IngestResult(
        graph_uri=graph_uri,
        ontology=ontology,
        triple_count=len(local),
        item_counts=repository.count_items(graph_uri),
    )
