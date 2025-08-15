import pandas as pd
from tqdm import tqdm
import json



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
    gene_list = []
    transcript_list = []
    exon_list = []
    cds_list = []
    three_utr_list = []
    five_utr_list = []

    gene_fields=["gene_id"]
    transcript_fields=["transcript_id", "gene_id"]
    exon_fields=["exon_id", "exon_number", "transcript_id"]
    coding_fields=["exon_number", "transcript_id"] # so I need to match this with the exon field
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
                    gene_line[field]=gene_line["annotations"][field]
                gene_list.append(gene_line)
            elif line["type"] == "transcript":
                transcript_line=line
                transcript_line = {key: transcript_line[key] for key in ["start", "end", "annotations"]}
                for field in transcript_fields:
                    transcript_line[field]=line["annotations"][field]
                transcript_list.append(transcript_line)
            elif line["type"] == "exon":
                exon_line=line
                exon_line = {key: exon_line[key] for key in ["start", "end", "annotations"]}
                for field in exon_fields:
                    exon_line[field]=line["annotations"][field]
                exon_list.append(exon_line)
            elif line["type"] == "CDS":
                coding_line=line
                coding_line = {key: coding_line[key] for key in ["start", "end", "annotations", "phase"]}
                for field in coding_fields:
                    coding_line[field]=line["annotations"][field]
                cds_list.append(coding_line)
            elif line["type"] == "three_prime_utr":
                three_utr_line=line
                three_utr_line = {key: three_utr_line[key] for key in ["start", "end", "annotations"]}
                for field in three_utr_fields:
                    three_utr_line[field]=line["annotations"][field]
                three_utr_list.append(three_utr_line)
            elif line["type"] == "five_prime_utr":
                five_utr_line = line
                five_utr_line = {key: five_utr_line[key] for key in ["start", "end", "annotations"]}
                for field in five_utr_fields:
                    five_utr_line[field] = line["annotations"][field]
                five_utr_list.append(five_utr_line)
            else:
                continue

    return (chrom_list, gene_list, transcript_list, exon_list, cds_list,
            three_utr_list, five_utr_list)

def start_genome(genome_name, genome_fasta_file, engine, transcriptome_fasta_file=None,
                 proteome_fasta_file=None, description=None):
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
    chrom_df=pd.DataFrame({"chrom":chrom_list})
    chrom_df["genome_id"]=genome_id
    chrom_df.to_sql("chrom", con=engine, if_exists='append', index=False)
    chrom_ids = pd.read_sql(f"select id, chrom from chrom where genome_id='{genome_id}'", con=engine)
    return chrom_ids

def insert_genes(chrom_ids, gene_list, engine):
    genes=pd.DataFrame(gene_list)
    genes=genes.merge(chrom_ids, on="chrom", how="left").drop(columns=["chrom"]).rename(columns={"id":"chrom_id"})
    genes['annotations'] = genes['annotations'].apply(lambda x: json.dumps(x, ensure_ascii=False))
    genes.to_sql("gene", con=engine, if_exists='append', index=False)
    gene_ids=pd.read_sql(
        f"select id, gene_id from gene where chrom_id in ({','.join(chrom_ids['id'].astype(str).tolist())})",
        con=engine)
    return gene_ids

def insert_transcripts(gene_ids, tx_list, engine):
    transcripts=pd.DataFrame(tx_list)
    transcripts=transcripts.merge(gene_ids, on="gene_id", how="left").drop(columns=["gene_id"]).rename(columns={"id":"gene_id"})
    transcripts['annotations'] = transcripts['annotations'].apply(lambda x: json.dumps(x, ensure_ascii=False))
    transcripts.to_sql("transcript", if_exists='append', index=False, con=engine)
    transcript_ids = pd.read_sql(
        f"select id, transcript_id from transcript where gene_id in ({','.join(gene_ids['id'].astype(str).tolist())})",
        con=engine)
    return transcript_ids

