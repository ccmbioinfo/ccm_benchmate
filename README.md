<div style="text-align: center;">
    <img src="./assets/benchmate.png" width="900" alt="CCM Benchmate logo" class="center">
</div>

# CCM Benchmate package:

This package aims to provide an integration setup for different biological from different sources and formats. There are
 several modules that are designed to work together to allow researchers to combine data from public databases, papers 
as well as their own data. 

To get started please see [installation instructions](INSTALLATION.md).

Each of the modules are designed to work independently from one another with few exceptions (see variant and ranges modules 
and how they are used in the apis and genome module). Each module has its own README file that provides usage instructions and 
how they can be integrated together. 

This package is a work in progress and is not yet ready for production use, that said, quite a few of the modules can be 
used to get started, and they can be used to build custom pipelines for data integration. Below is a brief overview of the
modules that are currently available in the package:

## Apis module:

The goal of the module is to provide a unified(-ish) interface to different biological databases. The module has interfaces
the following databases:

+ uniprot.org: This is a database of protein sequences and annotations. The module provides a way to search for proteins
and their respective annotations. The entirety of the uniprot database can be searched using the module, including variation
isoforms and mutagenesis endpoints. These are then integrated into a single dictionary that can be used to access the data.
+ ncbi.nlm.nih.gov: This is a database of nucleotide sequences and annotations. The module provides a way to search for all 
of the ncbi databases, including nucleotide sequences, protein sequences, gene annotations, and more. While you can search pubmed
using this module, the literature module is better suited for that purpose (see below). 
+ ensembl.org: This is a database of genomic sequences and annotations. The module provides a way to search for gene variants
mapping between different coordinates systems, and more. The module also provides a way to search for genes and their annotations,
annotate variants, query cross references from different databases and more. 
+ stringdb.org: This is a database of protein-protein interactions. The module provides a way to search for protein-protein interactions. 
Additionally you can use the biogrid and IntAct endpoints under others to perform similar queries.
+ For information on RNA the RNACentral module provides a way to search for RNA sequences and annotations. 

You can see a detailed overview of how these can be used in the readme file under ccm_benchmate/apis/README.md.

We are currently working on adding more databases to this module, if you have suggestions for databases that you would like to see
please open an issue on the GitHub repository and we will try to add them.

We are also working on a databses module that will provide a way to retrieve data from smaller platforms such as GTEx where the whole 
database is downloaded ahead of time in a read-only folder. 

## Literature module:

This module provides a way to search for scientific literature. It is designed to work with the NCBI PubMed and ARXIV databases.
You can search for articles and using free text queries as well as retriving specific articles by their identifiers. The latter is 
useful for retrieving articles that you already know about or more importantly are mentioned in the data you have retrieved using the 
apis modules. 

Articles titles and abstracts are returned as from pubmed and arxiv searches (pubmed already archives medarxiv and bioarxiv articles).
Additionally you can search for open acceess articles using openalex.org and retrieve their full text pdf files for download. 

These downloaded pdf (as well as any other local pdf that you already have) can be processed to extract the text, figures, tables from the 
downloaded documents. Using semantich chunking methods (sepearing the text into sections that convey similar topics) the text can further be
processed. Figures and tables can be automaticall interpreted using a vision language model (default is QWEN-7.5B-VL). These interpretations 
are similarly processed to the full text data. All of this can be permanantly stored in a database for later retrieval and analysis 
(more on that later, see knowledge_base module). 

## Container Runner module:

This is a module that would allow you to run any conteinerized application on your local machine or on a remote server. To give you the most
flexible way to incoporate your data into you database we have created a container runner class that can be used to run any singularity/apptainer
containter either locally or on HPC. We also have a to_container script that can be used to convert conda environments into singularity/appatiner
contianers. 

We are working on creating a small libarry of exisiting containers that can be immediately used to process your data. These will be available 
soon in our own docker container registry. You can then use these docker containers to create a singluarity/apptainer .sif file to run arbitrary packages and pipelines. You can run these packages and commands either in an interactive session or submit them as slurmm jobs in HPC. Please see the container runner module readme for usage instructions. 

Keep in mind that if you want to integrate the outputs of these containers/pipelines it's up to you to make sure that they are compatible with the modules in this package. 

