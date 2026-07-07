import os
from hashlib import md5
from pathlib import Path

from sqlalchemy import select

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from benchmate.sequence.sequence import Sequence as BaseSequence


class Sequence(BaseSequence):
    """
    a thin wrapper around the Sequence class so it is compatible with a project database
    """
    def __init__(self, config, name, sequence, seq_type, annotations):
        """
        :param config: project database config
        :param name: name of the sequence
        :param sequence: sequence
        :param seq_type: type of sequence
        :param annotations: sequence's annotations
        """
        self.config=config
        self._fastas()
        super().__init__(name, sequence, seq_type, features)

    @classmethod
    def from_fasta(cls, config, file):
        """
        create a sequence from a fasta file
        :param config: sequence section of the config file
        :param file: fasta file
        :return: a sequence instance
        """
        seq=super().from_fasta(file)
        cls(config, seq.name, seq.sequence, seq.seq_type, seq.features)
        return cls

    @classmethod
    def from_kb(cls, project, id):
        """
        create a sequence from a project database
        :param project: project class instance
        :param id: id of the sequence
        :return: a sequence instance
        """
        sequence_table = project.kb.db_tables["sequence"]
        stmt = select(sequence_table).where(sequence_table.c.id == id)
        result = project.kb.session.execute(stmt)
        info = result.scalar_one()
        return cls(name=info.name, sequence=info.sequence, seq_type=info.seq_type, features=info.features)

    def to_kb(self, project):
        """
        send a sequence to a project database and append it to the appropriate fasta file
        :param project: project class instance, this will also contain the fasta paths, see main config.yaml file
        :return: the id of the sequence
        """
        sequence_table = project.kb.db_tables["sequence"]
        stmt = sequence_table.insert().values(project_id=project.project_id,
                                              name=self.info.name,
                                              sequence=self.info.sequence,
                                              seq_type=self.info.seq_type,
                                              annotations=self.info.annotations,
                                              hash=md5(self.info.sequence).hexdigest()).returning(sequence_table.c.id)
        result = project.kb.session.execute(stmt)
        seq_id = result.scalar.one()
        project.kb.session.commit()

        if self.seq_type=="dna":
            fasta=os.path.join(self.config["fasta_root"], "dna.fa")
        elif self.seq_type=="rna":
            fasta=os.path.join(self.config["fasta_root"], "rna.fa")
        elif self.seq_type=="protein":
            fasta=os.path.join(self.config["fasta_root"], "protein.fa")
        elif self.seq_type=="3di":
            fasta=os.path.join(self.config["fasta_root"], "tdi.fa")

        new_record=SeqRecord(Seq(self.info.sequence), id=result, description=self.info.name)

        with open(fasta, "a") as f:
            SeqIO.write(new_record, f, "fasta")

        return seq_id

    def _fastas(self):
        """
        collect all the fasta files that are in the project folders
        :return: 4 paths for different kinds of sequence modalitites
        """
        os.makedirs(self.config["fasta_root"], exist_ok=True)
        files = ["dna.fa", "rna.fa", "protein.fa", "tdi.fa"]  # tdi is 3di
        for file in files:
            if os.path.exists(os.path.join(self.config["fasta_root"], file)):
                continue
            else:
                Path(os.path.join(self.config["fasta_root"], file)).touch()