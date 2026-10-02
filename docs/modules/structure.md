---
layout: default
title: Structure
parent: Modules
nav_order: 6
---

# Structure Module

The **Structure** module represents 3D protein structures using [Biotite](https://www.biotite-python.org/) under the hood. It provides lightweight interfaces for structure loading/downloading, sequence and 3Di extraction, structural alignment, contact analysis, pocket detection, and PDB export.

---

## Instantiation & File I/O

A `Structure` instance can be created directly from Biotite `AtomArray` objects or imported from PDB/CIF files (or downloaded online by PDB ID).

```python
from benchmate.structure import Structure

# 1. Load from a local PDB or CIF file
structure = Structure.from_file(name="1A2B", file="/path/to/1a2b.pdb")

# 2. Download directly by PDB ID from RCSB PDB
structure = Structure.from_file(name="1A2B", id="1A2B", source="pdb", destination="/path/to/download/")
```

---

## User-Facing Methods

- `from_file(name, file=None, source=None, destination=None, id=None)`: Class method to instantiate a structure from a PDB/CIF file or download it from RCSB PDB.
- `align(other)`: Align structural coordinates against another `Structure` using MUSTANG. Returns an aligned `Structure` object.
- `tm_score(other)`: Calculate structural similarity TM-score against another `Structure` using US-align (returns float score between 0 and 1).
- `find_pockets(**kwargs)`: Detect binding pockets using `fpocket`. Returns a list of `Structure` objects representing each detected pocket.
- `to_3di(chain)`: Convert a specific chain to 3Di structural alphabet sequence (`Sequence` object with `seq_type="3di"`).
- `sequence()`: Extract amino acid sequence for all chains. Returns a `Sequence` (if single protein chain) or a `SequenceList` (if multi-chain).
- `contacts(chain_id1, chain_id2, cutoff=5.0, level="atom", measure="any")`: Calculate pairwise contact points between two chains at specified distance threshold in Angstroms (`level="atom"` or `"residue"`).
- `write(fpath)`: Save structure coordinates to a PDB file.

---

## Usage Examples

```python
from benchmate.structure import Structure

# Load structures
st1 = Structure.from_file("struct1", file="protein1.pdb")
st2 = Structure.from_file("struct2", file="protein2.pdb")

# 1. Structural Alignment & TM-Score
aligned_st = st1.align(st2)
tm_val = st1.tm_score(st2)
print(f"TM-score: {tm_val:.4f}")

# 2. Pocket Detection
pockets = st1.find_pockets()
print(f"Detected {len(pockets)} binding pockets")

# 3. Inter-Chain Contact Analysis
contacts = st1.contacts(chain_id1="A", chain_id2="B", cutoff=5.0, level="residue")

# 4. Extract Sequence & 3Di Structural Alphabet
amino_acid_seq = st1.sequence()
seq_3di = st1.to_3di(chain="A")

# 5. Indexing Chains & Residues
chain_a_atoms = st1["A"]            # AtomArray slice for chain A
res_100_atoms = st1["A", 100]      # Atoms belonging to residue ID 100 in chain A

# 6. Save modified structure
st1.write("output.pdb")
```
