---
layout: default
title: Project Meta Module
parent: Modules
nav_order: 11
---

# Project Module

This module is meant to collect all the modalities discussed previously. You can store them in a postgresql database
and retieve them as needed. The goal is to give the user the ability to unleash benchmate in an autmated fashion to 
collect and curate to be queried at a later date. 

## Creating a new project

In the [installation](../installation.md) instructions we mentioned that you need to be able to install and use a 
postgresql database. This means you will need necessary priviliges and folder rights in a system. This does not have to be 
the same location that you run benchmate code. Any database server that you can connect from the location of your choosing will do

The benchmate config yaml describes how a project is set up and we will go through these in detail before we delve into 
how you can use the project instance. 

### Config file

There are many sections of the config file and those are described here. 

**Project Section**

The project is not your database, you can store multiple projects in the same database server. 

```yaml
project:
  name: benchmate
  description: "This is a description of the project with as many biological details as possible to help search algorithms 
  especially in the literature to filter out irrelevant results. This should be at the very least a decent sized paragraph but 
  not 100s pages of text. Currently there is no support for images or tables in (unless formatted as markdown) to be used in 
  project descriptions."
  inclusion: ["This is a", "dense list of things", "you want in the project", "it will be used to filter", "out papers and maybe api calls"]


```

As we discussed in the [literature](literature.md) section the prjoject description and the inclusion criteria is used
for determining if a publication is relevan for our project or not. We are working on applying this to api calls as well but that 
currently not implemented. 

**Knowledge Base**

There is not much going on here its just a string that you will use to call `sqlalchemy.create_engine`. You do not need to 
speficy this string here, you can load the config as a dict and then add the necessary key:value pair after the fact, as long 
as the it's in the correct place it does not matter. 

**Inference**

```yaml
inference:
  device: cuda

  interpret_image: #this is the model that is used to interpret figures
    cache_dir: /hpf/largeprojects/ccmbio/acelik_files/ccm_benchmate/benchmate/models/hf_models
    model_name: Qwen/Qwen3-VL-2B-Instruct
    model_kwargs: null
    processor_kwargs: null
    model_class: Qwen3VLForConditionalGeneration
    processor_class: AutoProcessor
    generation_kwargs:
      max_new_tokens: 100 # other generation kwargs that you want to pass in, this is passed to model.generate
    quantization_kwargs: null # if you want to use bitsandbytes quantization you can pass it here, see below for an example

  embedding: #this is the model that is used to embed the text
    cache_dir: /hpf/largeprojects/ccmbio/acelik_files/ccm_benchmate/benchmate/models/hf_models
    model_name: Qwen/Qwen3-VL-Embedding-2B
    model_kwargs: null
    processor_kwargs: null
    prompt: "Represent this scientific document for retrieval, focusing on methodology, data, and technical scientific meaning."
    quantization_kwargs:
      load_in_4bit: true
      bnb_4bit_quant_type: nf4
      bnb_4bit_use_double_quant: true
    dimensions: 2048

  rerank:
    cache_dir: /hpf/largeprojects/ccmbio/acelik_files/ccm_benchmate/benchmate/models/hf_models
    model_name: Qwen/Qwen3-VL-Reranker-2B
    model_kwargs: null
    processor_kwargs: null
    quantization_kwargs:
      load_in_4bit: true
      bnb_4bit_quant_type: nf4
      bnb_4bit_use_double_quant: true
    prompt: "
    You are a scientific reranking model.
    Evaluate how relevant the candidate is to the query.
    Consider:
      - Exact match of scientific concept, method, or finding
      - Correct interpretation of figures or tables if present
      - Alignment of key variables and outcomes

    Penalize:
      - Partial matches
      - Different experimental setups
      - Superficial keyword overlap

    Query:
      {query}

    Candidate:
      {candidate}
"
  semantic_chunk:
    cache_dir: /hpf/largeprojects/ccmbio/acelik_files/ccm_benchmate/benchmate/models/chunking
    model_name: celalp/benchmate_m2v_model
    chunking_kwargs:
      chunk_size: 500
      min_sentences: 5
      threshold: 0.75

  extract_info:
    cache_dir: /hpf/largeprojects/ccmbio/acelik_files/ccm_benchmate/benchmate/models/hf_models/
    model_name: google/medgemma-4b-it #4b even though it's not text only trying to keep things small
    model_class: AutoModelForCausalLM
    model_kwargs: null
    tokenizer_kwargs: null
    quantization_kwargs:
      load_in_4bit: true
      bnb_4bit_quant_type: nf4
      bnb_4bit_use_double_quant: true
    generation_kwargs:
       max_new_tokens: 250
    sys_prompt: "You are an expert scientist whose sole function is to extract structured information from CV text and return it as valid JSON.

    ## Output Rules
    - Return ONLY valid JSON. No prose, no markdown, no preamble, no code fences.
    - If a field is not found, use null for scalar values and [] for arrays.
    - Never hallucinate, infer, or embellish any information not explicitly present in the text.
    
    ## Formatting Rules
    - Normalize whitespace: strip leading/trailing spaces, collapse internal multiple spaces.
    - Preserve original casing for proper nouns
    - Return all arrays in the order they appear in the source text."

  layout_model: #this needs to match (the location) litertature above
    model: celalp/benchmate_layout
    cache_dir: /hpf/largeprojects/ccmbio/acelik_files/ccm_benchmate/benchmate/models/lp_model
```

This one collects all the model paths, params and prompts that are used in inference. We have already gone through how to use 
inference, you will just need to pass this section to the inference class `__init__` method and you can use the class

