---
layout: default
title: Project Meta Class
parent: API Reference
nav_order: 11
---

<a id="benchmate.project"></a>

# benchmate.project

<a id="benchmate.project.classes.genome"></a>

# benchmate.project.classes.genome

<a id="benchmate.project.classes.genome.Genomes"></a>

## Genomes Objects

```python
class Genomes(BaseGenome)
```

project integration of the genome class, this is so that instead of sqlite we are using the postgres server of the project

<a id="benchmate.project.classes.genome.Genomes.__init__"></a>

#### \_\_init\_\_

```python
def __init__(config, project)
```

create a genome instance using the project database and config

**Arguments**:

- `config`: genome section of config.yaml
- `project`: project class instance

<a id="benchmate.project.classes"></a>

# benchmate.project.classes

<a id="benchmate.project.classes.variant"></a>

# benchmate.project.classes.variant

<a id="benchmate.project.classes.variant.SequenceVariant"></a>

## SequenceVariant Objects

```python
class SequenceVariant(BaseSequenceVariant)
```

subclass of sequence variant with db methods

<a id="benchmate.project.classes.variant.SequenceVariant.to_kb"></a>

#### to\_kb

```python
def to_kb(project)
```

send a sequence variant to the database

<a id="benchmate.project.classes.variant.SequenceVariant.from_kb"></a>

#### from\_kb

```python
@classmethod
def from_kb(cls, project, id)
```

get the sequence variant from the database

**Arguments**:

- `project`: project class instance
- `id`: id of the sequence variant

**Returns**:

the sequence variant

<a id="benchmate.project.classes.variant.StructuralVariant"></a>

## StructuralVariant Objects

```python
class StructuralVariant(BaseStructuralVariant)
```

subclass of structural variant with db methods

<a id="benchmate.project.classes.variant.StructuralVariant.to_kb"></a>

#### to\_kb

```python
def to_kb(project)
```

send a structural variant to the database

**Arguments**:

- `project`: project class instance

**Returns**:

id of the structural variant

<a id="benchmate.project.classes.variant.StructuralVariant.from_kb"></a>

#### from\_kb

```python
@classmethod
def from_kb(cls, project, id)
```

get the structural variant from the database

**Arguments**:

- `project`: project class instance
- `id`: id of the structural variant

**Returns**:

structural variant

<a id="benchmate.project.classes.variant.TandemRepeatVariant"></a>

## TandemRepeatVariant Objects

```python
class TandemRepeatVariant(BaseTandemRepeatVariant)
```

tandem repeat variant with db methods

<a id="benchmate.project.classes.variant.TandemRepeatVariant.to_kb"></a>

#### to\_kb

```python
def to_kb(project)
```

send a tandem repeat variant to the database

**Arguments**:

- `project`: project class instance

**Returns**:

id of the tandem repeat variant

<a id="benchmate.project.classes.variant.TandemRepeatVariant.from_kb"></a>

#### from\_kb

```python
@classmethod
def from_kb(cls, project, id)
```

send a tandem repeat variant from the database

**Arguments**:

- `project`: project class instance
- `id`: id of the tandem repeat variant

**Returns**:

tandem repeat variant

<a id="benchmate.project.classes.api"></a>

# benchmate.project.classes.api

<a id="benchmate.project.classes.api.ApiCall"></a>

## ApiCall Objects

```python
class ApiCall(BaseApiCall)
```

A subclass of api call with methods to send and recieve api calls from the project database

<a id="benchmate.project.classes.api.ApiCall.to_kb"></a>

#### to\_kb

```python
def to_kb(project)
```

send an api call to the project database, so can get them later

**Arguments**:

- `project`: project object

**Returns**:

the id of the api call

<a id="benchmate.project.classes.api.ApiCall.from_kb"></a>

#### from\_kb

```python
@classmethod
def from_kb(cls, project, id)
```

given an api call id, return an api call object for that api call id

**Arguments**:

- `project`: project object
- `id`: api call id

**Returns**:

an api call object for that api call id

<a id="benchmate.project.classes.api.Apis"></a>

## Apis Objects

```python
class Apis()
```

a thin wrapper around the api call class instances so they can be run as project.apis.ncbi or something

<a id="benchmate.project.classes.literature"></a>

# benchmate.project.classes.literature

<a id="benchmate.project.classes.alignment"></a>

# benchmate.project.classes.alignment

<a id="benchmate.project.classes.alignment.Alignment"></a>

## Alignment Objects

```python
class Alignment()
```

This class simply creates alignment instances given a config so the user can run project.alignment.mmseqs, this is
a thin integration layer with the alignment module, the aligment module can still be used standalone and independently of the project
if desired

<a id="benchmate.project.classes.alignment.Alignment.__init__"></a>

#### \_\_init\_\_

```python
def __init__(config)
```

initialize the alignment class, this is a collection of alignment class instances that are specific to a project

**Arguments**:

- `config`: alignment section of the benchmate config

<a id="benchmate.project.classes.molecule"></a>

