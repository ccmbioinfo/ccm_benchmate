from dataclasses import dataclass
from typing import Optional, Any



from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import Descriptors
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem.rdFingerprintGenerator import GetMorganGenerator, GetMorganFeatureAtomInvGen
from rdkit.DataStructs.cDataStructs import CreateFromBitString

from benchmate.molecule.utils import tanimoto


@dataclass(slots=True)
class MoleculeInfo:
    name: str
    smiles: str
    mol: Chem.rdchem.Mol = None
    fingerprint_dim: int = 2048
    fingerprint_radius: int = 2

    ecfp4: Optional[str] = None
    fcfp4: Optional[str] = None
    maccs: Optional[str] = None


    _ecfp4_fp: Optional[Any] = None
    _fcfp4_fp: Optional[Any] = None
    _maccs_fp: Optional[Any] = None


    inchi: Optional[str] = None
    properties: Optional[dict] = None
    features: Optional[dict] = None

    def get_ecfp4_fp(self):
        if self._ecfp4_fp is None and self.ecfp4:
            self._ecfp4_fp = CreateFromBitString(self.ecfp4)
        return self._ecfp4_fp


    def get_fcfp4_fp(self):
        if self._fcfp4_fp is None and self.fcfp4:
            self._fcfp4_fp = CreateFromBitString(self.fcfp4)
        return self._fcfp4_fp


    def get_maccs_fp(self):
        if self._maccs_fp is None and self.maccs:
            self._maccs_fp = CreateFromBitString(self.maccs)
        return self._maccs_fp


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
        self.info = MoleculeInfo(name=name, smiles=smiles)
        self.info.mol = Chem.MolFromSmiles(smiles)
        self.info.fingerprint_dim = fingerprint_dim
        self.info.fingerprint_radius = radius

        ecfp4_fp, ecfp4_str = self._fingerprint("ecfp4")
        fcfp4_fp, fcfp4_str = self._fingerprint("fcfp4")
        maccs_fp, maccs_str = self._fingerprint("maccs")

        self.info.ecfp4 = ecfp4_str
        self.info.fcfp4 = fcfp4_str
        self.info.maccs = maccs_str

        self.info._ecfp4_fp = ecfp4_fp
        self.info._fcfp4_fp = fcfp4_fp
        self.info._maccs_fp = maccs_fp

        self.info.inchi = self.inchikey()
        self.info.properties = self._properties()

    #TODO disabling this for now until I decide what to do with it, this is a big dependency and not sure if we need it
    # def search(self, library, n=10, metric="tanimoto", using="ecfp4"):
    #     """
    #     Search for similar molecules in a given library using a specified fingerprinting method.
    #     :param library: The dataset to search within.
    #     :param n: Number of similar molecules to return.
    #     :param metric: Similarity metric to use (default is "tanimoto").
    #     :param using: Fingerprint type to use (default is "ecfp4").
    #     :return: A list of similar molecules from the library.
    #     """
    #     if metric != "tanimoto":
    #         raise NotImplementedError("metric must be tanimoto")
    #
    #     if using not in ["ecfp4", "fcfp4", "maccs"]:
    #         raise NotImplementedError("method must be ecfp4 or fcfp4 or maccs")
    #     elif using == "ecfp4":
    #         shape = shape_ecfp4
    #     elif using == "fcfp4":
    #         shape = shape_fcfp4
    #     elif using == "maccs":
    #         shape = shape_maccs
    #
    #     data = FingerprintedDataset(library, shapes=shape)
    #     results = data.search(smiles=self.info.smiles, n=n)
    #     return results

    def similarity(self, other, fingerprint):
        """
        get the similarity betweek two molecule instances
        :param other: other molecule instance
        :param fingerprint: what kind of fingerprint to use
        :return: returns the tanimoto similarity between to molecules
        """
        if not isinstance(other, Molecule):
            raise ValueError

        if fingerprint == "ecfp4":
            return tanimoto(self.info.get_ecfp4_fp(), other.info.get_ecfp4_fp())
        elif fingerprint == "fcfp4":
            return tanimoto(self.info.get_fcfp4_fp(), other.info.get_fcfp4_fp())
        elif fingerprint == "maccs":
            return tanimoto(self.info.get_maccs_fp(), other.info.get_maccs_fp())
        else:
            raise NotImplementedError("method must be ecfp4 or fcfp4 or maccs")

    def _fingerprint(self, type="ecfp4"):
        """
        generate the fingerprint and fingerprint bitstring for the molecule, this is done internally
        :param type:
        :return:
        """
        if type == "maccs":
            fp = rdMolDescriptors.GetMACCSKeysFingerprint(self.info.mol)
        elif type == "fcfp4":
            gen = GetMorganGenerator(radius=2, fpSize=2048,
                                     atomInvariantsGenerator=GetMorganFeatureAtomInvGen())
            fp = gen.GetFingerprint(self.info.mol)
        elif type == "ecfp4":
            gen = GetMorganGenerator(radius=2, fpSize=2048)
            fp = gen.GetFingerprint(self.info.mol)
        else:
            raise NotImplementedError

        return fp, fp.ToBitString()

    def _properties(self):
        """
        calculate all the descriptors that rdkit can mange and return a dictionary of them
        :return: a dictionary of properties
        """
        props = Chem.Descriptors.CalcMolDescriptors(self.info.mol)
        return props

    def generate_conformers(self, n, prune_thres=0.5, optimize_geom=True):
        """
        generate conformers
        :param n: number of conformers to try to generate, based on pruning they number can be smalled
        :param prune_thres: remove any conformer that has this much rmsd or less. So lower values will give more conformers
        :param optimize_geom: whether to optimize the geometry, this will also get rid of some comformers
        :return: returns a hydrogenated mol with all the conformers that you can get with mol.GetConformers(<conformer_id>) and a list of ids
        """
        params = AllChem.ETKDGv3()
        params.pruneRmsThresh = prune_thres

        mol_h = Chem.AddHs(self.info.mol)
        conformers = AllChem.EmbedMultipleConfs(mol_h, numConformers=n, params=params)
        if optimize_geom:
            AllChem.MMFFOptimizeMoleculeConfs(mol_h)

        return mol_h, list(conformers)

    def inchikey(self) -> str:
        """
        generate the inchi key for the molecule
        :return: inchikey
        """
        return Chem.inchi.MolToInchiKey(self.info.mol)

    def __hash__(self):
        return hash(self.inchikey())

    def __eq__(self, other):
        """
        using inchi key because the molecules might not be in canonical smiles, it's not perfect but close
        """
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

