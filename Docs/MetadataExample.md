```
# default graph
csd:A  a mdv:SemanticAsset ;
       rdfs:label "…" ; dcterms:description "…" ; owl:versionInfo "…" ;
       dcterms:type mdc:Vocabulary ; adms:status mdc:evaluationProposed ;
       mdv:downloadURL "…"^^xsd:anyURI ; mdv:downloadTime "…"^^xsd:dateTime ;
       foaf:page <doc> ; dcterms:publisher <org> ; dcterms:creator <org> ;
       dcat:previousVersion csd:A0 ;
       dcterms:hasPart csd:E1 .

csd:E1 a mdv:ElementGraph ;
       rdfs:label "…" ; dcterms:description "…" ;
       adms:status mdc:accepted ; foaf:page <doc> ; skos:example csd:P1 ;
       dcterms:isPartOf csd:A .

foaf:Person a mdv:DictionaryItem ;
       rdfs:isDefinedBy  csd:A ;
       mdv:definingGraph csd:E1 ;
       mdv:itemType      mdc:Class ;
       mdv:itemDescription "…" .

GRAPH csd:A  { …fuldt vokabular... }
GRAPH csd:E1 { foaf:Person … }
```


```
# ---------------------------------------------------------------------------
# default graph: metadata om vokabular og elementer, samt dictonary items
# ---------------------------------------------------------------------------

# The vocabulary (named graph csd:e209a4b8-…)
csd:e209a4b8-596d-4417-b8a1-f9eff775a5ae
       a mdv:SemanticAsset ;
       rdfs:label "Friend of a Friend (FOAF) vocabulary" ;
       dcterms:description "The Friend of a Friend (FOAF) RDF vocabulary, described using W3C RDF Schema and the Web Ontology Language.";
       owl:versionInfo "0.1 (2007-06-16)" ;
       dcterms:type mdc:Vocabulary ;
       adms:status mdc:evaluationProposed ;
       mdv:downloadURL "http://xmlns.com/foaf/spec/index.rdf"^^xsd:anyURI ;
       mdv:downloadTime "2026-10-22T10:15:00"^^xsd:dateTime ;
       foaf:page <http://xmlns.com/foaf/spec/> ;
       dcterms:publisher csd:org-foaf-project ;
       dcterms:creator   csd:org-foaf-project ;
       # dcat:previousVersion : er ikke med i eksemplet, da det antages at det er første upload af FOAF
       dcterms:hasPart csd:4ea21847-7c6e-4886-b288-0de20f75d1ad ,       # foaf:Person
                       csd:9bb2850e-af43-4117-ae7d-6ae55bec8ea9 .       # foaf:name … (osv. et per element)

csd:org-foaf-project a org:FormalOrganization ;
       rdfs:label "FOAF Project"@en .

# The element graph for foaf:Person (named graph csd:4ea21847-…)
csd:4ea21847-7c6e-4886-b288-0de20f75d1ad
       a mdv:ElementGraph ;
       rdfs:label "Elementgraf for foaf:Person"@da ;
       dcterms:description "De triples der definerer foaf:Person i FOAF-vokabularet, version 0.1."@da ;
       adms:status mdc:accepted ;
       foaf:page <http://xmlns.com/foaf/spec/#term_Person> ;
       dcterms:isPartOf csd:e209a4b8-596d-4417-b8a1-f9eff775a5ae .

# The dictionary item: the element IRI itself
foaf:Person
       a mdv:DictionaryItem ;
       rdfs:isDefinedBy  csd:e209a4b8-596d-4417-b8a1-f9eff775a5ae ;
       mdv:definingGraph csd:4ea21847-7c6e-4886-b288-0de20f75d1ad ;
       mdv:itemType      mdc:Class ;
       mdv:itemDescription "En person, dvs. et menneske, uanset om personen er levende, død, virkelig eller fiktiv."@da .   # editorial

# ---------------------------------------------------------------------------
# named graphs:
# ---------------------------------------------------------------------------

GRAPH csd:e209a4b8-596d-4417-b8a1-f9eff775a5ae {
    foaf: a owl:Ontology ;
          dc:title "Friend of a Friend (FOAF) vocabulary" ;
          dc:description "The Friend of a Friend (FOAF) RDF vocabulary, described using W3C RDF Schema and the Web Ontology Language." ;
          dc:date "$Date: 2007-06-16 23:18:26 $" .
    # … resten af foaf.ttl …
}

GRAPH csd:4ea21847-7c6e-4886-b288-0de20f75d1ad {
    foaf:Person
        a owl:Class ;
        rdfs:comment "A person." ;
        rdfs:isDefinedBy foaf: ;
        rdfs:label "Person" ;
        rdfs:subClassOf <http://www.w3.org/2003/01/geo/wgs84_pos#SpatialThing> ,
                        foaf:Agent ;
        owl:disjointWith foaf:Document , foaf:Organization , foaf:Project ;
        vs:term_status "stable" .
}
```