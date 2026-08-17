from dataclasses import dataclass, field
from typing import Optional, Dict, Any, KeysView
from uuid import uuid4

from benchmate.ranges.genomicranges import GenomicRange


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
    filter: Optional[str] = None
    qual: Optional[float] = None
    gt: Optional[str] = None
    dp: Optional[int] = None
    ad: Optional[list] = None
    ps: Optional[str] = None
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
        return self.pos

    def to_gr(self):
        return GenomicRange(self.chrom, self.start, self.end, strand="*", annotation=self.annotations.copy())


@dataclass
class SequenceVariant(BaseVariant):
    """
    Simple sequence variation (SNVs, small indels, insertions, deletions).
    """
    length: Optional[int] = None

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
                f"alt={self.alt}, filter={self.filter}, qual={self.qual}, gq=None, "
                f"gt={self.gt}, dp={self.dp}, ad={self.ad}, ps={self.ps}, id={self.id})")


@dataclass
class StructuralVariant(BaseVariant):
    """
    Larger genomic structural variations (DEL, DUP, INV, INS, BND, etc.).
    """
    svtype_val: Optional[str] = None
    end_val: Optional[int] = None
    svlen: Optional[int] = None
    cn: Optional[int] = None
    cistart: Optional[int] = None
    ciend: Optional[int] = None
    mateid: Optional[str] = None
    mei_type: Optional[str] = None
    sr: Optional[int] = None
    pr: Optional[int] = None

    def __post_init__(self):
        super().__post_init__()
        # Handle case where svtype or end is passed positionally or in ref/alt
        if isinstance(self.ref, str) and self.ref in ["DEL", "DUP", "INV", "INS", "BND"] and self.svtype_val is None:
            self.svtype_val = self.ref
            self.ref = "N"

    @property
    def svtype(self) -> str:
        if self.svtype_val:
            return self.svtype_val
        alt = (self.alt or "").upper()
        for st in ["DEL", "DUP", "INV", "INS", "BND"]:
            if st in alt:
                return st
        return "UNK"

    @property
    def end(self) -> int:
        if self.end_val is not None:
            return self.end_val
        if self.ref:
            return self.pos + len(self.ref) - 1
        return self.pos

    @property
    def confidence_interval(self):
        return (
            self.pos + (self.cistart or 0),
            self.end + (self.ciend or 0),
        )

    @property
    def is_copy_number_change(self) -> bool:
        return self.cn is not None

    def __len__(self):
        """Return the length of the variant."""
        if self.svlen is not None:
            return self.svlen
        if self.ref and self.alt:
            return abs(len(self.ref) - len(self.alt))
        return 0

    def reciprocal_overlap(self, other):
        """
        Calculate reciprocal overlap fraction between structural variants.
        """
        assert isinstance(other, StructuralVariant)
        start = max(self.pos, other.pos)
        end = min(self.end, other.end)

        overlap = max(0, end - start + 1)
        denom = min(len(self), len(other))
        return overlap / denom if denom > 0 else 0.0

    def __str__(self):
        """Return a string representation of the variant."""
        end_str = str(self.end_val) if self.end_val is not None else ('N/A' if self.end == self.pos and not self.ref else str(self.end))
        return (f"{self.chrom}:{self.pos}-{end_str} "
                f"{self.svtype} {self.ref} -> {self.alt} (ID: {self.id})")

    def __repr__(self):
        """Return a detailed string representation of the variant."""
        return (f"StructuralVariant(id={self.id}, chrom={self.chrom}, pos={self.pos}, svtype={self.svtype}, "
                f"end={self.end_val if self.end_val is not None else self.end}, ref={self.ref}, alt={self.alt}, svlen={self.svlen}, "
                f"cn={self.cn}, cistart={self.cistart}, ciend={self.ciend}, mei_type={self.mei_type}, sr={self.sr}, pr={self.pr}")


@dataclass
class TandemRepeatVariant(BaseVariant):
    """
    Class for Tandem Repeat variants.
    """
    end_val: Optional[int] = None
    motif: Optional[str] = None
    al: Optional[int] = None
    ms: Optional[int] = None
    mc: Optional[int] = None
    ap: Optional[float] = None
    am: Optional[float] = None
    sd: Optional[int] = None

    def __post_init__(self):
        super().__post_init__()
        # If end position was passed as 3rd positional argument (in ref)
        if isinstance(self.ref, int) and self.end_val is None:
            self.end_val = self.ref
            self.ref = None

    @property
    def end(self) -> int:
        if self.end_val is not None:
            return self.end_val
        return super().end

    @property
    def repeat_count(self):
        if not self.motif or self.al is None:
            return None
        return self.al / len(self.motif)

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
        return (f"{self.chrom}:{self.pos}-{self.end} TR {self.motif} (GT: {self.gt}, "
                f"ID: {self.id})")

    def __repr__(self):
        """Return a detailed string representation of the variant."""
        return (f"TandemRepeatVariant(chrom={self.chrom}, pos={self.pos}, end={self.end}, "
                f"gt={self.gt}, motif={self.motif}, al={self.al}, ref={self.ref}, alt={self.alt}, "
                f"ms={self.ms}, mc={self.mc}, ap={self.ap}, am={self.am}, "
                f"sd={self.sd}, id={self.id})")



