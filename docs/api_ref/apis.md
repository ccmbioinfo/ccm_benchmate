---
layout: default
title: APIs
parent: API Reference
nav_order: 1
---

<a id="benchmate.apis"></a>

# benchmate.apis

<a id="benchmate.apis.reactome"></a>

# benchmate.apis.reactome

<a id="benchmate.apis.reactome.Reactome"></a>

## Reactome Objects

```python
class Reactome()
```

<a id="benchmate.apis.reactome.Reactome.__init__"></a>

#### \_\_init\_\_

```python
def __init__()
```

constructor reacotme class, there are not parameters, while getting constructed obtains the latest information from the api

<a id="benchmate.apis.reactome.Reactome.search"></a>

#### search

```python
@api_call(lambda self: self.call_class)
def search(query,
           species=None,
           compartments=None,
           keywords=None,
           types=None,
           start=0,
           num_rows=1000,
           cluster=True,
           force_filters=True)
```

general query that return specific reactome ids for different types

**Arguments**:

- `query`: a string to be searched
- `species`: a species name see self.show_fields["species"]
- `compartments`: compartment name see self.show_fields["compartment"]
- `keywords`: see self.show_fields["keyword"]
- `types`: see self.show_fields["type"]
- `start`: where to start the search, default is 0
- `num_rows`: number of rows to return default is 1000 (shouldbe more than enough)
- `cluster`: whether the cluster the results by different types default True
- `force_filters`: if True and nothing is found will return an empty dict otherwise will try again w/o any filters

**Returns**:

response dict or an error

<a id="benchmate.apis.reactome.Reactome.get_details"></a>

#### get\_details

```python
@api_call(lambda self: self.call_class)
def get_details(id)
```

get detailed information about a reactome entry, you need the reacotme id

**Arguments**:

- `id`: reacome id

**Returns**:

response dict

<a id="benchmate.apis.reactome.Reactome.show_values"></a>

#### show\_values

```python
def show_values(field)
```

show available values for a given field

**Arguments**:

- `field`: see show fields

**Returns**:

a list

<a id="benchmate.apis.reactome.Reactome.show_fields"></a>

#### show\_fields

```python
def show_fields()
```

show available fields for filtering

**Returns**:

a list

<a id="benchmate.apis.uniprot"></a>

# benchmate.apis.uniprot

<a id="benchmate.apis.uniprot.UniProt"></a>

## UniProt Objects

```python
class UniProt()
```

<a id="benchmate.apis.uniprot.UniProt.__init__"></a>

#### \_\_init\_\_

```python
def __init__()
```

constructor for the UniProt class, which is used to gather data from the UniProt API. and process it in a readable format.

<a id="benchmate.apis.uniprot.UniProt.search"></a>

#### search

```python
def search(query, page_size=500)
```

free text query for the uniprot api

**Arguments**:

- `query`: text query, anything that can be searched on the uniprot website
- `page_size`: number of items per request, this is not the total number of results, it will get results until
there are no more pages

**Returns**:

a dataframe of name, uniprot id, gene name, organism and a brief description

<a id="benchmate.apis.uniprot.UniProt.get_info"></a>

#### get\_info

```python
@api_call(lambda self: self.call_class)
def get_info(uniprot_id,
             consolidate_refs=True,
             get_variations=True,
             get_interactions=True,
             get_mutagenesis=True,
             get_isoforms=True)
```

gather all the information about a specific entry described by the uniprot id

**Arguments**:

- `uniprot_id`: uniprot accession
- `consolidate_refs`: whether to consolidate all the references from the different sections into a single list
- `get_variations`: whether to call the variations api
- `get_interactions`: whether to call the interactions api
- `get_mutagenesis`: whether to call the mutagenesis api
- `get_isoforms`: whether to call the isoforms api

<a id="benchmate.apis.uniprot.UniProt.get_features"></a>

#### get\_features

```python
def get_features(results, feature_types=None)
```

filter already extracted features by type, this just filters the features from the json response

**Arguments**:

- `feature_types`: type of the feature to filter by

**Returns**:

the features

<a id="benchmate.apis.uniprot.UniProt.get_comments"></a>

#### get\_comments

```python
def get_comments(results, types=None)
```

get already extracted comments from the json response

**Arguments**:

- `types`: comment types to filter by

