import os
import io
from functools import partial
from PIL import Image
import warnings
import json

from sqlalchemy import select, insert
from sqlalchemy.exc import NoResultFound

from benchmate.utils.general_utils import DataIntegrityError

from benchmate.literature.literature import LitSearch as BaseLitSearch
from benchmate.literature.literature import OpenAlex
from benchmate.literature.literature import Paper as BasePaper

#TODO need to fix the to_from kb methods to reflect the new paddle structure
class Paper(BasePaper):
    def __init__(self, paper_id):
        super().__init__(paper_id)

    def to_kb(self, project):
        papers_table = project.kb.db_tables["papers"]
        figures_table = project.kb.db_tables["figures"]
        tables_table = project.kb.db_tables["tables"]
        chunked_text_table = project.kb.db_tables["body_text_chunked"]
        references_table = project.kb.db_tables["references"]
        related_works_table = project.kb.db_tables["related_works"]
        cited_by_table = project.kb.db_tables["cited_by"]

        # check if paper exists
        check_stmt = select(papers_table.c.id).where(papers_table.c.paper_id == self.info.id)
        existing = project.kb.session().execute(check_stmt).scalars().fetchall()
        if len(existing) > 1:
            raise DataIntegrityError(f"Found more than one paper with id:{self.info.id}")

        if len(existing) == 1:
            warnings.warn(f"Paper with openalex id {self.info.id} already exists within the project")
            return existing[0]

        stmt = insert(papers_table).values(
            project_id=project.project_id,
            paper_id=self.info.id,
            external_ids=self.info.external_ids,
            title=self.info.title,
            abstract=self.info.abstract,
            abstract_embeddings=self.info.abstract_embeddings,
            download_links=self.info.download_links,
            file_paths=self.info.file_paths,
            full_json=self.info.full_json,
            authors=self.info.authors,
            publication_date=self.info.publication_date,
            venue=self.info.venue,
            full_text=getattr(self.info, 'text', None) or "",
        ).returning(papers_table.c.id)

        paper_id = project.kb.session().execute(stmt).scalars().one()

        if self.info.figures is not None:
            for i in range(len(self.info.figures)):
                img = Image.open(self.info.figures[i]["image"])
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="JPEG")
                img_bytes = img_byte_arr.getvalue()
                figure_stms = insert(figures_table).values(
                    paper_id=paper_id,
                    image_blob=img_bytes,
                    figure_caption=self.info.figures[i]["text"],
                    figure_embeddings=self.info.figure_embeddings[i] if self.info.figure_embeddings else None,
                )
                project.kb.session().execute(figure_stms)

        if self.info.tables is not None:
            for i in range(len(self.info.tables)):
                img = Image.open(self.info.tables[i]["image"])
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="JPEG")
                img_bytes = img_byte_arr.getvalue()
                table_smts = insert(tables_table).values(
                    paper_id=paper_id,
                    image_blob=img_bytes,
                    table_content=self.info.tables[i]["text"],
                    table_embeddings=self.info.table_embeddings[i] if self.info.table_embeddings else None,
                )
                project.kb.session().execute(table_smts)

        # check if text_chunks exist
        if self.info.text_chunks is not None:
            for i in range(len(self.info.text_chunks)):
                chunk_stms = insert(chunked_text_table).values(
                    paper_id=paper_id,
                    chunk_id=self.info.text_chunks[i][0] if isinstance(self.info.text_chunks[i], (tuple, list)) else i,
                    chunk_text=self.info.text_chunks[i][1] if isinstance(self.info.text_chunks[i], (tuple, list)) else self.info.text_chunks[i],
                    chunk_embeddings=self.info.chunk_embeddings[i].tolist() if self.info.chunk_embeddings is not None else None,
                )
                project.kb.session().execute(chunk_stms)

        if self.info.references is not None:
            for paper in self.info.references:
                existing = select(papers_table.c.id).where(papers_table.c.paper_id == paper.id)
                ref_id = project.kb.session().execute(existing).scalar()
                if ref_id is None:
                    ref_id = paper.to_kb(project)
                stms = insert(references_table).values(source_id=paper_id, target_id=ref_id)
                project.kb.session().execute(stms)

        if self.info.related_works is not None:
            for paper in self.info.related_works:
                existing = select(papers_table.c.id).where(papers_table.c.paper_id == paper.id)
                related_id = project.kb.session().execute(existing).scalar()
                if related_id is None:
                    related_id = paper.to_kb(project)
                stms = insert(related_works_table).values(source_id=paper_id, target_id=related_id)
                project.kb.session().execute(stms)

        if self.info.cited_by is not None:
            for paper in self.info.cited_by:
                existing = select(papers_table.c.id).where(papers_table.c.paper_id == paper.id)
                cited_id = project.kb.session().execute(existing).scalar()
                if cited_id is None:
                    cited_id = paper.to_kb(project)
                stms = insert(cited_by_table).values(source_id=paper_id, target_id=cited_id)
                project.kb.session().execute(stms)

        project.kb.session().commit()
        return paper_id

    @classmethod
    def from_kb(cls, project, id):
        papers_table = project.kb.db_tables["papers"]
        figures_table = project.kb.db_tables["figures"]
        tables_table = project.kb.db_tables["tables"]
        chunked_text_table = project.kb.db_tables["body_text_chunked"]
        references_table = project.kb.db_tables["references"]
        related_works_table = project.kb.db_tables["related_works"]
        cited_by_table = project.kb.db_tables["cited_by"]

        selection = select(papers_table.c.paper_id,
                           papers_table.c.external_ids,
                           papers_table.c.title,
                           papers_table.c.abstract,
                           papers_table.c.abstract_embeddings,
                           papers_table.c.download_links,
                           papers_table.c.file_paths,
                           papers_table.c.full_json,
                           papers_table.c.authors,
                           papers_table.c.publication_date,
                           papers_table.c.venue,
                           papers_table.c.full_text).where(papers_table.c.paper_id == id)

        paper_info = project.kb.session().execute(selection).fetchall()

        if len(paper_info) > 1:
            raise DataIntegrityError("There are multiple papers with the id {}".format(id))
        elif len(paper_info) == 0:
            raise NoResultFound("Could not find a paper with id:{}".format(id))
        else:
            paper = cls(paper_id=paper_info[0][0])
            paper.info.external_ids = paper_info[0][1]
            paper.info.title = paper_info[0][2]
            paper.info.abstract = paper_info[0][3]
            paper.info.abstract_embeddings = paper_info[0][4]
            paper.info.download_links = paper_info[0][5]
            paper.info.file_paths = paper_info[0][6]
            paper.info.full_json = paper_info[0][7]
            paper.info.authors = paper_info[0][8]
            paper.info.publication_date = paper_info[0][9]
            paper.info.venue = paper_info[0][10]
            paper.info.text = paper_info[0][11]

        figures = select(figures_table.c.image_blob,
                         figures_table.c.figure_caption,
                         figures_table.c.figure_embeddings).where(figures_table.c.paper_id == id)

        figures = project.kb.session().execute(figures).fetchall()

        if len(figures) == 0:
            paper.info.figures = None
        else:
            paper.info.figures=[{"image":f[0], "text":f[1]} for f in figures]
            paper.info.figure_embeddings=[f[2] for f in figures]

        tables = select(tables_table.c.image_blob,
                        tables_table.c.table_content,
                        tables_table.c.table_embeddings).where(tables_table.c.paper_id == id)

        tables = project.kb.session().execute(tables).fetchall()
        if len(tables) == 0:
            paper.info.tables = None
        else:
            paper.info.tables=[{"image":f[0], "text":f[1]} for f in tables]
            paper.info.table_embeddings=[f[2] for f in tables]

        chunks = select(chunked_text_table.c.chunk_text,
                        chunked_text_table.c.chunk_embeddings).where(chunked_text_table.c.paper_id == id)
        chunks = project.kb.session().execute(chunks).fetchall()

        if len(chunks) == 0:
            paper.info.text_chunks = None
        else:
            paper.info.text_chunks = [chunk[0] for chunk in chunks]
            paper.info.chunk_embeddings = [chunk[1] for chunk in chunks]

        references = select(references_table.c.target_id).where(references_table.c.source_id == id)
        references = project.kb.session().execute(references).fetchall()
        if len(references) == 0:
            paper.info.references = None
        else:
            refs = []
            for ref in references:
                ref_paper = cls.from_kb(project, ref[0])
                refs.append(ref_paper)
            paper.info.references = refs

        cited_by = select(cited_by_table.c.target_id).where(cited_by_table.c.source_id == id)
        cited_by = project.kb.session().execute(cited_by).fetchall()
        if len(cited_by) == 0:
            paper.info.cited_by = None
        else:
            refs = []
            for ref in cited_by:
                ref_paper = cls.from_kb(project, ref[0])
                refs.append(ref_paper)
            paper.info.cited_by = refs

        related_works = select(related_works_table.c.target_id).where(related_works_table.c.source_id == id)
        related_works = project.kb.session().execute(related_works).fetchall()
        if len(related_works) == 0:
            paper.info.related_works = None
        else:
            refs = []
            for ref in related_works:
                ref_paper = cls.from_kb(project, ref[0])
                refs.append(ref_paper)
            paper.info.related_works = refs

        return paper

class LitSearch(BaseLitSearch):
    def __init__(self, config):
        self.config=config
        super().__init__()
        self.openalex=OpenAlex(self.config["openalex_api_key"])
        os.makedirs(self.config["pdf_path"], exist_ok=True)
        self.search=partial(self.search,openalex=self.openalex)