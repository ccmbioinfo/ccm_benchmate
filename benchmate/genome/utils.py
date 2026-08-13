from dataclasses import dataclass

import pandas as pd
from tqdm import tqdm
import json

from sqlalchemy import select, insert

from benchmate.ranges import GenomicRange, GenomicRangesList, GenomicRangesDict
from benchmate.genome.genome import Genome


#TODO annotations matching

def parse_gtf_attributes(attributes_str):
    """
    parse the gtf attributes column that is the last one
    :param attributes_str:
    :return:
    """
    attributes = {}
    for item in attributes_str.strip().split(';'):
        item = item.strip()
        if not item:
            continue
        parts = item.split(' ', 1)
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip().strip('"')
            attributes[key] = value
    return attributes

def parse_gtf(filepath):
    """
    for a given gtf file parse all the fields and get them ready for db insertion, this needs to be done once per genome
    this gets called by the genome class instances, there is no need for the end user to call this
    :param filepath: path for the gtf file
    :return: a list of all used genomic features
    """
    gene_list = []
    transcript_list = []
    exon_list = []
    cds_list = []
    three_utr_list = []
    five_utr_list = []

    gene_fields=["gene_id"]
    transcript_fields=["transcript_id", "gene_id"]
    exon_fields=["exon_id", "exon_number", "transcript_id"]
    coding_fields=["exon_number", "transcript_id", "ccds_id"] # so I need to match this with the exon field
    three_utr_fields=["transcript_id"]
    five_utr_fields=["transcript_id"]

    chrom_list=[]
    with open(filepath, 'r') as gtf_file:
        for line in tqdm(gtf_file, desc="Parsing GTF file", unit=" lines processed"):
            if line.startswith('#') or not line.strip():
                continue
            fields = line.strip().split('\t')

            if len(fields) != 9:
                continue

            fields = line.strip().split('\t')
            chrom_name = fields[0]
            if chrom_name not in chrom_list:
                chrom_list.append(chrom_name)

            feature_type = fields[2]
            start = int(fields[3])
            end = int(fields[4])
            strand = fields[6]
            phase = fields[7]
            attributes_str = fields[8]
            attributes = parse_gtf_attributes(attributes_str)
            line={"chrom":chrom_name,
                         "type":feature_type,
                         "start":start,
                         "end":end,
                         "strand":strand,
                         "phase":phase,
                         "annotations":attributes
                         }

            if line["type"] == "gene":
                gene_line=line
                gene_line={key: gene_line[key] for key in ["chrom", "start", "end", "strand", "annotations"]}
                for field in gene_fields:
                    try:
                        gene_line[field]=gene_line["annotations"][field]
                    except:
                        continue
                gene_list.append(gene_line)
            elif line["type"] == "transcript":
                transcript_line=line
                transcript_line = {key: transcript_line[key] for key in ["start", "end", "annotations"]}
                for field in transcript_fields:
                    try:
                        transcript_line[field]=line["annotations"][field]
                    except:
                        continue
                transcript_list.append(transcript_line)
            elif line["type"] == "exon":
                exon_line=line
                exon_line = {key: exon_line[key] for key in ["start", "end", "annotations"]}
                for field in exon_fields:
                    try:
                        exon_line[field]=line["annotations"][field]
                    except:
                        continue
                if "exon_id" not in exon_line:
                    tx_id = exon_line.get("transcript_id", "tx")
                    exon_num = exon_line.get("exon_number", len(exon_list) + 1)
                    exon_line["exon_id"] = f"{tx_id}_exon_{exon_num}"
                exon_list.append(exon_line)
            elif line["type"] == "CDS":
                coding_line=line
                coding_line = {key: coding_line[key] for key in ["start", "end", "annotations", "phase"]}
                for field in coding_fields:
                    try:
                        coding_line[field]=line["annotations"][field]
                    except:
                        continue
                cds_list.append(coding_line)
            elif line["type"] in ["three_prime_utr", "3UTR"]:
                three_utr_line=line
                three_utr_line = {key: three_utr_line[key] for key in ["start", "end", "annotations"]}
                for field in three_utr_fields:
                    try:
                        three_utr_line[field]=line["annotations"][field]
                    except:
                        continue
                three_utr_list.append(three_utr_line)
            elif line["type"] in ["five_prime_utr", "5UTR"]:
                five_utr_line = line
                five_utr_line = {key: five_utr_line[key] for key in ["start", "end", "annotations"]}
                for field in five_utr_fields:
                    try:
                        five_utr_line[field] = line["annotations"][field]
                    except:
                        continue
                five_utr_list.append(five_utr_line)
            else:
                continue

    return (chrom_list, gene_list, transcript_list, exon_list, cds_list,
            three_utr_list, five_utr_list)

