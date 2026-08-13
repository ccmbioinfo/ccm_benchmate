from typing import KeysView

from benchmate.variant.variant import (
    BaseVariant,
    SequenceVariant,
    StructuralVariant,
    TandemRepeatVariant,
)


class TestBaseVariant:
    def test_init_and_annotations(self):
        v = BaseVariant("chr1", 12345, filter="PASS", id="VAR1")
        assert v.chrom == "chr1"
        assert v.pos == 12345
        assert v.filter == "PASS"
        assert v.id == "VAR1"
        assert isinstance(v.annotations, dict)
        assert len(v.annotations) == 0

        # add/query/show annotations
        v.add_annotation("impact", "HIGH")
        v.add_annotation("gene", "BRCA1")
        assert v.query_annotation("impact") == "HIGH"
        assert v.query_annotation("gene") == "BRCA1"
        assert v.query_annotation("missing") is None

        keys = v.show_annotations()
        # keys() view is expected
        assert isinstance(keys, KeysView)
        assert set(keys) == {"impact", "gene"}

    def test_auto_id_generation(self):
        v = BaseVariant("chr2", 1)
        assert isinstance(v.id, str) and len(v.id) > 0


class TestSequenceVariant:
    def test_init_and_len_behavior(self):
        # explicit length overrides computation
        sv = SequenceVariant("chr1", 100, "A", "T", length=5, id="S1")
        assert len(sv) == 5

        # falls back to max(len(ref), len(alt))
        sv2 = SequenceVariant("chr1", 101, "A", "ATGC", id="S2")
        assert len(sv2) == 4

        sv3 = SequenceVariant("chr1", 102, "AT", "G", id="S3")
        assert len(sv3) == 2

        # missing ref/alt -> 0
        sv4 = SequenceVariant("chr1", 103, ref=None, alt=None, id="S4")
        assert len(sv4) == 0

    def test_str_and_repr(self):
        sv = SequenceVariant(
            chrom="chrX",
            pos=999,
            ref="C",
            alt="G",
            filter="q10",
            qual=99.1,
            gq=50.0,
            gt="0/1",
            dp=42,
            ad=[30, 12],
            ps="PS1",
            id="S1",
        )
        s = str(sv)
        r = repr(sv)
        assert s == "chrX:999 C -> G (ID: S1)"
        # repr contains all fields
        for fragment in [
            "SequenceVariant(",
            "chrom=chrX",
            "pos=999",
            "ref=C",
            "alt=G",
            "filter=q10",
            "qual=99.1",
            "gq=50.0",
            "gt=0/1",
            "dp=42",
            "ad=[30, 12]",
            "ps=PS1",
            "id=S1",
        ]:
            assert fragment in r

    def test_annotations_inherited(self):
        sv = SequenceVariant("chr1", 10, "A", "T")
        sv.add_annotation("function", "missense")
        assert sv.query_annotation("function") == "missense"


class TestStructuralVariant:
    def test_len_priority_and_fallbacks(self):
        # svlen provided
        sv = StructuralVariant("chr1", 1000, "DEL", end=1100, svlen=100, id="SV1")
        assert len(sv) == 100

        # no svlen -> |len(ref)-len(alt)|
        sv2 = StructuralVariant("chr1", 2000, "INS", ref="A", alt="ATG", id="SV2")
        assert len(sv2) == 2

        # nothing available -> 0
        sv3 = StructuralVariant("chr1", 3000, "BND", id="SV3")
        assert len(sv3) == 0

    def test_str_and_repr(self):
        sv = StructuralVariant(
            chrom="chr2",
            pos=500,
            svtype="INV",
            end=800,
            ref="N",
            alt="<INV>",
            filter="PASS",
            qual=12.3,
            gt="1/1",
            dp=20,
            ad=[0, 20],
            svlen=None,
            mateid="m1",
            cn=3,
            cistart=5,
            ciend=10,
            mei_type=None,
            sr=10,
            pr=5,
            ps="PS2",
            id="SVX",
        )
        s = str(sv)
        r = repr(sv)
        assert s == "chr2:500-800 INV N -> <INV> (ID: SVX)"
        for fragment in [
            "StructuralVariant(",
            "chrom=chr2",
            "pos=500",
            "svtype=INV",
            "end=800",
            "ref=N",
            "alt=<INV>",
            "filter=PASS",
            "qual=12.3",
            "gt=1/1",
            "dp=20",
            "ad=[0, 20]",
            "mateid=m1",
            "cn=3",
            "cistart=5",
            "ciend=10",
            "sr=10",
            "pr=5",
            "ps=PS2",
            "id=SVX",
        ]:
            assert fragment in r

    def test_str_uses_na_when_end_missing(self):
        sv = StructuralVariant("chr3", 100, "DUP", end=None, ref="N", alt="<DUP>", id="SVM")
        assert str(sv) == "chr3:100-N/A DUP N -> <DUP> (ID: SVM)"


class TestTandemRepeatVariant:
    def test_len_uses_al(self):
        tr = TandemRepeatVariant("chr1", 1000, 1050, al=20, id="TR1")
        assert len(tr) == 20

        tr2 = TandemRepeatVariant("chr1", 1000, 1050, al=None, id="TR2")
        assert len(tr2) == 0

    def test_str_and_repr(self):
        tr = TandemRepeatVariant(
            chrom="chr5",
            pos=200,
            end=240,
            gt="10/12",
            motif="CAG",
            al=12,
            ref="CAG10",
            alt="CAG12",
            filter="PASS",
            ms=100,
            mc=2,
            ap=0.95,
            am=0.05,
            sd=3,
            id="TRX",
        )
        s = str(tr)
        r = repr(tr)
        assert s == "chr5:200-240 TR CAG (GT: 10/12, ID: TRX)"
        for fragment in [
            "TandemRepeatVariant(",
            "chrom=chr5",
            "pos=200",
            "end=240",
            "gt=10/12",
            "motif=CAG",
            "al=12",
            "ref=CAG10",
            "alt=CAG12",
            "filter=PASS",
            "ms=100",
            "mc=2",
            "ap=0.95",
            "am=0.05",
            "sd=3",
            "id=TRX",
        ]:
            assert fragment in r

    def test_annotations_inherited(self):
        tr = TandemRepeatVariant("chr1", 1, 2, id="TRANN")
        tr.add_annotation("locus", "HTT")
        assert tr.query_annotation("locus") == "HTT"