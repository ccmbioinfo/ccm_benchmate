import math
import pytest

from benchmate.ranges.ranges import Range, RangesList, RangesDict
from benchmate.ranges.genomicranges import (
    GenomicRange,
    CompoundGenomicRange,
    GenomicRangesList,
    GenomicRangesDict,
)


class TestRange:
    def test_init_and_len_and_str(self):
        r = Range(10, 20)
        assert r.start == 10
        assert r.end == 20
        assert len(r) == 10
        assert "Range from 10 to 20" in str(r)

    def test_init_invalid_values(self):
        with pytest.raises(ValueError):
            Range(-1, 5)
        with pytest.raises(ValueError):
            Range(5, -1)
        with pytest.raises(ValueError):
            Range(10, 5)

    def test_shift_mutates_and_returns_self(self):
        r = Range(1, 3)
        out = r.shift(5)
        assert out is r
        assert (r.start, r.end) == (6, 8)

        with pytest.raises(ValueError):
            r.shift(-1000)

    def test_extend_mutates_and_returns_self(self):
        r = Range(10, 20)
        out = r.extend(-5, 5)
        assert out is r
        assert (r.start, r.end) == (5, 25)

        with pytest.raises(ValueError):
            r.extend(-10, -1000)

    def test_overlaps_types_and_validation(self):
        a = Range(10, 20)
        b = Range(10, 20)
        c = Range(15, 25)
        d = Range(30, 40)

        assert a.overlaps(b, type="exact") is True
        assert a.overlaps(c, type="exact") is False

        assert a.overlaps(c, type="any") is True
        assert a.overlaps(d, type="any") is False

        outer = Range(10, 30)
        inner = Range(15, 20)
        assert outer.overlaps(inner, type="within") is True
        assert inner.overlaps(outer, type="within") is False

        assert outer.overlaps(inner, type="start") is True
        assert inner.overlaps(outer, type="start") is False

        assert outer.overlaps(inner, type="end") is True
        assert inner.overlaps(outer, type="end") is False

        with pytest.raises(ValueError):
            a.overlaps(b, type="bad_type")

    def test_distance(self):
        a = Range(10, 20)
        b = Range(15, 25)
        c = Range(30, 40)

        assert a.distance(b) == 0
        assert a.distance(c) == 10

    def test_split_into_equal_parts(self):
        r = Range(0, 10)
        parts = r.split(3)
        assert isinstance(parts, RangesList)
        assert len(parts) == 3
        assert all(isinstance(p, Range) for p in parts)

        step = math.floor(10) / 3
        assert parts[0].start == 0
        assert parts[0].end == step
        assert pytest.approx(parts[2].end, rel=1e-12) == 10.0

        with pytest.raises(AssertionError):
            r.split(0)
        with pytest.raises(AssertionError):
            r.split(2.5)

    def test_add_with_range_and_int(self):
        a = Range(1, 2)
        b = Range(3, 4)
        out = a.__add__(b)
        assert out is a
        assert (a.start, a.end) == (4, 6)

        out = a.__add__(10)
        assert out is a
        assert (a.start, a.end) == (14, 16)

        with pytest.raises(NotImplementedError):
            a.__add__("x")

    def test_eq(self):
        assert Range(1, 2) == Range(1, 2)
        assert not (Range(1, 2) == Range(1, 3))
        assert not (Range(1, 2) == "not_a_range")


class TestRangesList:
    def test_constructor_and_len_and_iter(self):
        a, b = Range(1, 2), Range(3, 4)
        rl = RangesList([a, b])
        assert len(rl) == 2
        assert list(iter(rl)) == [a, b]

        with pytest.raises(AssertionError):
            RangesList([a, "bad"])

    def test_pop_insert_append_extend_remove(self):
        a, b, c = Range(1, 2), Range(3, 4), Range(5, 6)
        rl = RangesList([a, b])

        removed = rl.pop(1)
        assert removed is b
        assert len(rl) == 1

        rl.insert(1, b)
        assert len(rl) == 2
        assert rl[1] is b

        rl.append(c)
        assert len(rl) == 3
        assert rl[2] is c

        other = RangesList([Range(100, 101)])
        rl.extend(other)
        assert len(rl) == 4
        assert rl[3].start == 100

    def test_find_overlaps_return_ranges_and_indices(self):
        a = Range(10, 20)
        b = Range(15, 25)
        c = Range(30, 40)

        rl1 = RangesList([a, c])
        rl2 = RangesList([b])

        overlaps_ranges = rl1.find_overlaps(rl2, type="any", return_ranges=True)
        assert (a, b) in overlaps_ranges
        assert len(overlaps_ranges) == 1

        overlaps_indices = rl1.find_overlaps(rl2, type="any", return_ranges=False)
        assert (0, 0) in overlaps_indices
        assert len(overlaps_indices) == 1

    def test_coverage(self):
        r1 = Range(10, 20)
        r2 = Range(15, 25)
        rl = RangesList([r1, r2])

        cov = rl.coverage()
        assert len(cov) == 16

        idx = lambda pos: pos - 10
        for pos in range(10, 15):
            assert cov[idx(pos)] == 1
        for pos in range(15, 21):
            assert cov[idx(pos)] == 2
        for pos in range(21, 26):
            assert cov[idx(pos)] == 1

    def test_getitem_slice_and_index(self):
        a, b, c = Range(1, 2), Range(3, 4), Range(5, 6)
        rl = RangesList([a, b, c])

        assert rl[0] is a
        sub = rl[1:]
        assert isinstance(sub, RangesList)
        assert len(sub) == 2
        assert sub[0] is b and sub[1] is c

    def test_add_sub_contains_eq_ne_reduce_set_del(self):
        a, b, c = Range(1, 2), Range(3, 4), Range(5, 6)
        rl1 = RangesList([a, b])
        rl2 = RangesList([b, c])

        added = rl1 + rl2
        assert isinstance(added, RangesList)
        assert len(added) == 4

        subbed = rl1 - rl2
        assert isinstance(subbed, RangesList)
        assert subbed.items == [a]

        assert a in rl1
        assert c not in rl1

        rl3 = RangesList([b, a])
        assert rl1 == rl3
        assert not (rl1 != rl3)
        assert not (rl1 == "bad")

        rl1[0] = c
        assert rl1[0] is c
        del rl1[0]
        assert len(rl1) == 1 and rl1[0] is b

        rl = RangesList([Range(10, 12), Range(20, 25), Range(15, 18)])
        reduced = rl.reduce()
        assert isinstance(reduced, Range)
        assert (reduced.start, reduced.end) == (10, 25)


