---
layout: default
title: APIs
parent: Modules
has_children: true
nav_order: 1
---

## APIs module

This module allows you to connect to various select public repositories from benchmate. This is a large but opinionated collection. 
Some of the endpoints require an API key or an email to access. They are all free but may come with rate restrictions or 
query limits. In general please be nice and use aggressive, exponential backoff if you are performing many queries. 

## Implemented providers

Below are the implemented enpoints, if there are other ones you would like to see here you can create an issue or even better
create a pull request of your implementation. 

| Endpoint        | Description                                                             | Requirements                                                         | Documentation            | 
|:----------------|:------------------------------------------------------------------------|:---------------------------------------------------------------------|:-------------------------|  
| **alphagenome** | variant effect prediction for snps and genomic ranges                   | A free API key                                                       | [here](./alphagenome.md) |
| **biogrid**     | Protein protein interaction                                             | A fre API key                                                        | [here](./biogrid.md)     |
| **ebi tools**   | Various biological calculations and database search                     | Email and some rate limitations, some tools need you to check status | [here](./ebi.md)         |
| **ensembl**     | VEP, genomes, phenotypes, homolgy, cross refernces to other dbs         | None, but may hit rate limitations                                   | [here](./ensembl.md)     |
| **intact**      | Protein protein interaction database                                    | None                                                                 | [here](./intact.md)      |
| **ncbi**        | All of ncbi databses, can cross reference each other                    | email, can hit severe rate limits, keep it ~ 1 query per second      | [here](./ncbi.md)        |
| **ols**         | Ontology lookups service, find standard codes for genes, phenotypes etc | None                                                                 | [here](./ols.md)         |
| **reactome**    | Database of biochemical reactions                                       | None                                                                 | [here](./reactome.md)    |
| **rnacentral**  | RNA Database usuall for non-coding                                      | None                                                                 | [here](./rnacentral.md)  |
| **stringdb**    | another protein protein interaction database                            | None                                                                 | [here](./stringdb.md)    |
| **uniprot**     | very detailed information about all known proteins and cross references | None                                                                 | [here](./uniprot.md)     |


Most of these return an `ApiCall` instance (documentation [here](./apis/apicall.md)) that allows you to re-query at a later time with minimal effort. While we tried
to keep the outputs of the calls as consistent as possible, what they return is not in our control. For programmatic access
for large datasets you might want to invest some time to determine what the enpoint returns and program your queries accordingly. 

If there are issues please feel free to create an issue in our repository. 