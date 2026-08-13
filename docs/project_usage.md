---
layout: default
title: Project Workflow & Usage Examples
nav_order: 14
---

# End-to-End Project Workflow Examples

This guide provides a comprehensive, step-by-step tutorial on how to use the **`Project`** meta-module in `ccm_benchmate`. Unlike standalone module usage, the `Project` class serves as a central orchestrator. It connects to a PostgreSQL database, manages project metadata, processes scientific literature, executes and logs API queries, stores multi-modal biological entities (sequences, molecules, variants), and provides unified search and retrieval interfaces.

---

## 1. Project Overview & Configuration

In this example, we will setup a research project focused on **Nonsense-Mediated mRNA Decay (NMD)** and its core components (such as **UPF1**). 

### Creating the Project Configuration (`config.yaml`)

The project initialization requires a structured `config.yaml` file defining database connections, inference model locations, directory roots, and API parameters.

```yaml
project:
  name: "NMD_Mechanism_Study"
  description: "Nonsense-mediated mRNA decay (NMD) plays a critical role in eukaryotic gene expression and quality control. This project aims to investigate UPF1 regulation, premature termination codon (PTC) recognition mechanisms, structural features of NMD complexes, and potential small molecule inhibitors."
  inclusion:
    - "nonsense-mediated decay"
    - "UPF1"
    - "premature termination codon"
    - "SURF complex"
    - "mRNA degradation"

knowledge_base:
  conn_string: "postgresql://benchmate_user:password@localhost:5432/benchmate_db"

inference:
  device: "cuda"
  interpret_image:
    cache_dir: "./models/hf_models"
    model_name: "Qwen/Qwen2.5-VL-3B-Instruct"
    generation_kwargs:
      max_new_tokens: 150
  embedding:
    cache_dir: "./models/hf_models"
    model_name: "Qwen/Qwen3-Embedding-0.6B"
    dimensions: 2048
  rerank:
    cache_dir: "./models/hf_models"
    model_name: "Qwen/Qwen3-VL-Reranker-2B"
  semantic_chunk:
    cache_dir: "./models/chunking"
    model_name: "celalp/benchmate_m2v_model"
    chunking_kwargs:
      chunk_size: 500
      min_sentences: 5
      threshold: 0.75

literature:
  cache_dir: "./data/paddle"
  pdf_path: "./data/pdfs"
  openalex_api_key: "YOUR_OPENALEX_API_KEY"

alignment:
  folddisco_bin: "folddisco"
  folddisco_db_root: "./data/alignment/folddisco"
  foldseek_bin: "foldseek"
  foldseek_db_root: "./data/alignment/foldseek"
  mmseqs2_bin: "mmseqs"
  mmseqs2_db_root: "./data/alignment/mmseqs"
  blast_bin:
    blastn: "blastn"
    blastp: "blastp"
  blast_db_root: "./data/alignment/blast_db"

apis:
  email: "researcher@example.com"
  biogrid_api_key: ""
  alphagenome_api_key: ""

structure:
  pdb_path: "./data/structure/pdb"

molecule:
  fingerprint_dim: 2048
  fingerprint_radius: 2

sequence:
  fasta_root: "./data/sequence"

genomes:
  genome_path: "./data/genome"
  genomes: {}
```

---

## 2. Initializing the Project & Database

When you instantiate a `Project`, `benchmate` automatically:
1. Connects to PostgreSQL and initializes the schema (`KnowledgeBase`).
2. Registers or retrieves the project entry in the `project` database table.
3. Initializes inference engines and paper processing pipelines.
4. Prepares local project directories for storing PDFs, FASTA files, PDB structures, and alignment indices.

```python
from benchmate.project import Project

# Initialize the Project with our configuration file
project = Project(config_path="config.yaml")

print(project)
# Output:
# Project(name:
# NMD_Mechanism_Study
# 
# project_id:
# 1
# 
# description:
# Nonsense-mediated mRNA decay (NMD) plays a critical role...)
```

