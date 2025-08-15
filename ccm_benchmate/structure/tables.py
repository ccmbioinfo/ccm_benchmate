from sqlalchemy import (
    Column, ForeignKey, Integer, String, ARRAY, Float
)
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import declarative_base
Base = declarative_base()


class Structure(Base):
    __tablename__="structure"
    id = Column(Integer, primary_key=True, autoincrement=True)


