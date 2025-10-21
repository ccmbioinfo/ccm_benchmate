from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker

from benchmate.knowledge_base.tables import *


class KnowledgeBase:
    def __init__(self, engine):
        """
        basic db constructor, will create the tables if it doesn't exist but we assume that the database is already created
        :param engine: sqlalchemy engine created from sqlalchemy.create_engine()
        """
        self.engine=engine
        self.meta = MetaData(bind=self.engine)
        self.meta.reflect(bind=self.engine)
        sess=sessionmaker(bind=self.engine)
        self.session = sess()
        self.db_tables = self.meta.tables

    def _create_kb(self):
        if len(self.db_tables)==0:
            Base.metadata.create_all(self.engine)
            self.meta.reflect(bind=self.engine)
            self.db_tables = self.meta.tables
        else:
            print("Database already exists")

    def __str__(self):
        return f"KnowledgeBase with tables {self.engine}"