---
layout: default
title: Literature
parent: Modules
nav_order: 3
---

## Literature module

This module includes classes and methods to search for literature, gather information about papers, 
download open access pdfs, process them automatically to generate searchable python objects for text,
figures and tables. Below is some basic usage from start to finish.

### LitSearch

The `LitSearch` class provides methods to search [openalex](https://openalex.org/). This resource is
free but you will need to create an api key. It has quite generous api query allowance per day and stores a lot
of information. It automatically indexes pubmed, arxiv and so much more. I have opted for this resource 
as opposed to [semanticscholar](https://www.semanticscholar.org/) because of its generous api allowance and the ease with which you can get 
an api key. 

#### Usage

```python
from benchmate.literature.literature import LitSearch, OpenAlex

oa=OpenAlex(api_key="your api key")

# Initialize searcher (optional PubMed API key)
searcher = LitSearch()
ids=searcher.search(oa, query="something you are interested in")
```


This search only returns the paper ids. You can sort your results by relevance, publication date or number of papers that cite it.

After searching for papers you can get the information for each of them like so:

## Collecting information about papers

```python
for id in ids:
    p=Paper(paper_id=id)
    p.get_json() # get a lot of information about the paper including title, abstract, authors, references
    p.parse_json() # parse the data for the paperinfo class (see below)
    p.get_references() # create another set of paper class instances for each reference
    p.get_related_works() # as the name suggests
    p.get_cited_by() # same as above, this of course is time dependent and you might get different results 3 months later
    p.download(destination="where_you_want_your_pdfs") # if the paper is open access benchmate will aggressively try to find it and download pdf to desintation
```

On any given day you can query 100s of thousands of papers and get their information for free from openalex. If you are lucky
you will get quite a few pdfs as well. Next we will extract more information about them. 


## Processing pdfs

For all the papers that we have downloaded we can do the following:

+ Extracting text, figures and tables from a pdf
+ Semantically chunking the text
+ Generating embeddings for these chunks
+ Generating embeddings for the figures and tables (they are stored as images)
+ Generating interpretaions for figures and tables

The main reason for the last item is, because figure and table captions in papers come in many shapes and sizes. Sometimes
they are not even in the same page. The preparation of the pages also depends heavily from publisher to publisher and being
extremely flexible pdf files can contain all sorts of information about the content or none at all. Therefore it is more reliable
to create captions then to actually find them in the pdf. That said the text extraction method can and does capture all the text
this includes the figure and table captions. 

To start the processor class instance you will need a pdf and an inference class instance. 

```python
import yaml #you can create this manually if you want
from benchmate.inference.inference import Inference
from benchmate.literature.paper_processor import PaperProcessor

with open("config.yaml") as f: #see benchmate/config.yaml for an example for all the fields
    params=yaml.safe_load(f)

inference=Inference(config=params["inference"])
processor=PaperProcessor(params["literature"])
```

While there are individual methods you can just use the `pipeline` method to specify what you need accomplished. 

```python
papers=["A list of paper class instances"]

papers=processor.pipeline(papers, extract=True, embed_text=True, embed_images=True,
                            interpret_images=True)

```

As the names suggest, the class goes through every paper in the list one by one and applies each function
one by one in the order above. Each method is performed for each paper before moving on to the next. This way 
we minimize the amount of VRAM used. 

## Filtering irrelevant stuff

Any keyword search will return *a lot of* irrelevant papers. To get rid of the unwanted ones before we invest in 
processing them as we have seen above we can use 2 separate methods. There are pros and cons to each of them. 

### Using text score

This one is rather simple for a project description (a decent sized paragraph) we will chunk the descrption semantically
and do the same to each of the abstracts that we have collected. If there are no abstracts (rare but happens) we will just the
title. 

```python
project_description="a detailed description of what you are interested in"

scores=[]
for paper in papers:
    scores.append(inference.text_score(project_description, paper.info.abstract))
```
A score of 1 means that they project description and the abstract (or title) are indentical and 0 means they have 
nothing in common. A score > 0.55 is generally a safe bet. 

### Using a re-ranking model

While the above method is simple and effective it might miss some nuance. If you have the gpu you can use a more 
sophisticated approach using a re-ranking model. This will use a much heavier model but it will also be more sensitive
to subtle differences. It if of course possible to combine the two where you use the first method to get rid of obviously
irrelevant things and then use the second method to make sure. 

```python
to_rank=[]
for paper in papers:
    if paper.info.abstract is None:
        to_rank.append(paper.info.title)
    else:
        to_rank.append(paper.info.abstract)

scores=inference.rerank(project_description, to_rank)
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
    figure_interpretation: Optional[list] = None
    figure_interpretation_embeddings: Optional[np.ndarray] = None
    tables: Optional[list] = None
    table_embeddings: Optional[np.ndarray] = None
    table_interpretation: Optional[list] = None
    table_interpretation_embeddings: Optional[np.ndarray] = None
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


