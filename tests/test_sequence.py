import os
from pathlib import Path

import numpy as np
import pytest

from benchmate.sequence.sequence import (
    NoSequenceError,
    Sequence,
    SequenceInfo,
    SequenceList,
)


class TestSequenceInfo:
    """Tests for the sequence metadata container."""

    def test_stores_sequence_metadata(self):
        info = SequenceInfo(
            name="seq1",
            sequence="ATGC",
            seq_type="dna",
            annotations={"gene": "BRCA1"},
        )

        assert info.name == "seq1"
        assert info.sequence == "ATGC"
        assert info.seq_type == "dna"
        assert info.annotations == {"gene": "BRCA1"}

    def test_annotations_default_to_none(self):
        info = SequenceInfo(name="seq1", sequence="ATGC", seq_type="dna")

        assert info.annotations is None


class TestSequenceConstruction:
    """Tests for construction, metadata, basic protocol behavior, and equality."""

    @pytest.mark.parametrize("seq_type", ["dna", "rna", "protein", "3di"])
    def test_accepts_supported_sequence_types(self, seq_type):
        sequence = Sequence("seq1", "ATGC", seq_type=seq_type)

        assert sequence.name == "seq1"
        assert sequence.sequence == "ATGC"
        assert sequence.seq_type == seq_type

    def test_rejects_invalid_sequence_type(self):
        with pytest.raises(ValueError, match="Invalid sequence type"):
            Sequence("seq1", "ATGC", seq_type="carbohydrate")

    def test_annotations_are_preserved(self):
        annotations = {"gene": "BRCA1", "start": 10}
        sequence = Sequence("seq1", "ATGC", seq_type="dna", annotations=annotations)

        assert sequence.info.annotations == annotations

    def test_length(self):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        assert len(sequence) == 4

    def test_string_conversion_returns_sequence(self):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        assert str(sequence) == "ATGC"

    def test_repr_contains_metadata(self):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        assert repr(sequence) == "Sequence(name='seq1', len=4, type=dna)"

    def test_equality_is_case_insensitive_for_same_type(self):
        first = Sequence("seq1", "atgc", seq_type="dna")
        second = Sequence("seq2", "ATGC", seq_type="dna")

        assert first == second
        assert not (first != second)

    def test_sequences_of_different_types_are_not_equal(self):
        dna = Sequence("seq1", "ATGC", seq_type="dna")
        rna = Sequence("seq2", "ATGC", seq_type="rna")

        assert dna != rna

    def test_different_sequences_are_not_equal(self):
        first = Sequence("seq1", "ATGC", seq_type="dna")
        second = Sequence("seq2", "ATGT", seq_type="dna")

        assert first != second


