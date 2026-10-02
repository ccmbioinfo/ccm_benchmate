---
layout: default
title: Inference
parent: Modules
nav_order: 11
---

# Inference Module

The **Inference** module manages machine learning pipelines and local model executions across the Benchmate framework. It abstracts multi-modal text embedding, cross-encoder re-ranking, vision-language figure interpretation, semantic chunking, and structured metadata extraction behind a clean unified API.

---

## User-Facing Methods

- `Inference(config)`: Instantiate the inference orchestrator using the `inference` block from your `config.yaml` or configuration dictionary.
- `gather_models(task="all")`: Download and cache required HuggingFace and PaddleOCR model weights locally to avoid runtime downloads.
- `embed(texts)`: Generate dense vector embeddings for text chunks or queries using `Qwen3-VL-Embedding-2B` (or configured embedding model).
- `rerank(query, candidates)`: Score candidate text/figure documents against a search query using cross-attention re-ranking with `Qwen3-VL-Reranker-2B`.
- `chunk_text(text)`: Perform fast semantic text chunking via Model2Vec (`snowflake-arctic-embed-l-v2.0` distilled model).
- `interpret_image(image_path, prompt)`: Generate structured textual descriptions or figure/table captions from images using `Qwen3-VL-2B-Instruct`.
- `text_score(text1, text2)`: Calculate semantic similarity score between two text strings.

---

## Model Pipeline Architecture

| Task | Default Model | Description |
| :--- | :--- | :--- |
| **Layout & OCR** | PaddleOCR | Detects page boundaries, figures, and tables from PDFs |
| **Semantic Chunking** | Model2Vec (`snowflake-arctic-embed-l-v2.0`) | High-speed sentence-boundary chunking (1024 dims) |
| **Embedding** | `Qwen/Qwen3-VL-Embedding-2B` | Multimodal dense vector encoding for text & images |
| **Re-Ranking** | `Qwen/Qwen3-VL-Reranker-2B` | Cross-encoder relevance scoring for retrieval |
| **Image Interpretation**| `Qwen/Qwen3-VL-2B-Instruct` | Vision-language captioning for unlabeled figures/tables |
| **Structured Extraction**| `google/medgemma-4b-it` | Zero-shot JSON extraction for literature abstracts |

---

## Basic Usage Example

```python
import yaml
from benchmate.inference import Inference

# Load configuration
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# Instantiate inference manager
inf = Inference(config=config["inference"])

# Pre-download / cache all model weights locally
inf.gather_models()

# 1. Generate text embeddings
embeddings = inf.embed(["Protein-protein interaction network", "Cellular pathway analysis"])

# 2. Semantic text chunking
chunks = inf.chunk_text("Long scientific text passage describing experimental procedures...")

# 3. Interpret figure/table image
caption = inf.interpret_image(
    image_path="path/to/figure1.png",
    prompt="Describe the key biological findings and axes of this plot."
)

# 4. Re-rank retrieval candidates
candidates = ["Paper A abstract...", "Paper B abstract...", "Paper C abstract..."]
scores = inf.rerank(query="CRISPR gene editing efficiency", candidates=candidates)
```