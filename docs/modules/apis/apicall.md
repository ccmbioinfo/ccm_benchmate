---
layout: default
title: APICall Meta Class
parent: APIs
grand_parent: Modules
nav_order: 11
---

# APICall class

All the API endpoints return different dictionary structures and information. To be able to store all these different 
sources of data we need a standardized method to access them. For this we created the api call class to store and process
all the information. Additionally, the API Call class has the option to be re-run without any other arguments (save for your
email or api key depending on the endpoint) if you want to check if there is new information in the database of your choosing. 


With the exception of the `.rerun()` method all methods and attributes are for internal use only. For completeness sake here
we describe the features here. 

```python
from benchmate.apis.utils import ApiCall

# the dataclass looks like this:
@dataclass
class ApiCall:
    """
    Stores metadata and results of an API call. This is to make it easier to track api calls for knowledge base construction.
    """
    class_name: str = None
    method_name: str = None
    results: dict = None
    args: tuple= None
    kwargs: dict = None
    query_time: datetime = None
```

When you perform one of the queries in other methods (with the exception of alphagenome) you will not get the dictionary
you were looking for but an ApiCall class instance. There results will be under results property. The rest as might be able
to tell stores all the arguments that you used to make the call and when you made it. 

If you want to perform the same query at a different time you can just call the rerun method

```python
from benchmate.apis import UniProt
uniprot=UniProt()

results=uniprot.search_uniprot(uniprot_id="P01308", get_isoforms=True, get_variations=True,
                       get_mutagenesis=True, get_interactions=True, consolidate_refs=True, )

new_results=results.rerun()
```

This will return a new api call instance. 