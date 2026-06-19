from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from benchmate.utils.general_utils import DataIntegrityError

from rdkit import Chem
from benchmate.molecule.molecule import Molecule as BaseMolecule
from molecule.molecule import MoleculeInfo



class Molecule(BaseMolecule):
    def __init__(self, config, name, smiles):
        self.fingerprint_dim=config["fingerprint_dim"]
        self.fingerprint_radius=config["fingerprint_radius"]
        super().__init__(name, smiles, self.fingerprint_dim, self.fingerprint_radius)

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

        info = MoleculeInfo(
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
        molecule = cls(name=info.name, smiles=info.smiles)
        molecule.info = info
        return molecule

    def to_kb(self, project):
        molecule_table = project.kb.db_tables["molecule"]

        stmt = (molecule_table.insert().values(
                project_id=project.project_id,
                name=self.info.name,
                smiles=self.info.smiles,
                fingerprint_dim=self.info.fingerprint_dim,
                fingerprint_radius=self.info.fingerprint_radius,
                ecfp4=self.info.ecfp4,
                fcfp4=self.info.fcfp4,
                maccs=self.info.maccs,
                inchikey=self.info.inchikey,
                properties=self.info.properties,
                annotations=self.info.features,
            )
            .returning(molecule_table.c.id)
        )

        result = project.kb.session().execute(stmt)
        mol_id = result.scalar_one()
        project.kb.session().commit()

        return mol_id
