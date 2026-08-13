---
layout: default
title: Knowledge Base
parent: Modules
nav_order: 12
---

# Knowledge Base Module

The **Knowledge Base** (`KnowledgeBase`) is the relational and vector database abstraction layer for `ccm_benchmate`. Built on PostgreSQL 17+, it leverages `pgvector` for high-dimensional vector embeddings (literature text chunks, figures, tables) and `rdkit` for small molecule structure indices and fingerprint similarity.

The database tables are organized around the central `project` table, associating stored entities with a specific project ID. 

Usually, end users do not query `KnowledgeBase` directly, but interact with it seamlessly through the [`Project`](project.md) meta-module and `project.search`. For step-by-step examples of storing and querying entities in the Knowledge Base, see [Project Workflow Examples](../project_usage.md).

Below is the relational database schema:

![Database Schema](../assets/kb_schema.png)

## Database Extensions & Requirements:

- **PostgreSQL**: Version 17+
- **`pgvector` Extension**: Enables `<->` vector similarity operations for literature embeddings.
- **`rdkit` Extension**: Enables chemical SMILES indexing and Tanimoto similarity operations.

## Note for Developers:

The KnowledgeBase layer abstracts SQLAlchemy table creation (`_create_kb`) and session management for the [`Project`](project.md) module. Direct interaction is managed via `project.sequence.to_kb()`, `project.paper.to_kb()`, `project.molecule.to_kb()`, `project.apis.call_class.to_kb()`, and `project.sequence_variant.to_kb()`. 