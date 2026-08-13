import json
import os
import subprocess
import tempfile
from shutil import which
from typing import List

import pandas as pd

from benchmate.alignment.utils import find_root_name


class Blast:
    def __init__(self, path=None, db=None, dbtype=None):
        """
        initiate a Blast class instance
        :param path: path of the executable if none will check $PATH
        :type path: str
        :param db: path and name of the blast database if exists if not it can be created using create_db
        :type db: str
        :param dbtype: type of the database n for nucleotide p for protein
        :type dbtype: str
        """
        execs = ["blastn", "blastp", "blastx", "tblastn", "tblastx", "makeblastdb"]
        if path is not None:
            for ex in execs:
                full_path = os.path.join(path, ex)
                if not os.path.exists(full_path):
                    raise FileNotFoundError("There was a problem finding executable {} please check your blast "
                                            "installation".format(ex))
        else:
            for ex in execs:
                if which(ex) is None:
                    raise EnvironmentError("{} does not seem to be installed, have you added blast to your $PATH?".format(ex))
        self.local_databases = []
        self.db = db
        self.dbtype = dbtype

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

    def create_db(self, fasta, output_path, dbname, dbtype="n", overwrite=True, arg_dict=None):
        """
        create a blast databse and stor in self.db
        :param dbtype: database type n for nucleotide and p for protein
        :param fasta: path of the fasta file only fasta is implemented
        :param output_path: output path for the database this is different from the databse name
        :param dbname: database name so self.db will be output_path/dbname
        :param overwrite: if there is already a self.db you can override this just edits the class instance value
        dooes not touch the databse
        :param arg_dict: a dictionary of arguments, if left empty will use default values see blast documentation
        :return: output database path
        """
        if dbtype == "n":
            parsed_dbtype = "nucl"
        elif dbtype == "p":
            parsed_dbtype = "prot"
        else:
            raise ValueError("You can only have a nucleotide 'n' or a protein 'p' database")

        if not os.path.isfile(fasta):
            raise FileNotFoundError("{} does not exists".format(fasta))

        if self.db is not None and not overwrite:
            raise FileExistsError("There is already a database for this class instance you "
                                  "can create another instance")

        full_db_path = os.path.join(output_path, dbname)
        os.makedirs(output_path, exist_ok=True)

        command = ["makeblastdb", "-dbtype", parsed_dbtype, "-input_type",
                   "fasta", "-in", fasta, "-out", full_db_path]
        if arg_dict is not None:
            command.extend(self._parse_args(arg_dict))

        try:
            self._run_blast(command)
            self.db = full_db_path
            self.dbtype = dbtype
            return full_db_path
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode() if e.stderr else ""
            raise RuntimeError(f"makeblastdb failed: {err}") from e


    def search(self, seq, db, output_type="tabular", exec="blastn", arg_dict=None, cols=None):
        """
        Search an existing blast database with a sequence class instance
        :param seq: a benchmate.sequence.sequence.Sequence instance
        :param db: the path and name of the database
        :param output_type: tabular or json
        :param exec: what to use for serach depends on the type of sequence being searched
        :param arg_dict: additional arguments to blast
        :param cols: what columns to return if you are returning a table
        :return: pd.DataFrame of dict
        """
        if output_type not in ["tabular", "json"]:
            raise ValueError("output_type must be either 'tabular' or 'json'")

        if self.dbtype == "p" and exec in ["blastn", "tblastn", "tblastx"]:
            raise ValueError("You are trying to use a protein database for a query that needs nucleotide info")

        if self.dbtype == "n" and exec in ["blastp", "blastx"]:
            raise ValueError("You are trying to use a nucleotide database for a query that needs protein info")

        work_dir = tempfile.mkdtemp()

        seq.to_fasta(os.path.join(work_dir, "query.fasta"))

        command = [exec, "-db", db]
        command.extend(["-query", os.path.join(work_dir, "query.fasta")])

        if arg_dict is not None:
            other_args = self._parse_args(arg_dict)
            command=command+other_args

        target_cols = list(cols) if cols is not None else [
            "qaccver", "saccver", "pident", "length", "mismatch", "gapopen",
            "qstart", "qend", "sstart", "send", "evalue", "bitscore"
        ]

        if output_type == "tabular":
            outfile = os.path.join(work_dir, "results.tab")
            command.extend(["-out", outfile, "-outfmt", f"6 {' '.join(target_cols)}"])

        if output_type == "json":
            outfile=os.path.join(work_dir, "results.json")
            command.extend(["-out", outfile, "-outfmt", "15"])
        try:
            self._run_blast(command)
        except subprocess.CalledProcessError as e:
            print(f"Blast run resulted in an error please see the error in the output '\n' {e}")

        parsed = self._parse_output(outfile, output_type, target_cols)
        return parsed

    def _parse_args(self, arg_dict):
        """
        take a dict of arguments to be appended to the blast subprocess see blast documentation for available features
        :param arg_dict: a dictionary of argument key is the flat and value is the value if no value is needed for the flag
        it can be a 0 length string or None type
        :return: a list of strings to be passed to subprocess.run
        """
        arguments = []
        for arg, val in arg_dict.items():
            if val is not None and str(val) != "":
                arguments.extend(["-" + arg, str(val)])
            else:
                arguments.append("-" + arg)
        return arguments

    def _parse_output(self, results:str, out_type,  cols=None):
        """
        parse blast output, this depends on the out_type which there are several
        :param out_type: the kind of blast output
        :param results: tempfile created by search
        :return: depends on the input dict of pandas dataframe
        """
        if out_type=="tabular":
            if not os.path.exists(results) or os.path.getsize(results) == 0:
                return pd.DataFrame(columns=cols or [])
            parsed=pd.read_csv(results, sep="\t", header=None)
            parsed.columns=cols
            return parsed
        elif out_type=="json":
            if not os.path.exists(results) or os.path.getsize(results) == 0:
                return {}
            with open(results, "r") as f:
                parsed=json.load(f)
            return parsed
        else:
            raise NotImplementedError("only tabular and json files are implemented")

    def _run_blast(self, cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
        """
        Run blast locally
        :param cmd: command to run
        :param kwargs: additional arguments to blast binary
        :return: subprocess.CompletedProcess object
        """
        return subprocess.run(cmd, check=True, **kwargs)

    def _write_query_fasta(self, sequences: List[str], path: str):
        """
        Take a sequence object and convert that to a temp fasta file
        :param sequences: sequence object instance
        :param path: path to fasta file
        :return: a fasta file that gets deleted after the run this is just a temporary file
        """
        if isinstance(sequences, str):
            sequences = [sequences]
        with open(path, 'w') as f:
            for i, seq in enumerate(sequences):
                f.write(f">query_{i}\n{seq}\n")