## Databases Module

Currently this is empty, the goal is to gather information and requests from the general community to create either a standalone database with a query schema or just a collection of read-only file where users can search for their data on their own. Once this is done we will also release the files and their respective contents available here that are under hpc. Additionally we will provide a download script to create the same folder/database structure as well as instructions to how to regularly update the files as new versions of databases become available. 

## Genome Module

While it is possible to use the ensembl api class to query genomic ranges and intervals for instances where you are interested in only one genome (and its annotatoins) for the whole project and you will need to make repeated queries it would be more performant (and nicer to ther people using the ensembl api) to generate a data structure that can represent genomic/proteomic information. 

This is were the genom module comes into play. The genome.genome.Genome class takes a genome fasta file and a gtf fjile and creates a database of genomic regions. These regions can then be queried by genes, transcripts, exons, cdss, introns and utrs depending on the avalibility of these annotation types in the gtf file. You can also extract sequences from the genome fasta file for any arbitrary genome interval (see Ranges and GenomicRanges below) as well as providing (or generating) transcritome and proteome fasta files. 

The genome module also suspports saving these results to an arbitrary database, whether this is your knowledge base or any other kind of SQL databse (could even be in-memory sqlite). Each genome instance can be created and stored independently so if your analysis/project requires multiple genomes (or multiple annotations of the same fasta file, these are treated as different genomes). There is also support for that. 

Finally for your own work you can add arbitrary annotations to each of the tables in `JSON` format and then query them later. 

## Sequence Module