We tried to keep this as flexible as possible but there are some drawbacks to this approach. First benchmate does not support
closed source models, the main reason for this is provenance, without strict versioning of models and specific checkpoints (because
they are downloaded before use) there is no reproducibility. The second is trust, if want to use benchmate with sensitive data
you should have total control over the environment that runs benchmate. That's why we only opted for models and frameworks
that do not collect informamtion about your system or the data you process. 

The only notable exception to this is alphagenome but you don't have to use it. 

**Literature**

This section makes the heaviest use of the inference section (that might change in the future)

```yaml
literature:
  cache_dir: benchmate/paddle
  pdf_path: benchmate/data/pdfs
  openalex_api_key: api_key_goes_here
```
The sections are quite self explanatory, the paddle directory is for storing the paddle ocr models, the pdf path is
where the pdf files will be downloaded. 

**Sequence, Structure, Molecule** 

The only things here are some basic information about how (molecule) or where (sequence and structure) the data

```yaml
structure:
  pdb_path: benchmate/data/structure/pdb #this is where all the pdb files are stored this is a directory, you can usually override it in functions if you want to but this will be the default

molecule:
  fingerprint_dim: 2048
  fingerprint_radius: 2

sequence:
  fasta_root: benchmate/data/sequence #this will create 4 fasta files dna, rna, protein and 3di

```

**Genomes**

It is not uncommon for a lab to be interested in multiple model organisms. To support this we included the ability to
store mutiplle genomes in a single project. The fields are rather self explanatory

```yaml
genomes:
  genome_path: benchmate/data/genome #the fasta(s) and gtf will be copied here
  genomes:
    genome_name: # for each genome you want to use create a dict like this
      description: a quick genome description
      files:
        genome_fasta: genome.fasta
        gtf: gtf.gtf
        transcriptome_fasta: null #you can add one if you want
        proteome_fasta: null #same as above
```

When a project class is intiated (see below) these genomes will be created within the same postgres database, 
ther will not be separate genes, transcripts, exons etc tables for each genome but rather they will be identified by 
genome id foreign keys. 

**APIs**

Same is also true for api calls, just some info required for calling for select endpoints. 

```yaml
apis:
  email: mail@mail.com
  biogrid_api_key:
  alphagenome_api_key:
```

**Alignment**

Because all the tools in the alignment module requires different executables, you will need to specify where they are
if you have installed them using `conda` they will tbe in your `$PATH`, otherwise you can either add them or directly tell 
benchmate where they are. The folder locations are where different databases/indexes are stored (more on that later)

```yaml
alignment:
  folddisco_bin: folddisco
  folddisco_db_root: benchmate/data/alignment/folddisco
  foldseek_bin: foldseek
  foldseek_db_root: benchmate/data/alignment/foldseek
  mmseqs2_bin: mmseqs
  mmseqs2_db_root: benchmate/data/alignment/mmseqs
  blast_bin:
    blastn: blastn
    blastp: blastp
    tblastn: tblastn
    tblastx: tblastx
    blastx: blastx
  blast_db_root: benchmate/data/alignment/blast_db #same as above
```

### Actual Creation

Now that we know where things are we can start a project. After you fill out all the necessary fields (and you must have
all the fields) we are working on making this a little bit more flexible where you can omit installations of things but
currently if you are going to use a project class instance you will need full benchmate. 

```python
from benchmate.project import Project

my_project=Project(config_path="config.yaml")
```

That's it. Though depending on your configuration (especially genomes) this may take a while. You only need to do this 
once per project, assuming that you do not want to add more genomes. The `Genome` instance has ways to add more genomes after
the fact but if you have the storage space don't be shy. 

This action will also create a bunch of folders if they do not already exist. It is generally better practice
to have different folders for different projects even if they live on the same database server. While this does cause
some duplication issues (if two projects are interested in similar papers) it also removes a lot of complexity. 


## Using a Benchmate Project

All of the classes that are discussed previously are accessible via the project. That means if you want to 
use a sequence object you need to call `myproject.sequence` This is not a class instance but a whole new class. 

That means if you want to create a sequence called `seqA` you can do

```python
seqA=myproject.sequence(name="cool sequence", sequence="ATATATTTATAT", seq_type="DNA")
```

The reason for this is now the sequence classes have additional methods called `to_kb` and `from_kb` that 
allows you to upload them to your database we created above. 

```python
seqA.to_kb()
```

And that will return an id unique to your project (even if the same sequence exists in a different project) and
you can get them back 

```python
new_seq=myproject.sequence.from_kb(id=4)
```

Of course this assumes that you know the database id for the thing you are looking for. We will get into
how you can search for things in a bit. 

### Listing items

To get some brief information about what's availabe in your project you can use

```python
myproject.list_items("paper")
```

Valid types are "paper", "api_call", "sequence", "structure", "molecule", "sequencevariant", "structuralvariant", "tandemrepeatvariant". 
This will return a `pd.DataFrame` of all the items in the database with some basic information, including the database ids of the 
items. 

Genomes and alignment classes do not contain individual items, see [genome](genome.md) for more information on genomes. 

As described above you can use the types `from_kb` method to retrieve items using the database id. Please remember that
you will need to use the object classes associated with the class not the bare classes themselves. 

```python
#this:

myproject.structure.from_kb(id=23432)

#not this
structure.from_kb(id=23423)
```

Under the hood the project subclasses the data types within itself and fills in some fields to make the `from_kb` and `to_kb()`
methods to work. 

## Searching and Retrieval

You can search and retrieve stored items across all modalities using `project.list_items()`, `from_kb()`, or the unified search engine `project.search.search()`. For detailed end-to-end examples on literature processing, API queries, entity storage, and database search, see the [Project Workflow & Usage Examples](../project_usage.md).