# benchmate.project.classes.molecule

<a id="benchmate.project.classes.molecule.Molecule"></a>

## Molecule Objects

```python
class Molecule(BaseMolecule)
```

Molecule subclass with to and from project database

<a id="benchmate.project.classes.molecule.Molecule.__init__"></a>

#### \_\_init\_\_

```python
def __init__(config, name, smiles)
```

config and basic info of the molecule, the see project for usage, the config is autopopulated when a prject is initialized

**Arguments**:

- `config`: molecule section of config.yaml
- `name`: name of the molecule
- `smiles`: smiles of the molecule

<a id="benchmate.project.classes.molecule.Molecule.from_kb"></a>

#### from\_kb

```python
@classmethod
def from_kb(cls, project, id)
```

get a molecule instance from the database

**Arguments**:

- `project`: project class instance
- `id`: id of the molecule instance

**Returns**:

a molecule instance

<a id="benchmate.project.classes.molecule.Molecule.to_kb"></a>

#### to\_kb

```python
def to_kb(project)
```

send a molecule instance to project database

**Arguments**:

- `project`: project class instance

**Returns**:

id of the molecule instance

<a id="benchmate.project.classes.sequence"></a>

# benchmate.project.classes.sequence

<a id="benchmate.project.classes.sequence.Sequence"></a>

## Sequence Objects

```python
class Sequence(BaseSequence)
```

a thin wrapper around the Sequence class so it is compatible with a project database

<a id="benchmate.project.classes.sequence.Sequence.__init__"></a>

#### \_\_init\_\_

```python
def __init__(config, name, sequence, seq_type, annotations)
```

**Arguments**:

- `config`: project database config
- `name`: name of the sequence
- `sequence`: sequence
- `seq_type`: type of sequence
- `annotations`: sequence's annotations

<a id="benchmate.project.classes.sequence.Sequence.from_fasta"></a>

#### from\_fasta

```python
@classmethod
def from_fasta(cls, config, file)
```

create a sequence from a fasta file

**Arguments**:

- `config`: sequence section of the config file
- `file`: fasta file

**Returns**:

a sequence instance

<a id="benchmate.project.classes.sequence.Sequence.from_kb"></a>

#### from\_kb

```python
@classmethod
def from_kb(cls, project, id)
```

create a sequence from a project database

**Arguments**:

- `project`: project class instance
- `id`: id of the sequence

**Returns**:

a sequence instance

<a id="benchmate.project.classes.sequence.Sequence.to_kb"></a>

#### to\_kb

```python
def to_kb(project)
```

send a sequence to a project database and append it to the appropriate fasta file

**Arguments**:

- `project`: project class instance, this will also contain the fasta paths, see main config.yaml file

**Returns**:

the id of the sequence

<a id="benchmate.project.classes.structure"></a>

# benchmate.project.classes.structure

<a id="benchmate.project.classes.structure.Structure"></a>

## Structure Objects

```python
class Structure(BaseStructure)
```

a subclass to make structures compatible with project instances

<a id="benchmate.project.classes.structure.Structure.__init__"></a>

#### \_\_init\_\_

```python
def __init__(config, name, atoms, annotations)
```

**Arguments**:

- `config`: structure section of the config file
- `name`: name of the structure
- `atoms`: biotite atom array
- `annotations`: associated annotations

<a id="benchmate.project.classes.structure.Structure.to_kb"></a>

#### to\_kb

```python
def to_kb(project)
```

send a structure instance to project database

**Arguments**:

- `project`: project class instance

**Returns**:

structure id

<a id="benchmate.project.classes.structure.Structure.from_kb"></a>

#### from\_kb

```python
@classmethod
def from_kb(cls, project, id)
```

create a structure instance from a kb id

**Arguments**:

- `project`: project class instance
- `id`: id of the structure

**Returns**:

structure instance

<a id="benchmate.project.classes.structure.Structure.structure_from_file"></a>

#### structure\_from\_file

```python
@classmethod
def structure_from_file(cls, config, name, file, source, destination, id)
```

create a structure from a file same as structure.from file different name to avoid overwriting

**Arguments**:

- `config`: structure section of the config file
- `name`: name of the structure
- `file`: pdb or cif file
- `source`: source (if no file is there will be downloaded from afdb or pdb)
- `destination`: where to download it
- `id`: the (for downloading)

**Returns**:

a structure instance

<a id="benchmate.project.search"></a>

# benchmate.project.search

<a id="benchmate.project.search.StructureSearch"></a>

## StructureSearch Objects

```python
class StructureSearch(BaseSearch)
```

Search for structures either from their annotations or using another structure

<a id="benchmate.project.search.SequenceSearch"></a>

## SequenceSearch Objects

```python
class SequenceSearch(BaseSearch)
```

<a id="benchmate.project.search.SequenceSearch.sequence"></a>

#### sequence

```python
def sequence(query)
```

search for sequences using another sequence

**Arguments**:

- `project`: project instance

