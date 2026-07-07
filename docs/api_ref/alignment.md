---
layout: default
title: Alignment
parent: API Reference
nav_order: 8
---

<a id="benchmate.alignment"></a>

# benchmate.alignment

<a id="benchmate.alignment.mmseqs"></a>

# benchmate.alignment.mmseqs

<a id="benchmate.alignment.mmseqs.MMSeqs"></a>

## MMSeqs Objects

```python
class MMSeqs()
```

Corrected MMseqs2 wrapper:
- Always creates query DB via `createdb`
- Supports single and paired alignment (`pairaln`)
- GPU with padded DB
- Flexible extra args

<a id="benchmate.alignment.mmseqs.MMSeqs.__init__"></a>

#### \_\_init\_\_

```python
def __init__(mmseqs_bin: str = "mmseqs")
```

initialize the class

**Arguments**:

- `mmseqs_bin`: the path to the binary if it's not in your $PATH

<a id="benchmate.alignment.mmseqs.MMSeqs.find_local_databases"></a>

#### find\_local\_databases

```python
def find_local_databases(folder)
```

This is hacky because I do not know a way to check if this is compatible with the program

**Arguments**:

- `folder`: folder to search for

**Returns**:

nothing, but updates self.local_databases list

<a id="benchmate.alignment.mmseqs.MMSeqs.create_database"></a>

#### create\_database

```python
def create_database(
        fasta_path: str,
        db_path: str,
        db_name: str,
        gpu_padded: bool = False,
        extra_args: Optional[Union[List[str], Dict[str, str]]] = None) -> str
```

Create a new database from a fasta file

**Arguments**:

- `fasta_path`: path to the fasta file
- `db_path`: path to the database
- `db_name`: name of the database
- `gpu_padded`: whether to pad it for gpu compatbility
- `extra_args`: other args to pass to the binary see mmseqs documentation

**Returns**:

the path of the binary

<a id="benchmate.alignment.mmseqs.MMSeqs.pad_db"></a>

#### pad\_db

```python
def pad_db(old_db, new_db, **kwargs)
```

create a padded db from an exising one

:param old_db: old db to pad
:param new_db: new db path
:return the path of the new db if all goes well


<a id="benchmate.alignment.mmseqs.MMSeqs.search"></a>

#### search

```python
def search(query: Union[benchmate.sequence.sequence.Sequence,
                        benchmate.sequence.sequence.SequenceList],
           target_db: str,
           output_a3m: str,
           output_tsv: str,
           use_gpu: bool = False,
           sensitivity: float = 5.7,
           max_seqs: int = 1000,
           evalue: float = 1e-3,
           extra_search_args: Optional[Union[List[str], Dict[str,
                                                             str]]] = None,
           extra_result2msa_args: Optional[Union[List[str], Dict[str,
                                                                 str]]] = None,
           tmp_dir: Optional[str] = None)
```

Perform a search on a query sequence, this is the full search pipeline not easy-search

**Arguments**:

- `query`: query fasta
- `target_db`: which database to search
- `output_a3m`: where to write the a3m file
- `output_tsv`: where to write the tsv file
- `use_gpu`: whether to use gpu, this does not check if there is a gpu available or the database is compatible
- `sensitivity`: sensitivity of the search default 5.7
- `max_seqs`: max number of sequences to return default 1000
- `evalue`: e value cutoff default: 1e-3
- `extra_search_args`: extra arguments to search
- `extra_result2msa_args`: extra arguments to results2msa
- `tmp_dir`: where to put the temp files, if none will use a tempfile

**Returns**:

paths to the generated files

<a id="benchmate.alignment.mmseqs.MMSeqs.easy_search"></a>

#### easy\_search

```python
def easy_search(query, target, extra_args)
```

run easy search on a query and target fasta this is quick fasta to fasta search

**Arguments**:

- `query`: query fasta
- `target`: target fasta
- `extra_args`: extra arguments

**Returns**:

a pd dataframe with the results, default columns are used unless specified with extra args

<a id="benchmate.alignment.mmseqs.MMSeqs.list_dbs"></a>

#### list\_dbs

```python
def list_dbs()
```

list available downloadable dbs

**Returns**:

a string that is the stdout

<a id="benchmate.alignment.mmseqs.MMSeqs.download_db"></a>

#### download\_db

```python
def download_db(dbname, location, create=False)
```

download a specific db that is listed with list_dbs

**Arguments**:

- `dbname`: name of the db
- `location`: where to download the db
- `create`: whether to create the folder

**Returns**:

None

<a id="benchmate.alignment.blast"></a>

# benchmate.alignment.blast

<a id="benchmate.alignment.blast.Blast"></a>

## Blast Objects

```python
class Blast()
```

<a id="benchmate.alignment.blast.Blast.__init__"></a>

#### \_\_init\_\_

```python
def __init__(path=None)
```

