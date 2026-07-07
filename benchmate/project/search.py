import os
import importlib
import tempfile

from sqlalchemy import select

from benchmate.molecule.molecule import Molecule
from benchmate.ranges.genomicranges import GenomicRange, GenomicRangesList, GenomicRangesDict
from benchmate.variant.variant import SequenceVariant, TandemRepeatVariant, StructuralVariant
from benchmate.apis.utils import api_mapper
from benchmate.project.utils import *

@dataclass
class KeywordSearch:
    positive: str | list[str]
    negative: str | list[str] | None = None
    normalization: int = 32

    def __post_init__(self):
        if isinstance(self.positive, str):
            self.positive = self.positive.split()

        if isinstance(self.negative, str):
            self.negative = self.negative.split()

@dataclass
class SemanticSearch:
    query: Union[str, Image.Image]
    metric: str = "cosine"
    top_n: int = 500

    @property
    def query_dict(self):
        if isinstance(self.query, str):
            return {
                "type": "text",
                "text": self.query,
            }

        if isinstance(self.query, Image.Image):
            return {
                "type": "image",
                "image": self.query,
            }

        raise TypeError


class PaperSearch(BaseSearch):
    table_names =["papers", "figures", "tables", "body_text_chunked"]
    attributes = ["abstract", "full_text", "figure", "table"]

    @property
    def _base_statement(self):
        papers_table=self.tables["papers"]
        stms = select(papers_table.c.id, papers_table.c.title, papers_table.c.external_ids,
                     papers_table.c.venue, papers_table.c.publication_date)

        return stms

    def _table_column(self, attribute, type="keyword"):
        if attribute=="abstract":
            table=self.tables["papers"]
            if type=="keyword":
                column=table.c["abstract_ts_vector"]
            else:
                column=table.c["abstract_embeddings"]
        elif attribute=="full_text" and type=="keyword":
            table=self.tables["papers"]
            column=table.c["full_text_ts_vector"]
        elif attribute == "full_text" and type == "semantic":
            table=self.tables["body_text_chunked"]
            column=table.c["chunk_embeddings"]
        elif attribute == "figure":
            table=self.tables["figures"]
            if type=="keyword":
                column=table.c["figure_caption_ts_Vector"]
            else:
                column=table.c["figure_embeddings"]
        elif attribute == "table":
            table=self.tables["tables"]
            if type=="keyword":
                column=table.c["table_content_ts_vector"]
            else:
                column=table.c["table_embeddings"]

        return table, column

    #this will need the same structure as the chirpp search and will need a similar class method
    def body(self, query, inference, attribute):
        if attribute not in self.attributes:
            raise ValueError(f"Attribute {attribute} is not available, you can use {','.join(self.attributes)}")

        if isinstance(query, KeywordSearch):
            table, column = self._table_column(attribute, "keyword")
            stmt=self.keyword_search(self._base_statement,
                                query.positive,
                                query.negative,
                                table, column, query.normalization
                                )

        elif isinstance(query, SemanticSearch):
            table, column = self._table_column(attribute, "semantic")
            embeddings=inference.embed(query.query_dict)
            stmt=self.semantic_search(self._base_statement,
                                 embeddings,table, column, query.metric,
                                 query.top_n)

        results=self._execute_search(stmt)
        return results

    def metadata(self, query):
        #this is json_search
        column = "full_json"
        stms = self.json_search(self._base_statement(), self.table, column, query)
        ids = self._execute_search(stms)
        return ids

    def annotations(self, query):
        column="annotations"
        stms=self.json_search(self._base_statement(), self.table, column, query)
        ids=self._execute_search(stms)
        return ids

class StructureSearch(BaseSearch):
    """
    Search for structures either from their annotations or using another structure
    """
    table_name="structure"

    def _base_statement(self):
        stms = select(self.table.c.id, self.table.c.name, self.table.c.smiles).filter(self.table.c.project_id==self.project.id)
        return stms

    def structure(self, query, chain="A", method="foldseek", database=None, **kwargs):
        if method=="foldseek":
            with tempfile.NamedTemporaryFile(suffix=".pdb") as tmp:
                path=self.project.config["structure"]["pdb_path"]
                if len(os.listdir(path))>0:
                    query.write(tmp.name)
                    tmp.flush()
                    results=self.project.alignment.foldseek.easy_search(tmp.name, path)
                else:
                    FileNotFoundError("There are no pdb files in this project")
        #this needs a check for the database
        if method=="folddisco":
            path=self.project.config["alignment"]["folddisco_db_root"]
            if len(os.listdir(path))>0:
                if database:
                    if len(self.project.alignment.folddisco.local_databases)>0:
                        raise ValueError("You need to specify a local database, there is more than one")
                    elif len(self.project.alignment.folddisco.local_databases)==0:
                        raise ValueError("There are no local databases")
                    else:
                        with tempfile.NamedTemporaryFile(suffix=".pdb") as tmp:
                            query.write(tmp.name)
                            tmp.flush()
                            self.project.alignment.folddisco.search(tmp, database)
                else:
                    raise ValueError("If you want to run folddisco you must specify a database")
            else:
                raise FileNotFoundError("There are no pdb files in this project")

        return results


    def annotations(self, query):
        column="annotations"
        stms=self.json_search(self._base_statement(), self.table, column, query)
        ids=self._execute_search(stms)
        return ids

