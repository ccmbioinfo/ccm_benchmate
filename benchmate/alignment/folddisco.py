import subprocess
import os
import tempfile
from typing import Union, List, Dict, Optional

import pandas as pd
from benchmate.alignment.utils import find_root_name

class FoldDisco:
    """
    Wrapper class for folddisco structure search
    """
    def __init__(self, folddisco_bin: str = "folddisco"):
        """
        Initialize the wrapper.
        :param folddisco_bin: the path to the folddisco binary, if you are using conda this is just folddisco as
        it will be in your $PATH
        """
        self.folddisco_bin = folddisco_bin
        self._check_folddisco()
        self.local_databases = []

    def find_local_databases(self, folder):
        """
        This is hacky because I do not know a way to check if this is compatible with the program
        :param folder: folder to search for
        :return: nothing, but updates self.local_databases list
        """
        names=find_root_name(folder)
        db_locations=[]
        for name in names:
            location=os.path.join(folder, name)
            db_locations.append(location)
        self.local_databases.extend(db_locations)

    def create_index(
        self,
        pdb_dir: str,
        db_path: str,
        db_name: str,
        extra_args: Optional[Union[List[str], Dict[str, str]]] = None,
        tmp_dir: Optional[str] = None
    ) -> str:
        """
        Index a folder of pbds to be used with folddisco.
        :param pdb_dir: the path to the pdb folder
        :param db_path: the path to the db folder, this is where the indices will be
        :param extra_args: the extra arguments to pass to the folddisco binary
        :param tmp_dir: the tmp directory to use
        """
        db_path = os.path.join(db_path, db_name)
        if not os.path.isdir(pdb_dir):
            raise NotADirectoryError(f"Input directory not found: {pdb_dir}")

        if os.path.exists(db_path):
            raise FileExistsError(f"Database path already exists: {db_path}")

        os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)

        with tempfile.TemporaryDirectory(dir=tmp_dir) as tmp:
            cmd = ["index", "-p", pdb_dir, "-i", db_path]

            cmd += self._process_extra_args(extra_args)
            self._run_folddisco(cmd, check=True)

        print(f"Files indexed in: {db_path}")
        return db_path

    def search(self, structure, query_residues, target_db, extra_args=None):
        """
        search and exisiting folddisco database
        :param structure: a benchmate.structure.Structure object
        :param query_residues: a dict of chain:[residues], if you leave this blank the whole structure will be searched
        :param target_db: the database to search
        :param extra_args: additional args passed to folddisco query
        :return: pandas DataFrame of search results
        """
        if not os.path.exists(target_db):
            raise FileNotFoundError(f"Target database not found: {target_db}")

        query_str = None
        if query_residues is not None:
            query = []
            for chain, residues in query_residues.items():
                if hasattr(structure, "info") and hasattr(structure.info, "chains") and chain not in structure.info.chains:
                    raise ValueError(f"Chain {chain} not found in structure.info")
                for res in residues:
                    query.append(f"{chain}{res}")
            query_str = ",".join(query)
            
        with tempfile.TemporaryDirectory() as tmp:
            struct_name = getattr(structure, "name", "query")
            f = os.path.join(tmp, f"{struct_name}.pdb")
            if hasattr(structure, "write"):
                structure.write(f)
            elif isinstance(structure, str) and os.path.isfile(structure):
                f = structure
            else:
                raise ValueError("structure must be a Structure object or PDB file path")

            command = ["query", "-p", f, "-i", target_db, "--header"]
            if query_str is not None:
                command.extend(["-q", query_str])

            if extra_args:
                command += self._process_extra_args(extra_args)

            run = self._run_folddisco(command, capture_output=True, text=True)
            if run.returncode != 0:
                raise RuntimeError(f"folddisco query failed: {run.stderr}")

            stdout = run.stdout.strip()
            if not stdout:
                return pd.DataFrame()

            lines = [line.split("\t") for line in stdout.splitlines()]
            header = lines[0]
            data = lines[1:]
            return pd.DataFrame(data, columns=header)

    def _check_folddisco(self):
        """
        check if when you run folddisco binary do you actually get a response
        :return:
        """
        result = subprocess.run([self.folddisco_bin, "version"], capture_output=True, text=True)
        if result.returncode != 0:
            raise EnvironmentError(f"FoldDisco not found or not working: {self.folddisco_bin}")

    def _run_folddisco(self, args: List[str], **kwargs) -> subprocess.CompletedProcess:
        """Run folddisco command and return result."""
        cmd = [self.folddisco_bin] + args
        return subprocess.run(cmd, **kwargs)

    def _process_extra_args(self, extra_args) -> List[str]:
        """
        process extra arguments that will be passed to the folddisco binary
        :param extra_args: a bunch of extra arguments passed as a list of strings
        :return: a list of strings that will be passed to the folddisco binary
        """
        if extra_args is None:
            return []
        elif isinstance(extra_args, dict):
            return [str(item) for k, v in extra_args.items() for item in (f"--{k}", str(v))]
        elif isinstance(extra_args, (list, tuple)):
            return [str(x) for x in extra_args]
        else:
            raise TypeError("extra_args must be dict or list/tuple")


