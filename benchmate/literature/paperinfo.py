from dataclasses import dataclass
from typing import Optional
import io
import json

import numpy as np
from sqlalchemy import select, insert
from PIL import Image
from sqlalchemy.exc import NoResultFound

from benchmate.utils.general_utils import DataIntegrityError

@dataclass
class PaperInfo:
    """
    Dataclass to hold information about a paper, this is constructed inside the Paper class and desined to be compatible with
    semantic search and embedding distance searches
    """
    id: str
    id_type: str
    title: Optional[str] = None
    authors: Optional[list] = None
    abstract: Optional[str] = None
    abstract_embeddings: Optional[np.ndarray] = None
    text: Optional[str] = None
    text_chunks: Optional[list] = None
    chunk_embeddings: Optional[np.ndarray] = None
    figures: Optional[list] = None
    figure_embeddings: Optional[np.ndarray] = None
    tables: Optional[list] = None
    table_embeddings: Optional[np.ndarray] = None
    figure_interpretation: Optional[list] = None
    figure_interpretation_embeddings: Optional[np.ndarray] = None
    table_interpretation: Optional[list] = None
    table_interpretation_embeddings: Optional[np.ndarray] = None
    download_link: str = None
    downloaded: bool = False
    file_path: str = None
    openalex_info: Optional[dict] = None
    references: Optional[list] = None
    related_works: Optional[list] = None
    cited_by: Optional[list] = None
    pmc_id: Optional[str] = None

    def to_kb(self, project):
        papers_table = project.kb.db_tables["papers"]
        figures_table = project.kb.db_tables["figures"]
        tables_table = project.kb.db_tables["tables"]
        chunked_text_table = project.kb.db_tables["body_text_chunked"]
        references_table = project.kb.db_tables["references"]
        related_works_table = project.kb.db_tables["related_works"]
        cited_by_table = project.kb.db_tables["cited_by"]

        # if abstract_embeddings is a NumPy array, it should be converted before insert
        abstract_embedding = self.abstract_embeddings
        if hasattr(abstract_embedding, "tolist"):
            abstract_embedding = abstract_embedding.tolist()

        # Unlike the older PaperInfo version, the current schema uses
        # papers.id as the primary key and source, source_id as the 
        # external identity, so we look up an existing row before inserting.
        existing_stmts = select(papers_table.c.id).where(
            papers_table.c.source == self.id_type,
            papers_table.c.source_id == self.id,
        )
        paper_id = project.kb.session.execute(existing_stmts).scalar()

        if paper_id is None:
            stms = (
                insert(papers_table)
                .values(
                    source_id=self.id,
                    source=self.id_type,
                    title=self.title,
                    project_id=project.project_id,
                    abstract=self.abstract,
                    abstract_embeddings=abstract_embedding,
                    pdf_url=self.download_link,
                    pdf_path=self.file_path,
                    openalex_response=self.openalex_info,
                    authors=self.authors,
                    full_text=self.text or "",
                )
                .returning(papers_table.c.id)
            )

            paper_id = project.kb.session.execute(stms).scalar_one()

        # The older implementation assumed `self.figures[i]` was always a file path and
        # inserted directly using older schema field names. In the current pipeline,
        # figures may already be loaded as images, so this `if isinstance(...)`
        # branch keeps both cases working. The nested checks also
        # guard optional interpretation/embedding fields so papers without fully
        # processed figure metadata can still be persisted safely.
        if self.figures is not None:
            for i in range(len(self.figures)):
                img = self.figures[i]
                if isinstance(img, str):
                    img = Image.open(img)

                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="JPEG")
                img_bytes = img_byte_arr.getvalue()
                
                caption=""
                if self.figure_interpretation is not None and i < len(self.figure_interpretation):
                    caption = self.figure_interpretation[i]

                image_embedding = None
                if self.figure_embeddings is not None and i < len(self.figure_embeddings):
                    image_embedding = self.figure_embeddings[i]
                    if hasattr(image_embedding, "tolist"):
                        image_embedding = image_embedding.tolist()

                caption_embedding = None
                if self.figure_interpretation_embeddings is not None and i < len(self.figure_interpretation_embeddings):
                    caption_embedding = self.figure_interpretation_embeddings[i]
                    if hasattr(caption_embedding, "tolist"):
                        caption_embedding = caption_embedding.tolist()

                figure_stms = insert(figures_table).values(
                    paper_id=paper_id,
                    image_blob=img_bytes,
                    ai_caption=caption,
                    # The old PaperInfo persistence used figure-specific column
                    # names. The current schema normalizes these to
                    # image_embeddings / ai_caption_embeddings.
                    image_embeddings=image_embedding,
                    ai_caption_embeddings=caption_embedding,
                )
                project.kb.session.execute(figure_stms)

        # The previous version made the same assumptions for tables as figures: image
        # paths only, plus older embedding column names. The current
        # version may provide either file paths or already-loaded images, so
        # the type check keeps both representations valid. The
        # guards are there because it maybe possible that table interpretations and embeddings are not
        # existing yet even when the table image itself was extracted.
        if self.tables is not None:
            for i in range(len(self.tables)):
                img = self.tables[i]
                if isinstance(img, str):
                    img = Image.open(img)

                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="JPEG")
                img_bytes = img_byte_arr.getvalue()

                caption=""
                if self.table_interpretation is not None and i < len(self.table_interpretation):
                    caption = self.table_interpretation[i]

                image_embedding = None
                if self.table_embeddings is not None and i < len(self.table_embeddings):
                    image_embedding = self.table_embeddings[i]
                    if hasattr(image_embedding, "tolist"):
                        image_embedding = image_embedding.tolist()

                caption_embedding = None
                if self.table_interpretation_embeddings is not None and i < len(self.table_interpretation_embeddings):
                    caption_embedding = self.table_interpretation_embeddings[i]
                    if hasattr(caption_embedding, "tolist"):
                        caption_embedding = caption_embedding.tolist()

                table_stms = insert(tables_table).values(
                    paper_id=paper_id,
                    image_blob=img_bytes,
                    ai_caption=caption,
                    image_embeddings=image_embedding,
                    ai_caption_embeddings=caption_embedding,
                )
                project.kb.session.execute(table_stms)

        # Search works over chunk rows. If the processor has not produced
        # text_chunks yet, fall back to full text, then abstract, so every
        # searchable paper still gets at least one chunk row.
        if self.text_chunks:
            chunks = list(self.text_chunks)
        elif self.text:
            chunks = [self.text]
        elif self.abstract:
            chunks = [self.abstract]
        else:
            chunks = []

        # protect against duplicate chunk rows
        existing_chunks = select(chunked_text_table.c.id).where(
            chunked_text_table.c.paper_id == paper_id
        ).limit(1)

        has_chunks = project.kb.session.execute(existing_chunks).scalar() is not None

        if not has_chunks:
            for index, chunk_text in enumerate(chunks):
                embedding = None
                if self.chunk_embeddings is not None and index < len(self.chunk_embeddings):
                    embedding = self.chunk_embeddings[index]
                    # pgvector accepts plain Python lists more reliably than raw
                    # numpy arrays, so normalize model outputs before insert.
                    if hasattr(embedding, "tolist"):
                        embedding = embedding.tolist()

                chunk_stms = insert(chunked_text_table).values(
                    paper_id=paper_id,
                    chunk_id=index,
                    chunk_text=chunk_text,
                    chunk_embeddings=embedding,
                )
                project.kb.session.execute(chunk_stms)

        # The original logic inserted references once the target paper was found or
        # created, but it did not check whether the reference itself already existed. These
        # checks now do the following:
        # if the referenced paper is not yet in the KB, persist it first
        # if the reference already exists, do not insert a duplicate row

        if self.references is not None:
            for paper in self.references:
                existing = select(papers_table.c.id).where(
                    papers_table.c.source_id == paper.info.id,
                    papers_table.c.source == paper.info.id_type,
                )
                ref_id = project.kb.session.execute(existing).scalar()

                if ref_id is None:
                    ref_id = paper.info.to_kb(project)

                existing_relation = select(references_table.c.id).where(
                    references_table.c.source_id == paper_id,
                    references_table.c.target_id == ref_id,
                ).limit(1)

                if project.kb.session.execute(existing_relation).scalar() is None:
                    stms = insert(references_table).values(
                        source_id=paper_id,
                        target_id=ref_id,
                    )
                    project.kb.session.execute(stms)

        # This follows the same pattern as references.
        if self.related_works is not None:
            for paper in self.related_works:
                existing = select(papers_table.c.id).where(
                    papers_table.c.source_id == paper.info.id,
                    papers_table.c.source == paper.info.id_type,
                )
                related_id = project.kb.session.execute(existing).scalar()

                if related_id is None:
                    related_id = paper.info.to_kb(project)

                existing_relation = select(related_works_table.c.id).where(
                    related_works_table.c.source_id == paper_id,
                    related_works_table.c.target_id == related_id,
                ).limit(1)

                if project.kb.session.execute(existing_relation).scalar() is None:
                    stms = insert(related_works_table).values(
                        source_id=paper_id,
                        target_id=related_id,
                    )
                    project.kb.session.execute(stms)

        # Adds explicit existence checks that the previous version did not have. One check ensures the
        # cited paper is persisted before linking to it, and the other prevents duplicate
        # source_id : target_id rows if this paper is written to the KB more than once.
        if self.cited_by is not None:
            for paper in self.cited_by:
                existing = select(papers_table.c.id).where(
                    papers_table.c.source_id == paper.info.id,
                    papers_table.c.source == paper.info.id_type,
                )
                cited_id = project.kb.session.execute(existing).scalar()

                if cited_id is None:
                    cited_id = paper.info.to_kb(project)

                existing_relation = select(cited_by_table.c.id).where(
                    cited_by_table.c.source_id == paper_id,
                    cited_by_table.c.target_id == cited_id,
                ).limit(1)

                if project.kb.session.execute(existing_relation).scalar() is None:
                    stms = insert(cited_by_table).values(
                        source_id=paper_id,
                        target_id=cited_id,
                    )
                    project.kb.session.execute(stms)

        project.kb.session.commit()
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

        selection = select(
            papers_table.c.source_id,
            papers_table.c.source,
            papers_table.c.title,
            papers_table.c.abstract,
            papers_table.c.abstract_embeddings,
            papers_table.c.full_text,
            papers_table.c.pdf_url,
            papers_table.c.pdf_path,
            papers_table.c.openalex_response,
            papers_table.c.authors,
        ).where(papers_table.c.id == id)
        paper_info = project.kb.session.execute(selection).fetchall()

        if len(paper_info) > 1:
            raise DataIntegrityError("There are multiple papers with the id {}".format(id))
        elif len(paper_info) == 0:
            raise NoResultFound("Could not find a paper with id:{}".format(id))
        else:
            paper = cls(id=paper_info[0][0], id_type=paper_info[0][1])
            paper.title = paper_info[0][2]
            paper.abstract = paper_info[0][3]
            paper.abstract_embeddings = paper_info[0][4]
            paper.text = paper_info[0][5]
            paper.download_link = paper_info[0][6]
            paper.file_path = paper_info[0][7]
            if paper.file_path is not None:
                paper.downloaded = True
            else:
                paper.downloaded = False
            paper.openalex_info = paper_info[0][8]
            paper.authors = paper_info[0][9]

        figures = select(figures_table.c.image_blob,
                         figures_table.c.image_embeddings,
                         figures_table.c.ai_caption,
                         figures_table.c.ai_caption_embeddings).where(figures_table.c.paper_id == id)
        figures = project.kb.session.execute(figures).fetchall()
        if len(figures) == 0:
            paper.figures = None
        else:
            paper.figures = [Image.open(io.BytesIO(figure[0])) for figure in figures]
            paper.figure_embeddings = [figure[1] for figure in figures]
            paper.figure_interpretation = [figure[2] for figure in figures]
            paper.figure_interpretation_embeddings = [figure[3] for figure in figures]

        tables = select(tables_table.c.image_blob,
                        tables_table.c.image_embeddings,
                        tables_table.c.ai_caption,
                        tables_table.c.ai_caption_embeddings).where(tables_table.c.paper_id == id)
        tables = project.kb.session.execute(tables).fetchall()
        if len(tables) == 0:
            paper.tables = None
        else:
            paper.tables = [Image.open(io.BytesIO(table[0])) for table in tables]
            paper.table_embeddings = [table[1] for table in tables]
            paper.table_interpretation = [table[2] for table in tables]
            paper.table_interpretation_embeddings = [table[3] for table in tables]

        chunks = (select(chunked_text_table.c.chunk_text,
                        chunked_text_table.c.chunk_embeddings).where(chunked_text_table.c.paper_id == id).order_by(chunked_text_table.c.chunk_id)
                        )
        chunks = project.kb.session.execute(chunks).fetchall()
        if len(chunks) == 0:
            paper.text_chunks = None
        else:
            paper.text_chunks = [chunk[0] for chunk in chunks]
            paper.chunk_embeddings = [chunk[1] for chunk in chunks]

        references = select(references_table.c.target_id).where(references_table.c.source_id == id)
        references = project.kb.session.execute(references).fetchall()
        if len(references) == 0:
            paper.references = None
        else:
            refs = []
            for ref in references:
                ref_paper = cls.from_kb(project, ref[0])
                refs.append(ref_paper)
            paper.references = refs

        cited_by = select(cited_by_table.c.target_id).where(cited_by_table.c.source_id == id)
        cited_by = project.kb.session.execute(cited_by).fetchall()
        if len(cited_by) == 0:
            paper.cited_by = None
        else:
            refs = []
            for ref in cited_by:
                ref_paper = cls.from_kb(project, ref[0])
                refs.append(ref_paper)
            paper.cited_by = refs

        related_works = select(related_works_table.c.target_id).where(related_works_table.c.source_id == id)
        related_works = project.kb.session.execute(related_works).fetchall()
        if len(related_works) == 0:
            paper.related_works = None
        else:
            refs = []
            for ref in related_works:
                ref_paper = cls.from_kb(project, ref[0])
                refs.append(ref_paper)
            paper.related_works = refs

        return paper