def start_genome(genome_name, genome_fasta_file, engine, transcriptome_fasta_file=None,
                 proteome_fasta_file=None, description=None):
    """
    load a genome instance, this is called by the genome instance
    :param genome_name: name of the genome
    :param genome_fasta_file: name of the fasta file to be used
    :param engine: connection engine used by sqlalchemy, you are responsible for creating this
    :param transcriptome_fasta_file: optional transcritome file
    :param proteome_fasta_file: optional proteome file
    :param description: description of the genome
    :return: return genome id, this will be used to add other things to the genome db
    """
    df_genome=pd.DataFrame({"genome_name":[genome_name],
                            "genome_fasta_file":[genome_fasta_file],
                            "transcriptome_fasta_file":[transcriptome_fasta_file],
                            "proteome_fasta_file":[proteome_fasta_file],
                            "description":[description],})
    df_genome.to_sql("genome", if_exists='append', index=False, con=engine)
    genome_id = pd.read_sql(
        f"select id from genome where genome_name=\'{df_genome['genome_name'].tolist()[0]}\'",
        con=engine)
    genome_id=genome_id["id"].tolist()[0]
    return genome_id

def insert_chroms(genome_id, chrom_list, engine):
    """
    insert chrom info for a specific genome, given its id
    :param genome_id: see above,
    :param chrom_list: list of chrom ids
    :param engine: connection engine
    :return: inserted chrom ids, these will be used to insert other features
    """
    chrom_df=pd.DataFrame({"chrom":chrom_list})
    chrom_df["genome_id"]=genome_id
    chrom_df.to_sql("chrom", con=engine, if_exists='append', index=False)
    chrom_ids = pd.read_sql(f"select id, chrom from chrom where genome_id='{genome_id}'", con=engine)
    return chrom_ids

def insert_genes(chrom_ids, gene_list, engine):
    """
    insert genes
    :param chrom_ids: see above
    :param gene_list: list of genes to inser
    :param engine: connection engine
    :return: list of gene ids (not gene names or gene unique ids, this is specific to the db)
    """
    genes=pd.DataFrame(gene_list)
    if genes.empty:
        return pd.DataFrame(columns=["id", "gene_id"])
    genes=genes.merge(chrom_ids, on="chrom", how="left").drop(columns=["chrom"]).rename(columns={"id":"chrom_id"})
    genes['annotations'] = genes['annotations'].apply(lambda x: json.dumps(x, ensure_ascii=False))
    genes.to_sql("gene", con=engine, if_exists='append', index=False)
    gene_ids=pd.read_sql(
        f"select id, gene_id from gene where chrom_id in ({','.join(chrom_ids['id'].astype(str).tolist())})",
        con=engine)
    return gene_ids

def insert_transcripts(gene_ids, tx_list, engine):
    """
    insert transcripts for each gene id
    :param gene_ids: see above
    :param tx_list: list of transcripts
    :param engine: connection engine
    :return: list of db ids for all the inserted transcripts
    """
    transcripts=pd.DataFrame(tx_list)
    if transcripts.empty:
        return pd.DataFrame(columns=["id", "transcript_id"])
    transcripts=transcripts.merge(gene_ids, on="gene_id", how="left").drop(columns=["gene_id"]).rename(columns={"id":"gene_id"})
    transcripts['annotations'] = transcripts['annotations'].apply(lambda x: json.dumps(x, ensure_ascii=False))
    transcripts.to_sql("transcript", if_exists='append', index=False, con=engine)
    transcript_ids = pd.read_sql(
        f"select id, transcript_id from transcript where gene_id in ({','.join(gene_ids['id'].astype(str).tolist())})",
        con=engine)
    return transcript_ids

