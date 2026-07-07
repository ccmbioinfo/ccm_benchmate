from apis import Ncbi---
layout: default
title: NCBI
parent: APIs
grand_parent: Modules
nav_order: 2
---

## ncbi.Ncbi

This probabaly is the thinnest wrapper around all the APIs. The main reason for that is that we cover basically the entirety of the 
NCBI database and you have a lot of options and flexibility for querying. As always with that flexibility comes the burden of verbosity. 
We will cover some of the endpoints in this tutorial for the rest you can check the E-Utils guide and the NCBI website. 
One other quirk of this database is, some endpoints return detailed information via the summary endpoint while others return via fetch. 
You will need to try them out yourself before writing a comprehensive script.

```python
from benchmate.apis import Ncbi
ncbi = Ncbi(email=<your email>) # so ncbi can tell you to stop abusing their resources. Also the rate limit increase dramatically when an email or api key is provided, they put you in the nice queue.

# list all the databases:
ncbi.databases
```

To search a specific database you will need to specifiy it in the search method. This will return their NCBI ids and nothing else. 

```python
omim_codes=ncbi.search(db="omim", query="cancer", retmax=1000) # return 1000 items
```

To get more information about a specific id you can use the `summary` or `fetch` method. 

```python
mycodes=omim_codes[0:10]
summaries=[ncbi.summary("omim", code)[0] for code in mycodes]

full_record=ncbi.fetch("omim", omim_codes[0])
```

I'm not going to go into a lot of details partly because there are so many different databases and all of them either 
have the summary or fetch (or both like genes) method return something and what they return is different in each case. 
However, the response per call/db is quite consistent and if you know what you are looking for it's not that difficult to 
streamline the search and knowledge gathering using these endpoints.

In addition to searching and retrieving records you can also find connections between different ncbi entities  using the links method

```python
links=ncbi.links("pubmed", "gene", <some_id>)
```

This will get all records that are mentioned in the pubmed entry with the id that are in the gene database. This is useful
as a direct access to related entries. For example you can directly get all the SRA datasets of a publication w/o querying for the
paper title or any other potentially ambiguous queries. This makes automation much more reliable. Once you have the ids, you can 
then use the same methods above to return details about an entry. 