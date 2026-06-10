from dataclasses import dataclass
from typing import Optional

import numpy as np

@dataclass(slots=True)
class PaperInfo:
    """
    Dataclass to hold information about a paper, this is constructed inside the Paper class and desined to be compatible with
    semantic search and embedding distance searches
    """
    # in papers table
    id: str
    external_ids: Optional[dict] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    abstract_embeddings: Optional[np.ndarray] = None
    download_links: Optional[list] = None
    file_paths: Optional[list] = None
    full_json: Optional[dict] = None
    authors: Optional[list] = None
    publication_date: Optional[str] = None
    venue: Optional[str] = None
    text: Optional[str] = None

    #body_text_chunk table
    text_chunks: Optional[list] = None
    chunk_embeddings: Optional[np.ndarray] = None

    #in figures table
    figures: Optional[list] = None
    figure_embeddings: Optional[np.ndarray] = None
    figure_interpretation: Optional[list] = None
    figure_interpretation_embeddings: Optional[np.ndarray] = None

    #in tables table
    tables: Optional[list] = None
    table_embeddings: Optional[np.ndarray] = None
    table_interpretation: Optional[list] = None
    table_interpretation_embeddings: Optional[np.ndarray] = None

    #references table
    references: Optional[list] = None

    #related works table
    related_works: Optional[list] = None

    #cited by table
    cited_by: Optional[list] = None