def insert_exons(transcript_ids, exon_list, engine):
    """
    insert exons for each transcript
    :param transcript_ids: see above
    :param exon_list: list of exons
    :param engine: connection engine
    :return: list of db ids for all the inserted exons
    """
    exons=pd.DataFrame(exon_list)
    if exons.empty:
        return pd.DataFrame(columns=["id", "exon_number", "transcript_id"])
    exons=exons.merge(transcript_ids, on="transcript_id", how="left").drop(columns=["transcript_id"]).rename(columns={"id":"transcript_id"})
    exons['annotations'] = exons['annotations'].apply(lambda x: json.dumps(x, ensure_ascii=False))
    exons.to_sql("exon", con=engine, if_exists='append', index=False)
    exon_ids = pd.read_sql(f"select id, exon_number, transcript_id from exon where transcript_id in ({','.join(transcript_ids['id'].astype(str).tolist())})", con=engine)
    return exon_ids

def insert_three_utrs(transcript_ids, three_utr_list, engine):
    """
    insert three_utrs
    :param transcript_ids: see above
    :param three_utr_list: see above
    :param engine: connection engine
    :return: list of db ids for all the inserted three_utrs
    """
    three_utrs=pd.DataFrame(three_utr_list)
    if not three_utrs.empty and not transcript_ids.empty:
        three_utrs=three_utrs.merge(transcript_ids, on="transcript_id", how="left").drop(columns=["transcript_id"]).rename(columns={"id":"transcript_id"})
        three_utrs['annotations'] = three_utrs['annotations'].apply(lambda x: json.dumps(x, ensure_ascii=False))
        three_utrs.to_sql("three_utr", con=engine, if_exists='append', index=False)

def insert_five_utrs(transcript_ids, five_utr_list, engine):
    """
    insert five_utrs
    :param transcript_ids: see above
    :param five_utr_list: see above
    :param engine: connection engine
    :return: list of db ids for all the inserted five_utrs
    """
    five_utrs = pd.DataFrame(five_utr_list)
    if not five_utrs.empty and not transcript_ids.empty:
        five_utrs = five_utrs.merge(transcript_ids, on="transcript_id", how="left").drop(columns=["transcript_id"]).rename(columns={"id":"transcript_id"})
        five_utrs['annotations'] = five_utrs['annotations'].apply(lambda x: json.dumps(x, ensure_ascii=False))
        five_utrs.to_sql("five_utr", con=engine, if_exists='append', index=False)

def insert_coding(transcript_ids, exon_ids, coding_list, engine):
    """
    insert coding regions, this tracks not only transcripts but also which cds belongs to which exon
    :param transcript_ids: see above
    :param exon_ids: see above
    :param coding_list: see above
    :param engine: connection engine
    :return: list of db ids for all the inserted coding regions
    """
    coding=pd.DataFrame(coding_list)
    if coding.empty or transcript_ids.empty or exon_ids.empty:
        return
    coding=coding.merge(transcript_ids, on="transcript_id", how="left").rename(columns={"transcript_id":"transcript_name", "id":"transcript_id"})
    if "exon_number" in coding.columns and "exon_number" in exon_ids.columns:
        coding["exon_number"] = pd.to_numeric(coding["exon_number"], errors="coerce")
        exon_ids_copy = exon_ids.copy()
        exon_ids_copy["exon_number"] = pd.to_numeric(exon_ids_copy["exon_number"], errors="coerce")
        coding=coding.merge(exon_ids_copy[["transcript_id", "exon_number", "id"]], on=["transcript_id", "exon_number"], how="left").drop(columns=["transcript_id", "exon_number"]).rename(columns={"id":"exon_id"})
    else:
        coding=coding.merge(exon_ids[["transcript_id", "id"]], on="transcript_id", how="left").drop(columns=["transcript_id"]).rename(columns={"id":"exon_id"})

    coding['annotations'] = coding['annotations'].apply(lambda x: json.dumps(x, ensure_ascii=False))
    if "transcript_name" in coding.columns:
        coding=coding.drop(columns=["transcript_name"])
    coding.to_sql("coding", con=engine, if_exists='append', index=False)

