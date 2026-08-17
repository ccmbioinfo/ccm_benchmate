import logging
import subprocess
import os
import tempfile
import shutil
from typing import Union, List, Dict, Optional


import benchmate.sequence.sequence
from benchmate.alignment.utils import *

logger = logging.getLogger(__name__)


class MMSeqs:
    """
    Corrected MMseqs2 wrapper:
    - Always creates query DB via `createdb`
    - Supports single and paired alignment (`pairaln`)
    - GPU with padded DB
    - Flexible extra args
    """

    def __init__(self, mmseqs_bin: str = "mmseqs"):
        """
        initialize the class
        :param mmseqs_bin: the path to the binary if it's not in your $PATH
        """
        self.mmseqs_bin = mmseqs_bin
        self._check_mmseqs()
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

    def create_database(
        self,
        fasta_path: str,
        db_path: str,
        db_name: str,
        gpu_padded: bool = False,
        extra_args: Optional[Union[List[str], Dict[str, str]]] = None,
    ) -> str:
        """
        Create a new database from a fasta file
        :param fasta_path: path to the fasta file
        :param db_path: path to the database
        :param db_name: name of the database
        :param gpu_padded: whether to pad it for gpu compatbility
        :param extra_args: other args to pass to the binary see mmseqs documentation
        :return: the path of the binary
        """
        db_path = os.path.join(db_path, db_name)
        if os.path.exists(db_path):
            raise FileExistsError(f"Database exists: {db_path}")

        os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)

        cmd = ["createdb", fasta_path, db_path]
        if gpu_padded:
            cmd += ["--pad-db"]
        cmd += self._process_extra_args(extra_args)

        self._run_mmseqs(cmd, check=True)
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
        self._run_mmseqs(db_args, check=True)
        return new_db

    def search(
        self,
        query: Union[benchmate.sequence.sequence.Sequence, benchmate.sequence.sequence.SequenceList],
        target_db: str,
        output_a3m: str,
        output_tsv: str,
        use_gpu: bool = False,
        sensitivity: float = 5.7,
        max_seqs: int = 1000,
        evalue: float = 1e-3,
        extra_search_args: Optional[Union[List[str], Dict[str, str]]] = None,
        extra_result2msa_args: Optional[Union[List[str], Dict[str, str]]] = None,
        tmp_dir: Optional[str] = None
    ):
        """
        Perform a search on a query sequence, this is the full search pipeline not easy-search
        :param query: query fasta
        :param target_db: which database to search
        :param output_a3m: where to write the a3m file
        :param output_tsv: where to write the tsv file
        :param use_gpu: whether to use gpu, this does not check if there is a gpu available or the database is compatible
        :param sensitivity: sensitivity of the search default 5.7
        :param max_seqs: max number of sequences to return default 1000
        :param evalue: e value cutoff default: 1e-3
        :param extra_search_args: extra arguments to search
        :param extra_result2msa_args: extra arguments to results2msa
        :param tmp_dir: where to put the temp files, if none will use a tempfile
        :return: paths to the generated files
        """
        if not isinstance(query, (benchmate.sequence.sequence.Sequence, benchmate.sequence.sequence.SequenceList)):
            raise TypeError("Query must be a Sequence or SequenceList instance.")

        if isinstance(query, benchmate.sequence.sequence.SequenceList) and len(query) > 1:
            is_paired = True
        else:
            is_paired = False

        work_dir = tempfile.mkdtemp(dir=tmp_dir)

        try:
            # Paths
            query_fasta = os.path.join(work_dir, "query.fasta")
            query_db = os.path.join(work_dir, "query_db")
            result_db = os.path.join(work_dir, "result")
            a3m_tmp = os.path.join(work_dir, "result.a3m")

            # Step 1: Write query FASTA
            query.to_fasta(query_fasta)

            # Step 2: Create query DB
            self._run_mmseqs(["createdb", query_fasta, query_db], check=True)

            # Step 3: Search or Pairaln
            search_args = [
                "search",
                query_db,
                target_db,
                result_db,
                work_dir
            ]
            search_args += [
                "--max-seqs", str(max_seqs),
                "-s", str(sensitivity),
                "-e", str(evalue)
            ]

            if use_gpu:
                search_args += ["--gpu", "1"]

            search_args += self._process_extra_args(extra_search_args)

            try:
                self._run_mmseqs(search_args, check=True)
            except subprocess.CalledProcessError as e:
                err = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr or "")
                if use_gpu and ("GPU" in err or "cuda" in err.lower()):
                    logger.warning(f"GPU failed: {err}\nRetrying on CPU...")
                    new_args = []
                    idx = 0
                    while idx < len(search_args):
                        if search_args[idx] == "--gpu":
                            idx += 2
                        else:
                            new_args.append(search_args[idx])
                            idx += 1
                    search_args = new_args
                    self._run_mmseqs(search_args, check=True)
                else:
                    raise

            # Step 4: result2msa → A3M
            if is_paired:
                pairaln_args=[
                    "pairaln",
                    query_db,
                    target_db,
                    result_db,
                    a3m_tmp
                ]
                self._run_mmseqs(pairaln_args, check=True)
            else:

                result2msa_args = [
                    "result2msa",
                    query_db,
                    target_db,
                    result_db,
                    a3m_tmp,
                ]
                result2msa_args += self._process_extra_args(extra_result2msa_args)
                self._run_mmseqs(result2msa_args, check=True)

            # Step 5: convertalis → TSV
            self._run_mmseqs([
                "convertalis",
                query_db,
                target_db,
                result_db,
                output_tsv,
                "--format-output", "query,target,pident,alnlen,mismatch,gapopen,qstart,qend,tstart,tend,evalue,bits"
            ], check=True)

            # Step 6: Output A3M
            shutil.copy(a3m_tmp, output_a3m)

        finally:
            if not tmp_dir:
                shutil.rmtree(work_dir, ignore_errors=True)

        return output_a3m, output_tsv

    def easy_search(self, query, target, extra_args=None):
        """
        run easy search on a query and target fasta this is quick fasta to fasta search
        :param query: query fasta
        :param target:target fasta
        :param extra_args:extra arguments
        :return: a pd dataframe with the results, default columns are used unless specified with extra args
        """

        if not os.path.isfile(query):
            raise FileNotFoundError(f"Query file not found: {query}")

        if not os.path.isfile(target):
            raise FileNotFoundError(f"Target file not found: {target}")

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

            run = self._run_mmseqs(args, check=False, capture_output=True, text=True)

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
        if extra_args is None:
            return []
        if isinstance(extra_args, dict):
            res = []
            for k, v in extra_args.items():
                res.extend([f"--{k}", str(v)])
            return res
        elif isinstance(extra_args, (list, tuple)):
            return [str(x) for x in extra_args]
        else:
            raise TypeError("extra_args must be dict or list/tuple")

    def _check_mmseqs(self):
        result = subprocess.run([self.mmseqs_bin, "version"], capture_output=True, text=True)
        if result.returncode != 0:
            raise EnvironmentError(f"MMseqs2 not found: {self.mmseqs_bin}")

    def _run_mmseqs(self, args: List[str], **kwargs) -> subprocess.CompletedProcess:
        cmd = [self.mmseqs_bin] + args
        return subprocess.run(cmd, **kwargs)

    def list_dbs(self):
        """
        list available downloadable dbs
        :return: a string that is the stdout
        """
        dbs=self._run_mmseqs(["databases"], capture_output=True, text=True)
        return dbs.stdout.strip().split("\n")

    def download_db(self, dbname, location, create=False):
        """
        download a specific db that is listed with list_dbs
        :param dbname: name of the db
        :param location: where to download the db
        :param create: whether to create the folder
        :return: None
        """
        if "/" in dbname:
            dbpath = dbname.replace("/", "_")
        else:
            dbpath = dbname

        if not os.path.exists(location) and not create:
            raise NotADirectoryError(f"could not find {location}")

        if not os.path.exists(location) and create:
            os.mkdir(location)

        with tempfile.TemporaryDirectory() as work_dir:
            cmd=["databases", dbname, f"{location}/{dbpath}", work_dir]

            try:
                self._run_mmseqs(cmd, check=True)
                return f"{location}/{dbpath}"
            except subprocess.CalledProcessError as e:
                err = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr or "")
                logger.error(f"Database download failed: {err}")

        return None

