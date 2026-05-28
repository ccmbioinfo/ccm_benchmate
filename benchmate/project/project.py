import os
import shutil
import warnings

import pandas as pd
import yaml
from functools import cached_property, partial

from sqlalchemy import select, insert, create_engine

from benchmate.knowledge_base.knowledge_base import KnowledgeBase
from benchmate.project.utils import (Literature, Apis, Alignment, Genome, Sequence, Structure, Molecule)
from benchmate.inference.inference import Inference
from benchmate.utils.general_utils import DataIntegrityError, ProjectNameError

from benchmate.genome.genome import Genome

from benchmate.ranges.genomicranges import (GenomicRange,
                                            CompoundGenomicRange,
                                            GenomicRangesList, GenomicRangesDict)

from benchmate.ranges.ranges import Range, RangesList, RangesDict
from benchmate.variant.variant import SequenceVariant, StructuralVariant, TandemRepeatVariant



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
        self.literature=Literature(self.config["literature"], inference=self.inference)
        os.makedirs(self.config['literature']["pdf_path"], exist_ok=True)

        #alignment
        self.alignment=Alignment(self.config["alignment"])
        os.makedirs(self.config['alignment']["folddisco_db_root"], exist_ok=True)
        os.makedirs(self.config['alignment']["foldseek_db_root"], exist_ok=True)
        os.makedirs(self.config['alignment']["mmseqs2_db_root"], exist_ok=True)
        os.makedirs(self.config['alignment']["blast_db_root"], exist_ok=True)
        self.alignment.find_databases()

        self.apis = Apis(self.config["apis"])

        #here we use these instances it's always project.this or project.that
        self.molecule=Molecule
        self.molecule.to_kb=partial(self.molecule.to_kb, project=self)
        self.molecule.from_kb=partial(self.molecule.from_kb, project=self)

        self.sequence=Sequence
        self.sequence.to_kb=partial(self.sequence.to_kb, project=self)
        self.sequence.from_kb=partial(self.sequence.from_kb, project=self)

        self.structure=Structure
        self.structure.to_kb=partial(self.structure.to_kb, project=self)
        self.structure.from_kb=partial(self.structure.from_kb, project=self)

        # variants are straightforward
        self.structural_variant=StructuralVariant
        self.structural_variant.to_kb=partial(self.structural_variant.to_kb, project=self)
        self.structure.from_kb=partial(self.structure.from_kb, project=self)

        self.sequence_variant=SequenceVariant
        self.sequence_variant.to_kb=partial(self.sequence_variant.to_kb, project=self)
        self.sequence_variant.from_kb=partial(self.sequence_variant.from_kb, project=self)

        self.tandem_repeat_variant=TandemRepeatVariant
        self.tandem_repeat_variant.to_kb=partial(self.tandem_repeat_variant.to_kb, project=self)
        self.tandem_repeat_variant.from_kb=partial(self.tandem_repeat_variant.from_kb, project=self)

        #this is a major TODO
        for genome in self.config["genome"]["genomes"].keys():
            # bare minimum to create a genome
            if os.path.exists(self.config['genome']["genomes"][genome]["fasta"]) and \
                    os.path.exists(self.config['genome']["genomes"][genome]["gtf"]):
                genome_path=os.path.join(self.config["genome"]["genome_path"], genome)
                try:
                    os.makedirs(genome_path, exist_ok=False)

                    fasta=self.config['genome']["genomes"][genome]["fasta"]
                    gtf=self.config['genome']["genomes"][genome]["gtf"]
                    transcriptome=self.config["genome"]["genomes"][genome]["transcriptome"]
                    proteome=self.config["genome"]["genomes"][genome]["proteome"]
                    for file in [fasta, gtf, transcriptome, proteome]:
                        if file is not None:
                            shutil.copy(file, genome_path)

                    new_genome=Genome()
                except:
                    warnings.warn(f"a genome with the name {genome} already exists")


    def _project_create(self):
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

    #below methods return some basic informatio about different stored modalities, you can then use the
    # returned ids to get the actual instances of the objects


    def _kb_create(self):
        self.kb._create_kb()

    def __str__(self):
        return f"Project(name:\n{self.name}\n\nproject_id:\n{self.project_id}\n\ndescription:\n{self.description})"

    def __repr__(self):
        return f"Project(name={self.name}, project_id={self.project_id}"


    