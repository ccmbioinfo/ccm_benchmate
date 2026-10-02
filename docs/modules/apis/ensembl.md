---
layout: default
title: Ensembl
parent: APIs
grand_parent: Modules
nav_order: 1
---

## ensembl.Ensembl

**Description:**  
Client for the Ensembl REST API. Supports gene, variant, phenotype, sequence, mapping, and overlap queries. There are a lot of different functionalities in each of the different methods so please
test different options to see which one is best suited for your needs. 

### Variation methods

```python
from benchmate.apis import Ensembl
from benchmate.ranges import GenomicRange

ensembl = Ensembl()

# Variation info
info = ensembl.variation("rs56116432", add_annotations=True) # if you do not use the add annotations option the response would be a lot smaller

# this returns all the variants that are mentioned in a specific paper keep in mind that if you are looking for a very recent
# paper it might not be available yet
info_pub = ensembl.variation("26318936", method="publication", pubtype="pubmed")

# translate method translates one variant representation to other formats
info_translated = ensembl.variation("rs56116432", method="translate")
info_translated.results
```

### VEP

VEP is Ensembl's **V**ariant **E**ffect **P**redictor. You can run VEP on a single variant and return **a lot** of information based on what additionaly tools you have selected to use. To be able to use the VEP method you will need to use
`ccm_benchmate.variant.variant` module.

```python
from benchmate.variant import SequenceVariant
myvar = SequenceVariant(chrom="1", pos=55051215, ref="G", alt="GA")

vep_info = ensembl.vep(species="human", variant=myvar, tools=None)
vep_info.results
```

There are many tools that can be called with the VEP method. You can view all available VEP tools via:

```python
ensembl.show_vep_tools()
```

### Sequence & Homology

You can retrieve genomic, cDNA, or protein sequences directly by ID, or query orthologues and paralogues:

```python
# Fetch sequence by accession or gene symbol
seq_data = ensembl.sequence(id="ENSG00000139618", sequence_type="genomic")

# Find orthologues for a gene in a target species
orthologues = ensembl.homology(id="ENSG00000139618", type="orthologues", target_species="mouse")
```

### Phenotype

If you are interested in what phenotypes are associated with a genomic region you can use the `GenomicRanges` module and the phenotype method:

```python
from benchmate.ranges import GenomicRange
grange = GenomicRange("9", 22125503, 22125520, "+")
phenotypes = ensembl.phenotype(grange)

# Search for overlapping features (transcripts, exons, regulatory elements)
overlap = ensembl.overlap(grange, features=["transcript"])
```

### Mapping

If you have a genomic feature ID and you want to convert coordinates to cDNA or protein positions (or vice versa), use the mapping method:

```python
ensembl.mapping("ENST00000650946", 100, 120, type="cDNA")
```

### Xrefs & Info

Ensembl is a massive resource containing cross-references to other databases (UniProt, RefSeq, HGNC, etc.). Use `xrefs` to resolve IDs across platforms:

```python
xrefs = ensembl.xrefs("ENSG00000139618")
```

Finally, you can inspect species list and available API features using `ensembl.info()`.



