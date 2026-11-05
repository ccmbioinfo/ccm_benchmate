from benchmate.project.project import Project
from benchmate.project.classes.api import  ApiCall as ProjectApiCall
from benchmate.project.classes.sequence import Sequence as ProjectSequence
from benchmate.project.classes.structure import Structure as ProjectStructure
from benchmate.project.classes.molecule import Molecule as ProjectMolecule
from benchmate.project.classes.variant import StructuralVariant as ProjectStructuralVariant
from benchmate.project.classes.variant import SequenceVariant as ProjectSequenceVariant
from benchmate.project.classes.variant import TandemRepeatVariant as ProjectTandemRepeatVariant
from benchmate.project.classes.literature import Paper as ProjectPaper
from benchmate.project.classes.literature import LitSearch as ProjectLitSearch
from benchmate.project.classes.genome import Genomes as ProjectGenomes
from benchmate.project.classes.alignment import Alignment as ProjectAlignment

__all__ = ["Project", "ProjectApiCall", "ProjectSequence", "ProjectStructure", "ProjectMolecule",
           "ProjectSequenceVariant", "ProjectTandemRepeatVariant", "ProjectStructuralVariant",
           "ProjectPaper", "ProjectLitSearch", "ProjectGenomes", "ProjectAlignment"]


