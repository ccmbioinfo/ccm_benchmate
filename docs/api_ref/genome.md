---
layout: default
title: Genome
parent: API Reference
nav_order: 3
---

<a id="benchmate.genome"></a>

# benchmate.genome

<a id="benchmate.genome.genome"></a>

# benchmate.genome.genome

<a id="benchmate.genome.genome.Genome"></a>

## Genome Objects

```python
class Genome()
```

<a id="benchmate.genome.genome.Genome.__init__"></a>

#### \_\_init\_\_

```python
def __init__(name,
             description,
             genome_fasta,
             gtf,
             transcriptome_fasta=None,
             standalone=False,
             proteome_fasta=None,
             create=True,
             db_conn=None,
             project=None)
```

**Arguments**:

- `gtf_path`: Path to the GTF file
- `genome_fasta`: Path to the genome fasta file
- `transcriptome_fasta`: Path to the transcriptome fasta file
- `proteome_fasta`: Path to the proteome fasta file
- `db_conn`: database connection object this is a sqlalchemy engine
- `taxon_id`: taxon id of the genome

<a id="benchmate.genome.genome.Genome.genes"></a>

#### genes

```python
def genes(ids=None, range=None, ignore_strand=True)
```

Gene id or range if range is provided it will return the genes in that range depending on the overlap type

**Arguments**:

- `id`: Gene id, that used in the gtf file
- `range`: A GenomicRange object
- `ignore_strand`: whether to ignore strand this will return all the genes in the range regardless of strand

**Returns**:

a GenomicRangesDict object with the genes in it, each key is the gene name and the value is a GenomicRange object

<a id="benchmate.genome.genome.Genome.transcripts"></a>

#### transcripts

```python
def transcripts(gene_ids=None,
                ids=None,
                range=None,
                ignore_strand=True,
                group_by_gene=True)
```

return transcripts by gene id, transcript id or range

**Arguments**:

- `gene_ids`: return transcripts for these gene ids
- `ids`: return transcripts with these transcript ids
- `range`: return transcripts in this range
- `ignore_strand`: ignore strand when searching by range
- `group_by_gene`: whether to group the returned transcripts by gene id, if true the returned object
will have gene ids as keys and GenomicRangesList as values, if false the returned object will have transcript ids as keys and GenomicRange as values

**Returns**:

a genomic ranges dict object

<a id="benchmate.genome.genome.Genome.exons"></a>

#### exons

```python
def exons(transcript_ids=None,
          ids=None,
          range=None,
          group_by_transcript=True,
          ignore_strand=True)
```

same as genes but will need to search by transcript not gene, if you do not know the transcript search for it with transcripts first

**Arguments**:

- `transcript_id`: return all exons for this transcript id
- `id`: return exon with this id
- `range`: return exons in this range
- `group_by_transcript`: whether to group the returned exons by transcript id, if true the returned object
- `ignore_strand`: whether to ignore strand when searching by range

**Returns**:

a genomic ranges dict object, if not grouped by transcript the keys will be exon ids otherwise the keys will be transcript ids

<a id="benchmate.genome.genome.Genome.coding"></a>

#### coding

```python
def coding(transcript_ids=None,
           ids=None,
           range=None,
           group_by_transcript=True,
           ignore_strand=True)
```

same as exons return all the coding sequences for a transcript or a list of transcripts

**Arguments**:

- `transcript_id`: return all coding sequences for this transcript id
- `id`: return coding sequence with this id
- `range`: return coding sequences in this range
- `group_by_transcript`: whether to group the returned coding sequences by transcript id, if true the returned object

**Returns**:

a genomic ranges dict object, if not grouped by transcript the keys will be coding sequence ids otherwise the keys will be transcript ids

<a id="benchmate.genome.genome.Genome.three_utr"></a>

#### three\_utr

```python
def three_utr(transcript_ids=None, ids=None, range=None, ignore_strand=True)
```

return all the 3' utrs for a transcript or a list of transcripts

**Arguments**:

- `transcript_ids`: return 3' utrs for these transcript ids
- `range`: return 3' utrs in this range
- `ignore_strand`: regardless of strand

**Returns**:

a genomic ranges dict object with transcript ids as keys and GenomicRangesList as values, the utrs are not described as
separate exons but the exons are merged into one if that utr spans multple exons. Additionally if the utrs ends in the middle
of an exon the utr will end there.

