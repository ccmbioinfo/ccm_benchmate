
from ccm_benchmate.apis.ensembl import Ensembl
from ccm_benchmate.apis.ncbi import Ncbi
from ccm_benchmate.apis.reactome import Reactome
from ccm_benchmate.apis.uniprot import UniProt
from ccm_benchmate.apis.stringdb import StringDb
from ccm_benchmate.apis.rnacentral import RnaCentral
from ccm_benchmate.apis.others import BioGrid, IntAct

from ccm_benchmate.sequence.sequence import Sequence, SequenceList, SequenceDict
from ccm_benchmate.structure.structure import Structure, Complex
from ccm_benchmate.genome.genome import Genome
from ccm_benchmate.literature.literature import Paper, LitSearch



from ccm_benchmate.knowledge_base.knowledge_base import KnowledgeBase

class Apis:
    """
    This is just an aggreation of the classes in the apis section, this will be part of the project class
    """
    def __init__(self, email, biogrid_api_key):
        self.ensembl = Ensembl()
        self.ncbi = Ncbi(email=email)
        self.reactome = Reactome()
        self.UniProt = UniProt()
        self.stringdb = StringDb()
        self.biogrid = BioGrid(access_key=biogrid_api_key)
        self.rnacentral = RnaCentral()
        self.intact = IntAct()

    def api_call(self, kb=None, to_kb=True, **kwargs):
        pass


class Project:
    """
    this is the metaclass for the whole thing, it will collect all the modules and will be main point for interacting with the knowledgebase
    """
    def __init__(self, description):
        self.description = description
        self.apis = Apis()
        self.genome = Genome()
        self.structures=None
        self.sequences=None
        self.papers=None


    def _kb_create(self, engine):
        pass

    def _kb_connect(self, engine):
        pass

    #TODO this will do a lit search using the lit search class and then return papers will need to find a way to get them in the knowledge base
    def literature_search(self):
        pass

    #TODO
    def get_sequences(self):
        pass

    #TODO
    def get_structures(self):
        pass






    