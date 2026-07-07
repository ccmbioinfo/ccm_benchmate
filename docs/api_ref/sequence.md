---
layout: default
title: Sequence
parent: API Reference
nav_order: 5
---

<a id="benchmate.sequence"></a>

# benchmate.sequence

<a id="benchmate.sequence.sequence"></a>

# benchmate.sequence.sequence

<a id="benchmate.sequence.sequence.Sequence"></a>

## Sequence Objects

```python
class Sequence()
```

A biological sequence with associated metadata and utility methods.

<a id="benchmate.sequence.sequence.Sequence.blast"></a>

#### blast

```python
def blast(program, database, threshold=10, hitlist_size=50)
```

using the ncbi blast api run blast, I am not sure if localblast is needed

**Arguments**:

- `program`: which blast program to use
- `database`: which database to use
- `threshold`: e value threshold
- `hitlist_size`: how many hits to return
- `write`: whether to write the output file

**Returns**:

either the alignment dataframe or a Bio.SeqIO file connection or both

<a id="benchmate.sequence.sequence.Sequence.vienna"></a>

#### vienna

```python
def vienna(temperature=37, *args)
```

Predict RNA secondary structure using ViennaRNA RNAfold via Biotite.

**Arguments**:

- `temperature`: what temperature to use for folding
- `args`: additional arguments passed to vienna a string or a list of strings

**Returns**:

structure in dot-bracket notation, free energy in kcal/mol, list of base pairs

<a id="benchmate.sequence.sequence.Sequence.subseq"></a>

#### subseq

```python
def subseq(start, end, keep_features=True)
```

Return subsequence [start:end) (0-based, half-open).

<a id="benchmate.sequence.sequence.Sequence.find"></a>

#### find

```python
def find(subseq: str)
```

Returns all start indices (0-based) where subseq occurs (allowing overlaps).
Case-insensitive match.

<a id="benchmate.sequence.sequence.Sequence.reverse_complement"></a>

#### reverse\_complement

```python
def reverse_complement(keep_features=True)
```

reverse complement the sequence only works for dna and rna

**Arguments**:

- `keep_features`: keep the original features

**Returns**:

another Sequence instance

<a id="benchmate.sequence.sequence.Sequence.translate"></a>

#### translate

```python
def translate(table=1, keep_features=True, to_stop=False)
```

Translate nucleic acids to protein. Uses Biopython table if available; otherwise

supports only standard table (1) for unambiguous triplets; ambiguous codons → 'X'.

**Arguments**:

- `keep_features`: keep existing features

<a id="benchmate.sequence.sequence.Sequence.gc_content"></a>

#### gc\_content

```python
def gc_content(window=None)
```

GC fraction overall, or rolling mean over window (DNA/RNA).

<a id="benchmate.sequence.sequence.Sequence.gc_skew"></a>

#### gc\_skew

```python
def gc_skew(window) -> np.ndarray
```

GC skew = (G - C) / (G + C) in sliding windows.

<a id="benchmate.sequence.sequence.Sequence.kmer_counts"></a>

#### kmer\_counts

```python
def kmer_counts(k: int, normalize: bool = True) -> Dict[str, float]
```

Counts (or frequencies) of k-mers (case-insensitive).

<a id="benchmate.sequence.sequence.Sequence.aa_composition"></a>

#### aa\_composition

```python
def aa_composition() -> Dict[str, float]
```

Fractional composition over the 20 canonical amino acids (others grouped as 'X').

<a id="benchmate.sequence.sequence.Sequence.molecular_weight"></a>

#### molecular\_weight

```python
def molecular_weight() -> float
```

Approximate molecular weight in Daltons (average mass, subtract water for peptide bonds).

<a id="benchmate.sequence.sequence.Sequence.isoelectric_point"></a>

#### isoelectric\_point

```python
def isoelectric_point() -> float
```

Estimate pI using Henderson–Hasselbalch with a bisection search.
Uses an EMBOSS-like pKa set.