<a id="benchmate.genome.genome.Genome.five_utr"></a>

#### five\_utr

```python
def five_utr(transcript_ids=None, ids=None, range=None, ignore_strand=True)
```

return all the 5' utrs for a transcript or a list of transcripts

**Arguments**:

- `transcript_ids`: return 3' utrs for these transcript ids
- `range`: return 3' utrs in this range
- `ignore_strand`: regardless of strand

**Returns**:

a genomic ranges dict object with transcript ids as keys and GenomicRangesList as values, the utrs are not described as
separate exons but the exons are merged into one if that utr spans multple exons. Additionally if the utrs ends in the middle
of an exon the utr will end there.

<a id="benchmate.genome.genome.Genome.introns"></a>

#### introns

```python
def introns(transcript_ids=None,
            ids=None,
            range=None,
            group_by_transcript=True,
            ignore_strand=True)
```

return all the introns for a transcript or a list of transcripts

**Arguments**:

- `transcript_id`: return introns for this transcript id
- `id`: return intron with this id (introns usually are not descibed in a gtf, so this id may not be very useful since
it is an auto incremented id)
- `range`: return introns in this range
- `group_by_transcript`: return introns grouped by transcript
- `ignore_strand`: whether to ignore strand when searching by range

**Returns**:

return: a genomic ranges dict object, if not grouped by transcript the keys will be intron ids otherwise the keys will be transcript ids

<a id="benchmate.genome.genome.Genome.custom_range"></a>

#### custom\_range

```python
def custom_range(grange=None, ignore_strand=False)
```

query a user inserted custom ranges

**Arguments**:

- `grange`: a genomic ranges instance
- `ignore_strand`: whether to ignore strand when searching by range

**Returns**:

a GenomicRangesList with all the results, or None

<a id="benchmate.genome.genome.Genome.insert_custom_range"></a>

#### insert\_custom\_range

```python
def insert_custom_range(grange)
```

insert a new custom range

**Arguments**:

- `grange`: a GenomicRange instance, if you are using GenomicRangesList of GenomicRangesDict, run this
function multiple times

**Returns**:

None

<a id="benchmate.genome.genome.Genome.get_sequence"></a>

#### get\_sequence

```python
def get_sequence(genomic_range, type='genome')
```

Get the sequence of a genomic range. This takes a single genomc range you can iterate over a GenomicRangeList or GenomicRangeDict

**Arguments**:

- `genomic_range`: GenomicRange object

**Returns**:

sequence as string

<a id="benchmate.genome.genome.Genome.add_annotation"></a>

#### add\_annotation

```python
def add_annotation(table, row_id, annots)
```

add arbitrary annotations as a dictionary to a specific row in a specific table

**Arguments**:

- `table`: which table to add the annotations to
- `id`: which row id to add the annotations to, this is the datbase internal id not the gene_id or transcript_id, those
ids can be found in the annotations of each row
- `annots`: a dictionary of annotations to add

**Returns**:

None but the database will be updated

<a id="benchmate.genome.genome.Genome.search_annotation"></a>

#### search\_annotation

```python
def search_annotation(table, values=None)
```

search annotations in the database for a specific key or value in a table

**Arguments**:

- `table`: this determines what kinds of features you are searching genens, transcripts etc
- `values`: search all the values of all keys if keys is none otherwise search those keys and return matching values

**Returns**:

genomicRangesDict object with the matching rows

<a id="benchmate.genome.utils"></a>

# benchmate.genome.utils

<a id="benchmate.genome.utils.parse_gtf_attributes"></a>

#### parse\_gtf\_attributes

```python
def parse_gtf_attributes(attributes_str)
```

parse the gtf attributes column that is the last one

**Arguments**:

- `attributes_str`: 

<a id="benchmate.genome.utils.parse_gtf"></a>

#### parse\_gtf

```python
def parse_gtf(filepath)
```

for a given gtf file parse all the fields and get them ready for db insertion, this needs to be done once per genome

this gets called by the genome class instances, there is no need for the end user to call this

**Arguments**:

- `filepath`: path for the gtf file

**Returns**:

a list of all used genomic features

<a id="benchmate.genome.utils.start_genome"></a>

#### start\_genome

```python
def start_genome(genome_name,
                 genome_fasta_file,
                 engine,
                 transcriptome_fasta_file=None,
                 proteome_fasta_file=None,
                 description=None)
```

