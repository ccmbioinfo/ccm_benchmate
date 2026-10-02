---
layout: default
title: IntAct
parent: APIs
grand_parent: Modules
nav_order: 7
---

## others.IntAct

Intact is one other interaction database. There were a lot of requests to include all of these in the package. While they provide similar information they do have different use cases.

```python
from benchmate.apis import IntAct
intact=IntAct(page_size=100)

# Search interactions for an interactor ID (e.g. UniProt/EBI ID)
interactions=intact.search_interactions("Q05471")

# Search interactors matching a keyword query
interactors=intact.search_interactors("TP53")
```

Intact database contains information not just about protein-protein interactions but also other molecule types. 
This means your response could be quite large. Also I have integrated so that the API keeps searching for interactions 
until the last page is reached. This means you will get all the results once the request is complete but if your request 
has a lot of information it might take a few seconds or more.