class SequenceSearch(BaseSearch):
    table_name="sequence"

    def _base_statement(self):
        stms = select(self.table.c.id, self.table.c.name, self.table.c.sequence, self.table.c.type).filter(self.table.c.project_id==self.project.id)
        return stms

    def sequence(self, query):
        """
        search for sequences using another sequence
        :param project: project instance
        :return: a dataframe of hits, the hit column gives you the ids of hits, other columns come from mmseqs
        """
        if query.info.seq_type=="3di":
            fasta=os.path.join(self.project.config["sequence"]["fasta_root"], "tdi.fa")
            with tempfile.NamedTemporaryFile(suffix=".fasta") as tmp:
                query.to_fasta(tmp.name)
                tmp.flush()
                results=self.project.alignment.foldseek.easy_search(tmp.name, fasta)
        else:
            if query.info.seq_type=="protein":
                fasta=os.path.join(self.project.config["sequence"]["fasta_root"], "protein.fa")
            elif query.info.seq_type=="dna":
                fasta = os.path.join(self.project.config["sequence"]["fasta_root"], "dna.fa")
            elif query.info.seq_type=="rna":
                fasta = os.path.join(self.project.config["sequence"]["fasta_root"], "rna.fa")
            else:
                raise NotImplementedError("only dna, rna, protein and 3di are supported")
            with tempfile.NamedTemporaryFile(suffix=".fasta") as tmp:
                query.to_fasta(tmp.name)
                tmp.flush()
                results=self.project.alignment.mmseqs.easy_search(tmp.name, fasta)

        results=results.rename(columns={"target":"hit"})
        return results

    def annotations(self, query):
        column="annotations"
        stms=self.json_search(self._base_statement(), self.table, column, query)
        ids=self._execute_search(stms)
        return ids

class MoleculeSearch(BaseSearch):

    table_name="molecule"

    def _base_statement(self):
        stms=select(self.table.c.id, self.table.c.name, self.table.c.smiles).filter(self.table.c.project_id==self.project.id)
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
            ids = self._execute_search(stms)
        else:
            raise NotImplementedError(f"You can only use Molecule class instances in this method")
        return ids

    def annotations(self, query):
        column="annotations"
        stms=self.json_search(self._base_statement(), self.table, column, query)
        ids=self._execute_search(stms)
        return ids

class VariantSearch(BaseSearch):

    types=["sequencevariant", "structuralvariant", "tandemrepeatvariant"]

    def _base_statement(self, table):
       stms=select(table.c.id, table.c.chrom, table.c.pos, table.c.ref, table.c.alt).filter(self.table.c.project_id==self.project.id)
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
            ids=self._execute_search(stms)
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
                query_ids=self._execute_search(stms)
                ids[t]=query_ids

            return ids
        else:
            raise NotImplementedError(f"Cannot use {type(query)} for searching variants")

    def range(self, query, types=None):
        """
        find variants that fall into a range, this assumes that the genomem you are using in your ranges are the same
        as the variant annotations, there are no checks and not sure if there can ever be w/o significant overhead
        :param query: a genomicrange instance
        :param type: type of variant to search for
        :return: basic information and their ids for matches
        """
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
            ids[t]=self._execute_search(stms)
        return ids

class ApiCallSearch(BaseSearch):
    table_name="api_call"

    def __init__(self, project):
        super().__init__(project)

    def _base_statement(self, call_class, class_method):

        stms = select(self.table.c.id, self.table.c.class_name, self.table.c.method_name).filter(self.table.c.project_id==self.project.id)
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

    def calls(self, call_class, class_method, params=None):
        """
        search for api calls based on the kind of api call and method used
        :param call_class: class of the call
        :param class_method: which method was used to call
        :param params: parameters for the api call, this allows you to search for specific calls
        :return: ids, and basic info about the calls
        """
        column="params"
        stms=self._base_statement(call_class, class_method)
        if params:
            stms = self.json_search(stms, self.table, column, params)
        rows = self._execute_search(stms)
        return rows

    #there query is mandatory since you are looking for something specific
    def results(self, query, call_class, class_method):
        stms=self._base_statement(call_class, class_method)
        stms=self.json_search(stms, self.table,"results", query)
        rows = self._execute_search(stms)
        return rows

class ProjectSearch:
    def __init__(self, project):
        self.engines = {
            "paper": PaperSearch(project),
            "structure": StructureSearch(project),
            "sequence": SequenceSearch(project),
            "molecule": MoleculeSearch(project),
            "variant": VariantSearch(project),
            "apicall": ApiCallSearch(project),
        }

        self.registry = {
            ("paper", "annotations"): self.engines["paper"].annotations,
            ("paper", "metadata"): self.engines["paper"].metadata,
            ("paper", "body"): self.engines["paper"].body,

            ("structure", "annotations"): self.engines["structure"].annotations,
            ("structure", "structure"): self.engines["structure"].structure,

            ("sequence", "annotations"): self.engines["sequence"].annotations,
            ("sequence", "sequence"): self.engines["sequence"].sequence,

            ("molecule", "annotations"): self.engines["molecule"].annotations,
            ("molecule", "molecule"): self.engines["molecule"].molecule,

            ("variant", "annotations"): self.engines["variant"].annotations,
            ("variant", "variant"): self.engines["variant"].variant,
            ("variant", "range"): self.engines["variant"].range,

            ("apicall", "calls"): self.engines["apicall"].calls,
            ("apicall", "results"): self.engines["apicall"].results,
        }

    def search(self, modality, method, query=None, **kwargs):
        try:
            handler = self.registry[(modality, method)]
        except KeyError:
            raise ValueError(
                f"Unsupported search: entity={modality}, method={method}"
            )

        if query is None:
            return handler(**kwargs)
        return handler(query, **kwargs)
