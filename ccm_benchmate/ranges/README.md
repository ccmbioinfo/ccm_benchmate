---
layout: default
title: Ranges
---

# Ranges and GenomicRanges Module

This module provides classes for working with numeric and genomic intervals, supporting operations such as overlap detection, subtraction, and coverage calculation.

## Classes Overview

- `Range`: Represents a simple interval with a start and end.
- `RangesList`: Manages a list of `Range` objects and provides basic operations.
- `RangesDict`: A dictionary-like container mapping keys to `RangesList` objects.
- `GenomicRange`: Extends `Range` with chromosome and strand information for genomic data.
- `GenomicRangesList`: Manages a list of `GenomicRange` objects, supporting chromosome and strand-aware operations.
- `GenomicRangesDict`: A dictionary-like container mapping chromosomes (and optionally strands) to `GenomicRangesList` objects.

---

## Range

Represents a closed interval \[start, end\] (inclusive).

**Example:**
```python
from ccm_benchmate.ranges.ranges import Range

r1 = Range(10, 20)
r2 = Range(15, 25)

print(len(r1))            # 11
print(r1.overlaps(r2))    # True
print(r1.distance(r2))    # 0 (overlapping)
print(r1.merge(r2))       # Range(10, 25)
print(r1.split(n))    # split into 2 equal parts return a RangesList: [Range(10, 15), Range(15, 20)]
```

---

## RangesList

A collection of `Range` objects with basic operations.

**Example:**
```python
from ccm_benchmate.ranges.ranges import RangesList, Range

ranges = RangesList([Range(1, 5), Range(3, 7), Range(10, 12)])

# Check for overlaps
for r in ranges:
    print(r)

# Calculate coverage: number of ranges covering each position from min(start) to max(end)
coverage = ranges.coverage()  # e.g., [1, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1]
```
Additional operations include: pop, append, extend, remove, find_overlaps, as well as some basic list operations like len, index, contains
string, and iterating, seting, and getting items and in/equality checks. Reduce method is also available to reduce the list of ranges to a single range.


## RangesDict

A dictionary-like container mapping keys (e.g., names, categories) to `RangesList` objects.

**Example:**
```python
from ccm_benchmate.ranges.ranges import RangesDict, Range, RangesList

rdict = RangesDict()
rdict["A"] = RangesList([Range(1, 10), Range(15, 20)])
rdict["B"] = RangesList([Range(5, 12)])

# Access ranges for a key
print(rdict["A"])  # RangesList([Range(1, 10), Range(15, 20)])

# Iterate over keys
for key in rdict:
    print(key, rdict[key])
```

---

## GenomicRange

Represents a genomic interval with chromosome and strand.

**Example:**
```python
from ccm_benchmate.ranges.genomicranges import GenomicRange

gr = GenomicRange("chr1", 100, 200, "+")
print(gr.chrom)    # "chr1"
print(gr.start)    # 100
print(gr.end)      # 200
print(gr.strand)   # "+"
```

---

## GenomicRangesList

A collection of `GenomicRange` objects, supporting chromosome and strand-aware operations.

**Example:**
```python
from ccm_benchmate.ranges.genomicranges import GenomicRangesList, GenomicRange

granges = GenomicRangesList([
    GenomicRange("chr1", 100, 200, "+"),
    GenomicRange("chr1", 150, 250, "+"),
    GenomicRange("chr1", 175, 300, "-"),
    GenomicRange("chr2", 100, 200, "+")
])

# Coverage per chromosome and strand
cov = granges.coverage(ignore_strand=False)
# {
#   "chr1": {
#     "+": [...],  # coverage array for + strand
#     "-": [...]   # coverage array for - strand
#   },
#   "chr2": {
#     "+": [...],
#     "-": []
#   }
# }

# Coverage per chromosome, ignoring strand
cov_all = granges.coverage(ignore_strand=True)
# {
#   "chr1": [...],  # combined coverage array
#   "chr2": [...]
# }
```

---

## GenomicRangesDict

A dictionary-like container mapping chromosomes (and optionally strands) to `GenomicRangesList` objects.

**Example:**
```python
from ccm_benchmate.ranges.genomicranges import GenomicRangesDict, GenomicRange, GenomicRangesList

gdict = GenomicRangesDict()
gdict["chr1"] = GenomicRangesList([
    GenomicRange("chr1", 100, 200, "+"),
    GenomicRange("chr1", 300, 400, "-")
])
gdict["chr2"] = GenomicRangesList([
    GenomicRange("chr2", 500, 600, "+")
])

# Access ranges for a chromosome
print(gdict["chr1"])  # GenomicRangesList([...])

# Iterate over chromosomes
for chrom in gdict:
    print(chrom, gdict[chrom])
```

---

## Functionality Summary

- **Range**: Overlap, merge, subtract, length, distance.
- **RangesList**: Store and operate on multiple `Range` objects, compute coverage.
- **RangesDict**: Map keys to `RangesList` objects for grouped operations.
- **GenomicRange**: Chromosome and strand-aware intervals.
- **GenomicRangesList**: Chromosome/strand-aware storage and coverage (with or without strand).
- **GenomicRangesDict**: Map chromosomes (and optionally strands) to `GenomicRangesList` objects.

---

## Notes

- All intervals are 1-based and inclusive.
- There is no check for chromosome lengths; we assume that you know how big your chromosomes are. 
- Coverage arrays start at the minimum start and end at the maximum end for each chromosome (and strand, if applicable).
- For large datasets, consider memory usage when using coverage methods.

