import os
import tempfile
from collections import Counter
from dataclasses import dataclass
import subprocess
from typing import Dict, Optional

import biotite.sequence
from biotite.application.clustalo import ClustalOmegaApp
from biotite.application.viennarna import RNAfoldApp
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
    name: str
    sequence: str
    seq_type: str
    features: Optional [Dict]= None
    msa_path: Optional[str] = None
    blast_path: Optional[str] = None


class Sequence:
    """A biological sequence with associated metadata and utility methods."""

    def __init__(self, name, sequence,  seq_type= "protein", features=None):
        valid = ["dna", "rna", "protein", "3di"]
        if seq_type not in valid:
            raise ValueError(f"Invalid sequence type, must be one of: {', '.join(valid)}")

        self.info = SequenceInfo(name=name, sequence=sequence, seq_type=seq_type,
                                 features=features if features is not None else None)

    @property
    def name(self):
        return self.info.name

    @property
    def sequence(self):
        return self.info.sequence

    @property
    def seq_type(self):
        return self.info.seq_type

    @property
    def features(self):
        return self.info.features or {}


    def blast(self, program, database, threshold=10, hitlist_size=50):
        """
        using the ncbi blast api run blast, I am not sure if localblast is needed
        :param program: which blast program to use
        :param database: which database to use
        :param threshold: e value threshold
        :param hitlist_size: how many hits to return
        :param write: whether to write the output file
        :return: either the alignment dataframe or a Bio.SeqIO file connection or both
        """
        search=blast_search(program, database, self.sequence, threshold, hitlist_size)
        results=parse_blast_search(search)
        return results


    def vienna(self, temperature=37, *args):
        """
        Predict RNA secondary structure using ViennaRNA RNAfold via Biotite.
        :param temperature: what temperature to use for folding
        :param args: additional arguments passed to vienna a string or a list of strings
        :return: structure in dot-bracket notation, free energy in kcal/mol, list of base pairs
        """
        self._ensure_nucleic()
        seq=biotite.sequence.NucleotideSequence(self.sequence)
        app = RNAfoldApp(seq, temperature=temperature)
        if args:
            app.add_additional_options(*args)
        app.start()
        app.join()
        free_energy=app.get_free_energy()
        structure=app.get_dot_bracket()
        bp=app.get_base_pairs()
        return structure, free_energy, bp

    def subseq(self, start, end, keep_features=True):
        """Return subsequence [start:end) (0-based, half-open)."""
        if start < 0 or end < 0 or start > end or end > len(self):
            raise ValueError("Invalid subseq range.")
        sub_seq = self.sequence[start:end]
        if keep_features:
            return Sequence(name=f"{self.name}_sub{start}_{end}", sequence=sub_seq,
                        seq_type=self.seq_type, features=self.features)
        else:
            return Sequence(name=f"{self.name}_sub{start}_{end}", sequence=sub_seq,
                        seq_type=self.seq_type, features=None)

    def find(self, subseq: str):
        """
        Returns all start indices (0-based) where subseq occurs (allowing overlaps).
        Case-insensitive match.
        """
        s = self.sequence.upper()
        q = subseq.upper()
        if not q:
            return []
        hits = []
        i = s.find(q)
        while i != -1:
            hits.append(i)
            i = s.find(q, i + 1)
        return hits

    def _ensure_nucleic(self):
        if self.seq_type not in {"dna", "rna"}:
            raise TypeError("Operation requires DNA or RNA sequence.")

    def reverse_complement(self, keep_features=True):
        self._ensure_nucleic()
        seq=biotite.sequence.NucleotideSequence(self.sequence)
        seq=seq.complement().reverse()
        if keep_features:
            return Sequence(name=f"{self.name}_rc", sequence=str(seq),
                        seq_type=self.seq_type, features=self.features)
        else:
            return Sequence(name=f"{self.name}_rc", sequence=str(seq),
                        seq_type=self.seq_type, features=None)

    def translate(self, table=1, keep_features=True, to_stop=False):
        """
        Translate nucleic acids to protein. Uses Biopython table if available; otherwise
        supports only standard table (1) for unambiguous triplets; ambiguous codons → 'X'.
        """
        self._ensure_nucleic()
        seq=Seq(self.sequence)
        prot=seq.translate(table)
        if to_stop:
            prot=str(prot).split("*", 1)[0]
        else:
            prot=str(prot)
        if keep_features:
            return Sequence(name=f"{self.name}_trans", sequence=prot, seq_type="protein", features=self.features)
        else:
            return Sequence(name=f"{self.name}_trans", sequence=prot, seq_type="protein", features=None)

    def gc_content(self, window=None):
        """GC fraction overall, or rolling mean over window (DNA/RNA)."""
        self._ensure_nucleic()
        seq = self.sequence.upper().replace("U", "T")
        if len(seq) == 0:
            return 0.0 if window is None else np.array([])
        if window is None:
            g = seq.count("G");
            c = seq.count("C")
            return (g + c) / len(seq)
        if window <= 0:
            raise ValueError("window must be positive")
        arr = np.frombuffer(seq.encode(), dtype="S1")
        gc = (arr == b"G") | (arr == b"C")
        from numpy.lib.stride_tricks import sliding_window_view
        if len(arr) < window:
            return np.array([])
        sw = sliding_window_view(gc, window)
        return sw.mean(axis=1)

    def gc_skew(self, window) -> np.ndarray:
        """GC skew = (G - C) / (G + C) in sliding windows."""
        self._ensure_nucleic()
        if window <= 0:
            raise ValueError("window must be positive")
        seq = self.sequence.upper().replace("U", "T")
        arr = np.frombuffer(seq.encode(), dtype="S1")
        from numpy.lib.stride_tricks import sliding_window_view
        if len(arr) < window:
            return np.array([])
        sw = sliding_window_view(arr, window)  # shape (L-window+1, window)
        G = (sw == b"G").sum(axis=1).astype(float)
        C = (sw == b"C").sum(axis=1).astype(float)
        denom = G + C
        denom[denom == 0] = np.nan  # avoid divide by zero
        skew = (G - C) / denom
        # Replace NaN with 0 skew where no G/C present
        skew = np.nan_to_num(skew, nan=0.0)
        return skew

    def kmer_counts(self, k: int, normalize: bool = True) -> Dict[str, float]:
        """Counts (or frequencies) of k-mers (case-insensitive)."""
        if k <= 0:
            raise ValueError("k must be positive")
        s = self.sequence.upper()
        if len(s) < k:
            return {}

        counts = Counter(s[i:i + k] for i in range(len(s) - k + 1))
        if not normalize:
            return dict(counts)
        total = sum(counts.values())
        return {kmer: c / total for kmer, c in counts.items()}

    def _ensure_protein(self):
        if self.seq_type != "protein":
            raise TypeError("Operation requires a protein sequence.")

    def aa_composition(self) -> Dict[str, float]:
        """Fractional composition over the 20 canonical amino acids (others grouped as 'X')."""
        self._ensure_protein()
        s = self.sequence.upper()
        L = len(s) if len(s) > 0 else 1
        comp = {aa: 0 for aa in "ACDEFGHIKLMNPQRSTVWY"}
        other = 0
        for ch in s:
            if ch in comp:
                comp[ch] += 1
            else:
                other += 1
        comp = {k: v / len(s) for k, v in comp.items()}
        comp["X"] = other / L
        return comp

    def molecular_weight(self) -> float:
        """Approximate molecular weight in Daltons (average mass, subtract water for peptide bonds)."""
        self._ensure_protein()
        s = self.sequence.upper().replace("*", "")  # ignore terminal stop for mass
        if not s:
            return 0.0
        masses = [AA_MASS.get(aa, AA_MASS['X']) for aa in s]
        mw = sum(masses)

        return float(mw)

    def isoelectric_point(self) -> float:
        """
        Estimate pI using Henderson–Hasselbalch with a bisection search.
        Uses an EMBOSS-like pKa set.
        """
        self._ensure_protein()
        s = self.sequence.upper()

        counts = {aa: s.count(aa) for aa in "ACDEFGHIKLMNPQRSTVWY"}
        nterm_pka = PKA["Nterm"]
        cterm_pka = PKA["Cterm"]

        def net_charge(pH: float) -> float:
            # Positive groups: N-term, K, R, H
            pos = (
                    1.0 / (1.0 + 10 ** (pH - nterm_pka)) +
                    counts["K"] * (1.0 / (1.0 + 10 ** (pH - PKA["K"]))) +
                    counts["R"] * (1.0 / (1.0 + 10 ** (pH - PKA["R"]))) +
                    counts["H"] * (1.0 / (1.0 + 10 ** (pH - PKA["H"])))
            )
            # Negative groups: C-term, D, E, C, Y
            neg = (
                    1.0 / (1.0 + 10 ** (PKA["Cterm"] - pH)) +
                    counts["D"] * (1.0 / (1.0 + 10 ** (PKA["D"] - pH))) +
                    counts["E"] * (1.0 / (1.0 + 10 ** (PKA["E"] - pH))) +
                    counts["C"] * (1.0 / (1.0 + 10 ** (PKA["C"] - pH))) +
                    counts["Y"] * (1.0 / (1.0 + 10 ** (PKA["Y"] - pH)))
            )
            return pos - neg

        # Bisection between 0 and 14
        lo, hi = 0.0, 14.0
        for _ in range(60):
            mid = (lo + hi) / 2.0
            charge = net_charge(mid)
            if charge > 0:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2.0

    def hydropathy_profile(self, window= 9, scale = "KyteDoolittle") -> np.ndarray:
        """
        Sliding-window hydropathy. Only 'KyteDoolittle' is supported.
        Returns an array of length L - window + 1 (centered windows).
        """
        self._ensure_protein()
        if scale != "KyteDoolittle":
            raise NotImplementedError("Only 'KyteDoolittle' scale is supported currently.")
        if window <= 0:
            raise ValueError("window must be positive")
        s = self.sequence.upper()
        if len(s) < window:
            return np.array([])
        vals = np.array([KD.get(aa, 0.0) for aa in s], dtype=float)
        kernel = np.ones(window, dtype=float) / window
        prof = np.convolve(vals, kernel, mode="valid")
        return prof

    def mutate(self, position, to, new_name= None, keep_features=True):
        """
        Returns a NEW Sequence with a substitution at position (0-based).
        Maintains features as-is (positions are unchanged); if you need to
        propagate effects to per_position/intervals, use __getitem__/insert/delete or remap_features.
        """
        if position < 0 or position >= len(self):
            raise ValueError(f"Position {position} out of bounds for length {len(self)}")
        if len(to) != 1:
            raise ValueError("Mutation 'to' must be a single character.")
        new_seq_list = list(self.sequence)
        new_seq_list[position] = to
        new_seq = "".join(new_seq_list)
        nm = new_name if new_name else f"{self.name}_p{position}{self.sequence[position]}>{to}"
        if keep_features:
            return Sequence(nm, new_seq, self.seq_type, self.features)
        else:
            return Sequence(nm, new_seq, self.seq_type, None)

    def insert(self, position, segment, keep_features=True):
        """Insert segment at position (0-based index before insertion)."""
        if position < 0 or position > len(self):
            raise ValueError(f"Position {position} out of bounds for insertion in length {len(self)}")
        new_seq = self.sequence[:position] + segment + self.sequence[position:]
        # Remap features: shift intervals after position; extend per_position with gaps/None
        if keep_features:
            return Sequence(f"{self.name}_ins{position}", new_seq, self.seq_type, self.features)
        else:
            return Sequence(f"{self.name}_ins{position}", new_seq, self.seq_type, None)

    def delete(self, start, end, keep_features=True) -> "Sequence":
        """
        Delete [start:end) (0-based, half-open).
        """
        if start < 0 or end < 0 or start > end or end > len(self):
            raise ValueError("Invalid delete range.")
        new_seq = self.sequence[:start] + self.sequence[end:]

        if keep_features:
            return Sequence(f"{self.name}_del{start}:{end}", new_seq, self.seq_type, self.features)
        else:
            return Sequence(f"{self.name}_del{start}:{end}", new_seq, self.seq_type, None)

    @classmethod
    def from_fasta(cls, file_path, seq_type):
        """
        Read one or many sequences from a FASTA file.
        """
        records = list(SeqIO.parse(file_path, 'fasta'))
        if not records:
            raise NoSequenceError(f"No sequences in {file_path}")
        if len(records) > 1:
            print("There are multiple sequences in the FASTA file, returning a Sequence list.")
            seqs=[cls(name=rec.id, sequence=str(rec.seq), seq_type=seq_type) for rec in records]
            return SequenceList(seqs, type= seq_type)
        else:
            rec = records[0]
            return cls(name=rec.id, sequence=str(rec.seq), seq_type=seq_type)

    def to_fasta(self, file_path: str) -> None:
        """Write this sequence to a FASTA file."""
        rec = SeqIO.SeqRecord(Seq(self.sequence), id=self.name, description="")
        with open(file_path, "w") as handle:
            SeqIO.write(rec, handle, "fasta")

    def __len__(self) -> int:
        return len(self.info.sequence)

    def __repr__(self) -> str:
        return f"Sequence(name={self.name!r}, len={len(self)}, type={self.seq_type})"

    def __str__(self) -> str:
        return f"Sequence(name={self.name}, length={len(self)}, type={self.seq_type})"

    def __eq__(self, other: "Sequence") -> bool:
        return (self.seq_type == other.seq_type) and (self.sequence.upper() == other.sequence.upper())

    def __ne__(self, other):
        if not self.__eq__(other):
            return True
        else:
            return False


