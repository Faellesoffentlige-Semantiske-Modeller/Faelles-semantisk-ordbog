"""Ingesting an uploaded vocabulary into the dictionary."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DC, DCTERMS, OWL, RDF, RDFS, SKOS, FOAF, XSD

from datetime import datetime, timezone
from .models import ItemCard, Term, prefer_language
from .namespaces import MDC, MDV, ADMS, VANN
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
    labelDa: str = ""
    description: str = ""
    descriptionDa: str = ""
    version: str = ""
    download_url: str = ""
    page: str = ""
    prefix: str = ""


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


class InvalidPrefix(ValueError):
    """The prefix does not belong to the namespace in the file. The message is shown to the user."""


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
    # "none": only the prefixes the file declares, not rdflib's built-in ones
    graph = Graph(bind_namespaces="none")
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


def declared_prefixes(graph: Graph) -> list[tuple[str, str]]:
    return sorted((p, str(uri)) for p, uri in graph.namespaces())


def find_prefix(graph: Graph, namespace: str) -> str | None:
    """A prefix the file declares for the namespace, or None.

    The empty prefix (@prefix : <...>) is not a name worth suggesting.
    """
    namespace = namespace.strip()
    matches = sorted(p for p, uri in graph.namespaces() if p and str(uri) == namespace)
    return matches[0] if matches else None


def check_prefix(graph: Graph, namespace: str, prefix: str) -> None:
    """Raise InvalidPrefix unless the file declares the prefix for the namespace.

    An empty prefix is allowed: it means none was given.
    """
    prefix = prefix.strip()
    if not prefix:
        return
    declared = {p: str(uri) for p, uri in graph.namespaces()}
    if prefix not in declared:
        raise InvalidPrefix(f"Præfikset {prefix} er ikke deklareret i TTL-filen.")
    if declared[prefix] != namespace.strip():
        raise InvalidPrefix(
            f"Præfikset {prefix} peger på {declared[prefix]} i TTL-filen, "
            "ikke på det angivne namespace."
        )


# The rdf:types that make a subject a dictionary item, and the item type each
# gives, as shown in the /items table. Keep in step with the VALUES block in
# sparql/split_elements.rq, which is what the upload really uses.
_OWL = "http://www.w3.org/2002/07/owl#"
_ITEM_TYPE_BY_RDF_TYPE = {
    _OWL + "Class": "Class",
    str(RDFS) + "Class": "Class",
    _OWL + "DeprecatedClass": "Class",
    str(RDF) + "Property": "Property",
    _OWL + "ObjectProperty": "Property",
    _OWL + "DatatypeProperty": "Property",
    _OWL + "AnnotationProperty": "Property",
    _OWL + "FunctionalProperty": "Property",
    _OWL + "InverseFunctionalProperty": "Property",
    _OWL + "TransitiveProperty": "Property",
    _OWL + "SymmetricProperty": "Property",
    _OWL + "DeprecatedProperty": "Property",
    str(RDFS) + "Datatype": "DataType",
    str(SKOS) + "Concept": "Concept",
}


def preview_items(graph: Graph, namespace: str) -> list[ItemCard]:
    """The dictionary items an upload of the graph would create, as /items shows them.

    A preview only: it reads the parsed graph and never touches the store.
    """
    namespace = namespace.strip()
    if not namespace:
        return []

    types_by_element: dict[URIRef, set[str]] = {}
    for subject, rdf_type in graph.subject_objects(RDF.type):
        item_type = _ITEM_TYPE_BY_RDF_TYPE.get(str(rdf_type))
        if item_type and isinstance(subject, URIRef) and str(subject).startswith(namespace):
            types_by_element.setdefault(subject, set()).add(item_type)

    cards = []
    for element, item_types in types_by_element.items():
        labels = sorted(
            (Term(str(o), lang=o.language or "")
             for o in graph.objects(element, RDFS.label) if isinstance(o, Literal)),
            key=lambda term: term.value,
        )
        preferred = prefer_language(labels)
        cards.append(
            ItemCard(
                iri=str(element),
                vocabulary="",
                name=preferred[0].value if preferred else "",
                item_types=sorted(item_types),
            )
        )
    return sorted(cards, key=lambda card: card.label.casefold())


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

def vocabulary_metadata(vocabulary: URIRef, form: VocabularyForm) -> Graph:
    """The default-graph triples about the vocabulary itself.

    Only what was submitted in the form is stored. Values read from the file's
    header are suggestions for the form (Gæt namespace), not metadata.
    """
    g = Graph()
    g.add((vocabulary, RDF.type, MDV.SemanticAsset))
    g.add((vocabulary, DCTERMS.type, MDC.Vocabulary))
    g.add((vocabulary, ADMS.status, MDC.evaluationProposed))
    g.add((vocabulary, MDV.downloadTime,
           Literal(datetime.now(timezone.utc).replace(microsecond=0))))

    _add_text(g, vocabulary, RDFS.label, form.label, lang="en")
    _add_text(g, vocabulary, RDFS.label, form.labelDa, lang="da")
    _add_text(g, vocabulary, DCTERMS.description, form.description, lang="en")
    _add_text(g, vocabulary, DCTERMS.description, form.descriptionDa, lang="da")
    _add_text(g, vocabulary, OWL.versionInfo, form.version, lang=None)
    _add_text(g, vocabulary, VANN.preferredNamespacePrefix, form.prefix, lang=None)

    if form.download_url:
        g.add((vocabulary, MDV.downloadURL, Literal(form.download_url, datatype=XSD.anyURI)))
    if form.page:
        g.add((vocabulary, FOAF.page, URIRef(form.page)))
    return g

def _add_text(g, subject, predicate, text, lang):
    if text:
        g.add((subject, predicate, Literal(text, lang=lang)))

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
    form = form or VocabularyForm()
    check_prefix(local, ontology, form.prefix)

    # Re-uploads are not supported yet
    if repository.has_items_in_namespace(ontology):
        raise AlreadyUploaded(
            "Der findes allerede ordbogselementer for dette namespace. "
            "Genupload er ikke understøttet endnu."
        )

    graph_uri = repository.new_graph_iri()
    metadata = vocabulary_metadata(URIRef(graph_uri), form)
    repository.ingest_vocabulary(graph_uri, local, metadata, ontology)

    return IngestResult(
        graph_uri=graph_uri,
        ontology=ontology,
        triple_count=len(local),
        item_counts=repository.count_items(graph_uri),
    )
