---
layout: default
title: EBI Tools and DBFetch
parent: APIs
grand_parent: Modules
nav_order: 10
---

# EBI Python Client Documentation

This module provides a unified, structured interface for interacting with the **European Bioinformatics Institute (EBI)** REST services. 
It encapsulates asynchronous job submission for analytical tools and synchronous data retrieval via `dbfetch`. 

There are some overlaps with ebfetch and other api endpoints, that are implemented in benchmate. Whenever that is the case
like uniprot it is recommended to use the dedicated api endpoint because it provides better structured data and better error handling.



## 1. Supported Tools Overview

The client supports several EMBOSS, HMMER, and specialized domain tools.

| Tool | Category | Description |
| :--- | :--- | :--- |
| **pepinfo** | Protein Stats | Plots amino acid properties (hydrophobicity, size, charge). |
| **pepstats** | Protein Stats | Calculates molecular weight, pI, and amino acid composition. |
| **pepwindow** | Protein Stats | Draws hydropathy plots (Kyte-Doolittle). |
| **saps** | Protein Stats | Detailed statistical analysis of protein sequence properties. |
| **isochore** | Genomics | Plots large-scale genomic GC content heterogeneity. |
| **hmmscan** | Homology | Searches protein sequences against profile HMM libraries (e.g., Pfam). |
| **phmmer** | Homology | Protein sequence vs. protein database search (HMMER). |
| **nhmmer** | Homology | DNA/RNA sequence vs. nucleotide database search (HMMER). |
| **cmscan** | RNA Analysis | Covariance Model searching for structural RNA (Infernal). |
| **iprscan** | Annotation | Comprehensive functional annotation via InterProScan 5. |
| **pfamscan** | Annotation | Specific domain architecture scanning against Pfam. |
| **phobius** | Prediction | Combined transmembrane topology and signal peptide predictor. |
| **pratt** | Motifs | De novo conserved pattern discovery in unaligned sequences. |
| **radar** | Repeats | Detection and alignment of complex internal protein repeats. |

The ebi client endpoins support a large number of tools but a lot of them are for pairwise or multiple sequence alignments.
These tools are not supported here but if you want to add to the clients you can create a pull request.

The main rationale behind not supporting these tools is that `benchmate.sequence.sequence.SequenceLlist` support ClustalOmega,
and you can use blast, foldseek and mmseqs2 in `benchmate.alignment.alignment.Alignment`

## 2. Core Usage

The primary interface is the `EBI` class. Because EBI tools are shared resources, an **email address** is required for job tracking
and sending notifications to users when they exceed their quota.

### Initialization
```python
from benchmate.apis import EBI

# Initialize the master wrapper
ebi = EBI(email="your.email@example.com")
```

### Analytical Job Workflow
Running a tool involves three stages: parameter discovery, job submission, and result retrieval.

```python
from time import sleep

# 1. Discover parameters for a tool (e.g., phobius)
params = ebi.get_client_params("phobius")
# Get specifics on a parameter like 'format' or 'stype'
details = ebi.get_client_param_details("phobius", "sequence")

# 2. Run the client
# Note: 'email' is handled automatically by the wrapper
my_params = {"sequence": ">SeqName\nMAARL...""}
job = ebi.run_client("phobius", params=my_params)

# 3. Monitor and Retrieve
while True:
    status = ebi.get_client_status(job)
    print(f"Current Status: {status}")
    
    if status == "FINISHED":
        break
    elif status in ["ERROR", "FAILURE"]:
        raise Exception("Job failed on EBI server")
    sleep(5)

# 4. Fetch specific result types
# To see available types: print(job.result_names)
out_data = ebi.get_client_result(job, "out") # returns bytes
```

The ebi clients can return many different types of data. These range from simple text to structure json or xml to image. 
When you submit a job it returns a `benchmate.apis.ebi.Job` object that can be used to monitor the job status and retrieve results.
You can also pass the job instance to `ebi.get_client_result_typess` to see what kinds of results are available. After this you 
will need to pass the ressult "indentifier" in the returned dict to `ebi.get_client_result` to retrieve the actual data.

Because the results can be many different types, the `ebi.get_client_result` method returns bytes by default. Because you will know  
the kind of data you are getting, you can then convert it to the appriate type depending on your needs. 

## 3. Database Retrieval (dbfetch)

In addition to analytical tools, the EBI client also supports direct database retrieval via `dbfetch`. This supports quite
a few different databases and formats. Similar to the analytical tools, you can see what databases are available and what formats are supported.
with the `dbfetch_databses`. This returns a nested dict with the database information and the supported formats that it can return. 

`dbfetch` is used for direct entry retrieval from databases like UniProt, ENA, or PDB, however as mentioned above it is better
to use the dedicated api endpoints whenever they are available.

```python
# List available databases
dbs = ebi.dbfetch_databses

# Fetch a specific record
# Example: Fetching P12345 from UniProt in FASTA format
entry = ebi.search_database(
    query="P12345",
    database="uniprotkb",
    format="fasta",
    style="raw"
)

# entry.data contains the raw bytes
print(entry.data.decode("utf-8"))
```


