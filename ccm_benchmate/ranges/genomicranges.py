
from ccm_benchmate.ranges.ranges import Range, RangesList


class GenomicRange:
    def __init__(self, chrom, start, end, strand, annotation=None):
        self.chrom = chrom
        self.strand = strand
        self.ranges = Range(start, end)
        self.annotation = annotation

    def shift(self, amount):
        self.ranges=self.ranges.shift(amount)
        return self

    def extend(self, start, end):
        self.ranges=self.ranges.extend(start, end)
        return self

    def overlaps(self, other, ignore_strand=False, type="exact"):
        overlap_types=["exact", "within", "start", "end", "any"]
        if type not in overlap_types:
            raise ValueError(f"overlap_type must be one of {overlap_types}")

        if self.chrom != other.chrom:
            raise ValueError("Genomic ranges must have same chrom")

        if not ignore_strand:
            if self.strand != other.strand:
                raise ValueError("Genomic ranges must have same strand")

        return self.ranges.overlaps(other.ranges, type=type)

    def distance(self, other, ignore_strand=False):
        assert(isinstance(other, GenomicRange))
        if self.chrom != other.chrom:
            raise ValueError("Genomic ranges must have same chrom")
        if not ignore_strand:
            if self.strand != other.strand:
                raise ValueError("Genomic ranges must have same strand")
        return self.ranges.distance(other.ranges)


    def __str__(self):
        return f"{self.chrom}:{self.ranges.start}-{self.ranges.end}({self.strand})"

    def __repr__(self):
        return f"GenomicRange({self.chrom}:{self.ranges.start}-{self.ranges.end}({self.strand}))"


    def __eq__(self, other, ignore_strand=False):
        if self.chrom != other.chrom:
            return False
        else:
            if ignore_strand and self.strand == other.strand:
                return self.ranges == other.ranges
            else:
                return self.ranges == other.ranges


