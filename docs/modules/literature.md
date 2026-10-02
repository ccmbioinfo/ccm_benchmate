---
layout: default
title: Literature
parent: Modules
nav_order: 3
---

# Literature Module

The **Literature** module handles scientific literature retrieval, open-access manuscript PDF downloading, automated page layout analysis (OCR), semantic text chunking, figure/table extraction, and zero-shot relevance filtering.

---

## User-Facing Methods

### 1. `LitSearch`

Search OpenAlex and PubMed for relevant scientific publications.

- `search(oa, pos_query, pos_joiner="and", neg_query=None, neg_joiner="or", sort_by="relevance", max_results=1000)`: Query OpenAlex API for publication IDs matching positive/negative keyword filters.

---

### 2. `Paper`

Represents an individual publication, managing metadata, text chunks, figures, tables, and PDF processing.

- `get_json()`: Fetch metadata (title, abstract, authors, DOI, citations) from OpenAlex API.
- `parse_json()`: Populate internal `PaperInfo` dataclass from raw API JSON.
- `get_references()`: Retrieve a list of `Paper` instances cited by this publication.
- `get_related_works()`: Retrieve related `Paper` instances suggested by citation graphs.
- `get_cited_by()`: Retrieve `Paper` instances that cite this publication.
- `download(destination)`: Search Unpaywall / open-access sources and download PDF manuscript files.
- `process(extract=True, embed_text=True, embed_images=True)`: Execute full PDF OCR, text chunking, and figure vector embedding.

---

### 3. `PaperProcessor`

Orchestrates multi-modal processing pipelines across lists of `Paper` instances.

- `pipeline(papers, extract=True, embed_text=True, embed_images=True)`: Batch-process PDFs using PaddleOCR layout detection, Model2Vec semantic chunking, and Qwen3-VL figure interpretation.

---

### 4. `PaperRelevance`

Reranks candidate paper abstracts using vision-language / cross-encoder models.

- `__call__(abstracts)`: Evaluate abstract texts against project description and inclusion criteria, returning logit relevance scores.

---

## End-to-End Workflow Example

```python
from benchmate.literature import LitSearch, OpenAlex, Paper, PaperProcessor, PaperRelevance
from benchmate.inference import Inference

# 1. Search OpenAlex for candidate papers
oa = OpenAlex(api_key="<your_openalex_api_key>")
searcher = LitSearch()

paper_ids = searcher.search(
    oa=oa, 
    pos_query=["CRISPR", "base editing", "off-target"], 
    pos_joiner="and", 
    sort_by="relevance", 
    max_results=50
)

# 2. Collect metadata & Download open-access PDFs
papers = []
for pid in paper_ids[:10]:
    p = Paper(paper_id=pid)
    p.get_json()
    p.parse_json()
    p.download(destination="./pdf_downloads")
    papers.append(p)

# 3. Filter papers by project relevance
inf = Inference(config=inference_config)
relevance_eval = PaperRelevance(
    description="Study of precision genome editing and off-target evaluation methods",
    inclusion_criteria=["base editing", "CRISPR-Cas9", "off-target profiling"],
    inference=inf
)

abstracts = [p.info.abstract for p in papers if p.info.abstract]
scores = relevance_eval(abstracts)

# 4. Process PDFs (OCR, Chunking, Figure/Table Embeddings)
processor = PaperProcessor(config=literature_config)
processed_papers = processor.pipeline(papers, extract=True, embed_text=True, embed_images=True)
```

## PaperInfo dataclass

All the information about the papers are stored in a paperinfo class. The main fields of the class looks like this:

```python
@dataclass(slots=True)
class PaperInfo:
    """
    Dataclass to hold information about a paper, this is constructed inside the Paper class and desined to be compatible with
    semantic search and embedding distance searches
    """
    # in papers table
    id: str
    external_ids: Optional[dict] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    abstract_embeddings: Optional[np.ndarray] = None
    download_links: Optional[list] = None
    file_paths: Optional[list] = None
    full_json: Optional[dict] = None
    authors: Optional[list] = None
    publication_date: Optional[str] = None
    venue: Optional[str] = None
    text: Optional[str] = None
    text_chunks: Optional[list] = None
    chunk_embeddings: Optional[np.ndarray] = None
    figures: Optional[list] = None
    figure_embeddings: Optional[np.ndarray] = None
    tables: Optional[list] = None
    table_embeddings: Optional[np.ndarray] = None
    references: Optional[list] = None
    related_works: Optional[list] = None
    cited_by: Optional[list] = None
```

The first bunch of them are filled in when you call `paper.get_json()` and `paper.parse_json()`. If there are
available pdfs and you call `paper.download()` you will also get the `file_paths` attribute filled in. 

All the attributes that relate to the main body of the paper come then you the `PaperProcessor` class instance
with appropriate settings. Figures and tables are treated as images and are extracted with the `extract` method or if you
set `extract=True` in the `pipeline` method. Interpretations, embeddings of figures and tables need to be specified in the 
`pipeline` method to be filled in. 


