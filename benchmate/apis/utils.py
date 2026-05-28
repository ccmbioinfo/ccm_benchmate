
from functools import cached_property
import importlib
from dataclasses import dataclass
from datetime import datetime
from functools import wraps

import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.exc import NoResultFound

from benchmate.utils.general_utils import DataIntegrityError

#I'm keeping this here, instead of using the whole inference thing. I might need to re-write inference
# to be more generic and import method from utils depending on the kind of thing we are doing.


api_mapper={
    "Ensembl":"benchmate.apis.ensembl",
    "Ncbi":"benchmate.apis.ncbi",
    "Reactome":"benchmate.apis.reactome",
    "RnaCentral":"benchmate.apis.rnacentral",
    "StringDb":"benchmate.apis.stringdb",
    "UniProt":"benchmate.apis.uniprot",
    "BioGrid":"benchmate.apis.others",
    "IntAct":"benchmate.apis.others",
    "OLS":"benchmate.apis.ols",
}

def api_call(func):
    """
    add metadata to an api call and return the apicall dataclass instance insteaed of just a dict
    :param func: function to be decorated
    :return: a wrapper function, this will return an ApiCall instance with all information about the api call
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        query_time = datetime.now()
        result = func(*args, **kwargs)

        return ApiCall(
            class_name=args[0].__class__.__name__,
            method_name=func.__name__,
            results=result,
            args=args[1:],  # exclude 'self'
            kwargs=kwargs,
            query_time=query_time
        )
    return wrapper


@dataclass(slots=True)
class ApiCall:
    """
    Stores metadata and results of an API call. This is to make it easier to track api calls for knowledge base construction.
    """
    class_name: str = None
    method_name: str = None
    results: dict = None
    args: tuple= None
    kwargs: dict = None
    query_time: datetime = None

    def _get_method(self, access_key=None, email=None):
        module=importlib.import_module(api_mapper[self.class_name])
        cls=getattr(module, self.class_name)
        if access_key is not None:
            instance=cls(access_key=access_key)
        elif email is not None:
            instance=cls(email=email)
        elif email is not None and access_key is not None:
            instance=cls(email=email, access_key=access_key)
        else:
            instance=cls()
        method=getattr(instance, self.method_name)
        return method

    def rerun(self, access_key=None, email=None):
        """
        rerun the api call with the same parameters, useful if the api call failed or if you want to update the results
        :param access_key: if the api requires an access key like alphagenome or biogrid
        :param email: if the api requires an email like ncbi
        :return: an updated ApiCall instance
        """
        method=self._get_method(access_key=access_key, email=email)
        results=method(*self.args, **self.kwargs)
        # results is already an api call because of the decorator
        return results


    def __str__(self):
        return f"ApiCall @ {self.query_time} with args:{self.args}, kwargs:{self.kwargs}"

    def __repr__(self):
        return self.__str__()

    def to_kb(self, project):
        api_table = project.kb.db_tables["api_call"]
        params={"args":self.args, "kwargs":self.kwargs}
        # add main results

        stmt = insert(api_table).values(
            project_id=project.project_id,
            class_name=self.class_name,
            method_name=self.method_name,
            params=params,
            query_time=self.query_time,
            results=self.results,
        ).returning(api_table.c.id)

        result = project.kb.session().execute(stmt)
        new_id = result.scalar_one()
        project.kb.session().commit()
        # add chunks
        return new_id

    @classmethod
    def from_kb(cls, project, id):
        api_table = project.kb.db_tables["api_call"]

        main_stmt=select(api_table.c.class_name,
                          api_table.c.method_name,
                          api_table.c.params,
                          api_table.c.results,
                          api_table.c.query_time,
                          api_table.c.flat).where(api_table.c.id == id)

        results=project.kb.session().execute(main_stmt).fetchall()
        if len(results)==0:
            raise NoResultFound("Could not find an api call with id {}".format(id))

        if len(results)>1:
            raise DataIntegrityError("Found more than one api call with id {}".format(id))

        params = results[2]
        args = params.get("args")
        kwargs = params.get("kwargs")

        call=cls(
            class_name=results[0][0],
            method_name=results[0][1],
            results=results[0][3],
            args=args,
            kwargs=kwargs,
            query_time=results[0][4]
        )
        return call



