import os
import subprocess
import warnings
from dataclasses import dataclass

from typing import Dict, Optional

from Bio import Seq, SeqIO
import numpy as np

from benchmate.sequence.utils import *

class NoSequenceError(Exception):
    """
    Exception raised when there is no sequence in the file.
    """
    def __init__(self, message):
        super().__init__(message)

@dataclass
class SequenceInfo:
    name:str
    sequence:str
    type:str
    features:Optional[Dict]=None
    embeddings:Optional[np.ndarray]=None
    msa_path:Optional[str]=None
    blast_path:Optional[str]=None


#TODO features, what could this be?
class Sequence:
    def __init__(self, name, sequence, type="protein", features=None):
        """
        Sequence class constructuctor
        :param name: name of the sequence
        :param sequence: sequence str
        :param type: type of sequence whether its protein, 3di, dna or rna, this is important for embeddings and other comparison functions
        :param features: some sort of dictionary of features up to the user
        """
        types=["dna", "rna", "protein", "3di"]
        if type not in types:
            raise ValueError("Invalid sequence type, types can be {types}".format(types=", ".join(types)))
        self.info=SequenceInfo(name=name, sequence=sequence, type=type, features=features)

    def mutate(self, position, to, new_name=None):
        """
        position is 0 based, create a new instance of the sequence with the mutation
        """
        new_sequence = list(self.info.sequence)
        if position > len(new_sequence)-1:
            raise ValueError("Position is greater than the sequence length {}".format(len(new_sequence)))
        new_sequence[position] = to

        self.sequence = "".join(new_sequence)
        if new_name is not None:
            self.name = new_name
        return self

    #TODO replace with colabfold mmseqs request
    def msa(self, database, destination, output_name="msa.a3m", cleanup=True):
        """
        generate a multiple sequence alignment using mmseqs2 this assumes that you already have a database processed.
        :param database: the database that is ready to go
        :param destination: where to save the results.
        :param output_name: name of the a3m file
        :param cleanup: remove temporary files
        :return: path of the output file
        """
        self.write(os.path.join(destination, "query.fasta"))
        script=os.path.join(__file__.replace("sequence.py", ""), "../scripts/run_mmseqs.sh")
        #TODO better packaging
        command=" ".join(["bash", script, " -i", str(os.path.abspath(os.path.join(destination, "query.fasta"))),
                            "-d", database, "-o", str(os.path.join(destination, output_name)),
                            "-c"])
        run=subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if run.returncode != 0:
            raise ChildProcessError("There was an error with mmseqs run see error below '\n' {}".format(run.stderr))
        else:
            print("mmseqs run complete the results are in {}/{}".format(destination, output_name))

        if cleanup:
            items=["query.fasta", "query.index", "query.dbtype", "query.source", "query.lookup", "query",
                   "query.tab", "query_h", "query_h.dbtype", "query_h.index", "align", "align.dbtype","align.index"]
            for item in items:
                os.remove(os.path.join(destination, item))
        return os.path.join(destination, output_name)

    def blast(self, program, database, threshold=10, hitlist_size=50, write=True):
        """
        using the ncbi blast api run blast, I am not sure if localblast is needed
        :param program: which blast program to use
        :param database: which database to use
        :param threshold: e value threshold
        :param hitlist_size: how many hits to return
        :param write: whether to write the output file
        :return:
        """
        search=blast_search(program, database, self.sequence, threshold, hitlist_size)
        results=parse_blast_search(search)
        #TODO write to file and return path
        return results

    def write(self, fpath):
        seq=SeqIO.SeqRecord(Seq.Seq(self.sequence), id=self.name, description="")
        with open(fpath, "w") as handle:
            SeqIO.write(seq, handle, "fasta")

    #read a simple fasta or from database
    def read(self, fpath, type):
        fasta_sequences = SeqIO.parse(open(fpath),'fasta')
        length=len(fasta_sequences)
        if length < 1:
            raise NoSequenceError("There are no sequences in the file {}".format(fpath))
        elif length > 1:
            warnings.warn("There are multiple sequences in the file {} so will be returning a list of Sequence instances".format(fpath))
            sequences=[]
            for fasta in fasta_sequences:
                name, sequence = fasta.id, str(fasta.seq)
                sequences.append(Sequence(name=name, sequence=sequence, type=type))
                return sequences
        else:
            for fasta in fasta_sequences:
                name, sequence = fasta.id, str(fasta.seq)
                return Sequence(name=name, sequence=sequence, type=type)


    def __str__(self):
        return "Sequence with name {} and {} aas".format(self.name, len(self.sequence))

