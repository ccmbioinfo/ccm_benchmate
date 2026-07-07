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
myvar= SequenceVariant("variant_id", 1, 55051215, 'G', 'GA', {})

vep_info = ensembl.vep(species="human", variant=myvar, tools=None)
vep_info.results
```

There are many tools that can be called with the VEP method. You can see the whole list in the VEP [website](https://useast.ensembl.org/info/docs/tools/vep/script/vep_options.html)

### Phenotype

If you are interested in what phenotypes are associated with a genomic region you can use the `GenomicRanges` module and the phenotype method:

```python
from benchmate.ranges import GenomicRange
grange = GenomicRange(9, 22125503, 22125520, "+")
phenotypes = ensembl.phenotype(grange)
phenotypes

# or for a given range you can search for overlapping features (you can also do this in the genome module and it's the preffered method if you are planning to query a lot of different things)
overlap = ensembl.overlap(grange, features=["transcript"])
```

### Mapping

If you have some genomic feature id and you want to convert them to something else you can use the mapping method. This could mean convering genomic coordinates to cDNA or protein coordinates to genomic coordinates etc. 

```python

ensembl.mapping("ENST00000650946", 100, 120, type="cDNA")

```

### xrefs

Ensembl is a massive resource, it contains constantly updated cross-references to other databases. This is especially useful in our case because we can use this method to retrieve ids which then can be used to query other enpoints. 

```python
xrefs = ensembl.xrefs("ENSG00000139618")
```

Finally, you can return about the species, and the kinds of information that is available in the api (there may be changes and that is beyond our control) using `Ensembl.info` method.



