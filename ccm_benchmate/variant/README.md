---
layout: default
title: Variant
---

# Variant Module

This module defines classes for representing and annotating different types of genetic variants, including SNVs, indels, structural variants, and tandem repeats.
This module is not meant for you to store your variant for a whole genome or exome sequencing. Currenlt there is no support for 
storing large number of variants (in the order of 100s of millions, which would be about 40-50 WGS samples). That support might come in the future. 

If you have a smaller subset of variants that is the result of a filtered vcf file you might be able to use this to represent them and
store them in the knowledegbase database. 

---

## Classes

### `BaseVariant`

**Description:**  
Base class for all variant types. Stores core attributes such as chromosome, position, filter status, ID, and annotations.

**Public Methods & Usage:**
```python
from ccm_benchmate.variant.variant import BaseVariant

# Create a base variant
variant = BaseVariant(chrom="1", pos=12345, filter="PASS")

# Add an annotation
variant.add_annotation("impact", "HIGH")

# Query an annotation
impact = variant.query_annotation("impact")
```

---

### `SequenceVariant`

**Description:**  
Represents SNV and indel variants. Extends `BaseVariant` with reference/alternate alleles and sample/callset-specific fields.

**Public Methods & Usage:**
```python
from ccm_benchmate.variant.variant import SequenceVariant

# Create a sequence variant
seq_var = SequenceVariant(
    chrom="1", pos=12345, ref="A", alt="T", qual=99.0, gt="0/1", dp=30
)

# Add and query annotations (inherited)
seq_var.add_annotation("gene", "BRCA1")
gene = seq_var.query_annotation("gene")
```

---

### `StructuralVariant`

**Description:**  
Represents structural variants (e.g., INS, DEL, INV, DUP, BND, CNV). Extends `BaseVariant` with SV-specific fields.

**Public Methods & Usage:**
```python
from ccm_benchmate.variant.variant import StructuralVariant

# Create a structural variant
sv = StructuralVariant(
    chrom="2", pos=20000, svtype="DEL", end=20500, svlen=500, gt="1/1"
)

# Annotate and query
sv.add_annotation("clinical_significance", "pathogenic")
significance = sv.query_annotation("clinical_significance")
```

---

### `TandemRepeatVariant`

**Description:**  
Represents tandem repeat variants, including repeat motif, allele length, and sample-specific metrics.

**Public Methods & Usage:**
```python
from ccm_benchmate.variant.variant import TandemRepeatVariant

# Create a tandem repeat variant
tr = TandemRepeatVariant(
    chrom="3", pos=30000, end=30020, motif="CAG", al=10, gt="0/1"
)

# Annotate and query
tr.add_annotation("repeat_expansion", True)
is_expanded = tr.query_annotation("repeat_expansion")
```

You can convert these variants to HGVS format using the `to_hgvs` method:

While you can use this function on its own for your own, it is also useful to be used in the api.ensemble.Ensembl.vep method among others. 

```python
from ccm_benchmate.variant.variant import SequenceVariant
from ccm_benchmate.variant.utils import to_hgvs
# Convert to HGVS format

seq_var = SequenceVariant(
    chrom="1", pos=12345, ref="A", alt="T", qual=99.0, gt="0/1", dp=30
)
hgvs_variant = to_hgvs(seq_var)
```

How the data is stored:

The variants are stored in a knowledge base database, which allows for efficient querying and retrieval of variant information. Each variant type has its own table with fields corresponding to the attributes defined in the classes. 
Annotations are stored in a separate table linked to the variant tables, allowing for flexible and extensible annotation of variants. Annotations are basic `JSON` columns
which are then converted to `BSON` by postgres and are then back loaded as dictionaries. Currently we have not structured the database to support billions of variants
and their annotations that you would get form a large scale GWAS study. If you are planning to use this as a variant store you can for your filtered variants. Also keep in mind that
there is no column for distinguishing samples. You will need a secondary table to track the variant->sample connection. 

Please create an issue if you think this is a desirable feature. 

