---
layout: default
title: Project Meta Module
nav_order: 11
---

# Project Meta Module

Project meta module is the main connector between the other modules and your knowledge base. This module is responsible for:

- Reading and writing project meta data
- Reading and writing outputs from other modules
- Searching for things in the knowledge base
- Managing the overall project structure and organization

This module is a thin wrapper around other data retrieval modules and the knowledgebase. It has functions to add, update
delete records. The main motivation for this module is to prove a central point of control for the project.

## Creating a new project

```python
from benchmate.project.project import Project
from sqlalchemy import create_engine

engine = create_engine('postgresql+psycopg2://user:password@hostname/database_name')

my_project = Project(name="My Project", description="My Project Description", engine=engine)
```

Your project description is important for many of the projects search and retrieve functions. The project uses this document
to find and compare relevant results such as relevant papers or other api call results based on the free text description of 
elements that are returned from the api in some instances. This document ideally should be a one page executive summary of what
the project is about and what are the main goals. It also might be helpful to include a list of methodolgies (like wet-lab experiments)
that are planned to be used in the project as well as things that are not relevant. For example if you are interested in how
oxidative stress affects the gene expression in cancer you probably do not want to get any papers about how 
oxidative stress affects photosynthesis in rainforests. 

All the previous modules get initialized when the project is created. 

## Adding a new project or loading an existing project

If you have already created a project when you intialize the Project class instance the database will find and connect to the 
project you have specified. This search is based on the project name and description. If there are not projects with that name
than a new one is created. 

Inside the project instance there are 2 new attributes that are wrappers around the APIs and the literature module.

### Literature class

Here is the code for the entire class, it is pretty self-explanatory. 

```python
class Literature:
    def __init__(self):
        self.litsearch=LitSearch()
        self.paper=Paper()
```

You can use all the functions like so:

```python
my_project.literature.litsearch.search_papers(query="oxidative stress")
```

### APIs class

This is very similar to the literature class. 

```python
my_project.apis.ensembl.variation("rs56116432", add_annotations=False)
```

The main difference is, instead of just returning the results of the API call as a dict, you will get a ApiCall dataclass. 

Below is the entire code for the APICall dataclass, it is pretty self-explanatory. 

```python
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

    def __str__(self):
        return f"ApiCall @ {self.query_time} with args:{self.args}, kwargs:{self.kwargs}"

    def __repr__(self):
        return self.__str__()
```

This to make sure that we can track the API calls and when they were made, this is important to know because API endpoints get 
updated and we want to keep track of how we made the call to compare the results with the new API calls.

You can add arbitratr items form other modules to the project. 

# **NOT YET IMPLEMENTED**

```python
my_prject.to_kb([api_call, paper, ...])
```

If you know the id of the the thing you want to get you can use the `from_kb` function. 

```python
my_prject.from_kb(item_id=1, item_type="paper") #this will return a paper object instance
```

Finally, if you want to search the knowledge base for a specific item you can use the `search_kb` function. 