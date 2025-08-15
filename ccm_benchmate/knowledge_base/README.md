---
layout: default
title: Knowledge Base
---

This module is designed to store the results of your searches and queries in a database. The goal is to 
provide a way to store the data that you have retrieved from the different modules in a structured way 
that allows you to query it later. The database schema is still under heavy development. Currenlty we 
have schemas to store the paper classses, sequences, structures, variants and genomes. Due to semantic 
chunking and processing of the paper text there is a strict requiremen to use postgres as the database. 
This allows us to offload a lot of the semantic searching via pgvector extension. Unfortunately this 
means that you will need to install pgvector extension on your postgres database. We will be providing 
instructions how to do that under the knowledge base module readme.

One of the most ambitions goals of this module it to provide a natural language search capabilities to 
many different data modalities that are represented in by othe other modules. This means that you will 
be able to search for papers, sequences, structures, variants and genomes using natural language 
queries. The results will be returned in a structured way that allows you to easily access the data. 
This great flexilbilitly however comes at cost of requiring a gpu to run a language modeld that will 
perform the queyring for you. We are currently working on a few different modeld that can be used for 
this purpose and will be providing a unified interface to use either your local models served via 
llama.cpp or ollama or remote models served via huggingface.co or closed source models like openai.com. 
The goal of this project is not to provide an interface for analysis but rather to provide a way to 
store and query the data that you have retrieved from the different modules in a structured way that 
hopefully will allow you to generate hypoteses to test and analyze. This means that we will not be 
providing any analysis pipelines or tools otherthan simple ContainerRunner calls to run your own 
pipelines and we will not be supporiting any kind of security or will data privacy. This is a research 
project and we are not responsible for any data that you store in the knowledge base.
