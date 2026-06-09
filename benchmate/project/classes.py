import os
import io
import shutil
from pathlib import Path
from functools import partial
from hashlib import md5
from sqlalchemy import select, insert
from sqlalchemy.exc import NoResultFound

from benchmate.project.project import Project
from benchmate.utils.general_utils import DataIntegrityError
from benchmate.inference.inference import Inference

#sequence
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from benchmate.sequence.sequence import Sequence as BaseSequence

#molecule
from rdkit import Chem
from benchmate.molecule.molecule import Molecule as BaseMolecule
from molecule.molecule import MoleculeInfo

#structure
from benchmate.structure.utils import *
from benchmate.structure.structure import Structure as BaseStructure, StructureInfo
from biotite.structure.io.pdb import PDBFile

#variants
from benchmate.variant.variant import SequenceVariant as BaseSequenceVariant
from benchmate.variant.variant import StructuralVariant as BaseStructuralVariant
from benchmate.variant.variant import TandemRepeatVariant as BaseTandemRepeatVariant

#genomes
from benchmate.genome.genome import Genome as BaseGenome

#apis
from benchmate.apis.utils import ApiCall as BaseApiCall
from benchmate.apis.ensembl import Ensembl
from benchmate.apis.uniprot import UniProt
from benchmate.apis.stringdb import StringDb
from benchmate.apis.reactome import Reactome
from benchmate.apis.ebi import EBI
from benchmate.apis.ols import OLS
from benchmate.apis.biogrid import BioGrid
from benchmate.apis.alphagenome import AlphaGenome
from benchmate.apis.intact import IntAct
from benchmate.apis.rnacentral import RnaCentral
from benchmate.apis.ncbi import Ncbi

#alignment
from benchmate.alignment.blast import Blast
from benchmate.alignment.mmseqs import MMSeqs
from benchmate.alignment.foldseek import FoldSeek
from benchmate.alignment.folddisco import FoldDisco

#literature
from benchmate.literature.literature import LitSearch as BaseLitSearch
from benchmate.literature.literature import OpenAlex, paper_from_id, paper_from_response, paper_from_link
from benchmate.literature.paper_processor import PaperProcessor
from benchmate.literature.literature import Paper as BasePaper


class ApiCall(BaseApiCall):
    pass

class LitSearch(BaseLitSearch):
    def __init__(self, config):
        self.config=config
        super().__init__()
        self.openalex=OpenAlex(self["config"]["openalex_api_key"])
        os.makedirs(self.config["pdf_path"], exist_ok=True)
        self.search=partial(self.search,openalex=self.openalex)


class Paper(BasePaper):
    pass

class Genome(BaseGenome):
    def __init__(self, config, project:Project):
        self.config=config
        self.project=project
        self.genomes={}
        for name, info in self.config["genomes"].items():
            #info:
            description=self.config["genomes"]["name"]["description"]
            files=self.config["genomes"][name]["files"]
            for file in files.keys():
                if file is not None:
                    genome_path=os.path.join(config["genome_path"], name)
                    os.makedirs(genome_path, exist_ok=False)
                    shutil.copy(files[file], genome_path)
                    files[file]=os.path.join(genome_path, os.path.basename(files[file]))
                else:
                    continue

            g=super().__init__(genome_fasta=files["genome_fasta"],
                              gtf=files["gtf"],
                              name=name,
                              db_conn=self.project.kb.engine,
                              description=description,
                              proteome_fasta=files["proteome_fasta"],
                              transcriptome_fasta=files["transcriptome_fasta"],
                              standalone=False,
                              create=True
            )
            self.genomes[name]=g

class Alignment:
    def __init__(self, config):
        self.config=config
        self.blast=Blast()
        self.blast.find_local_databases(config["blast_db_root"])
        self.blast.create_db=partial(self.blast.create_db, output_path=self.config["blast_db_root"])
        self.mmseqs=MMSeqs()
        self.mmseqs.find_local_databases(config["mmseq_db_root"])
        self.mmseqs.download_database=partial(self.mmseqs.download_database, location=self.config["mmseqs_db_root"])
        self.foldseek=FoldSeek()
        self.foldseek.find_local_databases(config["foldseek_db_root"])
        self.foldseek.download_database=partial(self.foldseek.download_database, location=self.config["foldseek_db_root"])
        self.folddisco = FoldDisco()
        self.folddisco.find_local_databases(config["folddisco_db_root"])
        self.folddisco.create_index = partial(self.folddisco.create_index, db_path=self.config["folddisco_db_root"])