def insert_introns(transcript_ids, exon_list, engine):
    """
    insert introns, since there is no intron information they are calculated before insertion by grouping things
    by transcript and then calculating the missing areas in each exon for each transcript
    :param transcript_ids: see above
    :param exon_list: see above
    :param engine: connection engine
    :return: list of db ids for all the inserted introns
    """
    if not exon_list or transcript_ids.empty:
        return
    df_exons = pd.DataFrame(exon_list)
    if df_exons.empty:
        return
    exons=df_exons.merge(transcript_ids, on="transcript_id", how="left").\
        drop(columns=["transcript_id"]).rename(columns={"id":"transcript_id"})
    if "exon_number" in exons.columns:
        exons["exon_number"] = pd.to_numeric(exons["exon_number"], errors="coerce")
    exons = exons.groupby(["transcript_id"])
    introns=[]
    for tx, data in exons:
        tx_id = tx[0] if isinstance(tx, (tuple, list)) else tx
        if "exon_number" in data.columns:
            data=data.sort_values(by=["exon_number"])
        else:
            data=data.sort_values(by=["start"])
        for i in range(data.shape[0] - 1):
            exon1_start, exon1_end = int(data.iloc[i].start), int(data.iloc[i].end)
            exon2_start, exon2_end = int(data.iloc[i + 1].start), int(data.iloc[i + 1].end)
            intron_start = exon1_end + 1
            intron_end = exon2_start - 1
            if intron_start <= intron_end:
                introns.append({
                    'transcript_id': tx_id, 'intron_rank': i + 1,
                    'start': intron_start, 'end': intron_end
                })
            else:
                # Skip invalid or negative-length introns resulting from overlapping/out-of-order exons
                continue
    introns=pd.DataFrame(introns)
    if not introns.empty:
        introns["annotations"]= '{}'
        introns.to_sql("intron", con=engine, if_exists='append', index=False)


def insert_genome(gtf, engine, name, description, genome_fasta,
                  transcriptome_fasta=None, proteome_fasta=None):
    """
    this takes a gtf file and inserts all the available features
    :param gtf: gtf file
    :param engine: connection engine
    :param name: name of the genome
    :param description: description of the genome
    :param genome_fasta: fasta file
    :param transcriptome_fasta: transcriptome fasta file
    :param proteome_fasta: proteome fasta file
    :return: genome and chrom ids
    """
    print("Initializing genome database")
    genome_id=start_genome(genome_name=name, genome_fasta_file=genome_fasta,
                           engine=engine, transcriptome_fasta_file=transcriptome_fasta,
                           proteome_fasta_file=proteome_fasta, description=description)
    print("Reading GTF file")
    chrom_list, gene_list, transcript_list, exon_list, cds_list, three_utr_list, five_utr_list = parse_gtf(gtf)
    print("Inserting genome data into database")
    chrom_ids=insert_chroms(genome_id, chrom_list, engine)
    gene_ids=insert_genes(chrom_ids, gene_list, engine)
    transcript_ids=insert_transcripts(gene_ids, transcript_list, engine)
    exon_ids=insert_exons(transcript_ids, exon_list, engine)
    insert_three_utrs(transcript_ids, three_utr_list, engine)
    insert_five_utrs(transcript_ids, five_utr_list, engine)
    insert_coding(transcript_ids, exon_ids, cds_list, engine)
    insert_introns(transcript_ids, exon_list, engine)
    print("Finished genome database")
    return genome_id, chrom_ids