initiate a Blast class instance

**Arguments**:

- `path` (`str`): path of the executable if none will check $PATH
- `db` (`str`): path and name of the blast database if exists if not it can be created using create_db
- `dbtype` (`str`): type of the database n for nucleotide p for protein

<a id="benchmate.alignment.blast.Blast.find_local_databases"></a>

#### find\_local\_databases

```python
def find_local_databases(folder)
```

This is hacky because I do not know a way to check if this is compatible with the program

**Arguments**:

- `folder`: folder to search for

**Returns**:

nothing, but updates self.local_databases list

<a id="benchmate.alignment.blast.Blast.create_db"></a>

#### create\_db

```python
def create_db(fasta,
              output_path,
              dbname,
              dbtype="n",
              overwrite=True,
              arg_dict=None)
```

create a blast databse and stor in self.db

**Arguments**:

- `dbtype`: database type n for nucleotide and p for protein
- `fasta`: path of the fasta file only fasta is implemented
- `output_path`: output path for the database this is different from the databse name
- `dbname`: database name so self.db will be output_path/dbname
- `overwrite`: if there is already a self.db you can override this just edits the class instance value
dooes not touch the databse
- `arg_dict`: a dictionary of arguments, if left empty will use default values see blast documentation

**Returns**:

nothing just puts the new database path in self.db after database creation

<a id="benchmate.alignment.blast.Blast.search"></a>

#### search

```python
def search(seq,
           db,
           output_type="tabular",
           exec="blastn",
           arg_dict=None,
           cols=None)
```

Search an existing blast database with a sequence class instance

**Arguments**:

- `seq`: a benchmate.sequence.sequence.Sequence instance
- `db`: the path and name of the database
- `output_type`: tabular or json
- `exec`: what to use for serach depends on the type of sequence being searched
- `arg_dict`: additional arguments to blast
- `cols`: what columns to return if you are returning a table

**Returns**:

pd.DataFrame of dict

<a id="benchmate.alignment.folddisco"></a>

# benchmate.alignment.folddisco

<a id="benchmate.alignment.folddisco.FoldDisco"></a>

## FoldDisco Objects

```python
class FoldDisco()
```

Wrapper class for folddisco structure search

<a id="benchmate.alignment.folddisco.FoldDisco.__init__"></a>

#### \_\_init\_\_

```python
def __init__(folddisco_bin: str = "folddisco")
```

Initialize the wrapper.

**Arguments**:

- `folddisco_bin`: the path to the folddisco binary, if you are using conda this is just folddisco as
it will be in your $PATH

<a id="benchmate.alignment.folddisco.FoldDisco.find_local_databases"></a>

#### find\_local\_databases

```python
def find_local_databases(folder)
```

This is hacky because I do not know a way to check if this is compatible with the program

**Arguments**:

- `folder`: folder to search for

**Returns**:

nothing, but updates self.local_databases list

<a id="benchmate.alignment.folddisco.FoldDisco.create_index"></a>

#### create\_index

```python
def create_index(pdb_dir: str,
                 db_path: str,
                 db_name: str,
                 extra_args: Optional[Union[List[str], Dict[str, str]]] = None,
                 tmp_dir: Optional[str] = None) -> str
```

Index a folder of pbds to be used with folddisco.

**Arguments**:

- `pdb_dir`: the path to the pdb folder
- `db_path`: the path to the db folder, this is where the indices will be
- `extra_args`: the extra arguments to pass to the folddisco binary
- `tmp_dir`: the tmp directory to use

<a id="benchmate.alignment.folddisco.FoldDisco.search"></a>

#### search

```python
def search(structure,
           query_residues,
           target_db,
           extra_args=None) -> subprocess.CompletedProcess
```

search and exisiting folddisco database

**Arguments**:

- `structure`: a benchmate.structure.Structure object
- `query_residues`: a dict of chain:[redisudes], if you leave this blank the whole structure will be searched
- `target_db`: the database to search
- `kwargs`: additional kwargs passed to folddisco query

<a id="benchmate.alignment.utils"></a>

# benchmate.alignment.utils

<a id="benchmate.alignment.utils.find_root_name"></a>

#### find\_root\_name

```python
def find_root_name(folder, to_replace=[".", "_"])
```

This is used to find local databases however there is no check on what kind of db or file it is, we are just using file names

**Arguments**:

- `folder`: which folder to check
- `to_replace`: usually, foldseek, mmseqs, blast and folddisco add known suffixes to different files of a specific db, these are
removed so that we can identify uniqe dbs as one folder can contain an arbitrary number of files

**Returns**:

a list of potential dbs, not checked for specific compatibility, keep different kinds of dbs (blast, mmseqs, etc.) in different folders

<a id="benchmate.alignment.utils.SinglePassFastaIndex"></a>

## SinglePassFastaIndex Objects