**Returns**:

comments

<a id="benchmate.apis.uniprot.Interactions"></a>

## Interactions Objects

```python
class Interactions()
```

<a id="benchmate.apis.uniprot.Interactions.__init__"></a>

#### \_\_init\_\_

```python
def __init__(uniprot)
```

query the uniprot API for interaction data

**Arguments**:

- `uniprot`: uniprot class

<a id="benchmate.apis.uniprot.Isoforms"></a>

## Isoforms Objects

```python
class Isoforms()
```

<a id="benchmate.apis.uniprot.Isoforms.__init__"></a>

#### \_\_init\_\_

```python
def __init__(uniprot)
```

query the uniprot API for isoform data not all proteins have isoforms and there will be warnings if none are found

**Arguments**:

- `uniprot`: uniprot class

<a id="benchmate.apis.uniprot.Mutagenesis"></a>

## Mutagenesis Objects

```python
class Mutagenesis()
```

<a id="benchmate.apis.uniprot.Mutagenesis.__init__"></a>

#### \_\_init\_\_

```python
def __init__(uniprot)
```

query the uniprot API for mutagenesis data this is different than variations, these are not variations that are

seen in the wild but from experimental data

**Arguments**:

- `uniprot`: uniprot class

<a id="benchmate.apis.biogrid"></a>

# benchmate.apis.biogrid

<a id="benchmate.apis.biogrid.BioGrid"></a>

## BioGrid Objects

```python
class BioGrid()
```

<a id="benchmate.apis.biogrid.BioGrid.__init__"></a>

#### \_\_init\_\_

```python
def __init__(access_key)
```

Initialize the BioGrid class with the provided access key.

**Arguments**:

- `access_key`: you can get one from https://webservice.thebiogrid.org/

<a id="benchmate.apis.biogrid.BioGrid.interactions"></a>

#### interactions

```python
@api_call(lambda self: self.call_class)
def interactions(gene_list, evidence_types=None, organism=None)
```

Get the interactions for the given gene list.

**Arguments**:

- `gene_list`: list of genes
- `id_types`: the type of the identifier, e.g. "entrez", "uniprot", "ensembl"
- `evidence_types`: see self.evidence_types

**Returns**:

a pandas dataframe with the interactions and kinds of evidences that support them

<a id="benchmate.apis.intact"></a>

# benchmate.apis.intact

<a id="benchmate.apis.intact.IntAct"></a>

## IntAct Objects

```python
class IntAct()
```

<a id="benchmate.apis.intact.IntAct.search"></a>

#### search

```python
@api_call(lambda self: self.call_class)
def search(ebi_id, page=0)
```

search intact database

**Arguments**:

- `ebi_id`: ebi
- `page`: which page to start from, this is more of a precaution for very large searches, if you lose connection you can
resume from the last page you got data from, default 0

**Returns**:

a dataframe of all interactions found

<a id="benchmate.apis.rnacentral"></a>

# benchmate.apis.rnacentral

<a id="benchmate.apis.rnacentral.RnaCentral"></a>

## RnaCentral Objects

```python
class RnaCentral()
```

<a id="benchmate.apis.rnacentral.RnaCentral.get_information"></a>

#### get\_information

```python
@api_call(lambda self: self.call_class)
def get_information(id: str,
                    get_xrefs: bool = True,
                    get_publications: bool = True)
```

Get information about a specific RNAcentral entry.

**Arguments**:

- `id`: rnacentral identifier
- `get_xrefs`: whether to get cross-references form other databases
- `get_publications`: whether to get publications related to the entry, these will return pubmed ids

**Returns**:

a dictionary containing information about the RNAcentral entry

<a id="benchmate.apis.stringdb"></a>

# benchmate.apis.stringdb

<a id="benchmate.apis.stringdb.StringDb"></a>

## StringDb Objects

```python
class StringDb()
```

<a id="benchmate.apis.stringdb.StringDb.__init__"></a>

#### \_\_init\_\_

```python
def __init__()
```

constructor for StringDb class

**Arguments**:

- `name`: some sort of identifier for the protein it support uniprot, gene name, gene name synonyms
- `species`: species id for the protein, default is human, you can taxanomy id from ncbi
- `network_depth`: how deep you want to go in the network, default is 1, if more than 1 it will re search all the
results for the next depth this will increase the time it takes to get the network and the number will increase exponentially

