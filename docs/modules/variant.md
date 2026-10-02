---
layout: default
title: Variants
parent: Modules
nav_order: 10
---

# Variant Module

The **Variant** module represents genetic variations including single nucleotide variants (SNVs), insertions/deletions (indels), structural variants (SVs), and tandem repeat expansions. 

*Note: This module is intended for small to moderate sets of filtered variants rather than raw whole-genome VCF callsets with millions of sites.*

---

## Class Hierarchy & Public Methods

### 1. `BaseVariant`

Abstract base class for all variant types.

- `add_annotation(key, value)`: Attach metadata (scalars, dictionaries, or DataFrames).
- `query_annotation(key)`: Retrieve annotation by key name.
- `show_annotations()`: Return a list of all attached annotation key names.
- `to_gr()`: Convert variant position/interval to a `GenomicRange` object.

---

### 2. `SequenceVariant`

Represents single nucleotide variants (SNVs), insertions, deletions, and complex indels.

- `variant_type`: Property returning `"SNP"`, `"Insertion"`, `"Deletion"`, `"Indel"`, or `"Complex"`.
- `is_snv`: Boolean property checking if the variant is a Single Nucleotide Variant.
- `is_indel`: Boolean property checking if the variant is an Insertion or Deletion.
- `is_transition`: Boolean property returning `True` for purine-purine (A<->G) or pyrimidine-pyrimidine (C<->T) transitions.
- `len()`: Length difference between alternate and reference alleles (`len(alt) - len(ref)`).

```python
from benchmate.variant import SequenceVariant

# Instantiate SequenceVariant
snv = SequenceVariant(chrom="chr17", pos=43044295, ref="G", alt="A", qual=99.0, gt="0/1")

# Properties & Classifications
print("Type:", snv.variant_type)     # "SNP"
print("Is SNV:", snv.is_snv)         # True
print("Transition:", snv.is_transition) # True

# Convert to GenomicRange
gr = snv.to_gr()
```

---

### 3. `StructuralVariant`

Represents large structural changes including DEL, DUP, INV, INS, BND, and CNVs.

- `svtype`: Structural variant type (e.g. `"DEL"`, `"DUP"`, `"INV"`).
- `end`: End genomic coordinate of the structural variant.
- `reciprocal_overlap(other)`: Calculate reciprocal genomic interval overlap fraction (float between 0 and 1) with another `StructuralVariant`.
- `is_copy_number_change`: Property indicating whether the SV involves copy number changes (DEL/DUP/CNV).

```python
from benchmate.variant import StructuralVariant

# Create structural deletion
sv1 = StructuralVariant(chrom="chr2", pos=20000, svtype="DEL", end=20500, svlen=-500)
sv2 = StructuralVariant(chrom="chr2", pos=20100, svtype="DEL", end=20600, svlen=-500)

# Overlap calculation
overlap_frac = sv1.reciprocal_overlap(sv2)
print(f"Reciprocal overlap: {overlap_frac:.2%}")
```

---

### 4. `TandemRepeatVariant`

Represents microsatellite and tandem repeat expansion/contraction variants.

- `repeat_unit`: Repeat motif sequence (e.g. `"CAG"`).
- `repeat_count`: Number of repeat units present.
- `is_expansion`: Boolean check whether repeat count expanded beyond reference.
- `is_contraction`: Boolean check whether repeat count contracted.

```python
from benchmate.variant import TandemRepeatVariant

# Create tandem repeat variant
tr = TandemRepeatVariant(chrom="chr4", pos=3074876, end=3074936, motif="CAG", repeat_count=45, ref_count=20)
print("Is Expansion:", tr.is_expansion) # True
```

---

## Utilities & HGVS Formatting

Use `to_hgvs()` to format sequence variants into standard HGVS nomenclature strings:

```python
from benchmate.variant import SequenceVariant, to_hgvs

seq_var = SequenceVariant(chrom="chr1", pos=12345, ref="A", alt="T")
hgvs_str = to_hgvs(seq_var)
```

---

## Knowledge Base Persistence (`to_kb` / `from_kb`)

When managed through a `Project` meta-module instance, variants can be saved to PostgreSQL and retrieved using unique identifiers:

```python
# Save variant to project Knowledge Base
my_project.sequence_variant(chrom="chr17", pos=43044295, ref="G", alt="A").to_kb()

# Retrieve saved variant by database ID
saved_var = my_project.sequence_variant.from_kb(id=42)
```


