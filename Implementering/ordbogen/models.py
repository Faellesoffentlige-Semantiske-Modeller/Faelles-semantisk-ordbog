"""The shapes that cross the repository/view boundary.

Dataclasses rather than dicts: Jinja renders an unknown dict key as an empty
string, so a typo in a template silently blanks the field instead of failing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# A single RDF statement, already stringified for display.
Triple = tuple[str, str, str]


def local_name(iri: str) -> str:
    """Return the last path/fragment segment of an IRI, for display."""
    return iri.rstrip("/#").replace("#", "/").rsplit("/", 1)[-1] or iri


@dataclass
class Evaluation:
    """An mdv:Evaluation attached to a dictionary item."""

    iri: str
    comment: str = ""
    comment_lang: str = "da"
    creator: str = ""
    date: str = ""


@dataclass
class EvaluationSubmission:
    """Evaluation values submitted from the edit form.

    Built by the view from ``request.form`` so the repository never sees a
    Flask request object.
    """

    comment: str = ""
    comment_lang: str = "da"
    creator: str = ""
    date: str = ""


@dataclass
class Term:
    """An RDF object with the bits needed to present it."""

    value: str
    lang: str = ""
    is_iri: bool = False


def prefer_language(terms: list[Term]) -> list[Term]:
    """Keep only the terms in the best available language (da, en, untagged, other)."""
    if not terms:
        return terms

    def rank(term: Term) -> int:
        return {"da": 0, "en": 1, "": 2}.get(term.lang, 3)

    best = min(rank(term) for term in terms)
    return [term for term in terms if rank(term) == best]


@dataclass
class ItemCard:
    """One mdv:DictionaryItem as shown in the /items table."""

    uuid: str
    element: str
    vocabulary: str
    # The item's rdfs:label in the preferred language, if it has one.
    name: str = ""

    @property
    def label(self) -> str:
        return self.name or local_name(self.element)


# --- the "Om elementet" facts shown on an item page ---------------------
#
# Only predicates a non-technical reader cares about are shown, under a Danish
# heading each. Everything else in the defining graph is left out. The order
# here is the display order.

_RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
_RDFS = "http://www.w3.org/2000/01/rdf-schema#"
_SKOS = "http://www.w3.org/2004/02/skos/core#"
_DCT = "http://purl.org/dc/terms/"

LABEL_PREDICATE = _RDFS + "label"

FACT_HEADINGS: dict[str, str] = {
    _RDFS + "comment": "Beskrivelse",
    _DCT + "description": "Beskrivelse",
    _SKOS + "definition": "Definition",
    _RDF_TYPE: "Type",
    _RDFS + "domain": "Bruges på",
    _RDFS + "range": "Forventet værdi",
    _RDFS + "isDefinedBy": "Defineret i",
    _RDFS + "seeAlso": "Se også",
    "http://www.w3.org/2003/06/sw-vocab-status/ns#term_status": "Status",
}

# Predicates whose IRI value is shown in full rather than as its last segment.
_FULL_IRI_PREDICATES = {_RDFS + "isDefinedBy", _RDFS + "seeAlso"}

# Plain-language names for the RDF/OWL terms that turn up as types/ranges.
_FRIENDLY_IRIS: dict[str, str] = {
    "http://www.w3.org/2002/07/owl#DatatypeProperty": "Egenskab med en simpel værdi",
    "http://www.w3.org/2002/07/owl#ObjectProperty": "Egenskab der peger på en anden ting",
    "http://www.w3.org/2002/07/owl#FunctionalProperty": "Egenskab med højst én værdi",
    "http://www.w3.org/2002/07/owl#AnnotationProperty": "Annoteringsegenskab",
    "http://www.w3.org/2002/07/owl#DeprecatedProperty": "Udfaset egenskab",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property": "Egenskab",
    _RDFS + "Literal": "Tekst",
}


@dataclass
class FactValue:
    """One value of a fact: text to show, and a link if it is an IRI."""

    text: str
    href: str = ""
    title: str = ""


@dataclass
class Fact:
    """A heading with its value(s), e.g. Beskrivelse -> "Indicates the name ..."."""

    heading: str
    values: list[FactValue] = field(default_factory=list)


def build_facts(statements: list[tuple[str, Term]]) -> list[Fact]:
    """Turn (predicate, object) pairs into the user-facing facts, in display order."""
    by_predicate: dict[str, list[Term]] = {}
    for predicate, term in statements:
        by_predicate.setdefault(predicate, []).append(term)

    by_heading: dict[str, list[FactValue]] = {}
    for predicate, heading in FACT_HEADINGS.items():
        for term in prefer_language(by_predicate.get(predicate, [])):
            by_heading.setdefault(heading, []).append(
                _fact_value(predicate, term)
            )

    # dicts keep insertion order, so headings follow FACT_HEADINGS' order
    return [Fact(heading, values) for heading, values in by_heading.items()]


def _fact_value(predicate: str, term: Term) -> FactValue:
    if not term.is_iri:
        return FactValue(term.value)
    if predicate in _FULL_IRI_PREDICATES:
        text = term.value
    else:
        text = _FRIENDLY_IRIS.get(term.value) or local_name(term.value)
    return FactValue(text, href=term.value, title=term.value)


@dataclass
class DictionaryItem:
    """One mdv:DictionaryItem, described by the triples of its defining graph."""

    iri: str
    uuid: str
    element: str
    defining_graph: str
    vocabulary: str
    # The item's rdfs:label in the preferred language, if it has one.
    name: str = ""
    facts: list[Fact] = field(default_factory=list)
    evaluation: Evaluation | None = None

    @property
    def title(self) -> str:
        return self.name or local_name(self.element)