<a id="benchmate.apis.stringdb.StringDb.gather"></a>

#### gather

```python
@api_call(lambda self: self.call_class)
def gather(species, name, get_network=False, network_depth=1)
```

gather all the information about a specific entry

**Arguments**:

- `species`: which specices, this is to disambiguate, since homologs can have the same name across species
- `name`: name of the query
- `get_network`: whether to get the interactors of interactors
- `network_depth`: depth of the networks, this makes the queries grow exponentially.

**Returns**:

a dictionary of results, if the network depth is greater than one, under the "network" key you will
see other entries

<a id="benchmate.apis.ncbi"></a>

# benchmate.apis.ncbi

<a id="benchmate.apis.ncbi.Ncbi"></a>

## Ncbi Objects

```python
class Ncbi()
```

<a id="benchmate.apis.ncbi.Ncbi.__init__"></a>

#### \_\_init\_\_

```python
def __init__(access_key=None, email=None, collect_info=False)
```

**Arguments**:

- `api_key`: NCBI API key, you can get one from https://www.ncbi.nlm.nih.gov/account/settings/
- `email`: you can also use your email address if these are not provided the searches will be limited and there will be
stricter rate limits

<a id="benchmate.apis.ncbi.Ncbi.search"></a>

#### search

```python
def search(db, query, retmax=100)
```

thin wrapper around the NCBI Entrez esearch

**Arguments**:

- `db`: the database to search, use show_databases to see available databases
- `query`: the query string, this can be anything that can be typed into the NCBI search bar
- `retmax`: maximum number of results to return 10000 is the api max

**Returns**:

a list of ncbi ids matching the query from that database the ids are not unique to each database so there can be
another item with the same id in another database

<a id="benchmate.apis.ncbi.Ncbi.summary"></a>

#### summary

```python
@api_call(lambda self: self.call_class)
def summary(db, id)
```

thin wrapper around the NCBI Entrez esummary

**Arguments**:

- `db`: db name
- `id`: id to get summary for, you can get the ids from the search function

**Returns**:

list of summary records

<a id="benchmate.apis.ncbi.Ncbi.fetch"></a>

#### fetch

```python
@api_call(lambda self: self.call_class)
def fetch(db, id)
```

thin wrapper around the NCBI Entrez efetch

**Arguments**:

- `db`: database name
- `id`: id to fetch

**Returns**:

list parsed from the xml

<a id="benchmate.apis.ncbi.Ncbi.show_databases"></a>

#### show\_databases

```python
def show_databases()
```

show available databases

**Returns**:

a list of strings of database names, these strings can be used in other functions

<a id="benchmate.apis.ncbi.Ncbi.get_db_info"></a>

#### get\_db\_info

```python
def get_db_info(db)
```

get database info

**Arguments**:

- `db`: name of the database fron show_databases

**Returns**:

list of parameters and how they can be searched

<a id="benchmate.apis.ensembl"></a>

# benchmate.apis.ensembl

<a id="benchmate.apis.ensembl.Ensembl"></a>

## Ensembl Objects

```python
class Ensembl()
```

<a id="benchmate.apis.ensembl.Ensembl.call_class"></a>

#### call\_class

Ensembl API wrapper for the Ensembl REST API.

<a id="benchmate.apis.ensembl.Ensembl.__init__"></a>

#### \_\_init\_\_

```python
def __init__()
```

Initialize the Ensembl API wrapper. there are some basic variables that are set there is nothing here for the user to
set. The base url is the ensembl rest api url, the dataset is the dataset that will be used for the queries, and the
headers are the headers that will be used for the queries.

<a id="benchmate.apis.ensembl.Ensembl.variation"></a>

#### variation

```python
@api_call(lambda self: self.call_class)
def variation(id,
              method=None,
              species="human",
              pubtype=None,
              add_annotations=False)
```

Get variation information from the Ensembl REST API.

**Arguments**:

- `id`: variant id
- `method`: search method, default is None which means we will get information otherwise you can search for
publications (pmid and pmcid) or translation which converts the notations to other notations
- `species`: species to search for, default is human
- `pubtype`: 

**Returns**:

returns a detailed dict with the variation information depending on the paramters described above

<a id="benchmate.apis.ensembl.Ensembl.vep"></a>

