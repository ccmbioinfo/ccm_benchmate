import os

import pandas as pd
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq

def find_root_name(folder, to_replace=[".", "_"]):
    """
    This is used to find local databases however there is no check on what kind of db or file it is, we are just using file names
    :param folder: which folder to check
    :param to_replace: usually, foldseek, mmseqs, blast and folddisco add known suffixes to different files of a specific db, these are
    removed so that we can identify uniqe dbs as one folder can contain an arbitrary number of files
    :return: a list of potential dbs, not checked for specific compatibility, keep different kinds of dbs (blast, mmseqs, etc.) in different folders
    """
    files=os.listdir(folder)
    replaced=[]
    for f in files:
        if f.startswith("."):
            continue
        base = f.split(".")[0]
        if base:
            roots.add(base)
    return sorted(list(roots))

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
