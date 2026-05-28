from dataclasses import dataclass
from typing import Optional, Any

from sqlalchemy import select, insert
from sqlalchemy.exc import NoResultFound

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import Descriptors
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem.rdFingerprintGenerator import GetMorganGenerator, GetMorganFeatureAtomInvGen
from rdkit.DataStructs.cDataStructs import CreateFromBitString


from benchmate.utils.general_utils import DataIntegrityError
from benchmate.molecule.utils import *


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

    def to_kb(self, project):
        molecule_table = project.kb.db_tables["molecule"]

        stmt = (molecule_table.insert().values(
                project_id=project.project_id,
                name=self.name,
                smiles=self.smiles,
                fingerprint_dim=self.fingerprint_dim,
                fingerprint_radius=self.fingerprint_radius,
                ecfp4=self.ecfp4,
                fcfp4=self.fcfp4,
                maccs=self.maccs,
                inchikey=self.inchikey,
                properties=self.properties,
                annotations=self.features,
            )
            .returning(molecule_table.c.id)
        )

        result = project.kb.session().execute(stmt)
        mol_id = result.scalar_one()
        project.kb.session().commit()

        return mol_id

    @classmethod
    def from_kb(cls, project, id):
        molecule_table = project.kb.db_tables["molecule"]

        stmt = (
            select(
                molecule_table.c.name,
                molecule_table.c.smiles,
                molecule_table.c.fingerprint_dim,
                molecule_table.c.fingerprint_radius,
                molecule_table.c.ecfp4,
                molecule_table.c.fcfp4,
                molecule_table.c.maccs,
                molecule_table.c.inchikey,
                molecule_table.c.properties,
                molecule_table.c.annotations,
            )
            .where(molecule_table.c.id == id)
        )

        results = project.kb.session().execute(stmt).fetchall()

        if len(results) == 0:
            raise NoResultFound(f"Could not find a molecule with id {id}")

        if len(results) > 1:
            raise DataIntegrityError(f"Found more than one molecule with id {id}")

        row = results[0]

        info = cls(
            name=row[0],
            smiles=row[1],
            fingerprint_dim=row[2],
            fingerprint_radius=row[3],
            ecfp4=row[4],
            fcfp4=row[5],
            maccs=row[6],
            inchi=row[7],
            properties=row[8],
            features=row[9],
        )

        # restore RDKit mol
        info.mol = Chem.MolFromSmiles(info.smiles)

        return info

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

    @classmethod
    def from_kb(cls, project, id):
        info=MoleculeInfo.from_kb(project, id)
        molecule=cls(name=info.name, smiles=info.smiles, fingerprint_dim=info.fingerprint_dim,
                          radius=info.fingerprint_radius)
        molecule.info=info
        return molecule

    def to_kb(self, project):
        return self.info.to_kb(project)
