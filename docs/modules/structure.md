---
layout: default
title: Structure
parent: Modules
nav_order: 6
---

# Structure Module

A module for working with protein structures, providing functionality for structure analysis, prediction, alignment and embedding generation. 
Just like the sequence module this is a very lightweight module that only is meant to represent a protein structure and have a few
very basic calculations. Again similar to the sequence module, adding additional functionality that depends on some of the later 
nerual network modules will not be possible and will be ported the container runner class. As long as the output of whatever
program is running in the container is a PDB file, it will be possible to load it into this class.

Under the hood the main structure is represented using the [biotite](https://www.biotite-python.org/latest/index.html) package, which itself has 
a lot of other functionalities that can be immediately used.

One additional limitation of representing structures is that there can be multiple chains in a single PDB file. These chains are
not necessarily proteins. The structure can come from NMR, X-ray, EM, or other sources rendering a lot of the information in the header
very difficult to interpret and parse; this is assuming that the header is not weirdly formatted in the first place. 

So we are keeping this module basic and only supporting loading/downloading structures, aligning two structures and 
calculating contact points between chains. If you have other ideas that can be generalized to any structure, please let us know.

### Basic Usage

```python
from benchmate.structure import Structure

# Create from PDB file
structure = Structure(pdb="/path/to/structure.pdb")
# or download the pdb
structure = Structure(pdb_id="1A2B", source="pdb", destination="/path/to/download/")

```

### Structure Analysis (very limited)

```python
# find pockets in structure using fpocket
stucture.find_pockets()

# aling 2 structures
structure.align(other_structure)

# find contacts between chains only applies to pdb files with 2 chains (does not have to be proteins)
structure.find_contacts(chain_id1="A", chain_id2="B")

# calulcate tm score using US-align
structure.tm_score(other_structure)

#get the 3di sequence
structure.to_3di(chain="A")

#get the protein sequence
from benchmate.sequence import Sequence
structure.sequence()

```

You can also perform fancy indexing to get chains and atoms:

```python
# get the first 100 atoms of chain A
structure["A"][0:100]
```
If your structure has multiple chains you can calculate contacts between them

```python
structure.contacts(chain_id1="A", chain_id2="B", cutoff=5.0)
```

Finally, if you made changes to your structure you can write it to file. 

```python
structure.write("path") #only pdb file supported currently no cif files. 
```
