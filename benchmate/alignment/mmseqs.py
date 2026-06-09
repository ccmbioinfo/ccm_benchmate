import subprocess
import os
import tempfile
import shutil
from typing import Union, List, Dict, Optional


import benchmate.sequence.sequence
from benchmate.alignment.utils import *


class MMSeqs:
    """
    Corrected MMseqs2 wrapper:
    - Always creates query DB via `createdb`
    - Supports single and paired alignment (`pairaln`)
    - GPU with padded DB
    - Flexible extra args
    """

    def __init__(self, mmseqs_bin: str = "mmseqs"):
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
        """Create target database (optionally padded for GPU)."""
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
        Full pipeline: query → search/pairaln → A3M + TSV
        """
        if not isinstance(query, benchmate.sequence.sequence.Sequence) or \
                isinstance(query, benchmate.sequence.sequence.SequenceList):
            raise TypeError("Query must be a sequence or sequencelist instance.")

        if len(query) > 1 and isinstance(query, benchmate.sequence.sequence.SequenceList):
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
            query.to_fasta(os.path.join(work_dir, "query.fasta"))

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
                err = e.stderr.decode() if e.stderr else ""
                if use_gpu and ("GPU" in err or "cuda" in err.lower()):
                    print(f"GPU failed: {err}\nRetrying on CPU...")
                    search_args = [a for a in search_args if a not in ("--gpu", "1")]
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

    def easy_search(self, query, target, extra_args):
        """
        run easy search on a query and target fasta
        :param query:
        :param target:
        :param extra_args:
        :return:
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
                "--format-mode 4"
            ]

            args += self._process_extra_args(extra_args)

            run = self._run_foldseek(args,check=False, capture_output=True, text=True, )

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
            return [f"--{k} str(v)" for k, v in extra_args.items()]
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
        dbs=self._run_mmseqs(["databases"], capture_output=True, text=True)
        return dbs.stdout.strip().split("\n")

    def download_db(self, dbname, location, create=False):

        work_dir = tempfile.mkdtemp()

        if "/" in dbname:
            dbpath = dbname.replace("/", "_")
        else:
            dbpath = dbname

        if not os.path.exists(location) and not create:
            raise NotADirectoryError(f"could not find {location}")

        if not os.path.exists(location) and create:
            os.mkdir(location)

        cmd=["databases", dbname, f"{location}/{dbpath}", work_dir]

        try:
            self._run_mmseqs(cmd, check=True)
            return f"{location}/{dbpath}"
        except subprocess.CalledProcessError as e:
            err = e.stderr
            print(f"Database download failed: {err}")
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

        return

