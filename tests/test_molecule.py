import pytest
from rdkit import Chem

from benchmate.molecule.molecule import Molecule, MoleculeInfo
from benchmate.molecule.utils import tanimoto


@pytest.fixture
def aspirin():
    return Molecule(name="aspirin", smiles="CC(=O)OC1=CC=CC=C1C(=O)O")


@pytest.fixture
def benzoic_acid():
    return Molecule(name="benzoic acid", smiles="C1=CC=C(C=C1)C(=O)O")


def test_molecule_initialization(aspirin):
    assert isinstance(aspirin.info.mol, Chem.Mol)
    assert aspirin.info.name == "aspirin"
    assert aspirin.info.smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"
    assert isinstance(aspirin.info.ecfp4, str)
    assert isinstance(aspirin.info.fcfp4, str)
    assert isinstance(aspirin.info.maccs, str)
    assert isinstance(aspirin.info.inchi, str)
    assert len(aspirin.info.inchi) > 0


def test_repr_and_str(aspirin):
    assert "aspirin" in str(aspirin)
    assert "aspirin" in repr(aspirin)


def test_equality(aspirin, benzoic_acid):
    same = Molecule("same_aspirin", "CC(=O)OC1=CC=CC=C1C(=O)O")
    assert aspirin == same
    assert aspirin != benzoic_acid
    assert aspirin != "not a molecule"


def test_hash(aspirin):
    m_set = {aspirin}
    same = Molecule("same_aspirin", "CC(=O)OC1=CC=CC=C1C(=O)O")
    assert same in m_set


def test_properties(aspirin):
    props = aspirin.info.properties
    assert isinstance(props, dict)
    assert "MolWt" in props
    assert props["MolWt"] > 0


def test_fingerprints_and_similarity(aspirin, benzoic_acid):
    same = Molecule("same_aspirin", "CC(=O)OC1=CC=CC=C1C(=O)O")

    sim_ecfp4 = aspirin.similarity(same, "ecfp4")
    assert pytest.approx(sim_ecfp4) == 1.0

    sim_fcfp4 = aspirin.similarity(same, "fcfp4")
    assert pytest.approx(sim_fcfp4) == 1.0

    sim_maccs = aspirin.similarity(same, "maccs")
    assert pytest.approx(sim_maccs) == 1.0

    diff_sim = aspirin.similarity(benzoic_acid, "ecfp4")
    assert 0.0 <= diff_sim < 1.0

    with pytest.raises(ValueError):
        aspirin.similarity("not_a_mol", "ecfp4")

    with pytest.raises(NotImplementedError):
        aspirin.similarity(same, "invalid_fp")


def test_invalid_fingerprint_type(aspirin):
    with pytest.raises(NotImplementedError):
        aspirin._fingerprint(type="invalid")


def test_generate_conformers(aspirin):
    mol_h, conformers = aspirin.generate_conformers(n=3, prune_thres=0.5, optimize_geom=False)
    assert isinstance(mol_h, Chem.Mol)
    assert isinstance(conformers, list)
    assert len(conformers) > 0


def test_tanimoto_utils():
    import numpy as np
    a = np.array([1, 1, 0, 0])
    b = np.array([1, 0, 0, 0])
    # ands = 1, ors = 2 -> 1/2 = 0.5
    assert tanimoto(a, b) == 0.5
    assert tanimoto(a, a) == 1.0
    assert tanimoto(None, a) == 0.0
