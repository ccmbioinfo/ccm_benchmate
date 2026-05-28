import os
from pathlib import Path

from functools import cached_property, partial

#alignment
from benchmate.alignment.blast import Blast
from benchmate.alignment.mmseqs import MMSeqs
from benchmate.alignment.foldseek import FoldSeek
from benchmate.alignment.folddisco import FoldDisco

#APIS
from benchmate.apis.ensembl import Ensembl
from benchmate.apis.uniprot import UniProt
from benchmate.apis.stringdb import StringDb
from benchmate.apis.reactome import Reactome
from benchmate.apis.ebi import EBI
from benchmate.apis.ols import OLS
from benchmate.apis.biogrid import BioGrid
from benchmate.apis.alphagenome import AlphaGenome
from benchmate.apis.intact import IntAct
from benchmate.apis.rnacentral import RnaCentral
from benchmate.apis.ncbi import Ncbi

#Literature
from benchmate.literature.literature import LitSearch, Paper, OpenAlex
from benchmate.literature.paper_processor import PaperProcessor

#other modalities
from benchmate.sequence.sequence import Sequence as BaseSequence
from benchmate.molecule.molecule import Molecule as BaseMolecule
from benchmate.structure.structure import Structure as BaseStructure
from benchmate.genome.genome import Genome as BaseGenome

# no need for genome or knowledgebase they will be created by the clases themselves
# sequence, molecule, structure, variant, ranges are created per instance basis, so there needs to be
# some sort of method to add sequence, molecule etc.

class Apis:
    def __init__(self, config):
        self.config=config
        self.ensembl=Ensembl()
        self.uniprot=UniProt()
        self.stringdb=StringDb()
        self.biogrid=BioGrid(access_key=config["biogrid_api_key"])
        self.alphagenome=AlphaGenome(access_key=config["alphagenome_api_key"])
        self.reactome=Reactome()
        self.ebi=EBI(email=config["email"])
        self.ols=OLS()
        self.intact=IntAct()
        self.rnacentral=RnaCentral()
        self.ncbi=Ncbi(email=config["email"])

# the main issue here is now we need to create literture.paper instances not paper
class Literature:
    def __init__(self, config, inference, project):
        self.config=config
        self.openalex=OpenAlex(config["openalex_api_key"])
        self.litsearch=LitSearch()
        self.paper=Paper
        self.paper.get_json=partial(self.paper.get_json, openalex=self.openalex)
        self.paper.get_references=partial(self.paper.get_references, openalex=self.openalex)
        self.paper.get_related_works=partial(self.paper.get_related_works, openalex=self.openalex)
        self.paper.get_cited_by=partial(self.paper.get_cited_by, openalex=self.openalex)
        self.paper.download=partial(self.paper.download, destination=config["pdf_path"])
        self.paper.to_kb=partial(self.paper.to_kb, project=project)
        self.paper.from_kb = partial(self.paper.to_kb, project=project)
        self.processor=PaperProcessor(inference=inference, config=config)


class Alignment:
    def __init__(self, config):
        self.config=config
        self.blast=Blast()
        self.blast.create_db=partial(self.blast.create_db, output_path=self.config["blast_db_root"])
        self.mmseqs=MMSeqs()
        self.mmseqs.download_database=partial(self.mmseqs.download_database, location=self.config["mmseqs_db_root"])
        self.foldseek=FoldSeek()
        self.foldseek.download_database=partial(self.foldseek.download_database, location=self.config["foldseek_db_root"])
        self.folddisco = FoldDisco()
        self.folddisco.create_index = partial(self.folddisco.create_index, db_path=self.config["folddisco_db_root"])

    #this will go into the root folders and then count the specific files depending on the type
    def find_databases(self):
        pass

#TODO create genomes here
class Genome(BaseGenome):
    def __init__(self, config):
        self.config=config




class Sequence(BaseSequence):
    def __init__(self, config):
        self.config=config

    def _fastas(self):
        os.makedirs(self.config["fasta_root"], exist_ok=True)
        files=["dna.fa", "rna.fa", "protein.fa", "tdi.fa"] #tdi is 3di
        for file in files:
            if os.path.exists(os.path.join(self.config["fasta_root"], file)):
                continue
            else:
                Path(os.path.join(self.config["fasta_root"], file)).touch()


class Structure(BaseStructure):
    def __init__(self, config):
        self.config=config

class Molecule(BaseMolecule):
    def __init__(self, config):
        self.fingerprint_dim=config["fingerprint_dim"]
        self.fingerprint_radius=config["fingerprint_radius"]

