# Ordbogen UI

A simple Flask UI that reads and edits the Fuseki `Metadataordbog` dataset with
**rdflib**. It can ingest external vocabularies (TTL), split them into per-element
graphs, generate `mdv:DictionaryItem` resources, browse them, and attach an
editable `mdv:Evaluation` to each item.

## Routes

| Route          | Method    | Description                                                              |
|----------------|-----------|--------------------------------------------------------------------------|
| `/`            | GET       | Landing page with links                                                  |
| `/default`     | GET       | All triples from the **default graph**                                   |
| `/graph`       | GET       | Names of **all named graphs**                                            |
| `/items`       | GET       | Grid of dkfds cards, one per `mdv:DictionaryItem`, linking to its page   |
| `/item/<uuid>` | GET, POST | One dictionary item: its references, element triples, and evaluation form |
| `/upload`      | GET, POST | Upload TTL (file or pasted text) → new source graph + elements + items   |

## What the upload does

`/upload` accepts a TTL **file** or **pasted TTL text**. On submit it:

1. Parses/validates the Turtle with rdflib.
2. Loads the whole vocabulary into a new **source named graph**
   (`https://data.gov.dk/dataset/dictionary/common-semantic-dictionary/<uuid>`).
3. Splits every element (property/class) into its own **element graph** and, in
   the **default graph**, creates one `mdv:DictionaryItem` per element with:
   - `mdv:definingGraph` → the element graph
   - `mdv:representsElement` → the element IRI
   - `mdv:fromVocabulary` → the source graph

### Ontology namespace

The split filters elements by the vocabulary's namespace. It is resolved as:

1. the value typed into the optional **Ontologi** field (override), otherwise
2. the subject of `owl:Ontology` detected in the uploaded TTL.

If neither is available the upload fails with an error.

## Dictionary item & evaluation

`/item/<uuid>` shows the item's references and the triples from its defining
(element) graph. It also manages an `mdv:Evaluation` that lives in the **default
graph** and is linked from the item via `mdv:evaluation`:

- If no evaluation exists yet, an **Add** button creates an empty one.
- Once it exists, the following fields are editable (saved idempotently — the
  fields are cleared and re-inserted on each save):
  - `rdfs:comment` — note/comment, language-tagged (`da`/`en`)
  - `dct:creator` — evaluator (plain text)
  - `dct:date` — date (`xsd:date`)

## Project structure

```
ordbogen/                  the application package
├── __init__.py            create_app() — the app factory
├── config.py              Config, resolved from env vars or injected
├── store.py               Fuseki store factories + .rq template loading
├── models.py              DictionaryItem, Evaluation, ItemCard dataclasses
├── repository.py          DictionaryRepository — every SPARQL call lives here
├── ingest.py              parse TTL → load source graph → split elements
├── sparql/                the .rq query templates
├── templates/             Jinja templates
├── static/                style.css + vendored dkfds
└── views/                 the HTTP layer, one blueprint per group of routes
    ├── __init__.py        current_config() / current_repository()
    ├── main.py            /  /default  /graph
    ├── items.py           /items  /item/<uuid>
    └── upload.py          /upload
wsgi.py                    entrypoint: `app = create_app()`
```

The layering rule: **view functions hold no SPARQL.** They read the request,
call a `DictionaryRepository` method, and render a template. Config is passed
into `create_app()` rather than read at import time, so an app can be pointed
at a different endpoint without mutating the environment.

## SPARQL

Queries live as templates in [`ordbogen/sparql/`](ordbogen/sparql/) and are
loaded with `string.Template` (SPARQL uses `?vars`, so `$placeholder` names
don't collide):

| File                         | Purpose                                                 |
|------------------------------|---------------------------------------------------------|
| `insert_data_graph.rq`       | Load an uploaded vocabulary into its source graph       |
| `split_elements.rq`          | Split elements into element graphs + create items       |
| `list_items.rq`              | List all dictionary items (for the cards page)          |
| `item_info.rq`               | An item's references + its defining-graph triples       |
| `item_evaluation.rq`         | Read an item's evaluation and its fields                |
| `create_evaluation.rq`       | Create an empty evaluation and link it to the item      |
| `clear_evaluation_fields.rq` | Remove an evaluation's editable fields before re-insert |
| `insert_data_default.rq`     | Insert ground triples into the default graph            |
| `default_triples.rq`         | Every triple in the default graph                       |
| `list_named_graphs.rq`       | The name of every non-empty named graph                 |

## UI / design system

The pages use the Danish design system (**dkfds**), vendored under
[`ordbogen/static/dkfds/`](ordbogen/static/dkfds/) (css/fonts/img/js).
Components used include the file-upload field, cards, and the back link
(`history.back()` with a per-page fallback href).

## Run everything with Docker Compose

This compose file also builds and starts Fuseki from `../TripleStore`.

```shell
docker compose up --build
```

- UI:     <http://localhost:5000>
- Fuseki: <http://localhost:3031>

The Fuseki admin password is read from `../TripleStore/secrets/ADMIN_PASSWORD_PLAIN.txt`
(same secret the TripleStore compose uses) and shared with the UI so it can
authenticate against the SPARQL query **and** update endpoints.

## Configuration (environment variables)

| Variable                 | Default                                             |
|--------------------------|-----------------------------------------------------|
| `FUSEKI_ENDPOINT`        | `http://fuseki2:3030/Metadataordbog/sparql`         |
| `FUSEKI_UPDATE_ENDPOINT` | query endpoint with `/sparql` → `/update`           |
| `FUSEKI_USER`            | `admin` (in compose)                                |
| `FUSEKI_PASSWORD`        | —                                                   |
| `FUSEKI_PASSWORD_FILE`   | `/run/secrets/ADMIN_PASSWORD` (in compose)          |

## Run locally without Docker

```shell
pip install -r requirements.txt
export FUSEKI_ENDPOINT=http://localhost:3031/Metadataordbog/sparql
export FUSEKI_USER=admin
export FUSEKI_PASSWORD=yourpassword
python wsgi.py
```

## Known gaps

These are not addressed yet and are tracked separately from the structure:

- **No authentication and no CSRF protection** on the write routes.
- **SPARQL injection** — the ontology field, the evaluation IRI, and the item
  UUID are substituted into query text without validation.
- `wsgi.py` run directly serves via Flask's development server with
  `debug=True`; use gunicorn/waitress for anything real.
- No `LIMIT`/pagination on the listing routes, and no `MAX_CONTENT_LENGTH` on
  uploads.
- `DictionaryItem` and `Evaluation` are written to the **default graph**, not
  to a dictionary named graph as the data model describes.
