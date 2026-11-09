from sqlalchemy import select, insert
from sqlalchemy.exc import NoResultFound

from benchmate.utils.general_utils import DataIntegrityError

from benchmate.variant.variant import SequenceVariant as BaseSequenceVariant
from benchmate.variant.variant import StructuralVariant as BaseStructuralVariant
from benchmate.variant.variant import TandemRepeatVariant as BaseTandemRepeatVariant


class SequenceVariant(BaseSequenceVariant):
    """
    subclass of sequence variant with db methods
    """
    def __init__(self, project, chrom, pos, ref, alt, length=None, id=None, annotations=None):
        super().__init__(id=id, chrom=chrom, pos=pos, ref=ref, alt=alt, length=length, annotations=annotations)
        self.project = project

    def to_kb(self):
        "send a sequence variant to the database"
        table = self.project.kb.db_tables["sequencevariant"]
        stmt = insert(table).values(id=self.id, project_id=self.project.project_id,
                                    chrom=self.chrom, pos=self.pos,
                                    ref=self.ref, alt=self.alt, length=self.length,
                                    annotations=self.annotations).returning(table.c.id)
        session = self.project.kb.session() if callable(self.project.kb.session) else self.project.kb.session
        res = session.execute(stmt)
        new_id = res.scalar_one()
        session.commit()
        return new_id

    @classmethod
    def from_kb(cls, id, project):
        """get the sequence variant from the database
        :param project: project class instance
        :param id: id of the sequence variant
        :return: the sequence variant"""
        table = project.kb.db_tables["sequencevariant"]
        stmt = select(table).where(table.c.id == id, table.c.project_id == project.project_id)
        session = project.kb.session() if callable(project.kb.session) else project.kb.session
        results = session.execute(stmt).fetchall()
        if len(results) == 0:
            raise NoResultFound(f"SequenceVariant with id {id} not found")

        if len(results) > 1:
            raise DataIntegrityError(f"Multiple sequenceVariant with id {id} found")

        row = results[0]
        variant = cls(
            id=row.id,
            chrom=row.chrom,
            pos=row.pos,
            ref=row.ref,
            alt=row.alt,
            length=row.length,
            annotations=row.annotations,
            project=project
        )
        return variant

class StructuralVariant(BaseStructuralVariant):
    """
    subclass of structural variant with db methods
    """
    def __init__(self, project, chrom, pos, ref, alt, end, svtype, id=None, annotations=None):
        super().__init__(id=id, chrom=chrom, pos=pos, ref=ref, alt=alt, end=end, svtype=svtype, annotations=annotations)
        self.project = project

    def to_kb(self):
        """
        send a structural variant to the database
        :param project: project class instance
        :return: id of the structural variant
        """
        table = self.project.kb.db_tables["structuralvariant"]
        stmt = insert(table).values(id=self.id, project_id=self.project.project_id,
                                    chrom=self.chrom, pos=self.pos, ref=self.ref, alt=self.alt, svtype=self.svtype,
                                    end=self.end, annotations=self.annotations).returning(table.c.id)
        session = self.project.kb.session() if callable(self.project.kb.session) else self.project.kb.session
        res = session.execute(stmt)
        new_id = res.scalar_one()
        session.commit()
        return new_id

    @classmethod
    def from_kb(cls, project, id):
        """
        get the structural variant from the database
        :param project: project class instance
        :param id: id of the structural variant
        :return: structural variant
        """
        table = project.kb.db_tables["structuralvariant"]
        stmt = select(table).where(table.c.id == id, table.c.project_id == project.project_id)
        session = project.kb.session() if callable(project.kb.session) else project.kb.session
        results = session.execute(stmt).fetchall()
        if len(results) == 0:
            raise NoResultFound(f"structuralvariant with id {id} not found")

        if len(results) > 1:
            raise DataIntegrityError(f"Multiple structuralvariant with id {id} found")

        row = results[0]
        variant = cls(
            id=row.id,
            chrom=row.chrom,
            pos=row.pos,
            ref=row.ref,
            alt=row.alt,
            svtype=row.svtype,
            end=row.end,
            annotations=row.annotations,
            project=project
        )
        return variant

class TandemRepeatVariant(BaseTandemRepeatVariant):
    """
    tandem repeat variant with db methods
    """
    def __init__(self, project, chrom, pos, ref, alt, motif, annotations=None, id=None):
        super().__init__(chrom=chrom, pos=pos, ref=ref, alt=alt, motif=motif, annotations=annotations, id=id)
        self.project = project

    def to_kb(self):
        """
        send a tandem repeat variant to the database
        :return: id of the tandem repeat variant
        """
        table = self.project.kb.db_tables["tandemrepeatvariant"]
        stmt = insert(table).values(id=self.id, project_id=self.project.project_id,
                                    chrom=self.chrom, pos=self.pos, ref=self.ref, alt=self.alt,
                                    annotations=self.annotations).returning(table.c.id)
        session = self.project.kb.session() if callable(self.project.kb.session) else self.project.kb.session
        res = session.execute(stmt)
        new_id = res.scalar_one()
        session.commit()
        return new_id

    @classmethod
    def from_kb(cls, project, id):
        """
        send a tandem repeat variant from the database
        :param project: project class instance
        :param id: id of the tandem repeat variant
        :return: tandem repeat variant
        """
        table = project.kb.db_tables["tandemrepeatvariant"]
        stmt = select(table).where(table.c.id == id, table.c.project_id == project.project_id)
        session = project.kb.session() if callable(project.kb.session) else project.kb.session
        results = session.execute(stmt).fetchall()
        if len(results) == 0:
            raise NoResultFound(f"tandemrepeatvariant with id {id} not found")

        if len(results) > 1:
            raise DataIntegrityError(f"Multiple tandemrepeatvariant with id {id} found")

        row = results[0]
        variant = cls(
            id=row.id,
            chrom=row.chrom,
            pos=row.pos,
            ref=getattr(row, "ref", None),
            alt=getattr(row, "alt", None),
            annotations=row.annotations,
            motif=getattr(row, "motif", None),
            project=project
        )
        return variant

# I'm going let the classes above will do the param checks for the factories, there is no need to
# duplicate code here

class SequenceVariantFactory:
    def __init__(self, project):
        self.project = project

    def __call__(self, id, chrom, pos, ref, alt, annotations):
        return SequenceVariant(id=id, chrom=chrom, pos=pos, ref=ref, alt=alt, annotations=annotations,
                               project=self.project)

    def from_kb(self, id):
        return SequenceVariant.from_kb(id=id, project=self.project)

class StructuralVariantFactory:
    def __init__(self, project):
        self.project = project

    def __call__(self, id, chrom, pos, ref, alt, end, svtype, annotations):
        return StructuralVariant(id=id, chrom=chrom, pos=pos, ref=ref, alt=alt, end=end, svtype=svtype,
                                 project=self.project, annotations=annotations)

    def from_kb(self, id):
        return StructuralVariant.from_kb(project=self.project, id=id)

class TandemRepeatVariantFactory:
    def __init__(self, project):
        self.project = project

    def __call__(self, chrom, pos, ref, alt, motif, annotations, id=None):
        return TandemRepeatVariant(id=id, chrom=chrom, pos=pos, ref=ref, alt=alt, motif=motif,
                                   annotations=annotations, project=self.project)

    def from_kb(self, id):
        return TandemRepeatVariant.from_kb(self.project, id)