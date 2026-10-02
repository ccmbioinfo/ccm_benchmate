---
layout: default
title: Molecule
parent: Modules
nav_order: 7 
---

# Molecule Module

The **Molecule** module provides lightweight data structures for representing small chemical molecules via SMILES or InChI strings. Built on top of **RDKit**, it automatically computes molecular descriptors, generates fingerprints (ECFP4, FCFP4, MACCS), calculates Tanimoto similarities, and samples 3D conformers.

---

## User-Facing Methods

- `Molecule(name, smiles, fingerprint_dim=2048, radius=2)`: Instantiates a small molecule, generating RDKit Mol objects, 2048-bit ECFP4/FCFP4/MACCS fingerprint bitstrings, InChIKey, and standard molecular descriptors.
- `similarity(other, fingerprint)`: Compute the Tanimoto similarity score (float between 0 and 1) between two `Molecule` instances using `"ecfp4"`, `"fcfp4"`, or `"maccs"`.
- `generate_conformers(n, prune_thres=0.5, optimize_geom=True)`: Generate 3D spatial conformers using ETKDGv3 and MMFF geometry optimization. Returns a tuple of `(self, conformer_ids)`.
- `inchikey()`: Calculate and return the IUPAC InChIKey for the chemical structure.

---

## Basic Usage

```python
from benchmate.molecule import Molecule

# Create molecule instances with name and SMILES string
mol1 = Molecule(name="benzene", smiles="C1=CC=CC=C1")
mol2 = Molecule(name="toluene", smiles="Cc1ccccc1")

# Access calculated fingerprints and RDKit molecular descriptors
print(mol1.info.ecfp4)      # Bitstring representation of ECFP4
print(mol1.info.properties) # Dictionary of RDKit descriptors (MW, LogP, TPSA, etc.)
print(mol1.info.inchi)      # InChIKey

# Compute Tanimoto similarity between molecules
sim_score = mol1.similarity(mol2, fingerprint="ecfp4")
print(f"ECFP4 Tanimoto Similarity: {sim_score:.4f}")

# Generate 3D conformers
mol1, conformer_ids = mol1.generate_conformers(n=50, prune_thres=0.5, optimize_geom=True)
print(f"Generated {len(conformer_ids)} conformers")
```
