import io
from typing import Iterator, Tuple, Union, Optional, List

import pandas as pd

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Blast import NCBIWWW
from Bio.Blast import NCBIXML
# Use StringIO to handle the XML string directly



KD = {
    'I': 4.5, 'V': 4.2, 'L': 3.8, 'F': 2.8, 'C': 2.5, 'M': 1.9, 'A': 1.8, 'G': -0.4,
    'T': -0.7, 'S': -0.8, 'W': -0.9, 'Y': -1.3, 'P': -1.6, 'H': -3.2, 'E': -3.5,
    'Q': -3.5, 'D': -3.5, 'N': -3.5, 'K': -3.9, 'R': -4.5
}

AA_MASS = {
    'A': 89.0935, 'R': 174.2017, 'N': 132.1184, 'D': 133.1032, 'C': 121.1590,
    'E': 147.1299, 'Q': 146.1451, 'G': 75.0669,  'H': 155.1552, 'I': 131.1736,
    'L': 131.1736, 'K': 146.1882, 'M': 149.2124, 'F': 165.1900, 'P': 115.1310,
    'S': 105.0930, 'T': 119.1197, 'W': 204.2262, 'Y': 181.1894, 'V': 117.1469,
    # Handle uncommon letters by approximations or ignore
    'U': 168.053,  # selenocysteine approx
    'O': 255.313,  # pyrrolysine approx
    'B': (132.1184 + 133.1032) / 2,  # N/D
    'Z': (147.1299 + 146.1451) / 2,  # E/Q
    'X': 138.0,  # unknown average
    'J': 131.1736,  # I/L
    '*': 0.0
}


PKA = {
    "Cterm": 2.34, "Nterm": 9.69,
    "C": 8.33, "D": 3.86, "E": 4.25, "H": 6.00,
    "K": 10.5, "R": 12.5, "Y": 10.07
}


def blast_search(program, database, sequence, expect_threshold=10.0, hitlist_size=50):
    if not all([program, database, sequence]):
        raise ValueError("Program, database, and sequence are required parameters.")

    try:
        result_handle = NCBIWWW.qblast(
            program=program,
            database=database,
            sequence=sequence,
            expect=expect_threshold,
            hitlist_size=hitlist_size
        )

        blast_result_xml = result_handle.read()
        result_handle.close()

        if not blast_result_xml or "Status=WAITING" in blast_result_xml or "Status=FAILED" in blast_result_xml:
             if "Message" in blast_result_xml:
                 try:
                     message_start = blast_result_xml.find("<Message") + len("<Message")
                     message_start = blast_result_xml.find(">", message_start) + 1
                     message_end = blast_result_xml.find("</Message>")
                     if message_start > 0 and message_end > message_start:
                         error_message = blast_result_xml[message_start:message_end]
                         print(f"Error message from NCBI: {error_message}")
                 except Exception as e:
                     print(f"Could not parse specific error message: {e}")
             return None # Indicate failure or no results

        xml_handle = io.StringIO(blast_result_xml)
        blast_record = NCBIXML.read(xml_handle)

        print("BLAST search completed successfully.")
        return blast_record

    except Exception as e:
        print(f"An error occurred during the BLAST search: {e}")
        raise e


def parse_blast_search(blast_record):
    alignments=[]
    if blast_record.alignments:
        for alignment in blast_record.alignments:
            results={"alignment":alignment.title,
                     "length":alignment.length,
                     "score":alignment.hsps[0].score,
                     "evalue":alignment.hsps[0].expect,
                     "query_start":alignment.hsps[0].query_start,
                     "query_end":alignment.hsps[0].query_end,
                     "subject_start":alignment.hsps[0].sbjct_start,
                     "subject_end":alignment.hsps[0].sbjct_end,
                     "hit_sequence":alignment.hsps[0].sbjct,}
            alignments.append(results)
        alignments=pd.DataFrame(alignments)
    else:
        raise ValueError("No blast alignments found.")
    return alignments


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
    def __init__(self, table, alignment):
        cols = ["query", "target", "evalue", "bits", "alnlen", "qlen", "tlen", "pident", "raw"]
        self.table = pd.read_csv(table, sep="\t", names=cols)
        self.alignment = SinglePassFastaIndex(alignment)
        self.query=self.__getitem__(0)

    def __getitem__(self,key):
        return self.alignment[key]

    def __len__(self):
        return len(self.alignment.keys())

    def __str__(self):
        return f"MSA with {len(self)} sequences."






