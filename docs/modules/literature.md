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
from benchmate.literature import LitSearch, OpenAlex, Paper

oa=OpenAlex(api_key="your api key")

# Initialize searcher (optional PubMed API key)
searcher = LitSearch()
ids=searcher.search(oa, pos_query="something you are interested in")
```
There are a few options in the search function. Below are their descriptions

+ pos_query: list of keywords that you want
+ pos_joiner: "and" or "or" depending on how you want to search
+ neg_query: list of things you don't want
+ neg_joiner: same as above
+ sort_by: relevance, publication_date, cited_by_count
+ max_results: max 10K, seems sufficient

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

The embeddings for the figures are generated using both the image of the figure and the caption, and for tables we have the 
image of the table and the extracted content. 

To start the processor class instance you will need a pdf and an inference class instance. 

```python
import yaml #you can create this manually if you want
from benchmate.inference import Inference
from benchmate.literature import PaperProcessor

with open("config.yaml") as f: #see benchmate/config.yaml for an example for all the fields
    params=yaml.safe_load(f)

inference=Inference(config=params["inference"])
processor=PaperProcessor(params["literature"])
```

While there are individual methods you can just use the `pipeline` method to specify what you need accomplished. 

```python
papers=["A list of paper class instances"]

papers=processor.pipeline(papers, extract=True, embed_text=True, embed_images=True)
```

The other option is to use the process method that takes the same arguments. 

```python
paper.process( extract=True, embed_text=True, embed_images=True)
```

As the names suggest, the class goes through every paper in the list one by one and applies each function
one by one in the order above. Each method is performed for each paper before moving on to the next. This way 
we minimize the amount of VRAM used. 

### A word of caution on pdf processing

We made every effort to make this a reasonable process in terms of resource requirements, however  some papers have figures
that may have obsecenly high number of figures and/or tables and this may result in higher requirements. 

Additionally, if the open access paper is downloaded from pmc it may come with additional files, **only** pdfs will get processed
and **every** pdf will get processed in no particular order. We do not have a reliable way of determinig which pdf is the main 
paper and which one is the supplemental. If you do, please create a pull request. 

## Filtering irrelevant stuff

Any keyword search will return *a lot of* irrelevant papers. To get rid of the unwanted ones before we invest in 
processing them as we have seen above we can use the `PaperRelevance` class. There are a few ways you can use this to 
determine if a paper is relevant but the basic workflow is as follows:

1. Include a project description, this should be at least a generous paragraph but less than 10 pages. 
2. an inclusion criteria, a list of keywords that must be there semantically (i.e. cancer would work for leukemia)
3. Whether you want a max number of papers or dynamically determine the relevan papers using an elbow treshold, there are
pros and cons to each
    + For fixed number of papers you might over or undershoot
    + For elbow threshold there might not be a specific elbow for the relevance scores (see below), if the decrease in 
   relevance scores is constant the method might fail and return all or none of the papers. 

You can specify a semantic hard threshold and reranker dynamic (elbow) threshold and vice versa

```python
from benchmate.literature import PaperRelevance
from benchmate.inference import Inference

inf=Inference(config=<config_dict>)

pr=PaperRelevance(description="project description", 
                  inclusion_criteria=["list", "of", "strings"], 
                  inference=inf, 
                  top_k_semantic= 1000, #get the top 1K papers
                  top_k_rerank=None #use elbow method
                  )

```

After the intialization you can just call the class on a list of abstracts. 

```python
abstracts=[]

for p in papers:
    abstracts.append(p.info.abstract)

scores=pr(abstracts)
```

For items that do not pass the hard tresholds the score will be 0 for both re-ranker and semantic seearches, since re-rankers
work on logit scale at the very least selecting positive scores is a safe bet. 

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


