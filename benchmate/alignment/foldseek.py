import subprocess
import os
import tempfile
import shutil
from typing import Union, List, Dict, Optional

import pandas as pd
import benchmate.structure.structure

from benchmate.alignment.utils import find_root_name


class FoldSeek:
    """
    A Python wrapper for FoldSeek with support for:
    - Querying PDB structures (single or directory) against a database → A3M + TSV output
    - Creating FoldSeek databases (standard or GPU-padded)
    - GPU acceleration (if DB supports it)
    - Flexible extra arguments
    """

    def __init__(self, foldseek_bin: str = "foldseek"):
        """
        :param foldseek_bin: Path to the FoldSeek executable (default: assumes in PATH)
        """
        self.foldseek_bin = foldseek_bin
        self._check_foldseek()
        self.local_databases=[]

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

    def create_database(
        self,
        pdb_dir: str,
        db_path: str,
        db_name: str,
        gpu_padded: bool = False,
        extra_args: Optional[Union[List[str], Dict[str, str]]] = None,
        tmp_dir: Optional[str] = None
    ) -> str:
        """
        Create a FoldSeek database from a directory of PDB/CIF files.
        :param pdb_dir: path to PDB/CIF file
        :param db_path: path to FoldSeek database
        :param gpu_padded, If True create padded db
        :param extra_args: extra arguments passed to FoldSeek
        :param tmp_dir: Custom temporary directory
        :return: path to the created FoldSeek database
        """
        db_path = os.path.join(db_path, db_name)
        if not os.path.isdir(pdb_dir):
            raise NotADirectoryError(f"Input directory not found: {pdb_dir}")

        if os.path.exists(db_path):
            raise FileExistsError(f"Database path already exists: {db_path}")

        os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)

        with tempfile.TemporaryDirectory(dir=tmp_dir) as tmp:
            cmd = ["createdb", pdb_dir, db_path]

            if gpu_padded:
                cmd += ["--pad-db"]

            cmd += self._process_extra_args(extra_args)
            self._run_foldseek(cmd, check=True)

        print(f"Database created: {db_path}")
        return db_path

    def pad_db(self, old_db, new_db, **kwargs):
        """
        create a padded db from an exising one
        :param old_db: old db to pad
        :param new_db: new db path
        :return the path of the new db if all goes well
        """
        db_args = [
            "makepaddedseqdb",
            old_db,
            new_db
        ]

        db_args += self._process_extra_args(kwargs)
        self._run_foldseek(db_args, check=True)
        return new_db

    def search(
        self,
        structure: Union[benchmate.structure.structure.Structure, str],
        target_db: str,
        output_a3m: str,
        output_tsv: str,
        use_gpu: bool = False,
        sensitivity: float = 7.5,
        max_accept: int = 100000,
        evalue: float = 1e-3,
        extra_search_args: Optional[Union[List[str], Dict[str, str]]] = None,
        extra_result2msa_args: Optional[Union[List[str], Dict[str, str]]] = None,
        tmp_dir: Optional[str] = None
    ):
        """
        :param structure: a benchmate structure object or path to PDB file
        :param target_db: FoldSeek database to search against
        :param output_a3m: Output A3M file path
        :param output_tsv: Output TSV file path
        :param use_gpu: Enable GPU (FoldSeek will error if DB not padded or no GPU)
        :param sensitivity: Search sensitivity (higher = slower, more sensitive)
        :param max_accept: Maximum number of alignments to accept
        :param evalue: E-value threshold
        :param extra_search_args: Extra args for `search`
        :param extra_result2msa_args: Extra args for `result2msa`
        :param tmp_dir: Custom temporary directory
        """
        # Create temporary working directory
        work_dir = tempfile.mkdtemp(dir=tmp_dir)
        try:
            if hasattr(structure, "write"):
                query_pdb_file = os.path.join(work_dir, "query.pdb")
                structure.write(query_pdb_file)
            elif isinstance(structure, str) and os.path.isfile(structure):
                query_pdb_file = structure
            elif hasattr(structure, "info") and getattr(structure.info, "file", None) and os.path.isfile(structure.info.file):
                query_pdb_file = structure.info.file
            else:
                raise ValueError("structure must be a Structure object or valid PDB file path")

            query_db = os.path.join(work_dir, "query_db")
            aligned_db = os.path.join(work_dir, "aligned")
            result_db = os.path.join(work_dir, "result")
            a3m_tmp = os.path.join(work_dir, "result.a3m")

            # Step 1: Create query DB from PDB
            self._run_foldseek(["createdb", query_pdb_file, query_db], check=True)

            # Step 2: Search
            search_args = [
                "search",
                query_db,
                target_db,
                result_db,
                work_dir,
                "--alignment-type",
                "1"
            ]

            # Common search options
            search_args += [
                "-s", str(sensitivity),
                "--max-accept", str(max_accept),
                "-e", str(evalue)
            ]

            if use_gpu:
                search_args += ["--gpu", "1"]

            search_args += self._process_extra_args(extra_search_args)

            # Run search with GPU error handling
            try:
                self._run_foldseek(search_args, check=True)
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr or "")
                if use_gpu and ("GPU" in error_msg or "cuda" in error_msg.lower()):
                    print(f"GPU search failed: {error_msg}")
                    print("Retrying without GPU...")
                    new_args = []
                    idx = 0
                    while idx < len(search_args):
                        if search_args[idx] == "--gpu":
                            idx += 2
                        else:
                            new_args.append(search_args[idx])
                            idx += 1
                    search_args = new_args
                    self._run_foldseek(search_args, check=True)
                else:
                    raise

            self._run_foldseek([
                "align",
                query_db,
                target_db,
                result_db,
                aligned_db,
                "-a"
            ], check=True)

            # Step 3: Convert result to MSA (A3M)
            result2msa_args = [
                "result2msa",
                query_db,
                target_db,
                aligned_db,
                a3m_tmp
            ]
            result2msa_args += self._process_extra_args(extra_result2msa_args)
            self._run_foldseek(result2msa_args, check=True)

            # Step 4: Extract TSV
            self._run_foldseek([
                "convertalis",
                query_db,
                target_db,
                aligned_db,
                output_tsv,
                "--format-output",
                "query,target,fident,alnlen,mismatch,gapopen,qstart,qend,tstart,tend,evalue,bits,qtmscore,ttmscore,alntmscore,rmsd,lddt"
            ], check=True)

            # Step 5: Copy A3M to final output
            if not os.path.exists(a3m_tmp):
                raise FileNotFoundError(f"A3M file not generated: {a3m_tmp}")
            shutil.copy(a3m_tmp, output_a3m)

        finally:
            if not tmp_dir:  # Only remove if we created it
                shutil.rmtree(work_dir, ignore_errors=True)

        return output_a3m, output_tsv

    def easy_search(self, query, target, extra_args: Optional[Union[List[str], Dict[str, str]]] = None):
        """
        run easy search with a pdb file and a fasta of 3dis
        :param query: pdb file
        :param target: directory of pbds
        :param extra_args: Extra args for `easy_search`
        :return: a pandas dataframe of the results
        """

        if not os.path.isfile(query):
            raise FileNotFoundError(f"Query file not found: {query}")

        if not os.path.isdir(target):
            raise FileNotFoundError(f"Target directory not found: {target}")

            # Use a temporary directory that auto-cleans
        with tempfile.TemporaryDirectory() as tmpdir:
            # Output to stdout using "-"
            args = [
                "easy-search",
                query,
                target,
                "-",  # stdout
                tmpdir,
                "--format-mode", "4"
            ]

            args += self._process_extra_args(extra_args)

            run = self._run_foldseek(args, check=False, capture_output=True, text=True)

            if run.returncode != 0:
                raise RuntimeError(run.stderr)

            stdout = run.stdout.strip()
            if not stdout:
                return pd.DataFrame()

            lines = stdout.splitlines()
            header = lines[0].split("\t")
            data = [l.split("\t") for l in lines[1:]]

        df = pd.DataFrame(data, columns=header)
        return df


    def _process_extra_args(self, extra_args) -> List[str]:
            """Convert dict or list of extra args to list of strings."""
            if extra_args is None:
                return []
            elif isinstance(extra_args, dict):
                return [str(item) for k, v in extra_args.items() for item in (f"--{k}", str(v))]
            elif isinstance(extra_args, (list, tuple)):
                return [str(x) for x in extra_args]
            else:
                raise TypeError("extra_args must be dict or list/tuple")

    def _check_foldseek(self):
        """Check if FoldSeek is available."""
        result = subprocess.run([self.foldseek_bin, "version"], capture_output=True, text=True)
        if result.returncode != 0:
            raise EnvironmentError(f"FoldSeek not found or not working: {self.foldseek_bin}")

    def _run_foldseek(self, args: List[str], **kwargs) -> subprocess.CompletedProcess:
        """Run FoldSeek command and return result."""
        cmd = [self.foldseek_bin] + args
        print(f"Running: {' '.join(cmd)}")  # Optional debug
        return subprocess.run(cmd, **kwargs)

    def list_dbs(self):
        """
        List downloadable dbs
        """
        dbs=self._run_foldseek(["databases"], capture_output=True, text=True)
        return dbs.stdout.strip().split("\n")

    def download_db(self, dbname, location, create=False):
        """
        downlooad one of the items from listdbs
        :param dbname: name of the db
        :param location: where to download the db
        :param create: whether to create that directory
        :return: return the path of the downloaded db
        """

        work_dir = tempfile.mkdtemp()

        if not os.path.exists(location) and not create:
            raise NotADirectoryError(f"could not find {location}")

        if not os.path.exists(location) and create:
            os.mkdir(location)

        cmd=["databases", dbname, f"{location}/{dbname}", work_dir]

        try:
            self._run_foldseek(cmd, check=True)
            return f"{location}/{dbname}"
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr or "")
            print(f"Database download failed: {err}")
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