class SequenceList(list):
    """
    A list of Sequence objects with utility methods. Class methods are inherited from list
    """
    def __init__(self, sequences, type= "protein"):
        """Initialize with a list of Sequence objects, all must be Sequence instances."""
        for seq in sequences:
            assert isinstance(seq, Sequence) and seq.seq_type == type, "All items must be Sequence instances of the same type."
        super().__init__(sequences)

    def ClustalOmega(self, *args):
        """
        Perform multiple sequence alignment using Clustal Omega via Biotite. args are passed to ClustalOmegaApp.
        :param args: list of clustal omega arguments
        :return: returns a tuple of gapped_sequences, alignment_matrix and guide_tree
        """
        seqs= [biotite.sequence.ProteinSequence(seq.sequence) for seq in self]
        app= ClustalOmegaApp(seqs)
        if args:
            app.add_additional_options(*args)
        app.full_matrix_calculation()
        app.start()
        app.join()
        alignment = app.get_alignment()
        tree=str(app.get_guide_tree())
        gapped=alignment.get_gapped_sequences()
        matrix=app.get_distance_matrix()
        return gapped, matrix, tree


    @classmethod
    def from_fasta(cls, file_path, seq_type):
        """
        Read one or many sequences from a FASTA file.
        """
        records = list(SeqIO.parse(file_path, 'fasta'))
        if not records:
            raise NoSequenceError(f"No sequences in {file_path}")
        sequences = [Sequence(name=rec.id, sequence=str(rec.seq), seq_type=seq_type) for rec in records]
        return cls(sequences)

    def to_fasta(self, file_path: str) -> None:
        """Write all sequences to a FASTA file."""
        records = [SeqIO.SeqRecord(Seq(seq.sequence), id=seq.name, description="") for seq in self]
        with open(file_path, "w") as handle:
            SeqIO.write(records, handle, "fasta")