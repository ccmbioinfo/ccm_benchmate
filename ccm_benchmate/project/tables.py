
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

class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)