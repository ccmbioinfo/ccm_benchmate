import os
import pytest
import sqlalchemy

from benchmate.genome.genome import Genome
from benchmate.genome.utils import parse_gtf
from benchmate.ranges.genomicranges import GenomicRange


TEST_GTF = "tests/test_data/genome/Saccharomyces_cerevisiae.R64-1-1.114.gtf"
TEST_FASTA = "tests/test_data/genome/Saccharomyces_cerevisiae.R64-1-1.dna.toplevel.fa"
TEST_DB_PATH = "tests/test_data/genome/genome.db"


@pytest.fixture(scope="module")
def standalone_genome():
    engine = sqlalchemy.create_engine(f"sqlite:///{TEST_DB_PATH}")
    genome_obj = Genome(
        name="Saccharomyces_cerevisiae",
        description="Yeast genome R64-1-1.114",
        genome_fasta=TEST_FASTA,
        gtf=TEST_GTF,
        standalone=True,
        create=False,
        db_conn=engine,
    )
    return genome_obj


def test_gtf_parsing():
    (
        chrom_list,
        gene_list,
        transcript_list,
        exon_list,
        cds_list,
        three_utr_list,
        five_utr_list,
    ) = parse_gtf(TEST_GTF)

    assert len(chrom_list) > 0
    assert len(gene_list) > 0
    assert len(transcript_list) > 0
    assert len(exon_list) > 0
    assert len(cds_list) > 0
    assert isinstance(three_utr_list, list)
    assert isinstance(five_utr_list, list)


def test_standalone_genome_db_init(tmp_path):
    db_file = tmp_path / "temp_genome.db"
    engine = sqlalchemy.create_engine(f"sqlite:///{db_file}")

    genome_obj = Genome(
        name="Saccharomyces_cerevisiae_temp",
        description="Temp yeast genome",
        genome_fasta=TEST_FASTA,
        gtf=TEST_GTF,
        standalone=True,
        create=True,
        db_conn=engine,
    )

    assert genome_obj.genome_id is not None
    assert len(genome_obj.chrom_ids) > 0
    genes = genome_obj.genes()
    assert len(genes) > 0


def test_genome_existing_db_reopen(standalone_genome):
    assert standalone_genome.genome_id == 1
    assert len(standalone_genome.chrom_ids) == 17
    assert standalone_genome.name == "Saccharomyces_cerevisiae"


def test_genes_query(standalone_genome):
    all_genes = standalone_genome.genes()
    assert len(all_genes) == 7127

    single_gene = standalone_genome.genes(ids=["YAL068C"])
    assert "YAL068C" in single_gene
    gr = single_gene["YAL068C"]
    assert gr.chrom == "I"
    assert gr.ranges.start == 1807
    assert gr.ranges.end == 2169
    assert gr.strand == "-"

    range_genes = standalone_genome.genes(
        range=GenomicRange("I", 1, 10000, "-"), ignore_strand=False
    )
    assert len(range_genes) > 0


def test_transcripts_query(standalone_genome):
    all_txs = standalone_genome.transcripts()
    assert len(all_txs) > 0

    gene_txs = standalone_genome.transcripts(gene_ids=["YAL068C"])
    assert "YAL068C" in gene_txs

    ungrouped_txs = standalone_genome.transcripts(
        gene_ids=["YAL068C"], group_by_gene=False
    )
    assert "YAL068C_mRNA" in ungrouped_txs


def test_exons_coding_utr_introns_query(standalone_genome):
    exons = standalone_genome.exons(transcript_ids=["YAL068C_mRNA"])
    assert len(exons) > 0

    cds = standalone_genome.coding(transcript_ids=["YAL068C_mRNA"])
    assert len(cds) > 0

    five_utr = standalone_genome.five_utr()
    assert five_utr is not None

    introns = standalone_genome.introns()
    assert introns is not None


def test_get_sequence(standalone_genome):
    single_gene = standalone_genome.genes(ids=["YAL068C"])
    gr = single_gene["YAL068C"]
    seq = standalone_genome.get_sequence(gr)

    assert len(seq) == (gr.ranges.end - gr.ranges.start + 1)
    assert seq.startswith("ATGGTCAAATTAACTTCAAT")


def test_custom_ranges(standalone_genome):
    cr = GenomicRange("I", 5000, 6000, "+", {"note": "test_region"})
    standalone_genome.insert_custom_range(cr)

    queried_cr = standalone_genome.custom_range(GenomicRange("I", 4000, 7000, "+"))
    assert queried_cr is not None
    assert len(queried_cr) >= 1
    found = False
    for r in queried_cr:
        if r.ranges.start == 5000 and r.ranges.end == 6000:
            found = True
            break
    assert found


def test_annotations(standalone_genome):
    single_gene = standalone_genome.genes(ids=["YAL068C"])
    gr = single_gene["YAL068C"]
    db_id = gr.annotation["db_id"]

    unique_key = f"tag_{os.urandom(4).hex()}"
    standalone_genome.add_annotation("gene", db_id, {unique_key: "test_val"})
    search_res = standalone_genome.search_annotation("gene", {unique_key: "test_val"})
    assert "YAL068C" in search_res
