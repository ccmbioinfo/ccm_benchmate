---
layout: default
title: RNACentral
parent: APIs
grand_parent: Modules
nav_order: 8
---

## rnacentral.RnaCentral

Last but not least we have RNA Central, you will need the RNA Central id to query, you can get most of these through Ensembl xrefs

```python
from benchmate.apis import RnaCentral

#you need the rnacentral id to search
rnacentral=RnaCentral()

results=rnacentral.get_information(id="URS00000CE0D1")
results.keys()

dict_keys(['url', 'rnacentral_id', 'md5', 'sequence', 'length', 'xrefs', 'publications', 'is_active', 'description', 
    'rna_type', 'count_distinct_organisms', 'distinct_databases', 'references'])
```

The results are fairly obvious. 