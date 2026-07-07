---
layout: default
title: Molecule
parent: API Reference
nav_order: 7
---

<a id="benchmate.molecule"></a>

# benchmate.molecule

<a id="benchmate.molecule.molecule"></a>

# benchmate.molecule.molecule

<a id="benchmate.molecule.molecule.MoleculeInfo"></a>

## MoleculeInfo Objects

```python
@dataclass(slots=True)
class MoleculeInfo()
```

Molecule info to store all the information related to a small molecule

<a id="benchmate.molecule.molecule.MoleculeInfo.get_ecfp4_fp"></a>

#### get\_ecfp4\_fp

```python
def get_ecfp4_fp()
```

get ecfp4 fingerprint for a given fingerprint radius and dimensions

**Returns**:

the fingerpring attribute filled in returns nothing

<a id="benchmate.molecule.molecule.MoleculeInfo.get_fcfp4_fp"></a>

#### get\_fcfp4\_fp

```python
def get_fcfp4_fp()
```

same as above but with fcfp


<a id="benchmate.molecule.molecule.MoleculeInfo.get_maccs_fp"></a>

#### get\_maccs\_fp

```python
def get_maccs_fp()
```

same as above but with open source maccs


<a id="benchmate.molecule.molecule.Molecule"></a>

## Molecule Objects

```python
class Molecule()
```

Molecule class to represent chemical structures using SMILES or InChI. this will include methods for different property
calculations and structure comparisons using usearch molecules.

<a id="benchmate.molecule.molecule.Molecule.__init__"></a>

#### \_\_init\_\_

```python
def __init__(name, smiles, fingerprint_dim=2048, radius=2)
```

**Arguments**:

- `name`: name of the molecule
- `smiles`: the smiles of the molecule
- `fingerprint_dim`: the dimension of the fingerprint to generate all 3 fingerprints will use the same dim
- `radius`: the radius (in terms of graph distance, not angstroms) to use for fingerprinting

<a id="benchmate.molecule.molecule.Molecule.similarity"></a>

#### similarity

```python
def similarity(other, fingerprint)
```

get the similarity betweek two molecule instances

**Arguments**:

- `other`: other molecule instance
- `fingerprint`: what kind of fingerprint to use

**Returns**:

returns the tanimoto similarity between to molecules

<a id="benchmate.molecule.molecule.Molecule.generate_conformers"></a>

#### generate\_conformers

```python
def generate_conformers(n, prune_thres=0.5, optimize_geom=True)
```

generate conformers

**Arguments**:

- `n`: number of conformers to try to generate, based on pruning they number can be smalled
- `prune_thres`: remove any conformer that has this much rmsd or less. So lower values will give more conformers
- `optimize_geom`: whether to optimize the geometry, this will also get rid of some comformers

**Returns**:

returns a hydrogenated mol with all the conformers that you can get with mol.GetConformers(<conformer_id>) and a list of ids

<a id="benchmate.molecule.molecule.Molecule.inchikey"></a>

#### inchikey

```python
def inchikey() -> str
```

generate the inchi key for the molecule

**Returns**:

inchikey

<a id="benchmate.molecule.molecule.Molecule.__eq__"></a>

#### \_\_eq\_\_

```python
def __eq__(other)
```

using inchi key because the molecules might not be in canonical smiles, it's not perfect but close

<a id="benchmate.molecule.utils"></a>

# benchmate.molecule.utils

