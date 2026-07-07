from functools import cached_property

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from Bio import Seq
import pysam

from benchmate.knowledge_base.tables import *
from benchmate.genome.tables import *
from benchmate.genome.utils import insert_genome, CustomRange, CustomRangesDict, CustomRangesList
from benchmate.ranges.genomicranges import *


class Genome:
    def __init__(self, name, description, genome_fasta, gtf,
                 transcriptome_fasta=None, standalone=False,
                 proteome_fasta=None, create=True, db_conn=None, project=None):
        """
        :param gtf_path: Path to the GTF file
        :param genome_fasta: Path to the genome fasta file
        :param transcriptome_fasta:  Path to the transcriptome fasta file
        :param proteome_fasta: Path to the proteome fasta file
        :param db_conn: database connection object this is a sqlalchemy engine
        :param taxon_id: taxon id of the genome
        """
        self.name=name
        self.description=description
        self.gtf = gtf
        self.genome_fasta = pysam.FastaFile(genome_fasta) if genome_fasta is not None else None
        self.transcriptome_fasta = pysam.FastaFile(transcriptome_fasta) if transcriptome_fasta is not None else None
        self.proteome_fasta = pysam.FastaFile(proteome_fasta) if proteome_fasta is not None else None

        if standalone:
            self.db=db_conn
            Session = sessionmaker(self.db)
            self.session = Session()
            self.metadata = sqlalchemy.MetaData(self.db)
            self.metadata.reflect(bind=self.db)
            self.tables = self.metadata.tables

        else:
            self.project_id=self.project.id
            self.db=project.kb.engine
            self.session=project.kb.session
            self.metadata=project.kb.metadata
            self.tables=project.kb.tables


        if create: #assuming the tables are created when the project is initialized, a full db w/o any data takes up really
            #no space
            if len(self.tables) == 0:
                print("There are no tables in the database, creating tables and adding genome information")
                if standalone:
                    StandAloneBase.metadata.create_all(self.db)
                else:
                    Base.metadata.create_all(self.db)
                self.metadata.reflect(bind=self.db)

                genome_id, chrom_ids = insert_genome(gtf=gtf, engine=self.db, name=self.name, description=description,
                                                     genome_fasta=genome_fasta, transcriptome_fasta=transcriptome_fasta,
                                                     proteome_fasta=proteome_fasta, )
        else:
            genome_table=self.metadata.tables['genome']
            if standalone:
                idstmt = sqlalchemy.select(genome_table.c.id, genome_table.c.name).filter(genome_table.c.name==self.name)
            else:
                idstmt = sqlalchemy.select(genome_table.c.id, genome_table.c.name).filter(genome_table.c.name == self.name).\
                    filter(genome_table.c.project_id==self.project_id)

            genome_id=self.session.execute(idstmt).fetchall()

            if len(genome_id)==0:
                print("The database has all the tables but this particular genome is not in the database, adding now")
                genome_id, chrom_ids=insert_genome(gtf=gtf, engine=self.db, name=self.name, description=self.description,
                                             genome_fasta=genome_fasta, transcriptome_fasta=transcriptome_fasta,
                                            proteome_fasta=proteome_fasta)
            elif len(genome_id)==1:
                genome_id=genome_id[0]
                print(f"Found an existing genome with {name}, just setting things up, if this is an error re-initiate the class with a different name")
                chrom_ids = pd.read_sql(f"select id, chrom from chrom where genome_id={genome_id[0]}", con=self.db)
                description=pd.read_sql(f"select description from genome where id={genome_id[0]}", con=self.db)["description"].tolist()[0]
            else:
                raise ValueError(f"Found multiple genomes with the name {self.name}, this means a serious data integrity issue, please check your database. The genome ids are: {genome_id}")

        if self.genome_fasta is not None:
            self._check_chroms(chrom_ids)

        self.genome_id = genome_id
        self.chrom_ids=chrom_ids
        self.description = description

    def genes(self, ids=None, range=None, ignore_strand=True):
        """
        Gene id or range if range is provided it will return the genes in that range depending on the overlap type
        :param id: Gene id, that used in the gtf file
        :param range: A GenomicRange object
        :param ignore_strand: whether to ignore strand this will return all the genes in the range regardless of strand
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


        if range is not None:
            query=query.filter(
                chroms_table.c.chrom == range.chrom,
                genes_table.c.start>=range.ranges.start,
                genes_table.c.end<=range.ranges.end)
            if range.strand != "*" and not ignore_strand:
                query=query.filter(genes_table.c.strand == range.strand)

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

    def transcripts(self, gene_ids=None, ids=None, range=None, ignore_strand=True, group_by_gene=True):
        """
        return transcripts by gene id, transcript id or range
        :param gene_ids: return transcripts for these gene ids
        :param ids: return transcripts with these transcript ids
        :param range: return transcripts in this range
        :param ignore_strand: ignore strand when searching by range
        :param group_by_gene: whether to group the returned transcripts by gene id, if true the returned object
        will have gene ids as keys and GenomicRangesList as values, if false the returned object will have transcript ids as keys and GenomicRange as values
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

        if range is not None:
            query=query.filter(
                chroms_table.c.chrom == range.chrom,
                genes_table.c.start>=range.ranges.start,
                genes_table.c.end<=range.ranges.end)
            if range.strand != "*" and not ignore_strand:
                query=query.filter(genes_table.c.strand == range.strand)

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
            transcript_id=item[6]
            if group_by_gene:
                if gene_id not in res_dict.keys():
                    res_dict[gene_id]=GenomicRangesList([])
                res_dict[gene_id].append(GenomicRange(chrom, start, end, strand, annot))
            else:
                res_dict[transcript_id]=GenomicRange(chrom, start, end, strand, annot)

        gdict=GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict

    def exons(self, transcript_ids=None, ids=None, range=None, group_by_transcript=True, ignore_strand=True):
        """
        same as genes but will need to search by transcript not gene, if you do not know the transcript search for it with transcripts first
        :param transcript_id: return all exons for this transcript id
        :param id: return exon with this id
        :param range: return exons in this range
        :param group_by_transcript :whether to group the returned exons by transcript id, if true the returned object
        :param ignore_strand: whether to ignore strand when searching by range
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
            if type(ids) is int:
                ids = [ids]
            query = query.filter(exons_table.c.id.in_(ids))

        if range is not None:
            query = query.filter(
                chroms_table.c.chrom == range.chrom,
                exons_table.c.start >= range.ranges.start,
                exons_table.c.end <= range.ranges.end)
            if range.strand != "*" and not ignore_strand:
                query = query.filter(genes_table.c.strand == range.strand)

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
            exon_id=item[1] if item[1] is not None else item[0]
            if group_by_transcript:
                if tx_id not in res_dict.keys():
                    res_dict[tx_id]=GenomicRangesList([])
                res_dict[tx_id].append(GenomicRange(chrom, start, end, strand, annot))
            else:
                res_dict[str(exon_id)]=GenomicRange(chrom, start, end, strand, annot)

        gdict = GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict

    def coding(self, transcript_ids=None, ids=None, range=None, group_by_transcript=True, ignore_strand=True):
        """
        same as exons return all the coding sequences for a transcript or a list of transcripts
        :param transcript_id: return all coding sequences for this transcript id
        :param id:return coding sequence with this id
        :param range:return coding sequences in this range
        :param group_by_transcript: whether to group the returned coding sequences by transcript id, if true the returned object
        :return: a genomic ranges dict object, if not grouped by transcript the keys will be coding sequence ids otherwise the keys will be transcript ids
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
            if type(ids) is int:
                ids = [ids]
            query = query.filter(cds_table.c.id.in_(ids))

        if range is not None:
            query = query.filter(
                chroms_table.c.chrom == range.chrom,
                cds_table.c.start >= range.ranges.start,
                cds_table.c.end <= range.ranges.end)
            if range.strand != "*" and not ignore_strand:
                query = query.filter(genes_table.c.strand == range.strand)

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
            ccds_id=item[1] if item[1] is not None else item[0]
            if group_by_transcript:
                if tx_id not in res_dict.keys():
                    res_dict[tx_id]=GenomicRangesList([])
                res_dict[tx_id].append(GenomicRange(chrom, start, end, strand, annot))
            else:
                res_dict[str(ccds_id)]=GenomicRange(chrom, start, end, strand, annot)

        gdict = GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict


    def three_utr(self, transcript_ids=None, ids=None, range=None, ignore_strand=True):
        """
        return all the 3' utrs for a transcript or a list of transcripts
        :param transcript_ids: return 3' utrs for these transcript ids
        :param range: return 3' utrs in this range
        :param ignore_strand: regardless of strand
        :return: a genomic ranges dict object with transcript ids as keys and GenomicRangesList as values, the utrs are not described as
        separate exons but the exons are merged into one if that utr spans multple exons. Additionally if the utrs ends in the middle
        of an exon the utr will end there.
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

        if ids is not None:
            if type(ids) is int:
                ids = [ids]
            query = query.filter(three_utr_table.c.id.in_(ids))

        if range is not None:
            query = query.filter(
                chroms_table.c.chrom == range.chrom,
                three_utr_table.c.start >= range.ranges.start,
                three_utr_table.c.end <= range.ranges.end)
            if range.strand != "*" and not ignore_strand:
                query = query.filter(genes_table.c.strand == range.strand)

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


    def five_utr(self,  transcript_ids=None, ids=None, range=None, ignore_strand=True):
        """
        return all the 5' utrs for a transcript or a list of transcripts
        :param transcript_ids: return 3' utrs for these transcript ids
        :param range: return 3' utrs in this range
        :param ignore_strand: regardless of strand
        :return: a genomic ranges dict object with transcript ids as keys and GenomicRangesList as values, the utrs are not described as
        separate exons but the exons are merged into one if that utr spans multple exons. Additionally if the utrs ends in the middle
        of an exon the utr will end there.
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

        if ids is not None:
            if type(ids) is int:
                ids = [ids]
            query = query.filter(five_utr_table.c.id.in_(ids))

        if range is not None:
            query = query.filter(
                chroms_table.c.chrom == range.chrom,
                five_utr_table.c.start >= range.ranges.start,
                five_utr_table.c.end <= range.ranges.end)
            if range.strand != "*" and not ignore_strand:
                query = query.filter(genes_table.c.strand == range.strand)

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

    def introns(self, transcript_ids=None, ids=None, range=None, group_by_transcript=True, ignore_strand=True):
        """
        return all the introns for a transcript or a list of transcripts
        :param transcript_id:return introns for this transcript id
        :param id:return intron with this id (introns usually are not descibed in a gtf, so this id may not be very useful since
        it is an auto incremented id)
        :param range:return introns in this range
        :param group_by_transcript: return introns grouped by transcript
        :param ignore_strand: whether to ignore strand when searching by range
        :return: return: a genomic ranges dict object, if not grouped by transcript the keys will be intron ids otherwise the keys will be transcript ids
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

        if ids is not None:
            if type(ids) is int:
                ids = [ids]
            query = query.filter(introns_table.c.id.in_(ids))

        if range is not None:
            query = query.filter(
                chroms_table.c.chrom == range.chrom,
                introns_table.c.start >= range.ranges.start,
                introns_table.c.end <= range.ranges.end)
            if range.strand != "*" and not ignore_strand:
                query = query.filter(genes_table.c.strand == range.strand)

        result = self.session.execute(query).fetchall()

        res_dict = {}
        for item in result:
            chrom = item[1]
            start = item[2]
            end = item[3]
            strand = item[4]
            annot = item[5]
            annot["db_id"] = item[0]
            annot["db_transcript_id"] = item[8]
            tx_id = item[8]
            intron_id=item[1] if item[1] is not None else item[0]
            if group_by_transcript:
                if tx_id not in res_dict.keys():
                    res_dict[tx_id]=GenomicRangesList([])
                res_dict[tx_id].append(GenomicRange(chrom, start, end, strand, annot))
            else:
                res_dict[str(intron_id)]=GenomicRange(chrom, start, end, strand, annot)


        gdict = GenomicRangesDict(res_dict.keys(), res_dict.values())
        return gdict


    def custom_range(self, range=None, ignore_strand=False):
        """
        query a user inserted custom ranges
        :param range: a genomic ranges instance
        :param ignore_strand: whether to ignore strand when searching by range
        :return: a GenomicRangesList with all the results, or None
        """
        chroms_table = self.tables['chrom']
        custom_ranges_table = self.tables['custom_ranges']

        chrom_id_subq = sqlalchemy.select(chroms_table.c.id).where(
            (chroms_table.c.chrom == range.chrom) & (chroms_table.c.genome_id == self.genome_id)).subquery()

        query = (sqlalchemy.select(
            custom_ranges_table.c.id,
            custom_ranges_table.c.chrom,
            custom_ranges_table.c.start,
            custom_ranges_table.c.end,
            custom_ranges_table.c.strand,
            custom_ranges_table.c.annotations).where(
            chrom_id_subq.c.id==chrom_id_subq.c.id
        ))


        query=query.filter(
            custom_ranges_table.c.start >= range.ranges.start,
            custom_ranges_table.c.end <= range.ranges.end,
        )
        if not ignore_strand:
            query = query.filter(custom_ranges_table.c.strand == range.strand)

        result = self.session.execute(query).fetchall()
        if len(result) == 0:
            granges = None
        else:
            granges=[]
            for row in result:
                granges.append(GenomicRange(row[0][1], row[0][2], row[0][3], row[0][4], row[0][5]))
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

        chrom_id=self.genome.session.execute(chrom_stmt).fetchall()
        if len(chrom_id)==0:
            raise ValueError(f"There are no chroms with the name {self.chrom}")

        if len(chrom_id)>1:
            raise ValueError(f"There are multiple chroms with the name {self.chrom}")

        stmt = (sqlalchemy.insert(custom_ranges_table).values(
            genome_id=self.genome_id,
            chrom_id=chrom_id[0][0],
            start=range.ranges.start,
            end=range.ranges.end,
            strand=range.strand,
            annotations=range.annotation if self.annotation else None,
        ))

        self.session.execute(stmt)
        self.session.commit()

    
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

        if file is None:
            raise FileNotFoundError(f"There is no fasta file describing {type}")

        if str(genomic_range.chrom) not in file.references:
            raise ValueError(f"Chromosome {genomic_range.chrom} not found in genome fasta file.")
        start = genomic_range.ranges.start
        end = genomic_range.ranges.end
        strand = genomic_range.strand
        seq = file.fetch(genomic_range.chrom, start, end)
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
        if results is not None:
            query=sqlalchemy.select(table.c.annotations).where(table.c.id==row_id)
            row=self.session.execute(query).fetchone()
            current_annots=row[0]
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
                print(f"There was an error in updating the annotations: {e}")
        else:
            raise ValueError("The id returned 0 row, please make sure that the id you provided is correct")

    #TODO hacky not DRY, needs testing
    def search_annotation(self, table, values=None):
        """
        search annotations in the database for a specific key or value in a table
        :param table: this determines what kinds of features you are searching genens, transcripts etc
        :param values: search all the values of all keys if keys is none otherwise search those keys and return matching values
        :return: genomicRangesDict object with the matching rows
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
        table = self._get_table(table)

        if isinstance(values, [str, int, float]):
            values = [values]

        j = sqlalchemy.func.json_each(table.c.annotations).table_valued(
            "key", "value", "type", "path"
        )
        if self.db.dialect.name == 'sqlite':
            if isinstance(values, dict):
                stmt = (
                    sqlalchemy.select(table.c.id)
                    .select_from(table.c.annotations.join(j, sqlalchemy.true()))
                    .where(
                        j.c.key == "role",
                        j.c.value == "admin",
                    )
                )
            elif isinstance(values, list):
                j = sqlalchemy.func.json_each(table.c.annotations).table_valued(
                    "key", "value", "type", "path"
                )

                stmt = (
                    sqlalchemy.select(table.c.id)
                    .select_from(table.join(j, sqlalchemy.true()))
                    .where(j.c.value.in_(values)))

            else:
                raise ValueError(f"Annotation type {type(values)} not supported. They must be a dictionary, list or a single value")


        elif self.db.dialect.name == 'postgresql':
            if isinstance(values, dict):
                stmt = sqlalchemy.select(table).where(
                    sqlalchemy.func.jsonb_path_exists(
                        table.c.annotations,
                        "$.** ? (@.key() == $k && @ == $v)",
                        {"k": list(values.keys()), "v": list(values.values())},
                    )                )
            elif isinstance(values, list):
                stmt = sqlalchemy.select(table.c.id).where(
                    table.c.annotations["tags"].op("?|")(values)
                )
            else:
                raise ValueError(
                    f"Annotation type {type(values)} not supported. They must be a dictionary, list or a single value")

        #these are just the ids now I need to get the actual thing
        ids = [item[0] for item in self.session.execute(stmt).fetchall()]
        method=method_dict[table.name]

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
        types=["genome", "chrom", "gene", "transcript", "exon", "three_utr", "five_utr", "intron", "custom_ranges"]
        if type not in types:
            raise NotImplementedError(f"Type {type} not supported. Valid types are {','.join(types)}")
        return self.tables[type]


    def __str__(self):
        return f"Genome: for : {self.name}"

    def __repr__(self):
        return f"Genome: for : {self.name} with id {self.genome_id} and fasta file {self.genome_fasta}"



