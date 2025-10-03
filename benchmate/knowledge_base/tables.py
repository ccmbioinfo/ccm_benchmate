# I'm moving all the tables here so we can see it all in one place,
# this might not be the ideal solution since the creator of a module will need to add to this as well but it is a minimal burden


from sqlalchemy.orm import declarative_base

from sqlalchemy import (
    Column, ForeignKey, Integer, String, DateTime,
    Text, Float, types, Computed, Index,
    JSON, LargeBinary, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import TSVECTOR, JSONB, ARRAY

from pgvector.sqlalchemy import Vector

from sqlalchemy.ext.declarative import declared_attr

class TSVector(types.TypeDecorator):
    """
    generic class for tsvector type for full text search
    """
    impl = TSVECTOR

Base = declarative_base()

class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

#APIs table
class ApiCall(Base):
    __tablename__ = 'api_call'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    class_name = Column(String, nullable=False)
    method_name = Column(String, nullable=False)
    params =Column(JSONB, nullable=False)
    results=Column(JSONB, index=True)
    query_time = Column(DateTime, nullable=False)

# Literature tables

class Papers(Base):
    __tablename__ = 'papers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    source_id = Column(String, nullable=False)
    source=Column(String, nullable=False) #pubmed or arxiv
    title=Column(String, nullable=False)
    pdf_url = Column(String, nullable=True)
    pdf_path=Column(String, nullable=True)
    abstract=Column(Text, nullable=True)
    abstract_embeddings=Column(Vector(1024))
    openalex_response=Column(JSONB, nullable=True)
    full_text = Column(Text, nullable=False)
    full_text_ts_vector = Column(TSVector, Computed("to_tsvector('english', full_text)", ))
    abstract_ts_vector=Column(TSVector, Computed("to_tsvector('english', abstract)",
                                                 persisted=True))
    __table_args__ = (Index('ix_abstract_ts_vector',
                            abstract_ts_vector, postgresql_using='gin'),
                      UniqueConstraint('source', 'source_id'),
                      Index('ix_full_text_ts_vector',
                            full_text_ts_vector, postgresql_using='gin'),
                      )

class Authors(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id=Column(Integer, ForeignKey(Papers.id), nullable=False)
    name=Column(String, nullable=False)
    affiliation=Column(String, nullable=True)


class Figures(Base):
    __tablename__ = 'figures'
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id=Column(Integer, ForeignKey(Papers.id), nullable=False)
    image_blob=Column(LargeBinary, nullable=False)
    ai_caption=Column(Text, nullable=False)
    image_embeddings=Column(Vector(1024))
    ai_caption_embeddings=Column(Vector(1024))
    ai_caption_ts_vector=Column(TSVector, Computed("to_tsvector('english', ai_caption)",))

    __table_args__ = (
                      Index('ix_ai_figure_caption_ts_vector',
                            ai_caption_ts_vector, postgresql_using='gin'),
                      )

class Tables(Base):
    __tablename__ = 'tables'
    id=Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey(Papers.id), nullable=False)
    image_blob = Column(LargeBinary, nullable=False)
    ai_caption = Column(Text, nullable=False)
    image_embeddings = Column(Vector(1024))
    ai_caption_embeddings = Column(Vector(1024))
    ai_caption_ts_vector = Column(TSVector, Computed("to_tsvector('english', ai_caption)", ))

    __table_args__ = (
                      Index('ix_ai_table_caption_ts_vector',
                            ai_caption_ts_vector, postgresql_using='gin'),
                      )
class ChunkedBodyText(Base):
    __tablename__ = 'body_text_chunked'
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey(Papers.id), nullable=False)
    chunk_id=Column(Integer, nullable=False)
    chunk_text=Column(Text, nullable=False)
    chunk_embeddings=Column(Vector(1024))
    chunk_ts_vector = Column(TSVector, Computed("to_tsvector('english', chunk_text)", ))
    __table_args__ = (Index('ix_chunk_ts_vector',
                            chunk_ts_vector, postgresql_using='gin'),)

class References(Base):
    __tablename__ = 'references'
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id=Column(Integer, ForeignKey(Papers.id), nullable=False) #this is the paper
    target_id=Column(Integer, ForeignKey(Papers.id), nullable=False) #this is the reference

class CitedBy(Base):
    __tablename__ = 'cited_by'
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id=Column(Integer, ForeignKey(Papers.id), nullable=False) #this is the paper
    target_id=Column(Integer, ForeignKey(Papers.id), nullable=False) #this is the reference

class RelatedWorks(Base):
    __tablename__ = 'related_works'
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id=Column(Integer, ForeignKey(Papers.id), nullable=False) #see above
    target_id=Column(Integer, ForeignKey(Papers.id), nullable=False)

# genome tables
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
    annotations=Column(JSONB)