---

## 3. Literature Search, Processing, & Knowledge Base Storage

We perform a literature search on PubMed, filter papers based on semantic relevance to our project description, download open-access PDFs, extract full texts and figures, and push the processed papers into our PostgreSQL database.

```python
import time

# 1. Search PubMed for NMD literature using project.litsearch
search_results = project.litsearch.search(
    "nonsense mediated mrna decay UPF1", 
    database="pubmed", 
    max_results=50
)
print(f"Found {len(search_results)} candidate papers.")

# 2. Fetch paper abstracts
papers = []
for paper_id in search_results[:10]:
    p = project.paper(paper_id=paper_id, id_type="pubmed")
    p.get_abstract()
    papers.append(p)
    time.sleep(0.5)

# 3. Calculate semantic relevance scores against the project description
scores = project.paper_processor.text_score(project.description, papers)

relevant_papers = []
for paper, score in zip(papers, scores):
    print(f"Paper ID: {paper.info.id} | Score: {score:.3f} | Title: {paper.info.title[:60]}...")
    if score > 0.50:
        relevant_papers.append(paper)

# 4. Download PDFs for relevant papers
for paper in relevant_papers:
    try:
        paper.search_info()
        if paper.info.download_links:
            paper.download(project.config["literature"]["pdf_path"])
    except Exception as e:
        print(f"Download note for {paper.info.id}: {e}")

# 5. Process paper text, chunking, figures, tables, and embeddings
processed_papers = project.paper_processor.pipeline(
    relevant_papers,
    extract=True,
    embed_text=True,
    embed_images=False,
    interpret_images=True
)

# 6. Store processed papers in the Project Database (KnowledgeBase)
for paper in processed_papers:
    paper_db_id = paper.to_kb()
    print(f"Successfully saved Paper '{paper.info.title[:40]}' to KB with DB ID: {paper_db_id}")
```

---

## 4. Performing API Queries & Logging API Calls

The `project.apis` wrapper enables querying external databases (UniProt, NCBI, Ensembl, StringDB, IntAct) while automatically wrapping queries in `ApiCall` objects and saving them for full reproducibility.

```python
# 1. Search UniProt for UPF1 human protein entries
uniprot_search = project.apis.uniprot.search("human UPF1", page_size=5)
print(f"UniProt Search Hits: {len(uniprot_search)}")

# 2. Retrieve detailed info for Human UPF1 (UniProt ID: Q92900)
upf1_api_call = project.apis.uniprot.get_info("Q92900")

print(upf1_api_call)
# Output: ApiCall @ 2026-08-13 ... with args:('Q92900',), kwargs:{}

# 3. Access key fields from the result dictionary
protein_sequence = upf1_api_call.results["sequence"]
gene_name = upf1_api_call.results["gene"]

# 4. Save the API call to the Knowledge Base for audit trailing and fast retrieval
api_call_db_id = upf1_api_call.to_kb()
print(f"Saved API Call to database with ID: {api_call_db_id}")

# 5. Perform an Ensembl API lookup for the UPF1 gene model
ensembl_call = project.apis.ensembl.get_gene("ENSG00000005001")
ensembl_call.to_kb()
```

---

## 5. Adding Biological Entities (Sequences, Molecules, Variants)

All core biological entities can be constructed using project-bound wrappers (`project.sequence`, `project.molecule`, `project.sequence_variant`, `project.structural_variant`, `project.tandem_repeat_variant`) and uploaded directly to the PostgreSQL database.

### 5.1 Sequences

```python
# Create a protein sequence object for UPF1
upf1_seq = project.sequence(
    config=project.config["sequence"],
    name="Human_UPF1_Isoform1",
    sequence=protein_sequence,
    seq_type="protein",
    annotations={
        "gene": "UPF1",
        "uniprot_id": "Q92900",
        "organism": "Homo sapiens",
        "function": "RNA helicase essential for NMD"
    }
)

# Upload sequence to DB and automatically update local project FASTA index (protein.fa)
upf1_seq_id = upf1_seq.to_kb()
print(f"Saved Sequence to KB with DB ID: {upf1_seq_id}")
```