#### vep

```python
@api_call(lambda self: self.call_class)
def vep(species, variant, tools, check_existing=True)
```

"

Get variant effect prediction from the Ensembl REST API.

**Arguments**:

- `species`: species to search for
- `variant`: variant to search for, must be a Variant object
- `tools`: tools to use for the prediction, default is None which means we will just return basic information
- `check_existing`: check population frequencies from gnomad and 1kg

**Returns**:

variant effect prediction a detailed dict, not all tools are compatible with all variants and each other

<a id="benchmate.apis.ensembl.Ensembl.phenotype"></a>

#### phenotype

```python
@api_call(lambda self: self.call_class)
def phenotype(grange, species="human")
```

Get phenotype information from the Ensembl REST API that is associated with the genomic range.

**Arguments**:

- `grange`: a GenomicRange object
- `species`: species to search for, default is human

**Returns**:

a dictionary with the phenotype information

<a id="benchmate.apis.ensembl.Ensembl.sequence"></a>

#### sequence

```python
@api_call(lambda self: self.call_class)
def sequence(id,
             trim_end=None,
             trim_start=None,
             expand_3=None,
             expand_5=None,
             sequence_type="genomic")
```

Get sequence information from the Ensembl REST API for a given ensembl id

**Arguments**:

- `id`: ensembl id, because the ids also specify the species you do not need to specify the species
- `trim_end`: trim this many nucleotides from the end
- `trim_start`: trim this many nucleotides from the start
- `expand_3`: expand this many nucleotides from the 3' end not compatible with trim_end
- `expand_5`: expand this many nucleotides from the 5' end not compatible with trim_start
- `sequence_type`: genomics, cds, protein, cdna

**Returns**:

sequence of the thing that is requested, depending on the type this can be genomic sequence, cds sequence, protein sequence or cdna sequence,
multiple sequences are returned as a dataframe

<a id="benchmate.apis.ensembl.Ensembl.xrefs"></a>

#### xrefs

```python
@api_call(lambda self: self.call_class)
def xrefs(id, species="human", external=False)
```

Get cross references from the Ensembl REST API for a given ensembl id

**Arguments**:

- `id`: ensembl id, because the ids also specify the species you do not need to specify the species

**Returns**:

a dict of cross references these can be used to get the ids from other databases from other apis

<a id="benchmate.apis.ensembl.Ensembl.mapping"></a>

#### mapping

```python
@api_call(lambda self: self.call_class)
def mapping(id, start, end, type="cDNA")
```

Get mapping information from the Ensembl REST API for a given ensembl id, convert between cDNA, CDS and protein

**Arguments**:

- `id`: ensembl id, because the ids also specify the species you do not need to specify the species
- `start`: start position of the range
- `end`: end position of the range
- `type`: type of mapping, cDNA, CDS or protein

**Returns**:

dict of mapping information, this not really compatible with genomicranges that's why the inputs are different

<a id="benchmate.apis.ensembl.Ensembl.overlap"></a>

#### overlap

```python
@api_call(lambda self: self.call_class)
def overlap(grange, features=None, species="human")
```

Get overlap information from the Ensembl REST API for a given genomic range, this can be used to get the features that are

within a region of interest. The features can be specified as a list of strings, if no features are specified all features will be returned.

**Arguments**:

- `grange`: a GenomicRange object
- `features`: features to get, default is None which means all features will be returned
- `species`: species to search for, default is human

**Returns**:

a dict of overlap information, this is a dict of dicts where the keys are the features and the values are the genomic features

<a id="benchmate.apis.ensembl.Ensembl.homology"></a>

#### homology

```python
@api_call(lambda self: self.call_class)
def homology(id,
             type="orthologues",
             target_species=None,
             source_species="human")
```

Get homology information from the Ensembl REST API for a given ensembl id, this can be used to get orthologues and paralogues

**Arguments**:

- `id`: ensembl id, because the ids also specify the species you do not need to specify the species
- `type`: type of homology, orthologues or paralogues
- `target_species`: target species to get the homology for, if None all species will be returned
- `source_species`: source species to get the homology for, default is human

**Returns**:

a dict of homology information

<a id="benchmate.apis.ensembl.Ensembl.info"></a>

#### info

```python
def info()
```

Get information from the Ensembl REST API, this returns general information about the api,

