---
layout: default
title: Sequence Module
nav_order: 7
---

# Sequence Module

A module for working with biological sequences, providing sequence analysis, alignment, and embedding capabilities. Currenlty, 
the functionalities are limited to but are expanding. 

We are trying to make the sequence methodologies as type agnostic as possible, and this puts a limitation on the 
functionalities that can be provided.


## Sequence

The main class for working with individual sequences, providing methods for sequence analysis, mutation, 
alignment and searching.

### Basic Usage

```python
from benchmate.sequence.sequence import Sequence

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

## Future directions:

We are working on adding more functionalities to this module. While it is tempting to add a lot of stuff using some of the 
latest deeplearning models and predict a bunch of things about a sequence that is well beyond the scope of this module and 
will also cause the number of dependencies to explode. We are trying to keep this module light and focused on the core functionalities.

For other predictions or advanced tasks we are aiming to use the [containers](containers.md) module. This will allow us and you
to use whatever method and model you want and then re-create a Sequence object with the results. 