def insert_exons(transcript_ids, exon_list, engine):
    exons=pd.DataFrame(exon_list)
    exons=exons.merge(transcript_ids, on="transcript_id", how="left").drop(columns=["transcript_id"]).rename(columns={"id":"transcript_id"})
    exons['annotations'] = exons['annotations'].apply(lambda x: json.dumps(x, ensure_ascii=False))
    exons.to_sql("exon", con=engine, if_exists='append', index=False)
    exon_ids = pd.read_sql(f"select id, exon_number, transcript_id from exon where transcript_id in ({','.join(transcript_ids['id'].astype(str).tolist())})", con=engine)
    return exon_ids

def insert_three_utrs(transcript_ids, three_utr_list, engine):
    three_utrs=pd.DataFrame(three_utr_list)
    if not three_utrs.empty:
        three_utrs=three_utrs.merge(transcript_ids, on="transcript_id", how="left").drop(columns=["transcript_id"]).rename(columns={"id":"transcript_id"})
        three_utrs['annotations'] = three_utrs['annotations'].apply(lambda x: json.dumps(x, ensure_ascii=False))
        three_utrs.to_sql("three_utr", con=engine, if_exists='append', index=False)

def insert_five_utrs(transcript_ids, five_utr_list, engine):
    five_utrs = pd.DataFrame(five_utr_list)
    if not five_utrs.empty:
        five_utrs = five_utrs.merge(transcript_ids, on="transcript_id", how="left").drop(columns=["transcript_id"]).rename(columns={"id":"transcript_id"})
        five_utrs['annotations'] = five_utrs['annotations'].apply(lambda x: json.dumps(x, ensure_ascii=False))
        five_utrs.to_sql("five_utrs", con=engine, if_exists='append', index=False)

def insert_coding(transcript_ids, exon_ids, coding_list, engine):
    coding=pd.DataFrame(coding_list)
    coding=coding.merge(transcript_ids, on="transcript_id", how="left").rename(columns={"transcript_id":"transcript_name", "id":"transcript_id"})
    coding=coding.merge(exon_ids[["transcript_id", "id"]], on="transcript_id", how="left").drop(columns=["transcript_id", "exon_number"]).rename(columns={"id":"exon_id"})
    coding['annotations'] = coding['annotations'].apply(lambda x: json.dumps(x, ensure_ascii=False))
    coding=coding.drop(columns=["transcript_name"])
    coding.to_sql("coding", con=engine, if_exists='append', index=False)

def insert_introns(transcript_ids, exon_list, engine):
    exons=pd.DataFrame(exon_list).merge(transcript_ids, on="transcript_id", how="left").\
        drop(columns=["transcript_id"]).rename(columns={"id":"transcript_id"}).groupby(["transcript_id"])
    introns=[]
    for tx, data in exons:
        data=data.sort_values(by=["exon_number"])
        for i in range(data.shape[0] - 1):
            exon1_start, exon1_end = data.iloc[i].start, data.iloc[i].end
            exon2_start, exon2_end = data.iloc[i + 1].start, data.iloc[i + 1].end
            intron_start = exon1_end + 1
            intron_end = exon2_start - 1
            if intron_start < intron_end:  # the transcript is on the + strand
                introns.append({
                    'transcript_id': tx[0], 'intron_rank': i + 1,
                    'start': intron_start, 'end': intron_end
                })
            else:  # on the - strand
                introns.append({
                    'transcript_id': tx[0], 'intron_rank': i + 1,
                    'start': intron_end, 'end': intron_end
                })
    introns=pd.DataFrame(introns)
    introns["annotations"]= '{}'
    #introns['annotations'] = introns['annotations'].apply(lambda x: json.dumps(x, ensure_ascii=False))
    if not introns.empty:
        introns.to_sql("intron", con=engine, if_exists='append', index=False)


def insert_genome(gtf, engine, name, description, genome_fasta,
                  transcriptome_fasta=None, proteome_fasta=None):
    print("Initializing genome database")
    genome_id=start_genome(genome_name=name, genome_fasta_file=genome_fasta,
                           engine=engine, transcriptome_fasta_file=transcriptome_fasta,
                           proteome_fasta_file=proteome_fasta, description=description)
    print("Readig GTF file")
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




