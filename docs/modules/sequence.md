---
layout: default
title: Sequence
parent: Modules
nav_order: 5
---

# Sequence Module

The **Sequence** module represents biological sequences including DNA, RNA, protein, and 3Di structures. It provides comprehensive methods for sequence manipulation, feature calculation, file I/O, alignment, and external web tool integrations.

---

## `Sequence` Class

Represents an individual biological sequence with metadata and analytical tools.

### Constructor & Instantiation

```python
from benchmate.sequence import Sequence

# Initialize a sequence
seq = Sequence(
    name="my_sequence", 
    sequence="MKLLPRGPAAAAAAVLLLLSLLLLPQVQA", 
    seq_type="protein",           # "protein", "dna", "rna", or "3di"
    annotations={"gene": "EGFR"}  # Optional metadata dictionary
)
```

### User-Facing Methods

#### Sequence Editing & Manipulation

- `subseq(start, end, keep_annotations=True)`: Return a subsequence slice from index `start` to `end` (0-based, half-open).
- `mutate(position, to, new_name=None, keep_annotations=True)`: Substitute a character at a specific 0-based position.
- `insert(position, segment, keep_annotations=True)`: Insert a sequence segment at the specified index.
- `delete(start, end, keep_annotations=True)`: Delete a slice from `start` to `end` (0-based, half-open).
- `reverse_complement(keep_annotations=True)`: Compute the reverse complement of DNA or RNA sequences.
- `translate(table=1, keep_annotations=True, to_stop=False)`: Translate DNA or RNA into a protein `Sequence` object.

#### Sequence Properties & Composition

- `find(subseq)`: Return all 0-based start indices where `subseq` occurs (allowing overlapping hits).
- `kmer_counts(k, normalize=True)`: Calculate k-mer frequency distributions.
- `gc_content(window=None)`: Calculate overall GC fraction or rolling mean over a sliding window (DNA/RNA).
- `gc_skew(window)`: Compute GC skew `(G - C) / (G + C)` over a sliding window (DNA/RNA).
- `aa_composition()`: Compute fractional composition across the 20 canonical amino acids for protein sequences.
- `molecular_weight()`: Estimate molecular weight in Daltons (supports protein, DNA, and RNA).
- `isoelectric_point()`: Estimate protein isoelectric point (pI) using bisection search and EMBOSS pKa values.
- `hydropathy_profile(window=9, scale="KyteDoolittle")`: Compute sliding-window hydropathy profile for proteins.

#### External Integrations & IO

- `blast(program, database, threshold=10, hitlist_size=50)`: Run NCBI BLAST online via Web API and parse tabular results. *(For fast local BLAST database search, see the [Alignment module](alignment.md)).*
- `vienna(temperature=37, *args)`: Predict RNA secondary structure using ViennaRNA `RNAfold` via Biotite. Returns dot-bracket notation, free energy, and base pairs.
- `from_fasta(file_path, seq_type)`: Class method to parse a single sequence (or `SequenceList` if multiple) from a FASTA file.
- `to_fasta(file_path)`: Save the sequence to a FASTA file.

```python
# Protein calculations
seq = Sequence(name="prot1", sequence="MKLLPRGPAAAAAAVLLLLSLLLLPQVQA", seq_type="protein")

print("MW:", seq.molecular_weight())
print("pI:", seq.isoelectric_point())
print("Composition:", seq.aa_composition())
hydropathy = seq.hydropathy_profile(window=9)

# Mutate and slice
mutated_seq = seq.mutate(position=3, to="A")
sub_seq = seq.subseq(start=0, end=10)

# Search kmers
kmers = seq.kmer_counts(k=3, normalize=True)

# Save to file
seq.to_fasta("protein.fasta")

# DNA / RNA operations
rna_seq = Sequence(name="rna1", sequence="AUGGCCUAA", seq_type="rna")
rc_dna = Sequence(name="dna1", sequence="ATGGCC", seq_type="dna").reverse_complement()
protein_trans = rna_seq.translate(to_stop=True)

# RNA secondary structure
dot_bracket, free_energy, base_pairs = rna_seq.vienna(temperature=37)
```

---

## `SequenceList` Class

A specialized list container for managing collections of `Sequence` objects of uniform type.

### User-Facing Methods

- `ClustalOmega(*args)`: Perform multiple sequence alignment (MSA) using Clustal Omega via Biotite. Returns a tuple of `(gapped_sequences, distance_matrix, guide_tree)`.
- `from_fasta(file_path, seq_type)`: Class method to parse a multi-FASTA file into a `SequenceList`.
- `to_fasta(file_path)`: Write all contained sequences to a multi-FASTA file.

```python
from benchmate.sequence import SequenceList

# Load multi-FASTA file
seq_list = SequenceList.from_fasta("multiseq.fasta", seq_type="protein")

# Perform Multiple Sequence Alignment
gapped_seqs, dist_matrix, guide_tree = seq_list.ClustalOmega()

# Export aligned sequences
seq_list.to_fasta("aligned.fasta")
```