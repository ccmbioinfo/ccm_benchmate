import importlib
from dataclasses import dataclass
from datetime import datetime
from functools import wraps

#alphagenome is rather static and does not return an apicall
api_mapper={
    "Ensembl":"benchmate.apis.ensembl",
    "Ncbi":"benchmate.apis.ncbi",
    "Reactome":"benchmate.apis.reactome",
    "RnaCentral":"benchmate.apis.rnacentral",
    "StringDb":"benchmate.apis.stringdb",
    "UniProt":"benchmate.apis.uniprot",
    "BioGrid":"benchmate.apis.others",
    "IntAct":"benchmate.apis.others",
}

def api_call(func):
    """
    add metadata to an api call and return the apicall dataclass instance insteaed of just a dict
    :param func:
    :return:
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        query_time = datetime.now()
        result = func(*args, **kwargs)

        return ApiCall(
            class_name=args[0].__class__,
            method_name=func.__name__,
            results=result,
            args=args[1:],  # exclude 'self'
            kwargs=kwargs,
            query_time=query_time
        )
    return wrapper


@dataclass
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

    @api_call
    def rerun(self, access_key=None, email=None):
        module=importlib.import_module(api_mapper[self.class_name])
        cls=getattr(module, api_mapper[self.class_nane])
        if access_key is not None:
            instance=cls(access_key=access_key)
        elif email is not None:
            instance=cls(email=email)
        elif email is not None and access_key is not None:
            instance=cls(email=email, access_key=access_key)
        else:
            instance=cls()
        method=getattr(instance, self.method_name)
        results=method(*self.args, **self.kwargs)
        return results


    def __str__(self):
        return f"ApiCall @ {self.query_time} with args:{self.args}, kwargs:{self.kwargs}"

    def __repr__(self):
        return self.__str__()




