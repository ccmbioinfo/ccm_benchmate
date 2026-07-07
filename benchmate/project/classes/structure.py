import os
import io
from hashlib import md5

from sqlalchemy import select, insert
from sqlalchemy.exc import NoResultFound

from benchmate.structure.utils import *
from benchmate.structure.structure import Structure as BaseStructure, StructureInfo
from biotite.structure.io.pdb import PDBFile

from benchmate.utils.general_utils import DataIntegrityError

class Structure(BaseStructure):
    """
    a subclass to make structures compatible with project instances
    """
    def __init__(self, config, name, atoms, annotations):
        """
        :param config: structure section of the config file
        :param name: name of the structure
        :param atoms: biotite atom array
        :param annotations: associated annotations
        """
        self.config = config
        self._pdbs()
        super().__init__(name, atoms, annotations)


    def _pdbs(self):
        """
        create a structure folder so that all the available pdbs can be saved and queried via folddisco
        :return:
        """
        os.makedirs(self.config["pdb_path]"], exist_ok=True)

    def to_kb(self, project):
        """
        send a structure instance to project database
        :param project: project class instance
        :return: structure id
        """
        structure_table = project.kb.db_tables["structure"]

        # 1. Convert AtomArray -> PDB text
        pdb_file = PDBFile()
        pdb_file.set_structure(self.info.atoms)
        buf = io.StringIO()
        pdb_file.write(buf)
        pdb_text = buf.getvalue()

        # after you build pdb_text as a str, convert to bytes
        pdb_bytes = pdb_text.encode("utf-8")

        # 2. Build row data (atoms as TEXT) in a dictionary
        row_data = {
            "project_id": project.id,
            "name": self.name,
            "chains": self.info.chains,
            "atoms": pdb_bytes,  # plain text, no gzip
            "annotations": self.info.annotations,
            "hash":md5(pdb_bytes).hexdigest(),
        }
        # insert into structure table
        stmt = structure_table.insert().values(**row_data).returning(structure_table.c.id)
        result = project.session.execute(stmt)[0]
        project.session.commit()

        return result

    @classmethod
    def from_kb(cls, project, id):
        """
        create a structure instance from a kb id
        :param project: project class instance
        :param id: id of the structure
        :return: structure instance
        """
        structure_table = project.kb.db_tables["structure"]
        stmt = select(structure_table).where(structure_table.c.id == id)

        results = project.kb.session.execute(stmt).fetchall()

        if len(results) == 0:
            raise NoResultFound(f"Could not find a molecule with id {id}")
        if len(results) > 1:
            raise DataIntegrityError(f"Found more than one molecule with id {id}")

        # the first row
        row = results[0]._mapping

        name = row["name"]
        chains = row["chains"]

        # pdb pay load from the to_kb
        atoms_blob = row["atoms"]
        annotations = row["annotations"]

        # ran into attribute errors, memoryview to bytes , if bytes decode to utf- 8, crash if anything else
        if isinstance(atoms_blob, memoryview):
            atoms_blob = atoms_blob.tobytes()
        elif isinstance(atoms_blob, str):
            atoms_text = atoms_blob
        elif isinstance(atoms_blob, bytes):
            atoms_text = atoms_blob.decode("utf-8")
        else:
            raise TypeError(f"Unexpected atoms type: {type(atoms_blob)}")

        if not isinstance(atoms_blob, str):
            atoms_text = atoms_blob.decode("utf-8")

        # rebuild biotite struct
        buf = io.StringIO(atoms_text)
        pdb_file = PDBFile.read(buf)
        atom_array = pdb_file.get_structure(model=1)
        return cls(name, atom_array, annotations)

    @classmethod
    def structure_from_file(cls, config, name, file, source, destination, id):
        """
        create a structure from a file same as structure.from file different name to avoid overwriting
        :param config: structure section of the config file
        :param name: name of the structure
        :param file: pdb or cif file
        :param source: source (if no file is there will be downloaded from afdb or pdb)
        :param destination: where to download it
        :param id: the (for downloading)
        :return: a structure instance
        """
        if file is not None:
            if not os.path.exists(file):
                raise FileNotFoundError(f"File not found: {file}")

            structure=super().from_file(name, file, source, destination, id)

        if file is None and id is not None:
            file=os.path.abspath(download(id, source, destination))
            structure = super().from_file(file)

        if file is None and id is None:
            raise ValueError("You must provide a file or an id as well as a source and destination")

        return cls(config, name, structure)