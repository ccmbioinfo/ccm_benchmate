from typing import Optional, Dict, List, Any
from uuid import uuid4
from ccm_benchmate.variant.utils import *

#TODO add a way to query variants by type, e.g. SNV, INDEL, SV, CNV, TR form a database, this is an issue for later
# not sure if we are ever going to use or will have the resources to store all the variants in a study

class BaseVariant:
    """Base class for all variant types."""
    def __init__(self, chrom: str, pos: int, filter: Optional[str] = None, id: Optional[str] = None):
        self.chrom = chrom
        self.pos = pos
        self.filter = filter  # Callset-specific
        self.id = id if id is not None else str(uuid4()) #probably need somethign a bit more biologically relevant
        self.annotations: Dict[str, Any] = {}

    def show_annotations(self) -> Dict[str, Any]:
        """Return annotation types."""
        return self.annotations.keys()

    def query_annotation(self, key: str) -> Any:
        """Query a specific annotation."""
        return self.annotations.get(key)

    def add_annotation(self, key: str, value: Any) -> None:
        """Add or update an annotation."""
        self.annotations[key] = value


class SequenceVariant(BaseVariant):
    """Class for SNV and Indel variants."""
    def __init__(
        self,
        chrom: str,
        pos: int,
        ref: str,
        alt: str,
        filter: Optional[str] = None,
        qual: Optional[float] = None,  # Callset-specific
        gq: Optional[float] = None,   # Sample-specific
        gt: Optional[str] = None,     # Sample-specific
        dp: Optional[int] = None,     # Sample-specific
        ad: Optional[List[int]] = None,  # Sample-specific
        ps: Optional[str] = None,     # Sample-specific, Phase set (LRWGS only)
        length: Optional[int] = None,  # Calculated
        id: Optional[str] = None
    ):
        super().__init__(chrom, pos, filter, id)
        self.ref = ref
        self.alt = alt
        self.qual = qual
        self.gq = gq
        self.gt = gt
        self.dp = dp
        self.ad = ad
        self.ps = ps
        self.length = length

    def __len__(self):
        """Return the length of the variant."""
        if self.length is not None:
            return self.length
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

class StructuralVariant(BaseVariant):
    """Class for SV/CNV variants (INS, DEL, INV, DUP, BND, CNV)."""
    def __init__(
        self,
        chrom: str,
        pos: int,
        svtype: str,
        end: Optional[int] = None,
        ref: Optional[str] = None,
        alt: Optional[str] = None,
        filter: Optional[str] = None,
        qual: Optional[float] = None,  # Callset-specific
        gt: Optional[str] = None,     # Sample-specific
        dp: Optional[int] = None,     # Sample-specific
        ad: Optional[List[int]] = None,  # Sample-specific
        svlen: Optional[int] = None,
        mateid: Optional[str] = None,
        cn: Optional[int] = None,
        cistart: Optional[int] = None,
        ciend: Optional[int] = None,
        mei_type: Optional[str] = None,
        sr: Optional[int] = None,     # Sample-specific
        pr: Optional[int] = None,     # Sample-specific
        ps: Optional[str] = None,     # Sample-specific
        id: Optional[str] = None
    ):
        super().__init__(chrom, pos, filter, id)
        self.svtype = svtype
        self.end = end
        self.ref = ref
        self.alt = alt
        self.qual = qual
        self.gt = gt
        self.dp = dp
        self.ad = ad
        self.svlen = svlen
        self.mateid = mateid
        self.cn = cn
        self.cistart = cistart
        self.ciend = ciend
        self.mei_type = mei_type
        self.sr = sr
        self.pr = pr
        self.ps = ps

    def __len__(self):
        """Return the length of the variant."""
        if self.svlen is not None:
            return self.svlen
        if self.ref and self.alt:
            return abs(len(self.ref) - len(self.alt))
        return 0

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

class TandemRepeatVariant(BaseVariant):
    """Class for Tandem Repeat variants (SRWGS and LRWGS)."""
    def __init__(
        self,
        chrom: str,
        pos: int,
        end: int,
        gt: Optional[str] = None,     # Sample-specific
        motif: Optional[str] = None,
        al: Optional[int] = None,
        ref: Optional[str] = None,
        alt: Optional[str] = None,
        filter: Optional[str] = None,  # Callset-specific
        ms: Optional[int] = None,      # Sample-specific
        mc: Optional[int] = None,      # Sample-specific
        ap: Optional[float] = None,    # Sample-specific
        am: Optional[float] = None,    # Sample-specific
        sd: Optional[int] = None,      # Sample-specific
        id: Optional[str] = None
    ):
        super().__init__(chrom, pos, filter, id)
        self.end = end
        self.gt = gt
        self.motif = motif
        self.al = al
        self.ref = ref
        self.alt = alt
        self.ms = ms
        self.mc = mc
        self.ap = ap
        self.am = am
        self.sd = sd

    def __len__(self):
        """Return the length of the variant."""
        if self.al is not None:
            return self.al
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