class TestRangesDict:
    def test_init_and_len_and_contains_and_get_set_del(self):
        a, b = Range(1, 2), Range(3, 4)
        rl = RangesList([a, b])

        rd = RangesDict(["x", "y"], [rl, a])
        assert len(rd) == 2
        assert "x" in rd
        assert "y" in rd
        assert "z" not in rd

        assert rd["x"] is rl
        rd["z"] = b
        assert rd["z"] is b
        del rd["z"]
        assert "z" not in rd

    def test_find_overlaps_and_eq_ne_str(self):
        a1 = Range(10, 20)
        a2 = Range(15, 25)
        b1 = Range(100, 110)

        rd1 = RangesDict(["A", "B"], [RangesList([a1]), RangesList([b1])])
        rd2 = RangesDict(["A", "B"], [RangesList([a2]), RangesList([b1])])

        df = rd1.to_df()
        assert "name" in df.columns and "start" in df.columns and "end" in df.columns

        assert rd1 == rd1
        assert rd1 != rd2
        assert "RangesDict(" in str(rd1)
        assert "RangesDict(" in repr(rd1)


class TestGenomicRange:
    def test_init_and_str_eq(self):
        gr1 = GenomicRange("chr1", 10, 20, "+")
        gr2 = GenomicRange("chr1", 10, 20, "+")
        gr3 = GenomicRange("chr1", 10, 20, "-")

        assert str(gr1) == "chr1:10-20(+)"
        assert "GenomicRange(chr1:10-20(+))" in repr(gr1)
        assert gr1 == gr2
        assert gr1 != gr3
        assert not (gr1 == "bad")

    def test_annotations(self):
        gr = GenomicRange("chr1", 10, 20, "+", annotation="gene1")
        assert gr.annotation == {"annot": "gene1"}
        gr.add_annotation("type", "protein_coding")
        assert gr.annotation["type"] == "protein_coding"

    def test_shift_and_extend_delegate_and_mutate(self):
        gr = GenomicRange("chr1", 10, 20, "+")
        out = gr.shift(5)
        assert out is gr
        assert (gr.ranges.start, gr.ranges.end) == (15, 25)

        out = gr.extend(-5, 5)
        assert out is gr
        assert (gr.ranges.start, gr.ranges.end) == (10, 30)

    def test_overlaps_and_distance_with_chrom_and_strand_rules(self):
        a = GenomicRange("chr1", 10, 20, "+")
        b = GenomicRange("chr1", 15, 25, "+")
        c = GenomicRange("chr2", 15, 25, "+")
        d = GenomicRange("chr1", 15, 25, "-")

        assert a.overlaps(b, type="any") is True
        assert a.distance(b) == 0

        with pytest.raises(ValueError):
            a.overlaps(c, type="any")
        with pytest.raises(ValueError):
            a.distance(c)

        with pytest.raises(ValueError):
            a.overlaps(d, type="any", ignore_strand=False)
        with pytest.raises(ValueError):
            a.distance(d, ignore_strand=False)

        assert a.overlaps(d, type="any", ignore_strand=True) is True
        assert a.distance(d, ignore_strand=True) == 0


