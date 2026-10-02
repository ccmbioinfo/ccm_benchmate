---
layout: default
title: AlphaGenome
parent: APIs
grand_parent: Modules
nav_order: 5
---


## others.AlphaGenome

Unlike the other api calls this one does not return an api call instance. Instead, depending on the method used it will return
a sequence.Sequence, a variant.SequenceVariant, a ranges.GenomicRanges or just a dataframe or a list of dataframes. As the
name suggests, this class queries the [Alpha Genome server](https://www.alphagenomedocs.com/) and uses benchmate's class instances
to automatically convert to alphagenome's instances and back. In order to be able to use this module you will need an api key. 
You can get it through their website for free.

The three main prediction methods are below:

```python
from benchmate.apis import AlphaGenome
from benchmate.ranges import GenomicRange
from benchmate.variant import SequenceVariant
from benchmate.sequence import Sequence

# create the instance
ag=AlphaGenome(access_key="<your api key>")

# predict variant consequences
var1=SequenceVariant(chrom="chr22", pos=36201698, ref="A", alt="C")
var2=SequenceVariant(chrom="chr22", pos=36201698, ref="A", alt="T")
variants=[var1, var2]
variant_predictions=ag.predict_variant(variants, organism="human")

# predict features of a sequence
seq1=Sequence(name="seq1", sequence="GATTACA", seq_type="dna")
seq2=Sequence(name="seq2", sequence="GATTACAGATTACAGATTACA", seq_type="dna")
sequences=[seq1, seq2]
# pass specific ontology terms or None to query default ontologies
seq_predictions=ag.predict_sequence(sequences, ontology_terms=None, organism="human")

# predict features of genomic intervals
gr1=GenomicRange("chr22", 234234, 435345, "+")
gr2=GenomicRange("chr5", 2234, 4455, "+")
ranges=[gr1, gr2]
interval_predictions=ag.predict_interval(ranges, ontology_terms=None, organism="human")
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

