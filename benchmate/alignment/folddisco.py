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

    def search(self, structure, query_residues, target_db, extra_args=None) -> subprocess.CompletedProcess:
        """
        search and exisiting folddisco database
        :param structure: a benchmate.structure.Structure object
        :param query_residues: a dict of chain:[redisudes], if you leave this blank the whole structure will be searched
        :param target_db: the database to search
        :param kwargs: additional kwargs passed to folddisco query
        :return:
        """
        if not os.path.exists(target_db):
            raise FileNotFoundError(f"Target database not found: {target_db}")

        if query_residues is not None:
            for chain, residues in query_residues.items():
                if chain not in structure.info.chains:
                    raise ValueError(f"Chain {chain} not found in structure.info")
                else:
                    query=[]
                    for res in residues:
                        query.append(f"{chain}{res}")
            query=",".join(query)
            
        with tempfile.TemporaryDirectory() as tmp:
            f=os.path.join(tmp, f"{structure.name}.pdb")
            structure.write(f)
            command=[self.folddisco_bin, "query", "-p", f, "-i", target_db, "--header"]
            if query_residues is not None:
                command.extend(["-q", query])

            if extra_args:
                command+=self._process_extra_args(extra_args)

            run = subprocess.run(command, capture_output=True, text=True, check=True)
            if run.returncode != 0:
                raise RuntimeError(run.stderr)
            else:
                lines=[]
                for idx, line in enumerate(run.stdout.splitlines()):
                    if idx == 0: #the headers
                        header=line.split("\t")
                    else:
                        vals=line.split("\t")
                        lines.append(vals)

            for_df={}
            for col in header:
                for_df[col]=[]

            for line in lines:
                for i in range(len(header)):
                    col=header[i]
                    for_df[col].append(line[i])
            df=pd.DataFrame(for_df)
            return df

    def _check_folddisco(self):
        """
        check if when you run folddisco binary do you actually get a response
        :return:
        """
        result = subprocess.run([self.folddisco_bin, "version"], capture_output=True, text=True)
        if result.returncode != 0:
            raise EnvironmentError(f"FoldDisco not found or not working: {self.folddisco_bin}")

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


