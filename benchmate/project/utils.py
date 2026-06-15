type_dict={
    "api_call":{
        "table":"api_call",
        "columns":["id", "class_name", "method_name", "query_time"]
    },
    "paper":{
        "table":"papers",
        "columns":["id", "title", "venue", "publication_date"]
    },
    "genome":{
        "table":"genome",
        "columns":["id", "name", "description",]
    },
    "sequence":{
        "table":"sequence",
        "columns":["id", "name", "sequence", "type", "hash"]
    },
    "structure":{
        "table":"structure",
        "columns":["id", "name", "hash"]
    },
    "molecule":{
        "table":"molecule",
        "columns":["id", "name", "smiles"]
    },
    "sequencevariant":{
        "table":"sequencevariant",
        "columns":["id", "chrom", "pos", "ref", "alt"]
    },
    "structurevariant":{
        "table":"structurevariant",
        "columns":["id", "chrom", "pos", "ref", "alt"]
    },
    "tandemrepeatvariant":{
        "table":"tandemrepeatvariant",
        "columns":["id", "chrom", "pos", "ref", "alt"]
    }
}