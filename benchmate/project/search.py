import importlib
import tempfile

from sqlalchemy import select, and_, or_
from sqlalchemy import cast, String, func, and_

from alignment.folddisco import FoldDisco
from alignment.foldseek import FoldSeek
from benchmate.molecule.molecule import Molecule
from benchmate.sequence.sequence import Sequence
from benchmate.ranges.genomicranges import GenomicRange, GenomicRangesList, GenomicRangesDict
from benchmate.variant.variant import SequenceVariant, TandemRepeatVariant, StructuralVariant

from benchmate.apis.utils import api_mapper

class MethodNotFoundError(Exception):
    pass

class BaseSearch:
    table_names=None
    table_name=None

    def __init__(self, project):
        self.project = project
        self.session = project.kb.session()
        if self.table_name:
            self.table = self.kb.tables[self.table_name]

        if self.table_names:
            self.tables = {
                name: self.kb.db_tables[name]
                for name in self.table_names
            }

    @property
    def kb(self):
        return self.project.kb

    def _execute_ids(self, stmt):
        return [r[0] for r in self.session.execute(stmt).fetchall()]

    def json_search(self, statement, table, column_name, filters):
        """
        :param statement: This is a select statement, it can be as simple as a full table or a single column
        :param column_name: which column is the jsonb column
        :param filters: filters  str | dict | list[str | dict]
        :return: filters added to the query
        """

        column = getattr(table, column_name)
        if not isinstance(filters, (list, tuple)):
            filters = [filters]

        conditions = []

        for item in filters:
            if isinstance(item, str):
                # search for the string
                conditions.append(
                    cast(column, String).ilike(f"%{item}%")
                )

            # Search for key:value pairs
            elif isinstance(item, dict):
                conditions.append(column.contains(item))

            else:
                raise TypeError(f"Unsupported filter type: {type(item)}")
        return statement.where(and_(*conditions))


class ApiCallSearch(BaseSearch):
    table_name="api_call"

    def __init__(self, project):
        super().__init__(project)

    def _base_statement(self, call_class, class_method):

        stms = select(self.table.c.id, self.table.c.class_name, self.table.c.method_name)
        if call_class:
            stms = stms.where(self.table.c.class_name == call_class)
            if class_method:
                if not class_method in list(api_mapper.keys()):
                    raise ModuleNotFoundError(f"Class {class_method} does not exist")

                module = importlib.import_module(api_mapper[call_class])

                if not hasattr(module, class_method):
                    raise MethodNotFoundError(f"{call_class} does not have a method called {class_method}")

                stms = stms.where(self.table.c.method_name == class_method)
        return stms

    def calls(self, call_class, class_method, query=None):
        column="params"
        stms=self._base_statement(call_class, class_method)
        if query:
            stms = self.json_search(stms, self.table, column, query)
        rows = self._execute_ids(stms)
        ids = [row[0] for row in rows]
        return ids

    #there query is mandatory since you are looking for something specific
    def results(self, query, call_class, class_method, project):
        stms=self._base_statement(call_class, class_method)
        stms=self.json_search(stms, self.table,"results", query)
        rows = self._execute_ids(stms)
        ids = [row[0] for row in rows]
        return ids


class PaperSearch(BaseSearch):
    table_name = "papers"

    figures="figures"
    tables="tables"
    chunked_text="body_text_chunked"

    def _base_statement(self):
        stms = select(self.table.c.id, self.table.c.title, self.table.c.external_ids)
        return stms

    def text(self, query, attribute, inference):
        """
        this will perform both keyword
        :param query: this is a dict, that can include keywords (positive and negative) and semantic search with reranking
        :param project:
        :param attribute: what to search in (abstract, title, figure/table captions, full_text)
        :return:
        """
        pass

    def image(self, query, inference):
        """"""
        pass

    def metadata(self, query):
        #this is json_search
        column = "full_json"
        stms = self.json_search(self._base_statement(), self.table, column, query)
        ids = self._execute_ids(stms)
        return ids

    def annotations(self, query):
        column="annotations"
        stms=self.json_search(self._base_statement(), self.table, column, query)
        ids=self._execute_ids(stms)
        return ids

# this is going to run folddisco or foldseek depending on the input
class StructureSearch(BaseSearch):
    table_name="structure"

    def _base_statement(self):
        stms = select(self.table.c.id, self.table.c.name, self.table.c.smiles)
        return stms

    def structure(self, query, method="foldseek", **kwargs):
        pass

    def annotations(self, query):
        column="annotations"
        stms=self.json_search(self._base_statement(), self.table, column, query)
        ids=self._execute_ids(stms)
        return ids

#not done
class SequenceSearch:
    table_name="sequence"

    def sequence(self, query, project):
        pass

    def annotations(self, query):
        column="annotations"
        stms=self.json_search(self._base_statement(), self.table, column, query)
        ids=self._execute_ids(stms)
        return ids