class TestSequenceNucleicOperations:
    """Tests for operations requiring DNA or RNA sequences."""

    @pytest.mark.parametrize(
        ("sequence", "expected"),
        [
            ("ATGC", "GCAT"),
            ("AAAA", "TTTT"),
            ("AUGC", "GCAT"),
        ],
    )
    def test_reverse_complement(self, sequence, expected):
        seq_type = "rna" if "U" in sequence else "dna"
        sequence_obj = Sequence("seq1", sequence, seq_type=seq_type)

        result = sequence_obj.reverse_complement(keep_annotations=False)

        assert result.sequence == expected
        assert result.seq_type == seq_type
        assert result.name == "seq1_rc"

    def test_reverse_complement_preserves_annotations_when_requested(self):
        sequence = Sequence(
            "seq1",
            "ATGC",
            seq_type="dna",
            annotations={"gene": "BRCA1"},
        )

        result = sequence.reverse_complement(keep_annotations=True)

        assert result.info.annotations == sequence.info.annotations

    def test_reverse_complement_drops_annotations_when_requested(self):
        sequence = Sequence(
            "seq1",
            "ATGC",
            seq_type="dna",
            annotations={"gene": "BRCA1"},
        )

        result = sequence.reverse_complement(keep_annotations=False)

        assert result.info.annotations is None

    @pytest.mark.parametrize(
        ("start", "end", "expected"),
        [
            (0, 4, "ATGC"),
            (1, 3, "TG"),
            (0, 0, ""),
            (2, 4, "GC"),
        ],
    )
    def test_subseq(self, start, end, expected):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        result = sequence.subseq(start, end, keep_annotations=False)

        assert result.sequence == expected
        assert result.name == f"seq1_sub{start}_{end}"
        assert result.seq_type == "dna"

    @pytest.mark.parametrize(
        ("start", "end"),
        [
            (-1, 2),
            (0, -1),
            (3, 2),
            (0, 5),
        ],
    )
    def test_subseq_rejects_invalid_ranges(self, start, end):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        with pytest.raises(ValueError, match="Invalid subseq range"):
            sequence.subseq(start, end)

    @pytest.mark.parametrize(
        ("query", "expected"),
        [
            ("AT", [0]),
            ("at", [0]),
            ("GC", [2]),
            ("A", [0]),
            ("T", [1]),
            ("", []),
            ("GG", []),
        ],
    )
    def test_find_is_case_insensitive(self, query, expected):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        assert sequence.find(query) == expected

    def test_find_includes_overlapping_hits(self):
        sequence = Sequence("seq1", "AAAA", seq_type="dna")

        assert sequence.find("AA") == [0, 1, 2]

    @pytest.mark.parametrize("seq_type", ["protein", "3di"])
    def test_nucleic_operations_reject_non_nucleic_sequences(self, seq_type):
        sequence = Sequence("seq1", "MKT", seq_type=seq_type)

        with pytest.raises(TypeError, match="requires DNA or RNA"):
            sequence.reverse_complement(keep_annotations=False)

    @pytest.mark.parametrize(
        ("sequence", "expected"),
        [
            ("ATGGCC", "MA"),
            ("ATGTAA", "M*"),
            ("ATGTAA", "M"),
        ],
    )
    def test_translate(self, sequence, expected):
        sequence_obj = Sequence("seq1", sequence, seq_type="dna")
        to_stop = expected == "M"

        result = sequence_obj.translate(to_stop=to_stop, keep_annotations=False)

        assert result.sequence == expected
        assert result.seq_type == "protein"
        assert result.name == "seq1_trans"

    def test_translate_preserves_annotations(self):
        sequence = Sequence(
            "seq1",
            "ATGGCC",
            seq_type="dna",
            annotations={"gene": "BRCA1"},
        )

        result = sequence.translate(keep_annotations=True)

        assert result.info.annotations == sequence.info.annotations

    def test_translate_rejects_protein(self):
        sequence = Sequence("seq1", "MKT", seq_type="protein")

        with pytest.raises(TypeError, match="requires DNA or RNA"):
            sequence.translate()


