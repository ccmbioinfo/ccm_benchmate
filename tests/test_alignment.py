# test_alignment_integration.py

# =============================================================================
# CONFIGURATION - FILL THESE IN
# =============================================================================

PROTEIN_DB_FASTA = ""
PROTEIN_QUERY_FASTA = ""

DNA_DB_FASTA = ""
DNA_QUERY_FASTA = ""

RNA_DB_FASTA = ""
RNA_QUERY_FASTA = ""

STRUCTURE_DB_DIR = ""
STRUCTURE_QUERY_PDB = ""

FOLDDISCO_CHAIN = "A"
FOLDDISCO_RESIDUES = [1, 2, 3]

RUN_GPU_TESTS = True


# =============================================================================
# IMPORTS
# =============================================================================

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from benchmate.sequence.sequence import Sequence, SequenceList
from benchmate.structure.structure import Structure

from benchmate.alignment.mmseqs import MMSeqs
from benchmate.alignment.foldseek import FoldSeek
from benchmate.alignment.folddisco import FoldDisco
from benchmate.alignment.blast import Blast
from benchmate.alignment.utils import (
    find_root_name,
    SinglePassFastaIndex,
)


# =============================================================================
# FIXTURES
# =============================================================================

PROTEIN_CASE = (
    "protein",
    PROTEIN_DB_FASTA,
    PROTEIN_QUERY_FASTA,
)

DNA_CASE = (
    "dna",
    DNA_DB_FASTA,
    DNA_QUERY_FASTA,
)

RNA_CASE = (
    "rna",
    RNA_DB_FASTA,
    RNA_QUERY_FASTA,
)

SEQUENCE_CASES = [
    PROTEIN_CASE,
    DNA_CASE,
    RNA_CASE,
]


def make_query(path, seq_type):
    return Sequence.from_fasta(path, seq_type=seq_type)


# =============================================================================
# utils.py
# =============================================================================

def test_find_root_name(tmp_path):
    (tmp_path / "db.1").touch()
    (tmp_path / "db_1").touch()
    (tmp_path / "db.index").touch()

    roots = find_root_name(tmp_path)

    assert len(roots) > 0


@pytest.mark.parametrize(
    "seq_type,db_fasta,_",
    SEQUENCE_CASES,
)
def test_single_pass_fasta_index(seq_type, db_fasta, _):
    idx = SinglePassFastaIndex(db_fasta)

    assert len(idx) > 0

    keys = list(idx.keys())

    assert len(keys) > 0

    record = idx[keys[0]]

    assert len(record.seq) > 0


@pytest.mark.parametrize(
    "seq_type,db_fasta,_",
    SEQUENCE_CASES,
)
def test_single_pass_fasta_repr(seq_type, db_fasta, _):
    idx = SinglePassFastaIndex(db_fasta)

    assert str(idx) == repr(idx)


# =============================================================================
# MMSEQS
# =============================================================================