class MoleculeSearch(BaseSearch):

    table_name="molecule"

    def _base_statement(self):
        stms=select(self.table.c.id, self.table.c.name, self.table.c.smiles)
        return stms

    def molecule(self, query, fp_type="ecfp4", limit=1000):
        if isinstance(query, Molecule):  # this does tanimoto
            if not fp_type:
                fp_type = "ecfp4"
            if fp_type not in ["ecfp4", "fcfp4", "maccs"]:
                raise NotImplementedError(f"fp_type {fp_type} is not supported")

            col = getattr(self.table.c, fp_type)
            fp = getattr(query.info, fp_type)

            similarity = func.tanimoto_sml(
                col,
                fp
            ).label("similarity")

            base=self._base_statement().add_columns(similarity)
            stms = base.order_by(col.op("<->")(fp)).limit(limit)
            ids = self._execute_ids(stms)
        else:
            raise NotImplementedError(f"You can only use Molecule class instances in this method")
        return ids

    def annotations(self, query):
        column="annotations"
        stms=self.json_search(self._base_statement(), self.table, column, query)
        ids=self._execute_ids(stms)
        return ids


class VariantSearch(BaseSearch):

    types=["sequencevariant", "structuralvariant", "tandemrepeatvariant"]

    def _base_statement(self, table):
       stms=select(table.c.id, table.c.chrom, table.c.pos, table.c.ref, table.c.alt)
       return stms

    def _get_type(self, query):
        if isinstance(query, SequenceVariant):
            type="sequencevariant"
        elif isinstance(query, StructuralVariant):
            type="structuralvariant"
        elif isinstance(query, TandemRepeatVariant):
            type="tandemrepatvariant"
        else:
            raise ValueError(f"{type(query)} is not supported")
        return type

    def _get_tables(self, type):
        # define which table to query
        if type == "sequencevariant":
            tables = self.kb.tables["sequencevariant"]
        elif type == "structuralvariant":
            tables = self.kb.tables["structuralvariant"]
        elif type == "tandemrepatvariant":
            tables = self.kb.tables["tandemrepatvariant"]
        else:
            raise ValueError(f"Variant type {type} is not supported")
        return tables

    def variant(self, query):
        """
        search variants in the knowledge base
        :param query: what to search for if this is a variant or genomics range then the genomic coords are used
        if this is a list or str, we will be looking for annotation values, if it's a dict we will be looking for key value pairs
        :param type: type of variant to search for
        :param kwargs: other kwargs, that are specific to different variant types
        :return: ids, types and coords, ref alt of variants that are found
        """

        if isinstance(query, (SequenceVariant, StructuralVariant, TandemRepeatVariant)):
            var_type=self._get_type(query)
            table=self._get_tables(var_type)
            chrom=query.chrom
            start=query.pos
            ref=query.ref
            alt=query.alt
            base=self._base_statement(table)
            stms=base.where(table.c.chrom==chrom,
                             table.c.pos==start,
                             table.c.ref==ref,
                             table.c.alt==alt)
            ids=self._execute_ids(stms)
        else:
            raise NotImplementedError(f"Cannot use {type(query)} for searching variants")
        return ids

    def _query_range(self, query, types=None):
        ids={}
        if isinstance(query, GenomicRange):
            chrom=query.chrom
            start=query.ranges.start
            end=query.ranges.end
            if types is None:
                query_types=self.types
            else:
                query_types=[]
                for t in types:
                    if t not in types:
                        continue
                    else:
                      query_types.append(t)

            for t in query_types:
                table=self._get_tables(t)
                base=self._base_statement(table)
                stms=base.where(table.c.chrom==chrom, table.c.pos>=start, table.c.pos<=end)
                query_ids=self._execute_ids(stms)
                ids[t]=query_ids

            return ids
        else:
            raise NotImplementedError(f"Cannot use {type(query)} for searching variants")

    def range(self, query, types=None):
        if isinstance(query, GenomicRange):
            return self._query_range(query, types)
        elif isinstance(query, GenomicRangesList):
            to_return={}
            for t in types:
                to_return[t]=[]

            for item in query:
                i=self._query_range(item)
                for key, value in i.items():
                    to_return[key].append(value)

            return to_return

        elif isinstance(query, GenomicRangesDict):
            to_return = {}
            for t in types:
                to_return[t] = []

            for item in query.values():
                i = self._query_range(item)
                for key, value in i.items():
                    to_return[key].append(value)

            return to_return
        else:
            raise NotImplementedError(f"Cannot use {type(query)} for searching variants")

    def annotations(self, query, types=None):
        if types is None:
            query_types = self.types
        ids={}
        for t in query_types:
            table=self._get_tables(t)
            base=self._base_statement(table)
            stms=self.json_search(base, table, "annotations", query)
            ids[t]=self._execute_ids(stms)
        return ids


############ HAVE NOT TOUCHED THIS YET #############
class Search:
    def __init__(self, project, inference):
        self.project = project
        self.inference = inference
        #TODO methods needs to be "partial"ed
        self.variant = VariantSearch()
        self.sequence = SequenceSearch()

    def _pretty_return(self, ids, type):
        pass
