from hashlib import md5
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from benchmate.sequence.sequence import Sequence as BaseSequence, SequenceList
from benchmate.utils.general_utils import DataIntegrityError


class Sequence(BaseSequence):
    """
    a thin wrapper around the Sequence class so it is compatible with a project database
    """
    def __init__(self, name, sequence, seq_type, annotations, project):
        """
        :param config: project database config
        :param name: name of the sequence
        :param sequence: sequence
        :param seq_type: type of sequence
        :param annotations: sequence's annotations
        """
        self.project = project
        self._fastas()
        super().__init__(name, sequence, seq_type, annotations)

    @classmethod
    def from_fasta(cls, file, seq_type, annotations, project):
        """
        create a sequence from a fasta file
        :param config: sequence section of the config file
        :param file: fasta file
        :param seq_type: sequence type ("dna", "rna", "protein", "3di")
        :param annotations a dict of annotations
        :return: a sequence instance or SequenceList of sequence instances
        """
        seq = BaseSequence.from_fasta(file, seq_type, annotations)
        if isinstance(seq, SequenceList):
            return SequenceList([cls(s.name, s.sequence, s.seq_type, s.annotations, project) for s in seq], type=seq_type)
        return cls(seq.name, seq.sequence, seq.seq_type, seq.annotations, project)

    @classmethod
    def from_kb(cls, project, id):
        """
        create a sequence from a project database
        :param project: project class instance
        :param id: id of the sequence
        :return: a sequence instance
        """
        sequence_table = project.kb.db_tables["sequence"]
        stmt = select(sequence_table.c.name, sequence_table.c.sequence, sequence_table.c.type, sequence_table.c.annotations).where(sequence_table.c.id == id)
        result = project.kb.session().execute(stmt).fetchall()

        if result is None:
            raise NoResultFound(f"Could not find a sequence with id {id}")

        if len(result) > 1:
            raise DataIntegrityError(f"Found more than one sequence with id {id}")
        result = result[0]
        return cls(name=result[0], sequence=result[1], seq_type=result[2], annotations=result[3], project=project)

    def to_kb(self):
        """
        send a sequence to a project database and append it to the appropriate fasta file
        :param project: project class instance, this will also contain the fasta paths, see main config.yaml file
        :return: the id of the sequence
        """
        fasta_files = {
            "dna": "dna.fa",
            "rna": "rna.fa",
            "protein": "protein.fa",
            "3di": "tdi.fa",
        }
        try:
            fasta = Path(self.project.config["sequence"]["fasta_path"]) / fasta_files[self.info.seq_type]
        except KeyError:
            raise ValueError(f"Unsupported sequence type: {self.info.seq_type}") from None

        sequence_table = self.project.kb.db_tables["sequence"]
        stmt = sequence_table.insert().values(project_id=self.project.project_id,
                                              name=self.info.name,
                                              sequence=self.info.sequence,
                                              type=self.info.seq_type,
                                              annotations=self.info.annotations,
                                              hash=md5(self.info.sequence.encode()).hexdigest()).returning(sequence_table.c.id)
        result = self.project.kb.session().execute(stmt)
        seq_id = result.scalar_one()
        self.project.kb.session().commit()

        new_record = SeqRecord(Seq(self.info.sequence), id=str(seq_id), description=self.info.name)

        with fasta.open("a") as fasta_handle:
            SeqIO.write(new_record, fasta_handle, "fasta")

        return seq_id

    def _fastas(self):
        """
        Ensure that the project's FASTA directory and sequence files exist.
        """
        fasta_path = Path(self.project.config["sequence"]["fasta_path"])
        fasta_path.mkdir(parents=True, exist_ok=True)
        files = ["dna.fa", "rna.fa", "protein.fa", "tdi.fa"]  # tdi is 3di
        for file in files:
            (fasta_path / file).touch(exist_ok=True)

class SequenceFactory:
    """Create Sequence instances bound to a single Project."""

    def __init__(self, project):
        self.project = project

    def __call__(self, name, sequence, seq_type, annotations):
        """Create a project-associated Sequence instance."""
        return Sequence(name, sequence, seq_type, annotations, project=self.project)

    def from_fasta(self, file, seq_type, annotations):
        """Load one or more sequences from a FASTA file."""
        return Sequence.from_fasta(file, seq_type, annotations=annotations, project=self.project)

    def from_kb(self, id):
        """Load a sequence from this project's knowledge base."""
        return Sequence.from_kb(project=self.project, id=id)
