---
layout: home
title: Home
nav_order: 1
---


<div style="text-align: center;">
    <img src="./assets/benchmate.png" width="900" alt="CCM Benchmate logo" class="center">
</div>

# CCM Benchmate

**CCM Benchmate** is an open-source toolkit for integrating and analyzing biological data from diverse 
public resources, literature, and your own research. Designed for bioinformaticians and computational 
biologists, it offers modular, interoperable components to build data pipelines and accelerate 
discovery.

**🛠️ To get started, please see the [installation 
instructions](https://github.com/ccmbioinfo/ccm_benchmate/blob/master/INSTALLATION.md).** 
Each module is independently usable and well-documented—check out the README in each module's folder for 
details and code examples.

## 🚀 Key Features
- **Unified APIs**: Access major bioinformatics databases (UniProt, NCBI, Ensembl, STRINGdb, and more) 
through a simple Python interface.
- **Literature Search & Processing**: Find, download, and extract content from scientific articles 
(PubMed, arXiv, OpenAlex), with tools for processing PDFs and full-text mining.
- **Container Integration**: Seamlessly run and manage Singularity/Apptainer containers locally or on 
HPC, with tools to convert and deploy your own environments.
- **Genome, Sequence, and Variant Handling**: Intuitive classes for genomic intervals, sequences, 
variants, and annotations.
- **Structure Support**: Import, analyze, or predict molecular structures using state-of-the-art models.
- **Custom Knowledge Base**: Store and query your processed data and analysis results using PostgreSQL + 
pgvector for advanced semantic search (coming soon).

⭐️ Work in progress! Not yet intended for production. Feedback and 
[contributions](https://github.com/ccmbioinfo/ccm_benchmate/blob/master/CONTRIBUTING.md) are welcome.

## 💬 Documentation

Comprehensive documentation—including module guides and usage examples—is available at README.md under 
each module.

## 🎨 Modules Overview

Explore the main components (click for details):
- [APIs](API/): Unified interfaces for biological databases
- [Literature](Literature/): Advanced literature search and processing
- [Container Runner](ContainerRunner/): Manage and run containers
- [Databases](Databases/): (In development) Local and community-curated resources
- [Genome](Genome/): Genomic data structures and queries
- [Sequence](Sequence/): Sequence handling and analysis
- [Structure](Structure/): Structure loading, prediction, and analysis
- [Variant](Variant/): Variant representation and processing
- [Ranges](Ranges/): Generic and genomic intervals
- [Knowledge Base](KnowledgeBase/): Store and search for your results (coming soon)

## 💡 Roadmap

Our key development goals include:  

- **Knowledge Base:** Build a flexible, queryable database for integrated results and literature.  
- **Container Library:** Provide ready-to-use containers for common bioinformatics tasks.  
- **Expanded APIs & Databases:** Add support for more biological data resources with unified querying.  
- **Enhanced Models:** Integrate advanced models for sequence, structure, and variant analyses.  
- **Documentation & Testing:** Improve user guides, examples, and increase test coverage.  
- **Community Contributions:** Encourage feedback, examples, and additional containers from users.

We welcome contributions to help accelerate these efforts. For details, please see 
[ROADMAP.md](https://github.com/qin-work/Benchmate_doc_ccm/blob/main/ROADMAP.md)


## 🤝 Contributing

We welcome contributions of all kinds—code, docs, containers, and ideas.
- Bug reports or feature requests: please create an issue on the GitHub repository.
- See [CONTRIBUTING.md](https://github.com/ccmbioinfo/ccm_benchmate/blob/master/CONTRIBUTING.md) for 
details.

## 📄 License

[license](https://github.com/qin-work/Benchmate_doc_ccm/blob/main/LICENSE)

