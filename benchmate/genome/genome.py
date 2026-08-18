from functools import cached_property
import warnings
import json
import logging
import os.path
import warnings
from typing import Union, Dict, List

import pandas as pd
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from Bio import Seq
import pysam

from benchmate.genome.tables import *
from benchmate.genome.utils import insert_genome
from benchmate.ranges.genomicranges import *

logger = logging.getLogger(__name__)

class Genome:
    def __init__(self, name, description, genome_fasta, gtf,
                 transcriptome_fasta=None, standalone=False,
                 proteome_fasta=None, create=True, db_conn=None, project=None):
        """
        :param name: Name of the genome
        :param description: Description of the genome
        :param genome_fasta: Path to the genome fasta file
        :param gtf: Path to the GTF file
        :param transcriptome_fasta: Path to the transcriptome fasta file
        :param standalone: Whether running in standalone mode (SQLite) without project
        :param proteome_fasta: Path to the proteome fasta file
        :param create: Whether to create/insert tables and genome data if missing
        :param db_conn: database connection object (sqlalchemy engine) for standalone mode
        :param project: Project object for project mode
        """
        self.name=name
        self.description=description
        self.gtf = gtf
        self.genome_fasta = pysam.FastaFile(genome_fasta) if genome_fasta is not None else None
        self.transcriptome_fasta = pysam.FastaFile(transcriptome_fasta) if transcriptome_fasta is not None else None
        self.proteome_fasta = pysam.FastaFile(proteome_fasta) if proteome_fasta is not None else None

        if standalone:
            self.db=db_conn
            Session = sessionmaker(bind=self.db)
            self.session = Session()
            self.metadata = sqlalchemy.MetaData()
            self.metadata.reflect(bind=self.db)
            self.tables = self.metadata.tables
        else:
            self.project = project
            self.project_id = getattr(self.project, 'project_id', getattr(self.project, 'id', None))
            self.db = project.kb.engine
            self.session = project.kb.session() if callable(project.kb.session) else project.kb.session
            self.metadata = project.kb.metadata
            self.tables = getattr(project.kb, 'db_tables', project.kb.metadata.tables)


        if create:
            if len(self.tables) == 0:
                logger.info("There are no tables in the database, creating tables and adding genome information")
                if standalone:
                    StandAloneBase.metadata.create_all(self.db)
                else:
                    from benchmate.knowledge_base.tables import Base
                    Base.metadata.create_all(self.db)
                self.metadata.reflect(bind=self.db)
                self.tables = self.metadata.tables

            genome_table=self.metadata.tables['genome']
            if standalone:
                idstmt = sqlalchemy.select(genome_table.c.id, genome_table.c.genome_name).filter(genome_table.c.genome_name==self.name)
            else:
                idstmt = sqlalchemy.select(genome_table.c.id, genome_table.c.genome_name).filter(genome_table.c.genome_name == self.name).\
                    filter(genome_table.c.project_id==self.project_id)

            existing_genome=self.session.execute(idstmt).fetchall()
            if len(existing_genome) == 0:
                genome_id, chrom_ids = insert_genome(gtf=gtf, engine=self.db, name=self.name, description=description,
                                                     genome_fasta=genome_fasta, transcriptome_fasta=transcriptome_fasta,
                                                     proteome_fasta=proteome_fasta, project_id=self.project_id)
            else:
                genome_id = existing_genome[0][0]
                chrom_ids = pd.read_sql(f"select id, chrom from chrom where genome_id={genome_id}", con=self.db)
        else:
            genome_table=self.metadata.tables['genome']
            if standalone:
                idstmt = sqlalchemy.select(genome_table.c.id, genome_table.c.genome_name).filter(genome_table.c.genome_name==self.name)
            else:
                idstmt = sqlalchemy.select(genome_table.c.id, genome_table.c.genome_name).filter(genome_table.c.genome_name == self.name).\
                    filter(genome_table.c.project_id==self.project_id)

            existing_genome=self.session.execute(idstmt).fetchall()

            if len(existing_genome)==0:
                logger.info("The database has all the tables but this particular genome is not in the database, adding now")
                genome_id, chrom_ids=insert_genome(gtf=gtf, engine=self.db, name=self.name, description=self.description,
                                             genome_fasta=genome_fasta, transcriptome_fasta=transcriptome_fasta,
                                            proteome_fasta=proteome_fasta, project_id=self.project_id)
            elif len(existing_genome)==1:
                genome_id=existing_genome[0][0]
                logger.info(f"Found an existing genome with {self.name}, setting up genome instance")
                chrom_ids = pd.read_sql(f"select id, chrom from chrom where genome_id={genome_id}", con=self.db)
                description=pd.read_sql(f"select description from genome where id={genome_id}", con=self.db)["description"].tolist()[0]
            else:
                raise ValueError(f"Found multiple genomes with the name {self.name}, this means a serious data integrity issue, please check your database. The genome ids are: {existing_genome}")

        if self.genome_fasta is not None:
            self._check_chroms(chrom_ids)

        self.genome_id = genome_id
        self.chrom_ids=chrom_ids
        self.description = description

    def _apply_range_filter(self, query, feature_table, chroms_table, strand_table, range_obj, ignore_strand=True, overlap_type="within"):
        overlap_types = ["exact", "within", "any"]
        if overlap_type not in overlap_types:
            raise ValueError(f"overlap_type must be one of {overlap_types}")

        query = query.filter(chroms_table.c.chrom == range_obj.chrom)

        if overlap_type == "exact":
            query = query.filter(feature_table.c.start == range_obj.ranges.start, feature_table.c.end == range_obj.ranges.end)
        elif overlap_type == "within":
            query = query.filter(feature_table.c.start >= range_obj.ranges.start, feature_table.c.end <= range_obj.ranges.end)
        elif overlap_type == "any":
            query = query.filter(feature_table.c.start <= range_obj.ranges.end, feature_table.c.end >= range_obj.ranges.start)

        if range_obj.strand != "*" and not ignore_strand:
            query = query.filter(strand_table.c.strand == range_obj.strand)

        return query

    def genes(self, ids=None, db_ids=None, range=None, ignore_strand=True, overlap_type="within"):
        """
        Gene id or range if range is provided it will return the genes in that range depending on the overlap type
        :param ids: Gene id(s), as used in the gtf file
        :param db_ids: Internal database integer primary key id(s)
        :param range: A GenomicRange object
        :param ignore_strand: whether to ignore strand this will return all the genes in the range regardless of strand
        :param overlap_type: type of range overlap, one of "within", "exact", "any"
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

        # for supporting multiple genomes
        query=query.filter(chroms_table.c.id.in_(self.chrom_ids["id"].tolist()))

        if ids is not None:
            query = query.filter(genes_table.c.gene_id.in_(ids))

        if db_ids is not None:
            query = query.filter(genes_table.c.id.in_(db_ids))

        if range is not None:
            query = self._apply_range_filter(query, genes_table, chroms_table, genes_table, range, ignore_strand, overlap_type)

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
            if isinstance(annot, str):
                try:
                    annot = json.loads(annot)
                except:
                    annot = {}
            if annot is None:
                annot = {}
            annot["db_id"] = item[6]
            ranges.append(GenomicRange(chrom, start, end, strand, annot))
            keys.append(gene_name)

        gdict = GenomicRangesDict(keys, ranges)
        return gdict

    def transcripts(self, gene_ids=None, ids=None, db_ids=None, range=None, ignore_strand=True, group_by_gene=True, overlap_type="within"):
        """
        return transcripts by gene id, transcript id or range
        :param gene_ids: return transcripts for these gene ids
        :param ids: return transcripts with these transcript ids
        :param db_ids: return transcripts with these internal database IDs
        :param range: return transcripts in this range
        :param ignore_strand: ignore strand when searching by range
        :param group_by_gene: whether to group the returned transcripts by gene id, if true the returned object
        will have gene ids as keys and GenomicRangesList as values, if false the returned object will have transcript ids as keys and GenomicRange as values
        :param overlap_type: type of range overlap, one of "within", "exact", "any"
        :return: a genomic ranges dict object
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

        query=query.filter(chroms_table.c.id.in_(self.chrom_ids["id"].tolist()))

        if gene_ids is not None:
            if type(gene_ids) is int:
                gene_ids = [gene_ids]
            query = query.filter(genes_table.c.gene_id.in_(gene_ids))

        if ids is not None:
            query = query.filter(transcripts_table.c.transcript_id.in_(ids))

        if db_ids is not None:
            query = query.filter(transcripts_table.c.id.in_(db_ids))

        if range is not None:
            query = self._apply_range_filter(query, transcripts_table, chroms_table, genes_table, range, ignore_strand, overlap_type)

        result = self.session.execute(query).fetchall()
        res_dict={}
        for item in result:
            chrom = item[1]
            start = item[2]
            end = item[3]
            strand = item[4]
            annot = item[5]
            if isinstance(annot, str):
                try:
                    annot = json.loads(annot)
                except:
                    annot = {}
            if annot is None:
                annot = {}
            annot["db_id"] = item[0]
            gene_id=annot.get("gene_id", "unknown")
            transcript_id=item[6]
            if group_by_gene:
                if gene_id not in res_dict.keys():
                    res_dict[gene_id]=GenomicRangesList([])
                res_dict[gene_id].append(GenomicRange(chrom, start, end, strand, annot))
            else:
                res_dict[transcript_id]=GenomicRange(chrom, start, end, strand, annot)

        gdict=GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict

    def exons(self, transcript_ids=None, ids=None, db_ids=None, range=None, group_by_transcript=True, ignore_strand=True, overlap_type="within"):
        """
        same as genes but will need to search by transcript not gene, if you do not know the transcript search for it with transcripts first
        :param transcript_ids: return all exons for these transcript ids
        :param ids: return exon with these ids
        :param db_ids: internal database ids
        :param range: return exons in this range
        :param group_by_transcript: whether to group the returned exons by transcript id
        :param ignore_strand: whether to ignore strand when searching by range
        :param overlap_type: type of range overlap, one of "within", "exact", "any"
        :return: a genomic ranges dict object, if not grouped by transcript the keys will be exon ids otherwise the keys will be transcript ids
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

        query=query.filter(chroms_table.c.id.in_(self.chrom_ids["id"].tolist()))

        if transcript_ids is not None:
            query = query.filter(transcripts_table.c.transcript_id.in_(transcript_ids))

        if ids is not None:
            query = query.filter(exons_table.c.exon_id.in_(ids))

        if db_ids is not None:
            if type(db_ids) is int:
                db_ids = [db_ids]
            query = query.filter(exons_table.c.id.in_(db_ids))

        if range is not None:
            query = self._apply_range_filter(query, exons_table, chroms_table, genes_table, range, ignore_strand, overlap_type)

        result = self.session.execute(query).fetchall()

        res_dict = {}
        for item in result:
            chrom = item[2]
            start = item[3]
            end = item[4]
            strand = item[5]
            annot = item[6]
            if isinstance(annot, str):
                try:
                    annot = json.loads(annot)
                except:
                    annot = {}
            if annot is None:
                annot = {}
            annot["db_id"] = item[0]
            tx_id = annot.get("transcript_id", str(item[7]))
            exon_id=item[1] if item[1] is not None else item[0]
            if group_by_transcript:
                if tx_id not in res_dict.keys():
                    res_dict[tx_id]=GenomicRangesList([])
                res_dict[tx_id].append(GenomicRange(chrom, start, end, strand, annot))
            else:
                res_dict[str(exon_id)]=GenomicRange(chrom, start, end, strand, annot)

        gdict = GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict

    def coding(self, transcript_ids=None, ids=None, db_ids=None, range=None, group_by_transcript=True, ignore_strand=True, overlap_type="within"):
        """
        same as exons return all the coding sequences for a transcript or a list of transcripts
        :param transcript_ids: return all coding sequences for these transcript ids
        :param ids: return coding sequence with these ids
        :param db_ids: internal database ids
        :param range: return coding sequences in this range
        :param group_by_transcript: whether to group the returned coding sequences by transcript id
        :param overlap_type: type of range overlap, one of "within", "exact", "any"
        :return: a genomic ranges dict object
        """

        chroms_table = self.tables['chrom']
        genes_table = self.tables['gene']
        transcripts_table = self.tables['transcript']
        exons_table=self.tables['exon']
        cds_table=self.tables['coding']

        query = (sqlalchemy.select(
            cds_table.c.id,
            cds_table.c.ccds_id,
            chroms_table.c.chrom,
            cds_table.c.start,
            cds_table.c.end,
            genes_table.c.strand,
            cds_table.c.annotations,
            cds_table.c.exon_id,
            exons_table.c.transcript_id,
            transcripts_table.c.id,
            transcripts_table.c.transcript_id
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

        query=query.filter(chroms_table.c.id.in_(self.chrom_ids["id"].tolist()))

        if transcript_ids is not None:
            query = query.filter(transcripts_table.c.transcript_id.in_(transcript_ids))

        if ids is not None:
            query = query.filter(cds_table.c.ccds_id.in_(ids))

        if db_ids is not None:
            if type(db_ids) is int:
                db_ids = [db_ids]
            query = query.filter(cds_table.c.id.in_(db_ids))

        if range is not None:
            query = self._apply_range_filter(query, cds_table, chroms_table, genes_table, range, ignore_strand, overlap_type)

        result = self.session.execute(query).fetchall()

        res_dict = {}
        for item in result:
            chrom = item[2]
            start = item[3]
            end = item[4]
            strand = item[5]
            annot = item[6]
            if isinstance(annot, str):
                try:
                    annot = json.loads(annot)
                except:
                    annot = {}
            if annot is None:
                annot = {}
            annot["db_id"] = item[0]
            annot["db_exon_id"] = item[7]
            annot["db_transcript_id"] = item[9]
            tx_id = item[10]
            ccds_id=item[1] if item[1] is not None else item[0]
            if group_by_transcript:
                if tx_id not in res_dict.keys():
                    res_dict[tx_id]=GenomicRangesList([])
                res_dict[tx_id].append(GenomicRange(chrom, start, end, strand, annot))
            else:
                res_dict[str(ccds_id)]=GenomicRange(chrom, start, end, strand, annot)

        gdict = GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict


    def three_utr(self, transcript_ids=None, ids=None, db_ids=None, range=None, ignore_strand=True, overlap_type="within"):
        """
        return all the 3' utrs for a transcript or a list of transcripts
        :param transcript_ids: return 3' utrs for these transcript ids
        :param db_ids: internal database ids
        :param range: return 3' utrs in this range
        :param ignore_strand: regardless of strand
        :param overlap_type: type of range overlap, one of "within", "exact", "any"
        :return: a genomic ranges dict object with transcript ids as keys and GenomicRangesList as values
        """
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
            transcripts_table.c.id,
            transcripts_table.c.transcript_id,
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

        query=query.filter(chroms_table.c.id.in_(self.chrom_ids["id"].tolist()))

        if transcript_ids is not None:
            query = query.filter(transcripts_table.c.transcript_id.in_(transcript_ids))

        if db_ids is not None:
            if type(db_ids) is int:
                db_ids = [db_ids]
            query = query.filter(three_utr_table.c.id.in_(db_ids))

        if range is not None:
            query = self._apply_range_filter(query, three_utr_table, chroms_table, genes_table, range, ignore_strand, overlap_type)

        result = self.session.execute(query).fetchall()

        res_dict = {}
        for item in result:
            chrom = item[1]
            start = item[2]
            end = item[3]
            strand = item[4]
            annot = item[5]
            if isinstance(annot, str):
                try:
                    annot = json.loads(annot)
                except:
                    annot = {}
            if annot is None:
                annot = {}
            annot["db_id"] = item[0]
            annot["db_transcript_id"] = item[6]
            tx_id = item[7]
            if tx_id not in res_dict.keys():
                res_dict[tx_id] = GenomicRangesList([])
            res_dict[tx_id].append(GenomicRange(chrom, start, end, strand, annot))

        gdict = GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict


    def five_utr(self,  transcript_ids=None, ids=None, db_ids=None, range=None, ignore_strand=True, overlap_type="within"):
        """
        return all the 5' utrs for a transcript or a list of transcripts
        :param transcript_ids: return 5' utrs for these transcript ids
        :param db_ids: internal database ids
        :param range: return 5' utrs in this range
        :param ignore_strand: regardless of strand
        :param overlap_type: type of range overlap, one of "within", "exact", "any"
        :return: a genomic ranges dict object
        """
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
            transcripts_table.c.id,
            transcripts_table.c.transcript_id
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

        query=query.filter(chroms_table.c.id.in_(self.chrom_ids["id"].tolist()))

        if transcript_ids is not None:
            query = query.filter(transcripts_table.c.transcript_id.in_(transcript_ids))

        if db_ids is not None:
            if type(db_ids) is int:
                db_ids = [db_ids]
            query = query.filter(five_utr_table.c.id.in_(db_ids))

        if range is not None:
            query = self._apply_range_filter(query, five_utr_table, chroms_table, genes_table, range, ignore_strand, overlap_type)

        result = self.session.execute(query).fetchall()

        res_dict = {}
        for item in result:
            chrom = item[1]
            start = item[2]
            end = item[3]
            strand = item[4]
            annot = item[5]
            if isinstance(annot, str):
                try:
                    annot = json.loads(annot)
                except:
                    annot = {}
            if annot is None:
                annot = {}
            annot["db_id"] = item[0]
            annot["db_transcript_id"] = item[6]
            tx_id = item[7]
            if tx_id not in res_dict.keys():
                res_dict[tx_id] = GenomicRangesList([])
            res_dict[tx_id].append(GenomicRange(chrom, start, end, strand, annot))

        gdict = GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict

    def introns(self, transcript_ids=None, ids=None, db_ids=None, range=None, group_by_transcript=True, ignore_strand=True, overlap_type="within"):
        """
        return all the introns for a transcript or a list of transcripts
        :param transcript_ids: return introns for these transcript ids
        :param db_ids: internal database ids
        :param range: return introns in this range
        :param group_by_transcript: return introns grouped by transcript
        :param ignore_strand: whether to ignore strand when searching by range
        :param overlap_type: type of range overlap, one of "within", "exact", "any"
        :return: a genomic ranges dict object
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

        query=query.filter(chroms_table.c.id.in_(self.chrom_ids["id"].tolist()))

        if transcript_ids is not None:
            query = query.filter(transcripts_table.c.transcript_id.in_(transcript_ids))

        if db_ids is not None:
            if type(db_ids) is int:
                db_ids = [db_ids]
            query = query.filter(introns_table.c.id.in_(db_ids))

        if range is not None:
            query = self._apply_range_filter(query, introns_table, chroms_table, genes_table, range, ignore_strand, overlap_type)

        result = self.session.execute(query).fetchall()

        res_dict = {}
        for item in result:
            chrom = item[1]
            start = item[2]
            end = item[3]
            strand = item[4]
            annot = item[5]
            if isinstance(annot, str):
                try:
                    annot = json.loads(annot)
                except:
                    annot = {}
            if annot is None:
                annot = {}
            annot["db_id"] = item[0]
            annot["db_transcript_id"] = item[7]
            tx_id = item[8]
            intron_id=item[0]
            if group_by_transcript:
                if tx_id not in res_dict.keys():
                    res_dict[tx_id]=GenomicRangesList([])
                res_dict[tx_id].append(GenomicRange(chrom, start, end, strand, annot))
            else:
                res_dict[str(intron_id)]=GenomicRange(chrom, start, end, strand, annot)


        gdict = GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict


    def custom_range(self, ids=None, db_ids=None, range=None, ignore_strand=False, overlap_type="within"):
        """
        query a user inserted custom ranges
        :param range: a genomic ranges instance
        :param ignore_strand: whether to ignore strand when searching by range
        :param overlap_type: type of range overlap, one of "within", "exact", "any"
        :return: a GenomicRangesList with all the results, or None
        """
        chroms_table = self.tables['chrom']
        custom_ranges_table = self.tables['custom_ranges']

        query = (sqlalchemy.select(
            custom_ranges_table.c.id,
            chroms_table.c.chrom,
            custom_ranges_table.c.start,
            custom_ranges_table.c.end,
            custom_ranges_table.c.strand,
            custom_ranges_table.c.annotations
        ).join(
            chroms_table,
            custom_ranges_table.c.chrom_id == chroms_table.c.id
        ).where(
            chroms_table.c.id.in_(self.chrom_ids["id"].tolist())
        ))

        if db_ids is not None:
            if isinstance(db_ids, int):
                db_ids = [db_ids]
            query = query.filter(custom_ranges_table.c.id.in_(db_ids))

        if range is not None:
            query = self._apply_range_filter(query, custom_ranges_table, chroms_table, custom_ranges_table, range, ignore_strand, overlap_type)

        result = self.session.execute(query).fetchall()
        if len(result) == 0:
            granges = None
        else:
            granges=[]
            for row in result:
                annot = row[5]
                if isinstance(annot, str):
                    try:
                        annot = json.loads(annot)
                    except:
                        pass
                if annot is None:
                    annot = {}
                annot["db_id"] = row[0]
                granges.append(GenomicRange(row[1], row[2], row[3], row[4], annot))
            granges=GenomicRangesList(granges)
        return granges

    def insert_custom_range(self, range):
        """
        insert a new custom range
        :param range: a GenomicRange instance, if you are using GenomicRangesList of GenomicRangesDict, run this
        function multiple times
        :return: None
        """
        chroms_table = self.tables['chrom']
        custom_ranges_table = self.tables['custom_ranges']

        chrom_stmt = sqlalchemy.select(chroms_table.c.id).where(
            (chroms_table.c.chrom == range.chrom) & (chroms_table.c.genome_id == self.genome_id))

        chrom_id=self.session.execute(chrom_stmt).fetchall()
        if len(chrom_id)==0:
            raise ValueError(f"There are no chroms with the name {range.chrom}")

        if len(chrom_id)>1:
            raise ValueError(f"There are multiple chroms with the name {range.chrom}")

        annot = range.annotation if hasattr(range, "annotation") else None
        if isinstance(annot, dict):
            annot = json.dumps(annot)

        stmt = (sqlalchemy.insert(custom_ranges_table).values(
            chrom_id=chrom_id[0][0],
            start=range.ranges.start,
            end=range.ranges.end,
            strand=range.strand,
            annotations=annot,
        ))

        self.session.execute(stmt)
        self.session.commit()

    def get_sequence(self, genomic_range, type='genome'):
        """
        Get the sequence of a genomic range. This takes a single genomic range you can iterate over a GenomicRangeList or GenomicRangeDict
        :param genomic_range: GenomicRange object
        :return: sequence as string
        """
        if type == 'genome':
            file= self.genome_fasta
        elif type == 'transcriptome':
            file=self.transcriptome_fasta
        elif type == 'proteome':
            file=self.proteome_fasta

        if file is None:
            raise FileNotFoundError(f"There is no fasta file describing {type}")

        if str(genomic_range.chrom) not in file.references:
            raise ValueError(f"Chromosome {genomic_range.chrom} not found in genome fasta file.")
        start = genomic_range.ranges.start
        end = genomic_range.ranges.end
        strand = genomic_range.strand
        seq = file.fetch(genomic_range.chrom, start - 1, end)
        seq=seq.replace("\n", "")
        if strand == '-':
            seq = str(Seq.Seq(seq).reverse_complement())
        return seq

    def add_annotation(self, table, row_id, annots):
        """
        add arbitrary annotations as a dictionary to a specific row in a specific table
        :param table: which table to add the annotations to
        :param id: which row id to add the annotations to, this is the datbase internal id not the gene_id or transcript_id, those
        ids can be found in the annotations of each row
        :param annots: a dictionary of annotations to add
        :return: None but the database will be updated
        """
        if type(annots) != dict:
            raise ValueError(f"Annotation type {type(annots)} not supported. They must be dictionaries")

        table=self._get_table(table)

        try:
            row_id=int(row_id)
        except:
            raise ValueError(f"Row {row_id} is not a valid row id. It must be an integer")

        id_check=sqlalchemy.select(table).where(table.c.id==row_id)
        results=self.session.execute(id_check).fetchall()
        if results:
            query=sqlalchemy.select(table.c.annotations).where(table.c.id==row_id)
            row=self.session.execute(query).fetchone()
            current_annots=row[0]
            if isinstance(current_annots, str):
                try:
                    current_annots = json.loads(current_annots)
                except:
                    current_annots = {}
            if current_annots is None:
                current_annots=annots
            else:
                for key, value in annots.items():
                    if key not in current_annots:
                        current_annots[key]=value
                    else:
                        raise ValueError(f"Annotation key {key} is already in database.")
            try:
                stmt = (
                    sqlalchemy.update(table)
                    .where(table.c.id == row_id)
                    .values(annotations=current_annots)
                )
                self.session.execute(stmt)
                self.session.commit()
            except Exception as e:
                logger.error(f"There was an error in updating the annotations: {e}")
        else:
            raise ValueError("The id returned 0 row, please make sure that the id you provided is correct")

    def search_annotation(self, table_name, values=None):
        """
        search annotations in the database for a specific key or value in a table
        :param table_name: string name of feature: "gene", "transcript", "exon", etc.
        :param values: search key/value dictionary, list of values, or single scalar value
        :return: GenomicRangesDict or GenomicRangesList object with the matching rows
        """
        method_dict={
            "gene":self.genes,
            "transcript":self.transcripts,
            "five_utr":self.five_utr,
            "three_utr":self.three_utr,
            "intron":self.introns,
            "exon":self.exons,
            "coding":self.coding,
            "custom_ranges":self.custom_range,
        }
        table_obj = self._get_table(table_name)

        if isinstance(values, (str, int, float)):
            values = [values]

        if self.db.dialect.name == 'sqlite':
            j = sqlalchemy.func.json_each(table_obj.c.annotations).table_valued(
                "key", "value", "type", "path"
            )
            if isinstance(values, dict):
                conditions = []
                for k, v in values.items():
                    subq = (
                        sqlalchemy.select(table_obj.c.id)
                        .select_from(table_obj.join(j, sqlalchemy.true()))
                        .where(j.c.key == k, j.c.value == str(v))
                    )
                    conditions.append(table_obj.c.id.in_(subq))
                stmt = sqlalchemy.select(table_obj.c.id).where(sqlalchemy.and_(*conditions))
            elif isinstance(values, list):
                stmt = (
                    sqlalchemy.select(table_obj.c.id)
                    .select_from(table_obj.join(j, sqlalchemy.true()))
                    .where(j.c.value.in_([str(v) for v in values]))
                )
            else:
                raise ValueError(f"Annotation type {type(values)} not supported. They must be a dictionary, list or a single value")

        elif self.db.dialect.name == 'postgresql':
            if isinstance(values, dict):
                stmt = sqlalchemy.select(table_obj.c.id).where(
                    sqlalchemy.func.jsonb_path_exists(
                        table_obj.c.annotations,
                        "$.** ? (@.key() == $k && @ == $v)",
                        {"k": list(values.keys()), "v": list(values.values())},
                    )
                )
            elif isinstance(values, list):
                stmt = sqlalchemy.select(table_obj.c.id).where(
                    table_obj.c.annotations["tags"].op("?|")(values)
                )
            else:
                raise ValueError(
                    f"Annotation type {type(values)} not supported. They must be a dictionary, list or a single value")

        ids = [item[0] for item in self.session.execute(stmt).fetchall()]
        method=method_dict[table_name]
        try:
            results=method(db_ids=ids)
        except TypeError:
            results=method(ids=ids)
        return results


    def _check_chroms(self, genome_chroms):
        """
        Check if chroms of the genome is in the datbase for a specific genome
        :param genome_chroms: list of chroms from the genome
        :return: this is an internal function not to be used by the end user
        """
        fasta_chroms = self.genome_fasta.references
        for ref in fasta_chroms:
            if ref not in genome_chroms["chrom"].tolist():
                warnings.warn(
                    f"""Chromosome {ref} not found in the database, this step is not critical for database generation 
                    but it will effect sequence retrieval. If you are creating a new database, you may want to 
                    re-initialize the class with a different genome fasta file.""")

    def _get_table(self, type):
        """
        get the tables, this is used to check if a db has been initiated or used when the queries are being performed
        :param type: what kind of table
        :return:
        """
        types=["genome", "chrom", "gene", "transcript", "exon", "coding", "three_utr", "five_utr", "intron", "custom_ranges"]
        if type not in types:
            raise NotImplementedError(f"Type {type} not supported. Valid types are {','.join(types)}")
        return self.tables[type]


    def __str__(self):
        return f"Genome: for : {self.name}"

    def __repr__(self):
        return f"Genome: for : {self.name} with id {self.genome_id} and fasta file {self.genome_fasta}"



