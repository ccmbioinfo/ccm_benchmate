---
layout: default
title: Knowledge Base
parent: Modules
nav_order: 12
---

# Knowledge Base Module

The knowledge base as the name suggests is there for storing information. This is a posgresql database with tables organized
in a way that makes it easy to search for information. This is especially true for the Paper class instances and API calls. 

Usually, the end user will not really interact with the database, but will use the project [meta-class](project.md) to search
for different things. 

Below is the database schema, there might be some small changes as we develop the package further:

![Database Schema](../assets/kb_schema.png)

There are a lot of modalities represented in the database, and some of them are split into several different tables. 

All of the tables are centered around the project table where each different item refers to a project. 
One thing that is not ideal in this schema is if, for example, you have the same paper for different projects, you will need 
to save it twice. 

In future iterations we will try to make the schema more normalized and make it easier to search for different things across
projects. 

## Notes:

The knowledge base is soley there to abstract the database features for the [project](./project.md) module. There are no 
functions, methods or useful items for a user to interact with the knowledgebase directly. This documentation is here for 
reference for developers. 