load a genome instance, this is called by the genome instance

**Arguments**:

- `genome_name`: name of the genome
- `genome_fasta_file`: name of the fasta file to be used
- `engine`: connection engine used by sqlalchemy, you are responsible for creating this
- `transcriptome_fasta_file`: optional transcritome file
- `proteome_fasta_file`: optional proteome file
- `description`: description of the genome

**Returns**:

return genome id, this will be used to add other things to the genome db

<a id="benchmate.genome.utils.insert_chroms"></a>

#### insert\_chroms

```python
def insert_chroms(genome_id, chrom_list, engine)
```

insert chrom info for a specific genome, given its id

**Arguments**:

- `genome_id`: see above,
- `chrom_list`: list of chrom ids
- `engine`: connection engine

**Returns**:

inserted chrom ids, these will be used to insert other features

<a id="benchmate.genome.utils.insert_genes"></a>

#### insert\_genes

```python
def insert_genes(chrom_ids, gene_list, engine)
```

insert genes

**Arguments**:

- `chrom_ids`: see above
- `gene_list`: list of genes to inser
- `engine`: connection engine

**Returns**:

list of gene ids (not gene names or gene unique ids, this is specific to the db)

<a id="benchmate.genome.utils.insert_transcripts"></a>

#### insert\_transcripts

```python
def insert_transcripts(gene_ids, tx_list, engine)
```

insert transcripts for each gene id

**Arguments**:

- `gene_ids`: see above
- `tx_list`: list of transcripts
- `engine`: connection engine

**Returns**:

list of db ids for all the inserted transcripts

<a id="benchmate.genome.utils.insert_exons"></a>

#### insert\_exons

```python
def insert_exons(transcript_ids, exon_list, engine)
```

insert exons for each transcript

**Arguments**:

- `transcript_ids`: see above
- `exon_list`: list of exons
- `engine`: connection engine

**Returns**:

list of db ids for all the inserted exons

<a id="benchmate.genome.utils.insert_three_utrs"></a>

#### insert\_three\_utrs

```python
def insert_three_utrs(transcript_ids, three_utr_list, engine)
```

insert three_utrs

**Arguments**:

- `transcript_ids`: see above
- `three_utr_list`: see above
- `engine`: connection engine

**Returns**:

list of db ids for all the inserted three_utrs

<a id="benchmate.genome.utils.insert_five_utrs"></a>

#### insert\_five\_utrs

```python
def insert_five_utrs(transcript_ids, five_utr_list, engine)
```

insert five_utrs

**Arguments**:

- `transcript_ids`: see above
- `five_utr_list`: see above
- `engine`: connection engine

**Returns**:

list of db ids for all the inserted five_utrs

<a id="benchmate.genome.utils.insert_coding"></a>

#### insert\_coding

```python
def insert_coding(transcript_ids, exon_ids, coding_list, engine)
```

insert coding regions, this tracks not only transcripts but also which cds belongs to which exon

**Arguments**:

- `transcript_ids`: see above
- `exon_ids`: see above
- `coding_list`: see above
- `engine`: connection engine

**Returns**:

list of db ids for all the inserted coding regions

<a id="benchmate.genome.utils.insert_introns"></a>

#### insert\_introns

```python
def insert_introns(transcript_ids, exon_list, engine)
```

insert introns, since there is no intron information they are calculated before insertion by grouping things

by transcript and then calculating the missing areas in each exon for each transcript

**Arguments**:

- `transcript_ids`: see above
- `exon_list`: see above
- `engine`: connection engine

**Returns**:

list of db ids for all the inserted introns

<a id="benchmate.genome.utils.insert_genome"></a>

#### insert\_genome

```python
def insert_genome(gtf,
                  engine,
                  name,
                  description,
                  genome_fasta,
                  transcriptome_fasta=None,
                  proteome_fasta=None)
```

this takes a gtf file and inserts all the available features

**Arguments**:

- `gtf`: gtf file
- `engine`: connection engine
- `name`: name of the genome
- `description`: description of the genome
- `genome_fasta`: fasta file
- `transcriptome_fasta`: transcriptome fasta file
- `proteome_fasta`: proteome fasta file

**Returns**:

genome and chrom ids

<a id="benchmate.genome.tables"></a>

# benchmate.genome.tables

