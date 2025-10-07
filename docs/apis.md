---
layout: default
title: API's module
nav_order: 3
---

# API's module

This module includes the API classes for the ccm_benchmate package. Each API class is responsible for 
handling a specific type of request and returning the appropriate response. The classes assume that you know what you are
looking for and gives you the power to link different public databases to each other programmatically. Each of the APIs
return a dictionary with varying structures and the parsing also is different. The API classes are as follows:

The APIs marked with (WIP) are still under development and may not be fully functional yet.

+ Ensembl
+ Uniprot
+ NCBI E-Utils
+ Reactome
+ stringdb
+ Intact
+ RNAcentral
+ BioGrid
+ AlphaGenome


Here is a `README.md` for the classes under `benchmate/apis`. Each section describes the class and provides usage examples for each public method.

---

## ensembl.Ensembl

**Description:**  
Client for the Ensembl REST API. Supports gene, variant, phenotype, sequence, mapping, and overlap queries. There are a lot of different functionalities in each of the different methods so please
test different options to see which one is best suited for your needs. 

### Variation methods

```python
from benchmate.apis.ensembl import Ensembl
from benchmate.ranges.genomicranges import GenomicRange

ensembl = Ensembl()

# Variation info
info = ensembl.variation("rs56116432", add_annotations=True) # if you do not use the add annotations option the response would be a lot smaller

# this returns all the variants that are mentioned in a specific paper keep in mind that if you are looking for a very recent
# paper it might not be available yet
info_pub = ensembl.variation("26318936", method="publication", pubtype="pubmed")

# translate method translates one variant representation to other formats
info_translated = ensembl.variation("rs56116432", method="translate")

```

### VEP

VEP is Ensembl's **V**ariant **E**ffect **P**redictor. You can run VEP on a single variant and return **a lot** of information based on what additionaly tools you have selected to use. To be able to use the VEP method you will need to use
`ccm_benchmate.variant.variant` module.

```python
from benchmate.variant.variant import SequenceVariant
myvar= SequenceVariant(1, 55051215, 'G', 'GA')

vep_info = ensembl.vep(species="human", variant=myvar, tools=None)
vep_info
```

