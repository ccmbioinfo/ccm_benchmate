import os
import tempfile
import pytest
import numpy as np

from benchmate.structure import Structure
from benchmate.structure.utils import get_pocket_dimensions, THREE_TO_ONE
from benchmate.sequence import Sequence, SequenceList


DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data", "structure")
PDB_1AQ2 = os.path.join(DATA_DIR, "1AQ2.pdb")
PDB_4AF1 = os.path.join(DATA_DIR, "4AF1.pdb")
PDB_9KQW = os.path.join(DATA_DIR, "9KQW.pdb")


class TestStructure:
    def test_from_file_and_repr_str(self):
        s = Structure.from_file("1AQ2", PDB_1AQ2)
        assert s.name == "1AQ2"
        assert str(s) == "1AQ2"
        assert "Structure(" in repr(s)
        assert len(s.info.atoms) > 0

    def test_from_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            Structure.from_file("nonexistent", "nonexistent.pdb")

    def test_from_file_invalid_args(self):
        with pytest.raises(ValueError):
            Structure.from_file("invalid", file=None, id=None)

    def test_indexing(self):
        s = Structure.from_file("4AF1", PDB_4AF1)
        chain_a = s["A"]
        assert len(chain_a) > 0

        chain_0 = s[0]
        assert len(chain_0) == len(chain_a)

        slice_chains = s[0:1]
        assert isinstance(slice_chains, list)
        assert len(slice_chains) == 1

        atoms_res = s["A", 10]
        assert isinstance(atoms_res, list)

        with pytest.raises(KeyError):
            _ = s[12.34]

    def test_sequence(self):
        s1 = Structure.from_file("4AF1", PDB_4AF1)
        seq1 = s1.sequence()
        assert isinstance(seq1, Sequence)
        assert seq1.seq_type == "protein"

        s2 = Structure.from_file("1AQ2", PDB_1AQ2)
        seq2 = s2.sequence()
        assert isinstance(seq2, (Sequence, SequenceList))

    def test_to_3di(self):
        s = Structure.from_file("4AF1", PDB_4AF1)
        seq_3di = s.to_3di("A")
        assert isinstance(seq_3di, Sequence)
        assert seq_3di.seq_type == "3di"
        assert len(seq_3di) > 0

    def test_contacts(self):
        s = Structure.from_file("9KQW", PDB_9KQW)
        unique_chains = list(set(s.info.chains))

        if len(unique_chains) >= 2:
            c1, c2 = unique_chains[0], unique_chains[1]
        else:
            c1, c2 = unique_chains[0], unique_chains[0]

        contacts_atom = s.contacts(c1, c2, cutoff=4.0, level="atom", measure="any")
        assert isinstance(contacts_atom, list)

        contacts_res = s.contacts(c1, c2, cutoff=4.0, level="residue", measure="any")
        assert isinstance(contacts_res, list)

    def test_write(self):
        s = Structure.from_file("1AQ2", PDB_1AQ2)
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "out.pdb")
            s.write(out_file)
            assert os.path.exists(out_file)
            assert os.path.getsize(out_file) > 0


class TestStructureUtils:
    def test_three_to_one_map(self):
        assert THREE_TO_ONE["ALA"] == "A"
        assert THREE_TO_ONE["MSE"] == "M"

    def test_get_pocket_dimensions(self):
        center, bbox_size = get_pocket_dimensions(PDB_4AF1)
        assert len(center) == 3
        assert bbox_size > 0
