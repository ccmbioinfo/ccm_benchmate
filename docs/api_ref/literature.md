---
layout: default
title: Literature
parent: API Reference
nav_order: 2
---

<a id="benchmate.literature"></a>

# benchmate.literature

<a id="benchmate.literature.paperinfo"></a>

# benchmate.literature.paperinfo

<a id="benchmate.literature.paperinfo.PaperInfo"></a>

## PaperInfo Objects

```python
@dataclass(slots=True)
class PaperInfo()
```

Dataclass to hold information about a paper, this is constructed inside the Paper class and desined to be compatible with
semantic search and embedding distance searches

<a id="benchmate.literature.literature"></a>

# benchmate.literature.literature

<a id="benchmate.literature.literature.paper_from_response"></a>

#### paper\_from\_response

```python
def paper_from_response(response,
                        get_references=False,
                        get_related_papers=False,
                        get_cited_by=False)
```

take an openalex response and convert that to a paper object

**Arguments**:

- `response`: response json
- `get_references`: whether to return references or not
- `get_related_papers`: whether to return related papers or not
- `get_cited_by`: whether to return cited papers or not

**Returns**:

paper object

<a id="benchmate.literature.literature.paper_from_id"></a>

#### paper\_from\_id

```python
def paper_from_id(openalex,
                  id,
                  id_type,
                  get_references=False,
                  get_related_papers=False,
                  get_cited_by=False)
```

for an id type (instead of openalex id) this function will return a paper object, this can be useful when you are trying to

collect information from other sources like a uniprot api call

**Arguments**:

- `openalex`: openalex
- `id`: the actual id
- `id_type`: type of the id, pmid, full doi url, pmcid or magid
- `get_references`: as the name suggests
- `get_related_papers`: as the name suggests
- `get_cited_by`: as the name suggests

**Returns**:

a paper object instance, this call paper_from_response under the hood

<a id="benchmate.literature.literature.paper_from_link"></a>

#### paper\_from\_link

```python
def paper_from_link(link,
                    openalex,
                    get_references=False,
                    get_related_papers=False,
                    get_cited_by=False)
```

generate a paper object from an openalex link, this is useful for references and related works

**Arguments**:

- `link`: openalex link

**Returns**:

a paper object

<a id="benchmate.literature.literature.OpenAlex"></a>

## OpenAlex Objects

```python
@dataclass
class OpenAlex()
```

just storing basic information about openalex, this includes the link and yourj api key

<a id="benchmate.literature.literature.LitSearch"></a>

## LitSearch Objects

```python
class LitSearch()
```

<a id="benchmate.literature.literature.LitSearch.search"></a>

#### search

```python
def search(openalex,
           pos_query,
           pos_joiner="and",
           neg_query=None,
           neg_joiner="or",
           fields=["title", "abstract", "doi", "publication_date", "venue"],
           sort_by="relevance",
           max_results=10000)
```

search pubmed and arxiv for a query, this is just keyword search no other params are implemented at the moment

**Arguments**:

- `query`: this is a string that is passed to the search, as long as it is a valid query it will work and other fields can be specified
- `database`: pubmed or arxiv
- `results`: what to return, default is paper id PMID and arxiv id
- `max_results`: max number of results to return default 1000

**Returns**:

paper ids specific to the database

<a id="benchmate.literature.literature.Paper"></a>

## Paper Objects

```python
class Paper()
```

<a id="benchmate.literature.literature.Paper.__init__"></a>

#### \_\_init\_\_

```python
def __init__(paper_id)
```

This class is used to download and process a paper from a given id, it can also be used to process a paper from a file

**Arguments**:

- `paper_id`: openalex id of the paper

<a id="benchmate.literature.literature.Paper.get_json"></a>

#### get\_json

```python
def get_json(openalex)
```

for a given paper id query openalex api and get the detailed information

**Arguments**:

- `openalex`: openalex instance, see above

**Returns**:

json from openalex

<a id="benchmate.literature.literature.Paper.parse_json"></a>

#### parse\_json

```python
def parse_json()
```

parse the json and extract the most useful information into separate fields

**Returns**:

paper.info instance filled in for the attrs that are defined explicitly

<a id="benchmate.literature.literature.Paper.download"></a>

#### download

```python
def download(destination)
```

download the paper pdf to the destination folder

**Arguments**:

- `destination`: where to download the paper, it must exist, the folder will not be created or checked for existence

**Returns**:

download the paper pdf to the destination folder

<a id="benchmate.literature.literature.Paper.get_references"></a>

#### get\_references

```python
def get_references(openalex)
```

get the references of the paper from openalex

**Returns**:

