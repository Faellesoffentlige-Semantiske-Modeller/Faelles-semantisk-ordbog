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
    build_facts,
    local_name,
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


def _distinct(rows, column: str) -> list:
    """The values of a result column without repeats and unbound values, in order."""
    return list(dict.fromkeys(row[column] for row in rows if row[column] is not None))


def _item_type_names(rows) -> list[str]:
    """The local names of the mdv:itemType values in the rows, e.g. ["Class"]."""
    return sorted(local_name(str(item_type)) for item_type in _distinct(rows, "itemType"))


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

    def list_items(self) -> list[ItemCard]:
        """All dictionary items."""
        # An item comes back once per rdfs:label (one per language) and item type.
        rows_by_item: dict[str, list] = {}
        for row in self.reader.query(load_sparql("list_items.rq")):
            rows_by_item.setdefault(str(row.item), []).append(row)

        cards = []
        for item_iri, rows in rows_by_item.items():
            labels = [_term(label) for label in _distinct(rows, "label")]
            preferred = prefer_language(labels)
            cards.append(
                ItemCard(
                    iri=item_iri,
                    vocabulary=str(rows[0].vocabulary),
                    name=preferred[0].value if preferred else "",
                    item_types=_item_type_names(rows),
                )
            )
        return sorted(cards, key=lambda card: card.label.casefold())

    def get_item(self, item_iri: str) -> DictionaryItem | None:
        """Return one dictionary item described for display, or None."""
        rows = list(self.reader.query(load_sparql("item_info.rq", item=item_iri)))
        if not rows:
            return None

        first = rows[0]
        # The defining graph holds the element's own triples, plus the blank
        # nodes they point to; keep just the element's own. A triple repeats
        # once per item type and vocabulary label, so keep each once.
        own = dict.fromkeys(
            (str(row.p), row.o)
            for row in rows
            if row.s is not None and str(row.s) == item_iri
        )
        statements = [(predicate, _term(value)) for predicate, value in own]
        names = prefer_language(
            [term for predicate, term in statements if predicate == LABEL_PREDICATE]
        )
        vocabulary_names = prefer_language(
            [_term(label) for label in _distinct(rows, "vocabularyLabel")]
        )
        item = DictionaryItem(
            iri=item_iri,
            defining_graph=str(first.definingGraph),
            vocabulary=str(first.vocabulary),
            name=names[0].value if names else "",
            vocabulary_name=vocabulary_names[0].value if vocabulary_names else "",
            item_types=_item_type_names(rows),
            facts=build_facts(statements),
        )
        item.evaluation = self.read_evaluation(item_iri)
        return item

    def has_items_in_namespace(self, namespace: str) -> bool:
        """Whether any dictionary item's IRI starts with the namespace."""
        result = self.reader.query(
            load_sparql("items_in_namespace.rq", namespace=namespace)
        )
        return bool(result.askAnswer)

    def count_items(self, vocabulary: str) -> dict[str, int]:
        """How many dictionary items of each mdv:itemType a vocabulary gave."""
        rows = self.reader.query(load_sparql("count_items.rq", vocabulary=vocabulary))
        return {str(row.itemType): int(row.items) for row in rows}

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

    def ingest_vocabulary(
        self, vocabulary: str, graph: Graph, metadata: Graph, namespace: str
    ) -> None:
        """Load a vocabulary, its metadata, element graphs and items in one transaction.

        The operations run in order in a single update request, so each one sees
        what the earlier ones wrote, and Fuseki applies all of them or none.
        """
        operations = [
            load_sparql(
                "insert_data_graph.rq",
                graph=vocabulary,
                triples=graph.serialize(format="nt"),
            ),
            load_sparql(
                "insert_data_default.rq",
                triples=metadata.serialize(format="nt"),
            ),
            load_sparql(
                "split_elements.rq",
                vocabulary=vocabulary,
                namespace=namespace,
                graph_base=self.config.graph_base,
            ),
            load_sparql("copy_blank_nodes.rq", vocabulary=vocabulary),
        ]
        self.writer.update(" ;\n".join(operations))

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

    def new_graph_iri(self) -> str:
        """Mint an IRI for a newly uploaded source graph."""
        return self.config.graph_base + str(uuid4())