class TestSequenceComposition:
    """Tests for nucleotide composition and k-mer calculations."""

    @pytest.mark.parametrize(
        ("sequence", "expected"),
        [
            ("ATGC", 0.5),
            ("GGCC", 1.0),
            ("AATT", 0.0),
            ("AUGC", 0.5),
            ("", 0.0),
        ],
    )
    def test_gc_content(self, sequence, expected):
        sequence_obj = Sequence("seq1", sequence, seq_type="rna" if "U" in sequence else "dna")

        assert sequence_obj.gc_content() == pytest.approx(expected)

    def test_gc_content_rolling_window(self):
        sequence = Sequence("seq1", "ATGCCG", seq_type="dna")

        result = sequence.gc_content(window=3)

        np.testing.assert_allclose(result, [1 / 3, 2 / 3, 1.0, 1.0])

    def test_gc_content_returns_empty_array_for_window_longer_than_sequence(self):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        result = sequence.gc_content(window=5)

        assert isinstance(result, np.ndarray)
        assert result.size == 0

    @pytest.mark.parametrize("window", [0, -1])
    def test_gc_content_rejects_nonpositive_window(self, window):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        with pytest.raises(ValueError, match="window must be positive"):
            sequence.gc_content(window=window)

    def test_gc_content_rejects_protein(self):
        sequence = Sequence("seq1", "MKT", seq_type="protein")

        with pytest.raises(TypeError, match="requires DNA or RNA"):
            sequence.gc_content()

    def test_gc_skew(self):
        sequence = Sequence("seq1", "GGCCAT", seq_type="dna")

        result = sequence.gc_skew(window=4)

        np.testing.assert_allclose(result, [0.0, 0.0, 0.0])

    def test_gc_skew_returns_zero_when_window_has_no_g_or_c(self):
        sequence = Sequence("seq1", "AAAA", seq_type="dna")

        result = sequence.gc_skew(window=2)

        np.testing.assert_allclose(result, [0.0, 0.0, 0.0])

    def test_gc_skew_returns_empty_array_for_window_longer_than_sequence(self):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        result = sequence.gc_skew(window=5)

        assert result.size == 0

    @pytest.mark.parametrize("window", [0, -1])
    def test_gc_skew_rejects_nonpositive_window(self, window):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        with pytest.raises(ValueError, match="window must be positive"):
            sequence.gc_skew(window)

    def test_gc_skew_rejects_protein(self):
        sequence = Sequence("seq1", "MKT", seq_type="protein")

        with pytest.raises(TypeError, match="requires DNA or RNA"):
            sequence.gc_skew(2)

    def test_kmer_counts_without_normalization(self):
        sequence = Sequence("seq1", "ATAT", seq_type="dna")

        assert sequence.kmer_counts(2, normalize=False) == {
            "AT": 2,
            "TA": 1,
        }

    def test_kmer_counts_normalized(self):
        sequence = Sequence("seq1", "ATAT", seq_type="dna")

        assert sequence.kmer_counts(2) == {
            "AT": pytest.approx(2 / 3),
            "TA": pytest.approx(1 / 3),
        }

    def test_kmer_counts_is_case_insensitive(self):
        sequence = Sequence("seq1", "atat", seq_type="dna")

        assert sequence.kmer_counts(2, normalize=False) == {
            "AT": 2,
            "TA": 1,
        }

    def test_kmer_counts_returns_empty_for_k_larger_than_sequence(self):
        sequence = Sequence("seq1", "AT", seq_type="dna")

        assert sequence.kmer_counts(3) == {}

    @pytest.mark.parametrize("k", [0, -1])
    def test_kmer_counts_rejects_nonpositive_k(self, k):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        with pytest.raises(ValueError, match="k must be positive"):
            sequence.kmer_counts(k)


class TestSequenceProteinOperations:
    """Tests for protein-specific calculations."""

    def test_aa_composition(self):
        sequence = Sequence("seq1", "ACDX", seq_type="protein")

        composition = sequence.aa_composition()

        assert composition["A"] == pytest.approx(0.25)
        assert composition["C"] == pytest.approx(0.25)
        assert composition["D"] == pytest.approx(0.25)
        assert composition["X"] == pytest.approx(0.25)
        assert sum(composition.values()) == pytest.approx(1.0)

    def test_aa_composition_rejects_nucleic_sequence(self):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        with pytest.raises(TypeError, match="requires a protein"):
            sequence.aa_composition()

    def test_molecular_weight_of_empty_protein(self):
        sequence = Sequence("seq1", "", seq_type="protein")

        assert sequence.molecular_weight() == 0.0

    def test_protein_molecular_weight(self):
        sequence = Sequence("seq1", "AG", seq_type="protein")

        expected = 89.0935 + 75.0669 - 18.01528

        assert sequence.molecular_weight() == pytest.approx(expected)

    def test_protein_molecular_weight_ignores_stop(self):
        sequence = Sequence("seq1", "AG*", seq_type="protein")

        expected = 89.0935 + 75.0669 - 18.01528

        assert sequence.molecular_weight() == pytest.approx(expected)

    def test_dna_molecular_weight(self):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        expected = 313.21 + 304.2 + 329.21 + 289.18

        assert sequence.molecular_weight() == pytest.approx(expected)

    def test_rna_molecular_weight(self):
        sequence = Sequence("seq1", "AUGC", seq_type="rna")

        expected = 329.21 + 306.17 + 345.21 + 305.18

        assert sequence.molecular_weight() == pytest.approx(expected)

    def test_rna_treats_t_as_u(self):
        rna = Sequence("rna", "AU", seq_type="rna")
        rna_with_t = Sequence("rna", "AT", seq_type="rna")

        assert rna.molecular_weight() == pytest.approx(rna_with_t.molecular_weight())

    def test_isoelectric_point_returns_reasonable_value(self):
        sequence = Sequence("seq1", "ACDEFGHIKLMNPQRSTVWY", seq_type="protein")

        p_i = sequence.isoelectric_point()

        assert 0.0 <= p_i <= 14.0

    def test_isoelectric_point_is_basic_for_lysine_rich_sequence(self):
        sequence = Sequence("seq1", "KKKKKK", seq_type="protein")

        assert sequence.isoelectric_point() > 9.0

    def test_isoelectric_point_rejects_nucleic_sequence(self):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        with pytest.raises(TypeError, match="requires a protein"):
            sequence.isoelectric_point()

    def test_hydropathy_profile(self):
        sequence = Sequence("seq1", "AIL", seq_type="protein")

        result = sequence.hydropathy_profile(window=2)

        np.testing.assert_allclose(result, [(4.5 + 1.8) / 2, (1.8 + 3.8) / 2])

    def test_hydropathy_profile_returns_empty_when_window_is_too_large(self):
        sequence = Sequence("seq1", "AIL", seq_type="protein")

        assert sequence.hydropathy_profile(window=4).size == 0

    @pytest.mark.parametrize("window", [0, -1])
    def test_hydropathy_profile_rejects_nonpositive_window(self, window):
        sequence = Sequence("seq1", "AIL", seq_type="protein")

        with pytest.raises(ValueError, match="window must be positive"):
            sequence.hydropathy_profile(window=window)

    def test_hydropathy_profile_rejects_unsupported_scale(self):
        sequence = Sequence("seq1", "AIL", seq_type="protein")

        with pytest.raises(NotImplementedError, match="KyteDoolittle"):
            sequence.hydropathy_profile(scale="Eisenberg")

    def test_hydropathy_profile_rejects_nucleic_sequence(self):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        with pytest.raises(TypeError, match="requires a protein"):
            sequence.hydropathy_profile()