class SequenceVariant(BaseSequenceVariant):
    def to_kb(self, project):
        table = project.kb.db_tables["sequencevariant"]
        stmt = insert(table).values(id=self.id, chrom=self.chrom, pos=self.pos,
                                    ref=self.ref, alt=self.alt, length=self.length,
                                    annotations=self.annotations)
        project.kb.session.execute(stmt)
        project.kb.session.commit()

    @classmethod
    def from_kb(cls, project, id):
        table = project.kb.db_tables["sequencevariant"]
        stmt = select(table).where(table.c.id == id).fetchall()
        results = project.kb.session.execute(stmt)
        if len(results) == 0:
            raise NoResultFound(f"SequenceVariant with id {id} not found")

        if len(results) > 1:
            raise DataIntegrityError(f"Multiple sequenceVariant with id {id} found")

        results = results[0]
        variant = cls(
            id=results.id,
            chrom=results.chrom,
            pos=results.pos,
            ref=results.ref,
            alt=results.alt,
            length=results.length,
            annotations=results.annotations,
        )
        return variant

class StructuralVariant(BaseStructuralVariant):
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
            raise NoResultFound(f"structuralvariant with id {id} not found")

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

class TandemRepeatVariant(BaseTandemRepeatVariant):
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
            raise NoResultFound(f"tandemrepeatvariant with id {id} not found")

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

class Structure(BaseStructure):
    def __init__(self, config, name, atoms, annotations):
        self.config = config
        self._pdbs()
        super().__init__(name, atoms, annotations)


    def _pdbs(self):
        os.makedirs(self.config["pdb_path]"], exist_ok=True)
        if not os.path.exists(os.path.join(self.config["tdi_path"])):
            Path(self.config["tdi_path"]).touch()

    def to_kb(self, project):
        structure_table = project.kb.db_tables["structure"]

        # 1. Convert AtomArray -> PDB text
        pdb_file = PDBFile()
        pdb_file.set_structure(self.info.atoms)
        buf = io.StringIO()
        pdb_file.write(buf)
        pdb_text = buf.getvalue()

        # after you build pdb_text as a str, convert to bytes
        pdb_bytes = pdb_text.encode("utf-8")

        # 2. Build row data (atoms as TEXT) in a dictionary
        row_data = {
            "project_id": project.id,
            "name": self.name,
            "chains": self.info.chains,
            "atoms": pdb_bytes,  # plain text, no gzip
            "annotations": self.info.annotations,
            "hash":md5(pdb_bytes).hexdigest(),
        }
        # insert into structure table
        stmt = structure_table.insert().values(**row_data).returning(structure_table.c.id)
        result = project.session.execute(stmt)
        project.session.commit()

        unique_chains = list(set(self.info.chains))
        with open(self.config["tdi_path"], "a") as f:
            for i in range(len(unique_chains)):
                tdi=self.to_3di(unique_chains[i])
                new_record = SeqRecord(Seq(tdi.info.sequence), id=f"{result}_{i}", description=self.info.name)
                SeqIO.write(new_record, f, "fasta")

        return result.fetchone()[0]

    @classmethod
    def from_kb(cls, project, id):
        structure_table = project.kb.db_tables["structure"]
        stmt = select(structure_table).where(structure_table.c.id == id)

        results = project.kb.session.execute(stmt).fetchall()

        if len(results) == 0:
            raise NoResultFound(f"Could not find a molecule with id {id}")
        if len(results) > 1:
            raise DataIntegrityError(f"Found more than one molecule with id {id}")

        # the first row
        row = results[0]._mapping

        name = row["name"]
        chains = row["chains"]

        # pdb pay load from the to_kb
        atoms_blob = row["atoms"]
        annotations = row["annotations"]

        # ran into attribute errors, memoryview to bytes , if bytes decode to utf- 8, crash if anything else
        if isinstance(atoms_blob, memoryview):
            atoms_blob = atoms_blob.tobytes()
        elif isinstance(atoms_blob, str):
            atoms_text = atoms_blob
        elif isinstance(atoms_blob, bytes):
            atoms_text = atoms_blob.decode("utf-8")
        else:
            raise TypeError(f"Unexpected atoms type: {type(atoms_blob)}")

        if not isinstance(atoms_blob, str):
            atoms_text = atoms_blob.decode("utf-8")

        # rebuild biotite struct
        buf = io.StringIO(atoms_text)
        pdb_file = PDBFile.read(buf)
        atom_array = pdb_file.get_structure(model=1)
        return cls(name, atom_array, annotations)

    @classmethod
    def from_file(cls, config, name, file, source, destination, id):
        if file is not None:
            if not os.path.exists(file):
                raise FileNotFoundError(f"File not found: {file}")

            structure=super().from_file(file)

        if file is None and id is not None:
            file=os.path.abspath(download(id, source, destination))
            structure = super().from_file(file)

        if file is None and id is None:
            raise ValueError("You must provide a file or an id as well as a source and destination")

        return cls(config, name, structure)