class GenomicRangesList:
    def __init__(self, granges):
        for item in granges:
            assert isinstance(item, GenomicRange)

        self.items = granges

    def pop(self, index):
        assert (isinstance(index, int))
        return self.items.pop(index)

    def insert(self, index, value):
        assert (isinstance(index, int))
        assert (isinstance(value, GenomicRange))
        self.items.insert(index, value)

    def append(self, item):
        assert (isinstance(item, GenomicRange))
        self.items.append(item)

    def extend(self, other):
        assert (isinstance(other, GenomicRangesList))
        self.items.extend(other.items)

    def remove(self, item):
        assert (isinstance(item, GenomicRange))
        self.items.remove(item)

    def find_overlaps(self, other=None, type="exact", ignore_strand=False, return_ranges=True):
        if other is None:
            other = self
        assert (isinstance(other, GenomicRangesList))
        overlaps = []
        for i in range(len(self)):
            for j in range(len(other)):
                if self.items[i].chrom != other.items[j].chrom:
                    continue
                else:
                    if not ignore_strand:
                        if self.items[i].strand != other.items[j].strand:
                            continue
                        else:
                            overlap = self.items[i].overlaps(other.items[j], ignore_strand=False,
                                                             type=type)
                    else:
                        overlap = self.items[i].overlaps(other.items[j], ignore_strand=True, type=type)

                if overlap is not None:
                    if return_ranges:
                        overlaps.append((self.items[i], other.items[j]))
                    else:
                        overlaps.append((i, j))
        return overlaps

    def coverage(self, ignore_strand=False):
       """
       Calculate coverage depth at each position per chromosome and strand.

       :param ignore_strand: If True, combines coverage from both strands
       :return: Dictionary of chromosomes, each containing coverage arrays
               (either single array or separate arrays for + and - strands)
       """
       if not self.items:
           return {}

       # Group ranges by chromosome
       chrom_ranges = {}
       for grange in self.items:
           if grange.chrom not in chrom_ranges:
               if not ignore_strand:
                   chrom_ranges[grange.chrom] = {"+": [], "-": []}
               else:
                   chrom_ranges[grange.chrom] = []

           if not ignore_strand:
               chrom_ranges[grange.chrom][grange.strand].append(grange.ranges)
           else:
               chrom_ranges[grange.chrom].append(grange.ranges)

       # Calculate coverage for each chromosome
       coverage_dict = {}
       for chrom in chrom_ranges:
           if not ignore_strand:
               # Calculate coverage separately for each strand
               coverage_dict[chrom] = {
                   "+": self._calculate_coverage(chrom_ranges[chrom]["+"]),
                   "-": self._calculate_coverage(chrom_ranges[chrom]["-"])
               }
           else:
               # Calculate combined coverage
               coverage_dict[chrom] = self._calculate_coverage(chrom_ranges[chrom])

       return coverage_dict

    def _calculate_coverage(self, ranges):
       """
       Helper method to calculate coverage for a list of ranges.

       :param ranges: List of Range objects
       :return: List of coverage depths
       """
       if not ranges:
           return []

       # Find the overall span
       min_pos = min(r.start for r in ranges)
       max_pos = max(r.end for r in ranges)
       length = max_pos - min_pos + 1

       # Initialize coverage array
       coverage = [0] * length

       # Count coverage for each range
       for range_obj in ranges:
           start_idx = range_obj.start - min_pos
           end_idx = range_obj.end - min_pos + 1
           for i in range(start_idx, end_idx):
               coverage[i] += 1

       return coverage

    def __getitem__(self, item):
        if isinstance(item, int):
            results = self.items[item]
        elif isinstance(item, slice):
            results = RangesList(self.items[item])
        return results

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __add__(self, other):
        assert(isinstance(other, GenomicRangesList))
        return GenomicRangesList(self.items + other.items)

    def __sub__(self, other):
        assert(isinstance(other, GenomicRangesList))
        return GenomicRangesList([item for item in self.items if item not in other.items])

    def __contains__(self, item):
        assert(isinstance(item, GenomicRange))
        return item in self.items

    def __str__(self):
        return f"GenomicRangesList({self.items})"

    def __repr__(self):
        return f"GenomicRangesList({self.items})"

    def __setitem__(self, index, value):
        assert(isinstance(index, int))
        assert(isinstance(value, GenomicRange))
        self.items[index] = value

    def __delitem__(self, index):
        assert(isinstance(index, int))
        del self.items[index]

    def __eq__(self, other):
        assert(isinstance(other, GenomicRangesList))
        if len(self.items) != len(other.items):
            return False
        for item in self.items:
            if item not in other.items:
                return False
        return True

    def __ne__(self, other):
        if not isinstance(other, GenomicRangesList):
            return True
        elif self==other:
            return False
        else:
            return True

    def reduce(self, ignore_strand=False):
        ranges = {}
        for item in self.items:
            if item.chrom not in ranges.keys():
                if not ignore_strand:
                    ranges[item.chrom] = {"+": [], "-": []}
                else:
                    ranges[item.chrom] = []
            else:
                if not ignore_strand:
                    ranges[item.chrom][item.strand].append(item.ranges)
                else:
                    ranges[item.chrom].append(item.ranges)

        for chrom in ranges.keys():
            if not ignore_strand:
                ranges[chrom]["+"] = RangesList(ranges[chrom]["+"]).reduce()
                ranges[chrom]["-"] = RangesList(ranges[chrom]["-"]).reduce()
            else:
                ranges[chrom] = RangesList(ranges[chrom]).reduce()
        return ranges



class GenomicRangesDict(dict):
    def __init__(self, keys, values):
        super().__init__()
        for key, value in zip(keys, values):
            assert(isinstance(key, str))
            assert(isinstance(value, GenomicRangesList) or isinstance(value, GenomicRange))
            self[key] = value

    def find_overlaps(self, other=None, type="exact", ignore_strand=False):
        if other is None:
            other = self
        assert (isinstance(other, GenomicRangesDict))
        overlaps = {}
        for key in self.keys():
            if key not in other.keys():
                continue
            overlaps[key] = self[key].find_overlaps(other[key], type=type, ignore_strand=ignore_strand)
        return overlaps

    def __getitem__(self, key):
        assert (isinstance(key, str))
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        assert (isinstance(key, str))
        assert (isinstance(value, GenomicRangesList) or isinstance(value, GenomicRange))
        super().__setitem__(key, value)

    def __delitem__(self, key):
        assert (isinstance(key, str))
        super().__delitem__(key)

    def __iter__(self):
        return iter(self.keys())

    def __eq__(self, other):
        if not isinstance(other, GenomicRangesDict):
            return False
        if len(self) != len(other):
            return False
        for key in self.keys():
            if key not in other.keys():
                return False
            if self[key] != other[key]:
                return False
        return True

    def __ne__(self, other):
        if not isinstance(other, GenomicRangesDict):
            return True
        elif self == other:
            return False
        else:
            return True

    def __str__(self):
        return f"GenomicRangesDict({self.items()})"

    def __repr__(self):
        return f"GenomicRangesDict({self.items()})"

    def __len__(self):
        return len(self.items())

    def __contains__(self, item):
        assert (isinstance(item, str))
        return item in self.keys()



