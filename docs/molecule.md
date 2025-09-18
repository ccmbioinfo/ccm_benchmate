---
layout: default
title: Molecule Module
nav_order: 10
---

# Molecule Module

This is a small module that provides some tools and methods to deal with small molecules. It includes functions
to generate RDKit molecule object instances from SMILES strings, compute molecular fingerprints, and calculate various molecular properties.

Additionally, it provides searching and filtering capabilities based on molecular properties and substructure matching using the 
usearch-molecule packages. 

## Usage

```python
from benchmate.molecule.molecule import Molecule

smiles="C1=CC=CC=C1"  # Benzene
molecule = Molecule(smiles)

# all the information is stored in the info attribute
print(molecule.info.ecfp4) #or fcfp4 or maccs
print(molecule.info.properties) #all propertires that can be calculated with rdkit are available and stored in the info attribute

# you can also search for similar molecules in a library
molecule.search(library, n=10, metric="tanimoto", fingerprint="ecfp4") #search for the 10 most similar molecules in the library based on ecfp4 fingerprints and tanimoto similarity
```

The library in the search method is an indexed usearch-molecule library. You can create one from a list of SMILES please see
the git repository [here](https://github.com/ashvardanian/usearch-molecules) for more information.

We have already created indexed libraries for the following datasets:

- PubChem (~100 million molecules)
- Enamine REAL (~7 billion molecules)
- GB13M (~1.3 billion molecules)


