from functools import cached_property
import importlib
from dataclasses import dataclass
from datetime import datetime
from functools import wraps

import pandas as pd
from model2vec import StaticModel

from benchmate.config import *

embedding_model=StaticModel.from_pretrained(api_call["text_embedding_model"]["model"])

# alphagenome is rather static and does not return an apicall it returns, genomicrance, sequence or variant depending on the
# endpoint
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

    @cached_property
    def chunks(self, path="root", max_chunk_chars: int = 1000):
        """
        chunks an api response, this will be used for semantic searching the chunks
        :param max_chunk_chars: for larger ones with text
        :return: list of chunks with path of the dict starting with root
        """
        chunks=self._serialize(self.results, path=path, max_chunk_chars=max_chunk_chars)
        chunks_with_ids=[]
        for i in range(len(chunks)):
            chunks_with_ids.append([i, chunks[i]])
        return chunks_with_ids

    @cached_property
    def embeddings(self, model=embedding_model):
        texts=[chunk[1]["value"] for chunk in self.chunks]
        embeddings=model.encode(texts).tolist()
        return embeddings

    @cached_property
    def flat(self):
        """
        Flatten JSON response into a single summary string. This will be used for tsvector in full text search
        """
        return "|".join([item[1]["value"] for item in self.chunks])

    def _serialize(self, obj, path="root", max_chunk_chars=1000):
        scalars = (str, int, float, bool, type(None), bytes)
        chunks = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                path = f"{path}.{key}"
                if isinstance(value, dict):
                    chunks.extend(self._serialize(value, path, max_chunk_chars))
                elif isinstance(value, pd.DataFrame):
                    value = value.to_dict('records')
                    chunks.extend(self._serialize(value, path, max_chunk_chars))
                elif isinstance(value, (list, tuple, set)):
                    if isinstance(value, set):
                        value = list(value)
                    for i in range(len(value)):
                        new_path = f"{path}.{i}"
                        chunks.extend(self._serialize(value[i], new_path, max_chunk_chars))
                elif isinstance(value, scalars):
                    chunks.append({"path": path, "value": str(value)})
        return chunks