class Molecule(BaseMolecule):
    def __init__(self, config, name, smiles):
        self.fingerprint_dim=config["fingerprint_dim"]
        self.fingerprint_radius=config["fingerprint_radius"]
        super().__init__(name, smiles, self.fingerprint_dim, self.fingerprint_radius)

    @classmethod
    def from_kb(cls, project, id):
        molecule_table = project.kb.db_tables["molecule"]

        stmt = (
            select(
                molecule_table.c.name,
                molecule_table.c.smiles,
                molecule_table.c.fingerprint_dim,
                molecule_table.c.fingerprint_radius,
                molecule_table.c.ecfp4,
                molecule_table.c.fcfp4,
                molecule_table.c.maccs,
                molecule_table.c.inchikey,
                molecule_table.c.properties,
                molecule_table.c.annotations,
            )
            .where(molecule_table.c.id == id)
        )

        results = project.kb.session().execute(stmt).fetchall()

        if len(results) == 0:
            raise NoResultFound(f"Could not find a molecule with id {id}")

        if len(results) > 1:
            raise DataIntegrityError(f"Found more than one molecule with id {id}")

        row = results[0]

        info = MoleculeInfo(
            name=row[0],
            smiles=row[1],
            fingerprint_dim=row[2],
            fingerprint_radius=row[3],
            ecfp4=row[4],
            fcfp4=row[5],
            maccs=row[6],
            inchi=row[7],
            properties=row[8],
            features=row[9],
        )

        # restore RDKit mol
        info.mol = Chem.MolFromSmiles(info.smiles)
        molecule = cls(name=info.name, smiles=info.smiles)
        molecule.info = info
        return molecule

    def to_kb(self, project):
        molecule_table = project.kb.db_tables["molecule"]

        stmt = (molecule_table.insert().values(
                project_id=project.project_id,
                name=self.info.name,
                smiles=self.info.smiles,
                fingerprint_dim=self.info.fingerprint_dim,
                fingerprint_radius=self.info.fingerprint_radius,
                ecfp4=self.info.ecfp4,
                fcfp4=self.info.fcfp4,
                maccs=self.info.maccs,
                inchikey=self.info.inchikey,
                properties=self.info.properties,
                annotations=self.info.features,
            )
            .returning(molecule_table.c.id)
        )

        result = project.kb.session().execute(stmt)
        mol_id = result.scalar_one()
        project.kb.session().commit()

        return mol_id

class Sequence(BaseSequence):
    def __init__(self, config, name, sequence, seq_type, features):
        self.config=config
        self._fastas()
        super().__init__(name, sequence, seq_type, features)

    @classmethod
    def from_fasta(cls, config, file):
        seq=super().from_fasta(file)
        cls(config, seq.name, seq.sequence, seq.seq_type, seq.features)
        return cls

    @classmethod
    def from_kb(cls, project, id):
        sequence_table = project.kb.db_tables["sequence"]
        stmt = select(sequence_table).where(sequence_table.c.id == id)
        result = project.kb.session.execute(stmt)
        info = result.scalar_one()
        return cls(name=info.name, sequence=info.sequence, seq_type=info.seq_type, features=info.features)

    def to_kb(self, project):
        sequence_table = project.kb.db_tables["sequence"]
        stmt = sequence_table.insert().values(project_id=project.project_id,
                                              name=self.info.name,
                                              sequence=self.info.sequence,
                                              seq_type=self.info.seq_type,
                                              annotations=self.info.annotations,
                                              hash=md5(self.info.sequence).hexdigest()).returning(sequence_table.c.id)
        result = project.kb.session.execute(stmt)
        seq_id = result.scalar.one()
        project.kb.session.commit()

        if self.seq_type=="dna":
            fasta=os.path.join(self.config["fasta_root"], "dna.fa")
        elif self.seq_type=="rna":
            fasta=os.path.join(self.config["fasta_root"], "rna.fa")
        elif self.seq_type=="protein":
            fasta=os.path.join(self.config["fasta_root"], "protein.fa")
        elif self.seq_type=="3di":
            fasta=os.path.join(self.config["fasta_root"], "tdi.fa")

        new_record=SeqRecord(Seq(self.info.sequence), id=result, description=self.info.name)

        with open(fasta, "a") as f:
            SeqIO.write(new_record, f, "fasta")

        return seq_id

    def _fastas(self):
        os.makedirs(self.config["fasta_root"], exist_ok=True)
        files = ["dna.fa", "rna.fa", "protein.fa", "tdi.fa"]  # tdi is 3di
        for file in files:
            if os.path.exists(os.path.join(self.config["fasta_root"], file)):
                continue
            else:
                Path(os.path.join(self.config["fasta_root"], file)).touch()