**Returns**:

a dataframe of hits, the hit column gives you the ids of hits, other columns come from mmseqs

<a id="benchmate.project.search.VariantSearch"></a>

## VariantSearch Objects

```python
class VariantSearch(BaseSearch)
```

<a id="benchmate.project.search.VariantSearch.variant"></a>

#### variant

```python
def variant(query)
```

search variants in the knowledge base

**Arguments**:

- `query`: what to search for if this is a variant or genomics range then the genomic coords are used
if this is a list or str, we will be looking for annotation values, if it's a dict we will be looking for key value pairs
- `type`: type of variant to search for
- `kwargs`: other kwargs, that are specific to different variant types

**Returns**:

ids, types and coords, ref alt of variants that are found

<a id="benchmate.project.search.VariantSearch.range"></a>

#### range

```python
def range(query, types=None)
```

find variants that fall into a range, this assumes that the genomem you are using in your ranges are the same

as the variant annotations, there are no checks and not sure if there can ever be w/o significant overhead

**Arguments**:

- `query`: a genomicrange instance
- `type`: type of variant to search for

**Returns**:

basic information and their ids for matches

<a id="benchmate.project.search.ApiCallSearch"></a>

## ApiCallSearch Objects

```python
class ApiCallSearch(BaseSearch)
```

<a id="benchmate.project.search.ApiCallSearch.calls"></a>

#### calls

```python
def calls(call_class, class_method, params=None)
```

search for api calls based on the kind of api call and method used

**Arguments**:

- `call_class`: class of the call
- `class_method`: which method was used to call
- `params`: parameters for the api call, this allows you to search for specific calls

**Returns**:

ids, and basic info about the calls

<a id="benchmate.project.utils"></a>

# benchmate.project.utils

<a id="benchmate.project.utils.BaseSearch"></a>

## BaseSearch Objects

```python
class BaseSearch()
```

<a id="benchmate.project.utils.BaseSearch.json_search"></a>

#### json\_search

```python
def json_search(statement, table, column_name, filters)
```

**Arguments**:

- `statement`: This is a select statement, it can be as simple as a full table or a single column
- `column_name`: which column is the jsonb column
- `filters`: filters  str | dict | list[str | dict]

**Returns**:

filters added to the query this is not the result it's just a sqlalchemy query

<a id="benchmate.project.utils.BaseSearch.keyword_search"></a>

#### keyword\_search

```python
def keyword_search(statement,
                   positive_keywords,
                   negative_keywords,
                   table,
                   column,
                   normalization=32)
```

perform keyword search using postgres tsvector, this only applies to columns that has tsvector built in with indexes

**Arguments**:

- `statement`: This is a select statement, it can be as simple as a full table or a single column
- `positive_keywords`: things to look for
- `negative_keywords`: things to avoid
- `table`: which table to use
- `column`: which column from that table to use
- `normalization`: what kind of normalization to o use see details here: https://www.postgresql.org/docs/current/textsearch-controls.html#TEXTSEARCH-RANKING

**Returns**:

another statement added where tsvector filters are added.

<a id="benchmate.project.utils.BaseSearch.semantic_search"></a>

#### semantic\_search

```python
def semantic_search(statement,
                    query,
                    table,
                    column,
                    metric="cosine",
                    top_n=500)
```

perform semantic search using a pgvector column, the

**Arguments**:

- `statement`: base statementn from the class
- `query`: a list of embeddings, this is not what you are looking for but the embeddings of the thing you are looking for
- `table`: which table to search
- `column`: which column to search
- `top_n`: top n results to return, defaults to 500

**Returns**:

selection logic added to the base statement.

<a id="benchmate.project.project"></a>

# benchmate.project.project

<a id="benchmate.project.project.Project"></a>

## Project Objects

```python
class Project()
```

this is the metaclass for the whole thing, it will collect all the modules and will be main point for interacting with the knowledgebase

<a id="benchmate.project.project.Project.__init__"></a>

#### \_\_init\_\_

```python
def __init__(config_path)
```

This is the metaclass for the whole thing, it will collect all the modules and will be main point for interacting with

the knowledgebase, it will overwrite some of the methods with the parameters that are defnined in the config file

**Arguments**:

- `config_path`: path for the config file, see config.yaml for an example, it is not as flexible as the structure imples
especially for the inference part.

<a id="benchmate.project.project.Project.list_items"></a>

#### list\_items

```python
def list_items(type)
```

return a simple informative dataframe of all the items in the databse, if you have a lot of things (10s of thousands)

may take a few minutes

**Arguments**:

- `type`: what kind of thing to return

**Returns**:

a pandas dataframe of ids and basic info so you can get the actual class instance if you want

<a id="benchmate.project.project.Project.get_item"></a>

#### get\_item

```python
def get_item(type, id)
```

for a given id and type of thing get the thing

**Arguments**:

- `type`: what kind (the modality, sequence, structure, molecule paper etc.)
- `id`: the id of the thing

**Returns**:

the thing