class Transcript(Base):
    __tablename__ = 'transcript'
    id = Column(Integer, autoincrement=True, primary_key=True)
    transcript_id = Column(String, nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    gene_id=Column(Integer, ForeignKey('gene.id'))
    annotations=Column(JSONB)

class Exon(Base):
    __tablename__ = 'exon'
    id = Column(Integer, autoincrement=True, primary_key=True)
    exon_id = Column(String, nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    exon_number = Column(Integer, nullable=False)
    transcript_id=Column(Integer, ForeignKey('transcript.id'), nullable=False)
    annotations = Column(JSONB)

class ThreeUTR(Base):
    __tablename__ = 'three_utr'
    id = Column(Integer, autoincrement=True, primary_key=True)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    transcript_id = Column(Integer, ForeignKey('transcript.id'), nullable=True)
    annotations = Column(JSONB)

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
    annotations = Column(JSONB)

class Introns(Base):
    __tablename__ = 'intron'
    id = Column(Integer, autoincrement=True, primary_key=True)
    transcript_id = Column(Integer, ForeignKey('transcript.id'), nullable=False)
    intron_rank = Column(Integer, nullable=False)
    start=Column(Integer)
    end=Column(Integer)
    annotations = Column(JSONB)

# sequence tables
class Sequence(Base):
    __tablename__ = 'sequence'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    name = Column(String)
    sequence = Column(String)
    type = Column(String)
    features=Column(JSONB)

# structure tables
class Structure(Base):
    __tablename__="structure"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    name=Column(String)
    chains=Column(JSONB) #all the chaing is the pdb, I'm just storing the whole thing here not sure if a good idea
    structure=Column(Text) #this is a pdb dump
    features=Column(JSONB)

class Molecule(Base):
     __tablename__="molecule"
     id = Column(Integer, primary_key=True, autoincrement=True)
     project_id = Column(Integer, ForeignKey('project.id'))
     name=Column(String)
     smiles=Column(String)
     bound_structure=Column(ForeignKey('structure.id'))
     fingerprint_dim=Column(Integer, default=2048)
     fingerprint_radius=Column(Integer, default=2)
     ecfp4=Column(ARRAY(Integer, dimensions=1))
     fcfp4=Column(ARRAY(Integer, dimensions=1))
     maccs=Column(ARRAY(Integer, dimensions=1))
     properties=Column(JSONB)

class BaseVariant:
    """Abstract base class for all variant types."""
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    @declared_attr
    def project_id(cls):
        return Column(Integer, ForeignKey('project.id'))
    id = Column(Integer, primary_key=True, autoincrement=True)
    chrom = Column(String, nullable=False, index=True)
    pos = Column(Integer, nullable=False, index=True)
    filter = Column(String)  # Callset-specific

class SequenceVariant(Base, BaseVariant):
    """Table for SNV and Indel variants."""
    ref = Column(String, nullable=False, index=True)
    alt = Column(String, nullable=False, index=True)
    qual = Column(Float)  # Callset-specific
    gq = Column(Float)   # Sample-specific
    gt = Column(String, index=True)   # Sample-specific
    dp = Column(Integer)  # Sample-specific
    ad = Column(ARRAY(Integer))  # Sample-specific
    ps = Column(String)   # Sample-specific, Phase set (LRWGS only)
    length = Column(Integer)  # Calculated
    annotations = Column(JSONB, default=dict, nullable=False, index=True)

class StructuralVariant(Base, BaseVariant):
    """Table for SV/CNV variants (INS, DEL, INV, DUP, BND, CNV)."""
    svtype = Column(String, nullable=False)
    end = Column(Integer, index=True)
    ref = Column(String, index=True)
    alt = Column(String, index=True)
    qual = Column(Float)  # Callset-specific
    gt = Column(String, index=True)   # Sample-specific
    dp = Column(Integer)  # Sample-specific
    ad = Column(ARRAY(Integer))  # Sample-specific
    svlen = Column(Integer)
    mateid = Column(String)
    cn = Column(Integer)
    cistart = Column(Integer)
    ciend = Column(Integer)
    mei_type = Column(String)
    sr = Column(Integer)  # Sample-specific
    pr = Column(Integer)  # Sample-specific
    ps = Column(String)   # Sample-specific
    annotations = Column(JSONB, default=dict, nullable=False, index=True)

class TandemRepeatVariant(Base, BaseVariant):
    """Table for Tandem Repeat variants (SRWGS and LRWGS)."""
    end = Column(Integer, nullable=False)
    gt = Column(String, index=True)   # Sample-specific
    motif = Column(String)
    al = Column(Integer)
    ref = Column(String)
    alt = Column(String)
    ms = Column(Integer)  # Sample-specific
    mc = Column(Integer)  # Sample-specific
    ap = Column(Float)   # Sample-specific
    am = Column(Float)   # Sample-specific
    sd = Column(Integer)  # Sample-specific
    annotations = Column(JSONB, default=dict, nullable=False, index=True)