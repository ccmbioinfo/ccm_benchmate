---
layout: default
title: Modules
has_children: true
nav_order: 2
---


# Benchmate Modules

This is the documentation for usage instructions for all modules in the `ccm_benchmate` package. For a technical API reference, please see the [API Reference](../api_ref/index.md).

Modules can be used independently or unified under the `Project` meta-module:

- **[APIs](apis/index.md)**: Public biological database query clients (UniProt, NCBI, Ensembl, StringDB, IntAct, etc.).
- **[Literature](literature.md)**: Paper search, PDF parsing, chunking, and vision-language figure/table interpretation.
- **[Sequence](sequence.md)**: Representation and mutation of DNA, RNA, protein, and 3Di sequences.
- **[Structure](structure.md)**: PDB and AlphaFold 3D structure handling.
- **[Molecule](molecule.md)**: Small molecule handling with RDKit SMILES parsing and ECFP4/FCFP4 fingerprints.
- **[Genome](genome.md)**: Genomic feature annotation and sequence retrieval.
- **[Alignment](alignment.md)**: High-speed sequence and structure homology searches (BLAST, MMseqs2, Foldseek, Folddisco).
- **[Ranges](ranges.md)**: Genomic interval operations.
- **[Variant](variant.md)**: Sequence, structural, and tandem repeat variant models.
- **[KnowledgeBase](knowledge_base.md)**: PostgreSQL (17+) schema management with `pgvector` and `rdkit`.
- **[Project](project.md)**: Meta-module unifying database creation, entity persistence (`to_kb`), item listing (`list_items`), exact object retrieval (`from_kb`), and multimodal search (`project.search`).

For a complete tutorial combining all modules into an integrated workflow, see [Project Workflow & Usage Examples](../project_usage.md).

## Configuration

Benchmate relies on AI models specified in `config.yaml`. The default models (e.g. Qwen vision-language and embedding models) are selected to ensure accuracy while operating within standard single-GPU VRAM limits (<40GB). 