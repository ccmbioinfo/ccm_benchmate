
import pandas as pd
from Bio import SeqRecord, Seq


# These should have make db and __call__ methods
class Blast:
    pass

class MMseqs2:
    pass

class FoldSeek:
    pass

class FoldDisco:
    pass

class SinglePassFastaIndex:
    def __init__(self, fasta_path, delim="_"):
        self.fasta_path = fasta_path
        self.delim = delim
        self.offsets = {}  # merged unique key -> file offset
        self._build_index()

    def _build_index(self):
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

class MSA:
    def __init__(self, table, alignment, cols):
        self.table = pd.read_csv(table, sep="\t", names=cols)
        self.alignment = SinglePassFastaIndex(alignment)
        self.query=self.__getitem__(0)

    def __getitem__(self,key):
        return self.alignment[key]

    def __len__(self):
        return len(self.alignment.keys())

    def __str__(self):
        return f"MSA with {len(self)} sequences."