class TestCompoundGenomicRange:
    def test_compound_genomic_range_operations(self):
        g1 = GenomicRange("chr1", 10, 20, "+")
        g2 = GenomicRange("chr2", 50, 60, "-")
        cgr = CompoundGenomicRange([g1, g2])

        assert len(cgr) == 2
        assert "CompoundGenomicRange with 2 ranges" in str(cgr)
        assert "CompoundGenomicRange with 2 ranges" in repr(cgr)

        cgr.shift(5)
        assert (cgr.ranges[0].ranges.start, cgr.ranges[0].ranges.end) == (15, 25)
        assert (cgr.ranges[1].ranges.start, cgr.ranges[1].ranges.end) == (55, 65)

        cgr.extend(-5, 5)
        assert (cgr.ranges[0].ranges.start, cgr.ranges[0].ranges.end) == (10, 30)

        other_g = GenomicRange("chr1", 15, 25, "+")
        olaps = cgr.overlaps(other_g, ignore_strand=True)
        assert olaps[0] is True

        cgr2 = CompoundGenomicRange([GenomicRange("chr1", 10, 20, "+"), GenomicRange("chr2", 50, 60, "-")])
        assert cgr != cgr2  # because cgr was shifted/extended
        assert not (cgr == "bad")


class TestGenomicRangesList:
    def test_constructor_and_len_iter_indexing(self):
        a = GenomicRange("chr1", 10, 20, "+")
        b = GenomicRange("chr1", 30, 40, "+")
        grl = GenomicRangesList([a, b])
        assert len(grl) == 2
        assert list(iter(grl)) == [a, b]
        assert grl[0] is a

        sub = grl[1:]
        assert isinstance(sub, GenomicRangesList)
        assert len(sub) == 1

    def test_pop_insert_append_extend(self):
        a = GenomicRange("chr1", 10, 20, "+")
        b = GenomicRange("chr1", 30, 40, "+")
        c = GenomicRange("chr2", 5, 15, "-")

        grl = GenomicRangesList([a, b])
        removed = grl.pop(1)
        assert removed is b
        assert len(grl) == 1

        grl.insert(1, b)
        assert len(grl) == 2 and grl[1] is b

        grl.append(c)
        assert len(grl) == 3 and grl[2] is c

    def test_find_overlaps(self):
        a_plus = GenomicRange("chr1", 10, 20, "+")
        b_plus = GenomicRange("chr1", 15, 25, "+")
        c_minus = GenomicRange("chr1", 15, 25, "-")
        d_other_chrom = GenomicRange("chr2", 15, 25, "+")

        grl1 = GenomicRangesList([a_plus, d_other_chrom])
        grl2 = GenomicRangesList([b_plus, c_minus])

        overlaps = grl1.find_overlaps(grl2, type="any", ignore_strand=False, return_ranges=True)
        assert (a_plus, b_plus) in overlaps
        assert len(overlaps) == 1

        overlaps_ign = grl1.find_overlaps(grl2, type="any", ignore_strand=True, return_ranges=False)
        assert (0, 0) in overlaps_ign
        assert (0, 1) in overlaps_ign

    def test_coverage(self):
        a = GenomicRange("chr1", 10, 12, "+")
        b = GenomicRange("chr1", 11, 13, "+")
        c = GenomicRange("chr1", 10, 10, "-")
        d = GenomicRange("chr2", 5, 6, "+")

        grl = GenomicRangesList([a, b, c, d])
        cov = grl.coverage(ignore_strand=False)
        assert set(cov.keys()) == {"chr1", "chr2"}
        assert "+" in cov["chr1"] and "-" in cov["chr1"]

        assert len(cov["chr1"]["+"]) == 4
        assert cov["chr1"]["+"][0] == 1
        assert cov["chr1"]["+"][1] == 2

    def test_reduce(self):
        r = GenomicRangesList(
            [
                GenomicRange("chrX", 10, 12, "+"),
                GenomicRange("chrX", 20, 25, "+"),
                GenomicRange("chrX", 15, 18, "-"),
            ]
        )
        reduced = r.reduce(ignore_strand=False)
        assert set(reduced.keys()) == {"chrX"}
        assert (reduced["chrX"]["+"].start, reduced["chrX"]["+"].end) == (10, 25)
        assert (reduced["chrX"]["-"].start, reduced["chrX"]["-"].end) == (15, 18)

        reduced_ign = r.reduce(ignore_strand=True)
        assert (reduced_ign["chrX"].start, reduced_ign["chrX"].end) == (10, 25)


class TestGenomicRangesDict:
    def test_init_and_len_and_contains_and_df(self):
        a = GenomicRange("chr1", 10, 20, "+", annotation="annot1")
        grl = GenomicRangesList([a])

        gd = GenomicRangesDict(["g"], [grl])
        assert len(gd) == 1
        assert "g" in gd and "z" not in gd

        assert gd["g"] is grl
        gd["z"] = a
        assert isinstance(gd["z"], GenomicRange)
        del gd["z"]
        assert "z" not in gd

        df = gd.to_df()
        assert "name" in df.columns and "chrom" in df.columns and "annotation" in df.columns

        assert gd == gd
        assert not (gd == "bad")
        assert "GenomicRangesDict(" in str(gd)
        assert "GenomicRangesDict(" in repr(gd)
