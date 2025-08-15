from sqlalchemy.orm import declarative_base

from sqlalchemy import (
    Column, ForeignKey, Integer, String, JSON
)

Base = declarative_base()

#TODO metadata about the genome like spikeins etc
class Genome(Base):
    __tablename__ = 'genome'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    genome_name = Column(String, unique=True)
    genome_fasta_file = Column(String, nullable=True)
    transcriptome_fasta_file = Column(String, nullable=True)
    proteome_fasta_file = Column(String, nullable=True)
    description=Column(String, nullable=True)

class Chrom(Base):
    __tablename__ = 'chrom'
    id = Column(Integer, autoincrement=True, primary_key=True)
    chrom=Column(String, nullable=True)
    genome_id=Column(Integer, ForeignKey('genome.id'), nullable=True)

class Gene(Base):
    __tablename__ = 'gene'
    id = Column(Integer, autoincrement=True, primary_key=True)
    gene_id = Column(String, nullable=False)
    chrom_id=Column(Integer, ForeignKey('chrom.id'), nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    strand = Column(String, nullable=False)
    annotations=Column(JSON)

class Transcript(Base):
    __tablename__ = 'transcript'
    id = Column(Integer, autoincrement=True, primary_key=True)
    transcript_id = Column(String, nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    gene_id=Column(Integer, ForeignKey('gene.id'))
    annotations=Column(JSON)

class Exon(Base):
    __tablename__ = 'exon'
    id = Column(Integer, autoincrement=True, primary_key=True)
    exon_id = Column(String, nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    exon_number = Column(Integer, nullable=False)
    transcript_id=Column(Integer, ForeignKey('transcript.id'), nullable=False)
    annotations = Column(JSON)

class ThreeUTR(Base):
    __tablename__ = 'three_utr'
    id = Column(Integer, autoincrement=True, primary_key=True)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    transcript_id = Column(Integer, ForeignKey('transcript.id'), nullable=True)
    annotations = Column(JSON)

class FiveUTR(Base):
    __tablename__ = 'five_utr'
    id = Column(Integer, autoincrement=True, primary_key=True)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    transcript_id = Column(Integer, ForeignKey('transcript.id'), nullable=True)
    annotations = Column(JSON)

class Cds(Base):
    __tablename__ = 'coding'
    id = Column(Integer, autoincrement=True, primary_key=True)
    cds_id = Column(String, nullable=True)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    phase=Column(Integer, nullable=False)
    exon_id = Column(Integer, ForeignKey('exon.id'), nullable=False)
    annotations = Column(JSON)

class Introns(Base):
    __tablename__ = 'intron'
    id = Column(Integer, autoincrement=True, primary_key=True)
    transcript_id = Column(Integer, ForeignKey('transcript.id'), nullable=False)
    intron_rank = Column(Integer, nullable=False)
    start=Column(Integer)
    end=Column(Integer)
    annotations = Column(JSON)

