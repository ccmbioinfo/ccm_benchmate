---
layout: default
title: UniProt
parent: APIs
grand_parent: Modules
nav_order: 3
---

## uniprot.Uniprot

Uniprot is an extensive database of proteins and features of proteins, It has several API endpoints, the ones that are integrated 
are the most compreshenive ones called: proteins, mutagensis (high throughput mutagenesis experiments), isoforms and variation. 
You can query this using a single command like so:

```python
from benchmate.apis import UniProt
uniprot=UniProt()

results=uniprot.search_uniprot(uniprot_id="P01308", get_isoforms=True, get_variations=True,
                       get_mutagenesis=True, get_interactions=True, consolidate_refs=True, )
```

The results are consolidated into a few different locations, you can see the references under `results["references"]` as 
pubmed ids, there is a `description` that is a plain human readable text of describing the protein. All the keys are below:

```python
dict_keys(['id', 'name', 'sequence', 'organism', 'gene', 'feature_types', 'comment_types', 'references', 'xref_types', 'xrefs', 'description', 
'json', 'secondary_accessions', 'variation', 'interactions', 'mutagenesis', 'isoforms'])
```

You can see what kinds of features are available for a given protein using `get_features` method or you can you 
`get_comments` method to see other kinds of annotations that are more about the whole protein.

```python
results["comment_types"]
results["feature_types"]

uniprot.get_features(results["json"], "SIGNAL")
uniprot._get_comments(results["json"], "DISEASE")
```

If you do now know the uniprot id of the protein you are interested in it is also possible to search the uniprot database using keywors with the search function:

```python
search_results=uniprot.search("important biological question")
```

This will return a dataframe that contains the uniprot id, gene name, its synonyms and a brief description. You can then use
the ids provided in the dataframe to get all the results you need. 
