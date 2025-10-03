# test_molecule.py
import pytest
import numpy as np
from rdkit import Chem

from benchmate.molecule.molecule import Molecule

#TODO need to create a tiny dataset for this
class DummyDataset:
    """Mock FingerprintedDataset for testing search()."""
    def __init__(self, library, shape=None):
        self.library = library
        self.shape = shape

    def search(self, smiles, n=10):
        return [{"smiles": smiles, "similarity": 1.0}] * n



@pytest.fixture
def aspirin():
    # SMILES for aspirin
    return Molecule(name="aspirin", smiles="CC(=O)OC1=CC=CC=C1C(=O)O")


def test_initialization(aspirin):
    assert isinstance(aspirin.info.mol, Chem.Mol)
    assert aspirin.info.name == "aspirin"
    assert aspirin.info.smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"
    assert isinstance(aspirin.info.ecfp4, Chem.rdchem.ExplicitBitVect)
    assert isinstance(aspirin.info.fcfp4, Chem.rdchem.ExplicitBitVect)
    assert isinstance(aspirin.info.maccs, Chem.rdchem.ExplicitBitVect)


def test_repr_str(aspirin):
    assert "aspirin" in str(aspirin)
    assert "aspirin" in repr(aspirin)


def test_eq_and_ne(aspirin):
    same = Molecule("same", "CC(=O)OC1=CC=CC=C1C(=O)O")
    different = Molecule("benzoic acid", "C1=CC=C(C=C1)C(=O)O")

    assert aspirin == same
    assert aspirin != different
    assert aspirin != "not a molecule"


def test_properties_dict(aspirin):
    props = aspirin.info.properties
    assert isinstance(props, dict)
    assert "MolWt" in props  # one of RDKit descriptors
    assert props["MolWt"] > 0


def test_fingerprint_invalid(aspirin):
    with pytest.raises(NotImplementedError):
        aspirin._fingerprint(type="invalid")


def test_search_default(aspirin):
    results = aspirin.search(library=[{"smiles": "CCO"}], n=3)
    assert len(results) == 3
    assert all("smiles" in r for r in results)
    assert results[0]["smiles"] == aspirin.info.smiles


def test_search_invalid_metric(aspirin):
    with pytest.raises(NotImplementedError):
        aspirin.search(library=[], metric="cosine")


def test_search_invalid_fingerprint(aspirin):
    with pytest.raises(NotImplementedError):
        aspirin.search(library=[], using="otherfp")
