from dataclasses import dataclass
from typing import Optional, Union

import pandas as pd
from PIL import Image
from sqlalchemy import cast, String, func, and_, desc

type_dict={
    "api_call":{
        "table":"api_call",
        "columns":["id", "class_name", "method_name", "query_time"]
    },
    "paper":{
        "table":"papers",
        "columns":["id", "title", "venue", "publication_date"]
    },
    "genome":{
        "table":"genome",
        "columns":["id", "name", "description",]
    },
    "sequence":{
        "table":"sequence",
        "columns":["id", "name", "sequence", "type", "hash"]
    },
    "structure":{
        "table":"structure",
        "columns":["id", "name", "hash"]
    },
    "molecule":{
        "table":"molecule",
        "columns":["id", "name", "smiles"]
    },
    "sequencevariant":{
        "table":"sequencevariant",
        "columns":["id", "chrom", "pos", "ref", "alt"]
    },
    "structurevariant":{
        "table":"structurevariant",
        "columns":["id", "chrom", "pos", "ref", "alt"]
    },
    "tandemrepeatvariant":{
        "table":"tandemrepeatvariant",
        "columns":["id", "chrom", "pos", "ref", "alt"]
    }
}

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

    def _execute_search(self, stmt):
        results=self.session.execute(stmt).fetchall()
        return pd.DataFrame(results)

    def json_search(self, statement, table, column_name, filters):
        """
        :param statement: This is a select statement, it can be as simple as a full table or a single column
        :param column_name: which column is the jsonb column
        :param filters: filters  str | dict | list[str | dict]
        :return: filters added to the query this is not the result it's just a sqlalchemy query
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

    def keyword_search(self, statement, positive_keywords, negative_keywords,  table, column, normalization=32):
        """
        perform keyword search using postgres tsvector, this only applies to columns that has tsvector built in with indexes
        :param statement: This is a select statement, it can be as simple as a full table or a single column
        :param positive_keywords: things to look for
        :param negative_keywords: things to avoid
        :param table: which table to use
        :param column: which column from that table to use
        :param normalization: what kind of normalization to o use see details here: https://www.postgresql.org/docs/current/textsearch-controls.html#TEXTSEARCH-RANKING
        :return: another statement added where tsvector filters are added.
        """
        column_name = column if isinstance(column, str) else column.name
        resolved_column = table.c[column_name]

        pos_query = " & ".join(positive_keywords) if positive_keywords else ""
        neg_query = " & ".join([f"!{k}" for k in negative_keywords]) if negative_keywords else ""

        if pos_query and neg_query:
            query_str = f"({pos_query}) & ({neg_query})"
        elif pos_query:
            query_str = pos_query
        elif neg_query:
            query_str = neg_query
        else:
            return statement

        ts_query = func.to_tsquery('english', query_str)
        rank = func.ts_rank(resolved_column, ts_query, normalization)

        # Override select to include rank for tracking or ordering if required
        stmt = statement.where(resolved_column.op('@@')(ts_query)).order_by(desc(rank))
        return stmt

    def semantic_search(self, statement, query, table, column, metric="cosine", top_n=500):
        """
        perform semantic search using a pgvector column, the
        :param statement: base statementn from the class
        :param query: a list of embeddings, this is not what you are looking for but the embeddings of the thing you are looking for
        :param table: which table to search
        :param column: which column to search
        :param top_n: top n results to return, defaults to 500
        :return: selection logic added to the base statement.
        """
        column_name = column if isinstance(column, str) else column.name
        resolved_column = table.c[column_name]
        if metric=="cosine":
            distance_score = resolved_column.cosine_distance(query)
        elif metric=="L2":
            distance_score = resolved_column.l2_distance(query)
        elif metric=="L1":
            distance_score = resolved_column.l1_distance(query)
        else:
            raise NotImplementedError("Metric not implemented, it can only be cosine, L1 or L2")
        stmt = statement.add_columns(distance_score.label('distance'))
        stmt = stmt.order_by(distance_score.asc()).limit(top_n)
        return stmt

