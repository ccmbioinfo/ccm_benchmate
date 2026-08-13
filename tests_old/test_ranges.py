import math
import pytest

from benchmate.ranges.ranges import Range, RangesList, RangesDict
from benchmate.ranges.genomicranges import (
    GenomicRange,
    GenomicRangesList,
    GenomicRangesDict,
)


class TestRange:
    def test_init_and_len_and_str(self):
        r = Range(10, 20)
        assert r.start == 10
        assert r.end == 20
        # length is end - start (closed interval handling is only in coverage, not in __len__)
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

        # shifting to invalid range should raise
        with pytest.raises(ValueError):
            r.shift(-1000)

    def test_extend_mutates_and_returns_self(self):
        r = Range(10, 20)
        out = r.extend(-5, 5)
        assert out is r
        assert (r.start, r.end) == (5, 25)

        with pytest.raises(ValueError):
            r.extend(-10, -1000)  # would make start < 0 or start > end

    def test_overlaps_types_and_validation(self):
        a = Range(10, 20)
        b = Range(10, 20)
        c = Range(15, 25)
        d = Range(30, 40)

        # exact
        assert a.overlaps(b, type="exact") is True
        assert a.overlaps(c, type="exact") is False

        # any
        assert a.overlaps(c, type="any") is True
        assert a.overlaps(d, type="any") is False

        # within (self contains other fully)
        outer = Range(10, 30)
        inner = Range(15, 20)
        assert outer.overlaps(inner, type="within") is True
        assert inner.overlaps(outer, type="within") is False

        # start
        assert outer.overlaps(inner, type="start") is True
        assert inner.overlaps(outer, type="start") is False  # overlaps and self.start <= other.start

        # end
        assert outer.overlaps(inner, type="end") is True
        assert inner.overlaps(outer, type="end") is False  # overlaps and self.end >= other.end

        # invalid type
        with pytest.raises(ValueError):
            a.overlaps(b, type="bad_type")

    def test_distance(self):
        a = Range(10, 20)
        b = Range(15, 25)  # overlapping
        c = Range(30, 40)  # non-overlapping

        assert a.distance(b) == 0
        # min distance between endpoints: min(|10-30|, |20-40|, |10-40|, |20-30|) = min(20,20,30,10)=10
        assert a.distance(c) == 10

    def test_split_into_equal_parts(self):
        r = Range(0, 10)
        parts = r.split(3)
        # returns RangesList
        assert isinstance(parts, RangesList)
        assert len(parts) == 3
        assert all(isinstance(p, Range) for p in parts)

        # step uses floor(end-start)/n -> floor(10)/3 == 10/3
        step = math.floor(10) / 3
        assert parts[0].start == 0
        assert parts[0].end == 0 + step
        assert parts[1].start == 0 + step
        assert parts[1].end == 0 + 2 * step
        assert parts[2].start == 0 + 2 * step
        # allow for floating rounding
        assert pytest.approx(parts[2].end, rel=1e-12) == 10.0

        with pytest.raises(AssertionError):
            r.split(0)
        with pytest.raises(AssertionError):
            r.split(2.5)

    def test_add_with_range_and_int(self):
        a = Range(1, 2)
        b = Range(3, 4)
        # Adding mutates self and returns self
        out = a.__add__(b)
        assert out is a
        assert (a.start, a.end) == (1 + 3, 2 + 4)

        out = a.__add__(10)
        assert out is a
        assert (a.start, a.end) == (1 + 3 + 10, 2 + 4 + 10)

        with pytest.raises(NotImplementedError):
            a.__add__("x")

    def test_eq(self):
        assert Range(1, 2) == Range(1, 2)
        assert not (Range(1, 2) == Range(1, 3))


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

        rl.insert(1, b)  # no return
        assert len(rl) == 2
        assert rl[1] is b

        rl.append(c)
        assert len(rl) == 3
        assert rl[2] is c

        other = RangesList([Range(100, 101)])
        rl.extend(other)
        assert len(rl) == 4
        assert rl[3].start == 100

        rl.remove(b)
        assert len(rl) == 3
        assert all(x is not b for x in rl)

        with pytest.raises(AssertionError):
            rl.pop("0")
        with pytest.raises(AssertionError):
            rl.insert("0", a)
        with pytest.raises(AssertionError):
            rl.insert(0, "bad")
        with pytest.raises(AssertionError):
            rl.append("bad")
        with pytest.raises(AssertionError):
            rl.extend("bad")
        with pytest.raises(AssertionError):
            rl.remove("bad")

    def test_find_overlaps_return_ranges_and_indices(self):
        a = Range(10, 20)
        b = Range(15, 25)
        c = Range(30, 40)

        rl1 = RangesList([a, c])
        rl2 = RangesList([b])

        overlaps_ranges = rl1.find_overlaps(rl2, type="any", return_ranges=True)
        # Only (a,b) overlaps
        assert (a, b) in overlaps_ranges
        # behavior currently includes non-overlaps only when overlap != None, so False won't be added.
        assert all(isinstance(x[0], Range) and isinstance(x[1], Range) for x in overlaps_ranges)

        overlaps_indices = rl1.find_overlaps(rl2, type="any", return_ranges=False)
        assert (0, 0) in overlaps_indices
        assert all(isinstance(i, int) and isinstance(j, int) for (i, j) in overlaps_indices)

    def test_coverage(self):
        # two ranges overlapping at [15..20], inclusive coverage logic inside method
        r1 = Range(10, 20)
        r2 = Range(15, 25)
        rl = RangesList([r1, r2])

        cov = rl.coverage()
        # coverage length = max - min + 1 = 25 - 10 + 1 = 16
        assert len(cov) == 16

        # translate positions to indices
        idx = lambda pos: pos - 10

        # positions 10..14 covered by r1 only -> 1
        for pos in range(10, 15):
            assert cov[idx(pos)] == 1

        # positions 15..20 covered by both -> 2
        for pos in range(15, 21):
            assert cov[idx(pos)] == 2

        # positions 21..25 covered by r2 only -> 1
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

        # __contains__ asserts the item is a RangesList (per current implementation)
        with pytest.raises(AssertionError):
            _ = a in rl1  # triggers assertion in __contains__

        # equality compares content ignoring order presence-wise
        rl3 = RangesList([b, a])
        assert rl1 == rl3
        assert not (rl1 != rl3)

        # setitem and delitem
        rl1[0] = c
        assert rl1[0] is c
        del rl1[0]
        assert len(rl1) == 1 and rl1[0] is b

        # reduce returns a single Range spanning min..max
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

        with pytest.raises(AssertionError):
            RangesDict([1], [rl])
        with pytest.raises(AssertionError):
            RangesDict(["x"], ["bad"])

        with pytest.raises(AssertionError):
            _ = rd[1]
        with pytest.raises(AssertionError):
            rd[1] = rl  # bad key type
        with pytest.raises(AssertionError):
            rd["k"] = "bad"  # bad value type
        with pytest.raises(AssertionError):
            del rd[1]

    def test_find_overlaps_and_eq_ne_str(self):
        a1 = Range(10, 20)
        a2 = Range(15, 25)
        b1 = Range(100, 110)

        rd1 = RangesDict(["A", "B"], [RangesList([a1]), RangesList([b1])])
        rd2 = RangesDict(["A", "B"], [RangesList([a2]), RangesList([b1])])

        overlaps = rd1.find_overlaps(rd2, type="any")
        assert "A" in overlaps and "B" in overlaps
        # "A" has overlap (a1, a2)
        assert isinstance(overlaps["A"], list) and len(overlaps["A"]) == 1
        # "B" has overlap (b1, b1)
        assert isinstance(overlaps["B"], list) and len(overlaps["B"]) == 1

        assert rd1 == rd1
        assert rd1 != rd2
        assert "RangesDict(" in str(rd1)
        assert "RangesDict(" in repr(rd1)