class TestSequenceEditing:
    """Tests for mutation, insertion, and deletion."""

    def test_mutate(self):
        sequence = Sequence(
            "seq1",
            "ATGC",
            seq_type="dna",
            annotations={"gene": "BRCA1"},
        )

        result = sequence.mutate(1, "C", keep_annotations=False)

        assert result.sequence == "ACGC"
        assert result.name == "seq1_p1T>C"
        assert result.seq_type == "dna"
        assert result.info.annotations is None
        assert sequence.sequence == "ATGC"

    def test_mutate_accepts_custom_name(self):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        result = sequence.mutate(1, "C", new_name="mutant", keep_annotations=False)

        assert result.name == "mutant"

    def test_mutate_preserves_annotations(self):
        sequence = Sequence(
            "seq1",
            "ATGC",
            seq_type="dna",
            annotations={"gene": "BRCA1"},
        )

        result = sequence.mutate(1, "C", keep_annotations=True)

        assert result.info.annotations == sequence.info.annotations

    @pytest.mark.parametrize("position", [-1, 4])
    def test_mutate_rejects_out_of_bounds_position(self, position):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        with pytest.raises(ValueError, match="out of bounds"):
            sequence.mutate(position, "C")

    @pytest.mark.parametrize("to", ["", "AA", "AT"])
    def test_mutate_requires_single_character(self, to):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        with pytest.raises(ValueError, match="single character"):
            sequence.mutate(1, to)

    @pytest.mark.parametrize(
        ("position", "expected"),
        [
            (0, "CATGC"),
            (2, "ATCGC"),
            (4, "ATGCC"),
        ],
    )
    def test_insert(self, position, expected):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        result = sequence.insert(position, "C", keep_annotations=False)

        assert result.sequence == expected
        assert result.name == f"seq1_ins{position}"

    def test_insert_can_insert_empty_segment(self):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        result = sequence.insert(2, "", keep_annotations=False)

        assert result.sequence == "ATGC"

    @pytest.mark.parametrize("position", [-1, 5])
    def test_insert_rejects_out_of_bounds_position(self, position):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        with pytest.raises(ValueError, match="out of bounds"):
            sequence.insert(position, "C")

    def test_insert_preserves_annotations(self):
        sequence = Sequence(
            "seq1",
            "ATGC",
            seq_type="dna",
            annotations={"gene": "BRCA1"},
        )

        result = sequence.insert(2, "C", keep_annotations=True)

        assert result.info.annotations == sequence.info.annotations

    @pytest.mark.parametrize(
        ("start", "end", "expected"),
        [
            (0, 1, "TGC"),
            (1, 3, "AC"),
            (0, 4, ""),
            (4, 4, "ATGC"),
        ],
    )
    def test_delete(self, start, end, expected):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        result = sequence.delete(start, end, keep_annotations=False)

        assert result.sequence == expected
        assert result.name == f"seq1_del{start}:{end}"

    @pytest.mark.parametrize(
        ("start", "end"),
        [
            (-1, 2),
            (0, -1),
            (3, 2),
            (0, 5),
        ],
    )
    def test_delete_rejects_invalid_ranges(self, start, end):
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        with pytest.raises(ValueError, match="Invalid delete range"):
            sequence.delete(start, end)

    def test_delete_preserves_annotations(self):
        sequence = Sequence(
            "seq1",
            "ATGC",
            seq_type="dna",
            annotations={"gene": "BRCA1"},
        )

        result = sequence.delete(1, 2, keep_annotations=True)

        assert result.info.annotations == sequence.info.annotations