### 5.2 Molecules (Small Molecules & Inhibitors)

```python
# Create a Molecule object for NMDI-1 (a known Nonsense-Mediated Decay Inhibitor)
nmdi1_smiles = "O=C(Nc1ccc(C=C2C(=O)NC(=O)S2)cc1)c1ccccc1"

nmdi1 = project.molecule(
    config=project.config["molecule"],
    name="NMDI-1",
    smiles=nmdi1_smiles
)

# Compute fingerprint vectors and store in DB
mol_db_id = nmdi1.to_kb()
print(f"Saved Molecule '{nmdi1.info.name}' to KB with DB ID: {mol_db_id}")
```

### 5.3 Genomic Variants

```python
# 1. Sequence Variant (SNV in UPF1 coding region creating a premature stop codon)
seq_var = project.sequence_variant(
    id="UPF1_c.148C>T",
    chrom="chr19",
    pos=18873443,
    ref="C",
    alt="T",
    length=1,
    annotations={
        "gene": "UPF1",
        "consequence": "stop_gained",
        "clinical_significance": "pathogenic"
    }
)
seq_var.to_kb(project)

# 2. Structural Variant (Deletion spanning UPF1 promoter region)
struct_var = project.structural_variant(
    id="UPF1_promoter_del",
    chrom="chr19",
    pos=18870000,
    svlen=-1500,
    cn=1,
    cistart=18869950,
    ciend=18871550,
    annotations={
        "type": "DEL",
        "impact": "HIGH",
        "gene": "UPF1"
    }
)
struct_var.to_kb(project)

# 3. Tandem Repeat Variant
tr_var = project.tandem_repeat_variant(
    id="UPF1_STR_1",
    chrom="chr19",
    pos=18875000,
    al=28,
    annotations={
        "motif": "CAG",
        "gene": "UPF1"
    }
)
tr_var.to_kb(project)

print("Saved sequence, structural, and tandem repeat variants to KB.")
```

---

## 6. Retrieving & Searching Project Data

`ccm_benchmate` provides three primary ways to access stored project data:
1. **Listing overview DataFrames** (`project.list_items`).
2. **Direct object retrieval by DB ID** (`from_kb`).
3. **Multimodal Search Engine** (`project.search.search`).

### 6.1 Listing Items (`list_items`)

You can inspect all entries stored under the active project ID:

```python
# List stored papers
papers_df = project.list_items("paper")
print("--- Stored Papers ---")
print(papers_df[["id", "paper_id", "title"]])

# List stored sequences
seqs_df = project.list_items("sequence")
print("\n--- Stored Sequences ---")
print(seqs_df[["id", "name", "type"]])

# List stored molecules
mols_df = project.list_items("molecule")
print("\n--- Stored Molecules ---")
print(mols_df[["id", "name", "smiles"]])

# List stored API calls
api_calls_df = project.list_items("api_call")
print("\n--- Stored API Calls ---")
print(api_calls_df[["id", "class_name", "method_name"]])
```

### 6.2 Direct Retrieval by Database ID (`from_kb`)

You can reconstruct exact python class instances from database IDs:

```python
# 1. Retrieve Paper from DB
retrieved_paper = project.paper.from_kb(id=paper_db_id)
print(f"Retrieved Paper: {retrieved_paper.info.title}")
print(f"Abstract Snippet: {retrieved_paper.info.abstract[:150]}...")

# 2. Retrieve Sequence from DB
retrieved_seq = project.sequence.from_kb(project, id=upf1_seq_id)
print(f"Retrieved Sequence '{retrieved_seq.info.name}' (Len: {len(retrieved_seq.info.sequence)})")

# 3. Retrieve Molecule from DB
retrieved_mol = project.molecule.from_kb(project, id=mol_db_id)
print(f"Retrieved Molecule '{retrieved_mol.info.name}' InChIKey: {retrieved_mol.info.inchikey}")

# 4. Retrieve Sequence Variant from DB
retrieved_variant = project.sequence_variant.from_kb(project, id="UPF1_c.148C>T")
print(f"Retrieved Variant: {retrieved_variant.id} ({retrieved_variant.chrom}:{retrieved_variant.pos} {retrieved_variant.ref}>{retrieved_variant.alt})")

# 5. Retrieve API Call from DB
retrieved_api_call = project.apis.call_class.from_kb(project, id=api_call_db_id)
print(f"Retrieved API Call: {retrieved_api_call.class_name}.{retrieved_api_call.method_name} queried at {retrieved_api_call.query_time}")
```

