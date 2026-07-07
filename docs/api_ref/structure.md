---
layout: default
title: Structure
parent: API Reference
nav_order: 6
---

<a id="benchmate.structure"></a>

# benchmate.structure

<a id="benchmate.structure.structure"></a>

# benchmate.structure.structure

<a id="benchmate.structure.structure.Structure"></a>

## Structure Objects

```python
class Structure()
```

<a id="benchmate.structure.structure.Structure.__init__"></a>

#### \_\_init\_\_

```python
def __init__(name, atoms, annotations: dict = None)
```

**Arguments**:

- `name`: name
- `atoms`: a biotite.AtomArray
- `annotations`: a dict with annotations

<a id="benchmate.structure.structure.Structure.align"></a>

#### align

```python
def align(other)
```

align 2 structures using mustang

**Arguments**:

- `other`: other structure
- `destination`: where to save the output

**Returns**:

aligned structure as a Structure class and other supplementary file paths

<a id="benchmate.structure.structure.Structure.find_pockets"></a>

#### find\_pockets

```python
def find_pockets(**kwargs)
```

Run fpocket on this structure and return detected pocket info.
Returns (pocket_files, pocket_coords)

<a id="benchmate.structure.structure.Structure.to_3di"></a>

#### to\_3di

```python
def to_3di(chain)
```

for a chain convert the structure to 3di

<a id="benchmate.structure.structure.Structure.sequence"></a>

#### sequence

```python
def sequence()
```

extract the aa sequence from the pdb, if there are gap there will be - if there are uknown aa there will be an X

<a id="benchmate.structure.structure.Structure.tm_score"></a>

#### tm\_score

```python
def tm_score(other)
```

run us-align to get the tm score between 2 structures

**Arguments**:

- `other`: other structure

**Returns**:

retun the tm score

<a id="benchmate.structure.structure.Structure.contacts"></a>

#### contacts

```python
def contacts(chain_id1, chain_id2, cutoff=5.0, level="atom", measure="any")
```

Get contacts between two chains in the structure.

**Arguments**:

- `chain_id1`: chain 1
- `chain_id2`: chain 2
- `cutoff`: distance cutoff to be called contacting default 5A
- `level`: if "atom" return the contacting atom, if residue return the resdiues

**Returns**:

a list of atoms, residues etc.

<a id="benchmate.structure.structure.Structure.__getitem__"></a>

#### \_\_getitem\_\_

```python
def __getitem__(key: Union[str, int, slice, Tuple[str, Union[int, str]]])
```

Support indexing:
  - structure['A'] -> returns chain atoms (Biotite AtomArray slice)
  - structure[0] -> returns first chain atoms (by order in self.chains)
  - structure['A', 100] -> returns list of atoms belonging to residue id 100 in chain A
  - structure[0:2] -> list of chain AtomArray slices for the first two chains

<a id="benchmate.structure.utils"></a>

# benchmate.structure.utils

<a id="benchmate.structure.utils.download"></a>

#### download

```python
def download(id, source="PDB", destination=None)
```

download a cif file (RSCB) or a pdb file (AFDB) for a given id

**Arguments**:

- `id`: id
- `source`: where to get it from PDB or AFDB
- `destination`: where to download ti

**Returns**:

a path, you can use this to download things it's also being used by Structure internally

<a id="benchmate.structure.utils.get_pocket_dimensions"></a>

#### get\_pocket\_dimensions

```python
def get_pocket_dimensions(pocket_path)
```

get the bounding box of a pocket

**Arguments**:

- `pocket_path`: pocket pdb from find_pockets

**Returns**:

x,y,z coords

<a id="benchmate.structure.utils.bounding_box"></a>

#### bounding\_box

```python
def bounding_box(self, amino_acids=None, use_alpha_carbon=False)
```

generate a bounding box around a given list of amino acid ids. This can be used to generate more molecules or

calculate properties of a pocket

**Arguments**:

- `use`: target or bound structure, this needs to be a Structure instance
- `amino_acids`: which amino acids to use
- `use_alpha_carbon`: whether to use the alpha carbon or the side chains to get the bounding box

**Returns**:

6 coordinates of the bounding box

