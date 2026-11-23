import os
import io
from functools import partial
from PIL import Image
import warnings
import json

from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import NoResultFound

from benchmate.utils.general_utils import DataIntegrityError

from benchmate.literature.literature import LitSearch as BaseLitSearch
from benchmate.literature.literature import OpenAlex
from benchmate.literature.literature import Paper as BasePaper


class Paper(BasePaper):
    """
    Paper with project-database methods.

    Transaction model
    - to_kb / update_kb open (or reuse) ONE session and commit once at the very end. Any exception
      rolls back everything: the paper row, figures, tables, chunks, relationship rows and any
      related papers inserted along the way.
    - Pass `session=` to to_kb / update_kb to join a caller-owned transaction; in that case this code
      never commits or rolls back, the caller does.
    - Ids: to_kb returns, and from_kb / update_kb take, the DB primary key (papers.id), not the OpenAlex id.
    """
    _RELATIONSHIPS = (
        ("references", "references"),
        ("related_works", "related_works"),
        ("cited_by", "cited_by"),
    )

    def __init__(self, paper_id):
        super().__init__(paper_id)

    # ------------------------------------------------------------------ helpers
    def _paper_values(self):
        """mutable columns of the papers table (shared by insert and update)"""
        info = self.info
        return dict(
            external_ids=info.external_ids,
            title=info.title,
            abstract=info.abstract,
            abstract_embeddings=_as_list(info.abstract_embeddings),
            download_links=info.download_links,
            file_paths=info.file_paths,
            full_json=info.full_json,
            authors=info.authors,
            publication_date=info.publication_date,
            venue=info.venue,
            full_text=getattr(info, "text", None) or "",
        )

    def _find_pk(self, session, project, ids):
        """

        :param session:
        :param project:
        :param ids:
        :return:
        """
        openalex_id = self.info.id
        if openalex_id in ids:
            return ids[openalex_id]
        papers = project.kb.db_tables["papers"]
        rows = session.execute(
            select(papers.c.id).where(papers.c.paper_id == openalex_id,
                                      papers.c.project_id == project.project_id)
        ).scalars().all()
        if len(rows) > 1:
            raise DataIntegrityError(f"Found more than one paper with id:{openalex_id}")
        if rows:
            ids[openalex_id] = rows[0]
            return rows[0]
        return None

    def _ensure(self, session, project, ids):
        """

        :param session:
        :param project:
        :param ids:
        :return:
        """
        pk = self._find_pk(session, project, ids)
        if pk is not None:
            return pk
        return self._insert(session, project, ids)

    def _insert(self, session, project, ids):
        """

        :param session:
        :param project:
        :param ids:
        :return:
        """
        papers = project.kb.db_tables["papers"]
        pk = session.execute(
            insert(papers)
            .values(project_id=project.project_id, paper_id=self.info.id, **self._paper_values())
            .returning(papers.c.id)
        ).scalar_one()
        # register BEFORE recursing so citation cycles (A cites B cites A) terminate
        ids[self.info.id] = pk
        self._write_children(session, project, pk, replace=False)
        self._write_relationships(session, project, pk, ids, replace=False)
        return pk

    def _write_children(self, session, project, pk, replace):
        """
        figures / tables / text chunks. replace is useful during update_kb
        None  -> untouched (nothing loaded)
        []    -> with replace=True, clears the rows
        list  -> with replace=True, replaces the rows
        """
        tbl = project.kb.db_tables
        info = self.info

        if info.figures is not None:
            figures = tbl["figures"]
            if replace:
                session.execute(delete(figures).where(figures.c.paper_id == pk))
            embeddings = getattr(info, "figure_embeddings", None)
            rows = [dict(paper_id=pk,
                         image_blob=_to_jpeg_bytes(fig["image"]),
                         figure_caption=fig["text"],
                         figure_embeddings=_embedding_at(embeddings, i))
                    for i, fig in enumerate(info.figures)]
            if rows:
                session.execute(insert(figures), rows)

        if info.tables is not None:
            tables = tbl["tables"]
            if replace:
                session.execute(delete(tables).where(tables.c.paper_id == pk))
            embeddings = getattr(info, "table_embeddings", None)
            rows = [dict(paper_id=pk,
                         image_blob=_to_jpeg_bytes(tab["image"]),
                         table_content=tab["text"],
                         table_embeddings=_embedding_at(embeddings, i))
                    for i, tab in enumerate(info.tables)]
            if rows:
                session.execute(insert(tables), rows)

        if info.text_chunks is not None:
            chunks = tbl["body_text_chunked"]
            if replace:
                session.execute(delete(chunks).where(chunks.c.paper_id == pk))
            embeddings = getattr(info, "chunk_embeddings", None)
            rows = []
            for i, chunk in enumerate(info.text_chunks):
                is_pair = isinstance(chunk, (tuple, list))
                rows.append(dict(paper_id=pk,
                                 chunk_id=chunk[0] if is_pair else i,
                                 chunk_text=chunk[1] if is_pair else chunk,
                                 chunk_embeddings=_embedding_at(embeddings, i)))
            if rows:
                session.execute(insert(chunks), rows)

    def _write_relationships(self, session, project, pk, ids, replace):
        """references / related_works / cited_by (same None vs [] semantics as _write_children)"""
        tbl = project.kb.db_tables
        for attr, table_name in self._RELATIONSHIPS:
            related = getattr(self.info, attr, None)
            if related is None:
                continue
            table = tbl[table_name]
            if replace:
                session.execute(delete(table).where(table.c.source_id == pk))
            seen, rows = set(), []
            for rel in related:
                # call unbound so plain BasePaper instances in the lists work too (only .info is used)
                rel_pk = Paper._ensure(rel, session, project, ids)
                if rel_pk in seen:
                    continue
                seen.add(rel_pk)
                rows.append(dict(source_id=pk, target_id=rel_pk))
            if rows:
                session.execute(insert(table), rows)

    @staticmethod
    def _get_session(project):
        """works whether project.kb.session is a Session, a scoped_session or a sessionmaker"""
        session = project.kb.session
        return session() if callable(session) else session

    @staticmethod
    def _as_list(value):
        """numpy arrays / pgvector values -> plain lists; None stays None"""
        if value is None:
            return None
        return value.tolist() if hasattr(value, "tolist") else value

    @staticmethod
    def _embedding_at(embeddings, i):
        if embeddings is None or len(embeddings) <= i:
            return None
        return _as_list(embeddings[i])

    @staticmethod
    def _to_jpeg_bytes(src):
        """
        Accepts a path, file-like object, PIL image, or raw bytes (what from_kb returns).
        Bytes that are already JPEG are passed through untouched so repeated update_kb calls
        don't re-encode (and degrade) the image every time.
        """
        if isinstance(src, memoryview):
            src = src.tobytes()
        if isinstance(src, (bytes, bytearray)):
            if bytes(src[:2]) == b"\xff\xd8":
                return bytes(src)
            src = io.BytesIO(src)
        if isinstance(src, Image.Image):
            img = src
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG")  # RGBA / P modes can't be saved as JPEG directly
            return buf.getvalue()
        with Image.open(src) as img:
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG")
        return buf.getvalue()

    def to_kb(self, project, session=None):
        """
        insert this paper, its figures/tables/chunks and its relationships in ONE transaction.
        If the paper already exists in the project, warn and return the existing pk (no update;
        use update_kb for that).
        :param project: project class instance
        :param session: optional caller-owned session; if given, nothing is committed here
        :return: primary key of the paper
        """
        owns_transaction = session is None
        if owns_transaction:
            session = self._get_session(project)
        ids = {}
        try:
            existing = self._find_pk(session, project, ids)
            if existing is not None:
                warnings.warn(f"Paper with openalex id {self.info.id} already exists within the project")
                return existing
            pk = self._insert(session, project, ids)
            if owns_transaction:
                session.commit()
            return pk
        except Exception:
            if owns_transaction:
                session.rollback()
            raise

    def update_kb(self, project, id, session=None):
        """
        update an existing paper in ONE transaction.
        - papers row: all mutable columns overwritten from `instance`
        - figures / tables / chunks / references / related_works / cited_by:
            instance attribute None  -> left as is
            instance attribute []    -> existing rows deleted
            instance attribute list  -> existing rows replaced by the list
          (related papers not yet in the project are inserted; related papers are never deleted)
        :param project: project class instance
        :param id: primary key (papers.id) of the paper to update
        :param session: optional caller-owned session; if given, nothing is committed here
        :return: id
        """
        owns_transaction = session is None
        if owns_transaction:
            session = self._get_session(project)
        papers = project.kb.db_tables["papers"]
        scope = (papers.c.id == id, papers.c.project_id == project.project_id)
        try:
            current_openalex_id = session.execute(select(papers.c.paper_id).where(*scope)).scalar_one_or_none()
            if current_openalex_id is None:
                raise NoResultFound(f"Could not find a paper with id:{id}")
            if current_openalex_id != self.info.id:
                raise ValueError(f"Paper {id} is {current_openalex_id}, instance is {self.info.id}; "
                                 f"refusing to overwrite a different paper")

            session.execute(update(papers).where(*scope).values(**self._paper_values()))
            ids = {self.info.id: id}
            self._write_children(session, project, id, replace=True)
            self._write_relationships(session, project, id, ids, replace=True)

            if owns_transaction:
                session.commit()
            return id
        except Exception:
            if owns_transaction:
                session.rollback()
            raise

    @classmethod
    def from_kb(cls, project, id, _cache=None):
        """
        load a paper (and, recursively, its references / related works / cited by) from the project database
        :param project: project class instance
        :param id: primary key (papers.id) of the paper
        :return: a Paper instance
        """
        _cache = {} if _cache is None else _cache
        if id in _cache:  # citation graphs are cyclic (A.references has B, B.cited_by has A)
            return _cache[id]

        tbl = project.kb.db_tables
        session = _get_session(project)
        papers = tbl["papers"]

        rows = session.execute(
            select(papers).where(papers.c.id == id, papers.c.project_id == project.project_id)
        ).mappings().all()
        if len(rows) == 0:
            raise NoResultFound("Could not find a paper with id:{}".format(id))
        if len(rows) > 1:
            raise DataIntegrityError("There are multiple papers with the id {}".format(id))
        row = rows[0]

        paper = cls(paper_id=row["paper_id"])
        paper.info.external_ids = row["external_ids"]
        paper.info.title = row["title"]
        paper.info.abstract = row["abstract"]
        paper.info.abstract_embeddings = row["abstract_embeddings"]
        paper.info.download_links = row["download_links"]
        paper.info.file_paths = row["file_paths"]
        paper.info.full_json = row["full_json"]
        paper.info.authors = row["authors"]
        paper.info.publication_date = row["publication_date"]
        paper.info.venue = row["venue"]
        paper.info.text = row["full_text"]
        _cache[id] = paper  # register before recursing

        figures = tbl["figures"]
        figs = session.execute(
            select(figures.c.image_blob, figures.c.figure_caption, figures.c.figure_embeddings)
            .where(figures.c.paper_id == id)
        ).all()
        if figs:
            paper.info.figures = [{"image": bytes(f[0]), "text": f[1]} for f in figs]
            paper.info.figure_embeddings = [f[2] for f in figs]
        else:
            paper.info.figures = None

        tables = tbl["tables"]
        tabs = session.execute(
            select(tables.c.image_blob, tables.c.table_content, tables.c.table_embeddings)
            .where(tables.c.paper_id == id)
        ).all()
        if tabs:
            paper.info.tables = [{"image": bytes(t[0]), "text": t[1]} for t in tabs]
            paper.info.table_embeddings = [t[2] for t in tabs]
        else:
            paper.info.tables = None

        chunked = tbl["body_text_chunked"]
        chunks = session.execute(
            select(chunked.c.chunk_text, chunked.c.chunk_embeddings)
            .where(chunked.c.paper_id == id)
            .order_by(chunked.c.chunk_id)
        ).all()
        if chunks:
            paper.info.text_chunks = [c[0] for c in chunks]
            paper.info.chunk_embeddings = [c[1] for c in chunks]
        else:
            paper.info.text_chunks = None

        for attr, table_name in _RELATIONSHIPS:
            rel_table = tbl[table_name]
            target_ids = session.execute(
                select(rel_table.c.target_id).where(rel_table.c.source_id == id)
            ).scalars().all()
            setattr(paper.info, attr, [cls.from_kb(project, t, _cache) for t in target_ids] or None)

        return paper

class PaperFactory:
    def __init__(self, project):
        self.project = project

    def __call__(self, paper_id,  get_info=True, download=True, get_references=True,
                 get_related_works=True, get_cited_by=True):
        paper=Paper(paper_id)
        if get_info:
            paper.get_json(self.project.openalex)
            paper.parse_json()
            if download:
                paper.download(self.project.config["literature"]["pdf_path"])
            if get_references:
                paper.get_references(self.project.openalex)
            if get_related_works:
                paper.get_related_works(self.project.openalex)
            if get_cited_by:
                paper.get_cited_by(self.project.openalex)

        return paper

    def from_kb(self, id):
        return Paper.from_kb(self.project, id)

class LitSearch(BaseLitSearch):
    def __init__(self, pdf_path, openalex_api_key):
        super().__init__()
        self.openalex=OpenAlex(openalex_api_key)
        os.makedirs(pdf_path, exist_ok=True)
        self.search=partial(self.search,openalex=self.openalex)