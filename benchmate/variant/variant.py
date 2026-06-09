from dataclasses import dataclass

from typing import Optional, Dict, Any
from uuid import uuid4

from benchmate.ranges.genomicranges import GenomicRange

@dataclass(slots=True)
class BaseVariant:
    id: [str, uuid4()]
    chrom: str
    pos: int
    ref: str
    alt: str
    annotations: Dict[str, Any]

    def show_annotations(self) -> Dict[str, Any]:
        """Return annotation types."""
        return self.annotations.keys()

    def query_annotation(self, key: str) -> Any:
        """Query a specific annotation."""
        return self.annotations.get(key)

    def add_annotation(self, key: str, value: Any) -> None:
        """Add or update an annotation."""
        self.annotations[key] = value

    @property
    def start(self) -> int:
        return self.pos

    @property
    def end(self) -> int:
        return self.pos + len(self.ref) - 1

    def to_gr(self):
        return GenomicRange(self.chrom, self.start, self.end, strand="*", annotation=self.annotations)

@dataclass(slots=True)
class SequenceVariant(BaseVariant):
    length: Optional[int]=None

    @property
    def variant_type(self) -> str:
        if len(self.ref) == 1 and len(self.alt) == 1:
            return "SNV"

        if len(self.ref) < len(self.alt):
            return "INS"

        if len(self.ref) > len(self.alt):
            return "DEL"

        return "MNV"

    @property
    def is_snv(self) -> bool:
        return len(self.ref) == 1 and len(self.alt) == 1

    @property
    def is_indel(self) -> bool:
        return len(self.ref) != len(self.alt)

    @property
    def is_transition(self):
        transitions = {
            ("A", "G"),
            ("G", "A"),
            ("C", "T"),
            ("T", "C"),
        }

        return (self.ref, self.alt) in transitions


    def __len__(self):
        """Return the length of the variant."""
        if self.length is not None:
            return self.length
        else:
            return max(len(self.ref), len(self.alt)) if self.ref and self.alt else 0

    def __str__(self):
        """Return a string representation of the variant."""
        return f"{self.chrom}:{self.pos} {self.ref} -> {self.alt} (ID: {self.id})"

    def __repr__(self):
        """Return a detailed string representation of the variant."""
        return (f"SequenceVariant(chrom={self.chrom}, pos={self.pos}, ref={self.ref}, "
                f"alt={self.alt}, filter={self.filter}, qual={self.qual}, gq={self.gq}, "
                f"gt={self.gt}, dp={self.dp}, ad={self.ad}, ps={self.ps}, length={self.length}, "
                f"id={self.id})")

@dataclass(slots=True)
class StructuralVariant(BaseVariant):
    svlen: Optional[int] = None # length of the sv
    cn: Optional[int] = None
    cistart: Optional[int] = None
    ciend: Optional[int] = None

    @property
    def svtype(self) -> str:
        alt = self.alt.upper()

        if "DEL" in alt:
            return "DEL"

        if "DUP" in alt:
            return "DUP"

        if "INV" in alt:
            return "INV"

        if "INS" in alt:
            return "INS"

        return "UNK"

    @property
    def confidence_interval(self):
        return (
            self.pos + (self.cistart or 0),
            self.end + (self.ciend or 0),
        )

    @property
    def is_copy_number_change(self):
        return self.cn is not None

    def __len__(self):
        """Return the length of the variant."""
        if self.svlen is not None:
            return self.svlen
        if self.ref and self.alt:
            return abs(len(self.ref) - len(self.alt))
        return 0

    def reciprocal_overlap(self, other):
        assert isinstance(other, StructuralVariant)
        start = max(self.pos, other.pos)
        end = min(self.end, other.end)

        overlap = max(0, end - start)

        return overlap / min(len(self), len(other))

    def __str__(self):
        """Return a string representation of the variant."""
        return (f"{self.chrom}:{self.pos}-{self.end if self.end else 'N/A'} "
                f"{self.svtype} {self.ref} -> {self.alt} (ID: {self.id})")

    def __repr__(self):
        """Return a detailed string representation of the variant."""
        return (f"StructuralVariant(chrom={self.chrom}, pos={self.pos}, svtype={self.svtype}, "
                f"end={self.end}, ref={self.ref}, alt={self.alt}, filter={self.filter}, "
                f"qual={self.qual}, gt={self.gt}, dp={self.dp}, ad={self.ad}, svlen={self.svlen}, "
                f"mateid={self.mateid}, cn={self.cn}, cistart={self.cistart}, ciend={self.ciend}, "
                f"mei_type={self.mei_type}, sr={self.sr}, pr={self.pr}, ps={self.ps}, id={self.id})")


@dataclass(slots=True)
class TandemRepeatVariant(BaseVariant):
    """Class for Tandem Repeat variants (SRWGS and LRWGS)."""
    motif: Optional[str] = None,
    al: Optional[int] = None,

    @property
    def repeat_count(self):
        if not self.motif or self.al is None:
            return None

        return self.al / len(self.motif)

    @property
    def is_expansion(self):
        return len(self.alt) > len(self.ref)

    @property
    def is_contraction(self):
        return len(self.alt) < len(self.ref)

    def __len__(self):
        """Return the length of the variant."""
        if self.al is not None:
            return self.al
        else:
            return 0

    def __str__(self):
        """Return a string representation of the variant."""
        return (f"{self.chrom}:{self.pos}-{self.end} TR {self.motif} (GT: {self.gt}, "
                f"ID: {self.id})")

    def __repr__(self):
        """Return a detailed string representation of the variant."""
        return (f"TandemRepeatVariant(chrom={self.chrom}, pos={self.pos}, end={self.end}, "
                f"gt={self.gt}, motif={self.motif}, al={self.al}, ref={self.ref}, alt={self.alt}, "
                f"filter={self.filter}, ms={self.ms}, mc={self.mc}, ap={self.ap}, am={self.am}, "
                f"sd={self.sd}, id={self.id})")