class TestSequenceFastaIO:
    """Tests for single-sequence FASTA input/output."""

    def test_from_fasta_returns_sequence_for_one_record(self, tmp_path):
        fasta = tmp_path / "one.fa"
        fasta.write_text(">seq1 description\nATGC\n")

        result = Sequence.from_fasta(fasta, "dna")

        assert isinstance(result, Sequence)
        assert result.name == "seq1"
        assert result.sequence == "ATGC"
        assert result.seq_type == "dna"

    def test_from_fasta_returns_sequence_list_for_multiple_records(self, tmp_path):
        fasta = tmp_path / "multiple.fa"
        fasta.write_text(">seq1\nATGC\n>seq2\nGGCC\n")

        result = Sequence.from_fasta(fasta, "dna")

        assert isinstance(result, SequenceList)
        assert len(result) == 2
        assert [seq.name for seq in result] == ["seq1", "seq2"]
        assert [seq.sequence for seq in result] == ["ATGC", "GGCC"]

    def test_from_fasta_raises_for_empty_file(self, tmp_path):
        fasta = tmp_path / "empty.fa"
        fasta.write_text("")

        with pytest.raises(NoSequenceError, match="No sequences"):
            Sequence.from_fasta(fasta, "dna")

    def test_to_fasta_writes_sequence(self, tmp_path):
        fasta = tmp_path / "output.fa"
        sequence = Sequence("seq1", "ATGC", seq_type="dna")

        sequence.to_fasta(fasta)

        assert fasta.read_text() == ">seq1\nATGC\n"

    def test_fasta_round_trip(self, tmp_path):
        fasta = tmp_path / "roundtrip.fa"
        original = Sequence("seq1", "ATGCAT", seq_type="dna")

        original.to_fasta(fasta)
        restored = Sequence.from_fasta(fasta, "dna")

        assert restored == original
        assert restored.name == original.name


