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
            class_name=args[0].__class__.__name__,
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
        method=self._get_method(access_key=access_key, email=email)
        results=method(*self.args, **self.kwargs)
        # results is already an api call because of the decorator
        return results


    def __str__(self):
        return f"ApiCall @ {self.query_time} with args:{self.args}, kwargs:{self.kwargs}"

    def __repr__(self):
        return self.__str__()

def chunk_api_response(response: dict, max_chunk_chars: int = 1000):
    """
    chunks an api response, this will be used for semantic searching the chunks
    :param max_chunk_chars: for larger ones with text
    :return: list of chunks with path of the dict starting with root
    """
    chunks = []

    def recurse(obj, path="root"):
        if isinstance(obj, dict):
            # combine all key-values into one chunk if small enough
            temp_text = ""
            for k, v in obj.items():
                new_path = f"{path}.{k}"
                if isinstance(v, (dict, list)):
                    recurse(v, new_path)
                else:
                    temp_text += f"{k}: {v} | "
            if temp_text:
                # Split only if too large
                for i in range(0, len(temp_text), max_chunk_chars):
                    chunks.append({"text": temp_text[i:i + max_chunk_chars], "path": path})
        elif isinstance(obj, list):
            # combine list elements into one chunk if it fits
            list_text = " | ".join(str(x) for x in obj)
            if len(list_text) <= max_chunk_chars:
                chunks.append({"text": f"{path}: {list_text}", "path": path})
            else:
                # recursively split large lists
                for idx, item in enumerate(obj):
                    recurse(item, f"{path}[{idx}]")
        else:
            chunks.append({"text": f"{path}: {obj}", "path": path})

    recurse(response)
    return chunks



