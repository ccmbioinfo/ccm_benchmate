import warnings

import sqlalchemy
from sqlalchemy.orm import sessionmaker
import pandas as pd

from Bio import Seq, SeqIO
import pysam

from ccm_benchmate.genome.tables import *
from ccm_benchmate.genome.utils import insert_genome
from ccm_benchmate.ranges.genomicranges import *


class Genome:
    def __init__(self, genome_fasta, gtf, name, description, db_conn,
                 transcriptome_fasta=None,
                 proteome_fasta=None):
        """
        :param gtf_path: Path to the GTF file
        :param genome_fasta: Path to the genome fasta file
        :param transcriptome_fasta:  Path to the transcriptome fasta file
        :param proteome_fasta: Path to the proteome fasta file
        :param db_conn: database connection object this is a sqlalchemy engine
        :param taxon_id: taxon id of the genome
        """
        self.db=db_conn
        self.session = sessionmaker(self.db)
        self.metadata = sqlalchemy.MetaData(self.db)
        self.metadata.reflect(bind=self.db)
        self.tables = self.metadata.tables
        self.gtf = gtf
        self.name = name
        self.description = description
        if genome_fasta is not None:
            self.genome_fasta = pysam.FastaFile(genome_fasta)
        else:
            self.genome_fasta=None
        if transcriptome_fasta is not None:
            self.transcriptome_fasta = pysam.FastaFile(transcriptome_fasta)
        else:
            self.transcriptome_fasta=None
        if proteome_fasta is not None:
            self.proteome_fasta=pysam.FastaFile(proteome_fasta)
        else:
            self.proteome_fasta=None

        if len(self.tables)==0:
            print("There are no tables in the database, creating tables and adding genome information")
            Base.metadata.create_all(self.db)
            self.metadata.reflect(bind=self.db)
            genome_id, chrom_ids = insert_genome(gtf=gtf, engine=self.db, name=self.name, description=self.description,
                                                 genome_fasta=genome_fasta, transcriptome_fasta=transcriptome_fasta, proteome_fasta=proteome_fasta,
                                                 )
        else:
            genome_id = pd.read_sql(
                f"select genome.id from genome where genome.genome_name='{self.name}'",
                con=self.db)
            genome_id = genome_id["id"].tolist()
            if len(genome_id)==0:
                print("The database has all the tables but this particular genome is not in the database, adding now")
                genome_id, chrom_ids=insert_genome(gtf=gtf, engine=self.db, name=self.name, description=self.description,
                                             genome_fasta=genome_fasta, transcriptome_fasta=transcriptome_fasta,
                                                   proteome_fasta=proteome_fasta)
            elif len(genome_id)==1:
                print(f"Found an existing genome with {name}, just setting things up, if this is an error re-initiate the class with a different name")
                chrom_ids = pd.read_sql(f"select id, chrom from chrom where genome_id={genome_id[0]}", con=self.db)
            else:
                raise ValueError(f"Found multiple genomes with the name {self.name}, this means a serious data integrity issue, please check your database. The genome ids are: {genome_id}")

        if self.genome_fasta is not None:
            self._check_chroms(chrom_ids)

        self.genome_id = genome_id
        self.chrom_ids=chrom_ids

    def genes(self, gene_ids=None, range=None):
        """
        Gene id or range if range is provided it will return the genes in that range depending on the overlap type
        :param id: Gene id, that used in the gtf file
        :param range: A GenomicRange object
        :param overlap_type: one of ['any', 'start', 'end', 'within'] see rangaes and genomicranges for more info
        :return: a GenomicRangesDict object with the genes in it, each key is the gene name and the value is a GenomicRange object
        """

        chroms_table = self.tables['chrom']
        genes_table = self.tables['gene']


        query = sqlalchemy.select(
            genes_table.c.gene_id,
            chroms_table.c.chrom,
            genes_table.c.start,
            genes_table.c.end,
            genes_table.c.strand,
            genes_table.c.annotations,
            genes_table.c.id
        ).join(
            chroms_table,
            genes_table.c.chrom_id == chroms_table.c.id
        )

        if gene_ids is not None:
            if type(gene_ids) is str:
                gene_ids = [gene_ids]
            query = query.filter(genes_table.c.gene_name.in_(gene_ids))


        if range is not None:
            query=query.filter(
                chroms_table.c.chrom == range.chrom,
                genes_table.c.strand == range.strand,
                genes_table.c.start>=range.ranges.start,
                genes_table.c.end<=range.ranges.end)

        result = self.session.execute(query).fetchall()
        ranges=[]
        keys=[]
        for item in result:
            gene_name = item[0]
            chrom = item[1]
            start = item[2]
            end = item[3]
            strand = item[4]
            annot = item[5]
            annot["db_id"] = item[6]
            ranges.append(GenomicRange(chrom, start, end, strand, annot))
            keys.append(gene_name)

        gdict = GenomicRangesDict(keys, ranges)
        return gdict

    def transcripts(self, gene_ids=None, ids=None, range=None):
        """
        same as genes
        :param gene_id:
        :param id:
        :param range:
        :param overlap_type:
        :return:
        """

        chroms_table = self.tables['chrom']
        genes_table = self.tables['gene']
        transcripts_table = self.tables['transcript']

        query = sqlalchemy.select(
            transcripts_table.c.id,
            chroms_table.c.chrom,
            transcripts_table.c.start,
            transcripts_table.c.end,
            genes_table.c.strand,
            transcripts_table.c.annotations,
            transcripts_table.c.transcript_id
        ).join(
            genes_table,
            transcripts_table.c.gene_id == genes_table.c.id
        ).join(
            chroms_table,
            genes_table.c.chrom_id == chroms_table.c.id
        )

        if gene_ids is not None:
            if type(gene_ids) is int:
                gene_ids = [gene_ids]
            query = query.filter(transcripts_table.c.gene_id.in_(gene_ids))

        if ids is not None:
            if type(ids) is int:
                ids = [ids]
            query = query.filter(transcripts_table.c.id.in_(ids))

        if range is not None:
            query=query.filter(
                chroms_table.c.chrom == range.chrom,
                genes_table.c.strand == range.strand,
                transcripts_table.c.start>=range.ranges.start,
                transcripts_table.c.end<=range.ranges.end)


        result = self.session.execute(query).fetchall()
        res_dict={}
        for item in result:
            chrom = item[1]
            start = item[2]
            end = item[3]
            strand = item[4]
            annot = item[5]
            annot["db_id"] = item[0]
            gene_id=annot["gene_id"]
            if gene_id not in res_dict.keys():
                res_dict[gene_id]=GenomicRangesList([])
            res_dict[gene_id].append(GenomicRange(chrom, start, end, strand, annot))

        gdict=GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict

    def exons(self, transcript_ids=None, ids=None, range=None):
        """
        same as genes but will need to search by transcript not gene, if you do not know the transcript search for it with transcripts first
        :param transcript_id:
        :param id:
        :param range:
        :param overlap_type:
        :return:
        """
        chroms_table = self.tables['chrom']
        genes_table = self.tables['gene']
        transcripts_table = self.tables['transcript']
        exons_table=self.tables['exon']

        query = (sqlalchemy.select(
            exons_table.c.id,
            exons_table.c.exon_id,
            chroms_table.c.chrom,
            exons_table.c.start,
            exons_table.c.end,
            genes_table.c.strand,
            exons_table.c.annotations,
            exons_table.c.transcript_id,
            exons_table.c.exon_number,
            transcripts_table.c.id
        ).join(
            transcripts_table,
            exons_table.c.transcript_id == transcripts_table.c.id
        ).join(
            genes_table,
            transcripts_table.c.gene_id == genes_table.c.id
        ).join(
            chroms_table,
            genes_table.c.chrom_id == chroms_table.c.id
        ))

        if transcript_ids is not None:
            if type(transcript_ids) is int:
                transcript_ids = [transcript_ids]
            query = query.filter(exons_table.c.transcript_id.in_(transcript_ids))


        if ids is not None:
            if type(ids) is int:
                ids = [ids]
            query = query.filter(exons_table.c.id.in_(ids))

        if range is not None:
            query=query.filter(
                chroms_table.c.chrom == range.chrom,
                genes_table.c.strand == range.strand,
                exons_table.c.start>=range.ranges.start,
                exons_table.c.end<=range.ranges.end)

        result = self.session.execute(query).fetchall()

        res_dict = {}
        for item in result:
            chrom = item[2]
            start = item[3]
            end = item[4]
            strand = item[5]
            annot = item[6]
            annot["db_id"] = item[0]
            tx_id = annot["transcript_id"]
            if tx_id not in res_dict.keys():
                res_dict[tx_id] = GenomicRangesList([])
            res_dict[tx_id].append(GenomicRange(chrom, start, end, strand, annot))

        gdict = GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict

    def coding(self, transcript_ids=None, ids=None, range=None):
        """
        same as exons
        :param transcript_id:
        :param id:
        :param range:
        :param overlap_type:
        :return:
        """

        chroms_table = self.tables['chrom']
        genes_table = self.tables['gene']
        transcripts_table = self.tables['transcript']
        exons_table=self.tables['exon']
        cds_table=self.tables['coding']

        query = (sqlalchemy.select(
            cds_table.c.id,
            cds_table.c.cds_id,
            chroms_table.c.chrom,
            cds_table.c.start,
            cds_table.c.end,
            genes_table.c.strand,
            cds_table.c.annotations,
            cds_table.c.exon_id,
            exons_table.c.transcript_id,
            transcripts_table.c.id
        ).join(
            exons_table,
            cds_table.c.exon_id == exons_table.c.id,
        ).join(
            transcripts_table,
            exons_table.c.transcript_id == transcripts_table.c.id
        ).join(
            genes_table,
            transcripts_table.c.gene_id == genes_table.c.id
        ).join(
            chroms_table,
            genes_table.c.chrom_id == chroms_table.c.id
        ))

        if transcript_ids is not None:
            if type(transcript_ids) is int:
                transcript_ids = [transcript_ids]
            query = query.filter(exons_table.c.id.in_(transcript_ids))


        if ids is not None:
            if type(ids) is int:
                ids = [ids]
            query = query.filter(cds_table.c.id.in_(ids))

        if range is not None:
            query=query.filter(
                chroms_table.c.chrom == range.chrom,
                genes_table.c.strand <= range.strand,
                cds_table.c.start>=range.ranges.start,
                cds_table.c.end<=range.ranges.end)

        result = self.session.execute(query).fetchall()

        res_dict = {}
        for item in result:
            chrom = item[2]
            start = item[3]
            end = item[4]
            strand = item[5]
            annot = item[6]
            annot["db_id"] = item[0]
            annot["db_exon_id"] = item[7]
            annot["db_transcript_id"] = item[9]
            tx_id = annot["transcript_id"]
            if tx_id not in res_dict.keys():
                res_dict[tx_id] = GenomicRangesList([])
            res_dict[tx_id].append(GenomicRange(chrom, start, end, strand, annot))

        gdict = GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict


    def three_utr(self, transcript_ids=None, ids=None, range=None):
        chroms_table = self.tables['chrom']
        genes_table = self.tables['gene']
        transcripts_table = self.tables['transcript']
        three_utr_table = self.tables['three_utr']

        query = (sqlalchemy.select(
            three_utr_table.c.id,
            chroms_table.c.chrom,
            three_utr_table.c.start,
            three_utr_table.c.end,
            genes_table.c.strand,
            three_utr_table.c.annotations,
            transcripts_table.c.id
        ).join(
            transcripts_table,
            three_utr_table.c.transcript_id == transcripts_table.c.id
        ).join(
            genes_table,
            transcripts_table.c.gene_id == genes_table.c.id
        ).join(
            chroms_table,
            genes_table.c.chrom_id == chroms_table.c.id
        ))

        if transcript_ids is not None:
            if type(transcript_ids) is int:
                transcript_ids = [transcript_ids]
            query = query.filter(transcripts_table.c.id.in_(transcript_ids))

        if ids is not None:
            if type(ids) is int:
                ids = [ids]
            query = query.filter(three_utr_table.c.id.in_(ids))

        if range is not None:
            query = query.filter(
                chroms_table.c.chrom == range.chrom,
                genes_table.c.strand <= range.strand,
                three_utr_table.c.start >= range.ranges.start,
                three_utr_table.c.end <= range.ranges.end)

        result = self.session.execute(query).fetchall()

        res_dict = {}
        for item in result:
            chrom = item[1]
            start = item[2]
            end = item[3]
            strand = item[4]
            annot = item[5]
            annot["db_id"] = item[0]
            annot["db_transcript_id"] = item[7]
            tx_id = annot["transcript_id"]
            if tx_id not in res_dict.keys():
                res_dict[tx_id] = GenomicRangesList([])
            res_dict[tx_id].append(GenomicRange(chrom, start, end, strand, annot))

        gdict = GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict


    def five_utr(self,  transcript_ids=None, ids=None, range=None):
        chroms_table = self.tables['chrom']
        genes_table = self.tables['gene']
        transcripts_table = self.tables['transcript']
        five_utr_table = self.tables['five_utr']

        query = (sqlalchemy.select(
            five_utr_table.c.id,
            chroms_table.c.chrom,
            five_utr_table.c.start,
            five_utr_table.c.end,
            genes_table.c.strand,
            five_utr_table.c.annotations,
            transcripts_table.c.id
        ).join(
            transcripts_table,
            five_utr_table.c.transcript_id == transcripts_table.c.id
        ).join(
            genes_table,
            transcripts_table.c.gene_id == genes_table.c.id
        ).join(
            chroms_table,
            genes_table.c.chrom_id == chroms_table.c.id
        ))

        if transcript_ids is not None:
            if type(transcript_ids) is int:
                transcript_ids = [transcript_ids]
            query = query.filter(transcripts_table.c.id.in_(transcript_ids))

        if ids is not None:
            if type(ids) is int:
                ids = [ids]
            query = query.filter(five_utr_table.c.id.in_(ids))

        if range is not None:
            query = query.filter(
                chroms_table.c.chrom == range.chrom,
                genes_table.c.strand == range.strand,
                five_utr_table.c.start >= range.ranges.start,
                five_utr_table.c.end <= range.ranges.end)

        result = self.session.execute(query).fetchall()

        res_dict = {}
        for item in result:
            chrom = item[1]
            start = item[2]
            end = item[3]
            strand = item[4]
            annot = item[5]
            annot["db_id"] = item[0]
            annot["db_transcript_id"] = item[6]
            tx_id = annot["transcript_id"]
            if tx_id not in res_dict.keys():
                res_dict[tx_id] = GenomicRangesList([])
            res_dict[tx_id].append(GenomicRange(chrom, start, end, strand, annot))

        gdict = GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict

    def introns(self, transcript_ids=None, ids=None, range=None):
        """
        same as exons
        :param transcript_id:
        :param id:
        :param range:
        :param overlap_type:
        :return:
        """

        chroms_table = self.tables['chrom']
        genes_table = self.tables['gene']
        transcripts_table = self.tables['transcript']
        introns_table = self.tables['intron']

        query = (sqlalchemy.select(
            introns_table.c.id,
            chroms_table.c.chrom,
            introns_table.c.start,
            introns_table.c.end,
            genes_table.c.strand,
            introns_table.c.annotations,
            introns_table.c.transcript_id,
            transcripts_table.c.id,
            transcripts_table.c.transcript_id
        ).join(
            transcripts_table,
            introns_table.c.transcript_id == transcripts_table.c.id,
        ).join(
            genes_table,
            transcripts_table.c.gene_id == genes_table.c.id
        ).join(
            chroms_table,
            genes_table.c.chrom_id == chroms_table.c.id
        ))

        if transcript_ids is not None:
            if type(transcript_ids) is int:
                transcript_ids = [transcript_ids]
            query = query.filter(transcripts_table.c.transcript_id.in_(transcript_ids))

        if ids is not None:
            if type(ids) is int:
                ids = [ids]
            query = query.filter(introns_table.c.id.in_(ids))

        if range is not None:
            query = query.filter(
                chroms_table.c.chrom == range.chrom,
                genes_table.c.strand == range.strand,
                introns_table.c.start >= range.ranges.start,
                introns_table.c.end <= range.ranges.end)

        result = self.session.execute(query).fetchall()

        res_dict = {}
        for item in result:
            chrom = item[1]
            start = item[2]
            end = item[3]
            strand = item[4]
            annot = item[5]
            annot["db_id"] = item[0]
            annot["db_transcript_id"] = item[7]
            annot["transcript_id"] = item[8]
            tx_id = annot["transcript_id"]
            if tx_id not in res_dict.keys():
                res_dict[tx_id] = GenomicRangesList([])
            res_dict[tx_id].append(GenomicRange(chrom, start, end, strand, annot))

        gdict = GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict

    def get_sequence(self, genomic_range, type='genome'):
        """
        Get the sequence of a genomic range. This takes a single genomc range you can iterate over a GenomicRangeList or GenomicRangeDict
        :param genomic_range: GenomicRange object
        :return: sequence as string
        """
        if type == 'genome':
            file= self.genome_fasta
        elif type == 'transcriptome':
            file=self.transcriptome_fasta
        elif type == 'proteome':
            file=self.proteome_fasta

        if genomic_range.chrom not in file.references:
            raise ValueError(f"Chromosome {genomic_range.chromosome} not found in genome fasta file.")
        start = genomic_range.ranges.start
        end = genomic_range.ranges.end
        strand = genomic_range.strand
        seq = file.fetch(genomic_range.chrom, start, end)
        if strand == '-':
            seq = str(Seq.Seq(seq).reverse_complement())
        return seq

    def add_annotation(self, table, row_id, annots):
        """
        add arbitrary annotations as a dictionary to a specific row in a specific table
        :param table:
        :param id:
        :param annots:
        :return:
        """
        if type(annots) != dict:
            raise ValueError(f"Annotation type {type(annots)} not supported. They must be dictionaries")

        if table=="gene":
            table=self.tables['gene']
        elif table=="transcript":
            table=self.tables['transcript']
        elif table=="exon":
            table=self.tables['exon']
        elif table=="cds":
            table=self.tables['cds']
        elif table=="three_utr":
            table=self.tables['three_utr']
        elif table=="five_utr":
            table=self.tables['five_utr']
        elif table=="intron":
            table=self.tables['intron']
        else:
            raise ValueError(f"Table {table} is not a valid table.")

        try:
            row_id=int(row_id)
        except:
            raise ValueError(f"Row {row_id} is not a valid row id. It must be an integer")


        id_check=sqlalchemy.select(table).where(table.c.id==id)
        results=self.session.execute(id_check).fetchall()
        if results is not None:
            current_annots=sqlalchemy.select(table.c.annot).where(table.c.id==row_id).fetchall()
            current_annots=current_annots[0]
            if current_annots is None:
                current_annots=annots
            else:
                for key, value in annots.items():
                    if key not in current_annots:
                        current_annots[key]=value
                    else:
                        raise ValueError(f"Annotation key {key} is already in database.")
            try:
                sqlalchemy.update(table.c.annot).where(table.c.id==row_id).values(current_annots)
            except Exception as e:
                print(f"There was an error in updating the annotations: {e}")
        else:
            raise ValueError("The id returned 0 row, please make sure that the id you provided is correct")

    def _check_chroms(self, genome_chroms):
        fasta_chroms = self.genome_fasta.references
        for ref in fasta_chroms:
            if ref not in genome_chroms["chrom"].tolist():
                warnings.warn(
                    f"""Chromosome {ref} not found in the database, this step is not critical for database generation 
                    but it will effect sequence retrieval. If you are creating a new database, you may want to 
                    re-initialize the class with a different genome fasta file.""")

    def __str__(self):
        return f"Genome: for : {self.name}"

    def __repr__(self):
        return f"Genome: for : {self.name} with {self.genome_id} and fasta file {self.genome_fasta}"