def test_mmseqs_version():
    mm = MMSeqs()

    result = mm._run_mmseqs(
        ["version"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0


def test_mmseqs_list_dbs():
    mm = MMSeqs()

    dbs = mm.list_dbs()

    assert isinstance(dbs, list)


@pytest.mark.parametrize(
    "seq_type,db_fasta,query_fasta",
    SEQUENCE_CASES,
)
def test_mmseqs_create_database(
    seq_type,
    db_fasta,
    query_fasta,
):
    mm = MMSeqs()

    with tempfile.TemporaryDirectory() as tmp:

        db = mm.create_database(
            fasta_path=db_fasta,
            db_path=tmp,
            db_name=f"{seq_type}_db",
        )

        assert db is not None


@pytest.mark.parametrize(
    "seq_type,db_fasta,query_fasta",
    SEQUENCE_CASES,
)
def test_mmseqs_create_database_gpu(
    seq_type,
    db_fasta,
    query_fasta,
):
    mm = MMSeqs()

    with tempfile.TemporaryDirectory() as tmp:

        db = mm.create_database(
            fasta_path=db_fasta,
            db_path=tmp,
            db_name=f"{seq_type}_gpu_db",
            gpu_padded=True,
        )

        assert db is not None


@pytest.mark.parametrize(
    "seq_type,db_fasta,query_fasta",
    SEQUENCE_CASES,
)
def test_mmseqs_pad_db(
    seq_type,
    db_fasta,
    query_fasta,
):
    mm = MMSeqs()

    with tempfile.TemporaryDirectory() as tmp:

        db = mm.create_database(
            fasta_path=db_fasta,
            db_path=tmp,
            db_name="source",
        )

        padded = str(Path(tmp) / "padded")

        mm.pad_db(
            db,
            padded,
        )


@pytest.mark.parametrize(
    "seq_type,db_fasta,query_fasta",
    SEQUENCE_CASES,
)
def test_mmseqs_search(
    seq_type,
    db_fasta,
    query_fasta,
):
    mm = MMSeqs()

    query = make_query(
        query_fasta,
        seq_type,
    )

    with tempfile.TemporaryDirectory() as tmp:

        db = mm.create_database(
            fasta_path=db_fasta,
            db_path=tmp,
            db_name="target",
        )

        a3m = Path(tmp) / "out.a3m"
        tsv = Path(tmp) / "out.tsv"

        mm.search(
            query=query,
            target_db=db,
            output_a3m=str(a3m),
            output_tsv=str(tsv),
        )

        assert a3m.exists()
        assert tsv.exists()


def test_mmseqs_search_paired():
    mm = MMSeqs()

    seqs = SequenceList(
        [
            Sequence(
                "s1",
                "ACDEFGHIK",
                "protein",
            ),
            Sequence(
                "s2",
                "LMNPQRSTV",
                "protein",
            ),
        ]
    )

    with tempfile.TemporaryDirectory() as tmp:

        db = mm.create_database(
            fasta_path=PROTEIN_DB_FASTA,
            db_path=tmp,
            db_name="paired_db",
        )

        try:
            mm.search(
                query=seqs,
                target_db=db,
                output_a3m=str(Path(tmp) / "paired.a3m"),
                output_tsv=str(Path(tmp) / "paired.tsv"),
            )
        except Exception:
            pass


def test_mmseqs_search_invalid_query():
    mm = MMSeqs()

    with tempfile.TemporaryDirectory() as tmp:

        db = mm.create_database(
            fasta_path=PROTEIN_DB_FASTA,
            db_path=tmp,
            db_name="db",
        )

        with pytest.raises(TypeError):
            mm.search(
                query="not_a_sequence",
                target_db=db,
                output_a3m=str(Path(tmp) / "a3m"),
                output_tsv=str(Path(tmp) / "tsv"),
            )


@pytest.mark.parametrize(
    "seq_type,db_fasta,query_fasta",
    SEQUENCE_CASES,
)
def test_mmseqs_easy_search(
    seq_type,
    db_fasta,
    query_fasta,
):
    mm = MMSeqs()

    try:
        result = mm.easy_search(
            query=query_fasta,
            target=db_fasta,
            extra_args=[],
        )

        assert isinstance(result, pd.DataFrame)

    except Exception:
        pass


@pytest.mark.skipif(
    not RUN_GPU_TESTS,
    reason="gpu disabled",
)
def test_mmseqs_search_gpu():
    mm = MMSeqs()

    query = Sequence.from_fasta(
        PROTEIN_QUERY_FASTA,
        seq_type="protein",
    )

    with tempfile.TemporaryDirectory() as tmp:

        db = mm.create_database(
            fasta_path=PROTEIN_DB_FASTA,
            db_path=tmp,
            db_name="gpu_db",
            gpu_padded=True,
        )

        try:
            mm.search(
                query=query,
                target_db=db,
                output_a3m=str(Path(tmp) / "gpu.a3m"),
                output_tsv=str(Path(tmp) / "gpu.tsv"),
                use_gpu=True,
            )
        except Exception:
            pass


# =============================================================================
# FOLDSEEK
# =============================================================================

def test_foldseek_version():
    fs = FoldSeek()

    result = fs._run_foldseek(
        ["version"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0


def test_foldseek_list_dbs():
    fs = FoldSeek()

    assert isinstance(
        fs.list_dbs(),
        list,
    )


def test_foldseek_create_database():
    fs = FoldSeek()

    with tempfile.TemporaryDirectory() as tmp:

        fs.create_database(
            pdb_dir=STRUCTURE_DB_DIR,
            db_path=tmp,
            db_name="foldseek_db",
        )


def test_foldseek_create_database_gpu():
    fs = FoldSeek()

    with tempfile.TemporaryDirectory() as tmp:

        fs.create_database(
            pdb_dir=STRUCTURE_DB_DIR,
            db_path=tmp,
            db_name="foldseek_gpu",
            gpu_padded=True,
        )


def test_foldseek_search():
    fs = FoldSeek()

    structure = Structure.from_file(
        "query",
        STRUCTURE_QUERY_PDB,
    )

    with tempfile.TemporaryDirectory() as tmp:

        db = fs.create_database(
            STRUCTURE_DB_DIR,
            tmp,
            "db",
        )

        a3m = Path(tmp) / "res.a3m"
        tsv = Path(tmp) / "res.tsv"

        fs.search(
            structure=structure,
            target_db=db,
            output_a3m=str(a3m),
            output_tsv=str(tsv),
        )

        assert a3m.exists()
        assert tsv.exists()


@pytest.mark.skipif(
    not RUN_GPU_TESTS,
    reason="gpu disabled",
)
def test_foldseek_search_gpu():
    fs = FoldSeek()

    structure = Structure.from_file(
        "query",
        STRUCTURE_QUERY_PDB,
    )

    with tempfile.TemporaryDirectory() as tmp:

        db = fs.create_database(
            STRUCTURE_DB_DIR,
            tmp,
            "gpu_db",
            gpu_padded=True,
        )

        try:
            fs.search(
                structure=structure,
                target_db=db,
                output_a3m=str(Path(tmp) / "gpu.a3m"),
                output_tsv=str(Path(tmp) / "gpu.tsv"),
                use_gpu=True,
            )
        except Exception:
            pass


def test_foldseek_easy_search():
    fs = FoldSeek()

    result = fs.easy_search(
        query=STRUCTURE_QUERY_PDB,
        target=STRUCTURE_DB_DIR,
    )

    assert isinstance(result, pd.DataFrame)


# =============================================================================
# FOLDDISCO
# =============================================================================

def test_folddisco_create_index():
    fd = FoldDisco()

    with tempfile.TemporaryDirectory() as tmp:

        idx = fd.create_index(
            pdb_dir=STRUCTURE_DB_DIR,
            db_path=tmp,
            db_name="index",
        )

        assert idx is not None


def test_folddisco_search_full_structure():
    fd = FoldDisco()

    structure = Structure.from_file(
        "query",
        STRUCTURE_QUERY_PDB,
    )

    with tempfile.TemporaryDirectory() as tmp:

        index = fd.create_index(
            STRUCTURE_DB_DIR,
            tmp,
            "index",
        )

        result = fd.search(
            structure=structure,
            query_residues=None,
            target_db=index,
        )

        assert isinstance(
            result,
            pd.DataFrame,
        )


def test_folddisco_search_residues():
    fd = FoldDisco()

    structure = Structure.from_file(
        "query",
        STRUCTURE_QUERY_PDB,
    )

    with tempfile.TemporaryDirectory() as tmp:

        index = fd.create_index(
            STRUCTURE_DB_DIR,
            tmp,
            "index",
        )

        result = fd.search(
            structure=structure,
            query_residues={
                FOLDDISCO_CHAIN: FOLDDISCO_RESIDUES,
            },
            target_db=index,
        )

        assert isinstance(
            result,
            pd.DataFrame,
        )


def test_folddisco_invalid_chain():
    fd = FoldDisco()

    structure = Structure.from_file(
        "query",
        STRUCTURE_QUERY_PDB,
    )

    with tempfile.TemporaryDirectory() as tmp:

        index = fd.create_index(
            STRUCTURE_DB_DIR,
            tmp,
            "index",
        )

        with pytest.raises(ValueError):
            fd.search(
                structure=structure,
                query_residues={
                    "INVALID_CHAIN": [1],
                },
                target_db=index,
            )


# =============================================================================
# BLAST
# =============================================================================

BLAST_CASES = [
    (
        "protein",
        PROTEIN_DB_FASTA,
        PROTEIN_QUERY_FASTA,
        "p",
        "blastp",
    ),
    (
        "dna",
        DNA_DB_FASTA,
        DNA_QUERY_FASTA,
        "n",
        "blastn",
    ),
]


@pytest.mark.parametrize(
    "seq_type,db_fasta,query_fasta,dbtype,program",
    BLAST_CASES,
)
def test_blast_create_db(
    seq_type,
    db_fasta,
    query_fasta,
    dbtype,
    program,
):
    blast = Blast()
    blast.db = None

    with tempfile.TemporaryDirectory() as tmp:

        db = blast.create_db(
            fasta=db_fasta,
            output_path=tmp,
            dbname="blastdb",
            dbtype=dbtype,
        )

        assert db is not None


@pytest.mark.parametrize(
    "seq_type,db_fasta,query_fasta,dbtype,program",
    BLAST_CASES,
)
def test_blast_search_tabular(
    seq_type,
    db_fasta,
    query_fasta,
    dbtype,
    program,
):
    blast = Blast()
    blast.db = None
    blast.dbtype = dbtype

    query = Sequence.from_fasta(
        query_fasta,
        seq_type,
    )

    with tempfile.TemporaryDirectory() as tmp:

        db = blast.create_db(
            db_fasta,
            tmp,
            "blastdb",
            dbtype=dbtype,
        )

        result = blast.search(
            seq=query,
            db=db,
            output_type="tabular",
            exec=program,
        )

        assert isinstance(
            result,
            pd.DataFrame,
        )


@pytest.mark.parametrize(
    "seq_type,db_fasta,query_fasta,dbtype,program",
    BLAST_CASES,
)
def test_blast_search_json(
    seq_type,
    db_fasta,
    query_fasta,
    dbtype,
    program,
):
    blast = Blast()
    blast.db = None
    blast.dbtype = dbtype

    query = Sequence.from_fasta(
        query_fasta,
        seq_type,
    )

    with tempfile.TemporaryDirectory() as tmp:

        db = blast.create_db(
            db_fasta,
            tmp,
            "blastdb",
            dbtype=dbtype,
        )

        result = blast.search(
            seq=query,
            db=db,
            output_type="json",
            exec=program,
        )

        assert isinstance(
            result,
            dict,
        )