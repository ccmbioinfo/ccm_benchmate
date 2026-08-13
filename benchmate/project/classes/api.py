
from functools import partial
from sqlalchemy import select, insert
from sqlalchemy.exc import NoResultFound

from benchmate.utils.general_utils import DataIntegrityError

from benchmate.apis.utils import ApiCall as BaseApiCall
from benchmate.apis.ncbi import Ncbi
from benchmate.apis.ensembl import Ensembl
from benchmate.apis.alphagenome import AlphaGenome
from benchmate.apis.biogrid import BioGrid
from benchmate.apis.intact import IntAct
from benchmate.apis.ols import OLS
from benchmate.apis.reactome import Reactome
from benchmate.apis.rnacentral import RnaCentral
from benchmate.apis.stringdb import StringDb
from benchmate.apis.uniprot import UniProt
from benchmate.apis.ebi import EBI


class ApiCall(BaseApiCall):
    """
    A subclass of api call with methods to send and recieve api calls from the project database
    """
    def to_kb(self, project=None):
        """
        send an api call to the project database, so can get them later
        :param project: project object
        :return: the id of the api call
        """
        proj = project or self.project
        if proj is None:
            raise ValueError("Project instance is required to store API call in knowledge base")
        api_table = proj.kb.db_tables["api_call"]
        params = {"args": self.args, "kwargs": self.kwargs}

        stmt = insert(api_table).values(
            project_id=proj.project_id,
            class_name=self.class_name,
            method_name=self.method_name,
            init_kwargs=self.init_kwargs,
            params=params,
            query_time=self.query_time,
            results=self.results,
        ).returning(api_table.c.id)

        result = proj.kb.session().execute(stmt)
        new_id = result.scalar_one()
        proj.kb.session().commit()
        return new_id

    @classmethod
    def from_kb(cls, project, id):
        """given an api call id, return an api call object for that api call id
        :param project: project object
        :param id: api call id
        :return: an api call object for that api call id"""
        api_table = project.kb.db_tables["api_call"]

        main_stmt = select(api_table.c.class_name,
                           api_table.c.method_name,
                           api_table.c.init_kwargs,
                           api_table.c.params,
                           api_table.c.results,
                           api_table.c.query_time,
                           api_table.c.flat_results).where(api_table.c.id == id)

        results = project.kb.session().execute(main_stmt).fetchall()
        if len(results) == 0:
            raise NoResultFound("Could not find an api call with id {}".format(id))

        if len(results) > 1:
            raise DataIntegrityError("Found more than one api call with id {}".format(id))

        params = results[0][3] or {}
        args = params.get("args")
        kwargs = params.get("kwargs")

        call = cls(
            class_name=results[0][0],
            method_name=results[0][1],
            init_kwargs=results[0][2],
            args=args,
            kwargs=kwargs,
            results=results[0][4],
            query_time=results[0][5],
            project=project,
        )
        return call

class Apis:
    """
    a thin wrapper around the api call class instances so they can be run as project.apis.ncbi or something
    """
    def __init__(self, config, project=None):
        self.config=config
        self.email=self.config["email"]
        self.biogrid_api_key=self.config["biogrid_api_key"]
        self.alphagenome_api_key=self.config["alphagenome_api_key"]

        self.call_class=partial(ApiCall, project=project) if project else ApiCall

        #setup the classes
        self.alphagenome=AlphaGenome(self.alphagenome_api_key)

        self.biogrid=BioGrid(self.biogrid_api_key)
        self.biogrid.call_class=self.call_class

        self.ebi=EBI()

        self.ensembl=Ensembl()
        self.ensembl.call_class=self.call_class

        self.intact=IntAct()
        self.intact.call_class=self.call_class

        self.ncbi=Ncbi(email=self.email)
        self.ncbi.call_class=self.call_class

        self.ols=OLS()
        self.ols.call_class=self.call_class

        self.reactome=Reactome()
        self.reactome.call_class=self.call_class

        self.rnacentral=RnaCentral()
        self.rnacentral.call_class=self.call_class

        self.stringdb=StringDb()
        self.stringdb.call_class=self.call_class

        self.uniprot=UniProt()
        self.uniprot.call_class=self.call_class
