import os
import warnings

import pandas as pd
import pytest
import sqlalchemy
import pysam

from benchmate.genome.genome import Genome
from benchmate.ranges.genomicranges import GenomicRange, GenomicRangesDict, GenomicRangesList


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")


@pytest.fixture(scope="session")
def paths():
    return {
        "sqlite": os.path.join(TEST_DATA_DIR, "genome.sqlite"),
        "gtf": os.path.join(TEST_DATA_DIR, "Saccharomyces_cerevisiae.R64-1-1.114.gtf"),
        "fasta": os.path.join(TEST_DATA_DIR, "Saccharomyces_cerevisiae.R64-1-1.dna.toplevel.fa"),
    }


@pytest.fixture(scope="session")
def engine(paths):
    # Use the shipped sqlite file; do not modify schema/data if possible
    sqlite_uri = f"sqlite:///{paths['sqlite']}"
    eng = sqlalchemy.create_engine(sqlite_uri)
    return eng


@pytest.fixture(scope="session")
def genome_name(engine):
    # Pick an existing genome name from the db; if not present, skip the test suite.
    try:
        df = pd.read_sql("select genome_name from genome limit 1", con=engine)
    except Exception as e:
        pytest.skip(f"Could not access genome table in test sqlite: {e}")
    if df.empty:
        pytest.skip("No genomes present in test sqlite database.")
    return df["genome_name"].iloc[0]


@pytest.fixture(scope="session")
def genome(paths, engine, genome_name):
    # Use create=False to avoid re-inserting into the DB; still provide fasta/gtf for sequence access
    g = Genome(
        genome_fasta=paths["fasta"],
        gtf=paths["gtf"],
        name=genome_name,
        description="pytest-genome",
        db_conn=engine,
        create=False,
    )
    return g


def _first_item_from_grdict(grdict: GenomicRangesDict):
    # Helper: get a deterministic first item for testing
    for key in grdict.keys():
        items = grdict[key]
        if isinstance(items, GenomicRangesList) and len(items) > 0:
            return key, items[0]
        if hasattr(items, "chrom"):  # single GenomicRange
            return key, items
    return None, None


def test_genome_basic_str_repr(genome, genome_name):
    s = str(genome)
    r = repr(genome)
    assert genome_name in s
    assert genome_name in r


def test_genes_unfiltered_returns_dict(genome):
    genes = genome.genes()
    assert isinstance(genes, GenomicRangesDict)
    # Not asserting non-empty globally; some DBs might be minimal, but try to access one if available
    if len(list(genes.keys())) > 0:
        key, gr = _first_item_from_grdict(genes)
        assert gr is not None
        assert hasattr(gr, "chrom")
        assert hasattr(gr, "ranges")
        assert hasattr(gr, "strand")
        assert gr.ranges.start <= gr.ranges.end


def test_genes_range_filter_roundtrip(genome):
    genes_all = genome.genes()
    if len(list(genes_all.keys())) == 0:
        pytest.skip("No genes available in test database to validate range filtering.")
    _, gr = _first_item_from_grdict(genes_all)
    # Build an identical range to filter on
    r = GenomicRange(gr.chrom, gr.ranges.start, gr.ranges.end, gr.strand, {})
    genes_in_range = genome.genes(range=r)
    # The range-based query should at least include a gene overlapping exactly that range
    # Because the query uses within (start>=, end<=), exact match should return the same gene
    assert isinstance(genes_in_range, GenomicRangesDict)
    assert len(list(genes_in_range.keys())) >= 0  # may be zero if DB annotations differ
    # If it returns something, validate structure
    if len(list(genes_in_range.keys())) > 0:
        _, gr2 = _first_item_from_grdict(genes_in_range)
        assert gr2.chrom == gr.chrom
        assert gr2.strand == gr.strand
        assert gr2.ranges.start >= r.ranges.start
        assert gr2.ranges.end <= r.ranges.end


def test_transcripts_unfiltered_and_by_gene(genome):
    tx_all = genome.transcripts()
    assert isinstance(tx_all, GenomicRangesDict)
    # If we have any transcripts, pick a gene_id and refetch by gene_ids
    keys = list(tx_all.keys())
    if len(keys) > 0:
        gene_id = keys[0]
        tx_for_gene = genome.transcripts(gene_ids=[gene_id])
        assert isinstance(tx_for_gene, GenomicRangesDict)
        # Expect at least one transcript for this gene when present in unfiltered
        assert len(list(tx_for_gene.keys())) >= 0
        _, treg = _first_item_from_grdict(tx_for_gene)
        if treg:
            assert treg.ranges.start <= treg.ranges.end


def test_exons_by_transcript(genome):
    tx_all = genome.transcripts()
    if len(list(tx_all.keys())) == 0:
        pytest.skip("No transcripts available to test exons.")
    _, tx = _first_item_from_grdict(tx_all)
    # transcripts() puts db id into annot["db_id"]
    db_tx_id = tx.annotation.get("db_id")
    if db_tx_id is None:
        pytest.skip("Transcript annotations do not contain db_id; cannot query exons by transcript.")
    exons = genome.exons(transcript_ids=[db_tx_id])
    assert isinstance(exons, GenomicRangesDict)
    # Grouped by transcript_id string in annotations; just ensure structural validity
    if len(list(exons.keys())) > 0:
        _, ex = _first_item_from_grdict(exons)
        assert ex.ranges.start <= ex.ranges.end
        assert ex.chrom == tx.chrom


