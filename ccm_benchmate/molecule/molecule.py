
from rdkit import Chem
import numpy as np
from usearch_molecules.dataset import FingerprintedDataset, shape_ecfp4, shape_fcfp4, shape_maccs

from ccm_benchmate.structure.structure import Structure


class Molecule:
    """
    Molecule class to represent chemical structures using SMILES or InChI. this will include methods for different property
    calculations and structure comparisons using usearch molecules.
    """
    def __init__(self, smiles=None, bound_structure=None, fingerprint_dim=2048, radius=2):
        """
        Initialize a Molecule object with a SMILES string.
        :param smiles: A SMILES or InChI representation of the molecule.
        :param bound_structure: A bound strcutre this is a pdb it will become a strcture object upon loading
        """
        self.smiles = smiles
        self.mol = Chem.MolFromSmiles(smiles)
        if bound_structure is not None:
            self.bound_structure = Structure(pdb=bound_structure)
        else:
            self.bound_structure=None
        self.fingerprint_dim = fingerprint_dim
        self.fingerprint_radius=radius
        self.ecfp4 = self._fingerprint(type="ecfp4")
        self.fcfp4 = self._fingerprint(type="fcfp4")
        self.maccs = self._fingerprint(type="maccs")


    def _fingerprint(self, type="ecfp4"):
        if type == "ecfp4":
            fpgen = Chem.rdFingerprintGenerator.GetMorganGenerator(radius=self.fingerprint_radius,
                                                                   fpSize=self.fingerprint_dim,
                                                                   atomInvariantsGenerator=Chem.rdFingerprintGenerator.GetMorganAtomInvGen())
            fp = fpgen.GetFingerprint(self.mol)
        elif type == "fcfp4":
            fpgen=Chem.rdFingerprintGenerator.GetMorganGenerator(radius=self.fingerprint_radius,
                fpSize=self.fingerprint_dim,
                atomInvariantsGenerator=Chem.rdFingerprintGenerator.GetMorganFeatureAtomInvGen())
            fp = fpgen.GetFingerprint(self.mol)
        elif type == "maccs":
            fp=Chem.MACCSkeys.GenMACCSKeys(self.mol)
        else:
            raise NotImplementedError("Only ecfp4, fcfp4 and maccs fingerprints are implemented")

        return fp


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

        data = FingerprintedDataset(library, shape=shape)
        results = data.search(smiles=self.smiles, n=n)
        return results

    def bounding_box(self, amino_acids=None, use_alpha_carbon=False):
            """
            generate a bounding box around a given list of amino acid ids. This can be used to generate more molecules or
            calculate properties of a pocket
            :param use: target or bound structure, this needs to be a Structure instance
            :param amino_acids: which amino acids to use
            :param use_alpha_carbon: whether to use the alpha carbon or the side chains to get the bounding box
            :return: 6 coordinates of the bounding box
            """

            if self.bound_sturcutre is None:
                raise ValueError("bound_sturcutre must be set for bounding box calculation")

            coord = []

            for model in self.bound_structure:
                for chain in model:
                    for residue in chain:
                        if amino_acids is None or residue.resname in amino_acids:
                            for atom in residue:
                                if use_alpha_carbon:
                                    if atom.name == "CA":
                                        coord.append(atom.coord)
                                else:
                                    coord.append(atom.coord)

            coord_numpy = np.array(coord)

            x_max, y_max, z_max = np.max(coord_numpy, axis=0)
            x_min, y_min, z_min = np.min(coord_numpy, axis=0)

            return {"xmax": x_max, "ymax": y_max, "zmax": z_max, "xmin": x_min, "ymin": y_min, "zmin": z_min}



    def __repr__(self):
        return f"Molecule(smiles={self.smiles}, InChI={self.InChI})"

    def __str__(self):
        return f"Molecule with SMILES: {self.smiles} and InChI: {self.InChI}"






