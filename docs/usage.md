---
layout: default
title: Usage Examples
nav_order: 13
---

# Some Examples for Usage

This is not really an extensive usage guide but it is there to give you an idea about how to use different modules in the 
library together to get the most out of it. Here we will make some use of the project meta class to get some information about 
a specific project that we are interested in. 

In the document we will:

1. Create a new project and initialize a database for it.
2. Add a new description to be used later to aid us in fitering results
3. Search for some papers, find the relevant ones
4. Add a genome
5. Among the relevant ones get full-text data (if we can) and process the pdfs. 
6. Search for genes, proteins, compounds
7. Download some sequences and structures
8. Write a small script to do this in one go
9. Add all this to our knowledgebase to be searched later
10. Search for some information about the project


This will touch all the modules in the library, but we will not be using all the available functionalies especially in the 
apis module. We will also not be generating any image interpretations since that requires a lot of processing power. 