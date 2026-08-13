import pytest

from benchmate.variant.utils import infer_variant_type, to_hgvs
from benchmate.variant.variant import (
    BaseVariant,
    SequenceVariant,
    StructuralVariant,
    TandemRepeatVariant,
)


class TestBaseVariant:
    """Tests for BaseVariant state, annotations, coordinates, and conversion."""

    def test_id_is_generated_when_not_provided(self):
        variant = BaseVariant(chrom="chr1", pos=100, ref="A", alt="T")

        assert variant.id is not None
        assert isinstance(variant.id, str)
        assert variant.id

    def test_provided_id_is_preserved(self):
        variant = BaseVariant(id="var-1", chrom="chr1", pos=100, ref="A", alt="T")

        assert variant.id == "var-1"

    def test_annotations_default_to_empty_dict(self):
        variant = BaseVariant(chrom="chr1", pos=100)

        assert variant.annotations == {}

    def test_none_annotations_are_normalized_to_empty_dict(self):
        variant = BaseVariant(chrom="chr1", pos=100, annotations={})

        assert variant.annotations == {}

    def test_annotations_are_instance_specific(self):
        first = BaseVariant(chrom="chr1", pos=100)
        second = BaseVariant(chrom="chr1", pos=200)

        first.add_annotation("gene", "BRCA1")

        assert first.annotations == {"gene": "BRCA1"}
        assert second.annotations == {}

    def test_show_annotations_returns_keys(self):
        variant = BaseVariant(
            chrom="chr1",
            pos=100,
            annotations={"gene": "BRCA1", "impact": "HIGH"},
        )

        assert set(variant.show_annotations()) == {"gene", "impact"}

    def test_query_annotation_returns_value_or_none(self):
        variant = BaseVariant(
            chrom="chr1",
            pos=100,
            annotations={"gene": "BRCA1"},
        )

        assert variant.query_annotation("gene") == "BRCA1"
        assert variant.query_annotation("missing") is None

    def test_add_annotation_updates_existing_value(self):
        variant = BaseVariant(chrom="chr1", pos=100)

        variant.add_annotation("gene", "BRCA1")
        variant.add_annotation("gene", "TP53")

        assert variant.query_annotation("gene") == "TP53"

    @pytest.mark.parametrize(
        ("ref", "expected_end"),
        [
            ("A", 100),
            ("AT", 101),
            ("ATG", 102),
        ],
    )
    def test_end_is_reference_length_based(self, ref, expected_end):
        variant = BaseVariant(chrom="chr1", pos=100, ref=ref)

        assert variant.start == 100
        assert variant.end == expected_end

    def test_end_equals_position_when_reference_is_missing(self):
        variant = BaseVariant(chrom="chr1", pos=100, ref=None)

        assert variant.end == 100

    def test_positional_chrom_pos_ref_alt_compatibility(self):
        variant = BaseVariant("chr1", 12345, "A", "T")

        assert variant.chrom == "chr1"
        assert variant.pos == 12345
        assert variant.ref == "A"
        assert variant.alt == "T"
        assert variant.id is not None

    def test_to_gr_preserves_coordinates_and_annotations(self):
        variant = BaseVariant(
            chrom="chr1",
            pos=100,
            ref="AT",
            alt="GC",
            annotations={"gene": "BRCA1"},
        )

        genomic_range = variant.to_gr()

        assert genomic_range.chrom == "chr1"
        assert genomic_range.start == 100
        assert genomic_range.end == 101
        assert genomic_range.strand == "*"
        assert genomic_range.annotation == {"gene": "BRCA1"}


