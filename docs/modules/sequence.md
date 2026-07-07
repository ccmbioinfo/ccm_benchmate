---
layout: default
title: Sequence
parent: Modules
nav_order: 5
---

# Sequence Module

This module represents biological sequences, they can be protein, rna or dna they depending on the kind of 
sequence there are differnet functionalities available

## Sequence

The main class for working with individual sequences, providing methods for sequence analysis, mutation, 
alignment and searching.

### Basic Usage

#### Proteins

```python
from benchmate.sequence import Sequence

# Create a sequence object
seq = Sequence(name="my_sequence", sequence="MKLLPRGPAAAAAAVLLLLSLLLLPQVQA", 
               seq_type="protein", features={"some":"features"})

# perfom a blast search via ncbi api, local blast coming soon
seq.blast("blasp", "NP")

seq.subseq(start=10, end=100)

# Introduce mutations
seq.mutate(
    position=3,   # 0-based position 
    to="A",       # Amino acid to mutate to
)

seq.insert(0, "MTMTMT")

seq.delete(10, 5) #delete 5 aa starting from pos 10

#search (exact search only) 
seq.find("MKLL")

#kmer counts (works on all types)
seq.kmer_counts(5, normalize=True)

seq.aa_composition()

seq.molecular_weight()

seq.isoelectric_point()

seq.hydropathy_profile(window=9) #rolling window

seq.to_fasta("my.fa")

#or load from fasta
Sequence.from_fasta("my.fa")


```
#### For DNA/RNA

```python
seq=Sequence(name="my_other_seq", sequence="ATATATAGACACAGTAGACAGTA", type="RNA")

#calculate secondary structure (for rna)
seq.vienna(temperature=37)

seq.reverse_complement()
seq.translate(to_stop=False) #dont stop once you reach a stop codon

seq.gc_content(window=None) # or a rolling window
seq.gc_skew(windog=None) # same as above
```


### SequenceList

You can also have a list of sequence, if you load from a multifasta you will get one automatically, the only
catch is you cannot mix and match sequence types and you cannot have a nested list of sequences. 

In addition to all the list methods and all the sequence methods you can also perform MSA via ClustalOmega

```python
from benchmate.sequence import SequenceList

seq=Sequence.from_fasta("my.fa")

seq.ClustalOmega()
```

Similarly you can write a `SequenceList` to a multi fasta file using `.to_fasta` method. 