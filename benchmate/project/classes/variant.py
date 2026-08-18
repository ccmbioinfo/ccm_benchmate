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
    def to_kb(self, project):
        "send a sequence variant to the database"
        table = project.kb.db_tables["sequencevariant"]
        stmt = insert(table).values(id=self.id, project_id=project.project_id,
                                    chrom=self.chrom, pos=self.pos,
                                    ref=self.ref, alt=self.alt, length=self.length,
                                    annotations=self.annotations).returning(table.c.id)
        session = project.kb.session() if callable(project.kb.session) else project.kb.session
        res = session.execute(stmt)
        new_id = res.scalar_one()
        session.commit()
        return new_id

    @classmethod
    def from_kb(cls, project, id):
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
        )
        return variant

class StructuralVariant(BaseStructuralVariant):
    """
    subclass of structural variant with db methods
    """
    def to_kb(self, project):
        """
        send a structural variant to the database
        :param project: project class instance
        :return: id of the structural variant
        """
        table = project.kb.db_tables["structuralvariant"]
        stmt = insert(table).values(id=self.id, project_id=project.project_id,
                                    chrom=self.chrom, pos=self.pos,
                                    svlen=self.svlen, cn=self.cn, cistart=self.cistart,
                                    ciend=self.ciend, annotations=self.annotations).returning(table.c.id)
        session = project.kb.session() if callable(project.kb.session) else project.kb.session
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
            svlen=row.svlen,
            cn=row.cn,
            cistart=row.cistart,
            ciend=row.ciend,
            annotations=row.annotations,
        )
        return variant

class TandemRepeatVariant(BaseTandemRepeatVariant):
    """
    tandem repeat variant with db methods
    """
    def to_kb(self, project):
        """
        send a tandem repeat variant to the database
        :param project: project class instance
        :return: id of the tandem repeat variant
        """
        table = project.kb.db_tables["tandemrepeatvariant"]
        stmt = insert(table).values(id=self.id, project_id=project.project_id,
                                    chrom=self.chrom, pos=self.pos,
                                    al=self.al, annotations=self.annotations).returning(table.c.id)
        session = project.kb.session() if callable(project.kb.session) else project.kb.session
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
            al=row.al
        )
        return variant