class TestSequenceVariant:
    """Tests for SNVs, MNVs, indels, transition detection, and representations."""

    @pytest.mark.parametrize(
        ("ref", "alt", "expected_type"),
        [
            ("A", "T", "SNV"),
            ("AT", "GC", "MNV"),
            ("A", "AT", "INS"),
            ("AT", "A", "DEL"),
        ],
    )
    def test_variant_type(self, ref, alt, expected_type):
        variant = SequenceVariant(chrom="chr1", pos=100, ref=ref, alt=alt)

        assert variant.variant_type == expected_type

    @pytest.mark.parametrize(
        ("ref", "alt", "expected"),
        [
            ("A", "T", True),
            ("AT", "GC", False),
            (None, "T", False),
            ("A", None, False),
        ],
    )
    def test_is_snv(self, ref, alt, expected):
        variant = SequenceVariant(chrom="chr1", pos=100, ref=ref, alt=alt)

        assert variant.is_snv is expected

    @pytest.mark.parametrize(
        ("ref", "alt", "expected"),
        [
            ("A", "AT", True),
            ("AT", "A", True),
            ("AT", "GC", False),
            ("A", "T", False),
            (None, "T", True),
        ],
    )
    def test_is_indel(self, ref, alt, expected):
        variant = SequenceVariant(chrom="chr1", pos=100, ref=ref, alt=alt)

        assert variant.is_indel is expected

    @pytest.mark.parametrize(
        ("ref", "alt", "expected"),
        [
            ("A", "G", True),
            ("G", "A", True),
            ("C", "T", True),
            ("T", "C", True),
            ("A", "C", False),
            ("C", "G", False),
            ("A", "AT", False),
            ("a", "g", True),
        ],
    )
    def test_is_transition(self, ref, alt, expected):
        variant = SequenceVariant(chrom="chr1", pos=100, ref=ref, alt=alt)

        assert variant.is_transition is expected

    def test_length_uses_explicit_length_when_provided(self):
        variant = SequenceVariant(
            chrom="chr1",
            pos=100,
            ref="A",
            alt="AT",
            length=25,
        )

        assert len(variant) == 25

    @pytest.mark.parametrize(
        ("ref", "alt", "expected_length"),
        [
            ("A", "T", 1),
            ("A", "AT", 2),
            ("AT", "A", 2),
            ("AT", "GC", 2),
            (None, "AT", 2),
            ("AT", None, 2),
            (None, None, 0),
        ],
    )
    def test_length_is_max_allele_length_when_not_explicit(
        self, ref, alt, expected_length
    ):
        variant = SequenceVariant(chrom="chr1", pos=100, ref=ref, alt=alt)

        assert len(variant) == expected_length

    def test_string_representation(self):
        variant = SequenceVariant(
            id="var-1",
            chrom="chr1",
            pos=100,
            ref="A",
            alt="G",
        )

        assert str(variant) == "chr1:100 A -> G (ID: var-1)"

    def test_repr_contains_variant_fields(self):
        variant = SequenceVariant(
            id="var-1",
            chrom="chr1",
            pos=100,
            ref="A",
            alt="G",
            gt="0/1",
            dp=20,
        )

        representation = repr(variant)

        assert "SequenceVariant" in representation
        assert "chrom=chr1" in representation
        assert "pos=100" in representation
        assert "ref=A" in representation
        assert "alt=G" in representation
        assert "gt=0/1" in representation
        assert "dp=20" in representation


