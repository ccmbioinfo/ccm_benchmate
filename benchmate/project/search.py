from sqlalchemy import asc, select, cast
from pgvector.sqlalchemy import Vector

class Search:
    def __init__(self, project, inference):
        """
        Initialize a project-scoped search helper.

        :param project: Project object that owns the reflected knowledge-base
            tables and SQLAlchemy session.
        :type project: Project
        :param inference: Inference helper used to embed natural-language
            queries into the same vector space as stored chunk embeddings.
        :type inference: Inference
        """
        # Search needs both the current project/KB session and an inference object
        # that can embed natural-language queries
        self.project = project
        self.inference = inference
        self.session = project.kb.session

    def search(self, what, search_dict):
        """
        Dispatch a search request to the appropriate search backend.

        :param what: Search target identifier. Currently supports
            `"papers"` and `"literature"`.
        :type what: str
        :param search_dict: Search configuration dictionary. For semantic paper
            search this should contain at least a `query` key and may also
            include `metric`, `limit`, or `top_k`.
        :type search_dict: dict
        :return: Search results for the requested target.
        :rtype: list[dict]
        :raises NotImplementedError: If the requested search target is not supported.
        """
        # Keep the entry point generic so other search targets can be
        # added later. For now, literature search jsut means semantic paper search.
        if what in ["papers", "literature"]:
            return self._paper_semantic_search(search_dict)

        raise NotImplementedError(f"Search for {what} is not implemented")

    def _paper_semantic_search(self, search_dict):
        """
        Run semantic search over stored paper chunks.

        The query is embedded with the configured inference backend, compared
        against `body_text_chunked.chunk_embeddings` using pgvector distance
        operators, and then joined back to `papers` so each hit includes the
        associated paper metadata.

        :param search_dict: Semantic search configuration. Expected keys:
            `query` (required), plus optional `metric`, `limit`, or
            `top_k`.
        :type search_dict: dict
        :return: Chunk-level search hits with paper metadata, raw distance, and
            a derived score.
        :rtype: list[dict]
        :raises ValueError: If an unsupported metric is requested.
        """
        # Required natural-language query plus some optional search
        # controls. top_k is accepted as alt for limit.
        query = search_dict["query"]
        metric = search_dict.get("metric", "cosine")
        limit = search_dict.get("limit", search_dict.get("top_k", 10))

        # Convert the query text into the same vector space used for stored
        # chunks. pgvector accepts plain Python lists, so convert numpy arrays.
        query_vec = self.inference.embed_text([query])[0]
        if hasattr(query_vec, "tolist"):
            query_vec = query_vec.tolist()

        # papers stores paper metadata; body_text_chunked stores the
        # searchable text units and their embeddings.
        papers_table = self.project.kb.db_tables["papers"]
        chunks_table = self.project.kb.db_tables["body_text_chunked"]

        # The KB reflects tables from Postgres, so cast the reflected column back
        # to Vector(1024) to make pgvector distance helpers available reliably.
        embedding_col = cast(chunks_table.c.chunk_embeddings, Vector(1024))

        # Mostly from the CHIRPP semantic-query logic: choose the
        # pgvector distance from the requested metric, then order by
        # the resulting expression. pgvector distance operators sort with the
        # best match first when ordered ascending. For cosine, 
        # score where higher is better.
        if metric == "cosine":
            distance = embedding_col.cosine_distance(query_vec)
            order = asc(distance)
            score_from_distance = lambda value: 1.0 - float(value)
        elif metric in ["L2", "l2"]:
            distance = embedding_col.l2_distance(query_vec)
            order = asc(distance)
            score_from_distance = lambda value: -float(value)
        elif metric in ["L1", "l1"]:
            distance = embedding_col.l1_distance(query_vec)
            order = asc(distance)
            score_from_distance = lambda value: -float(value)
        elif metric == "max_inner_product":
            distance = embedding_col.max_inner_product(query_vec)
            order = asc(distance)
            score_from_distance = lambda value: -float(value)
        else:
            raise ValueError(f"Invalid metric: {metric}")

        distance = distance.label("distance")

        # Search chunks first, then join back to papers so each hit includes
        # paper metadata. The project filter prevents hits from unrelated
        # projects, and the embedding filter skips chunks that have not been
        # embedded yet.
        stmt = (
            select(
                papers_table.c.id.label("paper_id"),
                papers_table.c.source,
                papers_table.c.source_id,
                papers_table.c.title,
                papers_table.c.abstract,
                papers_table.c.pdf_url,
                papers_table.c.pdf_path,
                chunks_table.c.chunk_id,
                chunks_table.c.chunk_text,
                distance,
            )
            .select_from(
                chunks_table.join(
                    papers_table,
                    chunks_table.c.paper_id == papers_table.c.id,
                )
            )
            .where(papers_table.c.project_id == self.project.project_id)
            .where(chunks_table.c.chunk_embeddings.isnot(None))
            .order_by(order)
            .limit(limit)
        )

        rows = self.session.execute(stmt).fetchall()

        # Return plain dictionaries.
        return [
            {
                "paper_id": row.paper_id,
                "source": row.source,
                "source_id": row.source_id,
                "title": row.title,
                "abstract": row.abstract,
                "open_access": row.pdf_url is not None,
                "downloaded": row.pdf_path is not None,
                "chunk_id": row.chunk_id,
                "chunk_text": row.chunk_text,
                "distance": float(row.distance),
                "score": score_from_distance(row.distance),
            }
            for row in rows
        ]