used to get an idea of what is available in the api.

**Returns**:

divisions, species and consequences that are available in the api

<a id="benchmate.apis.ebi"></a>

# benchmate.apis.ebi

<a id="benchmate.apis.ebi.BaseClient"></a>

## BaseClient Objects

```python
class BaseClient()
```

Base class for EBI clients, not sure if double level abstraction is necessary but I wanted to be defensive, this way
if there are differences between clients, I can implement them in subclasses

<a id="benchmate.apis.ebi.BaseClient.__init__"></a>

#### \_\_init\_\_

```python
def __init__(base_url, email)
```

for longer running jobs ebi clients require an email address, this is used to send notifications

**Arguments**:

- `base_url`: This comes from the client_dict
- `email`: 

<a id="benchmate.apis.ebi.BaseClient.params"></a>

#### params

```python
@cached_property
def params()
```

thankfully each client has an enpoint that returns the parameters, and then you can get the details of each parameter

using param_details

**Returns**:

returns a list of parameters

<a id="benchmate.apis.ebi.BaseClient.param_details"></a>

#### param\_details

```python
def param_details(param_name)
```

for a given parameter name, return the details and what type it is, what it does etc.

**Arguments**:

- `param_name`: str, name of the param from BaseClient.params

<a id="benchmate.apis.ebi.Client"></a>

## Client Objects

```python
class Client(BaseClient)
```

This is here for defensive purposes, I cannot predict the future

<a id="benchmate.apis.ebi.Client.run"></a>

#### run

```python
def run(params)
```

run the client with the given parameters

**Arguments**:

- `params`: dict, parameters to pass to the client you can see what they are from BaseClient.params

**Returns**:

Job object instance see below

<a id="benchmate.apis.ebi.Job"></a>

## Job Objects

```python
@dataclass
class Job()
```

and ebi client job, depending on th submission the results might take a few seconds to a few minutes to be ready.

<a id="benchmate.apis.ebi.Job.status"></a>

#### status

```python
@property
def status()
```

query the status of the job

**Returns**:

simple string, one of QUEUED, RUNNING, FINISHED if failed you will get an EbiClientError

<a id="benchmate.apis.ebi.Job.result_types"></a>

#### result\_types

```python
@cached_property
def result_types()
```

each client can return multiple result types, this is a list of those result types

**Returns**:

list of dicts, each dict has the identifier and description you will need to pass the "identifier" to get the results

<a id="benchmate.apis.ebi.Job.get_results"></a>

#### get\_results

```python
def get_results(type)
```

get the results of your job in the format you want.

**Arguments**:

- `type`: type of the result, these vary, from MSA, to html, to xml to image and other formats, because of this
feature they will not be integrated into kb but will be thing that stands on its own like alphagenome

**Returns**:

this is raw bytes, if you know you are getting a text you can parse it but there is no guarantee or standard
text mode, you may need your own parsers.

<a id="benchmate.apis.ebi.DbFetchClient"></a>

## DbFetchClient Objects

```python
class DbFetchClient()
```

dbfetch is a universal query endpoint for ebi, it hosts many databases and can be used to query them. The downside is
you need to know what you want, that is you can only query databases for specific ids.

<a id="benchmate.apis.ebi.DbFetchClient.databases"></a>

#### databases

```python
@cached_property
def databases()
```

get the databases that are available for querying

**Returns**:

a list of dicts, each dict has the database name, description, and a list of formats and styles

<a id="benchmate.apis.ebi.DbFetchClient.fetch_data"></a>

#### fetch\_data

```python
def fetch_data(database: str,
               id: str,
               format: str = "default",
               style: str = "raw")
```

get some results from a database of your choosing

**Arguments**:

- `database`: which database
- `id`: the id of the thing you want
- `format`: which format you want it returned in, pdb, msa etc. these change depending on the database,
DbFetchClient.databases will tell you what formats are available for each database.
- `style`: which style you want it, defautl is raw, the options are usually html and raw.

**Returns**:

DBFetchData instance

<a id="benchmate.apis.ebi.DbFetchData"></a>

## DbFetchData Objects

```python
@dataclass
class DbFetchData()
```

<a id="benchmate.apis.ebi.DbFetchData.data"></a>

#### data

there are many formats, this is raw bytes, you will need to parse it

