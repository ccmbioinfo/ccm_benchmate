---
layout: default
title: Molecule
parent: Modules
nav_order: 7 
---

# Molecule Module

This is a small module that provides some tools and methods to deal with small molecules. It includes functions
to generate RDKit molecule object instances from SMILES strings, compute molecular fingerprints, and calculate various molecular properties.

Additionally, it provides searching and filtering capabilities based on molecular properties and substructure matching using the 
usearch-molecule packages. 

## Usage

```python
from benchmate.molecule import Molecule

smiles="C1=CC=CC=C1"  # Benzene
molecule = Molecule(smiles)

# all the information is stored in the info attribute
print(molecule.info.ecfp4) #or fcfp4 or maccs
print(molecule.info.properties) #all propertires that can be calculated with rdkit are available and stored in the info attribute
```

You can check how similar it is to another molecule or generate conformers. 


```python
molecule.generate_conformers(n=50, optimize_geom=True)
molecule.inchikey()
```