class TestStructuralVariant:
    """Tests for structural-variant type, interval, CI, CN, overlap, and representations."""

    def test_explicit_svtype_is_used(self):
        variant = StructuralVariant(
            chrom="chr1",
            pos=100,
            ref="N",
            alt="<DEL>",
            svtype_val="DEL",
        )

        assert variant.svtype == "DEL"

    @pytest.mark.parametrize(
        ("alt", "expected_type"),
        [
            ("<DEL>", "DEL"),
            ("<DUP>", "DUP"),
            ("<INV>", "INV"),
            ("<INS>", "INS"),
            ("N[chr2:200[", "BND"),
            ("<OTHER>", "UNK"),
            (None, "UNK"),
        ],
    )
    def test_svtype_is_inferred_from_alt(self, alt, expected_type):
        variant = StructuralVariant(
            chrom="chr1",
            pos=100,
            ref="N",
            alt=alt,
        )

        assert variant.svtype == expected_type

    @pytest.mark.parametrize("svtype", ["DEL", "DUP", "INV", "INS", "BND"])
    def test_svtype_can_be_supplied_in_ref(self, svtype):
        variant = StructuralVariant(
            chrom="chr1",
            pos=100,
            ref=svtype,
            alt="<placeholder>",
        )

        assert variant.svtype == svtype
        assert variant.ref == "N"

    def test_end_uses_explicit_end(self):
        variant = StructuralVariant(
            chrom="chr1",
            pos=100,
            ref="N",
            alt="<DEL>",
            end_val=250,
        )

        assert variant.end == 250

    def test_end_is_reference_based_when_end_is_not_provided(self):
        variant = StructuralVariant(
            chrom="chr1",
            pos=100,
            ref="NNN",
            alt="<DEL>",
        )

        assert variant.end == 102

    def test_confidence_interval_applies_offsets(self):
        variant = StructuralVariant(
            chrom="chr1",
            pos=100,
            ref="N",
            alt="<DEL>",
            end_val=250,
            cistart=-5,
            ciend=10,
        )

        assert variant.confidence_interval == (95, 260)

    def test_confidence_interval_defaults_missing_offsets_to_zero(self):
        variant = StructuralVariant(
            chrom="chr1",
            pos=100,
            ref="N",
            alt="<DEL>",
            end_val=250,
        )

        assert variant.confidence_interval == (100, 250)

    @pytest.mark.parametrize(
        ("cn", "expected"),
        [
            (0, True),
            (1, True),
            (2, True),
            (None, False),
        ],
    )
    def test_is_copy_number_change(self, cn, expected):
        variant = StructuralVariant(
            chrom="chr1",
            pos=100,
            ref="N",
            alt="<DEL>",
            cn=cn,
        )

        assert variant.is_copy_number_change is expected

    def test_length_uses_svlen_when_available(self):
        variant = StructuralVariant(
            chrom="chr1",
            pos=100,
            ref="N",
            alt="<DEL>",
            svlen=150,
        )

        assert len(variant) == 150

    def test_length_falls_back_to_allele_difference(self):
        variant = StructuralVariant(
            chrom="chr1",
            pos=100,
            ref="AAAA",
            alt="A",
        )

        assert len(variant) == 3

    def test_length_is_zero_without_svlen_or_both_alleles(self):
        variant = StructuralVariant(
            chrom="chr1",
            pos=100,
            ref=None,
            alt="<DEL>",
        )

        assert len(variant) == 0

    def test_reciprocal_overlap_for_partially_overlapping_variants(self):
        first = StructuralVariant(
            chrom="chr1",
            pos=100,
            ref="N",
            alt="<DEL>",
            end_val=200,
            svlen=100,
        )
        second = StructuralVariant(
            chrom="chr1",
            pos=150,
            ref="N",
            alt="<DEL>",
            end_val=250,
            svlen=100,
        )

        # The implementation uses end - start for overlap.
        assert first.reciprocal_overlap(second) == pytest.approx(0.5)

    def test_reciprocal_overlap_is_zero_for_nonoverlapping_variants(self):
        first = StructuralVariant(
            chrom="chr1",
            pos=100,
            ref="N",
            alt="<DEL>",
            end_val=150,
            svlen=50,
        )
        second = StructuralVariant(
            chrom="chr1",
            pos=200,
            ref="N",
            alt="<DEL>",
            end_val=250,
            svlen=50,
        )

        assert first.reciprocal_overlap(second) == 0.0

    def test_reciprocal_overlap_requires_structural_variant(self):
        variant = StructuralVariant(
            chrom="chr1",
            pos=100,
            ref="N",
            alt="<DEL>",
            end_val=150,
            svlen=50,
        )

        with pytest.raises(AssertionError):
            variant.reciprocal_overlap(
                SequenceVariant(chrom="chr1", pos=100, ref="A", alt="T")
            )

    def test_string_representation(self):
        variant = StructuralVariant(
            id="sv-1",
            chrom="chr1",
            pos=100,
            ref="N",
            alt="<DEL>",
            end_val=250,
        )

        assert str(variant) == "chr1:100-250 DEL N -> <DEL> (ID: sv-1)"

    def test_string_representation_without_explicit_end(self):
        variant = StructuralVariant(
            id="sv-1",
            chrom="chr1",
            pos=100,
            ref=None,
            alt="<DEL>",
        )

        assert str(variant) == "chr1:100-N/A DEL None -> <DEL> (ID: sv-1)"

    def test_repr_contains_structural_variant_fields(self):
        variant = StructuralVariant(
            id="sv-1",
            chrom="chr1",
            pos=100,
            ref="N",
            alt="<DEL>",
            end_val=250,
            svlen=150,
            cn=1,
        )

        representation = repr(variant)

        assert "StructuralVariant" in representation
        assert "id=sv-1" in representation
        assert "chrom=chr1" in representation
        assert "svtype=DEL" in representation
        assert "end=250" in representation
        assert "svlen=150" in representation
        assert "cn=1" in representation


