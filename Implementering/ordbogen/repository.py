"""Data access for the Metadataordbog dataset.

Every SPARQL query and update lives behind this class, so view functions deal
only in the dataclasses from :mod:`ordbogen.models`.
"""

from __future__ import annotations

from uuid import uuid4

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, RDFS, XSD

from .config import Config
from .models import (
    DictionaryItem,
    Evaluation,
    EvaluationSubmission,
    ItemCard,
    LABEL_PREDICATE,
    Term,
    Triple,
    build_facts,
    prefer_language,
)
from .store import load_sparql, query_store, update_store


def _term(node) -> Term:
    """Wrap an rdflib node from a query result for display."""
    return Term(
        str(node),
        lang=getattr(node, "language", None) or "",
        is_iri=isinstance(node, URIRef),
    )


class DictionaryRepository:
    """Reads and writes the dictionary via Fuseki's SPARQL endpoints.

    One instance is created per request; the underlying stores are built
    lazily so a read-only request never opens the update endpoint.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self._query_store = None
        self._update_store = None

    @property
    def reader(self):
        if self._query_store is None:
            self._query_store = query_store(self.config)
        return self._query_store

    @property
    def writer(self):
        if self._update_store is None:
            self._update_store = update_store(self.config)
        return self._update_store

    # --- reads ---------------------------------------------------------

    def default_graph_triples(self) -> list[Triple]:
        """Every triple in the default graph."""
        return [
            (str(row[0]), str(row[1]), str(row[2]))
            for row in self.reader.query(load_sparql("default_triples.rq"))
        ]

    def named_graph_names(self) -> list[str]:
        """The names of all named graphs, sorted."""
        rows = self.reader.query(load_sparql("list_named_graphs.rq"))
        return sorted(str(row[0]) for row in rows)

    def list_items(self) -> list[ItemCard]:
        """All dictionary items whose IRI sits under the configured item base."""
        base = self.config.item_base
        # An item comes back once per rdfs:label (one per language).
        rows_by_item: dict[str, list] = {}
        for row in self.reader.query(load_sparql("list_items.rq")):
            item_iri = str(row.item)
            if item_iri.startswith(base):
                rows_by_item.setdefault(item_iri, []).append(row)

        cards = []
        for item_iri, rows in rows_by_item.items():
            labels = [_term(row.label) for row in rows if row.label is not None]
            preferred = prefer_language(labels)
            cards.append(
                ItemCard(
                    uuid=item_iri[len(base):],
                    element=str(rows[0].element),
                    vocabulary=str(rows[0].vocabulary),
                    name=preferred[0].value if preferred else "",
                )
            )
        return sorted(cards, key=lambda card: card.label.casefold())

    def get_item(self, item_uuid: str) -> DictionaryItem | None:
        """Return one dictionary item described for display, or None."""
        item_iri = self.item_iri(item_uuid)
        rows = list(self.reader.query(load_sparql("item_info.rq", item=item_iri)))
        if not rows:
            return None

        last = rows[-1]
        element = str(last.element)
        # The defining graph holds the element's own triples; keep just those.
        statements = [
            (str(row.p), _term(row.o))
            for row in rows
            if row.s is not None and str(row.s) == element
        ]
        names = prefer_language(
            [term for predicate, term in statements if predicate == LABEL_PREDICATE]
        )
        item = DictionaryItem(
            iri=item_iri,
            uuid=item_uuid,
            element=element,
            defining_graph=str(last.definingGraph),
            vocabulary=str(last.vocabulary),
            name=names[0].value if names else "",
            facts=build_facts(statements),
        )
        item.evaluation = self.read_evaluation(item_iri)
        return item

    def read_evaluation(self, item_iri: str) -> Evaluation | None:
        """Return the evaluation linked from an item, or None if it has none."""
        evaluation = None
        for row in self.reader.query(load_sparql("item_evaluation.rq", item=item_iri)):
            if evaluation is None:
                evaluation = Evaluation(iri=str(row.evaluation))
            if row.comment is not None:
                evaluation.comment = str(row.comment)
                if getattr(row.comment, "language", None):
                    evaluation.comment_lang = row.comment.language
            if row.creator is not None:
                evaluation.creator = str(row.creator)
            if row.date is not None:
                evaluation.date = str(row.date)
        return evaluation

    # --- writes --------------------------------------------------------

    def insert_vocabulary(self, graph_uri: str, graph: Graph) -> None:
        """Load a parsed vocabulary into its own source named graph."""
        self.writer.update(
            load_sparql(
                "insert_data_graph.rq",
                graph=graph_uri,
                triples=graph.serialize(format="nt"),
            )
        )

    def split_elements(self, source_graph: str, ontology: str) -> None:
        """Split each element of a source graph into its own element graph.

        Also creates one mdv:DictionaryItem per element in the default graph.
        """
        self.writer.update(
            load_sparql(
                "split_elements.rq",
                source_graph=source_graph,
                ontology=ontology,
                element_base=self.config.graph_base,
                item_base=self.config.item_base,
            )
        )

    def create_evaluation(self, item_iri: str) -> str:
        """Create an empty evaluation, link it to the item, return its IRI."""
        evaluation_iri = self.config.graph_base + str(uuid4())
        self.writer.update(
            load_sparql(
                "create_evaluation.rq", item=item_iri, evaluation=evaluation_iri
            )
        )
        return evaluation_iri

    def replace_evaluation_fields(
        self, evaluation_iri: str, submission: EvaluationSubmission
    ) -> None:
        """Overwrite an evaluation's editable fields with submitted values.

        Idempotent: the existing fields are cleared and the non-empty
        submitted ones re-inserted.
        """
        self.writer.update(
            load_sparql("clear_evaluation_fields.rq", evaluation=evaluation_iri)
        )

        ev = URIRef(evaluation_iri)
        graph = Graph()
        if submission.comment:
            lang = submission.comment_lang or None
            graph.add((ev, RDFS.comment, Literal(submission.comment, lang=lang)))
        if submission.creator:
            graph.add((ev, DCTERMS.creator, Literal(submission.creator)))
        if submission.date:
            graph.add((ev, DCTERMS.date, Literal(submission.date, datatype=XSD.date)))
        if len(graph):
            self.writer.update(
                load_sparql(
                    "insert_data_default.rq", triples=graph.serialize(format="nt")
                )
            )

    def save_evaluation(
        self,
        item_iri: str,
        evaluation_iri: str,
        submission: EvaluationSubmission,
    ) -> str:
        """Update an item's evaluation, creating it first if it has none."""
        if not evaluation_iri:
            evaluation_iri = self.create_evaluation(item_iri)
        self.replace_evaluation_fields(evaluation_iri, submission)
        return evaluation_iri

    # --- IRI helpers ---------------------------------------------------

    def item_iri(self, item_uuid: str) -> str:
        """The IRI of the dictionary item with this UUID."""
        return self.config.item_base + item_uuid

    def new_graph_iri(self) -> str:
        """Mint an IRI for a newly uploaded source graph."""
        return self.config.graph_base + str(uuid4())