<a id="benchmate.apis.ebi.EBI"></a>

## EBI Objects

```python
class EBI()
```

this is a thin wrapper around the above classes

<a id="benchmate.apis.ebi.EBI.dbfetch_databses"></a>

#### dbfetch\_databses

```python
@property
def dbfetch_databses()
```

get a list of all available databases

<a id="benchmate.apis.ebi.EBI.search_database"></a>

#### search\_database

```python
def search_database(query, database, style, format)
```

search a database

**Arguments**:

- `query`: what to search for
- `database`: which database to search
- `style`: what style of output to return
- `format`: usually html or raw

**Returns**:

see dbfetchclient.fetch_data

<a id="benchmate.apis.ebi.EBI.ebi_clients"></a>

#### ebi\_clients

```python
@property
def ebi_clients()
```

get a list of all available clients

<a id="benchmate.apis.ebi.EBI.run_client"></a>

#### run\_client

```python
def run_client(client_name, params)
```

run a client see Client

<a id="benchmate.apis.ebi.EBI.get_client_params"></a>

#### get\_client\_params

```python
def get_client_params(client_name)
```

get client parameters that it supports see Client

<a id="benchmate.apis.ebi.EBI.get_client_param_details"></a>

#### get\_client\_param\_details

```python
def get_client_param_details(client_name, param_name)
```

get details about a client param see Client

<a id="benchmate.apis.ebi.EBI.get_client_status"></a>

#### get\_client\_status

```python
def get_client_status(client_job)
```

Check the status of a client job

<a id="benchmate.apis.ebi.EBI.get_client_result_types"></a>

#### get\_client\_result\_types

```python
def get_client_result_types(client_job)
```

Get the result types of a client job

<a id="benchmate.apis.ebi.EBI.get_client_result"></a>

#### get\_client\_result

```python
def get_client_result(client_job, result_type)
```

Get the result of a client job

<a id="benchmate.apis.ols"></a>

# benchmate.apis.ols

<a id="benchmate.apis.ols.Ontology"></a>

## Ontology Objects

```python
@dataclass
class Ontology()
```

Dataclass to store ontology term information. Same idea as the other dataclasses, this actually not used because
it get converted to dict later on, it's here for convenience

<a id="benchmate.apis.ols.OLS"></a>

## OLS Objects

```python
class OLS()
```

<a id="benchmate.apis.ols.OLS.call_class"></a>

#### call\_class

ontology Lookup Service (OLS) client for querying ontology information, because I have avoided
dealing with owl files and will continue to do so.

<a id="benchmate.apis.ols.OLS.ontologies"></a>

#### ontologies

```python
@cached_property
def ontologies()
```

get a list of all ontologies in OLS, this may take a few seconds to run the first time around but after that it will be cached

<a id="benchmate.apis.ols.OLS.get_term"></a>

#### get\_term

```python
@api_call(lambda self: self.call_class)
def get_term(ontology_id: str,
             term_id: str,
             iri: Optional[str] = None,
             get_children: bool = False,
             get_parents: bool = False,
             get_ancestors=False,
             get_descendants=False,
             get_graph=False)
```

get details about a specific term in an ontology, you will need to know the ontology id and either the term id or the iri

**Arguments**:

- `ontology_id`: name of the ontology to search
- `term_id`: the short form, or term id can be used
- `iri`: or you can use the full iri
- `get_children`: get the children, these will not be recursuve in the sense that it will just return the json, not additional
ontology objects
- `get_parents`: same as children but for parents
- `get_ancestors`: same as children but for ancestors
- `get_descendants`: same as children but for descendants
- `get_graph`: get the relationship graph for the term, this is just a dict of the graph {"nodes": [], "edges": []}

**Returns**:

ontology object with details and requested features

<a id="benchmate.apis.alphagenome"></a>

# benchmate.apis.alphagenome

<a id="benchmate.apis.alphagenome.AlphaGenome"></a>

## AlphaGenome Objects

```python
class AlphaGenome()
```

<a id="benchmate.apis.alphagenome.AlphaGenome.__init__"></a>

#### \_\_init\_\_

```python
def __init__(access_key)
```

Create an AlphaGenome object. this is used to query the alhpagenome api, but unlike other api calls this does

not return and api_call dataclass instance, instead it returns depending on the method, a variant, a genomic_range or
a dataframe will be returned

