import os

import pandas as pd
from Bio import SeqRecord, Seq

def find_root_name(folder, to_replace=[".", "_"]):
    files=os.listdir(folder)
    replaced=[]
    for f in files:
        name=f
        for item in to_replace:
            name=name.replace(item,"")
        replaced.append(name)
    return list(set(replaced))

class SinglePassFastaIndex:
    """
    this is a tiny class to access MSA a3m files, these files look like fasta but they are not reall so tools
    that deal with them have issues. This is not really a faster solution but a solution.
    """
    def __init__(self, fasta_path, delim="_"):
        """
        constructor, the goal is to create an index of the entries, sometimes you will get multiple entries with the same name
        these will have other things next to the name, a combination of these create a unique entry
        """
        self.fasta_path = fasta_path
        self.delim = delim
        self.offsets = {}  # merged unique key -> file offset
        self._build_index()

    #TODO write the index to file
    def _build_index(self):
        """
        collect all the entries in a "fasta" file, this would work for fastas assuming there are no duplicated entries
        """
        with open(self.fasta_path, "r") as f:
            while True:
                pos = f.tell()
                line = f.readline()
                if not line:
                    break
                if line.startswith(">"):
                    header = line[1:].strip()
                    key = self.delim.join(header.split())
                    # guarantee uniqueness if key repeats
                    counter = 1
                    uniq_key = key
                    while uniq_key in self.offsets:
                        counter += 1
                        uniq_key = f"{key}_{counter}"
                    self.offsets[uniq_key] = pos
                    # skip sequence lines until next header
                    while True:
                        pos_seq = f.tell()
                        seq_line = f.readline()
                        if not seq_line or seq_line.startswith(">"):
                            f.seek(pos_seq)
                            break

    def keys(self):
        return self.offsets.keys()

    def __getitem__(self, key):
        pos = self.offsets[key]
        with open(self.fasta_path) as f:
            f.seek(pos)
            header = f.readline().strip()[1:]
            seq_lines = []
            while True:
                pos_seq = f.tell()
                line = f.readline()
                if not line or line.startswith(">"):
                    f.seek(pos_seq)
                    break
                seq_lines.append(line.strip())

            return SeqRecord(Seq("".join(seq_lines)), id=key, description="")

    def __len__(self):
        return len(list(self.offsets.keys()))

    def __repr__(self):
        return f"{self.fasta_path} index with {self.__len__()} entries"

    def __str__(self):
        return self.__repr__()

#TODO need to add some methods to seeing what's in there and get them ala pandas slicing
class Alignment:
    def __init__(self, table, alignment, cols=None):
        if cols is None:
            cols=["query","target","pident","alnlen","mismatch","gapopen","qstart","qend","tstart","tend","evalue","bits"]
        self.table = pd.read_csv(table, sep="\t", names=cols)
        self.alignment = SinglePassFastaIndex(alignment)
        self.query=self.__getitem__(0)

    def __getitem__(self,key):
        return self.alignment[key]

    def __len__(self):
        return len(self.alignment.keys())

    def __str__(self):
        return f"Alignment with {len(self)} sequences."