from functools import partial

from benchmate.alignment.blast import Blast
from benchmate.alignment.mmseqs import MMSeqs
from benchmate.alignment.foldseek import FoldSeek
from benchmate.alignment.folddisco import FoldDisco


class Alignment:
    """
    This class simply creates alignment instances given a config so the user can run project.alignment.mmseqs, this is
    a thin integration layer with the alignment module, the aligment module can still be used standalone and independently of the project
    if desired
    """
    def __init__(self, config):
        """
        initialize the alignment class, this is a collection of alignment class instances that are specific to a project
        :param config: alignment section of the benchmate config
        """
        self.config=config
        self.blast=Blast()
        self.blast.find_local_databases(config["blast_db_root"])
        self.blast.create_db=partial(self.blast.create_db, output_path=self.config["blast_db_root"])
        self.mmseqs=MMSeqs()
        mmseqs_root = config.get("mmseqs_db_root") or config.get("mmseq_db_root") or config.get("mmseqs2_db_root")
        self.mmseqs.find_local_databases(mmseqs_root)
        self.mmseqs.download_db=partial(self.mmseqs.download_db, location=mmseqs_root)
        self.foldseek=FoldSeek()
        self.foldseek.find_local_databases(config["foldseek_db_root"])
        self.foldseek.download_database=partial(self.foldseek.download_database, location=self.config["foldseek_db_root"])
        self.folddisco = FoldDisco()
        self.folddisco.find_local_databases(config["folddisco_db_root"])
        self.folddisco.create_index = partial(self.folddisco.create_index, db_path=self.config["folddisco_db_root"])