<a id="benchmate.sequence.sequence.Sequence.hydropathy_profile"></a>

#### hydropathy\_profile

```python
def hydropathy_profile(window=9, scale="KyteDoolittle") -> np.ndarray
```

Sliding-window hydropathy. Only 'KyteDoolittle' is supported.
Returns an array of length L - window + 1 (centered windows).

<a id="benchmate.sequence.sequence.Sequence.mutate"></a>

#### mutate

```python
def mutate(position, to, new_name=None, keep_features=True)
```

Mutata a specific location to something else, use caution we are not checking for validitiy that is you can
insert arbitrary things

<a id="benchmate.sequence.sequence.Sequence.insert"></a>

#### insert

```python
def insert(position, segment, keep_features=True)
```

Insert segment at position (0-based index before insertion).

<a id="benchmate.sequence.sequence.Sequence.delete"></a>

#### delete

```python
def delete(start, end, keep_features=True) -> "Sequence"
```

Delete [start:end) (0-based, half-open).

<a id="benchmate.sequence.sequence.Sequence.from_fasta"></a>

#### from\_fasta

```python
@classmethod
def from_fasta(cls, file_path, seq_type)
```

Read one or many sequences from a FASTA file. If there are multiple sequence you will get a SequenceList

<a id="benchmate.sequence.sequence.Sequence.to_fasta"></a>

#### to\_fasta

```python
def to_fasta(file_path: str) -> None
```

Write this sequence to a FASTA file.

<a id="benchmate.sequence.sequence.SequenceList"></a>

## SequenceList Objects

```python
class SequenceList(list)
```

A list of Sequence objects with utility methods. Class methods are inherited from list

<a id="benchmate.sequence.sequence.SequenceList.__init__"></a>

#### \_\_init\_\_

```python
def __init__(sequences, type="protein")
```

Initialize with a list of Sequence objects, all must be Sequence instances.

<a id="benchmate.sequence.sequence.SequenceList.ClustalOmega"></a>

#### ClustalOmega

```python
def ClustalOmega(*args)
```

Perform multiple sequence alignment using Clustal Omega via Biotite. args are passed to ClustalOmegaApp.

**Arguments**:

- `args`: list of clustal omega arguments

**Returns**:

returns a tuple of gapped_sequences, alignment_matrix and guide_tree

<a id="benchmate.sequence.sequence.SequenceList.from_kb"></a>

#### from\_kb

```python
@classmethod
def from_kb(cls, project, ids)
```

given a list of ids generate a sequence list

**Arguments**:

- `project`: project class instance
- `ids`: list of ids

**Returns**:

a sequence list

<a id="benchmate.sequence.sequence.SequenceList.from_fasta"></a>

#### from\_fasta

```python
@classmethod
def from_fasta(cls, file_path, seq_type)
```

Read one or many sequences from a FASTA file. Unlike Sequence.from_fasta, this always returns a SequenceList.

<a id="benchmate.sequence.sequence.SequenceList.to_fasta"></a>

#### to\_fasta

```python
def to_fasta(file_path: str) -> None
```

Write all sequences to a FASTA file.

<a id="benchmate.sequence.utils"></a>

# benchmate.sequence.utils

<a id="benchmate.sequence.utils.blast_search"></a>

#### blast\_search

```python
def blast_search(program,
                 database,
                 sequence,
                 expect_threshold=10.0,
                 hitlist_size=50)
```

perfrom blast search via ncbi api this is not local blast

**Arguments**:

- `program`: which program to use blastp, blastn, blastx, tblastn, tblastx, psiblast
- `database`: 
- `sequence`: Sequence instance
- `expect_threshold`: threshold
- `hitlist_size`: max number of hits

**Returns**:

a dataframe

<a id="benchmate.sequence.utils.parse_blast_search"></a>

#### parse\_blast\_search

```python
def parse_blast_search(blast_record)
```

take the stdout from blast and convert to a dataframe

**Arguments**:

- `blast_record`: out from blast api call

**Returns**:

a pandas dataframe

