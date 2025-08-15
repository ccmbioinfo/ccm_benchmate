
from sqlalchemy import (
    Column, ForeignKey, Integer, String, DateTime,
    Date, Text, Float, Time, types, Computed, Index, Boolean,
    JSON, BLOB
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import declarative_base

from pgvector.sqlalchemy import Vector
class TSVector(types.TypeDecorator):
    impl = TSVECTOR

Base = declarative_base()

class Papers(Base):
    __tablename__ = 'papers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    source=Column(String, nullable=False) #pubmed or arxiv
    source_id=Column(String, nullable=False)
    title=Column(String, nullable=False)
    doi=Column(String, nullable=True)
    pdf_url = Column(String, nullable=True)
    pdf_path=Column(String, nullable=True)
    abstract=Column(Text, nullable=True)
    abstract_embeddings=Column(Vector(1024))
    abstract_ts_vector=Column(TSVector, Computed("to_tsvector('english', abstract)",
                                                 pesisted=True))
    __table_args__ = (Index('ix_abstract_ts_vector',
                            abstract_ts_vector, postgresql_using='gin'),)


class Figures(Base):
    __tablename__ = 'figures'
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id=Column(Integer, ForeignKey(Papers.id), nullable=False)
    image_blob=Column(BLOB, nullable=False)
    caption=Column(Text, nullable=True)
    ai_caption=Column(Text, nullable=False)
    image_embeddings=Column(Vector(1024))
    caption_embeddings=Column(Vector(1024))
    ai_caption_embeddings=Column(Vector(1024))
    caption_ts_vector=Column(TSVector, Computed("to_tsvector('english', caption)",))
    ai_caption_ts_vector=Column(TSVector, Computed("to_tsvector('english', ai_caption)",))

    __table_args__ = (Index('ix_caption_ts_vector',
                            caption_ts_vector, postgresql_using='gin'),
                      Index('ix_ai_caption_ts_vector',
                            ai_caption_ts_vector, postgresql_using='gin'),
                      )

class Tables(Base):
    __tablename__ = 'tables'
    paper_id = Column(Integer, ForeignKey(Papers.id), nullable=False)
    image_blob = Column(BLOB, nullable=False)
    caption = Column(Text, nullable=True)
    ai_caption = Column(Text, nullable=False)
    image_embeddings = Column(Vector(1024))
    caption_embeddings = Column(Vector(1024))
    ai_caption_embeddings = Column(Vector(1024))
    caption_ts_vector = Column(TSVector, Computed("to_tsvector('english', caption)", ))
    ai_caption_ts_vector = Column(TSVector, Computed("to_tsvector('english', ai_caption)", ))

    __table_args__ = (Index('ix_caption_ts_vector',
                            caption_ts_vector, postgresql_using='gin'),
                      Index('ix_ai_caption_ts_vector',
                            ai_caption_ts_vector, postgresql_using='gin'),
                      )

class BodyText(Base):
    __tablename__ = 'body_text'
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey(Papers.id), nullable=False)
    chunk_id=Column(Integer, nullable=False)
    embedding_mode=Column(String, nullable=False)
    chunk_text=Column(Text, nullable=False)
    chunk_embeddings=Column(Vector(1024))
    chunk_ts_vector = Column(TSVector, Computed("to_tsvector('english', chunk_text)", ))
    __table_args__ = (Index('ix_chunk_ts_vector',
                            chunk_ts_vector, postgresql_using='gin'),)