class TestGenomicRange:
    def test_init_and_str_eq(self):
        gr1 = GenomicRange("chr1", 10, 20, "+")
        gr2 = GenomicRange("chr1", 10, 20, "+")
        gr3 = GenomicRange("chr1", 15, 25, "+")

        assert str(gr1) == "chr1:10-20(+)"
        assert "GenomicRange(chr1:10-20(+))" in repr(gr1)
        assert gr1 == gr2
        assert not (gr1 == gr3)

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

        # basic overlap and distance
        assert a.overlaps(b, type="any") is True
        assert a.distance(b) == 0

        # chrom mismatch
        with pytest.raises(ValueError):
            a.overlaps(c, type="any")
        with pytest.raises(ValueError):
            a.distance(c)

        # strand mismatch unless ignore_strand
        with pytest.raises(ValueError):
            a.overlaps(d, type="any", ignore_strand=False)
        with pytest.raises(ValueError):
            a.distance(d, ignore_strand=False)

        assert a.overlaps(d, type="any", ignore_strand=True) is True
        assert a.distance(d, ignore_strand=True) == 0

        # type validation
        with pytest.raises(ValueError):
            a.overlaps(b, type="bad_type")


class TestGenomicRangesList:
    def test_constructor_and_len_iter_indexing(self):
        a = GenomicRange("chr1", 10, 20, "+")
        b = GenomicRange("chr1", 30, 40, "+")
        grl = GenomicRangesList([a, b])
        assert len(grl) == 2
        assert list(iter(grl)) == [a, b]
        assert grl[0] is a

        with pytest.raises(AssertionError):
            GenomicRangesList([a, "bad"])

        # slice returns a RangesList (from ranges module), per current implementation
        sub = grl[1:]
        from benchmate.ranges.genomicranges import GenomicRangesList as GRL  # type check only
        assert isinstance(sub, GRL)
        assert len(sub) == 1

    def test_pop_insert_append_extend_remove(self):
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

        other = GenomicRangesList([GenomicRange("chrX", 1, 2, "+")])
        grl.extend(other)
        assert len(grl) == 4

        grl.remove(b)
        assert len(grl) == 3 and all(x is not b for x in grl)

        with pytest.raises(AssertionError):
            grl.pop("0")
        with pytest.raises(AssertionError):
            grl.insert("0", a)
        with pytest.raises(AssertionError):
            grl.insert(0, "bad")
        with pytest.raises(AssertionError):
            grl.append("bad")
        with pytest.raises(AssertionError):
            grl.extend("bad")
        with pytest.raises(AssertionError):
            grl.remove("bad")

    def test_find_overlaps_ignore_strand_and_types(self):
        a_plus = GenomicRange("chr1", 10, 20, "+")
        b_plus = GenomicRange("chr1", 15, 25, "+")
        c_minus = GenomicRange("chr1", 15, 25, "-")
        d_other_chrom = GenomicRange("chr2", 15, 25, "+")

        grl1 = GenomicRangesList([a_plus, d_other_chrom])
        grl2 = GenomicRangesList([b_plus, c_minus])

        # default ignore_strand=False -> overlap only for same strand and chrom
        overlaps = grl1.find_overlaps(grl2, type="any", ignore_strand=False, return_ranges=True)
        assert (a_plus, b_plus) in overlaps
        assert all(isinstance(x[0], GenomicRange) and isinstance(x[1], GenomicRange) for x in overlaps)

        # ignore strand -> both (a_plus,b_plus) and (a_plus,c_minus) count
        overlaps_ign = grl1.find_overlaps(grl2, type="any", ignore_strand=True, return_ranges=False)
        assert (0, 0) in overlaps_ign
        assert (0, 1) in overlaps_ign
        # different chromosome pairs are skipped

    def test_coverage_grouped_by_chrom_and_strand(self):
        a = GenomicRange("chr1", 10, 12, "+")  # 10..12
        b = GenomicRange("chr1", 11, 13, "+")  # 11..13
        c = GenomicRange("chr1", 10, 10, "-")  # only 10 on minus
        d = GenomicRange("chr2", 5, 6, "+")    # chr2

        grl = GenomicRangesList([a, b, c, d])
        cov = grl.coverage(ignore_strand=False)
        assert set(cov.keys()) == {"chr1", "chr2"}
        assert "+" in cov["chr1"] and "-" in cov["chr1"]

        # chr1 plus spans 10..13 -> length 4
        assert len(cov["chr1"]["+"]) == 4
        # coverage values:
        # pos 10: a -> 1
        # pos 11: a,b -> 2
        # pos 12: a,b -> 2
        # pos 13: b -> 1
        # array indices relative to min(10)
        assert cov["chr1"]["+"][0] == 1
        assert cov["chr1"]["+"][1] == 2
        assert cov["chr1"]["+"][2] == 2
        assert cov["chr1"]["+"][3] == 1

        # chr1 minus has only c at pos 10
        assert len(cov["chr1"]["-"]) == 1
        assert cov["chr1"]["-"][0] == 1

        # chr2 plus spans 5..6 -> length 2
        assert len(cov["chr2"]["+"]) == 2
        assert cov["chr2"]["+"][0] == 1 and cov["chr2"]["+"][1] == 1
        assert cov["chr2"]["-"] == []

        cov_ign = grl.coverage(ignore_strand=True)
        # combined per chrom
        assert set(cov_ign.keys()) == {"chr1", "chr2"}
        assert isinstance(cov_ign["chr1"], list)
        # min..max for chr1 ranges are 10..13 -> length 4
        assert len(cov_ign["chr1"]) == 4

    def test_add_sub_contains_eq_ne_reduce_set_del(self):
        a = GenomicRange("chr1", 10, 20, "+")
        b = GenomicRange("chr1", 30, 40, "+")
        c = GenomicRange("chr1", 50, 60, "-")

        grl1 = GenomicRangesList([a, b])
        grl2 = GenomicRangesList([b, c])

        added = grl1 + grl2
        assert isinstance(added, GenomicRangesList)
        assert len(added) == 4

        subbed = grl1 - grl2
        assert isinstance(subbed, GenomicRangesList)
        assert subbed.items == [a]

        # __contains__ expects GenomicRange
        assert a in grl1
        with pytest.raises(AssertionError):
            _ = "bad" in grl1

        grl3 = GenomicRangesList([b, a])
        assert grl1 == grl3
        assert not (grl1 != grl3)

        grl1[0] = c
        assert grl1[0] is c
        del grl1[0]
        assert len(grl1) == 1 and grl1[0] is b

        # reduce groups by chrom and strand and reduces with RangesList.reduce
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
    def test_init_and_len_and_contains_and_get_set_del(self):
        a = GenomicRange("chr1", 10, 20, "+")
        grl = GenomicRangesList([a])

        gd = GenomicRangesDict(["g"], [grl])
        assert len(gd) == 1
        assert "g" in gd and "z" not in gd

        assert gd["g"] is grl
        gd["z"] = a
        assert isinstance(gd["z"], GenomicRange)
        del gd["z"]
        assert "z" not in gd

        with pytest.raises(AssertionError):
            GenomicRangesDict([1], [grl])
        with pytest.raises(AssertionError):
            GenomicRangesDict(["g"], ["bad"])

        with pytest.raises(AssertionError):
            _ = gd[1]
        with pytest.raises(AssertionError):
            gd[1] = grl
        with pytest.raises(AssertionError):
            gd["k"] = "bad"
        with pytest.raises(AssertionError):
            del gd[1]

    def test_find_overlaps_and_eq_ne_str(self):
        a1 = GenomicRange("chr1", 10, 20, "+")
        a2 = GenomicRange("chr1", 15, 25, "+")
        b1 = GenomicRange("chr2", 100, 110, "-")

        gd1 = GenomicRangesDict(["A", "B"], [GenomicRangesList([a1]), GenomicRangesList([b1])])
        gd2 = GenomicRangesDict(["A", "B"], [GenomicRangesList([a2]), GenomicRangesList([b1])])

        overlaps = gd1.find_overlaps(gd2, type="any", ignore_strand=False)
        assert "A" in overlaps and "B" in overlaps
        assert len(overlaps["A"]) == 1  # (a1, a2)
        assert len(overlaps["B"]) == 1  # (b1, b1)

        assert gd1 == gd1
        assert gd1 != gd2
        assert "GenomicRangesDict(" in str(gd1)
        assert "GenomicRangesDict(" in repr(gd1)