This module is there to represent biological sequences. There are a few methods (more to come, please create an issue if you'd like to see specific things). 

The base `Sequence` class can take 4 different kinds of sequences (DNA, RNA, protein and [3di](https://github.com/steineggerlab/foldseek)) and store arbitary properties and annoations in the features property. You can read/write these to fasta files, run blast searches using NCBI's blast api calculate msas using mmseqs (this will be moved to containers module and will call that container by default in the future) and calculate embeddings using several different AI models likek ESM2/3 or nucleotide transformer (more will come, please create an issue if you would like to see more models). 

For collections of sequences there are 2 other class types, `SequenceList` and `SequenceDict`, as the name suggests there are `list` and `dict`  like instances and contain many other methods that list and dictionaries have. Please see the sequence module readme for more information and usage instructions. 

## Structure Module

Similar to sequence module, the main goal is to store sequences and related information as well as some basic calculations related to biological structures. 

The base `Structure` class can take a pbd file and load its structure. It can extract the sequence of the structure, calculate embeddings using ESM3, calculate solvent accesible surface area, get its 3Di sequence (see above), align it to another `Structure` instance and write to results to a pdb file. Still under construction, you can also predict a structure using one of (OmegaFold, Alphafold2, AlphaFold3-you need to get your own weights due to licensing requirements, Boltz1 and Boltz2). These will be calls to the `ContainerRunner` module and results will be saved to disk. 

There is also a `StructureComplex` instance and as the name suggests this is there to represent complexes. These can be multiple proteins, or a protein+ligand, DNA/RNA/Protein complexes. Similar to the `Structure` instance we are working on creating `ContainerRunner` calls to predict arbitrary structure complexes using AlphaFold2/3 and Boltz1/2. 

Additionally we are working on creating a `Simulation` class to sample protein structure fluctiations either via [Openmm](https://openmm.org/) (very computationally intensive, but accurate and time resolved), [BioEmu](https://github.com/microsoft/bioemu) and [AlphaFlow](https://github.com/bjing2016/alphaflow). These again will be calls to `ContainerRunner` calls, which means if you have other calculations that will utilize these containers for arbitrary outputs. 

## Variant Module

As the name suggests, this is module to representing variants. These can range from simple snps/indels to large structural variations and tandem repeat expansions. These variants take some basic required information for their representations. You can create genomic HGVS notations from these variatns which would make them compatible with some of the enpoints in ensembl module. If there are other vairtion types that we have missed please create an issue and describe how that variant is represented. Before doing so please look at the code in variant.variant file to get ian idea about how we are approaching this problem. 

## Ranges Module

These module contains to main classes, `Ranges` moduel along with its counterparts `RangesList` and `RangesDict` are for storing arbitrary ranges. These can be any integer based ranges (that's the current limitation). Once you have a few ranges you can calculate the distance between them, you can merge them, calculate overlaps between 2 ranges. 

All these operations are also supported in `GenomicRanges` instances as well. It also requires strand and chromosome information for more biologically relevant calculations. These modules can be used on their own for perfoming pythonic operations similar to R's `GenomicFeatures` package. They are also being heavily used by the `genome.genome.Genome` class for querying, and some of the endpoints in the `apis.ensembl.Ensembl` instance. Please see the specific readme under the ranges module for usage instructions. 

## Knowledge Base

This module is designed to store the results of your searches and queries in a database. The goal is to provide a way to store the data that you have retrieved from the different modules in a structured way that allows you to query it later. The database schema
is still under heavy development. Currenlty we have schemas to store the paper classses, sequences, structures, variants and genomes. Due to semantic chunking and processing of the paper text there is a strict requiremen to use postgres as the database. This allows us
to offload a lot of the semantic searching via pgvector extension. Unfortunately this means that you will need to install pgvector extension on your postgres database. We will be providing instructions how to do that under the knowledge base module readme.

One of the most ambitions goals of this module it to provide a natural language search capabilities to many different data modalities that are represented in by othe other modules. This means that you will be able to search for papers, sequences, 
structures, variants and genomes using natural language queries. The results will be returned in a structured way that allows you to easily access the data. This great flexilbilitly however comes at cost of requiring a gpu to run a language modeld that will 
perform the queyring for you. We are currently working on a few different modeld that can be used for this purpose and will be providing a unified interface to use either your local models served via `llama.cpp` or `ollama` or remote models served via `huggingface.co` or
closed source models like `openai.com`. The goal of this project is not to provide an interface for analysis but rather to provide a way to store and query the data that you have retrieved from the different modules in a structured way that hopefully will 
allow you to generate hypoteses to test and analyze. This means that we will **not** be providing any analysis pipelines or tools otherthan simple `ContainerRunner` calls to run your own pipelines and we will not be supporiting any kind of security or 
will data privacy. This is a research project and we are not responsible for any data that you store in the knowledge base.

### Storing your searches/results

**COMING SOON**

### Querying your searches/results

**COMING SOON**

## ROADMAP

There are several avenues that we are currently exploring to expand the functionality of this package. Below is a list of the most important ones:

+ **Knowledge Base**: We are working on a knowledge base module that will allow you to store the results of your searches and queries in a database. 
This will allow you to query the data later and generate hypotheses to test and analyze. The goal is to provide a way to store the data that you have retrieved from the different modules in a structured way that allows you to query it later.
+ **Container Library**: We are working on a library of containers that can be used to process your data. These will be available in our own docker container registry and can be used to create singularity/apptainer containers.
+ **More APIs**: We are working on adding more APIs to the package. We are also trying to figure out a more streamlined way to combine the results of different api calls in to a more unified data structure. This would allow your 
queries to be scripted more easily. 
+ **More Models**: We are working on adding more models to the package. We are hoping to integrate the state of the art models for sequence, structure and variant analyses. 
+ **More Databases**: We are working on adding more databases to the package. We are then hoping to provide a way to query these databases in a unified way. These will be locally stored databases that do not require api calls.
+ **More Documentation**: We are working on adding more documentation to the package. Once we have a more functional package we will create a deatailed documentation for each module and how they can be used together both interactively and in a pipeline.
+ **More Tests**: We are working on adding more tests to the package. This is an urgent requirement that we could use help with. If you have experience using `pytest` and would like to help us write tests please create a pull request. 
+ **More Examples**: We are working on adding more examples to the package. If you have suggestions for examples that you would like to see please create an issue on the GitHub repository and we will try to add them.
+ **More Containers**: We are working on adding more containers to the package. Once we have a series of containers that can be used to process your data will create instructions as to how to pull them and use them as either Docker or Singularity/Apptainer containers.

### Contributing

Please see CCM Benchmate [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute to the package. We are always looking for help with writing tests, documentation, examples and more. 
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
Please see [CONTRIBUTING.md](CONTRIBUTING.md) for how to do that and basic reccomendations about our (very relaxed) code standards. 









