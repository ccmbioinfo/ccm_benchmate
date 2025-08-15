
from sqlalchemy import Column, Integer, String, Float, JSON
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import ARRAY

from sqlalchemy.orm import declarative_base
Base = declarative_base()

class BaseVariant:
    """Abstract base class for all variant types."""
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
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
    annotations = Column(JSON, default=dict, nullable=False, index=True)

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
    annotations = Column(JSON, default=dict, nullable=False, index=True)

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
    annotations = Column(JSON, default=dict, nullable=False, index=True)