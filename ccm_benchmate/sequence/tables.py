from sqlalchemy import (
    Column, ForeignKey, Integer, String,  Float
)
from pgvector.sqlalchemy import Vector

from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
Base = declarative_base()

class Sequence(Base):
    __tablename__ = 'sequence'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    sequence = Column(String)
    type = Column(String)
    msa_path=Column(String, nullable=True)
    blast_path=Column(String, nullable=True)
    embeddings=Column(Vector)
    features=Column(JSONB)

class SequenceList(Base):
    __tablename__ = 'sequence_list'
    id = Column(Integer, primary_key=True, autoincrement=True)
    seq_id=Column(Integer, ForeignKey('sequence.id'))
    paired_msa_path=Column(String, nullable=True)
    features=Column(JSONB)