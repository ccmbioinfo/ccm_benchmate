---
layout: default
title: Sequence
---

# Sequence Module

A module for working with biological sequences, providing sequence analysis, alignment, and embedding capabilities.

## Classes Overview

- `Sequence`: Base class for working with sequences
- `SequenceList`: Class for working with collections of sequences (not yet fully implemented)

## Sequence

The main class for working with individual sequences, providing methods for sequence analysis, mutation, 
alignment and searching.

### Basic Usage

```python
from ccm_benchmate.sequence.sequence import Sequence

# Create a sequence object
seq = Sequence(name="my_sequence", sequence="MKLLPRGPAAAAAAVLLLLSLLLLPQVQA")

# Generate embeddings (protein sequences only)
embeddings = seq.embeddings(
    model="esmc_300m",  # Options: esmc_300m, esmc_g00m
    normalize=False     # Whether to normalize embeddings
)

# Introduce mutations
mutated = seq.mutate(
    position=3,   # 0-based position 
    to="A",       # Amino acid to mutate to
    new_name="mutant_1"  # Optional new name
)
```

### Multiple Sequence Alignment

```python
# Run MSA using MMseqs2
aligned = seq.msa(
    database="/path/to/mmseqs/db",      # Pre-processed MMseqs2 database
    destination="/path/for/output/",     # Output directory
    output_name="my_msa.a3m",           # Output filename
    cleanup=True                         # Remove temporary files
)
```

### BLAST Search

```python
# Search sequence using NCBI BLAST
results = seq.blast(
    program="blastp",      # BLAST program to use
    database="nr",         # Database to search against  
    threshold=10,          # E-value threshold
    hitlist_size=50       # Maximum number of hits to return
)
```

### File Operations

```python
# Write sequence to FASTA file
seq.write("/path/to/output.fasta")
```

## Key Features

### Sequence Operations
- Sequence manipulation and mutation
- Generate sequence embeddings using ESM models
- Multiple sequence alignment using MMseqs2
- BLAST searching through NCBI API

### Supported Models for Embeddings
- ESMC 300M
- ESMC 600M

### File Formats
- FASTA input/output
- A3M format for MSA output

## Notes

- Embeddings require GPU support (falls back to CPU if unavailable)
- MMseqs2 must be installed for MSA functionality (Will move `ContainerRunner`)
- BLAST searches use NCBI's web API