class TestTandemRepeatVariant:
    """Tests for tandem-repeat coordinates, repeat counts, and state."""

    def test_end_uses_explicit_end(self):
        variant = TandemRepeatVariant(
            chrom="chr1",
            pos=100,
            ref="AT",
            alt="ATAT",
            end_val=110,
        )

        assert variant.end == 110

    def test_end_falls_back_to_base_variant_end(self):
        variant = TandemRepeatVariant(
            chrom="chr1",
            pos=100,
            ref="AT",
            alt="ATAT",
        )

        assert variant.end == 101

    def test_end_can_be_supplied_as_ref_positional_compatibility(self):
        variant = TandemRepeatVariant(
            chrom="chr1",
            pos=100,
            ref=150,
            alt="ATAT",
        )

        assert variant.end_val == 150
        assert variant.ref is None
        assert variant.end == 150

    @pytest.mark.parametrize(
        ("motif", "al", "expected"),
        [
            ("CAG", 12, 4.0),
            ("CA", 10, 5.0),
            ("CAG", None, None),
            (None, 12, None),
        ],
    )
    def test_repeat_count(self, motif, al, expected):
        variant = TandemRepeatVariant(
            chrom="chr1",
            pos=100,
            motif=motif,
            al=al,
        )

        assert variant.repeat_count == expected

    @pytest.mark.parametrize(
        ("ref", "alt", "expansion", "contraction"),
        [
            ("CAG", "CAGCAG", True, False),
            ("CAGCAG", "CAG", False, True),
            ("CAG", "CAG", False, False),
            (None, "CAG", True, False),
        ],
    )
    def test_expansion_and_contraction(
        self, ref, alt, expansion, contraction
    ):
        variant = TandemRepeatVariant(
            chrom="chr1",
            pos=100,
            ref=ref,
            alt=alt,
        )

        assert variant.is_expansion is expansion
        assert variant.is_contraction is contraction

    @pytest.mark.parametrize(
        ("al", "expected_length"),
        [
            (10, 10),
            (0, 0),
            (None, 0),
        ],
    )
    def test_length(self, al, expected_length):
        variant = TandemRepeatVariant(
            chrom="chr1",
            pos=100,
            al=al,
        )

        assert len(variant) == expected_length

    def test_string_representation(self):
        variant = TandemRepeatVariant(
            id="tr-1",
            chrom="chr1",
            pos=100,
            end_val=120,
            motif="CAG",
            gt="0/1",
        )

        assert str(variant) == "chr1:100-120 TR CAG (GT: 0/1, ID: tr-1)"

    def test_repr_contains_tandem_repeat_fields(self):
        variant = TandemRepeatVariant(
            id="tr-1",
            chrom="chr1",
            pos=100,
            end_val=120,
            motif="CAG",
            al=12,
            gt="0/1",
        )

        representation = repr(variant)

        assert "TandemRepeatVariant" in representation
        assert "chrom=chr1" in representation
        assert "pos=100" in representation
        assert "end=120" in representation
        assert "motif=CAG" in representation
        assert "al=12" in representation


class TestInferVariantType:
    """Tests for infer_variant_type in utils.py."""

    @pytest.mark.parametrize(
        ("ref", "alt", "expected"),
        [
            ("A", "G", "snv"),
            ("A", "AT", "insertion"),
            ("AT", "A", "deletion"),
            ("AT", "GC", "indel"),
            ("AT", "ATAT", "duplication"),
            ("A", "chr2:200", "translocation"),
        ],
    )
    def test_infer_variant_type(self, ref, alt, expected):
        assert infer_variant_type(ref, alt) == expected

    @pytest.mark.parametrize(
        ("ref", "alt"),
        [
            (None, "A"),
            ("A", None),
            ("", "A"),
            ("A", ""),
        ],
    )
    def test_missing_alleles_raise(self, ref, alt):
        with pytest.raises(
            ValueError,
            match="Reference and alternative alleles must be provided",
        ):
            infer_variant_type(ref, alt)

    def test_identical_alleles_raise(self):
        with pytest.raises(ValueError, match="Cannot infer variant type"):
            infer_variant_type("A", "A")


class TestToHgvs:
    """Tests for the simplified genomic HGVS conversion in utils.py."""

    @pytest.mark.parametrize(
        ("variant", "expected"),
        [
            (
                SequenceVariant(chrom="chr1", pos=100, ref="A", alt="G"),
                "chr1:g.100A>G",
            ),
            (
                SequenceVariant(chrom="chr1", pos=100, ref="A", alt="AT"),
                "chr1:g.100_101insAT",
            ),
            (
                SequenceVariant(chrom="chr1", pos=100, ref="AT", alt="A"),
                "chr1:g.100_101del",
            ),
            (
                SequenceVariant(chrom="chr1", pos=100, ref="AT", alt="ATAT"),
                "chr1:g.100_101dup",
            ),
            (
                SequenceVariant(chrom="chr1", pos=100, ref="AT", alt="GC"),
                "chr1:g.100_101delinsGC",
            ),
            (
                SequenceVariant(chrom="chr1", pos=100, ref="A", alt="chr2:200"),
                "chr1:g.100t(chr2:200)",
            ),
        ],
    )
    def test_to_hgvs(self, variant, expected):
        assert to_hgvs(variant) == expected

    def test_chromosome_prefix_is_normalized(self):
        variant = SequenceVariant(chrom="chr7", pos=123, ref="C", alt="T")

        assert to_hgvs(variant) == "chr7:g.123C>T"

    def test_to_hgvs_propagates_invalid_alleles(self):
        variant = SequenceVariant(chrom="chr1", pos=100, ref=None, alt="A")

        with pytest.raises(
            ValueError,
            match="Reference and alternative alleles must be provided",
        ):
            to_hgvs(variant)