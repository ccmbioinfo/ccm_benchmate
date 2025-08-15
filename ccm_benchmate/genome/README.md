---
layout: default
title: Genome
---

# Genome Module

A module for working with genomic data, providing functionality to query and manipulate genome sequences, annotations, and features through a database interface.

## Overview

The `Genome` class provides methods to:
- Load and query genomic sequences from FASTA files
- Query genomic features (genes, transcripts, exons, CDS regions, introns) 
- Generate transcriptome and proteome sequences
- Retrieve genomic sequences for specific regions

## Usage

### Initializing a Genome Object

```python
from ccm_benchmate.genome.genome import Genome

# Create a genome object with required files
genome = Genome(
    genome_fasta="path/to/genome.fa",
    transcriptome_fasta="path/to/transcriptome.fa",  # Optional
    proteome_fasta="path/to/proteome.fa",            # Optional
    db_conn=engine,                                  # SQLAlchemy engine
    taxon_id="9606"                                 # Optional taxonomy ID
)
```

### Querying Genomic Features

The module supports querying different types of genomic features:

```python
from ccm_benchmate.ranges.genomicranges import GenomicRange

# Query genes by ID
genes = genome.genes(ids=["ENSG00000139618"])

# Query genes in a specific region
region = GenomicRange("chr1", 1000000, 2000000, "+")
genes_in_region = genome.genes(range=region)

# Get transcripts for a gene
transcripts = genome.transcripts(gene_id="ENSG00000139618")

# Get exons for a transcript
exons = genome.exons(transcript_id="ENST00000380152")

# Get coding sequences
cds = genome.coding(transcript_id="ENST00000380152")

# Get introns
introns = genome.introns(transcript_id="ENST00000380152")
```

### Retrieving Sequences

```python
# Get sequence for a specific genomic range
gr = GenomicRange("chr1", 1000000, 1001000, "+")
sequence = genome.get_sequence(gr)
```

### Generating Transcriptome and Proteome

During initialization if `transcriptome_fasta` and `proteome_fasta` are not provided, the module can generate the 
transcriptome and proteome sequences and include them as attributes in the class to be queried. These are file connections
and are very light on memory but that means that they cannot be saved or pickled. 

### Adding arbitrary annotations:


## Database Schema

The module uses the following database tables:

### genome
- `genome_id`
- `version`
- `source`
- `genome_fasta_file` just the file path, there is a os.file check during
class instance initiation
- `transcriptome_fasta_file`
- `proteome_fasta_file`
- `description`

### chromosome
- `chrom_id` (PRIMARY KEY)
- `name` (TEXT)
- `length` (INTEGER)

### gene
- `gene_id` (PRIMARY KEY)
- `chrom` (TEXT)
- `start` (INTEGER)
- `end` (INTEGER)
- `strand` (TEXT)
- `annot` (JSON)

### transcript
- `transcript_id` (PRIMARY KEY)
- `gene_id` (FOREIGN KEY)
- `chrom` (TEXT)
- `start` (INTEGER)
- `end` (INTEGER)
- `strand` (TEXT)
- `annot` (JSON)

### exon
- `exon_id` (PRIMARY KEY)
- `transcript_id` (FOREIGN KEY)
- `chrom` (TEXT)
- `start` (INTEGER)
- `end` (INTEGER)
- `strand` (TEXT)
- `annot` (JSON)

### cds
- `cds_id` (PRIMARY KEY)
- `transcript_id` (FOREIGN KEY)
- `chrom` (TEXT)
- `start` (INTEGER)
- `end` (INTEGER)
- `strand` (TEXT)
- `annot` (JSON)

### intron
- `intron_id` (PRIMARY KEY)
- `transcript_id` (FOREIGN KEY)
- `chrom` (TEXT)
- `start` (INTEGER)
- `end` (INTEGER)
- `strand` (TEXT)
- `annot` (JSON)

## Notes:

- All genomic coordinates are 1-based and inclusive
- The database schema uses SQLAlchemy for ORM
- FASTA files are accessed using pysam
- Strand can be either '+', '-' or '*' for unstranded things like breaks. 
- Multiple genomes can be stored at the same time. 
- There is no requirement to use the knowledgebase to store your genome, you can use
any database connection that can be used with `SQLAlchemy`. 

