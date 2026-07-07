---
layout: default
title: Ontology Lookup Service (OLS)
parent: APIs
grand_parent: Modules
nav_order: 9
---

## apis.ols.OLS

Ontology Lookup Service (OLS) is a service provided by the European Bioinformatics Institute (EBI) 
that allows users to access and query a wide range of biomedical ontologies. Benchmate provides 
an interface to interact with OLS through the `OLS` class. This way you do not have to deal with the 
owl files directly and can use benchmate's data structures to work with ontology terms.

In this implementation I'm assuming that you know which ontology you want to query and the term you are looking for
I am not sure if there is a demand for the other way around that is finding ontologies based on keywords. If so 
please create an issue on github.

```python
from benchmate.apis import OLS
ols=OLS()

#get all available ontologies
ontologies=ols.get_ontologies()

#get the details of a specific ontology
go_details=term=ols.get_term(ontology_id="go", term_id="GO:0008150", 
                             get_graph=True, get_parents=True, 
                             get_children=True, get_ancestors=True, get_descendants=True)
```

The `get_term` method allows you to retrieve detailed information about a specific term within a given ontology.
You can specify whether you want to retrieve additional information such as the term's graph, parents, children, ancestors, 
and descendants by setting the corresponding parameters to `True`.

Graph refers to the directed acyclic graph (DAG) structure of the ontology, which represents the relationships between terms.
the retruned graph is a simple python dict that contains the nodes and their iris and the edges between them.

The parents, children, ancestors, and descendants parameters allow you to retrieve the respective relationships are simple
python dicttionaries as well. In the next push I will convert them to benchmate's own data structures.