**Arguments**:

- `access_key`: your alphagenome api key, you can get one from their website.

<a id="benchmate.apis.alphagenome.AlphaGenome.predict_variant"></a>

#### predict\_variant

```python
def predict_variant(variants,
                    interval_size="SEQUENCE_LENGTH_2KB",
                    organism="human")
```

for a given list of variants predict their consequences, this does not mean you can pass a whole vcf file to it

but you can do a few dozen at a time no problem.

**Arguments**:

- `variants`: list of variant objects, they do not need to have annotations
- `interval_size`: which interval should we consider, default 2KB
- `organism`: which organism should we consider, default human the other option is mouse, that's it.

**Returns**:

a benchmate.Variant.SequenceVariant instances, the same ones passed to the function but with annotations

<a id="benchmate.apis.alphagenome.AlphaGenome.predict_sequence"></a>

#### predict\_sequence

```python
def predict_sequence(sequences,
                     ontology_terms,
                     interval_size="SEQUENCE_LENGTH_2KB",
                     output_types=None,
                     organism="human")
```

predict features of a list of sequences, if you have only one you should pass [sequence] a

**Arguments**:

- `sequences`: list of benchmate.sequences.Sequence objects
- `ontology_terms`: which ontology terms to use if you do not specify any we'll use all of them
- `interval_size`: interval size to consider, default 2KB but if needs to be longer than your sequence
- `output_types`: see self.ouput_types or get them all (if none)
- `organism`: which organism to consider, default human the other option is mouse, that's it.

**Returns**:

a list of benchmate.sequences.Sequence objects same ones with the features property filled in

<a id="benchmate.apis.alphagenome.AlphaGenome.predict_interval"></a>

#### predict\_interval

```python
def predict_interval(granges,
                     ontology_terms,
                     interval_size="SEQUENCE_LENGTH_2KB",
                     output_types=None,
                     organism="human")
```

predict things about an interval,

**Arguments**:

- `granges`: a list of granges or a grageges list object, if you have only one grange then pass it as a list [grange]
- `ontology_terms`: which ontology terms to use
- `interval_size`: interval size to consider, default 2KB, it needs to be longer then len(grange)
- `output_types`: see above
- `organism`: see above

**Returns**:

a list of granges, with annotations

<a id="benchmate.apis.alphagenome.AlphaGenome.mutagenesis"></a>

#### mutagenesis

```python
def mutagenesis(granges,
                scorers,
                mutagenesis_region=None,
                interval_size="SEQUENCE_LENGTH_2KB",
                output_types=None,
                organism="human")
```

Perform in-silico mutagenesis for all the sequences in the range you provided

**Arguments**:

- `granges`: list of granges
- `scorers`: list of scorers, see self.scorers
- `interval_size`: which interval size to consider, default 2KB, it needs to be longer then len(grange)
- `mutagenesis_region`: which region of the sequence to mutate extensively, this needs to be shorter than your
interval size, the method picks the center of the rage and mutagenesis_region/2 on each side

**Returns**:

a dataframe of scores or a list of dataframe of scores if you picked more than one scorer, if you get
greedy and ask for all the things the server might kick you out.

<a id="benchmate.apis.utils"></a>

# benchmate.apis.utils

<a id="benchmate.apis.utils.api_call"></a>

#### api\_call

```python
def api_call(call_class_getter)
```

This is one of the workhorses of this module, it is a decorator function that takes a call (if decorated) and

returns and ApiCall instance (see below), This gives the api call a few handy tools that can be used later on.

**Arguments**:

- `call_class_getter`: See project, there is another api call class that includes methods to get things from a database
and put things in a database

**Returns**:

a decorated function

<a id="benchmate.apis.utils.ApiCall"></a>

## ApiCall Objects

```python
@dataclass(slots=True)
class ApiCall()
```

Stores metadata and results of an API call. This is to make it easier to track api calls for knowledge base construction.

<a id="benchmate.apis.utils.ApiCall.rerun"></a>

#### rerun

```python
def rerun()
```

rerun the api call with the same parameters, useful if the api call failed or if you want to update the results

**Arguments**:

- `access_key`: if the api requires an access key like alphagenome or biogrid
- `email`: if the api requires an email like ncbi

**Returns**:

an updated ApiCall instance