```python
class SinglePassFastaIndex()
```

this is a tiny class to access MSA a3m files, these files look like fasta but they are not reall so tools
that deal with them have issues. This is not really a faster solution but a solution.

<a id="benchmate.alignment.utils.SinglePassFastaIndex.__init__"></a>

#### \_\_init\_\_

```python
def __init__(fasta_path, delim="_")
```

constructor, the goal is to create an index of the entries, sometimes you will get multiple entries with the same name
these will have other things next to the name, a combination of these create a unique entry

<a id="benchmate.alignment.foldseek"></a>

# benchmate.alignment.foldseek

<a id="benchmate.alignment.foldseek.FoldSeek"></a>

## FoldSeek Objects

```python
class FoldSeek()
```

A Python wrapper for FoldSeek with support for:
- Querying PDB structures (single or directory) against a database → A3M + TSV output
- Creating FoldSeek databases (standard or GPU-padded)
- GPU acceleration (if DB supports it)
- Flexible extra arguments

<a id="benchmate.alignment.foldseek.FoldSeek.__init__"></a>

#### \_\_init\_\_

```python
def __init__(foldseek_bin: str = "foldseek")
```

**Arguments**:

- `foldseek_bin`: Path to the FoldSeek executable (default: assumes in PATH)

<a id="benchmate.alignment.foldseek.FoldSeek.find_local_databases"></a>

#### find\_local\_databases

```python
def find_local_databases(folder)
```

This is hacky because I do not know a way to check if this is compatible with the program

**Arguments**:

- `folder`: folder to search for

**Returns**:

nothing, but updates self.local_databases list

<a id="benchmate.alignment.foldseek.FoldSeek.create_database"></a>

#### create\_database

```python
def create_database(pdb_dir: str,
                    db_path: str,
                    db_name: str,
                    gpu_padded: bool = False,
                    extra_args: Optional[Union[List[str], Dict[str,
                                                               str]]] = None,
                    tmp_dir: Optional[str] = None) -> str
```

Create a FoldSeek database from a directory of PDB/CIF files.

:param pdb_dir: path to PDB/CIF file
:param db_path: path to FoldSeek database
:param gpu_padded, If True create padded db
:param extra_args: extra arguments passed to FoldSeek
:param tmp_dir: Custom temporary directory
:return: path to the created FoldSeek database


<a id="benchmate.alignment.foldseek.FoldSeek.pad_db"></a>

#### pad\_db

```python
def pad_db(old_db, new_db, **kwargs)
```

create a padded db from an exising one

:param old_db: old db to pad
:param new_db: new db path
:return the path of the new db if all goes well


<a id="benchmate.alignment.foldseek.FoldSeek.search"></a>

#### search

```python
def search(structure: benchmate.structure.structure.Structure,
           target_db: str,
           output_a3m: str,
           output_tsv: str,
           use_gpu: bool = False,
           sensitivity: float = 7.5,
           max_accept: int = 100000,
           evalue: float = 1e-3,
           extra_search_args: Optional[Union[List[str], Dict[str,
                                                             str]]] = None,
           extra_result2msa_args: Optional[Union[List[str], Dict[str,
                                                                 str]]] = None,
           tmp_dir: Optional[str] = None)
```

**Arguments**:

- `structure`: a benchmate structure object
- `target_db`: FoldSeek database to search against
- `output_a3m`: Output A3M file path
- `output_tsv`: Output TSV file path
- `use_gpu`: Enable GPU (FoldSeek will error if DB not padded or no GPU)
- `sensitivity`: Search sensitivity (higher = slower, more sensitive)
- `max_accept`: Maximum number of alignments to accept
- `evalue`: E-value threshold
- `extra_search_args`: Extra args for `search`
- `extra_result2msa_args`: Extra args for `result2msa`
- `tmp_dir`: Custom temporary directory
Note:
    GPU errors are caught and reported (FoldSeek handles compatibility).

<a id="benchmate.alignment.foldseek.FoldSeek.easy_search"></a>

#### easy\_search

```python
def easy_search(query,
                target,
                extra_args: Optional[Union[List[str], Dict[str, str]]] = None)
```

run easy search with a pdb file and a fasta of 3dis

**Arguments**:

- `query`: pdb file
- `target`: directory of pbds
- `extra_args`: Extra args for `easy_search`

**Returns**:

a pandas dataframe of the results

<a id="benchmate.alignment.foldseek.FoldSeek.list_dbs"></a>

#### list\_dbs

```python
def list_dbs()
```

List downloadable dbs

<a id="benchmate.alignment.foldseek.FoldSeek.download_db"></a>

#### download\_db

```python
def download_db(dbname, location, create=False)
```

downlooad one of the items from listdbs

**Arguments**:

- `dbname`: name of the db
- `location`: where to download the db
- `create`: whether to create that directory

**Returns**:

return the path of the downloaded db

