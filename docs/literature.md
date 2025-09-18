---
layout: default
title: Literature Module
nav_order: 5
---

# Literature Module

A module for searching and processing scientific literature from PubMed and arXiv, with functionality to download papers, 
extract content, and analyze metadata. There are various methods to extract information from papers. Currently we are 
reliant on the [OpenAlex](https://openalex.org/) API for paper metadata. I would love to be able to use Pubmed API but currently
I cannot get an API key. 

## Classes Overview

- `LitSearch`: Search for papers across scientific databases
- `Paper`: Download and process individual papers, extracting text, figures, and tables

## LitSearch

The `LitSearch` class provides methods to search PubMed and arXiv databases.

### Usage

```python
from benchmate.literature.literature import LitSearch

# Initialize searcher (optional PubMed API key)
searcher = LitSearch(pubmed_api_key="your_api_key")  # API key optional

# Search PubMed
pubmed_ids = searcher.search(
    query="BRCA1 breast cancer",
    database="pubmed",
    results="id",     # Return PMIDs
    max_results=1000  # Max number of results to return
)

# Search with DOIs
dois = searcher.search(
    query="BRCA1 breast cancer", 
    database="pubmed",
    results="doi"     # Return DOIs instead of PMIDs
)

# Search arXiv
arxiv_ids = searcher.search(
    query="machine learning genomics",
    database="arxiv"
)
```

This search only returns the paper ids. You can sort your results by relevance or publication date. For other
more advanced search you can pass them as free text into the query parameter.


## Paper

The `Paper` class handles downloading and processing individual papers. All the paper information is stored in a 
python `dataclass` under the paper.info attribute.

### Usage

```python
from benchmate.literature.literature import Paper

# Initialize from PubMed ID
paper = Paper(
    paper_id="12345678",
    id_type="pubmed",
    citations=True,      # Get citation data
    references=True,     # Get reference data
    related_works=True   # Get related papers
)

# Initialize from arXiv ID 
paper = Paper(
    paper_id="2101.12345",
    id_type="arxiv"
)

# Initialize from local PDF file
paper = Paper(
    paper_id=None,
    filepath="/path/to/paper.pdf"
)

# If you use an arxiv or pubmed id the abstract and the paper title will be automatically extracted
print(paper.info.title)
print(paper.info.abstract)

# you can additional information about the paper via openalex

paper.search_info()
paper.get_references()
paper.get_cited_by()
paper.get_related_works()
```

These methods will modify the paper class in place. The `paper_info` dataclass stores all the relevant information about the paper.
about the paper. Openalex provides a lot of information, including whether a paper is available via open access. If this is the
case there will be a link to the PDF that is stored in the `paper.info.pdf_link` attribute.

To download the PDF to a location of your choice, you can use the `download_pdf` method.

```python
paper.download(destination="/path/to/destination")
```

After the PDF is downloaded you can process the paper using the `process` method. This will extract the full text, figures,
and tables from the PDF. The PDF is processed page by page and the text is extracted using tessaract. The figures and tables
are converted to `pillow.PIL.Image` objects. These images are then interpreted individually using a vision language model to
provide free text context. 

The embeddings for the whole abstract are generated a model of your choosing. The whole text of the paper is 
semantically chunked into different bits, and these are also passed to the embedding model. The embeddings for the 
images and their VL model interpretations are also generated. This provides very extensive processing of the paper for 
a lot of different search and comparison options. These will be used in the [knowledgebase](knowledgebase.md) module.

all of this can be done in one line of code.
```python
paper.process(filepath="/path/to/paper.pdf", embed_images=True, embed_text=True, 
              embed_interatations=True, **kwargs)
```

Keep in mind that all you need is an id and where that id comes from (Pubmed or arxiv). Any of the ids that 
are returned from the APIs module are immediately usable as a paper class instance. 

Additionally, references, cited_by, and related works themselves are also a simple list of paper class instances. All 
the methods above can be used on these lists as well.

## Next Steps

Within the `literature.utils` module there are a couple of functions to determine whether a paper is 
relevant to a given project. These will likely move to the project [module](project.md) in the future.
The process function is very computationally expensive this means we want to be conservative about which papers we
process. We will be providing more instructions and documentation about this in the project metaclass documentation. 