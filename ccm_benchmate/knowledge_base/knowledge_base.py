import pandas as pd

from sqlalchemy import MetaData, select
from sqlalchemy.orm import sessionmaker

from ccm_benchmate.project.project import Project


class KnowledgeBase:
    def __init__(self, name):

        self.name=name

        # TODO create the engine based on the project name, if there is no database with that name init
        self.meta = MetaData(bind=self.engine)
        self.meta.reflect(bind=self.engine)
        self.session = sessionmaker(self.engine)
        self.db_tables = self.meta.tables

    def create_kb(self):
        pass





#TODO try some large-ish models for chatting with the data