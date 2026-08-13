---
layout: default
title: Home
nav_order: 1
---

![](assets/benchmate.png)

# CCM Benchmate Documentation

This package aims to provide an integration setup for different biological data from different sources and formats. There are
several modules that are designed to work together to allow researchers to combine data from public databases, papers 
as well as their own data. There are several modules that can be used independently or can be integrated into one cohesive
project (see [project module](modules/project.md) and [project workflow examples](project_usage.md)). 

This package is updated for Python 3.12+ and PostgreSQL 17+. The core modules (APIs, Genome, Literature, Sequence, Structure, Molecule, Alignment, Ranges, Variants, KnowledgeBase, and Project) can be used independently or unified via the `Project` meta-module.

Below is a brief description of the core modules:

+ APIs: A collection of classes for different prominent public databases (e.g. UniProt, NCBI, Ensembl, StringDB) for easy access and query.
+ Literature: A pythonic way to search and process scientific papers from PubMed and OpenAlex.
+ Sequence: A pythonic way to represent biological sequences (DNA, RNA, protein, 3Di).
+ Structure: A module to represent 3D biological structures from PDB and AlphaFold DB.
+ Molecule: A module to represent small drug-like molecules with ECFP4/FCFP4 fingerprint calculations.
+ Genome: A stable, fast and memory efficient way to interact with your genome(s).
+ Alignment: Use BLAST, MMseqs2, Foldseek, and Folddisco to search sequences and structures rapidly.
+ Ranges and GenomicRanges: Range operations over single and collections of genomic ranges.
+ Variant: A pythonic way to represent sequence, structural, and tandem repeat variations.

### Integrated Knowledge Base & Project Meta-Module

The **KnowledgeBase** and **Project** modules collect information from all the modalities described above into a single PostgreSQL (17+) database enabled with `pgvector` and `rdkit` extensions:

+ **KnowledgeBase**: Internal wrapper around PostgreSQL (17+) that manages database schemas, vector indexing, and table operations.
+ **Project**: The central meta-class that unifies literature ingestion, API call logging, multi-modal entity storage (`to_kb`), item listing (`list_items`), exact DB object retrieval (`from_kb`), and multimodal search (`project.search`). See the [Project Workflow & Usage Examples](project_usage.md) for detailed tutorials.

### Installation & Containerization

Please see the [installation instructions](installation.md) to get started with Python 3.12 and PostgreSQL 17+. Additionally, pre-built Docker containers and a Docker Compose setup are available (see [Containerization Overview](containerization/CONTAINER_OVERVIEW.md) and [Launcher Usage](containerization/LAUNCHER_USAGE.md)). 


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