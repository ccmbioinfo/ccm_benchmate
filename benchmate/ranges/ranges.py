
import pandas as pd
from math import floor


class Range:
    def __init__(self, start, end):
        self._check_values(start, end)
        self.start = start
        self.end = end
        self._range = pd.Interval(self.start, self.end, closed='both')

    def shift(self, amount=0):
        new_start = self.start + amount
        new_end = self.end + amount
        self._check_values(new_start, new_end)
        self.start += amount
        self.end += amount
        return self

    def extend(self, start=0, end=0):
        new_start = self.start + start
        new_end = self.end + end
        self._check_values(new_start, new_end)
        self.start += start
        self.end += end
        self._range = pd.Interval(new_start, new_end, closed='both')
        return self

    def overlaps(self, other, type="exact"):
        assert(isinstance(other, Range))
        overlap_types=["exact", "within", "start", "end", "any"]
        if type not in overlap_types:
            raise ValueError(f"overlap_type must be one of {overlap_types}")

        if type == "exact":
            return self==other
        elif type == "any":
            return self._range.overlaps(other._range)
        elif type == "within":
            return self._range.overlaps(other._range) and self.start <= other.start and self.end >= other.end
        elif type == "start":
            return self._range.overlaps(other._range) and self.start <= other.start
        elif type == "end":
            return self._range.overlaps(other._range) and self.end >= other.end
        else:
            return None

    def distance(self, other):
        assert(isinstance(other, Range))
        if self.overlaps(other, type="any"):
            return 0
        else:
            return min(abs(self.start - other.start), abs(self.end - other.end),
                       abs(self.start - other.end), abs(self.end - other.start))

    def split(self, n):
        """
        Splits the range into n equal parts
        :param n: number of parts to split the range into
        :return: a RangesList of the split ranges
        """
        assert(isinstance(n, int))
        assert(n > 0)
        step = floor(self.end - self.start) / n
        ranges = []
        for i in range(n):
            start = self.start + i * step
            end = self.start + (i + 1) * step
            ranges.append(Range(start, end))
        ranges=RangesList(ranges)
        return ranges

    def __str__(self):
        return f"Range from {self.start} to {self.end}"

    def __repr__(self):
        return f"Range from {self.start} to {self.end}"

    def __add__(self, other):
        if type(other) is Range:
            self.start += other.start
            self.end += other.end
        elif type(other)==int:
            self.start += other
            self.end += other
        else:
            raise NotImplementedError("Can only add Ranges or integer to a Range")

        return self


    def __eq__(self, other):
        if self.start == other.start and self.end == other.end:
            return True
        else:
            return False

    def __len__(self):
        return abs(self.end - self.start)

    def _check_values(self, start, end):
        if start > end or start < 0 or end < 0:
            raise ValueError("start and end must be positive and start needs to be <= end")


class RangesList:
    def __init__(self, ranges):
        assert(isinstance(ranges, list))
        for item in ranges:
            assert (isinstance(item, Range))
        self.items = ranges

    def pop(self, index):
        assert(isinstance(index, int))
        return self.items.pop(index)

    def insert(self, index, value):
        assert(isinstance(index, int))
        assert(isinstance(value, Range))
        self.items.insert(index, value)

    def append(self, item):
        assert(isinstance(item, Range))
        self.items.append(item)

    def extend(self, other):
        assert(isinstance(other, RangesList))
        self.items.extend(other.items)

    def remove(self, item):
        assert(isinstance(item, Range))
        self.items.remove(item)

    def find_overlaps(self, other=None, type="exact", return_ranges=True):
        if other is None:
            other = self
        assert(isinstance(other, RangesList))
        overlaps = []
        for i in range(len(self)):
            for j in range(len(other)):
                overlap=self.items[i].overlaps(other.items[j], type=type)
                if overlap is not None:
                    if return_ranges:
                        overlaps.append((self.items[i], other.items[j]))
                    else:
                        overlaps.append((i, j))
        return overlaps

    def coverage(self):

        min_pos = min(r.start for r in self.items)
        max_pos = max(r.end for r in self.items)
        length = max_pos - min_pos + 1
        coverage = [0] * length

        # Count coverage for each range
        for range_obj in self.items:
            # Adjust positions relative to min_pos
            start_idx = range_obj.start - min_pos
            end_idx = range_obj.end - min_pos + 1
            # Increment coverage count for all positions in this range
            for i in range(start_idx, end_idx):
                coverage[i] += 1

        return coverage

    def __getitem__(self, item):
        if isinstance(item, int):
            results=self.items[item]
        elif isinstance(item, slice):
            results= RangesList(self.items[item])
        return results

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __add__(self, other):
        assert (isinstance(other, RangesList))
        return RangesList(self.items + other.items)

    def __sub__(self, other):
        assert (isinstance(other, RangesList))
        return RangesList([item for item in self.items if item not in other.items])

    def __contains__(self, item):
        assert (isinstance(item, RangesList))
        return item in self.items

    def __str__(self):
        return f"RangesList({self.items})"

    def __repr__(self):
        return f"RangesList({self.items})"

    def __setitem__(self, index, value):
        assert (isinstance(index, int))
        assert (isinstance(value, Range))
        self.items[index] = value

    def __delitem__(self, index):
        assert (isinstance(index, int))
        del self.items[index]

    def __eq__(self, other):
        assert (isinstance(other, RangesList))
        if len(self.items) != len(other.items):
            return False
        for item in self.items:
            if item not in other.items:
                return False
        return True

    def __ne__(self, other):
        if not isinstance(other, RangesList):
            return True
        elif self == other:
            return False
        else:
            return True

    def reduce(self):
        starts=[]
        ends=[]
        for item in self.items:
            starts.append(item.start)
            ends.append(item.end)
        return Range(min(starts), max(ends))

    def __iter__(self):
        return iter(self.items)


class RangesDict(dict):
    def __init__(self, keys, values):
        super().__init__()
        for key, value in zip(keys, values):
            assert(isinstance(key, str))
            assert(isinstance(value, RangesList) or isinstance(value, Range))
            self[key] = value

    def find_overlaps(self, other=None, type="exact"):
        if other is None:
            other = self
        assert(isinstance(other, RangesDict))
        overlaps = {}
        for key in self.keys():
            if key not in other.keys():
                continue
            overlaps[key] = self[key].find_overlaps(other[key], type=type)
        return overlaps

    def __getitem__(self, key):
        assert(isinstance(key, str))
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        assert(isinstance(key, str))
        assert(isinstance(value, RangesList) or isinstance(value, Range))
        super().__setitem__(key, value)

    def __delitem__(self, key):
        assert(isinstance(key, str))
        super().__delitem__(key)

    def __iter__(self):
        return iter(self.keys())

    def __eq__(self, other):
        if not isinstance(other, RangesDict):
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
        if not isinstance(other, RangesDict):
            return True
        elif self == other:
            return False
        else:
            return True

    def __str__(self):
        return f"RangesDict({self.items()})"

    def __repr__(self):
        return f"RangesDict({self.items()})"

    def __len__(self):
        return len(self.items())

    def __contains__(self, item):
        assert(isinstance(item, str))
        return item in self.keys()



