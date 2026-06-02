# I'm moving all the tables here so we can see it all in one place,
# this might not be the ideal solution since the creator of a module will need to add to this as well but it is a minimal burden


from sqlalchemy.orm import declarative_base
from sqlalchemy.types import UserDefinedType

from sqlalchemy import (
    Column, ForeignKey, Integer, String, DateTime,
    Text, Float, types, Computed, Index, ARRAY,
    JSON, LargeBinary, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import TSVECTOR, JSONB, BIT

from pgvector.sqlalchemy import Vector

from sqlalchemy.ext.declarative import declared_attr

class TSVector(types.TypeDecorator):
    """
    generic class for tsvector type for full text search
    """
    impl = TSVECTOR

class Bfp(UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw):
        return "bfp"


Base = declarative_base()

class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

#APIs tables

class ApiCall(Base):
    __tablename__ = 'api_call'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    class_name = Column(String, nullable=False)
    method_name = Column(String, nullable=False)
    params = Column(JSONB, nullable=False)
    results = Column(JSONB, nullable=True)
    flat_results=Column(Text, nullable=True)
    full_text_tsv = Column(TSVector, Computed("to_tsvector('english', flat_results)", persisted=True))
    query_time = Column(DateTime, nullable=False)

    __table_args__ = (
        Index('ix_api_call_full_text_tsv', full_text_tsv, postgresql_using='gin'),
        Index('ix_api_call_results_gin', results, postgresql_using='gin')
    )

# Literature tables
class Papers(Base):
    __tablename__ = 'papers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    paper_id = Column(String, nullable=False) # This is the paperinfo.id
    external_ids=Column(JSONB, nullable=False) #pubmed or arxiv
    title=Column(String, nullable=False)
    abstract=Column(Text, nullable=True)
    abstract_embeddings=Column(Vector(4096))
    download_links = Column(ARRAY(String, dimensions=1), nullable=True)
    file_paths=Column(ARRAY(String, dimensions=1), nullable=True)
    full_json=Column(JSONB, nullable=True)
    authors=Column(JSONB, nullable=True)
    publication_date=Column(String, nullable=True)
    venue=Column(String, nullable=True)
    full_text = Column(Text, nullable=False)
    full_text_ts_vector = Column(TSVector, Computed("to_tsvector('english', full_text)", ))
    annotations=Column(JSONB) #this will have extracted information from the paper or abstract or other api calls
    abstract_ts_vector=Column(TSVector, Computed("to_tsvector('english', abstract)",
                                                 persisted=True))
    __table_args__ = (Index('ix_abstract_ts_vector',
                            abstract_ts_vector, postgresql_using='gin'),
                      UniqueConstraint('source', 'source_id'),
                      Index('ix_full_text_ts_vector',
                            full_text_ts_vector, postgresql_using='gin'),
                      Index('ix_paper_json_gin', full_json, postgresql_using='gin')
                      )

class Figures(Base):
    __tablename__ = 'figures'
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id=Column(Integer, ForeignKey(Papers.id), nullable=False)
    image_blob=Column(LargeBinary, nullable=False)
    ai_caption=Column(Text, nullable=False)
    image_embeddings=Column(Vector(4096))
    ai_caption_embeddings=Column(Vector(4096))
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
    image_embeddings=Column(Vector(4096))
    ai_caption_embeddings = Column(Vector(4096))
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
    chunk_embeddings=Column(Vector(4096))
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
    __table_args__ = (Index('ix_genes_annotation_gin', annotations, postgresql_using='gin')
                      )

class Transcript(Base):
    __tablename__ = 'transcript'
    id = Column(Integer, autoincrement=True, primary_key=True)
    transcript_id = Column(String, nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    gene_id=Column(Integer, ForeignKey('gene.id'))
    annotations=Column(JSONB)
    __table_args__ = (Index('ix_txs_annotation_gin', annotations, postgresql_using='gin')
                      )

class Exon(Base):
    __tablename__ = 'exon'
    id = Column(Integer, autoincrement=True, primary_key=True)
    exon_id = Column(String, nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    exon_number = Column(Integer, nullable=False)
    transcript_id=Column(Integer, ForeignKey('transcript.id'), nullable=False)
    annotations = Column(JSONB)
    __table_args__ = (Index('ix_exons_annotation_gin', annotations, postgresql_using='gin')
                      )

class ThreeUTR(Base):
    __tablename__ = 'three_utr'
    id = Column(Integer, autoincrement=True, primary_key=True)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    transcript_id = Column(Integer, ForeignKey('transcript.id'), nullable=True)
    annotations = Column(JSONB)
    __table_args__ = (Index('ix_three_utr_annotation_gin', annotations, postgresql_using='gin')
                      )

class FiveUTR(Base):
    __tablename__ = 'five_utr'
    id = Column(Integer, autoincrement=True, primary_key=True)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    transcript_id = Column(Integer, ForeignKey('transcript.id'), nullable=True)
    annotations = Column(JSON)
    __table_args__ = (Index('ix_five_annotation_gin', annotations, postgresql_using='gin')
                      )

class Cds(Base):
    __tablename__ = 'coding'
    id = Column(Integer, autoincrement=True, primary_key=True)
    ccds_id = Column(String, nullable=True)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    phase=Column(Integer, nullable=False)
    exon_id = Column(Integer, ForeignKey('exon.id'), nullable=False)
    annotations = Column(JSONB)
    __table_args__ = (Index('ix_cdss_annotation_gin', annotations, postgresql_using='gin')
                      )

class Introns(Base):
    __tablename__ = 'intron'
    id = Column(Integer, autoincrement=True, primary_key=True)
    transcript_id = Column(Integer, ForeignKey('transcript.id'), nullable=False)
    intron_rank = Column(Integer, nullable=False)
    start=Column(Integer)
    end=Column(Integer)
    annotations = Column(JSONB)
    __table_args__ = (Index('ix_introns_annotation_gin', annotations, postgresql_using='gin')
                      )

class CustomRanges(Base):
    __tablename__ = 'custom_ranges'
    id = Column(Integer, primary_key=True, autoincrement=True)
    chrom_id = Column(Integer, ForeignKey('chrom.id'), nullable=False)
    start = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    strand = Column(String, nullable=False)
    annotations=Column(JSON)
    __table_args__ = (Index('ix_custom_range_annotation_gin', annotations, postgresql_using='gin')
                      )

# sequence tables
class Sequence(Base):
    __tablename__ = 'sequence'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    name = Column(String)
    sequence = Column(String)
    type = Column(String)
    annotations=Column(JSONB)
    __table_args__ = (Index('ix_sequence_annotation_gin', annotations, postgresql_using='gin')
                      )

# structure tables
class Structure(Base):
    __tablename__="structure"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    name=Column(String)
    chains=Column(JSONB) #all the chaing is the pdb, I'm just storing the whole thing here not sure if a good idea
    atoms=Column(Text) #this is a pdb dump
    annotations=Column(JSONB)
    __table_args__ = (Index('ix_structure_annotation_gin', annotations, postgresql_using='gin')
                      )

class Molecule(Base):
     __tablename__="molecule"
     id = Column(Integer, primary_key=True, autoincrement=True)
     project_id = Column(Integer, ForeignKey('project.id'))
     name=Column(String)
     smiles=Column(String)
     fingerprint_dim=Column(Integer, default=2048)
     fingerprint_radius=Column(Integer, default=2)
     ecfp4 = Column(Bfp)
     fcfp4 = Column(Bfp)
     maccs = Column(Bfp)
     inchi=Column(String)
     properties=Column(JSONB)
     annotations=Column(JSONB)
     __table_args__ = (
         Index("ix_molecule_ecfp4_gist", ecfp4, postgresql_using="gist"),
         Index("ix_molecule_fcfp4_gist", fcfp4, postgresql_using="gist"),
         Index("ix_molecule_maccs_gist", maccs, postgresql_using="gist"),
         Index('ix_molecule_properties_gin', properties, postgresql_using='gin'),
         Index('ix_molecule_annotations_gin', annotations, postgresql_using='gin')
     )

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
    ref=Column(String, nullable=False, index=True)
    alt=Column(String, nullable=False, index=True)
    annotations = Column(JSONB)

class SequenceVariant(Base, BaseVariant):
    """Table for SNV and Indel variants."""
    length = Column(Integer)  # Calculated
    __table_args__ = (
        Index(
            f"ix_sequence_variant_annotations_gin",
            postgresql_using="gin",
        ),
        UniqueConstraint(
            "project_id"
            "chrom",
            "pos",
            "ref",
            "alt",
            name="uq_sequence_variant"
        )
    )

class StructuralVariant(Base, BaseVariant):
    """Table for SV/CNV variants (INS, DEL, INV, DUP, BND, CNV)."""
    svtype = Column(String, nullable=False)
    svlen = Column(Integer)
    cn = Column(Integer)
    cistart = Column(Integer)
    ciend = Column(Integer)
    __table_args__ = (
        Index(
            f"ix_structural_variant_annotations_gin",
            postgresql_using="gin",
        ),
        UniqueConstraint(
            "project_id"
            "chrom",
            "pos",
            "ref",
            "alt",
            "svtype",
            name="uq_structural_variant"
        ),
    )

class TandemRepeatVariant(Base, BaseVariant):
    """Table for Tandem Repeat variants (SRWGS and LRWGS)."""
    motif = Column(String)
    al = Column(Integer, nullable=False)
    __table_args__ = (
        Index(
            f"ix_tandemrepeat_variant_annotations_gin",
            postgresql_using="gin",
        ),
        UniqueConstraint(
            "project_id"
            "chrom",
            "pos",
            "motif",
            "al",
            name="uq_tandem_repeat_variant"
        ),
    )