---

### 6.3 Using the Unified Project Search Engine (`project.search`)

The `project.search` engine supports keyword, semantic, sequence homology, molecular fingerprint, genomic range, and API call parameter queries.

#### A. Literature Search (Keyword & Semantic Search)

```python
from benchmate.project.search import KeywordSearch, SemanticSearch

# 1. Full-text / Abstract Keyword Search
kw_query = KeywordSearch(positive="decay helicase", negative="plant")
kw_results = project.search.search(
    modality="paper", 
    method="body", 
    query=kw_query, 
    attribute="abstract"
)
print("Keyword Literature Results:", kw_results)

# 2. Vector Semantic Search over body text chunks
sem_query = SemanticSearch(query="mechanisms of SURF complex assembly during premature termination", top_n=5)
sem_results = project.search.search(
    modality="paper", 
    method="body", 
    query=sem_query, 
    inference=project.inference, 
    attribute="full_text"
)
print("Semantic Literature Results:", sem_results)
```

#### B. Sequence Homology Search

Search stored project fasta files using MMseqs2 or Foldseek:

```python
# Perform sequence similarity search against project sequences
seq_search_hits = project.search.search(
    modality="sequence", 
    method="sequence", 
    query=upf1_seq
)
print("Sequence Homology Hits:\n", seq_search_hits)
```

#### C. Molecule Fingerprint Similarity Search (Tanimoto)

Find small molecules similar to a target query molecule using ECFP4 fingerprints:

```python
# Search for chemically similar molecules in the project database
mol_search_hits = project.search.search(
    modality="molecule", 
    method="molecule", 
    query=nmdi1, 
    fp_type="ecfp4", 
    limit=10
)
print("Molecule Tanimoto Similarity Hits:\n", mol_search_hits)
```

#### D. Genomic Range & Variant Search

Find variants falling within a genomic region of interest using `GenomicRange`:

```python
from benchmate.ranges.genomicranges import GenomicRange

# Define genomic region around UPF1 locus (chr19:18,870,000-18,880,000)
upf1_region = GenomicRange(chrom="chr19", start=18870000, end=18880000)

# Query variants within this genomic range across all variant types
range_hits = project.search.search(
    modality="variant", 
    method="range", 
    query=upf1_region
)
print("Variants in UPF1 Region:\n", range_hits)

# Search variants by JSON annotation attributes
anno_variant_hits = project.search.search(
    modality="variant", 
    method="annotations", 
    query={"consequence": "stop_gained"}
)
print("Pathogenic Stop-Gained Variants:\n", anno_variant_hits)
```

#### E. API Call Audit Search

Search stored API calls based on class name, method, or parameters:

```python
# Locate all past UniProt get_info API calls
api_hits = project.search.search(
    modality="apicall", 
    method="calls", 
    call_class="UniProt", 
    class_method="get_info"
)
print("Historical UniProt API Calls:\n", api_hits)
```

---

## 7. Summary

By leveraging the `Project` class:
- All biological data modalities (literature, API logs, DNA/RNA/protein sequences, small molecules, structural variants) are unified under a single relational database schema.
- Data lineage is preserved across queries, inference embeddings, and external API requests.
- Multimodal search allows cross-referencing text, sequences, molecular structures, and genomic coordinates seamlessly.
