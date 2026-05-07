import pandas as pd
import yaml
from functools import cached_property, partial
from datetime import datetime

from openai import project
from sqlalchemy import select, insert, create_engine

from benchmate.knowledge_base.knowledge_base import KnowledgeBase
from benchmate.project.utils import Literature, Apis, Alignment
from benchmate.inference.inference import Inference
from benchmate.utils.general_utils import DataIntegrityError, ProjectNameError

from benchmate.sequence.sequence import Sequence, SequenceList
from benchmate.molecule.molecule import Molecule
from benchmate.structure.structure import Structure

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
        self.inference = Inference(self.config["inference"])
        self.name=self.config["project"]["name"]
        self.description=self.config["project"]["description"]
        self.engine=create_engine(self.config["knowledge_base"]["conn_string"])
        self.kb=KnowledgeBase(self.engine)
        self._kb_create()
        self._project_create()

        #modules
        self.literature=Literature(self.config["literature"], inference=self.inference)
        #self.apis=Apis(self.config["api"])
        #self.alignment=Alignment(self.config["alignment"])
        self.apis=None
        self.alignment=None

        #here we use these instances it's always project.this or project.that
        self.molecule=Molecule
        self.molecule.to_kb=partial(self.molecule.to_kb, project=self)
        self.sequence=Sequence
        self.sequence.to_kb=partial(self.sequence.to_kb, project=self)
        self.structure=Structure
        self.structure.to_kb=partial(self.structure.to_kb, project=self)
        self.structural_variant=StructuralVariant
        self.structural_variant.to_kb=partial(self.structural_variant.to_kb, project=self)
        self.sequence_variant=SequenceVariant
        self.sequence_variant.to_kb=partial(self.sequence_variant.to_kb, project=self)
        self.tandem_repeat_variant=TandemRepeatVariant
        self.tandem_repeat_variant.to_kb=partial(self.tandem_repeat_variant.to_kb, project=self)

    def _project_create(self):
        project_table=self.kb.db_tables["project"]
        query=select(project_table.c.id).filter(project_table.c.name==self.name) # key column in tables.py is "id" not "project_id" 
        results=self.kb.session.execute(query).fetchall() #session is an object, not a factory function, using instead of session() so there is only one session object

        if len(results)==0:
            now = datetime.now()
            ins=insert(project_table).values(name=self.name,
                                             description=self.description,created_at=now,updated_at=now).returning(project_table.c.id) # Project class in tables.py has created_at and updated_at
            self.project_id=self.kb.session.execute(ins).scalar()
            self.kb.session.commit() # new project row presists right away
        elif len(results)==1:
            self.project_id=results[0][0]
        else:
            raise ProjectNameError("There are more than one projects with the same name")
        return self

    #below methods return some basic informatio about different stored modalities, you can then use the
    # returned ids to get the actual instances of the objects
    @property
    def papers(self):
        """return some basic information about the papers in the project
        :return: a dataframe of papers and ids
        """
        papers_table=self.kb.db_tables["papers"]
        papers=papers_table.select(papers_table.c.id,
                                   papers_table.c.source,
                                   papers_table.c.source_id,
                                   papers_table.c.title,
                                   papers_table.c.abstract).where(papers_table.c.project_id==self.project_id)
        papers=pd.DataFrame(self.kb.session().execute(papers).fetchall())
        return papers

    @property
    def molecules(self):
        """
        return some basic information about the molecules in the project
        :return: a databframe of molecules and ids
        """
        molecules_table=self.kb.db_tables["molecule"]
        molecules=molecules_table.select(molecules_table.c.id,
                                         molecules_table.c.name,
                                         molecules_table.c.smiles).where(molecules_table.c.project_id==self.project_id)
        molecules=pd.DataFrame(self.kb.session().execute(molecules).fetchall())
        return molecules

    @property
    def genomes(self):
        """
        returns basic information about the genomes in the project
        :return: a dataframe of genomes and ids
        """
        genome_table=self.kb.db_tables["genome"]
        genomes=genome_table.select(genome_table.c.id,
                                    genome_table.c.genome_name,
                                    genome_table.c.description).where(genome_table.c.project_id==self.project_id)
        genomes=pd.DataFrame(self.kb.session().execute(genomes).fetchall())
        return genomes

    @property
    def sequences(self):
        sequence_table=self.kb.db_tables["sequence"]
        sequences=sequence_table.select(sequence_table.c.id,
                                       sequence_table.c.name,
                                       sequence_table.c.sequence).where(sequence_table.c.project_id==self.project_id)
        sequences=pd.DataFrame(self.kb.session().execute(sequences).fetchall())
        return sequences

    @property
    def structures(self):
        structure_table=self.kb.db_tables["structure"]
        structures=structure_table.select(structure_table.c.id,
                                         structure_table.c.name).where(structure_table.c.project_id==self.project_id)
        structures=pd.DataFrame(self.kb.session().execute(structures).fetchall())
        return structures

    @property
    def variants(self):
        seq_var_table=self.kb.db_tables["sequence_variant"]
        str_var_table=self.kb.db_tables["structural_variant"]
        tandem_repeat_table=self.kb.db_tables["tandem_repeat_variant"]
        seq_vars=seq_var_table.select(seq_var_table.c.id,
                                      seq_var_table.c.chrom,
                                      seq_var_table.c.pos,
                                      seq_var_table.c.ref,
                                      seq_var_table.c.alt).where(seq_var_table.c.project_id==self.project_id)

        str_vars=str_var_table.select(seq_var_table.c.id,
                                      seq_var_table.c.chrom,
                                      seq_var_table.c.pos,
                                      seq_var_table.c.ref,
                                      seq_var_table.c.alt).where(str_var_table.c.project_id==self.project_id)

        tandem_repeats=tandem_repeat_table.select(seq_var_table.c.id,
                                      seq_var_table.c.chrom,
                                      seq_var_table.c.pos,
                                      seq_var_table.c.ref,
                                      seq_var_table.c.alt).where(tandem_repeat_table.c.project_id==self.project_id)

        seq_vars=pd.DataFrame(self.kb.session().execute(seq_vars).fetchall())
        seq_vars["type"]="sequence_variant"
        str_vars=pd.DataFrame(self.kb.session().execute(str_vars).fetchall())
        str_vars["type"]="structural_variant"
        tandem_repeats=pd.DataFrame(self.kb.session().execute(tandem_repeats).fetchall())
        tandem_repeats["type"]="tandem_repeat_variant"

        vars=pd.concat([seq_vars, str_vars, tandem_repeats])
        return vars

    @property
    def api_calls(self):
        """
        return basic information about the api calls in the project
        :return: a dataframe of api calls and ids
        """
        api_calls_table=self.kb.db_tables["api_call"]
        calls=api_calls_table.select(api_calls_table.c.id,
                                     api_calls_table.c.class_name,
                                     api_calls_table.c.method_name,
                                     api_calls_table.c.params,
                                     api_calls_table.c.query_time).where(api_calls_table.c.project_id==self.project_id)
        calls=pd.DataFrame(self.kb.session().execute(calls).fetchall())
        return calls

    def _kb_create(self):
        self.kb._create_kb()

    def __str__(self):
        return f"Project(name:\n{self.name}\n\nproject_id:\n{self.project_id}\n\ndescription:\n{self.description})"

    def __repr__(self):
        return f"Project(name={self.name}, project_id={self.project_id}"


    