class TestSequenceList:
    """Tests for SequenceList construction, FASTA I/O, and alignment."""

    def test_accepts_sequences_of_matching_type(self):
        sequences = [
            Sequence("seq1", "MKT", seq_type="protein"),
            Sequence("seq2", "MRT", seq_type="protein"),
        ]

        result = SequenceList(sequences, type="protein")

        assert isinstance(result, SequenceList)
        assert list(result) == sequences

    def test_rejects_non_sequence_items(self):
        with pytest.raises(AssertionError, match="All items must be Sequence"):
            SequenceList(["MKT"], type="protein")

    def test_rejects_mixed_sequence_types(self):
        sequences = [
            Sequence("seq1", "MKT", seq_type="protein"),
            Sequence("seq2", "ATG", seq_type="dna"),
        ]

        with pytest.raises(AssertionError, match="same type"):
            SequenceList(sequences, type="protein")

    def test_from_fasta_always_returns_sequence_list(self, tmp_path):
        fasta = tmp_path / "sequences.fa"
        fasta.write_text(">seq1\nMKT\n>seq2\nMRT\n")

        result = SequenceList.from_fasta(fasta, "protein")

        assert isinstance(result, SequenceList)
        assert len(result) == 2
        assert [seq.name for seq in result] == ["seq1", "seq2"]

    def test_from_fasta_returns_one_sequence_in_a_list(self, tmp_path):
        fasta = tmp_path / "one.fa"
        fasta.write_text(">seq1\nMKT\n")

        result = SequenceList.from_fasta(fasta, "protein")

        assert isinstance(result, SequenceList)
        assert len(result) == 1
        assert result[0].sequence == "MKT"

    def test_from_fasta_raises_for_empty_file(self, tmp_path):
        fasta = tmp_path / "empty.fa"
        fasta.write_text("")

        with pytest.raises(NoSequenceError, match="No sequences"):
            SequenceList.from_fasta(fasta, "protein")

    def test_to_fasta_writes_all_sequences(self, tmp_path):
        fasta = tmp_path / "output.fa"
        sequences = SequenceList(
            [
                Sequence("seq1", "MKT", seq_type="protein"),
                Sequence("seq2", "MRT", seq_type="protein"),
            ]
        )

        sequences.to_fasta(fasta)

        assert fasta.read_text() == ">seq1\nMKT\n>seq2\nMRT\n"

    @pytest.mark.integration
    def test_clustalomega_runs_with_installed_binary(self):
        sequences = SequenceList(
            [
                Sequence("seq1", "MKTAYIAK", seq_type="protein"),
                Sequence("seq2", "MKTAYVAK", seq_type="protein"),
                Sequence("seq3", "MKTLYIAK", seq_type="protein"),
            ]
        )

        gapped, matrix, tree = sequences.ClustalOmega()

        assert len(gapped) == len(sequences)
        assert matrix is not None
        assert tree
        assert all(len(str(seq)) == len(str(gapped[0])) for seq in gapped)

    @pytest.mark.integration
    def test_clustalomega_accepts_additional_options(self):
        sequences = SequenceList(
            [
                Sequence("seq1", "MKTAYIAK", seq_type="protein"),
                Sequence("seq2", "MKTAYVAK", seq_type="protein"),
            ]
        )

        gapped, matrix, tree = sequences.ClustalOmega("--force")

        assert len(gapped) == 2
        assert matrix is not None
        assert tree


@pytest.mark.integration
class TestViennaRNA:
    """Minimal smoke test for the installed ViennaRNA/RNAfold executable."""

    def test_vienna_returns_structure_energy_and_base_pairs(self):
        seq = Sequence("rna", "GCGCUUCGCGC", seq_type="rna")

        structure, energy, base_pairs = seq.vienna()

        assert isinstance(structure, str)
        assert len(structure) == len(seq)
        assert isinstance(energy, (int, float))
        assert isinstance(base_pairs, list)


@pytest.mark.integration
class TestClustalOmega:
    """Minimal smoke test for the installed Clustal Omega executable."""

    def test_clustalomega_returns_alignment_matrix_and_tree(self):
        sequences = SequenceList(
            [
                Sequence("seq1", "MKTAYIAKQRQISFVKSHFSRQ", seq_type="protein"),
                Sequence("seq2", "MKTAYIAKQRQISFVKSHFSRQ", seq_type="protein"),
            ]
        )

        gapped, matrix, tree = sequences.ClustalOmega()

        assert len(gapped) == 2
        assert matrix is not None
        assert isinstance(tree, str)
        assert tree


# @pytest.mark.integration
# @pytest.mark.network
# class TestNCBIBlast:
#     """Single real NCBI BLAST API smoke test."""
#
#     def test_blast_returns_hits(self):
#         seq = Sequence(
#             "blast_test",
#             "MKTAYIAKQRQISFVKSHFSRQ",
#             seq_type="protein",
#         )
#
#         results = seq.blast(
#             program="blastp",
#             database="swissprot",
#             threshold=10,
#             hitlist_size=3,
#         )
#
#         assert results is not None
#         assert len(results) > 0