There are many tools that can be called with the VEP method. You can see the whole list in the VEP [website](https://useast.ensembl.org/info/docs/tools/vep/script/vep_options.html)

### Phenotype

If you are interested in what phenotypes are associated with a genomic region you can use the `GenomicRanges` module and the phenotype method:

```python
from benchmate.ranges.genomicranges import GenomicRange
grange = GenomicRange(9, 22125503, 22125520, "+")
phenotypes = ensembl.phenotype(grange)
phenotypes

# or for a given range you can search for overlapping features (you can also do this in the genome module and it's the preffered method if you are planning to query a lot of different things)
overlap = ensembl.overlap(grange, features=["transcript"])
```

### Mapping

If you have some genomic feature id and you want to convert them to something else you can use the mapping method. This could mean convering genomic coordinates to cDNA or protein coordinates to genomic coordinates etc. 

```python

ensembl.mapping("ENST00000650946", 100, 120, type="cDNA")

```

### xrefs

Ensembl is a massive resource, it contains constantly updated cross-references to other databases. This is especially useful in our case because we can use this method to retrieve ids which then can be used to query other enpoints. 

```python
xrefs = ensembl.xrefs("ENSG00000139618")
```

Finally, you can return about the species, and the kinds of information that is available in the api (there may be changes and that is beyond our control) using `Ensembl.info` method.

---

## stringdb.StrinDb

Stringdb is a web platform that focuses on protein-protein interactions, you will need to specify your species and protein identifiers. I've also built in an option to run the 
interaction queires recursively. That is, you can take a protein and gather all the other proteins that interact with it, then take them all and repeat the process to generate 
a network of arbitrary depth. Of course this will increase the number things returned exponentially and will take exponentially longer. So keep that in mind.

```python
from benchmate.apis.stringdb import StringDb
stringdb=StringDb()

network = stringdb.gather("human", name="ENSP00000354587", get_network=False)

```

Get network specifies whether you want to get the interactors of interactors. If you specify that to True and network depth, the number will grow exponentially. So anything over 3 is probably overkill by a wide margin. You can use a wide range of identifiers, in the example above we are using an Ensembl protein id (things need to be proteins) but it can be a whole bunch of other ids. See their [documentation](https://string-db.org/cgi/help.pl?subpage=api%23mapping-identifiers) for details. 

---


## others.BioGrid

Biogrid is a similar platform that focuses on protein-protein interactions with some experimental data annotations as to how that interaction is determined. To use Biogrid you need to get an access key but it is free.

```python
from benchmate.apis.others import BioGrid
biogrid=BioGrid(access_key="<your api key>")

interactions=biogrid.interactions(gene_list=["ENSP00000354587"]) # you can provide more than one gene


# list all available organisms
biogrid.organisms
```

---

## others.IntAct

Intact is one other interaction database. There were a lot of requests to include all of these in the package. While they provide similar information they do have different use cases.

```python
from benchmate.apis.others import IntAct
intact=IntAct(page_size=100)

# to search intact you need the ebi id, this you can get from ensembl.xrefs or from uniprot (see below)
interactions=intact.intact_search("Q05471")
interactions
```

Intact database contains information not just about protein-protein interactions but also other molecule types. This means your response could be quite large. Also I have integrated so that the API keeps searching for interactions until the last page is reached. This means you will get all the results once the request is complete but if your request has a lot of information it might take a few seconds or more.

---

## ncbi.Ncbi

This probabaly is the thinnest wrapper around all the APIs. The main reason for that is that we cover basically the entirety of the NCBI database and you have a lot of options and flexibility for querying. As always with that flexibility comes the burden of verbosity. We will cover some of the endpoints in this tutorial for the rest you can check the E-Utils guide and the NCBI website. One other quirk of this database is, some endpoints return detailed information via the summary endpoint while others return via fetch. You will need to try them out yourself before writing a comprehensive script.

```python
from benchmate.apis.ncbi import Ncbi
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

I'm not going to go into a lot of details partly because there are so many different databases and all of them either have the summary or fetch (or both like genes) method return something and what they return is different in each case. However, the response per call/db is quite consistent and if you know what you are looking for it's not that difficult to streamline the search and knowledge gathering using these endpoints.

---

## uniprot.Uniprot

Uniprot is an extensive database of proteins and features of proteins, It has several API endpoints, the ones that are integrated are the most compreshenive ones called: proteins, mutagensis (high throughput mutagenesis experiments), isoforms and variation. You can query this using a single command like so:

```python
from benchmate.apis.uniprot import UniProt
uniprot=UniProt()

results=uniprot.search_uniprot(uniprot_id="P01308", get_isoforms=True, get_variations=True,
                       get_mutagenesis=True, get_interactions=True, consolidate_refs=True, )
```

The results are consolidated into a few different locations, you can see the references under `results["references"]` as pubmed ids, there is a `description` that is a plain human readable text of describing the protein. All the keys are below:

```python
dict_keys(['id', 'name', 'sequence', 'organism', 'gene', 'feature_types', 'comment_types', 'references', 'xref_types', 'xrefs', 'description', 
'json', 'secondary_accessions', 'variation', 'interactions', 'mutagenesis', 'isoforms'])
```

You can see what kinds of features are available for a given protein using `get_features` method or you can you `get_comments` method to see other kinds of annotations that are more about the whole protein.

```python
results["comment_types"]
results["feature_types"]

uniprot.get_features(results["json"], "SIGNAL")
uniprot._get_comments(results["json"], "DISEASE")
```

---

## reactome.Reactome

Reactome is more concerned about biological reactions, pathways and the genes/proteins that are associated with it. You need to know your reactome id but I think we can figure that out either through Ensembl or Uniprot.

```python
from benchmate.apis.reactome import Reactome
reactome=Reactome()

# initialization gathers some information that is up to date, these are the fields you can search for
reactome.show_fields()

['species', 'type', 'keyword', 'compartment']

# see all species
reactome.show_values("species")

# search
results=reactome.query(query="cancer", species="Homo sapiens", force_filters=False)

results.keys()
dict_keys(['Pathway', 'Reaction', 'Interactor', 'Set', 'Protein', 'Complex', 'DNA Sequence', 'Icon'])

#get more details about one of the things
details=reactome.get_details(results["Pathway"][0]["dbId"])

details.keys()
dict_keys(['dbId', 'displayName', 'stId', 'stIdVersion', 'created', 'modified', 'isInDisease', 'isInferred', 'name', 'releaseDate', 
    'speciesName', 'authored', 'disease', 'edited', 'literatureReference', 'species', 'summation', 'reviewStatus', 'hasDiagram', 
    'hasEHLD', 'hasEvent', 'normalPathway', 'schemaClass', 'className'])
```

Each of the details has more information that are also stored as dictionaries. The API output is very consistent and some of the fields will be there reliably. That said, it will not hurt to do some basic checks like `"something" in results.keys()` if you are planning to loop through a lot of information. 

---

## rnacentral.RnaCentral

Last but not least we have RNA Central, you will need the RNA Central id to query, you can get most of these through Ensembl xrefs

```python
from benchmate.apis.rnacentral import RnaCentral

#you need the rnacentral id to search
rnacentral=RnaCentral()

results=rnacentral.get_information(id="URS00000CE0D1")
results.keys()

dict_keys(['url', 'rnacentral_id', 'md5', 'sequence', 'length', 'xrefs', 'publications', 'is_active', 'description', 
    'rna_type', 'count_distinct_organisms', 'distinct_databases', 'references'])
```

The results are fairly obvious. 

## others.AlphaGenome

Unlike the other api calls this one does not return an api call instance. Instead, depending on the method used it will return
a sequence.Sequence, a variant.SequenceVariant, a ranges.GenomicRanges or just a dataframe or a list of dataframes. As the
name suggests, this class queries the [Alpha Genome server](https://www.alphagenomedocs.com/) and uses benchmate's class instances
to automatically convert to alphagenome's instances and back. In order to be able to use this module you will need an api key. 
You can get it through their website for free.

The three main prediction methods are below:

```python
from benchmate.apis.others import AlphaGenome
from benchmate.ranges.genomicranges import GenomicRange
from benchmate.variant.variant import SequenceVariant
from benchmate.sequence.sequence import Sequence

# create the instance
ag=AlphaGenome(access_key=<your api key>)

# predict variant consequences
var1=SequenceVariant(chrom="chr22", pos=36201698, ref="A", alt="C")
var2=SequenceVariant(chrom="chr22", pos=36201698, ref="A", alt="T")
variants=[var1, var2]
variant_predictions=ag.predict_variant(variants)

# predict features of a sequence
seq1=Sequence("GATTACA")
seq2=Sequence("GATTACAGATTACAGATTACA")
sequences=[seq1, seq2]
seq_predictions=ag.predict_sequence(sequences)

# you can also use an interval
gr1=GenomicRange(chrom="chr22", start=234234, end=435345, strand="+")
gr2=GenomicRange(chrom="chr5", start=2234, end=4455, strand="+")

# can be a regular list or a GenomicRangesList or any other iterable really
ranges=[gr1, gr2]
interval_predictions=ag.predict_interval(ranges)
```

There are a few gotchas that you need to be aware of. Currently you can only pass sequence variants (snps, small indels)
this is not a limitation of benchmate but of alphagenome. The model(s) in alphagenome are trained on human and mouse sequences only
(GRCh38, mm10) and you can specify the organism ("human", "mouse") on each of the methods above. The default is human. 

Any ranges and variant coordinates are limited to these 2 genomes. While you can pass whatever sequence you want the predictions
will be done based on the organism you chose and may not be reliable or outright wrong for other organisms. 

There are quite a few different kinds of results you can get. You can read more about it in their [documentation](https://www.alphagenomedocs.com/index.html). 
For variants, sequences and intervals all of them are queried and this ususally is not a problem per item in the list you passed. 
If your list is too long you may get kicked out so it might be worthwhile to add a `time.sleep` after a few queries.

If you are passing sequences or intervals your interval_size argument needs to be larger than the sequence or GenomicRange instance
you can see available intervals under `ag.sequence_lengths` property. 

Finally, AlphaGenome returns a bunch of ontologies and annotations. These are based on the [OLS](https://www.ebi.ac.uk/ols4/) 
service. You can see what's available for each organism (human and mouse) under `ag.ontologies`. for interval and sequence predictions
if you'd like you can pass a list of ontologies from that collection. 

The last method is called `mutagenesis` and for a given interval we query every position one by one. This is computationally
intensive and if you query all the methods it will either time out or the sever will kick you out. So you will need to specify which
scorers you are interested in. You can see the available scorers under `ag.scorers` property. If you do not want to perform 
mutatenesis you can pass an integer and the scores for the middle section of that length will be queried. 

For example if you have 200bp region, and you pass mutagenesis_region=100 only the scores for the middle 100 will be 
calculated and the 50bp on each side will be ignored. 

```python
from alphagenome.models import variant_scorers

# mutagenesis takes a list of ranges
mutagenesis_results=ag.mutagenesis(ranges, scorers=[variant_scorers.CenterMaskScorer])
```

## Some Meta Programming

All api object instances (except alphagenome) will return an instance of an `ApiCall` dataclass. This class includes the results
of the query, when it was queried with what parameters. This is useful to keep track of new annotations in these databases since 
the same query performed at different times can yield different results based on the latest information. The ApiCall dataclass
has a single defined method called rerun which will rerun the call and return another instance of `ApiCall`. If the class instance needs
and email (ncbi) or an api key (biogrid, alphagenome) you will need to re-enter that information to rerun. Otherwise you will
get the relevant error associated with that method instance call or a 403 error. 