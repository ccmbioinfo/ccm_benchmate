import os
from pathlib import Path
from datetime import datetime
import yaml

from sqlalchemy import select, insert, create_engine

from benchmate.knowledge_base.knowledge_base import KnowledgeBase
from benchmate.inference.inference import Inference
from benchmate.literature.paper_processor import PaperProcessor

from benchmate.project.classes.variant import SequenceVariantFactory
from benchmate.project.classes.variant import StructuralVariantFactory
from benchmate.project.classes.variant import TandemRepeatVariantFactory

from benchmate.project.classes.structure import StructureFactory
from benchmate.project.classes.sequence import SequenceFactory
from benchmate.project.classes.molecule import MoleculeFactory

from benchmate.project.classes.alignment import Alignment

from benchmate.project.classes.literature import PaperFactory, LitSearch

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
        if isinstance(config_path, str):
            config_path = Path(config_path)
        with config_path.open("r") as f:
            self.config = yaml.safe_load(f)

        # basics
        self.name = self.config["project"]["name"]
        self.description = self.config["project"]["description"]
        self.engine = create_engine(self.config["knowledge_base"]["conn_string"])
        self.kb = KnowledgeBase(self.engine)
        self._kb_create()
        self._project_create()
        self.inference = Inference(self.config["inference"])

        self.paper = PaperFactory(self)
        self.litsearch = LitSearch(self.config["literature"])
        os.makedirs(self.config["literature"]["pdf_path"], exist_ok=True)
        self.paper_processor = PaperProcessor(self.inference, self.config["inference"]["layout_model"]["cache_dir"])

        # molecule
        self.molecule=MoleculeFactory(self)

        #structure
        os.makedirs(self.config["structure"]["pdb_path"], exist_ok=True)
        self.structure = StructureFactory(self)

        #sequence
        os.makedirs(self.config["sequence"]["fasta_path"], exist_ok=True)
        self.sequence = SequenceFactory(self)

        # Variants
        self.structural_variant = StructuralVariantFactory(self)
        self.sequence_variant = SequenceVariantFactory(self)
        self.tandem_repeat_variant = TandemRepeatVariantFactory(self)

        # alignment
        os.makedirs(self.config['alignment']["folddisco_db_root"], exist_ok=True)
        os.makedirs(self.config['alignment']["foldseek_db_root"], exist_ok=True)
        os.makedirs(self.config['alignment']["mmseqs2_db_root"], exist_ok=True)
        os.makedirs(self.config['alignment']["blast_db_root"], exist_ok=True)
        self.alignment = Alignment(self.config["alignment"])

        # apis
        self.apis = Apis(self.config["apis"], project=self)

        # genomes, a new genome instance for each genome specified, this may take a while
        os.makedirs(self.config["genome"]["genome_path"], exist_ok=True)
        self.genomes = Genomes(self.config["genome"], self)

        # search functions
        self.search = ProjectSearch(self)

    def _project_create(self):
        """
        create a project for a given db server connection the database must exist
        :return: self with project id
        """
        project_table = self.kb.db_tables["project"]
        query = select(project_table.c.id).filter(project_table.c.name == self.name)
        results = self.kb.session().execute(query).fetchall()

        if len(results) == 0:
            now = datetime.utcnow()
            ins = insert(project_table).values(name=self.name,
                                               description=self.description,
                                               created_at=now,
                                               updated_at=now).returning(project_table.c.id)
            self.project_id = self.kb.session().execute(ins).scalar()
            self.kb.session().commit()
        elif len(results) == 1:
            self.project_id = results[0][0]
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
            table = self.kb.db_tables[type]
            query_columns = [table.c[n] for n in type_dict[type]["columns"]]
            stmt = select(*query_columns).filter(table.c.project_id == self.project_id)
            results = self.kb.session().execute(stmt).fetchall()
            if len(results) == 0:
                return None
            else:
                return pd.DataFrame(results)

    def _kb_create(self):
        self.kb._create_kb()

    def __str__(self):
        return f"Project(name:\n{self.name}\n\nproject_id:\n{self.project_id}\n\ndescription:\n{self.description})"

    def __repr__(self):
        return f"Project(name={self.name}, project_id={self.project_id})"