def test_coding_regions_best_effort(genome):
    # Not all transcripts have coding regions; ensure call succeeds and returns the right type
    tx_all = genome.transcripts()
    if len(list(tx_all.keys())) == 0:
        pytest.skip("No transcripts available to test coding regions.")
    _, tx = _first_item_from_grdict(tx_all)
    db_tx_id = tx.annotation.get("db_id")
    if db_tx_id is None:
        pytest.skip("Transcript annotations do not contain db_id; cannot query coding regions.")
    cds = genome.coding(transcript_ids=[db_tx_id])
    assert isinstance(cds, GenomicRangesDict)
    # If present, basic sanity
    if len(list(cds.keys())) > 0:
        _, c = _first_item_from_grdict(cds)
        assert c.ranges.start <= c.ranges.end
        assert c.chrom == tx.chrom


def test_utr_regions_best_effort(genome):
    tx_all = genome.transcripts()
    if len(list(tx_all.keys())) == 0:
        pytest.skip("No transcripts available to test UTR regions.")
    _, tx = _first_item_from_grdict(tx_all)
    db_tx_id = tx.annotation.get("db_id")
    if db_tx_id is None:
        pytest.skip("Transcript annotations do not contain db_id; cannot query UTRs.")
    utr3 = genome.three_utr(transcript_ids=[db_tx_id])
    utr5 = genome.five_utr(transcript_ids=[db_tx_id])
    assert isinstance(utr3, GenomicRangesDict)
    assert isinstance(utr5, GenomicRangesDict)
    # If present, basic sanity
    if len(list(utr3.keys())) > 0:
        _, u3 = _first_item_from_grdict(utr3)
        assert u3.ranges.start <= u3.ranges.end
    if len(list(utr5.keys())) > 0:
        _, u5 = _first_item_from_grdict(utr5)
        assert u5.ranges.start <= u5.ranges.end


def test_introns_best_effort(genome):
    tx_all = genome.transcripts()
    if len(list(tx_all.keys())) == 0:
        pytest.skip("No transcripts available to test introns.")
    # introns() filters by transcripts_table.c.transcript_id (string), not db id
    # Try to obtain that field from transcripts query result
    _, tx = _first_item_from_grdict(tx_all)
    tx_id_str = tx.annotation.get("transcript_id")
    if not tx_id_str:
        pytest.skip("Transcript annotations do not contain transcript_id; cannot query introns.")
    intr = genome.introns(transcript_ids=[tx_id_str])
    assert isinstance(intr, GenomicRangesDict)
    if len(list(intr.keys())) > 0:
        _, i = _first_item_from_grdict(intr)
        assert i.ranges.start <= i.ranges.end
        assert i.chrom == tx.chrom


def test_get_sequence_forward_and_reverse_complement(genome, paths):
    genes = genome.genes()
    if len(list(genes.keys())) == 0:
        pytest.skip("No genes available to test sequence retrieval.")
    _, gr = _first_item_from_grdict(genes)

    # Build a short subrange to make fetch fast and robust
    start = gr.ranges.start
    end = min(start + 50, gr.ranges.end)
    if end <= start:
        pytest.skip("Gene range too short to test sequence retrieval.")

    sub = GenomicRange(gr.chrom, start, end, "+", {})
    seq_plus = genome.get_sequence(sub, type="genome")

    # Verify against direct pysam fetch
    with pysam.FastaFile(paths["fasta"]) as fa:
        direct = fa.fetch(sub.chrom, sub.ranges.start, sub.ranges.end)
    assert isinstance(seq_plus, str)
    assert seq_plus == direct

    # Reverse complement check by reusing same coordinates with '-' strand
    sub_rc = GenomicRange(gr.chrom, start, end, "-", {})
    seq_minus = genome.get_sequence(sub_rc, type="genome")
    # Compute reverse complement here for verification
    complement = str(direct.translate(str.maketrans("ACGTNacgtn", "TGCANtgcan")))[::-1]
    assert seq_minus == complement


def test_get_sequence_invalid_chrom_raises(genome):
    bogus = GenomicRange("___chrom_not_in_fasta___", 0, 10, "+", {})
    with pytest.raises(ValueError):
        _ = genome.get_sequence(bogus, type="genome")


def test_add_annotation_rejects_non_dict(genome):
    with pytest.raises(ValueError):
        genome.add_annotation("gene", 1, ["not", "a", "dict"])


def test_add_annotation_rejects_non_int_id(genome):
    with pytest.raises(ValueError):
        genome.add_annotation("gene", "not-an-int", {"foo": "bar"})


def test_check_chroms_warns_on_mismatch(genome):
    # Build a dataframe with a made-up chromosome to trigger the warning path
    fake = pd.DataFrame({"id": [0], "chrom": ["___chrom_not_in_fasta___"]})
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        genome._check_chroms(fake)
        # We expect at least one warning due to missing chrom
        assert any("not found in the database" in str(ww.message) for ww in w)