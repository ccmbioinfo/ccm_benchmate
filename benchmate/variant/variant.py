from dataclasses import dataclass

from typing import Optional, Dict, Any
from uuid import uuid4

from docker.errors import NotFound
from sqlalchemy import select, insert

from benchmate.utils.general_utils import DataIntegrityError


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

@dataclass(slots=True)
class SequenceVariant(BaseVariant):
    length: Optional[int]=None

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

    #THERE IS NOT CHECK TO SEE IF THE SAME VARIANT EXISTS BEFOREHAND, THE IF THERE ARE REGULAR IDS
    # THAT WOULD GIVE A UNIQUE VIOLATION ERROR BUT IF YOU ARE USING UUID4 THERE IS NO CHECK
    def to_kb(self, project):
        table=project.kb.db_tables["sequencevariant"]
        stmt=insert(table).values(id=self.id, chrom=self.chrom, pos=self.pos,
                                  ref=self.ref, alt=self.alt, length=self.length,
                                  annotations=self.annotations)
        project.kb.session.execute(stmt)
        project.kb.session.commit()

    @classmethod
    def from_kb(cls, project, id):
        table = project.kb.db_tables["sequencevariant"]
        stmt=select(table).where(table.c.id==id).fetchall()
        results=project.kb.session.execute(stmt)
        if len(results) == 0:
            raise NotFound(f"SequenceVariant with id {id} not found")

        if len(results) > 1:
            raise DataIntegrityError(f"Multiple sequenceVariant with id {id} found")

        results=results[0]
        variant=cls(
            id=results.id,
            chrom=results.chrom,
            pos=results.pos,
            ref=results.ref,
            alt=results.alt,
            length=results.length,
            annotations=results.annotations,
        )
        return variant


@dataclass(slots=True)
class StructuralVariant(BaseVariant):
    svlen: Optional[int] = None,  # length of the sv
    cn: Optional[int] = None,
    cistart: Optional[int] = None,
    ciend: Optional[int] = None,

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

    def to_kb(self, project):
        table = project.kb.db_tables["structuralvariant"]
        stmt = insert(table).values(id=self.id, chrom=self.chrom, pos=self.pos,
                                    svlen=self.svlen, cn=self.cn, cistart=self.cistart,
                                    ciend=self.ciend, annotations=self.annotations)
        project.kb.session.execute(stmt)
        project.kb.session.commit()

    @classmethod
    def from_kb(cls, project):
        table = project.kb.db_tables["structuralvariant"]
        stmt = select(table).where(table.c.id == id).fetchall()
        results = project.kb.session.execute(stmt)
        if len(results) == 0:
            raise NotFound(f"structuralvariant with id {id} not found")

        if len(results) > 1:
            raise DataIntegrityError(f"Multiple structuralvariant with id {id} found")

        results = results[0]
        variant = cls(
            id=results.id,
            chrom=results.chrom,
            pos=results.pos,
            svlen=results.svlen,
            cn=results.cn,
            cistart=results.cistart,
            ciend=results.cient,
            annotations=results.annotations,
        )
        return variant


@dataclass(slots=True)
class TandemRepeatVariant(BaseVariant):
    """Class for Tandem Repeat variants (SRWGS and LRWGS)."""
    motif: Optional[str] = None,
    al: Optional[int] = None,

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

    def to_kb(self, project):
        table = project.kb.db_tables["tandemrepeatvariant"]
        stmt = insert(table).values(id=self.id, chrom=self.chrom, pos=self.pos,
                                    al=self.al, annotations=self.annotations)
        project.kb.session.execute(stmt)
        project.kb.session.commit()

    @classmethod
    def from_kb(cls, project):
        table = project.kb.db_tables["tandemrepeatvariant"]
        stmt = select(table).where(table.c.id == id).fetchall()
        results = project.kb.session.execute(stmt)
        if len(results) == 0:
            raise NotFound(f"tandemrepeatvariant with id {id} not found")

        if len(results) > 1:
            raise DataIntegrityError(f"Multiple tandemrepeatvariant with id {id} found")

        results = results[0]
        variant = cls(
            id=results.id,
            chrom=results.chrom,
            pos=results.pos,
            ref=results.ref,
            alt=results.alt,
            annotations=results.annotations,
            motif=results.motif,
            al=results.al
        )
        return variant