fill in the paper info references

<a id="benchmate.literature.literature.Paper.get_related_works"></a>

#### get\_related\_works

```python
def get_related_works(openalex)
```

get the related works of the paper from openalex

**Returns**:

fill in the paper info related_works

<a id="benchmate.literature.literature.Paper.get_cited_by"></a>

#### get\_cited\_by

```python
def get_cited_by(openalex)
```

get the papers that cite this paper from openalex

**Arguments**:

- `cursor`: the used does not need to worry about this, it is used for pagination and recursive calls

**Returns**:

fill in the paper info cited_by

<a id="benchmate.literature.literature.Paper.process"></a>

#### process

```python
def process(processor, extract=True, embed_text=True, embed_images=True)
```

run the paper processor pipeline

**Arguments**:

- `processor`: processor class instance
- `extract`: extract text, figures and tables from the pdf
- `embed_text`: chunk and embed the paper text
- `embed_images`: embed figures and tables

**Returns**:

filled in paper info, doesnt return anything but fills inplace

<a id="benchmate.literature.paper_processor"></a>

# benchmate.literature.paper\_processor

<a id="benchmate.literature.paper_processor.PaperProcessor"></a>

## PaperProcessor Objects

```python
class PaperProcessor()
```

<a id="benchmate.literature.paper_processor.PaperProcessor.__init__"></a>

#### \_\_init\_\_

```python
def __init__(inference, cache_dir=None, device="gpu")
```

Init PaperProcessor, this will prepare and download the models if this is the first time you are using it. Make sure that

the cache directory exists and is consistent between run otherwise you will end up with multiple copies of the same models

**Arguments**:

- `inference`: benchmate.inference.inference instance for embedding
- `cache_dir`: cache dir for storing models, this exclusively for paddle ocr models
- `device`: gpu or cpu, not sure if you are ever going to run them on a tpu but that's also supported

<a id="benchmate.literature.paper_processor.PaperProcessor.pipeline"></a>

#### pipeline

```python
def pipeline(papers, extract=True, embed_text=True, embed_images=True)
```

run the full paper processing pipeline

**Arguments**:

- `papers`: list of paper class instance
- `extract`: perform the steps in parse
- `embed_text`: semantically chunk and embed the chunks for the full text
- `embed_images`: embed the image and their associated text all in one go using a vl model

**Returns**:

doesnt return anything but fills in the attributes of the paper instances provided
One thing to note here, if a paper instance has multiple files, it will go through them one by one and perform
all the actions, there is no check for file order, sometimes the main paper is the first one sometimes not, this
is especially true if we are downloading the tar file from ncbi, if there is a single oa location in openalex that one is
preffered.

<a id="benchmate.literature.utils"></a>

# benchmate.literature.utils

<a id="benchmate.literature.utils.PaperRelevance"></a>

## PaperRelevance Objects

```python
class PaperRelevance()
```

<a id="benchmate.literature.utils.PaperRelevance.__call__"></a>

#### \_\_call\_\_

```python
def __call__(abstracts, split_n=1, **kneedle_kwargs)
```

Score all abstracts through semantic + rerank stages.

**Arguments**:

- `abstracts`: list of abstract strings, arbitrary order
- `use_elbow`: if True, use kneedle for both stage cutoffs; if False, use top_k_semantic/top_k_rerank
- `kneedle_kwargs`: passed through to KneeLocator if use_elbow=True

**Returns**:

(combined_scores, combined_threshold)
combined_scores: list aligned to input abstracts order, 0.0 for non-survivors of stage 1
combined_threshold: minimum combined score to be considered relevant

<a id="benchmate.literature.utils.reconstruct_abstract"></a>

#### reconstruct\_abstract

```python
def reconstruct_abstract(inverted_index)
```

reconstruct the abstract of the paper because openalex only returns an inverted index

**Arguments**:

- `inverted_index`: 

<a id="benchmate.literature.utils.extract_pdfs_from_tar"></a>

#### extract\_pdfs\_from\_tar

```python
def extract_pdfs_from_tar(file, destination, base_name)
```

extract all pdf files from a tar.gz file to a destination folder and return the paths to the extracted pdf files

this is there to process pmc tar.gz files

**Arguments**:

- `file`: downloaded tar.gz file
- `destination`: where to extract the pdf files

**Returns**:

a list of paths to the extracted pdf files

<a id="benchmate.literature.utils.download_tar"></a>

#### download\_tar

```python
def download_tar(download_link, file)
```

download the pmc tar file to destination file

**Arguments**:

- `download_link`: web link to download tar file
- `file`: file to write the tar file into

**Returns**:

write/download tar file to file

