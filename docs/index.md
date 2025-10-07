---
layout: default
title: Home
nav_order: 1
---

![](assets/benchmate.png)

# CCM Benchmate Documentation

This package aims to provide an integration setup for different biological from different sources and formats. There are
several modules that are designed to work together to allow researchers to combine data from public databases, papers 
as well as their own data. There are several modules that can be used independently or can be integrated into one cohesive
project (see [project module](project.md)). 

This package is being actively developed and there may be breaking changes as well as additional requirements. That said, a
few of the modules can be used right now (APIs, genome and literature) as standalone modules or can be used together. There are
quite a few modules that are responsible to different functionalities. Each of these modules have their own page so please see 
them for detailed instructions about how to use them. 

## APIs module 

The goal of the module is to provide a unified(-ish) interface to different biological databases. The module has interfaces
the following databases:

+ [Uniprot](unprot.org): This is a database of protein sequences and annotations. The module provides a way to search for proteins
and their respective annotations. The entirety of the Uniprot database can be searched using the module, including variation
isoforms and mutagenesis endpoints. These are then integrated into a single dictionary that can be used to access the data.
+ [NCBI](ncbi.nlm.nih.gov): This is a database of nucleotide sequences and annotations. The module provides a way to search for all 
of the NCBI databases, including nucleotide sequences, protein sequences, gene annotations, and more. While you can search pubmed
using this module, the [literature module](literature.md) is better suited for that purpose (see below). 
+ [Ensembl](ensembl.org): This is a database of genomic sequences and annotations. The module provides a way to search for gene variants
mapping between different coordinates systems, and more. The module also provides a way to search for genes and their annotations,
annotate variants, query cross-references from different databases and more. 
+ [stringdb](stringdb.org): This is a database of protein-protein interactions. The module provides a way to search for protein-protein interactions. 
Additionally you can use the Biogrid and IntAct endpoints under others to perform similar queries.
+ [reactome](reactome.org): Reactome is a comprehensive database of biolgicla reaction, proteins and pathways. You can query many of the endpoints using 
this submodule
+ [rnacentral](rnacentral.org): RnaCentral *the* non-coding RNA sequence database, this is different from the NCBI genes in that it is dedicated to non-coding
sequences. 
+ [BioGrid]("https://thebiogrid.org/"): Biogrid is a biomedical interaction repository that contains information about protein-protein and protein-chemical 
interactions that are mostly manually curated at different levels. You will need a free API key to be able to use this module. You can obtain one [here](https://webservice.thebiogrid.org/)
+ [IntAct](https://www.ebi.ac.uk/intact/home): Simlar to BioGrid this database contains interaction data. You can query this database to arbitrary depth
to obtain information about different biological complexes and much more. 
+ [AlphaGenome](https://www.alphagenomedocs.com/index.html): AlphaGenome is a server running the latest alphagenome models
for variant, sequence and genomic interval consequence/feature predictions. 

You can see a detailed overview of each of the modules in the [APIs](apis.md) section. If you have suggestions for an API please create an issue with 
a description of the request and why that is important for your research and others.

## Literature module:

This module provides a way to search for scientific literature. It is designed to work with the NCBI PubMed and ARXIV databases.
You can search for articles and using free text queries as well as retriving specific articles by their identifiers. The latter is 
useful for retrieving articles that you already know about or more importantly are mentioned in the data you have retrieved using the 
APIs modules. 

Articles titles and abstracts are returned as from Pubmed and ARXIV searches (Pubmed already archives medarxiv and bioarxiv articles).
Additionally, you can search for open acceess articles using [openalex](openalex.org) and retrieve their full text pdf files for download. 

These downloaded pdf (as well as any other local pdf that you already have) can be processed to extract the text, figures, tables from the 
downloaded documents. Using semantic chunking methods (sepearing the text into sections that convey similar topics) the text can further be
processed. Figures and tables can be automaticall interpreted using a vision language model (default is QWEN-7.5B-VL). These interpretations 
are similarly processed to the full text data. All of this can be permanantly stored in a database for later retrieval and analysis 
(more on that later, see knowledge_base module). 

Depending on your use case you can also use a description of your research interest to filter papers based on their abstracts to save on compute
time and resources. Please see the literature module [documentation](literature.md) for more information and how to use these features. 

## Genome Module

While it is possible to use the Ensembl API class to query genomic ranges and intervals for instances where you are interested in only one genome (and its annotations) 
for the whole project and you will need to make repeated queries it would be more performant (and nicer to ther people using the Ensembl API) to 
generate a data structure that can represent genomic/proteomic information. 

This is were the genom module comes into play. The `genome.genome.Genome` class takes a genome fasta file and a gtf file and creates a database of 
genomic regions. These regions can then be queried by genes, transcripts, exons, cdss, introns and utrs depending on the availability of these annotation 
types in the gtf file. You can also extract sequences from the genome fasta file for any arbitrary genome interval (see Ranges and GenomicRanges below). 

The genome module also supports saving these results to a database, whether this is your knowledge base or any other kind of SQL databse (could even be in-memory sqlite). 
Each genome instance can be created and stored independently so if your analysis/project requires multiple genomes (or multiple annotations of the same fasta file, 
these are treated as different genomes) you can do that out of the box. 

Finally for your own work you can add arbitrary annotations to each of the tables in `JSON` format and then query them later. 

## Sequence Module

This module is there to represent biological sequences. There are a few methods (more to come, please create an issue if you'd like to see specific things). 

The base `Sequence` class can take 4 different kinds of sequences (DNA, RNA, protein and [3di](https://github.com/steineggerlab/foldseek)) and store arbitrary 
properties and annotations in the features property. You can read/write these to fasta files, run blast searches using NCBI's blast api calculate msas using mmseqs 
(this will be moved to [containers module](containers.md) and will call that container by default in the future) and calculate embeddings using several 
different AI models like ESM2/3 or nucleotide transformer (more will come, please create an issue if you would like to see more models). 

For collections of sequences there are 2 other class types, `SequenceList` and `SequenceDict`, as the name suggests there are `list` and `dict`  like instances 
and contain many other methods that list and dictionaries have. Please see the sequence module [documentation](sequence.md) for more information and usage instructions. 

## Structure Module

Similar to sequence module, the main goal is to store sequences and related information as well as some basic calculations related to biological structures. 

The base `Structure` class can take a pbd file and load its structure. It can extract the sequence of the structure, calculate embeddings using ESM3, calculate 
solvent accesible surface area, get its 3Di sequence (see above), align it to another `Structure` instance and write to results to a pdb file. 

There is also a `StructureComplex` instance and as the name suggests this is there to represent complexes. These can be multiple proteins, or a protein+ligand, DNA/RNA/Protein complexes. 

For both of these classes we are working on creating containers to perform structure predictions (single and complex), run molecular simulations. Stay tuned for more updates. 


## Container Runner module:

This is a module that would allow you to run any containerized application on your local machine or on a remote server. To give you the most
flexible way to incorporate your data into you database we have created a container runner class that can be used to run any singularity/apptainer
containter either locally or on HPC. We also have a to_container script that can be used to convert conda environments into singularity/appatiner
contianers. These modules have not been fully tested and we would appreciate if you can let us know with any issues you may encounter. 

We are working on creating a small library of exisiting containers that can be immediately used to process your data. These will be available 
soon in our own docker container registry. You can then use these docker containers to create a singluarity/apptainer .sif file to run arbitrary 
packages and pipelines. You can run these packages and commands either in an interactive session or submit them as slurmm jobs in HPC. 
Please see the container runner module [documentation](containers.md) for usage instructions. 

One of the main ambitions of this module is to avoid "pipeline graveyards" where pipelines developed by you or others can be used and re-used with ease
and their outputs can be integrated into other analyses without fighting with software dependencies and outdated instructions. 


## Ranges Module

These module contains a few classes, `Ranges` module along with its counterparts `RangesList` and `RangesDict` are for storing arbitrary ranges. 
These can be any integer based ranges (that's the current limitation). Once you have a few ranges you can calculate the distance between 
them, you can merge them, calculate overlaps between 2 ranges. If you have worked with R's [`IRanges`](https://www.bioconductor.org/packages/release/bioc/html/IRanges.html) package
the operations here will seem quite familiar

All these operations are also supported in `GenomicRanges` instances as well. It also requires strand and chromosome information for more biologically relevant 
calculations. These modules can be used on their own for perfoming pythonic operations similar to R's [`GenomicFeatures`](https://bioconductor.org/packages/release/bioc/html/GenomicFeatures.html)
package. They are also being heavily used by the `genome.genome.Genome` class for querying, and some of the endpoints in the `apis.ensembl.Ensembl` instance. 
Please see the ranges [documentation](ranges.md) for more information. 

## Molecule Module

This module is for representing small molecules. There are methods to calculate descriptors, fingerprints and store other information about a specific molecule. We also support
searching for similar molecules via tanimoto similarity using the usearch-molecule package. Additionally, we have created a massive database (>8B) of synthesizable drug-like
molecules that you can search. This is not immediately supported via this package since you will need to have the database itself that is not provided here because it is several
TBs in size. If you would like to search for molecules send us an email and we can look into how we can best assist you. 

## Variant Module

As the name suggests, this is module to representing variants. These can range from simple snps/indels to large structural variations and tandem repeat expansions. These variants 
take some basic required information for their representations. You can create genomic HGVS notations from these variatns which would make them compatible with some of 
the enpoints in Ensembl module. If there are other variant types that we have missed please create an issue and describe how that variant is represented. 
Before doing so please look at the code in `variant.variant.py` file to get an idea about how we are approaching this problem. Currently we do not support storing information from 
experiments and variant calling pipelines as a single human genome sequencing data can provide up to 4 million variants and with their respecitive annotation this can become
quite unwieldy. We are working on creating a scalable solution to this problem. 

## Knowledge Base

This module is designed to store the results of your searches and queries in a database. The goal is to provide a way to store the data that you have retrieved from the different 
modules in a structured way that allows you to query it later. The database schema is still under heavy development. Currenlty we have schemas to store the papers, sequences, structures, variants, api calls and genomes. 
Due to semantic chunking and processing of the paper text there is a strict requirement to use [postgres](https://www.postgresql.org/) as the database. This allows us to offload a lot of the semantic searching via 
[pgvector](https://github.com/pgvector/pgvector) extension. Unfortunately this means that you will need to install pgvector extension on your postgres database. We will be providing 
instructions how to do that under the knowledge base module [documentation](knowledgebase.md).

One of the most ambitions goals of this module it to provide a natural language search capabilities to many different data modalities that are represented in by othe other modules. 
This means that you will be able to search for papers, sequences, structures, variants and genomes using natural language queries. The results will be returned in a structured way that allows you to 
easily access the data. This great flexilbilitly however comes at cost of requiring a gpu to run a language model that will perform the querying for you. We are currently working on a few different models that can be 
used for this purpose and will be providing a unified interface to use either your local models served via `llama.cpp` or `ollama` or remote models served via `huggingface.co` or
closed source models like `openai.com`. The goal of this project is not to provide an interface for analysis but rather to provide a way to store and query the data that you have retrieved from the 
different modules in a structured way that hopefully will allow you to generate hypoteses to test and analyze. This means that we will **not** be providing any analysis pipelines or tools other than 
simple `ContainerRunner` calls to run your own pipelines and we will not be supporting any kind of security or data privacy guarantees. This is a research project and we are not responsible for any data 
that you store in the knowledge base.

### Contributing

Please see CCM Benchmate [CONTRIBUTING.md](contributing.md) for how to contribute to the package. We are always looking for help with writing tests, documentation, examples and more. 
If you have suggestions for features that you would like to see please create an issue on the GitHub repository and we will try to add them.

#### Need your support

This is a package written for bioinformaticians and computational biologists by bioinformaticians and computational biologists. Our goal is to provide you
seamless integration of different biological data sources and formats. We are a small team and we are working on this package in our free time. We would like 
know if you find this package useful and if you have any suggestions for improvements or features that you would like to see.

### Issues

If you find any bugs or have suggestions for improvements please create an issue on the GitHub repository. We will try to address them as soon as possible.
Additionaly feel free to fork this repository and create a pull request with your changes. We are always looking for help with improving thie package and integrating as many 
data sources and modalitites as possible.

### Contact us

The best way to contact us is via github issues, you can create an issue about problems you are facing or features, datasets, containers you would like to have. 
If you have container/code pipeline etc. That you think others could use, you can create a module for it and create a pull request or make changes to one of the existing modules. 
Please see [CONTRIBUTING.md](docs/contributing.md) for how to do that and basic reccomendations about our (very relaxed) code standards. 