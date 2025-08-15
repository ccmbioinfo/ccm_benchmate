---
layout: default
title: API
---

from PIL.features import featuresfrom PIL.features import featuresfrom 
sympy.physics.units.definitions.dimension_definitions import information

# API's module

This module includes the API classes for the ccm_demo application. Each API class is responsible for 
handling a specific type of request and returning the appropriate response. The classes assume that you know what you are
looking for and gives you the power to link different public databases to each other programmatically. Each of the apis
return a dictionary with varying degrees and the parsing also is different. The API classes are as follows:

The apis marked with (WIP) are still under development and may not be fully functional yet.

+ Ensembl
+ Uniprot
+ NCBI E utils
+ Reactome
+ stringdb
+ Intact
+ RNAcentral
+ EBI tools (requires testing)
+ BioGrid


Here is a `README.md` for the classes under `ccm_benchmate/apis`. Each section describes the class and provides usage examples for each public method.

---

## ensembl.Ensembl

**Description:**  
Client for the Ensembl REST API. Supports gene, variant, phenotype, sequence, mapping, and overlap queries.

**Usage Examples:**
```python
from ccm_benchmate.apis.ensembl import Ensembl
from ccm_benchmate.ranges.genomicranges import GenomicRange

ensembl = Ensembl()

# Variation info
info = ensembl.variation("rs56116432")
info_translated = ensembl.variation("rs56116432", method="translate")
info_pub = ensembl.variation("26318936", method="publication", pubtype="pubmed")

# VEP (requires Variant class)
# myvar = Variant(1, 6524705, 6524705, "C", "T")
# vep_info = ensembl.vep(myvar, check_exists=True)

# Phenotype
grange = GenomicRange(9, 22125503, 22125502, "+")
phenotypes = ensembl.phenotype(grange)

# Sequence
seq = ensembl.sequence("ENSG00000139618")

# Overlap
features = ["gene", "transcript", "cds", "exon", "repeat"]
overlap = ensembl.overlap(grange, features)

# Xrefs
xrefs = ensembl.xrefs("ENSG00000139618")

# Mapping
mapping = ensembl.mapping("ENSP00000288602", 100, 300)

# Info
info = ensembl.info()
```

---

## uniprot.Uniprot

**Description:**  
Client for the UniProt API. Retrieves protein information, mutagenesis data, isoforms, and protein-protein interactions.

**Usage Examples:**
```python
from ccm_benchmate.apis.uniprot import Uniprot

uniprot = Uniprot()

# Get protein info
protein_info = uniprot.get_protein("P38398")

# Mutagenesis
mutagenesis = uniprot.get_mutagenesis("P38398")

# Isoforms
isoforms = uniprot.get_isoforms("P38398")

# Interactions
interactions = uniprot.get_interactions("P38398")
```

---

## others.BioGrid

**Description:**  
Client for the BioGRID API. Retrieves molecular interaction data, evidence types, organisms, and supported identifiers.

**Usage Examples:**
```python
from ccm_benchmate.apis.others import BioGrid

biogrid = BioGrid(access_key="YOUR_BIOGRID_KEY")

# Interactions
interactions_df = biogrid.interactions(
    gene_list=["TP53", "BRCA1"],
    id_types=["entrez"],
    evidence_types=["physical"]
)

# Evidence types
evidence_types = biogrid._get_evidence_types()

# Organisms
organisms = biogrid._get_organisms()

# Supported identifiers
id_types = biogrid._get_supported_identifiers()
```

---

## others.Intact

**Description:**  
Client for the IntAct molecular interaction database. Fetches protein-protein interactions using EBI IDs.

**Usage Examples:**
```python
from ccm_benchmate.apis.others import Intact

intact = Intact()

# Search for interactions by EBI ID
interactions, last_page = intact._search("EBI-123456")

# Retrieve all interactions for a given interactor (requires intact.interactions to be set)
# all_interactions_df = intact.intact_search(page=0, page_size=1000)
```

---

## reactome.Reactome

**Description:**  
Client for the Reactome API. Accesses pathway and reaction data for genes and proteins.

**Usage Examples:**
```python
from ccm_benchmate.apis.reactome import Reactome

reactome = Reactome()

# Get pathways for a gene
pathways = reactome.get_pathways("TP53")
```

---

## rna.RNACentral

**Description:**  
Client for the RNAcentral API. Retrieves non-coding RNA information and cross-references.

**Usage Examples:**

```python
from ccm_benchmate.apis.rnacentral import RNACentral

rna_central = RNACentral()

# Get RNA info
rna_info = rna_central.get_rna("URS000075C6A6")
```

---

## stringdb.Stringdb

**Description:**  
Client for the STRING database API. Fetches protein-protein interaction networks and functional enrichment data.

**Usage Examples:**
```python
from ccm_benchmate.apis.stringdb import Stringdb

stringdb = Stringdb()

# Get interaction network
network = stringdb.get_network("9606.ENSP00000354587")
```

---
