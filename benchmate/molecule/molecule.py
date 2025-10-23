from dataclasses import dataclass
from typing import Optional

from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem.rdFingerprintGenerator import GetMorganGenerator, GetMorganFeatureAtomInvGen

from benchmate.molecule.utils import *

@dataclass
class MoleculeInfo:
    name: str
    smiles: str
    mol: Chem.rdchem.Mol = None
    fingerprint_dim: int = 2048
    fingerprint_radius: int = 2
    ecfp4: Optional[np.ndarray] = None
    fcfp4: Optional[np.ndarray] = None
    maccs: Optional[np.ndarray] = None
    inchikey: Optional[str] = None
    properties: Optional[dict] = None


class Molecule:
    """
    Molecule class to represent chemical structures using SMILES or InChI. this will include methods for different property
    calculations and structure comparisons using usearch molecules.
    """
    def __init__(self, name, smiles, fingerprint_dim=2048, radius=2):
        """

        :param name:
        :param smiles:
        :param fingerprint_dim:
        :param radius:
        """
        self.info=MoleculeInfo(name=name, smiles=smiles)
        self.info.mol = Chem.MolFromSmiles(smiles)
        self.info.fingerprint_dim = fingerprint_dim
        self.info.fingerprint_radius=radius
        self.info.ecfp4 = self._fingerprint(type="ecfp4")
        self.info.fcfp4 = self._fingerprint(type="fcfp4")
        self.info.maccs = self._fingerprint(type="maccs")
        self.info.inchi = self.inchikey()
        self.info.properties = self._properties()

    def search(self, library, n=10, metric="tanimoto", using="ecfp4"):
        """
        Search for similar molecules in a given library using a specified fingerprinting method.
        :param library: The dataset to search within.
        :param n: Number of similar molecules to return.
        :param metric: Similarity metric to use (default is "tanimoto").
        :param using: Fingerprint type to use (default is "ecfp4").
        :return: A list of similar molecules from the library.
        """
        if metric != "tanimoto":
            raise NotImplementedError("metric must be tanimoto")

        if using not in ["ecfp4", "fcfp4", "maccs"]:
            raise NotImplementedError("method must be ecfp4 or fcfp4 or maccs")
        elif using == "ecfp4":
            shape = shape_ecfp4
        elif using == "fcfp4":
            shape = shape_fcfp4
        elif using == "maccs":
            shape = shape_maccs

        data = FingerprintedDataset(library, shapes=shape)
        results = data.search(smiles=self.info.smiles, n=n)
        return results

    def similarity(self, other, fingerprint):
        if not isinstance(other, Molecule):
            raise ValueError("other must be an instance of Molecule")

        if fingerprint=="ecfp4":
            return tanimoto(self.info.ecfp4, other.info.ecfp4)
        elif fingerprint=="fcfp4":
            return tanimoto(self.info.fcfp4, other.info.fcfp4)
        elif fingerprint=="maccs":
            return tanimoto(self.info.maccs, other.info.maccs)
        else:
            raise NotImplementedError("method must be ecfp4 or fcfp4 or maccs")


    def _fingerprint(self, type="ecfp4"):
        if type=="maccs":
            return rdMolDescriptors.GetMACCSKeysFingerprint(self.info.mol)
        elif type=="fcfp4":
            fcfp_invariants = GetMorganFeatureAtomInvGen()
            fcfp_generator = GetMorganGenerator(radius=2, fpSize=2048, atomInvariantsGenerator=fcfp_invariants)
            return fcfp_generator.GetFingerprint(self.info.mol)
        elif type=="ecfp4":
            ecfp_generator = GetMorganGenerator(radius=2, fpSize=2048)
            return ecfp_generator.GetFingerprint(self.info.mol)
        else:
            raise NotImplementedError("Only ecfp4, fcfp4 and maccs fingerprints are implemented")

        return fp.ToList()

    def _properties(self):
        """
        calculate all the descriptors that rdkit can mange and return a dictionary of them
        :return: a dictionary of properties
        """
        props=Chem.Descriptors.CalcMolDescriptors(self.info.mol)
        return props

    def inchikey(self) -> str:
        return Chem.inchi.MolToInchiKey(self.info.mol)

    def __hash__(self):
        return hash(self.inchikey())

    def __eq__(self, other):
        return isinstance(other, Molecule) and self.inchikey() == other.inchikey()

    def __repr__(self):
        return f"Molecule(name={self.info.name}, smiles={self.info.smiles})"

    def __str__(self):
        return f"Molecule(name={self.info.name}, smiles={self.info.smiles})"

    def __ne__(self, other):
        if not isinstance(other, Molecule):
            return True
        elif self == other:
            return False
        else:
            return True








