import os
import yaml
from functools import partial

from sqlalchemy import select, insert, create_engine
import pandas as pd

from benchmate.knowledge_base.knowledge_base import KnowledgeBase
from benchmate.inference.inference import Inference
from benchmate.literature.paper_processor import PaperProcessor

from benchmate.project.classes.variant import *
from benchmate.project.classes.structure import Structure
from benchmate.project.classes.sequence import Sequence
from benchmate.project.classes.alignment import Alignment
from benchmate.project.classes.molecule import Molecule
from benchmate.project.classes.literature import *
from benchmate.project.classes.api import Apis
from benchmate.project.classes.genome import Genomes

from benchmate.project.search import ProjectSearch
from benchmate.project.utils import *


class ProjectNameError(Exception):
    pass

class Project:
    """
    this is the metaclass for the whole thing, it will collect all the modules and will be main point for interacting with the knowledgebase
    """
    def __init__(self, config_path):
        """
        This is the metaclass for the whole thing, it will collect all the modules and will be main point for interacting with
        the knowledgebase, it will overwrite some of the methods with the parameters that are defnined in the config file
        :param config_path: path for the config file, see config.yaml for an example, it is not as flexible as the structure imples
        especially for the inference part.
        """
        with config_path.open("r") as f:
            self.config=yaml.safe_load(f)

        #basics
        self.name=self.config["project"]["name"]
        self.description=self.config["project"]["description"]
        self.engine=create_engine(self.config["knowledge_base"]["conn_string"])
        self.kb=KnowledgeBase(self.engine)
        self._kb_create()
        self._project_create()
        self.inference = Inference(self.config["inference"])

        #literature
        self.paper=Paper
        self.paper.from_kb=partial(self.paper.from_kb, project=self)
        self.paper.to_kb=partial(self.paper.to_kb, project=self)
        self.litsearch=LitSearch(self.config["literature"])
        os.makedirs(self.config["literature"]["pdf_path"], exist_ok=True)
        self.paper_processor=PaperProcessor(self.inference, self.config["literature"])

        #alignment
        self.alignment=Alignment(self.config["alignment"])
        os.makedirs(self.config['alignment']["folddisco_db_root"], exist_ok=True)
        os.makedirs(self.config['alignment']["foldseek_db_root"], exist_ok=True)
        os.makedirs(self.config['alignment']["mmseqs2_db_root"], exist_ok=True)
        os.makedirs(self.config['alignment']["blast_db_root"], exist_ok=True)
        self.alignment.foldseek.find_local_databases()
        self.alignment.folddisco.find_local_databases()
        self.alignment.mmseqs.find_local_databases()
        self.alignment.blast.find_local_databases()

        #apis
        self.apis=Apis(self.config["apis"])
        self.apis.call_class.to_kb=partial(self.apis.call_class, project=self)
        self.apis.call_class.from_kb=partial(self.apis.call_class, project=self)

        #molecule
        self.molecule=Molecule
        self.molecule.to_kb=partial(self.molecule.to_kb, project=self)
        self.molecule.from_kb=partial(self.molecule.from_kb, project=self)

        #sequence
        self.sequence=Sequence
        self.sequence.to_kb=partial(self.sequence.to_kb, project=self)
        self.sequence.from_kb=partial(self.sequence.from_kb, project=self)

        #structure
        self.structure=Structure
        self.structure.to_kb=partial(self.structure.to_kb, project=self)
        self.structure.from_kb=partial(self.structure.from_kb, project=self)

        # variants
        self.structural_variant=StructuralVariant
        self.structural_variant.to_kb=partial(self.structural_variant.to_kb, project=self)
        self.structure.from_kb=partial(self.structure.from_kb, project=self)

        self.sequence_variant=SequenceVariant
        self.sequence_variant.to_kb=partial(self.sequence_variant.to_kb, project=self)
        self.sequence_variant.from_kb=partial(self.sequence_variant.from_kb, project=self)

        self.tandem_repeat_variant=TandemRepeatVariant
        self.tandem_repeat_variant.to_kb=partial(self.tandem_repeat_variant.to_kb, project=self)
        self.tandem_repeat_variant.from_kb=partial(self.tandem_repeat_variant.from_kb, project=self)

        #genomes, a new genome instance for each genome specified, this may take a while
        self.genomes=Genomes(self.config["genomes"], self)

        #search functions
        self.search=ProjectSearch(self)


    def _project_create(self):
        """
        create a project for a given db server connection the database must exist
        :return: self with project id
        """
        project_table=self.kb.db_tables["project"]
        query=select(project_table.c.project_id).filter(project_table.c.name==self.name)
        results=self.kb.session().execute(query).fetchall()

        if len(results)==0:
            ins=insert(project_table).values(name=self.name,
                                             description=self.description).returning(project_table.c.project_id)
            self.project_id=self.kb.session().execute(ins).scalar()
        elif len(results)==1:
            self.project_id=results[0][0]
        else:
            raise ProjectNameError("There are more than one projects with the same name")
        return self

    def list_items(self, type):
        """
        return a simple informative dataframe of all the items in the databse, if you have a lot of things (10s of thousands)
        may take a few minutes
        :param type: what kind of thing to return
        :return: a pandas dataframe of ids and basic info so you can get the actual class instance if you want
        """
        if type not in list(type_dict.keys()):
            raise ValueError(f"{type} is not a valid type, only {','.join(list(type_dict.keys()))} are allowed")
        else:
            table=self.kb.db_tables[type]
            query_columns = [table.__table__.c[n] for n in type_dict[type]["columns"]]
            stmt=select(*query_columns).filter(table.c.project_id==self.project_id)
            results=self.kb.session().execute(stmt).fetchall()
            if len(results)==0:
                return None
            else:
                return pd.DataFrame(results)

    def _kb_create(self):
        self.kb._create_kb()

    def __str__(self):
        return f"Project(name:\n{self.name}\n\nproject_id:\n{self.project_id}\n\ndescription:\n{self.description})"

    def __repr__(self):
        return f"Project(name={self.name}, project_id={self.project_id}"


    