from functools import partial

from benchmate.alignment.blast import Blast
from benchmate.alignment.mmseqs import MMSeqs
from benchmate.alignment.foldseek import FoldSeek
from benchmate.alignment.folddisco import FoldDisco


class Alignment:
    def __init__(self, config):
        self.config=config
        self.blast=Blast()
        self.blast.find_local_databases(config["blast_db_root"])
        self.blast.create_db=partial(self.blast.create_db, output_path=self.config["blast_db_root"])
        self.mmseqs=MMSeqs()
        self.mmseqs.find_local_databases(config["mmseq_db_root"])
        self.mmseqs.download_database=partial(self.mmseqs.download_database, location=self.config["mmseqs_db_root"])
        self.foldseek=FoldSeek()
        self.foldseek.find_local_databases(config["foldseek_db_root"])
        self.foldseek.download_database=partial(self.foldseek.download_database, location=self.config["foldseek_db_root"])
        self.folddisco = FoldDisco()
        self.folddisco.find_local_databases(config["folddisco_db_root"])
        self.folddisco.create_index = partial(self.folddisco.create_index, db_path=self.config["folddisco_db_root"])