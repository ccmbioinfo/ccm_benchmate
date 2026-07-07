---
layout: default
title: Stringdb
parent: APIs
grand_parent: Modules
nav_order: 6
---

## stringdb.StrinDb

Stringdb is a web platform that focuses on protein-protein interactions, you will need to specify your species and protein identifiers. I've also built in an option to run the 
interaction queires recursively. That is, you can take a protein and gather all the other proteins that interact with it, then take them all and repeat the process to generate 
a network of arbitrary depth. Of course this will increase the number things returned exponentially and will take exponentially longer. So keep that in mind.

```python
from benchmate.apis import StringDb
stringdb=StringDb()

network = stringdb.gather("human", name="ENSP00000354587", get_network=False)

```

Get network specifies whether you want to get the interactors of interactors. If you specify that to True and network depth, 
the number will grow exponentially. So anything over 3 is probably overkill by a wide margin. You can use a wide range of 
identifiers, in the example above we are using an Ensembl protein id (things need to be proteins) but it can be a 
whole bunch of other ids. See their [documentation](https://string-db.org/cgi/help.pl?subpage=api%23mapping-identifiers) for details.


