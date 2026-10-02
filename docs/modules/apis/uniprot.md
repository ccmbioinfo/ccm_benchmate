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

# Get detailed information for a specific UniProt ID
results=uniprot.get_info(uniprot_id="P01308", get_isoforms=True, get_variations=True,
                         get_mutagenesis=True, get_interactions=True, consolidate_refs=True)
```

The results are consolidated into an `ApiCall` object whose `.results` dictionary contains the details. You can see the references under `results["references"]` as PubMed IDs, and a human-readable `description`. All the keys in the result dictionary are:

```python
dict_keys(['id', 'name', 'sequence', 'organism', 'gene', 'feature_types', 'comment_types', 'references', 'xref_types', 'xrefs', 'description', 
'json', 'secondary_accessions', 'variation', 'interactions', 'mutagenesis', 'isoforms'])
```

### User-Facing Methods

- `search(query, page_size=500)`: Search UniProt by text query or keywords. Returns a pandas DataFrame with UniProt IDs, gene names, synonyms, and descriptions.
- `get_info(uniprot_id, ...)`: Retrieve complete entry details (sequence, features, isoforms, variants, mutagenesis data) for a protein ID.
- `get_features(results, feature_types)`: Extract specific feature annotations (e.g. `"SIGNAL"`, `"CHAIN"`, `"BINDING"`) from the raw JSON response.
- `get_comments(results, types)`: Extract functional comments (e.g. `"DISEASE"`, `"FUNCTION"`, `"SUBCELLULAR LOCATION"`) from the entry JSON.

```python
# Inspect available comment & feature categories
print(results["comment_types"])
print(results["feature_types"])

# Extract specific features or comments
signal_features = uniprot.get_features(results["json"], "SIGNAL")
disease_comments = uniprot.get_comments(results["json"], "DISEASE")
```

If you do not know the UniProt ID of the protein you are interested in, you can search UniProt using keywords:

```python
search_results=uniprot.search("insulin human")
```

This will return a dataframe that contains the uniprot id, gene name, its synonyms and a brief description. You can then use
the ids provided in the dataframe to get all the results you need. 
