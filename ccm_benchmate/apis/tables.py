from narwhals import Datetime
from sqlalchemy.orm import declarative_base

from sqlalchemy import (
    Column, Integer, String, JSON, DateTime, ForeignKey,
)

Base = declarative_base()

#TODO metadata about the genome like spikeins etc
class ApiCall(Base):
    __tablename__ = 'api_call'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    api_name = Column(String, nullable=False)
    params =Column(JSON, nullable=False)
    results=Column(JSON, index=True)
    query_time = Column(DateTime, nullable=False)

