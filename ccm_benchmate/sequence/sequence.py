import os
import subprocess
import warnings

from Bio import Seq, SeqIO

from ccm_benchmate.sequence.utils import *

class NoSequenceError(Exception):
    """
    Exception raised when there is no sequence in the file.
    """
    def __init__(self, message):
        super().__init__(message)

#TODO features, what could this be?
class Sequence:
    def __init__(self, name, sequence, type="protein", features=None):
        """

        :param name:
        :param sequence:
        :param type:
        :param features:
        """
        types=["dna", "rna", "protein", "3di"]
        if type not in types:
            raise ValueError("Invalid sequence type, types can be {types}".format(types=", ".join(types)))
        self.name = name
        self.sequence = sequence
        self.features=features
        self.device="cuda" if torch.cuda.is_available() else "cpu"

    #TODO need to be able to also do a DNA/RNA embedding
    def embeddings(self, model="esmc_300m", normalize=False):
        if model == "esmc_300m" or model == "esmc_g00m":
            embeddings=esm3_embeddings(sequence=self.sequence, model=model,
                                       normalize=normalize, device=self.device)
        else:
            raise NotImplementedError("That model is not implemented.")
        return embeddings


    def mutate(self, position, to, new_name=None):
        """
        position is 0 based, create a new instance of the sequence with the mutation
        """
        new_sequence = list(self.sequence)
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
        if write:
            pass
        return results

    def write(self, fpath):
        seq=SeqIO.SeqRecord(Seq.Seq(self.sequence), id=self.name, description="")
        with open(fpath, "w") as handle:
            SeqIO.write(seq, handle, "fasta")

    #read a simple fasta or from database
    def read(self, fpath, db, id):
        fasta_sequences = SeqIO.parse(open(fpath),'fasta')
        length=len(fasta_sequences)
        if length < 1:
            raise NoSequenceError("There are no sequences in the file {}".format(fpath))
        elif length > 1:
            warnings.warn("There are multiple sequences in the file {} so will be returning a SequenceList".format(fpath))
            sequences=[]
            for fasta in fasta_sequences:
                name, sequence = fasta.id, str(fasta.seq)
                sequences.append(Sequence(name=name, sequence=sequence))
                return SequenceList(sequences=sequences)
        else:
            for fasta in fasta_sequences:
                name, sequence = fasta.id, str(fasta.seq)
                return Sequence(name=name, sequence=sequence)


    def __str__(self):
        return "Sequence with name {} and {} aas".format(self.name, len(self.sequence))

#This needs to be different than a list of sequences,
class SequenceList:
    def __init__(self, sequences, features=None):
        """
        Sequence list object, the only reason for you to use this if you want to create a paired msa,
        otherwise a list of Sequence instances will have more features.
        :param sequences: list of Sequence instances
        :param features: a dict of annotations, whatever you want
        """
        for item in sequences:
            assert isinstance(item, Sequence)
        self.sequences = sequences

    #TODO paired msa
    def msa(self, **kwargs):
        for item in self.sequences:
            if not isinstance(item, Sequence):
                raise TypeError("All items in the sequence list must be of type Sequence")
            else:
                item.msa(**kwargs)

    #TODO return a multifasta
    def write(self, fpath):
        seqs= []
        for item in self.sequences:
            seqs.append(SeqIO.SeqRecord(Seq.Seq(item.sequence), id=item.name, description=""))
        with open(fpath, "w") as handle:
            SeqIO.write(seqs, handle, "fasta")

    #TODO read multifasta
    def read(self, fpath, db, id):
        fasta_sequences = SeqIO.parse(open(fpath), 'fasta')
        length = len(fasta_sequences)
        if length < 1:
            raise NoSequenceError("There are no sequences in the file {}".format(fpath))
        elif length == 1:
            warnings.warn(
                "There is onle one sequence in the file {} so will be returning a Sequence".format(fpath))
            for fasta in fasta_sequences:
                name, sequence = fasta.id, str(fasta.seq)
                return Sequence(name=name, sequence=sequence)
        else:
            sequences = []
            for fasta in fasta_sequences:
                name, sequence = fasta.id, str(fasta.seq)
                sequences.append(Sequence(name=name, sequence=sequence))
                return SequenceList(sequences=sequences)

    def __getitem__(self, item):
        if isinstance(item, int):
            results = self.items[item]
        elif isinstance(item, slice):
            results = SequenceList(self.items[item])
        return results

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __add__(self, other):
        assert(isinstance(other, SequenceList))
        return SequenceList(self.items + other.items)

    def __sub__(self, other):
        assert(isinstance(other, SequenceList))
        return SequenceList([item for item in self.items if item not in other.items])

    def __contains__(self, item):
        assert(isinstance(item, SequenceList))
        return item in self.items

    def __str__(self):
        return f"SequenceList({self.items})"

    def __repr__(self):
        return f"SequenceList({self.items})"

    def __setitem__(self, index, value):
        assert(isinstance(index, int))
        assert(isinstance(value, Sequence))
        self.items[index] = value

    def __delitem__(self, index):
        assert(isinstance(index, int))
        del self.items[index]

    def __eq__(self, other):
        assert(isinstance(other, SequenceList))
        if len(self.items) != len(other.items):
            return False
        for item in self.items:
            if item not in other.items:
                return False
        return True

    def __ne__(self, other):
        if not isinstance(other, SequenceList):
            return True
        elif self==other:
            return False
        else:
            return True

class SequenceDict(dict):
    def __init__(self, keys, values):
        for key, value in zip(keys, values):
            assert(isinstance(key, str))
            assert(isinstance(value, Sequence) or isinstance(value, SequenceList))
            self[key] = value

    def __getitem__(self, key):
        assert (isinstance(key, str))
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        assert (isinstance(key, str))
        assert (isinstance(value, SequenceList) or isinstance(value, Sequence))
        super().__setitem__(key, value)

    def __delitem__(self, key):
        assert (isinstance(key, str))
        super().__delitem__(key)

    def __iter__(self):
        return iter(self.keys())

    def __eq__(self, other):
        if not isinstance(other, SequenceDict):
            return False
        if len(self) != len(other):
            return False
        for key in self.keys():
            if key not in other.keys():
                return False
            if self[key] != other[key]:
                return False
        return True

    def __ne__(self, other):
        if not isinstance(other, SequenceDict):
            return True
        elif self == other:
            return False
        else:
            return True

    def __str__(self):
        return f"SequenceDict({self.items()})"

    def __repr__(self):
        return f"SequenceDict({self.items()})"

    def __len__(self):
        return len(self.items())

    def __contains__(self, item):
        assert (isinstance(item, str))
        return item in self.keys()

    def write(self, fpath):
        seqs= []
        for key, value in self.items:
            seqs.append(SeqIO.SeqRecord(Seq.Seq(value.sequence), id=value.name, description=value.key))
        with open(fpath, "w") as handle:
            SeqIO.write(seqs, handle, "fasta")

   # THere is no read methods because this is constructed from list of sequences or individual sequences.

