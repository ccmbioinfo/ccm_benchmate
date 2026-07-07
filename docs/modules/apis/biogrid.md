---
layout: default
title: BioGrid
parent: APIs
grand_parent: Modules
nav_order: 7
---

## others.BioGrid

Biogrid is a similar platform that focuses on protein-protein interactions with some experimental data 
annotations as to how that interaction is determined. To use Biogrid you need to get an access key but it is free.


```python
from benchmate.apis import BioGrid
biogrid=BioGrid(access_key="<your api key>")

interactions=biogrid.interactions(gene_list=["ENSP00000354587"]) # you can provide more than one gene

#see the results
interactions.results

# list all available organisms
biogrid.organisms
```