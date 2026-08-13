---
layout: default
title: Installation
nav_order: 2
---

![](assets/installation.png)

# Installation Instructions

`ccm_benchmate` runs on Python 3.12+ and requires PostgreSQL 17+ (with `pgvector` and `rdkit` extensions) for the `KnowledgeBase` and `Project` meta-modules. You can install Benchmate locally via Conda/Pip or deploy using our pre-built Docker containers.

## 1. Installing via Conda (Local Environment)

### Installing Conda

You can follow the instructions [here](https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html) to install Conda or Mamba. If you are installing under HPC, ensure your cache paths (`.cache`, `.conda`, `.singularity`) point to a partition with sufficient storage using environment variables or symbolic links.

### Installing Benchmate

First clone the repository:

```bash
# clone the repository
git clone https://github.com/ccmbioinfo/ccm_benchmate

# enter benchmate directory
cd ccm_benchmate
```

Create the Python 3.12+ Conda environment and install dependencies:

```bash
conda env create -f environment.yaml

conda activate benchmate
```

Install `ccm_benchmate` in editable/package mode:

```bash
pip install -e .
```

### PostgreSQL 17+ Database Setup (For Local Installs)

`benchmate` connects to PostgreSQL 17+. If you are running PostgreSQL locally outside of Docker:

**Start the database server:**

```bash
# initialize the database directory (if empty)
initdb -D <database_dir>

# start the server
pg_ctl -D <database_dir> -l <database_dir>/logfile start
```

**Create database and user:**

```bash
psql -d template1
```

```postgresql
CREATE ROLE benchmate_user WITH LOGIN SUPERUSER PASSWORD 'password'; 
CREATE DATABASE benchmate_db OWNER benchmate_user;
```

**Activate PostgreSQL extensions:**

```postgresql
\c benchmate_db
CREATE EXTENSION IF NOT EXISTS rdkit; 
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## 2. Containerized Deployment (Docker & Singularity)

For an out-of-the-box setup, `ccm_benchmate` provides a 4-target image matrix and container launcher options using Docker Compose and `benchmate.sh`:

- **Container Matrix**:
  - `full`: Complete GPU Python 3.12 stack + PostgreSQL 17+ server (with `pgvector` & `rdkit`)
  - `db-cpu`: CPU-only Python stack + PostgreSQL 17+ server
  - `gpu-nodb`: GPU Python stack without local PostgreSQL
  - `base`: Lightweight CPU stack without PostgreSQL

- **Using Docker Compose**:
  ```bash
  # Spin up the full stack (App + PostgreSQL 17)
  docker compose up -d
  ```

- **Using the Launcher Script (`benchmate.sh`)**:
  ```bash
  ./containerization/benchmate.sh --runtime docker --container rohanahkhan/ccm-benchmate:full --db-dir ./pgdata -- bash
  ```

For full documentation on container deployment, see:
- [Container Overview](containerization/CONTAINER_OVERVIEW.md)
- [Full Docker Image Guide](containerization/DOCKER_IMAGE.md)
- [Container Variants](containerization/DOCKER_VARIANTS.md)
- [Launcher Script Usage](containerization/LAUNCHER_USAGE.md)

---

## 3. Model Selection Note

The default models in `config.yaml` were selected based on performance, accuracy, and VRAM efficiency:
1. **Instruction Following**: Models follow strict structured output rules (e.g., Qwen2.5-VL for vision-language tasks, Qwen3 for embeddings).
2. **VRAM Footprint**: Designed to fit easily within single-GPU setups (<40GB VRAM or high-end consumer GPUs).
3. **Reproducibility**: Uses pinned HuggingFace checkpoints for deterministic inference across environments.
 