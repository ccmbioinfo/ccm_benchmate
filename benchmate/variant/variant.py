from dataclasses import dataclass, field
from typing import Optional, Dict, Any, KeysView
from uuid import uuid4

from benchmate.ranges.genomicranges import GenomicRange
from utils.general_utils import check_annotations


@dataclass
class BaseVariant:
    """
    Base variant class containing the core information of a genomic variant.
    """
    id: Optional[str] = None
    chrom: str = ""
    pos: int = 0
    ref: Optional[str] = None
    alt: Optional[str] = None
    annotations: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Handle case where positional arguments passed as (chrom, pos, ref, alt) without ID e.g. BaseVariant("chr1", 12345, "A", "T")
        if isinstance(self.chrom, int):
            orig_id = self.id
            orig_chrom = self.chrom
            orig_pos = self.pos
            orig_ref = self.ref

            self.alt = orig_ref if isinstance(orig_ref, str) else None
            self.ref = orig_pos if isinstance(orig_pos, str) else None
            self.pos = int(orig_chrom)
            self.chrom = str(orig_id)
            self.id = str(uuid4())

        if self.id is None:
            self.id = str(uuid4())

        if self.annotations is None:
            self.annotations = {}
        else:
            check_annotations(self)

    def show_annotations(self) -> Any:
        """Return annotation keys view or list."""
        return list(self.annotations.keys())

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
        if self.ref:
            return self.pos + len(self.ref) - 1
        else:
            return self.pos

    def to_gr(self):
        return GenomicRange(self.chrom, self.start, self.end, strand="*", annotations=self.annotations.copy())


@dataclass
class SequenceVariant(BaseVariant):
    """
    Simple sequence variation (SNVs, small indels, insertions, deletions).
    """
    length: Optional[int] = None

    def __post_init__(self):
        super().__post_init__()
        self.length=len(self)

    @property
    def variant_type(self) -> str:
        r_len = len(self.ref) if self.ref else 0
        a_len = len(self.alt) if self.alt else 0
        if r_len == 1 and a_len == 1:
            return "SNV"
        if r_len < a_len:
            return "INS"
        if r_len > a_len:
            return "DEL"
        return "MNV"

    @property
    def is_snv(self) -> bool:
        return bool(self.ref and self.alt and len(self.ref) == 1 and len(self.alt) == 1)

    @property
    def is_indel(self) -> bool:
        r_len = len(self.ref) if self.ref else 0
        a_len = len(self.alt) if self.alt else 0
        return r_len != a_len

    @property
    def is_transition(self) -> bool:
        transitions = {
            ("A", "G"),
            ("G", "A"),
            ("C", "T"),
            ("T", "C"),
        }
        if self.ref and self.alt:
            return (self.ref.upper(), self.alt.upper()) in transitions
        return False

    def __len__(self):
        """Return the length of the variant."""
        if self.length is not None:
            return self.length
        return max(len(self.ref or ""), len(self.alt or ""))

    def __str__(self):
        """Return a string representation of the variant."""
        return f"{self.chrom}:{self.pos} {self.ref} -> {self.alt} (ID: {self.id})"

    def __repr__(self):
        """Return a detailed string representation of the variant."""
        return (f"SequenceVariant(chrom={self.chrom}, pos={self.pos}, ref={self.ref}, "
                f"alt={self.alt}, id={self.id})")

@dataclass
class StructuralVariant(BaseVariant):
    svtype: Optional[str] = None
    end: Optional[int] = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.svtype = self.svtype.upper()

    def __len__(self) -> int:
        if self.end is None:
            return 0
        return self.end - self.pos + 1

    def reciprocal_overlap(self, other: "StructuralVariant") -> float:
        if (
            self.chrom != other.chrom
            or self.end is None
            or other.end is None
        ):
            return 0.0

        overlap = max(
            0,
            min(self.end, other.end) - max(self.pos, other.pos) + 1,
        )

        return overlap / min(len(self), len(other)) if overlap else 0.0


    def __str__(self):
        """Return a string representation of the variant."""
        return (f"{self.chrom}:{self.pos}-{self.end} "
                f"{self.svtype} {self.ref} -> {self.alt} (ID: {self.id})")

    def __repr__(self):
        """Return a detailed string representation of the variant."""
        return (f"StructuralVariant(id={self.id}, chrom={self.chrom}, pos={self.pos}, svtype={self.svtype}, "
                f"end={self.end}, ref={self.ref}, alt={self.alt}")


@dataclass
class TandemRepeatVariant(BaseVariant):
    """
    Class for Tandem Repeat variants.
    """
    motif: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()

    @property
    def repeat_count(self):
        if not self.motif or self.alt is None:
            return None
        return self.alt / len(self.motif)

    @property
    def is_expansion(self) -> bool:
        r_len = len(self.ref) if self.ref else 0
        a_len = len(self.alt) if self.alt else 0
        return a_len > r_len

    @property
    def is_contraction(self) -> bool:
        r_len = len(self.ref) if self.ref else 0
        a_len = len(self.alt) if self.alt else 0
        return a_len < r_len

    def __len__(self):
        """Return the length of the variant."""
        if self.al is not None:
            return self.al
        if self.end > self.pos:
            return self.end - self.pos + 1
        return 0

    def __str__(self):
        """Return a string representation of the variant."""
        return (f"{self.chrom}:{self.pos}-{self.end} TR {self.motif} ID: {self.id})")

    def __repr__(self):
        """Return a detailed string representation of the variant."""
        return (f"TandemRepeatVariant(chrom={self.chrom}, pos={self.pos}, end={self.end}, motif={self.motif}, al={self.al},  id={self.id})")



