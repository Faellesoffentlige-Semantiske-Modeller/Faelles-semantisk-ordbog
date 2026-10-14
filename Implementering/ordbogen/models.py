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
class ItemCard:
    """One mdv:DictionaryItem as shown in the /items grid."""

    uuid: str
    element: str
    vocabulary: str

    @property
    def label(self) -> str:
        return local_name(self.element)


@dataclass
class DictionaryItem:
    """One mdv:DictionaryItem with the triples from its defining graph."""

    iri: str
    uuid: str
    element: str
    defining_graph: str
    vocabulary: str
    triples: list[Triple] = field(default_factory=list)
    evaluation: Evaluation | None = None

    @property
    def count(self) -> int:
        return len(self.triples)
