
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
    "BioGrid":"benchmate.apis.biogrid",
    "IntAct":"benchmate.apis.intact",
    "OLS":"benchmate.apis.ols",
}

from datetime import datetime
from functools import wraps

def api_call(call_class_getter):
    """
    This is one of the workhorses of this module, it is a decorator function that takes a call (if decorated) and
    returns and ApiCall instance (see below), This gives the api call a few handy tools that can be used later on.
    :param call_class_getter: See project, there is another api call class that includes methods to get things from a database
    and put things in a database
    :return: a decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            query_time = datetime.now()
            result = func(self, *args, **kwargs)
            call_class = call_class_getter(self)
            return call_class(
                class_name=self.__class__.__name__,
                method_name=func.__name__,
                init_kwargs=self.init_kwargs,
                results=result,
                args=args,
                kwargs=kwargs,
                query_time=query_time,
            )
        return wrapper
    return decorator


@dataclass(slots=True)
class ApiCall:
    """
    Stores metadata and results of an API call. This is to make it easier to track api calls for knowledge base construction.
    """
    class_name: str = None
    method_name: str = None
    init_kwargs: dict = None
    results: dict = None
    args: tuple= None
    kwargs: dict = None
    query_time: datetime = None

    def _get_method(self, **init_kwargs):
        module=importlib.import_module(api_mapper[self.class_name])
        cls=getattr(module, self.class_name)
        instance=cls(**init_kwargs)
        method=getattr(instance, self.method_name)
        return method

    def rerun(self):
        """
        rerun the api call with the same parameters, useful if the api call failed or if you want to update the results
        :param access_key: if the api requires an access key like alphagenome or biogrid
        :param email: if the api requires an email like ncbi
        :return: an updated ApiCall instance
        """
        method=self._get_method(**self.init_kwargs)
        results=method(*self.args, **self.kwargs)
        # results is already an api call because of the decorator
        return results


    def __str__(self):
        return f"ApiCall @ {self.query_time} with args:{self.args}, kwargs:{self.kwargs}"

    def __repr__(self):
        return self.__str__()





