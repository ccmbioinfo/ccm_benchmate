import os
from hashlib import md5
from pathlib import Path

from sqlalchemy import select

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from benchmate.sequence.sequence import Sequence as BaseSequence


class Sequence(BaseSequence):
    def __init__(self, config, name, sequence, seq_type, features):
        self.config=config
        self._fastas()
        super().__init__(name, sequence, seq_type, features)

    @classmethod
    def from_fasta(cls, config, file):
        seq=super().from_fasta(file)
        cls(config, seq.name, seq.sequence, seq.seq_type, seq.features)
        return cls

    @classmethod
    def from_kb(cls, project, id):
        sequence_table = project.kb.db_tables["sequence"]
        stmt = select(sequence_table).where(sequence_table.c.id == id)
        result = project.kb.session.execute(stmt)
        info = result.scalar_one()
        return cls(name=info.name, sequence=info.sequence, seq_type=info.seq_type, features=info.features)

    def to_kb(self, project):
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
        os.makedirs(self.config["fasta_root"], exist_ok=True)
        files = ["dna.fa", "rna.fa", "protein.fa", "tdi.fa"]  # tdi is 3di
        for file in files:
            if os.path.exists(os.path.join(self.config["fasta_root"], file)):
                continue
            else:
                Path(os.path.join(self.config["fasta_root"], file)).touch()