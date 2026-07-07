---
layout: default
title: Alignment
parent: Modules
nav_order: 8
---

# Alignment module

This module provides a quick and easy interface to run local Blast, mmseqs and foldseek queries. There is a python class
for each of the modules and a metaclass to access that is currently under construction. 

## Blast

This is the same program that runs when you run blast searches online, it is available as a standalone program that you can download
and generate your own sequence databases. This is useful if you are trying constrain your sequence search or you have a unique
dataset that is not covered by the current databases. There are 5 search programs and one for creating a database

+ blastn (search nucleotides)
+ blastp (search proteins)
+ blastx (search nucleotides agains a protein database)
+ tblastn (align "translated sequences")
+ tblastx (align translated nucleotide query against a translated nucleotide database)

### Creating a local database

Before you can search you need to create a blast database, for this you can use the createdb method

```python
from benchmate.alignment.blast import Blast
blast=Blast()

blast.create_db(<path to fasta>, <db_path>, <db_name>, <db_type>)
```

This will create a blast databsae of type `n` for nucleotide and `p` for protein under `db_path` and the files
will have the name `db_name.*`. After this you can query your database. 

```python
from benchmate.sequence.sequence import Sequence

myseq=Sequence(name="name", sequence="TAGATAGATTATA", seq_type="rna")

blast.search(myseq, mydb, exec="blastn", output_type="tabular")
```

If you want you can specify which column you want to return. If left blank the default columns are `"qaccver", "saccver", 
"pident", "length", "mismatch", "gapopen", "qstart", "qend", "sstart", "send", "evalue", "bitscore"`. You also have the option
to return a json output which will then get parsed into a python dict. The json output will include alignment as well as all the
usual metrics. 

## MMSEQS2

MMSeqs is a fast sequence searching algorithm that can return MSAs and other kinds of alignments extremely fast. It is a
multiple to multiple sequence aligment program and if you use a padded db (see below) you can use a gpu to further accelerate
the process. 

### List and download db

Creators of mmseqs2 have already created a decent collection of databases that you can download easily. 


```python
from benchmate.alignment.mmseqs import MMSeqs

mmseqs=MMSeqs()
mmseqs.list_dbs()
```

Once you pick one you like you can dowload it

```python
mmseqs.download_db("dbname", "location", create=False)
```

The database will be downloaded to location, if you set create to True and the folder does not exist it will be 
created. The name of the dabase will be the same as the database you are downloading. 

After the database is downloaded you can craete a padded database if you want to use GPU accelerated search

```python
mmseqs.pad_db("old_db", "new_db")
```

After that you are ready for searching. Make sure that your sequence `seq_type` matches the type of database you are searching.
```python
from benchmate.sequence.sequence import Sequence

myseq=Sequence(name="name", sequence="TAGATAGATTATA", seq_type="rna")

mmseqs.search(query=myseq, target_db=<database/path/name>, <output_tsv>, <output_a3m>)
```

This will generate 2 files the output tsv will return some alignment metrics and what they have aligned to
the output_a3m will generate the MSA alignment file. Keep in mind that you need to name these paths.

### Creating a local database

If you have a collection of sequences that you want to create a database from you can do that as well. All you need is a
fasta file with unique sequences in it. The program will not check if this is the case and you might run into issues if you have
exact duplicates. 

```python
mmseqs.create_database(<fasta_path>, <db_path>, gpu_padded=False)
```

If you select gpu_padded, the program will create a padded database to be used with gpu searches. While you can use a padded
db without a gpu non padded dbs are a slightly more sensitive. The padding is necessary to make everything the same size so we 
can take advantage of parallelization that is provided by the gpu. 


## Foldseek

Foldseek is very similar to mmseqs. It converts your structures to a sequence and runs a similar sequence alignment algorithm.
The commands are also very similar to mmseqs. The main difference is you will need to provide a structure instance instead of 
a sequence. 

### List and download db

Creators of foldseek have already created a decent collection of databases that you can download easily. 


```python
from benchmate.alignment.foldseek import FoldSeek

foldseek=FoldSeek()
foldseek.list_dbs()
```

Once you pick one you like you can dowload it

```python
foldseek.download_db("<dbname>", "<location>", create=False)
```

### Creating a local database

If you have a collection of structures (a folder full of pdbs) that you want to create a database from you can do that as well. 
Like mmseqs please make sure that the structures you have in there are unique

```python
folseek.create_database(<pdb_dirh>, <db_path>, gpu_padded=False)
```

The rest is the same as mmseqs. 

After preparing databases you are ready for searching. Make sure that your sequence `seq_type` matches the type of database you are searching.

```python
from benchmate.structure.structure import Structure

my_structure=Structure(name="name", pdb="pdb_file.pdb")

foldseek.search(query=my_structure, target_db=<database/path/name>, <output_tsv>, <output_a3m>)
```

This will generate 2 files the output tsv will return some alignment metrics and what they have aligned to
the output_a3m will generate the MSA alignment file. Keep in mind that you need to name these paths.

