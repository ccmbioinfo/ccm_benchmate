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
project (see [project module](under_construction/project.md)). 

This package is being actively developed and there may be breaking changes as well as additional requirements. That said, a
few of the modules can be used right now (APIs, genome and literature among others) as standalone modules or can be used together. There are
quite a few modules that are responsible to different functionalities. Each of these modules have their own page so please see 
them for detailed instructions about how to use them. 

We hope that this module makes your life a little easier by streamlining your data collection from publicly available sources in 
your research. Below is a brief description of the modules that are planned:

+ APIs: A collection of classes for different prominent public databases (e.g. uniprot, ncbi etc.) for easy access and query.
+ Literature: A pythonic way to search and process scientifc papers from pubmed and arxiv
+ Sequence: A pythonic way to represent biological sequences (DNA, RNA, protein)
+ Structure: A module to represent 3D biological structures from RSCB and Alphafold DB
+ Molecule: A module to represent small drug-like molecules
+ Genome: A stable, fast and memory efficient way to interact with your genome(s)
+ Alignment: use blast, mmseqs, foldseek and folddisco to search for sequences and structures rapidly

Additionally, we have created several lightweight python modules to work with different biological ideas such as:

+ Ranges and GenomicsRanges: Range operations over single and collections of ranges
+ Variant: A pythonic way to represent genomic variations

Finally, we aim to collect all of this information in a single database that can be queries via sql or natural language. 

While still under construction, the final modules (project and knowledgebase) will collect information from all the modules
described above and make it searchable using sql, keywords and natural language. These modules include

+ KnowledgeBase: This is an internal module that will be used by the Project module (see below). It basically is a thin wrapper
around a PostgreSQL database that makes connections and streamlines data retrieval and upload
+ Project: This is the main meta class that we are hopping to use to interact with all the modules eventually. The aim is to 
provide methods to the user to put all the information gathered at different times, update them as necessary and query them using
sqlalchemy, key word searches, natural language and maybe even images. 

### Installation

Please see the [installation instructions](installation.md) to get started. There are 2 main ways to install benchmate (3rd and 4th are 
on the way). Creating a conda environment and installing the dependencies is the preffered methods at the moment. There is an untested
installation script that is also discussed. 


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