---
layout: default
title: Reactome
parent: APIs
grand_parent: Modules
nav_order: 4
---

## reactome.Reactome

Reactome is more concerned about biological reactions, pathways and the genes/proteins that are associated with it. You need to know your reactome id but I think we can figure that out either through Ensembl or Uniprot.

```python
from benchmate.apis import Reactome
reactome=Reactome()

# initialization gathers some information that is up to date, these are the fields you can search for
reactome.show_fields()

['species', 'type', 'keyword', 'compartment']

# see all species
reactome.show_values("species")

# search
results=reactome.query(query="cancer", species="Homo sapiens", force_filters=False)

results.keys()
dict_keys(['Pathway', 'Reaction', 'Interactor', 'Set', 'Protein', 'Complex', 'DNA Sequence', 'Icon'])

#get more details about one of the things
details=reactome.get_details(results["Pathway"][0]["dbId"])

details.keys()
dict_keys(['dbId', 'displayName', 'stId', 'stIdVersion', 'created', 'modified', 'isInDisease', 'isInferred', 'name', 'releaseDate', 
    'speciesName', 'authored', 'disease', 'edited', 'literatureReference', 'species', 'summation', 'reviewStatus', 'hasDiagram', 
    'hasEHLD', 'hasEvent', 'normalPathway', 'schemaClass', 'className'])
```

Each of the details has more information that are also stored as dictionaries. The API output is very consistent and some of the fields will be there reliably. That said, it will not hurt to do some basic checks like `"something" in results.keys()` if you are planning to loop through a lot of information. 